# D3 §2 — Open-Source & Academic Component Assessments (T05)

**Task:** T05 — Open-source component assessments (03 §2) incl. license + maintenance
**Owners in spec:** Research + CTO · **Accountable agent:** Researcher
**Output:** D3 (open-source section) + license register (`license_register.md`)
**Status:** Draft v2 — QA corrections applied (CEL-1761, C1–C7 + Athena note); resubmitted for focused T21 re-check
**Prepared:** 2026-11-21 · **Evidence access date:** 2026-11-21 (unless a different date is stated)

> **Assembly note.** This is the T05 contribution to D3. Merge it with T04 (commercial vendors, 03 §1) and T06 (data sources, 03 §3) before publishing D3. It resolves the open maintenance/license questions that 03 §2 flagged as `[GK]` or "verify".

---

## 1. Recommendation (read this first)

1. **Build the core from permissive components (Apache-2.0 / MIT / BSD / MPL-2.0).** This satisfies NFR-09 ("OSI-approved license for core, e.g. Apache 2.0") without legal friction. Recommended defaults: **HAPI FHIR or Medplum** (FHIR, FR-040), **Keycloak** (identity, FR-001), **Temporal** (workflow, FR-006), **OHDSI Atlas + WebAPI + CommonDataModel** (OMOP, FR-065/066), **Apache Superset** (dashboards, FR-002), **OpenTelemetry** (observability, FR-045), **SurveyJS / LHC-Forms** (forms, FR-030/032), **cBioPortal + igv.js + OHIF** (oncology/imaging modules, FR-074/075/078), **vantage6** (federated analysis, FR-061).
2. **Integrate strong-copyleft and non-OSI tools across a service boundary; do not link or embed them in the proprietary core.** This applies to **OpenStudyBuilder** (GPLv3), **Metabase** (AGPL-3.0), **DataSHIELD** and **OpenSAFELY** (GPL-3.0), **Airbyte** (ELv2), **Camunda 8** (Camunda License 1.0, not OSI), **REDCap** (Vanderbilt non-profit EULA), and **OncoKB** (proprietary, paid for API/commercial/clinical use).
3. **Integrate, do not rebuild, existing EDC.** REDCap, OpenClinica, Castor and ORTEC LogiqSuite remain external systems reached through their APIs (FR-036). Building a form engine that replaces them is duplication (08 §5) and would raise validation burden for no differentiation.
4. **Avoid / defer:** **tranSMART** (dormant), **Appsmith** (low-code lock-in contradicts the positioning against Yamicc/Mendix), **Form.io server** (commercial platform behind an MIT renderer), **i2b2** (optional niche, defer), **LibreClinica** and **OpenClinica Community Edition** as core bets (maintenance lag; integrate the commercial editions instead).
5. **License-status warning to carry into D8/T13:** cBioPortal changed from AGPL-3.0 to Apache-2.0 in **October 2026**. The latest tagged release (**v7.1.2, 2026-09-17**) predates that change and is still **AGPL-3.0**. Reuse must pin a post-change release/commit or accept AGPL obligations.

**Confidence:** **High** on license identity and version/date facts (GitHub licence metadata + licence files + official pages, read 2026-11-21). **Medium** on maintenance trajectory (release cadence is a proxy, not a health audit). **Low–medium** on operational fit: none of these has been installed in this project yet. No hands-on spike exists at the time of writing.

**What would change this recommendation:** (a) a licence change or relicense (cBioPortal shows this is live); (b) a security advisory or maintainer abandonment in a pinned component; (c) a hands-on spike showing integration cost far above estimate; (d) a CTO decision to accept copyleft for the core (then GPL/AGPL options reopen); (e) a commercial licence on OncoKB/REDCap that changes the cost basis.

---

## 2. Method and evidence conventions

- **Licence and version facts** were read from the GitHub REST API (`license.spdx_id`, latest release/tag, `pushed_at`), the repository `LICENSE`/`README`, or the official vendor page. The `owner/repo` for every GitHub-hosted component is listed in §9.1; the access date is 2026-11-21.
- **Maintenance bands (03 §2 requires "last release/commit as of Nov 2026"):**
  - **Active** — a tagged release or meaningful commit within ~6 months (since 2026-05).
  - **Slowing** — last *release* 6–18 months old, or commits only, or release cadence has clearly dropped.
  - **Dormant** — last meaningful activity >18 months, or archived.
- **Verdicts** use the 03 taxonomy: Direct competitor / Adjacent / Building block / Data source / Ignore.
- **Evidence labels** follow 00 (`00_README_INDEX.md` §"Labels used in every file"): `[VERIFIED]` (confirmed against a public source, URL given), `[CLAIMED-B]` / `[CLAIMED-C]` (stated in input B or C, not independently verified), `[GK]` (general domain knowledge, verify before reliance), `[INFERRED]` (reasoning, not fact). No other evidence labels are used in this section.
- **Reuse decisions** reference requirement IDs from 04.

Maintenance-band assignment is **`[INFERRED]`** from the dated facts in the tables. Verdicts and reuse decisions are **`[INFERRED]`** recommendations for the CTO, not decisions.

---

## 3. Assessments by group

### 3.1 EDC and study design

| Component | Type / key capabilities | Licence | Latest release / commit (2026-11-21) | Maintenance | APIs / interop | Overlap with Yamicc | Verdict | Reuse decision |
|---|---|---|---|---|---|---|---|---|
| **REDCap** (Vanderbilt/VUMC) | EDC, surveys, eConsent (via modules), large external-module ecosystem | **Proprietary** non-profit EULA — *not* OSI open source; no for-profit self-hosting; no redistribution `[VERIFIED]` projectredcap.org/join/ , /partners/termsofuse | 17.5.x (17.5.11 reported 2026-11-10 in the Univ. of Arizona REDCap changelog — secondary source, not vendor-confirmed) `[GK]` | Active | REST API, DDP, ODM/CSV export, external modules | Adjacent to LogiqSuite eCRF; strongest academic EDC incumbent | Adjacent | **Integrate as external EDC** (FR-036). Do not bundle or ship. Do not build a REDCap clone. |
| **OpenClinica Community Edition** | EDC, ODM, study build, queries | **LGPL-3.0** (community; enterprise is commercial) `[VERIFIED]` repo README | 3.17.2 (2024-08-02); last commit 2025-10-28 `[VERIFIED]` | Slowing (release >27 months old; commits only — arguably **Dormant** on release cadence) | REST, ODM/CDISC | Adjacent; EHR-to-EDC claims (03 §1) | Adjacent | **Integrate commercial OpenClinica** if a site uses it (FR-036). Community edition not a core dependency. |
| **LibreClinica** | Fork/continuation of OpenClinica CE | **LGPL-3.0** `[VERIFIED]` GitHub license API | v1.4.0rc1 (2025-06-13); commits 2026-11-18 `[VERIFIED]` | Slowing (RC only; no stable GA) | REST/SOAP, ODM | Adjacent | Adjacent | **Defer.** Only if a partner site already runs it; otherwise not worth the maintenance risk. |
| **OpenStudyBuilder** (Novo Nordisk) | Open study/protocol metadata design, CDISC-aligned | **GPL-3.0 overall**; components differ (`[VERIFIED]` repo root `LICENSE.md`: "The overall project and binary distribution license is GPLv3"; per-component `LICENSE.md`/`sbom.md` files govern each component. GitHub API `license.spdx_id` returns `NOASSERTION` because the licence is in `LICENSE.md`, not `LICENSE`) | v2.12.0 (2026-11-20) `[VERIFIED]` | Active | REST API; CDISC/ODM-oriented metadata model | Adjacent to Cori Clinical protocol authoring; building block for UI-003 | Building block (copyleft) | **Service boundary only** (FR-010/014/016). Option A: run as a separate GPL service. Option B: reuse its data model as reference and build a thin designer. Legal review before either. |

### 3.2 OHDSI / OMOP family

| Component | Type / key capabilities | Licence | Latest release / commit (2026-11-21) | Maintenance | APIs / interop | Overlap with Yamicc | Verdict | Reuse decision |
|---|---|---|---|---|---|---|---|---|
| **OMOP CommonDataModel** | Standard observational data model (v5.5) | **Apache-2.0** `[VERIFIED]` `DESCRIPTION: License: Apache License 2.0` | v5.5.0 (2026-08-25) `[VERIFIED]` | Active | SQL DDL for many dialects; R package | Data standard Yamicc only "announced" (02 §5) | Building block | **Reuse** (FR-065). Adopt CDM v5.5. |
| **Atlas** | Cohort definition, concept sets, OMOP UI | **Apache-2.0** `[VERIFIED]` | v2.15.0 (2025-07-25); commits 2026-09-16 `[VERIFIED]` | Slowing (release lag; active commits) | Web UI on OHDSI WebAPI | Cohort exploration (UI-009) | Building block | **Reuse/embed** for cohort UI (FR-066) if OMOP path chosen. |
| **WebAPI** | REST services behind Atlas | **Apache-2.0** `[VERIFIED]` | v3.0.1 (2026-11-09) `[VERIFIED]` | Active | REST | Cohort/analytics backend | Building block | **Reuse** with Atlas (FR-066). |
| **Achilles** | Data-quality/characterization profiling | **Apache-2.0** `[VERIFIED]` README | v1.7.2 (2023-05-18); commits 2026-10-09 `[VERIFIED]` | Slowing (stale release) | R; writes results tables | Data quality (FR-064) | Building block | **Reuse** with eyes open; pin and monitor security. |
| **DataQualityDashboard (DQD)** | Rule-based OMOP DQ checks | **Apache-2.0** `[VERIFIED]` README | v2.9.1 (2026-10-17) `[VERIFIED]` | Active | R/JSON; results viewable | Data quality (FR-064) | Building block | **Reuse** (FR-064). |
| **WhiteRabbit (+ Rabbit-in-a-Hat)** | Source profiling + source→CDM mapping UI | **Apache-2.0** `[VERIFIED]` | v1.0.0 (2024-08-05); commits 2026-10-13 `[VERIFIED]` | Slowing | Desktop Java; mapping export | Mapping workspace (UI-008) | Building block | **Reuse concepts**; build the review UI ourselves (FR-044). |
| **Usagi** | Term/concept mapping (AI-assisted suggestions) | **Apache-2.0** `[VERIFIED]` README | v1.4.3 (2021-04-09); commits 2026-05-26 `[VERIFIED]` | Slowing (old release) | Desktop Java; Lucene matching | Terminology mapping (FR-043/044/055) | Building block | **Reuse only as reference/benchmark**; evaluate a maintained replacement before depending on it. |
| **Athena** | OMOP vocabulary download service | **No licence statement in repo**; vocabularies carry their own upstream terms `[VERIFIED]` repo has no LICENSE; `[GK]` each vocabulary has separate terms | Repo pushed 2026-09-02 `[VERIFIED]` | Active (data) | Download bundles | Vocabularies for FR-043/073 | Data source | **Use the data under upstream terms** (see `license_register.md` §4). Not a software dependency. |

### 3.3 Federated / privacy-preserving analysis

| Component | Type / key capabilities | Licence | Latest release / commit (2026-11-21) | Maintenance | APIs / interop | Overlap with Yamicc | Verdict | Reuse decision |
|---|---|---|---|---|---|---|---|---|
| **vantage6** | Federated analysis orchestration (IKNL, Maastro, eScience Center, Erasmus MC) | **Apache-2.0** `[VERIFIED]` | v5.1.0 tag; latest published release v4.15.4 (2026-11-09); commits 2026-11-19 `[VERIFIED]` | Active | REST API, Python client, container algorithms | Federated multicenter (FR-061); 03 §3 notes Erasmus MC ties | Building block | **Preferred federated engine** (FR-061). Confirm the v5.1.0 GA status before pinning. |
| **DataSHIELD** | Federated analysis in R (dsBase + Opal) | **GPL-3.0** `[VERIFIED]` dsBase LICENSE | dsBase 6.3.5 (2026-02-22); commits 2026-11-16 `[VERIFIED]` | Active | R client/server; Opal | Federated analysis (FR-061) | Building block (copyleft) | **Service boundary only**, and only if the analytics stack is R-centric. Otherwise vantage6. |
| **OpenSAFELY** | Secure federated analytics *model* + tooling (UK) | **GPL-3.0** `[VERIFIED]` job-runner/airlock/opencodelists LICENSE | Active, commits 2026-11 (job-runner 2026-11-12) `[VERIFIED]` | Active | GitHub-driven analysis workflow; job-runner | Governance/architecture reference (FR-063) | Adjacent (reference) | **Reference the governance model**; do not adopt the stack wholesale. |

### 3.4 Data platforms and registries

| Component | Type / key capabilities | Licence | Latest release / commit (2026-11-21) | Maintenance | APIs / interop | Overlap with Yamicc | Verdict | Reuse decision |
|---|---|---|---|---|---|---|---|---|
| **MOLGENIS** (NL) | FAIR data platform for rare-disease registries/biobanks | **LGPL-3.0** `[VERIFIED]` | molgenis 10.2.4 (2026-03-04) `[VERIFIED]` | Slowing (8+ months since release) | REST, GraphQL, EMX model | Rare-disease data platform (FR-016/067) | Adjacent / building block | **Evaluate for registry-style cohorts only**; not a core dependency. LGPL = dynamic/service use. |
| **i2b2** | Cohort discovery / translational research | **MPL-2.0** (core server) `[VERIFIED]` LICENSE | v1.8.3 (2026-07-01); commits 2026-11-20 `[VERIFIED]` | Active | REST/i2b2 XML, SQL | Cohort discovery (FR-066) | Building block (niche) | **Defer.** OHDSI Atlas covers the same need for this project. |
| **tranSMART** | Translational research data warehouse | **GPL-3.0** (transmartApp) `[VERIFIED]` GitHub license API | Core apps last updated 2024-06; ETL last push 2018; latest tag v1.2.4 `[VERIFIED]` | **Dormant** | REST (Rmodules), ETL | Cohort/translational | Ignore | **Do not adopt.** |

### 3.5 Oncology, genomics and imaging

| Component | Type / key capabilities | Licence | Latest release / commit (2026-11-21) | Maintenance | APIs / interop | Overlap with Yamicc | Verdict | Reuse decision |
|---|---|---|---|---|---|---|---|---|
| **cBioPortal** | Cancer genomics exploration/visualization | **Apache-2.0 since Oct 2026; AGPL-3.0 before** `[VERIFIED]` README | v7.1.2 (2026-09-17) — **predates relicense, so AGPL** ; commits 2026-11-21 `[VERIFIED]` | Active | REST API, web UI, OncoKB/CIViC integration | Tumor board / genomics (FR-071/074/075) | Building block | **Reuse**, but **pin a post-Oct-2026 Apache-2.0 tag/commit** or accept AGPL. |
| **igv.js** | Embeddable genome browser | **MIT** `[VERIFIED]` | v3.8.9 (2026-10-11) `[VERIFIED]` | Active | JavaScript library | Variant visualization (UI-010) | Building block | **Reuse** (FR-075). |
| **CIViC** | Open variant→drug evidence knowledge base | Server code **MIT** `[VERIFIED]`; data is open | civic-server last push 2023-07 (code dormant); public data at civicdb.org is current `[VERIFIED]`+`[GK]` | Dormant (code) / Active (data) | GraphQL API; data dumps | Variant→drug evidence (FR-074) | Data source | **Use the data/API**, not the server code. Confirm current access terms. |
| **OncoKB** (MSK) | Curated variant→drug evidence with evidence levels | **Proprietary**; free academic research, **paid for commercial, clinical/hospital reporting, and API use** `[VERIFIED]` oncokb.org/terms , faq.oncokb.org/licensing | Data v7.6, 2026-09-30 `[VERIFIED]` | Active | REST API (token), annotator | Variant→drug evidence (FR-074) | Data source (licensed) | **Optional, licence-gated** (FR-074). Default to CIViC; buy OncoKB only if a trial protocol requires it. |
| **OHIF Viewer** | DICOMweb viewer | **MIT** `[VERIFIED]` | v3.13.15 (2026-11-19) `[VERIFIED]` | Active | JavaScript/React; DICOMweb | Imaging (FR-078) | Building block | **Reuse** (Phase 2+, FR-078). |
| **XNAT** | Imaging informatics archive/DICOM | **BSD-2-Clause** (Simplified BSD) `[VERIFIED]` xnat.org/about/license.php | 1.10.2 (current download, 2026) `[VERIFIED]` | Active | REST API, DICOM | Imaging archive (FR-078) | Building block | **Defer** to Phase 2+; reuse if imaging needs grow (FR-078). |

### 3.6 Healthcare backend, identity and interoperability

| Component | Type / key capabilities | Licence | Latest release / commit (2026-11-21) | Maintenance | APIs / interop | Overlap with Yamicc | Verdict | Reuse decision |
|---|---|---|---|---|---|---|---|---|
| **HAPI FHIR** | Java FHIR R4/R5 server + libraries | **Apache-2.0** `[VERIFIED]` | v9.0.0 (2026-11-18) `[VERIFIED]` | Active | FHIR REST, JPA | Yamicc Datahub is a mock-up (02 §3b) — a real FHIR server is a differentiator | Building block | **Primary FHIR candidate** (FR-040/046). Spike vs Medplum. |
| **Medplum** | TypeScript FHIR backend + React components | **Apache-2.0** `[VERIFIED]` | v5.2.18 (2026-11-20) `[VERIFIED]` | Active | FHIR R4 REST, TS SDK, React | Same as HAPI | Building block | **Alternative FHIR candidate** (FR-040). Better JS/TS fit; spike vs HAPI. |
| **OpenMRS** | EMR platform | **MPL-2.0** `[VERIFIED]` LICENSE | 2.8.10 (2026-10-06) `[VERIFIED]` | Active | REST + FHIR module, Java API | Adjacent EMR (not a trial system) | Adjacent | **Do not adopt for trials**; note for low-resource/global sites. |
| **Bahmni** | OpenMRS-based hospital distribution | **MPL-2.0** (core) `[VERIFIED]`; components vary | bahmni-core 1.3.0 (2025-10-10); commits 2026-11-20 `[VERIFIED]` | Active (release lag) | REST (OpenMRS), Odoo ERP | Adjacent EMR | Adjacent | **Do not adopt.** |
| **Keycloak** | Identity, SSO, MFA, OIDC/SAML | **Apache-2.0** `[VERIFIED]` | 26.8.2 (2026-11-05) `[VERIFIED]` | Active | OIDC, SAML, Admin REST | No Yamicc equivalent described | Building block | **Reuse** for FR-001. |

### 3.7 Orchestration, pipelines and observability

| Component | Type / key capabilities | Licence | Latest release / commit (2026-11-21) | Maintenance | APIs / interop | Overlap with Yamicc | Verdict | Reuse decision |
|---|---|---|---|---|---|---|---|---|
| **Temporal** | Durable workflow orchestration | **MIT** `[VERIFIED]` | v1.32.2 (2026-11-02) `[VERIFIED]` | Active | gRPC + SDKs | Workflow across systems (FR-006) | Building block | **Preferred workflow engine** (FR-006). Permissive and code-first. |
| **Camunda** | BPMN/DMN workflow engine (8.x) | **Camunda License 1.0** (source-available, **not OSI**) except Apache-2.0 parts `[VERIFIED]` README; Camunda 7 was Apache-2.0 and is EOL `[GK]` | 8.10.10 (2026-11-18) `[VERIFIED]` | Active | REST/gRPC, BPMN/DMN | Workflow (FR-006) | Building block (non-OSI) | **Avoid for core.** Use only if BPMN modelling is mandatory, with legal review. |
| **Apache NiFi** | Flow-based data pipelines | **Apache-2.0** `[VERIFIED]` | 2.12.0 (2026-09-13) `[VERIFIED]` | Active | REST, flow files | ETL (FR-042) | Building block | **Optional ETL**; heavier than needed for MVP. |
| **Airbyte** | Data integration/connectors | **ELv2** (platform, not OSI) + MIT connectors `[VERIFIED]` LICENSE | v2.0.0 (2025-10-15); commits 2026-11-21 `[VERIFIED]` | Active | Connector API | ETL (FR-042) | Building block (non-OSI) | **Avoid embedding.** Self-host as a separate service if connector breadth wins; ELv2 forbids a hosted-service offering. |
| **OpenTelemetry Collector** | Telemetry (traces/metrics/logs) | **Apache-2.0** `[VERIFIED]` | v0.165.0 (2026-11-06) `[VERIFIED]` | Active | OTLP | Integration monitoring (FR-045) | Building block | **Reuse** (FR-045). |

### 3.8 UI, forms and admin

| Component | Type / key capabilities | Licence | Latest release / commit (2026-11-21) | Maintenance | APIs / interop | Overlap with Yamicc | Verdict | Reuse decision |
|---|---|---|---|---|---|---|---|---|
| **Apache Superset** | BI/dashboards, SQL Lab, embedding | **Apache-2.0** `[VERIFIED]` | 6.1.0 (2026-05-13); commits 2026-11-21 `[VERIFIED]` | Active | REST API; SQL; embed SDK | Dashboards (FR-002) | Building block | **Preferred dashboard** (FR-002). Permissive embedding. |
| **Metabase** | BI/dashboards | **AGPL-3.0** (OSS edition); enterprise dir commercial `[VERIFIED]` LICENSE | v0.65.6 (2026-11-18) `[VERIFIED]` | Active | REST; embedding (some features commercial) | Dashboards (FR-002) | Building block (AGPL) | **Service boundary only**, or replace with Superset for an Apache-2.0 core. |
| **Form.io (formio.js)** | JSON form renderer | **MIT** (renderer/SDK) `[VERIFIED]`; the Form.io **server/platform is commercial** `[GK]`, verify | v5.7.0 tag; commits 2026-11-18 `[VERIFIED]` | Active | JSON forms; REST submission | eCRF rendering (FR-030/032, UI-004) | Building block | **Renderer only**; do not depend on the commercial Form.io server (FR-030). |
| **SurveyJS** | Form/survey library | **MIT** (survey-core/library) `[VERIFIED]` LICENSE; some products/add-ons may be commercial `[GK]` | v3.2.7 (2026-11-18) `[VERIFIED]` | Active | JSON schema; framework wrappers | eCRF rendering (FR-030/032) | Building block | **Strong candidate** for UI-004 (FR-030). |
| **LHC-Forms** (NLM) | FHIR Questionnaire renderer | **NLM custom BSD-style terms** + LOINC/UCUM terms `[VERIFIED]` LICENSE.md | 44.3.1 tag; commits 2026-11-19 `[VERIFIED]` | Active | JS; FHIR Questionnaire | eCRF from FHIR Questionnaire (FR-030) | Building block | **Candidate** where FHIR Questionnaire is the source of truth (FR-030). |
| **React Admin** | React admin framework | **MIT** `[VERIFIED]` | v5.15.7 (2026-11-13) `[VERIFIED]` | Active | React; REST/GraphQL data providers | Admin UI (FR-001/005) | Building block | **Optional UI scaffold**; not a product differentiator by itself. |
| **Appsmith** | Low-code internal app builder | **Apache-2.0** `[VERIFIED]` | v2.7.2 (2026-11-19) `[VERIFIED]` | Active | Low-code UI; datasource connectors | None direct | Ignore | **Do not adopt** for the product. It undercuts the "no low-code lock-in" position (03 §4). Internal tooling only, if ever. |

---

## 4. Composition and licence-compatibility risks

1. **NFR-09 vs copyleft.** NFR-09 requires an OSI-approved core licence (e.g. Apache-2.0). Strong copyleft (GPL-3.0: OpenStudyBuilder, DataSHIELD, OpenSAFELY, tranSMART) and network copyleft (AGPL-3.0: Metabase; cBioPortal if pinned to an old tag) cannot be linked into that core. They are usable only as **separate services** or as **reference models**. `[INFERRED]`
2. **Non-OSI "open" traps.** REDCap, OncoKB, Airbyte (ELv2) and Camunda 8 (Camunda License 1.0) are commonly described as "open" but are **not OSI open source**. They must be treated as commercial/licence-gated integrations (see `license_register.md`). `[VERIFIED]`
3. **Relicensing is live, not theoretical.** cBioPortal moved AGPL-3.0 → Apache-2.0 in Oct 2026 and the latest *tagged* release is still AGPL. Pin commits/tags and record the licence at the pinned commit. `[VERIFIED]`
4. **Vocabulary licensing is separate from software licensing.** SNOMED CT, LOINC, UCUM, ICD-10/ICD-O-3 and NCIt each have their own terms (Athena only distributes them). Software reuse does not grant terminology rights. `[GK]`/`[VERIFIED]` for LOINC/UCUM terms inside LHC-Forms.
5. **Maintenance concentration.** Several OHDSI tools have slow release cadence (Achilles 2023, Usagi 2021, WhiteRabbit 2024) even with recent commits, and CIViC's server code is dormant. Pinning old releases increases CVE exposure. `[INFERRED]`
6. **Validation burden.** Every component that touches patient data must enter the SBOM and the NEN 7510 / ISO 27001 / Annex 11 evidence set (NFR-02, NFR-11). Reusing more components reduces build effort but increases third-party validation surface. This trade is for the CTO. `[INFERRED]`

---

## 5. Integration notes and spikes to run

| Decision needed | Options | Recommendation | Why | Spike owner |
|---|---|---|---|---|
| FHIR backend (FR-040/046) | HAPI FHIR vs Medplum | Spike both, decide on team language | HAPI is mature Java/JPA; Medplum is TypeScript/React and closer to the UI stack | CTO + Engineer |
| Form engine (FR-030/032, UI-004) | SurveyJS vs LHC-Forms vs Form.io renderer | Spike SurveyJS first, LHC-Forms if FHIR Questionnaire is canonical | MIT, active, no server lock-in | Engineer |
| Workflow (FR-006) | Temporal vs Camunda 8 | Temporal | MIT; Camunda 8 is non-OSI | CTO |
| Dashboards (FR-002) | Superset vs Metabase | Superset for embedded core | Apache-2.0 vs AGPL | Engineer |
| Federated analysis (FR-061) | vantage6 vs DataSHIELD | vantage6 | Apache-2.0, container algorithms, NL lineage | CTO |
| Study design (FR-010/014/016) | OpenStudyBuilder as service vs model-only | Model-only first; service if GPL is acceptable | GPLv3 overall | CTO + legal |
| EDC strategy (FR-036) | REDCap / OpenClinica / Castor / LogiqSuite integration | Integrate, never rebuild | 08 §5 do-not-duplicate rule | PM + CTO |

---

## 6. Resolutions of 03 §2 open items

| 03 §2 item flagged | Resolution (2026-11-21) |
|---|---|
| OpenStudyBuilder "verify maintenance and license" | **GPL-3.0 overall**, v2.12.0 (2026-11-20), **Active**. Copyleft — service boundary. `[VERIFIED]` |
| LibreClinica "check maintenance" | **LGPL-3.0**, v1.4.0rc1 (2025-06-13), commits 2026-11-18. RC-only, **Slowing**. `[VERIFIED]` |
| vantage6 "v5.x in 2026" | Tag **v5.1.0**; latest *published release* **v4.15.4 (2026-11-09)**. **Active**. `[VERIFIED]` |
| MOLGENIS `[GK]` | **LGPL-3.0**, 10.2.4 (2026-03-04), **Slowing**. `[VERIFIED]` |
| i2b2 / tranSMART "check activity" | i2b2 **MPL-2.0**, v1.8.3 (2026-07-01), **Active**. tranSMART **GPL-3.0**, **Dormant** (core 2024, ETL 2018). `[VERIFIED]` |
| Camunda "check license changes" | Camunda 8 = **Camunda License 1.0** (non-OSI); Camunda 7 Apache-2.0 but EOL. `[VERIFIED]` |
| OncoKB "licensing restrictions" | **Paid** for commercial, clinical reporting and API; free academic. `[VERIFIED]` |
| cBioPortal licence | **Apache-2.0 since Oct 2026**; latest tag v7.1.2 (2026-09-17) is **AGPL-3.0**. `[VERIFIED]` |

---

## 7. Confidence and change triggers

- **High confidence:** licence identity, version numbers and dates (primary sources; access date recorded).
- **Medium confidence:** maintenance bands (release/commit proxies; no contributor-health or security audit done).
- **Low–medium confidence:** operational fit and integration effort (no spike run in this task; T05 is desk research).
- **Triggers that would change the recommendation:** a component relicense (as cBioPortal did), a critical CVE, maintainer abandonment, a CTO choice to accept copyleft in core, or a spike showing an integration cost materially above estimate.

## 8. Open questions → D15 (T19)

1. Is a strong-copyleft core acceptable to the Board/legal, or is Apache-2.0/MIT mandatory for everything shipped? (Decides OpenStudyBuilder, DataSHIELD, OpenSAFELY.)
2. Does the project need OncoKB's paid clinical/API licence, or is CIViC sufficient for MVP? (Cost + FR-074.)
3. Which EDC do the first pilot hospitals already run (REDCap, Castor, OpenClinica, LogiqSuite)? This determines FR-036 integration priority.
4. Should cBioPortal be pinned to a post-Oct-2026 Apache-2.0 release, and who owns the licence-at-commit check in the SBOM?
5. Who owns SBOM + CVE monitoring + licence-at-pinned-commit for reused components (NFR-02/11)?
6. Is imaging (OHIF/XNAT) in scope before Phase 2, or defer (FR-078)?
7. Terminology licensing: which SNOMED CT affiliate/member route and LOINC/UCUM terms apply to the pilot (FR-043/073)?

---

## 9. Sources (access date 2026-11-21 unless stated)

### 9.1 Repository identifiers (`owner/repo`)

This table lets a reader re-verify every GitHub-hosted component. Non-GitHub components are marked.

| Component | Repository (`owner/repo`) | URL |
|---|---|---|
| OpenClinica CE | `OpenClinica/OpenClinica` | https://github.com/OpenClinica/OpenClinica |
| LibreClinica | `reliatec-gmbh/LibreClinica` | https://github.com/reliatec-gmbh/LibreClinica |
| OpenStudyBuilder | `NovoNordisk-OpenSource/openstudybuilder-solution` | https://github.com/NovoNordisk-OpenSource/openstudybuilder-solution |
| OMOP CommonDataModel | `OHDSI/CommonDataModel` | https://github.com/OHDSI/CommonDataModel |
| Atlas | `OHDSI/Atlas` | https://github.com/OHDSI/Atlas |
| WebAPI | `OHDSI/WebAPI` | https://github.com/OHDSI/WebAPI |
| Achilles | `OHDSI/Achilles` | https://github.com/OHDSI/Achilles |
| DataQualityDashboard | `OHDSI/DataQualityDashboard` | https://github.com/OHDSI/DataQualityDashboard |
| WhiteRabbit | `OHDSI/WhiteRabbit` | https://github.com/OHDSI/WhiteRabbit |
| Usagi | `OHDSI/Usagi` | https://github.com/OHDSI/Usagi |
| Athena | `OHDSI/Athena` | https://github.com/OHDSI/Athena |
| vantage6 | `vantage6/vantage6` | https://github.com/vantage6/vantage6 |
| DataSHIELD (dsBase) | `datashield/dsBase` | https://github.com/datashield/dsBase |
| OpenSAFELY job-runner | `opensafely-core/job-runner` | https://github.com/opensafely-core/job-runner |
| OpenSAFELY airlock | `opensafely-core/airlock` | https://github.com/opensafely-core/airlock |
| OpenSAFELY opencodelists | `opensafely-core/opencodelists` | https://github.com/opensafely-core/opencodelists |
| MOLGENIS | `molgenis/molgenis` | https://github.com/molgenis/molgenis |
| i2b2 core server | `i2b2/i2b2-core-server` | https://github.com/i2b2/i2b2-core-server |
| tranSMART | `transmart/transmartApp` | https://github.com/transmart/transmartApp |
| cBioPortal | `cBioPortal/cbioportal` | https://github.com/cBioPortal/cbioportal |
| igv.js | `igvteam/igv.js` | https://github.com/igvteam/igv.js |
| CIViC server | `griffithlab/civic-server` | https://github.com/griffithlab/civic-server |
| OHIF Viewer | `OHIF/Viewers` | https://github.com/OHIF/Viewers |
| HAPI FHIR | `hapifhir/hapi-fhir` | https://github.com/hapifhir/hapi-fhir |
| Medplum | `medplum/medplum` | https://github.com/medplum/medplum |
| OpenMRS core | `openmrs/openmrs-core` | https://github.com/openmrs/openmrs-core |
| Bahmni core | `Bahmni/bahmni-core` | https://github.com/Bahmni/bahmni-core |
| Keycloak | `keycloak/keycloak` | https://github.com/keycloak/keycloak |
| Temporal | `temporalio/temporal` | https://github.com/temporalio/temporal |
| Camunda | `camunda/camunda` | https://github.com/camunda/camunda |
| Apache NiFi | `apache/nifi` | https://github.com/apache/nifi |
| Airbyte | `airbytehq/airbyte` | https://github.com/airbytehq/airbyte |
| Apache Superset | `apache/superset` | https://github.com/apache/superset |
| Metabase | `metabase/metabase` | https://github.com/metabase/metabase |
| Form.io (formio.js) | `formio/formio.js` | https://github.com/formio/formio.js |
| SurveyJS | `surveyjs/survey-library` | https://github.com/surveyjs/survey-library |
| LHC-Forms | `LHNCBC/lforms` | https://github.com/LHNCBC/lforms |
| React Admin | `marmelab/react-admin` | https://github.com/marmelab/react-admin |
| Appsmith | `appsmithorg/appsmith` | https://github.com/appsmithorg/appsmith |
| OpenTelemetry Collector | `open-telemetry/opentelemetry-collector` | https://github.com/open-telemetry/opentelemetry-collector |
| REDCap | *not on GitHub* — Vanderbilt project pages | https://projectredcap.org/ |
| OncoKB | *not on GitHub* — MSK terms pages | https://www.oncokb.org/terms |
| XNAT | *not on GitHub* — NRG-hosted source; licence page | https://www.xnat.org/about/license.php |

### 9.2 Source list

- GitHub REST API: `repos/{owner}/{repo}` (licence, `pushed_at`), `releases/latest`, `tags`, `license`, `readme`, `contents` for every component above; identifiers in §9.1.
- REDCap licence terms: https://projectredcap.org/partners/termsofuse and https://projectredcap.org/join/ ; version example (secondary, not vendor): https://cb2.arizona.edu/services/redcap/redcap-version-changes
- XNAT licence: https://www.xnat.org/about/license.php ; download: https://download.xnat.org/
- OncoKB terms/licensing: https://www.oncokb.org/terms ; https://faq.oncokb.org/licensing
- vantage6 Zenodo record (cited in 03): https://zenodo.org/records/20810243
- cBioPortal licence statement: repository `README.md` (`cBioPortal/cbioportal`) — "cBioPortal is licensed under the Apache License 2.0. Versions released before October 2026 were licensed under AGPL-3.0."
- OpenStudyBuilder licence overview: repository root `LICENSE.md` (`NovoNordisk-OpenSource/openstudybuilder-solution`) — overall GPLv3, per-component `LICENSE.md`/`sbom.md` govern each component.
- LHC-Forms licence text: repository `LICENSE.md` (`LHNCBC/lforms`).
- Camunda licence: repository `README.md` (`camunda/camunda`).
- CIViC licence text: repository `LICENSE` on `master` (`griffithlab/civic-server`) — MIT.
- LibreClinica licence text: repository `LICENSE` on `master` (`reliatec-gmbh/LibreClinica`) — LGPL-3.0.

*All version/date facts come from the GitHub API or the vendor page named in the row; none are estimated.*

---

## 10. Corrections log (2026-11-21)

This log maps each QA item from CEL-1761 (T21 review of CEL-1732) to the change made in this revision and in `license_register.md`.

**Version used.** We started from the repo file `deliverables/D3_s2_open_source_assessments.md`, which was byte-identical to the CEL-1732 document `d3-s2-open-source-assessments` (revision 1, 2026-11-21T09:07:47Z). The finished file is identical to the updated CEL-1732 document (revision 2).

| QA item | Change made |
|---|---|
| **C1 (medium)** — no `owner/repo` per row; impossible to re-verify | Added **§9.1** with `owner/repo` and URL for every GitHub-hosted component. Corrected the two problematic identifiers: LibreClinica → `reliatec-gmbh/LibreClinica`; CIViC → `griffithlab/civic-server`. Updated the §2 method note to point to §9.1. |
| **C2 (minor)** — REDCap 17.5.11 is the Univ. of Arizona changelog, shown as `[VERIFIED]` | REDCap version cell now says "reported 2026-11-10 in the Univ. of Arizona REDCap changelog — secondary source, not vendor-confirmed" and is labelled `[GK]`. Register row #1 evidence updated to match. |
| **C3 (medium)** — register §4 terminology rows have no labels or URLs; SNOMED claim unsourced | Register §4 now carries an evidence label and a source URL per row. SNOMED claim corrected to "member/affiliate licensing; use in Member countries is free but registration with the National Release Center is required", sourced to https://www.snomed.org/get-snomed. |
| **C4 (minor)** — `[CLAIMED]` is not a 00 label | §2 now lists only the 00 labels (`[VERIFIED]`, `[CLAIMED-B]`, `[CLAIMED-C]`, `[GK]`, `[INFERRED]`). The `[CLAIMED]` definition is removed. REDCap's secondary-source version uses `[GK]`, not a new label. |
| **C5 (minor)** — OpenStudyBuilder `LICENSE` path 404 / API `NOASSERTION`; vantage6 tag oddity | OpenStudyBuilder evidence now quotes the exact path **repo root `LICENSE.md`**, explains that GitHub returns `NOASSERTION` because the file is `LICENSE.md` not `LICENSE`, and notes that per-component `LICENSE.md`/`sbom.md` files govern each component. The vantage6 "confirm v5.1.0 GA before pinning" caveat is retained in §3.3, §5, §6 and register #13. |
| **C6 (minor)** — OpenClinica CE last release 2024-08-02 (>27 months); "Slowing" may be too soft | OpenClinica CE maintenance cell now reads "Slowing (release >27 months old; commits only — arguably **Dormant** on release cadence)". Register row #2 unchanged on licence; the maintenance note is carried in the assessor verdict. |
| **C7 (medium-minor)** — register §5 does not name D15/T19 and omits three `[GK]` gaps | Register §5 now opens with a D15 (T19) pointer. It adds the three gaps: Form.io server terms, SurveyJS add-on terms, and CIViC data terms, all `[GK]`. D3 §8 already names D15 (T19) and is unchanged. |
| **Athena note** — register #12 class `E/F` conflicts with §3 summary (E only) | Register #12 is now class **E** (data, not software; upstream vocabulary terms), so #2 and §3 agree. D3 §3.2 verdict "Data source" is unchanged. |
| **Not changed** — live re-check of every row | QA spot-checked a subset on 2026-11-21 and found no wrong licence. This revision adds identifiers and labels; it does not re-fetch every release tag. A full automated re-fetch is proposed as a later SBOM task, not done here. |

