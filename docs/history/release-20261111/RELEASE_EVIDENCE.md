> Historical report from the 2026-11-11 audit, finalized 2026-11-12. Superseded by [the current audit](../../../FINAL_ENGINEERING_AUDIT.md). Earlier findings and failures are preserved; links are relocated.

# Release evidence : 2026-11-12

Evidence was collected on 2026-11-11; this handoff was finalized on 2026-11-12. Saved commands, timestamps and digests retain their original dates. No cloud deployment or security clearance is implied.

All commands below run from the nested project root containing `coffee_ops` and this
file. Local raw artifacts are in `var/release-audit-20261111/`; that directory is ignored,
private by default and not required for a clean source build. Results and immutable
hashes are embedded here so this report does not rely on unversioned local claims.
Use new output paths when reproducing; existing evidence is never overwritten.

## Baseline, regression and final tests

| Environment / command | Status | Result |
|---|---|---|
| Baseline `.venv/Scripts/python.exe -B -m unittest discover -s tests -v` | VERIFIED | 182 run; 169 passed, 13 optional skips; 20.672 s |
| Baseline `.venv-notebook/Scripts/python.exe -B -m unittest discover -s tests -v` | VERIFIED | 182 passed, no skips; 39.311 s |
| New API tests before fix | FAILED (expected red) | Oversized cursor raised OverflowError / RemoteDisconnected; unauthenticated minimal probe returned 401. 7 run, 1 error and 1 failure. |
| `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_api.py -v` after fix | VERIFIED | 7 passed; 0.497 s |
| `.venv/Scripts/python.exe -B scripts/verify_mvp.py --output var/release-audit-20261111/windows-acceptance` | VERIFIED | Complete synthetic CLI acceptance passed; included 184 tests, 171 passed, 13 skips; tests 64.243 s, harness 90.482 s |
| `.venv-notebook/Scripts/python.exe -B -m unittest discover -s tests -v` after fix | VERIFIED | 184 passed, no skips; tests 126.880 s |
| `.venv-notebook/Scripts/python.exe -B scripts/verify_training_notebook.py --output var/release-audit-20261111/notebook-default.json` | VERIFIED | Notebook schema and actual default kernel execution passed, no download/training enabled |
| Both Windows interpreters: `-B -m pip check` | VERIFIED | No broken requirements |
| Linux CPU image, `python -m unittest discover -s tests -v` | VERIFIED | 184 run; 171 passed, 13 skips; 17.496 s |
| Linux video image, same command | VERIFIED | All 184 passed, no skips; 44.888 s |
| Linux CPU `python scripts/verify_mvp.py --output /audit/linux-acceptance` | VERIFIED | Complete acceptance passed; included 184 tests, 13 skips, 20.286 s; harness 48.976 s |
| Linux runtime `python -m coffee_ops doctor` | VERIFIED | Torch 2.9.0+cpu / TorchVision 0.24.0+cpu native NMS passed; no CUDA |
| Hosted GitHub Windows/Ubuntu execution | BLOCKED | Local equivalents observed only; no push or remote workflow execution |
| Real browser/frontend workflows | NOT TESTED | No frontend exists; loopback requests are real HTTP tests, not browser acceptance |
| Trained cafe inference / live RTSP / production capacity | NOT TESTED | No independent cafe validation or sustained hardware trial performed |

The 13 CPU skips are four review-label tests plus one streaming-COCO test requiring
ijson, and eight native PyAV video-review tests. The video environments run these tests with their dependencies present. Skips
are dependency/profile differences, not platform exemptions. Linux uses Debian in
Docker Desktop on this Windows laptop, CPU-only; it does not establish bare-metal
Linux, hosted-runner, CUDA, real-camera or browser behavior. Final Windows runs overlapped
image building and are functional results, not comparative performance measurements.

Acceptance verifies actual decode/replay, synthetic supplied detections, POS paid-unit
accounting, reconciliation, reports, event scoring, traffic review revision, repeat-run
idempotence and expected failures for missing files/models. Native detector tests use
locally generated untrained weights: compatibility evidence only. No acceptance threshold,
existing assertion or timeout was relaxed.

## Reproduce Linux builds, isolation and source integrity

```powershell
docker build --target runtime --tag coffee-ops-runtime-audit:20261111 .
docker build --target test --tag coffee-ops-cpu-audit:20261111 .
docker build --target video-test --tag coffee-ops-video-audit:20261111 .
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges --cpus 2 --memory 3g coffee-ops-cpu-audit:20261111
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges --cpus 2 --memory 3g coffee-ops-video-audit:20261111
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges coffee-ops-cpu-audit:20261111 python scripts/verify_egress.py
docker run --rm --network none coffee-ops-runtime-audit:20261111 python -m coffee_ops doctor
docker image inspect coffee-ops-runtime-audit:20261111
```

The observed video verification image was built before the benchmark helper was added;
it contains the fixed application and all 184 tests. The runtime/test images were then
built from the updated source. Performance uses the current helper mounted read-only;
no private dependencies/data are supplied to build or unit/native tests.

The egress test observed only `lo`, confirmed a local connection, and got errno 101
(network unreachable) for eight TCP/UDP probes to public IPv4, private IPv4, metadata and
public IPv6 destinations. Runtime containers used no network, no capabilities, no-new-privileges
and UID/GID 10001. The build/scanner download phases were explicitly separate and networked.
Health tests confirm that an unauthenticated `/healthz` response contains only status,
opens no DB, disables caching and does not grant private health/status access.

Docker context transferred approximately 485 KB in the first clean build; virtualenvs,
model caches, operational data and the source snapshot were excluded. CPU and video
tests ran inside images without source/data mounts. Synthetic acceptance used only an
output bind mount; it did not read a laptop ledger, footage or checkpoint.

A separate project-local Git baseline was subsequently created from the captured snapshot; enclosing-index fingerprints matched at initialization, with a later change recorded below. A clean local clone built and ran the full CPU test suite without private local inputs, as recorded below. The original P1 commit/story provenance and byte-identical future dependency resolution remain BLOCKED/FAILED respectively. CI records tracked source
hashes, checks for source mutation, builds/tests Docker, inventories licenses and fails
on Grype high-or-critical findings. No suppressions or continue-on-error security gate.
The source-license gate intentionally fails until an owner selects a license.

## Controlled diagnostics and limitations

The comparison baseline is the pre-edit source ZIP, not the unavailable P1 commit.
The completed comparison uses the same Windows `.venv` interpreter/dependency set and
unchanged host hardware/process allocation for both versions. Workload: 200 immutable events, 184,320-byte SQLite
DB, ten sequential warm-up requests, then 80 requests at concurrency four; four 50-row
event pages to one business report. No model, frontend, proxy or external DB is involved.

Six Windows trials interleave baseline/candidate in A-B-B-A-A-B order, three per version.
The first four Windows trials ran before the access/session change and the last two afterward; host-state continuity is not established. The large timing spread makes the Windows comparison inconclusive. This is a diagnostic, not
dedicated-host certification. Database hashes must agree before comparing trials.

The first attempts at the twelve Linux 0.1/0.5 CPU trials were **BLOCKED**; the completed resumed trials are recorded below. After successful Linux tests,
acceptance and image export, Grype returned `unexpected EOF` (exit 125). A scanner retry
limited to 2 CPUs / 2 GiB returned `Docker Desktop is unable to start` (exit 1). All twelve quota
commands failed before collecting measurements. No Docker restart, unrelated
container cleanup or resource-policy change was attempted. The cause is undetermined;
this is not evidence of a Grype vulnerability or a measured out-of-memory failure.

```powershell
.\.venv\Scripts\python.exe -B scripts/benchmark_api.py --requests 80 --concurrency 4
# Linux trial template: use the SAME image, helper, source and baseline mounts for all trials.
docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,nosuid,nodev,size=256m --cpus 0.1 --memory 1g coffee-ops-cpu-audit:20261111 python scripts/benchmark_api.py --requests 80 --concurrency 4
```

To reproduce the baseline, extract the recorded source snapshot to a new directory,
mount it read-only at `/baseline`, mount the current `scripts/` at `/checks`, and invoke
`python /checks/benchmark_api.py --source-root /baseline --requests 80 --concurrency 4`.
Use `--source-root /app` for the candidate. Repeat with CPU 0.5 in the planned interleaved
order once the engine is repaired. Failed quota commands are retained in `performance.json`;
completed Windows measurements and commands are in `windows-performance.json`.
For separate instrumentation, run `--profile --requests 80 --concurrency 1`; its timings
are not used in the uninstrumented comparison.

p50/p95/p99 use nearest-rank request latencies, throughput includes errors, and errors
are reported rather than discarded. Eighty requests per trial are insufficient for a
stable tail/SLA claim. Thread CPU measures request handlers; process CPU and sampled RSS
include the in-process client/harness. SQLite shares that process, so separate DB-server
CPU/RSS do not exist; file size is reported. No filesystem I/O counter or whole hosting
resource claim is inferred. There is no approved SLO or job-save workload to grade.

Detailed measurement, scanner and integrity tables follow. They are generated from the
retained raw artifacts; unresolved fields remain explicitly unverified.

## Completed Windows comparison : VERIFIED diagnostic

| Trial | Version | p50 ms | p95 ms | p99 ms | Requests/s | Error rate | Handler CPU mean ms | Peak RSS MiB |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | baseline | 32.941 | 493.886 | 980.835 | 31.50 | 0.000 | 11.574 | 33.32 |
| 2 | candidate | 121.793 | 669.549 | 1459.384 | 21.21 | 0.000 | 13.696 | 33.08 |
| 3 | candidate | 60.558 | 201.744 | 302.825 | 45.43 | 0.000 | 38.002 | 33.11 |
| 4 | baseline | 70.938 | 330.915 | 1051.597 | 31.69 | 0.000 | 17.940 | 33.48 |
| 5 | baseline | 5.670 | 17.417 | 18.634 | 513.15 | 0.000 | 5.208 | 33.23 |
| 6 | candidate | 6.083 | 22.178 | 28.440 | 457.40 | 0.000 | 4.244 | 33.07 |

Every trial used the same SQLite SHA-256 `0ee3ba768a0a057ec9843504c87983155d9bd55799d8d5d67977519f437d4fe0`, 184,320 bytes. Both versions returned all expected event/report results. Process CPU seconds and exact source hashes are in each raw row. Windows thread CPU is quantized; do not infer per-handler precision from the displayed decimals.

**No performance improvement is established.** These are small synthetic read workloads with scheduling noise; security/authentication remains enabled in both sources. The cursor fix is an error-boundary correction, not an optimization. The resumed CPU 0.1/0.5 diagnostic is below; filesystem I/O counters, real detector capacity and approved hosting SLO remain BLOCKED/NOT TESTED.

### Separate instrumented process profile

Instrumented 80-request/concurrency-one candidate run; not included in the comparison. The aggregate contains API, SQLite, serialization and HTTP-client frames. It is a mixed-thread process diagnostic, not isolated request-only CPU attribution. There is no frontend/proxy layer or separate DB process.

```text
183126 function calls (183125 primitive calls) in 0.232 seconds

   Ordered by: cumulative time
   List reduced from 306 to 20 due to restriction <20>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     6996    0.070    0.000    0.070    0.000 {method 'execute' of 'sqlite3.Connection' objects}
       79    0.001    0.000    0.065    0.001 C:\Users\aymen\Desktop\computer-vision-main\computer-vision-main\coffee_ops\storage.py:27(__init__)
       17    0.008    0.000    0.047    0.003 C:\Users\aymen\Desktop\computer-vision-main\computer-vision-main\coffee_ops\business_reporting.py:33(business_report)
     6657    0.005    0.000    0.028    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\json\__init__.py:299(loads)
       64    0.004    0.000    0.027    0.000 C:\Users\aymen\Desktop\computer-vision-main\computer-vision-main\coffee_ops\storage.py:188(event_page)
       81    0.001    0.000    0.026    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\http\client.py:635(_safe_read)
     6600    0.004    0.000    0.025    0.000 C:\Users\aymen\Desktop\computer-vision-main\computer-vision-main\coffee_ops\storage.py:242(latest)
     3451    0.007    0.000    0.023    0.000 C:\Users\aymen\Desktop\computer-vision-main\computer-vision-main\coffee_ops\storage.py:249(between)
     6657    0.007    0.000    0.022    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\json\decoder.py:340(decode)
       27    0.007    0.000    0.015    0.001 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\http\client.py:463(read)
       81    0.000    0.000    0.013    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\pathlib\_local.py:664(resolve)
       81    0.000    0.000    0.013    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\http\client.py:245(parse_headers)
       81    0.001    0.000    0.012    0.000 <frozen ntpath>:702(realpath)
       81    0.000    0.000    0.012    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\http\client.py:231(_parse_header_lines)
       81    0.000    0.000    0.012    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\email\parser.py:56(parsestr)
       81    0.001    0.000    0.011    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\email\parser.py:41(parse)
      162    0.011    0.000    0.011    0.000 {built-in method nt._getfinalpathname}
       81    0.000    0.000    0.010    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\http\client.py:425(_close_conn)
        4    0.000    0.000    0.010    0.003 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\http\client.py:291(_read_status)
       55    0.000    0.000    0.009    0.000 C:\Users\aymen\AppData\Local\Programs\Python\Python313\Lib\concurrent\futures\thread.py:54(run)
```

### Existing synthetic stress reproduced

| Orders | Events | Import s | Reconcile s | Repeat s | Allocations |
|---:|---:|---:|---:|---:|---:|
| 1000 | 100 | 0.3522 | 0.0838 | 0.0030 | 100 |
| 10000 | 1000 | 3.8886 | 0.5146 | 0.0104 | 1000 |

Allocation/idempotence assertions passed. Tracemalloc affects reconciliation timings and measures Python allocations only. This is not a controlled P1 before/after ledger comparison.

| Tracking scenario | IDF1 | Identity switches |
|---|---:|---:|
| smooth_two_person_crossing | 1.0 | 0 |
| temporary_occlusion_within_expiry | 1.0 | 0 |
| occlusion_beyond_expiry | 0.5 | 1 |
| movement_beyond_distance_gate | 0.3333333333333333 | 2 |

Long-occlusion and fast-motion identity failures remain visible rather than optimized speculatively. Expiry workload: 5000 frames; max 3 active tracks.

| Event scenario | Sample every | TP | FP | FN |
|---|---:|---:|---:|---:|
| short_visit | 1 | 2 | 0 | 0 |
| short_visit | 2 | 0 | 0 | 2 |
| short_visit | 4 | 0 | 0 | 2 |
| simultaneous | 1 | 4 | 0 | 0 |
| simultaneous | 2 | 0 | 0 | 4 |
| simultaneous | 4 | 0 | 0 | 4 |
| standing | 1 | 0 | 0 | 0 |
| standing | 2 | 0 | 0 | 0 |
| standing | 4 | 0 | 0 | 0 |
| boundary_jitter | 1 | 0 | 0 | 0 |
| boundary_jitter | 2 | 0 | 0 | 0 |
| boundary_jitter | 4 | 0 | 0 | 0 |

Synthetic fixture detections establish event/sampling behavior, not cafe model accuracy. Missed short transitions remain a known acceptance limitation.

## Recovery, adversarial and CI checks

**VERIFIED:** 12 additional real HTTP cases covered auth, probe query isolation, maximum/oversized cursors, duplicate camera parameters, SQL-looking input, cross-origin requests, path traversal, long URI, rejected POST and following-request recovery. No test token appeared in captured stderr/response bodies. This proves only these local error/log boundaries.

**VERIFIED local backup/restore:** synthetic main ledger had two records after a post-backup append; backup and restored copy each retained one. All three quick_check results were ok; restored copy opened through the supported read-only store. This is not a Render restore drill or a measured RPO/RTO.

**VERIFIED image payload check:** 39 runtime source/config/schema/requirements files compared against exported layer bytes; missing []; mismatched [].

**VERIFIED static workflow:** YAML parses; four OS/profile combinations, contents-read permissions and vendor-ref-pinned action commits checked. No hosted execution or complete dependency-license policy validation claimed.

## Immutable artifacts and payload manifest

Runtime image (Docker inspect Id/RepoDigest): `sha256:8aa08cddd5d6edc9d8f13a011711ff434a1880cb36a0e04a0263434c2e1dd2d8`.
Base Python image: `sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90`.
Grype 0.121.3 tool image: `sha256:13113eeceab017260370cf540e1d25442c59665fd07d1b09b66d63bb0c282887`.

Canonical source-manifest SHA-256: `70b57281e168f6ca68a47fe829ff601a6d3bbed1235192d2a053f90c1999d6ca` (JSON sorted keys, compact separators, UTF-8; excludes these four handoff documents to avoid self-referential hashes). Raw source/artifact manifests are retained locally. No signature, registry upload or verified project commit is implied.

| Raw artifact in audit directory | Bytes | SHA-256 |
|---|---:|---|
| before-source.zip | 1,105,871 | `d9b42bd0703be6c75519cf358f74bf56b3b28c59c101d9f4ddc6bd7b0d33424c` |
| before-manifest.json | 16,465 | `e156168af0dcf160126573fc1a4bafff77533c266818a173da3dc79d80b6ce7d` |
| windows-cpu-inventory.json | 170,687 | `151ee6f452ec0e0716f31ccbbbc569b98097b455ad65dc7011188482d42058f4` |
| windows-osv.json | 193,822 | `23369e0a7aa5f6312fa7f328091288e97b5fdf7c7b3fd829543ed407c88d8fc2` |
| local-checks.json | 1,818 | `7a952a7c40a83f945726204e23c64eaeec641a641d4a9e4f4a42383dd84596b4` |
| linux-checks.json | 5,447 | `4df404168ab1cd1e74fbd59aecca470f7c25d61476ec729fcc072ed5a169e589` |
| runtime-image.tar | 536,346,624 | `e884b5dc4a603b5816b932b4f0fd35aecc4e619f08a85e379b453a59ca09fd83` |
| runtime-inspect.log | 3,361 | `1405ce8484609ca73b3d3e010cc16ef5b9629337e9752a5e4ee2c0a6f76ebee0` |
| scanner-version.log | 303 | `935e65af4917a7d81fe2df90be1c1fa5602d3c5ef28ebf82fb558f63144fcceb` |
| grype-runtime.log | 95 | `99cc633fb9e0763a2959d185b09a7712f89a381ea1e1711f20cc2b1b9143859a` |
| grype-retry-result.json | 891 | `b35aacff336711ccc2235780aec46ad620cad218532ceed09dc57e709550d88c` |
| grype-retry.log | 62 | `5542eab2c643ea8936a2f2669330737bcbd26283aab55cf65021009ebf049c9a` |
| windows-performance.json | 10,439 | `151b075a55a654d3a4c0eb8af9007d20f2d52c07454f3f38899ea459bdd1c431` |
| windows-api-profile.log | 4,165 | `56f2e693837144548b2f5f401ca656178a17bd9e9184d27a59b534602665b0ec` |
| windows-ledger-stress.json | 2,376 | `f70f8b9cf23b7d6e63c38084787a5e7fa096e0d9c1f928c366a8b60e1fb82332` |
| windows-event-sampling.json | 44,344 | `50e27c2a0b8ca845dca3fd111c4573777fc8aa12849beb20ddc14172b2f323f2` |
| retention.json | 3,866 | `7d0a96df9fafa15e03cb6ddf51faa323677315b2c1b11bc0aa5a3617637d6f1d` |
| recovery.json | 258 | `a1f5d41443e746e46430bed33b289af8c6d89a07cbcf6a908ffdf87753918c1c` |
| adversarial.json | 1,629 | `3d375bb55dafc46c378e2909c80a4b36f68c3f12e436919d38d0e542002b73d9` |
| image-source-check.json | 4,014 | `4b68d3bb5e35538bc15b3dc156078c929952ed6633a73bbdbf0640793bccfa35` |
| workflow-validation.json | 465 | `d6a05aeca4a698c1710892d82e04a0e45713375609b90a4af866f2485d0f6676` |
| final-source-manifest.json | 16,836 | `e5448252933dae253bb73e34fc5230552dbe503111568824b1e207682447f002` |
| preservation-check.json | 354 | `5372978865c0a57eb1dbd69a18f408aa10cd7db617058ef9e80a2ad0b900e990` |

Preservation check: 146 original files unchanged, five explicitly changed, zero missing. The source snapshot preserves every original version of those five files.

### Source payload hashes

Includes application, tests, dependency manifests, CI/build inputs, notebook and reproduction scripts. Historical unchanged reference/evidence files are also in the retained full manifest.

| Source input | SHA-256 |
|---|---|
| .dockerignore | `20d86e7e1c078c829b2cdc76191bc364d07e0df1497a000065b3e7f414bfae7b` |
| .github/workflows/tests.yml | `845f6ba33dc533ef5bf04775cd865e0e730d735fc933c42d5fe3aadcc1cff96d` |
| .gitignore | `80fda0bad39fd186bdf11f54de80a12e9e57a6091fa345851f18fafd9bf84313` |
| coffee_ops/__init__.py | `6aef8f11cf9d1feadb75cf3d07003c09ca7079ba99d5bed041be8d3053be601d` |
| coffee_ops/__main__.py | `307299fda7b77d22c64cb51430ec75e5f59d78e9c948786afb3b2544fe45e4b7` |
| coffee_ops/alerts.py | `03db4aebbaeceaf5f0a5616a0b7690290a2f25b9f30ac3b3ab4cb60f0814161a` |
| coffee_ops/api.py | `431695e65e0c7b974255f898012e28e230dd359dcbf0d06661b69352e14b2121` |
| coffee_ops/business_reporting.py | `8d87e1fb9ba3217e869da3f7ee2d9a94043cc63e2f91f3e0d0cd77a958aa1fb9` |
| coffee_ops/cli.py | `a33f7bc96b34641f68372e76cd365b5113947321dae66101983e0de68a25b85d` |
| coffee_ops/config.py | `64fc5abd377257afb76cd9bcee242e56aa11ebba0050e21c5533202efade66d6` |
| coffee_ops/dataset.py | `a389e04375882943794fddcba01272e1c7f417a9d83bd71584e0717312449272` |
| coffee_ops/demo.py | `4c921b0936ac18f13356759c4f745d04d0c548837b7537843e563651e94d260d` |
| coffee_ops/detector.py | `882485ea399258af9cfe7609f49ec25b200b0d8a8bb0abf600bc4ee60105ef3f` |
| coffee_ops/evaluation.py | `088e146e5762a76fed08f18047567462c45e52d4a4429577e1dc696b3d72f548` |
| coffee_ops/event_engine.py | `fd82604b4b092187919b53726bb3983bd909f8b878300ec14145805055d69346` |
| coffee_ops/event_evaluation.py | `89b81f60f90f27498ac4ec4f06cf9c0226cd314a5fe953a0ffec9140f6bff990` |
| coffee_ops/exports.py | `36c7f1749fdb62868da227a12ff098bff34050817e61d22c126d25e5e68f5043` |
| coffee_ops/health.py | `1a03cb66fa8e41eecca0a64ff6ae41041e36778629369963158ab760780171f4` |
| coffee_ops/inventory.py | `fa9953b6f918367d93380961fbfdaa09f94690c21f2b93296a1206f55ced7a53` |
| coffee_ops/mlops.py | `4b2f0c9a1a1d17360e13ee9a3b211ba3e21966fbda545d091b0f7ab7db1457c1` |
| coffee_ops/pipeline.py | `9aad872549103fdcd000b3907e249a77734ee74b76a2d00c28c0e41ccf105763` |
| coffee_ops/pos_adapter.py | `6e046b8b5c3db450f5dd8d233180ab3c0d8eef74b1d80571450d1d2edd5d7840` |
| coffee_ops/product_evidence.py | `38f2878b797384ee75e63d420a0b5dc2221226e4b5ec23105b6b65ab9b8930ec` |
| coffee_ops/reconciliation.py | `3e4794e10917e1b3659f9fb87885bb0aefaccfaa1e0fa186990ccd4b2d8abc43` |
| coffee_ops/reporting.py | `0b6b8c1f4603768947b2b6ce2ff158dfe20409c019c565a22dfd920208872d5b` |
| coffee_ops/resources.py | `512d5038f7827005c509c287df77fdf07ea338c071dddabfd5d0dfbf7e7189c2` |
| coffee_ops/review_exports.py | `a490c05f6e6bb4a8924374d120557a3a4d37c44947a3e6598c01f14c8851031d` |
| coffee_ops/review_labels.py | `56e56f08172a7d4d7141972d90b0175af8aa33fe9d6d90120dba8bee5ba1073a` |
| coffee_ops/runtime.py | `86d7c3fe443c3c02ee0989305d50cea665a63299f2a25a9076ec2b1066583bb8` |
| coffee_ops/schema.py | `1218cafc80ae39c1239cf134d7eb0eefaad3f04b8026de97c1babb069ffc0d7a` |
| coffee_ops/storage.py | `57b1791d7298af200b02aa56d04bdeedf731a32f6ab535b44d7503dc876de3d8` |
| coffee_ops/tracker.py | `2fb52e17a473bf3cb9ad2e9349818debb90b5b4c0c8cc7794ad0e4f98e98dac4` |
| coffee_ops/traffic.py | `4d647237b1760c8646d7903daec3372556d1b4f24b9059e0745acc5f7aacd2d1` |
| coffee_ops/video_input.py | `a8bc1d91218b6fa6c2f56b64d77ed4671e8bcbec7ff7f335b14ff61decb1cabb` |
| coffee_ops/video_io.py | `4973fb27ea6eb941d4fc73475aa90c7c0d51a80b5f8bf70ff1bfd5f94061da80` |
| coffee_ops/video_overlay.py | `99c45376a9d1fddeb630da300e162584a0a7adc4079d88722563afe4706d9c35` |
| coffee_ops/video_review.py | `107294bb521d2bcbda54f74095748a75cc5df4928b98879dab47f7571998292e` |
| coffee_ops/zones.py | `2ddabc0a78c2d848649cd0b206ec6615371d8a1b44bf1a715b43428888c1e855` |
| config/example.json | `e92add4450ee742726ff118f4d1c866da350548cac8c85680f82094331d16cc3` |
| Dockerfile | `ac4edd3cc7bfdc18e4394a6ee4c3563a6fec695e1be7724dbfc040b1fb34b32e` |
| models/metadata.example.json | `df54eddd9694015a26442f40e513e6bd6bd51de9a0cd67c83911658c0e5e7721` |
| notebooks/cafe_model_benchmark.ipynb | `b96e09211c359999f826f299e851572117d34e34266b7aa26cce82dcdac6552b` |
| notebooks/README.md | `699389061573567e7863ee69d609fa8c2ba9a69e2f222f050f70f0ed575b07d6` |
| requirements-benchmark.txt | `37cc6b77b41edcea2abfc7cc42d8722b755b8a3bc4fe704ca39cc3d418262837` |
| requirements-notebook.txt | `403df1b27e55fa1e16f08f79c16068cc0a88086c0f9f206d69a3983795584caa` |
| requirements-video.txt | `eaddd9ef728e007c5c5f51d0d07b95da4b3ff23530e390b9c0e21d7287e61b27` |
| requirements.txt | `b6cb2c1410d1d25e5af9c7afe1f05f658e7ca688c486f5e6fa71aefb098153d2` |
| schemas/event_annotations.v1.schema.json | `97669a345698b43ec6b53e1dbfa006a31ac6462a7438f62c02f7925eca7ba360` |
| scripts/benchmark_api.py | `f01753fb73fbd46c42b6aa5dad71af0cb7606e3a518f3a629dd7b3c0469b77a1` |
| scripts/benchmark_events.py | `0cf36b8e739129ce1fd62696dabacb9e03c2989a945677fea96801e33653ff3b` |
| scripts/benchmark_models.py | `5bd5f1cd53f2ad48671517a89596d62c5997bb78ab1b97d3988691696599c826` |
| scripts/benchmark_mvp.py | `6c0ffd11de0ac9859812ff4eee297ba1f1b84329e6f7ca961d19e2c94179e51a` |
| scripts/benchmark_suite.py | `2cbd150a83315c551eacb0011d641945cf91ad0ab2b7c6b05d62b4eaf4de1697` |
| scripts/verify_egress.py | `711f515be0fbad2bc2c8f91d4466e38168981af84aef3dba2ab0a15e82100761` |
| scripts/verify_mvp.py | `536102a5579a0c93ebafc8882592b623509a7bbc0e341d120d8222eb397ef9c5` |
| scripts/verify_training_notebook.py | `a323f3ca639ae7055611153fa137128643b455faeb03422433f269d501a565d8` |
| scripts/verify_video_prototype.py | `3a3398f1f6c3297bee4f1ab304cdca2aabfae6396770c007f05a6bd7ea2b776c` |
| tests/test_api.py | `ac5b93c5d59c930ae443c1f049734d2e01112f491d636bb81fbbd2d03020aff9` |
| tests/test_business_reporting.py | `eb3f9d4695ed63ad8dd57fb82d89186e562bacf79ece45df18886e5cb6379d76` |
| tests/test_detector_backend.py | `db8374aac3bc78fdccf35e70997443861c29352b9f5e4ed2472bdd38eaf7e099` |
| tests/test_evaluation_and_data.py | `41f9b3825c20f3f3fb61f0b25b3c06e47311d1170c797a59d7d364180e678493` |
| tests/test_event_scoring.py | `9305549fa2fb3218e2e7e73906757ff4cc8b08e72eba2d0b56c07c139bc267bb` |
| tests/test_failure_boundaries.py | `3a63b279f9abce6734b1952272c9df677a2ad0b7ff9d500d45f7859660651fb7` |
| tests/test_model_benchmark.py | `0072d945cfdae8a9c65c5dff3de300481c8e79803c63269ed23b4ff65ef4179c` |
| tests/test_operations.py | `0a447aae32e54be911806185cbe5aa25aea62548dfe7bd42981af18e41c8c58f` |
| tests/test_product_evidence.py | `6a1092b8a37401f66f279eab59263f587ec9fa22aff16539b8da6fa7b44918a7` |
| tests/test_review_labels.py | `1a76f54fabd2d903ca414c302aa38ccd58a3ae74cec8d64173b8a8b1d9d915c8` |
| tests/test_storage_resilience.py | `49b692183a3a335255f0b5964461cb240e6197d58b5241fadc81f97bd1a680c0` |
| tests/test_traffic.py | `64840dfde928859fb6b13487016036df32efe2a63ea77180aa4aeecd46dff796` |
| tests/test_training_notebook.py | `05106295c2ef1e35b17c59785a49a7247e90e61c763618ba7ce2c858af464a21` |
| tests/test_video_integration.py | `5a6f9cbca7b715e17302e23903511beb4aee7f8bfd005bd50c0c453d93e5bdcb` |
| tests/test_video_review.py | `43d8cb0c51753239b08cf9dd287d6ca7da84dd7975a4f2b84429c25dc561bf9e` |

## Local Git provenance established after access change

Original home repository index SHA-256 before and after: `ea7531fb92642851b122453acefa53e341f755f236146569866d5fc1d4281cdd`. The project was wholly untracked there. No project command was issued to stage or rewrite the home index; its later fingerprint changed, as recorded below. A separate project `.git` was initialized on `audit/staging-readiness-20261111`; pre-edit snapshot baseline commit `0a39057885047038c2ba5829426d397ec73a9fb5`, implementation commit `9b4b98514fc698fd6432249f5545a754025bde3d`. Both commits use an explicit Local Audit bot identity, remain local, and do not claim the supplied P1 ancestry. Final handoff documentation is reviewed separately from the implementation commit.

## Instrumentation challenge and correction

The first profile straddled the warm-up boundary and included client frames. The benchmark helper now waits for all handler instrumentation to finish before clearing warm-up samples and after receiving measured responses; profile mode is restricted to concurrency one. A fresh smoke produced exactly 80 handler samples for 80 successful requests. The original Windows timing/profile artifacts are retained and are not substituted for the corrected Linux comparison. cProfile still contains client frames on this interpreter, so no per-layer latency percentage is inferred from it. SQLite connection setup, repeated per-event review lookups and JSON reads appear in the aggregate; no query optimization is claimed without a comparable acceptance target.

## Optional Windows video environment difference

The tested `.venv-notebook` uses Python 3.13.2, Torch 2.9.0+cu128 / TorchVision 0.24.0+cu128 and Ultralytics 8.4.204, plus PyAV 19.0.2, ijson 3.6.0 and Transformers 4.57.6. The operational Windows/Linux CPU stack uses Torch 2.9.0+cpu / TorchVision 0.24.0+cpu and Ultralytics 8.3.163. Optional Linux video requirements were installed over that CPU stack. Both video suites ran all 184 tests, but this is not a byte-identical dependency comparison across platforms or a real CUDA inference trial. Optional research/video environments were not fully vulnerability-triaged. Raw metadata is in windows-video-environment.json.

## Clean checkout verification after resumption

**VERIFIED:** local clone of implementation commit `9b4b98514fc698fd6432249f5545a754025bde3d`, empty Git status, no var directory or local environment. Docker built from that checkout and ran the full CPU suite offline: Ran 184 tests in 18.396s. Thirteen optional skips remain as documented; no acceptance timeout was changed. Windows Git newline conversion can change text-file bytes; the clean-checkout artifact is not claimed byte-identical to the earlier working-directory image. The earlier runtime tar still has its separately verified 39-file payload manifest.


## Completed interleaved Linux CPU diagnostic

**VERIFIED execution, no release SLO conclusion.** Three trials for each source/quota combination; exact commands and per-request summaries in resumed/quota-results-verified.json; the original twelve attempts remain in resumed/quota-results.json. Every container used the same CPU verification image, memory 1 GiB, read-only root, temporary filesystem 256 MiB, no network, ten warm-ups, 80 requests and concurrency four. The current synchronized helper was mounted read-only for both versions.

| Trial | CPU quota | Source | p50 ms | p95 ms | p99 ms | Requests/s | Error rate | CPU seconds (process) | RSS MiB |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.5 | candidate | 109.254 | 473.703 | 623.023 | 26.78 | 0.000 | 1.4900 | 36.02 |
| 3 | 0.1 | candidate | 294.647 | 999.558 | 2400.720 | 9.41 | 0.000 | 0.8400 | 36.70 |
| 4 | 0.5 | baseline | 114.506 | 485.238 | 601.010 | 23.79 | 0.000 | 1.5700 | 35.52 |
| 5 | 0.5 | baseline | 104.668 | 501.457 | 585.291 | 26.65 | 0.000 | 1.4900 | 36.30 |
| 6 | 0.1 | candidate | 297.059 | 1099.804 | 2400.890 | 9.41 | 0.000 | 0.8300 | 36.11 |
| 7 | 0.5 | candidate | 103.096 | 497.378 | 716.918 | 24.98 | 0.000 | 1.6000 | 36.07 |
| 8 | 0.1 | baseline | 300.979 | 1398.001 | 1765.863 | 9.40 | 0.000 | 0.8500 | 35.77 |
| 9 | 0.1 | candidate | 300.960 | 1196.026 | 2305.393 | 9.53 | 0.000 | 0.8000 | 36.67 |
| 10 | 0.5 | baseline | 104.698 | 490.325 | 609.510 | 28.73 | 0.000 | 1.3400 | 36.55 |
| 11 | 0.1 | baseline | 299.050 | 804.163 | 1899.331 | 11.11 | 0.000 | 0.7200 | 35.68 |
| 12 | 0.5 | candidate | 98.528 | 497.095 | 616.488 | 30.05 | 0.000 | 1.2600 | 36.48 |
| 13 | 0.1 | baseline | 293.988 | 796.950 | 2199.524 | 11.60 | 0.000 | 0.6600 | 36.07 |

Each trial recorded exactly 80 handler samples. Kernel cgroup cpu.max was checked against the requested 0.1/0.5 quota and memory.max against 1,073,741,824 bytes. Effective cpuset is retained in each row. Database SHA-256: `49a9f9fe9c2a7fbf90193b46eb7aec25b99b2bdd7ceb4771e94db4cc9af57cfa`; bytes 184320. p99 has only 80 observations per trial; this is diagnostic tail data.

| Quota | Source | Median trial p95 ms | Median throughput/s |
|---:|---|---:|---:|
| 0.1 | baseline | 804.163 | 11.11 |
| 0.1 | candidate | 1099.804 | 9.41 |
| 0.5 | baseline | 490.325 | 26.65 |
| 0.5 | candidate | 497.095 | 26.78 |

The first attempted trial was excluded from aggregates because the timed-out scanner was still being cleaned up at its startup boundary. Its raw result is retained in quota-results.json; a same-configuration replacement ran after all other trials and scanner termination. The verified set contains twelve measurements, three per combination. This exclusion addresses control uncertainty, not a latency threshold.

The Docker engine exposes 16 logical CPUs and approximately 7.6 GiB RAM; unrelated containers were running. Quotas/memory were held fixed, but the host was not exclusive and external load was not controlled. No unrelated containers were stopped. Interleaving limits ordering bias without proving statistical equivalence or eliminating scheduling noise. No builds, scans or other audit tests were intentionally run during the verified measurements.

Request thread CPU, process CPU/RSS and SQLite bytes are recorded in every raw result; SQLite shares the API process. Client/harness work shares the same CPU quota, so throughput is not isolated server capacity. Baseline modules came from a read-only Windows bind mount and candidate modules from the image; imports/startup are excluded by warm-up, and both runtime databases use the same temporary filesystem. Any remaining source-location effect was NOT TESTED. Frontend/proxy are absent; decoder/detector, OS filesystem I/O and GPU resources are outside this workload. No accepted target or representative inference data is supplied, so no larger-CPU fix, code performance gain or cost/SLO fitness is approved.

## Resumed Grype attempt

**BLOCKED:** no valid current report was produced. See resumed command/scan logs. No clean-image or complete-triage claim.


## Final payload revision

The first-pass payload hashes above remain frozen evidence of that pass. The benchmark helper subsequently gained warm-up/final-handler synchronization; current helper SHA-256 `38611dddc871fa502bb415ee79014d9b9863965bc84f8b3ad9b7c57702bb19a6`. All other runtime/application source remains unchanged from the tested implementation. Current canonical payload manifest SHA-256 `67f6d81ca76e12f3e962e543deffb24864a18994428a6115634693d6ddc6c3da`, at resumed/final-source-manifest.json; excludes the four handoff files to avoid self-reference. The corrected helper is exercised by the completed quota trials.


## Final separate home-index observation

**BLOCKED end-to-end preservation:** initial hash `ea7531fb92642851b122453acefa53e341f755f236146569866d5fc1d4281cdd`, final observed hash `54e58ba967788dc931cb25971557fefbd5c4458f52b4c0e8e1094965fd7ed5fe`; last write UTC 2026-11-11T21:53:37.459423+00:00. The index was 25088 bytes. Its current bytes were retained in resumed/home-index-observed-final.bin; no write or restore was issued against the home index. Initial full bytes/entry manifest were not captured, so no staged-entry delta or actor can be established. The project-local repository remains independently reviewable.

## Resumed artifact digests

| Artifact under resumed/ | Bytes | SHA-256 |
|---|---:|---|
| clean-build.log | 19,394 | `d01c7da5831461c2f92dde51488ddfe9a8de4c5da601c68f6386490658ef3eab` |
| clean-checkout.json | 209 | `80edf7688c53562501d72544c5843e992196b71eca944f17dbecee065a169dd8` |
| clean-tests.log | 29,179 | `bd5a7658ab4a539e2e150a3053f69863465f3778fb1797065467a52d5ab36b1b` |
| clone-clean.log | 139 | `092412a23b0a60bc927215aaa8872871ae2360d1f9d7a0069b0e9ab43dd71ffb` |
| commands.json | 14,176 | `d0e0b785c88ee07bbd568b953161c77bbcd34d8bdd0a8a8e3df8fc034365b740` |
| final-source-manifest.json | 16,836 | `cd5bf93813d3c621730d32a9c9c077a691a52ce7c51b4ff2e7c10ff4cd2f8f74` |
| final-verification.json | 370 | `bdf1e132fb01027b0d82deabe3a7b4bed0016682f4afa3c72c2c2ffde16c55a4` |
| grype-cache-inventory.json | 239 | `b378f150062466c07913e8b5b22345e1d30004a8949cca59808c624a15543c99` |
| grype-scan.log | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| grype.json | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| home-index-final.json | 513 | `b3e2de0095eeaaf9c4fdd0c21ea587ac2e8ee176b725c17374ee0918480dbd96` |
| home-index-observed-final.bin | 25,088 | `54e58ba967788dc931cb25971557fefbd5c4458f52b4c0e8e1094965fd7ed5fe` |
| quota-01.log | 4,053 | `a81e6b8028102f7f9122fef2dc069e8203ce9b765f818bd6c4cf9e0c3a68c7ca` |
| quota-02.log | 4,041 | `bc61b1f44aa3b0f25a0dab70366852cadd887c84020936a5c24a95feae906c56` |
| quota-03.log | 3,982 | `0ba2a03241ebb496ec4b59fb5b80f5934947ae80d721430501a6752846069ed9` |
| quota-04.log | 3,997 | `5c0cae6aefded4357f7b78c4bd805ab133edab9c4c6e6f4331962490408066b9` |
| quota-05.log | 4,077 | `83a72066592d1c4ebee8c4db50c4c9373630fec6e36e6054338cef9fa490379d` |
| quota-06.log | 4,038 | `2336e7683dc48ed8d79a834e89a53315c715f0c84df1b1c02f5799944b26f3b2` |
| quota-07.log | 4,098 | `d01db90545631042f8875fa69233aa7f648a330171dd831e00358b7528689ff8` |
| quota-08.log | 4,004 | `b2a3464238d58eb00936138e07de1b3437d8e4c0fcb85ac1221103709cde8e0f` |
| quota-09.log | 4,035 | `e74d3a0ef9cb6f446f7c1b5e940a4c9099ada8c8f0d6a0caa11ae895d47f0652` |
| quota-10.log | 3,996 | `feae404fc8a786e79d15745665a4ef75b0ea46556d25bbc3478f13ff5401fc41` |
| quota-11.log | 4,025 | `4932e70c1ebd69e3e22f393b553537864c936bb6fea2b8482c9f61e8d429f9fa` |
| quota-12.log | 4,049 | `5af3483ead5761715c1c35325c966f4b665865a893533bd22879d46ea17693af` |
| quota-13-resolved-control.log | 3,978 | `19e606a6bd49671088cc47fd29dfe8948414ed5699567d3a24bdb20ba0e3a1b1` |
| quota-control-replacement.json | 220 | `e0e3ffd7052d952f702701a46bca30e9c35df3198b0b02271e8320124a40a9a1` |
| quota-results-verified.json | 81,015 | `e6743be0464adaf494665b2e38f116ad6889bf2e299adc7cbd28b1af45dd6e96` |
| quota-results.json | 80,959 | `a1ec378ff0bf2fc47b2a361860c942bbca5b00b056c007c96f3dbba5ded22e09` |
| resumed-docker-resources.log | 17,074 | `7816b93980f2e6d6fb7d4a7cae53ef978dd7e1106cdef7f0e60c5fedb61ce5e7` |
| scanner-deadline-cleanup.json | 193 | `7f4c5e0f6ee9ff9221314cee7cc5b576c7f27f81ea191cb6e691402a3ad4efc2` |
| scanner-resource-sample-later.json | 246 | `6a3168f19c6af5f4cb55503ffc0f04462874777a267d46e69e28d1397e97d498` |
| scanner-resource-sample.json | 201 | `1ee173f318ceb0cc5e18b3857f7f05f175e11e7ab6ee5200b2686ad69db65e85` |
