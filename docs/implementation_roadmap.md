# Implementation roadmap and research gaps

Prototype update: [annotate-video](VIDEO_PROTOTYPE.md) supplies a local RT-DETR adapter,
PTS review, pickup evidence, labeling assets and evaluation. Real caf? labels,
confirmed action recognition, live recovery and production validation remain required.

Review date: 7 November 2026. The target is this laptop: i5-13450HX, approximately
16 GB RAM, RTX 3050 Laptop with 6,144 MiB VRAM. No authorized café footage, shop
ground truth or trained operational checkpoint is available. These are external
validation dependencies; they do not prevent software fault tests and an offline
prototype. No expensive training or large archive download is scheduled automatically.

## Priority and completion boundary

| Priority | Completed / retained in this repository | Required next evidence or work |
|---|---|---|
| P0 foundation | Baseline measured before changes; strict config/classes; isolated decoding/inference deadlines; atomic immutable ledger; scoped event scoring; annotation schema; dataset/license catalog; source URL hashing | Authorized recording collection, annotation QC execution, PTS-aware replay, patched native runtime/security audit, archival/retention policy |
| P1 traffic/table reporting | Person tracker control; calibrated directional crossing with dwell; replay-safe IDs; traffic correction revisions; local-day/hourly reports; time-weighted table coverage; authenticated local read API | Real entrance/exit and seating labels; calibrated numeric targets; live reconnect trials; dashboard built from the read API after data semantics are validated |
| P2 products | Generic placement/transfer/removal and review-required disappearance; training notebook and three detector candidates | Fully labeled shop classes, item episodes across fragmentation, object-person association, visible pickup/handover/preparation labels; product review/POS correction design |
| P3 optimization | Model-only CPU/GPU/FP16 study, stage timers, sampling counterexample, bounded active state and read API | Compare trackers on identical cached detections; ROI/tiling; full process-tree profiler; long-running multi-camera/storage growth; exported-model equivalence |
| P4 advanced | File/mock POS quantity conservation and refund revisions already work | Queue lifecycle/wait coverage, richer product categories, learned temporal model only if rules fail, controlled multi-camera association if justified |

Remote production deployment is not ready. The new HTTP endpoint is a local pilot;
no frontend, distributed coordination, live recovery SLA, calibrated event confidence,
production privacy approval or event-accuracy certification is claimed.

## Next complete experiment

1. Obtain permitted recordings spanning several days/operating periods. Document
   source ownership, camera/FPS/PTS, privacy regions and blind spots. Keep raw data local.
2. Calibrate doors/seating/queue/pickup regions, then label a modest representative
   pilot. Double-label difficult clips and adjudicate disagreement. Split by sessions
   before frame extraction; declare within-camera versus unseen-camera testing.
3. Run pretrained candidates with exact class mappings and cached detections. Evaluate
   class/size/lighting/occlusion recall and event errors. This establishes whether
   missing visual evidence, detection, association or event rules limit performance.
4. Fine-tune only classes with demonstrated error and complete labels. Compare the
   unchanged baseline and candidate on frozen validation, then an untouched test.
   The notebook provides the mechanics; it does not supply café ground truth.
5. Compare tracker controls and small-object crops before choosing a hybrid. Preserve
   low-confidence candidates for a ByteTrack experiment; the current class filter
   drops them before tracking, so plugging in ByteTrack alone cannot reproduce its
   association method. Staff/customer role stays unknown when unobservable.
6. Validate a patched runtime and exact weight/config combination, then offline
   replay, shadow live trials with outages, and a limited reviewed pilot. Promotion
   needs real held-out event/tracking/occupancy evidence plus rollback.

## Thirteen checks on the proposed gaps

These are project-specific evidence gaps, not claims of scientific novelty.

| Approach | Finding and countercheck | Feasible experiment |
|---|---|---|
| 1 claim to evidence | Public AP/speed tables score different tasks; local generic photos contain no cups | Reuse one annotated target-camera split for all candidates |
| 2 apparent disagreements | ByteTrack, BoT-SORT and OC-SORT differ in detections, appearance, motion and benchmarks | Fix input detections and compare both ID metrics and event errors |
| 3 operational definitions | Presence, preparation, handover and paid quantity are distinct | Annotate explicit positive/negative/unknown evidence per event |
| 4 assumptions | Constant FPS, stable geometry and track continuity currently matter | Test VFR, moved camera and missing-frame boundaries separately |
| 5 mechanism vs hypothesis | Finite crossing/dwell is implemented; handover inference is only proposed | Label visible interactions before adding a temporal classifier |
| 6 blind spots | Cup-only labels omit other targets; side/ego data mismatch ceiling view | Audit completeness and camera viewpoint before mixing sources |
| 7 generalization | One shop/day does not establish unseen-camera performance | Report separate session/day and camera/store holdouts |
| 8 negative findings | Long occlusion and distance jumps fragment the control tracker | Include these failures in regression, not only smooth examples |
| 9 temporal/object link | Item fragments need episodes before stable handover counts | Human-label object continuity and repeated handling |
| 10 repeated claims | Advertised FPS omits our decoding/ledger/network context | Profile complete capture-to-event latency and process tree |
| 11 ranking | Observability and label quality precede choosing a larger model | Error-source review on the first annotated pilot |
| 12 strongest gap challenged | Better detectors can reduce apparent temporal-rule errors; a learned temporal model may be unnecessary | Correct detections/association independently, then reassess rule failures |
| 13 executable work | Synthetic sampling already misses a brief event when processing less often | Repeat the controlled sampling experiment on complete labeled real clips |

The highest-impact unresolved issue is whether relevant preparation/handover evidence
is visible from the target cameras. If it is hidden, select a narrower observable
event or change authorized camera placement; more model complexity cannot recover
absent evidence. Conversely, clear visible transitions may be adequately served by
tracking and rules. Both outcomes must remain possible before selecting a model.

## Decisions to revisit

Retain SQLite until sustained concurrent writers/history scans show a real limit.
Retain the deterministic Kalman control until another tracker improves event outcomes.
Keep the three detector finalists until a real-label comparison identifies a winner.
Defer TensorRT/ONNX/quantization until a selected baseline and event equivalence test
exist. Reject face recognition, speculative customer identity, video-derived payment
judgments, indiscriminate dataset mixing and heavyweight distributed infrastructure
without a measured need. Training budgets and production thresholds remain reviewable
proposals; the tiny training smoke is not a cost forecast for a complete dataset.
