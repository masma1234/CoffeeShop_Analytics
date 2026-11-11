# Dataset and labeling strategy

Priority is authorized footage from the target ceiling camera. Public preparation
videos and image datasets can help transfer learning but cannot replace a local test
set. Product appearance, pixel size, occlusion and counter layout dominate this domain.

1. Collect representative sessions: quiet/busy, day/night, normal/low light, multiple
   cups, returns, staff restocking, queues, standing near tables, handover blocked by a
   body, camera movement and disconnects. Record exact source timestamps and frame rate.
2. Label people, observable products and visibility. Start with generic cup/bottle/
   pastry/package categories; use unknown_product where subtype cannot be observed.
   A cup's visible appearance does not establish its contents or readiness.
3. Label anonymous person/product track identities, seat-region occupancy intervals,
   entry/exit/queue intervals and observable preparation/ready/handover/return events.
   Include uncertain/occluded/not-observable labels and event time tolerance.
4. Maintain independent POS records. Only timestamp/zone/SKU-supported association is
   evaluated; neither annotators nor models should infer payment from appearance.
5. Split by recording session/day, and reserve a held-out camera where available.
   Never distribute adjacent frames across train/validation/test. Separate public
   image pretraining material from local acceptance recordings; hash manifests.
6. Have two annotators review a difficult subset. Document disagreement rules before
   scoring; report missing labels and unobservable outcomes, rather than force answers.

Initial planning target (not a statistical guarantee): 30-60 minutes of varied footage
and at least 100 observable handovers plus explicit hard negatives, expanded until
scenario-level error estimates stop being dominated by a few examples. Dedicate one
session to validation and another untouched session to final comparison. Low event
counts require uncertainty intervals and further collection, not a decisive ranking.

RetailAction provides the closest supplied overhead interaction perspective, but its
custom commercial terms need resolution. BARISTA is first-person/noncommercial and
cannot validate ceiling-camera performance. MERL has useful staged overhead temporal
actions; commercial rights are a separate gate. The [resource inventory](resource_inventory.md)
records those boundaries. Small Roboflow image sets require manual label and duplicate
audits before mixing with shop data.

Use the existing grouped split/manifest audit tools. Preserve recording/session IDs,
camera/calibration version, label taxonomy, license, source hash and independent POS
provenance. Keep identity labels local to each visit; avoid faces, biometrics and
cross-visit identity. Raw recordings remain private operational material.
