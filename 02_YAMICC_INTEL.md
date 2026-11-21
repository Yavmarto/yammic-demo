# 02 — YAMICC INTELLIGENCE (shared context for all agents)

## 1. Organization
- [VERIFIED] Name: "You And Me In Curing Cancer". Independent Dutch non-profit foundation with ANBI status, founded 2024, Westewagenstraat 60, Rotterdam. KvK 95190112. ~2–10 staff. Source: https://yamicc.org/about-us/, https://yamicc.org/what-we-do/ (footer).
- [VERIFIED] Mission: initiate, facilitate and coordinate large-scale collaboration to find effective treatments for (rare) cancers using innovative (information) technology, including AI. Source: https://yamicc.org/
- [VERIFIED, data-broker profiles] Roles listed publicly: Roald Kruit (co-founder, chairman), Carli Wischhoff (co-founder), Erik Bottenberg (CTO), Josje van den Bos (general manager), Lisa de Man (head of legal). Source: RocketReach profile. Do NOT store contact details.
- [GK, high confidence] Roald Kruit is a co-founder of Mendix (low-code platform). [CLAIMED-C] co-founded Yamicc with Erasmus MC neurosurgeons/researchers — not verified.
- [VERIFIED] Prof. Henk Verheul (chair Medical Oncology, Erasmus MC) publicly supports Yamicc. Source: https://yamicc.org/the-challenges/
- [VERIFIED] Funding: donations (incl. a Supporta fundraiser) and partners; partner program for hospitals, tech companies, patient groups.

## 2. Stated problem [VERIFIED, yamicc.org/about-us and /the-challenges]
- Single hospitals have only dozens of eligible rare-cancer patients; thousands are needed for statistically meaningful studies.
- Data scattered across hospitals, formats differ, combining is technically and legally hard.
- No central coordinating body; trials are costly and inefficient.
- [CLAIMED-C] Rare cancers ≈ 20% of cancer cases in EU/UK, ~650,000 new patients/year. Verify against RARECARE / RARECAREnet publications.

## 3. The Yamicc Platform — what is publicly described

### 3a. Website description [VERIFIED, yamicc.org/what-we-do and /the-challenges]
- "Trial Execution Platform": shared, scalable, reusable platform for clinical studies on (rare) cancers, built with hospitals, researchers and partners, step by step.
- Claims: lower cost per study via AI automation of repetitive work; automated data collection; data made FAIR; standardization across studies and hospitals "using open standards" (standards NOT named); faster design-to-results.

### 3b. Component architecture shown at Mendix Zorg Connect demo [VERIFIED via partner LinkedIn posts, demo 26 March 2026, Mendix HQ Rotterdam, presented by Roald Kruit]
| Component | Provider | Role | Maturity evidence |
|---|---|---|---|
| Yamicc Clinical Case Management | Yamicc, with MxBlue / SUPERP (Mendix partner) | Central layer connecting trials and patient cases | Demo |
| Protocol authoring AI | Cori Clinical | AI support for writing and reviewing research protocols | Demo |
| eCRF / data capture | ORTEC Logiqcare — LogiqSuite | Integrated eCRF, medical data management | Existing commercial product; integration shown in demo |
| Yamicc Datahub | Yamicc | Secure access to patient data from existing EHRs | **Mock-up EHR in demo** — interoperability NOT proven |
| Unknown | Koalitix | Named partner, role not stated | Unknown — research |
Sources: https://www.linkedin.com/in/zteven/ , https://www.linkedin.com/in/jeroen-leer-van-der-94240937/

- [INFERRED] Platform is likely built largely on Mendix (demo at a Mendix event, Mendix-partner integrator, Mendix co-founder as chair). [CLAIMED-C] states "built on Mendix" and "centralized, cloud-based" — treat as likely but unconfirmed.
- [CLAIMED-B] OMOP-related work publicly discussed — not verified; find source.

### 3c. Clinical anchor use case [VERIFIED, yamicc.org/what-we-do]
- ReDiReCCT-GB trial (Erasmus MC): every newly diagnosed glioblastoma patient in principle participates, followed from diagnosis; full genetic tumor profiling to find matching drugs; a new biological model tests which drugs reach/kill tumor cells per patient; large-scale testing of drugs approved for other cancers (drug repurposing).
- Prospective dataset initially from patients in Yamicc-facilitated trials across multiple hospitals.

### 3d. Claimed vision items not found on the website
- [CLAIMED-C] Four pillars incl. "Bioinformatics & AI Diagnostics / Digital Thread" linking clinical history, DICOM imaging and multi-omics to train diagnostic and treatment-recommendation models. Not found on yamicc.org — treat as roadmap/hypothesis until sourced.

## 4. Maturity assessment (to be completed by Research agent)
For each capability mark: Announced / Demonstrated / Pilot / Production / Validated / Roadmap.
Current best estimate [INFERRED]: case management, protocol AI, eCRF integration = Demonstrated (March 2026); EHR access = Demonstrated with mock data only; FAIR/OMOP standardization = Announced; AI diagnostics/digital thread = Roadmap or unconfirmed; ReDiReCCT-GB = trial started at Erasmus MC (platform's role in it unclear).

## 5. Conflict & uncertainty table
| # | Topic | Source A | Source B/C | Resolution needed |
|---|---|---|---|---|
| 1 | Tech base | Website silent | C: built on Mendix; B: "Mendix ecosystem involvement" | Confirm via Mendix case studies, job posts, talks |
| 2 | EHR integration | Website: "automated data collection" | Demo used mock-up EHR | Find any real hospital connection / pilot |
| 3 | Standards | Website: "open standards", unnamed | B: OMOP discussed | Find source naming FHIR/OMOP/CDISC |
| 4 | Imaging / multi-omics / AI diagnostics | Not on website | C: core pillar | Source or downgrade to hypothesis |
| 5 | Deployment | Unknown | C: centralized cloud | Verify; matters for differentiation (federated vs central) |
| 6 | Co-founders | RocketReach: Kruit, Wischhoff | C: + Erasmus MC neurosurgeons | Verify via KvK/ANBI pages |
| 7 | Rare cancer stats | — | C: ~20%, 650k/yr | Verify with RARECARE |
| 8 | Hartwig/DRUP relationship | Unknown | — | Partner, competitor or unrelated? |
| 9 | vantage6 use | Erasmus MC co-develops vantage6 | — | Does Yamicc use it? |
| 10 | Koalitix role | Named partner | — | Identify role |
