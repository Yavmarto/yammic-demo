# V5 manual-entry rehearsal

Local synthetic prototype only. Start the isolated stack with `make demo AI_PROVIDER=rules` from `~/yammic-v5`; open http://127.0.0.1:8082. It uses API port 8002 and does not use the v3 or v4 checkpoints.

1. Sign in as Nurse with Use demo account. Open AI review.
2. Select GBM-NL-004 and choose Enter from source. Select `Poliklinische brief neurochirurgie (fictief) (DOC-004-CLIN)`.
3. Select Age at diagnosis (years), enter `52`, and copy `LEEFTIJD BIJ DIAGNOSE: 52 jaar` into Exact source quote. Save as person-entered.
4. The review screen shows 52 years, Entered by a person, and the highlighted source quote. View audit trail to see the value entry.
5. Sign in as PI and open Export. Select GBM-NL-004 and preview the FHIR bundle. It includes the checked value and human/source provenance.
6. To show the existing AI path, select GBM-NL-001 in AI review, select a pending proposal, compare its highlighted source, and choose Accept.

Rehearsal: macOS, headless Chromium, Flutter release web build on 8082 against the synthetic v5 API on 8002, 22 November 2026. The AGE entry and one GBM-NL-001 AI proposal were saved during rehearsal, so these exact fields cannot be replayed without preparing a fresh v5 dataset. The API prevents overwriting verified values. The app is a local prototype, not for clinical use. Nurse cannot export; use PI or monitor. No mobile platform was checked.
