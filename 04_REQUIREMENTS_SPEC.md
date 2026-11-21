# 04 — MERGED REQUIREMENTS SPECIFICATION

Canonical IDs below replace the separate numbering in inputs A, B and C. "Src" shows origin (A = Claude prompt, B = Master prompt, C = Context prompt). Priorities are preliminary: **P0** essential for selected MVP · **P1** needed for production · **P2** advanced/future. Re-prioritize after MVP selection (08).

The Product agent must extend each row to: ID · Description · User role(s) · Priority · Dependencies · Acceptance criteria · Existing alternatives · Build / Integrate / Reuse / Defer.

## 1. User roles
| Role | Key needs |
|---|---|
| R1 Principal investigator | Study overview, recruitment, site performance, protocol status, safety & quality alerts, reporting |
| R2 Study coordinator | Enrollment, screening lists, visit scheduling, missing data, tasks, participant status |
| R3 Treating clinician | Relevant patient info, eligibility, history, confirm/correct extracted values, AE reporting, no duplicate entry |
| R4 Research nurse | Visit checklists, eCRF completion, sample workflows, follow-up tasks, validation alerts |
| R5 Clinical data manager | Quality dashboard, queries, provenance, AI extraction review, validation rules, locking, export |
| R6 Hospital data engineer / data steward | Source config, FHIR, terminology mapping, pipeline health, lineage, logs |
| R7 Trial designer / researcher | Protocol, study config, eligibility builder, visit schedule, eCRF builder, versioning, approvals |
| R8 Biostatistician / bioinformatician | Cohorts, approved data access, reproducible exports, survival/genomic stratification, notebooks |
| R9 Molecular tumor board member | Integrated clinical + genomic (+ imaging) view, evidence for drug options, recorded decision |
| R10 Admin / compliance officer | IAM, access policies, audit logs, consent status, retention, security monitoring, regulatory evidence |
| R11 Monitor / auditor | Read-only source verification, audit trail review |
| R12 Sponsor / funder | Read-only progress reporting |
| R13 Patient / caregiver (optional) | eConsent, questionnaires/ePRO, visit info, trial discovery, withdrawal |

## 2. Functional requirements

### 2.1 Unified workspace
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-001 | Authentication: institutional SSO, MFA, role- and attribute-based access | P0 | B,C |
| FR-002 | Study dashboard: active studies, enrollment, sites, open work, milestones | P0 | A,B |
| FR-003 | Task management: create, assign, track, complete | P0 | B |
| FR-004 | Notifications for changes, missing data, reviews, deadlines | P1 | B |
| FR-005 | Multi-institution navigation without exposing unauthorized data | P1 | B |
| FR-006 | Event-driven workflow orchestration with explicit states across connected systems | P0 | B |

### 2.2 Study & protocol design
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-010 | Study configuration: sites, roles, arms, cohorts, parameters | P0 | A,B |
| FR-011 | Protocol document management: upload, version, review, approve | P1 | B |
| FR-012 | AI extraction of structured elements from protocol documents | P1 | B |
| FR-013 | Machine-readable inclusion/exclusion criteria, usable for automated pre-screening | P1 | A,B |
| FR-014 | Visit schedule designer: visits, windows, assessments, required data | P1 | A,B |
| FR-015 | eCRF generation/configuration from study requirements | P1 | A,B |
| FR-016 | Library of reusable, versioned CRF modules / data elements mapped to standards (CDASH, mCODE, OMOP) | P1 | A |
| FR-017 | Basket, umbrella and platform designs (multiple cohorts, arms added mid-trial) | P1 | A |
| FR-018 | Protocol amendment management: approvals, effective dates, migration impact | P1 | B |
| FR-019 | AI-assisted protocol drafting and review (competes with Cori Clinical) | P2 | B |

### 2.3 Participant / case management
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-020 | Pseudonymized participant records and lifecycle states | P0 | B |
| FR-021 | Screening, enrollment, screen-failure documentation | P0 | B |
| FR-022 | Participant timeline: visits, treatments, assessments, events | P0 | B |
| FR-023 | Visit workflows: completion, outstanding assessments, windows | P1 | B |
| FR-024 | Treatment exposure and outcome documentation | P1 | B |
| FR-025 | Adverse event / SAE capture and escalation | P1 | A,B |
| FR-026 | Clinical review and electronic sign-off | P1 | B |
| FR-027 | eConsent with granular, revocable consent that drives data usage | P1 | A,C |
| FR-028 | Data queries and monitoring incl. remote source data verification | P1 | A,B |

### 2.4 Electronic data capture
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-030 | Dynamic forms with configurable field types | P0 | B |
| FR-031 | Validation: required, ranges, conditional logic, cross-field | P0 | B |
| FR-032 | Form versioning, reproducible definitions | P0 | B |
| FR-033 | Discrepancy queries raised and resolved | P1 | B |
| FR-034 | Record, form and dataset locking | P1 | B |
| FR-035 | Export with documented schemas and provenance; CDISC ODM/SDTM | P0 | A,B |
| FR-036 | Integrate external EDCs (Castor, REDCap, OpenClinica, LogiqSuite) instead of forcing replacement | P0 | B |
| FR-037 | Manual entry fallback | P0 | A |
| FR-038 | Audit trail on every data point (who, what, when, why, source) | P0 | A,B |

### 2.5 Hospital interoperability
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-040 | HL7 FHIR R4 APIs incl. mCODE profiles; Bulk FHIR | P0 | A,B,C |
| FR-041 | Connector framework with adapters for Dutch EHRs (Epic, HiX/ChipSoft, others) plus CSV/HL7v2 | P0 | A,B,C |
| FR-042 | Controlled data retrieval and synchronization | P0 | B |
| FR-043 | Terminology mapping to SNOMED CT, LOINC, ICD-10/ICD-O-3, RxNorm/ATC, HGNC | P0 | B,C |
| FR-044 | Mapping review UI with human approval | P1 | A,B |
| FR-045 | Integration monitoring: connector health, failures, retries | P0 | B,C |
| FR-046 | Source provenance for every imported value (FHIR Provenance) | P0 | B |
| FR-047 | Hospital-controlled / on-prem deployment option | P1 | A,B,C |
| FR-048 | Automated de-identification/pseudonymization: structured data, free text, DICOM headers | P1 | C |

### 2.6 AI-assisted automation
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-050 | Extract candidate structured data from authorized documents (pathology, notes, radiology, letters), Dutch + English | P1 | A,B,C |
| FR-051 | Evidence-linked output: each value points to source span/record | P0* | B,C |
| FR-052 | Human verification before values become research data | P0* | A,B,C |
| FR-053 | Confidence/uncertainty display and abstention when evidence is insufficient | P0* | B |
| FR-054 | AI-assisted eCRF pre-population | P1 | B,C |
| FR-055 | AI-assisted terminology/schema mapping | P1 | B,C |
| FR-056 | AI-assisted protocol-to-study configuration | P2 | B |
| FR-057 | AI data-quality review: inconsistencies, missing info | P1 | B |
| FR-058 | AI traceability: model version, prompt/config ref, inputs, output, reviewer action, timestamps | P0 | B |
| FR-059 | AI evaluation framework: accuracy, FP/FN, abstention, reviewer burden, per-field and per-site | P0 | A,B |
(*P0 whenever any AI workflow is in MVP.) Hard rule: AI never makes treatment decisions and never writes back to the EHR.

### 2.7 Multicenter research
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-060 | Multi-tenant institutional separation with study-specific collaboration | P1 | B |
| FR-061 | Federated analysis/transformation (vantage6, DataSHIELD or OHDSI network) | P2 | A,B,C |
| FR-062 | Hybrid: central pooling where consent and agreements allow | P2 | A,C |
| FR-063 | Purpose- and institution-specific data access governance, enforced at query time | P0 | B,C |
| FR-064 | Cross-site data quality monitoring | P1 | B |
| FR-065 | OMOP CDM mapping support | P1 | B,C |
| FR-066 | Privacy-preserving cohort exploration (ATLAS-like) with disclosure control | P2 | A,B,C |
| FR-067 | Versioned, documented research dataset generation | P1 | B |
| FR-068 | Secure analysis workspace or API export (Jupyter/RStudio) | P2 | C |
| FR-069 | Site onboarding and data-sharing agreement tracking | P1 | A |

### 2.8 Oncology & genomics modules (plug-in, not core)
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-070 | Tumor characteristics: diagnosis, histology, grade/stage, disease status | P1 | B |
| FR-071 | Molecular profiling import: VCF/MAF, Hartwig outputs, panel reports | P2 | A,B,C |
| FR-072 | Longitudinal treatment history | P1 | B |
| FR-073 | Oncology terminologies: ICD-O-3, NCIt, SNOMED CT, LOINC, HGVS | P1 | B |
| FR-074 | Variant-to-drug evidence (CIViC; OncoKB if licensed) with evidence levels | P2 | A,C |
| FR-075 | Molecular tumor board view with recorded decisions | P2 | A,C |
| FR-076 | Patient-to-trial/cohort matching across hospitals, explainable evidence cards, no black-box scores | P2 | A,C |
| FR-077 | Import of lab/biological model results (organoids, drug sensitivity) | P2 | A |
| FR-078 | Imaging integration (DICOM via OHIF/XNAT) | P2 | C |
| FR-079 | Rare-cancer cohort definitions and small-population workflows | P2 | B |

### 2.9 Patient-facing (optional)
| ID | Requirement | Prio | Src |
|---|---|---|---|
| FR-080 | Mobile-first ePRO / QoL questionnaires (e.g. EORTC QLQ-C30, licensing permitting) | P2 | A,B,C |
| FR-081 | Plain-language trial discovery | P2 | C |
| FR-082 | Withdrawal and consent revocation self-service | P2 | B,C |

## 3. Non-functional requirements
| ID | Requirement |
|---|---|
| NFR-01 | Compliance baseline: GDPR/UAVG, EU CTR 536/2014, ICH E6(R3), EU GMP Annex 11, 21 CFR Part 11 only if US sponsors; Dutch WMO/CCMO. HIPAA only if US data — not a default requirement. |
| NFR-02 | Security: NEN 7510/7512/7513, ISO 27001, encryption in transit/at rest, EU-only hosting, tamper-evident audit logs |
| NFR-03 | AI governance: EU AI Act obligations per intended purpose; human oversight; model change management; bias/subgroup monitoring |
| NFR-04 | MDR scope decision for decision-support features (matching, recommendations) made before building them |
| NFR-05 | Interoperability: FHIR (mCODE), OMOP, CDISC (ODM, CDASH, SDTM, ADaM), SNOMED CT, LOINC, ICD-O-3, NCIt, HGVS, GA4GH, DICOM |
| NFR-06 | FAIR by design; alignment with Health-RI and EHDS |
| NFR-07 | Deployment: hybrid — hospital data node + central coordination; containerized (Docker/Kubernetes); no raw identifiable data leaves the hospital by default |
| NFR-08 | Usability: Dutch + English; site workflows must be measurably faster than manual entry; WCAG 2.2 AA |
| NFR-09 | Openness: OSI-approved license for core (e.g. Apache 2.0); public, documented APIs (REST/FHIR; GraphQL optional) |
| NFR-10 | Scalability: one-hospital pilot → dozens of sites, multiple countries |
| NFR-11 | Validation readiness: requirements traceability, test evidence, release controls from day one |
| NFR-12 | Low cost: runnable by small academic groups; no mandatory proprietary licenses |

## 4. Example acceptance criteria (pattern for all rows)
- FR-052: Given an AI-extracted value, when a reviewer opens it, then the source span is highlighted, confidence is shown, and the value cannot enter the locked dataset until accepted or corrected; all actions are audit-logged.
- FR-041: A new hospital with a FHIR R4 endpoint can be connected and pass a conformance test suite in ≤ 5 working days using only configuration, no code changes.
