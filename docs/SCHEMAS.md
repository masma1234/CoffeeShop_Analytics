# Data contracts and operational semantics

The optional video path adds model backend rtdetr_v2, checkpoint_directory,
image_size and half; preparation/pickup zones; and opt-in rules.product_evidence.
Embedded class IDs/names still match exactly. Weight/config/processor checksums
bind local safetensors provenance. [The video contract](VIDEO_PROTOTYPE.md) describes
PTS journals, raw versus accepted detections and source-bound reviewed annotations.

Configuration is JSON, validated by `coffee_ops.config.Config`. `config/example.json`
is a complete working schema example. Its version and canonical content hash are
persisted for every run. Unknown top-level/nested keys and duplicate JSON keys fail.
Frame dimensions, polygon bounds/area/intersections, capacities, timeouts and mappings are
validated. Class IDs may be sparse, but must exactly match embedded model metadata;
the application never assigns meanings to another model's IDs.

## Pipeline interfaces

* `Detector.detect(frame, frame_index) -> list[Detection]`: class ID, xyxy pixel box,
  confidence. `close()` releases resources. `YOLODetector` and explicitly selected
  `FixtureDetector` implement this; fixture use is recorded in model health.
* `ObjectTracker.update(detections, timestamp) -> list[Observation]`: track ID, box,
  class, confidence, birth/last-seen times, hits, missed flag and quality ratio.
* `POSAdapter.orders() -> Iterable[dict]`: `FilePOSAdapter` and `MockPOSAdapter`.
  Future REST adapters must supply the same validated order-line contract.
* `EventStore`: minimal append/read protocol. `SQLiteStore` exposes additional
  repository methods for matching, reporting and ownership. All SQL lives in that
  adapter. PostgreSQL must implement its projections, leases and transaction semantics.

Tracking IDs are scoped to `(run_id, camera_id)`, never a person's identity.
Person center points determine membership; seat occlusion or overlap can produce
unknown states. Stored `age_seconds`, `quality`, `missed`, zone entry and table
assignment fields explain track quality; there is no biometric identification.

## POS lines

CSV headers or JSON list entries:

```json
{
  "order_id": "order-123",
  "line_id": "1",
  "revision": 1,
  "timestamp": "2026-11-01T10:15:00+01:00",
  "sku": "COFFEE",
  "quantity": 2,
  "payment_status": "paid",
  "camera_id": "shop",
  "zone_id": "T1",
  "channel": "table",
  "terminal_id": "terminal-1"
}
```

`revision` defaults to 1. `channel` and `terminal_id` are optional. All other fields
shown are required. Positive integer quantities only. Allowed states: paid, pending,
cancelled, refunded. SKU must map to a configured class. Repeated identical imports
are no-ops; same line/revision with different content fails atomically. Increase
revision to change payment state; order timestamp/SKU/quantity/camera/zone remain
immutable. Corrections need a separate line. Latest revision wins even if received
out of order. Partial refunds and financial amounts require a future financial ledger.

All timestamps are normalized to UTC with explicit offsets required. Daily reports
group by order capture date, not import date. Refund revisions restate that date's
derived unit total; older daily aggregate versions remain available.

Matching requires camera, product class, time window, observed source/destination
zone, confidence and remaining paid quantity. Ambiguity stays unresolved. Quantity
tolerance is deliberately zero in this MVP. One product track can allocate at most
one paid unit; repeated movements of it cannot inflate sales. ID switches can still
split a physical object into distinct tracks. A paid association is not proof of who
ordered or paid. Exit events can correlate to a table order after entry and no later
than the exit timestamp, but
never receive `confirmed_sale` or a claim about a particular customer's payment.

States: `observed`, `confirmed_sale` (matched paid POS unit), `likely_sale` (pending
order), `order_correlated` (exit/table-order correlation), `payment_unmatched`,
`inventory_discrepancy`, `needs_review`, and `sale_correlated_movement`. Placements
and disappearances alone never allocate sales. Disappearance of an already allocated
track is correlated to that earlier sale without consuming another unit. Operational
alerts remain open until reviewed, even if later POS data explains the event.

## Events and evidence

Each movement stores event ID, UTC timestamp, run/camera, class, track ID, source and
destination zones, confidence, evidence frame index/timestamp, status and nullable
linked order field. Raw visual events never change. Reconciliation results carry the
linked order/line, status, POS context digest and association confidence separately.
`confirmed_sale` means a paid POS unit was allocated by the configured heuristic;
reports always sum the independent POS ledger for confirmed units.

Alert fields include severity, reason, confidence, related tracks/events, timestamp,
evidence, resolution, false-positive field and human-review requirement. Feedback is
an append-only revision. Optional JPEG captures are keyed by run/camera/frame and are
disabled by default. Timestamp evidence remains available after JPEG retention;
the JPEG reference may then be expired. The run stores a source content hash; retain
a private mapping between hashes and authorized source recordings for review.

## Storage

SQLite WAL, explicit immediate transactions, immutable record IDs, SQL triggers
preventing record updates/deletes. One frame transaction includes frame fingerprint,
observations, occupancy, tracks, events, inventory and alerts. Conflicting replay
fails instead of silently accepting a different interpretation under the same key.

Record kinds: `runs`, `cameras`, `zones`, `class_catalog`, `model_versions`, `frames`,
`observations`, `people_tracks`, `product_tracks`, `occupancy`, `occupancy_sessions`,
`events`, `orders`, `reconciliations`, `inventory_movements`, `alerts`, `feedback`,
`model_feedback`, `daily_aggregates`, `health`, `failures`, `evaluation_results`,
`model_registry`. Allocation tables enforce one visual event per allocation and
one sold unit per track. Database history grows on disk; active tracking, decoder
queue and runtime sample memory are bounded. Offline evaluation/export loads the
selected dataset and is not intended as a bounded streaming service.

Current snapshots become unknown when processing stops or the latest health record
is older than 60 seconds. Health uses processing UTC, while observations use capture
UTC. File POS health is a snapshot status; it cannot detect an external POS outage
between imports. Failed imports create integration-unavailable alerts.

Version 2 adds indexed `heads`/`order_heads` projections updated atomically with
records. Migration rebuilds them from version 1 without changing history. A newer
unknown schema is rejected. Reconciliation uses bounded 200-event transactions and
indexed candidates. Reports hold a consistent read snapshot during concurrent POS
changes. Resolved alerts are filtered before pagination. Renewable camera leases
exclude concurrent workers; expired owners cannot renew a replacement's lease.

Use consistent SQLite backups; copying the file without its active WAL is unsafe.
Automatic historical retention and distributed coordination are not implemented.
Use local disk, one connection per thread/worker and separate camera IDs. Do not
place the database on a network filesystem.
