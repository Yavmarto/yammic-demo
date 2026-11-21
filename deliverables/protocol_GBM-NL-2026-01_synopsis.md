# Protocol Synopsis — GBM-NL-2026-01

> **SYNTHETIC — fictional protocol for prototype demonstration. Not for clinical use. No real patients, sites or data.**

| Field | Value |
|---|---|
| Study ID | GBM-NL-2026-01 |
| Short name | ReDiReCCT-GB Demo (synthetic) |
| Phase | II |
| Indication | Glioblastoma, IDH-wildtype (WHO CNS5, 2021) |
| Sponsor | Stichting Fictieve Neuro-Oncologie (fictional) |
| Coordinating site | SITE-01, FUMC Zuidhaven (fictional) |
| Protocol version | 1.0 (2026-11-21) |
| Target / current enrolment | 24 / 8 |
| Registry | NL-DEMO-0000 (fictional, not a real registry entry) |

## 1. Title

A fictional phase II, single-arm, open-label, multicentre study of standard
chemoradiotherapy (Stupp schedule) with biomarker follow-up in adults with newly
diagnosed glioblastoma, IDH-wildtype.

## 2. Objectives and endpoints

- **Primary objective.** Estimate progression-free survival at 6 months (PFS6)
  under the Stupp schedule. **Primary endpoint:** PFS6 by RANO criteria (fictional).
- **Secondary objectives.** Describe overall survival; measure eCRF data
  completeness after AI-assisted extraction; measure reviewer time per extracted
  field (simulated).

## 3. Design

Phase II, single-arm, open-label, multicentre (3 fictional sites: SITE-01,
SITE-02, SITE-03). Participants receive concurrent chemoradiotherapy followed by
adjuvant temozolomide. No randomisation. All data are synthetic fixtures; no
network calls and no live model calls (local rules plus Ollama only).

## 4. Population

Adults (≥18 years) with newly diagnosed, histologically confirmed glioblastoma,
IDH-wildtype, who meet every inclusion criterion and no exclusion criterion.
Each criterion below is checkable against the protocol source documents:
pathology and molecular reports, contrast-enhanced MRI reports and operative
notes, clinic and discharge letters, and laboratory results.

## 5. Eligibility criteria

### Inclusion criteria

1. **INC-01 — Age.** Age ≥18 years at diagnosis. *Check:* age from demographics or clinic letter; eCRF `AGE`.
2. **INC-02 — Histology.** Histologically confirmed glioblastoma, ICD-O-3 morphology 9440/3, IDH-wildtype (WHO CNS5, 2021). *Check:* pathology report plus IDH1/2 result; eCRF `HISTOLOGY`, `IDHSTAT`.
3. **INC-03 — MGMT status.** MGMT promoter methylation status is known (methylated or unmethylated). *Check:* molecular pathology report; eCRF `MGMTPROM`.
4. **INC-04 — Performance status.** Karnofsky Performance Status ≥60, recorded within 7 days before registration. *Check:* clinic or discharge letter; eCRF `KPS`.
5. **INC-05 — Bone-marrow function.** ANC ≥1.5 ×10⁹/L, platelets ≥100 ×10⁹/L, haemoglobin ≥9.0 g/dL. *Check:* haematology report with date.
6. **INC-06 — Hepatic function.** ALT ≤3 ×ULN and total bilirubin ≤1.5 ×ULN (≤3 ×ULN if Gilbert syndrome). *Check:* chemistry report with local ULN.
7. **INC-07 — Renal function.** Serum creatinine ≤1.5 ×ULN or eGFR ≥50 mL/min/1.73 m². *Check:* chemistry report.
8. **INC-08 — Imaging and surgery.** Post-surgical contrast-enhanced MRI is available and evaluable per RANO, and the participant has recovered from surgery (≥2 weeks after craniotomy or ≥1 week after biopsy). *Check:* MRI report, operative note, clinic letter; eCRF `EXTRES`.
9. **INC-09 — Consent and compliance.** Participant is able to give written informed consent and to comply with the visit schedule. *Check:* signed consent form and clinic letter.

### Exclusion criteria

10. **EXC-01 — Prior brain radiotherapy.** Any prior radiotherapy to the brain. *Check:* oncology history in clinic letter or radiotherapy record.
11. **EXC-02 — Prior systemic therapy.** Prior systemic anti-glioma therapy (chemotherapy, targeted therapy or immunotherapy), except corticosteroids. *Check:* treatment history in clinic letter.
12. **EXC-03 — Tumour genotype.** Tumour is IDH-mutant or IDH status is indeterminate / not assessable. *Check:* pathology plus IDH1/2 result; eCRF `IDHSTAT`.
13. **EXC-04 — Pregnancy or breastfeeding.** Participant is pregnant or breastfeeding; participants with reproductive potential must have a negative pregnancy test. *Check:* pregnancy test result and clinic letter; eCRF `SEX`.

> **SYNTHETIC · Page 1 of 2 · GBM-NL-2026-01 v1.0**

---

<!-- PAGE 2 -->

> **SYNTHETIC — fictional protocol for prototype demonstration. Not for clinical use. No real patients, sites or data.**

## 6. Treatment schedule (Stupp-like)

- **Concurrent phase.** Radiotherapy 60 Gy in 30 fractions (2 Gy per fraction,
  5 days per week, about 6 weeks) with temozolomide 75 mg/m²/day, every day
  during radiotherapy including weekends.
- **Adjuvant phase.** After a 4-week break, temozolomide 150 mg/m² on days 1–5 of
  a 28-day cycle for cycle 1, then 200 mg/m² on days 1–5 for cycles 2–6 (up to 6
  cycles). Dose adjustments follow CTCAE v5.0 toxicity.

## 7. Visit schedule

| Visit | Name | Day (window) | Key assessments |
|---|---|---|---|
| V0 | Screening | −14 to 0 | Eligibility, consent, baseline labs, MRI |
| V1 | Baseline | 0 | Demographics, diagnosis, surgery record, eCRF |
| V2 | Radiotherapy start | 14 (±7) | RT start, concurrent TMZ start |
| V3 | Radiotherapy end | 56 (±7) | RT dose/fractions, toxicity |
| V4–V9 | TMZ cycles 1–6 | 63, 91, 119, 147, 175, 203 (±7) | Labs, toxicity, MRI per RANO |
| V10 | End of treatment | 231–238 (±14) | Outcome, safety summary |
| V11 | Follow-up | 287 (±14), then 8-weekly | RANO assessment |
| V12 | Survival follow-up | 371 (±28), then 12-weekly | Survival status |

## 8. Key eCRF data points

Form `ECRF-GBM-BASELINE` v1.0, 13 required fields of 15 total.

| eCRF field | Label | Type / unit | CDISC |
|---|---|---|---|
| SUBJID | Subject identifier | string | DM.SUBJID |
| SITEID | Site identifier | string | DM.SITEID |
| SEX | Sex at birth | coded (F/M) | DM.SEX |
| AGE | Age at diagnosis | integer, years | DM.AGE |
| MHSTDAT | Date of diagnosis | date | MH.MHSTDAT |
| HISTOLOGY | Histology (central review) | coded, ICD-O-3 9440/3 | MH.MHTERM |
| IDHSTAT | IDH1/2 mutation status | coded (wildtype/mutant/indeterminate) | LB.LBORRES |
| MGMTPROM | MGMT promoter methylation | coded (methylated/unmethylated/indeterminate) | LB.LBORRES |
| KPS | Karnofsky Performance Status | integer, % | QS.QSORRES |
| EXTRES | Extent of resection | coded (gross total/subtotal/biopsy/not assessable) | PR.PRTRT |
| RTDOSE | Radiotherapy total dose | number, Gy | EX.EXDOSE |
| RTFRAC | Radiotherapy fractions | integer, fractions | EX.EXDOSFRQ |
| TMZPLNC | Planned adjuvant TMZ cycles | integer, cycles | EX.EXDOSTOT |
| AEGRADE | Maximum adverse event grade | integer, CTCAE v5.0 (optional) | AE.AETOXGR |
| PROGDAT | Date of progression (RANO) | date (optional) | RS.RSDTC |

## 9. Data provenance

All participants, sites, documents and AI extractions are fictional fixtures.
No real patient data, no live model calls and no network calls. Local rules and
Ollama only. See `app/assets/data/study.json` and `deliverables/protocol_criteria.json`.

> **SYNTHETIC · Page 2 of 2 · GBM-NL-2026-01 v1.0**
