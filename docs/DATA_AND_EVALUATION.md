# Dataset, labeling and evaluation workflow

For a local MP4 start with [the video prototype workflow](VIDEO_PROTOTYPE.md).
It exports PTS-bound labeling frames and supports reviewed YOLO labels through
evaluate-video-frames. Operating-point metrics and raw-proposal AP remain separate.
Unreviewed event templates cannot be used as zero-event truth. Keep complete
recordings/sessions in one split and map annotation class names explicitly.

## Collect real representative data

Record authorized footage from actual fixed camera views across independent days,
shops/environments and cameras. Include empty tables, occupied/full tables, staff
restocking, legitimate movement, queues, difficult crossings, occlusion, bags,
blind spots, day/night lighting and changing shadows. Include verified empty scenes.
Keep difficult examples as a distinct review queue. Do not treat random/generated
boxes or synthetic demo detections as real training labels.

Extract sparse frames using the README command. Extraction refuses overwrite and
does not create labels. A human must inspect images and annotate YOLO normalized
`class_id center_x center_y width height`. Draw actual object boxes, not filename-
derived guesses. Select distinguishable product categories: a camera often cannot
tell latte from cappuccino in opaque cups. Do not promise subclasses without data.
The old random-label and synthetic-training root scripts have been removed.

Use a manifest with paths relative to the manifest:

```json
{
  "dataset_version": "shop-real-v1",
  "synthetic": false,
  "classes": {"0": "person", "1": "coffee_cup", "2": "table"},
  "images": [
    {"image": "images/a.png", "label": "labels/a.txt", "width": 1920,
     "height": 1080, "camera_id": "cam-a", "environment_id": "shop-a",
     "video_id": "session-a", "split": "train", "verified_negative": false}
  ]
}
```

This one-row example is intentionally insufficient for validation. Supply real
train/val/test images. The splitter keeps connected camera/environment/video groups
together; at least three disconnected groups are needed. With one shop/environment,
collect more environments for this strict policy instead of silently splitting
neighboring frames. Default group proportions approximate 60/20/20, independent of
frame counts. The output manifest must stay beside the input or its relative paths
must be adjusted. Splitting only writes a manifest, never moves images or labels.

Validation checks unreadable images, wrong dimensions, missing/empty annotations,
invalid boxes, class IDs, duplicate decoded pixel content, camera/environment/video
leakage, minimum class examples and >20:1 imbalance. Verified negative labels may be
empty. It cannot detect perceptual near-duplicates, annotation correctness, subtle
leakage or mislabeled class meanings. Human review remains necessary.

Create YOLO `data.yaml` with exact names and paths/file lists corresponding to that
manifest's three splits. A validation-only metrics report does not prove the manifest
and labels were independently audited. Record dataset and weight hashes and preserve
the command/environment. The example promotion gates are operational policy defaults,
not a guarantee that these thresholds are sufficient for your shop.

## Annotate temporal behavior independently

Ground-truth JSON uses frames from the exact sampled source. Do not generate ground
truth from system output for a real evaluation. Track IDs denote annotated objects
only within this recording. Table states should represent actual occupancy; the
evaluation then exposes delay introduced by smoothing.

```json
{
  "provenance": {"kind": "real_heldout", "annotator": "reviewer-reference"},
  "dataset_manifest_sha256": "digest-of-audited-manifest",
  "event_tolerance_seconds": 1,
  "frames": [
    {"frame": 0, "seconds": 0,
     "detections": [{"class_id": 0, "bbox": [20, 20, 80, 150], "track_id": "p1"}],
     "tables": [{"zone_id": "T1", "status": "occupied"}]}
  ],
  "events": [
    {"kind": "transferred", "product_class": "coffee_cup", "source_zone": "shelf",
     "destination_zone": "T1", "seconds": 3}
  ],
  "reconciliations": [
    {"event_id": "reviewed-system-event-id", "status": "confirmed_sale"}
  ]
}
```

Prediction frames use the same format with `confidence` and predicted `track_id`.
`export-predictions` creates predictions from a replay, with model digest and runtime.
Include `events: []` when no ground-truth movements occurred. Omit reconciliation or
occupancy annotations only when those tasks are intentionally not evaluated; their
metrics are null. For sales labels, independently review the event/order association;
reuse only the event reference ID, never the inferred status as ground truth.

Detection precision/recall uses class-aware one-to-one IoU >= .5 matching. AP ranks
predictions by confidence and integrates interpolated precision at 101 recall levels,
averaged over IoU .50:.05:.95 and ground-truth-present classes. ECE uses ten bins on
predicted-box confidence/correctness. This is not full COCO evaluation (no crowd/area
handling); use `evaluate-model` for the model library's validation too. A deployed
thresholded replay excludes low-confidence boxes, so its AP is threshold-truncated;
use independent raw low-threshold predictions for detector AP/calibration analysis.

IDF1 globally maximizes ground-truth/predicted ID overlap over spatial matches. MOTA
counts misses, false positives and ID changes. Fragmentation counts matched tracks
interrupted by misses. These are baseline metrics, not a complete MOTChallenge
implementation; HOTA is null. Missing tracking IDs produce null tracking metrics.
There is no cross-camera identity evaluation. Event matching uses global one-to-one
assignment within semantic/time gates; prediction order cannot change the match count.
Missing event ground truth yields null counting accuracy rather than a zero error.

Occupancy accuracy includes unknown predictions as incorrect against known truth.
False-occupancy duration integrates intervals until the next labeled frame (the last
frame has no inferred duration). Detection delay covers episodes eventually detected;
occupied recall also exposes missed episodes. Counts include absolute/percentage error,
over/undercount, event precision/recall with time tolerance and duplicate event IDs.
An equal count does not prove matching events; inspect event precision/recall too.
Reconciliation precision, false alert and missed sale rates require independent labels.

## Separate verification levels

| Level | Command / evidence | Meaning |
|---|---|---|
| Unit rules | `python -m unittest discover -s tests -p test_operations.py -v` | Geometry, state, ledger, POS, alert invariants |
| Storage faults/concurrency | `python -m unittest discover -s tests -p test_storage_resilience.py -v` | Races, locks, migration, batches, POS revisions and projections |
| Runtime faults | `python -m unittest discover -s tests -p test_failure_boundaries.py -v` | IPC stalls, rollback/replay, ambiguity and invalid input |
| Actual backend | `python -m unittest discover -s tests -p test_detector_backend.py -v` | Native CPU inference with temporary untrained weights; no accuracy claim |
| Dataset/evaluation unit tests | `python -m unittest discover -s tests -p test_evaluation_and_data.py -v` | Metric and validation calculations |
| Integration/replay | `python -m unittest discover -s tests -p test_video_integration.py -v` | Real codec and worker IPC with fixture detections |
| Reproducible fixture run | `python scripts/verify_mvp.py --output var/acceptance-new` | Persisted reports, repeated replay, known failure codes |
| Model evaluation | `evaluate-model --data dataset/data.yaml --split test` | Actual detector metrics; requires weights/labels |
| Operational evaluation | `evaluate --truth ... --predictions ...` on real replay | Independent tracking/occupancy/event/POS accuracy |
| Live testing | `replay --live ...` with authorized camera | Hardware, network, uptime; currently unverified |
| Monitoring | `status`, `history --kind health`, `drift`, feedback | Trends and review queues; not accuracy ground truth |

MVP runtime measures processing FPS, average/p95 selected-frame latency, orchestrator
CPU time/wall-time percentage, current RSS, and dropped live queue frames. Latency
includes inference IPC and business processing, not capture queue delay. Samples are
bounded to the latest 10,000. Child detector/decoder CPU/RSS and GPU utilization are
not instrumented; do not interpret these as total-machine utilization.

## Model feedback, promotion and rollback

Use `model-feedback --file feedback.json` with `outcome` equal to `false_positive` or
`false_negative`, `class_id`, `evidence` (frame/source references) and `note`. Export
using `export-feedback --kind model_feedback --file var/retraining-review.jsonl`.
This is a labeling queue, not automatic training data. Review corrections and keep
held-out examples out of retraining. Drift hooks expose class histograms and mean
confidence for comparison with a saved real baseline, without inventing accuracy.

Promotion checks real-heldout provenance, model SHA-256, dataset manifest SHA-256,
dataset version, a non-synthetic valid audit, and every configured metric threshold.
The gate trusts operator-supplied annotation provenance; signed datasets/reports are
deferred. Registry history records model/config/evaluation/audit hashes. Store actual
versioned artifacts in your protected model directory. Rollback selects a previously
promoted entry; restore the associated configuration and restart explicitly.
