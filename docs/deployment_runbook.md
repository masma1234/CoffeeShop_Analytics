# Offline pilot runbook and monitoring

Current stage: **offline replay / local review**. No real café model or footage has
been validated. The following is a reproducible software pilot, not production
approval. Use the main [README](../README.md) for the verified CPU environment and
[notebook setup](../notebooks/README.md) for the separate training environment.

## Configure and replay

Run `doctor` and `validate-config` first. Operational weights must be trusted local
files whose checksum, model version and embedded class names exactly match config
and metadata. Cup-only notebook exports cannot supply person traffic or table
occupancy. Do not rename cup labels or an RT-DETR directory to bypass the contract.
The configured RT-DETRv2 adapter is implemented. Its old model smoke evidence
does not validate a new dependency stack or real cafe accuracy. Other detector
versions require separate compatibility checks before changing configuration.

To enable directional crossings, add `crossing_lines` inside the relevant camera:

```json
"crossing_lines": [{
  "id": "door", "start": [50,120], "end": [270,120],
  "inside_side": "positive", "anchor": "center",
  "hysteresis_pixels": 5, "dwell_seconds": 0.2, "max_gap_seconds": 1
}]
```

These are **320x240 fixture coordinates**, not a target-camera calibration. With
this left-to-right horizontal segment, positive is below the line. Use center for
an appropriate overhead projection, or bottom_center only when the view supports
that ground-position proxy. Confirm direction, anchor, minimum dwell, band width
and gap allowance using annotations. The default config has no crossing line;
traffic zeros therefore mean no counted events, not verified zero customers.

```powershell
$py = '.\.venv-candidate\Scripts\python.exe'
& $py -m coffee_ops make-demo --directory var/demo-new
& $py -m coffee_ops --db var/demo-new.sqlite3 replay --source var/demo-new/fixture.avi --camera shop --run-id demo --start 2026-01-01T09:00:00Z --fixture-detections var/demo-new/detections.json
& $py -m coffee_ops --db var/demo-new.sqlite3 business-report --date 2026-01-01 --timezone Africa/Tunis --camera shop --run-id demo
```

Remove the fixture adapter only when supplying validated weights and a real video.
Use offset-aware capture start time. For a business day beginning at 04:00 add
`--day-start-hour 4`. The older `report` command intentionally remains UTC/sample
weighted; use `business-report` for time-weighted local-day analytics. It emits
distinct UTC/offset labels for repeated DST hours and rejects ambiguous/nonexistent
business boundaries. Historical video scope is independent of the day's POS scope.

Crossing confirmation follows dwell; daily traffic is assigned by interpolated
crossing capture time. Missing/unreliable observations reset evidence. Do not
bridge a disconnect as a completed crossing. New run IDs are not new visitors:
overlapping camera runs reject combined business reports; select a run explicitly.

## Local authenticated API

Initialize the database through replay or another writer first. The server opens
one read-only SQLite connection per request and never creates/migrates a database.
It binds only `127.0.0.1`, has eight request slots and socket timeouts. Set a random
token in the process environment; do not commit it, put it in query strings or
share it in notebook outputs.

```powershell
$env:COFFEE_OPS_API_TOKEN = (& $py -c "import secrets; print(secrets.token_urlsafe(32))")
& $py -m coffee_ops --db var/demo-new.sqlite3 serve --port 8765
```

In another local process with the token available:

```powershell
$headers = @{Authorization = "Bearer $env:COFFEE_OPS_API_TOKEN"}
Invoke-RestMethod -Headers $headers -Uri 'http://127.0.0.1:8765/v1/business-report?date=2026-01-01&timezone=Africa%2FTunis&camera=shop&run_id=demo'
```

Endpoints: `/v1/health`, `/v1/cameras`, `/v1/status?camera=shop`,
`/v1/events?camera=shop&limit=100&after=0`, and `/v1/business-report`.
Events include a continuation sequence and review decision, without evidence disk
paths. Responses disable caching; cross-origin browser access is disabled. A future
dashboard must use these stored read models rather than inventing separate counts.
No dashboard is included in this phase.

This standard-library server is for a local pilot. Python explicitly advises
against production use of [http.server](https://docs.python.org/3.13/library/http.server.html).
Remote hosting requires a reviewed production server, TLS/access policy, secret
rotation, load tests and deployment approval. Do not expose the loopback server
through a public tunnel or change its bind address as a production shortcut.

## Corrections and failure recovery

```powershell
& $py -m coffee_ops --db var/demo-new.sqlite3 review-crossing --event-id EVENT_ID --decision rejected --note 'Reviewed source clip: boundary calibration error'
```

This appends a revision. Reports immediately exclude rejected/uncertain crossings;
reconfirmation restores the count. The original evidence remains intact. Product
corrections/POS reallocation are a separate pending workflow.

After a failed frame transaction, stop the damaged in-memory pipeline and replay
from frame zero with the same source/config/run. Committed frames/events deduplicate.
Changed source/config must use a new run. Do not edit the append-only database.
On camera movement recalibrate and start a new run. RTSP reconnect is not yet
implemented; a read failure is explicit and stops the run. A supervised reconnect
must create a visible observation gap and be tested on authorized hardware.

## Monitoring and response

| Signal | Available now | Operator response / missing validation |
|---|---|---|
| Camera/detector/storage status | Health records, read deadlines, errors, HTTP health | Stop on failure; inspect local logs; reconnect trial pending |
| Data freshness | Processing timestamp and last capture timestamp; status masks stale tables | Distinguish historical replay from a live feed; do not show old observations as current |
| Reliability/coverage | Reliable/unreliable frames, unknown tables, traffic calibration flag, time coverage | Investigate missing intervals before interpreting falling counts |
| Timing | p50/p95/p99 and stage samples, drops | Set a measured latency budget; child decode/GPU telemetry still needed |
| Geometry/video quality | Dimension mismatch rejection and camera-motion latch | Recalibrate; blur/lighting/occlusion monitors remain planned |
| Database | WAL, indexed reads, transactions, single writer | Monitor disk externally; long-term archival and retention design pending |
| Event quality | Per-class scoring, human traffic reviews, uncertain rate | Re-label independent clips before calling count shifts model drift |
| Business quality | POS-only sold units; explicit video scope and unknown occupancy | Count changes can reflect business demand, coverage or model errors |

Use camera-offline/storage-unavailable as errors; unresolved calibration/coverage as
warnings; count distribution changes as review signals. Severity and uptime targets
are proposed operational policy, not validated SLAs. GPU memory/usage, process-tree
RSS and multi-camera sustained capacity are not fully monitored.

## Backup, retention and rollback

Use SQLite's [online backup API](https://docs.python.org/3.13/library/sqlite3.html#sqlite3.Connection.backup)
to a **new** protected file, then test restore on a separate copy. Copying only the
main file while WAL writes are active is not a verified backup procedure. Keep
source/config/model checksums with the backup. Reader credentials and camera URLs
must stay out of artifacts. New live runs persist only a source hash; older ledgers
may contain camera URLs and need an owner-directed access/credential review.

`prune-evidence` handles only pipeline-generated JPEG expiry; run it only under the
chosen retention policy. It does not archive ledger history, annotations, source
videos or model checkpoints. No automatic deletion of those assets is implemented.
Keep privacy masks, restricted raw-video access and authorization records as in
[PRIVACY.md](PRIVACY.md). No face recognition or cross-visit identity is implemented.

Preserve a known-good config/runtime and checkpoint before upgrades. Promotion and
rollback use the existing registry with real held-out evidence; notebook ZIPs are
not promoted automatically. The original Torch pins have known advisory debt:
validate a patched matched Torch/TorchVision pair separately before production.
