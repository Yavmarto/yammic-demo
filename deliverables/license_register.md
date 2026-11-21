# License Register — Open-Source and Third-Party Components (T05)

**Task:** T05 — Open-source component assessments (03 §2) incl. license + maintenance
**Output:** License register (companion to `D3_s2_open_source_assessments.md`)
**Prepared:** 2026-11-21 · **Evidence access date:** 2026-11-21
**Status:** Draft v2 — QA corrections applied (CEL-1761, C1–C7 + Athena note); resubmitted for focused T21 re-check
**Owners in spec:** Research + CTO · **Accountable agent:** Researcher

> This register covers the third-party software named in 03 §2. It records the licence as observed on 2026-11-21, the licence family, whether the licence is OSI-approved, the copyleft scope, and the recommended use mode against the project rule in NFR-09 (OSI-approved core, e.g. Apache-2.0). It is **not legal advice**; the Regulatory/Privacy/Security Lead (D11) and counsel must confirm before shipping.

---

## 1. How to read this register

**Risk class** (for embedding in a proprietary/Apache-2.0 core):

| Class | Meaning | Default use mode |
|---|---|---|
| **A — Permissive** | MIT / BSD / Apache-2.0. No copyleft. | Embed or link freely; keep notices. |
| **B — Weak copyleft** | MPL-2.0 (file-level) or LGPL-3.0 (library-level). | Embed with obligations; prefer a service boundary for LGPL. |
| **C — Strong copyleft** | GPL-3.0. Derivative works must be GPL. | Separate process/service only; never link into the core. |
| **D — Network copyleft** | AGPL-3.0. Network use triggers source offer. | Service boundary + source-availability plan; avoid embedding. |
| **E — Source-available / proprietary** | ELv2, Camunda License, EULA, paid terms. Not OSI open source. | External integration only; legal review; licence fee may apply. |
| **F — Custom permissive** | NLM terms, dual/mixed. | Treat as A after review. |

**OSI-approved** = the licence is on the Open Source Initiative list. "No" means the component is *not* open source even if its source is public.

**Licence-at-pinned-commit rule.** Record the SPDX licence of the exact commit/tag used. Relicensing happens (cBioPortal, Oct 2026). The SBOM must store the licence per pinned commit.

---

## 2. Register

| # | Component | Assessed version (2026-11-21) | SPDX licence | Family | OSI? | Copyleft / network scope | Commercial use | Key obligations | Risk class | Recommended use mode | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | REDCap | 17.5.x (17.5.11 reported 2026-11-10; secondary Univ. of Arizona changelog `[GK]`) | Vanderbilt Non-Profit EULA (no SPDX) | Proprietary | **No** | Contract terms | **No** for-profit self-host; non-commercial research only | Non-transferable; no sharing/redistribution; host only on Licensee-controlled servers; report stats | **E** | External EDC integration (FR-036); never bundled | projectredcap.org/join, /partners/termsofuse; version: cb2.arizona.edu changelog (secondary `[GK]`) |
| 2 | OpenClinica Community Edition | 3.17.2 (2024-08-02; release >27 months old; arguably **Dormant** on release cadence) | LGPL-3.0 | Weak copyleft | Yes | Library-level; modifications to the library must be shared | Yes | Provide LGPL source for modified library; allow relinking | **B** | Integrate the commercial edition via API (FR-036); CE not a core dep | GitHub `OpenClinica/OpenClinica` README |
| 3 | LibreClinica | v1.4.0rc1 (2025-06-13) | LGPL-3.0 | Weak copyleft | Yes | Library-level | Yes | As above | **B** | Defer; only for sites already running it | GitHub `reliatec-gmbh/LibreClinica` `LICENSE` (master) |
| 4 | OpenStudyBuilder | v2.12.0 (2026-11-20) | GPL-3.0 (overall; components vary) | Strong copyleft | Yes | Derivatives must be GPLv3 | Yes | Publish source of derivative works | **C** | Separate GPL service, or model-only reference (FR-010/014/016) | repo root `LICENSE.md` (GitHub API `license.spdx_id` = `NOASSERTION`; per-component `LICENSE.md`/`sbom.md` govern each component) |
| 5 | OMOP CommonDataModel | v5.5.0 (2026-08-25) | Apache-2.0 | Permissive | Yes | None | Yes | Notices; patent grant | **A** | Reuse (FR-065) | `DESCRIPTION` |
| 6 | OHDSI Atlas | v2.15.0 (2025-07-25) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Reuse/embed (FR-066) | GitHub license API |
| 7 | OHDSI WebAPI | v3.0.1 (2026-11-09) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Reuse (FR-066) | GitHub license API |
| 8 | OHDSI Achilles | v1.7.2 (2023-05-18) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Reuse with CVE monitoring (FR-064) | repo README |
| 9 | OHDSI DataQualityDashboard | v2.9.1 (2026-10-17) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Reuse (FR-064) | repo README |
| 10 | OHDSI WhiteRabbit (+Rabbit-in-a-Hat) | v1.0.0 (2024-08-05) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Reuse concepts; build review UI (FR-044) | GitHub license API |
| 11 | OHDSI Usagi | v1.4.3 (2021-04-09) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Reference only until replaced (FR-043/055) | repo README |
| 12 | OHDSI Athena (vocabularies) | repo 2026-09-02 | No repo licence; **upstream vocabulary terms** | Mixed / data | No (repo) | Vocabulary-specific | Depends on each vocabulary | SNOMED CT, LOINC, UCUM, ICD, NCIt terms apply | **E** (data, not software) | Use data under upstream terms only (FR-043/073) | `OHDSI/Athena` repo has no LICENSE; see §4 for terms |
| 13 | vantage6 | v5.1.0 tag / 4.15.4 (2026-11-09) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Preferred federated engine (FR-061) | GitHub license API |
| 14 | DataSHIELD (dsBase) | 6.3.5 (2026-02-22) | GPL-3.0 | Strong copyleft | Yes | Derivatives must be GPLv3 | Yes | Publish source of derivatives | **C** | Separate service only (FR-061) | `dsBase` LICENSE |
| 15 | OpenSAFELY (job-runner/airlock) | commits 2026-11-12 | GPL-3.0 | Strong copyleft | Yes | Derivatives must be GPLv3 | Yes | Publish source of derivatives | **C** | Reference model only (FR-063) | repo LICENSE |
| 16 | MOLGENIS | 10.2.4 (2026-03-04) | LGPL-3.0 | Weak copyleft | Yes | Library-level | Yes | Share library modifications; allow relinking | **B** | Optional registry component; service/dynamic use | GitHub license API |
| 17 | i2b2 (core server) | v1.8.3 (2026-07-01) | MPL-2.0 | Weak copyleft | Yes | File-level | Yes | Publish modifications to MPL files | **B** | Defer (FR-066 covered by Atlas) | repo LICENSE |
| 18 | tranSMART (transmartApp) | dormant (core 2024, ETL 2018) | GPL-3.0 | Strong copyleft | Yes | Derivatives must be GPLv3 | Yes | Publish source | **C** | Do not adopt | GitHub license API |
| 19 | cBioPortal | v7.1.2 (2026-09-17) → **AGPL-3.0**; main after Oct 2026 → **Apache-2.0** | AGPL-3.0 **or** Apache-2.0 depending on pinned commit | Network copyleft / Permissive | Yes | AGPL: network use triggers source offer | Yes | If AGPL: offer source to network users, publish modifications | **D** (old tags) / **A** (new) | Pin a post-Oct-2026 Apache-2.0 commit (FR-071/074/075) | repo README |
| 20 | igv.js | v3.8.9 (2026-10-11) | MIT | Permissive | Yes | None | Yes | Notices | **A** | Reuse (FR-075) | GitHub license API |
| 21 | CIViC (civic-server) | code dormant (2023-07); data current | MIT (code); data open | Permissive / data | Yes (code) | None (code) | Yes | Notices; data citation terms | **A** | Use public data/API, not server code (FR-074) | GitHub license API |
| 22 | OncoKB | data v7.6 (2026-09-30) | Proprietary (MSK terms) | Proprietary | **No** | Contract terms | **Paid** (commercial, clinical/reporting, API) | No redistribution; licence for API/clinical/commercial | **E** | Optional licence-gated data (FR-074) | oncokb.org/terms, faq.oncokb.org/licensing |
| 23 | OHIF Viewer | v3.13.15 (2026-11-19) | MIT | Permissive | Yes | None | Yes | Notices | **A** | Reuse Phase 2+ (FR-078) | GitHub license API |
| 24 | XNAT | 1.10.2 (2026) | BSD-2-Clause | Permissive | Yes | None | Yes | Notices | **A** | Defer Phase 2+ (FR-078) | xnat.org/about/license.php |
| 25 | HAPI FHIR | v9.0.0 (2026-11-18) | Apache-2.0 | Permissive | Yes | None | Yes | Notices; patent grant | **A** | Primary FHIR candidate (FR-040/046) | GitHub license API |
| 26 | Medplum | v5.2.18 (2026-11-20) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Alternative FHIR candidate (FR-040) | GitHub license API |
| 27 | OpenMRS (core) | 2.8.10 (2026-10-06) | MPL-2.0 | Weak copyleft | Yes | File-level | Yes | Publish modifications to MPL files | **B** | Adjacent only; do not adopt for trials | repo LICENSE |
| 28 | Bahmni (core) | 1.3.0 (2025-10-10) | MPL-2.0 | Weak copyleft | Yes | File-level | Yes | As above | **B** | Do not adopt | repo LICENSE |
| 29 | Keycloak | 26.8.2 (2026-11-05) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Reuse (FR-001) | GitHub license API |
| 30 | Temporal | v1.32.2 (2026-11-02) | MIT | Permissive | Yes | None | Yes | Notices | **A** | Preferred workflow engine (FR-006) | GitHub license API |
| 31 | Camunda (8.x) | 8.10.10 (2026-11-18) | Camunda License 1.0 (parts Apache-2.0) | Source-available | **No** | Contract terms | Restricted by licence | Verify production/enterprise limits; no OSI rights | **E** | Avoid for core (FR-006); legal review if BPMN required | repo README |
| 32 | Apache NiFi | 2.12.0 (2026-09-13) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Optional ETL (FR-042) | GitHub license API |
| 33 | Airbyte | v2.0.0 (2025-10-15) | ELv2 (platform) + MIT (connectors) | Source-available | **No** (platform) | ELv2 restrictions | Yes with limits | No hosted/managed-service offering; do not defeat licence keys | **E** | Separate service only; avoid embedding (FR-042) | repo LICENSE |
| 34 | Apache Superset | 6.1.0 (2026-05-13) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Preferred dashboard (FR-002) | GitHub license API |
| 35 | Metabase | v0.65.6 (2026-11-18) | AGPL-3.0 (OSS); commercial for enterprise | Network copyleft | Yes (OSS) | Network use triggers source offer | Yes | Offer source; publish modifications | **D** | Service boundary only, or use Superset (FR-002) | repo LICENSE |
| 36 | Form.io (formio.js) | v5.7.0 tag | MIT (renderer/SDK) | Permissive | Yes | None | Yes | Notices | **A** | Renderer only; Form.io server is commercial (`[GK]` verify) | GitHub license API |
| 37 | SurveyJS (survey-library) | v3.2.7 (2026-11-18) | MIT | Permissive | Yes | None | Yes | Notices | **A** | Candidate form engine (FR-030/032) | repo LICENSE |
| 38 | LHC-Forms (NLM) | 44.3.1 tag | NLM BSD-style + LOINC/UCUM terms | Custom permissive | Approx. yes (BSD-style) | None beyond attribution | Yes | Retain notices; comply with LOINC/UCUM terms | **F** | Candidate FHIR Questionnaire renderer (FR-030) | repo LICENSE.md |
| 39 | React Admin | v5.15.7 (2026-11-13) | MIT | Permissive | Yes | None | Yes | Notices | **A** | Optional UI scaffold | GitHub license API |
| 40 | Appsmith | v2.7.2 (2026-11-19) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** (licence) / **Ignore** (fit) | Do not adopt for product (low-code lock-in) | repo LICENSE |
| 41 | OpenTelemetry Collector | v0.165.0 (2026-11-06) | Apache-2.0 | Permissive | Yes | None | Yes | Notices | **A** | Reuse (FR-045) | GitHub license API |

---

## 3. Summary by risk class

| Class | Components | Action for CTO/legal |
|---|---|---|
| **A / F (safe to embed)** | OMOP CDM, Atlas, WebAPI, Achilles, DQD, WhiteRabbit, Usagi, vantage6, cBioPortal (post-Oct-2026), igv.js, CIViC code, OHIF, XNAT, HAPI FHIR, Medplum, Keycloak, Temporal, NiFi, Superset, Form.io renderer, SurveyJS, LHC-Forms, React Admin, Appsmith (licence only), OpenTelemetry | Add to SBOM; keep notices; standard approval. |
| **B (weak copyleft)** | OpenClinica CE, LibreClinica, MOLGENIS, i2b2, OpenMRS, Bahmni | Prefer service/dynamic use; publish modifications to MPL/LGPL files only. |
| **C (strong copyleft)** | OpenStudyBuilder, DataSHIELD, OpenSAFELY, tranSMART | Separate process/service; never link into the core. tranSMART: do not adopt. |
| **D (network copyleft)** | Metabase; cBioPortal old tags | Service boundary + source-offer plan; prefer Apache alternatives (Superset) or relicense path. |
| **E (non-OSI / proprietary)** | REDCap, Athena vocabularies, OncoKB, Camunda 8, Airbyte | Legal review; licence fee possible; external integration only; no bundling. |

---

## 4. Terminology and data-rights licences (not software)

These are **not** in the OSI register above and must be tracked separately. Every row now carries an evidence label and a source URL; access date 2026-11-21.

| Asset | Owner / terms | Constraint | Requirement | Evidence (label + source) |
|---|---|---|---|---|
| SNOMED CT | SNOMED International; member/affiliate licensing | Use in a Member country is free but must be registered with that country's National Release Center (NRC); affiliate licensing outside a Member country | FR-043/073 | `[VERIFIED]` https://www.snomed.org/get-snomed |
| LOINC | Regenstrief; free under the LOINC terms of use | Attribution; terms-of-use compliance | FR-043/073 | `[VERIFIED]` https://loinc.org/license/ |
| UCUM | Regenstrief Institute; UCUM Specification License v1.1 (June 2024) | Separate copyright/licence terms; keep the notice | FR-043 | `[VERIFIED]` https://ucum.org/license |
| ICD-10 / ICD-O-3 | WHO (ICD-O-3 with IARC) | WHO terms; ICD-O-3 for oncology morphology | FR-043/073 | `[VERIFIED]` https://www.who.int/standards/classifications/classification-of-diseases |
| NCIt | NCI Enterprise Vocabulary Services (EVS) | Generally open with attribution; confirm the current NCI terms | FR-073 | `[GK]` https://ncit.nci.nih.gov/ncitbrowser/pages/license.jsf |
| HGNC | HUGO Gene Nomenclature Committee | Data released under CC0 1.0 (public domain); attribution is community practice, not a licence condition | FR-071/073 | `[VERIFIED]` https://www.genenames.org/about/license/ |
| HGVS | HGVS Nomenclature contributors | Text under CC0 1.0; code and machine-readable artefacts under MIT | FR-071/073 | `[VERIFIED]` https://hgvs-nomenclature.org/stable/ |
| OMOP vocabularies via Athena | Upstream owners | Athena is distribution only; each vocabulary keeps its own terms | FR-043/065 | `[VERIFIED]` https://athena.ohdsi.org/ (distribution) + the asset rows above |

> **Do not** treat "Athena download" as a licence grant. It distributes third-party vocabularies under their own terms.
>
> SNOMED CT, LOINC and UCUM are separate assets with separate terms. Software reuse (for example LHC-Forms shipping UCUM/LOINC terms) does not grant terminology rights for the pilot data.

---

## 5. Open licence questions → D15 (T19)

These questions feed the open-decisions register in **D15 (T19)**. The §8 list in `D3_s2_open_source_assessments.md` is the companion set.

1. **Core licence policy:** is GPL/AGPL acceptable anywhere in the shipped product, or is Apache-2.0/MIT mandatory? This decides OpenStudyBuilder (C), DataSHIELD (C), OpenSAFELY (C) and Metabase (D).
2. **OncoKB and REDCap:** are paid/proprietary licences in budget if a pilot requires them? (Gate 3 covers spend.)
3. **cBioPortal pin:** which commit/tag will be used, and is it after the Oct 2026 Apache-2.0 relicense?
4. **SNOMED CT route:** which national Member/affiliate licence covers the pilot hospitals?
5. **SBOM ownership:** who records licence-at-pinned-commit and runs CVE monitoring (NFR-02/11)?
6. **ELv2 / Camunda:** are Airbyte or Camunda needed at all before Gate 2? If not, defer and avoid the legal work.
7. **Form.io server terms `[GK]`:** the `formio.js` renderer is MIT, but the Form.io server/platform licence (commercial) is unverified. Confirm before any dependency on the hosted platform.
8. **SurveyJS add-on terms `[GK]`:** `survey-core`/`survey-library` is MIT, but some products/add-ons may be commercial. Confirm which add-ons (if any) the form engine would use.
9. **CIViC data terms `[GK]`:** the `civic-server` code is MIT (and dormant); the data at civicdb.org is current, but the data reuse/citation terms are unverified. Confirm before ingesting CIViC data into a product.

---

## 6. Sources and method

- GitHub REST API (`license.spdx_id`, `releases/latest`, `tags`, `pushed_at`, `license` content) for every GitHub-hosted component, read 2026-11-21.
- Official pages: projectredcap.org (EULA), xnat.org (licence), oncokb.org (terms), faq.oncokb.org (licensing).
- Repository licence files: cBioPortal, OpenStudyBuilder, LHC-Forms, Camunda, Metabase, OpenMRS, Bahmni, i2b2, Airbyte, OpenSAFELY components, DataSHIELD dsBase, SurveyJS, Appsmith, Form.io.
- `[GK]` marks licence nuances that need confirmation before reliance (Form.io server terms, SurveyJS add-on terms, Athena/upstream vocabulary terms, CIViC data terms).

*This register records observed licence facts, not legal conclusions. Counsel/Regulatory (D11) must confirm before shipping.*

---

## 7. Repository identifiers (`owner/repo`)

This table lets a reader re-verify each row. Non-GitHub components are marked.

| # | Component | Repository (`owner/repo`) |
|---|---|---|
| 1 | REDCap | *not on GitHub* — https://projectredcap.org/ |
| 2 | OpenClinica CE | `OpenClinica/OpenClinica` |
| 3 | LibreClinica | `reliatec-gmbh/LibreClinica` |
| 4 | OpenStudyBuilder | `NovoNordisk-OpenSource/openstudybuilder-solution` |
| 5 | OMOP CommonDataModel | `OHDSI/CommonDataModel` |
| 6 | OHDSI Atlas | `OHDSI/Atlas` |
| 7 | OHDSI WebAPI | `OHDSI/WebAPI` |
| 8 | OHDSI Achilles | `OHDSI/Achilles` |
| 9 | OHDSI DataQualityDashboard | `OHDSI/DataQualityDashboard` |
| 10 | OHDSI WhiteRabbit | `OHDSI/WhiteRabbit` |
| 11 | OHDSI Usagi | `OHDSI/Usagi` |
| 12 | OHDSI Athena | `OHDSI/Athena` (repo has no `LICENSE`) |
| 13 | vantage6 | `vantage6/vantage6` |
| 14 | DataSHIELD (dsBase) | `datashield/dsBase` |
| 15 | OpenSAFELY | `opensafely-core/job-runner`, `opensafely-core/airlock`, `opensafely-core/opencodelists` |
| 16 | MOLGENIS | `molgenis/molgenis` |
| 17 | i2b2 (core server) | `i2b2/i2b2-core-server` |
| 18 | tranSMART | `transmart/transmartApp` |
| 19 | cBioPortal | `cBioPortal/cbioportal` |
| 20 | igv.js | `igvteam/igv.js` |
| 21 | CIViC (civic-server) | `griffithlab/civic-server` |
| 22 | OncoKB | *not on GitHub* — https://www.oncokb.org/terms |
| 23 | OHIF Viewer | `OHIF/Viewers` |
| 24 | XNAT | *not on GitHub* — NRG-hosted; https://www.xnat.org/about/license.php |
| 25 | HAPI FHIR | `hapifhir/hapi-fhir` |
| 26 | Medplum | `medplum/medplum` |
| 27 | OpenMRS (core) | `openmrs/openmrs-core` |
| 28 | Bahmni (core) | `Bahmni/bahmni-core` |
| 29 | Keycloak | `keycloak/keycloak` |
| 30 | Temporal | `temporalio/temporal` |
| 31 | Camunda | `camunda/camunda` |
| 32 | Apache NiFi | `apache/nifi` |
| 33 | Airbyte | `airbytehq/airbyte` |
| 34 | Apache Superset | `apache/superset` |
| 35 | Metabase | `metabase/metabase` |
| 36 | Form.io (formio.js) | `formio/formio.js` |
| 37 | SurveyJS (survey-library) | `surveyjs/survey-library` |
| 38 | LHC-Forms (NLM) | `LHNCBC/lforms` |
| 39 | React Admin | `marmelab/react-admin` |
| 40 | Appsmith | `appsmithorg/appsmith` |
| 41 | OpenTelemetry Collector | `open-telemetry/opentelemetry-collector` |

---

## 8. Corrections log (2026-11-21)

This log maps each QA item from CEL-1761 (T21 review of CEL-1732) to the change made in this register and in `D3_s2_open_source_assessments.md`.

| QA item | Change made |
|---|---|
| **C1 (medium)** — no `owner/repo` per row; impossible to re-verify | Added **§7** with `owner/repo` for all 41 rows (non-GitHub rows marked). Corrected LibreClinica → `reliatec-gmbh/LibreClinica` and CIViC → `griffithlab/civic-server`. |
| **C2 (minor)** — REDCap 17.5.11 is the Univ. of Arizona changelog, shown as verified | Row #1 now records "17.5.11 reported 2026-11-10; secondary Univ. of Arizona changelog `[GK]`" and names that source in the Evidence cell. |
| **C3 (medium)** — §4 terminology rows have no labels or URLs; SNOMED claim unsourced | §4 now has an Evidence column with a label and source URL per row. The SNOMED claim is corrected to member/affiliate licensing with NRC registration, sourced to https://www.snomed.org/get-snomed. |
| **C4 (minor)** — `[CLAIMED]` is not a 00 label | This register only used `[GK]`; no `[CLAIMED]` remains. D3 §2 now lists only the 00 labels (`[VERIFIED]`, `[CLAIMED-B]`, `[CLAIMED-C]`, `[GK]`, `[INFERRED]`). |
| **C5 (minor)** — OpenStudyBuilder `LICENSE` path 404 / API `NOASSERTION`; vantage6 tag oddity | Row #4 Evidence now cites **repo root `LICENSE.md`**, explains the GitHub `NOASSERTION`, and notes per-component `LICENSE.md`/`sbom.md`. The vantage6 "confirm v5.1.0 GA" caveat is retained. |
| **C6 (minor)** — OpenClinica CE last release 2024-08-02; "Slowing" may be too soft | Row #2 version cell now says "release >27 months old; arguably **Dormant** on release cadence". |
| **C7 (medium-minor)** — §5 does not name D15/T19 and omits three `[GK]` gaps | §5 now opens with a **D15 (T19)** pointer and adds items 7–9: Form.io server terms, SurveyJS add-on terms, and CIViC data terms, all `[GK]`. |
| **Athena note** — row #12 class `E/F` conflicts with §3 summary (E only) | Row #12 is now class **E** (data, not software; upstream vocabulary terms), so the row and §3 agree. |
| **Not changed** — live re-check of every row | QA spot-checked a subset and found no wrong licence. This revision adds identifiers and labels; it does not re-fetch every release tag. A full automated re-fetch is proposed as a later SBOM task. |

