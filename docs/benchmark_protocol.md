# Operational benchmark protocol

Primary objective: correct observable events under a defined coverage and latency
budget. Detector AP and model-only FPS are supporting measurements. Real café
acceptance is pending authorized target-camera data.

## Reproduce the software baseline

From the project root, use the operational environment:

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe scripts/verify_mvp.py --output var/acceptance-unique
& .\.venv\Scripts\python.exe scripts/benchmark_mvp.py --output var/stress-unique.json
& .\.venv\Scripts\python.exe scripts/benchmark_events.py --output var/events-unique.json
```

Output paths must be new. The acceptance harness exercises real native CPU loading
with a tiny untrained model and synthetic replay/POS accounting. Neither establishes
model accuracy. `benchmark_events` uses supplied detections, Kalman tracking, event
logic and SQLite commits. It excludes model inference and decoding; saved stage
timings must not be presented as complete video-service capacity.

## Event scoring

```powershell
& .\.venv\Scripts\python.exe -m coffee_ops --output var/events-score.json evaluate-events --truth labels.json --predictions predictions.json
& .\.venv\Scripts\python.exe -m coffee_ops --db var/demo.sqlite3 export-predictions --run-id demo --camera shop --all-events
```

Use the [annotation contract](annotation_guidelines.md). Matching requires equal
scope declared by `scored_event_kinds`; annotate each listed kind exhaustively.
Kinds outside that task are excluded and reported. Within the task, matching requires equal
camera, event kind, product class, source/destination zones and line ID. Apply a
predeclared per-kind timestamp tolerance. Within each scope, global assignment
maximizes eligible one-to-one matches, then minimizes timestamp error. One prediction
cannot explain two events. Legacy single-camera labels may inherit an unambiguous
camera identity; mixed-camera omissions fail instead of wildcard matching.

Reports contain TP/FP/FN, precision/recall/F1, timestamp MAE, signed count bias,
absolute count error, per-class results, and repeated-event-ID rate. Repeated IDs
are only one kind of duplicate; different IDs for the same physical action still
require episode ground truth. Extra predictions remain false positives.

`duration_seconds` is annotated video exposure, not wall-clock runtime. Per-hour
false/missed event rates use scored exposure after subtracting unscored intervals.
No duration means these rates are unavailable. Uncertain/candidate predictions
are abstentions, not true positives; known ground-truth events still count as
missed. Unobservable ground truth needs explicit excluded intervals. Precision,
recall and percentage error remain null for undefined denominators.

Scoring is bounded to 10,000 events per clip and 2 million pair costs per scope.
Split larger material into independent annotated clips; do not exhaust laptop RAM.
The schema/CLI can score handover labels, but the runtime does not generate a
validated handover recognizer.

## Measurement and statistical design

Freeze source hashes, config, classes, dataset version, source FPS, sampling,
resolution, thresholds, precision, software versions, hardware and split. Record
exact detection/tracker/event recipes. Warm model-only measurements separately.
For a future real pilot, propose p95 event-confirmation latency <=2 s and event
precision >=0.95 / recall >=0.85 for entrances, with zero duplicate writes on replay.
These are proposed review targets, not achieved café results or fixed business SLAs.
Preparation/handover targets require a feasibility study and sufficient observability.

Measure per class/camera/day/lighting/occlusion/size. Aggregate count MAE and signed
bias over fixed hourly/day windows, including empty windows. Bootstrap confidence
intervals by independent recording/day, never by correlated frames. Preserve the
group manifest and random seed. With only one run or synthetic fixtures, report
the limitation rather than a population confidence interval. AP/speed alone do not
establish which architecture produces better business events.

Health now reports processing time, last capture time, reliable/unreliable frames,
calibration presence, p50/p95/p99 frame latency and detection/tracking/event/storage
stage samples. The detection stage is populated by runtime replay; direct fixture
calls have none. Decode/network buffering, evidence encoding and some orchestration
are outside individual stage timers. CPU/RSS exclude child workers and GPU metrics
remain unavailable. Use a full process-tree/GPU profiler before capacity claims.

## Controlled experiment registry

| Experiment | Current evidence | Decision |
|---|---|---|
| A detector | [Existing model study](benchmarks/performance_report.md), eight generic photos; zero cups | Keep YOLO11s/YOLO26s/RT-DETRv2-R18 as candidates; no café accuracy winner |
| B tracker | [Synthetic stress](validation-current/stress.json); identity fails beyond expiry/gating | Benchmark ByteTrack/BoT-SORT/OC-SORT on shared real detections before replacement |
| C sampling | [Foundation results](benchmarks/foundation_results.json), 12 controlled synthetic runs | Brief crossing detected at 10 Hz, missed at 5/2.5 Hz in this constructed case; no universal FPS recommendation |
| D ROI | No labeled small-cup footage | Plan same-resolution/full-frame versus crops/tiling, including coordinate transforms and latency |
| E temporal rules | New crossing/jitter/return/replay fault tests; current generic product states | Keep explicit rules; no preparation/handover claim |
| F fine-tuning | [Notebook API verification](benchmarks/notebook_verification.json), tiny person-only training | Training APIs work; no in-domain improvement established |
| G difficult scenes | Synthetic gaps/crossings plus known tracker failures | Real occlusion/crowding/transparent-container acceptance pending |
| H runtime | Existing FP32/FP16/CPU detector probes on the laptop | End-to-end optimized runtime and converted-model event equivalence unmeasured |

For every next run write hypothesis, changed variable, baseline, independent data
groups, configuration, metrics, uncertainty, failures and recommendation. Do not
rerun test clips to select a threshold. Export conversion, alternate trackers and
adaptive sampling require event-level regression evidence before adoption.
