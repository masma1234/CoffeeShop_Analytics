# GitHub readiness

Owner-directed publication, 15 November 2026: the owner explicitly requested a
push to the existing public repository
[masma1234/CoffeeShop_Analytics](https://github.com/masma1234/CoffeeShop_Analytics).
The selected branch is `audit/deep-clean-20261115`. All 194 tracked files are
included: application, tests, notebook, dependency locks, CI, configuration,
documentation, research and saved evidence. Local environments, model caches,
recordings and operational databases remain excluded. The current maintenance
results are in [the cleanup audit](docs/audits/deep-clean-20261115.md).

This owner instruction supersedes the earlier hold on pushing source. It does
not resolve the historical security, license/reference-rights or real-camera
validation findings below. This remains an offline pilot; production deployment
is not approved, and the existing unsuppressed release gates may fail. Statements
below about no remote, no push, unstaged work and old HEADs are historical audit
checkpoints, not instructions to reconstruct the current Git state.

Local continuation, 15 November 2026: the reviewed working tree was preserved as
baseline commit `b2ebc3c` on `fix/detector-startup-20261115` before new changes.
The unstaged/index/HEAD statements below describe the 12 November audit checkpoint.
Current inference startup work and its verification are documented in the
[startup report](docs/benchmarks/detector_startup_20261115.md). No remote, push,
publication or deployment was performed during this continuation.

**Decision: NO-GO for public publication.** Recommend a private owner-review
repository after explicit destination/visibility approval and rights review.
Preparation is local only: no push, repository creation, remote change, public
visibility change or cloud deployment was performed. Generated 2026-11-12T22:42:15.821075+00:00.

## Provenance and scope

Publish only the nested directory containing this README, `coffee_ops` and its
project-local `.git`. Current branch: `audit/final-engineering-20261112`; HEAD:
`87dc5612e5b91f39049df9ea133d8b8a6f450a8b`; no remote. Original three commits
remain intact. Candidate work is intentionally unstaged; no new source commit
was made before review. Both project and home index byte/staged-entry hashes match
the saved baseline; home history and private filenames are not part of this audit's
publication scope. Outer workspace settings are local and outside the Git candidate.

## Candidate/data screening

`scripts/review_publication.py` inspected 188 candidate files,
165 reachable blobs in all three local commits and DOCX
XML members. The finite signature/assignment scan found the synthetic URL-credential
fixture in `tests/test_traffic.py:134` and its historical blob; no real secret was
identified by those patterns. Values are redacted from the report. This is not
exhaustive entropy/forensic scanning or secret clearance. PDFs/images were not
rendered for private content; owner review is still required.

No runtime DB, real CCTV, model weights, dataset or local environment is in the
candidate set. `.gitignore` excludes those operational paths, caches and `var`;
`.dockerignore` defaults to deny and allowlists only runtime/verification inputs.
Raw evidence includes index backups, local paths and protected records and must
remain local; do not upload `var/engineering-audit-20261112` wholesale.
The committed cleanup/triage gzip files contain relative paths/hashes/statuses,
not footage, model contents or credentials. Current candidate files need no LFS.

## Licensing/attribution gates

There is no owner-selected root LICENSE; do not invent ownership permission or a
permissive license. Ultralytics 8.3.163 declares AGPL-3.0 in the installed metadata
and [publisher license](https://github.com/ultralytics/ultralytics/blob/v8.3.163/LICENSE).
Torch/Torchvision and other dependencies have separate licenses; the production
license inventory is saved. This records metadata, not legal approval.

Three retained reference binaries (two PDFs and one DOCX) and the benchmark PNG
need owner review of rights, authorship and private/visible content. Dataset terms
and each checkpoint's model card remain separate; for example the
[RT-DETR model card](https://huggingface.co/PekingU/rtdetr_v2_r18vd) declares Apache-2.0,
which does not grant rights to unrelated training footage or reference documents.

## Proposed local commits, not executed

1. Runtime reliability and typing: `coffee_ops` guards/annotations, SIGTERM entrypoint,
   entrypoint regression tests and corrected optional-import comment.
2. Reproducible setup and security verification: dependency inputs/constraints/platform
   locks, fresh-environment helper, Dockerfile/ignore policies, quality/container/
   inventory/cleanup/publication/docs tools and CI definition.
3. Audit handoff: six authoritative reports, current README/architecture, historical
   banners/archives and compressed exact cleanup/security records.

The exact [candidate path list](docs/audits/publication-candidate-20261112.txt)
contains existing tracked files plus proposed additions. Review it before staging;
do not stage the enclosing desktop or home directory. A file in that list is not
automatically rights-cleared. No `LICENSE` or remote is silently supplied.

## Verification and expected gates

Fresh Windows clone/overlay installation and 187-test acceptance passed; Linux
187-test/type/lint/acceptance checks and actual production-image isolation passed.
All final app source hashes match those tested artifacts. See
[RELEASE_EVIDENCE.md](RELEASE_EVIDENCE.md) for command exits and failed attempts.
CI defines Windows/Linux CPU/video jobs, actual image scanning/SBOM and source
integrity. It has not executed on GitHub. The security gate remains red with
62 high/critical OS matches, and the owner-license gate remains red without LICENSE.
Public source review is not the same decision as deploying the vulnerable image.

Before any push: owner chooses remote/visibility and source license, reviews the
reference artifacts and candidate diff, addresses the reported gates or records
specific accountable decisions, and explicitly approves publication. Preserve
history; any later sanitization/history rewrite needs separate authorization.
