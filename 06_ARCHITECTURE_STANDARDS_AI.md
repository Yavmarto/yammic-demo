# 06 — ARCHITECTURE, DATA STANDARDS & AI

## 1. Standards — roles and boundaries
| Standard | Role in platform |
|---|---|
| HL7 FHIR R4 (+ mCODE, SMART on FHIR, Bulk FHIR, Subscriptions) | Ingestion from hospitals, app launch in EHR, operational exchange |
| FHIR resources to evaluate | ResearchStudy, ResearchSubject, Questionnaire, QuestionnaireResponse, Observation, Condition, MedicationAdministration, Procedure, Specimen, Provenance, AuditEvent, Consent |
| OMOP CDM | Harmonized research/observational layer, cohorts, federated analysis |
| CDISC ODM / CDASH / SDTM / ADaM | Trial data definition, collection, regulatory tabulation and analysis datasets |
| SNOMED CT, LOINC, ICD-10, ICD-O-3, NCIt, RxNorm/ATC, HGNC, HGVS | Terminologies |
| GA4GH (Phenopackets, VRS, Beacon, Passports) | Genomic exchange and access |
| DICOM | Imaging |

Open decision for Architecture agent: the **canonical internal model**. Options: (a) FHIR-native operational store + OMOP and CDISC as derived views; (b) own domain model with mappers; (c) OMOP-centric. Must specify where each transformation happens, how information loss is detected, and how mappings are versioned. [INFERRED] Leading option: (a).

## 2. Reference architecture (to evaluate, not final)

### Layers
1. **Hospital data node** (inside each hospital): connectors (FHIR/HL7v2/CSV), de-identification/pseudonymization, local FHIR store, local OMOP ETL, document store, local AI extraction (so text never leaves hospital), federated compute node (vantage6).
2. **Central coordination layer**: study config, workflow orchestration, task management, pseudonymized research data (only where permitted), audit store, terminology service, model registry.
3. **Experience layer**: portals from 05.

### Candidate stack
| Concern | Candidates |
|---|---|
| Frontend | React + TypeScript, Next.js (or Vite SPA), shadcn/ui, TanStack Table, React Hook Form, React Flow, accessible charts; Mendix only if justified (note: Yamicc's likely choice — lock-in trade-off) |
| Backend | Python/FastAPI or TypeScript/NestJS; PostgreSQL; object storage (S3-compatible, e.g. MinIO); event bus (NATS/Kafka/Postgres-based queue); background jobs |
| Workflow | Temporal (preferred to check) or Camunda (check license) |
| FHIR | HAPI FHIR or Medplum |
| Terminology | Snowstorm (SNOMED), Ontoserver (licensed), OHDSI Athena vocabularies |
| ETL | Custom + OHDSI tools; NiFi/Airbyte optional |
| Graph (digital thread) | Postgres first; graph DB only if justified [C proposed graph store] |
| Federated | vantage6 (NL ecosystem fit), DataSHIELD, OHDSI Strategus |
| Identity | Keycloak (OIDC/SAML, MFA), fine-grained authz (OpenFGA / Cerbos / OPA) |
| Observability | OpenTelemetry, Grafana stack |
| Deployment | Docker, Kubernetes/Helm; sovereign EU cloud or on-prem |
Choose for operational simplicity first. Small team = fewer moving parts.

### Data separation
Keep separate: operational app data · identifiable clinical data (hospital only) · pseudonymized research data · documents · audit events · terminology · research datasets · model evaluation data. Avoid unnecessary copies of identifiable data. Define trust boundary per deployment option (SaaS, private cloud, on-prem, federated, hybrid).

## 3. AI architecture
### Use cases (ranked by value/risk [INFERRED])
1. Document → eCRF field extraction with evidence spans (high value, moderate risk)
2. Source-field → terminology/schema mapping suggestions (high value, low risk)
3. Data-quality anomaly detection (medium value, low risk)
4. Eligibility pre-screening against machine-readable criteria (high value, MDR-sensitive)
5. Protocol → study configuration (medium value, low risk)
6. Protocol drafting (crowded: Cori Clinical and others)
7. Variant → drug evidence summarization for MTB (high value, MDR-sensitive)
8. Predictive diagnostics / repurposing hypotheses [C Phase 3] (research-grade, high regulatory burden)

### Model strategy
- Evaluate self-hosted open-weight models inside hospital nodes vs EU-hosted API models under DPA. Criteria: data residency, Dutch clinical text quality, latency, cost, validation stability (pinned versions).
- Structured output with schema validation; mandatory evidence spans; abstain when unsupported.
- RAG only over authorized sources; no training on patient data without legal basis.
- Versioned prompts/configs in a registry; every run logged (FR-058).

### Evaluation & safety
- Gold-standard annotated sets per field type (synthetic + later pilot data under approval).
- Metrics: precision/recall per field, abstention rate, calibration, reviewer time saved, error severity, per-site/subgroup performance.
- Regression tests on every model or prompt change; change control per NFR-03.
- Human-in-the-loop UI (UI-005) is part of the safety case, not decoration.

## 4. Deliverables
Architecture diagrams (C4: context, container, component), data-flow diagrams per journey, interface specs (APIs, events), canonical model decision record, mapping/versioning strategy, AI architecture doc with evaluation plan, deployment options with trust boundaries.
