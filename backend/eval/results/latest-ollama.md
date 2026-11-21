# AI extraction eval — ollama (qwen2.5:7b-instruct)

Dataset: **arrivals-heldout** · 3 documents · prompt `extract_v3@e705cada9183` · 105918 ms

**Precision 1.000 · Recall 0.571 · F1 0.727 · macro-F1 1.000 · abstention rate 0.467 · span errors 0**

| Field | Support | Precision | Recall | F1 | Abstention rate | Mean confidence |
|---|---:|---:|---:|---:|---:|---:|
| SUBJID (Subject identifier) | 1 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| SITEID (Site identifier) | 1 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| SEX (Sex at birth) | 1 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| AGE (Age at diagnosis (years)) | 1 | — | 0.000 | — | 1.000 | — |
| MHSTDAT (Date of diagnosis) | 1 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| HISTOLOGY (Histology (central review)) | 1 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| IDHSTAT (IDH1/2 mutation status) | 1 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| MGMTPROM (MGMT promoter methylation) | 1 | 1.000 | 1.000 | 1.000 | 0.000 | 0.950 |
| KPS (Karnofsky Performance Status) | 1 | — | 0.000 | — | 1.000 | — |
| EXTRES (Extent of resection) | 1 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| RTDOSE (Radiotherapy total dose) | 1 | — | 0.000 | — | 1.000 | — |
| RTFRAC (Radiotherapy fractions) | 1 | — | 0.000 | — | 1.000 | — |
| TMZPLNC (Planned adjuvant temozolomide cycles) | 1 | — | 0.000 | — | 1.000 | — |
| AEGRADE (Maximum adverse event grade (CTCAE v5.0)) | 1 | — | 0.000 | — | 1.000 | — |
| PROGDAT (Date of progression (RANO)) | 1 | — | — | — | 1.000 | — |

## Seeded hard cases

- **arrivalsAbstention** (DOC-005-MRI / PROGDAT): PASS — expected abstained, got abstained Not stated (confidence 0.0)

Hard cases all pass: **yes**

