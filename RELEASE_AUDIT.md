# Release audit : 2026-11-12

Evidence was collected on 2026-11-11; this handoff was finalized on 2026-11-12. Saved commands, timestamps and digests retain their original dates. No cloud deployment or security clearance is implied.

**Decision: local synthetic POC only. Cloud staging, public beta and production are not approved.**

This review applies to the nested `computer-vision-main` project containing `coffee_ops`,
not the job-search repository named in the supplied task template. Evidence was collected
on Windows and in local Linux containers. Local baseline and implementation commits were created on a project audit branch. No pushes, cloud resources or deployments
were created. No files were removed. See `RELEASE_EVIDENCE.md`, `DEPLOYMENT_READINESS.md`
and `CLEANUP_MANIFEST.md` for reproduction, provider constraints and preservation.

## Scope and requirement mapping

`VERIFIED` means the stated, bounded check has evidence. `FAILED` means the current
implementation fails the stated gate. `BLOCKED` means a prerequisite is missing.
`NOT TESTED` means no execution or conclusive investigation established the requirement.
Passing synthetic tests does not establish real-video accuracy, security clearance,
legal approval, customer validation or hosted capacity.

| Requirement | Status | Evidence / limitation |
|---|---|---|
| Read existing audit, status, verification, privacy and deployment guidance | VERIFIED | README; docs/PROJECT_STATUS.md; docs/VERIFICATION.md; docs/audits/current_system_audit.md; docs/deployment_runbook.md; saved foundation/video evidence |
| Original release audit, cleanup manifest, Render runbook and frozen/post-freeze package | BLOCKED | No corresponding release package existed in this project. These four handoff documents are new. Historical coffee-ops evidence is retained, not promoted to a P1 freeze. |
| Candidate branch, supplied base commit and US01–US12/P1 preservation | BLOCKED | The named job-search baseline, accepted stories and six regression workloads were not supplied. Initially no project `.git` existed; after access changed, a local audit repository/branch was created from the pre-edit snapshot. The enclosing home index matched at initialization; a later fingerprint change leaves end-to-end index preservation BLOCKED. |
| Preserve pre-existing app, documents, environments and data | VERIFIED | Pre-edit snapshot: 151 source/reference files; original hashes retained. Nothing deleted; final differences recorded in cleanup manifest. Home-index fingerprints matched at project initialization but changed at final verification; no restoration was attempted. The new local baseline does not invent missing P1 history. |
| Reproduce job-save latency and six flagged P1 regressions | BLOCKED | No job-save endpoint or corresponding fixtures in coffee_ops. No thresholds or timeouts changed. |
| Synthetic API timing collection | VERIFIED | Raw timing/resource diagnostics collected against the captured pre-edit source. Windows continuity was interrupted; Linux quotas and limits are checked separately. No P1 equivalence, exclusive-host control or performance gain is established. |
| Controlled CPU 0.1/0.5 diagnostic | VERIFIED | After Docker recovered, twelve interleaved quota trials completed with identical image/dependencies, DB digest, warm-up, concurrency and memory. This is a synthetic diagnostic on shared hardware, not proof of a hosting fix. |
| Frontend/proxy profiling and genuine browser workflows | NOT TESTED | No dashboard/frontend/proxy exists. Real HTTP tests exercise the local API. Browser acceptance cannot be invented from API tests. |
| Approved performance target at proposed hosting cost | BLOCKED | No approved SLO, real-model workload or representative camera data; fractional CPU diagnostics do not establish hosting fitness. |
| Vulnerability report and triage | BLOCKED | The 2026-11-11 OSV installed-package lookup completed. Initial Grype attempts failed; the resumed scan timed out after 900 seconds without a usable image report. Individual exposure/backport investigation remains incomplete. The template states two critical / 77 high matches, but its report was not supplied; those are not this project's verified counts. |
| Synthetic-credential incident fully cleared | BLOCKED | No incident credential/fingerprint or history supplied. Selected source/log patterns were checked; archives, media, third-party caches and unavailable history are not secret-cleared. |
| API authentication, read-only access, input/error boundaries | VERIFIED | Real loopback requests cover missing/wrong bearer, origin rejection, pagination, redaction, storage failures and cursor overflow recovery. This token grants access to the entire local ledger. |
| Sessions, per-user authorization and cross-user isolation | FAILED | No multi-user identity/session/tenant model. Appropriate only for a trusted local operator; mandatory blocker for a public service. |
| Uploads, redirects, public registration, real payments and job-platform automation | NOT TESTED | No corresponding HTTP features in this application. Existing offline POS imports are synthetic in acceptance. No real integrations were exercised. |
| Production logging and retained private data | BLOCKED | HTTP access logging is disabled and responses omit evidence paths. Native decoder/detector errors and old ledgers need a separate credential/data-retention review. |
| Local synthetic egress enforcement | VERIFIED | Docker `--network none`, no capabilities and no-new-privileges; loopback works, eight unauthorized TCP/UDP probes return kernel network-unreachable. |
| Render synthetic egress enforcement | BLOCKED | Local Docker enforcement is not a Render control. Private ingress and outbound IP lists do not prove outbound denial. |
| Minimal probe and private readiness | VERIFIED | Exact `/healthz` returns only `{"status":"ok"}` without authentication or DB access. `/v1/health` remains authenticated. This is liveness, not database readiness or Render reachability. |
| Windows/Linux supported CPU/video test matrix | VERIFIED | 184 tests per environment; CPU profiles skip 13 optional tests; video profiles pass all 184. Linux is Docker Desktop's Linux engine, not an independently observed hosted runner. |
| Clean source-only container build and synthetic operation | VERIFIED | Allowlisted Docker context, no local environments/var/weights, fresh Linux dependencies, native CPU operator smoke, test and acceptance runs with networking disabled. |
| Fully reproducible dependency resolution | FAILED | Direct dependencies and base/scanner digests pinned; transitive wheels and apt repository state remain unlocked. Saved exact image is immutable by digest, but a later rebuild may resolve differently. |
| GitHub Actions coverage | VERIFIED | CPU/video × Windows/Ubuntu definitions, dependency checks, source integrity, Docker tests/build, Grype OS/Python high-severity gate and license inventory/check. No workflow was pushed or remotely executed. |
| Private GitHub CI remote execution | BLOCKED | Local audit checkout now exists; no remote or approval to push. Source license missing; high-severity security gate is expected to block until remediated. |
| Artifact hashes and manifest checks | VERIFIED | Exact local image metadata, exported image checksum, source manifest and pre-edit snapshot recorded in evidence; no signed registry publication claimed. |
| Minimal authorized cleanup and ignore policies | VERIFIED | No deletions. New Docker allowlist excludes private/runtime/research data. Additional SQLite filename variants ignored. |
| Render resource, storage, migration, recovery and rollback design | BLOCKED | Concrete proposed sizing/cost and stop gates in readiness; no deployable production server or verified provider egress boundary. |
| Cloud approval / deployment | NOT TESTED | Neither requested nor performed. Approval would follow closure of the listed blockers. |
| Independent adversarial review against original P1 requirements | BLOCKED | A separate post-change code/test review was performed locally; original P1 evidence is missing. This was a second review pass by the same reviewer, not an independent person or certification. |

## Reproduced defect and minimal fix

An authenticated request to `/v1/events?camera=shop&after=9223372036854775808`
raised `OverflowError` when Python bound the integer to SQLite. The client received
`RemoteDisconnected`, and a server traceback escaped the intended JSON error boundary.
The new regression test failed before the fix. Shared pagination validation now rejects
cursors outside `0..9223372036854775807` before SQL execution. Oversized, 500-digit and
negative cursors return 400; the largest valid cursor and a following normal request
return 200. Existing pagination behavior and accounting remain covered.

The probe addition has a separate negative test: it cannot open SQLite, disclose
diagnostics or make private health/status endpoints accessible. Adding query parameters
does not expose a detailed unauthenticated probe. Neither change relaxes the loopback bind.

No performance optimization, model replacement, dependency upgrade or architectural rewrite
was made. Security and runtime dependencies remain a release blocker rather than an
unverified upgrade being labeled safe.

## Security interpretation and residual risks

The vendor confirms arbitrary code execution from malicious checkpoints on the installed
Torch 2.9.0 line, including `weights_only=True`; the vendor identifies 2.10.0 as the fix
for that specific issue. A SHA-256 supplied alongside a checkpoint establishes integrity,
not trust in its publisher. See the [PyTorch vendor advisory](https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p).
Other Torch findings have different affected APIs and fix ranges; do not assume one
version bump clears them all. The RT-DETR adapter uses local safetensors and disables
remote code, while the YOLO path still loads trusted local pickle-based checkpoints.
No untrusted checkpoint exploit was executed.

No finding is accepted as residual risk, and no accountable risk approver has been
appointed. An alias/duplicate is not a false positive. Absence of a direct call site is
not proof a native dependency or model cannot reach an API. Backports and actual exposure
must be verified per package before security clearance; scanner success means the scan ran.

The local server is Python `http.server`, with a shared bearer token, eight request slots,
socket timeouts and no TLS or user accounts. Slow-client/resource exhaustion, growing
report scans and private-data retention remain production concerns. A read-only SQLite
connection prevents SQL writes, but does not create tenant isolation or an OS sandbox.

Installed metadata reports AGPL-3.0 for Ultralytics and ultralytics-thop. The repository
has no owner-selected source license. Dependency inventories are evidence, not legal
clearance, and missing license identifiers are not assumed permissive.

## Separate adversarial review pass

After the fix, challenged the SQLite maximum boundary and server recovery, tested the
liveness exception against private routes, reviewed the Docker context and non-root user,
and exercised fresh Linux CPU/video tests and outbound denial. Accounting, camera/run
scope, ambiguous reports, append-only records, quantity conservation, refunds, transaction
faults and replay idempotence stayed under the existing suite. No assertions, test
timeouts, acceptance thresholds or existing test expectations were weakened.

Remaining challenges are deliberately open: absent P1 provenance; unlocked dependency
resolution; known dependency advisories; no hosted server/tenant model; no Render egress
proof; no independently labeled cafe validation; long-occlusion/fast-motion identity loss;
no sustained camera/GPU/RTSP capacity or recovery test; and incomplete historical secret,
license and retention review. Passing tests does not override these failures.

## Release decisions

| Destination | Decision | Conditions |
|---|---|---|
| Local POC | VERIFIED : bounded GO | Synthetic fixtures, trusted local artifacts, local operator, preferably network-isolated container. No real cafe accuracy claim. |
| Private GitHub CI | BLOCKED | Definition prepared and local equivalents run; owner must provide project history/repository and approve any push. Security/license gates remain blocking. |
| Synthetic cloud staging | BLOCKED | Provider outbound policy, compatible process/server, artifact/security/license gates and explicit infrastructure approval required. |
| Public beta | FAILED : NO-GO | Missing production access controls, security closure, privacy/retention and real-video acceptance. |
| Production | FAILED : NO-GO | All preceding blockers plus sustained resource, recovery, monitoring and independent acceptance evidence. |

## Current vulnerability inventories

The following generated tables preserve current installed-package lookup records. They
must not be interpreted as completed vendor/backport/exposure validation. Every unresolved
entry has risk approver **unassigned**; no risk acceptance is implied.

### Windows installed-package OSV inventory : VERIFIED lookup, BLOCKED triage

38 installed distributions queried; 23 raw advisory records across pip 24.3.1, setuptools 78.1.0 and Torch 2.9.0+cpu. Aliases overlap; this is not 23 independent vulnerabilities. No fixes were installed and no risk accepted. Backport status is NOT TESTED for every entry.

| # | Installed package | Advisory / aliases | Reported fix | Exposure and action | Status |
|---:|---|---|---|---|---|
| 1 | pip 24.3.1 | [GHSA-4xh5-x5gv-qwph](https://osv.dev/vulnerability/GHSA-4xh5-x5gv-qwph) ([vendor record](https://github.com/pypa/pip/pull/13550)); aliases: CVE-2025-8869, PYSEC-2026-1795 | 25.3 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 2 | pip 24.3.1 | [GHSA-58qw-9mgm-455v](https://osv.dev/vulnerability/GHSA-58qw-9mgm-455v) ([vendor record](https://github.com/pypa/pip/issues/13867)); aliases: CVE-2026-3219, PYSEC-2026-2875 | 26.1 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 3 | pip 24.3.1 | [GHSA-6vgw-5pg2-w6jp](https://osv.dev/vulnerability/GHSA-6vgw-5pg2-w6jp) ([vendor record](https://github.com/pypa/pip/pull/13777)); aliases: CVE-2026-1703, PYSEC-2026-1796 | 26.0 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 4 | pip 24.3.1 | [GHSA-jp4c-xjxw-mgf9](https://osv.dev/vulnerability/GHSA-jp4c-xjxw-mgf9) ([vendor record](https://github.com/pypa/pip/pull/13923)); aliases: CVE-2026-6357, PYSEC-2026-2876 | 26.1 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 5 | pip 24.3.1 | [GHSA-qwm4-qh6w-59xr](https://osv.dev/vulnerability/GHSA-qwm4-qh6w-59xr) ([vendor record](https://github.com/pypa/pip/pull/14110)); aliases: CVE-2026-13346, PYSEC-2026-3721 | 26.2.0 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 6 | pip 24.3.1 | [GHSA-wf93-45jw-7689](https://osv.dev/vulnerability/GHSA-wf93-45jw-7689) ([vendor record](https://github.com/pypa/pip/pull/14000)); aliases: CVE-2026-8643, PYSEC-2026-196 | 26.1.2 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 7 | pip 24.3.1 | [PYSEC-2026-1795](https://osv.dev/vulnerability/PYSEC-2026-1795) ([vendor record](https://github.com/pypa/pip/pull/13550)); aliases: CVE-2025-8869, GHSA-4xh5-x5gv-qwph | 25.3 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 8 | pip 24.3.1 | [PYSEC-2026-1796](https://osv.dev/vulnerability/PYSEC-2026-1796) ([vendor record](https://github.com/pypa/pip/pull/13777)); aliases: CVE-2026-1703, GHSA-6vgw-5pg2-w6jp | 26.0 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 9 | pip 24.3.1 | [PYSEC-2026-196](https://osv.dev/vulnerability/PYSEC-2026-196) ([vendor record](https://github.com/pypa/pip/pull/14000)); aliases: CVE-2026-8643, GHSA-wf93-45jw-7689 | 26.1.2 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 10 | pip 24.3.1 | [PYSEC-2026-2875](https://osv.dev/vulnerability/PYSEC-2026-2875) ([vendor record](https://github.com/pypa/pip/issues/13867)); aliases: CVE-2026-3219, GHSA-58qw-9mgm-455v | 26.1 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 11 | pip 24.3.1 | [PYSEC-2026-2876](https://osv.dev/vulnerability/PYSEC-2026-2876) ([vendor record](https://github.com/pypa/pip/pull/13923)); aliases: CVE-2026-6357, GHSA-jp4c-xjxw-mgf9 | 26.1 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 12 | pip 24.3.1 | [PYSEC-2026-3721](https://osv.dev/vulnerability/PYSEC-2026-3721) ([vendor record](https://github.com/pypa/pip/pull/14110)); aliases: CVE-2026-13346, GHSA-qwm4-qh6w-59xr | 26.2 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 13 | setuptools 78.1.0 | [GHSA-5rjg-fvgr-3xxf](https://osv.dev/vulnerability/GHSA-5rjg-fvgr-3xxf) ([vendor record](https://github.com/pypa/setuptools/security/advisories/GHSA-5rjg-fvgr-3xxf)); aliases: BIT-setuptools-2025-47273, CVE-2025-47273, PYSEC-2025-49 | 78.1.1 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 14 | setuptools 78.1.0 | [GHSA-h35f-9h28-mq5c](https://osv.dev/vulnerability/GHSA-h35f-9h28-mq5c) ([vendor record](https://github.com/pypa/setuptools/security/advisories/GHSA-h35f-9h28-mq5c)); aliases: BIT-setuptools-2026-59890, CVE-2026-59890, PYSEC-2026-3447 | 83.0.0 | Advisory specifies macOS filesystem behavior; Windows exploitability NOT TESTED, not declared a false positive. Validate patched tooling. | BLOCKED |
| 15 | setuptools 78.1.0 | [GHSA-xmj3-9gf7-h52w](https://osv.dev/vulnerability/GHSA-xmj3-9gf7-h52w) ([vendor record](https://github.com/pypa/setuptools/security/advisories/GHSA-xmj3-9gf7-h52w)); aliases: none listed | 84.1.0 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 16 | setuptools 78.1.0 | [PYSEC-2025-49](https://osv.dev/vulnerability/PYSEC-2025-49) ([vendor record](https://github.com/pypa/setuptools/security/advisories/GHSA-5rjg-fvgr-3xxf)); aliases: BIT-setuptools-2025-47273, CVE-2025-47273, GHSA-5rjg-fvgr-3xxf | 78.1.1 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 17 | setuptools 78.1.0 | [PYSEC-2026-3447](https://osv.dev/vulnerability/PYSEC-2026-3447) ([vendor record](https://github.com/pypa/setuptools/commit/dd9f436a36486b4cb8a4c70a2321548b0be09b8f)); aliases: BIT-setuptools-2026-59890, CVE-2026-59890, GHSA-h35f-9h28-mq5c | 83.0.0 | Package/build/install tool, not an HTTP endpoint. Avoid untrusted distributions/indexes; separately validate patched tooling. Exact exploit/backport NOT TESTED. | BLOCKED |
| 18 | torch 2.9.0 (+cpu installed) | [GHSA-63cw-57p8-fm3p](https://osv.dev/vulnerability/GHSA-63cw-57p8-fm3p) ([vendor record](https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p)); aliases: BIT-pytorch-2026-24747, CVE-2026-24747, PYSEC-2026-1856, PYSEC-2026-2286 | 2.10.0 | Trusted checkpoints only; no exploit test. Validate patched matched Torch/vision pair; per-API reachability NOT TESTED. | BLOCKED |
| 19 | torch 2.9.0 (+cpu installed) | [GHSA-qfhq-4f3w-5fph](https://osv.dev/vulnerability/GHSA-qfhq-4f3w-5fph) ([vendor record](https://github.com/pytorch/pytorch/issues/149626)); aliases: BIT-pytorch-2025-3001, CVE-2025-3001, PYSEC-2025-195 | 2.10.0 | Trusted checkpoints only; no exploit test. Validate patched matched Torch/vision pair; per-API reachability NOT TESTED. | BLOCKED |
| 20 | torch 2.9.0 (+cpu installed) | [GHSA-rrmf-rvhw-rf47](https://osv.dev/vulnerability/GHSA-rrmf-rvhw-rf47) ([vendor record](https://github.com/pytorch/pytorch/issues/149623)); aliases: BIT-pytorch-2025-3000, CVE-2025-3000, PYSEC-2025-194 | 2.13.0 | Trusted checkpoints only; no exploit test. Validate patched matched Torch/vision pair; per-API reachability NOT TESTED. | BLOCKED |
| 21 | torch 2.9.0 (+cpu installed) | [GHSA-vgrw-7cvw-pwgx](https://osv.dev/vulnerability/GHSA-vgrw-7cvw-pwgx) ([vendor record](https://github.com/pytorch/pytorch/issues/149622)); aliases: BIT-pytorch-2025-2999, CVE-2025-2999, PYSEC-2025-193 | 2.9.1 | Trusted checkpoints only; no exploit test. Validate patched matched Torch/vision pair; per-API reachability NOT TESTED. | BLOCKED |
| 22 | torch 2.9.0 (+cpu installed) | [PYSEC-2026-139](https://osv.dev/vulnerability/PYSEC-2026-139) ([vendor record](https://github.com/pytorch/pytorch/pull/176791)); aliases: BIT-pytorch-2026-4538, CVE-2026-4538 | No fixed release recorded; investigate vendor | Trusted checkpoints only; no exploit test. Validate patched matched Torch/vision pair; per-API reachability NOT TESTED. | BLOCKED |
| 23 | torch 2.9.0 (+cpu installed) | [PYSEC-2026-2286](https://osv.dev/vulnerability/PYSEC-2026-2286) ([vendor record](https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p)); aliases: BIT-pytorch-2026-24747, CVE-2026-24747, GHSA-63cw-57p8-fm3p, PYSEC-2026-1856 | 2.10.0 | Trusted checkpoints only; no exploit test. Validate patched matched Torch/vision pair; per-API reachability NOT TESTED. | BLOCKED |

Grype runtime-image triage: **BLOCKED**. First scan exit 125 / unexpected EOF; retry exit 1 / Docker Desktop unable to start. Empty output is not a clean report. The unavailable template report's two critical and 77 high raw matches cannot be attributed or triaged here. Required package/version/vendor/backport/exposure/approver fields for those 79 matches remain BLOCKED.

Known vendor-verified Torch checkpoint issue is FAILED for release. Other inventory rows are scanner/database matches needing individual confirmation; none are labeled proven false positives. Raw OSV details preserve affected ranges, aliases, references and fixes. Risk approver: unassigned for every open finding.

## Additional security patch verification boundary

The vendor-published Torch 2.13 / TorchVision 0.28 compatibility pairing is available for Python 3.13; its compatibility with this application was NOT TESTED in this review. The original environments and dependency pins were preserved. This is an open remediation requirement, not a claim that a patched pair is unavailable. See the [vendor compatibility table](https://github.com/pytorch/vision#installation). No person has accepted the known dependency risk for a release.


Resumed image scan: **BLOCKED**, exit 124 after 900 seconds with no valid report. Only its own temporary scanner container was stopped after the deadline; no unrelated container, protected output or database cache was removed. Complete OS-image vendor/backport/exposure triage and the unavailable template report remain unresolved. The Windows OSV inventory is not a substitute for an OS scan.


## Final enclosing-index limitation

**BLOCKED:** the separate home repository index changed from the initial fingerprint by the final check. Source and the new project index are separate. No project command was issued to write the home index, and the actor/cause is NOT ESTABLISHED. The initial check retained a hash rather than a full index/entry snapshot, so byte-level restoration or staged-entry comparison cannot be safely performed. Its final observed bytes were copied to ignored evidence, and the current index was left untouched.
