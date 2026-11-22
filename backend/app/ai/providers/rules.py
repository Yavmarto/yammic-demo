"""Deterministic rules provider — always available, used as the fallback.

It is a small regex + terminology extractor for the 15 synthetic eCRF fields.
Every evidence span is produced from a real match in the document, so spans are
exact by construction. Fields with no match become explicit abstentions.
"""
from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Callable

from .. import registry, terminology
from ..span import expand_to_line, make_evidence
from ..types import Evidence, ExtractionResult, FieldDef, Proposal, RunMetadata

VERSION = "rules_v1"
# The rule set is the "prompt" for this deterministic provider; hash the module
# source so a change to any pattern produces a different recorded version.
PROMPT_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
PROMPT_TAG = f"{VERSION}@{PROMPT_HASH[:12]}"

# (pattern, normalizer) — the first match in this order wins.
Matcher = Callable[[str], "tuple[object, int, int, float, str] | None"]


def _value(match: re.Match[str], group: int = 1) -> str:
    return match.group(group).strip()


def _m(pattern: str, *, group: int = 1, flags: int = re.IGNORECASE) -> Callable:
    """Wrap a regex into a match that returns the captured value and the span of group 1."""
    rx = re.compile(pattern, flags)

    def match(text: str):
        m = rx.search(text)
        if not m:
            return None
        return _value(m, group), m.start(group), m.end(group), 0.95, m.group(0)
    return match


def rule_subjid(text: str):
    m = re.search(r"\b(?:PATIENTCODE|SUBJECT CODE|PATIËNTCODE)\s*:\s*(GBM-NL-\d{3})\b", text, re.I)
    if not m:
        return None
    return m.group(1).upper(), m.start(1), m.end(1), 0.99, m.group(0)


SITES = {
    "fictief universitair medisch centrum zuidhaven": "SITE-01",
    "fictional university medical center northhaven": "SITE-02",
    "fictief universitair medisch centrum noordhaven": "SITE-02",
    "fictief streekziekenhuis westpark": "SITE-03",
}


def rule_siteid(text: str):
    m = re.search(r"\bSITE-\d{2}\b", text)
    if m:
        return m.group(0).upper(), m.start(), m.end(), 0.99, m.group(0)
    low = text.casefold()
    for name, site in SITES.items():
        idx = low.find(name)
        if idx >= 0:
            return site, idx, idx + len(name), 0.98, text[idx:idx + len(name)]
    return None


def rule_labelled(label: str, value_rx: str, *, flags=re.I):
    rx = re.compile(rf"(?:{label})\s*[:\-]?\s*({value_rx})", flags)

    def match(text: str):
        m = rx.search(text)
        if not m:
            return None
        return _value(m), m.start(1), m.end(1), 0.96, m.group(0)
    return match


_SEX_NL = re.compile(r"GESLACHT\s*:\s*(vrouw|man)\b", re.I)
_SEX_EN = re.compile(r"\bSEX\s*:\s*(female|male)\b", re.I)


def rule_sex(text: str):
    for rx in (_SEX_NL, _SEX_EN):
        m = rx.search(text)
        if m:
            raw = m.group(1).casefold()
            normalized = "F" if raw in ("vrouw", "female") else "M"
            return normalized, m.start(0), m.end(0), 0.99, m.group(0)
    return None


def rule_age(text: str):
    for label in ("LEEFTIJD BIJ DIAGNOSE", "AGE AT DIAGNOSIS"):
        m = re.search(rf"{label}\s*[:\-]?\s*(\d{{1,3}})\s*(?:jaar|years?)?", text, re.I)
        if m:
            return int(m.group(1)), m.start(0), m.end(0), 0.97, m.group(0)
    return None


def rule_mhstdat(text: str):
    m = re.search(r"(?:DATUM ONTVANGST|SPECIMEN RECEIVED|DATE OF DIAGNOSIS|DIAGNOSED ON)"
                  r"\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})", text, re.I)
    if not m:
        return None
    return m.group(1), m.start(0), m.end(0), 0.92, m.group(0)


def rule_histology(text: str):
    m = re.search(r"(?:Glioblastoom|Glioblastoma)[,\s]+IDH[- ](?:wildtype|wild-type|mutant)", text, re.I)
    if not m:
        return None
    normalized = "glioblastoma_idh_mutant" if re.search(r"mutant", m.group(0), re.I) else "glioblastoma_idh_wildtype"
    return normalized, m.start(), m.end(), 0.97, m.group(0)


def rule_idhstat(text: str):
    m = re.search(r"IDH1\s+R132H[^\n.]{0,40}?\b(negatief|negative|positief|positive)\b", text, re.I)
    if m:
        raw = m.group(1).casefold()
        normalized = "mutant" if raw in ("positief", "positive") else "wildtype"
        # keep the whole clause in the highlight
        a, b = expand_to_line(text, m.start(), m.end(), left=0, right=0)
        return normalized, a, b, 0.96, text[a:b]
    return None


def rule_mgmtprom(text: str):
    negative = re.search(r"(?:niet[\s-]+gemethyleerd|unmethylated|not methylated|non-methylated|"
                         r"geen methylatie)", text, re.I)
    positive = re.search(r"(?:methylatie aangetoond|gemethyleerd|methylated|hypermethylated)", text, re.I)
    if not negative and not positive:
        return None
    if negative and (not positive or negative.start() <= positive.start()):
        normalized, m = "unmethylated", negative
    else:
        normalized, m = "methylated", positive
    # Highlight "MGMT promoter ... <word>" when it is on the same line.
    a, b = m.start(), m.end()
    line_start = text.rfind("\n", 0, a) + 1
    ctx = text[line_start:a]
    idx = ctx.casefold().rfind("mgmt")
    if idx >= 0 and a - (line_start + idx) <= 60:
        a = line_start + idx
    return normalized, a, b, 0.93, text[a:b]


def rule_kps(text: str):
    m = re.search(r"Karnofsky Performance Status[^\n:]{0,40}:\s*(\d{1,3})\s*%?", text, re.I)
    if not m:
        return None
    return int(m.group(1)), m.start(0), m.end(0), 0.9, m.group(0)


def rule_extres(text: str):
    gross = re.search(r"(?:gross[\s-]+total\s+(?:resectie|resection)|complete\s+resection|"
                      r"bruto\s+totale\s+resectie|totale\s+resectie)", text, re.I)
    sub = re.search(r"(?:sub[\s-]?total(?:e)?\s+(?:resectie|resection)|partial\s+resection)", text, re.I)
    hedge = re.search(r"(?:probably|probable|waarschijnlijk|may\s+be|possibly)\s+(?:a\s+)?sub", text, re.I)
    if gross and not (sub and sub.start() < gross.start()):
        return "gross_total", gross.start(), gross.end(), 0.91, gross.group(0)
    if hedge:
        return "subtotal", hedge.start(), hedge.end(), 0.45, hedge.group(0)
    if sub:
        return "subtotal", sub.start(), sub.end(), 0.89, sub.group(0)
    return None


def rule_rtdose(text: str):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*Gy\b", text)
    if not m:
        return None
    n = float(m.group(1).replace(",", "."))
    return (int(n) if n == int(n) else n), m.start(0), m.end(0), 0.96, m.group(0)


def rule_rtfrac(text: str):
    m = re.search(r"(\d+)\s*(?:fracties|fractions)\b", text, re.I)
    if not m:
        return None
    return int(m.group(1)), m.start(0), m.end(0), 0.96, m.group(0)


def rule_tmzplnc(text: str):
    m = re.search(r"(\d+)\s+(?:geplande\s+)?(?:cycli|cycles)\b", text, re.I)
    if not m:
        m = re.search(r"(\d+)\s+planned\s+[^.\n]{0,40}?(?:cycli|cycles)\b", text, re.I)
    if not m:
        return None
    return int(m.group(1)), m.start(0), m.end(0), 0.89, m.group(0)


_AE_SYMPTOMS = ("fatigue", "hoofdpijn", "headache", "nausea", "vermoeidheid", "rash", "diarree",
                "diarrhea", "trombocytopenie", "thrombocytopenia", "anemie", "anaemia",
                "neutropenie", "neutropenia", "misselijkheid")


def rule_aegrade(text: str):
    strong = re.search(r"(?:maximaal|maximum|max\.)\s+(?:graad|grade)\s+(\d)", text, re.I)
    if strong:
        return int(strong.group(1)), strong.start(0), strong.end(0), 0.86, strong.group(0)
    symptom = re.search(
        r"(?:graad|grade)\s+(\d+)\s+(?=" + "|".join(_AE_SYMPTOMS) + r")\b", text, re.I)
    if symptom:
        return int(symptom.group(1)), symptom.start(0), symptom.end(0), 0.82, symptom.group(0)
    above = re.search(r"(?:above|hoger dan|hoger)\s+(?:graad|grade)\s+(\d)", text, re.I)
    if above:
        return int(above.group(1)), above.start(0), above.end(0), 0.8, above.group(0)
    return None


def rule_progdat(text: str):
    # A date only when progression is explicitly dated; otherwise abstain.
    m = re.search(r"(?:progressie|progression|recidief|recurrence)[^.\n]{0,80}?"
                  r"(\d{4}-\d{2}-\d{2})", text, re.I)
    if m:
        return m.group(1), m.start(0), m.end(0), 0.85, m.group(0)
    return None


EXTRACTORS: dict[str, Callable] = {
    "SUBJID": rule_subjid,
    "SITEID": rule_siteid,
    "SEX": rule_sex,
    "AGE": rule_age,
    "MHSTDAT": rule_mhstdat,
    "HISTOLOGY": rule_histology,
    "IDHSTAT": rule_idhstat,
    "MGMTPROM": rule_mgmtprom,
    "KPS": rule_kps,
    "EXTRES": rule_extres,
    "RTDOSE": rule_rtdose,
    "RTFRAC": rule_rtfrac,
    "TMZPLNC": rule_tmzplnc,
    "AEGRADE": rule_aegrade,
    "PROGDAT": rule_progdat,
}


def _abstention_evidence(field: str, text: str) -> list[Evidence]:
    if field == "PROGDAT":
        m = re.search(r"[^.\n]*\bRANO\b[^.\n]*\.?", text, re.I)
        if not m:
            m = re.search(r"[^.\n]*Progressie kan[^.\n]*\.?", text, re.I)
        if m and m.group(0).strip():
            return [make_evidence(text, m.start(), m.end())]
    return []


class RulesProvider:
    name = "rules"
    model = "rules-regex-v1"
    paid = False

    def available(self) -> tuple[bool, str]:
        return True, "deterministic, offline"

    def extract(self, document_text: str, document_type: str,
                fields: list[FieldDef], *, prompt_version: str | None = None) -> ExtractionResult:
        t0 = time.perf_counter()
        proposals: list[Proposal] = []
        for field in fields:
            fn = EXTRACTORS.get(field.id)
            hit = fn(document_text) if fn else None
            if hit is None:
                proposals.append(Proposal(
                    field=field.id, status="abstained", value="Not stated",
                    confidence=0.0, abstention_reason="not_stated",
                    evidence=_abstention_evidence(field.id, document_text),
                    rationale=f"No deterministic rule matched {field.id} in this document.",
                ))
                continue
            normalized, start, end, confidence, _anchor = hit
            normalized, display = terminology.canonicalize(field.id, normalized)
            if normalized is None:
                proposals.append(Proposal(
                    field=field.id, status="abstained", value="Not stated", confidence=0.0,
                    abstention_reason="not_stated",
                    evidence=_abstention_evidence(field.id, document_text),
                    rationale=f"Rule matched but the value was not canonical for {field.id}.",
                ))
                continue
            proposals.append(Proposal(
                field=field.id, status="proposed", value=display,
                normalized_value=normalized, unit=field.unit, confidence=confidence,
                proposed_code=terminology.code_for(field),
                evidence=[make_evidence(document_text, start, end)],
                rationale=f"Deterministic {VERSION} rule matched {field.id}.",
            ))
        duration = int((time.perf_counter() - t0) * 1000)
        return ExtractionResult(
            proposals=proposals,
            metadata=RunMetadata(
                provider=self.name, model=self.model, prompt_version=PROMPT_TAG,
                prompt_hash=PROMPT_HASH, duration_ms=duration,
                document_type=document_type,
            ),
        )
