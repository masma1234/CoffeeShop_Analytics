# Cleanup and code audit, 15 November 2026

The project remains suitable for a local, supervised video prototype. It is not
yet validated for prepared-drink or customer-handover counting in a real cafe.
This audit improves evaluation integrity and removes disposable engineering
artifacts while retaining the application, training notebook and evidence.

## Scope and method

Baseline: `ac625d1`, clean project tree, branch `audit/deep-clean-20261115`.
The project is the nested directory containing `coffee_ops` and its own `.git`.
The outer workspace and home repository were not modified.

The recursive filesystem inventory found 104,640 files and 17,323,494,502 logical
bytes with zero read errors. Reparse links were recorded without following them.
Duplicate analysis reused 102,343 prior hashes only where path, size and nanosecond
mtime agreed; 178 hashes were freshly computed. This is not a fresh forensic hash
of every installed library. Deletion targets for the first cleanup were freshly
hashed before removal.

All 192 tracked files were inventoried with hashes and dispositions. Python AST,
JSON, every notebook Python cell and gzip integrity checks passed. Runtime review
covered input/worker deadlines, configuration, tracking, event semantics, storage,
POS reconciliation, reports, API, evaluation and model promotion. Tests, packaging,
locks, CI, notebook helpers and documentation were included in automated checks.
Reference PDF/DOCX content and installed third-party source were inventoried, not
semantically certified. Historical evidence is retained rather than relabelled as
new measurements. No new vulnerability-feed scan was performed.

## Fixed findings

1. **Frame scores could use an incomplete or foreign detection journal.** Evaluation
   now requires `complete: true` and a source identity matching the annotation
   manifest. Metadata is streamed, preserving bounded memory for long journals.
2. **Ambiguous annotation identities could mislead comparisons.** Frame IDs must be
   unique nonnegative integers, timestamps finite and nonnegative, dimensions
   positive, source class names unique and selected prediction timestamps equal
   to the manifest. Duplicate selected predictions fail immediately.
3. **Manifest image paths could escape the review directory.** Resolved paths must
   remain inside it, including symlink resolution; image checksum validation stays.
4. **Unused imports and incomplete lint coverage.** Removed 11 unused imports,
   renamed one shadowing loop variable and expanded regular Ruff checks to all `F`
   rules plus syntax errors. No dependency upgrade or broad formatting rewrite.

Five new regression tests cover incomplete/foreign journals, timestamp/ID mismatch,
duplicate manifests/catalog names, external image paths, and duplicate/missing
selected predictions. Existing reviewed negatives and sparse class mapping pass.

## Removal and retention decisions

Removed expired Grype/Trivy scanner caches, two local Docker export tar files and
29 completed task-only Python audit drivers: 35 files, 6,266,775,263 logical bytes.
Saved scan JSON/SBOM, image IDs and Docker-engine images remain; tar exports can be
regenerated from retained images. Exact historical vulnerability-feed replay is
no longer available and requires an independently retained feed snapshot.

The clone under `var/engineering-audit-20261112/clean-checkout` existed solely to
test fresh installation. Its disposable `.venv-candidate` is removed; the source
clone, verification logs and main `.venv-candidate` remain. Standard Windows path
enumeration/deletion encountered long-path errors; the final record reconciles
baseline paths using extended native PowerShell paths. Empty directories may remain.

Verified removals total **27,734 files and 7,566,902,280 logical bytes** (7.57 GB).
This includes 27,644 disposable environment files (1,122,480,350 bytes) and 55
generated tool-cache files (177,646,667 bytes). The post-cleanup inventory checkpoint
was 76,961 files / 9,906,363,627 bytes, a net reduction of 7,417,130,875 bytes after
new audit artifacts. Afterwards the two full inventories and clone deletion plan
were losslessly compressed, saving a further 82,095,483 bytes. Their decompressed
bytes and hashes were verified before removing the uncompressed copies. These
snapshots exclude later report/Git writes; they are not an atomic final disk image.

Retained: main candidate environment; `.venv`, `.venv-bench`, `.venv-notebook` and
their `.pth` dependency chain; model cache blobs/snapshots; datasets; recordings;
annotations; operational and synthetic ledgers; current annotated example; saved
test, benchmark and security results; baseline Git history and recovery snapshots.
Reusable scripts remain because they implement documented verification/research
commands. Reference documents and historical reports contain unique material;
their age or lack of runtime imports is not evidence that they are disposable.

Raw inventories, exact removal plans and execution results are local under
`var/deep-clean-20261115`. Curated totals, source hashes, file dispositions and
verification are in [the evidence JSON](deep-clean-20261115.json). Logical file
lengths do not prove equivalent physical disk reclamation; Docker engine storage
is outside the inventory. The final inventory includes newly generated audit logs.

## Verification and task suitability

Windows pytest: 205 tests and 48 subtests pass. Ruff `E9,F`, mypy across 36 app
modules, native NMS, dependency consistency and configuration checks pass.
Linux also passes all 205 tests; CLI acceptance passes all 21 expected command
outcomes, including repeated replay/report checks. Results and cleanup totals are
recorded in the evidence JSON. No fresh model benchmark was needed for these label-validation/import edits;
the earlier actual RT-DETR startup and replay evidence retains its original scope.

| Area | Assessment and remaining work |
|---|---|
| Local MP4 inference and review | Implemented; timestamp, replay, worker and failure fixtures pass. Actual pretrained smoke previously verified |
| Detection/tracking evaluation | Frame integrity improved. Need independent ceiling-camera labels, complete target annotation and recording-group splits |
| Preparation/handover | Only visible transitions/advisory candidates implemented. Confirmed completion, recipient role and paid sales cannot be inferred from cups alone |
| Traffic/table state | Calibrated geometry and conservative unknown states implemented; target-camera accuracy unmeasured |
| Queue analytics | Congestion rule exists; queue lifecycle, service time and staff/customer distinction remain absent |
| Storage/recovery | Atomic ledger, replay and leases tested. Disk retention, real backup/restore drills and live reconnect remain operational gaps |
| Scale | Tracker/worker state is bounded. Legacy export and POS JSON readers materialize whole documents; prefer streaming video exports and CSV POS for large inputs; distributed scale unverified |
| Security/deployment | Previous OS and optional Transformers findings remain unresolved. Local loopback API only; no production approval or fresh security clearance |
| Training/model selection | Notebook and conditional shortlist retained. Train only after a labeled baseline identifies detection errors; temporal or observability failures may need different work |

Next evidence needed: a permissioned representative ceiling-camera recording,
calibrated zones and independently reviewed frames/events. Measure missed objects,
ID fragmentation, event false positives and count error before choosing a model
or training experiment. Passing software tests does not supply those measurements.
