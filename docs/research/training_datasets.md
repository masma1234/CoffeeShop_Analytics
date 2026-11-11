# Datasets for the training notebook

Reviewed **7 November 2026** against publisher pages, Hugging Face repository metadata
and Kaggle's public view/file-list APIs. [Compact evidence](training-datasets.json)
records versions, sizes, declared licenses and example filenames. Availability and
uploader license labels do not establish rights to every original photograph.

## Recommended starting data

| Dataset | Why use it | Download and notebook settings | Limits |
|---|---|---|---|
| [HF detection-datasets/coco](https://huggingface.co/datasets/detection-datasets/coco) | Best practical common baseline for **person, cup, bottle**, with bounding boxes. Pinned mirror: 117,266 train / 4,952 val images. | `SOURCE="hf_coco"`, `TARGET_CLASSES=["person","cup","bottle"]`, `RUN_DOWNLOADS=True`. Start with 1,000 train / 200 test images. | Mirror boxes are **pixel XYXY**, IDs contiguous 0–79. Mirror omits crowd flags and has no clear blanket license in its card. Streaming may transfer large Parquet row groups. Public COCO data cannot prove café generalization. |
| [Kaggle Cup dataset](https://www.kaggle.com/datasets/samuelayman/cup-dataset) | Small cup-specialization experiment: uploader describes 1,000 JPEG images with 1,000 YOLO TXT annotations. | About **163 MB**, version **1**. Add as Kaggle Input or download with `kagglehub.dataset_download("samuelayman/cup-dataset/versions/1")`. Set `SOURCE="kaggle_cup"`, `TARGET_CLASSES=["cup"]`, and `DATASET_ROOT` to the returned folder. | Uploader declares Apache 2.0; original image provenance still needs review. Inspect TXT class IDs and examples before training. Cup-only annotations do **not** certify complete person/bottle labels. No published overhead-video validation. |
| [Kaggle COCO 2017](https://www.kaggle.com/datasets/awsaf49/coco-2017-dataset) | Full original instance annotations, useful on Kaggle without streaming. | **27.60 GB**, version **2**. Prefer **Add Input**. Set `SOURCE="coco_json"` and `DATASET_ROOT` to the directory containing `coco2017`. Notebook streams the large JSON annotation file with ijson. | Boxes are **XYWH** and category IDs are noncontiguous; the importer maps names. Target crowd images are excluded. Uploader labels CC BY-SA 4.0; COCO image-specific licenses still apply. |

For HF, the notebook pins commit
`cf0b22332314a937e9dc8a1957b21725430bb41d`, streams only the requested sample count,
then freezes decoded image hashes and annotations. It uses the original train pool
for train/validation, and original val as the public test subset. The bounded,
first-N sampling policy is deterministic, not a representative café sample.

For Kaggle Cup, pagination and direct downloads verified four JPEG/TXT pairs
(`31_10`, `31_1000`, `31_1001`, `31_1002`): eight boxes, all source ID **31**.
Images are under `cup/`; annotations under `cup/labels/`. The notebook defaults to
`YOLO_CLASS_NAMES={31:"cup"}` and maps that sparse source ID to output class 0.
One downloaded photo was visually reviewed: it contains cups at a crowded dining
table, not an overhead café view. Full annotation completeness has **not** been
established from this small sample. Review the preview grid and audit
before an expensive run. If adding cup-only data to a multi-class training set,
finish annotating every target class first, or conduct a separate cup-only run.

Original [COCO terms](https://cocodataset.org/#termsofuse) distinguish annotation
and image rights. Review the source terms for the intended use before redistribution.

## Useful later, with conditions

| Dataset | Useful for | Why it is not the default detector training set |
|---|---|---|
| [HF RetailAction](https://huggingface.co/datasets/standard-cognition/RetailAction) | Ceiling-camera take/put/touch temporal research; roughly 21k paired clips / 41 hours. | Point/interval supervision is not cup bounding-box ground truth. Custom terms require an owner license above the stated $10k revenue threshold. Confirm current terms directly. |
| [HF BARISTA](https://huggingface.co/datasets/ramblr/BARISTA) | Coffee preparation actions and object interactions; 185 first-person videos / roughly 4.4 hours. | Egocentric view differs from ceiling CCTV. CC BY-NC 4.0. UUID object categories, masks and activities require a dedicated conversion protocol. |
| [Kaggle mall surveillance](https://www.kaggle.com/datasets/rahulsonboro/mall-surveillance-object-detection) | Surveillance people and generic products; 1,598 labeled images. | No cup/drink class; uploader lists an "Other" license. Verify rights and prevent adjacent-frame leakage before use. |
| [Kaggle SKU110K mirror](https://www.kaggle.com/datasets/thedatasith/sku110k-annotations) | Dense shelf-object detection stress research. | About 15.1 GB, generic single class, different viewpoint. Uploader lists CC BY-NC-SA 3.0 IGO; mirror terms differ elsewhere. No direct café-product semantics. |

The previously suggested `keremberke/coffee-cup-object-detection` returned HTTP 401
when checked; it is excluded from the ready-to-download shortlist. Coffee bean
classification, restaurant sales tables, FIFA World Cup data, and robotics motion
datasets without suitable detection labels were also excluded.

## What public datasets cannot replace

Collect representative overhead café recordings with consent and appropriate access
controls. Annotate all target boxes, persistent tracks and independent preparation /
handover events. Keep complete recording sessions together and reserve unseen
days/lighting conditions for the final test. Include small/stacked/transparent cups,
hands covering drinks, spills, trays, reflections, crowded counters, empty scenes,
motion blur and changed camera geometry. Track confidence intervals and per-scenario
recall; do not infer preparation, payment or sales from detector AP alone.

The notebook compares the three detector architectures only. A VLM or hybrid needs
its own labeled event/question benchmark, latency budget and abstention criteria.

### Observed HF download limitation

The HF mirror's `/rows` endpoint returned `Scan size limit exceeded`: the first
row group requires about 485 MB, beyond the viewer's 300 MB scan limit. `/first-rows`
worked, but is not a full dataset download path. Pinned `datasets` streaming was
attempted locally; the first row-group transfer stalled and was interrupted.
The notebook supports that standard streaming API, but its end-to-end download
has **not** been validated on this network. The four-image Kaggle Cup download and
import succeeded. Prefer Kaggle Cup or pre-attached Kaggle COCO for the first run.
