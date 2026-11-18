# Workspace cleanup

Updated 17 November 2026 after the owner's request to minimize local storage.
This page records the current state; the JSON manifest retains the earlier
16 November documentation cleanup as historical evidence.

## Storage result

The measured folder size fell from **15.01 GiB to 1.83 GiB**,
a reduction of **13.18 GiB** (about 87.8%). The scan counted
about 141,337 regular files before cleanup and 37,913 afterward.
The final scan used Windows extended paths and completed with zero errors.
These are regular-file content sizes, with symlinks excluded; generated evidence
written afterward may change the totals slightly. They are not a claim about
filesystem allocation or storage reclaimed from other projects.

Source publication is unchanged at `097c1bd76d6c37efeb43fdab41dde9d6076596e7`,
branch `audit/deep-clean-20261115`. The candidate still has 193 existing
nonignored source/documentation files. No commit, push, deployment, license
selection or Git history rewrite occurred.

## Removed

- Four redundant host environments: `.venv`, `.venv-bench`, `.venv-notebook`
  and `.venv-ci`. Their package inventories were saved before deletion.
- The disposable audit `clean-env`, document-inspection tools and copied source
  checkouts used by earlier verification runs.
- The unused SmolVLM download, legacy YOLO research weights and the duplicate
  RT-DETR audit checkpoint. The original RT-DETR and both D-FINE checkpoints remain.
- The old Docker image export, Trivy database cache, scanner executables and
  redundant scanner/annotation download archives. Fresh verified tools and a
  new database download are needed for the next local security scan.
- Superseded large raw inventories and regenerable audit, test, lint and type
  caches. Unused publisher-test bytecode was also removed. The earlier removal
  of 16 obsolete Markdown documents remains in the
  [cleanup manifest](workspace-cleanup-20261116.json).

## Retained

- One independent CPU/video environment: `.venv-candidate`. It retains the host
  compatibility stack's known dependency debt; disk cleanup is not a security
  upgrade. The verified RT-DETR Docker profile is documented in
  [current release gates](../../GITHUB_READINESS.md).
- Compiled imports in the retained runtime. Clearing every runtime bytecode
  cache increased cold-import costs; these caches were rebuilt before the
  successful acceptance rerun and are preserved by the cleanup helper.
- All application modules, tests, scripts, configuration, schemas, requirements,
  notebooks and current documentation. Application file hashes are unchanged.
- All three shortlisted detector checkpoints and all 600 benchmark images with
  their labels, split/provenance manifest and evaluation results. Their SHA-256
  hashes were checked after cleanup.
- Current scan reports, SBOMs, licenses, test results and dated audit evidence.
- The two reference PDFs, DOCX, benchmark PNG and repository Git metadata.
  Their bytes are unchanged. Rights and source-license decisions remain open.

The old GPU/notebook environments are gone. Before GPU benchmarking or training,
create a fresh environment using the [notebook guide](../../notebooks/README.md).
The prior inherited CUDA stack has not been promoted or silently replaced.
Docker images, containers, volumes, other projects and user-wide caches were not
removed as part of this cleanup.

## Verification and safety

Fresh host validation passed 218 pytest tests and 51 subtests, package consistency,
configuration/native operators, Ruff and mypy across all 36 application modules.
Statement coverage is 84.8%. Final CLI acceptance passed all 21 commands and its
218-test unittest suite in 107.817 seconds, within the unchanged 180-second gate.

The first compound quality run remains recorded as eight passing checks and an
acceptance timeout (exit 124). A retry with the previously authorized Docker
services temporarily stopped also timed out. After restoring compiled runtime
imports, the separate final acceptance rerun passed. Neither failed record was
overwritten and no deadline or vulnerability threshold was weakened. Clearing
all runtime caches is not part of the final maintenance policy.

All 12 temporarily stopped Docker containers were restored, and a fresh check
confirmed they were running and healthy. Application/model/dataset/reference
hashes match their pre-cleanup values. This is software verification, not cafe
accuracy or production approval.

The [cleanup helper](../../scripts/cleanup_workspace.ps1) defaults to a preview.
It validates workspace containment, protects tracked and new source files,
checks running process paths and arguments, rejects directory links and external
file links, deduplicates nested targets, verifies the retained RT-DETR checkpoint
before removing its duplicate, and writes a per-target execution log.
PowerShell parsing and five process-path boundary checks passed, including
quoted paths and similarly named environments.

```powershell
# Preview reproducible artifacts and caches.
.\scripts\cleanup_workspace.ps1

# Apply the displayed cleanup plan.
.\scripts\cleanup_workspace.ps1 -Apply

# Optional research-environment removal requires saved package inventories.
.\scripts\cleanup_workspace.ps1 -RemoveResearchEnvironments
```

Execution logs, before/after inventories, package inventories and fresh test
results are under ignored `var/storage-cleanup` and
`var/workspace-cleanup-executed-*.json`. Review and sanitize them before sharing;
they contain local paths and are not publication artifacts.

## Incomplete additional reduction

A lossless archive of 1,155 retired evidence files was created and every archived
file hash was verified: 221.9 MiB of originals compress to 47.9 MiB. Automatic
tool policy rejected removal of those archived originals. It also rejected
removal of the newly redundant archive. Both remain; no other method was used
to bypass either rejection. Their locations and hashes are recorded in
`var/storage-cleanup/retired-evidence-manifest.json`.

These remaining files prevent claiming that every unnecessary file was deleted.
The completed large-file cleanup and its measured savings are separate from this
blocked final reduction. No security, licensing or cafe-accuracy gate is cleared
by deleting local files.
