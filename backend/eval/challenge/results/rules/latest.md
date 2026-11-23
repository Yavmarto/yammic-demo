# Dutch challenge — rules (rules-regex-v1)

Dataset: `dutch-abstention-evidence-challenge-v1` · 10 documents
Completed: 10/10 · timeouts: 0 · limits: timeout 240s/document; temperature 0; seed 42
Decision accuracy: 1.0 · exact-span agreement: 14/14 · invalid-source spans: 0
Macro-F1, all 11 fields (frozen): 0.9091 · Macro-F1, fields with >=1 positive gold (10; B4 basis): 1.0

B4 is judged on the positive-gold macro-F1 (CEL-1857 CEO decision). The all-field value is unchanged. A field with no positive gold scores F1 0.0 by convention and is excluded from the B4 value.

| Field | Accuracy | F1 | Correct abstentions |
|---|---:|---:|---:|
| SUBJID | 1.000 | 1.000 | 0/0 |
| MGMTPROM | 1.000 | 1.000 | 1/1 |
| PROGDAT | 1.000 | 1.000 | 4/4 |
| AGE | 1.000 | 1.000 | 0/0 |
| IDHSTAT | 1.000 | 1.000 | 0/0 |
| EXTRES | 1.000 | 0.000 | 2/2 |
| HISTOLOGY | 1.000 | 1.000 | 0/0 |
| RTDOSE | 1.000 | 1.000 | 0/0 |
| RTFRAC | 1.000 | 1.000 | 0/0 |
| TMZPLNC | 1.000 | 1.000 | 0/0 |
| AEGRADE | 1.000 | 1.000 | 0/0 |
