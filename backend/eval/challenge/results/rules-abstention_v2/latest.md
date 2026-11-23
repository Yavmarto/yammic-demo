# Dutch challenge — rules (rules-regex-v1)

Dataset: `dutch-abstention-v2-tuning-set` · 9 documents
Completed: 9/9 · timeouts: 0 · limits: timeout 240s/document; temperature 0; seed 42
Decision accuracy: 1.0 · exact-span agreement: 2/2 · invalid-source spans: 0
Macro-F1, all 3 fields (frozen): 0.6667 · Macro-F1, fields with >=1 positive gold (2; B4 basis): 1.0

B4 is judged on the positive-gold macro-F1 (CEL-1857 CEO decision). The all-field value is unchanged. A field with no positive gold scores F1 0.0 by convention and is excluded from the B4 value.

| Field | Accuracy | F1 | Correct abstentions |
|---|---:|---:|---:|
| EXTRES | 1.000 | 1.000 | 4/4 |
| IDHSTAT | 1.000 | 1.000 | 3/3 |
| PROGDAT | 1.000 | 0.000 | 1/1 |
