# Verified resource inventory - 2026-11-07

Verification means the card/page/API was inspected. It does not mean archives were
fully downloaded, labels audited or weights reproduced. The tiny COCO8 fixture and
four Kaggle Cup image/label pairs were downloaded in prior stages; no large action
archive was downloaded. Unknown commercial terms remain unresolved.

Unless a row explicitly says otherwise, source resolution/FPS, camera geometry,
tracking-ID completeness, inter-annotator reliability, subject consent, commercial
permission and redistribution rights are **not independently verified**. Counts and
annotation descriptions are publisher statements; metadata access is not full data
access. The first experiment should use the small training shortlist plus authorized
target-camera data, not every listed archive.

The foundation pass re-read RetailAction, both MERL pages, BARISTA, Breakfast, MOMA,
the kitchen preview and the two Roboflow pages, plus author GitHub READMEs for MOMA,
CARR and Cafe Vision. The supplied Figshare page still returned 410. No action
archive or third-party source implementation was imported. The Roboflow pages show
hosted image metrics; those were not reproduced locally. Some web results are cached,
so download/terms checks must be repeated when acquiring a specific version.

| Supplied resource | Access, content and size | View / annotations / restrictions | Decision |
|---|---|---|---|
| [RetailAction](https://huggingface.co/datasets/standard-cognition/RetailAction) | Card and file listing accessible; publisher reports 21,000 samples, about 41 hours, paired videos | Actual ceiling-mounted convenience-store views; take/put/touch intervals and spatial points, not cafe preparation labels. Custom [license](https://huggingface.co/datasets/standard-cognition/RetailAction/raw/main/LICENSE) requires attribution and an additional license above its USD 10,000 revenue trigger. | Best supplied perspective match for interaction research; terms and cafe transfer must be evaluated. No full download. |
| [MERL mirror](https://huggingface.co/datasets/Voxel51/MERL_Shopping_Dataset) | Accessible card; viewer error; card/sample counts are inconsistent | Overhead staged shelf activity, temporal annotations. Mirror cannot establish rights independently. | Use original metadata as authority; research only pending permission. |
| [MERL original](https://www.merl.com/research/downloads/MERL_Shopping_Dataset) | 106 approximately two-minute videos; original download directory linked | Overhead lab grocery scenario; five shelf/inspection actions, not handover or preparation. Research/noncommercial restriction must be checked before use. | Useful temporal baseline data; not a cafe acceptance set. |
| [CARR supplied URL](https://figshare.com/articles/dataset/Images_and_Label_7z/29470079) | Page returned 410; article API returned 404 | Original URL's videos, labels, perspective, size and license not verified | Supplied URL unavailable; see author-linked alternative below. Never treat as downloaded. |
| [Breakfast Actions](https://serre.lab.brown.edu/breakfast-actions-dataset.html) | Official page accessible; about 77 hours, 52 people/18 kitchens; current raw-video mirror noted incomplete | Household multi-view preparation, 320x240/15 FPS; temporal actions. Not ceiling cafe service. License/download completeness requires follow-up. | Optional action-method research, not direct counting validation. |
| [MOMA](https://moma.stanford.edu/) / [author repository](https://github.com/StanfordVL/moma) | Website JS shell; repository documents videos and graph annotations | General multi-actor/object activities; current MOMA-LRG differs from original MOMA statistics. Raw-video crawler availability and dataset rights not reproduced. | Interaction representation reference; defer large download and unsupported CCTV claims. |
| [BARISTA](https://huggingface.co/datasets/ramblr/BARISTA) | 185 videos / about 4.4 hours; publisher lists about 19.9 GB | Egocentric controlled coffee preparation; boxes/masks/attributes/relations/activity segments. CC BY-NC 4.0. | Useful research semantics; perspective mismatch and noncommercial restriction exclude direct commercial training by default. |
| [Wasila coffee cups](https://universe.roboflow.com/wasila/coffee-cup-detection) | 1,342 labeled images, two classes; hosted model demo | Images, not tracking videos. Coffee-cups/paper-cup; CC BY 4.0. Hosted metrics are publisher results; downloadable weights and provenance not verified. | Candidate seed images after label/leakage audit; no production accuracy claim. |
| [YAI cafe cup detector](https://universe.roboflow.com/yai-teh0x/cup-detector-in-cafe) | 325 labeled images; model page accessible | Classes empty/exist, CC BY 4.0; no verified continuous videos or freely downloadable checkpoint | Narrow cup-state experiment; not a general merchandise detector. |
| [Cafe Vision](https://github.com/Chinmay-Sakhare07/CafeVison-MGEN_Hackathon_2025) | README and zone-counting source inspected; demo video/weights listed | YOLOv8 + Norfair demo; cooldown counting flaw, no project license detected, no independently measured cafe benchmark | Learn from UI concepts; do not import code or counting claims. See audit. |
| [Commercial kitchen preview](https://huggingface.co/datasets/nova-dynamics/Chinese_Commercial_Kitchen_Manipulation_Dataset_Preview) | Public sample-pack card with image/video assets; full material by request | Chef workflow, mixed egocentric/side/overhead RGB-D; cutting/stir-fry rather than coffee. CC BY-NC 4.0. Label suitability not audited. | Defer; not cafe handover ground truth. |
| [Ahmed coffee sales](https://www.kaggle.com/datasets/ahmedabbas757/coffee-sales) | Page had no readable text; official metadata API succeeded, about 9 MB | Fictitious Maven Roasters transaction data; no synchronized video. License not verified in retrieved fields. | POS schema/report examples only; not CV supervision. |
| [ihelon coffee sales](https://www.kaggle.com/datasets/ihelon/coffee-sales) | Official metadata API succeeded, about 294 KB at retrieval | Vending-machine transactions, no paired video; retrieved license unresolved | Time-series examples only; cannot evaluate video-POS association. |

API failures and successful metadata checks are retained in
[resource-api-checks.json](resource-api-checks.json). Repository licensing/activity
metadata is in [repository_snapshot.json](repository_snapshot.json). A hosted demo is
not proof that local weights can be downloaded or used under the dataset license.

CARR follow-up found a legitimate [author repository](https://github.com/januaradip/CARR)
linking [Harvard Dataverse DOI 10.7910/DVN/CY24UB](https://doi.org/10.7910/DVN/CY24UB).
It documents 833 trimmed retail-surveillance sequences / 327,919 annotated frames,
six shelf-activity labels and person boxes, plus grouped evaluation protocols. The
distributed layout is image archives; availability of original continuous videos is
not established. Code is described as MIT. The Harvard API returned 403 here, so
download and dataset-license verification remain blocked; the code license is not
data clearance. This alternative is promising for retail interaction research, not
verified prepared-drink or handover labels. No archive was downloaded.

## Additional sources and coverage limits

- [COCO8](https://docs.ultralytics.com/datasets/detect/coco8): eight COCO training
  photos, used only to test actual inference and latency. Leakage is expected; no
  overhead-cafe or held-out accuracy claim.
- [MEVA author paper](https://arxiv.org/abs/2012.00914): multiview activity research;
  potential event-protocol reference, not a verified cafe preparation set here.
- [SKU-110K](https://github.com/eg4000/SKU110K_CVPR19): additional shelf-detection
  lead, but repository/paper fetches failed in this review. Current access, rights
  and contents remain unverified; it was not used in the benchmark.

No supplied resource provides verified, commercially cleared, representative footage
with all required customer/table/preparation/handover/POS annotations. Annotation
quality, annotation agreement and overhead product visibility require local sampling.
Model repositories supply generic checkpoints, not validated coffee-shop models.
