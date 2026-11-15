> Historical report from the 2026-11-11 audit, finalized 2026-11-12. Superseded by [the current audit](../../../FINAL_ENGINEERING_AUDIT.md). Earlier findings and failures are preserved; links are relocated.

# Deployment readiness : 2026-11-12

Evidence was collected on 2026-11-11; this handoff was finalized on 2026-11-12. Saved commands, timestamps and digests retain their original dates. No cloud deployment or security clearance is implied.

**Synthetic Render staging is BLOCKED. No infrastructure approval is requested.**
No resource, remote repository, push, public endpoint or deployment was created.

## Current architecture and provider fit

The application decodes video in a child process, detects/tracks objects, appends
observations and POS revisions to local SQLite/WAL, and produces reports/review exports.
Its optional read API opens read-only connections and binds `127.0.0.1` only. There is
no frontend, hosted login, registration, payment processor or job-platform integration.
Runtime images contain source/config examples, not weights, camera recordings, notebook
environments or operational ledgers. The default image validates config and exits.

| Provider gate | Status | Finding |
|---|---|---|
| Render service selection | BLOCKED | Proposed headless background worker has no public or private ingress. Current CLI commands exit; no reviewed long-running staging supervisor exists. Do not deploy the default validation command into a restart loop. |
| Web/private API hosting | FAILED | Current loopback `http.server` is a local pilot. No production listener/server was added. Do not bind publicly or tunnel it to make deployment appear to pass. |
| Public ingress disabled | VERIFIED | Proposed worker has no incoming service port; local containers publish no ports. No actual Render service exists. |
| Outbound deny policy on Render | BLOCKED | Need enforceable provider/network boundary for all child processes, native libraries, DNS, IPv4/IPv6, private networks and metadata. Offline library flags and URL validation are not firewall enforcement. |
| Synthetic inputs only | VERIFIED | Local acceptance creates synthetic video/detections/POS. No real footage, credentials, payments, accounts or platform automation were supplied to these runs. Cloud enforcement is untested. |
| CPU/memory capacity | BLOCKED | API quota diagnostic is not detector capacity. Actual inference, child-process peak RSS, sustained video and disk growth must fit approved resources with headroom. |
| Persistent storage semantics | VERIFIED | SQLite needs local disk and one writer; runtime changes need a persistent mount if retained. No remote DB or DB role provisioning proposed. |
| Provider storage/recovery execution | NOT TESTED | Provider snapshots, disk restore, restart and region failure not exercised. |
| Health probe format | VERIFIED | GET `/healthz`: 200, small JSON, no-store, no DB detail. Detailed `/v1/health` remains authenticated. |
| Render probe reachability/readiness | BLOCKED | Worker has no HTTP probe; private services support TCP probes; web HTTP probes require a reachable compatible service. Local liveness alone does not detect storage/inference failure. |
| Secrets and data access | BLOCKED | No cloud secrets created. Need owner-managed environment secrets, rotation, file ACL review and historical credential clearance before deployment. |
| Schema migration and rollback | BLOCKED | Migration/transaction tests pass locally. Need artifact-bound backup/restore drill and provider storage permissions before cloud approval. |
| Security, licensing and reproducible release | FAILED | Known dependency findings, absent project license/approver and unlocked transitive/apt resolution. |

Render documents that background workers can initiate requests even though they cannot
receive them. A private service changes ingress reachability, not outbound authorization.
See [service types](https://render.com/docs/private-services) and
[outbound addresses](https://render.com/docs/outbound-ip-addresses). An outbound address
allowlist at a destination is not proof that this service cannot reach other destinations.

## Concrete infrastructure proposal, pending blockers

The proposed synthetic-only footprint is **one Frankfurt background worker, one replica,
`1c-2g` (legacy Standard), 1 CPU / 2 GB RAM, 5 GB persistent disk at `/var/data`**.
No web service, database server, cache, domain, ingress gateway, autoscaling, GPU,
camera stream or external POS connection is included. Use a new isolated workspace;
auto-deploy must be off. Build the immutable reviewed runtime image; never upload `var/`
or mount the laptop ledger. Real-data paths and untrusted checkpoints remain prohibited.

This is a sizing and cost proposal, **not an executable Render configuration**. A safe
worker entry point, resource measurements and a provider-supported outbound boundary are
unresolved. If Render cannot supply the required boundary, this proposal is rejected;
selecting another hosting platform needs a new proposal and approval. No `render.yaml`
was added that might provision an insecure substitute.

| Cost component | Monthly USD estimate | Basis / status |
|---|---:|---|
| One 1c-2g worker | 25.00 | Vendor service-compute article; revalidate quote at approval |
| 5 GB disk | 1.25 | 0.25/GB/month |
| Hobby workspace assumption | 0.00 | Owner must confirm eligible plan and account terms |
| Proposed fixed subtotal | **26.25** | Excludes taxes, bandwidth/build overages, monitoring, retained backups and any outbound-control service |
| Optional Pro workspace | +25.00 | If required, fixed subtotal 51.25; not automatically authorized |
| Required outbound enforcement | **Unpriced / BLOCKED** | No verified compatible implementation or vendor quote; full safe hosting cost is unknown |

The vendor lists $25/month for Standard/1c-2g and $7/month for Starter/0.5c-512mb in
[its compute sizing article](https://render.com/articles/set-up-self-hosted-github-actions-runners-on-render),
and $0.25/GB/month for disks in [its storage explanation](https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses).
See [workspace pricing](https://render.com/pricing) and [current plan identifiers](https://render.com/docs/compute-plans).
The pricing page's extracted view was incomplete; this is an estimate from current
vendor material, not an account quote. A 0.1/0.5 CPU Docker diagnostic does not establish
that a free/Starter Render instance can run the model or meet an absent SLO.

## Local synthetic network boundary

The verified policy is Docker `--network none --cap-drop ALL --security-opt
no-new-privileges`, running UID/GID 10001 with no published ports and no Docker socket
mount. Dependencies download during an explicit image build; application execution is
offline. For read-only benchmark runs add `--read-only --tmpfs /tmp:rw,nosuid,nodev,size=256m`.
Give writable storage only to a new synthetic output location, never a private ledger.

`scripts/verify_egress.py` requires Linux, verifies that only `lo` exists, proves loopback
works, and checks TCP/UDP to public IPv4, RFC1918, link-local metadata and public IPv6
addresses. Only immediate kernel unreachable errors count as a pass; DNS failures and
timeouts do not. There is no application socket monkeypatch or hostname-only denylist.
This test must run again inside the exact proposed cloud boundary before approval.

## Health, migrations and storage

Keep detailed storage health, paths, exceptions, runtime and camera information private.
The minimal probe cannot report database readiness: if storage fails after server startup,
liveness can still return 200. A future hosted readiness endpoint should return only
200/503 after a bounded harmless read and keep diagnostics behind authentication.
[Render's health documentation](https://render.com/docs/health-checks) distinguishes web
HTTP checks from private-service TCP checks and excludes background workers.

Store the ledger, WAL/SHM and backups under the same protected persistent root; UID
10001 must have only the necessary permissions. Use one writer per camera/ledger and
one service instance for this proposal. SQLite has no PostgreSQL-style roles: the
writer's OS access and the API's read-only/query-only connection are the current boundary.
Do not split writer and API across separate disks or replicas and expect shared SQLite.

Before an upgrade, stop ingestion, use SQLite's online backup API to a **new** protected
file, verify `PRAGMA quick_check`, and restore/test that backup on a separate copy. Do
not copy only a live main DB while WAL writes continue. Open the copy with the candidate
writer to migrate; verify schema version and accounting/report invariants before switching.
Never run an older binary against a newer schema as a rollback shortcut.

[Render disks](https://render.com/docs/disks) persist only mounted paths, attach to one
service instance and affect deployment availability. Snapshot/restore and desired RPO/RTO
need an actual synthetic drill. Automatic snapshots alone do not prove SQLite consistency.
No retention duration or RPO/RTO has been silently selected on the owner's behalf.

## Recovery, rollback and teardown

For a failed frame transaction, stop the damaged in-memory pipeline; replay from frame
zero with the same immutable source/config/run ID to rebuild state and deduplicate.
Changing run IDs can duplicate business periods. For code rollback, stop the worker,
restore the known-good image/config/checkpoint manifest and its matching tested DB backup
to a new path, verify schema/reports, then restart. Preserve failed ledgers and evidence
for owner-directed review. Model registry rollback alone does not restore files or code.

After an approved synthetic trial: suspend the worker first, export the explicitly
approved synthetic evidence/backup, verify their hashes, revoke tokens, and delete the
approved service/disk through the provider. Confirm any snapshots, registry images,
build logs and retained backups are addressed under an owner-approved retention policy;
verify billing stops. Local images, caches and protected data are retained by this review.
This teardown procedure was designed, not executed, and authorizes no current deletion.

Before any cloud approval request, attach the exact image and source digests, final
worker command, current account quote including outbound enforcement, region/storage
settings, synthetic data manifest, secret handling, denied-destination test results,
resource/SLO results, restore drill and named security/license approvers. All are required
for a reviewable proposal. Public beta and production additionally require tenant access,
TLS/server hardening, privacy/retention decisions and independently labeled real footage.

## Additional observed evidence

Local synthetic SQLite backup/restore and twelve post-change HTTP challenges passed. This does not validate Render disk recovery, schema rollback on hosted storage or private-tenant isolation. Exported runtime image size is 2,383,761,838 bytes as reported by Docker; image disk size is not peak runtime RAM. No inference memory/capacity claim follows from API measurements. Docker Desktop temporarily became unavailable; resumed local checks and their outcomes are in RELEASE_EVIDENCE.md. Provider readiness remains BLOCKED regardless of local diagnostic recovery.

