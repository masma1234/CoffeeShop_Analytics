# Detector startup verification, 15 November 2026

This continuation targets the startup failure recorded in the 12 November audit.
The original RT-DETR attempt exceeded its 60-second deadline; a retry succeeded.
Those historical attempts remain preserved. No cafe footage or new labels are
available, and this change does not establish detector or event accuracy.

## Implementation

- The RT-DETR adapter now imports `RTDetrV2ForObjectDetection` and
  `RTDetrImageProcessor` directly. These are the classes in the
  [publisher's versioned example](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/rt_detr_v2#usage-tips).
  Architecture, native class IDs/names, processor type and hashed weight path are
  checked before loading. Existing checksum validation remains in place.
- Both detector adapters report fixed startup stages through their existing pipe.
  `detector_startup.py` enforces one absolute deadline from process start to ready,
  bounds the stage history and rejects invalid/repeated messages. Progress cannot
  extend the deadline. The configured 60-second default is unchanged.
- Cancellation, failed process creation, disconnects and deadline failures close
  the worker and pipe ends. Inference requires an `ok` response; startup messages
  cannot be mistaken for detection results.
- Successful and failed video processing summaries retain `detector_startup`.
  Its phase times are parent-observed operation starts, not isolated operation
  durations. Parent-side checkpoint hashing is outside this timer and inside the
  review's total wall time. Log messages use stderr; CLI stdout remains JSON.

The reviewed existing working tree was preserved as baseline commit `b2ebc3c` on
`fix/detector-startup-20261115` before edits. Only the nested project's Git index
was staged. No remote, push, deployment, model download or dependency upgrade
was performed. The earlier audit's security/licensing findings remain open.

## Import experiment

Four fresh Python processes ran in order: automatic, dedicated, dedicated,
automatic. Each imported Torch, then the relevant Transformers classes. All
imports succeeded. Local raw commands/results are retained under
`var/detector-startup-20261115/import-comparison.json`.

| Loader | Torch import seconds | Transformers import seconds | Process wall seconds |
|---|---:|---:|---:|
| Automatic, first | 15.98 | 88.95 | 106.67 |
| Dedicated, first | 12.52 | 26.75 | 40.77 |
| Dedicated, second | 11.30 | 30.20 | 43.20 |
| Automatic, second | 32.14 | 46.83 | 80.47 |

These are exploratory observations on the current Windows CPU environment, not
a controlled speedup estimate. OS/file caches were not cleared, other desktop
activity was uncontrolled, and the brief new unit-test invocation overlapped the
last automatic import. No model was loaded in this comparison, so it does not
measure ready time, inference latency or sustainable video FPS.

## Verification and reproducibility

The unchanged baseline passed 187 unittest tests. New fault tests exercise late
ready messages, progress without deadline refresh, malformed/repeated stages,
worker disconnects, cancellation, process-creation failure, wrong checkpoint
architecture/catalog/processor/path, and failed-summary preservation.

Run the checks from the folder containing `coffee_ops`, with a new output path:

```powershell
$py = '.\.venv-candidate\Scripts\python.exe'
& $py -B scripts/check_quality.py --output var/startup-quality-new
& $py -B scripts/verify_video_prototype.py --output var/startup-pretrained-new --device cpu
```

The pretrained smoke requires the already cached checkpoint and public COCO8
photo; it does not fetch either. Its eight repeated photo frames verify actual
inference, tracking, encoding and source-relative timestamps, with no accuracy
claims. Check `review/processing_summary.json` for startup stages and total time.

Final measured results and exact source hashes are recorded in
[the evidence JSON](detector_startup_20261115.json). The
[video guide](../VIDEO_PROTOTYPE.md) gives commands for a real local MP4.

| Check | Measured result |
|---|---|
| Windows unit suite | 200 pass; pytest also passes 41 subtests |
| Linux unit suite | 200 pass in the existing video-test image, current app/tests mounted read-only, network disabled |
| CLI acceptance | 21 expected command outcomes pass; synthetic replay/report/POS/review checks pass |
| Static/native checks | Final mypy passes 36 app modules; critical Ruff, pip check, native NMS and config validation pass |
| Coverage | 84% rounded overall; 98% for the startup deadline module. Subprocess inference is also checked separately |
| Actual CPU pretrained ready time | 31.23 s first run, 30.36 s replay; both below the unchanged 60 s deadline |
| Review wall time | 42.95 s first run, 42.21 s replay for eight repeated photo frames; not a sustained throughput estimate |
| Replay identity | Events and tracked frames identical; non-health ledger rows remain 148 before/after |
| Loader comparison | Preprocessing and postprocessing tensors equal; maximum raw logits/box differences both 0 on one CPU FP32 fixture |
| Video integrity | Eight output frames preserve offsets 0, 0.1, ..., 0.7 seconds; repeated annotated MP4 bytes are identical |

The first development fault-test invocation caught timeouts being misclassified
as disconnects because `TimeoutError` inherits `OSError`. The I/O catch is now
narrowed and both timeout regressions pass. The first quality invocation also
found an upstream argument-type mismatch exposed by the dedicated processor;
using its supported size-list argument passes final mypy and the real inference
comparison. Original failed outputs are not reclassified as successful checks.
No model deadline was extended to make a check pass.

The local example is
`var/detector-startup-20261115/pretrained-review/review/annotated.mp4`.
Raw evidence stays in that ignored experiment directory. Curated JSON retains
test/artifact/source hashes. Cleanup removed 29 generated files, 88,840,636 bytes:
quality-tool caches, the coverage database superseded by retained JSON, and the
hash-identical replay MP4. Exact hashes and completion are retained locally in
`cleanup-plan.json` and `cleanup-completed.json`. The primary example, source,
checkpoint, ledger and test logs remain. Empty cache directories may remain.

Fresh-process success does not establish cold-boot reliability or performance
under resource contention. The next useful accuracy experiment still requires
permissioned ceiling-camera video and independent event/frame labels before
choosing training or a more complex temporal model.
