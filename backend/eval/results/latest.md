# AI extraction eval — rules (rules-regex-v1)

Dataset: **all** · 13 documents · prompt `rules_v1` · 23 ms

**Precision 1.000 · Recall 1.000 · F1 1.000 · macro-F1 1.000 · abstention rate 0.066 · span errors 0**

| Field | Support | Precision | Recall | F1 | Abstention rate | Mean confidence |
|---|---:|---:|---:|---:|---:|---:|
| SUBJID (Subject identifier) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.990 |
| SITEID (Site identifier) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.980 |
| SEX (Sex at birth) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.990 |
| AGE (Age at diagnosis (years)) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.970 |
| MHSTDAT (Date of diagnosis) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.920 |
| HISTOLOGY (Histology (central review)) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.970 |
| IDHSTAT (IDH1/2 mutation status) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.960 |
| MGMTPROM (MGMT promoter methylation) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.930 |
| KPS (Karnofsky Performance Status) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.900 |
| EXTRES (Extent of resection) | 5 | 1.000 | 1.000 | 1.000 | 0.000 | 0.810 |
| RTDOSE (Radiotherapy total dose) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.960 |
| RTFRAC (Radiotherapy fractions) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.960 |
| TMZPLNC (Planned adjuvant temozolomide cycles) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.890 |
| AEGRADE (Maximum adverse event grade (CTCAE v5.0)) | 4 | 1.000 | 1.000 | 1.000 | 0.000 | 0.830 |
| PROGDAT (Date of progression (RANO)) | 4 | — | — | — | 1.000 | — |

## Seeded hard cases

- **wrongValue** (DOC-002-PATH / MGMTPROM): PASS — expected unmethylated, got proposed Unmethylated (confidence 0.93)
- **lowConfidence** (DOC-002-MRI / EXTRES): PASS — expected confidence < 0.6, got proposed Subtotal resection (confidence 0.45)
- **abstention** (DOC-003-MRI / PROGDAT): PASS — expected abstained, got abstained Not stated (confidence 0.0)
- **arrivalsAbstention** (DOC-005-MRI / PROGDAT): PASS — expected abstained, got abstained Not stated (confidence 0.0)

Hard cases all pass: **yes**

