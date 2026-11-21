# Monday demo — script, talking points and "what this is not"

Owner: PM (CEL-1755/CEL-1759) · Version 1.1 · Rehearsed 2026-11-21
Demo date: **Monday 2026-11-23** · Slot: **10 minutes + Q&A**
Build: Flutter (web + macOS) + Zeta design system, synthetic data only · **frozen commit `caf122c`** · Code freeze Sun 2026-11-22 20:00 CET

---

## 0. At a glance

**One-sentence thesis**
> Clinical trial data entry is still manual copying from hospital records into eCRFs; we show one open, auditable loop where AI proposes, a person decides, and the system remembers why.

**What the audience should remember (3 things)**
1. The product is the **review loop**, not the model: evidence span → proposal → human accept/correct/reject → audit.
2. AI output is **never** research data until a human acts. Uncertainty is shown, and the model may abstain.
3. This is a **synthetic prototype**. No MDR claim, no hospital connection, no accuracy claim.

**Decision requested (one sentence at the end)**
> Keep MVP B (AI-assisted data capture) as the direction, and let us finish the Gate 1 evidence so Gate 2 can decide scope, roadmap and cost.

**Do not add slides.** Five slides total: title, problem, "what this is / is not", next steps, back cover. The product is the deck.

---

## 1. Pre-flight (T-30 minutes)

| # | Check | Pass condition |
|---|---|---|
| 0 | `git -C ~/yammic-demo rev-parse --short HEAD` | `caf122c` — the rehearsed build. Do not present from a different tree. |
| 1 | `cd app && ~/flutter/bin/flutter build web --release` | Build succeeds; serve `build/web` on `127.0.0.1` |
| 2 | Open the app in Chrome, full screen (`F11`), zoom 100% | Banner "Synthetic data — prototype, not for clinical use" visible |
| 3 | Network off (Wi-Fi off, no hotspot) | App loads and all screens work |
| 4 | Click path once, end to end (5 minutes) | No red screen, no dead button, no yellow overflow stripe |
| 5 | Restart the app | State is fresh; audit trail is empty |
| 6 | Backup recording (2 min, silent clicks) | Plays from local disk if the live build fails |
| 7 | Laptop: power, Do Not Disturb, screen saver off, notifications off | No interruption |
| 8 | Second machine or second browser tab on the start screen | 5-second recovery option |

**Rule:** never debug on stage. If a click fails, say "this is a prototype" and switch to the recording. Do not lose the narrative.

---

## 2. Run sheet (timeboxed)

| Time | Segment | Screen / route | Goal |
|---|---|---|---|
| 0:00–0:40 | Opening + honesty frame | Title slide | Set trust: synthetic, prototype |
| 0:40–1:45 | The problem | Slide 2 (problem) | EHR-to-EDC burden is real and unsolved |
| 1:45–2:05 | What we will show | Live app, dashboard | Give the map before the tour |
| 2:05–2:55 | Study dashboard | `/` (UI-001) | "What needs my attention today" |
| 2:55–3:55 | Participant workspace | `/participant/GBM-NL-002` (UI-002) | The nurse's home; open the review queue |
| 3:55–7:10 | **AI extraction review** | `/review` (UI-005) | Accept (≈4:45) · Correct (≈5:25) · Defer (≈6:20) · provenance (≈6:55) |
| 7:10–8:00 | Audit trail | `/audit` | Every action is attributable and append-only |
| 8:00–8:45 | What this is / is not | Slide 3 | Pre-empt the overclaim objection |
| 8:45–9:35 | Next steps + ask | Slide 4 | Gate 1/2 path; one clear decision |
| 9:35–10:00 | Stop talking | — | 25 s of deliberate slack; invite Q&A |
| after | Q&A | Section 6 | Honest answers, no invented numbers |

**Pacing:** about 140 spoken words per minute. The measured spoken text is 6:38; with click transitions the full run is about 8:00, leaving 2:00 of buffer. If you are 45 seconds late at 3:55, cut the dashboard detail to 30 seconds and skip the visit timeline — never cut the Correct step, the abstention, or the audit trail.

---

## 3. Segment scripts

> Bracketed text is a stage direction. Quotes are spoken text. "Click" lines are the click path.
> The demo participant is `GBM-NL-002`; ids are `GBM-NL-001..008` in the frozen data (`app/assets/data/participants.json`). All three scripted cases — accept, correct, defer — exist on `GBM-NL-002`.

### 3.1 Opening — 0:00–0:40

**Slide:** Title — *"AI-assisted trial data capture — a synthetic working prototype"*.
Subtitle: *Synthetic data · prototype · not for clinical use.*

> "Thank you. In the last two days we built one workflow end to end. Everything you will see is invented: synthetic patients, synthetic documents, synthetic numbers. Nothing connects to a hospital, nothing calls a live model, and nothing here is for clinical use. [pause] Our question today is narrow: is this review loop the right first product?"

*Why this opener:* the banner and the honesty frame remove the two objections that kill demos — "is this real data?" and "are you claiming too much?".

### 3.2 The problem — 0:40–1:45

**Slide 2 — The problem** (text in §4.2).

> "Rare-cancer trials fail on data, not on ideas. One hospital may see only dozens of eligible patients, so a study must run across many sites. Yamicc states the same problem publicly: data is scattered across hospitals, formats differ, and combining it is technically and legally hard [VERIFIED — yamicc.org/the-challenges].
>
> The operational cost lands on research nurses and data managers. They read a pathology report and type the same values into an eCRF. That is the EHR-to-EDC gap, and it is not solved at scale: the i~HD oncology eSource task force concluded in 2025 that adoption is still limited by technical, regulatory and operational barriers, and that a common implementation framework was missing [VERIFIED — i~HD 2025, cited in 03 §1].
>
> One number I will not give you: our source pack says rare cancers are about 20% of cases and 650,000 patients a year in the EU/UK. That figure is still unverified [CLAIMED-C, unverified]. Treat it as a claim, not a fact."

**Talking points if asked to expand (do not volunteer):**
- Manual entry is not only slow; it is the main source of transcription errors and query loops between site, monitor and data manager [INFERRED — standard trial operations knowledge].
- Existing EHR-to-EDC products exist (OpenClinica, Castor, IgniteData Archer and others), so the gap is not "nobody thought of this" [VERIFIED — openclinica.com/ehr-to-edc-integration; others GK, verify].

### 3.3 What we will show — 1:45–2:05

**Switch to the live app at the dashboard.**

> "Three working screens and the audit trail. The study dashboard, one participant's visit, the review screen where AI proposals are accepted, corrected or deferred, and then the audit trail. Eight minutes of product, two minutes on what it is not."

### 3.4 Study dashboard — 2:05–2:55

**Click:** app opens on `/` — the **Research dashboard** for one glioblastoma study across three sites.

> "This screen answers one question for a coordinator: what needs my attention today? One synthetic glioblastoma study, three sites, recruitment against target, eCRF completeness, alerts, and the task list. It is deliberately thin: we are not rebuilding a CTMS dashboard; mature products already do that, and we should integrate, not duplicate.
>
> The work queue is the **Tasks** card, further down. The MGMT alert points at the same problem as the task. That is the work this product removes from the nurse's evening."

**Expected on screen:** "Research dashboard"; one card "ReDiReCCT-GB Demo (synthetic) · GBM-NL-2026-01 · phase II" with "Recruitment 8/24" and "eCRF completeness 71%"; sections "Alerts" (warning: "GBM-NL-002: AI MGMT proposal contradicts the pathology report."), "Sites", "Tasks", "Milestones". Task row: "Correct MGMT promoter value · Data manager (demo) · due 2026-11-24 · GBM-NL-002".
**Click next:** scroll one notch to **Tasks**, click the **Correct MGMT promoter value** row → participant. (The task list is below the fold at 1440×900; the scroll is part of the script, not a failure.)
**If the task row is not visible:** open **Participants** in the rail and click `GBM-NL-002`. Do not debug on stage.

### 3.5 Participant workspace — 2:55–3:55

**Click:** the task row, or **Participants** in the navigation rail → `/participant/GBM-NL-002`.

> "This is the site nurse's home. A pseudonymised id, status, the study and site, age and sex, and the clinical summary. Notice what is not here: no name, no date of birth, no hospital record number. In a real deployment, identifiers stay in the hospital node; this workspace works on the pseudonymised record.
>
> The visit timeline and eCRF status are further down; we do not need them today. The header button is our entry point: **Open AI review**."

**Expected on screen:** "GBM-NL-002" and an "active" chip; "GBM-NL-2026-01 · SITE-02 · 64 y · M"; "Clinical summary"; "Visit timeline"; header button **Open AI review**.
**Label note:** the build shows **Review AI values** only when an eCRF is `awaiting_review`; `GBM-NL-002` is `in progress`, so the label is **Open AI review**. Do not say "awaiting review".
**Click next:** **Open AI review** in the header. The app passes `GBM-NL-002` to `/review` and filters the queue to that participant.

### 3.6 AI extraction review — 3:55–7:10 (centrepiece)

**Screen:** UI-005, live in the frozen build. Left: synthetic source document with the evidence span highlighted. Middle: proposed values. Right: target eCRF field.
**Build facts:** toolbar reads "AI extraction review", filtered to `GBM-NL-002`; the queue has **16 pending** proposals (15 fields plus a duplicate `EXT` extent-of-resection row). The first card is **Subject identifier** — select a card before you click an action.

**(a) Layout — 45 s**

> "Three columns. On the left, the synthetic source document, with the AI's evidence highlighted so you can check it in one glance. In the middle, the proposed values: the value, the confidence, and the proposed standard code. On the right, the target eCRF field.
>
> The value on the right is not research data yet. It is a proposal. Nothing is saved into the dataset until a person acts. Four actions: accept, correct, reject, defer."

**(b) Accept — 40 s**

**Click:** click the **Histology (central review)** card, then **Accept**.
**Example:** `Glioblastoma, IDH-wildtype`, confidence 0.97, evidence span in the pathology report, code `ICD-O-3 9440/3 — Glioblastoma, NOS`.

> "Histology. Confidence 0.97. The highlighted sentence in the pathology report is the evidence. One click moves it from proposal to verified data — with the reviewer, the time and the source recorded. If the sentence did not support the value, we would not accept it, whatever the confidence says."

**(c) Correct — 50 s**

**Click:** click the **MGMT promoter methylation** card, then **Correct**. Replace **Methylated** with **Unmethylated**. Click **Save correction**.
**Example:** AI proposal `Methylated`, confidence 0.72; source span: `MGMT promoter is unmethylated`.

> "Now a harder one. The model proposes 'methylated' with confidence 0.72. The report says 'unmethylated'. The model was uncertain, and it was wrong. We replace the value and save. The record keeps the original proposal, the corrected value, the reviewer and the time, so the next reviewer can see exactly what changed.
>
> This case is in the demo on purpose. A demo that only shows the model being right is not a demo of a safety mechanism."

**Do not claim a reason field on Correct.** The build records a before/after pair plus the reviewer; free-text reason capture is on the Reject path only. In the current build **Cancel** wraps below **Save correction**; both are visible.

**(d) Defer / reject — 40 s**

**Click:** click the **Date of progression (RANO)** card, then **Defer**.
**Example:** model abstains — "Not stated", confidence 0.00; source: "RANO assessment is not available for this timepoint." Accept is disabled.

> "Third case: the MRI says the RANO assessment is not available. The model abstains: value 'Not stated', confidence 0.00, and Accept is disabled. It does not invent a value. We defer it, and it becomes an open task for the next visit instead of a silent gap in the dataset.
>
> Reject exists for a different case: a proposal that is not in the source at all. It asks for a reason, and it is recorded, not deleted."

**(e) Provenance — 20 s**

> "Every proposal carries the model id and the prompt version. When the model changes, the audit trail tells you which values came from which version. That is what makes an AI workflow reviewable in a regulated trial."

The target pane shows `Model demo-extractor v0.1 · prompt prompt-2026-11-21`; the MGMT code is a LOINC placeholder marked unverified.

### 3.7 Audit trail — 7:10–8:00

**Click:** **View audit trail** in the target pane (or **Audit** in the navigation rail) → `/audit`.

> "The queue load wrote one AI extraction event for every proposed value: forty-six events. Our three human decisions are on top, newest first: defer, correct, accept.
>
> Click **Human**. Three events. Who, what, when, before, after, and whether the source was AI or a human. The AI events carry the model and prompt version; the human events carry the reviewer.
>
> Click the correction. Before 'methylated', after 'unmethylated', with the reviewer and time. The list is append-only: no edit and no delete. A monitor can reconstruct exactly what happened to every value, and why."

**Point at:** the `Human` filter (count drops to "3 events"), then the **correct** row and its detail: `Methylated → Unmethylated`, actor `SYN-JD`, source `Human · verified`, model `demo-extractor v0.1`, prompt `prompt-2026-11-21`.
**If the human events are missing:** the review actions did not persist — switch to the backup recording for 30 seconds, then continue on the next steps slide. The 46 AI rows alone are not evidence of review.

### 3.8 What this is / is not — 8:00–8:45

**Slide 3** (text in §4.3). Read the five "is not" lines; do not paraphrase them into softer language.

> "So, plainly. It is a synthetic prototype of one workflow, with pre-computed AI output and a human review loop. It is not connected to anything. It is not a medical device, and we make no MDR claim. It is not validated and not clinically deployable. It is not an accuracy benchmark — we have not measured accuracy, and I will not give you a number today."

### 3.9 Next steps — 8:45–9:35

**Slide 4** (text in §4.4).

> "Two gates and two roadmap phases. Gate 1 is the evidence: a verified Yamicc analysis and a landscape and gap analysis. That research is running now. Gate 2 is the decision: MVP scope, roadmap and cost. This demo does not replace Gate 2; it gives you something concrete to judge.
>
> Roadmap phase 1 is the technical proof of concept: architecture, synthetic FHIR, one end-to-end flow, automated tests. Phase 2 is the functional MVP: role workspaces, an external EDC integration, validation, audit, and a measured AI workflow.
>
> The decision we ask for is not 'approve the product'. It is: keep this as the MVP B direction, and let us finish the Gate 1 evidence."

---

## 4. Slide text (copy-paste)

### 4.1 Slide 1 — Title

> **AI-assisted trial data capture**
> A synthetic working prototype
>
> Synthetic data · prototype · not for clinical use
>
> *[Project name] · 23 November 2026*

### 4.2 Slide 2 — The problem

> **The data is in the hospital. The eCRF is somewhere else.**
>
> - Rare-cancer trials need many sites; each site sees few eligible patients. Data is scattered, formats differ, combining is hard. *(Yamicc, public problem statement — VERIFIED)*
> - A nurse reads the record, then types the same values into the eCRF. That is the EHR-to-EDC gap.
> - Adoption is still limited by technical, regulatory and operational barriers, with no common implementation framework. *(i~HD oncology eSource task force, 2025 — VERIFIED)*
>
> **The gap is not "no software". The gap is production-grade, evidence-linked, human-verified capture.**

### 4.3 Slide 3 — What this demo is / is not

> **What this is**
> - A synthetic-data Flutter prototype of one workflow: AI-proposed eCRF values, human review, append-only audit.
> - Pre-computed AI output: evidence spans, confidence, abstention, model and prompt version.
> - A test of the *review mechanism*, not of a model.
>
> **What this is not**
> - Not connected to an EHR, a backend, the internet or a live AI model.
> - Not a medical device. No MDR claim. No clinical decision support.
> - Not validated. Not clinically deployable. Not production software.
> - Not an accuracy benchmark. No accuracy number exists yet.
> - Not a Gate 2 decision, and not a build-budget commitment.

### 4.4 Slide 4 — Next steps

> **Two gates before build spend**
> - **Gate 1 — evidence:** verified Yamicc analysis, landscape, capability gap. *Research in progress.*
> - **Gate 2 — decision:** MVP scope, roadmap, cost ranges.
>
> **Roadmap**
> - **Phase 1 — technical PoC:** architecture, synthetic FHIR, one end-to-end flow, automated tests. *Exit: demo on synthetic data.*
> - **Phase 2 — functional MVP:** role workspaces, external EDC integration, validation, audit, measured AI workflow. *Exit: internal acceptance tests pass.*
>
> **Decision requested:** keep MVP B as the direction; approve finishing Gate 1. No build spend before Gate 2.

---

## 5. Claims we may make and may not make

### 5.1 Safe to say (with the label)

| Claim | Label / source |
|---|---|
| Yamicc is an independent Dutch non-profit (ANBI, founded 2024) that coordinates rare-cancer research with IT and AI. | [VERIFIED] yamicc.org/about-us, yamicc.org |
| Yamicc publicly describes a "Trial Execution Platform" with AI automation of repetitive work, automated data collection, FAIR data and "open standards" — the standards are not named on the site. | [VERIFIED] yamicc.org/what-we-do, /the-challenges |
| The March 2026 Mendix demo showed case management (MxBlue/SUPERP), protocol AI (Cori Clinical), eCRF (ORTEC LogiqSuite) and a Datahub against a **mock-up EHR**; interoperability was not demonstrated. | [VERIFIED] partner LinkedIn posts, 02 §3b |
| The stack is partner-dependent, and a Mendix base is likely (Mendix event, Mendix-partner integrator, Mendix co-founder as chair). | [INFERRED] 02 §3b — say "likely", not "is" |
| EHR-to-EDC adoption is still limited by technical, regulatory and operational barriers; a unified framework was missing. | [VERIFIED] i~HD oncology eSource task force, Cambridge 2025, 03 §1 |
| OpenClinica offers EHR-to-EDC via FHIR/HL7 with Epic/Cerner support, live since 2021, and claims 450+ sites. | [VERIFIED] openclinica.com/ehr-to-edc-integration (vendor claim) |
| Castor is a Dutch EDC with a strong footprint in Dutch academic hospitals. | [GK] — say "widely used", do not give a count |
| Data capture and admin automation for research generally falls outside MDR; matching and treatment recommendation may be a medical device under Rule 11. | [INFERRED] 07 §3, MDCG 2019-11 |

### 5.2 Not allowed in the room

| Do not say | Why |
|---|---|
| Any AI accuracy figure ("95% accurate", "saves 70% of time") | Not measured. FR-059 evaluation is future work. |
| "Yamicc cannot do this" / "Yamicc is only a mock-up" | Overclaim. Say what the public demo showed, nothing more. |
| "650,000 rare-cancer patients a year" as fact | [CLAIMED-C, unverified]; verify against RARECARE first. |
| "MDR compliant", "MDR exempt", "GDPR compliant", "HIPAA compliant" | No legal or regulatory sign-off exists. |
| "Clinically validated", "production-ready", "hospital-ready" | 08 §3: never claim a prototype is clinically deployable. |
| "Open source" as a settled property | License not chosen; NFR-09 is a target only. |
| "This replaces your EDC" | The design integrates external EDCs (FR-036), it does not replace them. |

---

## 6. Likely questions and honest answers

**Q1. Is this real patient data?**
No. Every patient, document and number is synthetic, and the data is bundled JSON inside the app. The banner is on every screen, by rule. There is no network connection during the demo.

**Q2. Is the AI live?**
No. The output is pre-computed, versioned JSON with evidence spans. It uses the same fields a live model would return — value, span, confidence, code, model id, prompt version. We do this for stability, not because the model is unavailable.

**Q3. How accurate is the extraction?**
We do not know yet, and I will not guess. This demo shows the review mechanism, not model quality. The evaluation plan (FR-059) measures precision and recall per field, abstention rate, and reviewer burden — on synthetic data first, then pilot data under approval.

**Q4. Is this a medical device?**
We make no MDR claim. Research data capture and admin automation generally fall outside MDR. Anything that recommends treatment or matches a patient to a drug needs a classification decision before we build it — that is explicitly deferred.

**Q5. What happens when the AI is wrong?**
That is the design. The evidence span lets a reviewer check the source in one glance; confidence is visible; the model can abstain; and no value becomes research data without a human accept or correct. The demo includes a wrong value and an abstention on purpose.

**Q6. How is this different from Yamicc?**
Carefully: they have partners, a clinical anchor and a public demo; we have a synthetic prototype. On the public record, their Datahub was shown with a mock-up EHR, so interoperability is not proven [VERIFIED — partner posts]. Our bet is an open, standards-first, evidence-linked review layer that integrates existing EDCs instead of locking the stack to one low-code vendor [INFERRED].

**Q7. Isn't this just Castor or OpenClinica?**
Partly, and that is fine — we should integrate them, not rebuild them. The specific gap we target is Dutch-language, multi-source extraction with evidence spans, provenance and a review UI that fits site workflow. Whether that gap is big enough is exactly what Gate 1 and Gate 2 must test.

**Q8. Can it connect to Epic or HiX?**
Not in this demo — there is no network by design. The architecture targets FHIR R4/mCODE with Dutch EHR adapters, and a connector conformance test is a Phase 2–3 deliverable. We have not connected to a real hospital, and we will not claim otherwise.

**Q9. Where does the data live, and what about GDPR?**
The architecture assumes a hospital data node, with only pseudonymised research data leaving where consent and agreements allow, and EU hosting. A DPIA and the controller/processor model are Phase 1–2 work with legal review. Nothing is solved yet.

**Q10. What does a pilot cost, and when?**
I will not invent a number. Phase 3 is a controlled single-hospital pilot; cost ranges come with D14 at Gate 2. The honest answer today is: the demo is cheap, the pilot is not, and Gate 2 decides whether we fund it.

**Q11. Does the AI write back to the EHR?**
No. Hard rule: AI never writes to the EHR, and it never makes a treatment decision. Values go to the research dataset only after human review.

**Q12. Why Flutter?**
One codebase for web and macOS, which keeps the demo stable on the presenting laptop. The Board set it as the product UI default. The frozen build uses Flutter with the Zeta design system for the visual layer. The trade-off is a smaller widget ecosystem than React; for this workflow that is acceptable.

**Q13. What is still missing before a hospital could use it?**
Authentication and roles, real connectors, terminology services, validation evidence, a QMS, security assessment and a DPIA. That is Phase 2–4, and it is the larger part of the work.

**Q14. Why show a wrong value on purpose?**
Because a safety mechanism that is only shown working on easy cases is marketing. The correction and the abstention are the two cases that matter for a regulated buyer.

**Answering rule:** if you do not know, say "we have not measured that" or "that is Gate 1 / Gate 2 work". Never fill a gap with a number.

---

## 7. Failure plan

| Failure | Response |
|---|---|
| App does not start / "Data load failed" | Restart once. If it repeats, open the backup recording and present from it. |
| A click does nothing | Do not click twice. Say "prototype", go to the next screen from the navigation rail, keep the story. |
| Review screen shows no proposals | Go to the dashboard, reopen the participant, then review. If still empty, use the recording for the review segment. |
| Audit shows 46 AI events but no human events | The review actions did not persist. Say "state is in memory in this build", show the recording's audit segment, continue. |
| Projector or resolution breaks the layout | Switch to the macOS build, or use the recording at 1440×900. |
| Question you cannot answer | "We have not verified that; it goes on the open-questions list." Write it down. |

**Never:** install something, open a terminal, or debug in front of the audience.

---

## 8. Click-path verification against the frozen build

Rehearsal 2026-11-21 10:30 CET. Frozen build `caf122c` on `dev` (DEMO-1/5 + DEMO-2 data + DEMO-7 Zeta, plus two hotfixes found in this rehearsal: `a5083e2` ZetaProvider startup contrast, `caf122c` correction-button Wrap). Working tree clean except other teams' untracked `deliverables/` drafts.

**Checks run on `caf122c`**
- `~/flutter/bin/flutter analyze` → "No issues found".
- `~/flutter/bin/flutter test` → 8 of 8 passed (data contract, review/audit, smoke).
- `~/flutter/bin/flutter build web --release` → success.
- `~/flutter/bin/flutter build macos` → success; the macOS app launches (QA CEL-1757).
- Scripted click path through the real widget tree (app root with `ZetaProvider`, 1440×900): all taps resolved; no dead click. Audit: 49 events (46 AI extraction + 3 human), `Human` filter = 3 events, correction detail shows `Methylated → Unmethylated`, actor `SYN-JD`, source `Human · verified`, model `demo-extractor v0.1`, prompt `prompt-2026-11-21`.
- Banner `Synthetic data — prototype, not for clinical use` rendered on `/`, `/participant/GBM-NL-002`, `/review` and `/audit` (one `Shell`, hard rule).

| Step | Route | Exact on-screen label | Result |
|---|---|---|---|
| Dashboard | `/` | "Research dashboard"; "ReDiReCCT-GB Demo (synthetic) · GBM-NL-2026-01 · phase II" | Works |
| Tasks row | `/` | "Correct MGMT promoter value · Data manager (demo) · due 2026-11-24 · GBM-NL-002" | Works; row is below the fold — scroll one notch |
| Participant | `/participant/GBM-NL-002` | "GBM-NL-002", "active", "Clinical summary", header **Open AI review** | Works; eCRF/quality sections are below the fold |
| Review | `/review` (filtered) | "AI extraction review", "16 pending", `SOURCE · pathology report · DOC-002-PATH` | Works |
| Accept | review | **Histology (central review)** card + **Accept** → "Verified · Accepted" | Works |
| Correct | review | **MGMT promoter methylation** + **Correct** → **Save correction** → "Verified · Corrected" | Works; overflow found on `d807681`, fixed in `caf122c`; Cancel wraps below Save |
| Defer | review | **Date of progression (RANO)** + **Defer** → "Deferred"; Accept disabled | Works |
| Audit | `/audit` | **Human** filter → "3 events"; correction detail with before/after | Works |

**Deviations found and fixed in the script (v1.1)**
- Participant id `SYN-0001` → `GBM-NL-002`. The accept, correct and defer cases all exist on `GBM-NL-002`; `GBM-NL-001` has no wrong-MGMT case.
- Entry is the second task row, **Correct MGMT promoter value**, not the first ("Review AI extractions for TMZ cycle 5" → `GBM-NL-001`).
- Header button is **Open AI review** (002's eCRF is `in progress`, not `awaiting_review`).
- Confidences are 0.97 (accept), 0.72 (correct), 0.00 (abstain); code is `ICD-O-3 9440/3 — Glioblastoma, NOS`.
- Correct has no reason field; the build records a before/after pair plus the reviewer.
- Correction-mode controls overflowed by 53 px on `d807681`; fixed in `caf122c` (`Row` → `Wrap`) and re-verified clean at 1440×900.
- The audit is 49 events (46 AI + 3 human), not four. Click **Human** to show the three decisions, newest first: defer, correct, accept.
- Dashboard Tasks is below the fold; the participant eCRF/quality cards are below the fold. The script now scrolls once and does not claim those cards are visible.
- Run sheet rebalanced: the problem needs 1:05 and next steps 0:50; total spoken text is 6:38.

**Open risks**
- Two hotfixes landed during the rehearsal (`a5083e2`, `caf122c`). The app is feature-frozen, but `dev` is not commit-frozen until Sunday 20:00. If anything else lands after `caf122c`, repeat this checklist; the Zeta work changed colours only, not labels or routes.
- The timed read used TTS at 140 wpm, not the presenter's voice. Do one human read before Monday (§9).
- Data note: `GBM-NL-002` has two `EXTRES` proposals (conf 0.38 and 0.93). The script does not touch them; do not accept both on stage.

---

## 9. Rehearsal log and plan

**Run 1 — scripted click run, 2026-11-21, frozen `caf122c`:** one full pass through dashboard → participant → review (accept, correct, defer) → audit. Every tap resolved; banner present on all four screens; audit assertions passed. One layout exception in correction mode on `d807681` was fixed in `caf122c` and re-verified clean at 1440×900. No dead click.

**Run 2 — timed read, 2026-11-21:** the exact spoken text was rendered at 140 words per minute with macOS `say -r 140` and measured: **6:38**. Click budget: 8 mouse actions in the review segment plus ~10 typed characters (≈23 s at 2 s/action), 7 s in audit, 9 s for dashboard/participant navigation, 6 s for slide changes = **0:48**. Planned full run: **7:30–8:10 of 10:00**, including stage pauses.

| Segment | Spoken (measured) | Clicks | Budget |
|---|---|---|---|
| 3.1 Opening | 0:22 | — | 0:40 |
| 3.2 The problem | 1:02 | — | 1:05 |
| 3.3 What we will show | 0:16 | 0:04 | 0:20 |
| 3.4 Study dashboard | 0:35 | 0:04 | 0:39 |
| 3.5 Participant | 0:31 | 0:04 | 0:35 |
| 3.6 Review | 2:02 | 0:23 | 2:25 |
| 3.7 Audit | 0:40 | 0:07 | 0:47 |
| 3.8 Is / is not | 0:24 | 0:02 | 0:26 |
| 3.9 Next steps | 0:48 | 0:02 | 0:50 |
| **Total** | **6:38** | **0:48** | **7:47** |

**Remaining for a human (10 minutes)**
1. One full dress rehearsal in the presenter's own voice with a listener; take two hostile questions from §6.
2. Confirm `Save correction` and `Cancel` are both visible in correction mode (`Cancel` wraps below `Save`).
3. Record the 2-minute backup (silent clicks) on the frozen build, then play it once from local disk.
4. If the human read is slower than 140 wpm, cut in this order: audit provenance detail → dashboard alert detail → participant summary detail. Never cut the Correct step, the abstention, or the "is not" slide.

**Presenter card (one page, printed)**
`0:00 open · 0:40 problem · 1:45 map · 2:05 dashboard (scroll to Tasks) · 2:55 participant · 3:55 review (accept 4:45 · correct 5:25 · defer 6:20 · provenance 6:55) · 7:10 audit (Human filter, correction row) · 8:00 is/is not · 8:45 next steps · 9:35 stop talking · 10:00 end`

---

## 10. Appendix — sources and labels

Access date for all web sources: 2026-11-21.

| ID | Source | Label |
|---|---|---|
| A1 | https://yamicc.org/about-us/ | [VERIFIED] |
| A2 | https://yamicc.org/what-we-do/ | [VERIFIED] |
| A3 | https://yamicc.org/the-challenges/ | [VERIFIED] |
| A4 | Partner LinkedIn posts on the 26 March 2026 Mendix Zorg Connect demo (links in 02 §3b) | [VERIFIED] |
| A5 | https://openclinica.com/ehr-to-edc-integration | [VERIFIED — vendor claim] |
| A6 | i~HD oncology eSource task force, Cambridge 2025 (03 §1) | [VERIFIED] |
| A7 | 02 §3b — component table, Datahub mock-up EHR | [VERIFIED]; Mendix base [INFERRED] |
| A8 | 07 §3 — MDR / MDCG 2019-11 Rule 11 analysis | [INFERRED] |
| A9 | 08 §3 — roadmap phases and exit criteria | Source pack |
| A10 | Rare-cancer "20% / 650,000 per year" | [CLAIMED-C, unverified] — do not present as fact |

**Definition of done for this script:** every spoken claim carries a label or is framed as opinion; the click path matches journey 1 and the frozen routes; the "is not" slide is read without softening; the Q&A avoids invented numbers. Final build cross-check is DEMO-4b.
