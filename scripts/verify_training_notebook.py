"""Validate/execute the portable notebook; optionally smoke-train cached models.

Run with the optional notebook environment. Default execution downloads/trains nothing.
The optional smoke uses generic COCO8 photos and tests APIs, never café accuracy.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/cafe_model_benchmark.ipynb"


def load_namespace():
    namespace = {"__name__": "notebook_verification"}
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    with contextlib.redirect_stdout(io.StringIO()):
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                exec(compile("".join(cell["source"]), cell["id"], "exec"), namespace)
    return namespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-training", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "var/notebook-verification.json")
    args = parser.parse_args()
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager

    report = {"notebook": str(NOTEBOOK.relative_to(ROOT)), "schema_valid": False,
              "default_kernel_execution": False, "smoke_only": True,
              "accuracy_claims": False, "models": {}}
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    report["schema_valid"] = True
    # Explicit current interpreter avoids an unrelated global python3 kernelspec.
    km = KernelManager(kernel_name="python3")
    km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    NotebookClient(notebook, km=km, timeout=120, resources={"metadata": {"path": str(ROOT)}}).execute()
    report["default_kernel_execution"] = True
    if args.smoke_training:
        ns = load_namespace()
        ns.update(TARGET_CLASSES=["person"], IMAGE_SIZE=512, EPOCHS=1, YOLO_BATCH=2,
                  RT_BATCH=1, GRAD_ACCUMULATION=4, PATIENCE=1, AMP=True,
                  WARMUP_IMAGES=1, LATENCY_REPEATS=1, REAL_CAFE_DATA=False)
        import torch
        torch.set_num_threads(4)
        source = ROOT / "var/model-benchmark/coco8"
        if not source.is_dir():
            raise FileNotFoundError("Smoke requires existing COCO8 benchmark fixture; no implicit download.")
        rows = ns["import_yolo"](source, ns["COCO_NAMES"], ["person"], allow_empty=True)
        # COCO8's original train partition has no people. Repartition ONLY this
        # API-smoke fixture so each split has one positive photo. No quality claim.
        positives = [r for r in rows if r["labels"]]
        if len(positives) < 3:
            raise ValueError("Smoke fixture needs three person-positive images.")
        for row in rows:
            row["split"] = "train"
        positives[1]["split"] = "val"
        positives[2]["split"] = "test"
        rows, audit = ns["split_and_audit"](rows)
        run_dir = ns["RUN_DIR"]
        rows, digest = ns["prepare_dataset"](rows, ns["PREPARED"])
        report.update(run_directory=str(run_dir), dataset_audit=audit, environment=ns["environment"]())
        for name in ns["MODEL_NAMES"]:
            started = time.perf_counter()
            checkpoint = ns["pretrained_location"](name)
            trained = (ns["train_rtdetr"](checkpoint, rows, run_dir / name, digest)
                       if name == "rtdetr_v2_r18" else ns["train_yolo"](name, checkpoint, run_dir / name))
            adapter = ns["load_adapter"](name, trained, trained=True)
            result = ns["benchmark_adapter"](adapter, rows, "val", digest)
            final = ns["benchmark_adapter"](adapter, rows, "test", digest)
            ns["export_candidate"](name, trained, result, final, digest,
                                   run_dir / "smoke-exports" / (name + ".zip"))
            report["models"][name] = {"training_and_reload_passed": True,
                                     "test_and_export_passed": True,
                                     "elapsed_seconds": time.perf_counter() - started,
                                     "checkpoint_sha256": result["checkpoint_sha256"],
                                     "validation_images": result["images"],
                                     "finite_metrics": result["ap"]["map"] is not None}
            del adapter
            torch.cuda.empty_cache()
            print(name, "train/reload/evaluate passed", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
