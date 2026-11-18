# Coffee Shop AI Analytics

A Python 3.13 application for local video review, anonymous tracking, table
occupancy, product movements, directional crossings, POS reconciliation and JSON
reports. Paid POS lines determine sold units. A visible cup, zone departure or
candidate handover does not prove preparation, payment, a customer role or theft.

The supported application is `coffee_ops`. The repository is an offline pilot.
Real cafe accuracy, sustained operational performance and cloud staging have not
been validated. No weights, footage or operational database are bundled in Git.

The source is public at [CoffeeShop_Analytics](https://github.com/masma1234/CoffeeShop_Analytics),
branch `audit/deep-clean-20261115`. The original published baseline was
`097c1bd76d6c37efeb43fdab41dde9d6076596e7` (15 November 2026).
The owner authorized publishing the subsequent remediation, cleanup and
[project handoff](docs/PROJECT_HANDOFF.md) on 18 November. Use the latest branch
HEAD for the current source; the verification measurements below remain dated.
[Actions run 43731027661](https://github.com/masma1234/CoffeeShop_Analytics/actions/runs/43731027661)
passed all four Windows/Linux CPU/video jobs. Its image-security job failed:
62 high/critical package matches and no owner-selected root LICENSE.
Public source availability does not establish production readiness.

Local follow-up on 16 November benchmarks three permissive detector candidates
on 600 downloaded COCO images, with separate calibration and test partitions.
RT-DETRv2-R18 is the provisional pilot choice; cup recall remains insufficient
for reliable cafe counts. See the [model validation report](docs/benchmarks/model_validation_20261116.md)
for accuracy, stress tests, speed and remaining gates. No source license has been
selected. This follow-up is included in the owner-authorized branch update.
On 17 November all four Windows/Linux compatibility profiles and the separate
RT-DETR Linux profile passed all nine quality checks each. The rebuilt RT-DETR
image pins Transformers 5.23.0 and has **zero Trivy findings**, with a fresh SBOM
and passing isolated-container verification. Actual pretrained CPU inference
matched all 61 reference detections on 30 calibration images after preserving
the benchmark's PIL preprocessing. This is numerical compatibility, not new
cafe accuracy evidence. All 12 temporarily paused Docker containers were restored
and healthy. See [current verification evidence](docs/audits/release-verification-20261117.json).

Start with [current release gates](GITHUB_READINESS.md) and the
[post-publication audit](docs/audits/post-publication-20261115.md).
The [earlier cleanup audit](docs/audits/deep-clean-20261115.md) remains dated
historical evidence. Its 192-file inventory preceded two added audit reports;
the published commit contains 194 files.

[Implementation status](IMPLEMENTATION_STATUS.md) records current scope and gaps.
[Implemented architecture](docs/architecture/current_architecture.md) is the
authoritative architecture document. Proposals and historical measurements remain
separately identified.

## Host environment for legacy compatibility

The setup commands below retain the original YOLO compatibility environment,
which includes AGPL dependencies. For the owner's preferred RT-DETR direction,
`Dockerfile.permissive` and `requirements-lock-permissive-linux.txt` define a
separate, locally verified Python 3.13/Linux CPU profile without Ultralytics or
THOP. It pins Transformers 5.23.0 and passes native inference, the complete test
profile and the vulnerability gate. Source licensing, native-library notices,
reference/data rights and real cafe validation still block production approval.
The original `Dockerfile` remains legacy YOLO compatibility and retains its known
Debian findings. Use `-f Dockerfile.permissive` for the recommended profile.
Do not install both OpenCV wheel variants into the same environment.

Use the directory containing this README and `.git`, not its enclosing desktop
folder or home repository. Supported locks target Python 3.13, Windows AMD64 and
Linux x86-64. Other platforms need their own reviewed lock and native-operator test.
The 17 November storage cleanup retains `.venv-candidate` for CPU/video work.
The old GPU, notebook, base and disposable CI environments were removed after
preserving their package inventories. GPU training needs a fresh environment;
the retained host compatibility stack still has known dependency findings.
The separately verified RT-DETR Docker profile remains the recommended runtime.

```powershell
py -3.13 scripts/setup_environment.py --directory .venv-candidate --dev --video
$py = '.\.venv-candidate\Scripts\python.exe'
& $py -m coffee_ops validate-config
```

```sh
python3.13 scripts/setup_environment.py --directory .venv-candidate --dev --video
.venv-candidate/bin/python -m coffee_ops validate-config
```

Choose a fresh directory if `.venv-candidate` already exists. The helper refuses
to overwrite it. It handles Windows long wheel paths without registry changes,
installs pip 26.3, then installs every runtime package from the platform-specific
hash lock. Torch 2.13.0+cpu and Torchvision 0.28.0+cpu are a matched publisher pair.
`doctor` executes native NMS; package metadata alone is insufficient.
Development and optional video dependencies have direct version pins but do not
yet have full transitive hash locks. CUDA training is a separate, unvalidated
upgrade path described in [the notebook guide](notebooks/README.md).

To intentionally refresh a runtime lock, run `scripts/lock_requirements.py`
separately on each supported platform with `--input requirements.txt --output`
pointing to a new file, review its diff and rerun the full checks. One wheel hash
per package is platform-specific. Base-image digest and wheel hashes are fixed;
OS package repositories, transitive OS dependencies and optional/dev resolution
remain time-dependent. The separate RT-DETR Linux lock is refreshed using
`--input requirements-permissive.txt` on its supported platform.

## Run the synthetic workflow

```powershell
& $py scripts/verify_mvp.py --output var/acceptance-new
& $py scripts/check_quality.py --output var/quality-new
```

Use a new output directory each time. Acceptance exercises native operators,
an untrained YOLO architecture, replay, POS import, reconciliation, reports,
evaluation, repeated replay and expected failures. Unit tests and synthetic
fixtures establish software behavior, never real camera accuracy. The quality
runner records pytest/coverage, unittest acceptance, critical Ruff checks and
mypy with checked untyped function bodies. Its logs retain every exit code.

```powershell
& $py -m coffee_ops make-demo --directory var/demo-new
& $py -m coffee_ops --db var/demo-new.sqlite3 replay --source var/demo-new/fixture.avi --camera shop --run-id demo --start 2026-01-01T09:00:00Z --fixture-detections var/demo-new/detections.json
& $py -m coffee_ops --db var/demo-new.sqlite3 business-report --date 2026-01-01 --timezone Africa/Tunis --camera shop --run-id demo
```

The example config has no entrance calibration and no supplied operational
weights. Traffic zero without observation coverage is not verified zero traffic.
Calibrate exact camera dimensions, zones and line direction. Supply trusted local
weights and metadata with matching SHA-256 and class names. No silent fallback
downloads occur. Use offset-aware actual capture start times and immutable run IDs.

## Review a real local video

Follow [the video guide](docs/VIDEO_PROTOTYPE.md) after installing `--video`.
`prepare-video` requires a local RT-DETRv2 safetensors checkpoint. A checkpoint
cached on this laptop is local evidence, not an asset present in a clean checkout.
Pass `--model-dir` elsewhere. `annotate-video` produces an annotated MP4, PTS
journal, raw/accepted detections, event exports and unreviewed labeling templates.
Reviewed annotations and independent recording-group splits are required for
metrics. See [the annotation contract](docs/annotation_guidelines.md),
[evaluation workflow](docs/DATA_AND_EVALUATION.md) and
[benchmark protocol](docs/benchmark_protocol.md).

The public benchmark used only person/bottle/cup, 512-pixel inputs and thresholds
0.55/0.45/0.55. `prepare-video` defaults to a broader generic configuration;
it does not automatically reproduce those measurements. Record your class map,
thresholds, image size, precision and camera calibration explicitly. The COCO
thresholds have not been validated for a cafe camera.

Model startup logs identify the current import/load stage. One configured deadline
covers the whole worker startup; progress never extends it. Video processing
summaries retain startup timings and the last stage on a load failure. See the
[startup verification](docs/benchmarks/detector_startup_20261115.md) for measured
limits and the dedicated RT-DETR loader change.

## Local read API

Initialize the database with a writer first. Set `COFFEE_OPS_API_TOKEN` to a private
random ASCII value of at least 32 characters; do not put it in Git or a command log.
Run `python -m coffee_ops --db <existing-database> serve --port 8765`.
It binds only to 127.0.0.1. `/healthz` returns minimal liveness without credentials;
`/v1/health`, `/v1/cameras`, `/v1/status`, `/v1/events` and `/v1/business-report`
require the shared bearer token. There are no user accounts or tenant isolation.
The API is for a trusted local operator, not direct internet exposure.
See [the runbook](docs/deployment_runbook.md) for queries, backup and review steps.

## Docker verification

```sh
docker build -f Dockerfile.permissive --target production -t coffee-ops-local .
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,nosuid,nodev,size=128m --cpus 1 --memory 1g coffee-ops-local
python scripts/verify_container.py --image coffee-ops-local --backend rtdetr_v2 --output var/container-new.json
docker build -f Dockerfile.permissive --target test -t coffee-ops-video-tests .
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges coffee-ops-video-tests
```

Production runs as UID 10001, omits pip/ensurepip and copies only allowlisted
runtime files. Its default command validates configuration and exits. The host
verification script creates its own labelled temporary container and synthetic
database, checks auth/read-only root/blocked egress/native inference, and requires
graceful SIGTERM exit with Docker's three-second stop grace period. It records
the host Docker command duration separately; that is not a strict shutdown latency
bound. It mounts
no private data and publishes no ports. Docker limits must be supplied at runtime.
There is no deployed cloud service. Render private networking does not establish
internet egress denial; see [current release gates](GITHUB_READINESS.md).
The 1 GiB container check uses a tiny untrained integration model. Actual
pretrained parity ran separately with 2 GiB; neither establishes sustained
full-model capacity. The verified production image has 46 Python distributions;
Trivy additionally inventories vendored metadata, reporting 58 Python entries
and 35 OS packages in its 94-component SBOM.

## Evidence, licensing and publication

Current status is in [GitHub readiness](GITHUB_READINESS.md), with the latest
[security audit](docs/audits/post-publication-20261115.md) and
[model validation](docs/benchmarks/model_validation_20261116.md).
The [documentation index](docs/PROJECT_STATUS.md) points to the current guides.
Superseded guide copies were removed from the working tree at the owner's
request; their published versions remain recoverable from Git history.
The [workspace cleanup record](docs/audits/workspace-cleanup-20261116.md) explains
disk usage, actual removals, retained files and the exact generated-file cleanup
scope. Preview maintenance with `./scripts/cleanup_workspace.ps1`; add `-Apply`
to remove the listed reproducible artifacts. Old research environments are
removed only with the separate `-RemoveResearchEnvironments` switch and recorded
package inventories. Keep datasets, weights and operational data outside Git.
Raw local audit artifacts under ignored `var/` are not safe to upload wholesale.

No owner-selected source LICENSE exists. Ultralytics 8.3.163 and ultralytics-thop
declare AGPL-3.0; their obligations are separate from the license the owner chooses
for original project code. Checkpoint, dataset and reference-document rights also
need separate review. See the licensing options in the post-publication audit.
The recommended image passed its dated vulnerability gate; source licensing,
third-party rights and production validation remain unresolved. The owner
authorized this source publication on 18 November. History rewriting, reference
removal, visibility changes and deployment remain unauthorized. Future changes
must follow the owner's instructions. Start a new chat with the
[project handoff](docs/PROJECT_HANDOFF.md), not the old baseline alone.
