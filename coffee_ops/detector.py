"""Replaceable detector protocol with isolated, deadline-bounded inference."""
from __future__ import annotations

import json
import multiprocessing as mp
import pickle
import threading
import time
from pathlib import Path
from typing import Any, Callable, Protocol, cast

from .config import Config
from .detector_startup import StartupDeadline
from .schema import Detection, file_hash


class Detector(Protocol):
    def detect(self, frame: Any, frame_index: int) -> list[Detection]: ...
    def close(self) -> None: ...


def validate_metadata(config: Config) -> dict:
    model = config.data["model"]
    weights, metadata = config.path(model["weights"]), config.path(model["metadata"])
    if not weights.is_file():
        raise FileNotFoundError(f"Model weights unavailable: {weights}; no automatic fallback")
    data = json.loads(metadata.read_text(encoding="utf-8"))
    if data["version"] != model["version"] or not data["dataset_version"]:
        raise ValueError("Model version/dataset metadata mismatch")
    expected = {str(cid): item["name"] for cid, item in config.catalog.items()}
    if data["classes"] != expected:
        raise ValueError("Model metadata classes differ from configuration")
    if data["sha256"] != file_hash(str(weights)):
        raise ValueError("Model weight checksum mismatch")
    if model.get("backend")=="rtdetr_v2":
        root=config.path(model["checkpoint_directory"])
        for name,digest in data.get("checkpoint_files",{}).items():
            if name not in {"config.json","preprocessor_config.json"} or file_hash(str(root/name))!=digest:
                raise ValueError("Checkpoint configuration checksum mismatch")
    return data


def _worker(connection: Any, weights: str, names: dict[int, str], device: str, threshold: float) -> None:
    # A broad catch is intentional only at this process boundary: preserve type and
    # message for the parent, which records failure and exits nonzero.
    try:
        import sys
        sys.stdout = sys.stderr  # Third-party model diagnostics must not corrupt CLI JSON.
        connection.send(("loading", "backend_validation"))
        from .health import backend_health
        backend_health()
        connection.send(("loading", "backend_import"))
        from ultralytics import YOLO
        connection.send(("loading", "model_load"))
        model = YOLO(weights)
        connection.send(("loading", "class_validation"))
        actual = dict(enumerate(model.names)) if isinstance(model.names, list) else model.names
        if actual != names:
            raise ValueError(f"Weight class names/IDs mismatch: {actual}")
        connection.send(("ready", None))
        while True:
            frame = connection.recv()
            if frame is None:
                break
            result = model.predict(frame, device=device, conf=threshold, verbose=False)[0]
            output = []
            for b in result.boxes:
                x1, y1, x2, y2 = map(float, b.xyxy[0].tolist())
                output.append(Detection(int(b.cls[0]), (x1, y1, x2, y2), float(b.conf[0])))
            connection.send(("ok", output))
    except Exception as exc:
        connection.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        connection.close()


def _validate_rtdetr_checkpoint(directory: str, weights: str, names: dict[int, str]) -> None:
    root = Path(directory)
    if (root / "model.safetensors").resolve() != Path(weights).resolve():
        raise ValueError("RT-DETR metadata must hash the actual model.safetensors being loaded")
    configuration = json.loads((root / "config.json").read_text(encoding="utf-8"))
    if configuration.get("model_type") != "rt_detr_v2" or configuration.get("id2label") != {str(cid): name for cid, name in names.items()}:
        raise ValueError("RT-DETR architecture or embedded catalog differs from configuration")
    processor = json.loads((root / "preprocessor_config.json").read_text(encoding="utf-8"))
    if processor.get("image_processor_type") != "RTDetrImageProcessor":
        raise ValueError("RT-DETR requires the supported RTDetrImageProcessor checkpoint")


def _rtdetr_worker(connection: Any, directory: str, weights: str, names: dict, enabled: set,
                   device: str, threshold: float, acceptance: dict, image_size: int, half: bool) -> None:
    try:
        import sys
        sys.stdout=sys.stderr
        connection.send(("loading", "checkpoint_validation"))
        _validate_rtdetr_checkpoint(directory, weights, names)
        connection.send(("loading", "torch_import"))
        import torch
        from PIL import Image
        connection.send(("loading", "transformers_import"))
        from transformers import RTDetrImageProcessor,RTDetrV2ForObjectDetection
        root=Path(directory)
        connection.send(("loading", "model_load"))
        model=RTDetrV2ForObjectDetection.from_pretrained(root,local_files_only=True,use_safetensors=True)
        connection.send(("loading", "class_validation"))
        if model.config.model_type!="rt_detr_v2" or model.config.id2label!=names:
            raise ValueError("RT-DETR architecture or embedded catalog differs from configuration")
        connection.send(("loading", "processor_load"))
        processor=RTDetrImageProcessor.from_pretrained(root,local_files_only=True)
        processor.size={"height":image_size,"width":image_size}
        connection.send(("loading", "device_setup"))
        model=model.to(device).eval()
        half=half and device.startswith("cuda")
        if half:model.half()
        connection.send(("ready",None))
        while True:
            frame=connection.recv()
            if frame is None:break
            height,width=frame.shape[:2]
            batch=processor(images=Image.fromarray(frame[:,:,::-1]),return_tensors="pt").to(device)
            if half:batch["pixel_values"]=batch["pixel_values"].half()
            with torch.inference_mode():output=model(**batch)
            prediction=processor.post_process_object_detection(output,threshold=.001,
                target_sizes=[(height,width)])[0]
            detections=[]
            for b,c,s in zip(prediction["boxes"].cpu().tolist(),prediction["labels"].cpu().tolist(),prediction["scores"].cpu().tolist()):
                if c not in enabled:continue
                x1,y1,x2,y2=b
                box=(max(0.,min(width,x1)),max(0.,min(height,y1)),max(0.,min(width,x2)),max(0.,min(height,y2)))
                if box[2]>box[0] and box[3]>box[1]:detections.append(Detection(int(c),box,float(s)))
            accepted=[d for d in detections if d.confidence>=acceptance[d.class_id]]
            connection.send(("ok",{"detections":accepted,"proposals":detections,"proposal_confidence_floor":.001,"gpu_peak_allocated_bytes":
                torch.cuda.max_memory_allocated(device) if device.startswith("cuda") else None}))
    except Exception as exc:
        connection.send(("error",f"{type(exc).__name__}: {exc}"))
    finally:connection.close()


class YOLODetector:
    """Historical public name; preserves the worker protocol for configured backends."""
    def __init__(self, config: Config, camera_id: str):
        self.metadata = validate_metadata(config)
        cfg = config.data["model"]
        self.timeout = cfg["inference_timeout_seconds"]
        self.last_model_metrics: dict[str, Any] = {}
        self.last_raw_detections: list[Detection] = []
        ctx = mp.get_context("spawn")
        self.connection, child = ctx.Pipe()
        thresholds = list(config.camera(camera_id).get("thresholds", {}).values())
        thresholds += [c["threshold"] for c in config.catalog.values() if c["enabled"]]
        # Keep lower-confidence proposals available for uncertainty handling;
        # per-class acceptance remains in Config.filter.
        thresholds.append(config.data["rules"]["low_confidence"] * 0.5)
        names={cid:c["name"] for cid,c in config.catalog.items()}
        arguments: tuple[Any, ...]
        target: Callable[..., None]
        if cfg.get("backend","yolo")=="rtdetr_v2":
            arguments=(child,str(config.path(cfg["checkpoint_directory"])),str(config.path(cfg["weights"])),names,
                       {cid for cid,c in config.catalog.items() if c["enabled"]},cfg["device"],
                       min(thresholds,default=.25),{cid:config.camera(camera_id).get("thresholds",{}).get(str(cid),c["threshold"]) for cid,c in config.catalog.items()},
                       cfg.get("image_size",512),cfg.get("half",False))
            target=_rtdetr_worker
        else:
            arguments=(child,str(config.path(cfg["weights"])),names,cfg["device"],min(thresholds,default=.25))
            target=_worker
        self.process = ctx.Process(target=target,args=arguments,daemon=True)
        startup = StartupDeadline(cfg["load_timeout_seconds"])
        self.startup_metrics = startup.metrics
        try:
            self.process.start()
            child.close()
            startup.wait(self.connection)
        except BaseException:
            self.close()
            raise
        finally:
            child.close()

    def _receive(self, timeout: float) -> Any:
        if not self.connection.poll(timeout):
            self.close()
            raise TimeoutError(f"Detector exceeded {timeout}s deadline")
        status, payload = self.connection.recv()
        if status == "error":
            raise RuntimeError(f"Detector failed: {payload}")
        if status != "ok":
            self.close()
            raise RuntimeError("Invalid detector inference response")
        return payload

    def detect(self, frame: Any, frame_index: int) -> list[Detection]:
        deadline = time.monotonic()+self.timeout
        sent = threading.Event()
        errors: list[BaseException] = []
        def send() -> None:
            try:
                self.connection.send_bytes(pickle.dumps(frame, protocol=5))
            except (OSError, EOFError, ValueError) as exc:
                errors.append(exc)
            finally:
                sent.set()
        sender = threading.Thread(target=send, daemon=True)
        sender.start()
        if not sent.wait(self.timeout):
            # On Windows, closing a pipe during an overlapped write can leave an
            # exported pickle buffer alive. Closing the peer unblocks send first.
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(timeout=3)
            sender.join(timeout=1)
            self.close()
            raise TimeoutError("Detector input transfer exceeded deadline")
        if errors:
            self.close()
            raise RuntimeError(f"Detector input transfer failed: {errors[0]}") from errors[0]
        payload=self._receive(max(0, deadline-time.monotonic()))
        if isinstance(payload,dict) and "detections" in payload:
            self.last_raw_detections=cast(list[Detection], payload.get("proposals",payload["detections"]))
            self.last_model_metrics={k:v for k,v in payload.items() if k not in {"detections","proposals"}}
            return payload["detections"]
        self.last_raw_detections=payload
        return payload

    def close(self) -> None:
        if self.process.pid is not None:
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(timeout=3)
        self.connection.close()


class FixtureDetector:
    """Explicit test/replay adapter, never a fallback for absent model weights."""
    def __init__(self, path: str | Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("purpose") != "pipeline_fixture_not_model_accuracy":
            raise ValueError("Fixture must explicitly declare its non-model purpose")
        self.rows = {int(row["frame"]): row for row in data["frames"]}
        if len(self.rows) != len(data["frames"]) or any(type(row["frame"]) is not int or row["frame"] < 0 for row in data["frames"]):
            raise ValueError("Fixture frame IDs must be unique nonnegative integers")
        self.metadata = {"version": "fixture", "dataset_version": "synthetic-logic-only"}

    def detect(self, frame: Any, frame_index: int) -> list[Detection]:
        if frame_index not in self.rows:
            raise ValueError(f"Missing fixture frame {frame_index}; no implicit empty detections")
        return [Detection(d["class_id"], tuple(d["bbox"]), d["confidence"]) for d in self.rows[frame_index]["detections"]]

    def close(self) -> None:
        pass
