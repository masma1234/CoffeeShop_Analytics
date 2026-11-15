# Café model experiments

Open [cafe_model_benchmark.ipynb](cafe_model_benchmark.ipynb). It is self-contained:
upload that single notebook to Kaggle/Colab, or run it with VS Code's notebook UI.
It trains YOLO11s, YOLO26s and the exact Hugging Face RT-DETRv2-R18 checkpoint.

## Run locally on the RTX 3050 laptop

From the project folder, create a separate environment:

```powershell
py -3.13 -m venv .venv-notebook
$trainpy = '.\.venv-notebook\Scripts\python.exe'
& $trainpy -m pip install --upgrade pip
# Matched publisher pair; verify availability/driver support for your platform.
& $trainpy -m pip install torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cu128
& $trainpy -m pip install -r requirements-notebook.txt
```

Select `.venv-notebook` as the notebook interpreter/kernel. For CPU use the official
CPU wheel index instead and set `DEVICE="cpu"`. See the
[official Torch version instructions](https://pytorch.org/get-started/previous-versions/).
The application's existing `.venv` is separate. The locally prepared research
kernel currently reuses the previously tested CUDA 2.9.0 stack through a local
`.pth` file; this saves duplicate multi-GB downloads but retains its known advisory
debt. A clean environment created with the commands above has no such inheritance.
The CPU variant of this pair passes application checks; CUDA training with it has
not been revalidated. Do not substitute Torch 2.14.x: the publisher reports an
[advisory affecting that series](https://github.com/pytorch/pytorch/security/advisories/GHSA-v32g-mr63-3j83).

1. Run the notebook with all heavy-action switches off to inspect the workflow.
2. Choose a dataset from the [verified source guide](../docs/research/training_datasets.md).
   The default is Kaggle Cup with `TARGET_CLASSES=["cup"]`: enable `RUN_DOWNLOADS`
   or attach it and set `DATASET_ROOT`. For three classes choose HF COCO / original
   COCO and set `TARGET_CLASSES=["person","cup","bottle"]`. For Kaggle Cup check
   its source label IDs (the verified sample uses **31**, mapped with `{31:"cup"}`).
   For a custom YOLO dataset declare the full source catalog
   and fully annotated classes explicitly.
3. Review the labeled image grid, class counts and split warnings. Start small.
   Enable `RUN_PRETRAINED` and `RUN_TRAINING`; 512 px, batch 1–2 and workers 0 are
   initial laptop settings, not measured maximum capacity. Train all candidates on
   the same prepared files. RT-DETR gradient accumulation is configurable.
4. Review validation results and freeze the settings. Run the final-test cell once
   with `RUN_FINAL_TEST=True`, then export with `RUN_EXPORT=True`. During a live
   kernel session, run later cells directly instead of rerunning the Settings cell,
   which creates a new run and clears in-memory results. Test data must stay out of
   subsequent tuning even if you create a new run directory.
5. Keep `var/notebook-experiments/<run>/`: audit, hash-bound dataset manifest,
   native YOLO training logs, RT-DETR history, checkpoint files, validation/test JSON
   and candidate ZIPs. Optional `RUN_VIDEO` renders a bounded local video preview.

On Kaggle select a GPU accelerator, enable Internet for model/dependency downloads,
and use Add Input for the large COCO dataset. On Colab select a GPU runtime. Install
optional dependencies using the notebook cell, then restart the kernel. Authentication
uses Kaggle's standard login/secrets mechanisms; never paste credentials into cells.
On remote platforms, explicitly download the output ZIPs before the session expires.

## How the comparison stays reviewable

Every detector uses the same images, target class order, train/val/test split,
inference resolution, score floor and reporting code. Reports include COCO-style
mAP50–95, AP50, per-class precision/recall/F1 at IoU 0.5, checkpoint/data hashes,
package versions, GPU allocation and synchronized p50/p95 latency. Disk image decode,
tracking and database work are excluded from that latency. YOLO and RT-DETR retain
their native model-specific preprocessing/training recipes; this is a practical
fine-tuning comparison, not a controlled proof of architectural superiority.

The audit rejects malformed geometry, missing labels, incomplete annotation
coverage, duplicate decoded image pixels and cross-split recording groups. Original
images are never changed. Missing positives and small class support are reported;
unrepresented validation/test classes block export. Near-duplicate visual similarity
and annotation completeness still need human review. Imports are bounded to keep
initial experiments small; increase limits only after checking disk/VRAM budgets.

The notebook is not a production promotion tool. YOLO26 requires a newer application
runtime, RT-DETR requires an operational adapter, and detector AP does not validate
tracking/event logic. Exports are research candidates for the next integration step;
no weights are automatically added to `models/` or Git. VLM/hybrid event evaluation
remains separate because the current public detector labels cannot score it fairly.

## Verification

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests execute the actual notebook helper cells and exercise geometry, annotation
coverage, duplicate/session leakage, source immutability, prepared-file tampering
and hash-bound exports. The optional notebook dependencies support nbformat schema
validation and nbclient execution. The notebook ships with empty outputs.

Run the default notebook in a real kernel and optionally test all three cached model
training/reload/evaluation/export APIs:

```powershell
& .\.venv-notebook\Scripts\python.exe -B scripts/verify_training_notebook.py
& .\.venv-notebook\Scripts\python.exe -B scripts/verify_training_notebook.py --smoke-training
```

The optional smoke requires the existing `var/model-benchmark/coco8` fixture and
publisher checkpoints; it downloads nothing. It repartitions those eight photos
for a one-epoch, person-only **API check** at 512 px with AMP, not an accuracy
experiment. [Saved verification evidence](../docs/benchmarks/notebook_verification.json)
records the results. The HF streaming download limitation is described in the
dataset guide; it is not reported as a successful download test.
