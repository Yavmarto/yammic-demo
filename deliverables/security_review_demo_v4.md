# Security review — demo v4 backend (CEL-1807)

**Reviewer:** Security · **Date:** 2026-11-21 · **Target:** `demo-v3-checkpoint..v4` (branch `v4`)
**Scope:** `git -C ~/yammic-v4 diff demo-v3-checkpoint..v4 -- backend/` — authz on screening, queries, SDV and form approval; pseudonymisation across two hospitals; audit coverage; input validation on protocol/criteria text.
**Constraint:** review only. No backend code was changed by this review.

## Verdict

No critical or actively-exploited issue found. **2 high** findings block a "separate legal entities per hospital" reading of v4: enrolment can bypass consent, and no endpoint scopes a user to a site. SQL injection, secrets handling, audit chaining and the pseudonymisation of imported FHIR data were checked and held up.

| ID | Severity | Finding | Owner |
|----|----------|---------|-------|
| H-1 | High | PI can enrol a participant who never consented; consent date is back-filled | Engineering (backend) |
| H-2 | High | No site scoping: any nurse/PI can write screening, queries, SDV, forms for another site | Engineering (backend) |
| M-1 | Medium | Nurse can close a query they answered (no separation of duties) | Engineering (backend) |
| M-2 | Medium | Human can write AI-attributed screening results; audit `source` is spoofable | Engineering (backend) |
| M-3 | Medium | `GET /screening` performs privileged screening writes for any authenticated role | Engineering (backend) |
| M-4 | Medium | Sign-off to `eligible` succeeds with every criterion `unknown` | Engineering (backend) |
| M-5 | Medium | Postgres superuser password hard-coded (`yamicc`) in compose and tests | DevOps + Engineering |
| L-1 | Low | Undefined `external_results` breaks the rules-screening fallback (500 on import failure) | Engineering (backend) |
| L-2 | Low | Unbounded protocol/screening input on `/ai/*` (DoS, prompt-injection surface) | Engineering (backend) |
| L-3 | Low | Pseudonym scrubber gaps (short names, MRNs without an `MR` type code) | Engineering (backend) |
| L-4 | Low | Site-key heuristic `"2" in source_id` can assign the wrong site key | Engineering (backend) |
| L-5 | Low | Form approval re-applies field definitions with no allow-list/diff and fakes `before` | Engineering (backend) |
| L-6 | Low | Query input unbounded; `rule_id` forgeable; `field_id` not tied to participant | Engineering (backend) |
| L-7 | Low | `/integrations` exposes FHIR base URLs and error text to any authenticated user | Engineering (backend) |

---

## High

### H-1 — Enrolment does not require documented consent, and forges the consent date
`backend/app/routes.py:369-375`

`enrol_participant` accepts `status in ("eligible", "consented", "enrolled")`, so a PI can go straight from `eligible` to `enrolled` without the `POST /screening/consent` step. It then sets `cdate = p.get("consented_date") or edate`, i.e. it writes the **enrolment date into `consented_date`**. The audit event (`routes.py:376-378`) records only status and date, so the log shows a consented participant that never consented.

Verified (isolated DB): set `GBM-NL-004` to `eligible` with `consented_date=NULL`, then `POST /participants/GBM-NL-004/screening/enrol` as `pi` → `200`, `status=enrolled`, `consentedDate=2026-11-21`, `enrolledBy=pi`.

**Fix:** require `p["status"] == "consented"` **and** `p["consented_date"] is not None`; never derive `consented_date` from `enrolled_date`. Add a DB `CHECK`/trigger that an `enrolled` row has a non-null `consented_date` and `enrolled_at >= consented_date`. Audit the consent record id.

### H-2 — No site isolation on screening, queries, SDV or forms
`backend/app/security.py:32-41` (token carries only `sub/role/name`, no site); handlers: `routes.py:218,233,288,313,346,363,383,519,577,595,678`

Every v4 handler authorises on role only and looks up `participant`/`data_query`/`ecrf_value` by id. Nothing compares `participant.site_id` (or `data_query.site_id`) to the caller. The per-site pseudonym keys in `ingest/pseudo.py` imply the two hospitals are distinct data controllers, but the API lets a nurse at SITE-01 sign off, screen-fail, answer/close queries and tick SDV for a SITE-02 participant.

Verified (isolated DB): `nurse` confirmed `INC-01` on `GBM-NL-002` (SITE-02) → `200`; `nurse` then `sign-off` on the same SITE-02 participant → `200`.

**Fix:** add the caller's allowed sites to the token (or a `user_site` table) and add a central `require_participant_site(user, participant_id)` dependency used by every participant/query/SDV/form handler. Decide explicitly which roles are study-wide (monitor/PI) and make that an allow-list, not the default. Enforce on read (`GET /screening`, `/queries`) as well as write.

---

## Medium

### M-1 — Nurse can close a query they answered
`backend/app/routes.py:577` (`answer`, nurse/pi) and `routes.py:595` (`close`, nurse/pi/monitor)

The intended loop (see `tests/test_v4_features.py:140-151`) is nurse answers → monitor closes. The role list on `close` also includes `nurse`, so the answerer can resolve their own discrepancy. No `answered_by != closed_by` check exists.

Verified (isolated DB): monitor opened a query, nurse answered (`200`), nurse closed (`200`, `closedBy=nurse`).

**Fix:** restrict `close` to `monitor`/`pi` (the raiser or quality role), or reject when `closed_by == answered_by`. Require `status == "answered"` before close (or an explicit PI override with reason).

### M-2 — Human writer can produce AI-labelled screening results
`backend/app/routes.py:253-282`

`POST /participants/{pid}/screening/checks` is open to `service`, **nurse** and **pi**, and always writes `provider/model/prompt_version` from the request body and an audit event with `source="ai"` (`routes.py:280-282`). A nurse can therefore record arbitrary verdicts as if an AI produced them, including a fabricated `provider`/`model`.

Verified (isolated DB): nurse POSTed `INC-01=met`, `provider=ollama`, `model=forged` → `200`; `/audit?action=screening.ai_ingested` shows `source=ai`, `actor=nurse`.

**Fix:** restrict this route to `service` (the worker). Human overrides already have `criteria/{cid}/confirm`. If humans must ingest, derive `source` from `user["role"]` and reject a claimed `provider`/`model` that the worker API did not produce.

### M-3 — `GET /screening` performs privileged writes for any authenticated role
`backend/app/routes.py:217-238` → `workflows.run_ai_screening` (`workflows.py:59-227`)

`list_screenings` and `get_screening` use `ANY` but, when a participant has no checks, call `run_ai_screening`, which inserts `screening_check` rows and audit events. The explicit compute endpoint requires `nurse/pi/service` (`routes.py:242`), so a `monitor` (or any future read-only role) bypasses that restriction by issuing a GET, and every GET is a state change (bad for caching/retries/CSRF).

**Fix:** do not compute in a read handler. Return the stored state (or `unknown`) from GET and require `POST /screening/check`. If convenience is needed, gate the auto-run on `user["role"] in {"nurse","pi","service"}`.

### M-4 — `eligible` sign-off does not require met criteria
`backend/app/routes.py:322-341`

The only guard is `not_met_count > 0` (`routes.py:334`); `unknown` criteria are ignored. With 13 criteria all `unknown`, a nurse can sign a participant off as `eligible`. An explicit `outcome="eligible"` in the body hits the same check.

Verified (isolated DB): `GBM-NL-004`, `unknownCount=13`, `POST /screening/sign-off {"outcome":"eligible"}` → `200`, `status=eligible`.

**Fix:** require every inclusion criterion `met`, no `unknown` (or a PI-only, reasoned override recorded in the audit event). Treat "signed off with unknowns" as a screen failure by default.

### M-5 — Hard-coded Postgres superuser password
`docker-compose.yml:27`, `backend/tests/conftest.py:12,24`, `backend/app/db.py:7`

`POSTGRES_PASSWORD: yamicc` is committed; tests and the `db.py` fallback reuse `yamicc:yamicc`. The app runtime correctly uses the random `APP_DB_PASSWORD` (`ops/ensure-env.sh`), and Postgres binds to `127.0.0.1`, so exposure is local. Still a credential in code and a foot-gun if the bind is ever widened.

**Fix:** generate `POSTGRES_PASSWORD` in `ops/ensure-env.sh` like `APP_DB_PASSWORD`, pass it through compose, and have tests read it from the environment. Remove the credential-bearing default from `db.py` (require `DATABASE_URL`).

---

## Low

- **L-1** `backend/app/workflows.py:109` references `external_results`, which is never defined (the `try` at `:71-104` swallows the import error). If `app.ai.screening` fails to import, the fallback rules path raises `NameError` and screening returns 500. Fix: delete the `external_results` branch or initialise `external_results = {}`. (Covered by no test because the import succeeds.)
- **L-2** `backend/app/ai/routes.py:136` — `ProtocolProposalsIn.synopsis_text` has no length cap, while `FormVersionIn.protocol_text` is capped at 200 000 (`schemas.py`). `ScreeningIn.criteria/documents` (`ai/routes.py:130-132`) accept unbounded `list[dict]` and are passed to Ollama. Fix: reuse the `FormVersionIn` limits and cap list sizes; log/limit provider calls per user.
- **L-3** `backend/app/ingest/pseudo.py:32-42,48-49` — the `Scrubber` only gets tokens from `Patient.name` and only recognises an MRN whose identifier has `type.coding.code == "MR"`. Name tokens shorter than 3 chars are dropped, and MRN formats not resembling `MRN…` (e.g. a local "dossier" number) or names that appear only in a document are not redacted. No leak was observed on the seeded data, but these are blind spots. Fix: add every identifier value as a term regardless of type, lower/adjust the name threshold, add per-site redaction patterns (Dutch/English), and keep the post-sync canary scan as a regression check.
- **L-4** `backend/app/ingest/fhir.py:27` — `site_id = ... ("SITE-02" if "2" in sid else "SITE-01")`. A source id such as `hospital-12` silently becomes SITE-02, colliding the per-site key. Fix: require an explicit `siteId` per source and map with an allow-list; fail closed on unknown.
- **L-5** `backend/app/routes.py:678-735` — `approve_form_version` (PI only) overwrites `ecrf_field` type/section/min/max from the proposed JSON (`routes.py` INSERT ... ON CONFLICT) without validating `valueType` against an allow-list, and allows re-approving an already-approved version. The audit `before` is hard-coded `{"status":"proposed"}` (`routes.py:731-734`). Fix: whitelist `value_type`, require the row to be `status='proposed'`, record the real prior status, and show a diff before approval.
- **L-6** `backend/app/routes.py:563-571` + `schemas.py QueryIn/QueryAnswerIn` — `text`/`answer` are unbounded, `rule_id` is free text (a monitor can label a manual query as `DQ-04`), and `field_id` is not verified to belong to the participant's study. Fix: validate `rule_id` against `quality.RULES`, validate `field_id` against the participant's study, add `max_length`.
- **L-7** `backend/app/ingest/routes.py:62-63,67` — `GET /integrations` returns the FHIR `baseUrl` and the upstream error string to any authenticated user. Low information disclosure. Fix: restrict to `nurse/pi/service` or omit `error`/`baseUrl` for other roles.

---

## Checks that passed

- **SQL injection:** all v4 queries are parameterised. The only f-string SQL is a fixed `WHERE` fragment (`routes.py:745-752`) and seed helper with code-constant table/columns (`seed.py:35`). No user value is interpolated.
- **Secrets:** `JWT_SECRET`, `PSEUDONYM_KEY`, `AUDIT_KEY` fail closed below 32 chars (`security.py:10-11`, `pseudo.py:13-15`, `audit.py:14-16`); no committed defaults. `ops/.env.local` is git-ignored; no secret files are tracked. HAPI CORS is pinned and credentials disabled (`docker-compose.yml`).
- **Audit:** every new mutating action records an event (`screening.ai_checked`, `ai_ingested`, `criterion_confirmed`, `signed_off`, `screen_fail`, `consented`, `enrolled`; `query.opened/answered/closed/auto_opened`; `ecrf.sdv/sdv_cleared`; `form.version_proposed/approved`; `fhir.sync/document_ingested`). The chain is hash-chained; `yamicc_app` has `SELECT, INSERT` only on `audit_event` (`migrations/003,004`). Note `run_data_quality` with zero findings writes no event (L-7 class, low).
- **Pseudonymisation:** `_site_key` derives an independent HMAC subkey per site (`pseudo.py:18-29`); MRN and name tokens are scrubbed from document bodies, titles and FHIR fact JSON before storage (`sync.py:239,262,267`). Live check: synced hospital-2 through `:8001` (5 patients, 13 documents, 13 docs scrubbed) and scanned 13 participants across `/participants`, `/documents`, `/timeline`, `/screening`, `/ecrf`, plus `/audit` and `/integrations` (333 645 bytes) for `MRN`, `Proefpersoon` and every seeded given name → **0 hits**. `pseudonym("MRN-99999","SITE-01") != pseudonym("MRN-99999","SITE-02")` holds.
- **Input validation:** `FormVersionIn`/`FormFieldProposal`/`CriterionProposal` have `min/max_length`; evidence spans are checked against stored text (`routes.py:264-266`, `:849-851`); provider names are allow-listed (`routes.py:244`, `ai/routes.py:108`).

## How this was verified

- Ran against the **v4 stack on `:8001`** (`/openapi.json` title "Yamicc demo backend", 57 paths incl. screening/forms/timeline). v3 (`:8000`) and `~/yammic-demo*` were not touched.
- Live pseudonymisation check used `POST /integrations/fhir/hospital-2/sync` and `hospital-1` on `:8001`. This added the 5 synthetic hospital-2 participants `GBM-NL-201..205` to the **v4** database (additive; no v3 impact) so the two-hospital path could be inspected end to end.
- Findings H-1, H-2, M-1, M-2, M-4 were reproduced with a scratch script against the isolated `yamicc_v4_test` database (same app, `JWT_SECRET`/`PSEUDONYM_KEY`/`AUDIT_KEY` generated for the run), so the demo database was not mutated for the negative tests.
- `pytest tests/test_v4_features.py` → **5 passed** (the existing suite's role checks are the baseline this review extends; it does not test consent-before-enrol, site scope, or self-close).

## Open follow-ups (not fixed here)

1. Backend: implement H-1, H-2, M-1–M-4 and L-1, L-5, L-6 as one authz hardening PR on `v4`; QA should add the five negative tests above as regression tests.
2. DevOps: rotate the compose superuser password (M-5) and wire it from `ops/.env.local`.
3. Security: add these five probes to the recurring check (consent-before-enrol, cross-site write, self-close, AI-attribution, sign-off with unknowns), and schedule a dependency CVE scan (`pip-audit`/`uv` audit) for the v4 lockfile — not run here.
