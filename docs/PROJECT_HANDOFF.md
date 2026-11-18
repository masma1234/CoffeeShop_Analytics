# CoffeeShop Analytics: handoff for a new chat

Prepared 18 November 2026. The verification results below are dated 17 November;
preparing or publishing this handoff is not a new model evaluation or test run.

## Start here

Continue the existing **CoffeeShop_Analytics** Python computer-vision project.
Verify the actual repository root before applying instructions from unrelated
projects or IDE tabs; those do not establish this project's scope.

Repository: https://github.com/masma1234/CoffeeShop_Analytics

Branch: `audit/deep-clean-20261115`.

The earlier published baseline was
`097c1bd76d6c37efeb43fdab41dde9d6076596e7`. The owner authorized publishing the
subsequent remediation, cleanup and this handoff on 18 November. Use the current
branch HEAD and its workflow results. Do not mistake the baseline's failed
Actions run or the dated local reports for the status of a newer commit.

Read these files in order:

1. [README](../README.md): purpose, setup, commands and boundaries.
2. [Release gates](../GITHUB_READINESS.md): publication, security and decisions.
3. [Architecture](architecture/current_architecture.md): implemented modules.
4. [Model evaluation](benchmarks/model_validation_20261116.md): measurements and limitations.
5. [Current verification evidence](audits/release-verification-20261117.json): exact image, tests and parity.
6. [Storage cleanup](audits/workspace-cleanup-20261116.md): the environment that remains.
7. [Dataset research](research/training_datasets.md) and [notebook guide](../notebooks/README.md): future experiments.
8. [Annotation guidelines](annotation_guidelines.md), [evaluation](DATA_AND_EVALUATION.md)
   and [benchmark protocol](benchmark_protocol.md): acceptance and data splits.

The [documentation index](PROJECT_STATUS.md) lists the other current guides.
Dated historical tables remain evidence of their original environments. Current
release gates and later explicit updates take precedence over their old status.

## Purpose and implemented behavior

The target is an overhead-camera coffee-shop analytics pilot on the owner's
laptop, previously identified as an RTX 3050 Laptop GPU with 6 GB VRAM. Recheck
available hardware and dependencies before new experiments.

The `coffee_ops` application implements local video decoding/replay, isolated
detector workers, anonymous tracking, calibrated zones, occupancy/dwell,
directional crossings, product movement episodes, reviewable event candidates,
SQLite persistence, POS reconciliation, reports and a loopback read API.
The optional video workflow produces overlays, source-timestamp journals,
detections and annotation templates. These are software capabilities, not
validated coffee-shop business metrics.

**Paid POS lines establish sold quantities.** A visible cup or movement does not
prove preparation, payment, a customer's role, a handover or theft. Preserve
unknown/unobservable states and neutral review language. No representative cafe
video or independently reviewed cafe labels had been supplied at the last audit.

There is no production dashboard, multi-user authorization, cloud deployment,
validated multi-camera capacity or production SLO.

## Model choice and actual accuracy evidence

The owner prefers a permissive model stack. Three candidates were measured on a
balanced 600-image COCO subset, with 300 calibration images and 300 disjoint test
images. Thresholds were chosen using calibration only and frozen for testing.
This is not full COCO or a representative sample of overhead cafe footage.
The checkpoints already use COCO training data; no new cafe training was done.

| Candidate | Clean test AP50:95 | Cup F1 | Cup recall |
|---|---:|---:|---:|
| RT-DETRv2-R18 | 0.463 | 0.543 | 0.421 |
| D-FINE Small | 0.465 | 0.506 | 0.390 |
| D-FINE Nano | 0.378 | 0.474 | 0.360 |

**Provisional pilot choice: RT-DETRv2-R18.** Its cup/bottle operating point and
existing isolated adapter fit the pilot. D-FINE Small is the overall-AP
alternative; Nano is smaller and performed better on one blurred-cup probe.
D-FINE has a research adapter, not a production application integration.
YOLO remains legacy compatibility; a VLM has no demonstrated advantage here.

The RT-DETR benchmark used 512-pixel inputs and person/bottle/cup thresholds
0.55/0.45/0.55. Cup detections had 69 true positives, 21 false positives and
95 misses out of 164 cups. Cup F1 fell under dimming and blur. These results
do not support reliable cafe counts or an operational accuracy claim.
Generic `prepare-video` defaults do not automatically reproduce these settings.

The historical GPU benchmark used Transformers 4.57.6. The upgraded runtime's
separate CPU FP32 parity check used 30 calibration images: all 61 reference
detections matched, minimum box IoU 0.999995 and maximum score delta 0.0000508.
That is numerical compatibility, not new held-out AP or upgraded CUDA FP16 proof.

## Runtime changes and verified boundaries

- YOLO runtime and benchmarks share explicit resolution/precision options.
- RT-DETR explicitly preserves PIL preprocessing across Transformers versions.
  The upgrade's default processor initially changed numerical results.
- GPU benchmark transfers use bulk tensors instead of per-box synchronizations.
- Workers enforce local/offline loading and bounded startup/inference behavior.
- Idle worker shutdown allows two seconds for cooperative exit and one second
  for forced cleanup, preserving the existing three-second total budget.
- Timeout and failure paths retain partial evidence instead of hiding failure.

The recommended Linux CPU build is **`Dockerfile.permissive`**, target
`production`, with a 46-distribution wheel hash lock. It pins Transformers 5.23.0,
Hugging Face Hub 2.4.0, Torch 2.13.0+cpu and Torchvision 0.28.0+cpu, without
Ultralytics or THOP. The dated local image scan found zero vulnerabilities and
generated a 94-component SBOM. Scanner/database timestamps and the exact image
digest are in the verification report. This is point-in-time evidence.

The original `Dockerfile` is a legacy YOLO compatibility image with the original
62 HIGH/CRITICAL Debian matches. Do not describe its packages as fixed because
the recommended image uses different components.

The five local Windows/Linux CPU/video/RT-DETR profiles passed their nine checks
on 17 November. After storage cleanup, the retained host environment passed
218 pytest tests, 51 subtests, Ruff, mypy across 36 application modules and
21 CLI acceptance commands. Coverage was 84.8% in that host profile.

Two post-cleanup acceptance attempts hit the unchanged 180-second unit-suite
deadline. Compiled runtime imports were restored; the final 218-test unittest
run passed in 107.817 seconds. The failed attempts remain recorded. Keep runtime
bytecode in the retained environment; removing every cache harms cold startup.
All 12 temporarily stopped Docker containers were restored and checked healthy.

Native/tiny-model tests establish integration behavior. Neither those tests nor
the 30-image parity sample establish cafe accuracy or sustained capacity.

## Files and environments available locally

The storage cleanup reduced the folder from 15.01 GiB to about 1.83 GiB.
Only `.venv-candidate` remains as the host CPU/video environment. The old base,
GPU, notebook and disposable CI environments were removed after inventory.
GPU training needs a fresh, separately validated environment. The retained host
compatibility dependencies still have known debt; the recommended Linux image
and the host compatibility environment are different profiles.

The three shortlisted checkpoints and all 600 benchmark images were retained
locally and hash-verified. They are **ignored local assets**, not GitHub contents.
A clean clone does not contain weights, video, operational databases or `var/`.
Use the provenance and download/setup guides; never assume cached files exist.
The research notebook is `notebooks/cafe_model_benchmark.ipynb`.

Generated audit-file cleanup largely succeeded. Automatic tool policy blocked
removing approximately 270 MiB of older evidence and a redundant archive. Those
files remain in ignored local storage. Do not claim they were removed or bypass
the rejection through a different filesystem method.

## Open decisions and owner constraints

- **Original source license is undecided.** Do not invent a LICENSE or select MIT
  on the owner's behalf. The strict root-LICENSE CI gate remains unsatisfied.
- Model cards declare Apache-2.0; Ultralytics/THOP declare AGPL in the legacy
  profile. Native FFmpeg reports LGPL version 3 or later. Exact distribution,
  linkage and notice obligations require separate review.
- Dataset terms are per image. COCO annotation labels identify 401 of the
  600 images as noncommercial and 198 as no-derivatives, with overlap. This is
  not current permission for commercial training. Do not train on the frozen
  calibration/test set or infer rights from the hosting platform.
- The two PDFs, DOCX and benchmark PNG remain unchanged. Provenance does not
  establish publication rights. Do not delete these assets or rewrite history
  without the owner's explicit approval.
- The 18 November request authorizes this publication to the existing branch.
  It does not authorize force-push, history rewriting, merges, visibility changes,
  deployment, license decisions or indefinite publication of future changes.
- Preserve security thresholds and unsuppressed findings. A published source
  repository is not a production release or a green workflow.
- Never publish `.env`, credentials, private evidence, operational databases,
  model caches, environments or other projects' files.

## Recommended next work

1. Inspect the current branch and its Actions run. Distinguish the new run from
   the old baseline run and the dated local evidence. Report failures plainly.
2. Obtain permissioned overhead cafe recordings across lighting, occlusion,
   crowding and quiet/busy conditions. Establish camera geometry and capture times.
3. Annotate complete target frames/tracks/events using the contract. Split whole
   recording sessions before extracting frames; keep an untouched test set.
4. Evaluate detection, tracking, event precision/recall, count error, unknown
   coverage and sustained end-to-end performance. Set acceptance criteria with
   the owner. Train only when the measured failures justify it.
5. Resolve source licensing and third-party/data/reference obligations separately
   before production distribution or deployment.

Do not restart the project or replace measured evidence with marketing claims.
If code or dependencies change, rerun the checks appropriate to the change and
record the environment, source/checkpoint hashes and validation limits.

## First message for the new chat

```text
Continue CoffeeShop_Analytics on branch audit/deep-clean-20261115.
Read docs/PROJECT_HANDOFF.md, README.md and GITHUB_READINESS.md first,
then the architecture and model-validation documents linked there.
Use the current branch HEAD. Summarize the implemented system, verified
results, unresolved gates and the next three useful actions. Do not start
over, invent cafe accuracy, choose a source license or deploy anything.
Treat dated test reports as prior evidence, not tests you have run yourself.
```
