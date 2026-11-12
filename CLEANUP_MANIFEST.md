# Cleanup and preservation manifest : 2026-11-12

Evidence was collected on 2026-11-11; this handoff was finalized on 2026-11-12. Saved commands, timestamps and digests retain their original dates. No cloud deployment or security clearance is implied.

**No existing files were deleted, moved or reclassified as safe to destroy.**
The source/reference snapshot was captured before edits. Existing app/data, research
environments, reference PDFs/DOCX, historical evidence and model artifacts were retained.
The snapshot and all audit working artifacts are under ignored `var/release-audit-20261111/`.

| Requirement / class | Status | Disposition and reason |
|---|---|---|
| Original source/reference preservation | VERIFIED | 151-file pre-edit manifest and `before-source.zip`; SHA-256 `d9b42bd0703be6c75519cf358f74bf56b3b28c59c101d9f4ddc6bd7b0d33424c`. Original versions of changed files recoverable from that snapshot. |
| Original Git index preservation | BLOCKED | Home-index fingerprints matched at project initialization and earlier rechecks, but changed by the final check. No project command was issued to write it. Current bytes retained as evidence; no automatic restoration. Initial full index/entry snapshot was not captured, so logical changes and actor are not established. |
| Removed files | VERIFIED | None. No removal was explicitly authorized as an identified-file list, and no necessity for deletion was established. |
| Existing supported app/config/schema/model examples | VERIFIED | Retained. Only cursor validation and minimal liveness behavior changed in application source. |
| Legacy/reference source and documents | VERIFIED | Existing project contents retained. No attempt to reconstruct or delete the legacy files described as removed in older audits. |
| Generated runtime data / private evidence | VERIFIED | Existing `var/`, ledgers, videos, frames, annotations and model artifacts retained; excluded from Docker context. Retention/privacy clearance remains BLOCKED. |
| Virtual environments / downloaded libraries | VERIFIED | `.venv`, `.venv-bench`, `.venv-notebook` preserved. Inventory is separate from first-party source; they are not release inputs. |
| Archives / snapshots | VERIFIED | Retained, including new source snapshot and exported runtime image. Exhaustive archive secret clearance is NOT TESTED. |
| Vulnerability databases / scanner caches | VERIFIED | Scanner runs in a disposable container; no host cache/database removed. Raw report retained in audit working directory. Existing unrelated tools/caches left alone. |
| `.gitignore` | VERIFIED | Existing privacy rules retained; added `.db`/`.sqlite` and WAL/SHM variants used by SQLite. Ignore rules do not remove already-tracked files; the new local repository ignores runtime databases and audit output; no project command was issued to stage or rewrite the enclosing index; its later fingerprint change remains unattributed. |
| `.dockerignore` | VERIFIED | Default deny; allow only runtime examples/source and explicitly needed test/scripts/notebook inputs. No `var/`, virtualenv, Git metadata, media, real weights, credentials, reference documents or old benchmark outputs. |
| Production dependencies | VERIFIED | No runtime dependency added or upgraded. Existing advisory debt remains FAILED for release. Security scanner is a separate pinned tool image. |
| Minimal production image | VERIFIED | Runtime stage copies coffee_ops, example config/metadata and schemas; tests/notebooks/scripts only in verification stages. Default final stage inherits runtime and exits after config validation. |
| New audit outputs | VERIFIED | Four handoff Markdown files; supporting raw evidence remains ignored and local. No cloud resource or publication. |

Changed existing files: `coffee_ops/storage.py`, `coffee_ops/api.py`, `tests/test_api.py`,
`.github/workflows/tests.yml`, `.gitignore`. New source/build support:
`Dockerfile`, `.dockerignore`, `scripts/benchmark_api.py`, `scripts/verify_egress.py`.
The four requested handoff documents are new. No application acceptance assertions,
thresholds or timeouts were changed.

`CLEANUP_MANIFEST.md` does not authorize pruning operational footage, immutable history,
annotations, model/checkpoint caches, original environments, archives or the new audit
evidence. Detailed disk inventory and pattern-scan coverage are recorded in evidence;
counts are a point-in-time inventory and do not prove private-data clearance.

## Point-in-time workspace inventory

| Class/directory | Files | Bytes | Disposition |
|---|---:|---:|---|
| root_files | 15 | 738,076 | Retained; environments/data excluded from Docker |
| .github | 1 | 3,072 | Retained; environments/data excluded from Docker |
| .venv | 31,010 | 1,054,306,577 | Retained; environments/data excluded from Docker |
| .venv-bench | 21,348 | 4,905,232,988 | Retained; environments/data excluded from Docker |
| .venv-notebook | 13,156 | 291,146,254 | Retained; environments/data excluded from Docker |
| coffee_ops | 67 | 543,760 | Retained; environments/data excluded from Docker |
| config | 1 | 3,803 | Retained; environments/data excluded from Docker |
| docs | 79 | 1,017,654 | Retained; environments/data excluded from Docker |
| models | 1 | 219 | Retained; environments/data excluded from Docker |
| notebooks | 2 | 69,170 | Retained; environments/data excluded from Docker |
| schemas | 1 | 4,459 | Retained; environments/data excluded from Docker |
| scripts | 10 | 86,773 | Retained; environments/data excluded from Docker |
| tests | 30 | 363,490 | Retained; environments/data excluded from Docker |
| var | 297 | 4,944,291,449 | Retained; environments/data excluded from Docker |

Selected credential-pattern scan: 201 textual first-party/runtime-evidence files; 1 hit. The hit is the synthetic credential-bearing stream URL in `tests/test_traffic.py:134`, used to verify source hashing. The raw credential value is not repeated in these reports.

This is **not** exhaustive secret clearance: no incident fingerprint, Git history, entropy scan, binary/media inspection or exhaustive archive scan. Third-party environments and audit copies were excluded from pattern matching. One DOCX archive and reference PDFs remain retained and un-cleared; runtime databases/media/checkpoints remain protected. Counts predate the last report writes.

First-pass source preservation result: **VERIFIED**: 146 unchanged originals, five documented modifications, zero missing files. Full source and raw artifact digests are embedded in RELEASE_EVIDENCE.md. No additional source mutation or cleanup occurred.


Retained scanner-cache inventory: 3414958080 bytes. The timed-out scan did not establish a validated current database/report. Cache digests are in resumed/grype-cache-inventory.json; no cache was deleted.


After access changed, local Git metadata, a clean local clone, resumed scan/benchmark evidence and the synchronized audit helper were retained. Nothing was removed. Final source recheck: 146 original files unchanged, five documented originals changed, zero missing. End-to-end enclosing-index preservation is BLOCKED by an observed fingerprint change; its current bytes were copied as evidence, with no restoration or home-index write. Local baseline/implementation commits do not authorize a push or supply missing P1 ancestry.

