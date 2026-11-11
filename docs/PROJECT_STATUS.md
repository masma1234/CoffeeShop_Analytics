# Coffee Shop AI Analytics: review and deliverable index

Latest implementation: [the local-video prototype](VIDEO_PROTOTYPE.md) adds actual
local RT-DETRv2 inference, PTS-based annotated MP4, pickup evidence, raw/accepted
exports and reviewed-label evaluation. [Its verification](benchmarks/video_prototype_results.json)
supersedes foundation test counts without changing the historical experiment snapshot.

The supported application remains `coffee_ops`. This review extends the existing
baseline rather than replacing working detector supervision, tracking, persistence
or POS accounting. Start with [final recommendations](final_recommendations.md),
then the [offline runbook](deployment_runbook.md) and [roadmap](implementation_roadmap.md).

## Requested deliverables and authoritative locations

Existing equivalent documents are reused to avoid duplicate/stale copies.

| Requested subject | Authoritative artifact |
|---|---|
| repository audit / gap analysis | [Module decisions and audit](audits/current_system_audit.md) |
| current architecture | [Implemented architecture](architecture/current_architecture.md) |
| research evidence | [Technology comparison and primary evidence](research/technology_comparison.md) |
| research gap analysis | [Thirteen evidence checks](implementation_roadmap.md) |
| dataset catalog | [Verified resource inventory](research/resource_inventory.md), [training dataset guide](research/training_datasets.md) and compact API evidence |
| annotation guidelines | [Ontology/QC](annotation_guidelines.md), [versioned JSON Schema](../schemas/event_annotations.v1.schema.json) |
| data pipeline | [Data/evaluation workflow](DATA_AND_EVALUATION.md), annotation timing/split contract |
| model selection | [Three-model decision report](benchmarks/model_comparison.md) |
| training strategy | [Portable notebook](../notebooks/cafe_model_benchmark.ipynb), [execution guide](../notebooks/README.md) |
| inference architecture | Implemented architecture plus [proposed architecture](architecture/recommended_architecture.md) |
| event definitions | Annotation ontology and [future product episode design](architecture/event_counting_design.md) |
| benchmark protocol | [Operational protocol](benchmark_protocol.md) |
| experiment results | [Foundation results](benchmarks/foundation_results.json), [model performance](benchmarks/performance_report.md), [training API evidence](benchmarks/notebook_verification.json) |
| monitoring plan | [Available signals and responses](deployment_runbook.md) |
| privacy and licenses | [Privacy policy](PRIVACY.md), dataset source terms and technology license gates |
| deployment runbook | Offline runbook, local read API, backup/rollback guidance |
| implementation roadmap | Prioritized roadmap and evidence dependencies |
| final recommendations | Technical decisions, changes, measured limits and next experiment |

## Implemented versus validation-dependent

Working software now covers replay, anonymous tracking, generic product movements,
table state, directional crossings, reviewed traffic corrections, local business-day
reports, POS-only paid totals, event scoring, an authenticated loopback read API and
training experiments. All model-generated cafÃ© business accuracy remains unmeasured.
The default example config has **no calibrated entrance lines and no supplied shop
weights**. The demo is a logic fixture. The new annotate-video path preserves source
PTS; legacy replay/live clock approximations remain. Camera reconnection, dashboard,
a validated preparation/handover recognizer and sustained production
capacity remain open. No remote deployment or model promotion was performed.
