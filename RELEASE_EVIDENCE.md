# Release evidence

The [15 November startup continuation](docs/benchmarks/detector_startup_20261115.md)
records subsequent source changes and their separate checks. The 12 November
image digests and source-equality claims below apply to that historical checkpoint,
not to the later working tree. No new production-image scan or deployment is
claimed by the startup continuation.

Audit started 2026-11-12. Generated 2026-11-12T22:42:15.821075+00:00. Commands and raw logs are local under
`var/engineering-audit-20261112`. They are preserved as executed, including failed
attempts. No remote CI, cloud staging, real-camera accuracy or production capacity
is claimed. Windows uses Python 3.13; Linux uses Docker Desktop's Linux engine,
the pinned Python 3.13-slim base and matched Torch 2.13.0+cpu/Torchvision 0.28.0+cpu.

## Starting checks and observed failures

Base commit `87dc5612e5b91f39049df9ea133d8b8a6f450a8b`, clean 159-file tracked tree,
branch `audit/staging-readiness-20261111`, no remote. Old unittest: 184 tests run with
13 optional skips; pytest invocation failed because pytest was absent. Docker was
initially stopped, then started locally. Baseline container auth/read-only/egress
passed but SIGTERM forced exit 137. Initial mypy: 89 errors in 17 of 35 modules.
These failures were not erased or reclassified as passing checks.

The first new Torch install hit Windows long-path error 206 and left incomplete
metadata in the new candidate environment. Extended-path installation repaired
only that environment; no registry/global package or old environment was changed.
Initial lock generation lacked archive hashes for metadata-only wheel resolutions;
the resolver now hashes the actual wheel over HTTPS when needed. Final Windows
fresh install and Linux Docker install both enforce the generated hashes.

## Final Windows candidate

Command: `.venv-candidate/Scripts/python.exe -B scripts/check_quality.py --output var/engineering-audit-20261112/final-windows`.
Pytest: **187 passed, no skips, 31 subtests**. Coverage: 84% when rounded by coverage.
Acceptance separately ran unittest's 187 tests and end-to-end CLI/POS/replay checks.

| Check | Exit | Seconds |
|---|---:|---:|
| pip-check | 0 | 2.724 |
| doctor | 0 | 82.877 |
| config | 0 | 0.168 |
| pytest-coverage | 0 | 135.405 |
| coverage-report | 0 | 1.315 |
| coverage-json | 0 | 0.494 |
| ruff | 0 | 0.985 |
| mypy | 0 | 35.875 |
| acceptance | 0 | 129.358 |

Ruff scope is `E9,F63,F7,F82`, not every style rule. Mypy checks all 35 app modules,
including untyped function bodies; missing third-party stubs are explicitly ignored.
JSON, IPC and external SDK boundaries retain dynamic types where appropriate.

## Final Linux video environment

Command: Docker image `coffee-ops-engineering-video:20261112`, `--network none`,
no capabilities/no-new-privileges, 2 CPUs/3 GiB, `scripts/check_quality.py --output /evidence/quality`.
Only its output directory and the final quality-runner script were mounted on the
second run. Pytest: **187 passed, no skips, 31 subtests**; rounded coverage 83%.

| Check | Exit | Seconds |
|---|---:|---:|
| pip-check | 0 | 1.122 |
| doctor | 0 | 10.580 |
| config | 0 | 0.325 |
| pytest-coverage | 0 | 33.552 |
| coverage-report | 0 | 1.174 |
| coverage-json | 0 | 1.124 |
| ruff | 0 | 0.226 |
| mypy | 0 | 135.926 |
| acceptance | 0 | 46.519 |

First Linux run: tests/acceptance passed, Ruff cache initialization failed and mypy
exited 2. Moving all tool caches to the writable evidence output fixed the rerun;
the original failed logs remain under `final-linux`. No type rules or app timeouts
were relaxed. The cached re-run is a local Linux container result, not a hosted CI run.

## Fresh checkout and published setup

A new local clone of commit 87dc561, without hardlinked Git objects, received an
exact candidate overlay. Its synthetic `origin` was removed in that verification
clone only. Nothing was committed or remotely published. The original project and
home indexes were untouched. This is a baseline clone plus an explicitly recorded
uncommitted overlay, not a claim that the candidate already has a commit ID.

From that clone, the actual `scripts/setup_environment.py --directory .venv-candidate --dev --video`
created a fresh environment, enforced all Windows wheel hashes, passed pip check
and native NMS, then passed unittest's 187 tests and CLI acceptance.

| Check | Exit | Seconds |
|---|---:|---:|
| setup | 0 | 234.189 |
| acceptance | 0 | 125.250 |

`clean-checkout-overlay.json` records copied paths/hashes. All 35 app modules in
that clone and in the scanned production image match the final main working tree.
Later documentation/helper edits do not change that app-source equivalence.

The source-only verification clone also completed an actual production Docker
build: exit 0,
14.188 seconds. Its separate tag is
`coffee-ops-clean-engineering:20261112`; the original scanned production tag was
not overwritten. Cached build layers can be reused; fresh apt snapshot
reproducibility is not claimed. Exact command/output are in `clean-docker-check.json`
and `clean-docker-build.log`.

## Actual production image and isolation

Build commands: `docker build --target production -t coffee-ops-engineering:20261112 --progress plain .`
and `docker build --target video-test -t coffee-ops-engineering-video:20261112 --progress plain .`.
Successful exporter logs, image inspection and the actual runtime runs verify both artifacts.
The Docker context is default-deny and copies no local `var`, environment, Git,
reference binary, footage, credential, operational DB or real checkpoint.

Manifest/index digest: `sha256:6b1918bc03856f0fa2ea0d051507e90a712a92f8fb17cb98bd6d59ac0150e078`.
Config ID: `sha256:494ecc220c502cfaa3d1083f5396bed9d354280d1e514290ada3303320c6d00e`.
The saved archive manifest references that exact config blob. Its raw JSON scan,
CycloneDX SBOM and installed license inventory therefore identify the same artifact.
The image archive is 550,058,496 bytes. No signature/registry publication is claimed.
The follow-up `container-final-limits.json` additionally asserts actual Docker
HostConfig limits rather than relying only on launch arguments; it passed with
the same artifact and unchanged stop limit.

Actual runtime: UID 10001, read-only root, no ports, all eight negative egress probes
blocked and loopback usable. An untrained local YOLO architecture inferred offline
without pip/ensurepip. SIGTERM exited 0 in 0.489s under the unchanged
3-second stop limit. All runtime checks passed; this is not model accuracy.

| Image check | Exit | Seconds |
|---|---:|---:|
| final-image-inspect | 0 | 1.159 |
| final-image-config | 0 | 148.697 |
| final-container | 0 | 21.969 |
| final-image-licenses | 0 | 38.998 |
| final-image-save | 0 | 68.995 |
| final-image-scan | 0 | 40.663 |
| final-image-sbom | 0 | 0.172 |

Scan completion exit 0 is distinct from vulnerability policy: the high/critical
gate is **exit 1**, with 1 critical + 61 high OS matches. Python-package findings
are zero. [The security report](docs/audits/security-20261112.md) retains every
match and explains optional Transformers/development debt and scanner limits.
The actual local image-policy and missing-LICENSE commands both returned 1;
their exact commands and output are preserved in `release-gates.json`.

## Pretrained RT-DETR compatibility check

Two repeated frames from the existing public COCO-photo loop, with the cached
PekingU RT-DETRv2-R18 safetensors checkpoint, were used. The first app run returned
2 after its unchanged 60-second load deadline. A phase diagnostic loaded Torch in
6.9s, Transformer classes by 46.0s and the trusted local model/processor by 47.3s.
After concurrent installation/cleanup stopped, the exact configuration/source and
deadlines passed on repeat in 18.2s; only the synthetic DB/output paths differed.
The config SHA-256 remained `b560ff924b7b6587aea18e808b472cc83f7b5af1c2c22bc39184b3080387c26f`.

Both attempts and partial outputs remain. Warm repeat success does not prove
reliable cold starts. No event accuracy, real handover/preparation count, sustained
FPS or performance improvement follows from this two-frame public-image smoke.

## Cleanup, documentation and provenance

The first post-cleanup inventory was stopped while read-only after excessive
small-file buffer allocation/page faults and Git long-path warnings. Its counters
and log remain in `inventory-after-first-attempt.json` and `inventory-after.log`;
it produced no usable inventory and contributes no final counts. Reusable digest
buffers, four bounded read workers and per-command Git long-path support completed
the full hash pass. A final quiet checkpoint reused only unchanged size/mtime hash
witnesses and reported zero errors. This is audit-tool behavior, not an application
performance improvement or sustained model benchmark.

Removed 18,189 source-backed caches,
370,659,765 logical bytes; no matching source is
missing. One post-delete result log failed and was explicitly reconciled. See
[the complete manifest](CLEANUP_MANIFEST.md). All models/data/DBs/history remain.

Both original Git index byte hashes and staged-entry hashes match the starting
capture. Project HEAD remains 87dc561, on `audit/final-engineering-20261112` with
intentional unstaged candidate changes, no staged diff and no remote. Home HEAD
remains 35a344a. The prior audit's earlier home-index change remains unattributed;
this audit establishes its own end-to-end unchanged fingerprints.

Documentation links: PASS: 155 existing local targets; 43 Markdown files
Fragment anchors and external links are not comprehensively validated by the local checker.

## Raw artifact integrity

| Local evidence artifact | Bytes | SHA-256 |
|---|---:|---|
| `source-before.zip` | 1,146,030 | `5184206d61626c78341deac67722013ccee132fe6da92092d42bf19dab5f72a5` |
| `baseline.bundle` | 1,064,625 | `cd204d9edf58f80c30be3f8b63435edcfb582fb7297dede291ab11ccd0f4da17` |
| `inventory-before.json` | 34,474,769 | `96d38cdf14ca3268afe067e9387b1c5194c1f4c07d3fe8d05102db4bdd19d24e` |
| `runtime-image.tar` | 550,058,496 | `8ebda3a7fd5e2e6f9af64443bbcb18cd675e4867654682e30f95fb8c933f43b8` |
| `final-image-trivy.json` | 1,368,453 | `8dcca9c908c2b0e3776c4ec69cd030850ec87277e6fa36e53a2d47c509315f24` |
| `final-image-sbom.cdx.json` | 767,794 | `762b7e10b1f4cac133680d7f2b457a4dac64f3f3cbbd02ba7a5c1e7a934efeca` |
| `final-image-licenses.log` | 172,484 | `f4fc75c7560727d415a8e9e2526e07a158b2d5d4625b60988d12ca147b452f47` |
| `container-final.json` | 1,763 | `718c89c95960a7bd8169125b2f7a23175c4df5e581d403dec900cd8bf7812fa7` |
| `candidate-pip-audit.json` | 9,841 | `a661f6d530a2f7e7691412ab0b1d058abe6c5aea0eddaaac85f67b1d9beafef1` |
| `cleanup-summary.json` | 609 | `106dfaa525683dbe86fa893a228b47550b2cd6050ec53f88986c13a83ac622db` |
| `cache-cleanup-proposed.json` | 10,840,863 | `88cb1dd1d06aabe3d960442187bfcdf2e68132525c89d82c13344ebbda8c9ef8` |
| `cache-cleanup-record.jsonl` | 2,305,641 | `c5b1f9fd5831a00c44838580aa0a0312258ee1ddfb1c29cebf25922f3fa74ead` |
| `cache-cleanup-resumed.jsonl` | 10,146,312 | `f5cb50e1b4d5bacbe590aabdd2912fd9d5f63885ca7736974fa12ea15f918293` |
| `cache-cleanup-partial-reconciliation.json` | 1,314 | `2fe768a4d14b7a9e08958e6d1e81bbea42b7473a1d46bc53c192cd3451151e91` |
| `rtdetr-smoke-check.json` | 1,370 | `308dce08369365076570897bc5c68486d9b917087bbb48970ec8c4c870f656a7` |
| `rtdetr-smoke-retry-check.json` | 1,763 | `092a19ac1f981a3a26d8dbd914962f48f409f2268528d09f29e76af30bc792ce` |
| `inventory-handoff.json` | 55,247,904 | `4de106b9b6198eec9c682186180e6b62b06b0610599adae499b8e3adf876cfb6` |
| `container-final-limits.json` | 2,067 | `be797a11ee37dc89b527a3a900f505b00eb29ff7572c664fad8f953b7b484fd7` |
| `release-gates.json` | 1,068 | `5211e45421aebcdce0d3fc8d5da5b2143ee75d774a9750f80938c608be571ff8` |
| `clean-docker-check.json` | 3,765 | `f18a83bc1b8d844718cfea3f3ade78f0e9b60fb4117fff9fe28849aaeb80fa75` |
| `doc-links-confirmed.json` | 178 | `aec32c555fd77d2f33bb54c940ed0bc50db75000df11f66adbf13941f20b0c42` |

Command arrays, exit codes and timing values are in `baseline-checks.json`,
`windows-candidate-checks.json`, `final-windows/checks.json`,
`linux-run2/quality/checks.json`, `clean-windows-checks.json`,
`final-image-checks.json` and the two RT-DETR check JSON files. Tool-created
temporary containers are removed by name plus UUID label, including recovery
after a Docker-client timeout. No unrelated container was stopped or pruned.
