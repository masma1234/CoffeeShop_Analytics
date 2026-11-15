# Cleanup manifest: 2026-11-12

Status: **COMPLETED with one reconciled logging interruption**, documented below.
The exact proposal was written and reviewed before the first deletion.

Exact proposal: [compressed JSON](docs/audits/cache-cleanup-proposed-20261112.json.gz).
It contains 18,189 exact relative paths, sizes, SHA-256 hashes, matching
source paths/hashes, reasons and recovery instructions: 370,659,765
logical bytes. Archive SHA-256: `bb25c86666f2875d5bb0850133cd87f867f8f0d3adbbf18732c8327344070afc`.
The original local proposal is `var/engineering-audit-20261112/cache-cleanup-proposed.json`.

Every proposed file is an untracked CPython cache under `__pycache__`, with a
matching source file. CPython magic/header timestamp+size or source hash is
verified. Source, cache and all parents must stay within the project without
reparse points. Imports may regenerate these caches from retained source.
No source module or resource points exclusively to the removed cache.
The executor rechecks both SHA-256 values, exact size and path bounds immediately
before individually removing a file. Changed or ambiguous files are skipped.
No directory is recursively deleted. Eighteen ambiguous/stale cache entries were
excluded at proposal time; the candidate environment and `var/` were excluded.

Recovery: retained identical `.py` files regenerate the bytecode. App source and
unique documentation additionally have `source-before.zip`, a SHA-256 manifest,
the `baseline.bundle` and local baseline commit 87dc561. Cache bytes themselves
contain no unique source or business evidence.

Preserved: all source/configuration, original environments and their dependencies,
model weights, datasets, media, annotations, SQLite/business ledgers, credentials,
reference documents, archives and unique audit evidence. In particular, the old
3,414,958,080-byte Grype cache database is retained because the request explicitly
protects databases. Its removal needs a separate decision. Trivy's current
database and the previous image archive remain reproducibility artifacts.
Exact duplicate library binaries stay in their functioning environments.

The previous root reports and README are retained under
`docs/history/release-20261111`, with historical banners and relocated Markdown
links. Original bytes remain in Git and the snapshot. No historical finding is
discarded. `document-archive.json` records original and archive hashes.

Execution results are in the local `cache-cleanup-record.jsonl`, resumed record
and separate compressed final record below. Recovered space is based on actual
absence checks and result provenance, not only the proposed sizes.
Logical byte counts do not equal guaranteed physical disk space reclamation.

## Executed result

Observed removed: **18,189 files, 370,659,765 logical bytes** (353.49 MiB). All matching source files remain. No directory or tracked source file was deleted.

The first run logged 7,723 successful deletions, then PowerShell Add-Content
failed after the next Remove-Item. Reconciliation identified exactly one additional
absent cache (26,663 bytes), whose matching source still hashed correctly. Its
outcome is explicitly labelled as reconciled, not a successful original log entry.
The executor was changed to one shared-readable stream and a flushed intent before
each deletion. The resumed run recorded 10,465 further successful deletions and
skipped the 7,724 already-absent paths. Raw failed and resumed logs are preserved.

The [completed exact-path record](docs/audits/cache-cleanup-completed-20261112.json.gz)
contains proposal hashes, source hashes, per-file final presence checks and outcome
provenance. It records every removed path while preserving the logging limitation.
Its SHA-256 is `444a7107d5af09296fe8d5c690045eed7b74e8ce53b74a8cacaa120b1119c319`.

No scanner database was removed. No uncertain duplicate, old environment, model,
dataset, annotation, footage, archive, credential or unique report was discarded.
Before/after totals include new verification environments and image evidence;
net repository growth is separate from these proven cache removals.
