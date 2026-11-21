# Synthetic demo dataset (GBM)

**Everything in this folder is fictional and synthetic. It contains no real
patient data, no real names, no real institutions and no live AI output. It is
a prototype fixture, not for clinical use.**

Every screen that shows this data must display:
`Synthetic data — prototype, not for clinical use`.

## Files

| File | Purpose |
|---|---|
| `study.json` | One fictional glioblastoma (IDH-wildtype) trial, 3 fictional Dutch sites, the visit schedule and the 15-field baseline eCRF with target terminology. |
| `participants.json` | 8 pseudonymised participants (`GBM-NL-001` … `GBM-NL-008`), statuses, visits, eCRF completion, quality issues, treatments. |
| `documents.json` | Index of the 10 source documents: owner, type, language, date, asset path, length and sha256. |
| `documents/*.txt` | The source document text (pathology, radiology, operative, discharge). Dutch or English, each with a synthetic banner. |
| `extractions.json` | Pre-computed AI extractions: one flat record per document field, with confidence, proposed code, model/prompt and exact evidence character spans. |
| `dashboard.json` | Dashboard fixture (one study, 3 sites, milestones, alerts, tasks). |
| `validate_data.py` | See `app/tool/`. |

The JSON is consumed by `app/lib/models/models.dart`. The app contract is:
`participants.json` → `{"participants": [...]}` and
`extractions.json` → `{"extractions": [...]}`. Extra keys in a record are
ignored by the Dart models, so this dataset can stay richer than the models.

## Generator and validation

```bash
# regenerate all files from app/tool/generate_demo_data.py
python3 app/tool/generate_demo_data.py

# independent check of every span, checksum and cross-reference
python3 app/tool/validate_data.py
```

`validate_data.py` exits non-zero if any evidence span does not match the
document text exactly. Run it after any data change and before the demo.

## Evidence spans

Each extraction carries:

```json
{
  "documentId": "DOC-001-PATH",
  "field": "HISTOLOGY",
  "status": "proposed",
  "value": "Glioblastoma, IDH-wildtype",
  "normalizedValue": "glioblastoma_idh_wildtype",
  "confidence": 0.98,
  "proposedCode": { "system": "ICD-O-3", "code": "9440/3", "display": "Glioblastoma, NOS", "codeVerified": true },
  "sourceDocument": "assets/data/documents/DOC-001-PATH.txt",
  "sourceText": "<full document text, embedded for the review screen>",
  "spanStart": 512,
  "spanEnd": 538,
  "evidence": [{ "start": 512, "end": 538, "text": "Glioblastoom, IDH-wildtype" }],
  "model": "demo-extractor v0.1",
  "promptVersion": "prompt-2026-11-21",
  "abstentionReason": null,
  "seededIssue": null,
  "reviewState": "pending"
}
```

Rules:

- `start` / `end` are a **half-open** interval `[start, end)` into `sourceText`.
  Index 0 is the first character. `sourceText.substring(start, end)` equals
  `evidence[0].text` exactly, including spaces and line breaks.
- Offsets are Dart `String` indices (UTF-16 code units). The corpus contains no
  characters outside the Basic Multilingual Plane, so code-unit and code-point
  offsets are identical. Do not add emoji to a document.
- `spanStart` / `spanEnd` mirror `evidence[0]` for the simple one-span case used
  by `AiExtraction`. `evidence` is a list so a value can cite more than one
  sentence later; keep `evidence[0]` as the primary highlight.
- `value` is always a display string (e.g. `"80"`, `"Gross total resection"`,
  `"2026-06-02"`). `normalizedValue` is the typed value the app can compare.
- `status` is `proposed` (a value exists) or `abstained` (the document does not
  state it). An abstention has `value: "Not stated"`, `confidence: 0`,
  `normalizedValue: null`, `proposedCode: null` and an `abstentionReason`
  (currently `not_stated`).
- `codeVerified: true` means the terminology code was checked. `false` means it
  is a demo placeholder and must not be presented as a valid coded value.
  Several fields intentionally use placeholders (IDH, MGMT, KPS, extent of
  resection).

## Deliberate demo cases

`extractions.json.seededDemoCases` points directly at three records. Do not
"fix" them: they are the script for the review demo.

| Case | Where | What the demo shows |
|---|---|---|
| Low confidence | `DOC-002-MRI` / `EXTRES`, confidence `0.38` | Hedged wording ("probably subtotal") needs human verification. |
| Wrong value to correct | `DOC-002-PATH` / `MGMTPROM` | The AI proposes `methylated`; the highlighted source says `unmethylated`. The reviewer corrects it. |
| Abstention | `DOC-003-MRI` / `PROGDAT` | The AI returns "Not stated" because no RANO assessment exists yet. |

Two more abstentions exist (`DOC-001-MRI`, `DOC-002-MRI`) so the queue looks
realistic.

## Field identifiers and terminology

Field ids are CDISC-ish and stable: `SUBJID`, `SITEID`, `SEX`, `AGE`,
`MHSTDAT`, `HISTOLOGY`, `IDHSTAT`, `MGMTPROM`, `KPS`, `EXTRES`, `RTDOSE`,
`RTFRAC`, `TMZPLNC`, `AEGRADE`, `PROGDAT`.

`study.json.ecrf.fields` is the source of truth for labels, sections, value
type, unit, allowed values, CDISC variable and target terminology. Each field
carries `cdiscVerified`; each code carries `codeVerified`. Unverified codes are
demo placeholders, not authoritative mappings.

## Participants and documents

| Participant | Site | Status | Documents |
|---|---|---|---|
| `GBM-NL-001` | SITE-01 | active, on treatment | pathology (nl), MRI (nl), discharge (nl) |
| `GBM-NL-002` | SITE-02 | active, on treatment | pathology (en), MRI (en), operative note (en), discharge (en) |
| `GBM-NL-003` | SITE-03 | active, on treatment | pathology (nl), MRI (nl), discharge (nl) |
| `GBM-NL-004` | SITE-01 | screening | none |
| `GBM-NL-005` | SITE-02 | active | none |
| `GBM-NL-006` | SITE-03 | completed, follow-up | none |
| `GBM-NL-007` | SITE-01 | withdrawn, screen failure (IDH-mutant) | none |
| `GBM-NL-008` | SITE-02 | withdrawn, consent withdrawn | none |

Participant `status` uses the app enum `screening | enrolled | active |
completed | withdrawn`. The finer state is in the extra key `statusDetail`.

## What this dataset is not

- Not real patient data and not derived from real records.
- Not a validated terminology mapping.
- Not model output from a real call; the extraction records are hand-written
  fixtures, generated by `app/tool/generate_demo_data.py`.
- Not for clinical, regulatory or publication use.
