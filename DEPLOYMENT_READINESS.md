# Deployment readiness

**NO-GO for cloud staging, public beta or production.** Local offline software
verification does not authorize or validate a hosted deployment. Generated 2026-11-12T22:42:15.821075+00:00.
No deployment, registry push, remote creation or visibility change occurred.

## Verified local container

The scanned artifact is `coffee-ops-engineering:20261112`, manifest/index digest
`sha256:6b1918bc03856f0fa2ea0d051507e90a712a92f8fb17cb98bd6d59ac0150e078`. It runs as UID/GID 10001, copies only runtime app/example
config/schema files and the Linux hash lock, and contains no pip/ensurepip, tests,
notebook, local environments, credentials, footage, real weights or operational DB.
The default command validates example configuration and exits; it is not a web
service entrypoint. No ports are exposed or published by default.

The actual runtime passed auth, read-only root, native CPU NMS and untrained
YOLO inference under `--network none --cap-drop ALL --security-opt no-new-privileges`,
1 CPU, 1 GiB RAM and a 128 MiB tmpfs. Eight TCP/UDP probes to public, metadata,
private IPv4 and public IPv6 destinations were kernel-rejected; loopback worked.
These are invocation controls. HF offline flags alone do not deny network access.
The follow-up `container-final-limits.json` verifies the actual Docker HostConfig:
network none, read-only root, NanoCpus 1,000,000,000, memory 1,073,741,824 bytes,
all capabilities dropped, no-new-privileges and the bounded tmpfs.

The same three-second Docker stop test changed from forced exit 137 to graceful
exit 0 in 0.489 seconds after SIGTERM handling was fixed.
This checks server cleanup, not a complete long-running real camera failure drill.
The production image's 35 app-source hashes match the working tree and tested clone.

## Remaining gates

| Gate | State / concrete next action |
|---|---|
| Image vulnerabilities | FAILED: 1 critical, 61 high OS matches; no fixed versions from current feed. Resolve/vendor-triage each or obtain accountable component-specific acceptance. No acceptance is inferred |
| Optional video stack | OPEN Transformers advisories; evaluate a patched major release with actual RT-DETR/notebook APIs before changing it |
| Cold startup | First RT-DETR CPU worker exceeded its unchanged 60-second load deadline; warmed repeat passed. Establish reliable cold starts and diagnose host/storage/package costs before claiming readiness |
| Real model/event accuracy | BLOCKED by missing real cafe footage and independent truth; see implementation status |
| API hosting boundary | Current server binds 127.0.0.1 and has one shared token. Public TLS/proxy, identities, per-user access, rate controls and safe audit logging require a separate reviewed design |
| Persistent state | Provision a private writable volume owned by UID 10001, budget WAL/evidence growth, test SQLite backup/restore and migration against a copy. No real business DB was changed |
| Runtime health | `/healthz` is minimal liveness; authenticated `/v1/health` checks storage. No unconditional Docker HEALTHCHECK is added to a default batch command that exits |
| Resources/capacity | No approved SLO or representative workload. Local test limits are not cloud sizing or price evidence |
| Privacy/license | Owner-selected source license missing; AGPL dependency/reference/dataset/checkpoint rights and footage retention need owner review |
| Recovery/operations | Assign retention, disk alerts, backup schedule, credential rotation, rollback and camera reconnect behavior; exercise a real synthetic-data staging drill after explicit deployment approval |
| Cloud egress | No provider-equivalent deny policy has been configured or tested |

## Render investigation

Render's [web service documentation](https://render.com/docs/web-services) requires
a listener on 0.0.0.0 and its designated port. The present loopback API and default
validate-and-exit container do not meet that service model. A
[private service](https://render.com/docs/private-services) prevents public ingress;
that fact alone establishes no outbound-denial guarantee.

The [private-network documentation](https://render.com/docs/private-network)
describes inter-service connectivity and environment isolation. The
[outbound-IP documentation](https://render.com/docs/outbound-ip-addresses)
describes source IP ranges for external allowlists. Inference: neither is evidence
of the tested Docker `--network none` property. No documented or configured
equivalent was demonstrated here. Do not relabel private ingress as private egress.

Before any provider trial, choose an enforceable allowlist/deny architecture,
identify the necessary camera/POS/model paths, then repeat negative TCP/UDP probes
for public/private/metadata/IPv6 destinations and a permitted synthetic path.
Record provider settings, service identity, artifact digest, logs and enforcement
failures. Do not deploy production footage or credentials for that trial.
Actual staging remains **NOT TESTED**, pending the user's explicit approval.

Use [the offline runbook](docs/deployment_runbook.md) for current operations and
[the security report](docs/audits/security-20261112.md) for component triage.
