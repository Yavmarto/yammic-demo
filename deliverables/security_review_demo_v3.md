# Security review — Yamicc demo v3 backend (pre-Board)

**Issue:** CEL-1780 · **Reviewer:** Security Engineer · **Date:** 2026-11-21
**Scope:** `backend/` at `dev`, commit `4810f1f` (W1 + W5; no backend files were modified in the working tree)
**Status:** No Critical findings for the local demo. **3 High**, 7 Medium, 9 Low. CTO owns remediation; no backend code was changed by this review.

> The demo runs on localhost with synthetic data only. Several findings below would be **Critical in production** but are **High for this demo** because reach is limited to the demo machine and the data is not real. Do not lift this code into a hosted environment without fixing SEC-01, SEC-02, SEC-03 and SEC-04.

---

## 1. Executive summary (ranked)

| # | Sev | Finding | Where | Why it matters |
|---|-----|---------|-------|----------------|
| SEC-01 | **High** | JWT signing secret has a committed default and the app does not fail closed. A token for any user/role can be forged with a value in the repo. | `backend/app/security.py:9`, `:25-39` | Full authentication and role-model bypass. Demonstrated: a forged `role=pi` token accepted a review decision; a forged `role=service` token was accepted by `/me`. |
| SEC-02 | **High** | The hash chain is unkeyed and has no external head anchor. A DB writer can delete the newest events undetected, or rewrite the whole chain so `/audit/verify` returns `ok:true`. | `backend/app/audit.py:18-19`, `:44-56`; `backend/migrations/001_init.sql:92-98` | The audit trail is not tamper-evident against the DB role the app uses (which is a Postgres superuser). Demonstrated all three cases against a live DB. |
| SEC-03 | **High** | HAPI FHIR 8.12.0 image has 3 Critical Java CVEs (Spring RCE) + 4 Critical total, is unauthenticated, has CORS enabled, and shares the same Postgres **superuser** as the app. It serves the raw MRN and patient name. | `docker-compose.yml:38,45-51,56-57` | A local browser page or any local process can read raw identifiers and may reach a known RCE; that DB account can then rewrite the audit chain (SEC-02). |
| SEC-04 | **Medium** | Pseudonymisation key has a committed default (`yamicc-demo-pseudonym-key-not-for-production`). The stored HMACs are reversible by dictionary attack with that key. | `backend/app/ingest/pseudo.py:13`, `:16-22`; `sync.py:216-217` | Demonstrated: recomputing HMACs for the seed MRNs reproduced `pseudonym_map` rows exactly (e.g. `MRN-01-00101 → PSN-DD7C3EAA310D`). |
| SEC-05 | **Medium** | JWTs are accepted from `?access_token=` on **every** endpoint, not only SSE, and uvicorn logs the full query string. | `backend/app/security.py:30-32`; `backend/app/routes.py:362-383` | Credential exposure in access logs and proxy/browser history. Demonstrated full JWT in `ops/logs`-style access log. |
| SEC-06 | **Medium** | Read access to PHI-bearing resources is not audited. Only login, decisions, sync and exports write audit events. | `backend/app/routes.py:160-170,188-196,249-262`; `audit.py` | No non-repudiation for who viewed a document/eCRF/audit page. GCP/Annex 11 expect access logging. |
| SEC-07 | **Medium** | Authorisation is global, not site/study scoped. `service` can read everything and export ODM/FHIR; `monitor` can push data back to the hospital FHIR server. | `backend/app/routes.py:18` (ANY), `export/routes.py:15,52-53` | No tenant/institution isolation (07 §4); least privilege is coarse. |
| SEC-08 | **Medium** | All accounts, including the `ai` service account, share password `demo`; no login rate limit; PBKDF2-HMAC-SHA256 uses 60 000 iterations and an 8-byte (64-bit) salt. | `backend/app/seed.py:18-19,57`; `ai/client.py:27`; `security.py:10-16`; `routes.py:53-61` | Service credential is guessable; offline cracking is cheap if the DB leaks. |
| SEC-09 | **Medium** | Container base images have unpatched High/Critical CVEs (postgres 16: 2 Critical/151 High; HAPI: 4 Critical/25 High at scan time). | `docker-compose.yml:15,38` | Priority-3 dependency risk. Most postgres issues are in `gosu`/OS packages with no fix; HAPI's are reachable through its HTTP API. |
| SEC-10 | **Medium** | CORS is `*` on the API, `/docs` and `/openapi.json` are public, and HAPI CORS is on with no auth. | `backend/app/main.py:14-15`; `docker-compose.yml:51` | With SEC-01 this gives a browser-based exploit path to a localhost demo. Docs exposure is reconnaissance. |

**Low** (batched, details in §5): JWT claim/rotation hygiene (SEC-11), unbounded inputs (SEC-12), no TLS/security headers (SEC-13), stale/static DB credentials (SEC-14), verbose errors (SEC-15), pseudonym linkage/key versioning (SEC-16), audit `before`/`after` readable by `service` (SEC-17), no CI security gates/SBOM (SEC-18), local model supply chain (SEC-19).

**Verified clean:** parameterised SQL throughout (no injection found); append-only trigger blocks UPDATE/DELETE/TRUNCATE for the app role; role gates for review/SDV/query/run endpoints behave as designed; pseudonymisation scrubbed MRNs and names in every DB column and API response we tested; Python dependency audit is clean; images are digest-pinned; the FHIR/ODM exports carry no MRN or patient name; no private keys or `.env` files are committed.

---

## 2. Scope, method and limits

**Reviewed:** auth/JWT/RBAC, the hash-chained audit, pseudonymisation and FHIR ingestion, exports, input validation, CORS, secrets, DB roles and container images. Also read `07_REGULATORY_SECURITY.md` and `deliverables/backend_architecture.md`.

**Method:** code review plus live tests against two scratch databases (`sec_probe`, `sec_probe2`) created in the existing local Postgres container. The long-running demo process on `:8000` was not touched; I ran the current `dev` code on `:8011` and `:8012` with `DATABASE_URL` pointed at the scratch DBs. Scratch DBs and test processes were removed after the review.

**Commands run (representative):**
```bash
# role matrix
curl -s -X POST :8011/auth/login -d '{"username":"monitor","password":"demo"}' ...   # 200
curl -s -X POST :8011/extractions/EXT-0009/decision -H "authorization: Bearer $MON" # 403
curl -s -X POST :8011/participants/GBM-NL-001/extraction-runs -H ... $MON          # 403
# forged token with the repo default secret
# (HS256 over {"sub":"ghost","role":"service"}) -> GET /me 200, role=service
# audit
docker exec -i yamicc-postgres psql -U yamicc -d sec_probe -c "ALTER TABLE audit_event DISABLE TRIGGER USER; DELETE FROM audit_event WHERE seq=(SELECT max(seq) ...); ALTER TABLE audit_event ENABLE TRIGGER USER;"
curl -s :8011/audit/verify                                                           # {"ok":true,...} after tail delete
# pseudonymisation
# recomputed HMAC-SHA256(default key, "mrn:"+MRN) -> matched pseudonym_map rows exactly
# containers
trivy image --severity HIGH,CRITICAL --scanners vuln <postgres digest>
trivy image --severity HIGH,CRITICAL --scanners vuln <hapi digest>
cd backend && uv run --with pip-audit pip-audit                                     # No known vulnerabilities found
```

**Limits:** local host only; no DAST/fuzzing beyond the checks listed; no penetration test; no review of the Flutter app or Ollama binary; Trivy is a point-in-time scanner and not every CVE is reachable in this deployment. The synthetic-data disclaimer reduces business impact but does not change the control gaps that would carry into a real deployment.

---

## 3. Findings (High)

### SEC-01 — High — Forgeable JWTs from the committed default secret

**Evidence**
- `backend/app/security.py:9` — `SECRET = os.environ.get("JWT_SECRET", "yamicc-demo-secret-not-for-production-use-1234")`.
- `backend/app/security.py:25-27` — token payload is `{sub, role, name, exp}`, signed HS256; the role in the token is trusted verbatim by `current_user()` at `:30-39`.
- `Makefile:96,137` starts the backend without `JWT_SECRET`; `ops/RUNBOOK.md` documents no secret provisioning. The running demo on `:8000` had no `JWT_SECRET` in its environment.
- `deliverables/backend_architecture.md:74` acknowledges the default.

**Exploit path (demonstrated)**
1. Read the secret from the repo.
2. Sign `{"sub":"ghost","role":"service","name":"forged","exp":…}`.
3. `GET /me` returns `{"username":"ghost","role":"service"}`; `POST /extractions/{id}/decision` with a forged `role:"pi"` token returned **200**.
4. With SEC-10 (`Access-Control-Allow-Origin: *`), a malicious web page visited on the demo machine can send the forged token to `http://127.0.0.1:8000` and read the response.

**Impact:** complete bypass of the nurse/monitor/PI/service role model the demo is showcasing. Any role can read all synthetic patient data, accept/reject AI proposals, open/close queries, run syncs and export.

**Proposed fix (CTO)**
- Remove the literal default. At startup, require `JWT_SECRET` (≥32 random bytes) and **fail closed** if missing or too short (`raise SystemExit`). Add a `make secret` helper that writes a gitignored `.env`/`ops/run/jwt_secret` with `openssl rand -base64 48`.
- Ensure every start path (`make backend`, `make demo`, the RUNBOOK) loads it; add a startup test.
- Rotate after any exposure. For production, move to the Keycloak/OIDC design in 07 §4 and use short-lived access tokens.

---

### SEC-02 — High — Audit chain is unkeyed and unanchored: tail deletion and full rewrite are invisible to `/audit/verify`

**Evidence**
- `backend/app/audit.py:18-19` — `hash = SHA-256(prev_hash + canonical_json(event))`; no key, no signature.
- `backend/app/audit.py:44-56` — `verify()` walks rows and only checks `prev_hash` links and per-row hashes. It has no expected head/count to compare against.
- `backend/migrations/001_init.sql:92-98` — trigger blocks UPDATE/DELETE/TRUNCATE, but the table and trigger are owned by the app role `yamicc`, which is a **Postgres superuser** (`docker-compose.yml:17-20,45-47`; `ops/RUNBOOK.md:10`). A superuser can `ALTER TABLE ... DISABLE TRIGGER`, then modify/delete/recompute at will.
- `deliverables/backend_architecture.md:67` correctly notes that a removed last event is only visible if an earlier `headHash` is kept. No code stores or compares one.

**Exploit path (all three demonstrated on a live DB)**
1. **Middle modification/deletion:** with the trigger disabled, change `actor` at `seq=5` or delete a middle row. `/audit/verify` returns `ok:false` and the right `brokenSeq` — this part works.
2. **Tail truncation:** delete the newest row (`max(seq)`) with the trigger disabled. `/audit/verify` returns `{"ok":true,"count":61,...}`. The removal is undetected.
3. **Full rewrite:** after modifying a row, recompute `prev_hash`/`hash` for every remaining row in order and write them back. `/audit/verify` returns `{"ok":true,"count":63,"headHash":"d40f…"}` with the forged actor still in row 5. The endpoint is fooled.

**Impact:** the hash chain is tamper-**detecting** for accidental corruption and for a writer who cannot recompute, but it is not tamper-**evident** against a DB-level writer. The app uses a superuser that can do exactly this, and that same credential is shared with HAPI (SEC-03), making the chain reachable through a second service. For Annex 11/GCP audit trails this is a material gap.

**Proposed fix (CTO)** — defence in depth, all three:
1. **Anchor the head externally.** Persist `(count, headHash, lastSeq)` after each write/at least after each run to a store the app DB role cannot rewrite (separate DB/schema with a different owner, a signed append-only file, or the ops log with a rotating MAC). `/audit/verify` must compare the DB head to the anchor and return `ok:false` with `reason:"head mismatch"` on a tail truncation. Alert on mismatch.
2. **Least privilege.** Create a non-superuser app role in a migration: `SELECT, INSERT` on `audit_event`; no `UPDATE/DELETE/TRUNCATE/ALTER`; trigger owned by a separate owner role. Use a different role for HAPI. Revoke the shared `yamicc` superuser from services.
3. **Key the chain.** Use `HMAC-SHA256(AUDIT_KEY, …)` (key outside the repo) or sign the head, so a DB writer cannot recompute hashes. Add regression tests for tail deletion and full-chain rewrite (the current test at `tests/test_api.py:136-160` covers only modification and middle deletion).

---

### SEC-03 — High — Unauthenticated HAPI FHIR with critical CVEs, raw identifiers and the shared superuser DB

**Evidence**
- `docker-compose.yml:38` — `hapiproject/hapi:latest@sha256:0ff8…`; HAPI reports software version **8.12.0** (`GET /integrations`).
- `docker-compose.yml:51` — `hapi.fhir.cors.enabled: "true"`; no authentication is configured. `:56-57` publishes `127.0.0.1:8090`.
- `docker-compose.yml:45-47` — HAPI connects to Postgres with the same `yamicc`/`yamicc` **superuser** as the app.
- Live: `curl http://127.0.0.1:8090/fhir/Patient?_count=1` returns **200** with `MRN-01-00101` and `"Alfa Proefpersoon"`. This bypasses the pseudonymisation layer entirely.
- Trivy (2026-11-21) on the pinned HAPI digest: **4 Critical, 25 High**. Criticals include:
  - `CVE-2026-47884` / `CVE-2026-47890` — Spring `spring-webmvc 6.2.19`, RCE via XsltView / SSE view fragments; fixed in 7.0.9.
  - `CVE-2026-33701` — OpenTelemetry Java agent 2.24.0, RCE via RMI deserialisation; fixed in 2.26.1.
  - `CVE-2026-111497` — `libbrotli1` out-of-bounds write; Debian fix available.

**Exploit path / chain:** a malicious browser page or local process reaches `127.0.0.1:8090` (CORS on, no auth), reads raw identifiers and can attempt the Spring/OTel RCE. HAPI's DB credential is the same superuser as the app, so a compromised HAPI can read `pseudonym_map` and rewrite `audit_event` (SEC-02). The two High findings multiply.

**Impact:** the "pseudonymised platform" guarantee is only true for the platform DB/API; the source FHIR store exposes the MRN and name. On an untrusted network or a shared demo machine this would be Critical.

**Proposed fix (CTO/DevOps)**
- Upgrade HAPI to a release with fixed Spring/OTel (or a patched image). Re-run Trivy and record the result.
- Set `hapi.fhir.cors.enabled: "false"`; the Flutter app never calls HAPI directly (architecture §3), so browser CORS is not needed.
- Stop publishing `:8090` to the host. Put HAPI on an internal Docker network and let only the backend reach it (or firewall to the backend process). If a host port is required for the demo, document the acceptance and keep it bound to `127.0.0.1`.
- Create a dedicated, non-superuser Postgres role for HAPI limited to the `hapi` database. Do not share the app's superuser.
- Add a written risk acceptance for the demo if the image cannot be upgraded before the freeze.

---

## 4. Findings (Medium)

### SEC-04 — Medium — Default pseudonym key makes HMACs reversible
`backend/app/ingest/pseudo.py:13` falls back to `yamicc-demo-pseudonym-key-not-for-production`. `mrn_hmac()` (`:16-17`) is HMAC-SHA256 over `"mrn:"+MRN`, and `pseudonym_map` stores it (`sync.py:216-217`). With the key from the repo, an offline dictionary of plausible MRNs reproduces the stored values. **Demonstrated:** `MRN-01-00101 → PSN-DD7C3EAA310D`, `MRN-02-00102 → PSN-086F9D8BC62F`, etc., exactly matched `pseudonym_map`. **Fix:** require `PSEUDONYM_KEY` (≥32 bytes) at startup, fail closed, keep it outside the repo, and rotate it if it has ever been shared. Document that pseudonymised ≠ anonymous (07 §1). Consider per-study key versions to limit cross-study linkage (SEC-16).

### SEC-05 — Medium — JWT accepted in the query string on all endpoints; logged
`backend/app/security.py:30-32` accepts `?access_token=`; `routes.py:362-383` only needs it for SSE, but the dependency applies everywhere. Live: `GET /participants?access_token=<jwt>` returned **200**, and uvicorn logged the full token in the request line (reproduced: `GET /runs/1/events?access_token=eyJhbGciOi…`). Tokens end up in terminal scrollback, log files, proxies and browser history. **Fix:** accept the query token only on the SSE route, make it short-lived (60 s) and single-use, or switch to a cookie/fetch-based SSE that can send headers; redact query strings in access logs (`--no-access-log` for the demo or a logging filter). Never log `authorization`.

### SEC-06 — Medium — PHI reads are not audited
`GET /participants`, `/participants/{id}`, `/documents/{id}`, `/participants/{id}/ecrf`, `/extractions`, `/audit` do not call `A.record`. Only login, decisions, SDV, queries, syncs and exports are audited. GCP/Annex 11 and 07 §4 expect access trails. **Fix:** add a read-audit event for document/eCRF/participant/audit access with actor, entity, timestamp; throttle repeated reads of the same entity to avoid noise. Add a test that a document read produces an audit row.

### SEC-07 — Medium — No site/tenant scoping; broad service and monitor rights
`ANY = Depends(current_user)` (`routes.py:18`) protects most reads, so any authenticated user (including `service`) reads every site/participant. `export/routes.py:15` lets `service` export ODM/FHIR; `:52-53` lets a **monitor** push a bundle back to the hospital FHIR server (a write to an external system). 07 §4 requires least privilege, RBAC + ABAC and tenant isolation. **Fix:** add `site_id`/study scope to the user model and apply it to every query; restrict `service` to `/runs*` + `/documents` + `/participants/{id}/ecrf`; require `pi` for `push_fhir`; document the matrix.

### SEC-08 — Medium — Weak authentication hygiene
All demo users and the `ai` service account use password `demo` (`backend/app/seed.py:18-19,57`; `backend/app/ai/client.py:27`). `/auth/login` has no rate limit or lockout (`routes.py:53-61`; 8 rapid failures all returned 401). PBKDF2-HMAC-SHA256 uses 60 000 iterations and an 8-byte (64-bit) salt (`security.py:11,15`), below current OWASP guidance (600 000 / 16-byte salt). **Fix:** per-user random passwords for human demos, a separate non-interactive credential for `ai`, rate-limit `/auth/login` (e.g. 5/min/IP + lockout), and raise to `pbkdf2_hmac(..., 600_000)` with a 16-byte salt (or Argon2id). Keep `ai` out of the interactive login path if possible.

### SEC-09 — Medium — Container/base-image CVEs
Trivy on the pinned images at review time:
- `postgres:16@sha256:3950…`: **2 Critical, 151 High**. Criticals: `CVE-2026-6653` libxml2 (use-after-free, no fix at scan), `CVE-2025-68121` Go `crypto/tls` in `gosu`. Most Highs are Debian packages in layers not exercised by the demo.
- `hapiproject/hapi:latest@sha256:0ff8…`: **4 Critical, 25 High** (see SEC-03).
**Fix:** refresh base images before the freeze (and at least record the scan), pin new digests, and triage the HAPI Java CVEs as SEC-03. Add Trivy to CI with a HIGH/CRITICAL gate and an explicit allowlist for unreachable packages; produce an SBOM (07 §4).

### SEC-10 — Medium — Wide-open CORS and public API docs
`backend/app/main.py:14-15` sets `allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]`. Live preflight from `Origin: https://evil.example` returned `access-control-allow-origin: *` and allowed `authorization`. `/docs`, `/redoc` and `/openapi.json` are public (200). With SEC-01 this lets a visited web page forge a token and talk to the local API. **Fix:** restrict to `http://127.0.0.1:8080` / `http://localhost:8080`, disable docs in the demo (`docs_url=None, redoc_url=None` or an env flag), and add `Content-Security-Policy`/`X-Content-Type-Options`/`Referrer-Policy` on the static app. HAPI CORS off as in SEC-03.

---

## 5. Findings (Low — batched)

| # | Finding | Evidence | Fix |
|---|---------|----------|-----|
| SEC-11 | JWT has no `aud`, `iss`, `iat`, `jti`; 8 h TTL; no logout/revocation; role/name are trusted from the token and never re-read from `app_user`. | `security.py:10,25-39` | Add `aud`/`iss`/`iat`/`jti`; shorten to 30–60 min with refresh; re-load the user/role on each request or use a denylist for logout. |
| SEC-12 | Unbounded inputs: login/decision/query text, `confidence`, evidence indices, client-supplied extraction `id`; `action` LIKE wildcards not escaped. | `schemas.py:18-20,197-200,281-285,319-334`; `routes.py:313-321,418-433` | `max_length` on strings; `ge/le` on confidence; validate `0 <= start < end <= len(text)`; server-generate IDs; escape `%`/`_` in LIKE. |
| SEC-13 | HTTP only (localhost), no HSTS/security headers. | `Makefile:96,137`; `main.py` | Fine for localhost; add TLS + headers before any non-local use. |
| SEC-14 | Static DB password `yamicc`/`yamicc`, app role is superuser, HAPI shares it. | `docker-compose.yml:17-20,45-47`; `db.py:6-8` | Dedicated least-privilege roles per service; secrets from env; rotate. (Also required for SEC-02.) |
| SEC-15 | Verbose error detail returned to clients (`/integrations`, `/ai/providers`). | `ingest/routes.py:47-48`; `ai/providers/ollama.py:133-138` | Return a generic message; log detail server-side only. |
| SEC-16 | Pseudonyms are stable across studies (one global key/map); no key version/rotation; map is global. | `pseudo.py:13-22`; `migrations/002_ingest.sql:10-13` | Per-study key/namespace, key-version column, documented rotation and linkage risk. |
| SEC-17 | `/audit` (ANY user, including `service`) returns `before`/`after` that can contain clinical values. | `routes.py:308-322` | Restrict audit to PI/monitor; minimise clinical values in `after` or mask them. |
| SEC-18 | No CI security gates, SBOM, secret scanning or dependency updates; `latest` tag plus digest for HAPI. | `Makefile`, CI absent | Add pip-audit/Trivy/secret scanning to CI, generate SBOM, pin and review digests on a schedule. |
| SEC-19 | Local Ollama model is pulled by name/version without digest verification; no model integrity record beyond the prompt hash. | `ai/providers/ollama.py:21-22,130-152`; `ai/service.py` | Pin the model digest, record it in the run/audit, and document the local model trust boundary. |

---

## 6. STRIDE threat model — local v3 demo, mapped to `07_REGULATORY_SECURITY.md` §4

**Assets:** source documents (synthetic PHI-like text), eCRF values and review decisions, the audit trail, the pseudonym map, JWT/pseudonym keys, the raw FHIR store, model prompts/outputs, and the demo machine itself.
**Trust boundaries:** Flutter ↔ API (:8000); AI service ↔ API (service JWT); API ↔ Postgres (:5433); API ↔ HAPI (:8090); local machine ↔ browser (CORS).

| STRIDE | Threat in this deployment | Current control / gap | 07 §4 control to meet |
|---|---|---|---|
| **Spoofing** | Forge a JWT with the committed HS256 secret; log in with `demo`. | Gap SEC-01/SEC-08. Role checks work only if the token is genuine. | Keycloak IAM + MFA; secrets management; short-lived tokens. |
| **Tampering** | DB writer deletes the tail or rewrites the chain; unauthenticated client writes to HAPI; forged AI proposals. | Trigger blocks normal UPDATE/DELETE; `verify` catches middle edits and deletions. Gaps SEC-02/SEC-03. Evidence spans are re-checked and AI output needs human review. | Tamper-evident audit; validation; least privilege; SAST/DAST. |
| **Repudiation** | A user views a document or exports data and denies it; a deleted tail hides an action. | Exports and writes are audited; reads are not (SEC-06); no external anchor (SEC-02). | Tamper-evident audit; security monitoring; incident response. |
| **Information disclosure** | Raw MRN/name from HAPI; pseudonym HMAC reversal with the default key; token in URL/logs; `service` reads all; CORS `*`. | Scrubber + `pseudonym_map`-free API are good; gaps SEC-03/SEC-04/SEC-05/SEC-07/SEC-10. | Secrets management; encryption; tenant isolation; least privilege; DPIA/pseudonymisation (07 §1). |
| **Denial of service** | No login rate limit; unbounded bodies/strings; repeated `full` FHIR sync; HAPI CVE DoS. | Local-only, small dataset; gaps SEC-08/SEC-09/SEC-12. | Backup/DR, monitoring, rate limits, patched images. |
| **Elevation of privilege** | Forged `pi`/`service` token; `service` can export/read all; `monitor` can push to the hospital; HAPI compromise → shared DB superuser. | Role matrix is mostly correct (monitor cannot review), but gaps SEC-01/SEC-03/SEC-07. | RBAC + ABAC; least privilege; tenant isolation; pen testing. |

**Production-only threats not modelled here (flagged for the roadmap):** model-weight tampering/supply chain, device provisioning and attestation, telemetry-ingestion abuse, cross-institution identity federation, backup/restore and key rotation, and formal validation (GAMP 5 / IQ/OQ/PQ). These are out of scope for a localhost synthetic demo but belong in the first hosted threat model.

---

## 7. Controls verified as working (do not regress)

- **Role gates:** monitor → review decision **403**; monitor → create run **403**; monitor → sync **403**; nurse → post AI extractions **403**; anon → `/participants` **401**. Monitor can SDV and open/close queries by design. `service` can update runs/post extractions and cannot review.
- **SQL injection:** all user values are bound parameters; dynamic SQL is limited to constant fragments/whitelists (`routes.py:23-24,314-321`). No injection found.
- **Append-only trigger:** direct `UPDATE`, `DELETE` and `TRUNCATE` are rejected with `audit_event is append-only` (`migrations/001_init.sql:92-98`).
- **Chain detection (partial):** modifying an event or deleting a middle event makes `/audit/verify` return `ok:false` with the correct `brokenSeq` (test at `tests/test_api.py:136-160`; live re-check).
- **Pseudonymisation:** end-to-end FHIR ingestion of the arrival bundles scrubbed `MRN-…`, `Proefpersoon` and given names from documents, `fhir_fact`, participant summaries, audit `before`/`after` and sync errors (0 hits in all columns); `/integrations`, `/integrations/fhir/runs`, `/participants/{id}`, documents, `/audit` returned no MRN/name or `mrn_hmac`. Existing test: `tests/test_ingest_export.py:108-131`.
- **AI safety rails:** evidence spans are re-located in the stored document text and rejected on mismatch (`routes.py:418-420`); abstentions cannot be accepted (`:209-210`); human review is mandatory before an eCRF value exists.
- **Exports:** ODM/FHIR bundles contain the participant pseudonym and staff usernames, not MRN/patient names; ODM is XSD-validated; every export is audited.
- **Dependencies:** `pip-audit` → “No known vulnerabilities found” for the Python environment. Images are pinned by digest.
- **Secrets:** no `.env`, private key, or cloud credential files are tracked; `ops/logs` and `ops/run` are gitignored. The only committed secrets are the two documented defaults (SEC-01/SEC-04) and the local DB password (SEC-14).

---

## 8. Remediation plan before the Board demo

**Must fix (High)**
1. **SEC-01** — remove the JWT default; fail closed; provision a per-machine secret; add a startup test. Owner: CTO (trivial same-agent patch if needed).
2. **SEC-02** — anchor the head `(count, headHash)` externally; restrict the app DB role; add tail-deletion + chain-rewrite tests. Owner: CTO + DevOps.
3. **SEC-03** — upgrade HAPI (or written acceptance), disable HAPI CORS, stop publishing `:8090`, split the DB role. Owner: CTO + DevOps.

**Should fix (Medium) before freeze if time allows**
4. **SEC-04** — require `PSEUDONYM_KEY` from env, rotate.
5. **SEC-05** — query token only on SSE, short-lived, redact access logs.
6. **SEC-06** — read-audit documents/eCRF/participant/audit.
7. **SEC-07** — site scoping + narrow `service`/monitor rights.
8. **SEC-08** — rate limit, stronger PBKDF2, per-user passwords.
9. **SEC-09/SEC-10** — image refresh + Trivy CI; restrict CORS/docs.

**Backlog (Low):** SEC-11 — SEC-19 in §5; batch them into the next security summary.

---

## 9. Sign-off and residual risk

- **No Critical findings** for the local, synthetic, localhost-only demo.
- The demo is **not** safe to host in its current state: SEC-01 and SEC-02 would become Critical the moment the API is reachable by an untrusted user or the DB credential is shared.
- The audit trail is tamper-**detecting** for ordinary app writes but not tamper-**evident** against the DB superuser; this must be fixed before citing it as an Annex 11/GCP control.
- Formal legal/regulatory sign-off remains with qualified humans; this review is an engineering assessment, not a certification.

*Prepared by Security Engineer (CEL-1780). Backend code was not modified. Scratch DBs and review processes were removed after testing.*
