# Post-publication release audit, 15-16 November 2026

17 November continuation: the [current release gates](../../GITHUB_READINESS.md)
and [verification evidence](release-verification-20261117.json) record a separate
RT-DETR image with zero findings and five passing quality profiles. The Debian
findings and licensing/reference decisions below are retained as dated evidence;
the original image's packages have not been declared fixed.

**Public source is available; production release remains blocked.** This audit
prepares local documentation and evidence for review. It does not authorize
publication, deployment, a license choice or removal of reference documents.
Evidence collection began 15 November; the final local review completed
16 November. Vendor pages and scanner records retain their individual timestamps.

## Verified publication and evidence provenance

Local HEAD and the remote `audit/deep-clean-20261115` ref resolve to
`097c1bd76d6c37efeb43fdab41dde9d6076596e7`, parent
`ef598c0bcabcd49289ce3f67aef600a274b54df3`. The working tree was clean at the start.
The repository is [public](https://github.com/masma1234/CoffeeShop_Analytics).
The audit changes are uncommitted local review material.

The 192-file cleanup inventory was taken before adding
`docs/audits/deep-clean-20261115.md` and `.json` in `ef598c0`. That commit's
194-file tree is also the tree size of `097c1bd`; the latter changed only readiness
documentation. This is a timing difference, not two omitted application files.

[Actions run 43731027661](https://github.com/masma1234/CoffeeShop_Analytics/actions/runs/43731027661)
matches the published commit. All four Windows/Ubuntu CPU/video jobs passed.
The image-security job failed both the high/critical gate and the independent
root-LICENSE check. Scanning and evidence upload completed.

The actual downloaded `image-security-evidence`, artifact **14168039662**, has ZIP
SHA-256 `e34b8c6a493d34ed1c6ba818021742a92f68805731a82d5bb6eeba5ff71d0436`.
It contains `trivy.json`, `sbom.cdx.json`, `licenses.json`, `image-metadata.json`,
`container-check.json`, `source.sha256` and `runtime.tar.sha256`.
All **194 source hashes** match Git blob bytes at the published commit.

The published Docker inspection ID is an OCI index digest starting `d4049667`;
Trivy records an image-config digest starting `56db460d`. These represent different
objects. All 14 ordered root filesystem DiffIDs agree between the two reports.
The original image tar was not uploaded, so its checksum cannot independently be
recomputed from the downloaded artifact. The fresh local export is hashed and
scanned separately; it is not claimed to be the original CI image.

## Security findings and remediation assessment

The actual report has **62 matches: 61 HIGH, 1 CRITICAL**, across **24 advisories,
23 binary packages and nine Debian source packages**. The image reports Debian
13.7. The SBOM has 177 components, including its root component; Trivy inventories
176 packages. The Python license inventory contains 36 distributions. No
high/critical Python-package finding appears in this report. That does not certify
all embedded native libraries or establish that no vulnerabilities exist.

The [JSON companion](post-publication-20261115.json) enumerates **every match** with
package, exact installed version, advisory, severity, source component and a
reference to its vendor assessment/remediation. No match was removed, downgraded,
ignored or converted into a waiver.

All 24 Debian tracker pages were fetched on 15 November. Each currently labels
trixie vulnerable, including its listed security update where present. Fixed
versions below are **Debian unstable versions**, not compatible upgrades already
available from the image's stable repositories. The installed/candidate comparison
is retained with the local rebuild evidence.

| Advisory | Source component | First fixed Debian unstable version |
|---|---|---|
| [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720) | ncurses / infocmp | 6.6+20251231-1 |
| [CVE-2026-113351](https://security-tracker.debian.org/tracker/CVE-2026-113351) | Expat reset accounting | 2.10.0-1 |
| [CVE-2026-115506](https://security-tracker.debian.org/tracker/CVE-2026-115506) | Expat entity amplification | 2.10.0-1 |
| [CVE-2026-117610](https://security-tracker.debian.org/tracker/CVE-2026-117610) | Expat empty external entity | 2.10.0-1 |
| [CVE-2026-118370](https://security-tracker.debian.org/tracker/CVE-2026-118370) | Expat extreme attribute counts | 2.10.0-1 |
| [CVE-2026-119373](https://security-tracker.debian.org/tracker/CVE-2026-119373) | SQLite FTS5 doclists | 3.54.1-1 |
| [CVE-2026-119374](https://security-tracker.debian.org/tracker/CVE-2026-119374) | SQLite FTS5 secure delete | 3.54.1-1 |
| [CVE-2026-119379](https://security-tracker.debian.org/tracker/CVE-2026-119379) | SQLite session changesets | 3.54.1-1 |
| [CVE-2026-16742](https://security-tracker.debian.org/tracker/CVE-2026-16742) | systemd-homed authentication | 261.2-1 |
| [CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369) | libacl pathname operations | 2.4.0-1 |
| [CVE-2026-6653](https://security-tracker.debian.org/tracker/CVE-2026-6653) | libxml2 internal subset; CRITICAL | 2.14.5+dfsg-0.1 |
| [CVE-2026-74860](https://security-tracker.debian.org/tracker/CVE-2026-74860) | libxml2 Python SAX binding | 2.15.3+dfsg-1 |
| [CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642) | util-linux mount hooks | 2.42.3-1 |
| [CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408) | util-linux nsenter/cgroups | 2.42.4-1 |
| [CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409) | util-linux detached subdirectory mount | 2.42.3-1 |
| [CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410) | util-linux restricted bind mount | 2.42.3-1 |
| [CVE-2026-86138](https://security-tracker.debian.org/tracker/CVE-2026-86138) | libxml2 dictionary allocation | 2.15.4+dfsg-1 |
| [CVE-2026-86139](https://security-tracker.debian.org/tracker/CVE-2026-86139) | libxml2 URI escaping | 2.15.4+dfsg-1 |
| [CVE-2026-86140](https://security-tracker.debian.org/tracker/CVE-2026-86140) | libxml2 validation formatting | 2.15.4+dfsg-1 |
| [CVE-2026-86142](https://security-tracker.debian.org/tracker/CVE-2026-86142) | libxml2 XPointer | 2.15.4+dfsg-1 |
| [CVE-2026-86143](https://security-tracker.debian.org/tracker/CVE-2026-86143) | libxml2 output callbacks | 2.15.4+dfsg-1 |
| [CVE-2026-86144](https://security-tracker.debian.org/tracker/CVE-2026-86144) | libxml2 XInclude flags | 2.15.4+dfsg-1 |
| [CVE-2026-88806](https://security-tracker.debian.org/tracker/CVE-2026-88806) | libX11 XKB reply parsing | 2:1.8.14-1 |
| [CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538) | Perl Archive::Tar allocation | 5.42.3-1 |

### Versioning, reachability and safe changes

Debian revisions, epochs, `~deb13u1`, binary rebuild suffixes and `+really` must be
interpreted using Debian's source-package status. For example, the installed
libxml2 `2.12.7+dfsg+really2.9.14-2.1+deb13u3` contains the older 2.9.14 code line;
the prefix is not proof that the upstream 2.11.0 fix is included. Debian explicitly
explains its reversion and still marks CVE-2026-6653 vulnerable. Its minor-issue
triage does not remove the scanner's CRITICAL result.

Two cases require further vendor/source-patch clarification. For CVE-2026-78409,
the [upstream advisory](https://github.com/util-linux/util-linux/security/advisories/GHSA-8f2p-47x3-43mv)
lists an affected range starting at 2.42, while Debian marks the installed 2.41.5
line affected. For CVE-2026-86139, Debian's note about introduction in 2.13.0 raises
a similar question for its reverted libxml2 branch. Neither discrepancy proves a
false positive without examining the actual Debian patches. Both remain unresolved.

Source-package matching also propagates findings to binaries that may not contain
the vulnerable feature. systemd-homed is different from libsystemd0/libudev1;
Archive::Tar is different from perl-base; infocmp is different from terminfo data.
The rebuilt image probe found **no systemd-homed executable, no Archive::Tar
module and no libxml2 Python module**. The `infocmp` tool is present. Python
actually uses Expat **2.9.0** and SQLite **3.46.1**, with both FTS5 and session
support compiled in. Those libraries are not merely unused package metadata.
Application source has no FTS5/session calls, but malformed database handling and
future code paths remain concerns. No claim of
62 independently exploitable application defects follows from 62 package matches.
Conversely, absence of a known application call path does not establish a fix.

The safest immediate attempt was a **no-cache rebuild of the existing production
target**, including its current `apt-get update` and stable `apt-get upgrade`.
The refreshed apt candidate check covers all 23 affected binary packages:
**every installed version equals the candidate; no stable upgrade is available**.
No supported, tracker-confirmed fixed trixie version was found for these advisories.
No dependency lock, base digest or application source was changed on speculation.
No sid/testing packages, hand-edited dependency metadata or version relabeling was
introduced. The rebuild and full rescan results are recorded below.

For a durable reduction, evaluate a separate headless inference dependency
profile, then regenerate locks and test native inference and video codecs. Simply
substituting `opencv-python-headless` does not satisfy Ultralytics' declared
`opencv-python` dependency; installing both causes a competing `cv2` namespace.
A supported base migration or reviewed stable backports must address the remaining
core libraries too. Manual SQLite replacement needs ABI, corruption, backup and
restore testing; ACL 2.4.0 introduces symbols with known collision risks; Debian
postpones the Perl fix while upstream regressions are resolved. These are reasons
to test a coherent replacement image, not to mix distributions for a green scan.

## Licensing decisions, not an invented license

The repository has no owner-selected root LICENSE. Public visibility alone does
not grant general reuse rights; GitHub's public-view/fork permissions do not
replace a project license. See [GitHub's no-license guidance](https://choosealicense.com/no-permission/).
Ownership and authority over contributions still need confirmation.

Ultralytics **8.3.163** supplies
[AGPL-3.0 text](https://github.com/ultralytics/ultralytics/blob/v8.3.163/LICENSE).
The shipped `ultralytics-thop` **2.2.5** also declares AGPL. Selecting an Apache or
MIT license for original code cannot relicense either dependency or remove
obligations on a combined covered work. AGPL allows commercial use; distribution
and modification obligations still apply, and section 13 requires a source offer
to remote users of a modified covered program supporting network interaction.
The precise combined-work boundary needs review for the intended distribution.
Ultralytics offers an [Enterprise alternative](https://www.ultralytics.com/license);
its publisher guidance is not a substitute for the actual license or a signed
contract covering the required code, weights, redistribution and deployment.

| Owner option | Practical consequence |
|---|---|
| Open the covered application under AGPL-3.0 | Lowest dependency-change path for the current YOLO integration, if the owner accepts the applicable source-sharing and notice obligations and has authority over the code. A license file alone is not a complete compliance process. |
| Retain YOLO under an appropriate Enterprise agreement | Allows terms negotiated for the intended closed/commercial distribution. Verify coverage of Ultralytics, THOP, weights and all deployment scenarios before choosing the original-code license. Other dependency obligations remain. |
| Build a reviewed permissive inference profile | Remove AGPL dependencies from that distribution and validate an RT-DETR/Transformers or other compatible implementation, all transitive licenses and checkpoint terms. Only then consider Apache-2.0, MIT or proprietary terms for owner-controlled code. |

**Recommendation:** use the AGPL route if the intended product is fully open under
its conditions; for a closed commercial product, compare an Enterprise agreement
with a separately tested permissive RT-DETR profile. The owner must select the
business/licensing direction. None has been implemented and no LICENSE was added.

Torch and Torchvision are not AGPL dependencies. Their exact
[Torch 2.13.0 notice](https://github.com/pytorch/pytorch/blob/v2.13.0/LICENSE) and
[Torchvision 0.28.0 notice](https://github.com/pytorch/vision/blob/v0.28.0/LICENSE)
contain BSD-style terms, but the Torch wheel declares a composite expression:
Apache-2.0, Apache-2.0 WITH LLVM-exception, BSD-2-Clause, BSD-3-Clause, BSL-1.0
and MIT. Preserve vendored notices as well as the main license.

The full 36-package metadata inventory is retained. Other obligations include
certifi's MPL-2.0, tqdm's MPL-2.0/MIT expression, NumPy/SciPy bundled notices,
Matplotlib's PSF-based terms and Pillow's MIT-CMU. Jinja2 3.1.6 appears UNKNOWN in
the simple metadata inventory, but its installed notice and
[versioned license](https://github.com/pallets/jinja/blob/3.1.6/LICENSE.txt) establish
BSD-3-Clause terms. UNKNOWN metadata is not automatically an unknown legal license.
OpenCV's Apache-2.0 metadata is incomplete for its binary distribution: its
`LICENSE-3RD-PARTY.txt` documents bundled FFmpeg under LGPL-2.1 and non-headless
Linux Qt under LGPL-3.0. Debian base packages also carry their own notices and,
where applicable, corresponding-source obligations. An SBOM and license strings
do not certify redistribution compliance.

Dataset, model checkpoint and media terms are separate. For example,
[PekingU/rtdetr_v2_r18vd](https://huggingface.co/PekingU/rtdetr_v2_r18vd) declares
Apache-2.0; this does not license the project's reference PDFs or café recordings.
Before adding trained weights, retain the exact model revision/hash, model card,
training-data provenance, required citations/notices, commercial/redistribution
restrictions and rights to the footage. Hosting on Hugging Face or Kaggle alone
does not grant those rights. No weights or datasets were added by this audit.

## Public binary-content review

Both PDFs were text-extracted and all 34 pages rendered and visually inspected
as contact sheets. PDF metadata, links, annotations and attachments were checked.
The DOCX XML, metadata, relationships, comments and embedded images were inspected;
its three embedded diagrams were rendered separately. The benchmark PNG was also
viewed and compared with its accompanying performance report.

| File | Findings | Recommendation pending owner approval |
|---|---|---|
| `Solutions et ressources pour un système d’analytics de ventes et de commandes de coffee-shop.pdf` | 18-page research report; metadata says ChatGPT Deep Research/ChatGPT/WeasyPrint. Public vendor/research citations, diagrams, generic schemas and pricing comparisons. No attachments or annotations. | Not needed to run, test or build the application. Prefer a private research archive and concise public links/provenance notes after rights review. |
| `Système analytique de ventes et commandes pour coffee shops _ jeux de données, architecture, APIs, E.pdf` | 16-page research report with the same generator metadata, public citations, SQL examples, architecture and planning diagrams. No attachments or annotations. | Same recommendation. It discusses proposed architectures, not the implemented application's release status. |
| Same-title `.docx` | Research-export counterpart; custom property says ChatGPT Deep Research, core author absent, placeholder 1970 timestamps, Word application metadata. Empty comments, no tracked edits, three diagrams, no embedded executable/object package. | Redundant editable reference; private archive is more appropriate unless redistribution rights and public necessity are confirmed. |
| `docs/benchmarks/model_latency.png` | Chart of local detector timings, RTX 3050 hardware and explicit scope limits. No photos, faces, customer records or credentials. Values/labels correspond to the published performance table. | Useful public evidence after the owner confirms origin/rights. Retain its dated methodology and limitation statements. Exact plot-generation provenance is not established merely by matching the table. |

No private customer/employee records, credentials, personal contact information,
local usernames or internal host addresses were identified in the inspected
documents. Public citation authors, public GitHub handles, brand names, generator
metadata and the chart's hardware description are identifying information, but
are not evidence of leaked private café records. This is a bounded content review,
not proof that no hidden or external private information can exist.

Generated-document metadata is not proof of ownership or permission to republish
third-party text, logos or diagrams. The originating account, input rights and
third-party reuse permissions are not established by this repository. None of
these four files was deleted or modified. A future removal from the current tree
would not erase earlier public commits; any history treatment needs separate
authorization and a specific reason.

## Verification results

The production target rebuilt successfully without cached build steps. Its OCI
index digest is `b4ac8c8245dab6565e74692f3f57d942934bb1d22fcfb75d13eb58f3b378df4d`;
the exported tar SHA-256 is
`0a93136e6d00a0bbc05e9441d62b0640098c86a7c80a4b32179ec0a19a2e0e60`.
Trivy 0.76.2 scanned that export with the database updated
`2026-11-15T18:56:37Z`. The full OS/Python scan and CycloneDX generation completed.
**The rebuilt image still has exactly the same 62 high/critical package/advisory
tuples; none was fixed.** Its new SBOM has 177 components. The unchanged security
threshold exits 1, and the missing-LICENSE check exits 1.

The actual production-image probe passed UID 10001, read-only root, authenticated
private endpoints, no published ports, blocked public/private/metadata TCP/UDP
egress, native CPU NMS, untrained-architecture inference and graceful exit checks.
No trained-model accuracy was tested. Docker was configured with a three-second
SIGTERM grace period and the process exited 0 with its stopped marker. Host
`docker stop` wall time was **9.86 seconds** during concurrent build/testing; the
script does not enforce a three-second host command duration. This is not evidence
of a three-second end-to-end shutdown SLA. The README now makes that distinction.

All four local profiles completed all nine quality checks with exit code 0:

| Profile | Pytest | Subtests | Statement coverage | Acceptance |
|---|---|---|---|---|
| Windows CPU | 186 passed, 19 optional-video skips | 41 passed | 73.42% | Passed |
| Windows video | 205 passed, no skips | 48 passed | 83.90% | Passed |
| Linux CPU | 186 passed, 19 optional-video skips | 41 passed | 73.42% | Passed |
| Linux video | 205 passed, no skips | 48 passed | 83.69% | Passed |

Each profile also passed dependency consistency, native backend doctor,
configuration validation, Ruff **E9/F** checks and mypy with checked untyped bodies
over **36 application files**. Acceptance reruns unittest and 21 CLI checks,
including expected rejection cases and repeated-replay consistency. Coverage is
statement coverage, not branch coverage, exhaustive robustness or model accuracy.
The source files and dependency locks were unchanged throughout this audit.
Only README/readiness documentation and the two new audit files are proposed.

Windows setup used a new environment and all hashed runtime requirements from a
clean `git archive` of the published commit; optional video requirements were
installed after completing the CPU profile. A separate local clone made without
hardlinks was clean at the same commit, all 194 file bytes matched the archive,
and configuration validation succeeded from that clone. Linux profiles used the
actual rebuilt `test` and `video-test` Docker targets with network access disabled
during tests. This verifies setup from clean source, but optional/dev dependencies
and apt resolution remain time-dependent, as documented in the README.

All local Markdown targets exist. External checks covered **272 unique links**:
268 returned HTTP 200; two Roboflow dataset pages returned 403 and Figshare/Harvard
Dataverse pages returned 202. Those four require manual access/content confirmation;
they are not silently counted as verified. HTTP success establishes reachability,
not factual accuracy or license rights. Markdown fragment anchors and fenced
example URLs are outside the local-target check's scope.

### Secret and identifying-content review

The publication scanner covered 194 candidate files and 262 reachable text blobs
across all seven local commits. It found the intentionally synthetic RTSP URL
credential in `tests/test_traffic.py` and the same historical blob. Gitleaks 8.30.1
scanned all seven commits and returned a nonzero result for four generic-key
candidates in the original benchmark JSON reports. Each is a 64-hex source hash
whose value was independently recomputed from the referenced file at that commit.
All four are verified source-integrity hashes, not API keys. The raw redacted
findings, scanner exit status and per-finding explanations are retained; no
allowlist or suppression was installed. Finite scanners do not prove absence of
every possible secret or private record.

Gitleaks also scanned the **196-file local publication candidate** (194 tracked
files plus these two new audit files), including archive traversal to depth two.
The initial candidate scan reported the same four source hashes. The final scan
also flagged the checksum of `candidate-secret-triage.json` in this audit's new
evidence manifest. That fifth match was independently recomputed and is an audit
file SHA-256, not a credential. All five remain in the scanner's raw nonzero
result, with their explanations retained and no suppression added.
The published tree remains 194 files until a separately approved commit/push.

A separate content check found **19 local-user-path occurrences in three existing
documents**: `FINAL_ENGINEERING_AUDIT.md`,
`docs/benchmarks/benchmark-environment.txt`, and
`docs/history/release-20261111/RELEASE_EVIDENCE.md`. These identify the local account
and directory layout, not authentication secrets. Git commit author metadata is
also identifying. Historical evidence was preserved; the owner can decide whether
future public copies should redact those paths. The private-network address in
`scripts/verify_egress.py` is a deliberate test destination, not a discovered café
network. No model weights, operational database or real footage are tracked.

## Decisions and production blockers

- Owner selection of the source/distribution licensing route and confirmation of
  contribution rights, followed by actual notice/source-offer implementation.
- Owner approval of reference-document retention or a private archive. No deletion
  or history rewrite is implied by this report.
- A supported production image whose complete unsuppressed scan meets the existing
  high/critical threshold. Component absence and containment are not a green scan.
- Representative labeled café video, camera calibration, sustained performance
  evidence and operational/privacy validation before real-business use.
- Separate approval of the final local diff before any further publication.

Historical reports and their dates are preserved. Raw evidence is ignored under
`var/post-publication-20261115`; it includes local paths and extracted documents
and should not be uploaded wholesale. The JSON companion contains the reviewable
per-finding inventory and hashes of supporting evidence.
