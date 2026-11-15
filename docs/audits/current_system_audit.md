# Current-system audit - 2026-11-07

> Historical foundation audit. The authoritative current review is
> [FINAL_ENGINEERING_AUDIT.md](../../FINAL_ENGINEERING_AUDIT.md). Preserve the
> original observations below; the Git, dependency and verification state has changed.

Repository scope: coffee_ops, configuration, dependency manifests, scripts, tests,
saved verification evidence and documentation. Project-scoped git log returned no
project commits; the enclosing user worktree is not a usable project history.
Original reference PDFs/DOCX are retained. No trained operational weights, real videos
or labeled cafe dataset were present at the start of this review.

## Implemented behavior

- OpenCV decoding runs in a spawned process with a two-item queue. Recorded replay
  applies backpressure; live input discards stale queued frames. A read deadline
  terminates stalled input. Frame sampling is configured per camera.
- YOLODetector loads explicitly supplied local weights in a spawned process, verifies
  class names/checksum and imposes loading/inference/IPC deadlines. Original runtime
  pins Ultralytics 8.3.163 and CPU Torch 2.9.0. No trained shop model is bundled.
- A class-aware Kalman/Hungarian tracker gives anonymous, run-local IDs, predicts with
  elapsed time and applies distance/IoU gates. It has no appearance recovery.
- Table polygons, temporal hysteresis, product placements/transfers/removals,
  disappearance review events and person-zone transitions are implemented.
- Immutable SQLite records, indexed projections, bounded reconciliation transactions,
  leases, POS revisions, feedback and daily JSON reports are implemented. A bounded,
  authenticated loopback read API now serves stored read models; no dashboard exists.
- Directional lines, traffic review revisions, local-day/hourly time-weighted reports,
  event-only scoring, reliability counters and stage timers were added in the foundation
  pass. The default config has no entrance calibration. See [status index](../PROJECT_STATUS.md).
- The earlier verification contained 101 passing tests; the immediate foundation
  baseline was 126 tests with one optional dependency skip. Its replay uses supplied
  synthetic detections; the tiny real inference test uses untrained weights.

## Confirmed limitations and requirements gaps

| Finding | Evidence | Consequence / priority |
|---|---|---|
| No preparation or handover recognizer | event_engine.py emits zone movements, not those actions | A placement cannot be reported as a prepared drink. Add independently annotated temporal events first. |
| Track IDs are not physical-item identities | tracker.py expiry creates new IDs; saved stress IDF1 drops to 0.5/0.333 for long occlusion/large motion | Replay deduplication does not prevent double counting after identity fragmentation. Highest counting priority. |
| Table occupancy is proximity evidence | Person-center polygon membership plus timed hysteresis in event_engine.py/zones.py | Nearby standing people or staff can appear occupied. Calibrate seat regions and evaluate seated-presence evidence. |
| Tracker protocol is not configurable at construction | Pipeline directly creates KalmanTracker | Alternate trackers require explicit factory/injection work; they are not already integrated. |
| Missing business metrics | No preparation/handover state machine, full visit lifecycle, queue waiting-time or staff-role model | Do not expose these as measured analytics. |
| Legacy UTC reporting | daily_report remains UTC/sample weighted; business_report now supports explicit timezone, shifted-day boundaries, observed-duration coverage and hourly counts | Use business-report for local analytics; camera/coverage correctness still requires real labels. |
| No live reconnect | video_input exits on failed reads; runtime records failure | RTSP recovery and gap-aware state transitions need hardware testing and implementation. |
| Constant-FPS replay timestamps | frame index / reported FPS | Variable-frame-rate timestamps remain unsupported. |
| Partial resource monitoring | Pipeline measures orchestrator RSS/CPU; GPU metrics null | Existing FPS/RSS is not total inference-system capacity. |
| Historical growth | Per-frame ledger writes; full history reconciliation/report scans | Bounded active state is not bounded disk usage; long-duration profiling/retention needed. |
| Single-writer persistence | SQLite WAL/local-disk design | Multiple cameras need measured contention; distributed scale unproven. |
| Exact class catalog contract | detector rejects model/config class mismatch | COCO person/cup/dining-table IDs cannot be silently renamed to shop-specific classes. |
| Unverified production security | Local API has a bearer token/read-only DB/loopback binding; no production web server, full SBOM/CVE scan or secrets workflow | Torch advisories remain; pilot authentication and process isolation do not establish production certification. |

No evidence justifies replacing the working persistence/POS layer. Retain its invariants
and tests. The best immediate change is a controlled detector/tracker comparison on
real footage, not a wholesale rewrite.

## Module disposition after the foundation pass

| Modules | Decision | Evidence / boundary |
|---|---|---|
| config, schema, health | Retain/extend | Strict class/geometry validation and native NMS check; crossing geometry and tzdata requirement added |
| detector | Retain; benchmark adapters first | Spawned deadlines/checksums; no compatible trained shop checkpoint exists |
| tracker | Retain as control; replace only after comparison | Existing occlusion/gating failures are measured, but no real-label alternative has won |
| event_engine, zones, traffic | Extend | Conservative directional lines added; generic product/table state remains; no handover/preparation classifier |
| pipeline, runtime, video_input | Extend | Transaction/fail-stop behavior retained; stage/coverage health and source hashing added; PTS/live reconnect still open |
| storage, reporting, business_reporting | Retain/extend | Indexed interval reads, read-only mode, local-day coverage and append-only traffic reviews; one SQLite writer remains |
| pos_adapter, reconciliation, inventory, alerts | Retain | Quantity conservation/refunds and neutral review workflow remain; legacy exit naming is not a payment conclusion |
| evaluation, event_evaluation, exports | Extend | Event-only task scope, camera/line matching, exposure/abstention handling and all-event exports added |
| dataset, mlops | Retain; extend after real-label policy review | Existing integrity/promotion controls preserved; strict cross-camera audit differs from notebook group split |
| cli, api | Extend | Existing JSON commands plus authenticated local read endpoints; production hosting/dashboard deferred |
| demo, scripts, tests | Retain/extend | Explicit synthetic provenance, recorded replay acceptance, fault tests and controlled sampling benchmark |
| training notebook and optional environments | Retain | Actual three-model training/reload/export API checks already recorded; no café accuracy claim |

No working module was removed. New live run source identifiers hash the URL so
credentials are not persisted in future run records. Existing old-ledger URL values
are immutable and were not silently rewritten or deleted.

[Direct dependency advisory evidence](dependency_advisories.json) contains six OSV
records for Torch 2.9.0, including aliases (not six independent bugs). They cover
untrusted-checkpoint execution and other affected APIs; exploitability in these
specific paths has not been tested. The lookup is not a complete transitive audit.
Production must use a separately validated patched native-library pair. Existing
application pins were not silently upgraded as part of model comparison.

Hardware detected: i5-13450HX (10 cores/16 logical processors), about 16 GB system RAM,
RTX 3050 Laptop GPU with 6,144 MiB dedicated VRAM according to nvidia-smi. The Windows
CIM AdapterRAM field truncates this GPU's memory; do not use it for VRAM planning.

## External cafe implementation audit

[Cafe Vision](https://github.com/Chinmay-Sakhare07/CafeVison-MGEN_Hackathon_2025)
contains useful overlay/zone-helper examples. Its inspected filters_zone_logic.py
counts a cup in the barista zone using a five-second wall-clock cooldown, so a
stationary cup can repeatedly count and simultaneous cups can be suppressed. No
usable license was detected in repository metadata. Do not copy it or adopt its
production-count interpretation. This is a code finding, not a model accuracy result.
