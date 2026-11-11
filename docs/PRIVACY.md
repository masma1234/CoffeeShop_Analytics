# Privacy and operator controls

This MVP processes anonymous, session-scoped object tracks. It has no face recognition,
biometric templates, customer names, audio capture or cross-camera identity linkage.
Track IDs are not identities. Video events do not establish intent, theft or payment;
use neutral review states and have an authorized person assess context.

Before collecting footage, the shop operator must establish the applicable local
requirements for camera placement, notice, lawful use, workplace monitoring, employee
consultation and customer/employee rights. Requirements depend on location and use;
this repository does not supply a legal determination or a jurisdictional compliance
claim. Obtain appropriate local guidance. Explain purpose, review practices and
retention in notices; avoid filming private areas or screens containing payment data.

The CLI is local only; no unauthenticated network API is started. Access control is
currently the operating-system account and filesystem ACLs. Restrict model, footage,
database, evidence and backup directories to authorized operators/reviewers. A future
web service must add authentication, role-based access, TLS and audit logging before
exposure. Do not share stream credentials in reports or shell history. The current
CLI logs error messages; review logs before sharing because source paths can occur.

Use encrypted disks and protected backups. SQLite itself is not encrypted and the
repository does not implement key management. Load only trusted local model artifacts;
checksums establish consistency, not trusted authorship. Run the detector under an
appropriately restricted OS account; its worker process is a timeout boundary, not a
security sandbox.

JPEG evidence capture defaults to off. When enabled, `evidence.retention_days` and
`prune-evidence` remove only pipeline-generated JPEGs in the configured directory.
Schedule this command with your approved OS scheduler. Source videos are never copied
or retained by replay; manage their retention in the recording system. Append-only
timestamps and expired-image references remain in the ledger. Disclose this distinction
to operators. Avoid sensitive free-text feedback and unnecessary evidence exports.

Database/event retention is not automated. The operator must select a retention period
and implement approved archival/purge with verified backups and access auditing before
long-term deployment. Append-only SQL triggers intentionally prevent ad-hoc deletion;
a planned retention migration is needed. Do not promise deletion of historic data from
this MVP simply because JPEG retention ran. Limit access to archives and backup copies.

The event log, POS revisions, model registry and reviewer feedback provide a technical
change trail, but there is no authenticated actor attribution, tamper-resistant audit
service or read-access audit yet. Add those controls before multi-user deployment.
Alerts remain review candidates; record false positives and corrections, and do not
use these outputs alone for adverse action against customers or employees.

The foundation pass adds a bearer-authenticated **loopback-only** read API with
read-only SQLite connections. It excludes raw images/evidence paths from event
responses, disables caching and rejects cross-origin browser access. This is not a
production identity/access-management service. Actor attribution, TLS/remote hosting,
read auditing and secret rotation still need a deployment design.
New live runs persist a source URL hash; prior ledgers may contain credential-bearing
URLs. No historic data was deleted. Owners should review access/credentials for such
databases. Traffic review notes must reference evidence without identifying people.

annotate-video intentionally writes processed imagery and optionally sampled JPEGs.
Treat review outputs as sensitive as the source. Original source bytes are unchanged,
but output retention is not automatic. Keep outputs local with approved access and
expiry; no hosted upload or external video inference is performed.
