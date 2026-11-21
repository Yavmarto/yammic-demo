# `fhir-seed/` — synthetic hospital EHR for the Yamicc demo

A **fictional** hospital FHIR R4 endpoint, filled with the synthetic GBM dataset
already used by the Flutter app. The Yamicc platform pulls from it (workstream
W5), so the demo is truly connected: no bundled JSON, no hosted service.

- Everything is synthetic. No real patients, names, hospitals or MRNs.
- Every resource carries `meta.tag` `SYNTHETIC` and `meta.security` `HTEST`.
- Runs only against the local HAPI FHIR R4 server from `docker-compose.yml`
  (`http://127.0.0.1:8090/fhir`). No paid APIs, no external network.
- Owner: Junior Engineer (CEL-1776). Do not edit other workstreams' paths.

## Quick start

```bash
# 1. Start Postgres + HAPI FHIR (DevOps W2)
make up

# 2. Load the 8 baseline participants (this is what `make seed` runs)
python3 fhir-seed/load.py --set baseline

# 2b. Load hospital 2 (FUMC Noordhaven, 5 baseline GBM patients + 2 arrivals)
python3 fhir-seed/load.py --hospital 2 --set baseline
python3 fhir-seed/load.py --hospital 2 --set arrivals

# 3. During the demo: sync the 3 new arrivals
python3 fhir-seed/load.py --set arrivals
```

Other commands:

```bash
python3 fhir-seed/load.py --set all            # baseline + arrivals
python3 fhir-seed/load.py --dry-run            # show the plan, touch nothing
python3 fhir-seed/load.py --no-validate        # skip $validate (faster reload)
python3 fhir-seed/load.py --check-counts       # fail if server totals differ
python3 fhir-seed/generate.py                  # regenerate the committed bundles
python3 fhir-seed/generate.py --check          # fail if bundles are stale
python3 -m unittest discover -s fhir-seed/tests -v
```

Exit codes: `0` OK, `1` connection or load failure, `2` `$validate` errors when
`--strict-validate` is set.

## Layout

```
fhir-seed/
  generate.py              deterministic bundle generator (stdlib only)
  load.py                  idempotent transaction loader + $validate (stdlib only)
  shared/codesystems.json  4 synthetic local CodeSystems (loaded by both sets)
  baseline/
    manifest.json          order, counts, per-patient file names + sha256
    organizations.json     3 fictional trial sites
    patient-GBM-NL-001.json ... -008.json
  arrivals/
    manifest.json
    organizations.json
    patient-GBM-NL-009.json ... -011.json
  source/
    arrivals.json          the 3 new patients (the live-sync fixture)
    documents/*.txt        7 new report texts (not part of app/assets)
  tests/test_fhir_seed.py  19 offline tests (+1 optional integration test)
```

`baseline` is generated from `app/assets/data/` (8 participants, 10 documents).
`arrivals` is generated from `fhir-seed/source/` (3 new patients, 7 new
documents). Nothing under `app/` is changed.

## Resource inventory

Counts are asserted by `fhir-seed/tests/test_fhir_seed.py` and by
`manifest.json`; `load.py --check-counts` compares them with the server.

| Resource | baseline | arrivals | What it contains |
|---|---:|---:|---|
| `Patient` | 8 | 3 | Fictional name (`Proefpersoon` + NATO call sign), year-only `birthDate`, sex, active flag, and 3 identifiers: hospital **MRN**, **study subject** code, study number |
| `Organization` | 3 | 3 | The 3 fictional trial sites from `study.json` (same ids in both sets) |
| `Condition` | 8 | 3 | Primary cancer condition: GBM IDH-wildtype (SNOMED `393563007` + ICD-O-3 `9440/3`), IDH-mutant glioma (screen failure 007), or provisional lesion (screening 004, 011). Body site, onset, verification status |
| `Encounter` | 8 | 3 | One episode per patient: surgical admission (IMP), chemoradiotherapy course (AMB), or screening visit. `DocumentReference.context.encounter` points here |
| `Observation` | 90 | 39 | KPS (LOINC `89261-2`), MGMT promoter (LOINC `88199-1`), IDH status, extent of resection (SNOMED `262143007`), and 6 blood labs × 2 timepoints (LOINC: Hb `718-7`, WBC `6690-2`, platelets `777-3`, ANC `26464-8`, ALT `1742-6`, creatinine `2160-0`) with reference ranges and H/L/N interpretation |
| `Procedure` | 8 | 4 | Tumour resection or stereotactic biopsy where the dataset states one, plus radiotherapy course (60 Gy / 30 fractions) as an mCODE-style Procedure with `performedPeriod` |
| `MedicationRequest` | 11 | 4 | Temozolomide (ATC `L01AX03`): concurrent 75 mg/m² daily during RT, and adjuvant 200 mg/m² days 1–5 every 28 days |
| `MedicationAdministration` | 13 | 0 | One completed adjuvant cycle per completed `TMZ cycle N` visit in the dataset (13 cycles across 6 participants) |
| `DiagnosticReport` | 6 | 4 | One per pathology or radiology report: LOINC type, category, `conclusion` parsed from the report, and the full report as `presentedForm` base64 |
| `DocumentReference` | **10** | **7** | One per report (pathology, radiology, operative note, discharge/clinic letter). The **report text is the base64 `text/plain` attachment**; `masterIdentifier` is the hospital document id (`DOC-001-PATH`, …) |
| `CodeSystem` | 4 | 4 | Synthetic local code systems for provenance, MGMT status, procedure type, resection extent (same ids in both sets) |
| **total** | **169** | **74** | union = **236** unique resources (shared CodeSystems and Organizations loaded once) |

### Documents

Baseline (10): `DOC-001-PATH/MRI/DIS`, `DOC-002-PATH/MRI/SURG/DIS`,
`DOC-003-PATH/MRI/DIS` — exactly the files in
`app/assets/data/documents/`.

Arrivals (7):

| Patient | Documents | Story |
|---|---|---|
| `GBM-NL-009` | pathology, post-op MRI, discharge letter | 58F, right parietal GBM, gross total resection, MGMT unmethylated. The live extraction target |
| `GBM-NL-010` | pathology, discharge letter | 66M, left frontal GBM, biopsy only, MGMT methylated |
| `GBM-NL-011` | MRI, neurology clinic letter | 51F, suspected high-grade lesion, screening. Histology pending |

The arrival texts deliberately reuse the label patterns in the existing corpus
(`PATIENTCODE:`, `SUBJECT CODE:`, `GESLACHT:`, `Karnofsky Performance Status`,
`MGMT-promotermethylering`, `ICD-O-3 9440/3`) so the deterministic `rules`
extractor in `backend/app/ai/providers/rules.py` finds the same fields live.

## Idempotency and determinism

- Every bundle is a FHIR `transaction` whose entries are `PUT Type/id` with
  client-assigned ids. Re-running the loader updates the same resources
  (`created=0, updated=N`), so `make seed` can run twice and the count does not
  change.
- `generate.py` uses fixed timestamps (`2026-11-21T10:30:00+01:00`, `AS_OF =
  2026-11-21`) and seeded PRNGs keyed by patient id for lab values. Output bytes
  are stable; `generate.py --check` fails on drift.
- The committed bundles are what the loader reads. `make reset` does not need
  to run the generator.

## Identifiers and pseudonymisation (contract for W5)

Each `Patient` has three identifiers:

| System | Example | Notes |
|---|---|---|
| `urn:oid:2.16.840.1.113883.4.9999` | `MRN-01-00101` | Fictional hospital MRN. **The platform must not persist this value.** Store a keyed hash/salt instead; the demo can show the MRN only in the ingest log |
| `https://yamicc.example/fhir/NamingSystem/study-subject-id` | `GBM-NL-001` | Join key to the backend participants. Equals the `Patient.id` |
| `https://yamicc.example/fhir/NamingSystem/study-number` | `GBM-NL-2026-01` | Study id from `app/assets/data/study.json` |

`DocumentReference.masterIdentifier` is the hospital document id. Ingestion
should de-duplicate on it, so syncing twice does not create two documents.

## mCODE alignment

The resources follow the mCODE data model where practical:

- `Condition` = primary cancer condition, with ICD-O-3 histology and body site.
- `Procedure` = cancer-related surgical procedure and radiotherapy course
  summary (`performedPeriod`, dose/fractions in `code.text`).
- `MedicationRequest` = cancer-related medication request (temozolomide ATC).
- `Observation` = tumour marker/biomarker style observations with LOINC where a
  code exists.
- `DiagnosticReport` + `DocumentReference` = the report and the source text.

`meta.profile` mCODE URLs are **not** asserted by default. The demo HAPI server
has no mCODE implementation guide installed, so `$validate` returns
`VALIDATION_VAL_PROFILE_UNKNOWN_NOT_POLICY`. To assert the profiles against an
IG-enabled server, regenerate with:

```bash
python3 fhir-seed/generate.py --mcode-profiles
```

## Terminology caveats

The source dataset flags some codes as unverified
(`app/assets/data/study.json`, `codeVerified`). This seed mirrors that:

- **Verified in the dataset:** ICD-O-3 `9440/3`, ATC `L01AX03`, UCUM units.
- **Placeholder, copied from the dataset:** SNOMED `393563007` (GBM),
  `445048000` (IDH1 wild type), `262143007` (extent of resection), LOINC
  `88199-1` (MGMT), `89261-2` (KPS). Each is noted in the resource `note`.
- **Synthetic local code systems** (no external terminology): MGMT status,
  procedure type, resection extent, provenance. See `shared/codesystems.json`.
- Radiotherapy and resection have no verified SNOMED procedure code in the
  dataset, so they use the local `procedure-type` code system plus a clear
  `code.text`. Do not present these as SNOMED-coded in the demo.

All resources include a generated `text.div` narrative, so HAPI `$validate`
passes with 0 errors and the resources are readable in any FHIR viewer.

## Known gaps / deliberate omissions

- Participants `GBM-NL-004`–`008` have no documents in the source dataset, so
  they get no `DocumentReference`/`DiagnosticReport` and only the clinical
  facts present in `participants.json` (no KPS/MGMT/IDH/resection observation).
  This is visible as real-world incompleteness, not missing code.
- Resection `Procedure` exists only where the dataset states a resection date
  (001, 002, 003) or the arrival fixture states one (009, 010). No date is
  invented for 005/006/008.
- Labs are deterministic synthetic values, not clinically meaningful results.
- No `Specimen`, `Provenance`, `Consent`, `ResearchStudy`/`ResearchSubject` or
  `QuestionnaireResponse` resources. `QuestionnaireResponse` + `Provenance`
  write-back is W5.
- Radiotherapy is one `Procedure` per course (mCODE course summary), not one per
  fraction.

## Verification

```bash
# Fresh HAPI database, then:
python3 fhir-seed/load.py --set baseline --check-counts
# -> FHIR seed OK: 169 bundle entries sent (169 unique resources; created 169, updated 0)
# -> validated 169 resources, 0 with errors
# -> DocumentReference on server: 10 (expected 10 for set baseline)

python3 fhir-seed/load.py --set baseline --no-validate --quiet --check-counts
# -> created 0, updated 169  (idempotent)

curl -s "http://127.0.0.1:8090/fhir/DocumentReference?_summary=count"
# -> "total": 10

python3 -m unittest discover -s fhir-seed/tests -v
# -> Ran 19 tests ... OK (skipped=1)
```

After loading arrivals as well, the union is 236 resources and 17
`DocumentReference` resources.

## Regenerating

```bash
python3 fhir-seed/generate.py
python3 -m unittest discover -s fhir-seed/tests -v
git add fhir-seed && git commit -m "FHIR seed: ..."
```

Inputs under `app/` are owned by other workstreams. If `participants.json`,
`documents.json`, `extractions.json` or the document texts change, regenerate
and commit the result; `generate.py --check` in CI/QA will fail until you do.
