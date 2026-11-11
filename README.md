# Coffee-shop operations analytics

A modular, CPU-first Python MVP for table occupancy, product movements, POS order
reconciliation, review alerts and daily JSON reports. **Video alone cannot prove
payment or theft.** Paid POS lines determine sold units; visual events remain
observations or neutral review candidates.

The supported application is `coffee_ops`. Legacy detector scripts, random-label
generators, synthetic-training helpers and duplicate entry points have been removed.
Use the commands below from the folder containing this README.

[Current project status and deliverables](docs/PROJECT_STATUS.md) links the
engineering review, measured limits, annotation contract and remaining roadmap.
The [offline pilot runbook](docs/deployment_runbook.md) covers calibrated traffic
lines, local business-day reports, review corrections and the authenticated local API.

## Inspect your own MP4 with a pretrained model

The [local-video prototype guide](docs/VIDEO_PROTOTYPE.md) provides setup, calibration,
model/license information, labeling and evaluation. The RT-DETRv2-R18 checkpoint is
already cached on this laptop; this path downloads no weights automatically.

```powershell
$vp = '.\.venv-notebook\Scripts\python.exe'
& $vp -m coffee_ops prepare-video --source 'C:\Videos\my-cafe.mp4' --directory var/my-video-config --device cuda:0
# Edit generated zones/boundaries, then supply the actual recording start:
& $vp -m coffee_ops --config var/my-video-config/config.json annotate-video --source 'C:\Videos\my-cafe.mp4' --directory var/my-video-review --camera video --run-id my-video-001 --start '2026-11-07T10:00:00+01:00' --sample-every 1 --export-frames-every 5
```

Outputs include `annotated.mp4`, tracking/PTS evidence, event JSON/CSV, labeling assets
and a processing summary. Pickup transitions and advisory interaction candidates
remain separate from preparation, confirmed handover and paid sale. Unsupported
business counts remain unavailable until independent evidence validates a recognizer.

## Install and check the runtime

Windows / Python 3.13:

```powershell
py -3.13 -m venv .venv
$py = '.\.venv\Scripts\python.exe'
& $py -m pip install torch==2.9.0 torchvision==0.24.0 --index-url https://download.pytorch.org/whl/cpu
& $py -m pip install -r requirements.txt
& $py -m coffee_ops doctor
& $py -m coffee_ops validate-config
```

Use this project's `.venv` interpreter in your IDE. A clean CPU environment was
installed and tested during the robustness review. The host's global Python had
incompatible Torch/TorchVision binaries; package metadata alone did not expose the
problem. `doctor` executes the native NMS operator and reports actual loaded versions.

Torch and TorchVision are pinned as a compatible pair using the
[official compatibility table](https://github.com/pytorch/vision#installation).
On Linux use `python3 -m venv .venv` and `.venv/bin/python` for the same commands.
The GitHub workflow defines Windows and Linux checks; only local Windows execution
has been verified here. The saved environment snapshot records transitive versions.

## Run the full test and acceptance workflow

```powershell
& $py -m unittest discover -s tests -v
& $py scripts/verify_mvp.py --output var/acceptance-new
& $py scripts/benchmark_mvp.py --output var/stress-new.json
```

Acceptance runs unit/integration/fault tests, a native CPU detector smoke test,
recorded-video replay, POS import, reconciliation, reporting, evaluation and repeated
replay. Tests use temporary files and clean them up. The detector smoke test creates
a tiny **untrained** network locally: it checks compatibility, never model accuracy.

The benchmark characterizes indexed reconciliation with 1,000/10,000 orders,
tracking crossings/occlusion/fast motion, and 5,000-frame expiry behavior.
[Verification, strengths and weaknesses](docs/VERIFICATION.md) links the measured
results. No real trained weights or shop footage are bundled.

## Directional traffic and local-day reports

Configure camera-specific `crossing_lines` as shown in the runbook before counting
entrances/exits. Missing observations reset crossing evidence; people appearing in
a frame are not entrance events. Directional crossings do not identify unique
customers or infer staff roles. The default example has no calibrated entrance.

```powershell
& $py -m coffee_ops --db var/demo.sqlite3 business-report --date 2026-01-01 --timezone Africa/Tunis --camera shop --run-id demo
& $py -m coffee_ops --db var/demo.sqlite3 export-predictions --run-id demo --camera shop --all-events
& $py -m coffee_ops evaluate-events --truth labels.json --predictions predictions.json
& $py scripts/benchmark_events.py --output var/event-benchmark-new.json
```

`business-report` uses observed-duration table coverage and explicit timezone/day
boundaries. Rejected/uncertain `review-crossing` revisions update traffic totals
without altering original observations. Paid units still come exclusively from POS.
The older `report` command remains UTC/sample-weighted for compatibility.

An optional bearer-authenticated, read-only HTTP API binds only to `127.0.0.1`.
See the runbook for `serve`, token setup, pagination and limits. It is a local review
service; dashboard, live reconnect and production hosting remain pending.

## Pretrained model comparison on this laptop

For the next training stage, open the self-contained
[training and benchmark notebook](notebooks/cafe_model_benchmark.ipynb).
[Setup and execution](notebooks/README.md) covers this laptop and Kaggle/Colab;
the [dataset guide](docs/research/training_datasets.md) compares verified Hugging Face
and Kaggle sources. It trains YOLO11s, YOLO26s and RT-DETRv2-R18, audits labels/splits,
and exports hash-bound research candidates for later integration. Heavy actions are
off by default; it does not add weights to the operational app.

The [model-selection report](docs/benchmarks/model_comparison.md) shortlists YOLO11s,
YOLO26s and RT-DETRv2-R18 for a real-video pilot. Eight actual pretrained detectors
were measured on CPU and the RTX 3050 in FP32/FP16; a small VLM was also probed.
[Measured performance and reproduction commands](docs/benchmarks/performance_report.md)
include raw results and a latency chart. This benchmark uses generic COCO photos
with zero cups, so it cannot establish coffee-shop accuracy.

Use the optional requirements-benchmark.txt in the separate .venv-bench environment
described in that report. The operational .venv stays on its verified CPU stack;
benchmark adapters and alternate trackers are not automatically deployed into it.
The operational detector defaults to FP32 and has no FP16 configuration key yet;
the measured FP16 mode belongs to the standalone benchmark until integrated and tested.
The [full research index](docs/research/README.md) links the resource inventory,
architecture audit, proposed counting design and remaining evaluation work.

A [direct-package advisory lookup](docs/audits/dependency_advisories.json) flagged
issues in the pinned Torch version. Functional test success is not security
clearance; validate a patched native-library pair before production and load only
trusted checkpoints. A complete transitive dependency audit is still outstanding.

## Demonstrate the complete pipeline without trained weights

```powershell
& $py -m coffee_ops make-demo --directory var/demo
& $py -m coffee_ops --db var/demo.sqlite3 import-pos --file var/demo/orders.json
& $py -m coffee_ops --db var/demo.sqlite3 replay --source var/demo/fixture.avi --camera shop --run-id demo --start 2026-01-01T09:00:00Z --fixture-detections var/demo/detections.json
& $py -m coffee_ops --db var/demo.sqlite3 reconcile
& $py -m coffee_ops --db var/demo.sqlite3 --output var/demo/daily.json report --date 2026-01-01
& $py -m coffee_ops --db var/demo.sqlite3 alerts
& $py -m coffee_ops --db var/demo.sqlite3 unresolved
```

This is a synthetic logic fixture with supplied detections. It tests video decoding
and business logic, not YOLO accuracy. The cup is placed, transferred, then disappears.
One paid POS unit matches the transfer; later movement does not consume a second unit.
The person's exit has no matching table order and remains a review candidate.

Use a new artifact path for another run: output files are never overwritten.
Replaying with the **same** source, run ID, camera, start time, model and configuration
deduplicates events. Different run IDs intentionally represent different sessions.
Do not replay the same business period under new IDs into the same operational ledger.

## Use actual footage

Copy `config/example.json` to `config/shop.json`, then configure:

- Real camera dimensions, sampling and non-self-intersecting ROI polygons.
- Exact model class IDs/names, enabled classes and per-class/per-camera thresholds.
- Table capacities and occupancy/movement timeouts.
- Explicit local weights and metadata, using `models/metadata.example.json`.
- Model version, dataset version and SHA-256 of the supplied weights.
- SKU mapping, matching window and POS mode: `file`, `mock` or `camera_only`.

Paths inside configuration resolve relative to its file. The sample is 320 x 240
with person, coffee_cup and table classes; choose actual classes from representative
human-labeled data. Seat zones must include seated people. Overlapping membership is
unknown. A camera move requires recalibration and a new session.

```powershell
(Get-FileHash models/shop-v1.pt -Algorithm SHA256).Hash.ToLower()
& $py -m coffee_ops --config config/shop.json replay --source footage/shop.mp4 --camera shop --run-id shop-session-1 --start 2026-11-04T08:00:00+01:00
& $py -m coffee_ops --config config/shop.json import-pos --file orders/2026-11-04.csv
& $py -m coffee_ops --config config/shop.json reconcile
& $py -m coffee_ops --config config/shop.json report --date 2026-11-04
```

No generic weights are downloaded or relabeled during inference. Model/metadata errors
fail clearly. For a camera, add `--live` and use `--source 0` or a stream URL.
Physical live cameras/RTSP remain unverified. Capture start must include a timezone.
Constant-FPS recordings are assumed; variable-frame-rate timestamp accuracy is deferred.

One active worker per camera/database is enforced by a renewable lease. Replay uses
bounded backpressure; live input uses a bounded newest-frame queue. Detector loading,
input transfer and inference have deadlines. Failed frame writes roll back atomically;
the in-memory pipeline must then be rebuilt by replaying from frame zero. Ctrl+C closes
workers. A crash releases ownership after lease expiry.

## Reports, review and evaluation

Global options `--config`, `--db`, `--output` precede the command.

```powershell
& $py -m coffee_ops status --camera shop
& $py -m coffee_ops history --kind events --limit 100 --after 0
& $py -m coffee_ops history --kind inventory_movements
& $py -m coffee_ops unresolved
& $py -m coffee_ops alerts
& $py -m coffee_ops feedback --alert-id ALERT_ID --resolution dismissed --false-positive yes --note "Staff restocking"
& $py -m coffee_ops drift --camera shop
& $py -m coffee_ops --db var/demo.sqlite3 --output var/demo/predictions.json export-predictions --run-id demo --camera shop
& $py -m coffee_ops --output var/demo/evaluation.json evaluate --truth var/demo/ground-truth.json --predictions var/demo/predictions.json
& $py -m coffee_ops --config config/shop.json --output var/model-evaluation.json evaluate-model --data dataset/data.yaml --split test
```

JSON is the MVP API; no network dashboard is included. History uses `_seq` cursors.
Reports use UTC days and paid POS units, not monetary revenue. Daily snapshots are
consistent database reads; revised POS states produce new aggregates. Unknown table
states are excluded from utilization and reported separately. Old-session observations
cannot become current when a new session starts. Health older than 60 seconds is stale;
running workers publish updates after their first processed frame and every five
seconds of processing. Stalls eventually appear unknown.

POS accepts immutable order-line revisions for paid/pending/cancelled/refunded states.
Ambiguous matches remain unresolved. Each visual track can allocate at most one paid
unit. Reports always sum the independent POS ledger. Alerts stay open until reviewed,
even when later order data explains them. Read current reconciliation for context.

## Data, model lifecycle and retention

```powershell
& $py -m coffee_ops extract-frames --video footage/shop.mp4 --directory dataset/raw --every 30
& $py -m coffee_ops --output dataset/split-manifest.json split-dataset --manifest dataset/manifest.json --seed 42
& $py -m coffee_ops --output var/dataset-audit.json validate-dataset --manifest dataset/split-manifest.json --minimum-examples 20
.\.venv\Scripts\yolo.exe detect train model=models/initial.pt data=dataset/data.yaml epochs=50 imgsz=640 device=cpu seed=42 deterministic=True project=var/training name=shop-v1
& $py -m coffee_ops --config config/shop.json promote --evaluation var/real-evaluation.json --dataset-audit var/dataset-audit.json
& $py -m coffee_ops rollback --registry-id PREVIOUS_PROMOTION_ID
& $py -m coffee_ops export-feedback --file var/review-queue.jsonl
& $py -m coffee_ops prune-evidence
```

Training requires real labeled data and explicit initial weights. Promotion requires
real held-out provenance, matching hashes and all configured thresholds. Rollback
records a previously promoted target; restore its artifacts/config and restart.
There is no automatic deployment or retraining.

Evidence JPEGs default to disabled. Retention pruning removes only generated JPEGs.
Source recordings and historical database retention require an operator policy.
See [privacy and access controls](docs/PRIVACY.md).

## Structure and maintenance

| Location | Responsibility |
|---|---|
| `coffee_ops/detector.py`, `tracker.py`, `video_input.py` | Replaceable vision and input adapters |
| `zones.py`, `event_engine.py`, `alerts.py` | Temporal operational rules |
| `pos_adapter.py`, `inventory.py`, `reconciliation.py` | Separate visual and paid-order ledgers |
| `storage.py` | SQLite transactions, migration, indexes, projections and leases |
| `pipeline.py`, `runtime.py` | Frame orchestration and worker lifetime |
| `reporting.py`, `exports.py`, `cli.py` | Read models, evaluation exports and command interface |
| `evaluation.py`, `dataset.py`, `mlops.py`, `health.py` | Measurement, labeling, registry and native backend checks |
| `config/`, `models/` | Configuration and metadata examples |
| `tests/`, `scripts/`, `.github/workflows/` | Regression tests, acceptance, stress characterization and CI |
| `docs/` | Architecture, schemas, labeling/privacy guides and current verification evidence |

Keep generated experiments under ignored `var/`; keep only the current curated
verification evidence in `docs/`. Tests clean their temporary videos, weights and
databases. Never delete operational footage, model artifacts or a live database as
routine source cleanup. The project virtualenv is needed to run the verified stack.

[Architecture and audit](docs/ADR-001.md) · [Data contracts](docs/SCHEMAS.md) ·
[Labeling and evaluation](docs/DATA_AND_EVALUATION.md) · [Verification](docs/VERIFICATION.md)

Remaining limits: SQLite has one writer and requires local disk; distributed/multi-site
scale is unverified. Tracking loses identity after long occlusion or motion outside
the gate. No appearance ReID, cross-camera identity, HOTA, operational VLM review,
POS webhooks, authenticated HTTP service or automatic historical-data archival is
implemented. Real shop accuracy and production inference throughput require independent
labeled recordings and an actual trained model. No project license has been selected.
