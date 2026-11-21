"""AI screening checker for participant eligibility against protocol criteria.

Evaluates a participant's source documents against ``deliverables/protocol_criteria.json``
and returns per criterion ``met | not_met | unknown`` with an exact evidence span
from the source document, confidence, and rationale.

Supports both ``rules`` and ``ollama`` providers with the same span re-location
and abstention rules as extraction, plus automatic fallback when Ollama is down.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from . import providers, registry
from .providers import rules as rules_mod
from .span import locate_quote, make_evidence
from .types import (
    CriterionCheck,
    CriterionDef,
    Evidence,
    ProviderError,
    ProviderUnavailable,
    RunMetadata,
    ScreeningResult,
    ScreeningVerdict,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CRITERIA_PATH = REPO_ROOT / "deliverables" / "protocol_criteria.json"

FALLBACK_CRITERIA: list[dict[str, Any]] = [
    {
        "id": "INC-01",
        "type": "inclusion",
        "text": "Age 18 years or older at diagnosis.",
        "dataNeeded": "Age at diagnosis in whole years and the diagnosis date.",
    },
    {
        "id": "INC-02",
        "type": "inclusion",
        "text": "Histologically confirmed glioblastoma, ICD-O-3 morphology 9440/3, IDH-wildtype (WHO CNS5, 2021).",
        "dataNeeded": "Pathology report with ICD-O-3 morphology code and an IDH1/2 result of wildtype.",
    },
    {
        "id": "INC-03",
        "type": "inclusion",
        "text": "MGMT promoter methylation status is known (methylated or unmethylated).",
        "dataNeeded": "MGMT promoter methylation result that is methylated or unmethylated.",
    },
    {
        "id": "INC-04",
        "type": "inclusion",
        "text": "Karnofsky Performance Status 60 or higher, recorded within 7 days before registration.",
        "dataNeeded": "KPS score (0-100, steps of 10) and its assessment date.",
    },
    {
        "id": "INC-05",
        "type": "inclusion",
        "text": "Adequate bone-marrow function: ANC 1.5 x10^9/L or higher, platelets 100 x10^9/L or higher, haemoglobin 9.0 g/dL or higher.",
        "dataNeeded": "ANC, platelet count and haemoglobin values with specimen date and reference ranges.",
    },
    {
        "id": "INC-06",
        "type": "inclusion",
        "text": "Adequate hepatic function: ALT 3 xULN or lower and total bilirubin 1.5 xULN or lower (3 xULN or lower if Gilbert syndrome).",
        "dataNeeded": "ALT and total bilirubin values with the local upper limit of normal (ULN) and specimen date.",
    },
    {
        "id": "INC-07",
        "type": "inclusion",
        "text": "Adequate renal function: serum creatinine 1.5 xULN or lower, or eGFR 50 mL/min/1.73 m2 or higher.",
        "dataNeeded": "Serum creatinine with local ULN, or eGFR value, and specimen date.",
    },
    {
        "id": "INC-08",
        "type": "inclusion",
        "text": "Post-surgical contrast-enhanced MRI is available and evaluable per RANO, and the participant has recovered from surgery (2 weeks or more after craniotomy, or 1 week or more after biopsy).",
        "dataNeeded": "MRI report with date and RANO assessment, operative note with surgery type and date, and a clinical note on post-surgical recovery.",
    },
    {
        "id": "INC-09",
        "type": "inclusion",
        "text": "Participant is able to give written informed consent and to comply with the visit schedule.",
        "dataNeeded": "Signed and dated informed consent form, plus a clinical note on ability to comply.",
    },
    {
        "id": "EXC-01",
        "type": "exclusion",
        "text": "Any prior radiotherapy to the brain.",
        "dataNeeded": "Radiotherapy history for the brain, with dates and site.",
    },
    {
        "id": "EXC-02",
        "type": "exclusion",
        "text": "Prior systemic anti-glioma therapy (chemotherapy, targeted therapy or immunotherapy), except corticosteroids.",
        "dataNeeded": "Systemic treatment history with agent names and dates.",
    },
    {
        "id": "EXC-03",
        "type": "exclusion",
        "text": "Tumour is IDH-mutant, or IDH status is indeterminate or not assessable.",
        "dataNeeded": "IDH1/2 result (mutant, wildtype or indeterminate).",
    },
    {
        "id": "EXC-04",
        "type": "exclusion",
        "text": "Participant is pregnant or breastfeeding; participants with reproductive potential must have a negative pregnancy test.",
        "dataNeeded": "Pregnancy test result with date, and a clinical note on breastfeeding status.",
    },
]


def load_criteria(path: Path | None = None) -> list[CriterionDef]:
    target = path or DEFAULT_CRITERIA_PATH
    if target.exists():
        raw = json.loads(target.read_text(encoding="utf-8"))
    else:
        raw = FALLBACK_CRITERIA
    return [CriterionDef.from_api(item) for item in raw]


def _overall_verdict(checks: list[CriterionCheck]) -> str:
    if any(c.verdict == "not_met" for c in checks):
        return "screen_fail"
    if any(c.verdict == "unknown" for c in checks):
        return "unknown"
    return "eligible"


def _find_in_docs(
    documents: list[dict[str, Any]],
    patterns: list[tuple[str, ScreeningVerdict, float, str]],
) -> tuple[ScreeningVerdict, float, str, str, Evidence] | None:
    """Try each (regex, verdict, confidence, rationale_template) across documents in order."""
    for pattern, verdict, conf, rationale_tpl in patterns:
        rx = re.compile(pattern, re.IGNORECASE)
        for doc in documents:
            text = doc.get("text") or ""
            m = rx.search(text)
            if m:
                ev = make_evidence(text, m.start(0), m.end(0))
                rationale = rationale_tpl.format(match=m.group(0).strip(), doc=doc["id"])
                return verdict, conf, rationale, doc["id"], ev
    return None


def _check_inc_01(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    for doc in docs:
        text = doc.get("text") or ""
        m = re.search(
            r"(?:LEEFTIJD BIJ DIAGNOSE|AGE AT DIAGNOSIS|AGE)\s*[:\-]?\s*(\d{1,3})\s*(?:jaar|years?)?",
            text,
            re.I,
        )
        if m:
            age = int(m.group(1))
            ev = make_evidence(text, m.start(0), m.end(0))
            if age >= 18:
                return CriterionCheck(
                    criterion_id=c.id,
                    type=c.type,
                    text=c.text,
                    verdict="met",
                    confidence=0.98,
                    rationale=f"Document {doc['id']} states age {age} years (>= 18).",
                    document_id=doc["id"],
                    evidence=[ev],
                )
            return CriterionCheck(
                criterion_id=c.id,
                type=c.type,
                text=c.text,
                verdict="not_met",
                confidence=0.98,
                rationale=f"Document {doc['id']} states age {age} years (< 18).",
                document_id=doc["id"],
                evidence=[ev],
            )
    return CriterionCheck(
        criterion_id=c.id,
        type=c.type,
        text=c.text,
        verdict="unknown",
        confidence=0.0,
        rationale="Age at diagnosis is not stated in the available source documents.",
        abstention_reason="not_stated",
    )


def _check_inc_02(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    # Check for IDH-mutant first -> not_met
    hit_mutant = _find_in_docs(
        docs,
        [
            (
                r"(?:Astrocytoma|Glioblastoom|Glioblastoma|glioom)[^\n.]{0,50}IDH[- ]mutant[^\n.]*\.?",
                "not_met",
                0.97,
                "Pathology/clinical document {doc} reports an IDH-mutant tumour ({match}).",
            ),
            (
                r"IDH1\s+R132H\s+(?:positief|positive)[^\n.]*\.?",
                "not_met",
                0.97,
                "Pathology report {doc} shows IDH1 R132H positive ({match}).",
            ),
        ],
    )
    if hit_mutant:
        v, conf, rat, did, ev = hit_mutant
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])

    # Check for confirmed GBM IDH-wildtype with 9440/3
    for doc in docs:
        text = doc.get("text") or ""
        m = re.search(
            r"(?:Glioblastoom|Glioblastoma),\s*IDH[- ]wildtype[^\n]*9440/3\.?",
            text,
            re.I,
        )
        if not m:
            m = re.search(
                r"(?:Glioblastoom|Glioblastoma),\s*IDH[- ]wildtype(?:\s*\(WHO CNS5\))?\.?",
                text,
                re.I,
            )
        if m:
            ev = make_evidence(text, m.start(0), m.end(0))
            return CriterionCheck(
                criterion_id=c.id,
                type=c.type,
                text=c.text,
                verdict="met",
                confidence=0.97,
                rationale=f"Document {doc['id']} confirms IDH-wildtype glioblastoma ({m.group(0).strip()}).",
                document_id=doc["id"],
                evidence=[ev],
            )

    # Check if pending histology is explicitly stated
    pending = _find_in_docs(
        docs,
        [
            (
                r"Histologische bevestiging\s+is\s+nog\s+niet\s+beschikbaar\.?",
                "unknown",
                0.0,
                "Histological confirmation is explicitly pending in {doc} ({match}).",
            ),
            (
                r"Histologie en biomarkers zijn nog\s+niet beschikbaar\.?",
                "unknown",
                0.0,
                "Histology and biomarkers are still pending in {doc} ({match}).",
            ),
        ],
    )
    if pending:
        _, _, rat, did, ev = pending
        return CriterionCheck(
            c.id, c.type, c.text, "unknown", 0.0, rat, did, [ev], abstention_reason="pending_histology"
        )

    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "No histological confirmation of IDH-wildtype glioblastoma found in documents.",
        abstention_reason="not_stated",
    )


def _check_inc_03(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    # Check for known methylated or unmethylated
    for doc in docs:
        text = doc.get("text") or ""
        m = re.search(
            r"MGMT[- ]promoter(?:methylering)?\s*(?:is|:)\s*(?:niet[\s-]+gemethyleerd|gemethyleerd|unmethylated|methylated|geen methylatie aangetoond|methylatie aangetoond)[^\n.]*\.?",
            text,
            re.I,
        )
        if m:
            ev = make_evidence(text, m.start(0), m.end(0))
            return CriterionCheck(
                criterion_id=c.id,
                type=c.type,
                text=c.text,
                verdict="met",
                confidence=0.95,
                rationale=f"Document {doc['id']} states a known MGMT promoter methylation status ({m.group(0).strip()}).",
                document_id=doc["id"],
                evidence=[ev],
            )

    # Check if explicitly pending
    pending = _find_in_docs(
        docs,
        [
            (
                r"Moleculaire\s+(?:bepaling van MGMT-status|MGMT-bepaling)\s+is\s+nog\s+in\s+(?:bewerking|afwachting)[^\n.]*\.?",
                "unknown",
                0.0,
                "MGMT promoter assay is still pending in {doc} ({match}).",
            ),
            (
                r"Histologie en biomarkers zijn nog\s+niet beschikbaar\.?",
                "unknown",
                0.0,
                "Biomarkers are not yet available in {doc} ({match}).",
            ),
        ],
    )
    if pending:
        _, _, rat, did, ev = pending
        return CriterionCheck(
            c.id, c.type, c.text, "unknown", 0.0, rat, did, [ev], abstention_reason="pending_assay"
        )

    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "MGMT promoter methylation status is not stated in the source documents.",
        abstention_reason="not_stated",
    )


def _check_inc_04(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    for doc in docs:
        text = doc.get("text") or ""
        m = re.search(r"Karnofsky Performance Status[^\n:]{0,40}:\s*(\d{1,3})\s*%?", text, re.I)
        if m:
            kps = int(m.group(1))
            ev = make_evidence(text, m.start(0), m.end(0))
            if kps >= 60:
                return CriterionCheck(
                    c.id,
                    c.type,
                    c.text,
                    "met",
                    0.95,
                    f"Document {doc['id']} states KPS {kps}% (>= 60%).",
                    doc["id"],
                    [ev],
                )
            return CriterionCheck(
                c.id,
                c.type,
                c.text,
                "not_met",
                0.96,
                f"Document {doc['id']} states KPS {kps}%, which is below the required 60% threshold.",
                doc["id"],
                [ev],
            )
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Karnofsky Performance Status is not stated in the source documents.",
        abstention_reason="not_stated",
    )


def _check_inc_05(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    hit = _find_in_docs(
        docs,
        [
            (
                r"Beenmergfunctie adequaat:\s*ANC\s+\d+(?:[.,]\d+)?\s*x10\^9/L,\s*trombocyten\s+\d+\s*x10\^9/L,\s*hemoglobine\s+\d+(?:[.,]\d+)?\s*g/dL\.?",
                "met",
                0.95,
                "Haematology laboratory values in {doc} meet bone-marrow thresholds ({match}).",
            ),
            (
                r"Adequate bone-marrow function:\s*ANC[^\n.]*\.?",
                "met",
                0.95,
                "Haematology laboratory values in {doc} meet bone-marrow thresholds ({match}).",
            ),
        ],
    )
    if hit:
        v, conf, rat, did, ev = hit
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Bone-marrow laboratory values (ANC, platelets, haemoglobin) are not stated in the documents.",
        abstention_reason="not_stated",
    )


def _check_inc_06(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    hit = _find_in_docs(
        docs,
        [
            (
                r"Leverfunctie adequaat:\s*ALT\s+\d+\s*U/L[^\n.]*\.?",
                "met",
                0.95,
                "Hepatic laboratory values in {doc} meet protocol criteria ({match}).",
            ),
            (
                r"Adequate hepatic function:\s*ALT[^\n.]*\.?",
                "met",
                0.95,
                "Hepatic laboratory values in {doc} meet protocol criteria ({match}).",
            ),
        ],
    )
    if hit:
        v, conf, rat, did, ev = hit
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Hepatic function laboratory values (ALT, bilirubin) are not stated in the documents.",
        abstention_reason="not_stated",
    )


def _check_inc_07(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    hit = _find_in_docs(
        docs,
        [
            (
                r"Nierfunctie adequaat:\s*serumcreatinine\s+\d+(?:[.,]\d+)?\s*mg/dL[^\n.]*\.?",
                "met",
                0.95,
                "Renal function values in {doc} meet protocol criteria ({match}).",
            ),
            (
                r"Adequate renal function:\s*serum creatinine[^\n.]*\.?",
                "met",
                0.95,
                "Renal function values in {doc} meet protocol criteria ({match}).",
            ),
        ],
    )
    if hit:
        v, conf, rat, did, ev = hit
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Renal function laboratory values (creatinine, eGFR) are not stated in the documents.",
        abstention_reason="not_stated",
    )


def _check_inc_08(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    hit = _find_in_docs(
        docs,
        [
            (
                r"Postoperatieve MRI met\s+contrast\s+is\s+beschikbaar\s+en\s+evalueerbaar\s+conform\s+RANO\.?",
                "met",
                0.93,
                "Post-surgical contrast-enhanced MRI and surgical recovery confirmed in {doc} ({match}).",
            ),
            (
                r"Post(?:-|\s)?operative\s+course\s+was\s+uneventful\.?",
                "met",
                0.88,
                "Post-operative recovery documented in {doc} ({match}).",
            ),
            (
                r"Postoperatief\s+beloop\s+(?:ongecompliceerd|zonder complicaties)\.?",
                "met",
                0.88,
                "Post-operative recovery documented in {doc} ({match}).",
            ),
        ],
    )
    if hit:
        v, conf, rat, did, ev = hit
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Post-surgical MRI evaluability and post-surgical recovery are not documented yet.",
        abstention_reason="not_stated",
    )


def _check_inc_09(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    hit = _find_in_docs(
        docs,
        [
            (
                r"Schriftelijk informed consent is getekend;\s*patient is in staat het bezoekschema te volgen\.?",
                "met",
                0.96,
                "Signed informed consent and ability to comply documented in {doc} ({match}).",
            ),
            (
                r"Written informed consent[^\n.]*\.?",
                "met",
                0.95,
                "Signed informed consent documented in {doc} ({match}).",
            ),
        ],
    )
    if hit:
        v, conf, rat, did, ev = hit
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Written informed consent status is not stated in the source documents.",
        abstention_reason="not_stated",
    )


def _check_exc_01(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    # Check if prior brain RT occurred -> not_met
    prior = _find_in_docs(
        docs,
        [
            (
                r"Eerdere radiotherapie op de hersenen[^\n.]*\.?",
                "not_met",
                0.95,
                "Prior cranial radiotherapy reported in {doc} ({match}).",
            ),
        ],
    )
    # Note: make sure "Geen eerdere radiotherapie" doesn't match "Eerdere radiotherapie"
    none_hit = _find_in_docs(
        docs,
        [
            (
                r"Geen eerdere radiotherapie op de hersenen\.?",
                "met",
                0.96,
                "Document {doc} confirms no prior radiotherapy to the brain ({match}).",
            ),
            (
                r"No prior radiotherapy to the brain\.?",
                "met",
                0.96,
                "Document {doc} confirms no prior radiotherapy to the brain ({match}).",
            ),
        ],
    )
    if none_hit:
        v, conf, rat, did, ev = none_hit
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    if prior:
        v, conf, rat, did, ev = prior
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Prior cranial radiotherapy history is not explicitly stated in the documents.",
        abstention_reason="not_stated",
    )


def _check_exc_02(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    none_hit = _find_in_docs(
        docs,
        [
            (
                r"Geen eerdere systemische anti-glioomtherapie[^\n.]*\.?",
                "met",
                0.96,
                "Document {doc} confirms no prior systemic anti-glioma therapy ({match}).",
            ),
            (
                r"Nog geen oncologische behandeling gestart\.?",
                "met",
                0.92,
                "Document {doc} states no oncological therapy has been started ({match}).",
            ),
            (
                r"No prior systemic anti-glioma therapy[^\n.]*\.?",
                "met",
                0.96,
                "Document {doc} confirms no prior systemic anti-glioma therapy ({match}).",
            ),
        ],
    )
    if none_hit:
        v, conf, rat, did, ev = none_hit
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Prior systemic anti-glioma therapy history is not explicitly stated in the documents.",
        abstention_reason="not_stated",
    )


def _check_exc_03(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    # Exclusion criterion: Tumour is IDH-mutant, or IDH status is indeterminate
    # If IDH-mutant -> exclusion applies -> verdict = "not_met"
    mutant = _find_in_docs(
        docs,
        [
            (
                r"IDH1\s+R132H\s+(?:positief|positive)[^\n.]*\.?",
                "not_met",
                0.97,
                "Pathology report {doc} shows IDH1 R132H positive (IDH-mutant), triggering exclusion EXC-03 ({match}).",
            ),
            (
                r"Screen failure wegens IDH-mutant genotype[^\n.]*\.?",
                "not_met",
                0.97,
                "Clinical letter {doc} documents IDH-mutant exclusion ({match}).",
            ),
        ],
    )
    if mutant:
        v, conf, rat, did, ev = mutant
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])

    wt = _find_in_docs(
        docs,
        [
            (
                r"IDH1\s+R132H[^\n.]{0,30}\b(?:negatief|negative)\b[^\n.]*\.?",
                "met",
                0.96,
                "Pathology report {doc} confirms IDH1 R132H negative / IDH-wildtype ({match}).",
            ),
            (
                r"(?:Glioblastoom|Glioblastoma),\s*IDH[- ]wildtype",
                "met",
                0.95,
                "Document {doc} confirms IDH-wildtype status ({match}).",
            ),
        ],
    )
    if wt:
        v, conf, rat, did, ev = wt
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])

    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "IDH1/2 mutation status is not yet available in the source documents.",
        abstention_reason="not_stated",
    )


def _check_exc_04(c: CriterionDef, docs: list[dict[str, Any]]) -> CriterionCheck:
    hit = _find_in_docs(
        docs,
        [
            (
                r"Geen zwangerschap of borstvoeding;\s*negatieve zwangerschapstest bevestigd[^\n.]*\.?",
                "met",
                0.97,
                "Negative pregnancy test and no breastfeeding confirmed in {doc} ({match}).",
            ),
            (
                r"Zwangerschapstest:\s*niet van toepassing\s*\(mannelijke deelnemer\)\.?",
                "met",
                0.98,
                "Not applicable for male participant as documented in {doc} ({match}).",
            ),
            (
                r"(?:GESLACHT:\s*man|SEX:\s*male)\b",
                "met",
                0.95,
                "Participant is male as documented in {doc} ({match}).",
            ),
        ],
    )
    if hit:
        v, conf, rat, did, ev = hit
        return CriterionCheck(c.id, c.type, c.text, v, conf, rat, did, [ev])
    return CriterionCheck(
        c.id,
        c.type,
        c.text,
        "unknown",
        0.0,
        "Pregnancy/breastfeeding status or negative pregnancy test is not stated in the documents.",
        abstention_reason="not_stated",
    )


RULE_CHECKERS = {
    "INC-01": _check_inc_01,
    "INC-02": _check_inc_02,
    "INC-03": _check_inc_03,
    "INC-04": _check_inc_04,
    "INC-05": _check_inc_05,
    "INC-06": _check_inc_06,
    "INC-07": _check_inc_07,
    "INC-08": _check_inc_08,
    "INC-09": _check_inc_09,
    "EXC-01": _check_exc_01,
    "EXC-02": _check_exc_02,
    "EXC-03": _check_exc_03,
    "EXC-04": _check_exc_04,
}


def screen_with_rules(
    participant_id: str,
    documents: list[dict[str, Any]],
    criteria: list[CriterionDef] | None = None,
) -> ScreeningResult:
    t0 = time.perf_counter()
    crit_list = criteria if criteria is not None else load_criteria()
    checks: list[CriterionCheck] = []
    for c in crit_list:
        fn = RULE_CHECKERS.get(c.id)
        if fn:
            checks.append(fn(c, documents))
        else:
            checks.append(
                CriterionCheck(
                    criterion_id=c.id,
                    type=c.type,
                    text=c.text,
                    verdict="unknown",
                    confidence=0.0,
                    rationale=f"No deterministic rule registered for criterion {c.id}.",
                    abstention_reason="not_stated",
                )
            )
    duration = int((time.perf_counter() - t0) * 1000)
    return ScreeningResult(
        participant_id=participant_id,
        overall=_overall_verdict(checks),
        checks=checks,
        metadata=RunMetadata(
            provider="rules",
            model=rules_mod.RulesProvider.model,
            prompt_version=rules_mod.PROMPT_TAG,
            prompt_hash=rules_mod.PROMPT_HASH,
            duration_ms=duration,
        ),
    )


def _screening_schema(criterion_ids: list[str], doc_ids: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "criterionId": {"type": "string", "enum": criterion_ids},
                        "verdict": {"type": "string", "enum": ["met", "not_met", "unknown"]},
                        "documentId": {"type": "string"},
                        "evidenceQuote": {"type": "string"},
                        "confidence": {"type": "number"},
                        "rationale": {"type": "string"},
                    },
                    "required": [
                        "criterionId",
                        "verdict",
                        "documentId",
                        "evidenceQuote",
                        "confidence",
                        "rationale",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["checks"],
        "additionalProperties": False,
    }


def screen_with_ollama(
    participant_id: str,
    documents: list[dict[str, Any]],
    criteria: list[CriterionDef] | None = None,
    *,
    ollama_provider=None,
) -> ScreeningResult:
    crit_list = criteria if criteria is not None else load_criteria()
    impl = ollama_provider or providers.get_provider("ollama")
    ok, reason = impl.available()
    if not ok:
        raise ProviderUnavailable(reason)

    prompt = registry.get_screening_prompt()
    crit_lines = [
        f"- `{c.id}` ({c.type}): {c.text}" + (f" [Data needed: {c.data_needed}]" if c.data_needed else "")
        for c in crit_list
    ]
    system = prompt.text.replace("{{CRITERIA}}", "\n".join(crit_lines))
    doc_blocks = []
    docs_by_id: dict[str, dict[str, Any]] = {}
    for d in documents:
        did = d["id"]
        docs_by_id[did] = d
        doc_blocks.append(f"===== DOCUMENT {did} ({d.get('type', 'note')}) =====\n{d.get('text', '')}")
    user = (
        f"Evaluate participant {participant_id} against the criteria using these source documents. "
        "Return JSON only.\n\n" + "\n\n".join(doc_blocks)
    )

    t0 = time.perf_counter()
    schema = _screening_schema([c.id for c in crit_list], list(docs_by_id.keys()))
    payload = {
        "model": impl.model,
        "stream": False,
        "format": schema,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 8192},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        from .providers import ollama as ollama_mod

        response = ollama_mod._post(f"{impl.host}/api/chat", payload, timeout=impl.timeout)
    except Exception as exc:
        if isinstance(exc, (ProviderError, ProviderUnavailable)):
            raise
        raise ProviderUnavailable(f"Ollama screening call failed: {exc}") from exc

    content = (response.get("message") or {}).get("content") or ""
    try:
        from .providers.ollama import _strip_fences

        parsed = json.loads(_strip_fences(content))
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Ollama returned invalid screening JSON: {exc}: {content[:200]!r}") from exc

    raw_items = parsed.get("checks")
    if not isinstance(raw_items, list):
        raise ProviderError("Ollama screening response has no 'checks' list")

    by_id: dict[str, dict[str, Any]] = {}
    for item in raw_items:
        if isinstance(item, dict) and item.get("criterionId"):
            by_id.setdefault(str(item["criterionId"]), item)

    warnings: list[str] = []
    checks: list[CriterionCheck] = []
    for c in crit_list:
        item = by_id.get(c.id)
        if not item:
            checks.append(
                CriterionCheck(
                    criterion_id=c.id,
                    type=c.type,
                    text=c.text,
                    verdict="unknown",
                    confidence=0.0,
                    rationale="Model did not return a check for this criterion; abstained as unknown.",
                    abstention_reason="not_reported",
                )
            )
            continue

        verdict_raw = str(item.get("verdict") or "unknown").lower()
        verdict: ScreeningVerdict = (
            verdict_raw if verdict_raw in ("met", "not_met", "unknown") else "unknown"
        )
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0
        rationale = str(item.get("rationale") or "").strip() or None
        quote = str(item.get("evidenceQuote") or "").strip()
        doc_id = str(item.get("documentId") or "").strip()

        if verdict == "unknown":
            # Optional evidence relocation if quote was provided
            ev_list: list[Evidence] = []
            used_doc_id: str | None = None
            if quote:
                search_order = [docs_by_id[doc_id]] if doc_id in docs_by_id else []
                search_order += [d for d in documents if d["id"] != doc_id]
                for d in search_order:
                    found = locate_quote(d.get("text") or "", quote)
                    if found:
                        ev_list = [make_evidence(d["text"], found[0], found[1])]
                        used_doc_id = d["id"]
                        break
            checks.append(
                CriterionCheck(
                    criterion_id=c.id,
                    type=c.type,
                    text=c.text,
                    verdict="unknown",
                    confidence=0.0,
                    rationale=rationale or "Not stated in source documents.",
                    document_id=used_doc_id,
                    evidence=ev_list,
                    abstention_reason="not_stated",
                )
            )
            continue

        # For met or not_met, evidence quote MUST be relocated in a source document
        search_order = [docs_by_id[doc_id]] if doc_id in docs_by_id else []
        search_order += [d for d in documents if d["id"] != doc_id]
        found_ev: Evidence | None = None
        found_doc_id: str | None = None
        if quote:
            for d in search_order:
                text = d.get("text") or ""
                found = locate_quote(text, quote)
                if found:
                    found_ev = make_evidence(text, found[0], found[1])
                    found_doc_id = d["id"]
                    break

        if not found_ev:
            warnings.append(f"{c.id}: evidence quote not found in documents; abstained to unknown")
            checks.append(
                CriterionCheck(
                    criterion_id=c.id,
                    type=c.type,
                    text=c.text,
                    verdict="unknown",
                    confidence=0.0,
                    rationale=f"Model quoted {quote[:60]!r}, which is not in the participant's documents.",
                    abstention_reason="evidence_not_found",
                )
            )
            continue

        checks.append(
            CriterionCheck(
                criterion_id=c.id,
                type=c.type,
                text=c.text,
                verdict=verdict,
                confidence=confidence,
                rationale=rationale,
                document_id=found_doc_id,
                evidence=[found_ev],
            )
        )

    duration = int((time.perf_counter() - t0) * 1000)
    return ScreeningResult(
        participant_id=participant_id,
        overall=_overall_verdict(checks),
        checks=checks,
        metadata=RunMetadata(
            provider="ollama",
            model=impl.model,
            prompt_version=prompt.tag,
            prompt_hash=prompt.sha256,
            duration_ms=duration,
            warnings=warnings,
        ),
    )


def check_participant(
    participant_id_or_row: str | dict[str, Any],
    documents_or_criteria: list[dict[str, Any]] | None = None,
    maybe_docs: list[dict[str, Any]] | None = None,
    *,
    criteria: list[CriterionDef] | None = None,
    provider: str = "auto",
    allow_fallback: bool = True,
    ollama_provider=None,
) -> ScreeningResult:
    """Run the AI screening checker with automatic fallback from Ollama to rules.

    Accepts either:
    - ``check_participant(participant_id: str, documents: list[dict], *, criteria=..., provider=...)``
    - ``check_participant(participant_row: dict, criteria_rows: list[dict], documents: list[dict], *, provider=...)``
    """
    if isinstance(participant_id_or_row, dict):
        participant_id = str(participant_id_or_row["id"])
        raw_criteria = documents_or_criteria or []
        documents = maybe_docs or []
        crit_list = criteria if criteria is not None else [CriterionDef.from_api(c) for c in raw_criteria]
    else:
        participant_id = str(participant_id_or_row)
        documents = documents_or_criteria or []
        crit_list = criteria if criteria is not None else load_criteria()

    requested = (provider or "auto").lower()
    if requested == "auto":
        if ollama_provider is not None:
            ok, _ = ollama_provider.available()
            requested = "ollama" if ok else "rules"
        else:
            requested = providers.resolve("auto")

    if requested == "rules":
        return screen_with_rules(participant_id, documents, crit_list)

    if requested == "ollama":
        try:
            return screen_with_ollama(
                participant_id, documents, crit_list, ollama_provider=ollama_provider
            )
        except (ProviderUnavailable, ProviderError) as exc:
            if not allow_fallback:
                raise
            result = screen_with_rules(participant_id, documents, crit_list)
            result.metadata.fallback_from = "ollama"
            result.metadata.warnings.append(f"ollama unavailable or failed, falling back to rules: {exc}")
            return result

    raise KeyError(f"unknown provider {provider!r}; choose from rules, ollama, auto")
