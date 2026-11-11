# Technical decision report — 7 November 2026

This document records the foundation phase. The subsequent [video prototype](VIDEO_PROTOTYPE.md)
and [verification](benchmarks/video_prototype_results.json) add actual RT-DETR inference,
PTS-aware annotated output, semantic candidates and reviewed-label evaluation. They
supersede earlier missing pilot-adapter/PTS statements; production and caf? accuracy
remain unverified.

## Current assessment and adopted changes

Preserve the modular CPU application, supervised detector/decoder processes,
deterministic tracker, transactional immutable SQLite records, POS quantity
conservation and model promotion gates. The initial baseline was **126 tests, 125
passed / one optional ijson skip**, plus a fresh synthetic ledger/tracker benchmark.
Current verification and raw experiment records are linked in
[foundation_results.json](benchmarks/foundation_results.json).

Implemented in this pass:

- Configurable finite directional lines with center/bottom-center anchors,
  dwell/hysteresis, continuous-track evidence, explicit direction and anonymous roles.
  Initial appearance, boundary jitter and missing observations do not establish entry.
- Capture-time crossing records persisted in the same frame transaction. Replay after
  a failed write rebuilds state and deduplicates committed records.
- Append-only confirmed/rejected/uncertain traffic reviews with idempotent retries.
  Local business-day/hourly totals apply the latest review without rewriting evidence.
- IANA timezone and shifted-day reporting, including 23/25-hour DST days. Table
  utilization is weighted by observed duration, caps stale-state extension, reports
  unknown/unobserved time and rejects overlapping camera runs without an explicit run.
- Event-only evaluation with exact camera/line/class scope, one-to-one assignment,
  per-kind tolerances, F1, timing error, signed bias, false/missed events per annotated
  hour, abstentions and unscored visibility intervals.
- Authenticated loopback read API with read-only SQLite connections, bounded request
  concurrency, redacted event output and no image-serving endpoint.
- Source URL hashing for new live runs, capture/reliability health fields and stage
  latency samples. Existing decoder/inference deadlines and fail-stop recovery remain.
- Versioned annotation schema, operational benchmark, module decisions, research
  evidence addendum, runbook and prioritized work plan.

Actual source changes: `traffic.py`, `business_reporting.py`, `event_evaluation.py`
and `api.py` are new; config, event engine, pipeline, runtime, storage, CLI, exports
and evaluation are extended. `tzdata==2026.6` is now an explicit dependency for
Windows timezone availability; it was already installed locally. Four new test
modules cover these features. `scripts/benchmark_events.py` is the reproducible
sampling/semantics experiment. Working modules, user reference files, operational
data and the existing training notebook are preserved.

## Measurements and practical limits

The constructed six-second crossing benchmark uses fixture detections and the real
tracker/event/SQLite path. At 10 Hz it detects the expected two directional events
for one brief visit and four for simultaneous people; at 5/2.5 Hz the dwell evidence
is missed. Stationary/jitter controls produce no false crossing. These are synthetic
boundary cases, not measured café event F1 or a recommended universal camera FPS.
The results include configuration/source hashes and stage timing scope.

The pre-existing stress benchmark demonstrates identity loss after long occlusion
and movements beyond the gate; those failures remain. SQLite reconciliation and
replay conservation still work in software tests. No throughput improvement is
claimed for the new reporting/API layer. Full process-tree memory, GPU usage,
network buffering, p95 capture-to-event latency and sustained multi-camera uptime
remain unmeasured. The foundation report stores baseline/after synthetic timings;
single-run differences are not statistically established improvements.

The earlier generic-photo detector study recommends **YOLO11s first**, **YOLO26s
as challenger**, and **RT-DETRv2-R18 as an alternative**. This is an integration/
laptop-latency shortlist, not an accuracy ranking. Both YOLO candidates are near
the same repeated FP16 latency; RT-DETR needs its own runtime adapter. Alternate
trackers are not wired into the operational pipeline yet. Keep the existing tracker
as control; compare ByteTrack/BoT-SORT/OC-SORT on the same detections and event labels.

## Dataset and training decision

The [dataset catalog](research/resource_inventory.md) covers all supplied leads.
The [training guide](research/training_datasets.md) adds practical HF/Kaggle routes
and actual small Cup downloads. Kaggle Cup is a cup-only seed (verified sparse ID
31); HF/original COCO supports person/cup/bottle. HF mirror streaming stalled locally
and its viewer row API hits a scan-size limit. Pre-attached Kaggle COCO is the
alternative; no large archive was downloaded in this pass.

RetailAction and MERL are useful overhead retail-action references, not complete
café preparation/handover truth. BARISTA has closer coffee semantics but egocentric
view and noncommercial terms. Breakfast raw-video mirrors are incomplete; MOMA
access/rights remain conditional; supplied CARR Figshare is unavailable and its
author-linked alternative still needs dataset access/license verification. Hosted
cup model metrics are publisher claims, not local validation. Dataset/weight/code
terms require separate review; public access is not commercial permission.

The existing notebook trains the exact three shortlisted detectors and exports
hash-bound research candidates. Its one-epoch tests establish API compatibility,
not a fine-tuning benefit. Do not train a larger temporal model or full shop model
before target-camera labels demonstrate the error it is intended to fix. A later
VLM/hybrid must use a separate event/question benchmark, explicit abstention and
budgeted ambiguous-event calls. Do not send surveillance footage to a cloud model
without authorization.

## Correctness, monitoring and readiness

Person crossings do not identify globally unique customers or staff roles. Net
crossings are not an in-store occupancy estimate without a known initial count and
complete door coverage. Table states remain proximity evidence, not a validated
seated-person classifier. Generic item movement is not preparation, handover or sale.
Paid POS lines determine sold quantities; refunds/revisions affect those totals
independently. Traffic reviews change only their own read-model totals. Product
correction must be designed with allocations/episodes before implementation.

Monitor frame/capture freshness, unreliable/unknown coverage, camera movement,
processing lag, per-class reviewed event errors, database health/disk growth and POS
coverage. Count changes can reflect business demand instead of model drift. The
runbook separates available metrics from proposed monitors and documents backups,
retention limits and fail-stop replay. New live source identifiers omit credentials;
old databases may require an owner-led credential/access review.

**Readiness:** suitable for reproducible offline software experiments and local
authenticated review. Production is blocked by real footage/labels and calibrated
event evidence, patched-runtime validation, live reconnect/fault trials, long-run
capacity, source PTS accuracy, approved privacy/retention and deployment security.
The local standard-library HTTP server is not an internet production service.

## Decision classification and next action

| Classification | Decision |
|---|---|
| Adopt now | Existing ledger/POS invariants, deterministic tracker control, explicit unknowns, versioned annotations, event scoring, local read reports |
| Adapt/implement | Newly added crossing/report/review modules; target-camera calibration and label feedback workflow |
| Benchmark first | Tracker alternatives, small-object crops, adaptive sampling, converted runtimes and a temporal classifier if needed |
| Defer | Dashboard until reviewed data semantics, sustained multi-camera rollout, learned handover model, automatic retraining, global product episodes |
| Reject | Cup-presence sales/preparation counts, persistent customer recognition, unsupported product subtype inference, indiscriminate datasets and needless distributed infrastructure |

Next: collect the authorized diverse pilot and label doors/seating/products using
the new contract, then run the unchanged pretrained baseline. The highest remaining
gap is observability of the requested business events, followed by label quality,
small objects and track fragmentation. [The roadmap](implementation_roadmap.md)
tests these hypotheses and their counterevidence before increasing model complexity.
