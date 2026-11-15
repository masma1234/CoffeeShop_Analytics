# Run the inspectable local-video prototype

This extends the existing application; tracking, camera zones, transactional event
storage, traffic and POS modules are retained. The new path accepts a local MP4 and
produces an annotated MP4, tracking/event evidence, JSON/CSV exports and a processing
summary. **No real coffee-shop footage or manual café labels have been supplied.**
The actual pretrained-model check uses a clearly identified public-photo loop.

## Launch with the reviewed CPU environment

Run from the project folder containing `coffee_ops`. Follow the [current setup](../README.md)
with `--video` in a new environment. Old research environments retain known
advisory debt and are preserved for historical reproducibility.

```powershell
$vp = '.\.venv-candidate\Scripts\python.exe'
```

Prepare a configuration using your video's decoded dimensions and the local model:

```powershell
& $vp -m coffee_ops prepare-video --source 'C:\Videos\my-cafe.mp4' --directory var/my-video-config --device cpu
```

The default checkpoint is the already cached **PekingU/rtdetr_v2_r18vd** revision
`5650961749fa93567c0d46fc7f43ea4f9e914107`. Weights occupy 80,904,640 bytes. Nothing
is downloaded automatically. For another local RT-DETRv2 checkpoint add
`--model-dir 'C:\Models\my-rtdetr-checkpoint'`; it must contain `config.json`,
`preprocessor_config.json` and `model.safetensors`. Missing files fail explicitly.

Open `var/my-video-config/config.json`. Its camera is named `video`; the dimensions
match the decoded source. Initially `zones` and `crossing_lines` are empty so no
camera geometry is invented. Add your calibrated preparation/pickup/seating polygons
and entrance boundaries, then run:

```powershell
& $vp -m coffee_ops --config var/my-video-config/config.json annotate-video --source 'C:\Videos\my-cafe.mp4' --directory var/my-video-review --camera video --run-id my-video-001 --start '2026-11-07T10:00:00+01:00' --sample-every 1 --export-frames-every 5
```

Replace the example start with the actual recording start at the first decoded
presentation frame. Without zones the command still tests detection/tracking;
pickup, preparation and table observations require relevant calibration. The sample
rate and spatial/temporal thresholds are configurable experiment settings, not
validated optimal values. Use `--device cpu` when preparing a CPU config, or edit
the generated model device explicitly. No silent CPU fallback is used for a failed
CUDA model load. `--max-frames 300` bounds an initial source-frame trial.

Startup reports stages such as `torch_import`, `transformers_import`, `model_load`
and `device_setup` to stderr; stdout remains JSON. RT-DETR uses its dedicated model
and image processor classes, with exact checkpoint architecture/catalog/processor
validation before imports. The default 60-second `model.load_timeout_seconds`
still covers the entire spawned worker startup. Progress does not reset it. A
failure names the last stage, terminates the worker and writes the available
`detector_startup` diagnostics in `processing_summary.json`. Phase timestamps are
parent-observed operation starts, not isolated operation durations. Parent-side
checkpoint hashing is excluded from this startup timer and included in total
review wall time. See [the measured startup check](benchmarks/detector_startup_20261115.md).

Always choose a new output directory. To replay the same source/config without
duplicating ledger events, use the same run ID and database with another new output
directory. Changed source/config requires a new run. Keep sessions separate when
reviewing historical analytics. Exact confidence changes on nondeterministic hardware
can cause an immutable replay conflict; that fails visibly instead of rewriting data.

## Configure the scene and read the overlay

Zones support `preparation` and `pickup`, plus the existing table, queue, counter,
shelf, restock and exit kinds. A table needs `capacity`; polygons use raw source
pixel coordinates. Calibrate seated-person regions rather than only tabletops.
Use [directional line settings](deployment_runbook.md) for entrances. Overlapping
zones are ambiguous; do not overlap the entire preparation and pickup surfaces.
The pipeline does not automatically correct camera rotation or stabilize geometry.
Normalize orientation before calibration when necessary.

Accepted detections/tracks, temporary IDs, lost tracks, zone names, table states,
event times, detector confidence and evidence status are rendered. `?` identifies a
tentative track. Gray standalone boxes are accepted detections without a matching
track overlay. The source-frame timestamp and sampling status stay visible.
Unsampled frames get no current boxes; table/event displays refer to the last sample.
Low-score raw proposals are kept in data exports instead of flooding the overlay or
being treated as independently accepted people. Confidence is not a calibrated
preparation/handover probability.

## Output files

| File | Purpose |
|---|---|
| `annotated.mp4` | Review video, every decoded frame retained at source-relative PTS |
| `frames.jsonl` | Exact original PTS/time base, capture time, raw/accepted detections, sampled tracks and event IDs |
| `detections.json` | Streaming raw enabled-class proposals at confidence floor 0.001, for AP evaluation |
| `predictions.json` | Streaming tracked-frame/table/event export for the existing evaluation format |
| `events.json`, `events.csv` | Stable-ID event evidence and status; no paid-sale inference |
| `processing_summary.json` | Completion/failure, frame counts, latency scope, throughput, resources and unavailable business metrics |
| `run_manifest.json` | Source hash, config/root/hash, capture start, sampling and provenance |
| `annotation_frames/`, `annotation_frames.json` | Optional sampled JPEGs, exact frame/time/source/group mapping and image hashes; capped at 100 |
| `annotation_classes.txt` | Enabled class names in the proposed labeling order |
| `event_labels_template.json` | Source-bound **unreviewed** template; not accepted as ground truth |
| `error_report.json` | Event error cases and review taxonomy when labels exist; otherwise explicitly awaiting labels |

The generated configuration directory contains `model_metadata.json` and the
persistent `operations.sqlite3` ledger. Review artifacts can contain personal data:
keep them local, restrict access and apply the approved retention policy. Optional
frame extraction copies original imagery only when explicitly requested. No cloud
upload, facial recognition or persistent cross-visit identity is added.

## What the event layer can establish

| Event | Evidence used / limit |
|---|---|
| `product_visible` | Confirmed visibility episode of a track fragment; not a count of unique products/drinks |
| `product_present_at_pickup` | Product already visible in the pickup region when first observed |
| `item_placed_at_pickup` | Same continuously observed product seen outside, then stabilized inside pickup; initial presence alone is insufficient |
| `product_handled_candidate` | Sustained person proximity plus product motion; hands and role remain unverified |
| `item_left_pickup` | Visible product leaves its previously observed pickup region; recipient/action still uncertain |
| `candidate_handover` | Visible pickup-region departure with sustained nearby-person evidence; advisory only |
| `preparation_completion_unobservable` | Container at preparation region does not establish a completed drink |
| `unknown_product_state` | Track currently missing; absence is not pickup or handover |

No rule converts a cup, an occlusion or a dwell timer into confirmed preparation,
handover, customer pickup or payment. Therefore `prepared_drinks`,
`confirmed_handovers` and `customer_pickups` are **null**, not zero. A reliable
completion/transfer recognizer still requires visible evidence, independent labels
and validation. Staff/customer roles remain unknown. Reusable cups, returns and
track fragmentation need an item-episode policy before physical-unit counts.

The old generic `placed/transferred/removed` events remain for compatibility;
`placed` can include initial stable zone presence. Use the narrower semantic event
when asking whether placement at pickup was actually observed. Stable IDs and
transactions prevent replay duplication; they do not solve physical identity after
unobserved fragmentation. Paid quantities still come exclusively from POS.

## Label frames and evaluate the pretrained detector first

Use a local/self-hosted annotation tool such as CVAT; follow its
[installation guide](https://docs.cvat.ai/docs/administration/community/basics/installation/).
Do not send surveillance data to a hosted service without authorization. Import the
exported JPEGs, create the classes listed in `annotation_classes.txt`, annotate every
target class completely, and export [YOLO bounding boxes](https://docs.cvat.ai/docs/dataset_management/formats/format-yolo/).
Keep the exported `obj.names`/class-name order with the TXT labels; IDs are mapped
explicitly by exact class name, never guessed from numeric coincidence.

```powershell
& $vp -m coffee_ops --output var/my-detection-evaluation.json evaluate-video-frames --review-directory var/my-video-review --labels-dir 'C:\Labels\my-clip' --classes 'C:\Labels\my-clip\obj.names' --labels-reviewed
```

This verifies unchanged exported-image hashes, requires one TXT per exported frame,
maps annotation names to native model IDs, and streams the raw detections. Empty TXT
means a verified negative only after the explicit reviewed declaration. It reports
operating-point precision/recall/F1 separately from raw-proposal AP50/AP50–95. Errors
include missed boxes/false positives with frame/time references. Those are detector
outcomes against reviewed labels, not automatic explanations of occlusion/lighting.
Unrecognized products such as unsupported pastry categories are not silently renamed.

YOLO box export does not retain track identity or temporal events. For tracking use
CVAT/MOT identity labels and the [existing evaluation contract](DATA_AND_EVALUATION.md);
export only matching sampled frames. Keep whole recordings in one train/val/test
group. The source hash prevents mixing frames from one file, but related segments
from the same recording/day still need a shared session group. The training notebook
can consume the reviewed YOLO export with the exact source class list and group CSV.
Do not enable training before the pretrained errors justify it.

## Label and evaluate events

Copy `event_labels_template.json`; preserve `source_identity`, camera, time origin
and recording group. After human review set `annotation_status` to `reviewed` and
replace `events:null` with actual event annotations (or `[]` for verified zero).
Declare exhaustively labeled `scored_event_kinds`, explicit visibility exclusions,
event times/status and ambiguity. See [annotation guidelines](annotation_guidelines.md).
Double-label difficult clips and adjudicate disagreement before final scoring.

```powershell
& $vp -m coffee_ops --output var/my-event-evaluation.json evaluate-events --truth 'C:\Labels\my-events.json' --predictions var/my-video-review/events.json
```

For an integrated evidence/error report, run another new review output with
`--event-labels 'C:\Labels\my-events.json'`. This checks source/camera/start and
review status before model loading. It refuses labels outside a truncated trial.
Per-kind precision/recall/F1, timing error, false/missed events per annotated hour,
duplicates and count bias use the documented one-to-one matcher. An unimplemented
completion recognizer will miss annotated completions; those results are not hidden.
Do not iteratively tune rules on the final test recordings.

Event failures remain unclassified until evidence supports a cause. The report
offers detector miss/false positive, lost/switched track, occlusion, zone geometry,
temporal rule, deduplication, unobservable action and annotation ambiguity categories,
with video timestamps and frame-journal references. It does not invent causal labels.

## Model, timing, resources and measured status

The publisher lists the selected [RT-DETRv2-R18 checkpoint as Apache-2.0](https://huggingface.co/PekingU/rtdetr_v2_r18vd).
It is a permissively licensed detector candidate, not commercial clearance for every
dependency, codec, dataset or deployment. Exact weight/config/processor hashes and
the native 80-class catalog are checked. Safetensors/local-only loading is enforced.
Enabled categories are person, cup, bottle, donut and cake; this is not a trained
recognizer for every café pastry, SKU or drink subtype. The RT path does not call
Ultralytics; the existing YOLO backend remains available with its own license terms.
PyAV 19.0.2 declares BSD-3-Clause; bundled FFmpeg/codec distribution terms require
their own review. No license purchase or external inference service was used.

Original presentation timestamps are retained in `frames.jsonl`. Output MP4 timing
uses a 1/60000-second time base, with measured rounding error recorded. Odd dimensions
are padded on the right/bottom. Audio is omitted; source video bytes are unchanged.
The final-frame duration may use declared stream duration or a nominal-rate estimate
when a run is truncated. Missing/nonmonotonic PTS and corrupt input fail explicitly.

Decode and encode workers have two-frame queues and deadlines; inference retains
the existing process/transfer deadlines. Frame/error exports stream to disk, active
tracking state and timing windows are bounded, and optional labeling frames are capped.
Resource telemetry keeps aggregates rather than an ever-growing sample list.
Throughput includes worker loading and final encoder flush after preflight; parent
frame turnaround excludes asynchronous decoder/mux completion. RSS is a sampled
process-tree sum; NVIDIA utilization is device-wide. Short smoke timing is not a
steady-state or multi-camera capacity estimate.

[Verification results](benchmarks/video_prototype_results.json) and
[the actual annotated software-check MP4](../var/video-prototype-current/review/annotated.mp4)
record the completed checks. Reproduce with:

```powershell
& $vp -B -m unittest discover -s tests -v
& $vp -B scripts/verify_video_prototype.py --output var/video-check-new --device cuda:0
```

The model check repeats one public COCO8 photograph for eight frames. It establishes
actual pretrained inference → tracking → annotated MP4/JSON output and PTS fidelity,
not real-video event accuracy. Café detection sufficiency, preparation/handover F1,
table accuracy and the need for custom training remain **undetermined**. The next
highest-value step is a short authorized overhead recording plus independent frame
and event labels, followed by this unchanged pretrained baseline.

## Implementation map

New modules: `video_review.py` orchestrates the existing pipeline; `video_io.py`
owns PTS decoder/encoder workers; `video_overlay.py` renders evidence;
`product_evidence.py` implements conservative semantic states; `review_exports.py`
streams artifacts; `review_labels.py` maps/evaluates reviewed YOLO labels; and
`resources.py` samples bounded telemetry. Detector, config, event engine and CLI
are extended; the working tracker/POS transaction path is preserved.

Regression coverage is in `test_product_evidence.py`, `test_video_review.py` and
`test_review_labels.py`, alongside the original suite. The reproducible actual-model
check is `scripts/verify_video_prototype.py`. `requirements-video.txt` keeps optional
dependencies separate. No new shop training, model promotion, remote deployment or
Git push was performed.
