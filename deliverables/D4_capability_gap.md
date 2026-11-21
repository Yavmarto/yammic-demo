# D4 — Capability Gap Analysis: Yamicc Capabilities × Existing Solutions

**Task:** T07 ([CEL-1734](/CEL/issues/CEL-1734)) — Capability gap analysis
**Owners in the spec:** Research + Product · **Accountable agent:** Researcher
**Output:** D4 · **Prepared:** 21 November 2026 · **Revision:** v2 (QA fixes F1–F4, M1–M8) · **Review:** T21 ([CEL-1792](/CEL/issues/CEL-1792))
**Status:** Gate 1 draft, revision 2. QA re-review pending. §6 is an input to T17 (D13); Product owns the final MVP scoring.

**Inputs:** `D2_yamicc.md` §4 (maturity, T02), `d3_competitive_landscape.md` (commercial, T04), `D3_s2_open_source_assessments.md` + `license_register.md` (open source, T05), `D3_appendix_data_sources.md` (data sources, T06), `03` (landscape), `04` (requirements), `08` §2 (MVP options).
**Evidence access date:** 2026-11-21 for every source cited here. D4 adds no new web research; it synthesises the QA-tracked inputs above and inherits their evidence status. Where an input is still under review, that is stated.

---

## 0. Recommendation first

**The gap is not "Yamicc is weak, so copy Yamicc". Most of Yamicc's capability list is already supplied by mature products that we should integrate. The defensible gap is narrower: a production-grade, Dutch-language, evidence-linked document→eCRF path that writes into the EDC a hospital already owns, inside the hospital trust boundary, at an academic price.**

1. **Yamicc sets no capability bar to beat.** Its 13 public capabilities contain **zero** above "Demonstrated — demo only" ([VERIFIED for the ceiling only; the four Demonstrated ratings are [CLAIMED] and rest on D2-S14, a search-index capture of LinkedIn posts — see §1 limits and X1]). But absence at Yamicc does not prove a market gap: 3 of the 13 capabilities are **closed** by established commercial or open-source products, and 2 are outside MVP scope. Do not build those.
2. **No capability is cleanly "open" in the software sense.** After the four tests, **7 are contested**: products exist but fail at least one Dutch-fit, governance or adoption test. One (C10) is open only as a **non-software data partnership**; 2 are out of scope. The build budget is set by the cross-cutting gaps in §4, not by a count of "open" rows.
3. **The build surface is the cross-cutting layer no single vendor owns** (§4): Dutch clinical-document extraction with evidence spans and abstention (G1), multi-EDC write-back with provenance (G2), hospital-side processing plus thin multi-site orchestration (G3), and validation evidence for AI-assisted capture (G4). **Confidence: medium-high.**
4. **Research recommendation: MVP B plus thin A elements** (08 §2). B closes G1/G2 and the Datahub gap; thin A closes C01/C11 orchestration. **In our assessment, pending T17, MVP A alone is not defensible** — it is a workflow shell over EDCs. **Research view: MVP C is a Phase-2 capability**, not the wedge. **Research view: MVP D is too broad** for the team and pulls MDR-sensitive matching into Phase 1. Product must confirm this scoring in T17; D4 does not decide it. Note that `04` tags FR-050, FR-052 and FR-059 as A, so A is not wholly extraction-free. **Confidence: medium-high.**
5. **Score us on measured extraction quality, not feature parity.** The differentiator is Dutch-text accuracy, reviewer time saved, correction/override rate (FR-052, FR-058) and abstention rate per field and per site (FR-059). If we cannot measure those against Castor Catalyst, we have no claim. **Confidence: high** that measurement is the decision gate.

**What would change this recommendation**

| Change | Effect | Owner |
|---|---|---|
| Castor Catalyst publishes credible Dutch-language extraction quality, or Castor exposes a documented write-API for third-party extraction | Flip from "compete" to "integrate/co-sell" for G1 | Research |
| ORTEC LogiqSuite or Castor confirms authenticated eCRF write access | G2 shrinks to an adapter; effort falls materially | CTO |
| IgniteData or OpenClinica announces an EU-hosted HiX/ChipSoft connector | The Dutch-connectivity gap narrows; emphasis moves to review, audit and price | Research |
| Yamicc's 2026 POC names a hospital, a standard and live data | C01/C04/C11 ratings rise; the "no production competitor" premise weakens (that premise already rests only on [CLAIMED] D2-S14 evidence) | Research |
| A pilot site signs a DPA for a US/EU vendor's cloud processing | C04/G3 lose their "hospital-side" differentiator | Product / CTO |

---

## 1. Scope, method and limits

**Question this document answers:** for each capability Yamicc publicly claims, is a suitable solution already available to a Dutch academic rare-cancer consortium, and if not, what exactly must we build?

**Method**
1. Start from the 13-capability inventory and maturity ratings in D2 §4 (the only QA-tracked maturity source).
2. Match each capability to the best available commercial product (`D3-1`), open-source component (`D3-2`) and data source (`D3-3`).
3. Apply a four-part fit test (below) and assign one gap class.
4. Promote capabilities that no single supplier owns into cross-cutting gaps (§4).
5. Map the result to MVP options and requirement IDs, then state what we build, integrate, reuse, defer or ignore.

**Fit test used for every row.** A row is *closed* only if all four hold; otherwise it is contested or open. Out-of-scope rows skip the test because the need is not in the MVP.

| Test | Question | Failure means |
|---|---|---|
| **Need** | Does the capability exist as a product or maintained component? | No product → open |
| **Dutch fit** | Does it work for Dutch EHRs and Dutch clinical text? | US-only evidence → contested |
| **Governance fit** | Can it run with hospital-side data control, EU residency and audit-grade review? | Cloud-only, raw-data-export model → contested |
| **Adoption fit** | Can a small academic consortium buy or reuse it without lock-in or a large licence? | Enterprise-only, non-OSI, mandatory suite → contested |

**Gap classes**

| Class | Definition | Default action |
|---|---|---|
| **Closed** | A suitable, maintained solution passes all four tests; no realistic build differentiation | Integrate or reuse; do not build |
| **Contested** | Solutions exist but fail ≥1 fit test for our use case | Build only the narrow missing layer |
| **Open — software** | No suitable solution and the missing layer is code we would own | Build or partner; this is the differentiation budget |
| **Open — non-software** | No suitable solution, but the missing input is data access, a partnership or a process, not code | Partner or defer; do not add to the build budget |
| **Out of scope** | No MVP need, or MDR/regulatory burden not justified before Gate 2 | Defer or ignore |

**Evidence aliases used in this document.** `D2` = `deliverables/D2_yamicc.md` (T02). `D3-1` = `deliverables/d3_competitive_landscape.md` (commercial vendors, T04). `D3-2` = `deliverables/D3_s2_open_source_assessments.md` (open source, T05). `D3-3` = `deliverables/D3_appendix_data_sources.md` (data sources, T06). `04` = `04_REQUIREMENTS_SPEC.md`. `08` = `08_STRATEGY_MVP_ROADMAP.md`. D2 source IDs are prefixed `D2-Sn` to avoid colliding with the §10 source table.

**Limits — read before using this document**
- No hands-on product test, no vendor contact, no price discovery. Gate 0 forbids outreach. All vendor capability statements are public claims, not test results.
- Yamicc's four "Demonstrated" ratings (C01–C04) rest partly on **D2-S14** (LinkedIn posts via search index, [CLAIMED]). If D2-S14 fails, those four fall to Announced and the gap conclusion does **not** change; the baseline is "no production capability" either way (D2 §4.2).
- Dutch hospital EHR facts (which sites run Epic vs HiX, which expose FHIR R4) are not established. C04 and G5 therefore carry medium-high confidence on the gap's existence and medium confidence on effort.
- D2 and D3 were under T21 review during drafting. Findings in this document inherit their final labels. This revision found no drift against the current D2 §4 text (M8); X6 stays open until the D2/D3 T21 re-checks close. "Epic research module" has one weak mention in `D3-1` and is treated as [INFERRED], not a verified product.

---

## 2. The capability inventory (from D2 §4)

Thirteen capabilities, each with Yamicc's public maturity on 21 Nov 2026. IDs C01–C13 are introduced here for traceability only; they are not requirement IDs.

| ID | Capability | Yamicc maturity | Evidence basis |
|---|---|---|---|
| C01 | Clinical case management / orchestration | Demonstrated — demo only [CLAIMED: rests on D2-S14] | D2 §4.2, D2-S6/D2-S13/D2-S14 |
| C02 | Protocol-authoring AI | Demonstrated — demo only (integration) [CLAIMED: rests on D2-S14] | D2 §4.2, D2-S14; vendor depth = T03 |
| C03 | eCRF / data capture | Demonstrated — demo only (integration); partner product is Production [CLAIMED: demo half rests on D2-S14] | D2 §4.2–4.3 |
| C04 | Datahub / EHR access | Demonstrated — demo only (mock data) [CLAIMED: rests on D2-S10/D2-S14] | D2 §4.2, D2-S10/D2-S14 |
| C05 | FAIR data principles | Announced | D2 §4.2, D2-S1/D2-S4 |
| C06 | Interoperability via open standards | Announced — none named | D2 §2 item 3, D2-S1–S5/D2-S10/D2-S11 |
| C07 | AI diagnostics / treatment recommendations | Roadmap | D2 §4.2, D2-S11 |
| C08 | Digital thread (cross-database linkage) | Roadmap | D2 §4.2, D2-S11 |
| C09 | Imaging / DICOM / radiology | Unconfirmed — not in stated scope | D2 §2 item 4 |
| C10 | Multi-omics collection and linkage | Announced (collection) / Roadmap (analysis) | D2 §4.2, D2-S2 |
| C11 | Multi-hospital live use | Announced — no named site | D2 §4.2, D2-S3 |
| C12 | Hosting and deployment model | Unconfirmed — not publicly committed | D2 §2 item 5, D2-S10/D2-S11 |
| C13 | GxP / validated platform | Roadmap | D2 §4.2, D2-S7 |

---

## 3. Gap matrix

Reading the "Coverage" column: **Strong** = a suitable product exists and passes the four tests; **Partial** = products exist but fail at least one test; **Weak** = no suitable product for our use case.

| ID | Capability | Best existing solution(s) | Coverage | Gap class | Action | Requirements | Confidence |
|---|---|---|---|---|---|---|---|
| C01 | Case management / orchestration | Castor, OpenClinica Enterprise, Medidata Rave/CTMS, Veeva, Florence (site workflows). All orchestrate *inside* their own suite or EDC | **Partial** — no neutral multi-EDC, multi-hospital orchestration layer for Dutch academic research; Yamicc's demo is the only public attempt | **Contested** | **Build thin orchestration**; integrate EDCs | FR-002, FR-003, FR-005, FR-006, FR-020, FR-022 | Medium-high |
| C02 | Protocol-authoring AI | Cori Clinical (early commercial and not validated, `D3-1` §3.4); OpenStudyBuilder (GPLv3 metadata, not drafting) | **Partial** — Cori is early commercial; the Erasmus MC customer claim is [CLAIMED-VENDOR]; no Dutch-fit, EU-residency or lock-in-free adoption evidence | **Contested** (provisional) | **Integrate/partner or defer**; do not build | FR-012, FR-019, FR-056 | Medium |
| C03 | eCRF / data capture | Castor (6 Dutch UMCs [VERIFIED: `D3-1` §4.4]), ORTEC LogiqSuite (Yamicc partner; production), REDCap (UMCG), OpenClinica, Medidata, Veeva, Viedoc | **Strong** — mature, validated, already installed | **Closed** | **Integrate the EDC**; do not build a full EDC. Note `04` FR-030–FR-032 and FR-035 are P0 native form requirements (FR-033/034 are P1) — see X7 | FR-030–FR-036, FR-037 | High |
| C04 | Datahub / EHR access | OpenClinica Unite, IgniteData Archer, Medidata Health Record Connect/Companion, Oracle Clinical Connector, Castor Catalyst EHR export [CLAIMED-VENDOR], Epic research module [INFERRED: single weak `D3-1` mention] | **Partial** — US-centric evidence; no public Dutch HiX/ChipSoft connector (public absence, not proof); EU hosting and hospital-side processing unclear for most | **Contested** | **Build the Dutch connector + FHIR + provenance layer** | FR-040–FR-046, FR-050 | Medium-high |
| C05 | FAIR data principles | OMOP CDM + OHDSI (Apache-2.0), MOLGENIS (LGPL-3.0), Health-RI, EHDEN | **Strong** for retrospective/observational FAIR outputs; this row does not cover prospective trial capture — that is C03/G2 | **Closed** (as principle/tooling; the Need test is met for FAIR outputs only, not prospective capture) | **Reuse standards and tools**; publish FAIR outputs, not the slogan | FR-065–FR-067, NFR-06 | High |
| C06 | Interoperability via open standards | HAPI FHIR / Medplum (Apache-2.0), mCODE, OMOP, CDISC ODM/SDTM, terminology services | **Strong** — standards and servers are commodity | **Closed** | **Reuse**; publish a conformance statement naming FHIR R4/mCODE, OMOP, CDISC | FR-040, FR-043, FR-065, NFR-05 | High |
| C07 | AI diagnostics / recommendations | Tempus, Flatiron, cBioPortal + CIViC evidence; commercial diagnostic AI | **Strong** in the US commercial market; MDR-sensitive and outside MVP | **Out of scope** | **Defer/ignore for MVP**; revisit under NFR-04 | FR-074–FR-076 | High |
| C08 | Digital thread | OHDSI, cBioPortal, MOLGENIS, Health-RI cover parts; no integrated cross-source linkage product | **Partial** — fragmented; long-horizon | **Contested** | **Defer to Phase 3+**; reuse building blocks | FR-065–FR-067, FR-071 | Medium |
| C09 | Imaging / DICOM | OHIF Viewer (MIT), XNAT (BSD-2), hospital PACS | **Strong** — commodity viewers and archives | **Out of scope** | **Ignore for now**; defer to Phase 2+ | FR-078 | High |
| C10 | Multi-omics collection/linkage | Hartwig (NL, controlled), AACR GENIE, GDC/TCGA, ICGC ARGO, EGA, cBioPortal | **Partial** — data exists but access is gated and takes weeks to months; not a software gap | **Open — non-software** (data partnership) | **Partner/defer**; do not build a genomics archive | FR-071, FR-077 | High on access model |
| C11 | Multi-hospital live use | Castor (6 UMCs), OpenClinica (450+ sites [CLAIMED-VENDOR]), DRUP (36 hospitals [VERIFIED: `D3-3` DS-02; a Hartwig page says 37 — X8]), EORTC | **Partial** — multi-site EDC exists; integrated multi-site orchestration and governance do not | **Contested** | **Build governance/onboarding**; integrate EDC per site | FR-060, FR-063, FR-069 | Medium-high |
| C12 | Hosting / deployment | EU hosting from Castor, LogiqSuite, Viedoc, TrialKit; federated analysis from vantage6/DataSHIELD; hospital-side capture not productised | **Partial** — EU residency is sold; hospital-side *capture* is not a product feature | **Contested** | **Build deployment option**: hospital node + central coordination | FR-047, FR-061, FR-062, NFR-07 | Medium |
| C13 | GxP / validated platform | Medidata, Veeva, Castor validated suites; no public validation package for AI-assisted capture | **Partial** — validated EDC exists; validated *AI extraction* does not | **Contested** | **Treat validation as a capability**, not paperwork; build evidence from day one | NFR-11, FR-058, FR-059 | Medium-high |

**Counts:** Closed **3** (C03, C05, C06) · Contested **7** (C01, C02, C04, C08, C11, C12, C13) · Open — non-software **1** (C10) · Open — software **0** · Out of scope **2** (C07, C09). Total 13.

**The headline:** applying the four tests strictly leaves **no capability that is both open and software-shaped**. Seven capabilities are Contested: a product exists, but it fails a Dutch-fit, governance or adoption test. C04 (Dutch EHR connectivity) and C12 (deployment posture) are the two contested rows closest to open and still software we would own. C10 is a data-access partnership; C13 is a quality/validation programme. The real build surface is the cross-cutting layer in §4, not any single C-row, and it is smaller than Yamicc's capability list suggests.

---

## 4. Cross-cutting gaps: the actual build surface

These are the layers that no single EDC vendor, open-source component or data source owns. They are the reason MVP B is a product and not an integration project.

| ID | Gap | What exists today | Why it does not close the gap | What we build | Requirements | Confidence |
|---|---|---|---|---|---|---|
| **G1** | Dutch-language, evidence-linked document→eCRF extraction with abstention and audit | Castor Catalyst (confidence + bounding boxes + human acceptance; Dutch quality not public); IgniteData Archer Intelligence (US, notes extraction, no EU/NL evidence); OpenClinica Unite (structured EHR mapping, not Dutch free text); Paradigm eSource (US) | All are either US-market, EDC-locked, or silent on Dutch clinical text. None publishes Dutch accuracy or a portable review/audit layer across EDCs | Extraction service + UI-005 review screen: per-field evidence span, confidence, abstain, accept/correct/reject, full audit | FR-050–FR-054, FR-058, FR-059 | Medium-high |
| **G2** | Multi-EDC pre-population and write-back with provenance | Castor REST API (write scopes not public); LogiqSuite REST (write support not public); OpenClinica ODM/REST; REDCap API | Each EDC has its own model and partial API. No neutral adapter guarantees "extract once, write into whichever EDC the site owns" with source provenance | EDC adapter layer + mapping + provenance + idempotent write with human approval | FR-036, FR-046, FR-054, FR-038 | Medium |
| **G3** | Hospital-side processing + thin multi-site orchestration | Castor/LogiqSuite/Viedoc cloud with EU residency; vantage6/DataSHIELD for federated *analysis* | Federated analysis tools do not capture or review trial data; EDC clouds centralise it. No product combines hospital-side capture with central coordination | Deployable hospital node (containers), central coordination service, site-scoped access, integration monitoring | FR-047, FR-061–FR-063, FR-045, NFR-07 | Medium |
| **G4** | Validation evidence for AI-assisted data capture | Validated EDC suites (21 CFR Part 11 / Annex 11); no public validation package for an LLM/extraction workflow in this market | Vendors claim GxP alignment, not a traceable validation package for AI output and reviewer action | Validation-ready design: model version, prompt/config ref, input snapshot, output, reviewer action, timestamps; IQ/OQ/PQ evidence plan | NFR-11, FR-058, FR-059 | High that the gap exists |
| **G5** | Dutch EHR connector conformance (Epic NL, HiX/ChipSoft) + terminology | OpenClinica Unite (Epic/Cerner, US); Epic research module [INFERRED: single weak `D3-1` mention]; HAPI/Medplum FHIR servers; SNOMED/LOINC mapping tools | No public evidence of a third-party product with a production HiX connector and Dutch terminology mapping for trial capture | Connector framework + conformance test suite + terminology mapping review UI | FR-041, FR-043, FR-044 | Medium-high |
| **G6** | Rare-cancer small-N cohort and consent-aware reuse | Generic EDC cohort tools; OHDSI Atlas; OpenSAFELY governance model | Generic tools assume larger N and do not encode rare-cancer recruitment or granular consent at query time | Thin cohort/eligibility layer + consent/purpose enforcement + disclosure control | FR-027, FR-063, FR-079 | Medium |

**Do not confuse G1–G6 with "build a platform".** G1, G2 and G5 are extraction/connector engineering. G3 is deployment engineering. G4 is process and evidence. G6 is governance. Only G1 carries product differentiation; the rest are entry requirements or enablers.

---

## 5. What looks like a gap but is not (anti-gap list)

This list prevents the most expensive mistake: rebuilding mature software because Yamicc does not have it.

| Tempting to build | Why it is not a gap | Correct action | Evidence |
|---|---|---|---|
| An EDC or eCRF form engine | Castor, LogiqSuite, REDCap, OpenClinica, Medidata, Veeva are mature; 6 Dutch UMCs already run Castor; UMCG mandates REDCap | Integrate via API (FR-036) | `D3-1` §4.4 |
| Protocol-writing AI | Cori ships it, reports Erasmus MC [CLAIMED-VENDOR], and is already in Yamicc's stack | Integrate/partner or defer (FR-019 P2) | `D3-1` §3.4 |
| A FHIR server | HAPI and Medplum are Apache-2.0 and active | Reuse; spike both | `D3-2` §3.6 |
| An identity provider | Keycloak is Apache-2.0 and active | Reuse (FR-001) | `D3-2` §3.6 |
| A workflow engine | Temporal is MIT and active | Reuse (FR-006) | `D3-2` §3.7 |
| Dashboards | Superset (Apache-2.0) covers it | Reuse (FR-002) | `D3-2` §3.8 |
| An OMOP/cohort stack | OHDSI Atlas/WebAPI/CDM are Apache-2.0 | Reuse (FR-065/066) | `D3-2` §3.2 |
| A terminology server | Existing terminology services and Athena vocabularies; licensing is the real issue | Reuse/licence (FR-043) | `D3-2` §3.2 |
| A federated analysis engine | vantage6 is Apache-2.0, NL lineage, active | Reuse (FR-061) | `D3-2` §3.3 |
| An imaging archive/viewer | OHIF and XNAT are mature | Defer (FR-078) | `D3-2` §3.5 |
| AI diagnostics or trial matching | MDR-sensitive, US incumbents, outside MVP | Defer (FR-074–FR-076, NFR-04) | `D3-1` §4 |
| A genomics data commons | Hartwig/GENIE/GDC/EGA exist; access is the constraint | Partner (FR-071) | `D3-3` |

**Rule for T16/D12:** any row in this table that appears as "Build" in the build-vs-buy matrix needs an explicit justification that contradicts this section.

---

## 6. Gap → MVP option fit (input to T17)

MVP definitions from `08` §2. This is a research-side scoring; Product owns the final decision.

| MVP | Capabilities closed | Gaps still open after MVP | Regulatory burden | Defensibility | Verdict |
|---|---|---|---|---|---|
| **A — Trial operations cockpit** | C01 partially; C11 partially | G1, G2, G4, G5 — the hard differentiators | Low–medium | **Low** — a workflow shell over Castor/LogiqSuite; easy to copy | **Research view: not sufficient alone.** Use as thin elements inside B |
| **B — AI-assisted data capture** | C04 (live connector, [CLAIMED-VENDOR] upstream), C01 partially; attacks G1, G2, G5; carries G3 as a thin hospital node for the pilot | G4, G6 (and full G3 for multi-site scale) | Medium (AI Act, possible MDR classification of extraction) | **Medium-high** — narrow but real: Dutch text + evidence + audit + multi-EDC | **Research view: recommended primary MVP** |
| **C — Multicenter data platform** | C05, C06, C08 partially, C11 partially | G1, G2, C04 live capture | Low–medium | **Medium** — standards plumbing; OHDSI already covers much | **Research view: Phase-2 capability**, not the wedge |
| **D — Broad first release** | Most of C01–C08 at shallow depth | All deep gaps remain | High (matching is MDR-sensitive) | Low — breadth without depth | **Research view: reject for Phase 1** |

**Recommended combination:** **B + thin A**.
- B supplies the wedge: Dutch document/FHIR → evidence-linked extraction → human review → EDC write-back, with audit and provenance.
- Thin A supplies the operational shell: study dashboard, task list, participant status, integration monitor — enough to run a pilot, not a CTMS.
- C becomes the Phase-2/3 data platform once one site is live and the extraction quality is measured.
- D is rejected: it pulls matching and diagnostics into Phase 1 and spreads a small team across every capability.

**Why B wins on the evidence (research view, not a Product decision):** no capability is both open and software-shaped; C04 and C12 are the two contested rows closest to open. B is the MVP that attacks C04 and creates G1/G2. B does not close C12 on its own: G3 is carried inside B as a thin hospital node for the pilot, while full multi-site orchestration stays open until Phase 2. That is still the right trade because A and C leave G1/G2 untouched, and G1/G2 are the only defensible product surface in this market; C12/G3 is an enabler, not the wedge. **Confidence: medium-high.** The main uncertainty is not the gap; it is whether Castor Catalyst or IgniteData closes it first with Dutch support.

---

## 7. Recommendations (for CTO and Product)

These are recommendations. The CTO owns the build-vs-buy call (T16/D12); Product owns the MVP choice (T17/D13).

| # | Recommendation | Type | Requirements | Confidence | What would change it |
|---|---|---|---|---|---|
| R1 | Build G1: Dutch document extraction with evidence spans, confidence, abstention and audit | Build | FR-050–FR-054, FR-058, FR-059 | Medium-high | Catalyst/Archer proves Dutch accuracy and opens an API |
| R2 | Build G2: EDC adapter layer with human-approved write-back and provenance | Build | FR-036, FR-046, FR-054 | Medium | LogiqSuite/Castor confirm authenticated write APIs |
| R3 | Build a thin hospital node + central coordination (G3) | Build | FR-047, FR-061–FR-063, NFR-07 | Medium | A pilot site accepts a vendor cloud under a DPA |
| R4 | Integrate the EDC, protocol AI, FHIR server, identity, workflow, dashboards and OMOP stack | Integrate/reuse | FR-001, FR-002, FR-006, FR-019, FR-030–FR-036, FR-040, FR-065 | High | A vendor mandates replacement or a licence blocks reuse |
| R5 | Treat validation evidence as a product capability from day one (G4) | Build/process | NFR-11, FR-058, FR-059 | High | Regulatory guidance says AI extraction is out of scope |
| R6 | Measure extraction quality per field and per site from the first synthetic run | Build/process | FR-059 | High | None — without this, B has no defensible claim |
| R7 | Defer AI diagnostics, digital-thread analysis, imaging and multi-omics analysis | Defer | FR-074–FR-078 | High | A funded Phase-3 partner requires them |
| R8 | Do not claim a capability gap where a mature product already exists (EDC, FHIR, identity, dashboards) | Positioning | — | High | None |

Every R-row inherits the D2-S14 caveat: "no production Yamicc" means no verified production capability above demo level, and the four demo-level ratings are [CLAIMED] because they rest on D2-S14 (search-index capture only).

**Note on confidence:** R1 is the only recommendation that carries product differentiation and therefore the only one that justifies a feasibility spike before Gate 2. Spike scope: one Dutch synthetic document set, one target EDC (LogiqSuite or Castor sandbox), one field set, measured time and override rate. It is throwaway prototype work and does not merge without Engineering review.

---

## 8. Confidence, conflicts and change triggers

### 8.1 Confidence summary

| Claim | Confidence | Basis |
|---|---|---|
| No Yamicc capability is above demo level | High | D2 §4 (QA-passed; four demo ratings are [CLAIMED] on D2-S14) |
| EDC, FHIR, identity, dashboards and OMOP are closed | High | `D3-1`/`D3-2`, licence + version facts |
| Protocol AI can be integrated rather than built | Medium | Cori is early commercial; Erasmus MC claim is vendor-sourced |
| Dutch-language evidence-linked extraction is the narrow gap | Medium-high | `D3-1` §0/§4.1–4.2; no public Dutch benchmark |
| No Dutch HiX connector exists in the reviewed products | Medium-high | Public absence, not proof; vendor docs are incomplete |
| Hospital-side capture is not productised | Medium | Inferred from vendor deployment models; no vendor call |
| MVP B + thin A is the best gap-closing option | Medium-high | 08 §2 + this matrix; Product must confirm |
| Yamicc 2026 POC timing | Low | No date or site published |

### 8.2 Conflicts carried forward (not hidden)

| # | Conflict | Sources | Handling in D4 |
|---|---|---|---|
| X1 | Yamicc demo evidence (D2-S14) is not a stable page | D2 §4.2 | Ratings inherit [CLAIMED]; headline unchanged if D2-S14 fails |
| X2 | Cori's Erasmus MC customer claim is vendor-sourced | `D3-1` §3.4 | Treated as [CLAIMED-VENDOR]; does not change "integrate/defer" |
| X3 | Castor Catalyst's 99.16% acceptance is a vendor figure with no Dutch evidence | `D3-1` §3.1 | Treated as [CLAIMED-VENDOR]; Dutch fit marked low |
| X4 | IgniteData/OpenClinica have no Dutch deployment evidence | `D3-1` §4, `D3-2` | Recorded as inference from absence, not as fact |
| X5 | LogiqSuite write-API support is not public | `D3-1` §3.3 | G2 effort marked medium, not low |
| X6 | D2/D3 review status may change before Gate 1 | T21 | No drift found against the current D2 §4 text (M8). T21 must still re-check D4 against the approved D2/D3 revisions; X6 closes only when those re-checks close |
| X7 | D4 integrate-only stance conflicts with `04` P0 native form requirements (FR-030–FR-032, FR-035; FR-033/034 are P1) and `08` §2 B ("own or external EDC") | `04` FR table, `08` §2 | Raised, not resolved. Owner: Product (T17/T10). Either re-scope FR-030–FR-035 as form-layer extensions on the integrated EDC, or de-prioritise them below P0. CTO rules at T16 if it changes build scope |
| X8 | DRUP hospital count is 36 or 37 | `D3-3` DS-02 (36, ClinicalTrials.gov) vs Hartwig methods page (37) | D4 uses 36; 37 is not used. Does not change C11's class |

### 8.3 Watch triggers

| Trigger | Effect on D4 | Owner |
|---|---|---|
| Castor Catalyst publishes Dutch accuracy or a write API | G1/G2 move from "build" to "integrate/co-sell" | Research (vendor/web watch) |
| IgniteData or OpenClinica announces EU hosting + HiX connector | C04/G5 narrow; hospital-side emphasis becomes the differentiator | Research (vendor/web watch) |
| LogiqSuite publishes authenticated write scopes | G2 effort drops; adapter becomes configuration | CTO (G2) |
| Yamicc POC names a hospital, standard and live data | C01/C04/C11 upgrade; urgency rises | Research (vendor/web watch) |
| A Dutch UMC mandates a single EDC | Integration-first becomes mandatory (already the default) | Product (site choice) |
| EU MDR classifies document→eCRF extraction as a device | G4 scope and timeline change; escalate to CTO/Security | Regulatory (MDR) / CTO |
| A pilot site accepts vendor cloud under a DPA | G3 hospital-side requirement becomes optional | Product (site choice) / CTO (G3) |

---

## 9. Open questions for D15 (T19)

| # | Question | Why it matters | Owner / route |
|---|---|---|---|
| Q1 | Does Castor Catalyst preserve evidence spans and perform acceptably on Dutch clinical text? | Decides G1 build vs integrate | Research (Gate 0 vendor briefing) |
| Q2 | Do Castor and LogiqSuite expose authenticated write APIs for third-party pre-population? | Decides G2 effort | CTO (Gate 0) |
| Q3 | Which Dutch hospitals in scope run Epic vs HiX/ChipSoft, and which expose FHIR R4 today? | Sizes G5 and C04 | Interop (T12/T13) |
| Q4 | Is IgniteData available in the EU/NL, and does Archer support HiX? | Could close C04/G1 externally | Research (Gate 0) |
| Q5 | Is document→eCRF extraction a medical device for our intended purpose? | Changes scope, cost and timeline | Regulatory (T15) |
| Q6 | What is the minimum validation evidence a Dutch pilot site will accept for AI-assisted capture? | Defines G4 acceptance criteria | Regulatory + CTO (T15/T13) |
| Q7 | Does a pilot site accept vendor-cloud processing under a DPA, or require hospital-side only? | Decides whether G3 is mandatory or optional | Product (T09 interviews, Gate 0) |
| Q8 | Which EDC do the first pilot hospitals already run? | Sets FR-036 integration priority | Product + Research (T09/T06) |
| Q9 | Is a strong-copyleft component acceptable for any gap-closing layer (OpenStudyBuilder, DataSHIELD)? | Constrains reuse options | CTO + legal (T16) |

---

## 10. Sources

D4 synthesises QA-tracked inputs. The load-bearing primary sources for the competitive claims are listed below; internal evidence is cited by section.

| # | Source | URL | Access date | Used for |
|---|---|---|---|---|
| S1 | Castor — Catalyst milestone (3 Sep 2026) | https://www.castoredc.com/news/castor-catalyst-data-extraction-milestone/ | 2026-11-21 | Catalyst capability and 99.16% claim (vendor) |
| S2 | Castor — Catalyst product page | https://www.castoredc.com/catalyst-ai-clinical-data-extraction/ | 2026-11-21 | Confidence, bounding boxes, FHIR/TEFCA |
| S3 | Health-RI — institutional EDC licences | https://www.health-ri.nl/en/overview-local-support-offices-and-institutional-edc-licenses | 2026-11-21 | Castor at six Dutch UMCs; UMCG REDCap |
| S4 | OpenClinica — EHR-to-EDC | https://www.openclinica.com/ehr-to-edc-integration/ | 2026-11-21 | Unite capability, site activation |
| S5 | IgniteData — Solutions | https://ignitedata.com/solutions/ | 2026-11-21 | Archer and Archer Intelligence |
| S6 | ORTEC Logiqcare | https://logiqcare.com/ | 2026-11-21 | LogiqSuite eCRF/ePRO |
| S7 | Cori Clinical | https://www.cori-clinical.com/ | 2026-11-21 | Protocol AI capability |
| S8 | HAPI FHIR repository | https://github.com/hapifhir/hapi-fhir | 2026-11-21 | FHIR server (Apache-2.0) |
| S9 | Medplum repository | https://github.com/medplum/medplum | 2026-11-21 | FHIR server alternative |
| S10 | OHDSI CommonDataModel | https://github.com/OHDSI/CommonDataModel | 2026-11-21 | OMOP CDM (Apache-2.0) |
| S11 | vantage6 repository | https://github.com/vantage6/vantage6 | 2026-11-21 | Federated analysis (Apache-2.0) |
| S12 | Keycloak repository | https://github.com/keycloak/keycloak | 2026-11-21 | Identity (Apache-2.0) |
| S13 | Temporal repository | https://github.com/temporalio/temporal | 2026-11-21 | Workflow (MIT) |
| S14 | Apache Superset | https://github.com/apache/superset | 2026-11-21 | Dashboards (Apache-2.0) |
| S15 | OHIF Viewer | https://github.com/OHIF/Viewers | 2026-11-21 | Imaging viewer (MIT) |
| S16 | Hartwig Medical Foundation | https://www.hartwigmedicalfoundation.nl/en/data/research-and-science/onderzoek | 2026-11-21 | Genomic data access (controlled) |
| S17 | Yamicc Annual Report 2025 | https://yamicc.org/wp-content/uploads/2026/06/Jaarrekening-2025-Stichting-Yamicc-Website.pdf | 2026-11-21 | Yamicc maturity baseline |
| S18 | D2 — Verified Yamicc analysis | `deliverables/D2_yamicc.md` §4 | 2026-11-21 | Capability inventory and maturity ratings |
| S19 | D3 §1 — Commercial vendors | `deliverables/d3_competitive_landscape.md` | 2026-11-21 | Vendor coverage and verdicts |
| S20 | D3 §2 — Open-source assessments | `deliverables/D3_s2_open_source_assessments.md` | 2026-11-21 | Component coverage, licences, maintenance |
| S21 | D3 §3 — Data sources | `deliverables/D3_appendix_data_sources.md` | 2026-11-21 | Data-source coverage and access model |

**Evidence labels:** `[VERIFIED]` public source supports the claim · `[CLAIMED-VENDOR]` vendor claim, not independently tested · `[INFERRED]` reasoning, not fact · `[GK]` general domain knowledge. D2/D3 labels carry through.

---

## 11. Definition of done check (09 §5)

- [x] **Sources cited with access date** — §10; D4 also cites D2 and `D3-1`/`D3-2`/`D3-3` by section with access date 2026-11-21.
- [x] **Evidence labels present** — §1 and §10 legends; applied to the named vendor claims in §3 (Castor, OpenClinica, DRUP, Cori) and to the conditional claims in §4. The C-matrix is a synthesis; "labelled" means these named claims carry a label, not that every cell has one.
- [x] **Conflicts flagged, not hidden** — §8.2 X1–X8; no conflict averaged away.
- [x] **Requirement IDs consistent with 04** — every FR/NFR used in §3, §4, §6 and §7 exists in `04` with matching meaning (checked: FR-001–006, FR-012, FR-019–022, FR-027, FR-030–036, FR-038, FR-040–047, FR-050–054, FR-056, FR-058–059, FR-060–063, FR-065–067, FR-069, FR-071, FR-074–079, NFR-04–07, NFR-11).
- [ ] **Reviewed by Fact-Checker** — first review returned changes (F1–F4, M1–M8); this revision applies them. Not yet PASS. Review stays on [CEL-1792](/CEL/issues/CEL-1792); this box closes only on a QA PASS.
- [x] **Open questions added to D15** — §9, Q1–Q9, for the T19 owner to merge.
- [x] **Owners acknowledged** — Research authored; Product co-owns §6 and must confirm the MVP fit in T17.
- [ ] **Gate 1 package complete** — D4 awaiting QA re-review PASS and the D2/D3 re-check closure (X6).

---

## 12. QA handoff (T21)

**What to check**
1. **Synthesis accuracy** — does each C-row correctly reflect D2 §4 and the D3 verdicts? Flag any row where D4 is stronger than its input.
2. **Gap-class logic** — apply the four tests in §1 to C01–C13; challenge any "Closed" that is not truly mature or any "Open" that a listed product already covers.
3. **MVP scoring** — §6 is research input, not a Product decision. Confirm it is labelled as such and does not pre-empt T17.
4. **Requirement IDs** — verify every ID against `04`; no new IDs should be introduced.
5. **Confidence and triggers** — are the change triggers observable and owned?
6. **No overstatement** — "no Dutch HiX connector" must read as public absence, not proof. "No production Yamicc" must carry the S14 caveat.
7. **Privacy** — no personal contact data; company/business information only.

**Review task:** [CEL-1792](/CEL/issues/CEL-1792) — first review returned request-changes; v2 applies F1–F4 and M1–M8. Re-review requested 21 Nov 2026. Review notes go on that task; further fixes return to T07.

---

## Change log (2026-11-21)

| Version | Change | Reason |
|---|---|---|
| v1 | First complete D4 draft | T07; blockers T02/T04/T05 resolved |
| v2 | Apply T21 F1–F4: Open/Contested logic aligned to §1 definitions (C04, C12, C13 → Contested; C10 → Open — non-software); C02 → Contested (provisional); X7 added for `04` FR-030–FR-035; S14 caveat added to §0. Apply M1–M8: confidence unified, D3 file aliases, D2-S numbering, owned triggers, softened MVP wording, FR-059 wording, DoD evidence-label wording, X6/X8. | QA request changes on [CEL-1792](/CEL/issues/CEL-1792) |
