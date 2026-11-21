# 05 — UX / UI SPECIFICATION

## 1. Principles
Role-specific · task-oriented · WCAG 2.2 AA · consistent · responsive · explainable · auditable · efficient for high-volume entry (keyboard-first) · suitable for busy clinical settings · minimizes duplicate work · explicit about uncertainty. Speculative AI output must never look like confirmed clinical data (distinct visual state until verified). Dutch + English.

Rule: for every screen, decide Reuse / Embed / Integrate / Extend / Build. Never build custom just because it looks nicer.

## 2. Portals (grouping of screens by audience)
1. **Site workspace** — coordinators, nurses, clinicians (R2–R4)
2. **Study & data management** — PI, designers, data managers, monitors (R1, R5, R7, R11)
3. **Data steward / IT console** — hospital data engineers (R6)
4. **Research & tumor board** — analysts, bioinformaticians, MTB (R8, R9)
5. **Admin & compliance** (R10)
6. **Patient portal** — optional, later (R13)

## 3. Screen inventory
| ID | Screen | Contents | Likely approach [INFERRED] |
|---|---|---|---|
| UI-001 | Research dashboard | Studies, recruitment, sites, completeness, tasks, milestones, alerts | Build (thin) on Superset/Metabase components or custom |
| UI-002 | Participant workspace | Pseudonymized ID, status, visit timeline, clinical summary, eCRF status, quality issues, treatment history | Build — core differentiator for site staff |
| UI-003 | Study designer | Config, protocol metadata, forms, eligibility, visit schedule, versions, approvals | Integrate/extend (OpenStudyBuilder, EDC designer) |
| UI-004 | Data capture | Dynamic forms, conditional fields, inline validation, save/resume, completion, keyboard nav, audit history | Reuse a form engine (FHIR Questionnaire renderer, SurveyJS, Form.io) or external EDC |
| UI-005 | **AI extraction review** (most important custom screen) | Left: source document/record with highlighted evidence. Middle: proposed values, confidence, terminology mapping. Right: target eCRF, validation, Accept / Correct / Reject / Defer. Provenance retained. Batch mode for repetitive fields. | **Build** |
| UI-006 | Data quality workbench | Discrepancy queue, validation failures, missing data, source conflicts, assignment, history, approval | Build or extend EDC queries |
| UI-007 | Integration monitor | Connected systems, status, last sync, failed records, mapping issues, logs, retry | Build on OpenTelemetry/Grafana-style components |
| UI-008 | Mapping workspace | Source field → standard concept suggestions (AI), approve/edit, versioned mappings | Integrate Usagi/Rabbit-in-a-Hat concepts; build review UI |
| UI-009 | Cohort explorer | Visual criteria, standard concepts, counts under disclosure rules, availability, export requests | Reuse/embed OHDSI ATLAS where possible |
| UI-010 | Molecular tumor board | Patient summary, variants (cBioPortal/igv.js), candidate drugs with evidence cards (CIViC), prior treatment, trial options, imaging (OHIF, later), decision record | Embed components + build composition layer |
| UI-011 | Trial-matching / screening list | Candidates per cohort with criterion-by-criterion evidence, met/unmet/unknown | Build |
| UI-012 | Administration | Users, roles, permissions, institutions, audit logs, retention, config | Keycloak admin + thin custom |
| UI-013 | Consent management | Consent status per participant and purpose, revocations | Build on FHIR Consent |
| UI-014 | Patient portal (optional) | eConsent, questionnaires, visit info, ePRO, trial discovery, withdrawal | Defer or reuse existing ePRO |

## 4. Critical user journeys to design first
1. Research nurse completes a visit eCRF using AI-pre-populated values (UI-002 → UI-005 → UI-004).
2. Data manager resolves a discrepancy between EHR source and eCRF (UI-006).
3. Hospital data steward connects a new FHIR source and approves mappings (UI-007, UI-008).
4. Coordinator screens new patients against cohort eligibility (UI-011).
5. Tumor board reviews a newly profiled glioblastoma patient and records a decision (UI-010).
6. PI checks study progress across sites (UI-001).

## 5. Deliverables for the UX agent
1. Information architecture and navigation hierarchy
2. Role–permission matrix (roles R1–R13 × screens × actions)
3. Primary user journeys (above) as flow diagrams
4. Low-fidelity wireframes for UI-002, UI-005, UI-006, UI-008, UI-011 first
5. High-fidelity specs for the MVP screens
6. Component inventory and design-system recommendation (e.g. shadcn/ui + Radix, TanStack Table, React Hook Form)
7. Interaction, error, empty and loading states
8. Accessibility requirements per screen
9. User acceptance criteria per screen
10. Reuse/build decision per screen with justification

## 6. Competitive UX benchmarks to study
Castor, OpenClinica Unite review flow, REDCap data entry, Medidata Rave, LogiqSuite, OHDSI ATLAS, cBioPortal patient view, Epic research activities. Note what each does well and badly for site staff speed.
