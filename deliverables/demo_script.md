# Monday demo v3 — the connected platform slice

Owner: PM (CEL-1789) · Version **3.1** · Demo: **Monday 2026-11-23**, 10 minutes + Q&A
Build check: **CEO re-verification 2026-11-21 ~15:45 CET** (after CEL-1785 `f5b0386` and `c60b2be`) · measured model queue: **all runs 323 s ≈ 5.4 min; plan for 3–6 min**
Board click-through: **2026-11-21, evening** — same running build and flow; the app clock stays at 23 Nov (cosmetic, R5)
Build: Flutter (web + macOS) → FastAPI → PostgreSQL 16 → HAPI FHIR R4, all local · **synthetic data only**
Code freeze: **Sunday 2026-11-22 20:00 CET** · This script replaces the v1 script for the disconnected prototype.

> **Why v2 exists.** The Board rejected the v2 Monday demo on 2026-11-21 10:21: the app read bundled JSON, there was no backend, the UI looked plain, and the work was too shallow. This script is for the rebuilt demo: a **connected, local platform slice** (plan v3, [CEL-1727](/CEL/issues/CEL-1727#document-plan)). It shows the same review loop, but every number comes from a live backend, the new patients arrive over FHIR, and the AI extraction runs on a local model during the demo.

---

## 0. At a glance

**One-sentence thesis**
> We rebuilt the demo as a connected platform: a synthetic hospital sends FHIR R4 data into a local backend, a local open-weight model extracts eCRF values with evidence, a human decides, and a hash-chained audit plus standards exports make the result reviewable.

**What the audience must remember (3 things)**
1. **It is connected.** The app talks to a real backend and a real FHIR server; the hospital sync is live, and every document that arrives through **Sync** is extracted live on the local model on this laptop.
2. **The product is the review loop, not the model.** Evidence span → proposal → human accept/correct/defer → audit → export. AI output is never research data until a person acts.
3. **It is honest.** Synthetic data, local only, not a medical device, no accuracy claim beyond a synthetic gold set. Gate 2 still decides the real MVP.

**Decision requested (one sentence at the end)**
> Keep **MVP B** (AI-assisted data capture) as the direction and let us finish the Gate 1 evidence, so **Gate 2** can decide scope, roadmap and cost.

**Deck rule:** four slides maximum — title, connected slice, "is / is not", next steps. The product is the deck. Do not add slides.

---

## 1. What changed since the rejected demo (say this only if asked)

| Then (v2, rejected) | Now (v3, this demo) |
|---|---|
| Flutter read a bundled JSON file. No network. | Flutter → FastAPI → Postgres. Login, live data, real writes. |
| "AI" values were pre-computed JSON. | The 8 baseline participants still carry **pre-computed** fixture extractions (`provider: fixture`, model `demo-extractor v0.1`). Documents that arrive through **Sync** are extracted **live** by a local Ollama model (`qwen2.5:7b-instruct`, prompt `extract_v4`); `rules` is the fallback. |
| No hospital. | HAPI FHIR R4 server on this machine; new patients arrive over FHIR and are pseudonymised on ingest. |
| No audit. | Every action is hash-chained with a key held outside the database and anchored outside it. Verify detects edits and deletions, including changes made directly in the database (SEC-02 fixed and verified live, CEL-1785 / `c60b2be`). |
| No exports. | CDISC ODM 1.3.2 study XML and FHIR QuestionnaireResponse + Provenance + AuditEvents, with write-back to FHIR. |
| Zeta looked plain. | Redesigned shell and screens (visual direction v2, `deliverables/D7b_visual_direction.md`); before/after shots in `deliverables/design/`. |

The v2 rule "no backend, no network" is **withdrawn**. The rule now: everything runs locally (Docker Desktop + local processes). No hosting, no real data, no outreach, no paid APIs (Gate 3).

---

## 2. Pre-flight (T-30 to T-0)

Run this once, 30 minutes before. **Do not do any of it on stage.** `make reset` deletes the local volumes; it is safe because the data is synthetic and reseeded.

```bash
# Run from the v4 checkout root.

# 1. Clean slate: Postgres + HAPI FHIR, backend seed, baseline FHIR set.
#    Expect: 8 participants, 46 pre-computed fixture proposals (not live model output), 7 open queries, HAPI 8 patients.
make reset

# 2. The hospital "receives" 3 new patients (staged, NOT yet synced into the platform).
#    Expect: HAPI 11 patients; the platform still has 8 participants.
python3 fhir-seed/load.py --set arrivals

# 3. Start backend + AI worker + web and health-check all five components.
make demo
make health STRICT=1          # Result: OK — full demo stack is healthy.

# 4. Confirm exactly ONE AI worker runs (make demo starts it; CEL-1784).
ops/ai-workers.sh             # expect one pid; make demo prints "AI worker: <pid>"
tail -3 ops/logs/ai.log        # expect no ai.poll_error lines (silent when the queue is empty)

# 5. Record the build you are presenting.
git rev-parse --short HEAD    # write it here: ________
```

| # | Check | Pass condition |
|---|---|---|
| 1 | `make health STRICT=1` | Postgres, FHIR, backend, web all OK |
| 2 | Browser tab A: `http://127.0.0.1:8080`, full screen (F11), 100 % zoom | Login screen, banner "Synthetic data — prototype, not for clinical use" |
| 3 | Tab A: sign in **PI** (`Use demo account`) | Dashboard; top bar "Connected · N ms"; no offline banner |
| 4 | Integrations | "Connected"; **Pseudonymised patients 8**; **Last sync never** |
| 5 | Participants | **8** rows; GBM-NL-009/010/011 **absent** |
| 6 | AI review | **46 pending** (pre-computed fixture proposals), no live 009 cards yet |
| 7 | Second tab B: same URL, sign in **Monitor** | Read-only banner; keep this tab in the background |
| 8 | AI quality | ollama | rules segmented button; precision/recall table visible |
| 9 | Export (PI) | "Generate export" enabled |
| 10 | Laptop: power, Do Not Disturb, notifications off, screen saver off | No interruption |
| 11 | Backup recording: 2–3 minutes of silent clicks on the frozen build, played once from local disk | Plays offline |
| 12 | PIDs: exactly one AI worker | `ops/ai-workers.sh` prints one pid; `make health STRICT=1` shows `[ OK ] ai` |

**If step 4 shows "Last sync" not "never":** someone synced after the reset. Run `make reset` and repeat from step 2. A sync on stage must create the 3 arrivals; otherwise the live beat is dead.

**Why the arrivals are staged before the demo but synced on stage:** the pull is live (about 1.5 s), and the 3 new patients are genuinely new to the platform at the moment you press **Sync now**. Staging them in the hospital server is the realistic scenario: the hospital has the data, the platform does not yet.

---

## 3. Run sheet (10:00)

| Time | Segment | Screen / route | Goal |
|---|---|---|---|
| 0:00–0:30 | Opening + honesty frame | Slide 1 | Set trust; name what changed |
| 0:30–1:00 | Login | `/login` | Connected; three roles; banner |
| 1:00–1:40 | Live dashboard | `/` | KPIs from Postgres; the work queue |
| 1:40–2:30 | **FHIR sync** | `/integrations` | Press Sync; result in ~1.5 s; 7 arrival runs queued |
| 2:30–4:30 | **Queue wait: integrations + audit + AI-quality talk** | `/integrations` (no clicks) | Cover a 3–6 min queue; open the first finished arrival document |
| 4:30–4:55 | New participant | `/participants/GBM-NL-009` | Pseudonymised, 3 source documents |
| 4:55–5:30 | **Live AI extraction** (first finished arrival doc) | `/review` (009) | Local model, evidence, abstention |
| 5:30–5:55 | Accept | `/review` (009) | Proposal → verified data |
| 5:55–6:30 | Correct | `/review` (002) | Catch a wrong value; before/after |
| 6:30–6:45 | Defer | `/review` (009) | Abstention → open task |
| 6:45–7:15 | **Audit verify** | `/audit` | Hash chain, human decisions |
| 7:15–7:30 | **AI quality** (screen only; the talk is in 4.4b) | `/ai-quality` | Per-field metrics + registry |
| 7:30–8:10 | **Export + write-back** | `/export` | ODM + FHIR + push |
| 8:10–8:40 | Monitor | `/participants/GBM-NL-002` (tab B) | Read-only + SDV |
| 8:40–9:20 | Is / is not + decision | Slide 3–4 | Honest limits; one ask |
| 9:20–10:00 | Stop talking | — | ~40 s of slack; invite Q&A |

**Pacing:** ≈140 spoken words per minute. Spoken text measured with `say -r 140`: the prepared segments are **≈8:17** after the 4.4b wait talk replaced the separate audit and AI-quality talk; the click/transition budget is about **1:25** (30 clicks at ~2 s plus ~10 route loads). The planned content ends at **9:20**, leaving **40 s before 10:00 if you leave the wait early and about 20 s if you use the full 2-minute block**. **The 4.4b wait talk is not optional:** measured on this machine after a fresh sync, the queue needs **3–6 minutes** (all runs finished in **323 s ≈ 5.4 min**; the earlier run was **179 s ≈ 3 min**). Seven runs are the live Ollama arrival runs, and the first arrival document finishes early in the queue: **open the first finished arrival document as soon as it appears** — never wait for the whole queue. If you are 45 s late at 2:30, shorten the dashboard to 30 s and the participant to 15 s. **Never cut:** the sync result, 4.4b, the correction, the abstention, the audit verify, or the "is not" slide.

---

## 4. Segment scripts

> Bracketed text is a stage direction. Quotes are spoken text. "Click" lines are the click path.
> Demo clock is fixed at **23 Nov 2026** (`Session.demoToday`). Data is from `GBM-NL-2026-01`, three fictional sites.
> Two tabs: **A = PI** (main flow), **B = Monitor** (last beat). Do not resize between tabs.

### 4.1 Opening — 0:00–0:30

**Slide 1:** *"Clinical research, connected — a working platform slice"*. Subtitle: *Synthetic data · local · prototype · not for clinical use.*

> "Thank you. Yesterday you told us the last demo was a mock-up: a Flutter app reading a JSON file. You were right. So we rebuilt it. What you will see now runs on this laptop as a real platform: a synthetic hospital FHIR server, a database, a backend and the app. Everything is local. Every patient is synthetic. And none of it is a medical device. Ten minutes, then questions."

*Why this opener:* it accepts the rejection in one sentence and sets the two boundaries (synthetic, local) before the first click.

### 4.2 Login — 0:30–1:00

**Click:** open tab A at `http://127.0.0.1:8080`. Click the **PI** role card → **Use demo account**. (The demo password is `demo`; the card fills it.)

> "We start at the front door. Three demo roles: research nurse, monitor, principal investigator. I sign in as PI, because export is a PI action in this build. The screen already knows the backend is healthy, and it names the stack: FHIR R4 and Postgres 16. The amber banner never goes away: synthetic data, prototype, not for clinical use."

**Audience should notice:** the amber banner; "Sign in"; three role cards with one-line scopes; "Local backend healthy · FHIR R4 · Postgres 16"; "SSO is disabled in the local demo. Demo password: demo."

**Recovery:** if the left panel says "Local backend is down", the backend is not running: do **not** debug on stage. Say "the local backend is not up; the app can show the last snapshot" and continue in the offline snapshot (read-only) for the dashboard and review story; skip sync/export and use the recording for those beats.

### 4.3 Live dashboard — 1:00–1:40

**Screen:** `/` — **Research dashboard**, signed in as PI.

> "This is live from Postgres, not from a bundled file. Eight participants, target twenty-four. Zero eCRF fields verified yet. Forty-six AI proposals waiting — these are pre-computed from our gold set, so the queue is populated before the live run. Seven open queries. The connection pill shows the round-trip to the local API, and the date is the demo clock. The queue is sorted lowest confidence first, and the alert already points at the MGMT contradiction we will review. This is the nurse's morning."

**Audience should notice:** "Connected · N ms" (a real latency, 1–50 ms locally); "Data as of 23 Nov 2026"; **Enrolled 8/24**; **eCRF verified 0 %** ("0 of 45 fields · verified only"); **Open queries 7**; **AI queue 46**; **AI acceptance —**; recruitment chart; three sites; alert "GBM-NL-002: AI MGMT proposal contradicts the pathology report."

**Provenance note:** the **46 baseline proposals are pre-computed fixtures** (`provider: fixture`, model `demo-extractor v0.1`, no model call), not live output. The live model runs only on the synced arrivals (4.6). If asked, say so plainly (Q2b).

**Click next:** **Integrations** in the PLATFORM section of the sidebar.

**Recovery:** if the numbers differ because the state is not a fresh reset, do not apologise and do not quote exact counts: say "the figures are live from the backend; the shape is what matters" and move on. The only count that must be exact on stage is the sync result.

### 4.4 FHIR sync — 1:40–2:30 (the missing backend, live)

**Screen:** `/integrations`.

> "Now the part that was missing. Integrations. The hospital is a HAPI FHIR R4 server on this machine, standing in for the hospital EHR. It is green, and the platform has pseudonymised zero patients so far. The hospital has just received three new patients. I press Sync now."

**Click:** **Sync now** (leave **Full re-sync** unchecked). Wait for the result line (≈1.5 s). Then point at the run row.

> "It pulled the new records, pseudonymised them, de-duplicated the ten documents we already had, stored seven new reports, and queued seven AI extraction runs. Three new participants; eleven pseudonymised patients in total. The run took about a second and a half, and the run log keeps the counts, the mode and who triggered it."

**Audience should notice:**
- Panel "Hospital EHR (FHIR R4)" · **Connected**; Endpoint `http://localhost:8090/fhir`; FHIR version **4.0.1**; Server **HAPI FHIR Server 8.12.0**.
- **Pseudonymised patients 0 → 11** (E2E evidence: the sync output below).
- Result line: **"Sync completed: 218 resources fetched, 7 new documents, 7 extraction runs queued."**
- "Sync runs" table: Run **full**, Mode **full**, Status **Completed**, Created **7**, Duration **≈1500 ms**, By **pi**.

**Click next:** stay on the page for 4.4b; **Participants** comes after the model wait.

**Recovery:**
- If the result says **0 new documents / 0 runs**, the arrivals were already synced. Say "this machine was synced during rehearsal; the run log shows the three arrivals" and point at the earlier run row. Then continue to review on the existing queue. Do **not** press Sync twice.
- If the panel says **Unreachable**, the FHIR container is down. Say "the hospital endpoint is unreachable; the platform keeps the last synced data and keeps working" and skip to Participants. Restart `make up` only after the demo.
- If **Sync now** is disabled, you are signed in as monitor (tab B). Switch to tab A (PI).

### 4.4b Queue wait — integrations + audit + AI-quality talk (2:30–4:30, extend to 5:30 if needed)

**Screen:** stay on `/integrations`; do **not** open another tab or a terminal. The extraction runs are queued and the local model is working. Measured on this machine after a fresh sync: the queue needs **3–6 minutes** (all runs finished in **323 s ≈ 5.4 min**; the earlier run took **179 s ≈ 3 min**). Seven runs are the live Ollama arrival runs. **Check for a finished arrival document every ~30 s:** the first arrival documents finish early in the queue, and you must **open the first finished arrival document as soon as it appears** (4.5–4.6). Never wait for the whole queue and never stand in silence.

> "While those runs go, three things about what sits under this screen.
>
> First, integrations: this is one connector, a FHIR R4 pull from a HAPI server. In production the same ingest path takes a hospital feed, pseudonymises at the boundary and keeps the raw identifiers out of the platform tables. Nothing in the review loop changes when the connector changes.
>
> Second, the audit trail: every ingest, every proposal and every human decision is appended to one hash chain. Each event carries the hash of the one before it. The chain is keyed with a key held outside the database and anchored in an append-only file outside the database, so verify detects edits and deletions, including changes made directly in the database. That is the difference between a log file and a control. The honest limit: someone with both the database and the key and the anchor file on this machine could still defeat it. In production the key and the anchor go to a separate service; that is on the roadmap.
>
> Third, AI quality: precision, recall and abstention, per field, for the local model and for the deterministic rules fallback. The hard cases are the point, and the measured numbers are on the next screens — including why a hundred percent on a synthetic gold set proves the pipeline, not clinical accuracy."

**Audience should notice:** the "Sync runs" row stays **Completed**; the queue is visible as the extraction runs; no error toast. The point of this beat is that the model runs in the background and the platform does not block on it.

**If the first arrival document is ready before 4:30:** leave this beat and open **Participants → GBM-NL-009** (4.5). Do not fill the time with a status check or a refresh.

**If no arrival document is ready at 4:30:** continue the same three topics — the audit limit and the AI-quality hard cases — until **5:30** at the latest, then go to 4.5 anyway. To keep the 10:00 stop, cut the AI-quality screen (7:15) to a 10-second look and keep Export and Monitor to the click path. If 009 still has no finished proposals when you reach 4.6, run the loop on **GBM-NL-002**'s pre-computed queue (4.7–4.9) and return to 009 after the audit if its live proposals have arrived.

**Wording note (SEC-02 fixed, verified live 2026-11-21):** the chain is keyed (HMAC, key outside the DB) and anchored in an append-only file outside the DB (CEL-1785 `f5b0386`, verify fix `c60b2be`). The CEO tested a superuser who disabled the trigger and deleted the newest event, then made a normal app write: **Verify chain reported "chain rewritten (does not match the external anchor)"**. Use the wording above. The bans stand: no "Annex 11 compliant", no "GCP compliant", no "certified".

### 4.5 The new participant — 4:30–4:55

**Screen:** `/participants` → click row **GBM-NL-009**.

> "Participants. We had eight; now eleven. GBM-NL-009 is one of the new arrivals: 58, female, right parietal, gross total resection. Three source documents. No name, no date of birth, no hospital number — only the pseudonymised study id. The next twenty-four hours of that patient's trial data will come from these documents."

**Audience should notice:** 11 rows; the three new ids at the bottom; the **GBM-NL-009** workspace: status chip, "58 y · F · SITE-01 · enrolled 22 Nov 2026", "Clinical summary", "Source documents · 3", and the header button **"Review AI (N)"**.

**Click next:** **Review AI (N)** in the participant header (it passes 009 to the review screen).

**Recovery:** if 009 is absent, the sync did not create it. Open the **AI review** rail item and continue on GBM-NL-002 (recovery from 4.4).

### 4.6 Live AI extraction — 4:55–5:30 (the centrepiece, synced arrival only)

**Screen:** `/review`, filtered to **GBM-NL-009** (the dropdown shows `GBM-NL-009`).

> "This is the live run, on a patient that arrived through Sync a few minutes ago. The local Qwen 2.5 model, seven billion parameters, running on this laptop through Ollama, read the pathology report. No data leaves the machine, no paid API. Here is what it produced: histology, IDH status, MGMT — unmethylated, which matches the report — and nine abstentions. The model does not guess what the document does not say. Every proposal carries its evidence span, a confidence, the model id and the prompt version, and the run and the proposal are in the audit chain."

**Audience should notice:**
- Toolbar: "AI extraction review"; dropdown **GBM-NL-009**; progress counts the 009 proposals that have finished (15 when only the pathology report is done).
- Left pane: **"SOURCE · pathology report · DOC-009-PATH"**, Dutch source text with the matched sentence highlighted.
- Middle: cards with amber **"AI · Unverified"**, `conf 0.95`, and low-confidence flags where present; nine of the fifteen pathology proposals are grey **"AI abstained"**.
- Right pane: **Model `qwen2.5:7b-instruct`**, **Prompt `extract_v4@1ef2060c673d`**, **Provider `ollama`**.
- If you press **Run extraction**: the run bar reads "Extraction running · ollama…" for the selected document (one run, ~45 s). The sync's arrival runs finish in the background in **3–6 minutes**; the first arrival document finishes early in the queue. **Do not wait for the queue on stage** — you are here because the first finished arrival document was ready.

**Provenance note:** every card on 009 is live `ollama` output. The 8 baseline participants (including GBM-NL-002, used for the correction) carry **pre-computed** fixtures: `provider: fixture`, model `demo-extractor v0.1`. Never call those "live". The review loop is identical; only the provenance differs.

**Timing note (measured 2026-11-21):** Ollama takes **35–66 s per document** on this laptop (44 s for DOC-009-PATH); `rules` is <10 ms. The worker processes runs sequentially. Measured after a fresh sync: **all runs finished in 323 s (~5.4 min)**, against **179 s (~3 min)** in the earlier run; **plan a 3–6 minute window**. Seven runs are the live Ollama arrival runs, and the first arrival document finishes early in the queue. Open the **first finished arrival document**; never wait for the whole queue.

**Recovery:**
- If 009 shows **"Queue is empty"** when you arrive, the first run is unusually slow. Return to **4.4b**, check again every ~30 s and finish the integrations/audit/AI-quality talk, then return to 009 (not later than 5:30). If it is still empty, say "the local model is still reading the three reports; the platform does not block on it — let us review the existing queue while it works", switch the dropdown to **GBM-NL-002**, and do 4.7–4.9 there. Return to 009 after the audit if proposals have arrived.
- If no new proposals arrive at all, the AI worker is not running. Say "the local model service is not running in this snapshot; these are the pre-computed gold-set proposals, and the live run is what we rehearsed" and continue. Do not start a terminal on stage.
- If Ollama is slow, the service **falls back to `rules` automatically**; the proposals then show Provider `rules`. Same story, different provider: "the local model was slow, so the deterministic extractor took over; the review loop is identical." This is the recovery line for a 6-minute queue: keep the review loop moving and never wait in silence.

### 4.7 Accept — 5:30–5:55

**Click:** click the **Histology (central review)** card in the middle column, then **Accept** (or press `A`).

> "AI review, filtered to GBM-NL-009. Three columns: the source on the left, proposals in the middle, the target eCRF field on the right. This one is histology, 0.95, with the sentence highlighted in the Dutch pathology report. It is still an AI proposal, not research data. I accept. One click, and it becomes a verified eCRF value with my name, the time, and the source extraction attached."

**Audience should notice:** the card and target pane turn green **"Verified · Accepted"**; the target shows "Verified by pi"; a snackbar "Histology (central review) accepted — verified by pi"; the progress line increments; the **AI review** badge in the sidebar drops by one.

**Recovery:** if **Accept** is disabled, the card has no valid evidence span (an abstention). Pick a proposed card (amber), not a grey one. If the write fails ("Could not save: …"), say "the local API rejected the write" and continue; the audit will show the truth.

### 4.8 Correct — 5:55–6:30 (the case that matters)

**Click:** set the participant dropdown to **GBM-NL-002**. Scroll the middle column to the **MGMT promoter methylation** card (13th of 16; two flicks). Click it → **Correct** (or `C`) → replace `Methylated` with `Unmethylated` → **Save correction**.

> "Now the case that matters. GBM-NL-002, the MGMT promoter. The proposal says methylated at 0.72. The report says unmethylated. This is a scripted fixture from our synthetic gold set, injected on purpose: a demo that only shows the model being right is not a demo of a safety mechanism. I correct it and save. The eCRF now says unmethylated; the original proposal, the correction, the reviewer and the time are all kept."

**Audience should notice:** the proposal card `Methylated`, confidence **0.72**, **Low confidence** flag; the highlighted source sentence "MGMT promoter is unmethylated"; after saving, **"Verified · Corrected"** and "Unmethylated". The **Provider** row reads `fixture` for this gold-set case — say so if asked (see Q10); the live model's own proposals are on 009.

**Do not claim a reason field on Correct.** The build records the before/after value plus the reviewer; a free-text reason exists on **Reject** only. **Cancel** wraps below **Save correction**; both are visible.

**Recovery:** if the MGMT card is hard to find, type the participant filter `GBM-NL-002` and use the card's label; do not scroll blindly. If you cannot reach it in 20 s, skip the correction and go to 4.9 (the abstention already proves the safety story). Never cut the audit verify.

### 4.9 Defer — 6:30–6:45

**Click:** set the dropdown back to **GBM-NL-009**; click the **Date of progression (RANO)** card (grey, `Not stated`, conf 0.00); click **Defer** (or `D`).

> "Third case. The RANO progression date. The model abstains: not stated, confidence zero, accept disabled. We defer it; it becomes an open task for the next visit, not a silent gap. Reject is for a proposal that is not in the source at all; it asks for a reason and records it."

**Audience should notice:** **Accept** is disabled with "Accept is disabled: no evidence in source"; the card becomes grey **"Deferred"**; the source pane explains "No evidence span: the AI abstained."

**Recovery:** if the defer write fails, continue to audit; the previous two decisions are enough to show the loop.

### 4.10 Audit trail + hash-chain verify — 6:45–7:15

**Click:** **View audit trail** in the target pane, or **Audit trail** in the sidebar. Click **Verify chain**. Then click the **Human** segment.

> "Audit trail. Press Verify chain [press]: every event, no gaps and no edits, with the head hash — the chain is keyed outside the database and anchored outside it, so this also catches edits and deletions made directly in the database. Filter to human actions. There are the three decisions, newest first — the defer, the correction, the accept — next to the eCRF writes they triggered. Open the correction: before methylated, after unmethylated, by whom, when, and which model and prompt proposed it."

**Required wording (do not improvise):** "Every action is hash-chained with a key held outside the database and anchored outside it. Verify detects edits and deletions, including changes made directly in the database." Do **not** say "tamper-proof", "cannot be tampered with", "Annex 11 compliant", "GCP compliant" or "certified". The fixed chain detects DB-level edits, but the check depends on the key and the anchor file on this machine; a compliance or certification claim needs validation and a separate key/anchor service.

**Evidence note (SEC-02 fixed, verified live 2026-11-21):** CEL-1785 (`f5b0386`) keys the chain with an HMAC key outside the DB and anchors it in an append-only file outside the DB; `c60b2be` makes verify check every anchor line. The CEO tested a superuser who disabled the trigger and deleted the newest event, then made a normal app write: **Verify chain reported "chain rewritten (does not match the external anchor)"**. Use the wording above; do not add "compliant" or "certified".

**Click next:** click the `extraction.decision` row for the correction (Entity `EXT-0020`).

**Audience should notice:**
- Green banner: **"Chain verified · N events, no gaps or edits. Head …"** (N grows with the session; do not quote a fixed number).
- `Human` filter: `extraction.decision` rows (defer, correct, accept) and `ecrf.value_set` rows, newest first; "Hide sign-ins" is on by default.
- Detail panel: **BEFORE `{"reviewState":"pending"}` / AFTER `{… "decision":"correct" …}`**, actor, role, time, **Prompt** version, **Prev hash** and **Hash** (copyable).
- The verify call is fast (≈30 ms locally).

**Recovery:** if the human rows are missing, the review writes did not persist. Say "the review state did not persist in this run" and show the recording's audit segment; continue. If **Verify chain** returns red, read the reason — e.g. "chain rewritten (does not match the external anchor at event N)" or "events deleted from the end of the chain". Say "a row was changed outside the application; catching that is what the verifier does" and move on. Do not debug, and do not claim the demo is unbreakable: someone with the database, the key and the anchor file on this machine could still defeat it (Q9).

### 4.11 AI quality — 7:15–7:30

**Click:** **AI quality** in the PLATFORM sidebar.

> "AI quality, as I said while the model ran. Per-field precision, recall and abstention for the local model and the rules fallback; the hard cases — the hedged wording at 0.38, the wrong MGMT, the abstention; and the model and prompt registry with the prompt hash. The hundred percent is on the synthetic gold set only; real evaluation comes with site data under approval."

**Audience should notice:** segmented **ollama | rules**; metric strip **Precision 100 % · Recall 100 % · F1 100 % · Abstention 7 % · Documents 13**; subtitle "Precision and recall against the gold set, per field and provider. Quality is measured before it is trusted."; per-field table (Support, Precision, Recall, F1, Abstain, Mean conf.). **Scroll once** to the **Model registry** and **Prompt registry**: `rules` and `ollama` available and local; the active prompt is `extract_v4` with a SHA-256.

**If you are short of time:** this screen is a quick confirmation of the talk from 4.4b; show the metric strip and the registry, then move to Export. If the queue ran long, skip the scroll.

**Recovery:** if the screen says "No evaluation results yet", the committed eval JSON is not present. Say "the eval harness output is not loaded in this build; the number we can defend is that the gold set has 13 documents and 57 annotations" and move on. Do not invent metrics.

### 4.12 Export + FHIR write-back — 7:30–8:10

**Click:** **Export** (PLATFORM). Format **CDISC ODM 1.3.2** → **Generate export**. Point at the XML. Then click the **FHIR R4 bundle** card; choose **GBM-NL-002** (it is preselected as the participant with verified values); **Generate export**; then **Push to FHIR server**.

> "Export. Only human-verified values leave the platform; AI proposals never do. CDISC ODM one point three two: the study snapshot for sponsors and regulators, including the audit records. Generate — about ten kilobytes of XML. Then the FHIR bundle for GBM-NL-002: a QuestionnaireResponse, Provenance that separates AI from human, and the AuditEvents. And push it back to the hospital FHIR server. Six resources written. That is a full round trip: in over FHIR, out over FHIR, with evidence."

**Audience should notice:**
- Header line: "Only human-verified eCRF values leave the platform. AI proposals are never exported. Every export is audited."
- Steps **1 Choose format · 2 Generate · 3 Download or push**.
- ODM preview: `ODM 1.3.2` XML with `ItemData` for the verified values and `AuditRecord` elements (about 10 KB).
- FHIR preview: `QuestionnaireResponse`, `Provenance`, `AuditEvent` entries (about 5 resources).
- Push result: **"Pushed to the FHIR server: 6 resources written."** (the bundle carries the audit events; the push itself is audited). Generation under 0.3 s; push ≈3 s (HAPI writes history).
- **Do not press Download on stage**; it opens a file dialog and breaks the flow.

**Recovery:** if **Generate export** is disabled, you are on monitor/nurse or offline. Switch to tab A (PI). If the FHIR push fails (hospital server down), show the generated bundle and say "the export is valid; write-back needs the FHIR server, which is down in this run." If the ODM preview is truncated ("… more characters in the download"), that is by design (8 000-char preview), not an error.

### 4.13 Monitor, read-only + SDV — 8:10–8:40

**Click:** switch to **tab B** (Monitor, pre-signed in). Click **Participants** → **GBM-NL-002**. Scroll the eCRF table to **MGMT promoter methylation** (the corrected value); click **Mark SDV**.

> "Last, the monitor. This is a second tab, signed in as monitor. Same data, read-only: the banner says so, and the write actions are disabled. On the participant's eCRF, the monitor marks source data verification. MGMT: SDV done. The monitor independently confirms the value the PI corrected. That is the role separation a sponsor expects."

**Audience should notice:** blue banner **"Monitor role is read-only in this demo."**; the top bar role **Monitor**; on `/review`, Accept/Correct/Defer/Reject are disabled; on the participant eCRF, verified fields show **Verified** and a **Mark SDV** button; after the click, **"SDV done"** and the dashboard KPI "SDV done" increments.

**Recovery:** if tab B is signed out or shows the offline snapshot, switch the role from tab A (avatar → **Switch demo role**) and sign in as Monitor; that takes about 10 s. If time is short, skip SDV and just show the read-only banner and disabled buttons.

### 4.14 Is / is not + decision — 8:40–9:20

**Slide 3 → 4.** Read the four "is not" lines; do not soften them.

> "So, plainly. This is a connected, local slice of the platform on synthetic data. It is not real patient data, not a hospital connection beyond this laptop, not a medical device, and not validated. It is not an accuracy claim, and it is not a Gate 2 decision. What we ask is narrow: keep MVP B as the direction, and let us finish the Gate 1 evidence so Gate 2 can decide scope, roadmap and cost. Thank you."

### 4.15 Stop — 9:20–10:00

Stop talking. Leave the last slide up. Invite questions.

---

## 5. Slide text (copy-paste)

### 5.1 Slide 1 — Title

> **Clinical research, connected**
> A working platform slice — not a mock-up
>
> Synthetic data · everything local · prototype · not for clinical use
>
> *[Project name] · 23 November 2026*

### 5.2 Slide 2 — The connected slice (one diagram, no bullets)

```
 Synthetic hospital EHR            Yamicc platform (this laptop)                 Experience
 ┌────────────────────┐  FHIR   ┌──────────────────────────────────────┐   REST   ┌───────────────────┐
 │ HAPI FHIR R4       │ ──────▶ │ FastAPI · PostgreSQL 16              │ ◀──────▶ │ Flutter web/macOS │
 │ 11 synthetic GBM   │  pull   │ ingest · pseudonymise · eCRF · review│          │ nurse · PI ·      │
 │ patients, 17 docs  │         │ local AI (Ollama) · hash-chain audit │          │ monitor (read-only)│
 └────────────────────┘         │ exports: CDISC ODM · FHIR QR+Prov.   │          └───────────────────┘
                                └──────────────────────────────────────┘
```

> **In:** FHIR R4 (mCODE-style) from a synthetic hospital. **Out:** CDISC ODM 1.3.2 and FHIR QuestionnaireResponse + Provenance. **Every value:** evidence span, confidence, model + prompt version, human decision, audit hash.

### 5.3 Slide 3 — What this is / is not

> **What this is**
> - A connected, local platform slice on **synthetic** data: FHIR ingest, pseudonymisation, live local AI extraction, human review, hash-chained audit, standards exports.
> - Evidence-linked and human-verified: AI proposes, people decide, nothing is exported unverified.
> - Reproducible on this laptop: `make reset && make demo` plus the two documented pre-steps.
>
> **What this is not**
> - Not real patient data, and not a hospital connection beyond this machine.
> - Not a medical device. No MDR claim. No clinical decision support.
> - Not validated, not production, not QMS-validated. No clinical accuracy claim; the only metrics are on a synthetic gold set.
> - Not a Gate 2 decision and not a build-budget commitment. Gate 2 still decides the real MVP.

### 5.4 Slide 4 — Next steps

> **Two gates before build spend**
> - **Gate 1 — evidence:** verified Yamicc analysis, landscape, capability gap. *Research in progress.*
> - **Gate 2 — decision:** MVP scope, roadmap, cost ranges.
>
> **What this demo changes**
> - The platform path is real: connected ingest, local AI, review, audit, exports.
> - The remaining work is engineering and validation, not a re-architecture.
>
> **Decision requested:** keep **MVP B** as the direction; approve finishing Gate 1. No build spend before Gate 2.

---

## 6. Claims: safe to say, and not allowed

### 6.1 Safe to say (with the label)

| Claim | Label / source |
|---|---|
| The demo runs locally: Flutter → FastAPI → PostgreSQL 16 → HAPI FHIR R4, all on this machine. | Verified in the rehearsal (§9) |
| New patients arrive over FHIR R4 and are pseudonymised on ingest (keyed HMAC); raw MRN and name are not stored in the app tables. | `backend/app/ingest/`, security review §3 SEC-04 |
| AI extraction uses a local open-weight model (`qwen2.5:7b-instruct`) behind one provider interface; `rules` is the deterministic fallback; every run logs model + prompt version. | `backend/app/ai/`, `/ai/providers`, `/ai/prompts` |
| Every proposal must carry an evidence span that is re-located in the source; an unsupported value becomes an abstention. | `backend/app/ai/span.py`, `ollama.py` |
| Every action is hash-chained with a key held outside the database and anchored outside it. Verify detects edits and deletions, including changes made directly in the database. | `backend/app/audit.py`, `/audit/verify`; SEC-02 fixed in CEL-1785 (`f5b0386`) and re-verified live (`c60b2be`) |
| The 8 baseline participants carry pre-computed fixture extractions (`provider: fixture`, model `demo-extractor v0.1`); only synced arrivals are extracted live (`ollama`, `qwen2.5:7b-instruct`, prompt `extract_v4`). | `backend/app/seed.py`; `app/assets/data/extractions.json`; live run §9 |
| Exports: CDISC ODM 1.3.2 study XML with AuditRecords; FHIR QuestionnaireResponse + Provenance + AuditEvents, with write-back. | `backend/app/export/`; rehearsal §9 |
| On the synthetic gold set (13 documents, 57 annotations) the local model scored 100 % precision and recall with 6.6 % abstention. | `backend/eval/results/latest.json` |
| Standards named: FHIR R4 (+ mCODE-style), CDISC ODM; ICD-O-3 used; LOINC/SNOMED entries marked unverified where they are placeholders. | 06 §1; `study.json`; UI shows "placeholder, unverified" |
| Yamicc is a credible Dutch rare-cancer ecosystem orchestrator; on public evidence no capability reaches Pilot. | `deliverables/D2_yamicc.md` §0, §4 |
| EHR-to-EDC is a funded product category (OpenClinica, IgniteData, Medidata, Oracle, Castor Catalyst, Paradigm). | `deliverables/d3_competitive_landscape.md` §4.1 |
| Research data capture/admin automation generally falls outside MDR; matching/recommendation may be a device under Rule 11. | 07 §3, MDCG 2019-11 [INFERRED] |
| The security review found no Critical issue for this local demo and lists 3 High / 7 Medium / 9 Low to fix before any pilot. | `deliverables/security_review_demo_v3.md` §1 |

### 6.2 Not allowed in the room

| Do not say | Why |
|---|---|
| Any clinical accuracy or time-saving figure ("95 % accurate", "saves 70 %") | Only a synthetic gold set exists; no clinical evidence. |
| "Clinically validated", "production-ready", "hospital-ready", "MDR compliant", "GDPR compliant" | No validation, QMS, DPIA or legal sign-off. |
| "Secure" without the qualifier | The four High findings are fixed (CEL-1785 `f5b0386`), but the Medium findings and a penetration test are open. Say "local demo; the gaps are documented". |
| "Yamicc cannot do this" / "Yamicc is only a mock-up" | Overclaim. Say what public evidence shows, nothing more. |
| "Yamicc's 650,000 patients / 20 %" as fact | [CLAIMED-C, unverified]; verify first. |
| "This replaces your EDC" | The design integrates external EDCs (FR-036). |
| "Open source" as settled | Licence not chosen; NFR-09 is a target. |
| "The audit cannot be tampered with" / "tamper-proof" | The chain is keyed and externally anchored, so verify catches DB-level edits and deletions — but the key and the anchor file sit on the same machine. Say the required §4.10 sentence: "hash-chained with a key held outside the database and anchored outside it; verify detects edits and deletions, including changes made directly in the database". |
| "Annex 11 compliant" / "GCP compliant" / "certified" / "validated audit trail" | The mechanism is now keyed and anchored, but there is no validation, QMS evidence or certification, and the key/anchor are local (Q9). A demo mechanism is not a compliance control. |
| Calling the 46 pre-computed fixture proposals "live AI" | Only synced arrivals (GBM-NL-009/010/011) are live `ollama` output. The baseline queue is `provider: fixture`, model `demo-extractor v0.1` (Q2b). |
| "All data stays in the hospital" | In this demo everything is on one laptop; the production trust boundary is a design, not a demonstrated deployment. |

---

## 7. Q&A prep (honest answers, no invented numbers)

**Q1. Is this real patient data?**
No. Every patient, document and number is synthetic. The FHIR server, the database and the model all run on this laptop. The banner is on every screen, by rule.

**Q2. Is the AI live?**
Yes — for the documents that arrived through Sync. A local Qwen 2.5 7B model through Ollama read the new pathology report during the demo; you saw its proposals, its abstentions, and its model and prompt version. That document took about 45 seconds; the full queue can run for 3–6 minutes, so we open the first finished document. `rules` is the deterministic fallback if the model is slow. No paid API, and no data leaves the machine.

**Q2b. Then why do the pre-loaded participants say `fixture`?**
Because the 8 baseline participants are seeded with **pre-computed** extractions: provider `fixture`, model `demo-extractor v0.1`, generated offline with no model call. They exist to populate the review queue and the synthetic gold set, not to fake a live run. Only documents that arrive through Sync — tonight GBM-NL-009/010/011 — are extracted live by `ollama` (`qwen2.5:7b-instruct`, prompt `extract_v4`). Provenance is stored per proposal and shown on the card, so a reviewer can always tell which run produced it.

**Q3. How accurate is it?**
I will not give you a clinical accuracy number. On our synthetic gold set — 13 documents, 57 annotations — precision and recall are 100 %, with 6.6 % abstention. That proves the pipeline and the evaluation harness, not performance on Dutch hospital text. A 100 % result on a synthetic set is a warning sign, not a selling point. The evaluation plan is precision/recall per field, abstention, calibration and reviewer time, first on synthetic data and later on site data under approval.

**Q4. Why show a wrong value on purpose?**
Because a safety mechanism shown only on easy cases is marketing. The wrong MGMT row is a scripted fixture from the gold set; the correction and the abstention are the two cases a regulated buyer cares about. The live model's own output is on the new patient; it abstained on nine fields rather than guess.

**Q5. Is this a medical device?**
We make no MDR claim. Research data capture and admin automation generally fall outside MDR; anything that recommends treatment or matches a patient to a drug may be a device under Rule 11. We deliberately did not build that. A classification decision precedes any such feature.

**Q6. What happens when the AI is wrong?**
The reviewer sees the evidence span in one glance, the confidence, and an abstention when the source does not support a value. No value becomes research data without a human accept or correct. Every step is in the audit chain, including the original proposal and the correction. The AI never writes to the EHR, and only human-verified values are exported.

**Q7. What is the architecture?**
Flutter (web and macOS) → FastAPI → PostgreSQL 16 as the canonical store; HAPI FHIR R4 for ingest and write-back; a separate AI service that talks to the API, never the database; exports to CDISC ODM and FHIR. The canonical-model choice is a demo decision; the T-chain decision stays open (`deliverables/backend_architecture.md`, 06 §2).

**Q8. Which standards do you use?**
FHIR R4 with mCODE-style resources in and out; CDISC ODM 1.3.2 out; ICD-O-3 for histology; LOINC/SNOMED where a code exists, and the UI marks placeholder codes as unverified. A terminology service and full mCODE conformance are Phase 2. Naming the standards publicly is a deliberate differentiator: Yamicc says "open standards" but names none in its primary sources (`deliverables/D2_yamicc.md` §0).

**Q9. Can I trust the audit trail?**
It is tamper-detecting, and it is now keyed and anchored. Every action is hash-chained with a key held outside the database and anchored outside it — an HMAC key outside the DB and an append-only anchor file outside the DB — and the verifier checks every link and every anchor line. Verify detects edits and deletions, including changes made directly in the database: we tested a superuser who disabled the trigger and deleted the newest event, then made a normal app write, and Verify chain reported "chain rewritten (does not match the external anchor)". **What could still defeat it?** Someone with both the database and the key and the anchor file on this machine. In production the key and anchor go to a separate service (roadmap). I do not claim Annex 11, GCP compliance or certification for it; the demo proves the mechanism, not the production control.

**Q10. Why does the corrected row say provider `fixture`?**
Because that wrong-value case is a scripted fixture from the synthetic gold set, loaded through the backend on purpose. The live model's proposals on GBM-NL-009 carry provider `ollama`, model `qwen2.5:7b-instruct` and prompt `extract_v4`. We label provenance per proposal so a reviewer can always tell which came from which run.

**Q11. Is it secure?**
It is a local demo, not a secure deployment. The security review found no Critical issue for this scope, but it lists High findings: a committed default JWT secret, an unkeyed audit chain, an unauthenticated HAPI with known CVEs, and a default pseudonymisation key. These were fixed in CEL-1785 (`f5b0386`) — no default secrets, a keyed and externally anchored audit chain, least-privilege DB roles, and HAPI's own DB user with pinned CORS — and SEC-02 was re-verified live (`c60b2be`). The Medium findings and a penetration test are still open before any pilot, and the code must not be lifted into a hosted environment as is (`deliverables/security_review_demo_v3.md`).

**Q12. What about GDPR and pseudonymisation?**
Pseudonymisation here is a keyed HMAC of the hospital MRN; the raw MRN and name are not persisted in the app tables. Pseudonymised is not anonymous. A DPIA, the controller/processor model, the legal basis and EU-only hosting are Phase 1–2 work with legal review. Nothing is solved yet (07 §1).

**Q13. How is this different from Yamicc?**
Carefully: Yamicc is a credible ecosystem orchestrator with partners, a clinical anchor and public demos. On the public record, no capability reaches Pilot: the Annual Report describes a paper prototype and an initial technical demonstration, and the 2026 demo components include a mock-up EHR [CLAIMED]. They name no interoperability standard publicly. Our wedge is a working, standards-first, evidence-linked review layer — and we should integrate, not disparage (`deliverables/D2_yamicc.md` §0, §3).

**Q14. Isn't this Castor Catalyst or IgniteData?**
Partly, and that is fine. EHR-to-EDC is a funded category; Castor Catalyst is the closest commercial threat, and IgniteData/OpenClinica/Medidata already ship extraction with human acceptance. We integrate with EDCs rather than replace them. The remaining differentiation is narrow: Dutch-language documents, hospital-side processing, audit-grade review and a low-cost multi-site model — and whether that is enough is exactly what Gate 1 and Gate 2 must test (`deliverables/d3_competitive_landscape.md` §0, §4).

**Q15. Can it connect to Epic or HiX?**
Not in this demo. The target is FHIR R4 with Dutch EHR adapters; a connector conformance test is Phase 2–3. HAPI is a stand-in for the hospital endpoint, not a claim of an Epic/HiX integration.

**Q16. What exactly is exported?**
Two formats: a study-wide CDISC ODM 1.3.2 XML with the eCRF metadata, the verified values and audit records; and a per-participant FHIR bundle with a QuestionnaireResponse, Provenance (AI vs human) and AuditEvents, pushed back to the FHIR server. Only human-verified values leave the platform.

**Q17. What do the roles do?**
Demo JWT roles: research nurse (review and eCRF), monitor (read-only plus source data verification), PI (study actions and export). The monitor view is genuinely read-only: the API returns 403 on a decision and the UI disables the buttons. Production needs OIDC/SSO, MFA and site scoping (SEC-07).

**Q18. Why local Ollama and not GPT/Claude?**
Gate 3: no paid APIs, and no data may leave the machine. A local open-weight model keeps the data boundary and the cost at zero. The provider interface is pluggable; a hosted model is a decision for the Board, not a demo default.

**Q19. What is still missing before a hospital could use it?**
Real connectors and terminology services; an IdP with SSO/MFA and site scoping; the audit key and anchor moved to a separate service, plus secret management; HAPI hardening and network isolation; validation evidence and a QMS; a DPIA and legal agreements; a penetration test. That is Phase 2–4 and the larger part of the work.

**Q20. What does a pilot cost, and when?**
I will not invent a number. Phase 3 is a controlled single-hospital pilot; cost ranges come with Gate 2. The demo is cheap; the pilot is not.

**Answering rule:** if you do not know, say "we have not measured that" or "that is Gate 1 / Gate 2 work". Never fill a gap with a number.

---

## 8. Failure plan

| Failure | Response |
|---|---|
| Backend down / "Local backend is down" | Continue in the offline snapshot (read-only banner). Say "the app keeps the last snapshot; writes need the local backend". Use the recording for sync/export. |
| FHIR panel "Unreachable" | Skip the sync beat; go to Participants and use the existing queue. Say "the hospital endpoint is down; the platform keeps the last synced data". |
| Sync returns 0 created | Already synced. Point at the previous run row and continue; never press twice. |
| Model still running when you reach 009 ("Queue is empty") | Go back to **4.4b** and continue the integrations/audit/AI-quality talk; check every ~30 s, open the first finished arrival document. The queue needs **3–6 min** (measured 323 s ≈ 5.4 min). If still empty at 5:30, review GBM-NL-002's pre-computed queue; say "the model runs in the background; the review loop does not block on it". |
| Sync was pressed late | 4.4b absorbs the wait (3–6 min). Never stand in silence and never press Sync twice. |
| Ollama slow | The service falls back to `rules` automatically; the proposals show Provider `rules`. Same story, and this is the recovery line if the queue runs to 6 min. |
| Review write fails | Say "the local API rejected the write"; go to audit and show what did persist. |
| Audit human rows missing | The writes did not persist; use the recording's audit segment; continue. |
| "Chain broken" / "chain rewritten" | Say "a row was changed outside the application; catching that is what the verifier does"; move on. Do not claim the demo is unbreakable. |
| Export 403 / disabled | You are on nurse or monitor; switch to tab A (PI). |
| Push fails | Show the generated bundle; say write-back needs the FHIR server. |
| Layout breaks on the projector | Switch to the macOS app, or use the recording at 1440×900. |
| Question you cannot answer | "We have not verified that; it goes on the open-questions list." Write it down. |

**Never:** install anything, open a terminal, restart containers, or debug in front of the audience. The only exception is switching to the backup recording.

---

## 9. Rehearsal log (against the real build)

Rehearsed **2026-11-21 14:00–14:40 CET** on `dev` at `a8e397f` (W7 connected app, after the W7 screenshots). The shared stack was being exercised by QA at the same time, so the timed flow was re-run against a **private scratch database** on port `8011` seeded with the same migrations and seed (`yamicc_rehearsal`), with the shared HAPI FHIR server (11 patients after loading `--set arrivals`). This avoids stealing or corrupting another agent's run. The scratch database and backend were removed afterwards.

**Update 2026-11-21 15:20 — CEO cold-start verification.** The CEO verified Demo v3 from a cold start on the running stack. Three claims were tightened in this revision (CEL-1786): the audit wording (§4.10, §6.2, Q9), the fixture-versus-live provenance split (§1, 4.3, 4.6, Q2/Q2b, Q10), and the model-queue timing (run sheet, 4.4b, 4.6). **Measured on that machine: a sync queues 7 runs and the local model needs about 3 minutes to finish all 7; the first proposals arrive sooner (45–70 s).** This script now schedules a 4.4b talk-through so the presenter never waits in silence.

**Update 2026-11-21 ~15:45 — CEO re-verification after the security fixes (CEL-1789).** The CEO re-verified Demo v3 from a cold start after CEL-1785 (`f5b0386`) and the verify fix (`c60b2be`). Two changes in v3.1: (1) **audit wording is upgraded** — the chain is keyed (HMAC, key outside the DB) and anchored in an append-only file outside the DB, and the CEO's tamper test returned **"chain rewritten (does not match the external anchor)"**; the switch-back note is retired and the old "database-level anchoring is the next hardening step" wording is gone (§1, 4.4b, 4.10, 6.1, 6.2, Q9). (2) **the live-extraction wait is re-timed** — after a fresh sync **all 17 runs in the queue at that time finished in 323 s (~5.4 min)**, against **179 s (~3 min)** earlier; seven are live Ollama arrival runs and the first arrival documents finish early, so the run sheet now reserves a **3–6 minute** window and opens the first finished arrival document first, filling the wait with integrations, audit and AI-quality talk. The `rules` fallback stays the recovery line.

**What was verified, with commands**

| Check | Command / method | Result |
|---|---|---|
| Stack healthy | `make health STRICT=1` | Postgres 16.16, HAPI 8.12.0, backend `/health` ok, web serving |
| Clean seed | `uv run python -m app.seed --reset` (scratch DB) | 8 participants, 46 pre-computed fixture proposals, 7 open queries, 45 eCRF fields, 3 sites, audit 47 events |
| Arrivals staged | `python3 fhir-seed/load.py --set arrivals` | HAPI 11 patients (baseline 8 + arrivals 3); platform still 8 |
| FHIR sync | `POST /integrations/fhir/sync` (PI) | **1.47 s**; participants created 3 / existing 8; documents created 7 / existing 10; extraction runs queued 7; 218 resources fetched |
| Pseudonymisation count | `GET /integrations` after sync | `pseudonymisedPatients: 11` |
| Live extraction (Ollama) | `python -m app.ai --run-id 11 --provider ollama` on `DOC-009-PATH` | **44.2 s**; 15 proposals (6 proposed, 9 abstained); model `qwen2.5:7b-instruct`; prompt `extract_v4@1ef2060c673d` |
| Per-document model latency | provider timed on all 7 arrival documents | **35–66 s** (mean ≈45 s); `rules` < 10 ms |
| Whole queue (earlier) | CEO cold-start verification, 2026-11-21 15:20 | **179 s ≈ 3 min**; first proposals at **45–70 s** |
| Whole queue (re-verified) | CEO re-verification, 2026-11-21 ~15:45, after a fresh sync | **323 s ≈ 5.4 min** for all 17 runs in the queue at that time (7 are live Ollama arrival runs); plan **3–6 min** |
| Accept | `POST /extractions/EXT-0018/decision {"decision":"accept"}` | 200 in **71 ms**; eCRF value written |
| Correct | `POST /extractions/EXT-0020/decision {"decision":"correct","correctedValue":"Unmethylated"}` | 200 in **21 ms**; `reviewState=corrected`; before/after recorded |
| Defer | `POST /extractions/EXT-0023/decision {"decision":"defer"}` | 200 in **27 ms** |
| Audit verify | `GET /audit/verify` | `ok: true` in **33 ms**, head hash returned |
| Audit tamper test (SEC-02) | Superuser disabled the trigger, deleted the newest event, then a normal app write; `GET /audit/verify` | **`ok: false`** — reason **"chain rewritten (does not match the external anchor at event N)"** (CEO, 2026-11-21 ~15:45) |
| Human audit filter | `GET /audit?source=human` | `extraction.decision` rows for defer/correct/accept + `ecrf.value_set` rows |
| ODM export | `GET /studies/GBM-NL-2026-01/export/odm` (PI) | 200 in **204 ms**, **9 694–10 525 bytes**, `ItemData` for verified values, `AuditRecord` present |
| FHIR export | `GET /participants/GBM-NL-002/export/fhir` (PI) | 200 in **43 ms**, 4 779 bytes, resources `QuestionnaireResponse`, `Provenance`, `AuditEvent`×3 |
| FHIR push | `POST /participants/GBM-NL-002/export/fhir/push` (PI) | 200 in **3.3 s**, **6 resources** written with `_history` |
| Monitor is read-only | `POST /extractions/EXT-0020/decision` as monitor | **403** "Role 'monitor' may not do this (needs nurse, pi)" |
| Monitor SDV | `POST /participants/GBM-NL-002/ecrf/MGMTPROM/sdv` (and `HISTOLOGY`) | 200; value now has `sdvBy: monitor`, `sdvAt`; UI shows "SDV done" |
| Seed 404 guard | SDV on a not-yet-verified field | 404 (expected; SDV needs a verified value) |
| AI eval data | `GET /ai/eval` | 13 documents, 57 TP, 0 FP/FN, precision/recall/F1 1.0, abstention 6.6 %, provider ollama, prompt `extract_v4` |
| UI labels and layout | W7 screenshots `deliverables/design/w7_after/` (1440×900, real build) + source review of every screen | Labels in §4 match the build; review/monitor/audit/export states confirmed |

**What was not verified by this agent (honest limits)**
- No browser or GUI control in this session, so the click path was not driven with a mouse. QA (CEL-1781) owns the interactive web + macOS click path ×3; W7's screenshots and the widget tests cover rendering. A human must do one full dress rehearsal before Monday (see Remaining below).
- Timings for the spoken text were measured with `say -r 140` (see below), not the presenter's voice.
- The shared QA run was mutating the main database during this rehearsal; that is why exact counts in §4.3/§4.10 are labelled "fresh reset" or omitted.

**Spoken-text timing (`say -r 140`, measured) and click budget**

| Segment | Spoken (`say -r 140`) | Clicks | Planned window |
|---|---|---|---|
| 4.1 Opening | 0:26 | — | 0:30 |
| 4.2 Login | 0:25 | 0:05 | 0:30 |
| 4.3 Dashboard | 0:28 | 0:04 | 0:40 |
| 4.4 Sync | 0:40 | 0:08 | 0:50 |
| 4.4b Queue wait: integrations + audit + AI-quality talk | 1:22 (prepared) | — | 2:00 |
| 4.5 Participant | 0:25 | 0:05 | 0:25 |
| 4.6 Live extraction | 0:38 | 0:05 | 0:40 |
| 4.7 Accept | 0:31 | 0:05 | 0:30 |
| 4.8 Correct | 0:32 | 0:18 | 0:45 |
| 4.9 Defer | 0:20 | 0:05 | 0:20 |
| 4.10 Audit | 0:34 | 0:10 | 0:30 |
| 4.11 AI quality | 0:25 | 0:05 | 0:15 |
| 4.12 Export | 0:41 | 0:14 | 0:40 |
| 4.13 Monitor | 0:21 | 0:10 | 0:30 |
| 4.14 Is / is not | 0:29 | 0:05 | 0:40 |
| **Total** | **8:17** (re-measured 2026-11-21) | **≈1:25** | **9:20** |

Content ends at **~9:20** in practice; the 10:00 slot leaves **≈40 s of slack** for a hostile question or a slow local model, and more if you leave the wait block early. If the human read is slower than 140 wpm, cut in this order: AI-quality per-field detail, dashboard alert detail, participant summary. **Never cut 4.4b while the model queue runs** — that is the silence the CEO flagged — but leave it as soon as the first arrival document is finished.

**Presenter card (print this)**
`0:00 open · 0:30 PI login · 1:00 dashboard (8/24, 46 pre-computed queue) · 1:40 Sync now (3 patients, 7 docs, 7 arrival runs) · 2:30 queue wait: integrations + audit + AI-quality talk (3–6 min; leave when the first arrival doc is done) · 4:30 Participants → GBM-NL-009 · 4:55 review 009 (live ollama, abstains; fixture ≠ live) · 5:30 accept histology · 5:55 002 → correct MGMT · 6:30 009 → defer RANO · 6:45 audit → Verify chain → Human → EXT-0020 (keyed + externally anchored; no compliance or certification claim) · 7:15 AI quality (screen; 100 % synthetic, say why) · 7:30 ODM → FHIR 002 → Push (6 resources) · 8:10 tab B monitor → 002 → Mark SDV · 8:40 is/is not + ask · 9:20 stop`

**Remaining for the human/engineer before Monday**
1. **`make demo` starts the AI worker** (`backend/app/ai`) since CEL-1784: background process, `ops/run/ai.pid`, log `ops/logs/ai.log`, stopped by `make stop`. Pre-flight step 4 now only confirms one worker runs. Keep `make demo` in front of the audience, never `make ai`.
2. **`make seed` loads the FHIR baseline only.** The arrivals are staged by `make stage-arrivals` (`fhir-seed/load.py --set arrivals`). Keep it in the pre-flight; it does not touch platform data.
3. **`deliverables/demo_script.md` must be re-pointed at the freeze commit** on Sunday 20:00 (record `git rev-parse --short HEAD` in §2 and §9).
4. **Record the 2–3 minute backup** of silent clicks on the frozen build, then play it once from local disk.
5. **One full dress rehearsal in the presenter's voice** with a listener; take two hostile questions from §7. If the human read is slower than 140 wpm, cut in this order: AI-quality per-field detail → dashboard alert detail → participant summary. **Never cut** the sync result, the correction, the abstention, the audit verify, or the "is not" slide.
6. **Confirm the two-tab setup at 1440×900** on the presenting laptop (tab A PI, tab B monitor) and that the monitor tab is already signed in before the talk.

---

## 10. Open items and risks

| # | Item | Owner | Effect on the demo |
|---|---|---|---|
| R1 | `make demo` now starts **one** AI worker (CEL-1784); `make health STRICT=1` fails if it is missing or if two run | DevOps / Engineer | Pre-flight step 4 confirms one pid; if it dies on stage, no live proposals (recovery §8) |
| R2 | Arrivals are staged by `make stage-arrivals`, not by `make reset`/`make seed` | DevOps / Junior Engineer | Pre-flight step 2; without it the sync creates 0 participants |
| R3 | Ollama is a single local server; QA + demo workers share it, and concurrent runs serialise; measured queue **3–6 min** (323 s ≈ 5.4 min; earlier 179 s ≈ 3 min) | Engineer | 4.4b fills the wait; open the first finished arrival document; `rules` is the fallback; never wait in silence |
| R4 | Security High findings SEC-01/02/03/04 fixed in CEL-1785 (`f5b0386`); SEC-02 re-verified live (`c60b2be`); Medium findings and a pen test remain | CTO / Security | Say "local demo"; do not claim "secure", "compliant" or "certified" |
| R5 | `Session.demoToday` is fixed at 2026-11-23; after Monday the UI date is stale | Engineer | Cosmetic; keep the clock for the demo |
| R6 | AI quality shows 100 % on the synthetic set; a Board member may read it as marketing | PM | The script pre-empts it (§4.11, Q3) |
| R7 | The `/ai/eval` screen hint says "Run `make eval`", but there is no `make eval` target | Engineer / DevOps | Cosmetic; do not show the empty state on stage |
| R8 | No browser in this session; the interactive click path is QA/human-owned | QA / PM | QA CEL-1781 + the dress rehearsal cover it |
| R9 | The 8 baseline participants are fixtures (`provider: fixture`); only synced arrivals are live. Easy to mislabel under pressure | PM | §1, 4.3, 4.6 and Q2b state the split; never call fixture output "live" |
| R10 | Residual audit risk: the DB, the HMAC key and the anchor file are on one machine | CTO / CEO | Q9 line: "someone with all three could still defeat it; separate service is roadmap"; no "compliant" or "certified" |

---

## 11. Appendix — sources and labels

Access date for all web sources: 2026-11-21. Labels: [VERIFIED] primary source; [INFERRED] reasoned; [CLAIMED] single/non-stable source; [GK] general knowledge.

| ID | Source | Label |
|---|---|---|
| A1 | `deliverables/D2_yamicc.md` — verified Yamicc analysis (organisation, funding, platform status, maturity) | Internal research |
| A2 | `deliverables/d3_competitive_landscape.md` — vendor profiles and cross-cutting findings | Internal research |
| A3 | `deliverables/security_review_demo_v3.md` — audit, pseudonymisation, authz, containers | Internal review |
| A4 | `deliverables/backend_architecture.md` — backend architecture and data model | Internal |
| A5 | `deliverables/D7b_visual_direction.md` — visual direction v2 and screen specs | Internal |
| A6 | `deliverables/D5_users_workflows.md` — user journeys and roles | Internal research |
| A7 | `deliverables/design/w7_after/` — real-build screenshots, 1440×900 | Evidence |
| A8 | `06_ARCHITECTURE_STANDARDS_AI.md` — standards, stack, AI architecture and evaluation | Source pack |
| A9 | `07_REGULATORY_SECURITY.md` — MDR/AI Act, GDPR, security, validation | Source pack |
| A10 | `fhir-seed/README.md` — synthetic hospital inventory and the arrivals story | Source pack |
| A11 | `ops/RUNBOOK.md` — local stack, recovery, cold start | Source pack |
| A12 | yamicc.org/about-us, /what-we-do, /the-challenges (via D2) | [VERIFIED] |
| A13 | i~HD oncology eSource task force, Cambridge 2025 (via 03 §1) | [VERIFIED] |
| A14 | Rare-cancer "20 % / 650,000 per year" | [CLAIMED-C, unverified] — do not present as fact |

**Definition of done for this script:** every spoken claim carries a label or is framed as opinion; every step names the click, the line, what the audience should notice and a recovery; the "is not" slide is read without softening; the Q&A cites the research deliverables and never invents a number; the run was rehearsed against the real connected build and the timings are recorded above.
