# Disk and file inventory: 2026-11-12

Checkpoint: 2026-11-12T22:40:17.406919+00:00 to 2026-11-12T22:40:30.999554+00:00.

Before: 14,676,673,897 logical bytes / 82,955 files. After: 17,262,158,076 bytes / 104,456 files.
Net delta: +2,585,484,179 bytes. Proven cache removal is separately 370,659,765 bytes. Added environments/image/tools/evidence explain growth.

Logical file lengths, not filesystem allocation. Hardlinks can count more than once. Parent/child directory totals overlap; do not sum them. Git metadata is counted separately, not classified as tracked source.
Raw baseline ignored tally: 14,669,716,784; corrected for ignored var/ nested-clone contents: 14,673,132,421. The corrected classification inherits directory prefixes reported by Git; raw baseline evidence remains unchanged.
The initial pass overlapped candidate installation and reported 10,249 changed/missing reads. Final hash reuse is limited to identical relative path, length and nanosecond mtime; original SHA-256 witnesses are retained. This is a filesystem checkpoint, not an atomic snapshot or adversarial filesystem guarantee. Newly written reports/inventory output can postdate enumeration.

Final hash accounting: {'fresh': 13, 'reused_unchanged_size_mtime': 102357}. Errors: 0; links/reparse points skipped: 21.

## All top-level directories

| Path | Before bytes | After bytes | After files | Share |
|---|---:|---:|---:|---:|
| `.git` | 1,248,833 | 1,248,994 | 224 | 0.007% |
| `.github` | 3,377 | 4,000 | 1 | 0.000% |
| `.mypy_cache` | 0 | 88,899,813 | 18 | 0.515% |
| `.pytest_cache` | 0 | 20,868 | 4 | 0.000% |
| `.ruff_cache` | 0 | 3,874 | 5 | 0.000% |
| `.venv` | 1,054,306,577 | 850,312,722 | 21,679 | 4.926% |
| `.venv-bench` | 4,905,232,988 | 4,784,950,465 | 15,597 | 27.719% |
| `.venv-candidate` | 568,210,684 | 1,121,969,106 | 27,616 | 6.500% |
| `.venv-notebook` | 291,146,254 | 245,114,339 | 10,079 | 1.420% |
| `<root files>` | 786,132 | 745,708 | 22 | 0.004% |
| `coffee_ops` | 543,760 | 446,912 | 52 | 0.003% |
| `config` | 3,803 | 3,803 | 1 | 0.000% |
| `docs` | 1,017,654 | 4,861,357 | 91 | 0.028% |
| `models` | 219 | 219 | 1 | 0.000% |
| `notebooks` | 69,170 | 69,361 | 2 | 0.000% |
| `schemas` | 4,459 | 4,459 | 1 | 0.000% |
| `scripts` | 95,239 | 95,642 | 18 | 0.001% |
| `tests` | 363,490 | 142,841 | 17 | 0.001% |
| `var` | 7,853,641,258 | 10,163,263,593 | 29,028 | 58.876% |

## Largest 100 files

| Path | Logical bytes | Tracked | Ignored |
|---|---:|---|---|
| `var/release-audit-20261111/grype-cache/grype-db-download3031804826/vulnerability.db` | 3,414,958,080 | False | True |
| `var/model-benchmark/huggingface/hub/models--HuggingFaceTB--SmolVLM2-500M-Video-Instruct/blobs/b9bfd456c9472c0acd5719d6e514c4b859891af205ee1a736552fd3497b8b0c3` | 2,029,990,624 | False | True |
| `var/engineering-audit-20261112/trivy-cache/db/trivy.db` | 1,764,192,256 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/torch_cuda.dll` | 902,044,160 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cublasLt64_12.dll` | 674,667,520 | False | True |
| `var/engineering-audit-20261112/runtime-image.tar` | 550,058,496 | False | True |
| `var/release-audit-20261111/runtime-image.tar` | 536,346,624 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cudnn_engines_precompiled64_9.dll` | 513,926,688 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cusparse64_12.dll` | 379,535,872 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib/torch_cpu.dll` | 305,081,856 | False | True |
| `.venv-candidate/Lib/site-packages/torch/lib/torch_cpu.dll` | 305,081,856 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cudnn_adv64_9.dll` | 282,445,872 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cufft64_11.dll` | 276,121,600 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/torch_cpu.dll` | 257,887,232 | False | True |
| `.venv/Lib/site-packages/torch/lib/torch_cpu.dll` | 257,736,704 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cusolver64_11.dll` | 225,683,456 | False | True |
| `var/engineering-audit-20261112/tools/trivy.exe` | 179,937,280 | False | True |
| `.venv-bench/Lib/site-packages/_polars_runtime_32/_polars_runtime.pyd` | 167,937,024 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cusolverMg64_11.dll` | 157,071,360 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cudnn_ops64_9.dll` | 126,508,576 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cublas64_12.dll` | 113,716,224 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/nvrtc64_120_0.alt.dll` | 86,794,240 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/nvrtc64_120_0.dll` | 86,728,192 | False | True |
| `var/model-benchmark/huggingface/hub/models--PekingU--rtdetr_v2_r18vd/blobs/d18309d0d7ea57048138885c4c6ecfcb1e24506fc6153b94ad484f8ab62c7115` | 80,904,640 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/nvJitLink_120_0.dll` | 77,860,352 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/cv2/cv2.pyd` | 74,938,880 | False | True |
| `.venv-candidate/Lib/site-packages/cv2/cv2.pyd` | 74,938,880 | False | True |
| `.venv/Lib/site-packages/cv2/cv2.pyd` | 74,938,880 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/curand64_10.dll` | 71,955,968 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cudnn_heuristic64_9.dll` | 56,823,328 | False | True |
| `var/engineering-audit-20261112/inventory-final.json` | 55,275,888 | False | True |
| `var/engineering-audit-20261112/inventory-complete.json` | 55,248,036 | False | True |
| `var/engineering-audit-20261112/tools/trivy_0.76.2_windows-64bit.zip` | 53,905,616 | False | True |
| `var/model-benchmark/huggingface/hub/models--ustc-community--dfine-small-coco/blobs/a144baff3a27bfd538fe37b11fa8d4fca5744b8c054b5301e7c699a1379cd18f` | 41,497,620 | False | True |
| `var/engineering-audit-20261112/inventory-before.json` | 34,474,769 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/torch_cpu.lib` | 29,437,568 | False | True |
| `.venv/Lib/site-packages/torch/lib/torch_cpu.lib` | 29,437,568 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib/torch_cpu.lib` | 29,242,954 | False | True |
| `.venv-candidate/Lib/site-packages/torch/lib/torch_cpu.lib` | 29,242,954 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/cv2/opencv_videoio_ffmpeg4110_64.dll` | 27,954,688 | False | True |
| `.venv-candidate/Lib/site-packages/cv2/opencv_videoio_ffmpeg4110_64.dll` | 27,954,688 | False | True |
| `.venv/Lib/site-packages/cv2/opencv_videoio_ffmpeg4110_64.dll` | 27,954,688 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Scripts/ruff.exe` | 26,974,000 | False | True |
| `.venv-candidate/Scripts/ruff.exe` | 26,974,000 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/nvperf_host.dll` | 21,641,792 | False | True |
| `var/model-benchmark/weights/yolo26s.pt` | 20,422,725 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/numpy.libs/libscipy_openblas64_-43e11ff0749b8cbe0a615c9cf6737e0e.dll` | 20,301,824 | False | True |
| `.venv-candidate/Lib/site-packages/numpy.libs/libscipy_openblas64_-43e11ff0749b8cbe0a615c9cf6737e0e.dll` | 20,301,824 | False | True |
| `.venv/Lib/site-packages/numpy.libs/libscipy_openblas64_-43e11ff0749b8cbe0a615c9cf6737e0e.dll` | 20,301,824 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/6ec57f84c680d3a3778b__mypyc.cp313-win_amd64.pyd` | 20,294,656 | False | True |
| `.venv-candidate/Lib/site-packages/6ec57f84c680d3a3778b__mypyc.cp313-win_amd64.pyd` | 20,294,656 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/cudnn_engines_runtime_compiled64_9.dll` | 20,201,008 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy.libs/libscipy_openblas-f07f5a5d207a3a47104dca54d6d0c86a.dll` | 20,155,392 | False | True |
| `.venv-candidate/Lib/site-packages/scipy.libs/libscipy_openblas-f07f5a5d207a3a47104dca54d6d0c86a.dll` | 20,155,392 | False | True |
| `.venv/Lib/site-packages/scipy.libs/libscipy_openblas-f07f5a5d207a3a47104dca54d6d0c86a.dll` | 20,155,392 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/avcodec-63-2756d4fffb772585dcdece87427716a4.dll` | 19,569,664 | False | True |
| `.venv-notebook/Lib/site-packages/av.libs/avcodec-63-2756d4fffb772585dcdece87427716a4.dll` | 19,569,664 | False | True |
| `.venv-candidate/Lib/site-packages/av.libs/avcodec-63-2756d4fffb772585dcdece87427716a4.dll` | 19,569,664 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib/torch_python.dll` | 19,529,216 | False | True |
| `.venv-candidate/Lib/site-packages/torch/lib/torch_python.dll` | 19,529,216 | False | True |
| `var/model-benchmark/weights/yolo11s.pt` | 19,313,732 | False | True |
| `.venv-notebook/Lib/site-packages/pyarrow/arrow.dll` | 19,270,144 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/torch_python.dll` | 18,822,656 | False | True |
| `.venv/Lib/site-packages/torch/lib/torch_python.dll` | 18,472,960 | False | True |
| `var/model-benchmark/huggingface/hub/models--ustc-community--dfine-nano-coco/blobs/19e06bdc873da819920a8d373b879721a5b9759d822f8213220bb09abbdab58b` | 15,278,996 | False | True |
| `.venv-notebook/Lib/site-packages/pyarrow/arrow_flight.dll` | 15,126,528 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/libx265-ee9d492f3fb55d0a3b564bb1bf4f6822.dll` | 12,830,720 | False | True |
| `.venv-notebook/Lib/site-packages/av.libs/libx265-ee9d492f3fb55d0a3b564bb1bf4f6822.dll` | 12,830,720 | False | True |
| `.venv-candidate/Lib/site-packages/av.libs/libx265-ee9d492f3fb55d0a3b564bb1bf4f6822.dll` | 12,830,720 | False | True |
| `var/engineering-audit-20261112/cache-cleanup-proposed.json` | 10,840,863 | False | True |
| `var/engineering-audit-20261112/pypi-coverage.json` | 10,623,645 | False | True |
| `var/engineering-audit-20261112/cache-cleanup-resumed.jsonl` | 10,146,312 | False | True |
| `.venv-notebook/Lib/site-packages/pyarrow/arrow_compute.dll` | 10,125,312 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/sleef.lib` | 8,812,252 | False | True |
| `.venv/Lib/site-packages/torch/lib/sleef.lib` | 8,812,252 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib/sleef.lib` | 8,811,892 | False | True |
| `.venv-candidate/Lib/site-packages/torch/lib/sleef.lib` | 8,811,892 | False | True |
| `var/engineering-audit-20261112/pypi-ruff.json` | 8,133,838 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/PIL/_avif.cp313-win_amd64.pyd` | 7,890,944 | False | True |
| `.venv-candidate/Lib/site-packages/PIL/_avif.cp313-win_amd64.pyd` | 7,890,944 | False | True |
| `.venv/Lib/site-packages/PIL/_avif.cp313-win_amd64.pyd` | 7,890,944 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/libSvtAv1Enc-7a2b2046575991edd70ef501ca085458.dll` | 7,724,032 | False | True |
| `.venv-notebook/Lib/site-packages/av.libs/libSvtAv1Enc-7a2b2046575991edd70ef501ca085458.dll` | 7,724,032 | False | True |
| `.venv-candidate/Lib/site-packages/av.libs/libSvtAv1Enc-7a2b2046575991edd70ef501ca085458.dll` | 7,724,032 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/tokenizers/tokenizers.pyd` | 7,395,328 | False | True |
| `.venv-candidate/Lib/site-packages/tokenizers/tokenizers.pyd` | 7,395,328 | False | True |
| `.venv-bench/Lib/site-packages/tokenizers/tokenizers.pyd` | 7,395,328 | False | True |
| `.venv-bench/Lib/site-packages/torchvision/_C.pyd` | 7,340,032 | False | True |
| `var/engineering-audit-20261112/linux-run2/quality/.mypy_cache/3.13/cache.12.db` | 7,286,784 | False | True |
| `.venv-notebook/Lib/site-packages/pyarrow/parquet.dll` | 7,191,552 | False | True |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torchvision/python313.dll` | 7,145,800 | False | True |
| `.venv-candidate/Lib/site-packages/torchvision/python313.dll` | 7,145,800 | False | True |
| `.venv-bench/Lib/site-packages/torchvision/python313.dll` | 7,114,568 | False | True |
| `.venv/Lib/site-packages/torchvision/python313.dll` | 7,114,568 | False | True |
| `var/engineering-audit-20261112/linux-run2/quality/.mypy_cache/3.13/cache.14.db` | 7,098,368 | False | True |
| `.mypy_cache/3.13/cache.4.db` | 6,950,912 | False | True |
| `.mypy_cache/3.13/cache.5.db` | 6,815,744 | False | True |
| `.mypy_cache/3.13/cache.11.db` | 6,606,848 | False | True |
| `var/model-benchmark/weights/yolov8n.pt` | 6,549,796 | False | True |
| `.venv-bench/Lib/site-packages/torch/lib/nvrtc-builtins64_128.dll` | 6,356,480 | False | True |

## Largest 100 directories

Parent and child totals overlap. Do not sum this table.

| Directory | Logical bytes | Files | Share |
|---|---:|---:|---:|
| `var` | 10,163,263,593 | 29,028 | 58.876% |
| `.venv-bench` | 4,784,950,465 | 15,597 | 27.719% |
| `.venv-bench/Lib/site-packages` | 4,782,888,416 | 15,573 | 27.707% |
| `.venv-bench/Lib` | 4,782,888,416 | 15,573 | 27.707% |
| `.venv-bench/Lib/site-packages/torch` | 4,502,711,987 | 11,428 | 26.084% |
| `.venv-bench/Lib/site-packages/torch/lib` | 4,421,606,964 | 58 | 25.614% |
| `var/engineering-audit-20261112` | 3,972,271,320 | 28,298 | 23.011% |
| `var/release-audit-20261111` | 3,959,754,627 | 657 | 22.939% |
| `var/release-audit-20261111/grype-cache/grype-db-download3031804826` | 3,414,958,080 | 1 | 19.783% |
| `var/release-audit-20261111/grype-cache` | 3,414,958,080 | 1 | 19.783% |
| `var/model-benchmark` | 2,230,455,366 | 54 | 12.921% |
| `var/model-benchmark/huggingface/hub` | 2,172,546,678 | 29 | 12.586% |
| `var/model-benchmark/huggingface` | 2,172,546,678 | 29 | 12.586% |
| `var/model-benchmark/huggingface/hub/models--HuggingFaceTB--SmolVLM2-500M-Video-Instruct` | 2,034,845,205 | 17 | 11.788% |
| `var/model-benchmark/huggingface/hub/models--HuggingFaceTB--SmolVLM2-500M-Video-Instruct/blobs` | 2,034,845,165 | 12 | 11.788% |
| `var/engineering-audit-20261112/trivy-cache` | 1,765,240,983 | 3 | 10.226% |
| `var/engineering-audit-20261112/trivy-cache/db` | 1,764,192,407 | 2 | 10.220% |
| `var/engineering-audit-20261112/clean-checkout` | 1,129,812,981 | 28,052 | 6.545% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate` | 1,122,480,350 | 27,644 | 6.503% |
| `.venv-candidate` | 1,121,969,106 | 27,616 | 6.500% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages` | 1,090,398,005 | 27,591 | 6.317% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib` | 1,090,398,005 | 27,591 | 6.317% |
| `.venv-candidate/Lib/site-packages` | 1,089,888,955 | 27,563 | 6.314% |
| `.venv-candidate/Lib` | 1,089,888,955 | 27,563 | 6.314% |
| `.venv` | 850,312,722 | 21,679 | 4.926% |
| `.venv/Lib/site-packages` | 847,808,017 | 21,650 | 4.911% |
| `.venv/Lib` | 847,808,017 | 21,650 | 4.911% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch` | 462,435,123 | 11,793 | 2.679% |
| `.venv-candidate/Lib/site-packages/torch` | 462,435,123 | 11,793 | 2.679% |
| `.venv/Lib/site-packages/torch` | 407,152,767 | 11,393 | 2.359% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib` | 368,650,828 | 23 | 2.136% |
| `.venv-candidate/Lib/site-packages/torch/lib` | 368,650,828 | 23 | 2.136% |
| `.venv/Lib/site-packages/torch/lib` | 326,051,680 | 27 | 1.889% |
| `.venv-notebook` | 245,114,339 | 10,079 | 1.420% |
| `.venv-notebook/Lib/site-packages` | 242,492,588 | 10,039 | 1.405% |
| `.venv-notebook/Lib` | 242,492,588 | 10,039 | 1.405% |
| `var/engineering-audit-20261112/tools` | 233,854,253 | 3 | 1.355% |
| `.venv-bench/Lib/site-packages/_polars_runtime_32` | 167,937,324 | 3 | 0.973% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/cv2` | 113,314,035 | 80 | 0.656% |
| `.venv-candidate/Lib/site-packages/cv2` | 113,314,035 | 80 | 0.656% |
| `.venv/Lib/site-packages/cv2` | 113,314,035 | 80 | 0.656% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy` | 100,240,027 | 1,530 | 0.581% |
| `.venv-candidate/Lib/site-packages/scipy` | 100,240,027 | 1,530 | 0.581% |
| `.venv/Lib/site-packages/scipy` | 100,240,027 | 1,530 | 0.581% |
| `.mypy_cache` | 88,899,813 | 18 | 0.515% |
| `.mypy_cache/3.13` | 88,899,584 | 16 | 0.515% |
| `.venv-notebook/Lib/site-packages/pyarrow` | 88,581,473 | 752 | 0.513% |
| `var/engineering-audit-20261112/linux-run2/quality` | 88,380,487 | 45 | 0.512% |
| `var/engineering-audit-20261112/linux-run2` | 88,380,487 | 45 | 0.512% |
| `var/engineering-audit-20261112/linux-run2/quality/.mypy_cache` | 88,076,512 | 18 | 0.510% |
| `var/engineering-audit-20261112/linux-run2/quality/.mypy_cache/3.13` | 88,076,288 | 16 | 0.510% |
| `var/model-benchmark/huggingface/hub/models--PekingU--rtdetr_v2_r18vd/blobs` | 80,910,521 | 3 | 0.469% |
| `var/model-benchmark/huggingface/hub/models--PekingU--rtdetr_v2_r18vd` | 80,910,521 | 4 | 0.469% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs` | 67,240,448 | 23 | 0.390% |
| `.venv-notebook/Lib/site-packages/av.libs` | 67,240,448 | 23 | 0.390% |
| `.venv-candidate/Lib/site-packages/av.libs` | 67,240,448 | 23 | 0.390% |
| `var/model-benchmark/weights` | 57,444,470 | 5 | 0.333% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/transformers` | 52,124,225 | 2,240 | 0.302% |
| `.venv-candidate/Lib/site-packages/transformers` | 52,124,225 | 2,240 | 0.302% |
| `.venv-bench/Lib/site-packages/transformers` | 52,124,225 | 2,240 | 0.302% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/transformers/models` | 45,061,388 | 1,958 | 0.261% |
| `.venv-candidate/Lib/site-packages/transformers/models` | 45,061,388 | 1,958 | 0.261% |
| `.venv-bench/Lib/site-packages/transformers/models` | 45,061,388 | 1,958 | 0.261% |
| `var/model-benchmark/huggingface/hub/models--ustc-community--dfine-small-coco/blobs` | 41,504,955 | 3 | 0.240% |
| `var/model-benchmark/huggingface/hub/models--ustc-community--dfine-small-coco` | 41,504,955 | 4 | 0.240% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/include` | 39,245,962 | 9,375 | 0.227% |
| `.venv-candidate/Lib/site-packages/torch/include` | 39,245,962 | 9,375 | 0.227% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/pandas` | 38,256,617 | 1,580 | 0.222% |
| `.venv-candidate/Lib/site-packages/pandas` | 38,256,617 | 1,580 | 0.222% |
| `.venv/Lib/site-packages/pandas` | 38,249,832 | 1,580 | 0.222% |
| `.venv-bench/Lib/site-packages/torch/include` | 36,274,979 | 9,260 | 0.210% |
| `.venv/Lib/site-packages/torch/include` | 36,273,647 | 9,256 | 0.210% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Scripts` | 32,069,579 | 50 | 0.186% |
| `.venv-candidate/Scripts` | 32,067,451 | 50 | 0.186% |
| `.venv-notebook/Lib/site-packages/debugpy` | 27,941,223 | 295 | 0.162% |
| `.venv-notebook/Lib/site-packages/debugpy/_vendored` | 27,622,360 | 263 | 0.160% |
| `.venv-notebook/Lib/site-packages/debugpy/_vendored/pydevd` | 27,611,911 | 259 | 0.160% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/sympy` | 26,601,980 | 1,561 | 0.154% |
| `.venv-candidate/Lib/site-packages/sympy` | 26,601,980 | 1,561 | 0.154% |
| `.venv/Lib/site-packages/sympy` | 26,601,980 | 1,561 | 0.154% |
| `.venv-bench/Lib/site-packages/torchvision` | 25,484,991 | 198 | 0.148% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/include/ATen` | 24,516,026 | 7,768 | 0.142% |
| `.venv-candidate/Lib/site-packages/torch/include/ATen` | 24,516,026 | 7,768 | 0.142% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/matplotlib` | 22,430,072 | 556 | 0.130% |
| `.venv-candidate/Lib/site-packages/matplotlib` | 22,430,072 | 556 | 0.130% |
| `.venv/Lib/site-packages/matplotlib` | 22,430,072 | 556 | 0.130% |
| `.venv-bench/Lib/site-packages/torch/include/ATen` | 22,335,342 | 7,704 | 0.129% |
| `.venv/Lib/site-packages/torch/include/ATen` | 22,334,397 | 7,703 | 0.129% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/numpy` | 21,434,685 | 887 | 0.124% |
| `.venv-candidate/Lib/site-packages/numpy` | 21,434,685 | 887 | 0.124% |
| `.venv/Lib/site-packages/numpy` | 21,434,685 | 887 | 0.124% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/numpy.libs` | 20,876,880 | 2 | 0.121% |
| `.venv-candidate/Lib/site-packages/numpy.libs` | 20,876,880 | 2 | 0.121% |
| `.venv/Lib/site-packages/numpy.libs` | 20,876,880 | 2 | 0.121% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy.libs` | 20,155,392 | 1 | 0.117% |
| `.venv-candidate/Lib/site-packages/scipy.libs` | 20,155,392 | 1 | 0.117% |
| `.venv/Lib/site-packages/scipy.libs` | 20,155,392 | 1 | 0.117% |
| `.venv-notebook/Lib/site-packages/debugpy/_vendored/pydevd/pydevd_attach_to_process` | 17,904,927 | 79 | 0.104% |
| `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy/special` | 15,666,284 | 186 | 0.091% |
| `.venv-candidate/Lib/site-packages/scipy/special` | 15,666,284 | 186 | 0.091% |

## Extension and category counts

| Extension | Files |
|---|---:|
| `.py` | 45,016 |
| `.h` | 37,744 |
| `.pyi` | 8,757 |
| `<none>` | 4,427 |
| `.pyd` | 1,337 |
| `.txt` | 650 |
| `.json` | 453 |
| `.yaml` | 423 |
| `.a` | 345 |
| `.mat` | 330 |
| `.hpp` | 313 |
| `.pxd` | 270 |
| `.lib` | 259 |
| `.typed` | 257 |
| `.cuh` | 242 |
| `.c` | 226 |
| `.exe` | 208 |
| `.dll` | 197 |
| `.md` | 185 |
| `.afm` | 183 |
| `.f90` | 180 |
| `.cpp` | 171 |
| `.sav` | 141 |
| `.log` | 132 |
| `.ttf` | 120 |
| `.png` | 114 |
| `.cmake` | 113 |
| `.csv` | 102 |
| `.mplstyle` | 93 |
| `.dat` | 84 |
| `.npz` | 75 |
| `.f` | 72 |
| `.pyx` | 71 |
| `.wav` | 66 |
| `.svg` | 59 |
| `.xml` | 55 |
| `.jinja` | 53 |
| `.al` | 48 |
| `.arff` | 48 |
| `.rst` | 46 |
| `.sample` | 42 |
| `.pdf` | 41 |
| `.npy` | 36 |
| `.db` | 35 |
| `.gz` | 26 |
| `.html` | 25 |
| `.cu` | 25 |
| `.tpl` | 24 |
| `.cc` | 24 |
| `.css` | 22 |
| `.sh` | 21 |
| `.pyf` | 21 |
| `.jpg` | 20 |
| `.js` | 20 |
| `.xsd` | 20 |
| `.pxi` | 19 |
| `.build` | 18 |
| `.pyc` | 18 |
| `.ini` | 13 |
| `.bz2` | 13 |
| `.cfg` | 12 |
| `.tab` | 12 |
| `.bat` | 11 |
| `.apache` | 11 |
| `.bsd` | 11 |
| `.1` | 10 |
| `.pth` | 10 |
| `.tmpl` | 10 |
| `.xsl` | 9 |
| `.nc` | 9 |
| `.mjs` | 8 |
| `.pem` | 8 |
| `.tag` | 7 |
| `.ps1` | 7 |
| `.sqlite3` | 6 |
| `.pt` | 6 |
| `.whl` | 6 |
| `.g4` | 6 |
| `.lark` | 6 |
| `.license` | 6 |
| `.a99` | 6 |
| `.b99` | 6 |
| `.pdb` | 6 |
| `.fish` | 5 |
| `.docx` | 4 |
| `.jsonl` | 4 |
| `.zip` | 4 |
| `.ipynb` | 4 |
| `.yml` | 4 |
| `.in` | 4 |
| `.ld` | 4 |
| `.thrift` | 4 |
| `.xslt` | 4 |
| `.about` | 4 |
| `.parquet` | 4 |
| `.orc` | 4 |
| `.mp4` | 3 |
| `.bin` | 3 |
| `.zi` | 3 |
| `.ani` | 3 |
| `.toml` | 3 |
| `.pkl` | 3 |
| `.fits` | 3 |
| `.pc` | 3 |
| `.template` | 3 |
| `.inc` | 3 |
| `.f95` | 3 |
| `.lua` | 3 |
| `.xrc` | 3 |
| `.external` | 3 |
| `.tar` | 2 |
| `.sqlite3-shm` | 2 |
| `.sqlite3-wal` | 2 |
| `.markdown-it` | 2 |
| `.scss` | 2 |
| `.graph` | 2 |
| `.bazel` | 2 |
| `.bzl` | 2 |
| `.bundle` | 1 |
| `.crt` | 1 |
| `.key` | 1 |
| `.mo` | 1 |
| `.po` | 1 |
| `.feather` | 1 |
| `.cmd` | 1 |
| `.egg` | 1 |

| Category | Files |
|---|---:|
| local_environment | 102,483 |
| local_data_or_evidence | 897 |
| git_metadata | 658 |
| media_or_dataset | 137 |
| source_or_configuration | 133 |
| documentation_or_requirements | 62 |
| database_or_security_cache | 41 |
| python_cache | 18 |
| model_artifact | 16 |
| archive | 11 |

## Exact duplicates

37,948 SHA-256 groups, 1,816,160,223 redundant logical bytes. Equal content does not authorize removal. Required environment libraries, verification copies, models and historical evidence remain.

| SHA-256 | Bytes each | Copies | Duplicate bytes | Example paths |
|---|---:|---:|---:|---|
| `ac7cfa1b31556e7ae60381ad4bd9df4286a4f82738c3120045c6a7803aab5fe5` | 305,081,856 | 2 | 305,081,856 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib/torch_cpu.dll`<br>`.venv-candidate/Lib/site-packages/torch/lib/torch_cpu.dll` |
| `d2e14633f0699469c37e43210ca9e167887ce4a162e01f1490be49fd8e45388f` | 74,938,880 | 3 | 149,877,760 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/cv2/cv2.pyd`<br>`.venv-candidate/Lib/site-packages/cv2/cv2.pyd`<br>`.venv/Lib/site-packages/cv2/cv2.pyd` |
| `f0460320ac08c074bdf6d5a19f5c13d204e585e85030fdd40e20a3c0b3adeb67` | 27,954,688 | 3 | 55,909,376 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/cv2/opencv_videoio_ffmpeg4110_64.dll`<br>`.venv-candidate/Lib/site-packages/cv2/opencv_videoio_ffmpeg4110_64.dll`<br>`.venv/Lib/site-packages/cv2/opencv_videoio_ffmpeg4110_64.dll` |
| `634687ca5fedef76e784d8c54fc4ba2f965a44c0b60d754c49174589deab8157` | 20,301,824 | 3 | 40,603,648 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/numpy.libs/libscipy_openblas64_-43e11ff0749b8cbe0a615c9cf6737e0e.dll`<br>`.venv-candidate/Lib/site-packages/numpy.libs/libscipy_openblas64_-43e11ff0749b8cbe0a615c9cf6737e0e.dll`<br>`.venv/Lib/site-packages/numpy.libs/libscipy_openblas64_-43e11ff0749b8cbe0a615c9cf6737e0e.dll` |
| `6b2103f2ae4d8547998b5d188e9801fba6cb12404ae8e4bfff319e8cc1949000` | 20,155,392 | 3 | 40,310,784 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy.libs/libscipy_openblas-f07f5a5d207a3a47104dca54d6d0c86a.dll`<br>`.venv-candidate/Lib/site-packages/scipy.libs/libscipy_openblas-f07f5a5d207a3a47104dca54d6d0c86a.dll`<br>`.venv/Lib/site-packages/scipy.libs/libscipy_openblas-f07f5a5d207a3a47104dca54d6d0c86a.dll` |
| `8e13fdedbeefb6a8b5d22b567122ec3c00384add569de9e589e53a86bd08422c` | 19,569,664 | 3 | 39,139,328 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/avcodec-63-2756d4fffb772585dcdece87427716a4.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/avcodec-63-2756d4fffb772585dcdece87427716a4.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/avcodec-63-2756d4fffb772585dcdece87427716a4.dll` |
| `3adbd544c7eacfd8f2b66d6cff870ef1d638952246665d206b01e5402ef13db6` | 29,437,568 | 2 | 29,437,568 | `.venv-bench/Lib/site-packages/torch/lib/torch_cpu.lib`<br>`.venv/Lib/site-packages/torch/lib/torch_cpu.lib` |
| `03d73d1b5694a097112c57294d1547eecc048fe9b774d7d9225fe07d04dfd0b8` | 29,242,954 | 2 | 29,242,954 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib/torch_cpu.lib`<br>`.venv-candidate/Lib/site-packages/torch/lib/torch_cpu.lib` |
| `0e71094b51a4241cb725e76e6375c55c8433dd06ec380ab987c970edd1618565` | 26,974,000 | 2 | 26,974,000 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Scripts/ruff.exe`<br>`.venv-candidate/Scripts/ruff.exe` |
| `efe075f1ee008c722eb71adfe00d926071836d777cc9ef23b59c9ecb9db7d57f` | 12,830,720 | 3 | 25,661,440 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/libx265-ee9d492f3fb55d0a3b564bb1bf4f6822.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/libx265-ee9d492f3fb55d0a3b564bb1bf4f6822.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/libx265-ee9d492f3fb55d0a3b564bb1bf4f6822.dll` |
| `9656e2f0ebf0f909ed8b14f698ed110d98f8d554378592cc1e8fe19a3174264e` | 20,294,656 | 2 | 20,294,656 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/6ec57f84c680d3a3778b__mypyc.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/6ec57f84c680d3a3778b__mypyc.cp313-win_amd64.pyd` |
| `e72775751fbb56efcf186ccde3b5255626ff2597cbf034bc4f2aea663a0b2977` | 19,529,216 | 2 | 19,529,216 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib/torch_python.dll`<br>`.venv-candidate/Lib/site-packages/torch/lib/torch_python.dll` |
| `6c6e5d33db5ecd8a28252103c97ac7867d376371875b6baa609947d8e778022a` | 7,890,944 | 3 | 15,781,888 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/PIL/_avif.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/PIL/_avif.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/PIL/_avif.cp313-win_amd64.pyd` |
| `7a2b2046575991edd70ef501ca085458ebdff3bf96282350057ae1dee0afaf9f` | 7,724,032 | 3 | 15,448,064 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/libSvtAv1Enc-7a2b2046575991edd70ef501ca085458.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/libSvtAv1Enc-7a2b2046575991edd70ef501ca085458.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/libSvtAv1Enc-7a2b2046575991edd70ef501ca085458.dll` |
| `7acb83f5b89136597e0d14b788d82917bf2870df94575bf77e12731c4e49c4df` | 7,395,328 | 3 | 14,790,656 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/tokenizers/tokenizers.pyd`<br>`.venv-candidate/Lib/site-packages/tokenizers/tokenizers.pyd`<br>`.venv-bench/Lib/site-packages/tokenizers/tokenizers.pyd` |
| `a9b9e84178dd73162f47a3a531c321fad955ca3a7ff04a9517db7e7c78bf9ab2` | 5,956,608 | 3 | 11,913,216 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/avfilter-12-87c7677b784d3ea4ecceb3e6cae9c9f1.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/avfilter-12-87c7677b784d3ea4ecceb3e6cae9c9f1.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/avfilter-12-87c7677b784d3ea4ecceb3e6cae9c9f1.dll` |
| `e3df9b5eb64f95f3b95dcbc94951376d182623383553bc9996b299ea4c5d10e8` | 5,775,360 | 3 | 11,550,720 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy/optimize/_highspy/_core.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/scipy/optimize/_highspy/_core.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/scipy/optimize/_highspy/_core.cp313-win_amd64.pyd` |
| `b4788f9c1678cccc12844d196f4e998f26a53018c6e9068279f67458826d7ba3` | 8,811,892 | 2 | 8,811,892 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torch/lib/sleef.lib`<br>`.venv-candidate/Lib/site-packages/torch/lib/sleef.lib` |
| `d40cbb04b6fc4a78a2e681ca751e39681287760d386cb979dfdeefe89e113abc` | 4,275,712 | 3 | 8,551,424 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy/sparse/_sparsetools.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/scipy/sparse/_sparsetools.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/scipy/sparse/_sparsetools.cp313-win_amd64.pyd` |
| `184a7e73e77d7e30cf6da81eb888a159561154a7875bf4af7216a8c0a38fc0a0` | 4,176,896 | 3 | 8,353,792 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/numpy/_core/_multiarray_umath.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/numpy/_core/_multiarray_umath.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/numpy/_core/_multiarray_umath.cp313-win_amd64.pyd` |
| `e1c7a0f81abcb01050fb6c2f31435be16b83d736adf9cbb34bad2325590dc20c` | 7,145,800 | 2 | 7,145,800 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/torchvision/python313.dll`<br>`.venv-candidate/Lib/site-packages/torchvision/python313.dll` |
| `ad90b8270582f8a4538ede163cbf7b03024a9907d477787cbcb61e88d63006a1` | 7,114,568 | 2 | 7,114,568 | `.venv-bench/Lib/site-packages/torchvision/python313.dll`<br>`.venv/Lib/site-packages/torchvision/python313.dll` |
| `102c5f7376a6dd5d7de31800b3b8e8e6ba39ddd20b21803754dac404306818b5` | 3,111,936 | 3 | 6,223,872 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy/special/cython_special.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/scipy/special/cython_special.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/scipy/special/cython_special.cp313-win_amd64.pyd` |
| `49759edae5286f10e4b11a442f51fb70bacde1f92b7b876038231c4d8140c506` | 2,888,704 | 3 | 5,777,408 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/avformat-63-e8c4f8fc30664f2b7e85dcc683bd4b0d.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/avformat-63-e8c4f8fc30664f2b7e85dcc683bd4b0d.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/avformat-63-e8c4f8fc30664f2b7e85dcc683bd4b0d.dll` |
| `57843408fe594a59256afc1f79fb32b5bb53b450c74d57221befa8df6c3f10a8` | 2,761,216 | 3 | 5,522,432 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy/io/_fast_matrix_market/_fmm_core.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/scipy/io/_fast_matrix_market/_fmm_core.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/scipy/io/_fast_matrix_market/_fmm_core.cp313-win_amd64.pyd` |
| `0e5ee47ecc13269d54dd7a55f8b53752167c52587720877732388fb078a0480a` | 2,689,040 | 3 | 5,378,080 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/cv2/data/haarcascade_frontalface_alt_tree.xml`<br>`.venv-candidate/Lib/site-packages/cv2/data/haarcascade_frontalface_alt_tree.xml`<br>`.venv/Lib/site-packages/cv2/data/haarcascade_frontalface_alt_tree.xml` |
| `832167d2ecd950dc2382a9866e346d5886262bc8790bbf24613f56ad19d52f82` | 2,662,400 | 3 | 5,324,800 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/PIL/_imaging.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/PIL/_imaging.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/PIL/_imaging.cp313-win_amd64.pyd` |
| `1cba2ca3b6f410fa4b03b01b479f7663493ea9903857cd753dc8dbc772f67447` | 2,660,352 | 3 | 5,320,704 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/libstdc++-6-7ad22040206bf70776b13a24ec3f87b2.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/libstdc++-6-7ad22040206bf70776b13a24ec3f87b2.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/libstdc++-6-7ad22040206bf70776b13a24ec3f87b2.dll` |
| `738629b026940c256dfe988a62062bdc96ae5065d13163bf7e579dc95a4634f4` | 2,583,552 | 3 | 5,167,104 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/libvpx-1-dd81d2b55a771749d485047772201cc1.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/libvpx-1-dd81d2b55a771749d485047772201cc1.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/libvpx-1-dd81d2b55a771749d485047772201cc1.dll` |
| `e62fe32b41b5eb2494c5768f52a83a2940846b4126af2dd186b453dd88fa861c` | 2,377,728 | 3 | 4,755,456 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy/special/_ufuncs_cxx.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/scipy/special/_ufuncs_cxx.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/scipy/special/_ufuncs_cxx.cp313-win_amd64.pyd` |
| `baf6cfd01136b13ee1cfaf5dbd0aaade784df0cd6e0798d27c9d4341d65ac137` | 2,323,968 | 3 | 4,647,936 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/matplotlib/ft2font.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/matplotlib/ft2font.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/matplotlib/ft2font.cp313-win_amd64.pyd` |
| `0f71f37cf3f3ee0e2ecac2b06829e9ff3cf2b3e237f25bb14aef6b8de14cd777` | 2,267,648 | 3 | 4,535,296 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/libx264-165-0f71f37cf3f3ee0e2ecac2b06829e9ff.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/libx264-165-0f71f37cf3f3ee0e2ecac2b06829e9ff.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/libx264-165-0f71f37cf3f3ee0e2ecac2b06829e9ff.dll` |
| `91f0a8e145163803637620517bad32ad5cb551d8a4dc02c3309811af24dbcbcc` | 2,250,752 | 3 | 4,501,504 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/PIL/_imagingft.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/PIL/_imagingft.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/PIL/_imagingft.cp313-win_amd64.pyd` |
| `b2b1849db5032f55dba4c7f7154ee45f0c89159613a9871e3b9a61b54bc49ce2` | 2,236,928 | 3 | 4,473,856 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/numpy/_core/_simd.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/numpy/_core/_simd.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/numpy/_core/_simd.cp313-win_amd64.pyd` |
| `5469d6ef7baf7426269a9483c24587b77bf6cb6a005f2bd98443a396f528e82b` | 2,203,136 | 3 | 4,406,272 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/libdav1d-5469d6ef7baf7426269a9483c24587b7.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/libdav1d-5469d6ef7baf7426269a9483c24587b7.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/libdav1d-5469d6ef7baf7426269a9483c24587b7.dll` |
| `b3a6c323a442f5af9d538403c8d5da042c1606b5accbbf8a852a75c72ccd46af` | 2,190,336 | 3 | 4,380,672 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy/special/_special_ufuncs.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/scipy/special/_special_ufuncs.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/scipy/special/_special_ufuncs.cp313-win_amd64.pyd` |
| `f2956978470b3ed26c4f5db80b45d4c3a9188a4a8622133f73ded71504df85d6` | 2,124,800 | 3 | 4,249,600 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/av.libs/swscale-10-9af0a10ad7003982e48548ff39e98465.dll`<br>`.venv-notebook/Lib/site-packages/av.libs/swscale-10-9af0a10ad7003982e48548ff39e98465.dll`<br>`.venv-candidate/Lib/site-packages/av.libs/swscale-10-9af0a10ad7003982e48548ff39e98465.dll` |
| `d25d5468bdc063c22087f0190d942e7c8c4fac8b69067cb3fc5e813cc61f8cac` | 2,064,041 | 3 | 4,128,082 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/fontTools/misc/bezierTools.c`<br>`.venv-candidate/Lib/site-packages/fontTools/misc/bezierTools.c`<br>`.venv/Lib/site-packages/fontTools/misc/bezierTools.c` |
| `3762c0fe15163e1d3fbf6dcc6518f4b75b37efd7a1663a5d4921ae57189a8c7c` | 2,055,680 | 3 | 4,111,360 | `var/engineering-audit-20261112/clean-checkout/.venv-candidate/Lib/site-packages/scipy/linalg/_flapack.cp313-win_amd64.pyd`<br>`.venv-candidate/Lib/site-packages/scipy/linalg/_flapack.cp313-win_amd64.pyd`<br>`.venv/Lib/site-packages/scipy/linalg/_flapack.cp313-win_amd64.pyd` |
| `843acfbbc20b002ef0226cc8f07f729b8b7d0fa1c43adeab97666be48217680b` | 1,230,510 | 4 | 3,691,530 | `.venv-bench/Lib/site-packages/torch/_VF.pyi`<br>`.venv-bench/Lib/site-packages/torch/_C/_VariableFunctions.pyi`<br>`.venv/Lib/site-packages/torch/_VF.pyi` |

Full paths for every group are in the local inventory JSON; no exact duplicate model/media/environment component was deleted. Only independently source-backed Python caches qualified.

Ignored bytes: 17,254,777,968; tracked bytes: 2,217,924. .git metadata is counted but not tracked source. Top-level var includes scanner DBs, protected caches, models, image evidence, source snapshots and a verification clone/environment.

Retained large decisions: old Grype DB 3,414,958,080 bytes; SmolVLM/model caches; working and historical environments; current Trivy DB; prior/new image archives. No Docker daemon/VHD space outside this project was inventoried or pruned.

Raw inventory files and their hashes remain local. The complete read-only procedure is `scripts/audit_repository.py --previous <prior.json> --output <new.json>`. Per-invocation Git long-path support changes no Git configuration file. Exact duplicate hashes may be reused only when reported size/mtime are unchanged.

## Inventory errors

```json
[]
```
