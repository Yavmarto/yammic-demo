# 03 — COMPETITIVE & ECOSYSTEM LANDSCAPE

For EVERY item, the Research agent must record: type, license, maintenance status (last release/commit as of Nov 2026), key capabilities, APIs, overlap with Yamicc, and verdict: Direct competitor / Adjacent / Building block / Data source / Ignore.

## 1. Commercial trial software
| Product | Notes | Status |
|---|---|---|
| Castor (NL) | EDC, eConsent, ePRO, EHR integration, AI features; strong in Dutch academic hospitals. Biggest local competitor. | [GK] verify |
| OpenClinica (Enterprise + Unite) | EHR-to-EDC via FHIR/HL7, Epic/Cerner support, live since 2021, 450+ sites claimed | [VERIFIED] openclinica.com/ehr-to-edc-integration |
| ORTEC Logiqcare — LogiqSuite (NL) | Yamicc's eCRF partner | [VERIFIED] partner; capabilities to research |
| Cori Clinical | Yamicc's protocol-AI partner | [VERIFIED] partner; research product |
| Medidata Rave, Veeva Vault EDC/CTMS, Oracle Clinical One, Medrio, Viedoc, TrialKit, Florence Healthcare | Enterprise/industry EDC, CTMS, eISF | [GK] adjacent; verify |
| IgniteData Archer, Epic research module | EHR-to-EDC | [GK] verify |
| Flatiron, Tempus, Paradigm Health | Oncology RWD / trial-matching platforms (mostly US) | [GK] adjacent |

Evidence on the gap: [VERIFIED] i~HD oncology eSource task force (Cambridge, 2025) — EHR-to-EDC adoption still limited by technical, regulatory and operational barriers; a unified implementation framework was lacking.

## 2. Open-source / academic software
| Component | Role | Notes |
|---|---|---|
| REDCap | Academic EDC, surveys, API, external modules | Free for eligible non-profits but NOT unrestricted open source — license terms matter |
| OpenClinica Community Edition / LibreClinica | Open EDC | Check maintenance; community ≠ enterprise features |
| OpenStudyBuilder | Open-source protocol/study metadata design (CDISC-aligned) | [CLAIMED-C] verify maintenance and license |
| OHDSI: OMOP CDM, ATLAS, WebAPI, Achilles, DataQualityDashboard, WhiteRabbit, Rabbit-in-a-Hat, Usagi, Athena vocabularies | Observational research harmonization and cohort tools | OMOP is NOT a prospective trial execution system |
| vantage6 | Federated analysis (Apache 2.0), by IKNL, Maastro, eScience Center, Erasmus MC; v5.x in 2026 | [VERIFIED] zenodo.org/records/20810243 |
| DataSHIELD | Federated analysis in R | [GK] |
| MOLGENIS (NL) | FAIR data platform for rare-disease registries/biobanks | [GK] |
| i2b2 / tranSMART | Cohort discovery, translational research | [GK] check activity |
| OpenSAFELY | Secure federated analytics model (UK) | [GK] governance model reference |
| cBioPortal, igv.js | Cancer genomics visualization | Building block for tumor board view |
| CIViC (open), OncoKB (licensing restrictions for commercial use) | Variant → drug evidence | Check licenses |
| OHIF Viewer, XNAT | DICOM viewing / imaging archive | Phase 2+ |
| HAPI FHIR, Medplum | FHIR servers / healthcare backend | Building blocks |
| OpenMRS, Bahmni | EMR systems | Mostly adjacent |
| Keycloak | Identity, SSO, MFA | Building block |
| Temporal, Camunda | Workflow orchestration | Building block (check Camunda license changes) |
| Apache NiFi, Airbyte | Data pipelines | Possible ETL |
| Superset, Metabase | Dashboards | Building block |
| Form.io, SurveyJS, LHC-Forms (FHIR Questionnaire) | Form engines | Evaluate for eCRF rendering |
| React Admin, Appsmith | Admin UI | Optional |
| OpenTelemetry | Observability | Building block |

## 3. Data sources and networks
| Source | Type | Access notes |
|---|---|---|
| Hartwig Medical Foundation | WGS + RNA-seq + clinical data of metastatic patients, NL | Controlled access; [VERIFIED] runs WGS/database for DRUP |
| DRUP (NCT02925234) | Dutch pan-cancer basket/umbrella repurposing trial, 49-hospital network | [VERIFIED] closest functional overlap with ReDiReCCT-GB approach — partner candidate |
| Netherlands Cancer Registry (NKR, IKNL) | Population cancer registry | Request-based access |
| PALGA | National pathology archive | Request-based |
| Health-RI | Dutch national health data infrastructure | Align with |
| PROFILES | PRO registry (IKNL) | QoL data |
| AACR Project GENIE | Clinical-genomic multicenter data | Registration; benchmarking |
| NCI GDC / TCGA | Cancer genomics | Open + controlled tiers |
| EGA | Controlled-access genomic/phenotypic data | DAC approval |
| ICGC / ICGC-ARGO | International cancer genomics | Controlled |
| Project Data Sphere | Historical trial arm data | Registration |
| "Pattern Data Commons" | [CLAIMED-C] unknown — verify existence or drop |
| ClinicalTrials.gov (API v2), EU CTIS | Trial metadata, eligibility text | Public; good for matching / protocol-AI training |
| EHDEN | European OMOP federated network | Governance reference |
| EURACAN, ERNs, EORTC, BBMRI-ERIC, ELIXIR, GA4GH | Networks / standards | Partnership and standards |

For each source document: data type, size/coverage, API, license, access restrictions, patient-level availability, refresh frequency, quality, AI suitability, trial suitability, GDPR implications. Publicly searchable ≠ unrestricted patient-level access.

## 4. Initial positioning hypotheses [INFERRED]
- None of Yamicc's components is unique; its value is neutral coordination + a curated partner stack.
- Its stack is partner-dependent (Mendix, LogiqSuite, Cori) — an open, standards-first alternative can compete on lock-in, cost and transparency.
- Biggest real gap in the market: production-grade, multi-hospital EHR/document → eCRF automation with evidence-linked AI and human review, especially for Dutch EHRs (Epic, HiX/ChipSoft) and Dutch-language notes.
- Hartwig/DRUP and IKNL/vantage6 are more useful as partners than enemies.
- For every claimed differentiator, name competitors already offering it. AI alone is not a differentiator.
