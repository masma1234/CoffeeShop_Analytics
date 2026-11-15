# Final engineering audit

Audit started 2026-11-12; generated 2026-11-12T22:42:15.821075+00:00. **NO-GO for public GitHub publication
and deployment.** The code is prepared for private owner review; unresolved
licensing/reference rights, security debt and operational validation remain.
No push, remote creation, visibility change, history rewrite or deployment occurred.

## Verified starting state

The intended root is the nested `computer-vision-main` containing `coffee_ops`,
README and its own `.git`. The enclosing desktop folder is a workspace, and
`C:/Users/aymen/.git` is a separate home repository. Project HEAD was
`87dc5612e5b91f39049df9ea133d8b8a6f450a8b`, branch
`audit/staging-readiness-20261111`, clean, 159 tracked files, no remote/alternates.
History also contains 9b4b985 and baseline 0a39057; missing earlier product history
is not invented. Prior reports were compared with files and rerun commands.

Before edits: all tracked source was zipped and SHA-256 manifested; both Git
indexes/staged-entry bytes and a full project history bundle were preserved.
Work continued on `audit/final-engineering-20261112`. Both index byte hashes and
logical staged-entry hashes remain unchanged, and no original file is missing.
The home index is unchanged during this audit; the previous audit's earlier
unattributed change cannot be retroactively assigned to an actor.

Outer workspace VS Code settings now disable parent-repository discovery and scan
the nested project explicitly. The original settings were backed up. This is a
local workspace change outside the publishable repository; it does not alter
either Git index, global Git settings or existing history.

Baseline: old unittest 184 with 13 optional skips; pytest absent; native Torch
2.9 pair loaded. Docker was initially stopped and recovered locally. The actual
old image had 298 vulnerability matches and forced API SIGTERM termination.
Initial mypy found 89 errors. Prior unrelated job-search template requirements
do not describe this application's releases or business requirements.

## Implemented engineering improvements

- Repaired SIGTERM handling so the existing API/server cleanup runs; unchanged
  three-second container stop now exits 0 in 0.489s instead of forced 137.
- Added/narrowed types across storage, reports, detector IPC, evaluation and CLI.
  Explicitly reject missing DB/run/POS prerequisites rather than dereferencing
  optional values. No broad type-error suppression or architecture rewrite.
- Upgraded the matched CPU Torch/Torchvision pair to 2.13.0/0.28.0, constrained
  setuptools 84.2.1 and updated vulnerable OS packages where apt supplied fixes.
- Added platform-specific hashed runtime wheel locks and a fresh-environment
  helper with Windows long-path support. Kept existing environments untouched.
- Split dependency/test/runtime image stages; production omits pip/ensurepip,
  disables automatic package/model fetching, stays non-root and retains its small
  default validate-and-exit contract. Resource/network isolation is tested at launch.
- Added reproducible inventory, source-backed cleanup, publication screening,
  documentation-link and evidence-quality tools. Changed the scanner workflow
  from unsuccessful Grype attempts to verified Trivy release assets with JSON/SBOM
  output before an unsuppressed high/critical gate.
- Kept one README overview and one current architecture. Archived old root
  reports/README with original bytes recoverable in Git/snapshot; old foundation
  reports are clearly historical. Research/measurements/runbooks remain separate.

## Reference and disposition review

| Files / group | Reference and decision |
|---|---|
| Previous root audit, evidence, deployment and cleanup reports; previous README | Superseded as current instructions, but contain unique failures/digests/decisions. Archived under `docs/history/release-20261111`; original bytes retained in Git and snapshot |
| `docs/PROJECT_STATUS.md` | Replaced by a short navigation index; current overview stays in README and current scope in IMPLEMENTATION_STATUS. Original index remains recoverable in baseline Git/snapshot |
| `docs/architecture/recommended_architecture.md`, `event_counting_design.md`, roadmap/recommendations | Retain unique future design and foundation decisions. Recommendation/historical status is explicit; they do not override implemented architecture or release gates |
| `docs/research`, `docs/benchmarks`, `docs/validation-current` | Retain primary-source catalogs, licensing notes, raw measurements and old experiment provenance. Historical results are not new capacity/accuracy evidence |
| Existing benchmark, notebook and verification scripts | Referenced by development/research/runbooks/CI or retain useful reproducibility behavior. No unreferenced migration helper was proven disposable; do not remove by filename alone |
| Old prototype attempt directories and generated reports under `var` | Protected/ambiguous or unique local evidence; retained. An empty or apparently unused directory is not deletion evidence |
| Model cache blobs/snapshot links, notebook `.pth` dependencies and equal-content libraries | Framework/environment references require these copies; size or equal SHA-256 alone does not make them disposable |
| Proposed bytecode paths | CPython import cache with verified matching source and source/header/hash evidence; exact per-file manifest, bounds checks and recovery justify deletion |

All new one-off audit drivers and raw outputs stay in the single ignored audit
directory. Reusable tools are in `scripts`; source caches are covered by Git ignore
rules. Original reference documents remain pending rights/content review.

## API, storage and event review

The API is shared-token, authenticated read-only loopback JSON. Minimal public
liveness exposes no DB details. Query/64-bit cursor bounds, redaction, storage
failures, thread limits and socket deadlines are covered. There is no per-user
authorization model; that is a hosting gap, not a feature established by a token.
SQLite frame/projection writes and POS allocations are transactional, camera leases
prevent competing writers, repeated replay is idempotent, and failed frames poison
in-memory state rather than silently continuing. Fault/concurrency tests exercise
these boundaries; they are not a proof that every possible race is absent.

Anonymous tracks expire and decoder/tracker/telemetry/review buffers are bounded.
Ledgers, health history, clips and exports can grow on disk; retention/capacity and
backup remain operational work. Real source credentials are hashed/redacted in
current provenance/HTTP paths; old logs and private ledgers need owner-controlled
review before export. Only paid POS lines count as sold units. Visible products,
pickup movements and handover candidates remain neutral observations with unknown
business semantics. No real payment integration or handover recognizer was added.

## Verification and unresolved security

Windows and Linux: **187 tests pass, no optional skips, 31 subtests**, end-to-end
unittest/CLI acceptance, pip check, native NMS, critical Ruff checks and mypy over
35 app modules. Rounded coverage is 84% Windows / 83% Linux. A new Windows checkout
installed the reviewed hash lock and passed all 187 unittest tests plus acceptance.
All 35 final app-module hashes match the tested clone and scanned image.

Pretrained RT-DETR ran on two repeated public-photo frames after a failed cold-load
attempt. Both are retained. Warm success does not clear cold-start reliability,
camera accuracy, business counting or sustained hardware sizing.

The production-image scan completed: **278 OS package/advisory matches**,
including **1 critical and 61 high**, across 130 distinct IDs. There are **zero
Python-package findings in that production image**, not zero vulnerabilities.
No fixed OS versions were supplied by the current feed for those remaining matches.
All stay open with component context and vendor references in the
[security triage](docs/audits/security-20261112.md). Optional Transformers 4.57.6
has six advisory IDs and remains isolated from production. Old research
environments retain advisory debt. No finding is risk-accepted or silently suppressed.

## Disk inventory and cleanup

Starting full-inventory checkpoint: 14,676,673,897 logical bytes,
82,955 files, 14,669,716,784 ignored bytes and
2,285,234 tracked bytes. The snapshot includes candidate/tool
bootstrap already in progress; it is not an atomic task-start image. It reported
13,073 exact duplicate groups, 151,265,845 duplicate logical bytes, and 10,249
changed/missing reads mainly in the active candidate install. Those limitations
are retained and a stable final pass follows.
The raw baseline ignored tally missed 3,415,637
bytes inside an ignored nested verification clone; inheriting the already-existing
`var/` rule corrects it to 14,673,132,421 bytes. Final classification
handles Git's ignored-directory entries explicitly without changing ignore rules.

Final inventory checkpoint: **17,262,158,076 logical bytes (16.08 GiB), 104,456 files**, 17,254,777,968 ignored bytes. Net change: **+2,585,484,179 bytes**.

Duplicate groups: 37,948; redundant logical bytes within equal-content groups: 1,816,160,223. Errors: 0; reparse links not followed: 21. SHA-256 reuse/fresh-read counts are explicitly recorded.

Removed **18,189 bytecode caches,
370,659,765 logical bytes (353.49 MiB)**, retaining
every matching source file. The exact proposal existed before deletion. One
post-delete log write failed, was reconciled with its retained source/hash, and
is separately marked in the final record. No recursive directory deletion occurred.
No source/config/model/data/annotation/database/credential/archive was deleted.

Net growth includes a new isolated environment, a fresh verification environment,
actual production image evidence, scanner/tools and complete audit records.
Cache bytes removed must not be presented as net project shrinkage. Logical file
lengths are not filesystem allocation, hardlinks may be double-counted, directory
parent/child totals overlap, and inventory files/report writes can occur after a
checkpoint. Docker engine storage outside this root is not included or pruned.

[The disk appendix](docs/audits/disk-inventory-20261112.md) includes every top-level
directory, largest 100 files and directories, extension/category counts and exact
duplicate findings. [The cleanup manifest](CLEANUP_MANIFEST.md) links exact
proposed/completed paths, sizes, hashes, reasons, recovery and logging limitations.

Retained decisions: the 3,414,958,080-byte failed Grype DB, current Trivy DB, prior
image archive, cached model weights and old virtual environments. Database/model
preservation takes priority over size reduction. Equal-content library files stay
inside environments that require them. Reference PDFs/DOCX and the benchmark plot
need owner publication-rights/content review. No LFS migration is needed for current
source candidates; future licensed models/datasets belong in approved artifact
storage or explicitly reviewed LFS, never an accidental `git add .` from home.

## Decision and prioritized next actions

1. **Public publication: NO-GO.** Owner must choose a source license and review the
   three reference documents, benchmark image, attribution and intended private
   GitHub destination. No remote has been assumed or configured.
2. Resolve or obtain accountable, package-specific risk decisions for remaining
   OS findings. Independently validate a patched optional Transformers stack.
   The unsuppressed security and missing-LICENSE CI gates are expected to fail now.
3. Establish reliable cold model startup and real ceiling-camera evaluation with
   held-out annotations, event/count/tracking metrics and resource measurements.
4. Design provider-appropriate auth, persistent storage/restore, retention and
   enforceable egress controls. Actual Render/cloud staging is untested and needs
   a separately approved synthetic-data deployment.
5. Review the proposed commits and candidate file list, then obtain the user's
   explicit approval before any push, publication or deployment. Private review
   is the recommended next sharing scope while rights/security work is open.

See [release evidence](RELEASE_EVIDENCE.md), [deployment gates](DEPLOYMENT_READINESS.md),
[GitHub readiness](GITHUB_READINESS.md) and [implementation status](IMPLEMENTATION_STATUS.md).
