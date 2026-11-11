# Model selection - 2026-11-07

**Shortlist for the real-video pilot: YOLO11s, YOLO26s and RT-DETRv2-R18.** This is
an engineering shortlist based on local latency, integration and licensing choices,
not a demonstrated cafe-accuracy ranking. Eight detectors were measured locally;
additional families were researched and a small VLM was probed. No "all models" or
exhaustive-benchmark claim is made.

The recommended system is detector + anonymous tracker + calibrated zones + temporal
event logic + independent POS reconciliation. A VLM can be added as an asynchronous
review component after proving benefit on ambiguous labeled clips. It should not own
the authoritative count or payment state.

## The three candidates

| Priority | Model / proposed pipeline | Why selected | Main gate |
|---|---|---|---|
| 1: first functional pilot | YOLO11s + existing tracker control, then compare class-wise ByteTrack | Locally fast in FP16; compatible model family with original Ultralytics pin; minimal detector integration change. | No overhead cup/event accuracy measured; fix runtime security debt and calibrate real footage. |
| 2: direct challenger | YOLO26s + the same tracker/event pipeline | Similar repeated laptop latency, end-to-end detector path and improved author-reported generic COCO AP. | Needs a newer Ultralytics runtime, export validation and independent shop fine-tuning/evaluation. No measured cafe-quality advantage over YOLO11s. |
| 3: permissive detector alternative | RT-DETRv2-R18 + class-wise ByteTrack + existing ledger | Measured FP16 speed is practical for a pilot; native Transformers implementation and Apache-2.0 model card offer a useful alternative to the YOLO licensing path. | New operational adapter/class mapping, numerical/export validation, real-video accuracy and deployment dependency review. |

These are proposed combinations: alternate trackers are not yet wired into Pipeline.
ByteTrack is an initial comparator, not a proven winner on cups. Run one tracker per
class or explicitly gate classes; do not let a class-agnostic association merge people
and products. Retain the current tracker as the deterministic reference.

YOLO11s and YOLO26s are effectively tied for this latency decision once the larger
repeat run is considered. The recommendation to start with YOLO11s is about lower
integration risk, not a claim of superior detection accuracy. YOLO26n remains a useful
CPU/smaller-model fallback; smaller was not automatically faster in the FP16 GPU run.

## Published evidence versus local evidence

[Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11) reports 47.0 COCO AP
for YOLO11s. [YOLO26 documentation](https://docs.ultralytics.com/models/yolo26) lists
48.6 for YOLO26s and 47.8 for its end-to-end mode; the inspected architecture defaults
to end-to-end. These are author results on generic COCO, not reproduced shop scores.
[RT-DETRv2](https://github.com/lyuwenyu/RT-DETR) reports 48.1 COCO AP for the R18/S
configuration. Published TensorRT/T4 speeds are not this laptop's PyTorch measurements.
The HF port's exact correspondence to the updated author training recipe/AP was not
independently established; no publisher AP is assigned as a locally reproduced score.

Use the [performance report](performance_report.md) and its raw JSON for all local
numbers. In particular, the eight-image COCO8 sample contains zero cup annotations
and is drawn from COCO training data. Its diagnostic accuracy cannot determine which
model detects overhead cups best. No training, held-out cafe evaluation or model
promotion was performed.

## VLM and hybrid decision

The locally probed [SmolVLM2-500M](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct)
is an inexpensive compatibility/latency reference. Prompt/protocol sensitivity must
be inspected in the saved outputs; a fluent caption is not a counted handover. Two
still images do not benchmark video understanding, action recognition or counting.

With canonical image binding, changing only the task-style prompt to a neutral
description changed incorrect denials of visible objects into recognizable food/
giraffe descriptions. That is a local prompt-sensitivity finding, not a general
model score. Test prompts on held-out positive and negative clips before adoption.

For a future hybrid trial, compare **the winning detector + tracker + rules**, versus
**the identical pipeline + event-triggered VLM review**. The current compact research
leads are [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) and
[MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6), whose publisher cards
list Apache-2.0 and image/video capabilities. Their required runtimes, cafe accuracy,
clip latency, quantized quality and coexistence with the detector in 6 GB VRAM remain
unmeasured. Neither is presented as a locally benchmarked winner. Keep the tested
SmolVLM2 as a low-cost baseline, Qwen3-VL-2B as an additional established comparison,
and allow unknown/abstain responses. Prioritize measured benefit over release date.

Example hybrid behavior: the tracker proposes a pickup, rules flag a blocked view,
and the VLM examines a bounded before/after clip and returns supporting evidence or
unknown. Human review resolves ambiguous outcomes. POS still determines paid units.
Review requests need capacity/time limits and cannot stall the detector.

## Why other candidates are not first choices

- D-FINE-N/S: actual Transformers-port benchmarks were completed. They remain strong
  alternatives, but did not establish an accuracy advantage or a compelling latency
  advantage over the selected options in this setup. Revisit with shop labels or
  optimized exports; this is not a claim that D-FINE is intrinsically slower.
- RF-DETR Nano/Small: credible permissive fine-tuning alternatives, but not reproduced
  locally in this bounded review. Larger backbone/resolution/runtime differences
  prevent transferring their advertised latency to this laptop.
- YOLOv8n/YOLO11n: measured controls and lightweight fallbacks; small-model speed alone
  cannot justify sacrificing product recall. YOLOv10/12 were screened, not reproduced.
- YOLOE/YOLO-World/Grounding DINO: useful product discovery/annotation candidates;
  open vocabulary does not solve persistent identity or action counting.
- VideoMAE/SlowFast: supervised temporal methods may become appropriate after real
  action labels exist. Their generic labels/checkpoints do not already recognize this
  shop's preparation/handover workflow.
- VLM-only continuous counting: no validated identity, event idempotence or event
  precision/recall evidence here justifies using generated totals as the ledger.

See the [technology matrix](../research/technology_comparison.md) for exact sources,
maintenance snapshots and license caveats. No external implementation was copied.

## Next work, in order

1. Highest correctness benefit: collect and independently label representative
   ceiling-camera sessions, especially occlusion, cup reuse and pickup/return. Data
   effort is substantial; implementation risk is low. Agree event meanings first.
2. Moderate implementation: save annotated replay for YOLO11s/YOLO26s/RT-DETRv2 on
   those exact sessions and measure per-class recall and event errors. A generic cup
   detector is a baseline, not a coffee/preparation classifier.
3. Moderate complexity: compare tracker fragmentation and add conservative logical
   item/preparation episodes. Retain transactional deduplication and uncertainty.
4. Performance benefit: select CUDA FP16/export settings after verifying detection
   and event parity. TensorRT/ONNX/OpenVINO gains are not established by this review.
5. Higher complexity/risk: run the VLM ablation on ambiguous clips only. Adopt it only
   if held-out event metrics improve enough to justify latency, memory and maintenance.

Commercial distribution also has a license gate: Ultralytics offers AGPL/Enterprise
paths; choosing an Apache detector does not automatically remove existing application
dependency obligations. The runtime advisory lookup is a separate predeployment gate.
