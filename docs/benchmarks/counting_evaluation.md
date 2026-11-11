# Counting evaluation status and protocol

**Blocked for real-world ranking:** the user confirmed no cafe video is available.
There are no independent labels for prepared drinks, handovers, table occupancy,
visits, queues or video-POS association. No model/pipeline has a measured score for
these business outcomes. A detector speed ranking is not an event-accuracy ranking.

Existing [logic-fixture results](../validation-current/fixture-evaluation.json) remain
valid only for their synthetic supplied detections: occupancy accuracy about 0.667,
event precision/recall 1.0 on three product movements, zero duplicated event IDs.
They do not score preparation or handovers. The stress tracker loses identity beyond
expiry/distance gates; this is a synthetic failure characterization, not real IDF1.

## Controlled real-video experiment

Freeze held-out session IDs, calibration, taxonomy and scoring policy before tests.
Use the same videos/detections for tracker comparisons and the same event/POS logic
for detector comparisons. Keep a deterministic baseline, detector+tracker candidate,
and detector+tracker+VLM ablation. Freeze VLM prompt, frame sampling, token limits,
temperature and review trigger. Include unsuccessful/abstained reviews in results.

Report per normal and difficult scenario:

| Layer | Metrics |
|---|---|
| Detection | Per-class precision/recall/AP, small-object recall, calibration; sufficient independent annotations required |
| Tracking | IDF1, ID switches, fragmentation and HOTA through an independently validated evaluator; HOTA is not currently implemented |
| Prepared / handover / returns | Separate event precision, recall, F1, false positive events/hour, duplicate rate, absolute count error |
| Daily totals | Signed and absolute count error, relative error only when true count is nonzero; keep observed and paid totals separate |
| Tables | Occupied/empty/unknown confusion, duration error, false occupancy time, entry/departure delay, turnover error |
| Queue / visits | Waiting-time and length error, missed/duplicated visits, ambiguous identity cases |
| POS association | Match precision/recall, ambiguous/unmatched rate, paid quantity conservation, refund behavior |
| Runtime | Warm/cold latency distributions, capture-to-event latency, processed FPS, drop rate, full process RSS/CPU/GPU/VRAM, review backlog |

Use global one-to-one event matching by event type/product/camera/zone and predeclared
time tolerance. Associate episodes without requiring guessed track IDs to equal human
labels. Missing ground truth means unavailable, not zero errors. Include recording
hours and event counts beside rates and uncertainty intervals.

Suggested pilot acceptance targets to agree before labeling (not achieved results):
handover precision at least 0.95, recall at least 0.90, duplicate rate at most 0.01,
per-session absolute count error reported, and detector p95 budget compatible with
the selected sampling rate. Occupancy targets must include unknown coverage and
detection delay. Production thresholds depend on business tolerance and scene rate.

Test crowded counters, identical/partially hidden cups, cup reuse, pickup/return,
restocking, low light, fast motion, scene changes, replay/restart, disconnection and
simultaneous cameras. Evaluate detector and VLM on negative clips too; descriptions
that sound plausible are not success evidence.

Current standalone model benchmark uses only eight generic COCO training photos and
brightness/blur perturbations, with no track/event ground truth. Its diagnostic AP
uses the project's 101-point evaluator, confidence-truncated predictions and a tiny
leaky subset; it is not official COCO mAP. Never use it to promote a model.
