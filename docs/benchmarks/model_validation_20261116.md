# Model validation and remediation, 16 November 2026

18 November publication: the owner authorized publishing this follow-up and the
[project handoff](../PROJECT_HANDOFF.md). Branch/HEAD and unpublished-state
statements in the dated body below describe the 16 November snapshot.

**17 November continuation:** [current release gates](../../GITHUB_READINESS.md)
and [fresh verification evidence](../audits/release-verification-20261117.json)
record five passing quality profiles, the rebuilt Transformers 5.23.0 CPU image,
zero Trivy findings and a fresh SBOM. An initial upgrade changed the default
processor and failed numerical parity. Explicit PIL preprocessing fixed that
drift: all 61 reference detections matched on 30 calibration images, minimum
box IoU 0.999995 and maximum score delta 0.0000508. This is CPU FP32 compatibility,
not a full held-out accuracy test or an upgraded CUDA FP16 benchmark. Worker
shutdown now allows two seconds for cooperative exit and one for forced cleanup
within the existing three-second budget; regression tests cover both paths.
The dated model measurements and failures below retain their original
environments; the 4.57.6 research results do not certify 5.23.0 cafe accuracy.

**Provisional pilot choice: RT-DETRv2-R18 at 512 pixels, CUDA FP16. Production
approval remains blocked.** The owner prefers a permissive stack and has left
the project's own license undecided. Nothing in this follow-up was pushed.

Published branch `audit/deep-clean-20261115` and local HEAD still point to
`097c1bd76d6c37efeb43fdab41dde9d6076596e7`. The published tree has 194 files;
192 was the cleanup inventory before its two audit reports were added.
The local changes and this report are unpublished review material.
At completion of this benchmark, the candidate contained 204 nonignored source files: the published 194 plus
two post-publication audit reports and eight files from this follow-up. Temporary
datasets, weights, environments and raw evidence are excluded from that inventory.
The owner's subsequent [workspace cleanup](../audits/workspace-cleanup-20261116.md)
removes superseded documentation; the 204-file count describes the pre-cleanup snapshot.

## What was measured

Downloaded the original COCO 2017 annotation archive and **600 images**, about
92 MiB of photographs, into ignored `var/model-validation-20261116/coco-targets`.
The manifest preserves source IDs, URLs, per-image license IDs, original labels,
dimensions, file hashes and decoded-pixel hashes. No duplicate decoded images
were found. Near-duplicate scenes and prior publisher validation-set tuning
cannot be ruled out.

Sampling uses four mutually exclusive strata: cup first, then bottle, then
person, then images with none of those labels. Each contributes 150 images.
Images with target-class crowd annotations are excluded. Seed 42 assigns
**300 calibration and 300 held-out test images**, with no shared source IDs.
This is a deliberately balanced subset, not the official full-COCO benchmark or
an estimate of cafe scene prevalence. The checkpoints already use COCO training.

Class thresholds maximize F1 at IoU 0.5 on calibration only. They are frozen
for clean, 35%-brightness and Gaussian 9x9 blur test conditions. AP uses
IoU 0.50:0.95, a prediction floor of 0.001 and standard maxDets=100. The metric
warning about discarded predictions beyond 100 is retained. No test labels are
used to tune thresholds. Stress transformations are diagnostic, not naturally
labeled low-light or motion-blur footage.

| Candidate | Clean test AP | Person F1 | Bottle F1 | Cup F1 | Cup recall |
|---|---:|---:|---:|---:|---:|
| RT-DETRv2-R18 | 0.463 | 0.811 | 0.623 | 0.543 | 0.421 |
| D-FINE Small | 0.465 | 0.823 | 0.583 | 0.506 | 0.390 |
| D-FINE Nano | 0.378 | 0.777 | 0.522 | 0.474 | 0.360 |

RT-DETR's person/bottle/cup thresholds are **0.55 / 0.45 / 0.55**. On clean test
images, cup detection has 69 true positives, 21 false positives and 95 misses.
Its cup F1 falls to 0.492 under dimming and 0.378 under blur. D-FINE Nano is
stronger on this particular blurred-cup probe despite weaker clean results.
These are observed differences on one sample, not a statistical superiority claim.

RT-DETR is preferred for the current pilot because of its cup/bottle operating
point and existing isolated application adapter. D-FINE Small remains the
overall-AP alternative; D-FINE Nano remains the smaller alternative. D-FINE has
only a research adapter here, not an approved production integration. YOLO is
excluded from this new selection under the owner's permissive-stack preference.
A VLM has no measured advantage here that justifies adding it to the counting path.

## Accuracy and inference alignment

- Fixed the YOLO worker to honor configured resolution and precision. Runtime
  and benchmark now share explicit square resizing, IoU and maximum detections.
- Fixed the Transformers benchmark to honor its requested image size and use
  dedicated model classes. Previously the processor could retain its default.
- Replaced per-detection CUDA transfers with three bulk tensor transfers,
  matching the RT-DETR worker. All 1,200 prediction lists per model, across clean
  and stress conditions for all three candidates, were identical before and
  after this transfer change.
- RT-DETR's clean-test detector p95 improved from 143.2 ms in the initial run
  to 67.7 ms in the repeat, with unchanged AP. Initial runs overlapped image
  construction, so the whole timing difference cannot be attributed solely to
  the transfer fix. These are local observations, not latency guarantees.

The GPU is the laptop's RTX 3050 6 GB. Research measurements use Torch
2.9.0+cu128 and Transformers 4.57.6. This research environment is separate from
the new CPU container, which uses Torch 2.13.0+cpu and Torchvision 0.28.0+cpu.
GPU benchmark speed does not establish CPU deployment performance or clear the
research environment's dependency-security findings. Image timing includes
preprocessing, model execution and result transfer, but excludes worker IPC,
tracking, database writes and video decoding/encoding.

| Repeat, clean test | Mean detector ms | p95 detector ms |
|---|---:|---:|
| RT-DETRv2-R18 FP16 | 50.9 | 67.7 |
| D-FINE Small FP16 | 59.4 | 81.9 |
| D-FINE Nano FP16 | 41.3 | 63.8 |
| RT-DETRv2-R18 FP32 | 37.4 | 51.0 |

FP32 AP was 0.462917 versus FP16 0.462507; cup TP/FP/FN and calibrated thresholds
were identical. The faster sequential FP32 run did **not** establish a stable
speed ranking: a separate alternating-order experiment on 40 calibration images,
three repeats, measured FP16 mean/p95 81.0/87.7 ms and FP32 138.2/144.7 ms.
That experiment kept two models resident and excludes image loading. These
different execution conditions and laptop variability limit throughput claims.
FP16 remains a provisional setting, with no material accuracy difference on this
sample. Test the single resident worker over a sustained real-video run before
setting a frame-rate or camera-capacity commitment.

An actual calibrated video run also passed using the same pinned weights,
512-pixel input, FP16 and class thresholds. All eight input frames passed through
the isolated detector, tracker, database and MP4 export. The input repeats one
public photograph, so it supplies no temporal or cafe-accuracy evidence.
Startup took 5.44 s; total wall time was 7.25 s. Frame-turnaround p50/p95 was
92.5/411.7 ms, including the cold first inference. This short cold run must not
be presented as sustained real-video throughput. The first local test harness
attempt lacked a Windows multiprocessing main guard; that harness was corrected,
and its failed log was retained separately from the successful application run.

The [machine-readable evidence](model_validation_20261116.json) records repeat
timings, precision comparisons, checkpoint hashes, tests and remaining gates.
Raw predictions and diagnostic logs remain local under
`var/model-validation-20261116`; they should not be uploaded wholesale.

The tested local configuration is
`var/model-validation-20261116/calibrated-prototype/configuration/config.json`;
the annotated smoke video is in its sibling `review/annotated.mp4` directory.
For a different video, use `prepare-video` to generate new dimensions and paths,
then apply the recorded class thresholds and calibrate its camera geometry.
Do not reuse this photo-loop camera configuration for another scene unchanged.

## Runtime and security remediation

Added `Dockerfile.permissive`, `requirements-permissive.txt` and a Linux x86-64
33-package hash lock. The candidate keeps Python 3.13, uses headless OpenCV,
Transformers and RT-DETR, and omits Ultralytics/THOP. Its Wolfi base is pinned by
digest, direct OS packages are pinned, and Python installs enforce wheel hashes.
Transitive OS repository availability remains time-dependent.

The actual candidate build completed as `coffee-ops-permissive:20261116`, image
index `sha256:4296db40777cb25e73605543c0930e7f3bd6148870a7ee19b4fbea17c8f76fb8`.
Dependency installation and `pip check` passed in the build. Subsequent isolated
runtime verification and Trivy scanning **failed before inspecting the image**:
Docker Desktop's API returned HTTP 500, including on its version endpoint.
There is no successful candidate scan, replacement SBOM or native-runtime result.

The [published Debian findings](../audits/post-publication-20261115.md) remain
open. The original Dockerfile and CI security/license gates are unchanged.
Replacing the OS and dependencies is a remediation candidate, not proof that
the 62 original matches are resolved. No finding is ignored or suppressed.

The drive fell below 0.5 GB free. Further large downloads, rebuilds and training
are blocked until space is restored. User-approved deletion of the old generated
audit tar and temporary environment was rejected by automatic tool policy
with only "blocked by policy"; neither was removed through another mechanism.
No reference document or Git history was deleted.

## Tests and limits

Fresh Windows video checks: **214 tests and 51 subtests passed**. Fresh Linux CPU
checks: **194 tests and 44 subtests passed, 20 optional-profile skips**.
Both profiles passed all nine checks: dependency consistency, native doctor,
configuration validation, pytest/coverage, coverage outputs, Ruff, mypy and
the CLI acceptance workflow. The isolated RT-DETR test loads locally generated
untrained weights and executes real inference; it is an integration test only.

Added regression cases cover calibration/test separation, deterministic splits,
negative images, crowd exclusions, duplicate IDs, invalid boxes, duplicate
detections, incorrect classes, missing calibration classes and configured worker
precision/resolution. Existing failure, concurrency, tracking, event, timestamp,
video and replay tests remain active. Optional YOLO tests skip only when that
backend is absent; RT-DETR has its own actual-worker test.

The 15 November audit passed all four Windows/Linux CPU/video profiles. This
follow-up has not completed a fresh four-profile matrix or clean candidate-image
test because of the environment blockers. Passing subsets do not stand in for
those pending checks. The candidate remains unsuitable for production release.

Git history scanning again reports four hash-related findings across seven
commits. Changed-source scanning reports the retained audit's SHA-256 value for
`candidate-secret-triage.json`, which was recomputed and matched. Raw scanner
exit codes remain nonzero; these are reviewed false positives, not suppressed
results. Existing identifying paths and reference-publication rights remain
documented in the historical audit and require the owner's decision.
Final Ruff and mypy checks passed again, as did `git diff --check`.
All 181 local Markdown link targets resolved; remote links and heading fragments
were not comprehensively rechecked in this follow-up.

## Reproduce and next steps

Use the notebook/research environment with Torch, Transformers, Torchmetrics,
faster-coco-eval, Pillow and OpenCV. Keep it separate from the runtime environment.
The annotation archive URL is
`https://s3.amazonaws.com/images.cocodataset.org/annotations/annotations_trainval2017.zip`.
Extract `annotations/instances_val2017.json`; the downloader verifies image
dimensions and hashes. Use new output directories for each experiment.

```powershell
python scripts/benchmark_public.py prepare --annotations annotations/instances_val2017.json --output var/public-coco --per-bucket 150 --seed 42 --download
python scripts/benchmark_public.py measure --dataset var/public-coco --model rtdetr-v2-r18 --revision 5650961749fa93567c0d46fc7f43ea4f9e914107 --precision fp16 --imgsz 512 --output var/rtdetr-measurement
```

Measurement requires the pinned checkpoint in the existing local cache; it
never downloads a model implicitly. The same command accepts `dfine-small` and
`dfine-nano` with the revisions in the JSON evidence.

No weights were retrained or promoted in this follow-up. Training on the frozen
evaluation subset would invalidate its purpose. The next useful training input
is independently annotated overhead cafe footage, split by recording/session
before extracting frames, including occlusion, tiny cups, clutter, low light and
empty scenes. Use the existing notebook to fine-tune only the training partition,
select on validation, and evaluate a locked test once. Generic cups do not prove
coffee preparation, payment or a handover; those need separate temporal labels.

Restore disk space and Docker first, then verify the candidate image, scan all OS
and Python packages, generate its SBOM/license inventory, and rerun all four
platform/profile checks from clean source. Only after those results and an owner
license/rights decision should CI's production image change or another publication
be considered. No deployment is authorized.

The [RT-DETR model card](https://huggingface.co/PekingU/rtdetr_v2_r18vd) and
[D-FINE Small model card](https://huggingface.co/ustc-community/dfine-small-coco)
declare Apache-2.0. This does not license the project's source or all bundled
native libraries. Preserve notices and review their individual terms. COCO
image-specific licenses remain separate from annotation terms; the download
manifest retains them. Consult [COCO terms](https://cocodataset.org/#termsofuse)
before redistribution. [Wolfi base documentation](https://images.chainguard.dev/directory/image/wolfi-base/overview)
describes the candidate OS; its security marketing does not replace our scan.
