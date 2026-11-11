# Verification record - 2026-11-07

## Latest local-video prototype verification

The [current video verification](benchmarks/video_prototype_results.json) records
**182 passing tests** in the isolated video environment and 182 tests with 13
optional-dependency skips in the unchanged operational environment. See the
[video test log](benchmarks/video_prototype_tests.txt) and
[operational log](benchmarks/video_operational_tests.txt). Actual cached RT-DETRv2-R18
inference reached tracking and encoded an eight-frame public-photo loop with matching
output PTS. This is a software/native-model check, not caf? accuracy. The source MP4,
annotated example and processing summary are in var/video-prototype-current.

The preceding foundation phase passed 161 tests with one optional skip and 21 CLI
checks; [its frozen evidence](benchmarks/foundation_results.json) retains source
hashes, ledger timings and synthetic sampling failures. The older record below
remains historical. No trained caf? model, real caf? labels, production uptime or
validated preparation/handover recognizer is claimed. Use the
[video guide](VIDEO_PROTOTYPE.md) for current source-PTS support and launch commands.

## Earlier CPU foundation record

**110 automated tests passed** in the isolated project virtualenv on Windows 11 / Python
3.13.2. End-to-end CLI acceptance passed, repeated replay preserved daily business
totals, and pip check reported no broken requirements. These results establish the
tested software behavior; real shop accuracy and production capacity remain unverified.
Current acceptance evidence was generated on November 7. The synthetic ledger/tracker
stress characterization is retained from November 4. The separate pretrained-model
study is in the [performance report](benchmarks/performance_report.md).

## Reproduce and inspect

Follow the installation commands in the [README](../README.md), using the project's
.venv interpreter rather than global Python. Run from the project root:

    .\.venv\Scripts\python.exe -m coffee_ops doctor
    .\.venv\Scripts\python.exe scripts/verify_mvp.py --output var/acceptance-new
    .\.venv\Scripts\python.exe scripts/benchmark_mvp.py --output var/stress-new.json
    .\.venv\Scripts\python.exe -m pip check

Choose new output paths: existing reports are never overwritten. The acceptance
harness uses temporary videos, databases and model weights, then cleans them up.

| Saved evidence | Contents |
|---|---|
| [Automated tests](validation-current/tests.txt) | Individual test names; 110 passed in 13.692 seconds |
| [Acceptance](validation-current/acceptance.json) | CLI exit codes, replay idempotence, actual loaded backend versions and environment |
| [Stress characterization](validation-current/stress.json) | Ledger scaling, tracking failure cases and bounded expiry workload |
| [Daily report](validation-current/daily-report.json) | Independent POS totals, visual movements and unmatched exit review candidate |
| [Fixture evaluation](validation-current/fixture-evaluation.json) | Detection, tracking, occupancy, event and reconciliation metrics with synthetic provenance |
| [Runtime](validation-current/runtime.json) | Short fixture replay timing, queue and orchestrator resource measurements |
| [Installed environment](validation-current/environment.txt) | Installed package versions; a snapshot, not a portable lockfile |

The CPU environment uses Torch 2.9.0+cpu, TorchVision 0.24.0+cpu, Ultralytics
8.3.163, OpenCV 4.11.0.86, NumPy 2.2.5, SciPy 1.15.2, PyYAML 6.0.2 and psutil 7.0.0.
The GitHub workflow defines Windows and Ubuntu checks; remote CI/Linux execution has
not been observed in this review.

The November 7 model study also verified CUDA inference in a separate research
environment. The limitations below concern the operational application and its real
shop validation. A [direct-package advisory check](audits/dependency_advisories.json)
flagged Torch vulnerabilities; these functional tests do not establish security clearance.

## Strengths supported by tests

| Area | Evidence and boundary |
|---|---|
| Durable records | Concurrent duplicate writes have one winner; immutable history rejects conflicting replay; nested savepoints, schema migration, injected disk failures and lock timeouts preserve consistency. |
| POS accounting | Concurrent reconciliation conserves paid quantities; refunds, restored orders, out-of-order revisions, ambiguous matches and camera-only mode are covered. A future payment cannot explain an earlier exit. |
| Recovery | Failed frame commits roll back database changes, remove uncommitted JPEG evidence and stop the damaged in-memory pipeline. Replay rebuilds state and deduplicates committed frames. |
| Worker control | Camera leases reject concurrent owners; expired owners cannot take over a replacement lease. Hung inference and blocked large IPC writes have deadlines and terminate their worker. |
| Reporting | Read snapshots stay consistent during concurrent POS updates. Resolved alerts do not hide later open alerts. Camera exports and current occupancy stay isolated across cameras and sessions. |
| Input validation | Duplicate JSON keys, unknown nested settings, malformed polygons, nonfinite timestamps, detection caps, invalid model classes and missing fixture frames fail explicitly. |
| Evaluation | Event matching is independent of input ordering; calibration bins do not double-count boundaries; absent event annotations produce unavailable accuracy metrics. |
| Native backend | A tiny locally generated, untrained model loads and executes CPU inference in the real worker. Incompatible embedded class names are rejected. This measures compatibility only. |
| CLI artifacts | An existing output artifact rejects a POS import before it changes the ledger. |

The native backend tests exposed incompatible global Torch/TorchVision binaries that
package metadata alone missed. The project now pins a compatible pair, uses an isolated
verified environment, and provides doctor to execute the native NMS operator.

## Measured scaling and weaknesses

The synthetic ledger workload uses unique matching zones and a local SQLite database.
It checks exact allocated quantities and unchanged allocations on repeated reconciliation.

| Orders | Visual events | First reconciliation | Repeated reconciliation | Peak Python allocation |
|---:|---:|---:|---:|---:|
| 1,000 | 100 | 0.034 s | 0.0010 s | 211 KB |
| 10,000 | 1,000 | 0.372 s | 0.0092 s | 759 KB |

Order import is timed separately in the JSON. Allocation peaks exclude native/OS
memory, and tracemalloc affects elapsed time. Indexed candidates and bounded batches
avoid rescanning every order for every event. Full reconciliation still visits event
history, and SQLite permits one writer. This single local run is not a production
capacity estimate or distributed-load test.

| Synthetic tracking scenario | IDF1 | Identity switches | What to improve |
|---|---:|---:|---|
| Smooth two-person crossing | 1.000 | 0 | Test crowded real crossings and noisy detections |
| Short occlusion within expiry | 1.000 | 0 | Tune expiry against labeled shop footage |
| Occlusion beyond expiry | 0.500 | 1 | Appearance association or a stronger tracker |
| Movement beyond distance gate | 0.333 | 2 | Tune motion gates and evaluate frame sampling |

The 5,000-frame expiry workload retained at most three active tracks and used a peak
9,176 bytes of traced Python allocation. This supports bounded tracker state under
that workload, not bounded historical database size or whole-process memory.

The 12-frame logic fixture has event precision/recall 1.0 and zero duplicate events.
Its detection metrics use supplied detections and establish **no model accuracy**.
Occupancy accuracy is **0.667**, occupied recall 0.714, entry delay 2 seconds and false
occupancy duration 2 seconds. Temporal smoothing trades responsiveness for stability;
this fixture does not meet the example real-data occupancy promotion threshold.
The three product events are evaluated separately from the unmatched person exit.

The fixture runtime JSON is a short decode/logic smoke measurement. It is not YOLO
inference throughput. CPU/RSS metrics exclude child detector and decoder workers.

## Remaining validation and improvement priorities

1. Supply compatible trained weights and independent real shop annotations, including
   dim light, glare, crowded tables, similar products, camera shake and partial visibility.
   Measure detection, tracking, occupancy, movement counting and POS association by scenario.
2. Evaluate an appearance-aware tracker against long occlusions and fast movement;
   adjust occupancy timing against measured false-positive and detection-delay tradeoffs.
3. Run sustained hardware/RTSP trials with reconnects, network loss and resource monitoring
   across the full process tree. Real CPU throughput, GPU operation and camera reliability
   are currently unverified.
4. Measure concurrent-camera and growing-history workloads before choosing production
   storage. Distributed coordination, database archival and a server database are deferred.

No real model training, promotion, deployment, external POS connection or payment
determination was performed. HOTA, appearance/cross-camera ReID, VLM review, POS webhooks,
an authenticated HTTP service and automatic historical retention are not implemented.

## Source cleanup

The supported application is now coffee_ops. Removed 24 obsolete root helpers and
configuration fragments plus three legacy-only test modules; their meaningful guards
are covered by the supported tests. Removed superseded validation reports, temporary
demo databases/videos and Python caches. The original project reference documents,
configuration examples, current evidence, source/tests and required project virtualenv
are retained. Operational footage and trained models must not be deleted as routine cleanup.
