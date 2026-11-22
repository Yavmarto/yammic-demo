#!/usr/bin/env python3
"""Build synthetic FHIR R4 transaction bundles for the Yamicc demo.

Inputs (read-only, owned by other workstreams):
    app/assets/data/participants.json
    app/assets/data/study.json
    app/assets/data/documents.json
    app/assets/data/extractions.json
    app/assets/data/documents/*.txt

Extra inputs (owned by this workstream):
    fhir-seed/source/arrivals.json
    fhir-seed/source/documents/*.txt

Outputs (all generated, commit them so `make reset` needs no generator run):
    fhir-seed/shared/codesystems.json
    fhir-seed/baseline/organizations.json
    fhir-seed/baseline/patient-GBM-NL-001.json  ...  -008
    fhir-seed/baseline/manifest.json
    fhir-seed/arrivals/organizations.json
    fhir-seed/arrivals/patient-GBM-NL-009.json ... -011
    fhir-seed/arrivals/manifest.json

Every resource carries meta.tag SYNTHETIC and meta.security HTEST. All data is
fictional. Bundles use transaction entries with PUT + client-assigned ids, so
loading them twice is idempotent.

Usage:
    python3 fhir-seed/generate.py            # write the bundles
    python3 fhir-seed/generate.py --check    # fail if the files on disk differ
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import pathlib
import random
import re
import sys
from datetime import date as date_cls, timedelta
from typing import Any

SEED_DIR = pathlib.Path(__file__).resolve().parent
REPO = SEED_DIR.parent
DATA = REPO / "app" / "assets" / "data"
SOURCE = SEED_DIR / "source"

GENERATED_AT = "2026-11-21T10:30:00+01:00"
AS_OF = "2026-11-21"
STUDY_ID = "GBM-NL-2026-01"
SERVER_BASE = "http://127.0.0.1:8090/fhir"
TZ = "+01:00"

CS = {
    "provenance": "https://yamicc.example/fhir/CodeSystem/data-provenance",
    "mgmt": "https://yamicc.example/fhir/CodeSystem/mgmt-promoter-status",
    "procedure": "https://yamicc.example/fhir/CodeSystem/procedure-type",
    "extent": "https://yamicc.example/fhir/CodeSystem/resection-extent",
    "doc_id": "https://yamicc.example/fhir/NamingSystem/hospital-document-id",
    "subject_id": "https://yamicc.example/fhir/NamingSystem/study-subject-id",
    "study_no": "https://yamicc.example/fhir/NamingSystem/study-number",
    "site_id": "https://yamicc.example/fhir/NamingSystem/trial-site-id",
    "mrn": "urn:oid:2.16.840.1.113883.4.9999",
    "snomed": "http://snomed.info/sct",
    "loinc": "http://loinc.org",
    "icdo3": "http://terminology.hl7.org/CodeSystem/icd-o-3",
    "atc": "http://www.whocc.no/atc",
    "ucum": "http://unitsofmeasure.org",
    "v2-0203": "http://terminology.hl7.org/CodeSystem/v2-0203",
    "v2-0074": "http://terminology.hl7.org/CodeSystem/v2-0074",
    "v3-actreason": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
    "v3-interpretation": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
    "v3-actcode": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "v3-route": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
    "condition-clinical": "http://terminology.hl7.org/CodeSystem/condition-clinical",
    "condition-ver": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
    "condition-category": "http://terminology.hl7.org/CodeSystem/condition-category",
    "diagnosis-role": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
    "observation-category": "http://terminology.hl7.org/CodeSystem/observation-category",
    "us-core-doc": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
}

SYNTHETIC_TAG = {
    "system": CS["provenance"],
    "code": "SYNTHETIC",
    "display": "Synthetic demo data",
}
TEST_SECURITY = {
    "system": CS["v3-actreason"],
    "code": "HTEST",
    "display": "test health data",
}

MCODE_PROFILES = {
    "Patient": "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-cancer-patient",
    "Condition": "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-primary-cancer-condition",
    "Observation": "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-cancer-disease-status",
    "Procedure": "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-cancer-related-surgical-procedure",
    "MedicationRequest": "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-cancer-related-medication-request",
    "DiagnosticReport": "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-cancer-genomics-report",
}

NATO = [
    "Alfa", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel",
    "India", "Juliett", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa",
]

DOC_TYPES = {
    "pathology_report": {
        "loinc": ("11526-1", "Pathology study"),
        "category": ("PAT", "Pathology"),
        "diagnostic_report": True,
    },
    "radiology_report": {
        "loinc": ("18748-4", "Diagnostic imaging study"),
        "category": ("RAD", "Radiology"),
        "diagnostic_report": True,
    },
    "operative_report": {
        "loinc": ("28570-0", "Procedure note"),
        "category": ("GE", "General"),
        "diagnostic_report": False,
    },
    "discharge_letter": {
        "loinc": ("34133-9", "Summary of episode note"),
        "category": ("GE", "General"),
        "diagnostic_report": False,
    },
    "clinic_letter": {
        "loinc": ("34133-9", "Summary of episode note"),
        "category": ("GE", "General"),
        "diagnostic_report": False,
    },
}

GBM_SNOMED = ("393563007", "Glioblastoma (morphologic abnormality)")
GBM_ICDO3 = ("9440/3", "Glioblastoma, NOS")
IDH_WT_SNOMED = ("445048000", "IDH1 wild type")
MGMT_LOINC = ("88199-1", "MGMT promoter methylation [Presence] in Tissue")
KPS_LOINC = ("89261-2", "Karnofsky Performance Status score")
EXTRES_SNOMED = ("262143007", "Extent of surgical resection")
TMZ_ATC = ("L01AX03", "temozolomide")
ORAL_ROUTE_SNOMED = ("26643006", "Oral route")


# --------------------------------------------------------------------------- utils
def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def narrative(*lines: str) -> dict[str, str]:
    body = "".join(f"<p>{esc(line)}</p>" for line in lines if line)
    return {
        "status": "generated",
        "div": f'<div xmlns="http://www.w3.org/1999/xhtml">{body}</div>',
    }


def finish(resource: dict[str, Any], *, line: str, mcode: bool = False) -> dict[str, Any]:
    meta = resource.setdefault("meta", {})
    meta["tag"] = [SYNTHETIC_TAG]
    meta["security"] = [TEST_SECURITY]
    if mcode and mcode_enabled() and resource["resourceType"] in MCODE_PROFILES:
        meta["profile"] = [MCODE_PROFILES[resource["resourceType"]]]
    resource["text"] = narrative(line)
    return resource


_PROFILES_FLAG = {"enabled": False}


def mcode_enabled() -> bool:
    return bool(_PROFILES_FLAG["enabled"])


def ref(resource_type: str, resource_id: str) -> dict[str, str]:
    return {"reference": f"{resource_type}/{resource_id}"}


def coding(system: str, code: str, display: str | None = None) -> dict[str, str]:
    out = {"system": system, "code": code}
    if display:
        out["display"] = display
    return out


def codeable(system: str, code: str, display: str | None = None, text: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"coding": [coding(system, code, display)]}
    if text:
        out["text"] = text
    return out


def quantity(value: float | int, unit: str, code: str | None = None) -> dict[str, Any]:
    return {
        "value": value,
        "unit": unit,
        "system": CS["ucum"],
        "code": code or unit,
    }


def ts(date: str, time: str = "10:00:00") -> str:
    return f"{date}T{time}{TZ}"


def money_round(value: float, digits: int) -> float | int:
    out = round(value, digits)
    return int(out) if digits == 0 else out


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: pathlib.Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


# ------------------------------------------------------------------- source data
def load_study() -> dict[str, Any]:
    return load_json(DATA / "study.json")


def load_baseline_participants() -> list[dict[str, Any]]:
    return load_json(DATA / "participants.json")["participants"]


def load_documents() -> list[dict[str, Any]]:
    return load_json(DATA / "documents.json")["documents"]


def load_arrivals() -> list[dict[str, Any]]:
    return load_json(SOURCE / "arrivals.json")["participants"]


def load_hospital2() -> dict[str, Any]:
    return load_json(SOURCE / "hospital2.json")



def extraction_values() -> dict[str, dict[str, Any]]:
    data = load_json(DATA / "extractions.json")
    values: dict[str, dict[str, Any]] = {}
    for item in data["extractions"]:
        if item.get("status") == "abstained" or item.get("value") in (None, "Not stated"):
            continue
        values.setdefault(item["participantId"], {})[item["field"]] = item["value"]
    return values


def document_text(doc: dict[str, Any], *, arrivals: bool) -> str:
    if arrivals:
        return (SOURCE / "documents" / doc["file"]).read_text(encoding="utf-8")
    relative = doc["assetPath"].replace("assets/data/", "")
    return (DATA / relative).read_text(encoding="utf-8")


# ---------------------------------------------------------------- normalisation
def as_int(value: Any) -> int | None:
    if value is None:
        return None
    match = re.search(r"-?\d+", str(value))
    return int(match.group(0)) if match else None


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    match = re.search(r"-?\d+(?:[.,]\d+)?", str(value))
    return float(match.group(0).replace(",", ".")) if match else None


def norm_sex(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).casefold()
    if text.startswith("f") or text.startswith("vrouw"):
        return "female"
    if text.startswith("m") or text.startswith("man"):
        return "male"
    return None


def norm_mgmt(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).casefold()
    if "unmethyl" in text or "niet gemethyleerd" in text:
        return "unmethylated"
    if "methyl" in text:
        return "methylated"
    if "indeterminate" in text:
        return "indeterminate"
    return None


def norm_idh(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).casefold()
    if "mutant" in text:
        return "mutant"
    if "wild" in text:
        return "wildtype"
    if "indeterminate" in text:
        return "indeterminate"
    return None


def norm_extent(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).casefold()
    if "gross" in text or "totaal" in text:
        return "gross_total"
    if "subtotal" in text or "sub-total" in text or "partie" in text:
        return "subtotal"
    if "biopsy" in text:
        return "biopsy"
    if "not" in text:
        return "not_assessable"
    return None


EXTENT_LABEL = {
    "gross_total": "Gross total resection",
    "subtotal": "Subtotal resection",
    "biopsy": "Biopsy only",
    "not_assessable": "Not assessable",
}

CONDITION_LABEL = {
    "gbm_idh_wildtype": "Glioblastoma, IDH-wildtype",
    "glioma_idh_mutant": "Diffuse glioma, IDH-mutant",
    "suspected_lesion": "Space-occupying lesion of the brain",
}


def parse_treatments(participant: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "rt": None,
        "tmz_concurrent": None,
        "tmz_adjuvant": None,
    }
    for treatment in participant.get("treatments") or []:
        name = treatment.get("name", "")
        lower = name.casefold()
        if lower.startswith("radiotherapy"):
            dose = as_float(treatment.get("dose"))
            fractions = None
            match = re.search(r"/\s*(\d+)\s*fractions", treatment.get("dose", ""), re.I)
            if match:
                fractions = int(match.group(1))
            out["rt"] = {
                "start": treatment.get("start"),
                "end": treatment.get("end"),
                "dose": dose or 60.0,
                "fractions": fractions or 30,
            }
        elif lower.startswith("temozolomide"):
            item = {
                "start": treatment.get("start"),
                "end": treatment.get("end"),
                "doseText": treatment.get("dose"),
            }
            if "concurrent" in lower:
                out["tmz_concurrent"] = item
            elif "adjuvant" in lower:
                out["tmz_adjuvant"] = item
    return out


def parse_summary(summary: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    match = re.search(r"(Gross total|Subtotal) resection (\d{4}-\d{2}-\d{2})", summary, re.I)
    if match:
        extent = "gross_total" if match.group(1).casefold() == "gross total" else "subtotal"
        out["surgery"] = {"date": match.group(2), "extent": extent, "procedure": "resection"}
    match = re.search(r"\b(right|left)\s+(frontal|temporal|parietal|occipital)\b", summary, re.I)
    if match:
        out["bodySite"] = f"{match.group(1).capitalize()} {match.group(2).lower()} lobe"
    return out


def condition_type(participant: dict[str, Any]) -> str:
    explicit = (participant.get("condition") or {}).get("type")
    if explicit:
        return explicit
    summary = participant.get("summary", "")
    if re.search(r"IDH[- ]mutant", summary, re.I):
        return "glioma_idh_mutant"
    if re.search(r"glioblastoma", summary, re.I):
        return "gbm_idh_wildtype"
    return "suspected_lesion"


def completed_cycles(participant: dict[str, Any]) -> list[dict[str, Any]]:
    cycles: list[dict[str, Any]] = []
    for visit in participant.get("visits") or []:
        match = re.search(r"TMZ cycle\s+(\d+)", visit.get("name", ""), re.I)
        if match and visit.get("status") == "completed" and visit.get("date"):
            cycles.append({"number": int(match.group(1)), "date": visit["date"]})
    cycles.sort(key=lambda item: (item["date"], item["number"]))
    return cycles


def build_record(participant: dict[str, Any], *, extractions: dict[str, Any], site: dict[str, Any],
                 documents: list[dict[str, Any]], arrivals: bool) -> dict[str, Any]:
    clinical = participant.get("clinical") or {}
    summary = parse_summary(participant.get("summary", ""))
    treatments = parse_treatments(participant)

    kps = as_int(clinical.get("kps", extractions.get("KPS")))
    mgmt = norm_mgmt(clinical.get("mgmt", extractions.get("MGMTPROM")))
    idh = norm_idh(clinical.get("idh", extractions.get("IDHSTAT")))
    extent = norm_extent(clinical.get("extentOfResection", extractions.get("EXTRES")))
    max_ae = as_int(clinical.get("maxAeGrade", extractions.get("AEGRADE")))

    surgery = participant.get("surgery") or summary.get("surgery")
    if surgery and not surgery.get("extent"):
        surgery = dict(surgery, extent=extent or "not_assessable")

    rt = participant.get("radiotherapy") or treatments["rt"]
    if rt:
        rt = {
            "start": rt.get("start"),
            "end": rt.get("end"),
            "dose": as_float(rt.get("doseGy", rt.get("dose"))) or 60.0,
            "fractions": as_int(rt.get("fractions")) or 30,
        }

    tmz = participant.get("temozolomide")
    if tmz:
        tmz = {
            "concurrentStart": tmz.get("concurrentStart"),
            "concurrentEnd": tmz.get("concurrentEnd"),
            "adjuvantStart": tmz.get("adjuvantStart"),
            "adjuvantEnd": tmz.get("adjuvantEnd"),
            "plannedCycles": as_int(tmz.get("plannedCycles")) or 6,
        }
    else:
        concurrent = treatments["tmz_concurrent"]
        adjuvant = treatments["tmz_adjuvant"]
        tmz = {
            "concurrentStart": concurrent and concurrent.get("start"),
            "concurrentEnd": concurrent and concurrent.get("end"),
            "adjuvantStart": adjuvant and adjuvant.get("start"),
            "adjuvantEnd": adjuvant and adjuvant.get("end"),
            "plannedCycles": 6,
        }

    cycles = participant.get("completedCycles") or completed_cycles(participant)
    if cycles and not tmz.get("adjuvantStart"):
        tmz["adjuvantStart"] = cycles[0]["date"]
    condition = participant.get("condition") or {}
    body_site = condition.get("bodySite") or summary.get("bodySite")
    reference_date = (
        participant.get("diagnosisDate")
        or (participant.get("visits") or [{}])[0].get("date")
        or "2026-06-01"
    )

    return {
        "id": participant["id"],
        "site": site,
        "sex": norm_sex(participant.get("sex")),
        "age": as_int(participant.get("age")),
        "status": participant.get("status"),
        "statusDetail": participant.get("statusDetail"),
        "summary": participant.get("summary", ""),
        "diagnosisDate": participant.get("diagnosisDate"),
        "enrolledDate": participant.get("enrolledDate"),
        "referenceDate": reference_date,
        "conditionType": condition_type(participant),
        "verificationStatus": condition.get("verificationStatus")
        or ("provisional" if condition_type(participant) == "suspected_lesion" else "confirmed"),
        "bodySite": body_site,
        "kps": kps,
        "mgmt": mgmt,
        "idh": idh,
        "extent": extent,
        "maxAe": max_ae,
        "surgery": surgery,
        "rt": rt if rt and rt.get("start") else None,
        "tmz": tmz,
        "cycles": cycles,
        "documents": documents,
        "arrivals": arrivals,
        "visits": participant.get("visits") or [],
    }


# ------------------------------------------------------------------- resources
def organizations(study: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for site in study["sites"]:
        resource = {
            "resourceType": "Organization",
            "id": site["id"],
            "identifier": [
                {
                    "system": CS["site_id"],
                    "value": site["id"],
                    "type": {"text": "Trial site identifier"},
                }
            ],
            "active": True,
            "type": [{"text": "Hospital"}],
            "name": site["name"],
            "alias": [site["shortName"]],
            "address": [{"city": site["city"], "country": site["country"]}],
        }
        out.append(finish(resource, line=f"{site['name']} — {site['city']}, {site['country']} (fictional)"))
    return out


def code_systems() -> list[dict[str, Any]]:
    specs = [
        (
            "yamicc-data-provenance",
            "Yamicc data provenance",
            "Provenance markers used by the Yamicc demo platform.",
            [("SYNTHETIC", "Synthetic demo data")],
        ),
        (
            "mgmt-promoter-status",
            "MGMT promoter methylation status",
            "Demo value set for MGMT promoter methylation. Not a licensed terminology.",
            [
                ("methylated", "Methylated"),
                ("unmethylated", "Unmethylated"),
                ("indeterminate", "Indeterminate or failed"),
            ],
        ),
        (
            "procedure-type",
            "Yamicc demo procedure type",
            "Demo procedure categories used where no verified SNOMED CT code is available in the source dataset.",
            [
                ("brain-tumour-resection", "Resection of brain tumour"),
                ("brain-tumour-biopsy", "Stereotactic biopsy of brain tumour"),
                ("external-beam-radiotherapy", "External beam radiotherapy course"),
            ],
        ),
        (
            "resection-extent",
            "Extent of surgical resection",
            "Demo value set for the extent of tumour resection.",
            [
                ("gross-total", "Gross total resection"),
                ("subtotal", "Subtotal resection"),
                ("biopsy", "Biopsy only"),
                ("not-assessable", "Not assessable"),
            ],
        ),
    ]
    out = []
    for code, name, description, concepts in specs:
        resource = {
            "resourceType": "CodeSystem",
            "id": code,
            "url": f"https://yamicc.example/fhir/CodeSystem/{code}",
            "identifier": [{"system": "urn:ietf:rfc:3986", "value": f"https://yamicc.example/fhir/CodeSystem/{code}"}],
            "version": "1.0.0",
            "name": "".join(part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", name)),
            "title": name,
            "status": "active",
            "experimental": True,
            "publisher": "Yamicc demo (synthetic)",
            "description": description,
            "caseSensitive": True,
            "content": "fragment",
            "concept": [{"code": c, "display": d} for c, d in concepts],
        }
        out.append(finish(resource, line=f"{name} — synthetic local code system"))
    return out


def patient_resource(record: dict[str, Any]) -> dict[str, Any]:
    pid = record["id"]
    number = int(pid.rsplit("-", 1)[-1])
    site_number = record["site"]["id"].rsplit("-", 1)[-1]
    given = NATO[(number - 1) % len(NATO)]
    birth_year = int(record["referenceDate"][:4]) - (record["age"] or 60)
    resource = {
        "resourceType": "Patient",
        "id": pid,
        "identifier": [
            {
                "use": "usual",
                "type": {"coding": [coding(CS["v2-0203"], "MR", "Medical record number")]},
                "system": CS["mrn"],
                "value": f"MRN-{site_number}-{100 + number:05d}",
                "assigner": {"display": record["site"]["name"]},
            },
            {
                "type": {"text": "Study subject identifier"},
                "system": CS["subject_id"],
                "value": pid,
            },
            {
                "type": {"text": "Study identifier"},
                "system": CS["study_no"],
                "value": STUDY_ID,
            },
        ],
        "active": record["status"] != "withdrawn",
        "name": [
            {
                "use": "official",
                "family": "Proefpersoon",
                "given": [given],
                "text": f"{given} Proefpersoon (fictional)",
            }
        ],
        "gender": record["sex"] or "unknown",
        "birthDate": str(birth_year),
        "managingOrganization": ref("Organization", record["site"]["id"]),
    }
    if record["statusDetail"] == "screen_failure":
        resource["active"] = False
    out = finish(
        resource,
        line=f"{given} Proefpersoon — synthetic GBM participant {pid}, {record['age']} years, "
             f"{record['sex']}, {record['site']['name']}",
        mcode=True,
    )
    return out


def condition_resource(record: dict[str, Any], encounter_id: str | None) -> dict[str, Any] | None:
    kind = record["conditionType"]
    pid = record["id"]
    clinical = "inactive" if record["status"] == "withdrawn" else "active"
    if kind == "gbm_idh_wildtype":
        code: dict[str, Any] = {
            "coding": [
                coding(CS["snomed"], GBM_SNOMED[0], GBM_SNOMED[1]),
                coding(CS["icdo3"], GBM_ICDO3[0], GBM_ICDO3[1]),
            ],
            "text": "Glioblastoma, IDH-wildtype (WHO CNS5)",
        }
    elif kind == "glioma_idh_mutant":
        code = {"text": "Diffuse glioma, IDH-mutant (ICD-O-3 morphology not assigned in source)"}
    else:
        code = {"text": "Space-occupying lesion of the brain, suspected high-grade glioma"}

    resource = {
        "resourceType": "Condition",
        "id": f"COND-{pid}-PRIMARY",
        "clinicalStatus": {"coding": [coding(CS["condition-clinical"], clinical)]},
        "verificationStatus": {"coding": [coding(CS["condition-ver"], record["verificationStatus"])]},
        "category": [{"coding": [coding(CS["condition-category"], "problem-list-item", "Problem list item")]}],
        "code": code,
        "subject": ref("Patient", pid),
        "onsetDateTime": record["diagnosisDate"] or record["referenceDate"],
        "recordedDate": ts(record["diagnosisDate"] or record["referenceDate"]),
        "note": [{"text": "Synthetic diagnosis record. IDH/MGMT and resection details are in Observations."}],
    }
    if record["bodySite"]:
        resource["bodySite"] = [{"text": record["bodySite"]}]
    if encounter_id:
        resource["encounter"] = ref("Encounter", encounter_id)
    label = CONDITION_LABEL.get(kind, "Condition")
    return finish(resource, line=f"{label} — {record['bodySite'] or 'site not stated'} ({pid})", mcode=True)


def encounter_resource(record: dict[str, Any], encounter_id: str) -> dict[str, Any]:
    pid = record["id"]
    surgery = record["surgery"]
    rt = record["rt"]
    if surgery and surgery.get("date"):
        period = {"start": ts(surgery["date"], "08:00:00"), "end": ts(add_days(surgery["date"], 4), "18:00:00")}
        encounter_class = "IMP"
        label = "Surgical admission"
    elif rt:
        period = {"start": ts(rt["start"], "08:00:00"), "end": ts(rt.get("end") or rt["start"], "18:00:00")}
        encounter_class = "AMB"
        label = "Chemoradiotherapy course"
    else:
        day = record["referenceDate"]
        period = {"start": ts(day, "09:00:00"), "end": ts(day, "10:00:00")}
        encounter_class = "AMB"
        label = "Screening visit"

    status = "finished"
    if period["start"][:10] > AS_OF:
        status = "planned"
    elif period["end"][:10] > AS_OF:
        status = "in-progress"

    resource: dict[str, Any] = {
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": status,
        "class": coding(CS["v3-actcode"], encounter_class, "inpatient encounter" if encounter_class == "IMP" else "ambulatory"),
        "type": [{"text": label}],
        "subject": ref("Patient", pid),
        "period": period,
        "serviceProvider": ref("Organization", record["site"]["id"]),
    }
    if record["conditionType"] in ("gbm_idh_wildtype", "glioma_idh_mutant"):
        resource["diagnosis"] = [
            {
                "condition": ref("Condition", f"COND-{pid}-PRIMARY"),
                "use": {"coding": [coding(CS["diagnosis-role"], "DD", "Diagnosis")]},
                "rank": 1,
            }
        ]
    return finish(resource, line=f"{label} for {pid} ({status}) — synthetic encounter")


def observation_kps(record: dict[str, Any], encounter_id: str) -> dict[str, Any] | None:
    if record["kps"] is None:
        return None
    pid = record["id"]
    day = record["diagnosisDate"] or record["referenceDate"]
    resource = {
        "resourceType": "Observation",
        "id": f"OBS-{pid}-KPS",
        "status": "final",
        "category": [
            {"coding": [coding(CS["observation-category"], "exam", "Exam")], "text": "Clinical assessment"}
        ],
        "code": {
            "coding": [coding(CS["loinc"], KPS_LOINC[0], KPS_LOINC[1])],
            "text": "Karnofsky Performance Status",
        },
        "subject": ref("Patient", pid),
        "encounter": ref("Encounter", encounter_id),
        "effectiveDateTime": ts(day),
        "valueQuantity": quantity(record["kps"], "%", "%"),
        "note": [{"text": "LOINC code is a demo placeholder; see app/assets/data/study.json codeVerified=false."}],
    }
    return finish(resource, line=f"KPS {record['kps']}% for {pid} on {day}", mcode=True)


def observation_mgmt(record: dict[str, Any], encounter_id: str) -> dict[str, Any] | None:
    if not record["mgmt"]:
        return None
    pid = record["id"]
    day = record["diagnosisDate"] or record["referenceDate"]
    resource = {
        "resourceType": "Observation",
        "id": f"OBS-{pid}-MGMT",
        "status": "final",
        "category": [
            {"coding": [coding(CS["observation-category"], "laboratory", "Laboratory")], "text": "Biomarker"}
        ],
        "code": {
            "coding": [coding(CS["loinc"], MGMT_LOINC[0], MGMT_LOINC[1])],
            "text": "MGMT promoter methylation",
        },
        "subject": ref("Patient", pid),
        "encounter": ref("Encounter", encounter_id),
        "effectiveDateTime": ts(day),
        "valueCodeableConcept": {
            "coding": [coding(CS["mgmt"], record["mgmt"], record["mgmt"].capitalize())],
            "text": record["mgmt"].capitalize(),
        },
        "note": [{"text": "LOINC code is a demo placeholder; value uses a synthetic local code system."}],
    }
    return finish(resource, line=f"MGMT promoter {record['mgmt']} for {pid}", mcode=True)


def observation_idh(record: dict[str, Any], encounter_id: str) -> dict[str, Any] | None:
    if not record["idh"]:
        return None
    pid = record["id"]
    day = record["diagnosisDate"] or record["referenceDate"]
    value: dict[str, Any] = {
        "text": "IDH-wildtype" if record["idh"] == "wildtype" else f"IDH-{record['idh']}",
    }
    if record["idh"] == "wildtype":
        value["coding"] = [coding(CS["snomed"], IDH_WT_SNOMED[0], IDH_WT_SNOMED[1])]
    resource = {
        "resourceType": "Observation",
        "id": f"OBS-{pid}-IDH",
        "status": "final",
        "category": [
            {"coding": [coding(CS["observation-category"], "laboratory", "Laboratory")], "text": "Biomarker"}
        ],
        "code": {"text": "IDH1/2 mutation status"},
        "subject": ref("Patient", pid),
        "encounter": ref("Encounter", encounter_id),
        "effectiveDateTime": ts(day),
        "valueCodeableConcept": value,
        "note": [{"text": "SNOMED CT code is a demo placeholder for IDH-wildtype (study.json codeVerified=false)."}],
    }
    return finish(resource, line=f"IDH status {record['idh']} for {pid}", mcode=True)


def observation_extent(record: dict[str, Any], encounter_id: str) -> dict[str, Any] | None:
    if not record["extent"]:
        return None
    pid = record["id"]
    day = (record["surgery"] or {}).get("date") or record["diagnosisDate"] or record["referenceDate"]
    resource = {
        "resourceType": "Observation",
        "id": f"OBS-{pid}-EXTRES",
        "status": "final",
        "category": [
            {"coding": [coding(CS["observation-category"], "exam", "Exam")], "text": "Clinical assessment"}
        ],
        "code": {
            "coding": [coding(CS["snomed"], EXTRES_SNOMED[0], EXTRES_SNOMED[1])],
            "text": "Extent of surgical resection",
        },
        "subject": ref("Patient", pid),
        "encounter": ref("Encounter", encounter_id),
        "effectiveDateTime": ts(day),
        "valueCodeableConcept": {
            "coding": [coding(CS["extent"], record["extent"].replace("_", "-"), EXTENT_LABEL[record["extent"]])],
            "text": EXTENT_LABEL[record["extent"]],
        },
        "note": [{"text": "SNOMED CT code is a demo placeholder (study.json codeVerified=false)."}],
    }
    return finish(resource, line=f"{EXTENT_LABEL[record['extent']]} for {pid}", mcode=True)


LAB_SPECS = [
    {
        "key": "HB",
        "loinc": ("718-7", "Hemoglobin [Mass/volume] in Blood"),
        "unit": "g/dL",
        "low": 12.0,
        "high": 17.5,
        "range": (10.8, 15.6),
        "digits": 1,
    },
    {
        "key": "WBC",
        "loinc": ("6690-2", "Leukocytes [#/volume] in Blood by Automated count"),
        "unit": "10*3/uL",
        "low": 4.0,
        "high": 10.0,
        "range": (3.2, 9.6),
        "digits": 1,
    },
    {
        "key": "PLT",
        "loinc": ("777-3", "Platelets [#/volume] in Blood by Automated count"),
        "unit": "10*3/uL",
        "low": 150.0,
        "high": 400.0,
        "range": (110.0, 390.0),
        "digits": 0,
    },
    {
        "key": "ANC",
        "loinc": ("26464-8", "Neutrophils [#/volume] in Blood"),
        "unit": "10*3/uL",
        "low": 1.8,
        "high": 7.5,
        "range": (1.2, 7.2),
        "digits": 1,
    },
    {
        "key": "ALT",
        "loinc": ("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma"),
        "unit": "U/L",
        "low": 7.0,
        "high": 35.0,
        "range": (12.0, 58.0),
        "digits": 0,
    },
    {
        "key": "CREA",
        "loinc": ("2160-0", "Creatinine [Mass/volume] in Serum or Plasma"),
        "unit": "mg/dL",
        "low": 0.6,
        "high": 1.3,
        "range": (0.55, 1.25),
        "digits": 2,
    },
]


def lab_observations(record: dict[str, Any], encounter_id: str) -> list[dict[str, Any]]:
    pid = record["id"]
    timepoints = []
    if record["diagnosisDate"]:
        timepoints.append(("BL", record["diagnosisDate"]))
    if record["rt"]:
        timepoints.append(("OT", add_days(record["rt"]["start"], 14)))
    if not timepoints and record["referenceDate"]:
        timepoints.append(("BL", record["referenceDate"]))

    rng = random.Random(int(hashlib.sha256(pid.encode()).hexdigest()[:8], 16))
    out = []
    for label, day in timepoints:
        for spec in LAB_SPECS:
            value = money_round(rng.uniform(*spec["range"]), spec["digits"])
            if value < spec["low"]:
                interpretation = "L"
            elif value > spec["high"]:
                interpretation = "H"
            else:
                interpretation = "N"
            resource = {
                "resourceType": "Observation",
                "id": f"OBS-{pid}-LAB-{spec['key']}-{label}",
                "status": "final",
                "category": [{"coding": [coding(CS["observation-category"], "laboratory", "Laboratory")]}],
                "code": {
                    "coding": [coding(CS["loinc"], spec["loinc"][0], spec["loinc"][1])],
                    "text": spec["loinc"][1].split(" [")[0],
                },
                "subject": ref("Patient", pid),
                "encounter": ref("Encounter", encounter_id),
                "effectiveDateTime": ts(day),
                "valueQuantity": quantity(value, spec["unit"]),
                "referenceRange": [
                    {
                        "low": quantity(spec["low"], spec["unit"]),
                        "high": quantity(spec["high"], spec["unit"]),
                        "text": f"{spec['low']}-{spec['high']} {spec['unit']}",
                    }
                ],
                "interpretation": [{"coding": [coding(CS["v3-interpretation"], interpretation)]}],
            }
            out.append(
                finish(
                    resource,
                    line=f"{spec['key']} {value} {spec['unit']} ({interpretation}) for {pid} on {day}",
                )
            )
    return out


def procedure_resection(record: dict[str, Any], encounter_id: str) -> dict[str, Any] | None:
    surgery = record["surgery"]
    if not surgery or not surgery.get("date"):
        return None
    pid = record["id"]
    extent = surgery.get("extent") or record["extent"] or "not_assessable"
    is_biopsy = extent == "biopsy" or surgery.get("procedure") == "biopsy"
    if is_biopsy:
        code = {
            "coding": [coding(CS["procedure"], "brain-tumour-biopsy", "Stereotactic biopsy of brain tumour")],
            "text": "Stereotactic biopsy of brain tumour",
        }
        label = "Stereotactic biopsy"
    else:
        code = {
            "coding": [coding(CS["procedure"], "brain-tumour-resection", "Resection of brain tumour")],
            "text": "Resection of brain tumour",
        }
        label = EXTENT_LABEL.get(extent, "Resection")
    resource: dict[str, Any] = {
        "resourceType": "Procedure",
        "id": f"PROC-{pid}-RESECTION",
        "status": "completed",
        "category": {"text": "Surgical procedure"},
        "code": code,
        "subject": ref("Patient", pid),
        "encounter": ref("Encounter", encounter_id),
        "performedDateTime": ts(surgery["date"], "08:30:00"),
        "reasonReference": [ref("Condition", f"COND-{pid}-PRIMARY")],
        "outcome": {"text": EXTENT_LABEL.get(extent, "Not assessable")},
        "note": [
            {"text": f"Synthetic operative record. Extent of resection: {EXTENT_LABEL.get(extent, 'not assessable')}."}
        ],
    }
    if record["bodySite"]:
        resource["bodySite"] = [{"text": record["bodySite"]}]
    return finish(resource, line=f"{label} for {pid} on {surgery['date']}", mcode=True)


def procedure_radiotherapy(record: dict[str, Any], encounter_id: str) -> dict[str, Any] | None:
    rt = record["rt"]
    if not rt:
        return None
    pid = record["id"]
    if rt["start"] > AS_OF:
        status = "preparation"
    elif (rt.get("end") or rt["start"]) > AS_OF:
        status = "in-progress"
    else:
        status = "completed"
    resource: dict[str, Any] = {
        "resourceType": "Procedure",
        "id": f"PROC-{pid}-RT",
        "status": status,
        "category": {"text": "Radiotherapy"},
        "code": {
            "coding": [
                coding(
                    CS["procedure"],
                    "external-beam-radiotherapy",
                    "External beam radiotherapy course",
                )
            ],
            "text": f"External beam radiotherapy, {int(rt['dose'])} Gy in {rt['fractions']} fractions",
        },
        "subject": ref("Patient", pid),
        "encounter": ref("Encounter", encounter_id),
        "performedPeriod": {
            "start": ts(rt["start"], "09:00:00"),
            "end": ts(rt.get("end") or rt["start"], "12:00:00"),
        },
        "reasonReference": [ref("Condition", f"COND-{pid}-PRIMARY")],
        "bodySite": [{"text": "Brain"}],
        "note": [{"text": f"Synthetic radiotherapy course: {rt['dose']} Gy in {rt['fractions']} fractions."}],
    }
    return finish(resource, line=f"Radiotherapy {int(rt['dose'])} Gy / {rt['fractions']} fractions for {pid} ({status})", mcode=True)


def medication_requests(record: dict[str, Any], encounter_id: str) -> list[dict[str, Any]]:
    tmz = record["tmz"]
    if not tmz:
        return []
    pid = record["id"]
    out = []
    medication = {
        "coding": [coding(CS["atc"], TMZ_ATC[0], TMZ_ATC[1])],
        "text": "Temozolomide",
    }
    if tmz.get("concurrentStart"):
        end = tmz.get("concurrentEnd")
        status = "completed" if end and end <= AS_OF else "active"
        resource = {
            "resourceType": "MedicationRequest",
            "id": f"MEDREQ-{pid}-TMZ-CONCURRENT",
            "identifier": [{"system": CS["doc_id"], "value": f"RX-{pid}-TMZ-CONCURRENT"}],
            "status": status,
            "intent": "order",
            "category": [{"text": "Concurrent chemoradiotherapy"}],
            "medicationCodeableConcept": medication,
            "subject": ref("Patient", pid),
            "encounter": ref("Encounter", encounter_id),
            "authoredOn": ts(tmz["concurrentStart"]),
            "reasonReference": [ref("Condition", f"COND-{pid}-PRIMARY")],
            "dosageInstruction": [
                {
                    "text": "Temozolomide 75 mg/m2 orally once daily during radiotherapy",
                    "route": {"coding": [coding(CS["snomed"], ORAL_ROUTE_SNOMED[0], ORAL_ROUTE_SNOMED[1])]},
                    "doseAndRate": [
                        {"doseQuantity": quantity(75, "mg/m2", "mg/m2")}
                    ],
                }
            ],
            "dispenseRequest": {
                "validityPeriod": {
                    "start": ts(tmz["concurrentStart"]),
                    "end": ts(end or tmz["concurrentStart"]),
                }
            },
            "note": [{"text": "Synthetic prescription. ATC L01AX03 is a verified code in the source dataset."}],
        }
        out.append(finish(resource, line=f"Concurrent temozolomide prescription for {pid} ({status})", mcode=True))
    if tmz.get("adjuvantStart"):
        cycles_done = len(record["cycles"])
        planned = tmz.get("plannedCycles") or 6
        adjuvant_end = tmz.get("adjuvantEnd")
        if record["status"] == "withdrawn":
            status = "stopped"
        elif adjuvant_end and adjuvant_end <= AS_OF:
            status = "completed"
        elif cycles_done >= planned:
            status = "completed"
        else:
            status = "active"
        resource = {
            "resourceType": "MedicationRequest",
            "id": f"MEDREQ-{pid}-TMZ-ADJUVANT",
            "identifier": [{"system": CS["doc_id"], "value": f"RX-{pid}-TMZ-ADJUVANT"}],
            "status": status,
            "intent": "order",
            "category": [{"text": "Adjuvant chemotherapy"}],
            "medicationCodeableConcept": medication,
            "subject": ref("Patient", pid),
            "encounter": ref("Encounter", encounter_id),
            "authoredOn": ts(tmz["adjuvantStart"]),
            "reasonReference": [ref("Condition", f"COND-{pid}-PRIMARY")],
            "dosageInstruction": [
                {
                    "text": "Temozolomide 200 mg/m2 orally on days 1-5 of a 28-day cycle",
                    "route": {"coding": [coding(CS["snomed"], ORAL_ROUTE_SNOMED[0], ORAL_ROUTE_SNOMED[1])]},
                    "doseAndRate": [
                        {"doseQuantity": quantity(200, "mg/m2", "mg/m2")}
                    ],
                }
            ],
            "dispenseRequest": {
                "numberOfRepeatsAllowed": max(planned - 1, 0),
                "expectedSupplyDuration": {"value": 28, "unit": "days", "system": CS["ucum"], "code": "d"},
            },
            "note": [
                {
                    "text": f"Synthetic adjuvant prescription. Planned cycles: {planned}; "
                            f"completed cycles in source: {cycles_done}."
                }
            ],
        }
        out.append(finish(resource, line=f"Adjuvant temozolomide prescription for {pid} ({status})", mcode=True))
    return out


def medication_administrations(record: dict[str, Any], encounter_id: str) -> list[dict[str, Any]]:
    pid = record["id"]
    out = []
    for cycle in record["cycles"]:
        resource = {
            "resourceType": "MedicationAdministration",
            "id": f"MEDADM-{pid}-TMZ-C{cycle['number']}",
            "status": "completed",
            "category": {"text": "Adjuvant chemotherapy"},
            "medicationCodeableConcept": {
                "coding": [coding(CS["atc"], TMZ_ATC[0], TMZ_ATC[1])],
                "text": "Temozolomide",
            },
            "subject": ref("Patient", pid),
            "context": ref("Encounter", encounter_id),
            "effectiveDateTime": ts(cycle["date"], "09:30:00"),
            "dosage": {
                "text": f"Cycle {cycle['number']}: temozolomide 200 mg/m2 on days 1-5",
                "route": {"coding": [coding(CS["snomed"], ORAL_ROUTE_SNOMED[0], ORAL_ROUTE_SNOMED[1])]},
                "dose": quantity(200, "mg/m2", "mg/m2"),
            },
            "note": [{"text": "Synthetic administration record for one adjuvant cycle."}],
        }
        out.append(finish(resource, line=f"Temozolomide cycle {cycle['number']} given to {pid} on {cycle['date']}"))
    return out


def conclusion_from(text: str) -> str | None:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped in ("CONCLUSIE", "CONCLUSION", "IMPRESSIE", "IMPRESSION", "DIAGNOSIS"):
            start = index + 1
            break
    if start is None:
        return None
    collected: list[str] = []
    for line in lines[start:]:
        if not line.strip():
            if collected:
                break
            continue
        collected.append(line.strip())
    return " ".join(collected)[:1000] or None


def document_resources(record: dict[str, Any], encounter_id: str) -> list[dict[str, Any]]:
    pid = record["id"]
    out: list[dict[str, Any]] = []
    for doc in record["documents"]:
        text = document_text(doc, arrivals=record["arrivals"])
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        digest = base64.b64encode(hashlib.sha1(text.encode("utf-8")).digest()).decode("ascii")
        spec = DOC_TYPES[doc["type"]]
        doc_ref_id = doc["id"]
        date = doc["documentDate"]
        attachment = {
            "contentType": "text/plain",
            "language": doc["language"],
            "data": encoded,
            "size": len(text.encode("utf-8")),
            "hash": digest,
            "title": doc["title"],
            "creation": ts(date, "09:00:00"),
        }

        resource: dict[str, Any] = {
            "resourceType": "DocumentReference",
            "id": doc_ref_id,
            "masterIdentifier": {"system": CS["doc_id"], "value": doc["id"]},
            "identifier": [{"system": CS["doc_id"], "value": doc["id"]}],
            "status": "current",
            "docStatus": "final",
            "type": {
                "coding": [coding(CS["loinc"], spec["loinc"][0], spec["loinc"][1])],
                "text": spec["loinc"][1],
            },
            "category": [
                {
                    "coding": [coding(CS["us-core-doc"], "clinical-note", "Clinical Note")],
                    "text": spec["category"][1],
                }
            ],
            "subject": ref("Patient", pid),
            "date": ts(date, "09:00:00"),
            "author": [ref("Organization", record["site"]["id"])],
            "description": doc["title"],
            "content": [{"attachment": attachment}],
            "context": {
                "encounter": [ref("Encounter", encounter_id)],
                "period": {"start": ts(date, "08:00:00"), "end": ts(date, "17:00:00")},
                "sourcePatientInfo": ref("Patient", pid),
            },
        }
        related = []
        if spec["diagnostic_report"]:
            related.append(ref("DiagnosticReport", f"DR-{doc['id']}"))
        if related:
            resource["context"]["related"] = related
        out.append(
            finish(
                resource,
                line=f"{doc['title']} — {doc['id']} for {pid} ({doc['language']}, {date})",
            )
        )

        if spec["diagnostic_report"]:
            report: dict[str, Any] = {
                "resourceType": "DiagnosticReport",
                "id": f"DR-{doc['id']}",
                "identifier": [{"system": CS["doc_id"], "value": f"DR-{doc['id']}"}],
                "status": "final",
                "category": [
                    {
                        "coding": [coding(CS["v2-0074"], spec["category"][0], spec["category"][1])],
                        "text": spec["category"][1],
                    }
                ],
                "code": {
                    "coding": [coding(CS["loinc"], spec["loinc"][0], spec["loinc"][1])],
                    "text": spec["loinc"][1],
                },
                "subject": ref("Patient", pid),
                "encounter": ref("Encounter", encounter_id),
                "effectiveDateTime": ts(date, "09:00:00"),
                "issued": ts(date, "12:00:00"),
                "performer": [ref("Organization", record["site"]["id"])],
                "presentedForm": [attachment],
            }
            conclusion = conclusion_from(text)
            if conclusion:
                report["conclusion"] = conclusion
            out.append(
                finish(
                    report,
                    line=f"{spec['loinc'][1]} — {doc['id']} for {pid} ({date})",
                    mcode=doc["type"] == "pathology_report",
                )
            )
    return out


def add_days(date: str, days: int) -> str:
    base = date_cls.fromisoformat(date)
    return (base + timedelta(days=days)).isoformat()


def bundle_for(record: dict[str, Any]) -> dict[str, Any]:
    pid = record["id"]
    encounter_id = f"ENC-{pid}-EPISODE"
    resources = [patient_resource(record), encounter_resource(record, encounter_id)]
    condition = condition_resource(record, encounter_id)
    if condition:
        resources.append(condition)
    for factory in (observation_kps, observation_mgmt, observation_idh, observation_extent):
        observation = factory(record, encounter_id)
        if observation:
            resources.append(observation)
    resources.extend(lab_observations(record, encounter_id))
    for factory in (procedure_resection, procedure_radiotherapy):
        procedure = factory(record, encounter_id)
        if procedure:
            resources.append(procedure)
    resources.extend(medication_requests(record, encounter_id))
    resources.extend(medication_administrations(record, encounter_id))
    resources.extend(document_resources(record, encounter_id))

    entries = []
    for resource in resources:
        resource_type = resource["resourceType"]
        resource_id = resource["id"]
        entries.append(
            {
                "fullUrl": f"{SERVER_BASE}/{resource_type}/{resource_id}",
                "resource": resource,
                "request": {"method": "PUT", "url": f"{resource_type}/{resource_id}"},
            }
        )
    return {
        "resourceType": "Bundle",
        "id": f"bundle-{pid}",
        "type": "transaction",
        "timestamp": GENERATED_AT,
        "entry": entries,
    }


def transaction_bundle(resources: list[dict[str, Any]], bundle_id: str) -> dict[str, Any]:
    entries = []
    for resource in resources:
        resource_type = resource["resourceType"]
        resource_id = resource["id"]
        entries.append(
            {
                "fullUrl": f"{SERVER_BASE}/{resource_type}/{resource_id}",
                "resource": resource,
                "request": {"method": "PUT", "url": f"{resource_type}/{resource_id}"},
            }
        )
    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "transaction",
        "timestamp": GENERATED_AT,
        "entry": entries,
    }


def count_resources(files: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for bundle in files.values():
        for entry in bundle["entry"]:
            resource_type = entry["resource"]["resourceType"]
            counts[resource_type] = counts.get(resource_type, 0) + 1
    return dict(sorted(counts.items()))


def serialise(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def build() -> dict[str, str]:
    study = load_study()
    sites = {site["id"]: site for site in study["sites"]}
    extractions = extraction_values()
    baseline_docs = load_documents()
    docs_by_patient: dict[str, list[dict[str, Any]]] = {}
    for doc in baseline_docs:
        docs_by_patient.setdefault(doc["participantId"], []).append(doc)
    for docs in docs_by_patient.values():
        docs.sort(key=lambda item: (item["documentDate"], item["id"]))

    baseline_records = [
        build_record(
            participant,
            extractions=extractions.get(participant["id"], {}),
            site=sites[participant["siteId"]],
            documents=docs_by_patient.get(participant["id"], []),
            arrivals=False,
        )
        for participant in load_baseline_participants()
    ]

    arrivals_records = []
    for participant in load_arrivals():
        docs = [
            dict(doc, assetPath=f"source/documents/{doc['file']}")
            for doc in participant.get("documents", [])
        ]
        arrivals_records.append(
            build_record(
                participant,
                extractions={},
                site=sites[participant["siteId"]],
                documents=docs,
                arrivals=True,
            )
        )

    h2_source = load_hospital2()
    h2_baseline_records = []
    for participant in h2_source["baseline"]:
        docs = [
            dict(doc, assetPath=f"source/documents/{doc['file']}")
            for doc in participant.get("documents", [])
        ]
        h2_baseline_records.append(
            build_record(
                participant,
                extractions={},
                site=sites[participant["siteId"]],
                documents=docs,
                arrivals=True,
            )
        )
    h2_arrivals_records = []
    for participant in h2_source["arrivals"]:
        docs = [
            dict(doc, assetPath=f"source/documents/{doc['file']}")
            for doc in participant.get("documents", [])
        ]
        h2_arrivals_records.append(
            build_record(
                participant,
                extractions={},
                site=sites[participant["siteId"]],
                documents=docs,
                arrivals=True,
            )
        )

    organizations_bundle = transaction_bundle(organizations(study), "bundle-organizations")
    code_systems_bundle = transaction_bundle(code_systems(), "bundle-codesystems")

    outputs: dict[str, str] = {}
    outputs["shared/codesystems.json"] = serialise(code_systems_bundle)

    set_specs = (
        ("baseline", baseline_records, 1, [
            "app/assets/data/participants.json",
            "app/assets/data/study.json",
            "app/assets/data/documents.json",
            "app/assets/data/extractions.json",
            "app/assets/data/documents/*.txt",
        ]),
        ("arrivals", arrivals_records, 1, [
            "fhir-seed/source/arrivals.json",
            "fhir-seed/source/documents/*.txt",
        ]),
        ("hospital2/baseline", h2_baseline_records, 2, [
            "fhir-seed/source/hospital2.json",
            "fhir-seed/source/documents/DOC-20*.txt",
        ]),
        ("hospital2/arrivals", h2_arrivals_records, 2, [
            "fhir-seed/source/hospital2.json",
            "fhir-seed/source/documents/DOC-20*.txt",
        ]),
    )

    for name, records, hospital_num, source_paths in set_specs:
        files: dict[str, dict[str, Any]] = {
            "shared/codesystems.json": code_systems_bundle,
            "organizations.json": organizations_bundle,
        }
        paths: list[str] = ["shared/codesystems.json", f"{name}/organizations.json"]
        outputs[f"{name}/organizations.json"] = serialise(organizations_bundle)
        patient_files: list[dict[str, Any]] = []
        for record in records:
            bundle = bundle_for(record)
            relative = f"patient-{record['id']}.json"
            files[relative] = bundle
            paths.append(f"{name}/{relative}")
            outputs[f"{name}/{relative}"] = serialise(bundle)
            patient_files.append(
                {
                    "patientId": record["id"],
                    "file": f"{name}/{relative}",
                    "resources": len(bundle["entry"]),
                    "documents": [doc["id"] for doc in record["documents"]],
                    "sha256": sha256_text(serialise(bundle)),
                }
            )
        counts = count_resources(files)
        manifest: dict[str, Any] = {
            "schemaVersion": "1.0.0",
            "set": name.split("/")[-1],
            "synthetic": True,
            "generatedAt": GENERATED_AT,
            "asOf": AS_OF,
            "studyId": STUDY_ID,
            "source": source_paths,
            "order": paths,
            "patients": patient_files,
            "counts": counts,
            "totalResources": sum(counts.values()),
            "documentCount": counts.get("DocumentReference", 0),
            "patientCount": len(records),
        }
        if hospital_num != 1:
            manifest["hospital"] = hospital_num
        outputs[f"{name}/manifest.json"] = serialise(manifest)
    return outputs


def write_outputs(outputs: dict[str, str], *, check: bool) -> int:
    changed = []
    for relative, text in outputs.items():
        path = SEED_DIR / relative
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                changed.append(relative)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if check:
        if changed:
            print("fhir-seed: generated files are out of date:", file=sys.stderr)
            for relative in changed:
                print(f"  - {relative}", file=sys.stderr)
            print("Run: python3 fhir-seed/generate.py", file=sys.stderr)
            return 1
        print(f"fhir-seed: {len(outputs)} generated files are up to date")
        return 0
    print(f"fhir-seed: wrote {len(outputs)} files under {SEED_DIR}")
    for name in ("baseline", "arrivals", "hospital2/baseline", "hospital2/arrivals"):
        manifest = json.loads(outputs[f"{name}/manifest.json"])
        print(
            f"  {name:18s} patients={manifest['patientCount']:2d} "
            f"documents={manifest['documentCount']:2d} resources={manifest['totalResources']:3d}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic FHIR R4 bundles for the Yamicc demo.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if the committed bundles differ from the generator output",
    )
    parser.add_argument(
        "--mcode-profiles",
        action="store_true",
        help="assert mCODE StructureDefinition URLs in meta.profile (needs a server with the mCODE IG loaded)",
    )
    args = parser.parse_args(argv)
    _PROFILES_FLAG["enabled"] = args.mcode_profiles
    outputs = build()
    return write_outputs(outputs, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
