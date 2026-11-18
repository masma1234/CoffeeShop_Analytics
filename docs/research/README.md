# Model-selection review - 2026-11-07

The [current local-video prototype](../VIDEO_PROTOTYPE.md) now exercises cached pretrained RT-DETR inference through tracking and annotated MP4/export. Research claims and real caf? validation remain separate.

Scope: select three practical model/pipeline candidates for this laptop and overhead
cafe analytics. This is a bounded review of relevant families, not a benchmark of
every released model. No cafe footage or event ground truth is available (confirmed
by the user). Pretrained-model smoke measurements and published benchmarks cannot
establish cafe counting accuracy.

Execution priorities:

1. Audit current contracts, counting semantics and available hardware.
2. Verify the 13 supplied resources, then screen detectors, trackers, VLMs and runtimes.
3. Benchmark actual pretrained candidates in an isolated environment; retain provenance,
   failures, latency distributions and measurement boundaries.
4. Select three candidates conditionally on data, latency, integration and licensing.
5. Document a real-video comparison protocol and implement only justified benchmark tooling.

Read [current model validation](../benchmarks/model_validation_20261116.md) for
the owner's permissive-stack selection and latest measurements. The earlier
[performance report](../benchmarks/performance_report.md) covers different
models and experiments; its dates and limitations still apply.

Supporting work:

- [Current release gates](../../GITHUB_READINESS.md)
- [Verified resource inventory](resource_inventory.md)
- [Technology screening](technology_comparison.md)
- [Dataset strategy](dataset_strategy.md)
- [Downloadable training dataset shortlist](training_datasets.md)
- [Portable training and benchmark notebook](../../notebooks/cafe_model_benchmark.ipynb)
- [Current architecture](../architecture/current_architecture.md)
- [Recommended architecture](../architecture/recommended_architecture.md)
- [Counting design](../architecture/event_counting_design.md)
- [Counting evaluation status](../benchmarks/counting_evaluation.md)
- [Implementation changes](../audits/implementation_changes.md)

Evidence classification: **local measurement**, **publisher report**, **engineering
recommendation**, or **unverified**. Missing values remain unavailable. A candidate
is not promoted into the operational application merely because it completed a smoke test.
