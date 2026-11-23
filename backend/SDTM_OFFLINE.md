# Offline fictional SDTM-style VS weight slice

This local mapping experiment is not a submission-ready or independently CDISC-conformant dataset. The primary reference is [CDISC SDTMIG v3.4](https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-4), accessed 2026-11-23. CDISC states that v3.4 is used with SDTM v2.0; the full v3.4 files require sign-in, so the exact domain specification and controlled terminology were not independently checked here. Full standards review, current controlled terminology, Define-XML, submission transport format, metadata, and independent conformance validation remain necessary. CSV and this JSON sidecar are not an XPT submission package. No CDISC conformance is claimed.

The explicit JSON fixture has `fictional: true`, `study_id`, and `rows`. Each row has boolean `checked`. Like the existing ODM export, selection is of human-verified values, not pending proposals; `checked` represents that review decision. It does not mean separate source data verification (SDV), which ODM records separately. Unchecked rows and null/empty values are omitted. A selected row must contain WEIGHT, kg, a positive decimal string at most 500 with up to three decimals, a valid full ISO date, and restricted identifiers for subject, source and verifier. Duplicate selected subject/date pairs fail the entire export. This is a local fixture contract, not a de-identification guarantee; use fictional values only. Unselected rows are not validated beyond the checked flag. Missing rows are not represented as not-done findings.

| VS variable | Mapping |
| --- | --- |
| STUDYID | fixture study_id |
| DOMAIN | VS |
| USUBJID | study_id + `-` + subject_id |
| VSSEQ | one-based per subject, sorted by subject and date |
| VSTESTCD / VSTEST | WEIGHT / Weight |
| VSORRES / VSORRESU | original decimal string / kg |
| VSSTRESC / VSSTRESN / VSSTRESU | normalized decimal string / same numeric text / kg; no conversion |
| VSDTC | supplied date |

The generated UTF-8 CSV has the column order above, LF endings, a header even when empty, and no timestamps. The JSON sidecar binds each exported USUBJID/VSSEQ to source_id and verified_by; its `csv_sha256` is the lowercase SHA-256 of the exact CSV bytes. The sidecar is a local provenance aid, not Define-XML or an SDTM dataset. Input order does not change output; changing a raw representation such as `70.50` to `70.5` changes the checksum. The checksum detects changes but is not an authenticity signature. The program reads only the supplied fixture and writes only the selected output directory; no database or network is used.

From `backend`:

```sh
python3 -m app.export.sdtm_offline fixtures/sdtm/fictional_weight.json /path/to/output
python3 -m pytest -q tests/test_sdtm_offline.py
```

Review the output directory before running: `vs.csv` and `vs.provenance.json` are overwritten. These checks validate only this mapping and input contract, not study metadata, clinical correctness, CDISC controlled terminology, cross-domain relationships, or independent CDISC conformance.
