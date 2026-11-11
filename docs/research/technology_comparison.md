# Technology comparison - 2026-11-07

These are candidate-specific engineering judgments, not measured cafe scores. Local
timings belong in the [performance report](../benchmarks/performance_report.md).
Published COCO AP measures generic detection; VQA scores, tracking scores and event
F1 measure different tasks and must not share a numerical ranking.

## Model screening

| Candidate / primary source | Role and ceiling-camera fit | Hardware / integration / limitations | Decision |
|---|---|---|---|
| [YOLOv8n](https://docs.ultralytics.com/models/yolov8/) | Generic person/cup/product proposal baseline | Small; compatible with original stack. No preparation labels. Ultralytics license applies. | Locally benchmark as historical control. |
| [YOLO11n/s](https://docs.ultralytics.com/models/yolo11/) | Practical closed-set detector; shop fine-tuning needed | Small/nano options, original integration compatible. Generic COCO has cup, not coffee contents. | Locally benchmark; retain as low-upgrade-risk fallback. |
| [YOLO26n/s](https://docs.ultralytics.com/models/yolo26) | Updated detector with end-to-end option; small objects still need adequate pixels | Requires newer Ultralytics than operational pin; isolation prevents breaking the app. License gate before deployment. | Locally benchmark; lead detector candidate conditional on shop validation. |
| [YOLOv10](https://github.com/THU-MIG/yolov10) | End-to-end detector alternative | Another training/export path without a demonstrated local advantage | Defer full reproduction; no claim that it is worse on cafe footage. |
| [YOLO12](https://docs.ultralytics.com/models/yolo12) | Attention-based detector | Additional compatibility/training considerations; no local overhead evidence | Screen/defer; compare if first-stage candidates fail. |
| [RT-DETRv2-R18](https://huggingface.co/PekingU/rtdetr_v2_r18vd) | NMS-free transformer detector, direct generic-box alternative | About 20M parameters; Transformers adapter/catalog normalization required. Apache-2.0 model card. | Locally benchmark; main permissive detector comparator. |
| [D-FINE-N/S](https://github.com/Peterande/D-FINE) | Compact DETR localization alternative | Official COCO-N reports 42.8 AP; S 48.5 AP. Author T4/TensorRT timings are not laptop measurements. Apache code; Objects365-based checkpoints have separate data terms. | Locally benchmark the [nano](https://huggingface.co/ustc-community/dfine-nano-coco) and [small](https://huggingface.co/ustc-community/dfine-small-coco) Transformers ports, with exact revisions recorded; not an original-engine reproduction. |
| [RF-DETR Nano/Small](https://github.com/roboflow/rf-detr) | Fine-tuning-oriented transformer detector | Extra stack/backbone and different resolutions; Apache core N/S/M/L. Other sizes have different terms. | Strong reserve, especially if commercial distribution favors permissive dependencies; not locally reproduced. |
| [YOLO-World](https://docs.ultralytics.com/models/yolo-world) / [YOLOE](https://docs.ultralytics.com/models/yoloe) | Text/visual-prompted product discovery | Open vocabulary is useful for annotation/proposals but not proof of subtype correctness or stable identity | Evaluate offline labeling benefit before considering the live path. |
| [Grounding DINO](https://github.com/IDEA-Research/GroundingDINO) | Open-set localization for new merchandise | More integration/dependency burden; no native persistent counting | Optional annotation assistant; not first live baseline. |
| [Florence-2-base](https://huggingface.co/microsoft/Florence-2-base) | Caption/grounding assistant | Original card uses custom remote code; inspect/pin before execution. Still-image language output is not temporal identity. | Defer; not executed. |
| [Qwen3-VL-2B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct) | Candidate clip reviewer for ambiguous human-object interactions | Apache-2.0; bounded frame/token budgets essential. Two billion FP16 parameters alone imply roughly 4 GB, before vision/cache/runtime overhead; 6 GB coexistence is unverified. | Hybrid research candidate; not locally measured or production-approved. |
| [Qwen2.5-VL-3B](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct) | Alternative grounding/video reasoning | Larger than the chosen 2B starting point; exact checkpoint terms and memory need inspection | Defer local download; no quality inferiority claim. |
| [SmolVLM2-500M](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct) | Lightweight image/video language baseline | Apache-2.0; lower download/memory cost. Two still-image probes do not test temporal reasoning. | Local qualitative/latency probe only; not an authoritative counter. |
| [SmolVLM2-2.2B](https://huggingface.co/HuggingFaceTB/SmolVLM2-2.2B-Instruct) | Larger lightweight video-review option | Apache-2.0; larger memory budget, independent cafe testing needed | Reserve for comparison with Qwen if clip review shows value. |
| [InternVL3.5-1B](https://huggingface.co/OpenGVLab/InternVL3_5-1B) | Smaller alternative reviewer | Apache model card; provided usage includes custom code. Requires inspected/pinned implementation and representative prompts. | Reserve; not executed. |
| [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) / [2B](https://huggingface.co/Qwen/Qwen3.5-2B) | Newer compact image/video review candidates | Apache model cards. Different model type/runtime support from the pinned Transformers 4.57 benchmark stack; actual memory and clip performance unverified. | Prioritize 0.8B for a future low-memory hybrid ablation; neither downloaded nor locally measured. |
| [MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6) | Newer lightweight image/video reviewer | Apache model card; publisher describes an edge-oriented model. Exact native/quantized runtime support and cafe accuracy not reproduced. | Compare with the small Qwen candidate after clip labels exist; not locally measured. |
| [FastVLM](https://machinelearning.apple.com/research/fast-vision-language-models) | Efficient vision encoding / on-device image-query research | Apple provides multiple deployment paths, including Apple-specific formats; exact checkpoint license and Windows/CUDA path need separate verification. | Reserve; browser/Apple demonstrations are not this laptop's measured video latency. |
| [VideoMAE](https://github.com/MCG-NJU/VideoMAE) / [SlowFast](https://github.com/facebookresearch/SlowFast) | Learned temporal action classification/localization components | Need cafe action segments and negatives; generic action labels do not imply handover recognition. Original VideoMAE LICENSE is CC BY-NC 4.0. | Defer training until labeled error analysis justifies it. |
| Hosted VLM services | Optional remote clip review | API access, ongoing cost, privacy and rate limits; no configured service or benchmark here | Defer; never substitute assumed cloud performance for local measurements. |
| VLM-only continuous counting | Language-generated counts over frames/clips | No implemented stable item identity, transactional deduplication or calibrated event evidence | Reject as the initial authoritative counting design; no universal claim about all VLMs. |

YOLO27 was presented as unreleased in the inspected vendor documentation. It is not
a reproducible deployed candidate in this review. Screening is deliberately bounded;
larger model variants and untested quantizations are not hidden behind an "all models"
claim.

## Trackers and temporal logic

| Component | Relevant behavior / tradeoff | Decision |
|---|---|---|
| Existing Kalman/Hungarian | Tested caps/replay behavior; loses IDs under long occlusion/large motion | Retain reference; measure real identity fragmentation. |
| [ByteTrack](https://github.com/FoundationVision/ByteTrack) | Associates lower-confidence detections as well; MIT; original repo's last push is old | First alternate benchmark. Person-benchmark success does not prove cup tracking. Use maintained, pinned integration with checked license. |
| [BoT-SORT](https://github.com/NirAharon/BoT-SORT) | Motion compensation and optional appearance association; MIT; more runtime/ReID weights | Compare for people only if ByteTrack remains insufficient; no cross-visit identities. |
| [OC-SORT](https://github.com/noahcao/OC_SORT) | Motion-based occlusion/nonlinear-motion handling; MIT | Useful tracker comparator without appearance model; not reproduced. |
| [DeepSORT](https://github.com/nwojke/deep_sort) | Appearance matching with additional feature model; GPL-3.0 original | Defer integration/rights/compute burden; overhead apparel features may be weak. |
| [Norfair](https://github.com/tryolabs/norfair) | Lightweight distance-based flexibility; BSD-3-Clause | Valid alternative, but replacing a similar working tracker needs measured benefit. |
| [MMTracking](https://github.com/open-mmlab/mmtracking) | Unified research comparisons, Apache-2.0; old last push in snapshot | Defer migration: compiled OpenMMLab dependencies/Python 3.13 compatibility unverified. |
| [MMAction2](https://github.com/open-mmlab/mmaction2) | Action-model training/evaluation framework; Apache code | Offline option after action annotation; not another detector. |

No tracker was compared on real cafe video. Repository timestamps and licenses are
recorded in [repository_snapshot.json](repository_snapshot.json); metadata activity
does not establish maintainability or production support. Unit/synthetic results
are kept separate from real identity metrics.

## Runtime and tooling choices

| Technology | Use / primary source | Decision |
|---|---|---|
| OpenCV | Current decoding, geometry and transforms | Retain measured baseline; no native accelerated-decoder claim. |
| GStreamer / FFmpeg | [RTSP source](https://gstreamer.freedesktop.org/documentation/rtsp/rtspsrc.html), [protocol options](https://ffmpeg.org/ffmpeg-protocols.html#rtsp) | Consider reconnect/decode needs; both document fetches timed out in this review, so exact current options remain unverified. |
| ONNX Runtime | [Execution providers](https://onnxruntime.ai/docs/execution-providers/) | First portable export comparison after detector selection; verify numerical/event parity. Not measured here. |
| TensorRT | [NVIDIA docs](https://docs.nvidia.com/deeplearning/tensorrt/latest/) | Relevant to RTX 3050 after FP32 baseline; FP16/INT8 accuracy must be tested. Not measured here. |
| OpenVINO | [Intel runtime](https://docs.openvino.ai/2026/about-openvino.html) | CPU/iGPU deployment alternative, not NVIDIA acceleration. Not measured here. |
| DeepStream | [NVIDIA implementation](https://github.com/NVIDIA/DeepStream) | Future Linux/multi-stream path; do not add its GStreamer/platform burden to this Windows MVP without need. |
| Supervision | [Source](https://github.com/roboflow/supervision) | Potential overlays/tracker adapter; no need to replace ledger/event semantics. |
| FiftyOne | [Source](https://github.com/voxel51/fiftyone) | Optional dataset/error inspection environment; no need as a runtime dependency. |

## License and security gates

[Ultralytics](https://www.ultralytics.com/license) presents AGPL-3.0 and Enterprise
paths. Research inference is not commercial license clearance. RT-DETR/D-FINE/RF-DETR
core licenses do not automatically relicense an application still using Ultralytics.
Check code, exact weight and dataset terms separately before choosing distribution.
No licensed external source code was copied into the application.

Benchmark downloads use official publisher asset/model locations, opt-in fetching,
size-limited archive extraction and pinned/hash-recorded checkpoints. Hugging Face
model loading disables remote code and uses safetensors. This is supply-chain risk
reduction, not a full security audit. A limited [direct-requirement OSV lookup](../audits/dependency_advisories.json)
flagged Torch 2.9.0 advisories; pinned does not mean patched. The benchmark uses only
publisher/hash-checked checkpoints. Do not accept untrusted model files. Review
affected execution paths and validate a patched Torch/TorchVision pair before
production; transitive dependencies and exploitability were not fully audited.

## Foundation review: primary evidence and transfer limits

Rechecked primary paper pages on 7 November 2026. Method descriptions below are
publisher/research evidence; relevance to this café is an engineering hypothesis.

| Claim | Original source / experimental setting | Evidence boundary | Project consequence / confidence |
|---|---|---|---|
| Recovering low-score detections can improve identity continuity | [ByteTrack paper](https://arxiv.org/abs/2110.06864), pedestrian MOT benchmarks with specified detections; published speed uses a V100 | Not a ceiling-cup or event-counting result; detector+association context differs | High confidence in the described method, unmeasured transfer. Preserve low-score candidates for a fair comparison: our current class filter removes them before tracking. |
| Appearance/motion/camera-motion components can improve pedestrian association | [BoT-SORT paper](https://arxiv.org/abs/2206.14651), MOT17/MOT20 | Additional components and ReID cost; benchmark ranking is not a controlled café comparison | Benchmark against the existing control, including latency, anonymous identity fragmentation and final event errors. |
| Linear prediction can accumulate error during occlusion | [OC-SORT paper](https://arxiv.org/abs/2203.14360), several MOT/nonlinear-motion benchmarks | Its association-only throughput excludes our neural detector and storage | Plausible mechanism for measured control failures; no claim it solves our long café occlusions without testing. |
| Tracking quality includes detection, association and localization | [HOTA paper](https://arxiv.org/abs/2009.07736), MOTChallenge evaluation analysis | Requires identity ground truth and a validated evaluator | HOTA remains unavailable here. Do not infer it from IDF1 or detection AP. |
| IANA local-day boundaries differ from a fixed 24-hour UTC window | [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html), implementation/timezone data | Timezone data availability and ambiguous local boundaries require explicit handling | Implemented tzdata dependency and tested 23/25-hour reporting; not proof of source-clock accuracy. |
| A basic standard-library HTTP server is not a production host | [Python http.server](https://docs.python.org/3.13/library/http.server.html) | Basic server mechanisms, not production identity/TLS/hosting assurance | New API is limited to authenticated loopback review; remote deployment remains a separate decision. |

The tracker papers are not contradictory recommendations: they evaluate different
components, detections and conditions. A reported generic benchmark advantage does
not rank their downstream café counting. Compare common cached detections, then
repeat the measurement with the intended detector thresholds and complete event
pipeline. Small-object recall, partial visibility and episode semantics can dominate
even when a tracker's pedestrian ID score improves.

The strongest temporal-model hypothesis also has counterevidence: better detection,
sampling and continuity can resolve apparent action-rule failures. Our synthetic
sampling experiment already loses dwell evidence at coarser rates. Establish the
remaining real rule errors after fixing those inputs before adding a learned model.
