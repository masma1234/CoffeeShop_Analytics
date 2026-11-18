# Implementation status

Audit started 2026-11-12. Report generated 2026-11-12T22:42:15.821075+00:00. This is a scope and validation
record; the [README](README.md) is the authoritative overview and setup guide.

17 November current status: all four Windows/Linux CPU/video profiles and the
RT-DETR Linux profile passed nine checks each. The rebuilt RT-DETR image passed
native/isolation checks and has zero Trivy findings; its SBOM has 94 components.
Pretrained CPU numerical parity passed on 30 calibration images. Source license,
third-party/publication rights and real cafe acceptance remain open. See the
[current release gates](GITHUB_READINESS.md) and
[verification evidence](docs/audits/release-verification-20261117.json).
The capability table below is the dated 12 November snapshot, including the
legacy image's unresolved findings; it does not describe the new RT-DETR image.

15 November continuation: [startup verification](docs/benchmarks/detector_startup_20261115.md)
documents the dedicated RT-DETR loader, fixed deadline, bounded stage diagnostics
and cancellation/disconnect regression tests. The capability table below records
the earlier audit checkpoint; new inference checks do not establish cafe accuracy,
cold-boot reliability or security clearance.

| Capability | Implemented behavior | Validation boundary |
|---|---|---|
| Decode/replay | Spawned decoder, bounded queue, sampling, deadlines, camera lease | Synthetic recordings and fault tests; live reconnection and sustained camera operation unvalidated |
| Detection | Trusted local YOLO or configured RT-DETRv2, matching metadata/checksums/class names, fail visibly on absence/timeouts | Native NMS/untrained YOLO pass. Two public-photo frames pass pretrained RT-DETR on repeat; first cold load exceeded 60 seconds. No camera accuracy claim |
| Tracking | Anonymous Kalman association, lifecycle expiry, unknown/lost state | Logic/occlusion fixtures; no real CCTV IDF1/HOTA or calibrated identity-switch rate |
| Tables/traffic | Calibrated zones, directional crossings, dwell/gap rules, append-only review corrections | Exact fixture geometry only; example has no real entrance calibration |
| Products | Visibility and movement episodes, pickup placement/departure, proximity/motion interaction candidates | No validated preparation-completion, handover or recipient-role classifier |
| Persistence | SQLite schema v2, immutable ledger/projections, transactional frames/allocations, leases, snapshot reads | Concurrent/failure/replay tests; real business DB migration/backup drill not performed |
| POS | File/mock import and quantity-bounded reconciliation; paid POS units are sold units | Synthetic POS only; no real terminal integration or payment verification |
| Reporting | UTC legacy reports, time-weighted IANA business days, coverage and unknowns, neutral alerts | Synthetic acceptance and timezone/review tests; no verified business metrics |
| Local API | Shared bearer token, loopback read-only JSON, bounded threads, redaction and validation | Request/auth/storage fault tests and actual isolated container checks; no accounts/tenants/TLS/front end |
| Video review | Source PTS, MP4 overlay, streaming raw/accepted detections, review templates and event/frame scoring | Optional tests pass; pretrained smoke uses a repeated public image, no independent labels |
| Training research | Notebook, dataset/split audit and promotion gates | Historical experiments retained. No new training, model replacement or promotion in this audit |
| Packaging | CPU runtime hash locks, non-root allowlisted image, isolated test stages, SIGTERM cleanup | Windows fresh install and Linux Docker checks pass. Apt and optional/dev transitive resolution are not fully frozen |
| Security/release | Complete OS/Python image scan and SBOM, no suppressions | FAILED release gate: 1 critical + 61 high OS matches. Optional Transformers advisories also remain |

There is no dashboard, multi-user authorization, public endpoint, hosted staging,
production SLO, approved retention schedule or validated cloud egress control.
Database history and exported videos grow with use; bounded RAM state does not
bound disk use. Original environments remain preserved with known dependency debt.

## Real cafe acceptance still required

1. Obtain permissioned ceiling-camera clips across representative busy/quiet periods,
   occlusion, crowding, lighting changes, reflections and camera movement. Preserve
   capture clocks, camera calibration and recording-group identity.
2. Independently annotate complete target frames, tracks, zones and observable
   events. Mark genuinely unobservable transfers/roles as unknown. Keep each
   recording/camera/environment group in one split and reserve a held-out test set.
3. Measure detection AP, event precision/recall/F1, false events per hour,
   missed events per hour, product-count absolute error and bias, and tracking
   metrics including identity switches. Report unknown/abstention and observation
   coverage; synthetic fixture scores do not substitute for these measurements.
4. Measure end-to-end FPS, p50/p95 latency, dropped/decoded/inferred frames,
   CPU/GPU utilization, RSS/VRAM, disk growth and startup/shutdown behavior on the
   intended hardware with representative durations. Retain raw measurements.
5. Have the owner select acceptance thresholds and review failure causes before
   tuning or training. Bind a promotion to the exact weights, dataset, annotations,
   configuration and real-held-out evaluation. No numeric business target is invented.

See [the architecture](docs/architecture/current_architecture.md),
[current verification](docs/benchmarks/model_validation_20261116.md), [annotation contract](docs/annotation_guidelines.md)
and [benchmark protocol](docs/benchmark_protocol.md).
