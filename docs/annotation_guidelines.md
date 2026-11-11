# Annotation contract and observable events

Version 1, 7 November 2026. This is the labeling specification for the next pilot,
not a claim that these labels or a trained cafÃ© recognizer already exist.
Machine-readable clip contract: [event_annotations.v1.schema.json](../schemas/event_annotations.v1.schema.json).

## Coordinates, time and identity

Use raw decoded-image pixel XYXY boxes, with image width/height recorded. Do not
rotate, crop or resize a frame without transforming its annotations and recording
the transform. Use the same class spelling/order in labels, model heads and config.
The notebook handles source-specific COCO XYWH and normalized YOLO conversions.

Each event clip belongs to one camera, one recording group and one annotation
version. `scored_event_kinds` explicitly lists the exhaustively annotated task
classes; other kinds in a full runtime export are excluded rather than assumed
negative. `time_origin_utc` is an offset-aware capture start; `seconds` is relative
to that start. The scored clip is `[0, duration_seconds)`. Mark the event's visible
transition at `seconds`; optional start/end describe its evidence interval.
Store temporary `track_refs`, never names, faces or cross-visit identities.

The legacy replay decoder assumes constant FPS. The optional annotate-video path
retains original VFR PTS in its journal and quantizes MP4 offsets to 1/60000 second.
Use that path for timestamp-sensitive local-video review. Live offsets measure decoder arrival elapsed time, not a camera exposure
clock. Network buffering is therefore a timing uncertainty. Processing health time,
event capture time and crossing confirmation time are distinct fields.

## Ontology

| Label | Positive evidence | Negative/unknown example | Current software |
|---|---|---|---|
| person | Visible person box, anonymous track across observable frames | Staff/customer role is unknown without independent evidence | Detection/tracking interface implemented; no shop weights supplied |
| cup / bottle / product | Visible, separately distinguishable item box | Stacked/hidden multiplicity is unknown; do not invent a count | Generic categories supported; custom labels require training |
| person_entered / person_exited | Continuous person anchor crosses the finite entrance line; stable residence on both sides | Appearance in view, touching the band, crossing its extension, or missing observations | Implemented with dwell/hysteresis; direction configured per camera |
| person_zone_entered | Stable calibrated zone transition | Zone membership is not a store entrance or customer identity | Existing transition engine; destination can be null when leaving |
| occupied / empty / unknown | Calibrated seating-region person evidence with temporal support | Standing beside a table, passersby, occlusion or unusable camera | Existing hysteresis; seated-presence accuracy unverified |
| placed / transferred / removed | Tracked item stabilizes in a new calibrated zone | A still image cannot establish movement | Implemented generic visual movements |
| disappeared | Previously observed item lost beyond timeout | No proof of destination, handover, preparation or sale | Review-required observation, not a completed business action |
| queue_joined / queue_left | Observable trajectory into/out of a queue with persistence | Walking past, starting mid-queue, or losing a track | Label schema can represent these; lifecycle/waiting estimator deferred |
| item_placed_at_pickup | Visible placement at a designated pickup surface | Cup elsewhere, disappearance, or restocking ambiguity | Implemented for continuous outside-to-pickup movement; initial presence is insufficient |
| preparation_completed | Visible, labeled completion action/transition at the preparation station | Closed cup alone or process hidden by a person | Not implemented; require evidence and independent labels |
| handover / pickup | Visible item transfer/pickup with temporally consistent interaction | Several reaching people, occluded item, or unassigned recipient | Advisory candidate_handover/item_left_pickup implemented; confirmed transfer/customer pickup unimplemented |

Pastry, tray and packaged-product classes are optional. Add only distinguishable,
fully annotated categories. Equipment and table regions are static calibration
unless evidence demonstrates a need for per-frame detection. A cup-only dataset
must not be treated as exhaustively annotated for people and bottles.

## Visibility, difficult cases and adjudication

Use `visibility=clear|partial|unobservable` and
`status=observed|confirmed|review_required|uncertain|unobservable|candidate` as
appropriate. Model abstention may use `abstained`. These express evidence state,
not calibrated probabilities or payment status. `confirmed` does not mean paid.

Tag clips for lighting, blur, reflections, tiny objects, overlapping people, hands
covering products, stacked cups, returns/replacement, crowding and camera movement.
All known visibility gaps must have sorted, disjoint `unscored_intervals` with a
reason. Exclude these intervals from both event scoring and observed exposure;
do not convert an unobservable event into a verified negative. Include complete
empty clips as `events=[]`; missing `events` means no usable event ground truth.

Double-annotate a proposed 20% of the first pilot, oversampling difficult clips.
This percentage is a planning choice. Reviewers must work independently before
adjudication. Use `evaluate-events` to measure one-to-one event agreement and
timestamp disagreement between matching clips. Event F1 agreement is not a
reliability coefficient or proof of annotation truth. Resolve disagreements with
a third review; retain versions, notes and the original labels. Do not overwrite
annotations in place or automatically turn model feedback into truth.

Clip IDs, recording group, camera, time origin and duration must agree when
comparing two versioned annotation documents. JSON Schema expresses the editing
contract; runtime checks additionally validate times, scope, confidence, capacity
and disjoint intervals. Quality/completeness still require human inspection.

## First collection and split plan

No cafÃ© footage is available yet. Start with an authorized, modest 2â€“4 hours over
several days and busy/quiet/lighting periods, then expand according to event
coverage. This is a proposal, not collected data or a sufficient sample guarantee.
Record all relevant doors and note blind areas. Mask private regions before
exporting annotations; keep access and retention controlled locally.

Split complete recording sessions before extracting frames. Maintain a fixed
validation set for thresholds and an untouched final test. Report whether a test
shares camera/store geometry with training. Within-camera day generalization and
unseen-camera generalization are separate questions. The operational dataset
validator currently demands stronger camera/environment separation than the
notebook's recording-group split: a notebook audit is not an automatic promotion
audit. Review that policy explicitly before the first real model promotion.

## Corrections

`review-crossing` appends confirmed/rejected/uncertain decisions and an evidence
note. It never changes the original observation. `business-report` applies the
latest decision to traffic totals; identical retries are idempotent. This review
workflow is deliberately limited to directional crossings. Product-event correction
must first be designed together with POS allocation revisions and item episodes.
The legacy `possible_unpaid_exit` name denotes a review candidate, never a finding
of nonpayment; exclude it from customer entrance/exit totals.
