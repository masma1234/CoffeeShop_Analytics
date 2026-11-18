"""Exercise a local image's auth, isolation and graceful SIGTERM shutdown.

Creates only its own temporary, labelled container. No host ports or private data
are mounted. The database/token are synthetic. A forced stop is a test failure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
import uuid


def native_probe(backend: str) -> str:
    common = """
import importlib.util,json,numpy as np
from coffee_ops.health import backend_health
health=backend_health()
assert importlib.util.find_spec('pip') is None
assert importlib.util.find_spec('ensurepip') is None
"""
    if backend == "yolo":
        inference = """
from ultralytics import YOLO
model=YOLO('yolov8n.yaml')
prediction=model.predict(np.zeros((64,64,3),dtype=np.uint8),imgsz=64,device='cpu',verbose=False)
assert len(prediction)==1
"""
    elif backend == "rtdetr_v2":
        inference = """
import torch
from transformers import RTDetrResNetConfig,RTDetrV2Config,RTDetrV2ForObjectDetection
assert importlib.util.find_spec('ultralytics') is None
assert importlib.util.find_spec('thop') is None
backbone=RTDetrResNetConfig(embedding_size=16,hidden_sizes=[16,32,64,128],depths=[1,1,1,1],layer_type='basic',out_indices=[2,3,4])
# Two decoder layers exercise the shared-head contract used by pretrained RT-DETR.
# Transformers 5.23 rejects the one-layer fixture's empty tied-head target set.
config=RTDetrV2Config(backbone_config=backbone,use_pretrained_backbone=False,num_labels=3,num_queries=10,encoder_hidden_dim=32,encoder_in_channels=[32,64,128],encoder_attention_heads=4,encoder_ffn_dim=64,encoder_layers=1,decoder_in_channels=[32,32,32],d_model=32,decoder_attention_heads=4,decoder_ffn_dim=64,decoder_layers=2)
model=RTDetrV2ForObjectDetection(config).eval()
with torch.inference_mode(): prediction=model(pixel_values=torch.zeros(1,3,64,64))
assert prediction.pred_boxes.shape==(1,10,4)
assert prediction.logits.shape==(1,10,3)
assert torch.isfinite(prediction.pred_boxes).all() and torch.isfinite(prediction.logits).all()
"""
    else:
        raise ValueError("Unsupported container smoke backend")
    return common + inference + "\nprint(json.dumps({'health':health,'backend':" + repr(backend) + ", 'untrained_architecture_inference':True,'model_accuracy_validated':False}))\n"


def verify(image: str, backend: str = "yolo") -> dict:
    native = native_probe(backend)
    identity = uuid.uuid4().hex
    name = "coffee-ops-check-" + identity
    token = "synthetic-isolated-test-" + "x" * 32
    result = {"image": image, "synthetic_only": True, "passed": False}
    container = None
    def docker(*arguments: str, check: bool = True):
        return subprocess.run(["docker", *arguments], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", check=check, timeout=60)
    try:
        result["image_id"] = docker("image", "inspect", image, "--format", "{{.Id}}").stdout.strip()
        bootstrap = ("import os,sys; from coffee_ops.storage import SQLiteStore; "
                     "s=SQLiteStore('/tmp/synthetic.sqlite3');s.close(); "
                     "os.execv(sys.executable,[sys.executable,'-m','coffee_ops','--db',"
                     "'/tmp/synthetic.sqlite3','serve','--port','8765'])")
        container = docker("run", "--detach", "--name", name, "--label", "coffee-ops.audit=" + identity,
            "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m", "--cpus", "1", "--memory", "1g",
            "--env", "COFFEE_OPS_API_TOKEN=" + token, image, "python", "-B", "-c", bootstrap).stdout.strip()
        deadline = time.monotonic() + 30
        probe = "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8765/healthz',timeout=2).read().decode())"
        while time.monotonic() < deadline:
            response = docker("exec", container, "python", "-B", "-c", probe, check=False)
            if response.returncode == 0:
                assert json.loads(response.stdout) == {"status": "ok"}
                break
            time.sleep(.2)
        else:
            raise RuntimeError("Local synthetic API did not become live")
        checks = """
import errno,json,os,urllib.request,urllib.error
from pathlib import Path
assert os.getuid()==10001
try:Path('/app/forbidden-write').write_text('test')
except OSError as exc:assert exc.errno in {errno.EROFS,errno.EACCES}
else:raise AssertionError('Root filesystem unexpectedly writable')
try:urllib.request.urlopen('http://127.0.0.1:8765/v1/health',timeout=2)
except urllib.error.HTTPError as exc:assert exc.code==401
else:raise AssertionError('Private readiness exposed')
request=urllib.request.Request('http://127.0.0.1:8765/v1/events?camera=shop',headers={'Authorization':'Bearer '+os.environ['COFFEE_OPS_API_TOKEN']})
with urllib.request.urlopen(request,timeout=2) as response:
    assert json.load(response)=={'events':[],'next_after':0}
print(json.dumps({'non_root':True,'root_read_only':True,'private_health_auth':True,'events':0}))
"""
        result["runtime"] = json.loads(docker("exec", container, "python", "-B", "-c", checks).stdout)
        egress = (Path(__file__).with_name("verify_egress.py")).read_text(encoding="utf-8")
        result["egress"] = json.loads(docker("exec", container, "python", "-B", "-c", egress).stdout)
        native_result = docker("exec", container, "python", "-B", "-c", native)
        result["native_smoke"] = json.loads(native_result.stdout.splitlines()[-1])
        start = time.perf_counter()
        docker("stop", "--time", "3", container)
        result["stop_seconds"] = time.perf_counter() - start
        inspected = json.loads(docker("inspect", container).stdout)[0]
        limits = inspected["HostConfig"]
        assert limits["NetworkMode"] == "none" and limits["ReadonlyRootfs"]
        assert limits["NanoCpus"] == 1_000_000_000 and limits["Memory"] == 1_073_741_824
        assert "ALL" in limits["CapDrop"]
        assert any(value.startswith("no-new-privileges") for value in limits["SecurityOpt"])
        result["runtime_limits"] = {key: limits[key] for key in
            ["NetworkMode", "ReadonlyRootfs", "NanoCpus", "Memory", "CapDrop", "SecurityOpt", "Tmpfs"]}
        result["exit_code"] = inspected["State"]["ExitCode"]
        result["published_ports"] = inspected["NetworkSettings"]["Ports"]
        result["stdout"] = docker("logs", container).stdout.strip()
        assert not result["published_ports"]
        assert result["exit_code"] == 0, "SIGTERM forced termination instead of graceful cleanup"
        assert json.loads(result["stdout"]) == {"status": "stopped"}
        result["passed"] = True
    except (AssertionError, OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            result["failed_command_stderr"] = (exc.stderr or "")[-8000:]
            result["failed_command_stdout"] = (exc.stdout or "")[-8000:]
    finally:
        if container is None:
            # A Docker client timeout can occur after the daemon creates the
            # container. Recover only our exact name and UUID label for cleanup.
            candidate = docker("inspect", name, check=False)
            if candidate.returncode == 0:
                inspected = json.loads(candidate.stdout)[0]
                if inspected["Config"]["Labels"].get("coffee-ops.audit") == identity:
                    container = inspected["Id"]
        if container:
            inspected = json.loads(docker("inspect", container).stdout)[0]
            assert inspected["Config"]["Labels"].get("coffee-ops.audit") == identity
            if inspected["State"]["Running"]:
                docker("stop", "--time", "3", container)
            docker("rm", container)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--backend", choices=["yolo", "rtdetr_v2"], default="yolo")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.image, args.backend)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
