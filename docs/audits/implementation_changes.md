# Implementation changes - model benchmark review

The operational pipeline, event/POS semantics and database were retained. There is
no cafe dataset demonstrating that a replacement is more correct. This review adds
the smallest standalone integrations needed to measure pretrained candidates without
relabeling their outputs as shop-specific classes or changing application pins.

## Code and configuration

- scripts/benchmark_models.py: actual pretrained YOLOv8/11/26, RT-DETRv2 and D-FINE
  adapters plus a small SmolVLM2 qualitative probe. Records package/model revisions,
  weight hashes, input hashes, per-call latency samples, cold load/warm-up, perturbation
  results, sampled process RSS and CUDA allocation/reservation peaks when used.
- scripts/benchmark_suite.py: independent sequential subprocesses with deadlines,
  isolated logs and failure records. Known model-name choices prevent output-path
  injection; duplicate model requests and invalid timeouts are rejected.
- requirements-benchmark.txt and ignored .venv-bench: optional pinned tooling; the
  existing verified .venv and requirements.txt remain the application baseline.
  The local benchmark environment imports unchanged scientific dependencies from
  .venv via a .pth file, and overrides research packages/native GPU wheels locally.
- tests/test_model_benchmark.py: nine offline tests for download opt-in, overwrite
  avoidance, archive traversal/symlinks, size-limit cleanup, framework box clipping
  rejection of CPU FP16 before artifact creation, and complete COCO synonym validation.
- README and linked research/architecture/audit/evaluation reports describe measured
  boundaries, reproducibility, proposed counting semantics and deployment gaps.

## Failures found while integrating

1. Windows' default text encoding failed on the current vendor COCO YAML. The
   benchmark now reads UTF-8 explicitly.
2. RT-DETR emits some coordinates outside the image; shared detection validation
   correctly rejected negative boxes. The benchmark adapter now clips coordinates
   to image bounds, drops empty boxes and rejects nonfinite values before scoring.
   This normalization is a required integration detail, not an accuracy improvement.
3. SmolVLM's processor required num2words; the isolated optional requirements now
   include it. No missing dependency was installed into the operational environment.
4. Large single-transfer downloads stalled. Bounded HTTP range retrieval succeeded
   with publisher SHA-256 verification. This was download preparation, not model
   inference latency; the reproduction commands use normal publisher tools.
5. The Transformers COCO catalogs use six conventional older synonyms (for example,
   pottedplant and sofa). Exact-name filtering initially omitted these categories.
   The adapter now validates a complete one-to-one mapping through explicit COCO
   aliases and rejects unknown/ambiguous catalogs. Affected CPU/GPU measurements were
   rerun; obsolete diagnostic scores are excluded from the final comparison.

Failed initial attempts are recorded separately from successful measurements. There
is no timing imputation for a failed model, and load/download time is not counted as
steady-state inference. Transformers ports are identified as such; publisher
TensorRT benchmark numbers were not reproduced by running Python inference.

## Validation and retention

110 automated tests and 13 acceptance commands passed in the unchanged application
environment; native CPU NMS passed and repeat replay retained identical daily totals.
See [current test evidence](../validation-current/tests.txt). Real pretrained-model
results are separate from those logic tests and linked in the performance report.

Public images/checkpoints and working logs stay under ignored var/model-benchmark;
curated metrics/provenance stay under docs/benchmarks. Installer wheels and abandoned
partial downloads are disposable after successful installation and hash verification.
Required virtualenvs, pretrained benchmark weights, user references and application
source remain. Empty-directory removal previously blocked by policy is not required
to keep the supported source clean. No user video or operational database was removed.

Remaining work is explicit: real-video labels, preparation/handover episodes,
configurable tracker integration, RTSP reconnects, local business-day reports,
full-process monitoring, security-patched native runtime validation and an independently
measured commercial deployment. A functioning benchmark is not that deployment.
