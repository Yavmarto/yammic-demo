# Monday demo — script, talking points and "what this is not"

Owner: PM (CEL-1755) · Version 1.0 · Prepared 2026-11-21
Demo date: **Monday 2026-11-23** · Slot: **10 minutes + Q&A**
Build: Flutter (web + macOS), synthetic data only · Code freeze Sun 2026-11-22 20:00 CET

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
| 1 | `cd app && ~/flutter/bin/flutter build web --release` | Build succeeds; serve `build/web` on `127.0.0.1` |
| 2 | Open the app in Chrome, full screen (`F11`), zoom 100% | Banner "Synthetic data — prototype, not for clinical use" visible |
| 3 | Network off (Wi-Fi off, no hotspot) | App loads and all screens work |
| 4 | Click path once, end to end | No red screen, no dead button |
| 5 | Restart the app | State is fresh; audit trail is empty |
| 6 | Backup recording (2 min, silent clicks) | Plays from local disk if the live build fails |
| 7 | Laptop: power, Do Not Disturb, screen saver off, notifications off | No interruption |
| 8 | Second machine or second browser tab on the start screen | 5-second recovery option |

**Rule:** never debug on stage. If a click fails, say "this is a prototype" and switch to the recording. Do not lose the narrative.

---

## 2. Run sheet (timeboxed)

| Time | Segment | Screen / route | Goal |
|---|---|---|---|
| 0:00–0:45 | Opening + honesty frame | Title slide | Set trust: synthetic, prototype |
| 0:45–1:45 | The problem | Slide 2 (problem) | EHR-to-EDC burden is real and unsolved |
| 1:45–2:15 | What we will show | Live app, dashboard | Give the map before the tour |
| 2:15–3:15 | Study dashboard | `/` (UI-001) | "What needs my attention today" |
| 3:15–4:30 | Participant workspace | `/participant/SYN-0001` (UI-002) | The nurse's home; open review task |
| 4:30–7:45 | **AI extraction review** | `/review` (UI-005) | Accept · Correct · Defer · provenance |
| 7:45–8:45 | Audit trail | `/audit` | Every action is attributable and append-only |
| 8:45–9:30 | What this is / is not | Slide 3 | Pre-empt the overclaim objection |
| 9:30–10:00 | Next steps + ask | Slide 4 | Gate 1/2 path; one clear decision |
| after | Q&A | Section 6 | Honest answers, no invented numbers |

**Pacing:** roughly 140 spoken words per minute. If you are 30 seconds late at 4:30, cut the dashboard tour to 30 seconds — never cut the Correct step or the audit trail.

---

## 3. Segment scripts

> Bracketed text is a stage direction. Quotes are spoken text. "Click" lines are the click path.
> `SYN-0001` is the participant id in the frozen Dart contract (`app/lib/models/models.dart`). If the data task lands a different id format (DEMO-2 brief says `GBM-NL-001`), say that id instead — see §8 open flags.

### 3.1 Opening — 0:00–0:45

**Slide:** Title — *"AI-assisted trial data capture — a synthetic working prototype"*.
Subtitle: *Synthetic data · prototype · not for clinical use.*

> "Thank you. In the last two days we built one workflow end to end. Everything you will see is invented: synthetic patients, synthetic documents, synthetic numbers. Nothing connects to a hospital, nothing calls a live model, and nothing here is for clinical use. [pause] Our question today is narrow: is this review loop the right first product?"

*Why this opener:* the banner and the honesty frame remove the two objections that kill demos — "is this real data?" and "are you claiming too much?".

### 3.2 The problem — 0:45–1:45

**Slide 2 — The problem** (text in §4.2).

> "Rare-cancer trials fail on data, not on ideas. One hospital may see only dozens of eligible patients, so a study must run across many sites. Yamicc states the same problem publicly: data is scattered across hospitals, formats differ, and combining it is technically and legally hard [VERIFIED — yamicc.org/the-challenges].
>
> The operational cost lands on research nurses and data managers. They read a pathology report and type the same values into an eCRF. That is the EHR-to-EDC gap, and it is not solved at scale: the i~HD oncology eSource task force concluded in 2025 that adoption is still limited by technical, regulatory and operational barriers, and that a common implementation framework was missing [VERIFIED — i~HD 2025, cited in 03 §1].
>
> One number I will not give you: our source pack says rare cancers are about 20% of cases and 650,000 patients a year in the EU/UK. That figure is still unverified [CLAIMED-C, unverified]. Treat it as a claim, not a fact."

**Talking points if asked to expand (do not volunteer):**
- Manual entry is not only slow; it is the main source of transcription errors and query loops between site, monitor and data manager [INFERRED — standard trial operations knowledge].
- Existing EHR-to-EDC products exist (OpenClinica, Castor, IgniteData Archer and others), so the gap is not "nobody thought of this" [VERIFIED — openclinica.com/ehr-to-edc-integration; others GK, verify].

### 3.3 What we will show — 1:45–2:15

**Switch to the live app at the dashboard.**

> "Three screens and one loop. The study dashboard, one participant's visit, and the review screen where AI proposals are accepted, corrected or rejected. Then the audit trail. Eight minutes of product, two minutes on what it is not."

### 3.4 Study dashboard — 2:15–3:15

**Click:** app opens on `/` — "one glioblastoma study, three sites" dashboard.

> "This screen answers one question for a coordinator: what needs my attention today? One synthetic glioblastoma study, three sites, enrolment against target, eCRF completeness, and the open review tasks. This is deliberately thin. We are not rebuilding a CTMS dashboard; mature products already do that, and we should integrate, not duplicate.
>
> The number that matters is here: [point] open AI extractions waiting for a human. That is the work this product removes from the nurse's evening."

**Expected on screen:** study title, sites with enrolled/target, completeness, milestone, alerts, task list with a participant link.
**If a chart is missing:** do not wait. Say "the table is the source of truth" and move on.

### 3.5 Participant workspace — 3:15–4:30

**Click:** the open task or the participant row → `/participant/SYN-0001`.

> "This is the site nurse's home. A pseudonymised id, status, the visit timeline, eCRF status and the open quality issues. Notice what is not here: no name, no date of birth, no hospital record number. In a real deployment, identifiers stay in the hospital node; this workspace works on the pseudonymised record.
>
> Baseline is complete. Week four is scheduled. And the eCRF card says 'awaiting review' — that is our entry point."

**Click:** "Review AI extractions" → `/review` (the app passes the participant id).

### 3.6 AI extraction review — 4:30–7:45 (centrepiece)

**Screen:** UI-005. Left: synthetic source document. Middle: proposal. Right: target eCRF field.

**(a) Layout — 45 s**

> "Three columns. On the left, the synthetic source document. The AI's evidence is highlighted, so you can check it in one glance. In the middle, the proposal: the value, the confidence, the proposed standard code, and the model and prompt version that produced it. On the right, the target eCRF field.
>
> The value on the right is not research data yet. It is a proposal. Nothing is saved into the dataset until a person acts. Four actions: accept, correct, reject, defer."

**(b) Accept — 40 s**

**Click:** Accept on histology.
**Example:** `histology = "Glioblastoma, IDH-wildtype"`, confidence 0.96, evidence span in the pathology report, proposed code ICD-O-3 9440/3.

> "Histology. Confidence 0.96. The highlighted sentence in the report is the evidence. One click, and it moves from proposal to verified data — with the reviewer, the time and the source recorded. If the sentence did not support the value, we would not accept it, whatever the confidence says."

**(c) Correct — 50 s**

**Click:** Correct on `mgmt_methylation`.
**Example:** AI proposal `methylated`, confidence 0.61; source text says `unmethylated`.

> "Now a harder one. The model proposes 'methylated' with confidence 0.61. The report says 'unmethylated'. The model was uncertain, and it was wrong. We correct the value and type the reason. That reason is part of the record, because the next reviewer needs to know why the proposal changed.
>
> This case is in the demo on purpose. A demo that only shows the model being right is not a demo of a safety mechanism."

**(d) Defer / reject — 40 s**

**Click:** Defer on `progression_date` (RANO).
**Example:** model abstains — "not stated" in the document, confidence 0.18.

> "Third case: the document does not state a RANO progression date. The model abstains. It does not invent a value. We defer it, and it becomes an open task for the next visit instead of a silent gap in the dataset.
>
> Reject exists for a different case: a proposal that is not in the source at all. Rejecting is not deleting — it is a recorded human decision."

**(e) Provenance — 20 s**

> "Every proposal carries the model id and the prompt version. When the model changes, the audit trail tells you which values came from which version. That is what makes an AI workflow reviewable in a regulated trial."

### 3.7 Audit trail — 7:45–8:45

**Click:** Audit in the navigation → `/audit`.

> "Four events, in order. The AI extraction, then accept, correct and defer. Who, what, when, before, after, and whether the source was AI or a human. The AI event carries the model and prompt version; the human events carry the reviewer.
>
> The list is append-only. There is no edit and no delete button, because the audit trail is the safety argument. A monitor can reconstruct exactly what happened to every value, and why."

**Point at:** one AI row and one human row, then the before/after pair on the correction.
**If the trail is empty:** the review actions did not persist — switch to the backup recording for 30 seconds, then continue on the next steps slide.

### 3.8 What this is / is not — 8:45–9:30

**Slide 3** (text in §4.3). Read the four "is not" lines; do not paraphrase them into softer language.

> "So, plainly. It is a synthetic prototype of one workflow, with pre-computed AI output and a human review loop. It is not connected to anything. It is not a medical device, and we make no MDR claim. It is not validated and not clinically deployable. It is not an accuracy benchmark — we have not measured accuracy, and I will not give you a number today."

### 3.9 Next steps — 9:30–10:00

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
One codebase for web and macOS, which keeps the demo stable on the presenting laptop. The Board set it as the product UI default. The trade-off is a smaller widget ecosystem than React; for this workflow that is acceptable.

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
| Audit trail empty after review | Say "state is in memory in this build", show the recording's audit segment, continue. |
| Projector or resolution breaks the layout | Switch to the macOS build, or use the recording at 1440×900. |
| Question you cannot answer | "We have not verified that; it goes on the open-questions list." Write it down. |

**Never:** install something, open a terminal, or debug in front of the audience.

---

## 8. Click-path verification against spec and build

Status at 2026-11-21 10:00 CET (script v1.0).

| Step | Route | Contract source | Status |
|---|---|---|---|
| Dashboard | `/` | `demo_tech_spec.md` routes; plan screen table (UI-001) | Route fixed; screen in build |
| Participant | `/participant/<id>` | `demo_tech_spec.md`; `main.dart` router | Route fixed; screen in build |
| AI review | `/review` (optional participant argument) | `demo_tech_spec.md`; `05` §3 UI-005; journey 1 in `05` §4 | Route fixed; **UI details pending D7 spec, screen pending DEMO-5** |
| Audit | `/audit` | `demo_tech_spec.md`; `04` FR-038 | Route fixed; **screen pending DEMO-5** |

**Checked now**
- Sequence matches journey 1 exactly (dashboard → participant → review → accept/correct/reject → audit).
- Actions match `05` §3 (Accept / Correct / Reject / Defer, evidence highlighted, confidence shown, provenance retained).
- Field names match the planned eCRF set (histology, MGMT promoter methylation, RANO progression date) and the `AiExtraction` model fields (`value`, `sourceText`, `spanStart`, `spanEnd`, `confidence`, `model`, `promptVersion`).
- Banner, no-network and pre-computed-AI rules match the plan's stability rules.

**Pending (owner + date)**
- D7 screen spec (Designer, due Sat 18:00): confirm layout order, colour/icon of "AI proposal — not verified", keyboard shortcuts; adjust the click wording, not the sequence.
- Final build (CTO + Engineer, before freeze Sun 20:00): run the script once; fix timings and any dead click. Tracked in **DEMO-4b**.
- Acceptance run (QA, DEMO-6): include this click path in the stability run and report deviations.

**Open data flags**
- Participant id format: `models.dart` says `SYN-0001`; the DEMO-2 brief says `GBM-NL-001`. Align before rehearsal; the script uses `SYN-0001`.
- `extractions.json` must contain the three scripted cases: high-confidence accept, plausible-but-wrong medium-confidence value (to correct), and an abstention ("not stated", to defer). If the fourth (reject) case exists, add 20 seconds in the review segment and cut dashboard detail.
- The placeholder dashboard still says "Synthetic Cardio Study"; the demo needs the GBM study before rehearsal.

---

## 9. Rehearsal plan

1. **Silent run** (20 min): click the full path three times with no talking. Fix any dead click or missing state. Reset the app between runs.
2. **Timed read** (15 min): read the spoken text at a normal pace with a timer. Target 9:30 to leave 30 seconds of slack.
3. **Dress rehearsal** (20 min): full run with one listener who asks two hostile questions from §6. Record it; check the banner is visible in every frame.
4. **Cut order if over time:** dashboard detail → audit polish → Q&A depth. Never cut the Correct step, the abstention, or the "is not" slide.

**Presenter card (one page, printed)**
`0:00 open · 0:45 problem · 1:45 map · 2:15 dashboard · 3:15 participant · 4:30 review (accept 5:15 · correct 5:55 · defer 6:45 · provenance 7:25) · 7:45 audit · 8:45 is/is not · 9:30 next steps · 10:00 stop`

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
