# Monday demo v4 — the connected platform, now with screening and two hospitals

Owner: PM (CEL-1808) · Version **4.0** · Demo: **Monday 2026-11-23**, **12–15 minutes** + Q&A
Build: Flutter (web + macOS) → FastAPI → PostgreSQL 16 → HAPI FHIR R4 (two hospitals), all local · **synthetic data only**
Stack: v4 on **web :8081 / API :8001** · Postgres :5434 · hospital 1 :8091 · hospital 2 :8092
Code freeze: **Sunday 2026-11-22 20:00 CET** · Stability gate: **Sunday 18:00 CET** (if v4 is not stable, Monday uses v3 — §11)
This script replaces the v3.1 script for the v4 build. The v3 checkpoint stays frozen at `~/yammic-demo-v3` (tag `demo-v3-checkpoint`, `eb634e2`).

> **Why v4 exists.** The Board froze v3 as a checkpoint and asked for a more complete demo. v4 adds five things on top of the v3 story: **screening**, a **second hospital**, **data quality and queries**, a **patient timeline**, and **protocol-to-form**. The v3 core is unchanged: a real backend, FHIR ingest, live local AI extraction, human review, a hash-chained audit, and standards exports.

---

## 0. What v4 is, in plain language (the Board reads only this first)

**The same working platform you saw in v3, with five additions. Everything runs on this laptop, on synthetic data.**

1. **Screening.** The AI checks a new patient against the trial's 13 entry criteria and shows the exact sentence in the hospital documents for each one. A coordinator confirms each criterion. If evidence is missing, the patient **stays in screening**; the platform does not guess and does not enrol.
2. **Two hospitals.** Two hospital FHIR feeds (hospital 1 and hospital 2) are connected at the same time, each with its own FHIR server and its own pseudonymisation key. One **Sync** pulls both feeds, and the dashboard compares the study's three sites or filters to one.
3. **Data quality and queries.** Five automatic checks flag contradictions — for example, the MRI says partial resection but the surgery note says complete. The monitor asks the site a question; the nurse answers; the monitor closes it and marks source-data verification.
4. **Patient timeline.** Surgery, radiotherapy, chemotherapy cycles, scans, diagnosis and visits appear on one line, in date order, and each event links to the source document.
5. **Protocol to form.** The AI reads the protocol summary and proposes the eCRF fields and the entry criteria, with the source sentence. The PI approves, and that creates a new audited form version. Existing values keep the version they were captured under.

**What it is not:** not real patient data, not a medical device, not validated, and not a clinical accuracy claim. Every AI value is a proposal until a person accepts, corrects or defers it. The audit, the exports and the honesty rules from v3 are unchanged.

**What the Board must remember:** (1) it is connected; (2) the product is the **review loop**, not the model; (3) it is **honest** about what it does not know.

**Decision requested at the end:** keep **MVP B** (AI-assisted data capture) as the direction and let us finish the Gate 1 evidence, so **Gate 2** can decide scope, roadmap and cost.

---

## 1. At a glance

**One-sentence thesis**
> This is a connected, multi-site clinical-research platform on synthetic data: two hospital feeds arrive over FHIR, a local model proposes eCRF values and screening evidence, a person decides, and a hash-chained audit plus standards exports make the result reviewable.

**What the audience must remember (3 things)**
1. **It is connected.** Two FHIR R4 servers, a real backend and a real database; the sync is live, and new documents are extracted live on the local model.
2. **The product is the review loop.** Evidence → AI proposal → human decision → audit → export. Screening, queries, timeline and protocol-to-form all use the same rule: AI proposes, a person decides.
3. **It is honest.** Synthetic data, local only, not a medical device, no accuracy claim beyond a synthetic gold set. When evidence is missing, the platform says so.

**Deck rule:** four slides maximum — title, connected slice, "is / is not", next steps. The product is the deck. Do not add slides.

---

## 2. What is new in v4 (say this only if asked)

| Then (v3, frozen checkpoint) | Now (v4, this demo) |
|---|---|
| One hospital (HAPI on :8090), 8 baseline patients. | **Two hospitals** (HAPI :8091 and :8092), own database and pseudonymisation key each; one Sync pulls both. Dashboard site filter and site comparison. |
| Review queue: accept / correct / defer. | Same review loop, plus **screening**: 13 entry criteria with evidence, coordinator confirmation, sign-off, and a visible "still in screening" state when evidence is missing. |
| One alert about an MGMT contradiction. | **Five data-quality rules** (`DQ-01`..`DQ-05`) open **queries** automatically; monitor asks, nurse answers, monitor closes and marks SDV. |
| Visit list on the participant page. | **Timeline** of surgery, radiotherapy, chemotherapy, scans, diagnosis and visits, each linked to its source document. |
| One approved eCRF form. | **Protocol → form:** the AI proposes 15 fields and 13 criteria from the protocol synopsis; the PI approves a new audited version. |
| 10-minute run. | **12–15 minute run**; the v3 beats are still inside it. |

The v2 rule "no backend, no network" stays withdrawn. The rule now: everything runs locally (Docker Desktop + local processes). No hosting, no real data, no outreach, no paid APIs (Gate 3).

---

## 3. Where to work, and what not to touch (strict)

- Work **only** in `~/yammic-v4`, branch `v4`. Commit small and often; never rewrite history.
- **Do not touch** `~/yammic-demo`: it holds an uncommitted rename pending a Board decision.
- **Do not touch** `~/yammic-demo-v3`: it is the frozen v3 fallback.
- **Do not stop, restart or reset the running v3 stack** (Postgres :5433, HAPI :8090, backend :8000, web :8080). The Board may use it. v4 runs on its own ports: Postgres **:5434**, hospital 1 **:8091**, hospital 2 **:8092**, backend **:8001**, web **:8081**.
- Rules: synthetic data only, local only, free local AI only (rules + Ollama). No Claude API, no outreach.
- If v4 is not stable by **Sunday 18:00 CET**, Monday uses **v3** (§11). Keep v4 runnable at every commit.

---

## 4. Pre-flight (T-30 to T-0)

Run this once, 30 minutes before. **Do not do any of it on stage.** `make reset` deletes only the **v4** volume; the v3 stack is not touched.

```bash
cd ~/yammic-v4
git switch v4
git rev-parse --short HEAD        # write it here: ________

# 1. Clean slate: v4 Postgres + both HAPI servers, backend seed, both baselines.
#    Expect: 8 participants, 46 pre-computed fixture proposals, 7 open queries, 3 sites;
#            hospital 1 has 8 patients, hospital 2 has 5.
make reset

# 2. Stage the arrivals on BOTH hospital servers (platform data untouched).
#    Expect: hospital 1 has 11 patients, hospital 2 has 7; platform still has 8 participants.
make stage-arrivals

# 3. Start backend + one AI worker + web, and health-check all components.
make demo
make health STRICT=1              # Result: OK — full v4 demo stack is healthy (both hospitals).

# 4. Confirm exactly ONE AI worker runs (make demo starts it).
ops/ai-workers.sh                 # expect one pid
tail -3 ops/logs/ai.log           # expect no ai.poll_error lines
```

| # | Check | Pass condition |
|---|---|---|
| 1 | `make health STRICT=1` | Postgres, hospital 1, hospital 2, backend, AI worker, web all OK |
| 2 | Browser tab A: `http://127.0.0.1:8081`, full screen (F11), 100 % zoom | Login screen, banner "Synthetic data — prototype, not for clinical use" |
| 3 | Tab A: **PI** → **Use demo account** | Dashboard; "Connected · N ms"; no offline banner |
| 4 | Dashboard | **8/24**; **AI queue 46**; **Open queries 7**; **eCRF verified 0 %**; 3 sites; site rows **3/10, 3/8, 2/6** |
| 5 | Integrations | Hospital 1 connected; **Pseudonymised patients 0**; **Last sync never**; no runs |
| 6 | Screening | **1 to screen** (GBM-NL-004); 8 referred |
| 7 | AI review | **46 pending** (fixtures), no live 009 cards yet |
| 8 | Tab B: same URL, sign in **Nurse**; Tab C: **Monitor** | Tab B normal; tab C read-only banner; keep both in the background |
| 9 | Export (PI) | "Generate export" enabled |
| 10 | Laptop | Power, Do Not Disturb, notifications off, screen saver off |
| 11 | Backup recording: 2–3 minutes of silent clicks on the v4 build, played once from local disk | Plays offline |
| 12 | PIDs | exactly one AI worker (`ops/ai-workers.sh`); `make health STRICT=1` shows `[ OK ] ai` |

**Why the arrivals are staged before the demo but synced on stage:** the pull is live (about 3 seconds for both feeds), and the new patients are genuinely new to the platform at the moment you press **Sync now**. Staging them in the hospital servers is the realistic scenario: the hospitals have the data, the platform does not yet.

**After the sync, expect (fresh reset, measured 2026-11-21):**
- **18 participants** (8 baseline + 3 from hospital 1 + 7 from hospital 2), **3 sites**: SITE-01 4, SITE-02 11, SITE-03 3.
- **25 new documents** and **25 extraction runs**: hospital 1 adds 3 patients / 7 documents; hospital 2 adds 7 patients / 18 documents.
- The result line shows the **last** source (hospital 2): **"Sync completed: 142 resources fetched, 18 new documents, 18 extraction runs queued."**
- **3 to screen** (GBM-NL-004, GBM-NL-011, GBM-NL-207), **0 screen-fail**, **9 open queries**.
- The AI queue **starts at 46 and grows** as the worker processes the new documents (up to 15 proposals per document). Do not quote a fixed number after the sync; the queue is the work.

**If step 5 shows "Last sync" not "never":** someone synced after the reset. Run `make reset`, then `make stage-arrivals`, then `make demo`, and repeat from step 2. A sync on stage must create the arrivals; otherwise the live beat is dead.

**If the v3 stack is also running:** leave it alone. Do not run `make stop` in the v3 checkout while the v4 worker runs (the v3 stop script also matches the v4 worker). v4's own `make stop` is port-scoped.

---

## 5. Run sheet (14:00 content, 15:00 with Q&A)

| Time | Segment | Screen / route | Tab | Goal |
|---|---|---|---|---|
| 0:00–0:35 | Opening + honesty frame | Slide 1 | A | Set trust; name what changed |
| 0:35–1:00 | Login | `/login` | A | Connected; three roles; banner |
| 1:00–2:00 | Dashboard + **two hospitals** | `/` | A | Live KPIs; site filter and comparison |
| 2:00–3:10 | Integrations + **Sync** | `/integrations` | A | One click pulls both feeds; 25 docs queued |
| 3:10–5:20 | **Screening** | `/screening` | A | 13 criteria; evidence; confirm; incomplete stays in screening |
| 5:20–6:40 | **Data quality + queries** | `/queries` | A → B | DQ rules; monitor asks; nurse answers |
| 6:40–7:20 | **Timeline** | `/participants/GBM-NL-002/timeline` | A | One line; each event links to its document |
| 7:20–8:25 | **Protocol → form** | `/protocol` | A | AI proposes; PI approves; v2 active |
| 8:25–10:05 | **AI review**: live 009 + correct 002 + defer | `/review` | A | The centrepiece; live local model |
| 10:05–10:50 | **Audit verify** | `/audit` | A | Hash chain; human decisions |
| 10:50–11:25 | Monitor: close query + SDV | `/queries`, `/participants/GBM-NL-002` | C | Role separation; source verification |
| 11:25–11:40 | AI quality | `/ai-quality` | A | Synthetic gold set; abstention |
| 11:40–12:30 | **Export + FHIR write-back** | `/export` | A | ODM + FHIR; round trip |
| 12:30–13:20 | Is / is not + decision | Slides 3–4 | A | Honest limits; one ask |
| 13:20–15:00 | Stop talking / Q&A | — | — | Invite questions |

**Pacing:** ≈140 spoken words per minute. The prepared spoken text is **10:59** (measured on 2026-11-21 with `say -r 140`); click and route budget is **≈1:10**; that is **12:09** of content, and the plan leaves **~1:10** of slack inside 13:20. The five v4 segments (screening, queries, timeline, protocol, monitor) also absorb the **3–6 minute** model queue, so there is **no silent wait** in v4. **Never cut:** the sync result, the screening abstention, the correction, the audit verify, or the "is not" slide.

**12-minute cut (if the room is tight):** skip the site-filter comparison (keep the site table), shorten screening to GBM-NL-207 only, skip the timeline, and show AI quality for 10 seconds. Keep every v3 beat and the screening/audit/export. **Do not** skip the 009 live review; it is the proof that the model runs locally.

---

## 6. Segment scripts

> Bracketed text is a stage direction. Quotes are spoken text. "Click" lines are the click path.
> Demo clock is fixed at **23 Nov 2026** (`Session.demoToday`). Data is from `GBM-NL-2026-01`, three fictional sites.
> Three tabs: **A = PI** (main flow; the PI can also confirm screening criteria in this build), **B = Research nurse** (query answer), **C = Monitor** (read-only, query close, SDV). Do not resize between tabs.

### 6.1 Opening — 0:00–0:35

**Slide 1:** *"Clinical research, connected — the platform, one step further"*. Subtitle: *Synthetic data · local · prototype · not for clinical use.*

> "Thank you. You froze v3 as a checkpoint and asked for more. So this is v4: the same connected platform, now with patient screening, a second hospital, data-quality queries, a patient timeline and protocol-to-form. Everything is local, every patient is synthetic, and none of it is a medical device. Fifteen minutes, then questions."

*Why this opener:* it accepts the checkpoint, names the five additions in one breath, and sets the two boundaries before the first click.

### 6.2 Login — 0:35–1:00

**Click:** open tab A at `http://127.0.0.1:8081`. Click the **PI** role card → **Use demo account**. (The demo password is `demo`; the card fills it.)

> "We start at the front door. Three demo roles: research nurse, monitor, principal investigator. I sign in as PI, because export and form approval are PI actions. The screen already knows the backend is healthy, and it names the stack: FHIR R4 and Postgres 16. The amber banner never goes away: synthetic data, prototype, not for clinical use."

**Audience should notice:** the amber banner; three role cards with one-line scopes; "Local backend healthy · FHIR R4 · Postgres 16"; "SSO is disabled in the local demo. Demo password: demo."

**Recovery:** if the left panel says "Local backend is down", do **not** debug on stage. Say "the local backend is not up; the app can show the last snapshot" and continue in the offline snapshot (read-only) for the dashboard, screening and review story; skip sync/export and use the recording for those beats.

### 6.3 Dashboard + the second hospital — 1:00–2:00

**Screen:** `/` — **Research dashboard**, signed in as PI.

> "This is live from Postgres, not from a bundled file. Eight participants, target twenty-four. Zero eCRF fields verified yet. Forty-six AI proposals waiting — these are pre-computed from our gold set, so the queue is populated before the live run. Seven open queries. The connection pill shows the round-trip to the local API, and the date is the demo clock."

**Click:** the site chip **FUMC Noordhaven (fictional)**.

> "Two hospitals are connected. This is hospital two, Noordhaven: three patients on treatment of a target of eight, two open queries. It has its own FHIR server and its own pseudonymisation key. Click back to All sites: the comparison table shows both hospitals next to each other. Same platform, same review loop, two sites."

**Click:** **All sites**.

**Audience should notice:** "Connected · N ms"; "Data as of 23 Nov 2026"; **8/24**; **eCRF verified 0 %** ("0 of 45 fields · verified only"); **Open queries 7**; **AI queue 46**; **AI acceptance —**; site chips for FUMC Zuidhaven, FUMC Noordhaven, Westpark; the site comparison with Screening / Eligible / Enrolled / Queries / SDV / AI accept / Enrolment; the alert "GBM-NL-002: AI MGMT proposal contradicts the pathology report."

**Provenance note:** the **46 baseline proposals are pre-computed fixtures** (`provider: fixture`, model `demo-extractor v0.1`, no model call), not live output. The live model runs only on the synced arrivals (6.9). If asked, say so plainly (Q2b).

**Click next:** **Integrations** in the PLATFORM section of the sidebar.

**Recovery:** if the numbers differ because the state is not a fresh reset, do not apologise and do not quote exact counts: say "the figures are live from the backend; the shape is what matters" and move on. The only count that must be exact on stage is the sync result.

### 6.4 Integrations + Sync — 2:00–3:10 (the missing backend, live)

**Screen:** `/integrations`.

> "Integrations. The hospital is a HAPI FHIR R4 server on this machine, standing in for the hospital EHR. Both hospitals are green, and the platform has pseudonymised zero patients so far. The hospitals have just received five new referrals: three at hospital one, two at hospital two. I press Sync once."

**Click:** **Sync now** (leave **Full re-sync** unchecked). Wait for the result line (≈3 s). Then point at the run rows.

> "One click pulled both feeds. Hospital one added three patients and seven documents; hospital two added seven patients and eighteen documents, because its five baseline patients were not in the platform yet. Twenty-five new documents, twenty-five extraction runs queued, ten new participants. The run log keeps the two runs, with the source and the counts. The hospital data was pseudonymised at the boundary; the raw hospital numbers and names are not in the platform tables."

**Audience should notice:**
- Panel "Hospital 1" · **Connected**; Endpoint `http://127.0.0.1:8091/fhir`; FHIR version **4.0.1**; Server **HAPI FHIR Server 8.12.0**.
- **Pseudonymised patients 0 → 11** (hospital 1; hospital 2 is on the dashboard).
- Result line (last source, hospital 2): **"Sync completed: 142 resources fetched, 18 new documents, 18 extraction runs queued."**
- "Sync runs" table: two rows, newest first — **#2 hospital 2 (Created 167, ≈1049 ms)** on top, **#1 hospital 1 (Created 220, ≈1494 ms)** below, both **Completed**, by **pi**. The table has no source column in this build; the run order is the source order (hospital 1, then hospital 2).
- Two hospital FHIR servers stay green; no error toast.

**Click next:** **Screening** in the STUDY section. (The model is already working through the 25 documents in the background.)

**Recovery:**
- If the result says **0 new documents / 0 runs**, the arrivals were already synced. Say "this machine was synced during rehearsal; the run log shows the arrivals" and point at the earlier run rows. Then continue to screening on the existing queue. Do **not** press Sync twice.
- If a panel says **Unreachable**, that hospital's FHIR container is down. Say "one hospital endpoint is unreachable; the platform keeps the last synced data and keeps working" and continue. Restart `make up` only after the demo.
- If **Sync now** is disabled, you are signed in as monitor (tab C). Switch to tab A (PI).

### 6.5 Screening — 3:10–5:20 (AI proposes, a person decides)

**Screen:** `/screening`.

> "Screening. Three new referrals to screen, zero screen-fails, eighteen patients referred in total. The AI has already checked every referral against the trial's thirteen entry criteria. Each criterion shows met, not met or unknown, with the exact source sentence. A coordinator confirms every criterion before the platform allows a sign-off."

**Click:** select **GBM-NL-207** (SITE-02, **5 met · 8 unknown**). Then click the **INC-01** row.

> "This is a new referral from hospital two. The AI found five criteria with evidence: age sixty-three, KPS eighty, no prior radiotherapy, no prior systemic therapy, and a male participant. Here is the exact sentence in the discharge letter. Eight criteria are unknown — the pathology report and the labs have not arrived. The AI does not guess."

**Click:** **Confirm AI "met" rows**.

> "I confirm the five that have evidence. The progress says five of thirteen confirmed, and the Sign off button stays disabled. That is the control: the platform will not let me sign off a referral with eight unchecked criteria. This patient stays in screening until the missing report arrives. That is the honest state, not an error."

**Click:** **All** (second row of the filter chips). Scroll the queue to **GBM-NL-201** (SITE-02, **13 met · 0 unknown**). Select it.

> "Switch to All and you see the complete case from hospital two: thirteen met, zero unknown, every criterion with a source sentence. This patient is already on treatment at the hospital, so the platform shows them as enrolled, not in the referral queue. When a patient like this is referred into the trial, the coordinator confirms all thirteen and signs off; the buttons appear as the state changes. We do not force a sign-off on an incomplete or already-treated record on stage."

**Audience should notice:**
- Header: **"3 to screen · 0 screen-fail · 18 referred. AI proposes, a person decides."**
- Queue: **GBM-NL-004** (0 met · 13 unknown), **GBM-NL-011** (3 met · 10 unknown), **GBM-NL-207** (5 met · 8 unknown), all **Screening**.
- 207's checklist: 5 **Met · AI** with **Evidence**, 8 **Unknown · AI** with no evidence; **Sign off** disabled; "5 of 13 confirmed by a person".
- 201's checklist: 13 **Met · AI**, 0 unknown, **"13 met · 0 not met · 0 unknown"**; the patient pill **Enrolled** (on treatment at the hospital).
- Evidence boxes quote the Dutch source, the document id and `rules · confidence 0.95+`.

**If you have 30 seconds:** open the **INC-03 MGMT** row on 201 and show the pathology sentence; it is the same value the review corrects on 002 later.

**Recovery:** if the queue is empty, the sync did not create participants; say "the screening queue is empty because the sync did not create referrals in this run" and go to Participants → 009 for the review loop. If **Confirm AI "met" rows** fails, say "the local API rejected the write" and continue; do not retry on stage more than once.

### 6.6 Data quality + queries — 5:20–6:40 (the monitor asks, the nurse answers)

**Screen:** `/queries` (tab A, PI, read-only for this beat).

> "Data quality and queries. Five automatic rules run after every sync and every decision. They flag real conflicts: dates out of order, values out of range, a lab against an eligibility criterion, and disagreements between documents. Here are nine open queries. The high one is the MGMT contradiction: the AI proposed 'methylated', the pathology report says 'unmethylated'."

**Click:** the **GBM-NL-002 · MGMTPROM** high query (row 3 after a fresh sync) to open the thread. Then switch to **tab B** (Nurse).

> "The monitor opened the question. The nurse owns the answer. In tab B I am the research nurse. I answer in the source, not in a chat: the pathology report says unmethylated; the eCRF will be corrected at review."

**Click (tab B):** type the answer, **Send answer**. It becomes **Answered**.

> "The query moves to 'answered'. It is not closed yet: the monitor closes it after seeing the correction. That order matters: the question, the answer, the evidence, then the close."

**Audience should notice:** the 9 open queries, including **DQ-05** rows ("ANC 1.4 below INC-05", "KPS 50 % below INC-04"); the high MGMT query; the thread with the monitor and the nurse; the status chips **Open → Answered**.

**Recovery:** if the MGMT query is already answered or closed, use **DQ-05 GBM-NL-203** (KPS 50) instead: the nurse answers "KPS 50 % at baseline; the site confirms the value; INC-04 is not met." The story is the same.

### 6.7 Timeline — 6:40–7:20 (the patient record on one line)

**Click:** **Participants** → **GBM-NL-002** → **Timeline** (top-right of the participant header).

> "The timeline. Twenty events from the source records, in date order: screening, surgery, pathology, the post-operative MRI, radiotherapy, six chemotherapy cycles, the visits. Each event links to the document it came from. This is the record a monitor reads before source verification; it is built from the same FHIR facts and documents, not typed twice."

**Click:** the **Chemotherapy** filter once.

> "Filter by category. The same events, no retyping."

**Audience should notice:** "20 events from the source records. Each links to its document."; category chips All / Visit / Surgery / Diagnosis / Scan / Radiotherapy / Chemotherapy; the date column on the left; the document link under each event (DOC-002-SURG, DOC-002-PATH, DOC-002-MRI, DOC-002-DIS).

**Recovery:** if the timeline is empty, say "this participant has no synced events in this run" and open GBM-NL-201's timeline instead (the second hospital's complete record).

### 6.8 Protocol → form — 7:20–8:25 (the AI reads the protocol, the PI approves)

**Click:** **Protocol → form** in the PLATFORM sidebar → **Analyse protocol** (top right).

> "Protocol to form. The AI reads the protocol synopsis and proposes the eCRF fields and the entry criteria, with the exact source sentence for each. Fifteen fields, thirteen criteria — the same thirteen we just screened against. The PI checks the proposal and approves. Approval is the only way the form and the criteria change."

**Click:** the proposed **v2** row if it is not already selected (it is first). Scroll once to the **Entry criteria** table. Then **Approve version** (bottom of the detail panel) → **Approve** in the dialog.

> "I approve version two. The dialog tells me the approval is written to the audit trail, and existing values keep their own form version. That is the control: a protocol change never silently rewrites captured data."

**Audience should notice:** "The AI reads the protocol synopsis and proposes form fields and entry criteria. The PI approves."; **v2** proposed (15 fields, 13 criteria); each field with **Section / Type / Req. / Protocol sentence**; the entry criteria table; the approve dialog text; after approval, **v2 · Active** and "Approved by pi".

**Recovery:** if **Analyse protocol** returns no proposals, say "the protocol parser is not loaded in this build; the criteria we screened against are the approved v1 set" and skip to Export later. If **Approve version** is disabled, you are on nurse/monitor; switch to tab A (PI). If the screen shows both v1 and v2 as "Active" (a label quirk in this build), say "v2 is now the current version; v1 is kept for the values already captured" and move on.

### 6.9 AI review — 8:25–10:05 (the centrepiece: live 009, correct 002, defer)

**Click:** **Participants** → **GBM-NL-009** → **Review AI (N)** in the participant header.

> "This is the live run on a patient that arrived through Sync a few minutes ago. The local Qwen 2.5 model, seven billion parameters, running on this laptop through Ollama, read the pathology report. No data leaves the machine, no paid API. Here is what it produced: histology, IDH status, MGMT — unmethylated, which matches the report — and nine abstentions. The model does not guess what the document does not say. Every proposal carries its evidence span, a confidence, the model id and the prompt version, and the run and the proposal are in the audit chain."

**Click:** the **Histology (central review)** card whose source is **DOC-009-PATH** and confidence **0.95** (not the MRI card at 0.35, not the discharge-letter card at 0.98). Then **Accept** (or press `A`).

> "Three columns: the source on the left, proposals in the middle, the target eCRF field on the right. I pick the pathology-report card: histology, 0.95, with the sentence highlighted in the Dutch report. The same field also appears from the discharge letter and the MRI; the source pane tells me which is which. It is still an AI proposal, not research data. I accept. One click, and it becomes a verified eCRF value with my name, the time, and the source extraction attached."

**Click:** set the participant dropdown to **GBM-NL-002**. Scroll the middle column to the **MGMT promoter methylation** card (provider `fixture`, conf 0.72, source `DOC-002-PATH`). Click it → **Correct** (or `C`) → replace `Methylated` with `Unmethylated` → **Save correction**.

> "Now the case that matters. GBM-NL-002, the MGMT promoter. The proposal says methylated at 0.72. The report says unmethylated. This is a scripted fixture from our synthetic gold set, injected on purpose: a demo that only shows the model being right is not a demo of a safety mechanism. I correct it and save. The eCRF now says unmethylated; the original proposal, the correction, the reviewer and the time are all kept."

**Click:** set the dropdown back to **GBM-NL-009**; click any **Date of progression (RANO)** card (all three documents abstain: grey, `Not stated`, conf 0.00); click **Defer** (or `D`).

> "Third case. The RANO progression date. The model abstains: not stated, confidence zero, accept disabled. We defer it; it becomes an open task for the next visit, not a silent gap. Reject is for a proposal that is not in the source at all; it asks for a reason and records it."

**Audience should notice:**
- Toolbar: "AI extraction review"; dropdown **GBM-NL-009**; progress counts the 009 proposals that have finished (15 per document; more than one document by now).
- Left pane: **"SOURCE · pathology report · DOC-009-PATH"**, Dutch source text with the matched sentence highlighted.
- Middle: cards with amber **"AI · Unverified"**, `conf 0.95`, low-confidence flags where present; nine of the fifteen pathology proposals are grey **"AI abstained"**.
- Right: **Model `qwen2.5:7b-instruct`**, **Prompt `extract_v4@1ef2060c673d`**, **Provider `ollama`**.
- After accept: card and target turn green **"Verified · Accepted"**; "Verified by pi"; the sidebar **AI review** badge drops by one.
- For 002: the MGMT card shows **Provider `fixture`**, `conf 0.72`, **Low confidence**, and the highlighted source says "unmethylated"; after save, **"Verified · Corrected"**, value **Unmethylated**.
- For 009 RANO: **Accept** disabled with "Accept is disabled: no evidence in source"; the card becomes grey **"Deferred"**.

**Provenance note:** every card on 009 is live `ollama` output. The 8 baseline participants (including GBM-NL-002, used for the correction) carry **pre-computed** fixtures: `provider: fixture`, model `demo-extractor v0.1`. Never call those "live". The review loop is identical; only the provenance differs.

**Timing note (measured 2026-11-21):** Ollama takes **35–66 s per document** on this laptop (57 s for DOC-009-PATH); `rules` is <10 ms. The worker processes runs sequentially, in creation order. After a fresh sync the **hospital 1 arrivals are queued first**, so GBM-NL-009's first document is finished in about **1 minute** and all three by about **3 minutes**. You reach this screen at **8:25**, so the live proposals are ready. The whole 25-document queue needs **15–25 minutes**, but you never wait for it: review 009 and move on.

**Recovery:**
- If 009 shows **"Queue is empty"** when you arrive, the worker is still on another document. Say "the local model is still reading the reports; the platform does not block on it — let us review the pre-computed queue while it works", switch the dropdown to **GBM-NL-002**, and do Accept/Correct/Defer there. Return to 009 after the audit if proposals have arrived.
- If no new proposals arrive at all, the AI worker is not running. Say "the local model service is not running in this snapshot; these are the pre-computed gold-set proposals, and the live run is what we rehearsed" and continue. Do not start a terminal on stage.
- If Ollama is slow, the service **falls back to `rules` automatically**; the proposals then show Provider `rules`. Same story, different provider: "the local model was slow, so the deterministic extractor took over; the review loop is identical."
- If **Accept** is disabled, the card has no valid evidence span (an abstention). Pick a proposed card (amber), not a grey one.
- If the write fails ("Could not save: …"), say "the local API rejected the write" and continue; the audit will show the truth.

### 6.10 Audit trail + hash-chain verify — 10:05–10:50

**Click:** **View audit trail** in the target pane (or **Audit trail** in the sidebar). Click **Verify chain**. Then click the **Human** segment.

> "Audit trail. Press Verify chain [press]: every event, no gaps and no edits, with the head hash — the chain is keyed outside the database and anchored outside it, so this also catches edits and deletions made directly in the database. Filter to human actions. There are the decisions, newest first — the defer, the correction, the accept, the screening confirmations, the query answer — next to the eCRF writes they triggered. Open the correction: before methylated, after unmethylated, by whom, when, and which model and prompt proposed it."

**Required wording (do not improvise):** "Every action is hash-chained with a key held outside the database and anchored outside it. Verify detects edits and deletions, including changes made directly in the database." Do **not** say "tamper-proof", "cannot be tampered with", "Annex 11 compliant", "GCP compliant" or "certified". The fixed chain detects DB-level edits, but the check depends on the key and the anchor file on this machine; a compliance or certification claim needs validation and a separate key/anchor service.

**Click next:** click the **`extraction.decision`** row for the correction (Entity `EXT-0020`).

**Audience should notice:**
- Green banner: **"Chain verified · N events, no gaps or edits. Head …"** (N grows with the session; do not quote a fixed number; measured 176 events after the full rehearsal).
- `Human` filter: `extraction.decision` rows (defer, correct, accept), `screening.criterion_confirmed`, `query.answered`, `query.closed`, `ecrf.sdv`, and `ecrf.value_set` rows, newest first; "Hide sign-ins" is on by default.
- Detail panel: **BEFORE `{"reviewState":"pending"}` / AFTER `{… "decision":"correct" …}`**, actor, role, time, **Prompt** version, **Prev hash** and **Hash** (copyable).
- The verify call is fast (≈0.1 s locally).

**Recovery:** if the human rows are missing, the review writes did not persist. Say "the review state did not persist in this run" and show the recording's audit segment; continue. If **Verify chain** returns red, read the reason — e.g. "chain rewritten (does not match the external anchor at event N)" or "events deleted from the end of the chain". Say "a row was changed outside the application; catching that is what the verifier does" and move on. Do not debug, and do not claim the demo is unbreakable: someone with the database, the key and the anchor file on this machine could still defeat it (Q9).

### 6.11 Monitor: close the query and mark SDV — 10:50–11:25

**Click:** switch to **tab C** (Monitor, pre-signed in). Click **Queries** → the **GBM-NL-002 MGMT** thread → **Close query**.

> "The monitor. Same data, read-only: the banner says so, and the write actions on the eCRF are disabled. The nurse answered the MGMT contradiction; the PI corrected the value. The monitor sees the evidence, closes the query, and independently marks source-data verification."

**Click:** **Participants** → **GBM-NL-002**. Scroll the eCRF table to **MGMT promoter methylation** (the corrected value); click **Mark SDV**.

> "MGMT: SDV done. The monitor independently confirms the value the PI corrected. That is the role separation a sponsor expects. The dashboard KPI and the site row move with it."

**Audience should notice:** blue banner **"Monitor · queries and source verification only. The eCRF is read-only."**; top bar role **Monitor**; on `/review`, Accept/Correct/Defer/Reject disabled; the query status **Closed**, closed by monitor; the eCRF value **Verified** with **SDV done** and `sdvBy: monitor`; the dashboard **Open queries** drops and **SDV** increments.

**Recovery:** if tab C is signed out or shows the offline snapshot, switch the role from tab A (avatar → **Switch demo role**) and sign in as Monitor; that takes about 10 s. If time is short, skip the close and just show the read-only banner and disabled buttons; the audit already proved the roles.

### 6.12 AI quality — 11:25–11:40

**Click:** **AI quality** in the PLATFORM sidebar.

> "AI quality, as I said while the model ran. Per-field precision, recall and abstention for the local model and the rules fallback; the hard cases — the hedged wording at 0.38, the wrong MGMT, the abstention; and the model and prompt registry with the prompt hash. The hundred percent is on the synthetic gold set only; real evaluation comes with site data under approval."

**Audience should notice:** segmented **ollama | rules**; metric strip **Precision 100 % · Recall 100 % · F1 100 % · Abstention 7 % · Documents 13**; subtitle "Precision and recall against the gold set, per field and provider. Quality is measured before it is trusted."; the per-field table; the **Model registry** and **Prompt registry** (`rules` and `ollama` local; active prompt `extract_v4` with a SHA-256).

**If you are short of time:** show the metric strip and the registry, then move to Export. If the queue ran long, skip the scroll.

**Recovery:** if the screen says "No evaluation results yet", the committed eval JSON is not present. Say "the eval harness output is not loaded in this build; the number we can defend is that the gold set has 13 documents and 57 annotations" and move on. Do not invent metrics.

### 6.13 Export + FHIR write-back — 11:40–12:30

**Click:** **Export** (PLATFORM). Format **CDISC ODM 1.3.2** → **Generate export**. Point at the XML. Then click the **FHIR R4 bundle** card; choose **GBM-NL-002** (it is preselected as the participant with verified values); **Generate export**; then **Push to FHIR server**.

> "Export. Only human-verified values leave the platform; AI proposals never do. CDISC ODM one point three two: the study snapshot for sponsors and regulators, including the audit records. Generate — about eleven kilobytes of XML. Then the FHIR bundle for GBM-NL-002: a QuestionnaireResponse, Provenance that separates AI from human, and the AuditEvents. And push it back to the hospital FHIR server. That is a full round trip: in over FHIR, out over FHIR, with evidence."

**Audience should notice:**
- Header: "Only human-verified eCRF values leave the platform. AI proposals are never exported. Every export is audited."
- Steps **1 Choose format · 2 Generate · 3 Download or push**.
- ODM preview: `ODM 1.3.2` XML with `ItemData` for the verified values and `AuditRecord` elements (about 11 KB; measured 11,075 bytes).
- FHIR preview: `QuestionnaireResponse`, `Provenance`, `AuditEvent` entries (8 entries in the rehearsal).
- Push result: **"Pushed to the FHIR server: N resources written."** (the bundle carries the audit events; the push itself is audited; measured 9 resources in 6.1 s).
- **Do not press Download on stage**; it opens a file dialog and breaks the flow.

**Recovery:** if **Generate export** is disabled, you are on monitor/nurse or offline. Switch to tab A (PI). If the FHIR push fails (hospital server down), show the generated bundle and say "the export is valid; write-back needs the FHIR server, which is down in this run." If the ODM preview is truncated ("… more characters in the download"), that is by design (8 000-char preview), not an error.

### 6.14 Is / is not + decision — 12:30–13:20

**Slide 3 → 4.** Read the four "is not" lines; do not soften them.

> "So, plainly. This is a connected, local, multi-site slice of the platform on synthetic data. It is not real patient data, not a hospital connection beyond this laptop, not a medical device, and not validated. It is not an accuracy claim, and it is not a Gate 2 decision. The v4 additions are real: screening with evidence, two hospitals, data-quality queries, a timeline and protocol versioning. What we ask is narrow: keep MVP B as the direction, and let us finish the Gate 1 evidence so Gate 2 can decide scope, roadmap and cost. Thank you."

### 6.15 Stop — 13:20–15:00

Stop talking. Leave the last slide up. Invite questions. Use the Q&A prep; if you do not know, say "we have not measured that" or "that is Gate 1 / Gate 2 work".

---

## 7. Slide text (copy-paste)

### 7.1 Slide 1 — Title

> **Clinical research, connected**
> The platform, one step further
>
> Screening · two hospitals · data quality · timeline · protocol-to-form
> Synthetic data · everything local · prototype · not for clinical use
>
> *Yamicc · 23 November 2026*

### 7.2 Slide 2 — The connected slice (one diagram, no bullets)

```
 Hospital 1 EHR                 Yamicc platform (this laptop)                  Experience
 ┌──────────────────┐  FHIR  ┌────────────────────────────────────────┐  REST  ┌────────────────────┐
 │ HAPI FHIR R4     │ ─────▶ │ FastAPI · PostgreSQL 16                │ ◀────▶ │ Flutter web/macOS  │
 │ 11 synthetic GBM │        │ ingest · pseudonymise · screening      │        │ nurse · PI ·       │
 │ patients, 17 docs│        │ review · queries · timeline · forms    │        │ monitor (read-only)│
 ├──────────────────┤  FHIR  │ local AI (Ollama) · hash-chain audit   │        └────────────────────┘
 │ Hospital 2 EHR   │ ─────▶ │ exports: CDISC ODM · FHIR QR+Prov.     │
 │ 7 synthetic GBM  │        └────────────────────────────────────────┘
 └──────────────────┘
```

> **In:** FHIR R4 (mCODE-style) from two synthetic hospitals. **Out:** CDISC ODM 1.3.2 and FHIR QuestionnaireResponse + Provenance. **Every value:** evidence span, confidence, model + prompt version, human decision, audit hash.

### 7.3 Slide 3 — What this is / is not

> **What this is**
> - A connected, local **multi-site** platform slice on **synthetic** data: FHIR ingest, pseudonymisation, live local AI extraction, screening, human review, data-quality queries, a timeline, form versioning, hash-chained audit, standards exports.
> - Evidence-linked and human-verified: AI proposes, people decide, nothing is exported unverified, and incomplete screening stays open.
> - Reproducible on this laptop: `make reset`, `make stage-arrivals`, `make demo`.
>
> **What this is not**
> - Not real patient data, and not a hospital connection beyond this machine.
> - Not a medical device. No MDR claim. No clinical decision support.
> - Not validated, not production, not QMS-validated. No clinical accuracy claim; the only metrics are on a synthetic gold set.
> - Not a Gate 2 decision and not a build-budget commitment. Gate 2 still decides the real MVP.

### 7.4 Slide 4 — Next steps

> **Two gates before build spend**
> - **Gate 1 — evidence:** verified Yamicc analysis, landscape, capability gap. *Research in progress.*
> - **Gate 2 — decision:** MVP scope, roadmap, cost ranges.
>
> **What this demo changes**
> - The platform path is real: multi-site ingest, local AI, screening, review, audit, exports.
> - The remaining work is engineering and validation, not a re-architecture.
>
> **Decision requested:** keep **MVP B** as the direction; approve finishing Gate 1. No build spend before Gate 2.

---

## 8. Claims: safe to say, and not allowed

### 8.1 Safe to say (with the label)

| Claim | Label / source |
|---|---|
| The demo runs locally: Flutter → FastAPI → PostgreSQL 16 → two HAPI FHIR R4 servers, all on this machine. | Verified in the rehearsal (§10) |
| New patients arrive over FHIR R4 from both hospitals and are pseudonymised on ingest (keyed HMAC, per site); raw MRN and name are not stored in the app tables. | `backend/app/ingest/`, security review §3 SEC-04 |
| One Sync pulls both hospital feeds; the dashboard filters and compares the sites. | `GET /integrations`, `/studies/{id}/sites`; rehearsal §10 |
| AI extraction uses a local open-weight model (`qwen2.5:7b-instruct`) behind one provider interface; `rules` is the deterministic fallback; every run logs model + prompt version. | `backend/app/ai/`, `/ai/providers`, `/ai/prompts` |
| Screening checks 13 protocol criteria and returns `met | not_met | unknown` with a verified source span; a coordinator confirms every criterion, and the platform blocks sign-off until all are checked. | `backend/app/ai/screening.py`, `backend/app/workflows.py`, `deliverables/protocol_criteria.json` |
| Five data-quality rules (`DQ-01`..`DQ-05`) open queries automatically; the lifecycle is open → answered → closed, with role checks and per-field SDV. | `backend/app/quality.py`, `/data-quality/rules`, `/queries`, `/participants/{id}/ecrf/{field}/sdv` |
| The timeline is built from FHIR facts, visits and documents, in date order, each event linked to its source. | `GET /participants/{id}/timeline`, `deliverables/D7c_v4_screens.md` |
| Protocol-to-form proposes 15 fields and 13 criteria from the protocol synopsis; only the PI can approve, and approval creates an audited version; existing values keep their `formVersion`. | `POST /studies/{id}/forms/propose`, `/forms/{v}/approve`, `backend/app/ai/protocol.py` |
| Every action is hash-chained with a key held outside the database and anchored outside it. Verify detects edits and deletions, including changes made directly in the database. | `backend/app/audit.py`, `/audit/verify`; SEC-02 fixed in CEL-1785 (`f5b0386`) and re-verified live (`c60b2be`) |
| The 8 baseline participants carry pre-computed fixture extractions (`provider: fixture`, model `demo-extractor v0.1`); only synced documents are extracted live (`ollama`, `qwen2.5:7b-instruct`, prompt `extract_v4`). | `backend/app/seed.py`; live run §10 |
| Exports: CDISC ODM 1.3.2 study XML with AuditRecords; FHIR QuestionnaireResponse + Provenance + AuditEvents, with write-back. | `backend/app/export/`; rehearsal §10 |
| On the synthetic gold set (13 documents, 57 annotations) the local model scored 100 % precision and recall with 6.6 % abstention. | `backend/eval/results/latest.json`; `/ai/eval` |
| Standards named: FHIR R4 (+ mCODE-style), CDISC ODM; ICD-O-3 used; LOINC/SNOMED entries marked unverified where they are placeholders. | 06 §1; `study.json`; UI shows "placeholder, unverified" |
| The security review found no Critical issue for this local demo and lists 3 High / 7 Medium / 9 Low to fix before any pilot. | `deliverables/security_review_demo_v3.md` §1 |

### 8.2 Not allowed in the room

| Do not say | Why |
|---|---|
| Any clinical accuracy or time-saving figure ("95 % accurate", "saves 70 %") | Only a synthetic gold set exists; no clinical evidence. |
| "The AI decides eligibility" | The coordinator decides; the AI proposes criterion states with evidence. |
| "Every patient in the queue is trial-enrolled" | The queue and the dashboard count hospital patients on treatment; trial enrolment is a separate status. |
| "Clinically validated", "production-ready", "hospital-ready", "MDR compliant", "GDPR compliant" | No validation, QMS, DPIA or legal sign-off. |
| "Secure" without the qualifier | The four High findings are fixed, but the Medium findings and a penetration test are open. Say "local demo; the gaps are documented". |
| "Yamicc cannot do this" / "Yamicc is only a mock-up" | Overclaim. Say what public evidence shows, nothing more. |
| "Yamicc's 650,000 patients / 20 %" as fact | [CLAIMED-C, unverified]; verify first. |
| "This replaces your EDC" | The design integrates external EDCs (FR-036). |
| "Open source" as settled | Licence not chosen; NFR-09 is a target. |
| "The audit cannot be tampered with" / "tamper-proof" | The chain is keyed and externally anchored, so verify catches DB-level edits and deletions — but the key and the anchor file sit on the same machine. Use the §6.10 sentence. |
| "Annex 11 compliant" / "GCP compliant" / "certified" / "validated audit trail" | The mechanism is keyed and anchored, but there is no validation, QMS evidence or certification. A demo mechanism is not a compliance control. |
| Calling the 46 pre-computed fixture proposals "live AI" | Only synced documents are live `ollama` output. The baseline queue is `provider: fixture`. |
| "All data stays in the hospital" | In this demo everything is on one laptop; the production trust boundary is a design, not a demonstrated deployment. |
| "The second hospital is live in production" | It is a second local HAPI server. The connector is the same pattern, not a hospital deployment. |

---

## 9. Q&A prep (honest answers, no invented numbers)

**Q1. Is this real patient data?**
No. Every patient, document and number is synthetic. Both FHIR servers, the database and the model run on this laptop. The banner is on every screen, by rule.

**Q2. Is the AI live?**
Yes — for the documents that arrived through Sync. A local Qwen 2.5 7B model through Ollama read the new documents during the demo; you saw its proposals, its abstentions, and its model and prompt version. The first document took about a minute; the full 25-document queue runs for 15–25 minutes, so we review the first finished documents and move on. `rules` is the deterministic fallback if the model is slow. No paid API, and no data leaves the machine.

**Q2b. Why do the pre-loaded participants say `fixture`?**
Because the 8 baseline participants are seeded with **pre-computed** extractions: provider `fixture`, model `demo-extractor v0.1`, generated offline with no model call. They exist to populate the review queue and the synthetic gold set, not to fake a live run. Only documents that arrive through Sync are extracted live by `ollama` (`qwen2.5:7b-instruct`, prompt `extract_v4`). Provenance is stored per proposal and shown on the card, so a reviewer can always tell which run produced it.

**Q3. How accurate is it?**
I will not give you a clinical accuracy number. On our synthetic gold set — 13 documents, 57 annotations — precision and recall are 100 %, with 6.6 % abstention. That proves the pipeline and the evaluation harness, not performance on Dutch hospital text. A 100 % result on a synthetic set is a warning sign, not a selling point. The evaluation plan is precision/recall per field, abstention, calibration and reviewer time, first on synthetic data and later on site data under approval.

**Q4. Does screening decide eligibility?**
No. The AI proposes `met`, `not_met` or `unknown` for each of the 13 criteria and shows the source sentence. A coordinator confirms every criterion; the platform blocks sign-off until all are checked. A `not_met` criterion blocks an eligible decision. If evidence is missing, the patient stays in screening or is screen-failed with a reason. That is a human decision, recorded in the audit.

**Q5. Why show a wrong value on purpose?**
Because a safety mechanism shown only on easy cases is marketing. The wrong MGMT row is a scripted fixture from the gold set; the correction and the abstention are the two cases a regulated buyer cares about. The live model's own output is on the new patient; it abstained on nine fields rather than guess.

**Q6. How do two hospitals work? And why does the dashboard show three sites?**
Two HAPI FHIR R4 servers, each with its own database and its own HMAC pseudonymisation key, are listed in `FHIR_SOURCES`. One Sync pulls both; the dashboard filters by site and compares them. The **study** has three sites; two hospital FHIR feeds are connected in this demo, and Westpark is study data without a FHIR feed. The connector is the same FHIR pull for both; in production each site would have its own endpoint, credentials and network path.

**Q7. What is a data-quality query?**
An automatic rule (`DQ-01`..`DQ-05`) or a monitor sees a conflict — a date out of order, a value out of range, a lab against an eligibility threshold, MRI vs surgery wording — and opens a query on the participant field. The nurse answers in the source; the monitor closes it and marks SDV. Every step is audited.

**Q8. What is the timeline built from?**
The FHIR facts, visits and source documents already stored for that participant. It is not typed twice. Each event carries the date, the category and a link to the document or resource it came from. The monitor uses it before source verification.

**Q9. How does protocol-to-form work?**
The AI reads the protocol synopsis and proposes the eCRF fields and entry criteria, with the exact source sentence for each. The PI reviews and approves; approval creates a new audited form version. Existing values keep the `formVersion` they were captured under, so a protocol change never silently rewrites data. Screening uses the approved criteria.

**Q10. Why are some patients not in the screening queue?**
The screening queue is for new **referrals**. A patient whose hospital record already has a confirmed diagnosis and is on treatment appears as **Enrolled** (the underlying status is active); the same patient's full 13-criterion checklist is visible under **All**. The distinction is deliberate: the trial status is not the same as the hospital treatment status. In the next build we will separate the two labels more clearly.

**Q11. Is this a medical device?**
We make no MDR claim. Research data capture and admin automation generally fall outside MDR; anything that recommends treatment or matches a patient to a drug may be a device under Rule 11. We deliberately did not build that. A classification decision precedes any such feature.

**Q12. What happens when the AI is wrong?**
The reviewer sees the evidence span in one glance, the confidence, and an abstention when the source does not support a value. No value becomes research data without a human accept or correct. Every step is in the audit chain, including the original proposal and the correction. The AI never writes to the EHR, and only human-verified values are exported.

**Q13. What is the architecture?**
Flutter (web and macOS) → FastAPI → PostgreSQL 16 as the canonical store; two HAPI FHIR R4 servers for ingest and write-back; a separate AI service that talks to the API, never the database; exports to CDISC ODM and FHIR. The canonical-model choice is a demo decision; the T-chain decision stays open (`deliverables/backend_architecture.md`, 06 §2).

**Q14. Which standards do you use?**
FHIR R4 with mCODE-style resources in and out; CDISC ODM 1.3.2 out; ICD-O-3 for histology; LOINC/SNOMED where a code exists, and the UI marks placeholder codes as unverified. A terminology service and full mCODE conformance are Phase 2. Naming the standards publicly is a deliberate differentiator: Yamicc says "open standards" but names none in its primary sources (`deliverables/D2_yamicc.md` §0).

**Q15. Can I trust the audit trail?**
It is tamper-detecting, and it is keyed and anchored. Every action is hash-chained with a key held outside the database and anchored outside it — an HMAC key outside the DB and an append-only anchor file outside the DB — and the verifier checks every link and every anchor line. Verify detects edits and deletions, including changes made directly in the database: we tested a superuser who disabled the trigger and deleted the newest event, then made a normal app write, and Verify chain reported "chain rewritten (does not match the external anchor)". **What could still defeat it?** Someone with both the database and the key and the anchor file on this machine. In production the key and anchor go to a separate service (roadmap). I do not claim Annex 11, GCP compliance or certification for it; the demo proves the mechanism, not the production control.

**Q16. Why does the corrected row say provider `fixture`?**
Because that wrong-value case is a scripted fixture from the synthetic gold set, loaded through the backend on purpose. The live model's proposals on GBM-NL-009 carry provider `ollama`, model `qwen2.5:7b-instruct` and prompt `extract_v4`. We label provenance per proposal so a reviewer can always tell which came from which run.

**Q17. Is it secure?**
It is a local demo, not a secure deployment. The security review found no Critical issue for this scope, but it lists High findings: a committed default JWT secret, an unkeyed audit chain, an unauthenticated HAPI with known CVEs, and a default pseudonymisation key. These were fixed in CEL-1785 (`f5b0386`) — no default secrets, a keyed and externally anchored audit chain, least-privilege DB roles, and HAPI's own DB user with pinned CORS — and SEC-02 was re-verified live (`c60b2be`). The Medium findings and a penetration test are still open before any pilot, and the code must not be lifted into a hosted environment as is (`deliverables/security_review_demo_v3.md`).

**Q18. What about GDPR and pseudonymisation?**
Pseudonymisation here is a keyed HMAC of the hospital MRN, with a separate key per site; the raw MRN and name are not persisted in the app tables. Pseudonymised is not anonymous. A DPIA, the controller/processor model, the legal basis and EU-only hosting are Phase 1–2 work with legal review. Nothing is solved yet (07 §1).

**Q19. How is this different from Yamicc?**
Carefully: Yamicc is a credible ecosystem orchestrator with partners, a clinical anchor and public demos. On the public record, no capability reaches Pilot: the Annual Report describes a paper prototype and an initial technical demonstration, and the 2026 demo components include a mock-up EHR [CLAIMED]. They name no interoperability standard publicly. Our wedge is a working, standards-first, evidence-linked review layer — and we should integrate, not disparage (`deliverables/D2_yamicc.md` §0, §3).

**Q20. Isn't this Castor Catalyst or IgniteData?**
Partly, and that is fine. EHR-to-EDC is a funded category; Castor Catalyst is the closest commercial threat, and IgniteData/OpenClinica/Medidata already ship extraction with human acceptance. We integrate with EDCs rather than replace them. The remaining differentiation is narrow: Dutch-language documents, hospital-side processing, audit-grade review and a low-cost multi-site model — and whether that is enough is exactly what Gate 1 and Gate 2 must test (`deliverables/d3_competitive_landscape.md` §0, §4).

**Q21. Can it connect to Epic or HiX?**
Not in this demo. The target is FHIR R4 with Dutch EHR adapters; a connector conformance test is Phase 2–3. HAPI is a stand-in for the hospital endpoint, not a claim of an Epic/HiX integration.

**Q22. What exactly is exported?**
Two formats: a study-wide CDISC ODM 1.3.2 XML with the eCRF metadata, the verified values and audit records; and a per-participant FHIR bundle with a QuestionnaireResponse, Provenance (AI vs human) and AuditEvents, pushed back to the FHIR server. Only human-verified values leave the platform.

**Q23. What do the roles do?**
Demo JWT roles: research nurse (review, screening, query answers), monitor (read-only plus source data verification and query close), PI (study actions, form approval, export). The monitor view is genuinely read-only: the API returns 403 on a decision and the UI disables the buttons. Production needs OIDC/SSO, MFA and site scoping (SEC-07).

**Q24. Why local Ollama and not GPT/Claude?**
Gate 3: no paid APIs, and no data may leave the machine. A local open-weight model keeps the data boundary and the cost at zero. The provider interface is pluggable; a hosted model is a decision for the Board, not a demo default.

**Q25. What is still missing before a hospital could use it?**
Real connectors and terminology services; an IdP with SSO/MFA and site scoping; the audit key and anchor moved to a separate service, plus secret management; HAPI hardening and network isolation; validation evidence and a QMS; a DPIA and legal agreements; a penetration test. That is Phase 2–4 and the larger part of the work.

**Q26. What does a pilot cost, and when?**
I will not invent a number. Phase 3 is a controlled single-hospital pilot; cost ranges come with Gate 2. The demo is cheap; the pilot is not.

**Answering rule:** if you do not know, say "we have not measured that" or "that is Gate 1 / Gate 2 work". Never fill a gap with a number.

---

## 10. Rehearsal log (against the real v4 build)

Rehearsed **2026-11-21 21:20–21:45 CET** on the **v4 stack** in `~/yammic-v4`: code at `1aeba7d` (rename), plus the docs-only security review `9a81b9a`; the v4 script is `00a88d5` (the freeze commit is recorded on Sunday). The frozen v3 stack ran untouched on 8080/8000. The rehearsal used the real v4 web build (:8081), the real backend (:8001), both HAPI servers, and the local Ollama worker. The click path was driven in a headless Chromium at **1440×900** with screenshots at every screen; the write path was verified with the same API calls the UI makes. No v3 data or process was touched.

**Stack and data**

| Check | Command / method | Result |
|---|---|---|
| Cold start | `make stop && make reset && make demo` | `make reset` **3:59**; `make demo` **0:52**; `make health STRICT=1` **OK** for both hospitals |
| Arrivals staged | `make stage-arrivals` | **8.2 s**; hospital 1 **11** patients, hospital 2 **7**; platform still **8** |
| Fresh sync | `POST /integrations/fhir/sync` | **2.57 s** wall; hospital 1 **1.49 s** (3 participants, 7 docs, 7 runs); hospital 2 **1.05 s** (7 participants, 18 docs, 18 runs); result line **142 resources fetched, 18 new documents, 18 runs**; **10 new participants** total |
| After sync | `GET /participants`, `/screening`, `/queries`, dashboard | **18 participants**; **3 to screen** (004, 011, 207); **9 open queries**; SITE-01 4, SITE-02 11, SITE-03 3 |
| Screening 207 | `GET /participants/GBM-NL-207/screening` | **5 met · 0 not met · 8 unknown**; evidence spans on INC-01/04, EXC-01/02/04 |
| Screening 201 | `GET /participants/GBM-NL-201/screening` | **13 met · 0 unknown**; all with evidence (complete case under **All**) |
| Confirm met rows | 13 × `POST …/screening/criteria/{cid}/confirm` | **0.66 s** for 13 rows; sign-off stays disabled until all 13 are confirmed |
| Sign-off / consent / enrol (API) | `POST …/screening/sign-off`, `/consent`, `/enrol` | **<0.1 s** each; eligible → consented → enrolled; audit events written |
| Query answer | `POST /queries/3/answer` (nurse) | **0.05 s**; open → answered |
| Query close | `POST /queries/3/close` (monitor) | **0.07 s**; answered → closed |
| SDV | `POST /participants/GBM-NL-002/ecrf/MGMTPROM/sdv` (monitor) | **0.08 s**; `sdvBy: monitor` |
| Timeline | `GET /participants/GBM-NL-002/timeline` | **20 events**, dated and linked to DOC-002-* |
| Protocol propose | `POST /studies/GBM-NL-2026-01/forms/propose` | **0.04 s**; **15 fields, 13 criteria**, provider `rules`, source sentences |
| Protocol approve | `POST /forms/2/approve` (PI) | **0.09 s**; v2 **Active** |
| Live extraction | worker log, `DOC-009-PATH` | **56.9 s**; **15 proposals, 9 abstained**; `qwen2.5:7b-instruct`, `extract_v4@1ef2060c673d` |
| Accept / correct / defer | `POST /extractions/{id}/decision` | **0.12 s / 0.46 s / 0.05 s**; eCRF value + audit rows |
| Audit verify | `GET /audit/verify` | **ok: true**, **176 events**, **0.12 s** |
| ODM export | `GET /studies/GBM-NL-2026-01/export/odm` | **0.10 s**, **11,075 bytes**, `ItemData` + `AuditRecord` |
| FHIR export / push | `GET/POST /participants/GBM-NL-002/export/fhir` | bundle **8 entries**; push **6.1 s**, **9 resources** written |
| UI labels | Playwright screenshots at 1440×900 | Login, dashboard, integrations, screening, queries, timeline, protocol, review, audit, export all render; labels in §6 match |
| Click/route budget | Playwright | Login **2.5 s**; screen route **<0.2 s**; screening data load **~2 s** (rules); review load **~2–3 s** |

**What was not verified by this agent (honest limits)**
- The spoken text was **measured with `say -r 140` (10:59)** but not voiced by the presenter in the rehearsal; the segment budget is that measurement plus the measured click/route budget. A human dress rehearsal in the presenter's voice is still required before Monday.
- The **second hospital is visible on the dashboard, in the site filter and on the screening patient**, but the Integrations card in this build shows **hospital 1 only** (the legacy single-source card). The run table shows two runs; the result line shows the last source (hospital 2). Do not claim the card lists both. (Follow-up: add a source column/card in the next build.)
- The dashboard **"Enrolled"** KPI counts patients on treatment at the site, not only trial-enrolled; after the sync it shows **18/24** and SITE-02 **11/8**. The script speaks of "participants" and the site comparison only before the sync; if asked, use Q10.
- The screening queue has **3 new referrals**, all with incomplete evidence; the complete 13/13 patient (201) is **active** (already on treatment), so the live sign-off is shown as "still in screening" and the complete checklist is shown under **All**. The eligible → consent → enrol transition is verified by the backend and widget tests, not clicked on stage.
- The **v1/v2 form version pills** both read "Active" in this build; the current version is v2 (the API and the detail panel agree). The script says v2 is current and v1 keeps captured values.

**Presenter card (print this)**
`0:00 open · 0:35 PI login · 1:00 dashboard → Noordhaven → All sites (8/24, 46 queue) · 2:00 Integrations → Sync (3 s; h1 3/7, h2 7/18; 25 docs, 25 runs) · 3:10 Screening → 207 (5 met/8 unknown) → confirm met (sign-off disabled; stays in screening) → All → 201 (13/13) · 5:20 Queries → q3 → tab B nurse answers · 6:40 002 → Timeline (20 events) · 7:20 Protocol → Analyse → Approve v2 · 8:25 009 → Review AI → accept histology · 002 → correct MGMT (fixture) · 009 → defer RANO · 10:05 Audit → Verify chain → Human → correction · 10:50 tab C monitor → close q3 → 002 MGMT → Mark SDV · 11:25 AI quality (100 % synthetic) · 11:40 ODM → FHIR 002 → Push · 12:30 is/is not + ask · 13:20 stop`

**Remaining for the human before Monday**
1. **One full dress rehearsal in the presenter's voice** with a listener; take two hostile questions from §9. If the read is slower than 140 wpm, cut the site-filter comparison, the timeline and the AI-quality scroll; never cut the sync result, the screening abstention, the correction, the audit verify or the "is not" slide.
2. **Record the 2–3 minute backup** of silent clicks on the frozen v4 build; play it once from local disk.
3. **Confirm the three-tab setup at 1440×900** on the presenting laptop (A PI, B nurse, C monitor), all signed in before the talk.
4. **Re-point this script at the freeze commit** on Sunday 20:00 (`git rev-parse --short HEAD` in §4 and §10).
5. **Confirm the v4 stack is the one running** (`make health STRICT=1`, web :8081, API :8001) and the v3 stack is untouched (:8080/:8000) for the fallback.

---

## 11. Fallback to the v3 checkpoint (read this before Monday 18:00)

**When to choose v3**
- v4 does not pass the **Sunday 18:00 stability gate** (cold start + full click path), **or**
- Monday pre-flight fails on :8081/:8001, or a v4 feature is missing/broken, **or**
- the v4 demo would need more than 15 minutes to set up on the presenting laptop.

**Do not mix the stacks.** If you fall back, present v3 only; do not show v4 screens, and do not copy v4 data into v3.

**The v3 checkpoint (do not modify)**
- Folder: `~/yammic-demo-v3`, a **separate frozen checkout** at tag **`demo-v3-checkpoint`** (`eb634e2`). It is not the `v4` branch.
- Ports: Postgres **:5433**, HAPI **:8090**, backend **:8000**, web **:8080**.
- Script: `~/yammic-demo-v3/deliverables/demo_script.md` — **v3.1**, the 10-minute run. Use that script, not this one.
- The product is branded **Yammic** in v3; the rename to Yamicc is v4 only. Do not apply the v4 name to the v3 screens.

**Exact steps the morning of Monday**
1. Decide once, at the pre-flight: **v3 only** for this session. Do not edit `~/yammic-v4` data or code. You may stop v4's **app processes** with v4's own port-scoped `make stop` (step 7) so v3 has Ollama to itself; do not reset containers or volumes.
2. Check v3 is healthy (read-only):
   ```bash
   curl -s http://127.0.0.1:8000/health
   curl -s http://127.0.0.1:8090/fhir/metadata | head -c 120
   open http://127.0.0.1:8080
   ```
   Expect `{"status":"ok"...}`, a FHIR CapabilityStatement, and the v3 login screen.
3. If v3 is down, start it **from its own folder**:
   ```bash
   cd ~/yammic-demo-v3
   make demo            # starts backend, one AI worker, web; v3 ports
   make health STRICT=1
   ```
   Do **not** run `make reset` in the v3 folder unless the data is known bad; the frozen volume is the checkpoint. If a reset is unavoidable, the synthetic data is reseeded from the checkout, but record that decision.
4. Stage the **v3** arrivals only if the pre-flight says the v3 sync is empty:
   ```bash
   cd ~/yammic-demo-v3
   python3 fhir-seed/load.py --set arrivals
   ```
5. Open `~/yammic-demo-v3/deliverables/demo_script.md` and follow **v3.1**: 8 participants, one hospital, 10 minutes, the same review loop, audit, export and monitor SDV. Skip the five v4 features; do not mention them as shown.
6. Tell the Board in one sentence at the start: **"We are running the frozen v3 checkpoint today; the v4 build did not pass our stability gate. The review loop, audit and exports are the same."** Do not hide the switch.
7. If the v4 AI worker is running, it shares Ollama with v3 and slows the queue. Before the v3 demo, stop **only** the v4 app processes with v4's own `make stop` (port-scoped; run it in `~/yammic-v4`). Do **not** use v3's `make stop` for this: the older v3 stop script also matches v4's worker. After that, run no v4 commands during the v3 demo.

**What the Board loses in v3:** screening, the second hospital, the data-quality queries, the timeline, protocol-to-form, and the multi-site dashboard. **What stays:** connected FHIR ingest, local AI extraction, accept/correct/defer, the hash-chained audit, ODM/FHIR export, and monitor SDV. Say that plainly.

---

## 12. Open items and risks

| # | Item | Owner | Effect on the demo |
|---|---|---|---|
| R1 | `make demo` starts **one** AI worker; `make health STRICT=1` fails if it is missing or if two run | DevOps / Engineer | Pre-flight step 4; if it dies on stage, no live proposals (recovery §6.9) |
| R2 | Arrivals are staged by `make stage-arrivals` on **both** hospitals, not by `make reset`/`make seed` | DevOps / Junior Engineer | Pre-flight step 2; without it the sync creates 0 participants |
| R3 | Ollama is a single local server; 25 documents serialise. The first 009 document is ready in ~1 min; the whole queue takes 15–25 min | Engineer | The v4 segments fill the time; review 009 and move on; `rules` is the fallback; never wait in silence |
| R4 | The Integrations card shows hospital 1 only; the run table has no source column | Engineer | The second hospital is shown on the dashboard, the site filter and the screening patient; do not overclaim the card (follow-up) |
| R5 | The dashboard "Enrolled" KPI counts patients on treatment, not only trial-enrolled; after sync it shows 18/24 and SITE-02 11/8 | PM / Engineer | Speak of "participants"; show the site comparison before the sync; Q10 |
| R6 | The screening queue has only incomplete referrals; the complete 13/13 patient is active and cannot be signed off in the UI | PM / Engineer | The script shows "still in screening" for 207 and the complete checklist under All; the state machine is tested but not clicked on stage |
| R7 | Both form version pills read "Active" | Engineer | Say v2 is current; v1 keeps captured values; cosmetic follow-up |
| R8 | Security High findings SEC-01/02/03/04 fixed in CEL-1785 (`f5b0386`); SEC-02 re-verified (`c60b2be`); Medium findings and a pen test remain | CTO / Security | Say "local demo"; do not claim "secure", "compliant" or "certified" |
| R9 | `Session.demoToday` is fixed at 2026-11-23; after Monday the UI date is stale | Engineer | Cosmetic; keep the clock for the demo |
| R10 | AI quality shows 100 % on the synthetic set; a Board member may read it as marketing | PM | The script pre-empts it (§6.12, Q3) |
| R11 | The 8 baseline participants are fixtures (`provider: fixture`); only synced documents are live. Easy to mislabel under pressure | PM | §1, §6.3, §6.9 and Q2b state the split; never call fixture output "live" |
| R12 | Residual audit risk: the DB, the HMAC key and the anchor file are on one machine | CTO / CEO | Q15 line: "someone with all three could still defeat it; separate service is roadmap"; no "compliant" or "certified" |
| R13 | v4 and v3 share Ollama; a v4 worker slows the v3 fallback | DevOps | Stop the v4 worker with v4's `make stop` before a v3 fallback demo |

---

## 13. Appendix — sources and labels

Access date for all web sources: 2026-11-21. Labels: [VERIFIED] primary source; [INFERRED] reasoned; [CLAIMED] single/non-stable source; [GK] general knowledge.

| ID | Source | Label |
|---|---|---|
| A1 | `deliverables/D2_yamicc.md` — verified Yamicc analysis (organisation, funding, platform status, maturity) | Internal research |
| A2 | `deliverables/d3_competitive_landscape.md` — vendor profiles and cross-cutting findings | Internal research |
| A3 | `deliverables/security_review_demo_v3.md` — audit, pseudonymisation, authz, containers | Internal review |
| A4 | `deliverables/backend_architecture.md` — backend architecture and data model | Internal |
| A5 | `deliverables/D7b_visual_direction.md` — visual direction v2 and screen specs | Internal |
| A6 | `deliverables/D7c_v4_screens.md` — v4 screen specs for screening, sites, queries/SDV, timeline, protocol-to-form | Internal design |
| A7 | `deliverables/protocol_GBM-NL-2026-01_synopsis.md` and `protocol_criteria.json` — the synthetic protocol and the 13 criteria | Source data |
| A8 | `backend/openapi.json` — v4 API contract (multi-site, screening, queries, timeline, forms) | Source |
| A9 | `06_ARCHITECTURE_STANDARDS_AI.md` — standards, stack, AI architecture and evaluation | Source pack |
| A10 | `07_REGULATORY_SECURITY.md` — MDR/AI Act, GDPR, security, validation | Source pack |
| A11 | `fhir-seed/README.md` — synthetic hospital inventory, both hospitals and the arrivals story | Source pack |
| A12 | `ops/RUNBOOK.md` — local stack, v3/v4 side by side, recovery, cold start | Source pack |
| A13 | yamicc.org/about-us, /what-we-do, /the-challenges (via D2) | [VERIFIED] |
| A14 | i~HD oncology eSource task force, Cambridge 2025 (via 03 §1) | [VERIFIED] |
| A15 | Rare-cancer "20 % / 650,000 per year" | [CLAIMED-C, unverified] — do not present as fact |

**Definition of done for this script:** every spoken claim carries a label or is framed as opinion; every step names the click, the line, what the audience should notice and a recovery; the "is not" slide is read without softening; the Q&A cites the research deliverables and never invents a number; the run was rehearsed against the real v4 build and the timings are recorded above; the v3 fallback is a complete, tested alternative.
