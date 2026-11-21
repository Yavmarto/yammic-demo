# 08 — STRATEGY, MVP OPTIONS, ROADMAP & FINAL DELIVERABLES

## 1. Strategic options to evaluate
A. Full replacement of trial software
B. Orchestration/automation layer over existing EDC, EHR and research tools
C. AI-native data capture & validation product
D. Federated research data infrastructure
E. Combination
Score each on: development cost, time to market, regulatory burden, integration complexity, adoption barriers, open-source availability, defensibility, technical risk, user value, sustainability. Do not assume A is best.

## 2. MVP candidates
| MVP | Scope | Goal |
|---|---|---|
| **A — Trial operations cockpit** | Auth, study dashboard, participant workflow, tasks, external EDC integration, integration monitoring, audit | Unified operational layer without replacing existing systems |
| **B — AI-assisted data capture** | Authorized document/FHIR ingestion, extraction, evidence view, human review (UI-005), validation, eCRF population (own or external EDC), provenance & audit | Cut manual trial data entry |
| **C — Multicenter research data platform** | FHIR ingestion, terminology mapping, OMOP transformation, data quality, site governance, cohort exploration, dataset export | Reusable standardized multicenter datasets |
| **D — Input C's Phase 1** | Core trial execution + FHIR/OMOP ingestion + auto-populated eCRFs + basic molecular trial matching | Broad first release |

[INFERRED] Initial view: **B** (optionally with thin A elements) best matches the verified market gap (EHR-to-EDC still not scaled), stays outside MDR, plugs into existing EDCs (incl. Castor/LogiqSuite) and directly attacks Yamicc's weakest verified point (Datahub = mock-up). D is likely too broad for a small team and puts matching (MDR-sensitive) in phase 1 [CONFLICT B vs C]. The Strategy agent must test this view, not adopt it.

## 3. Phased roadmap (merged B + C; adjust after MVP choice)
| Phase | Content | Exit criterion |
|---|---|---|
| 0 Discovery & validation | Verify Yamicc intel, stakeholder interviews (with human approval), product analysis, use-case choice, intended purpose, regulatory scan, synthetic data | Approved MVP decision |
| 1 Technical PoC | Core architecture, initial UI, synthetic FHIR (Synthea), one end-to-end flow, automated tests | Demo on synthetic data |
| 2 Functional MVP | Role workspaces, participant workflow, external EDC integration, validation, audit, selected AI workflow + evaluation | Internal acceptance tests pass |
| 3 Controlled pilot | One hospital, real integration under approvals, security assessment, user testing, measured time savings | Measured efficiency gain, no critical findings |
| 4 Production readiness | QMS/validation, scalability, multi-institution, docs, support | Validated release |
| 5 Advanced | Embedded genomics/imaging viewers, federated querying, ePRO/eConsent portal, matching, protocol AI, repurposing hypotheses (C Phases 2–3) | Per-module intended purpose and approvals |

Never claim a prototype is clinically deployable because it works technically.

## 4. Cost & resource estimate template
Estimate ranges (with assumptions on team, geography, hosting, licenses) for: discovery, UX, frontend, backend, FHIR integration, EDC integration, data engineering, AI, security, QA, regulatory validation, infrastructure, maintenance, onboarding, hospital integration support — for four levels: (1) synthetic prototype, (2) research MVP, (3) controlled hospital pilot, (4) production multicenter platform. No false precision.

## 5. Build-vs-buy matrix template
Columns: Capability · Existing products · Open-source alternatives · License · Maintenance status · Functional completeness · Integration effort · Security maturity · Validation burden · Dev effort · Op cost · Recommendation (Build / Reuse OSS / Integrate commercial / Defer).
Avoid duplicating: REDCap/OpenClinica form builders, OHDSI cohort tools, terminology servers, FHIR servers, identity providers, generic dashboards.

## 6. Differentiators to test (name existing competitors for each)
Open-source transparent architecture · AI-native workflows · EHR-to-EDC automation · modular interoperability · source-grounded AI · federated deployment · low cost for academic and rare-disease networks · task-oriented UX · Dutch EHR and Dutch-language strength · no low-code lock-in (vs Yamicc/Mendix).

## 7. Final report structure (Deliverables D1–D15)
D1 Executive summary · D2 Verified Yamicc analysis (built / demonstrated / announced / proposed, cited) · D3 Competitive landscape · D4 Capability gap analysis · D5 Users & workflows · D6 Requirements matrix · D7 UI/UX spec · D8 Technical architecture · D9 Data & standards strategy · D10 AI architecture · D11 Regulatory & security strategy · D12 Build-vs-buy matrix · D13 Recommended MVP (scope, exclusions, metrics, architecture, acceptance criteria) · D14 Roadmap (phases, milestones, staffing, costs, risks) · D15 Open questions.

## 8. Final strategic answer must cover
What to build · reuse · integrate · explicitly avoid · what the first demo looks like · minimum credible hospital pilot · differentiation vs Castor, OpenClinica, REDCap, OHDSI and Yamicc · biggest technical and regulatory risks · how to validate demand cheaply · realistic deliverables at 3, 6 and 12 months.
End with: (1) product strategy, (2) prioritized MVP spec, (3) tech stack, (4) component reuse plan, (5) UI screen inventory, (6) phased roadmap, (7) rough cost estimate, (8) the 10 most important decisions before development.
