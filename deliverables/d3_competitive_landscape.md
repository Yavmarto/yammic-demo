# D3 — Competitive & Ecosystem Landscape

**Part 1 of 3 — Commercial trial software (03 §1)**
Task: T04 · Owner: Research · Accountable agent: Researcher
Prepared: 21 November 2026 · Revised: 21 November 2026 (QA pass) · All sources accessed 2026-11-21 unless stated otherwise.

**Status of this document**
- §1 Commercial trial software — **complete in this revision** (T04).
- §2 Open-source / academic components + license register — owned by T05; not in this revision.
- §3 Data sources and networks + data-source register — owned by T06; not in this revision.
- Read 00 (rules), 02 (Yamicc intel), 03 (landscape) and 04 (requirements) before this document.

**Evidence labels** (from 00, with two additions used in this revision): [VERIFIED] public source supports the claim · [VERIFIED: advertised] the vendor publicly advertises the feature; this is not an independent test · [CLAIMED-VENDOR] vendor marketing claim, not independently confirmed · [CLAIMED-INSTITUTION] an institution's own press release or self-report; no independent study cited · [CLAIMED-SECONDARY] third-party aggregator or trade summary; not primary verification · [GK] general domain knowledge, verify before relying · [INFERRED] reasoning, not fact · [CONFLICT] sources disagree.

**Revision note (QA CEL-1731 review).** This revision adds full source URLs (S1–S52 in §9), corrects the Cori / Erasmus MC attribution (both tech.eu and Tech Funding News carry the sentence, but both attribute it to Cori, so it stays a vendor claim), relabels press-release and secondary-source figures, uses one primary verdict per row, rewords the Netherlands threat statement, removes the unsupported "two years ahead" and Verheul claims, fixes the NFR mapping, and corrects the C1–C6 reference.

---

## 0. Recommendation (read this first)

1. **Do not build an EDC, CTMS, eTMF or eISF.** The commercial market is mature, consolidated and cheaper to integrate than to displace. `FR-036` already requires integrating Castor, REDCap, OpenClinica and LogiqSuite; this research supports that choice. **Confidence: high.**
2. **Castor is the incumbent in Dutch academic research and therefore the competitor to beat, not a vendor to replace.** Six Dutch UMCs are listed as Castor users, including Erasmus MC — the Yamicc clinical anchor. Amsterdam UMC publishes an institutional licence and support process. [VERIFIED, S6, S7] Any Dutch go-to-market must assume Castor is already installed and politically entrenched. **Confidence: high.**
3. **"EHR-to-EDC automation" is no longer an empty gap; it is a funded product category.** OpenClinica Unite, IgniteData Archer, Medidata Health Record Connect/Rave Companion, Oracle Clinical Connector, Castor Catalyst and Paradigm's eSource all ship it in 2026. The remaining differentiation is narrower than 03 §4 assumes: **Dutch-language, evidence-linked extraction from Dutch EHR documents, inside the hospital trust boundary, with audit-grade review and a low-cost multi-site model.** **Confidence: medium-high.**
4. **Castor Catalyst is the single closest commercial threat to MVP B.** It already does protocol-aware extraction from source documents with a confidence score, source bounding boxes, human acceptance, and a claimed 99.16% reviewer acceptance rate in live studies across five countries. It is generic, not Dutch-EHR-native, and its Dutch-language performance is not public. **Confidence: medium-high on capability, low on Dutch fit.** [CLAIMED-VENDOR, S4]
5. **Cori Clinical is the closest analogue to Yamicc's protocol-AI partner and reports Erasmus MC as a customer.** It is early-stage (incorporated December 2024; USD 4M seed in October 2026) but credible (ISO/IEC 27001, GxP-aligned, regional hosting, two of the top five CROs claimed). Treat protocol authoring (`FR-019`) as **integrate/partner or defer, not build**. **Confidence: medium.** The Erasmus MC customer claim is Cori's own; both press reports repeat it without an independent record. [CLAIMED-VENDOR, S19, S20]
6. **Ignore the global enterprise CTMS/EDC suites (Medidata, Veeva, Oracle) for build decisions.** They set the capability bar and the integration interfaces, but they are not realistic competitors for a Dutch rare-cancer consortium and not realistic suppliers for a small academic team. **Confidence: high.**

**What would change these recommendations**
- If Castor exposes a documented partner API for third-party AI extraction *into* Castor EDC, and Catalyst performs acceptably on Dutch clinical text, then Recommendation 4 flips from "compete" to "integrate/co-sell".
- If IgniteData or OpenClinica announces a Dutch `HiX/ChipSoft` connector plus EU hosting, the whitespace in Recommendation 3 shrinks materially; MVP B should then emphasise review/audit/provenance rather than transfer.
- If a Dutch UMC mandates Castor-only procurement, integration-first becomes mandatory, not optional.
- If Yamicc demonstrates a real (non-mock) hospital Datahub connection, competitive urgency rises and the "mock-up" differentiator in 03 §4 weakens.
- If EU MDR classification of document-to-eCRF extraction is clarified as non-device, time-to-pilot shortens; if classified as device, MVP scope and cost change (see T15).

---

## 1. Scope, method and limits

**In scope (03 §1):** Castor; OpenClinica Enterprise/Unite; ORTEC Logiqcare LogiqSuite; Cori Clinical; Medidata Rave; Veeva Vault EDC/CTMS; Oracle Clinical One; Medrio; Viedoc; TrialKit; Florence Healthcare; IgniteData Archer; Epic research module; Flatiron; Tempus; Paradigm Health. Adjacent products named only in passing in 03 are noted in §1.5.

**Method:** vendor official sites and product pages first; regulator/academic sources second; independent analyst/comparison sources third. Where only secondary sources exist, the claim is marked and the limitation stated. Source IDs (S1–S52) resolve to full URLs in §9.

**Limits — read before using numbers**
- No vendor was contacted. Gate 0 forbids outreach without Board approval. All capability and accuracy figures are public claims, not tested.
- Commercial vendors do not publish release notes or commit history. "Maintenance status" below therefore means **latest public product/news evidence as of Nov 2026**, not a verified release date.
- Pricing is opaque except TrialKit's secondary-source summary. Do not treat any price in this document as a quote.
- This document profiles **vendors**, not Dutch hospital deployments. Per-hospital system facts belong in T06/T13.

---

## 2. Market map (verdicts at a glance)

Verdict vocabulary from 03: **Direct competitor · Adjacent · Building block · Data source · Ignore.** One primary verdict per row; secondary roles are in Notes.

| Vendor / product | Type | License | Status, Nov 2026 | Primary overlap with Yamicc | Verdict | Notes |
|---|---|---|---|---|---|---|
| **Castor** (EDC, eCOA, eConsent, Catalyst) | EDC/CDMS + AI extraction | Proprietary SaaS | Mature; active (Catalyst milestone Sep 2026) | EDC + source-document AI extraction; Dutch academic incumbent | **Direct competitor** | Integration target; do not displace (`FR-036`). Catalyst is the product to beat. |
| **OpenClinica** (Enterprise, Unite) | EDC + EHR-to-EDC | Proprietary; separate OSS community edition (T05) | Mature; Unite scaling since 2021 | EHR-to-EDC automation; mid-market EDC | **Direct competitor** | Best public benchmark for site activation and FHIR mapping; no Dutch customer found. |
| **ORTEC Logiqcare LogiqSuite** | Medical data management / eCRF | Proprietary SaaS (Azure EU) | Production; active (docs Nov 2025, news Oct 2026) | eCRF/ePRO for registries and trials; **Yamicc partner** | **Building block** | Integrate (`FR-036`); do not compete. Substitute for Castor inside the same account. |
| **Cori Clinical** | Protocol/study authoring AI | Proprietary SaaS | Early commercial; seed Oct 2026 | Protocol authoring/review; **Yamicc partner**; Erasmus MC reported customer | **Direct competitor** | Partner in the Yamicc stack; closest protocol-AI analogue. Erasmus MC claim is Cori's own. |
| **Medidata Rave** | Enterprise EDC/CDMS | Proprietary SaaS | Very mature; active | EDC; EHR-to-EDC via Companion | **Adjacent** | Capability benchmark; not a near-term Dutch rival or supplier. |
| **Veeva Vault EDC/CTMS** | Enterprise clinical suite | Proprietary SaaS | Very mature; active (eSource 2026) | EDC/CTMS/eTMF; site network | **Adjacent** | Integration target only if a sponsor mandates Veeva EDC. |
| **Oracle Clinical One** | Enterprise EDC + RTSM | Proprietary SaaS | Mature; active (EHR connector Aug 2025) | EDC + randomisation/supply | **Adjacent** | Capability and API benchmark. |
| **Medrio** | Mid-market EDC/CDMS | Proprietary SaaS | Mature; active | EDC for small/mid sponsors | **Adjacent** | Ignore for MVP; optional integration target. |
| **Viedoc** | Mid-market EDC suite | Proprietary SaaS | Mature; active (8,000+ studies claim) | EDC + ePRO/eTMF/RTSM | **Adjacent** | Pricing and UX benchmark; ignore for build. |
| **TrialKit** (Crucial Data Solutions) | Mobile-first EDC suite | Proprietary SaaS | Active; published pricing (secondary summary) | EDC + eCOA/eConsent/RTSM | **Adjacent** | Public cost anchor only; ignore for competition. |
| **Florence Healthcare** | eISF/eTMF/eConsent, site enablement | Proprietary SaaS | Mature; active (AI Sep–Oct 2026) | Site workflows, eISF, eConsent | **Adjacent** | Ignore for MVP; possible site-workflow partner later. |
| **IgniteData Archer** | EHR-to-EDC + notes extraction | Proprietary SaaS | Scale-up; active (Archer Intelligence 2026) | EHR→EDC transfer + unstructured-note extraction | **Direct competitor** | Best external benchmark for MVP B; not yet a Dutch market threat. |
| **Epic** (Research module, Discovery) | EHR platform | Proprietary | Mature; active | Source data, recruitment, trial linkage — not an EDC | **Data source** | Integration surface; never a build target. |
| **Flatiron Health** | Oncology RWD + OncoEMR | Proprietary | Mature; clinical research unit divested Dec 2025 | Oncology RWD, trial matching (US-centric) | **Data source** | Benchmark and possible RWD partner; ignore for MVP build. |
| **Tempus** | Clinico-genomic RWD/AI | Proprietary | Mature; active (Merck collab Mar 2026) | Biomarker/trial matching, RWD (US-centric) | **Data source** | Ignore for MVP; later genomics/matching modules only. |
| **Paradigm Health** | Oncology trial network + eSource | Proprietary | Scale-up; acquired Flatiron clinical research Dec 2025 | Multicentre oncology trial execution + EHR-integrated eSource (US) | **Adjacent** | US-only model to watch; not an EU competitor in 2026. |

**Reading the map:** Castor is the only near-term **direct competitor with a proven Dutch academic footprint**. OpenClinica and IgniteData are direct competitors in capability but show no Dutch customer evidence yet. Cori is a direct competitor for protocol AI and is reported to serve Erasmus MC. The other twelve are adjacent, building blocks or data sources: integration surfaces and benchmarks, not near-term Dutch rivals.

---

## 3. Vendor profiles

### 3.1 Castor — the Dutch incumbent

| Field | Assessment |
|---|---|
| **Type** | Cloud EDC/CDMS with native eCOA/ePRO, eConsent, RWE and AI extraction (Catalyst) |
| **License** | Proprietary SaaS [VERIFIED, S1, S2] |
| **Maintenance, Nov 2026** | Mature and actively shipping. Latest public evidence: Catalyst production milestone (3 Sep 2026); continuous product pages. No public release calendar. [VERIFIED, S2, S4] |
| **Company** | Founded 2012 in Amsterdam by Derk Arts MD PhD. [VERIFIED, S2] |
| **Scale (vendor claims)** | Homepage: 19,000+ studies, 900+ customers. About page: 31,900+ clinical studies, 9.5M+ participants, 70,000 investigator sites, 171 countries, 62,000+ researchers, 3,200+ publications. The vendor's own pages disagree on the study count; flag, do not reconcile silently. [CLAIMED-VENDOR; CONFLICT C1] |
| **Key capabilities** | Low-code eCRF builder; validation and edit checks; audit trail; eConsent with remote signature; eCOA/ePRO; randomisation; RWE/registry studies; Catalyst AI extraction. [VERIFIED: advertised, S1, S2, S5] |
| **Catalyst (critical)** | Reads paper, PDFs, scans, CSVs, EHR exports and FHIR feeds; protocol-aware extraction of structured fields; per-field confidence; source bounding boxes; human acceptance before values enter the eCRF; EDC edit checks applied at extraction. Direct-to-patient EHR retrieval is US-only (HIPAA release, TEFCA or FHIR). Live in production across five countries in RWE, PMCF and pivotal device studies; reviewers accepted 99.16% and overrode 0.78% of extracted values in one commercial study (14,290 values, 285 source files, 158 participants). [CLAIMED-VENDOR, S3, S4] |
| **APIs / integration** | Open REST API (`data.castoredc.com/api`); states alignment with HL7 FHIR; third-party analysis notes no specific CDISC export claim. API scopes for third-party write into eCRFs are not public. [VERIFIED/INFERRED, S1] |
| **Compliance** | FDA 21 CFR Part 11, EU Annex 11, GDPR, ISO 27001, ICH E6(R3), EU MDR 2017/745 (PMCF). [CLAIMED-VENDOR, S2] |
| **Dutch footprint** | Health-RI lists Castor at Amsterdam UMC, Erasmus MC, Leiden UMC, Maastricht UMC+, Radboudumc and UMC Utrecht. (UMCG uses REDCap as its mandatory EDC.) Amsterdam UMC publishes an institutional licence and support process. [VERIFIED, S6, S7] |
| **Yamicc relationship** | None found in public sources. No public endorsement or partnership evidence. [INFERRED from absence] |
| **Overlap with Yamicc** | High for eCRF/data capture and AI extraction; low for multi-hospital orchestration and federated data. Yamicc's LogiqSuite partnership means Castor and LogiqSuite are substitutes inside the same account. |
| **Verdict** | **Direct competitor** for EDC and document-to-eCRF automation. Integrate, do not displace (`FR-036`); treat Catalyst as the product to beat and as a possible partner. |

**Implication:** In any Dutch sales conversation, expect "we already have Castor". The honest answer is not "replace it" but "we feed it, review it, and audit it better, across hospitals".

---

### 3.2 OpenClinica — the EHR-to-EDC specialist

| Field | Assessment |
|---|---|
| **Type** | EDC/eClinical platform + Unite EHR-to-EDC |
| **License** | Proprietary Enterprise/Unite; a separate community edition exists (assess in T05 — do not conflate). [VERIFIED/INFERRED, S9] |
| **Maintenance, Nov 2026** | Mature, active. Unite marketed as live since 2021; product/blog activity through 2026. [VERIFIED, S9] |
| **Scale (vendor claims)** | 20+ years; 10,000+ studies and 100+ countries claimed. Unite: "450+ sites and 24 major health systems" (May 2025) and "450+ sites across 20+ major health systems" (Mar 2025). Counts are inconsistent across dates and definitions, not necessarily contradictory. Report "450+ sites". [CLAIMED-VENDOR, S13; CONFLICT C2] |
| **Key capabilities** | EDC, eConsent, eCOA, randomisation, recruitment, reporting; Unite pulls EHR data into any EDC/CRF; SMART on FHIR launch; major EHR support (Epic, Cerner); LOINC/SNOMED/ICD-10/RxNorm mapping. [VERIFIED: advertised, S9] |
| **Implementation claim** | Health-system mapping once, then sites activate in ~90 minutes; 15–20 hours hospital configuration. [CLAIMED-VENDOR, S9, S12] |
| **APIs / standards** | CDISC ODM-XML v1.3 with vendor extensions; REST APIs; XForms/XLSForm; FHIR R4; SAS/CSV/JSON export. [VERIFIED, S14] |
| **Compliance** | 21 CFR Part 11, EU Annex 11, ICH E6(R3), HIPAA/GDPR; SOC 2 Type II and ISO 27001 claimed in a secondary profile. [CLAIMED-VENDOR / CLAIMED-SECONDARY, S13] |
| **Dutch footprint** | No Dutch customer or HiX connector found in public sources. US-centric evidence base. [INFERRED from absence] |
| **Overlap with Yamicc** | High on the automation thesis, medium on EDC. Directly validates that "EHR-to-EDC at scale" is a real market, not a hypothesis. |
| **Verdict** | **Direct competitor** for MVP B. Benchmark for the site activation model and FHIR mapping. |

**Implication:** OpenClinica is the best public evidence that the value proposition works. It is also proof that the proposition is no longer unique.

---

### 3.3 ORTEC Logiqcare — LogiqSuite (Yamicc eCRF partner)

| Field | Assessment |
|---|---|
| **Type** | Medical data management platform: eCRF, ePRO, registries, cohorts, CDSS integration |
| **License** | Proprietary SaaS (Microsoft Azure, EU data residency). [VERIFIED, S15] |
| **Maintenance, Nov 2026** | Production, active. Public product and case pages updated 2025–2026. [VERIFIED, S15, S16] |
| **Key capabilities** | Configurable data models, eCRF, multilingual ePRO, real-time analytics (Power BI), attribute-based access control, prediction-model integration, care/research data linkage; used in multicentre registries and trials (e.g. RESOLVE, P4O2, AML-MRD, PROSPERA). [VERIFIED: advertised, S15] |
| **APIs / integration** | REST API for query and data ingress; CSV/JSON import/export; OIDC/SAML; EU Azure; TLS 1.2. [VERIFIED: advertised, S15] |
| **Compliance** | GDPR, GCP, ISO 27001, NEN 7510. [CLAIMED-VENDOR, S15] |
| **Yamicc relationship** | Named eCRF partner in the March 2026 Mendix demo (02 §3b). [VERIFIED via partner posts, 02] |
| **Overlap with Yamicc** | Complementary, not competitive: Yamicc supplies case management/orchestration; LogiqSuite supplies eCRF/ePRO. But it is also a substitute for Castor inside the same hospital. |
| **Verdict** | **Building block.** Integrate (`FR-036`); do not compete. |

See `deliverables/D2_appendix_partners.md` §3.1 (T03) for the Yamicc-side profile of this partner.

**Open question:** whether LogiqSuite's REST API supports *write* into eCRFs (not just ingest/query). Public docs show ingress and query; write scopes and partner terms are not public. This is decision-relevant for MVP B.

---

### 3.4 Cori Clinical — the protocol-AI analogue

| Field | Assessment |
|---|---|
| **Type** | AI workspace for trial design and authoring ("living blueprint") |
| **License** | Proprietary SaaS. [VERIFIED, S17] |
| **Maintenance, Nov 2026** | Early commercial, active. Incorporated December 2024 (London, per UK Companies House cited by Tech Funding News); USD 4M seed announced 7 Oct 2026; ISO/IEC 27001; GxP-aligned; regional hosting. [VERIFIED, S17, S20] |
| **Key capabilities** | Protocol and amendment drafting; ICF, CRF, CSR, CTD authoring; feasibility and site strategy; schedule of assessments; risk register; bid/budget linked to design; compliance review; decision records; Word add-in; registry and regulatory-guidance retrieval (FDA/EMA/MHRA/ICH); Scite evidence partnership. [VERIFIED: advertised, S17, S18] |
| **Standards** | Knowledge Hub mapped to CDISC USDM v4.0. [CLAIMED-VENDOR, S18] |
| **Evidence** | Internal evaluation: flagged 82% of protocol errors classed avoidable; estimated ≥33% set-up cost reduction (internal modelling, not independent). Customers include Erasmus MC (two neurosurgery/neuro-oncology trials) and two of the top five CROs. The Erasmus MC sentence appears in tech.eu and Tech Funding News, but both attribute it to Cori; no independent customer record found. [CLAIMED-VENDOR, S19, S20] |
| **Overlap with Yamicc** | Direct: Yamicc's protocol-authoring AI partner in the March 2026 demo. Also overlaps `FR-019` (AI-assisted protocol drafting) and parts of `FR-012`/`FR-056`. |
| **Verdict** | **Direct competitor** for protocol AI. Partner in the Yamicc stack; not a reason to build protocol authoring. |

See `deliverables/D2_appendix_partners.md` §3.2 (T03) for the Yamicc-side profile. Note the non-exclusivity: Cori also sells directly to Erasmus MC, as reported by Cori. [CLAIMED-VENDOR]

**Implication:** `FR-019` should be re-read as "integrate or defer", not "build". Cori has a shipping product and a reported Erasmus MC deployment; `FR-019` is not yet built.

---

### 3.5 Medidata Rave — the enterprise benchmark

| Field | Assessment |
|---|---|
| **Type** | Enterprise EDC/CDMS, core of the Medidata Platform |
| **License** | Proprietary SaaS. [VERIFIED, S21] |
| **Maintenance, Nov 2026** | Very mature, active. 26+ years in clinical use; 37K studies; 1.8M users; 700K+ certified site users; AI-assisted study build; Rave Lite tier. [CLAIMED-VENDOR, S21, S24] |
| **EHR-to-EDC** | Health Record Connect + Rave Companion; multi-standard connectivity (FHIR, C-CDA, DICOM, HL7, HIEs); no site-by-site setup; forms up to 90% faster; connectivity to 90%+ of top US research sites; CRIO integration for eSource. [CLAIMED-VENDOR, S22, S23] |
| **APIs / integration** | Platform integrations with eConsent, eCOA, RTSM, imaging; Clinical Data Studio; no public open-API scope for third-party eCRF automation. [INFERRED] |
| **Dutch footprint** | Global enterprise; no specific Dutch academic evidence found. Used mainly by pharma/CRO-sponsored trials, not investigator-initiated academic studies. [INFERRED] |
| **Overlap with Yamicc** | Medium: same data-capture function, different buyer. |
| **Verdict** | **Adjacent.** Benchmark for AI-assisted build and EHR connectivity; not a near-term competitor or supplier. |

---

### 3.6 Veeva Vault EDC / CTMS — enterprise suite and site network

| Field | Assessment |
|---|---|
| **Type** | Enterprise clinical operations + data suite (EDC, CTMS, eTMF, RTSM, eCOA, SiteVault) |
| **License** | Proprietary SaaS on Vault. [VERIFIED, S25] |
| **Maintenance, Nov 2026** | Very mature, active. 100+ customers; 8 of top 20 biopharmas; SiteVault 11,000+ research sites; Veeva ID 88,000+ monthly users; AI "Falcon" agents for clinical operations; Veeva eSource and 45-minute study-build ambition. [CLAIMED-VENDOR / trade press, S25] |
| **Key capabilities** | Common data model across CTMS/EDC/eTMF; real-time protocol-deviation flow; site payments; study start-up; SiteVault free eISF for sites; study suite packaging. [VERIFIED: advertised, S25, S26] |
| **APIs / integration** | Vault connections; standardised inter-application flows; not an open partner surface for third-party EDC replacement. [INFERRED] |
| **Dutch footprint** | Enterprise pharma/CRO; no Dutch academic evidence found. [INFERRED] |
| **Overlap with Yamicc** | Low for the rare-cancer academic consortium; high for sponsor-facing operations. |
| **Verdict** | **Adjacent.** Integration target only if a sponsor mandates Veeva EDC. Do not build against it. |

---

### 3.7 Oracle Clinical One — EDC + RTSM

| Field | Assessment |
|---|---|
| **Type** | Unified EDC/data collection + randomisation and trial supply (RTSM) |
| **License** | Proprietary SaaS on Oracle Cloud Infrastructure. [VERIFIED, S27] |
| **Maintenance, Nov 2026** | Mature, active. EHR interoperability via AI-enabled Oracle Clinical Connector (Aug 2025); document upload at subject level; safety integration; Everest Group Leader in EDC (2024). [VERIFIED: advertised, S27] |
| **APIs / integration** | Public REST API reference and Digital Gateway for integrations; CDISC ODM; CDISC LAB intake. Public Part 11 statement and study/customer counts are missing. [VERIFIED, S27, S28] |
| **Overlap with Yamicc** | Low-medium: enterprise EDC and supply; not the academic multi-site niche. |
| **Verdict** | **Adjacent.** Capability and API benchmark only. |

---

### 3.8 Medrio — mid-market EDC

| Field | Assessment |
|---|---|
| **Type** | EDC/CDMS with ePRO, eConsent, RTSM |
| **License** | Proprietary SaaS. [VERIFIED, S29] |
| **Maintenance, Nov 2026** | Mature, active. 20+ years, 11K studies deployed, 65K sites across 30+ countries; no-code build; offline capture; mid-tier analytics. [CLAIMED-VENDOR, S29] |
| **Compliance** | 21 CFR Part 11, ICH E6(R2), HIPAA, GDPR. [CLAIMED-VENDOR, S29] |
| **Pricing** | Quote-based; secondary sources describe it as higher than Viedoc. No public list price. [INFERRED] |
| **Overlap with Yamicc** | Low: EDC only; no multi-hospital orchestration or Dutch EHR focus. |
| **Verdict** | **Adjacent.** Ignore for MVP; optional integration target. |

---

### 3.9 Viedoc — European mid-market EDC

| Field | Assessment |
|---|---|
| **Type** | EDC suite with ePRO, eTMF, RTSM, Televisits |
| **License** | Proprietary SaaS; study-based licensing with unlimited users. [VERIFIED, S30] |
| **Maintenance, Nov 2026** | Mature, active. 8,000+ completed studies, 75+ countries; go-live in as little as 8 weeks; 24/6/365 support; 100% FDA inspection pass rate claimed. [CLAIMED-VENDOR, S31] |
| **Pricing** | Modular, study-based, no per-seat fee; no public list prices. [VERIFIED, S30] |
| **Overlap with Yamicc** | Low-medium: European academic/CRO EDC; no Dutch EHR automation. |
| **Verdict** | **Adjacent.** Pricing and UX benchmark; ignore for build. |

---

### 3.10 TrialKit (Crucial Data Solutions) — published pricing benchmark

| Field | Assessment |
|---|---|
| **Type** | Mobile-native EDC with eCOA/ePRO, eConsent, RTSM, eTMF, AI analytics |
| **License** | Proprietary SaaS. [VERIFIED, S32] |
| **Maintenance, Nov 2026** | Active. Unified suite; offline mobile capture; AWS EU (Ireland, Paris) and US regions. [VERIFIED: advertised / CLAIMED-SECONDARY, S32, S33] |
| **Pricing** | Published subscription: from USD 1,350/month for one live study to USD 90,000/month for unlimited concurrent studies. [CLAIMED-SECONDARY, S33, rfp.wiki summary of vendor/press materials; confirm before quoting] |
| **Overlap with Yamicc** | Low: EDC suite only. |
| **Verdict** | **Adjacent.** Use only as a public cost anchor for build-vs-buy (T16). Ignore for competition. |

---

### 3.11 Florence Healthcare — site enablement and eISF

| Field | Assessment |
|---|---|
| **Type** | eISF/eBinders, eTMF, eConsent, SiteLink, remote monitoring, site feasibility |
| **License** | Proprietary SaaS. [VERIFIED, S34] |
| **Maintenance, Nov 2026** | Mature, active. AI Site Feasibility live since Sep 2026; DocQC; agentic roadmap announced Oct 2026. [VERIFIED, S34, S35] |
| **Scale (vendor claims)** | "65,000+ sites" (homepage), "12,000+ sites activated in 45 countries" (site-conduct page), "88,000+ sites" (eConsent page). Different definitions, not reconcilable from public pages; flag. [CONFLICT C3, S34, S35] |
| **Key capabilities** | Digitised regulatory binders; version control; Part 11/Annex 11 eSignatures; remote monitoring and source review; eTMF sync; eConsent; site feasibility. [VERIFIED: advertised, S34, S35] |
| **Overlap with Yamicc** | Low for MVP B; medium for site-start-up and monitoring workflows (`FR-028`, `FR-069`). |
| **Verdict** | **Adjacent.** Ignore for MVP; candidate site-workflow partner later. |

---

### 3.12 IgniteData Archer — closest functional analogue to MVP B

| Field | Assessment |
|---|---|
| **Type** | EHR-to-EDC / eSource-to-sponsor transfer, plus unstructured-note extraction |
| **License** | Proprietary SaaS; no data retained after transfer. [VERIFIED, S36] |
| **Maintenance, Nov 2026** | Scale-up, active. Archer Intelligence launched 2026; Lilly/Veeva integration; AACI webinar Oct 2026; Microsoft case Nov 2026. [VERIFIED, S36, S39, S40] |
| **Key capabilities** | HL7 SMART on FHIR; system-agnostic across Epic, OncoEMR, Oracle Health, Advarra, Veeva, Medidata, Castor, Cisiv; study-specific mapping with LOINC/SNOMED; human-in-the-loop; no new PHI repository; Archer Intelligence extracts from notes/reports with source evidence and CRC confirmation, purpose-built models, no external AI services. [VERIFIED: advertised, S36, S37, S39] |
| **Implementation** | Site connection in <90 minutes; broader onboarding weeks. [CLAIMED-VENDOR, S41] |
| **Evidence** | Mount Sinai Tisch Cancer Center: all 16 disease groups, ~70% of eCRF data auto-populated, entry time 5.5 → 2.5 min/visit, 100% accuracy, 0% re-query (Oct 2026). Memorial Sloan Kettering and Lilly cited. Vendor claims 89% fewer queries, 85% faster time-to-data. [CLAIMED-INSTITUTION for Mount Sinai; CLAIMED-VENDOR for the rest, S38, S40] |
| **Footprint** | 4 continents, 6 countries, hundreds of sites; US/UK centred. No Dutch hospital or HiX evidence found. [VERIFIED/INFERRED, S36] |
| **Overlap with Yamicc** | Very high on the automation thesis; high on AI note extraction; low on Dutch/EU data residency and multi-hospital research orchestration. |
| **Verdict** | **Direct competitor** in concept. Best external benchmark for MVP B; not yet a Dutch market threat. |

**Implication:** Archer proves the workflow and the economics (70% auto-population, ~55% time reduction). It does **not** prove Dutch-language performance, HiX connectivity, EU hosting, or academic multi-site governance — the three things a Dutch MVP can still own. The Mount Sinai figures are an institution self-report; no study or audit method is cited. [CLAIMED-INSTITUTION]

---

### 3.13 Epic — EHR platform and integration surface

| Field | Assessment |
|---|---|
| **Type** | EHR; Research module; Discovery life-sciences platform; Cosmos de-identified dataset (US) |
| **License** | Proprietary; licensed per organisation. [VERIFIED, S42] |
| **Maintenance, Nov 2026** | Mature, active. [VERIFIED, S42] |
| **Research capabilities** | Study records (RSH); patient-to-study linkage; recruitment (MyChart, BPAs); eConsent; PRO questionnaires; SlicerDicer cohort/feasibility; research billing; integrations with OnCore; FHIR APIs; Cosmos. [VERIFIED: advertised, S42] |
| **Yamicc relevance** | Not an EDC and not a competitor. It is the most important **source system and channel** where installed (`FR-041`). Dutch footprint differs by hospital: verify per site; `HiX/ChipSoft` is also material in NL (see 03 §4 and T06/T13). [INFERRED] |
| **Verdict** | **Data source.** Integration surface; never a build target. |

---

### 3.14 Flatiron Health — oncology RWD benchmark

| Field | Assessment |
|---|---|
| **Type** | Oncology RWD/RWE, OncoEMR, Telescope analytics |
| **License** | Proprietary; Roche subsidiary. [VERIFIED, S43] |
| **Maintenance, Nov 2026** | Mature, active. Telescope launched May 2026; 6M+ research-ready patient records across US/UK/DE/JP; 2,000+ publications; 45+ regulatory decisions informed. [CLAIMED-VENDOR, S43, S44] |
| **Structural change** | Divested its Clinical Research Business to Paradigm Health (announced 4 Dec 2025); multi-year partnership to integrate Paradigm into OncoEMR. [VERIFIED, S45] |
| **Overlap with Yamicc** | RWD and trial matching, not prospective multi-hospital trial execution in NL. |
| **Verdict** | **Data source.** Useful for benchmarking and possible RWD partnership; ignore for MVP build. |

---

### 3.15 Tempus — clinico-genomic RWD and matching

| Field | Assessment |
|---|---|
| **Type** | Diagnostics + clinico-genomic data + AI; trial matching and RWE |
| **License** | Proprietary; data licensing and sponsored research. [VERIFIED, S47] |
| **Maintenance, Nov 2026** | Mature, active. Merck strategic collaboration announced 3 Mar 2026. [VERIFIED, S46] |
| **Overlap with Yamicc** | Biomarker-stratified research, companion diagnostics, trial matching; US-centric, sequencing-derived cohorts. |
| **Verdict** | **Data source.** Ignore for MVP; relevant only to later genomics/matching modules (`FR-074`–`FR-076`). |

---

### 3.16 Paradigm Health — US oncology trial network + eSource

| Field | Assessment |
|---|---|
| **Type** | Tech-enabled oncology trial network, AI patient matching, site feasibility, EHR-integrated eSource |
| **License** | Proprietary. [VERIFIED, S48] |
| **Maintenance, Nov 2026** | Scale-up, active. Two separate announcements on 4 Dec 2025: a USD 78M Series B and the acquisition of Flatiron's clinical-research business. Network: 45 US states, 166 provider organisations, 123 community oncology practices, 43 health systems/AMCs. [VERIFIED, S48, S49] |
| **Evidence** | Prospective observational study (J&J-sponsored, four community sites; Ghanim et al., npj Health Systems, DOI 10.1038/s44401-025-00066-9): 91% of essential data points were eligible for automated transfer; 67% were actually transferred through the EHR-to-EDC connector; completeness was >99% (0.59% missing); median structured-data transfer 1.7 days; query rate <2% for transferred data vs 5.2% manual. The vendor release's ">99%" wording does not distinguish transfer rate from completeness; this document uses the paper's figures. [VERIFIED, peer-reviewed paper S52; vendor summary S50] |
| **Conflict** | Founding year stated as 2021 (trade press) and "launched 2023 with USD 203M Series A" (MobiHealthNews). Flag; not decision-relevant. [CONFLICT C4, S51] |
| **Overlap with Yamicc** | Conceptual: multicentre oncology trial execution with embedded eSource. Geographic: US only. |
| **Verdict** | **Adjacent.** US-only model to watch; not an EU competitor in 2026. The strongest signal that "trial network + eSource + AI matching" is a funded model. |

---

## 4. Cross-cutting findings

### 4.1 EHR-to-EDC has moved from pilot to product (2025–2026)
- OpenClinica Unite: live since 2021, 450+ sites/24 health systems claimed. [CLAIMED-VENDOR, S9, S10]
- IgniteData Archer: Mount Sinai all 16 disease groups, 70% auto-population, 5.5 → 2.5 min/visit. [CLAIMED-INSTITUTION, S38]
- Medidata: Companion + Health Record Connect, 90% faster form completion claim. [CLAIMED-VENDOR, S22, S23]
- Oracle: Clinical Connector, Aug 2025. [VERIFIED: advertised, S27]
- Paradigm/Flatiron: 91% of data points eligible for automated transfer, 67% actually transferred, >99% completeness in a community-oncology study. [VERIFIED, peer-reviewed paper S52]
- Castor Catalyst: 99.16% acceptance across five countries. [CLAIMED-VENDOR, S4]

**Consequence:** 03 §4's "biggest real gap" is now a contested category, not whitespace. The defensible gap is narrower: **Dutch-language documents, Dutch EHR connectors, hospital-side processing, academic multi-site governance, and price**.

### 4.2 AI extraction is table stakes; human review is the norm
Every serious vendor now pairs extraction with a human acceptance step, confidence or evidence, and an audit trail. Vendors that skip evidence linkage will lose regulated deals. **Consequence:** evidence spans (`FR-051`), abstention (`FR-053`) and traceability (`FR-058`) are not differentiators by themselves — they are entry requirements. The differentiator is **quality on Dutch clinical text and reviewer time saved**, measured per field.

### 4.3 Consolidation and capital gravity
- Paradigm acquired Flatiron's clinical-research business (announced 4 Dec 2025).
- Paradigm separately raised a USD 78M Series B (announced 4 Dec 2025; C5 notes a USD 77M figure in one source).
- Cori raised USD 4M seed (Oct 2026).
- Veeva, Medidata and Oracle are bundling EDC + CTMS + eTMF + eSource + AI into suites.
- Castor is expanding from EDC into AI extraction and RWE.

**Consequence:** standalone point tools are being absorbed. A small platform should be an **orchestration/integration layer with a sharp AI capability**, not another suite.

### 4.4 The Dutch academic market is Castor's home turf
Six UMCs are listed as Castor users; Amsterdam UMC has an institutional licence and a published support process. Switching costs are organisational, not technical. **Consequence:** integration (`FR-036`) is the only realistic entry; "replace Castor" is a losing pitch.

### 4.5 Pricing is opaque, and that is a market feature
Only TrialKit has a published price band, and even that is a secondary summary (USD 1,350–90,000/month). [CLAIMED-SECONDARY, S33] Castor publishes a pricing *process* but no numbers. Viedoc publishes a licensing *model* but no numbers. **Consequence:** T16 must use public tender documents and institutional licence evidence, not vendor websites, for cost anchors. Do not put invented prices in D12.

### 4.6 EU data residency is a live selling point
Cori (regional hosting), LogiqSuite (EU Azure), Viedoc (EU), TrialKit (EU AWS), Castor (EU/US storage) all market it. IgniteData's and most US vendors' EU posture is less clear. **Consequence:** EU-only hosting (`NFR-02`, `NFR-07`) is a real advantage in Dutch procurement, not a compliance checkbox.

---

## 5. What this means for the platform (mapped to requirements)

| Decision | Recommendation | Requirements |
|---|---|---|
| EDC / eCRF | **Integrate** Castor/LogiqSuite/OpenClinica; do not build | `FR-036`, `FR-035` |
| EHR-to-EDC transfer | **Build only the Dutch-specific layer**; reuse FHIR patterns proven by Unite/Archer | `FR-040`–`FR-046` |
| Document → eCRF extraction | **Build**, with evidence spans, abstention, reviewer UI and audit; benchmark against Catalyst and Archer | `FR-050`–`FR-054`, `FR-058`, `FR-059` |
| Protocol authoring | **Integrate/partner (Cori) or defer** | `FR-019`, `FR-012`, `FR-056` |
| CTMS / eTMF / eISF | **Do not build**; integrate later if a pilot demands it | `FR-002`, `FR-028`, `FR-069` |
| Oncology RWD / matching | **Defer**; T06 and T14 own the data and model choices | `FR-074`–`FR-076` |
| Deployment | **EU-only, hospital-side processing** as a differentiator | `NFR-02`, `NFR-07` |

---

## 6. Watch list and triggers

| Watch item | Why it matters | Trigger that changes our plan | Owner |
|---|---|---|---|
| Castor Catalyst Dutch performance + evidence spans | Closest threat to MVP B | Demo or public evidence of Dutch note extraction with spans | Research (Gate 0 for briefing) |
| Castor partner/API programme for third-party extraction | Could turn competitor into channel | Public partner docs or API scopes for eCRF write | Research + CTO |
| IgniteData EU/NL expansion and HiX support | Would shrink whitespace | EU hosting + HiX connector announcement | Research |
| OpenClinica Unite EU/NL deployment | Same | Dutch site or HiX/Epic NL reference | Research |
| Cori Clinical growth and Erasmus MC expansion | Protocol AI becomes entrenched | Multi-site NL customer or bundled with Yamicc | Research |
| Paradigm/Flatiron EU expansion | US model could enter EU | EU site network or EU data residency | Research |
| EU AI Act / MDR classification of extraction | Changes cost and timeline | Guidance or notified-body position | Regulatory (T15) |

---

## 7. Open questions for D15 (T19)

1. Does Castor offer a documented partner API for third-party AI extraction *into* Castor EDC, and on what commercial terms? **Needs vendor briefing; Gate 0 approval required.**
2. Does LogiqSuite's REST API support authenticated *write* into eCRFs, or only query/ingress? **Public docs insufficient; ask ORTEC under Gate 0.**
3. Which Dutch hospitals in scope run Epic vs HiX/ChipSoft, and which expose FHIR R4 today? **T06/T13.**
4. Is IgniteData available in the EU/NL, and does Archer support HiX? **Public sources silent; Gate 0.**
5. What is Castor Catalyst's measured accuracy on Dutch clinical text, and does it preserve evidence spans? **No public Dutch evidence.**
6. What are realistic institutional licence price bands for Castor, OpenClinica and Viedoc in NL? **Use public tender/award documents, not vendor sites.**
7. Is document-to-eCRF extraction a medical device under EU MDR for our intended purpose? **T15.**

---

## 8. Conflicts flagged (not hidden)

| # | Conflict | Sources | Handling |
|---|---|---|---|
| C1 | Castor study count | 19,000+ studies (homepage) vs 31,900+ studies (about page) | Vendor's own pages disagree; different definitions and snapshot dates. Cite the dated page; do not average. |
| C2 | OpenClinica Unite network size | 450+ sites / 20+ systems (Mar 2025) vs 450+ sites / 24 systems (May 2025) | Different dates and definitions; inconsistent or not comparable, not a true conflict. Report "450+ sites" and note the system count moved from 20+ to 24. |
| C3 | Florence site count | 12,000 activated vs 65,000+ sites vs 88,000+ network | Different definitions; use "tens of thousands". |
| C4 | Paradigm founding year | 2021 (trade press) vs launched 2023 (MobiHealthNews) | Not decision-relevant; flag only. |
| C5 | Paradigm funding | USD 78M (company release) vs USD 77M (STAT) | Use primary source; note discrepancy. |
| C6 | Viedoc study count | 8,000+ completed studies vs 7,000+ studies in 75+ countries (two vendor pages) | Different dates; cite "7,000–8,000+" or the dated page. |

---

## 9. QA handoff (T21)

**Revision 2 (21 Nov 2026) — QA fixes applied:**
- Full source URLs added as S1–S52, each with access date; vendor claim rows now point to a concrete page.
- Cori / Erasmus MC re-checked: the sentence is in both tech.eu (S19) and Tech Funding News (S20), but both attribute it to Cori. Kept as [CLAIMED-VENDOR]; no independent customer record found.
- Press-release and secondary figures relabelled: Mount Sinai → [CLAIMED-INSTITUTION]; Paradigm study → [VERIFIED] against the located peer-reviewed paper (S52), with the vendor release's ">99%" wording corrected to the paper's 67% transfer rate; TrialKit pricing → [CLAIMED-SECONDARY]; vendor feature lists → [VERIFIED: advertised].
- Verdicts reduced to one primary word per row; partner/benchmark/watch roles moved to Notes.
- §2 Netherlands threat sentence reworded; "two years ahead" and the Verheul/VUmc inference removed.
- §5 NFR mapping corrected to `NFR-02`/`NFR-07` for deployment; `NFR-09` removed from that row.
- §8 conflict range corrected to C1–C6; C2 reworded as "inconsistent or not comparable".
- Paradigm's USD 78M round and Flatiron deal split into separate statements.

**Requested review focus:**
- Every vendor claim is labelled and sourced; vendor claims are not presented as independent facts.
- Access dates present; conflicting counts flagged (C1–C6).
- No personal contact data; no invented prices.
- Verdict vocabulary matches 03; requirement IDs match 04.
- Recommendation is explicit, confidence is stated, and reversal conditions are listed.

**Sources (all accessed 2026-11-21 unless stated):**

| ID | Source | URL | Supports |
|---|---|---|---|
| S1 | Castor — Home | https://www.castoredc.com/ | 19,000+ studies, 900+ customers; Catalyst submission stats |
| S2 | Castor — About | https://www.castoredc.com/about-castor/ | Founded 2012; 31,900+ studies; compliance list |
| S3 | Castor — Catalyst product | https://www.castoredc.com/catalyst-ai-clinical-data-extraction/ | Confidence scores, bounding boxes, FHIR/TEFCA, Source Vault |
| S4 | Castor — Catalyst milestone, 3 Sep 2026 | https://www.castoredc.com/news/castor-catalyst-data-extraction-milestone/ | 99.16% accepted / 0.78% overridden; five countries; US/EU residency |
| S5 | Castor — EDC | https://www.castoredc.com/electronic-data-capture-system/ | EDC capabilities |
| S6 | Health-RI — Overview of local support offices and institutional EDC licenses | https://www.health-ri.nl/en/overview-local-support-offices-and-institutional-edc-licenses | Castor at six Dutch UMCs (AUMC, Erasmus MC, LUMC, Maastricht, Radboud, UMC Utrecht); UMCG uses REDCap |
| S7 | Amsterdam UMC — Data collection tools | https://www.amsterdamumc.org/en/research/support/services-facilities/data-management/data-collection-tools | Castor institutional licence and support process |
| S8 | Castor — Netherlands press, 4 Sep 2019 | https://www.castoredc.com/press/press-release-castor-edc-leading-the-netherlands | Historical Dutch site licences (not used for any Verheul claim) |
| S9 | OpenClinica — EHR-to-EDC | https://www.openclinica.com/ehr-to-edc-integration/ | Unite since 2021; 90-minute site activation |
| S10 | OpenClinica — blog, 13 May 2025 | https://www.openclinica.com/blog/reimagining-the-protocol-for-the-future-of-research | 450+ sites / 24 systems |
| S11 | OpenClinica — blog, 25 Mar 2025 | https://www.openclinica.com/blog/ehr-to-edc-a-short-demo | 450+ sites / 20+ systems |
| S12 | OpenClinica — blog, 16 Oct 2024 | https://www.openclinica.com/blog/you-asked-and-we-answered-what-is-ehr-to-edc-in-clinical-trials | 15–20 hours config; 30–90 minutes per site |
| S13 | OpenClinica — About | https://www.openclinica.com/about-us/ | Company background |
| S14 | CASRAI — OpenClinica guide | https://casrai.org/guides/openclinica | ODM-XML, APIs, standards |
| S15 | ORTEC Logiqcare — Home | https://logiqcare.com/ | LogiqSuite, CDSS, medical data management |
| S16 | ORTEC — Corporate | https://ortec.com/ | Company |
| S17 | Cori Clinical — Home | https://www.cori-clinical.com/ | ISO 27001, GxP, regional hosting |
| S18 | Cori Clinical — Platform | https://cori-clinical.com/platform | Product modules and capabilities |
| S19 | tech.eu — 7 Oct 2026 | https://tech.eu/2026/10/07/cori-clinical-secures-4m-seed-to-improve-clinical-trial-design-and-cut-delays | USD 4M seed; 33%/82%; Erasmus MC (attributed to Cori) |
| S20 | Tech Funding News — 7 Oct 2026 | https://techfundingnews.com/london-startup-cori-clinical-raises-4m-to-cut-the-cost-of-clinical-trial-protocol-amendments | Incorporated Dec 2024; Erasmus MC (attributed to Cori); CROs unnamed |
| S21 | Medidata — Rave EDC | https://www.medidata.com/en/data-experience/edc-systems | Rave capabilities; EHR integration |
| S22 | Medidata — Rave Companion | https://www.medidata.com/en/data-experience/rave-companion/ | EHR-to-EDC entry |
| S23 | Medidata — Health Record Connect | https://www.medidata.com/en/data-experience/health-record-connect/ | EHR connectivity |
| S24 | Medidata — Rave fact sheet (PDF) | https://assetlibrary.medidata.com/m/10dfa6d2aefbd876/original/Rave-EDC-Fact-Sheet.pdf | 700K+ certified users; 1.8M users; 37K studies; 26+ years |
| S25 | Veeva — Clinical Operations | https://www.veeva.com/products/clinical-operations/ | Suite, Veeva Connections |
| S26 | Veeva — EDC | https://www.veeva.com/products/veeva-edc/ | EDC product page |
| S27 | Oracle — Clinical One hub | https://www.oracle.com/life-sciences/clinical-trials/clinical-one/hub | Platform, Digital Gateway |
| S28 | Oracle — Clinical One REST API docs | https://docs.oracle.com/en/industries/life-sciences/clinical-one/coapi | Documented REST APIs |
| S29 | Medrio — Home | https://www.medrio.com/ | 20+ years; 11K studies; 65K sites |
| S30 | Viedoc — Pricing | https://www.viedoc.com/pricing | Modular licensing; unlimited users; no list prices |
| S31 | Viedoc — Home | https://www.viedoc.com/ | Platform overview |
| S32 | TrialKit — Home | https://www.trialkit.com/ | Mobile-first EDC suite |
| S33 | rfp.wiki — TrialKit | https://www.rfp.wiki/specialty-industries/healthcare-life-sciences/healthcare/life-science-e-clinical-systems/trialkit | USD 1,350–90,000/month (secondary) |
| S34 | Florence — Home | https://www.florencehc.com/ | eISF/eTMF/eConsent |
| S35 | Florence — Products | https://www.florencehc.com/products/ | Product list |
| S36 | IgniteData — Solutions | https://ignitedata.com/solutions/ | Archer, Archer Intelligence |
| S37 | IgniteData — FAQ | https://ignitedata.com/faqs | Rave/Castor/Cisiv integrations |
| S38 | Mount Sinai — press release, 5 Oct 2026 | https://www.mountsinai.org/about/newsroom/2026/mount-sinai-tisch-cancer-center-cuts-clinical-trial-data-entry-time-by-more-than-half-with-real-time-ehr-to-edc-tech | 70%, 5.5→2.5 min, 100%, 0% re-query (institution self-report) |
| S39 | AACI — IgniteData deck, 14 Oct 2026 | https://www.aaci-cancer.org/Files/Admin/Webinars/2026-10-14-Tech-Gold-IgniteData.pdf | Archer Intelligence; no external AI; no new PHI repository |
| S40 | Microsoft Bay Area — 6 Nov 2026 | https://blogs.microsoft.com/bayarea/2026/11/06/how-ignitedata-is-bringing-trusted-automation-to-clinical-trial-data/ | Vendor-reported 89%/85%; MSK |
| S41 | Labcorp — interview, 10 Aug 2026 | https://www.labcorp.com/education-events/articles/expanding-clinical-research-efficiency-through-intelligent-data-flow-ignitedata-approach-healthcare | <90 minutes; vendor claims |
| S42 | Epic — Life Sciences | https://www.epic.com/software/life-sciences/ | Research module and Discovery |
| S43 | Flatiron — Real-World Evidence | https://flatiron.com/real-world-evidence | 6M+ records; 2,000+ publications; 45+ decisions |
| S44 | Flatiron — Telescope press, 19 May 2026 | https://resources.flatiron.com/press/flatiron-health-launches-flatiron-telescope-a-new-ai-platform-delivering-oncology-insights-in-minutes | Telescope launch |
| S45 | Flatiron — Paradigm acquisition press, 4 Dec 2025 | https://resources.flatiron.com/press/paradigm-health-acquires-flatiron-healths-clinical-research-business-and-forms-strategic-partnership-to-rebuild-clinical-research-ecosystem | Clinical-research divestiture |
| S46 | Tempus — Merck release, 3 Mar 2026 | https://www.tempus.com/news/pr/tempus-announces-strategic-collaboration-agreement-with-merck-to-accelerate-ai-driven-precision-medicine/ | Merck collaboration |
| S47 | Tempus — Home | https://www.tempus.com/ | Clinico-genomic data and AI |
| S48 | Paradigm — Series B press, 4 Dec 2025 | https://www.paradigmhealth.ai/resources/paradigm-health-raises-78-million-series-b-to-make-clinical-trials-part-of-routine-care-across-the-u-s-and-globally | USD 78M Series B; 45 states/166 organisations |
| S49 | Paradigm — Acquisition press, 4 Dec 2025 | https://www.paradigmhealth.ai/resources/paradigm-health-acquires-flatiron-healths-clinical-research-business-and-forms-strategic-partnership-to-rebuild-clinical-research-ecosystem | Flatiron clinical-research acquisition |
| S50 | Paradigm — Research press, 8 Apr 2026 | https://www.paradigmhealth.ai/resources/new-peer-reviewed-research-demonstrates-effectiveness-of-paradigm-health-study-conduct-products | Vendor's summary; the peer-reviewed paper is S52 |
| S51 | MobiHealthNews — 8 Dec 2025 | https://www.mobihealthnews.com/news/paradigm-health-raises-78m-acquires-flatiron-healths-clinical-research-business | Launched 2023 with USD 203M Series A; funding/acquisition |
| S52 | Ghanim et al. — npj Health Systems, 2026 | https://www.nature.com/articles/s44401-025-00066-9 | Peer-reviewed study: 91% eligible, 67% transferred, >99% completeness, 1.7 days, <2% queries (DOI 10.1038/s44401-025-00066-9) |

## 10. Reviewer note (known limits of this revision)

- Vendors were not contacted (Gate 0). Capability and accuracy figures remain public claims.
- The 99.16% Catalyst acceptance figure is from Castor's own press release and an internal production study; the review method and dataset are described but not independently audited.
- The Mount Sinai figures are an institution press release. No study, sample size beyond "data evaluated to date", or independent audit is cited.
- Paradigm's April 2026 release calls the study peer-reviewed but gives no journal or DOI. The paper has been located (Ghanim et al., npj Health Systems, DOI 10.1038/s44401-025-00066-9). It reports 91% eligible and 67% actually transferred, not ">99% automation"; the document now uses the paper's figures.
- TrialKit pricing is a secondary summary (rfp.wiki), not a vendor list price; confirm before quoting.
- OpenClinica's network counts vary by page and date; this document reports "450+ sites" and does not reconcile the system count.
- Dutch per-hospital deployments (Epic vs HiX/ChipSoft) are out of scope here and belong in T06/T13.

---

## Corrections log (2026-11-21)

This log maps each QA item from CEL-1731 (T21 review of D3 §1) to the change in this revision.

| QA item (CEL-1731) | Change |
|---|---|
| 1 — no source URLs | Added source IDs S1–S52 with full URLs and one access date (2026-11-21) in §9. Every vendor profile row now carries an S-reference. |
| 2 — Cori / Erasmus MC | Kept as **[CLAIMED-VENDOR]**. tech.eu (S19) and Tech Funding News (S20) both carry the Erasmus MC sentence but both attribute it to Cori; no independent record. Rec 5 and §3.4 now say "reports/claims", not "is already working with". |
| 3 — Mount Sinai / Paradigm labels | Mount Sinai → **[CLAIMED-INSTITUTION]**, with "no study cited". Paradigm → **[VERIFIED]** against the located peer-reviewed paper (S52, DOI 10.1038/s44401-025-00066-9), which reports 91% eligible / 67% transferred / >99% completeness, not ">99% automation". |
| 4 — TrialKit prices | Relabelled **[CLAIMED-SECONDARY]**, rfp.wiki (S33). "Confirm before quoting" kept in §3.10 and §4.5. D12 is outside the three files in this issue's scope; the caveat is recorded here for its owner. |
| 5 — "Key capabilities [VERIFIED]" | Vendor feature lists now read **[VERIFIED: advertised]** (S-reference given). Vendor-only compliance/accuracy claims use **[CLAIMED-VENDOR]**. |
| 6 — verdict vocabulary | §2 and all §3 verdicts use one primary verdict from 03. Secondary roles (partner, benchmark, integration target, watch) are in a Notes column or the prose. |
| 7 — §2 "four near-term threats" | Reworded. Castor is the only direct competitor with a proven Dutch academic footprint; Cori is a direct protocol-AI competitor; OpenClinica and IgniteData have no Dutch customer evidence yet. |
| 8 — "Cori is two years ahead" | Deleted. Replaced with the sourced claim that Cori reports two Erasmus MC trials. |
| 9 — Verheul 2016 endorsement | Removed. The section now says no public Yamicc/Castor relationship was found. (QA allowed "mark [INFERRED] or remove"; removal is cleaner because the 2016 statement was at VUmc.) |
| 10 — §5 NFR mapping | Deployment row now maps to `NFR-02`, `NFR-07`. `NFR-09` removed from that row (openness is not a deployment attribute). |
| 11 — §9 C1–C5 | Now C1–C6. C2 and C3 are described as "inconsistent or not comparable" (different dates and units), not true conflicts. |
| 12 — Paradigm funding vs deal | §3.16 and §4.3 now state that the USD 78M Series B and the Flatiron clinical-research acquisition were announced on the same day but are separate; acquisition terms were not disclosed. C5 records the same and keeps the 78/77 discrepancy. |

**Extra corrections made while re-checking (not QA items):**
- Health-RI lists Castor at **UMC Utrecht**; **UMCG** uses REDCap. The earlier text wrongly listed UMCG as a Castor user. Corrected in §3.1, S6 and §4.4.
- The Paradigm paper was located. Its figures replace the vendor release's ">99% automation" wording (which mixed completeness with transfer rate).
- The earlier revision note said "S1–S51"; the table now runs to S52.
