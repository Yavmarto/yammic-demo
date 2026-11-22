# Purpose and site access · Board decision draft

**Status:** Proposed design for local synthetic development. Regulatory re-check pending. [D16 brief](/CEL/issues/CEL-1848#document-g02-fr063-decision) · [Regulatory findings](/CEL/issues/CEL-1849#comment-c02cb9b3-90b7-4959-a3da-6c870dc02178)

## Proposed decision

Require a current operational grant before extracting study data, sending reviewed values to the trial system, or exporting data. Require the same check **when a read runs** before enabling any path that can return participant-level or sensitive results. A bypass or a new multi-site read blocks release of that path until the control and audit evidence pass. [G02](/CEL/issues/CEL-1747#document-d15) · [MVP acceptance criteria](/CEL/issues/CEL-1745#document-artifact-review-daee312e-93c1-4186-aec0-1c122e04b292)

- **Authorization.** A named site authority issues and can withdraw the operational grant. It records its issuer, proof of approval, effective dates, status, study and protocol version, purpose, institution and site/node, authenticated user or service identity, role, permitted action and field scope. Bind each operation to the authorized EHR source, trial-system tenant, or allow-listed export recipient and destination as applicable. Service identities can run delegated actions. A person approves reviewed values.
- **Separate evidence.** Consent or waiver evidence is a separate record. For synthetic tests, use fictional grants and evidence references. Before a real-data pilot, site and Regulatory owners must confirm which evidence is required and how it affects grants. [Gate 2 decision](/CEL/issues/CEL-1750#document-gate-2-decision)
- **Failure and retry.** Deny before access or movement when a grant cannot be verified, is malformed, expired, revoked, or outside scope. Re-check current grants before each retrieval, write, release, or queued retry. Revocation invalidates cached allow decisions. If receipt is uncertain, reconcile it before repeating the write.
- **Audit and retention.** Record the decision, reason, policy/grant version, effective revocation time and scope where applicable, actor, action, site, and delivery result. Keep values and free text out of these decision logs. Use participant linkages only where reconciliation needs them and keep the re-identification key at the site. The named site data steward owns access, integrity checks and the retention and deletion schedule for grant evidence and audit events. Site and Regulatory must approve that schedule before a pilot.

Extend the existing D16 matrix with tests for unusable grant records, revocation between retries, wrong destination, consent evidence without an operational grant, and a read that would return out-of-scope results. Record a denial and confirm that no data moved in each case. [D16 test matrix](/CEL/issues/CEL-1848#document-g02-fr063-decision)

Approval of this draft would set the **synthetic implementation scope**. Real data, transfers and outreach remain subject to their existing approvals. [Project governance](/CEL/issues/CEL-1727#document-09-agent-org-and-tasks)
