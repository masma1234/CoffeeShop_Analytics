# Publication state and release gates

Publication verified 15 November; local verification resumed 17 November 2026.
The owner authorized publication of the remediation and handoff on 18 November.
Use the latest `audit/deep-clean-20261115` HEAD for source; dated test and scan
results below are prior evidence, not an automatically successful new CI run.
**Source published; production release blocked.**
This page supersedes earlier current-state instructions. It does not change the
status or original dates of historical audit evidence.

## Published source

- Repository: [masma1234/CoffeeShop_Analytics](https://github.com/masma1234/CoffeeShop_Analytics), public.
- Branch: `audit/deep-clean-20261115`.
- Original published commit and local audit baseline: `097c1bd76d6c37efeb43fdab41dde9d6076596e7`.
- Parent: `ef598c0bcabcd49289ce3f67aef600a274b54df3`.
- Published tree: **194 tracked files**. The cleanup inventoried 192 before adding
  `docs/audits/deep-clean-20261115.md` and its JSON companion in the parent commit.
  All 194 Git blob hashes match the Actions source manifest.
- The remediation, cleanup and new [handoff](docs/PROJECT_HANDOFF.md) are included
  in the owner-authorized 18 November branch update. The exact current commit is
  the branch HEAD; no merge, history rewrite, visibility change or deployment is
  part of that publication.
- The 17 November candidate had **193 existing nonignored files**: 194 published,
  minus 16 superseded documents, plus 15 new source/test/lock/audit files. The
  frozen source used for the final tests also had 193 files. Subsequent edits
  finalized documentation and the storage-cleanup helper; all 36 application
  files match the image and the tested source export.
- The 18 November handoff adds one Markdown guide: **194 current source files**.
  This equals the old published count for a different inventory: 194 original
  files, minus 16 superseded guides, plus 16 new source/test/lock/audit/handoff files.

## Actual GitHub Actions result

[Run 43731027661](https://github.com/masma1234/CoffeeShop_Analytics/actions/runs/43731027661)
executed against the original baseline, not the 18 November branch update:

| Job | Result |
|---|---|
| Windows CPU | Passed |
| Windows video | Passed |
| Ubuntu CPU | Passed |
| Ubuntu video | Passed |
| image-security | Failed |

The image scan completed and uploaded `image-security-evidence` (artifact
14168039662). Its Trivy report contains **61 HIGH and 1 CRITICAL matches**, across
24 advisories and 23 Debian binary packages. The artifact also contains a
177-component CycloneDX SBOM, 36 Python dependency license records, image metadata,
source hashes and passing isolated-container checks. The vulnerability gate and
the separate root-LICENSE existence check both failed. Four passing test jobs do
not override either release gate.

The source update triggers a new workflow. Inspect the
[current branch runs](https://github.com/masma1234/CoffeeShop_Analytics/actions?query=branch%3Aaudit%2Fdeep-clean-20261115)
for its actual results. The root-LICENSE check intentionally remains unsatisfied
until the owner chooses a license; publishing source does not waive that gate.

## Verified local remediation, 17 November

The recommended profile is `Dockerfile.permissive`, built explicitly with
`--target production`. The final image is `coffee-ops-permissive:20261117-verified`,
OCI index digest
`sha256:62c967fe065187fa76d79e37096fb400332c82645ad086918778db7c9caaf7d1`.
It pins Transformers **5.23.0**, Hugging Face Hub **2.4.0**, Torch **2.13.0+cpu**
and Torchvision **0.28.0+cpu** with a 46-distribution Linux wheel hash lock.

- **Image scan passed:** zero findings at any severity across 35 OS package and
  58 Python metadata entries, including vendored metadata. Trivy 0.76.2 used
  database updated 17 November at 13:00:16 UTC. The strict HIGH/CRITICAL rejection
  gate passed with no suppressions. CycloneDX SBOM: **94 components**.
- **Runtime passed:** non-root UID 10001, read-only root, no published ports,
  dropped capabilities, `no-new-privileges`, blocked egress on eight probes,
  authenticated private API, native NMS and tiny RT-DETR inference, graceful
  SIGTERM and absence of pip/ensurepip, Ultralytics and THOP.
- **Pretrained parity passed:** 30 calibration images, CPU FP32, 512 pixels;
  all 61 reference detections matched, minimum IoU 0.999995 and maximum score
  difference 0.0000508. Explicit PIL preprocessing preserves the benchmark
  contract after the dependency upgrade. No full new held-out AP or CUDA FP16
  benchmark is claimed.
- **Workstation restored:** the owner-approved temporary pause completed;
  all 12 previously running containers were restarted and verified healthy.

Initial failures remain recorded: workstation Docker timeouts, four HIGH and
one MEDIUM finding in Transformers 4.57.6, the upgraded tiny fixture's shared-head
configuration, preprocessing drift and insufficient cooperative worker shutdown
time under Windows. The final source fixes and reruns passed existing gates;
no vulnerability thresholds, timeout gates or scan exclusions were weakened.
See [verification evidence](docs/audits/release-verification-20261117.json)
and [model measurements](docs/benchmarks/model_validation_20261116.md).

## Outstanding release decisions

1. **Legacy image security:** the original `Dockerfile` remains a YOLO
   compatibility profile with the published 62 HIGH/CRITICAL Debian matches.
   The recommended image replaces its affected components; this does not make
   the old Debian packages fixed. Current vendor status, backport distinctions
   and all 62 findings remain in the
   [post-publication audit](docs/audits/post-publication-20261115.md) and
   [per-finding evidence](docs/audits/post-publication-20261115.json).
   Use the explicit RT-DETR build file. The scan is a dated result, not continuous
   assurance or a security clearance for legacy/research environments.
2. **Source and dependency licensing:** the owner has not selected a LICENSE.
   The legacy YOLO profile includes Ultralytics and ultralytics-thop, which declare AGPL; the original project license,
   combined distribution obligations, third-party notices and checkpoint/data
   terms require an explicit decision. A permissive root file alone cannot
   resolve these obligations. The RT-DETR candidate omits those packages, but
   PyAV's bundled FFmpeg reports LGPL version 3 or later; native libraries and
   distribution notices need review independently. Prefer the RT-DETR stack,
   preserve dependency/model notices and decide the original source license
   explicitly before distribution. No LICENSE has been created; that gate
   intentionally remains unsatisfied.
3. **Published reference rights:** the two PDFs, DOCX and benchmark PNG have been
   inspected. Metadata and citations are evidence of provenance, not permission.
   The audit recommends an owner-approved private archive for the three research
   references and retention of the benchmark chart after provenance approval.
   Nothing has been deleted; any history change needs separate authorization.
4. **Dataset/checkpoint rights:** the model cards declare Apache-2.0, but the
   downloaded COCO photos have individual terms: 401 of 600 carry noncommercial
   labels and 198 carry no-derivatives labels, with overlap. Those annotation
   labels are not a current rights clearance for training or commercial use.
   No photos or weights are included in source publication. See the
   [dataset review](docs/research/training_datasets.md).
5. **Operational validity:** no representative cafe ground truth, sustained
   multi-camera capacity, production authorization model or cloud deployment
   validation establishes production suitability. Synthetic tests cannot supply
   those results. RT-DETRv2-R18 is a provisional pilot choice: public-test cup
   recall is 42.1%, with 95 misses out of 164 cups. No training was performed on
   the frozen evaluation set. Collect permissioned cafe recordings, split by
   recording session, annotate independently and evaluate before training.

## Local verification and evidence

The [post-publication report](docs/audits/post-publication-20261115.md) records
fresh Windows/Linux CPU/video checks, image verification and scanning, license and
reference review, secret/history findings, link checks and clean-source setup.
It distinguishes passed checks, failures, incomplete checks and owner decisions.
All four 15 November local quality profiles passed their nine checks; their
Debian image retained the 62 findings. The final 17 November source export passed
all nine checks in **five profiles**, including package consistency, native
doctor/configuration, pytest/coverage, Ruff, mypy and 21 CLI acceptance commands:

| Profile | Pytest result | Statement coverage |
|---|---|---|
| Windows CPU | 197 passed, 21 optional skips, 44 subtests | 74.1% |
| Linux CPU | 197 passed, 21 optional skips, 44 subtests | 74.1% |
| Windows video | 218 passed, 51 subtests | 84.8% |
| Linux video | 218 passed, 51 subtests | 84.6% |
| Linux RT-DETR | 216 passed, 2 YOLO-only skips, 51 subtests | 84.6% |

Coverage measures the parent process; model subprocess inference also has
integration/parity evidence but is not merged into that coverage percentage.
The frozen 193-file clean source export excludes `.git`, private data, weights,
caches and generated artifacts. Windows used a fresh hash-locked CPU environment;
Linux compatibility and RT-DETR used their isolated test images. The notebook
passed actual smoke kernel execution without training or accuracy claims.
The tiny 1 GiB container smoke and pretrained 2 GiB parity do not establish
sustained full-model capacity. Optional/dev dependencies and transitive OS
resolution are not fully frozen.
Vendor checks and scanner database timestamps are recorded in the report so these
dated results are not mistaken for continuous security monitoring.
Raw artifacts are retained under ignored `var/post-publication-20261115` and
`var/release-verification-20261117`; review and sanitize evidence before sharing
it. Do not upload those directories wholesale. Secret scanning includes all
seven reachable commits and the current source. Raw scanner findings are
retained and individually reviewed as evidence-digest false positives; no
credential was identified. An account-specific historical wheel path was
redacted from the current environment inventory; Git history is unchanged.

The owner's later cleanup request removes superseded guide copies from the local
working tree. Current guides are listed in the [documentation index](docs/PROJECT_STATUS.md);
the [workspace cleanup record](docs/audits/workspace-cleanup-20261116.md) lists removals.
The latest [security audit](docs/audits/post-publication-20261115.md),
[model validation](docs/benchmarks/model_validation_20261116.md) and relevant
measurement evidence remain. Earlier guide versions are recoverable from Git history.
The later 17 November storage cleanup reduced the local folder from about
15.0 GiB to 1.83 GiB, retaining one CPU/video environment, all three shortlisted
checkpoints, all 600 benchmark images and all 193 candidate source files.
The GPU/notebook environments were removed after inventory; future training
requires a fresh installation. Additional removal of retired evidence and its
new archive was rejected by automatic tool policy; both remain. The cleanup
record distinguishes successful removals from that blocked final reduction.
The [previous readiness page](https://github.com/masma1234/CoffeeShop_Analytics/blob/097c1bd76d6c37efeb43fdab41dde9d6076596e7/GITHUB_READINESS.md)
is a historical snapshot; its no-remote/no-push and pre-publication instructions
are no longer the current state.

The owner approved publishing this remediation and handoff on 18 November.
That approval does not authorize deployment, license selection, reference
removal, force-push, history rewriting, branch merges or visibility changes.
The CI configuration selects the verified RT-DETR profile and retains the four
compatibility jobs, strict vulnerability rejection and root-LICENSE gate.
The original Actions failure above remains historical evidence; new run results
must be read from the current branch workflow, independently of local passes.
