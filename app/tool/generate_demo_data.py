#!/usr/bin/env python3
"""Generate the synthetic Yammic demo dataset.

Everything produced by this script is fictional. No real patients, no real
names, no real institutions, no live model calls. The "AI extractions" are
pre-computed fixtures that imitate an extractor output.

Usage:
    python3 app/tool/generate_demo_data.py

Outputs (under app/assets/data/):
    study.json          one fictional GBM trial + 3 sites + visit schedule + eCRF
    participants.json   8 pseudonymised participants ({"participants": [...]})
    documents/*.txt     10 fictional source documents
    documents.json      document index (asset path, language, sha256, charLength)
    extractions.json    flat AI extraction records with exact evidence spans
    dashboard.json      dashboard fixture that matches lib/models/models.dart

The generated JSON also satisfies the Dart contract in
app/lib/models/models.dart (see deliverables/demo_tech_spec.md).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any

APP = pathlib.Path(__file__).resolve().parents[1]
DATA = APP / "assets" / "data"
DOCS = DATA / "documents"

STUDY_ID = "GBM-NL-2026-01"
MODEL_ID = "demo-extractor v0.1"
PROMPT_VERSION = "prompt-2026-11-21"
GENERATED_AT = "2026-11-21T10:30:00+01:00"
DISCLAIMER = "Synthetic data \u2014 prototype, not for clinical use"
SCHEMA_VERSION = "1.0.0"

# --------------------------------------------------------------------------
# eCRF definition (CDISC-ish ids; terminology codes flagged when unverified)
# --------------------------------------------------------------------------

FIELDS: list[dict[str, Any]] = [
    {
        "id": "SUBJID",
        "label": "Subject identifier",
        "section": "identification",
        "valueType": "string",
        "required": True,
        "cdiscDomain": "DM",
        "cdiscVariable": "SUBJID",
        "cdiscVerified": True,
        "unit": None,
        "terminology": None,
        "help": "Pseudonymised participant code. Never a real name or hospital number.",
    },
    {
        "id": "SITEID",
        "label": "Site identifier",
        "section": "identification",
        "valueType": "string",
        "required": True,
        "cdiscDomain": "DM",
        "cdiscVariable": "SITEID",
        "cdiscVerified": True,
        "unit": None,
        "terminology": None,
        "help": "Fictional trial site code.",
    },
    {
        "id": "SEX",
        "label": "Sex at birth",
        "section": "demographics",
        "valueType": "coded",
        "required": True,
        "cdiscDomain": "DM",
        "cdiscVariable": "SEX",
        "cdiscVerified": True,
        "unit": None,
        "terminology": None,
        "allowedValues": [
            {
                "value": "F",
                "label": "Female",
                "code": {
                    "system": "SNOMED CT",
                    "code": "248152002",
                    "display": "Female",
                    "codeVerified": True,
                },
            },
            {
                "value": "M",
                "label": "Male",
                "code": {
                    "system": "SNOMED CT",
                    "code": "248153007",
                    "display": "Male",
                    "codeVerified": True,
                },
            },
        ],
        "help": "Synthetic sex value; no relation to any real person.",
    },
    {
        "id": "AGE",
        "label": "Age at diagnosis (years)",
        "section": "demographics",
        "valueType": "integer",
        "required": True,
        "cdiscDomain": "DM",
        "cdiscVariable": "AGE",
        "cdiscVerified": True,
        "unit": "years",
        "terminology": None,
        "min": 18,
        "max": 100,
        "help": "Whole years at the fictional diagnosis date.",
    },
    {
        "id": "MHSTDAT",
        "label": "Date of diagnosis",
        "section": "diagnosis",
        "valueType": "date",
        "required": True,
        "cdiscDomain": "MH",
        "cdiscVariable": "MHSTDAT",
        "cdiscVerified": True,
        "unit": None,
        "terminology": None,
        "help": "ISO 8601 date (yyyy-mm-dd) of the fictional histological diagnosis.",
    },
    {
        "id": "HISTOLOGY",
        "label": "Histology (central review)",
        "section": "diagnosis",
        "valueType": "coded",
        "required": True,
        "cdiscDomain": "MH",
        "cdiscVariable": "MHTERM",
        "cdiscVerified": True,
        "unit": None,
        "terminology": {
            "system": "ICD-O-3",
            "code": "9440/3",
            "display": "Glioblastoma, NOS",
            "codeVerified": True,
            "equivalent": [
                {
                    "system": "SNOMED CT",
                    "code": "393563007",
                    "display": "Glioblastoma (morphologic abnormality)",
                    "codeVerified": False,
                }
            ],
        },
        "help": "ICD-O-3 morphology 9440/3. SNOMED CT equivalent not verified for demo.",
    },
    {
        "id": "IDHSTAT",
        "label": "IDH1/2 mutation status",
        "section": "diagnosis",
        "valueType": "coded",
        "required": True,
        "cdiscDomain": "LB",
        "cdiscVariable": "LBORRES",
        "cdiscVerified": True,
        "unit": None,
        "terminology": {
            "system": "SNOMED CT",
            "code": "445048000",
            "display": "IDH1 wild type",
            "codeVerified": False,
        },
        "allowedValues": [
            {"value": "wildtype", "label": "IDH-wildtype"},
            {"value": "mutant", "label": "IDH-mutant"},
            {"value": "indeterminate", "label": "Indeterminate / not assessable"},
        ],
        "help": "Placeholder SNOMED CT code; marked unverified on purpose.",
    },
    {
        "id": "MGMTPROM",
        "label": "MGMT promoter methylation",
        "section": "diagnosis",
        "valueType": "coded",
        "required": True,
        "cdiscDomain": "LB",
        "cdiscVariable": "LBORRES",
        "cdiscVerified": True,
        "unit": None,
        "terminology": {
            "system": "LOINC",
            "code": "88199-1",
            "display": "MGMT promoter methylation [Presence] in Tissue",
            "codeVerified": False,
        },
        "allowedValues": [
            {"value": "methylated", "label": "Methylated"},
            {"value": "unmethylated", "label": "Unmethylated"},
            {"value": "indeterminate", "label": "Indeterminate / failed"},
        ],
        "help": "Placeholder LOINC code; marked unverified on purpose.",
    },
    {
        "id": "KPS",
        "label": "Karnofsky Performance Status",
        "section": "clinical_status",
        "valueType": "integer",
        "required": True,
        "cdiscDomain": "QS",
        "cdiscVariable": "QSORRES",
        "cdiscVerified": False,
        "unit": "%",
        "terminology": {
            "system": "LOINC",
            "code": "89261-2",
            "display": "Karnofsky Performance Status score",
            "codeVerified": False,
        },
        "min": 0,
        "max": 100,
        "help": "KPS in steps of 10. Placeholder LOINC code, unverified.",
    },
    {
        "id": "EXTRES",
        "label": "Extent of resection",
        "section": "surgery",
        "valueType": "coded",
        "required": True,
        "cdiscDomain": "PR",
        "cdiscVariable": "PRTRT",
        "cdiscVerified": False,
        "unit": None,
        "terminology": {
            "system": "SNOMED CT",
            "code": "262143007",
            "display": "Extent of surgical resection",
            "codeVerified": False,
        },
        "allowedValues": [
            {"value": "gross_total", "label": "Gross total resection"},
            {"value": "subtotal", "label": "Subtotal resection"},
            {"value": "biopsy", "label": "Biopsy only"},
            {"value": "not_assessable", "label": "Not assessable"},
        ],
        "help": "Surgeon/radiology wording. Placeholder SNOMED CT code, unverified.",
    },
    {
        "id": "RTDOSE",
        "label": "Radiotherapy total dose",
        "section": "treatment",
        "valueType": "number",
        "required": True,
        "cdiscDomain": "EX",
        "cdiscVariable": "EXDOSE",
        "cdiscVerified": True,
        "unit": "Gy",
        "terminology": {
            "system": "UCUM",
            "code": "Gy",
            "display": "gray",
            "codeVerified": True,
        },
        "min": 0,
        "max": 80,
        "help": "Total dose in gray, Stupp-style 60 Gy.",
    },
    {
        "id": "RTFRAC",
        "label": "Radiotherapy fractions",
        "section": "treatment",
        "valueType": "integer",
        "required": True,
        "cdiscDomain": "EX",
        "cdiscVariable": "EXDOSFRQ",
        "cdiscVerified": False,
        "unit": "fractions",
        "terminology": None,
        "min": 1,
        "max": 40,
        "help": "Number of fractions. CDISC variable is a demo approximation.",
    },
    {
        "id": "TMZPLNC",
        "label": "Planned adjuvant temozolomide cycles",
        "section": "treatment",
        "valueType": "integer",
        "required": True,
        "cdiscDomain": "EX",
        "cdiscVariable": "EXDOSTOT",
        "cdiscVerified": False,
        "unit": "cycles",
        "terminology": {
            "system": "ATC",
            "code": "L01AX03",
            "display": "temozolomide",
            "codeVerified": True,
        },
        "min": 0,
        "max": 12,
        "help": "Planned adjuvant cycles after chemoradiotherapy.",
    },
    {
        "id": "AEGRADE",
        "label": "Maximum adverse event grade (CTCAE v5.0)",
        "section": "safety",
        "valueType": "integer",
        "required": False,
        "cdiscDomain": "AE",
        "cdiscVariable": "AETOXGR",
        "cdiscVerified": True,
        "unit": "grade",
        "terminology": None,
        "min": 0,
        "max": 5,
        "help": "0 = no adverse event recorded; 1-5 = CTCAE v5.0 grade.",
    },
    {
        "id": "PROGDAT",
        "label": "Date of progression (RANO)",
        "section": "outcome",
        "valueType": "date",
        "required": False,
        "cdiscDomain": "RS",
        "cdiscVariable": "RSDTC",
        "cdiscVerified": True,
        "unit": None,
        "terminology": None,
        "help": "Leave blank until a RANO assessment documents progression.",
    },
]

FIELD_BY_ID = {f["id"]: f for f in FIELDS}

SECTIONS = [
    {"id": "identification", "label": "Identification"},
    {"id": "demographics", "label": "Demographics"},
    {"id": "diagnosis", "label": "Diagnosis"},
    {"id": "clinical_status", "label": "Clinical status"},
    {"id": "surgery", "label": "Surgery"},
    {"id": "treatment", "label": "Treatment"},
    {"id": "safety", "label": "Safety"},
    {"id": "outcome", "label": "Outcome"},
]

# --------------------------------------------------------------------------
# Sites and visit schedule
# --------------------------------------------------------------------------

SITES = [
    {
        "id": "SITE-01",
        "name": "Fictief Universitair Medisch Centrum Zuidhaven",
        "shortName": "FUMC Zuidhaven (fictional)",
        "city": "Zuidhaven",
        "country": "NL",
        "principalInvestigator": "Dr. A. Voorbeeld (fictional)",
        "status": "open",
        "targetEnrolment": 10,
        "currentEnrolment": 3,
        "openQueries": 4,
    },
    {
        "id": "SITE-02",
        "name": "Fictief Universitair Medisch Centrum Noordhaven",
        "shortName": "FUMC Noordhaven (fictional)",
        "city": "Noordhaven",
        "country": "NL",
        "principalInvestigator": "Dr. B. Voorbeeld (fictional)",
        "status": "open",
        "targetEnrolment": 8,
        "currentEnrolment": 3,
        "openQueries": 3,
    },
    {
        "id": "SITE-03",
        "name": "Fictief Streekziekenhuis Westpark",
        "shortName": "Westpark (fictional)",
        "city": "Westpark",
        "country": "NL",
        "principalInvestigator": "Dr. C. Voorbeeld (fictional)",
        "status": "open",
        "targetEnrolment": 6,
        "currentEnrolment": 2,
        "openQueries": 2,
    },
]

VISIT_SCHEDULE = [
    {"visitId": "V0", "name": "Screening", "dayFrom": -14, "dayTo": 0, "windowDays": 0, "repeating": False},
    {"visitId": "V1", "name": "Baseline", "dayFrom": 0, "dayTo": 0, "windowDays": 0, "repeating": False},
    {"visitId": "V2", "name": "Radiotherapy start", "dayFrom": 14, "dayTo": 14, "windowDays": 7, "repeating": False},
    {"visitId": "V3", "name": "Radiotherapy end", "dayFrom": 56, "dayTo": 56, "windowDays": 7, "repeating": False},
    {"visitId": "V4", "name": "TMZ cycle 1", "dayFrom": 63, "dayTo": 63, "windowDays": 7, "repeating": False},
    {"visitId": "V5", "name": "TMZ cycle 2", "dayFrom": 91, "dayTo": 91, "windowDays": 7, "repeating": False},
    {"visitId": "V6", "name": "TMZ cycle 3", "dayFrom": 119, "dayTo": 119, "windowDays": 7, "repeating": False},
    {"visitId": "V7", "name": "TMZ cycle 4", "dayFrom": 147, "dayTo": 147, "windowDays": 7, "repeating": False},
    {"visitId": "V8", "name": "TMZ cycle 5", "dayFrom": 175, "dayTo": 175, "windowDays": 7, "repeating": False},
    {"visitId": "V9", "name": "TMZ cycle 6", "dayFrom": 203, "dayTo": 203, "windowDays": 7, "repeating": False},
    {"visitId": "V10", "name": "End of treatment", "dayFrom": 231, "dayTo": 238, "windowDays": 14, "repeating": False},
    {"visitId": "V11", "name": "Follow-up (8-weekly)", "dayFrom": 287, "dayTo": 287, "windowDays": 14, "repeating": True},
    {"visitId": "V12", "name": "Survival follow-up (12-weekly)", "dayFrom": 371, "dayTo": 371, "windowDays": 28, "repeating": True},
]

STUDY = {
    "schemaVersion": SCHEMA_VERSION,
    "generatedAt": GENERATED_AT,
    "synthetic": True,
    "disclaimer": DISCLAIMER,
    "study": {
        "id": STUDY_ID,
        "shortName": "ReDiReCCT-GB Demo (synthetic)",
        "title": "A fictional phase II study of standard chemoradiotherapy with biomarker follow-up in newly diagnosed glioblastoma, IDH-wildtype",
        "registryId": "NL-DEMO-0000 (fictional, not a real registry entry)",
        "phase": "II",
        "indication": "Glioblastoma, IDH-wildtype (WHO CNS5, 2021)",
        "sponsor": "Stichting Fictieve Neuro-Oncologie (fictional)",
        "coordinatingSite": "SITE-01",
        "protocolVersion": "1.0 (2026-11-21)",
        "protocolStatus": "approved (fictional)",
        "status": "recruiting",
        "targetEnrolment": 24,
        "currentEnrolment": 8,
        "enrolmentOpenedOn": "2026-06-01",
        "plannedLastPatientIn": "2027-03-31",
        "primaryEndpoint": "Progression-free survival at 6 months by RANO criteria (fictional).",
        "secondaryEndpoints": [
            "Overall survival (fictional).",
            "eCRF data completeness after AI-assisted extraction (fictional).",
            "Reviewer time per extracted field (fictional, simulated).",
        ],
        "eligibilitySummary": [
            "Age 18 years or older (fictional).",
            "Histologically confirmed glioblastoma, IDH-wildtype (fictional).",
            "Karnofsky Performance Status 60 or higher (fictional).",
            "No prior radiotherapy to the brain (fictional).",
        ],
        "dataProvenance": {
            "kind": "synthetic_fixture",
            "realPatients": False,
            "liveModelCalls": False,
            "networkCalls": False,
            "note": "All participants, sites, documents and AI extractions are fictional fixtures.",
        },
    },
    "sites": SITES,
    "visitSchedule": VISIT_SCHEDULE,
    "ecrf": {
        "formId": "ECRF-GBM-BASELINE",
        "formVersion": "1.0",
        "label": "Glioblastoma baseline eCRF",
        "fieldsRequired": sum(1 for f in FIELDS if f["required"]),
        "sections": SECTIONS,
        "fields": FIELDS,
    },
}

# --------------------------------------------------------------------------
# Source documents (fictional, Dutch and English)
# --------------------------------------------------------------------------


class Doc:
    def __init__(self, doc_id: str, participant_id: str, doc_type: str,
                 title: str, language: str, document_date: str, text: str) -> None:
        self.id = doc_id
        self.participant_id = participant_id
        self.doc_type = doc_type
        self.title = title
        self.language = language
        self.document_date = document_date
        self.text = text

    def span(self, anchor: str, occurrence: int = 1) -> dict[str, Any]:
        start = 0
        idx = -1
        for _ in range(occurrence):
            idx = self.text.index(anchor, start)
            start = idx + 1
        return {"start": idx, "end": idx + len(anchor), "text": anchor}


DOC_001_PATH = Doc(
    "DOC-001-PATH",
    "GBM-NL-001",
    "pathology_report",
    "Pathologieverslag — stereotactisch resectiepreparaat (fictief)",
    "nl",
    "2026-06-05",
    """SYNTHETISCH DOCUMENT - FICTIEF - NIET VOOR KLINISCH GEBRUIK
Fictief Universitair Medisch Centrum Zuidhaven
Afdeling Pathologie
Prof. dr. J. Voorbeeld (fictief)

PATIENTCODE: GBM-NL-001
DATUM ONTVANGST: 2026-06-02
DATUM VERSLAG: 2026-06-05
ONDERZOEK: Resectiepreparaat, rechter frontaal

KLINISCHE GEGEVENS
Ruimte-innemende laesie rechts frontaal, verdacht voor hooggradig glioom.
Verwijzend neurochirurg: dr. M. Voorbeeld (fictief).

MACROSCOPIE
Meerdere fragmenten van grijs-wit weefsel, tesamen 24 gram.

MICROSCOPIE
Hypercellulair glioom met duidelijke nucleaire atypie, mitosen en
microvasculaire proliferatie. Gebieden met pseudopalisadering en necrose.
Immunohistochemie: GFAP positief. IDH1 R132H negatief. ATRX behouden.
MGMT-promotermethylering: methylatie aangetoond (MS-PCR).

CONCLUSIE
1. Glioblastoom, IDH-wildtype (WHO CNS5). ICD-O-3 morfologiecode 9440/3.
2. MGMT-promoter is gemethyleerd.
""",
)

DOC_001_MRI = Doc(
    "DOC-001-MRI",
    "GBM-NL-001",
    "radiology_report",
    "MRI-verslag hersenen, postoperatief (fictief)",
    "nl",
    "2026-06-06",
    """SYNTHETISCH DOCUMENT - FICTIEF - NIET VOOR KLINISCH GEBRUIK
Fictief Universitair Medisch Centrum Zuidhaven - Afdeling Radiologie

PATIENTCODE: GBM-NL-001
ONDERZOEK: MRI hersenen met contrast (postoperatief)
DATUM: 2026-06-06
AANVRAAG: postoperatieve staudevaluatie

VERSLAG
Status na rechter frontale craniotomie. Er is een reseptiecaviteit zichtbaar
zonder aantoonbaar residueel aankleurend tumorweefsel. Beoordeling: gross total
resectie. Geen nieuwe laesies. Geen tekenen van hydrocephalus.

Er is geen baseline RANO-meting van voor de operatie beschikbaar.
Progressie kan met dit onderzoek niet worden vastgesteld.
""",
)

DOC_001_DIS = Doc(
    "DOC-001-DIS",
    "GBM-NL-001",
    "discharge_letter",
    "Ontslagbrief neuro-oncologie (fictief)",
    "nl",
    "2026-06-08",
    """SYNTHETISCH DOCUMENT - FICTIEF - NIET VOOR KLINISCH GEBRUIK
Fictief Universitair Medisch Centrum Zuidhaven - Afdeling Neuro-oncologie

PATIENTCODE: GBM-NL-001
GESLACHT: vrouw
LEEFTIJD BIJ DIAGNOSE: 57 jaar
DATUM OPNAME: 2026-06-01
DATUM ONTSLAG: 2026-06-08

ONTSLAGBRIEF
Patient werd opgenomen voor een rechter frontale craniotomie. Histopathologisch
onderzoek toonde een glioblastoom, IDH-wildtype. Postoperatief beloop ongecompliceerd.

FUNCTIONELE STATUS
Karnofsky Performance Status bij ontslag: 80%.

BELEID
Adjuvante radiotherapie 60 Gy in 30 fracties met gelijktijdig temozolomide,
gevolgd door 6 geplande cycli adjuvante temozolomide. De eerste cyclus start
in week 5. Er zijn tot nu toe geen bijwerkingen van graad 3 of hoger opgetreden;
maximaal graad 2 vermoeidheid.
""",
)

DOC_002_PATH = Doc(
    "DOC-002-PATH",
    "GBM-NL-002",
    "pathology_report",
    "Pathology report — stereotactic biopsy (fictional)",
    "en",
    "2026-05-08",
    """SYNTHETIC DOCUMENT - FICTIONAL - NOT FOR CLINICAL USE
Fictional University Medical Center Northhaven - Department of Pathology
Reported by: Dr. R. Example (fictional)

SUBJECT CODE: GBM-NL-002
SPECIMEN RECEIVED: 2026-05-06
REPORT DATE: 2026-05-08
PROCEDURE: Resection specimen, left temporal lobe

MICROSCOPY
Infiltrating high-grade astrocytic tumour with necrosis and microvascular
proliferation. IDH1 R132H immunohistochemistry is negative; sequencing shows
no IDH1 or IDH2 mutation. MGMT promoter is unmethylated by pyrosequencing.
ATRX expression retained.

DIAGNOSIS
Glioblastoma, IDH-wildtype (WHO CNS5). ICD-O-3 morphology code 9440/3.
MGMT promoter: unmethylated.
""",
)

DOC_002_MRI = Doc(
    "DOC-002-MRI",
    "GBM-NL-002",
    "radiology_report",
    "MRI report, post-operative (fictional)",
    "en",
    "2026-05-12",
    """SYNTHETIC DOCUMENT - FICTIONAL - NOT FOR CLINICAL USE
Fictional University Medical Center Northhaven - Department of Radiology

SUBJECT CODE: GBM-NL-002
EXAMINATION: MRI brain with contrast (post-operative)
DATE: 2026-05-12

FINDINGS
Status post left temporal craniotomy. There is a thin rim of enhancement along
the resection cavity. The extent of resection is probably subtotal; a small
residual area may be present, although post-surgical change cannot be excluded.

No hydrocephalus. No new distant lesions.

IMPRESSION
Probable subtotal resection. RANO assessment is not available for this timepoint.
""",
)

DOC_002_SURG = Doc(
    "DOC-002-SURG",
    "GBM-NL-002",
    "operative_report",
    "Operative note — left temporal craniotomy (fictional)",
    "en",
    "2026-05-05",
    """SYNTHETIC DOCUMENT - FICTIONAL - NOT FOR CLINICAL USE
Fictional University Medical Center Northhaven - Department of Neurosurgery

SUBJECT CODE: GBM-NL-002
PROCEDURE: Left temporal craniotomy and tumour resection
DATE: 2026-05-05

OPERATIVE NOTE
Neuronavigation was used. Macroscopically, a subtotal resection was achieved
because the tumour involved the eloquent cortex. Residual tumour was left in
place intentionally. Estimated blood loss 250 mL. No intra-operative
complications.
""",
)

DOC_002_DIS = Doc(
    "DOC-002-DIS",
    "GBM-NL-002",
    "discharge_letter",
    "Discharge summary, neuro-oncology (fictional)",
    "en",
    "2026-05-09",
    """SYNTHETIC DOCUMENT - FICTIONAL - NOT FOR CLINICAL USE
Fictional University Medical Center Northhaven - Department of Neuro-Oncology

SUBJECT CODE: GBM-NL-002
SEX: male
AGE AT DIAGNOSIS: 64 years
ADMISSION DATE: 2026-05-04
DISCHARGE DATE: 2026-05-09

DISCHARGE SUMMARY
The patient underwent a left temporal craniotomy with subtotal resection of a
glioblastoma, IDH-wildtype. Post-operative course was uneventful.

FUNCTIONAL STATUS
Karnofsky Performance Status at discharge: 70%.

PLAN
Adjuvant radiotherapy 60 Gy in 30 fractions with concurrent temozolomide,
followed by 6 planned adjuvant temozolomide cycles. No adverse events above
grade 1 fatigue have been recorded.
""",
)

DOC_003_PATH = Doc(
    "DOC-003-PATH",
    "GBM-NL-003",
    "pathology_report",
    "Pathologieverslag — resectiepreparaat (fictief)",
    "nl",
    "2026-08-22",
    """SYNTHETISCH DOCUMENT - FICTIEF - NIET VOOR KLINISCH GEBRUIK
Fictief Streekziekenhuis Westpark - Laboratorium Pathologie

PATIENTCODE: GBM-NL-003
DATUM ONTVANGST: 2026-08-19
DATUM VERSLAG: 2026-08-22
ONDERZOEK: Resectiepreparaat, links parietaal

MICROSCOPIE
Hooggradig astrocytair glioom met necrose. IDH1 R132H negatief.
MGMT-promotermethylering: niet gemethyleerd.

CONCLUSIE
Glioblastoom, IDH-wildtype (WHO CNS5), ICD-O-3 9440/3.
""",
)

DOC_003_MRI = Doc(
    "DOC-003-MRI",
    "GBM-NL-003",
    "radiology_report",
    "MRI-verslag hersenen, postoperatief (fictief)",
    "nl",
    "2026-08-25",
    """SYNTHETISCH DOCUMENT - FICTIEF - NIET VOOR KLINISCH GEBRUIK
Fictief Streekziekenhuis Westpark - Afdeling Radiologie

PATIENTCODE: GBM-NL-003
ONDERZOEK: MRI hersenen met contrast
DATUM: 2026-08-25

VERSLAG
Postoperatieve situatie na links parietale craniotomie. Subtotale resectie met
een klein residueel contrast-aankleurend gebied. Geen tekenen van progressie.
Een RANO-beoordeling is voor dit tijdstip nog niet verricht.
""",
)

DOC_003_DIS = Doc(
    "DOC-003-DIS",
    "GBM-NL-003",
    "discharge_letter",
    "Ontslagbrief neurologie (fictief)",
    "nl",
    "2026-08-26",
    """SYNTHETISCH DOCUMENT - FICTIEF - NIET VOOR KLINISCH GEBRUIK
Fictief Streekziekenhuis Westpark - Afdeling Neurologie

PATIENTCODE: GBM-NL-003
GESLACHT: man
LEEFTIJD BIJ DIAGNOSE: 61 jaar
DATUM OPNAME: 2026-08-18
DATUM ONTSLAG: 2026-08-26

ONTSLAGBRIEF
Opname voor links parietale craniotomie. Histologie: glioblastoom, IDH-wildtype.
Postoperatief beloop zonder complicaties.

FUNCTIONELE STATUS
Karnofsky Performance Status bij ontslag: 90%.

BELEID
Radiotherapie 60 Gy in 30 fracties met gelijktijdig temozolomide. Aansluitend
6 geplande cycli adjuvante temozolomide. Tijdens opname graad 1 hoofdpijn,
geen graad 3 of hoger.
""",
)

DOCUMENTS = [
    DOC_001_PATH,
    DOC_001_MRI,
    DOC_001_DIS,
    DOC_002_PATH,
    DOC_002_MRI,
    DOC_002_SURG,
    DOC_002_DIS,
    DOC_003_PATH,
    DOC_003_MRI,
    DOC_003_DIS,
]

# --------------------------------------------------------------------------
# Pre-computed "AI" extractions
# --------------------------------------------------------------------------

extractions: list[dict[str, Any]] = []
_seed_counter = 0


def add_extraction(
    doc: Doc,
    field_id: str,
    value: Any,
    confidence: float,
    anchor: str,
    *,
    occurrence: int = 1,
    status: str = "proposed",
    code: dict[str, Any] | None = None,
    unit: str | None = None,
    display: str | None = None,
    abstention_reason: str | None = None,
    seeded: dict[str, Any] | None = None,
    review_state: str = "pending",
) -> None:
    global _seed_counter
    _seed_counter += 1
    field = FIELD_BY_ID[field_id]
    ev = doc.span(anchor, occurrence)
    display_value = display if display is not None else str(value)
    record: dict[str, Any] = {
        "id": f"EXT-{_seed_counter:04d}",
        "documentId": doc.id,
        "documentType": doc.doc_type,
        "documentDate": doc.document_date,
        "participantId": doc.participant_id,
        "field": field_id,
        "fieldLabel": field["label"],
        "status": status,
        "value": display_value,
        "normalizedValue": None if status == "abstained" else value,
        "unit": unit if unit is not None else field.get("unit"),
        "confidence": confidence,
        "proposedCode": code if status != "abstained" else None,
        "abstentionReason": abstention_reason,
        "sourceDocument": f"assets/data/documents/{doc.id}.txt",
        "sourceText": doc.text,
        "spanStart": ev["start"],
        "spanEnd": ev["end"],
        "evidence": [ev],
        "model": MODEL_ID,
        "promptVersion": PROMPT_VERSION,
        "reviewState": review_state,
        "seededIssue": seeded,
    }
    extractions.append(record)


def codes(system: str, code: str | None, display: str, verified: bool) -> dict[str, Any]:
    return {"system": system, "code": code, "display": display, "codeVerified": verified}


ICD_O_3 = {
    "system": "ICD-O-3",
    "code": "9440/3",
    "display": "Glioblastoma, NOS",
    "codeVerified": True,
    "equivalent": [
        {
            "system": "SNOMED CT",
            "code": "393563007",
            "display": "Glioblastoma (morphologic abnormality)",
            "codeVerified": False,
        }
    ],
}

# --- GBM-NL-001 -----------------------------------------------------------

add_extraction(DOC_001_PATH, "SUBJID", "GBM-NL-001", 0.99, "GBM-NL-001")
add_extraction(
    DOC_001_PATH, "SITEID", "SITE-01", 0.98,
    "Fictief Universitair Medisch Centrum Zuidhaven",
)
add_extraction(DOC_001_PATH, "HISTOLOGY", "glioblastoma_idh_wildtype", 0.98,
               "Glioblastoom, IDH-wildtype", code=ICD_O_3,
               display="Glioblastoma, IDH-wildtype")
add_extraction(DOC_001_PATH, "IDHSTAT", "wildtype", 0.96, "IDH1 R132H negatief",
               code=codes("SNOMED CT", "445048000", "IDH1 wild type", False),
               display="IDH-wildtype")
add_extraction(DOC_001_PATH, "MGMTPROM", "methylated", 0.93,
               "methylatie aangetoond (MS-PCR)",
               code=codes("LOINC", "88199-1",
                          "MGMT promoter methylation [Presence] in Tissue", False),
               display="Methylated")
add_extraction(DOC_001_PATH, "MHSTDAT", "2026-06-02", 0.91,
               "DATUM ONTVANGST: 2026-06-02", display="2026-06-02")

add_extraction(DOC_001_MRI, "EXTRES", "gross_total", 0.91, "gross total\nresectie",
               code=codes("SNOMED CT", "262143007", "Extent of surgical resection", False),
               display="Gross total resection")
add_extraction(
    DOC_001_MRI, "PROGDAT", "Not stated", 0.0,
    "Progressie kan met dit onderzoek niet worden vastgesteld.",
    status="abstained", abstention_reason="not_stated",
    seeded={"kind": "abstention",
            "note": "No RANO progression assessment exists in this document."},
)

add_extraction(DOC_001_DIS, "SEX", "F", 0.99, "GESLACHT: vrouw", display="Female")
add_extraction(DOC_001_DIS, "AGE", 57, 0.97, "LEEFTIJD BIJ DIAGNOSE: 57 jaar")
add_extraction(DOC_001_DIS, "KPS", 80, 0.90,
               "Karnofsky Performance Status bij ontslag: 80%",
               code=codes("LOINC", "89261-2", "Karnofsky Performance Status score", False))
add_extraction(DOC_001_DIS, "RTDOSE", 60, 0.96, "60 Gy in 30 fracties",
               code=codes("UCUM", "Gy", "gray", True))
add_extraction(DOC_001_DIS, "RTFRAC", 30, 0.96, "30 fracties")
add_extraction(DOC_001_DIS, "TMZPLNC", 6, 0.89, "6 geplande cycli",
               code=codes("ATC", "L01AX03", "temozolomide", True))
add_extraction(DOC_001_DIS, "AEGRADE", 2, 0.84, "maximaal graad 2 vermoeidheid")

# --- GBM-NL-002 -----------------------------------------------------------

add_extraction(DOC_002_PATH, "SUBJID", "GBM-NL-002", 0.99, "GBM-NL-002")
add_extraction(DOC_002_PATH, "SITEID", "SITE-02", 0.98,
               "Fictional University Medical Center Northhaven", occurrence=1)
add_extraction(DOC_002_PATH, "HISTOLOGY", "glioblastoma_idh_wildtype", 0.97,
               "Glioblastoma, IDH-wildtype", code=ICD_O_3,
               display="Glioblastoma, IDH-wildtype")
add_extraction(DOC_002_PATH, "IDHSTAT", "wildtype", 0.95,
               "IDH1 R132H immunohistochemistry is negative",
               code=codes("SNOMED CT", "445048000", "IDH1 wild type", False),
               display="IDH-wildtype")
# Deliberate demo case: the extractor proposes the OPPOSITE of the source text.
add_extraction(
    DOC_002_PATH, "MGMTPROM", "methylated", 0.72,
    "MGMT promoter is unmethylated",
    code=codes("LOINC", "88199-1",
               "MGMT promoter methylation [Presence] in Tissue", False),
    display="Methylated",
    seeded={
        "kind": "wrong_value",
        "expectedCorrectValue": "unmethylated",
        "expectedCorrectDisplay": "Unmethylated",
        "note": "Deliberate demo case: the proposal contradicts the highlighted evidence. Reviewer must correct it to unmethylated.",
    },
)
add_extraction(DOC_002_PATH, "MHSTDAT", "2026-05-06", 0.92,
               "SPECIMEN RECEIVED: 2026-05-06")

# Deliberate demo case: low confidence from hedged radiology wording.
add_extraction(
    DOC_002_MRI, "EXTRES", "subtotal", 0.45, "probably subtotal",
    code=codes("SNOMED CT", "262143007", "Extent of surgical resection", False),
    display="Subtotal resection",
    seeded={
        "kind": "low_confidence",
        "note": "Hedged wording ('probably subtotal'). Reviewer must verify against the operative note.",
    },
)
add_extraction(
    DOC_002_MRI, "PROGDAT", "Not stated", 0.0,
    "RANO assessment is not available for this timepoint.",
    status="abstained", abstention_reason="not_stated",
    seeded={"kind": "abstention",
            "note": "No RANO progression assessment in this report."},
)

add_extraction(DOC_002_SURG, "EXTRES", "subtotal", 0.93,
               "subtotal resection was achieved",
               code=codes("SNOMED CT", "262143007", "Extent of surgical resection", False),
               display="Subtotal resection")

add_extraction(DOC_002_DIS, "SEX", "M", 0.99, "SEX: male", display="Male")
add_extraction(DOC_002_DIS, "AGE", 64, 0.97, "AGE AT DIAGNOSIS: 64 years")
add_extraction(DOC_002_DIS, "KPS", 70, 0.90,
               "Karnofsky Performance Status at discharge: 70%",
               code=codes("LOINC", "89261-2", "Karnofsky Performance Status score", False))
add_extraction(DOC_002_DIS, "RTDOSE", 60, 0.96, "60 Gy in 30 fractions",
               code=codes("UCUM", "Gy", "gray", True))
add_extraction(DOC_002_DIS, "RTFRAC", 30, 0.96, "30 fractions")
add_extraction(DOC_002_DIS, "TMZPLNC", 6, 0.88,
               "6 planned adjuvant temozolomide cycles",
               code=codes("ATC", "L01AX03", "temozolomide", True))
add_extraction(DOC_002_DIS, "AEGRADE", 1, 0.82, "grade 1 fatigue")

# --- GBM-NL-003 -----------------------------------------------------------

add_extraction(DOC_003_PATH, "SUBJID", "GBM-NL-003", 0.99, "GBM-NL-003")
add_extraction(DOC_003_PATH, "SITEID", "SITE-03", 0.98,
               "Fictief Streekziekenhuis Westpark", occurrence=1)
add_extraction(DOC_003_PATH, "HISTOLOGY", "glioblastoma_idh_wildtype", 0.95,
               "Glioblastoom, IDH-wildtype", code=ICD_O_3,
               display="Glioblastoma, IDH-wildtype")
add_extraction(DOC_003_PATH, "IDHSTAT", "wildtype", 0.90, "IDH1 R132H negatief",
               code=codes("SNOMED CT", "445048000", "IDH1 wild type", False),
               display="IDH-wildtype")
add_extraction(DOC_003_PATH, "MGMTPROM", "unmethylated", 0.88, "niet gemethyleerd",
               code=codes("LOINC", "88199-1",
                          "MGMT promoter methylation [Presence] in Tissue", False),
               display="Unmethylated")
add_extraction(DOC_003_PATH, "MHSTDAT", "2026-08-19", 0.90,
               "DATUM ONTVANGST: 2026-08-19")

add_extraction(DOC_003_MRI, "EXTRES", "subtotal", 0.87, "Subtotale resectie",
               code=codes("SNOMED CT", "262143007", "Extent of surgical resection", False),
               display="Subtotal resection")
add_extraction(
    DOC_003_MRI, "PROGDAT", "Not stated", 0.0,
    "Een RANO-beoordeling is voor dit tijdstip nog niet verricht.",
    status="abstained", abstention_reason="not_stated",
    seeded={"kind": "abstention",
            "note": "Primary demo abstention: no RANO assessment has been performed yet."},
)

add_extraction(DOC_003_DIS, "SEX", "M", 0.99, "GESLACHT: man", display="Male")
add_extraction(DOC_003_DIS, "AGE", 61, 0.97, "LEEFTIJD BIJ DIAGNOSE: 61 jaar")
add_extraction(DOC_003_DIS, "KPS", 90, 0.86,
               "Karnofsky Performance Status bij ontslag: 90%",
               code=codes("LOINC", "89261-2", "Karnofsky Performance Status score", False))
add_extraction(DOC_003_DIS, "RTDOSE", 60, 0.95, "60 Gy in 30 fracties",
               code=codes("UCUM", "Gy", "gray", True))
add_extraction(DOC_003_DIS, "RTFRAC", 30, 0.95, "30 fracties")
add_extraction(DOC_003_DIS, "TMZPLNC", 6, 0.88, "6 geplande cycli",
               code=codes("ATC", "L01AX03", "temozolomide", True))
add_extraction(DOC_003_DIS, "AEGRADE", 1, 0.80, "graad 1 hoofdpijn")

# --------------------------------------------------------------------------
# Participants
# --------------------------------------------------------------------------


def ecrf(form: str, status: str, complete_pct: int) -> dict[str, Any]:
    return {"form": form, "status": status, "completePct": complete_pct}


def visit(name: str, date: str, status: str, note: str = "") -> dict[str, Any]:
    return {"name": name, "date": date, "status": status, "note": note}


def treatment(name: str, dose: str, start: str, end: str | None = None) -> dict[str, Any]:
    return {"name": name, "dose": dose, "start": start, "end": end}


PARTICIPANTS = [
    {
        "id": "GBM-NL-001",
        "studyId": STUDY_ID,
        "siteId": "SITE-01",
        "status": "active",
        "statusDetail": "on_treatment",
        "age": 57,
        "sex": "F",
        "summary": "Fictional participant: glioblastoma, IDH-wildtype, right frontal. Gross total resection 2026-06-01. Chemoradiotherapy completed 2026-07-31; adjuvant temozolomide cycle 4 of 6 done, cycle 5 due 2026-11-27.",
        "diagnosisDate": "2026-06-02",
        "enrolledDate": "2026-06-05",
        "documentIds": ["DOC-001-PATH", "DOC-001-MRI", "DOC-001-DIS"],
        "visits": [
            visit("Screening (V0)", "2026-05-22", "completed"),
            visit("Baseline (V1)", "2026-06-05", "completed"),
            visit("Radiotherapy start (V2)", "2026-06-19", "completed"),
            visit("Radiotherapy end (V3)", "2026-07-31", "completed"),
            visit("TMZ cycle 1 (V4)", "2026-08-07", "completed"),
            visit("TMZ cycle 2 (V5)", "2026-09-04", "completed"),
            visit("TMZ cycle 3 (V6)", "2026-10-02", "completed"),
            visit("TMZ cycle 4 (V7)", "2026-10-30", "completed"),
            visit("TMZ cycle 5 (V8)", "2026-11-27", "scheduled", "eCRF pre-populated, awaiting review"),
        ],
        "ecrfs": [
            ecrf("Baseline (V1)", "complete", 100),
            ecrf("TMZ cycle 5 (V8)", "awaiting_review", 80),
        ],
        "issues": [
            {"severity": "medium",
             "message": "MGMT value awaits human confirmation of the AI proposal.",
             "field": "MGMTPROM"},
            {"severity": "low",
             "message": "Progression date is not stated in any uploaded document.",
             "field": "PROGDAT"},
        ],
        "treatments": [
            treatment("Temozolomide (concurrent)", "75 mg/m2 daily", "2026-06-19", "2026-07-31"),
            treatment("Radiotherapy", "60 Gy / 30 fractions", "2026-06-19", "2026-07-31"),
            treatment("Temozolomide (adjuvant)", "200 mg/m2 days 1-5, 28-day cycle", "2026-08-07"),
        ],
    },
    {
        "id": "GBM-NL-002",
        "studyId": STUDY_ID,
        "siteId": "SITE-02",
        "status": "active",
        "statusDetail": "on_treatment",
        "age": 64,
        "sex": "M",
        "summary": "Fictional participant: glioblastoma, IDH-wildtype, left temporal. Subtotal resection 2026-05-05. Chemoradiotherapy completed 2026-07-13; adjuvant temozolomide cycle 5 of 6 done.",
        "diagnosisDate": "2026-05-06",
        "enrolledDate": "2026-05-15",
        "documentIds": ["DOC-002-PATH", "DOC-002-MRI", "DOC-002-SURG", "DOC-002-DIS"],
        "visits": [
            visit("Screening (V0)", "2026-05-01", "completed"),
            visit("Baseline (V1)", "2026-05-15", "completed"),
            visit("Radiotherapy start (V2)", "2026-06-01", "completed"),
            visit("Radiotherapy end (V3)", "2026-07-13", "completed"),
            visit("TMZ cycle 1 (V4)", "2026-07-20", "completed"),
            visit("TMZ cycle 2 (V5)", "2026-08-17", "completed"),
            visit("TMZ cycle 3 (V6)", "2026-09-14", "completed"),
            visit("TMZ cycle 4 (V7)", "2026-10-12", "completed"),
            visit("TMZ cycle 5 (V8)", "2026-11-09", "completed"),
            visit("TMZ cycle 6 (V9)", "2026-12-07", "scheduled"),
        ],
        "ecrfs": [
            ecrf("Baseline (V1)", "complete", 100),
            ecrf("TMZ cycle 5 (V8)", "in_progress", 60),
        ],
        "issues": [
            {"severity": "high",
             "message": "AI proposed 'methylated' but the pathology report states 'unmethylated'.",
             "field": "MGMTPROM"},
            {"severity": "medium",
             "message": "Extent of resection differs in wording between MRI and operative note.",
             "field": "EXTRES"},
        ],
        "treatments": [
            treatment("Temozolomide (concurrent)", "75 mg/m2 daily", "2026-06-01", "2026-07-13"),
            treatment("Radiotherapy", "60 Gy / 30 fractions", "2026-06-01", "2026-07-13"),
            treatment("Temozolomide (adjuvant)", "200 mg/m2 days 1-5, 28-day cycle", "2026-07-20"),
        ],
    },
    {
        "id": "GBM-NL-003",
        "studyId": STUDY_ID,
        "siteId": "SITE-03",
        "status": "active",
        "statusDetail": "on_treatment",
        "age": 61,
        "sex": "M",
        "summary": "Fictional participant: glioblastoma, IDH-wildtype, left parietal. Subtotal resection 2026-08-18. Chemoradiotherapy completed 2026-10-27; adjuvant temozolomide cycle 1 of 6 done. No RANO progression assessment yet.",
        "diagnosisDate": "2026-08-19",
        "enrolledDate": "2026-09-01",
        "documentIds": ["DOC-003-PATH", "DOC-003-MRI", "DOC-003-DIS"],
        "visits": [
            visit("Screening (V0)", "2026-08-14", "completed"),
            visit("Baseline (V1)", "2026-09-01", "completed"),
            visit("Radiotherapy start (V2)", "2026-09-15", "completed"),
            visit("Radiotherapy end (V3)", "2026-10-27", "completed"),
            visit("TMZ cycle 1 (V4)", "2026-11-03", "completed"),
            visit("TMZ cycle 2 (V5)", "2026-12-01", "scheduled"),
        ],
        "ecrfs": [
            ecrf("Baseline (V1)", "complete", 100),
            ecrf("TMZ cycle 1 (V4)", "awaiting_review", 73),
        ],
        "issues": [
            {"severity": "low",
             "message": "Progression date not yet applicable; no RANO assessment performed.",
             "field": "PROGDAT"},
        ],
        "treatments": [
            treatment("Temozolomide (concurrent)", "75 mg/m2 daily", "2026-09-15", "2026-10-27"),
            treatment("Radiotherapy", "60 Gy / 30 fractions", "2026-09-15", "2026-10-27"),
            treatment("Temozolomide (adjuvant)", "200 mg/m2 days 1-5, 28-day cycle", "2026-11-03"),
        ],
    },
    {
        "id": "GBM-NL-004",
        "studyId": STUDY_ID,
        "siteId": "SITE-01",
        "status": "screening",
        "statusDetail": "screening",
        "age": 52,
        "sex": "F",
        "summary": "Fictional participant: screening in progress after MRI showed a right frontal lesion. Histology and biomarker results are pending.",
        "diagnosisDate": None,
        "enrolledDate": None,
        "documentIds": [],
        "visits": [
            visit("Screening (V0)", "2026-11-24", "scheduled", "Screening visit planned"),
        ],
        "ecrfs": [ecrf("Baseline (V1)", "not_started", 0)],
        "issues": [
            {"severity": "medium",
             "message": "Histology and MGMT result not available yet.",
             "field": "HISTOLOGY"},
        ],
        "treatments": [],
    },
    {
        "id": "GBM-NL-005",
        "studyId": STUDY_ID,
        "siteId": "SITE-02",
        "status": "active",
        "statusDetail": "on_treatment",
        "age": 70,
        "sex": "M",
        "summary": "Fictional participant: glioblastoma, IDH-wildtype. Chemoradiotherapy completed 2026-11-13; adjuvant temozolomide cycle 1 started 2026-11-20.",
        "diagnosisDate": "2026-09-02",
        "enrolledDate": "2026-09-18",
        "documentIds": [],
        "visits": [
            visit("Screening (V0)", "2026-09-04", "completed"),
            visit("Baseline (V1)", "2026-09-18", "completed"),
            visit("Radiotherapy start (V2)", "2026-10-02", "completed"),
            visit("Radiotherapy end (V3)", "2026-11-13", "completed"),
            visit("TMZ cycle 1 (V4)", "2026-11-20", "completed"),
            visit("TMZ cycle 2 (V5)", "2026-12-18", "scheduled"),
        ],
        "ecrfs": [
            ecrf("Baseline (V1)", "complete", 100),
            ecrf("TMZ cycle 1 (V4)", "in_progress", 45),
        ],
        "issues": [],
        "treatments": [
            treatment("Temozolomide (concurrent)", "75 mg/m2 daily", "2026-10-02", "2026-11-13"),
            treatment("Radiotherapy", "60 Gy / 30 fractions", "2026-10-02", "2026-11-13"),
            treatment("Temozolomide (adjuvant)", "200 mg/m2 days 1-5, 28-day cycle", "2026-11-20"),
        ],
    },
    {
        "id": "GBM-NL-006",
        "studyId": STUDY_ID,
        "siteId": "SITE-03",
        "status": "completed",
        "statusDetail": "in_follow_up",
        "age": 68,
        "sex": "F",
        "summary": "Fictional participant: glioblastoma, IDH-wildtype. All 6 adjuvant temozolomide cycles completed 2026-05-29. In 8-weekly follow-up; no progression documented.",
        "diagnosisDate": "2025-11-20",
        "enrolledDate": "2025-12-05",
        "documentIds": [],
        "visits": [
            visit("Screening (V0)", "2025-11-21", "completed"),
            visit("Baseline (V1)", "2025-12-05", "completed"),
            visit("Radiotherapy start (V2)", "2025-12-19", "completed"),
            visit("Radiotherapy end (V3)", "2026-01-30", "completed"),
            visit("TMZ cycle 6 (V9)", "2026-05-29", "completed"),
            visit("End of treatment (V10)", "2026-06-26", "completed"),
            visit("Follow-up (V11)", "2026-08-21", "completed"),
            visit("Follow-up (V11)", "2026-10-16", "completed"),
            visit("Follow-up (V11)", "2026-12-11", "scheduled"),
        ],
        "ecrfs": [
            ecrf("Baseline (V1)", "complete", 100),
            ecrf("End of treatment (V10)", "complete", 100),
        ],
        "issues": [],
        "treatments": [
            treatment("Radiotherapy", "60 Gy / 30 fractions", "2025-12-19", "2026-01-30"),
            treatment("Temozolomide (adjuvant)", "200 mg/m2 days 1-5, 28-day cycle", "2026-02-06", "2026-05-29"),
        ],
    },
    {
        "id": "GBM-NL-007",
        "studyId": STUDY_ID,
        "siteId": "SITE-01",
        "status": "withdrawn",
        "statusDetail": "screen_failure",
        "age": 59,
        "sex": "M",
        "summary": "Fictional participant: screen failure. Tumour was IDH-mutant, so the participant did not meet the IDH-wildtype eligibility criterion.",
        "diagnosisDate": "2026-10-21",
        "enrolledDate": None,
        "documentIds": [],
        "visits": [
            visit("Screening (V0)", "2026-10-27", "completed", "Screen failure: IDH-mutant"),
            visit("Baseline (V1)", "2026-11-10", "missed", "Not required after screen failure"),
        ],
        "ecrfs": [ecrf("Baseline (V1)", "not_started", 0)],
        "issues": [
            {"severity": "high",
             "message": "Participant did not meet the IDH-wildtype eligibility criterion.",
             "field": "IDHSTAT"},
        ],
        "treatments": [],
    },
    {
        "id": "GBM-NL-008",
        "studyId": STUDY_ID,
        "siteId": "SITE-02",
        "status": "withdrawn",
        "statusDetail": "consent_withdrawn",
        "age": 47,
        "sex": "F",
        "summary": "Fictional participant: withdrew informed consent on 2026-08-20 after temozolomide cycle 1. No further data collection.",
        "diagnosisDate": "2026-07-08",
        "enrolledDate": "2026-07-10",
        "documentIds": [],
        "visits": [
            visit("Screening (V0)", "2026-07-06", "completed"),
            visit("Baseline (V1)", "2026-07-10", "completed"),
            visit("Radiotherapy start (V2)", "2026-07-24", "completed"),
            visit("TMZ cycle 1 (V4)", "2026-08-14", "completed"),
            visit("TMZ cycle 2 (V5)", "2026-09-11", "missed", "Consent withdrawn"),
        ],
        "ecrfs": [ecrf("Baseline (V1)", "complete", 100)],
        "issues": [],
        "treatments": [
            treatment("Temozolomide (concurrent)", "75 mg/m2 daily", "2026-07-24", "2026-08-20"),
        ],
    },
]

# --------------------------------------------------------------------------
# Serialisation helpers
# --------------------------------------------------------------------------


def write_json(path: pathlib.Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)

    doc_index = []
    for doc in DOCUMENTS:
        path = DOCS / f"{doc.id}.txt"
        path.write_text(doc.text, encoding="utf-8")
        encoded = doc.text.encode("utf-8")
        doc_index.append({
            "id": doc.id,
            "participantId": doc.participant_id,
            "type": doc.doc_type,
            "title": doc.title,
            "language": doc.language,
            "documentDate": doc.document_date,
            "assetPath": f"assets/data/documents/{doc.id}.txt",
            "charLength": len(doc.text),
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "synthetic": True,
        })

    documents_json = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": GENERATED_AT,
        "synthetic": True,
        "disclaimer": DISCLAIMER,
        "note": "Document text lives in the listed .txt files. Extractions embed a copy as sourceText; validate_data.py checks both copies and every evidence span.",
        "documents": doc_index,
    }

    per_doc_summary = []
    for doc in DOCUMENTS:
        rows = [e for e in extractions if e["documentId"] == doc.id]
        per_doc_summary.append({
            "documentId": doc.id,
            "proposedFields": sum(1 for e in rows if e["status"] == "proposed"),
            "abstainedFields": sum(1 for e in rows if e["status"] == "abstained"),
            "extractionIds": [e["id"] for e in rows],
        })

    extractions_json = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": GENERATED_AT,
        "synthetic": True,
        "disclaimer": DISCLAIMER,
        "generator": {
            "modelId": MODEL_ID,
            "promptVersion": PROMPT_VERSION,
            "runId": "demo-fixture-2026-11-21",
            "liveModelCalls": False,
            "note": "Pre-computed fixture that imitates an extractor. No model was called.",
        },
        "seededDemoCases": {
            "lowConfidence": {
                "extractionId": next(e["id"] for e in extractions if (e.get("seededIssue") or {}).get("kind") == "low_confidence"),
                "documentId": "DOC-002-MRI",
                "field": "EXTRES",
                "confidence": 0.45,
                "whatToShow": "Hedged wording ('probably subtotal') gives a low-confidence proposal that needs reviewer verification.",
            },
            "wrongValue": {
                "extractionId": next(e["id"] for e in extractions if (e.get("seededIssue") or {}).get("kind") == "wrong_value"),
                "documentId": "DOC-002-PATH",
                "field": "MGMTPROM",
                "proposedValue": "methylated",
                "expectedCorrectValue": "unmethylated",
                "whatToShow": "The AI says 'methylated' but the highlighted source text says 'unmethylated'. The reviewer corrects it.",
            },
            "abstention": {
                "extractionId": next(e["id"] for e in extractions if (e.get("seededIssue") or {}).get("kind") == "abstention"),
                "documentId": "DOC-003-MRI",
                "field": "PROGDAT",
                "whatToShow": "The extractor abstains ('not stated') because no RANO assessment exists yet.",
            },
        },
        "documents": per_doc_summary,
        "extractions": extractions,
    }

    dashboard_json = {
        "synthetic": True,
        "disclaimer": DISCLAIMER,
        "studies": [
            {
                "id": STUDY_ID,
                "title": "ReDiReCCT-GB Demo (synthetic)",
                "phase": "II",
                "target": 24,
                "enrolled": 8,
                "completeness": 0.71,
            }
        ],
        "sites": [
            {
                "id": site["id"],
                "name": site["shortName"],
                "studyId": STUDY_ID,
                "target": site["targetEnrolment"],
                "enrolled": site["currentEnrolment"],
                "openQueries": site["openQueries"],
            }
            for site in SITES
        ],
        "milestones": [
            {"studyId": STUDY_ID, "name": "First patient in", "date": "2026-06-05", "done": True},
            {"studyId": STUDY_ID, "name": "Interim safety review", "date": "2026-12-15", "done": False},
            {"studyId": STUDY_ID, "name": "Database lock", "date": "2027-06-30", "done": False},
        ],
        "alerts": [
            {"studyId": STUDY_ID, "severity": "warning",
             "message": "GBM-NL-002: AI MGMT proposal contradicts the pathology report."},
            {"studyId": STUDY_ID, "severity": "warning",
             "message": "GBM-NL-002: resection extent differs between MRI and operative note."},
            {"studyId": STUDY_ID, "severity": "info",
             "message": "3 extractions are low-confidence or abstained and need review."},
        ],
        "tasks": [
            {"studyId": STUDY_ID, "title": "Review AI extractions for TMZ cycle 5",
             "due": "2026-11-24", "assignee": "Research nurse (demo)", "participantId": "GBM-NL-001"},
            {"studyId": STUDY_ID, "title": "Correct MGMT promoter value",
             "due": "2026-11-24", "assignee": "Data manager (demo)", "participantId": "GBM-NL-002"},
            {"studyId": STUDY_ID, "title": "Check screening eligibility",
             "due": "2026-11-25", "assignee": "Research nurse (demo)", "participantId": "GBM-NL-004"},
        ],
    }

    participants_json = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": GENERATED_AT,
        "synthetic": True,
        "disclaimer": DISCLAIMER,
        "studyId": STUDY_ID,
        "participants": PARTICIPANTS,
    }

    write_json(DATA / "study.json", STUDY)
    write_json(DATA / "participants.json", participants_json)
    write_json(DATA / "documents.json", documents_json)
    write_json(DATA / "extractions.json", extractions_json)
    write_json(DATA / "dashboard.json", dashboard_json)

    print(f"Wrote {len(DOCUMENTS)} documents, {len(extractions)} extractions, "
          f"{len(PARTICIPANTS)} participants, {len(FIELDS)} eCRF fields to {DATA}")


if __name__ == "__main__":
    main()
