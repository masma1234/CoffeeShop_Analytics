# Coffee Shop AI Analytics

A Python 3.13 application for local video review, anonymous tracking, table
occupancy, product movements, directional crossings, POS reconciliation and JSON
reports. Paid POS lines determine sold units. A visible cup, zone departure or
candidate handover does not prove preparation, payment, a customer role or theft.

The supported application is `coffee_ops`. The repository is an offline pilot.
Real cafe accuracy, sustained operational performance and cloud staging have not
been validated. No weights, footage or operational database are bundled in Git.

[Implementation status](IMPLEMENTATION_STATUS.md) records current scope and gaps.
[Implemented architecture](docs/architecture/current_architecture.md) is the
authoritative architecture document. Proposals and historical measurements remain
separately identified.

## Set up a new environment

Use the directory containing this README and `.git`, not its enclosing desktop
folder or home repository. Supported locks target Python 3.13, Windows AMD64 and
Linux x86-64. Other platforms need their own reviewed lock and native-operator test.
Existing local research environments retain old dependency findings; preserve
them for evidence and create a new environment for current work.

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
apt security repositories and optional/dev resolution remain time-dependent.

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
docker build --target production -t coffee-ops-local .
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,nosuid,nodev,size=128m --cpus 1 --memory 1g coffee-ops-local
python scripts/verify_container.py --image coffee-ops-local --output var/container-new.json
docker build --target video-test -t coffee-ops-video-tests .
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges coffee-ops-video-tests
```

Production runs as UID 10001, omits pip/ensurepip and copies only allowlisted
runtime files. Its default command validates configuration and exits. The host
verification script creates its own labelled temporary container and synthetic
database, checks auth/read-only root/blocked egress/native inference, and requires
graceful SIGTERM completion within the existing three-second stop limit. It mounts
no private data and publishes no ports. Docker limits must be supplied at runtime.
There is no deployed cloud service. Render private networking does not establish
internet egress denial; see [deployment readiness](DEPLOYMENT_READINESS.md).

## Evidence, licensing and publication

Start with [the final engineering audit](FINAL_ENGINEERING_AUDIT.md),
[release evidence](RELEASE_EVIDENCE.md), [cleanup manifest](CLEANUP_MANIFEST.md)
and [GitHub readiness](GITHUB_READINESS.md). Historical results stay under
`docs/benchmarks`, `docs/validation-current` and `docs/history`; their original
dates, environments and limitations apply. Raw local audit artifacts are ignored
under `var/engineering-audit-20261112` and are not safe to upload wholesale.

No owner-selected source LICENSE exists. Ultralytics is AGPL-3.0, with commercial
licensing offered by its publisher. Do not describe it as permissive. Checkpoint,
dataset and reference-document rights need separate review. Public publication,
cloud deployment and real-business use remain gated by the release reports.
No remote, push, public repository or deployment is created by this audit.
