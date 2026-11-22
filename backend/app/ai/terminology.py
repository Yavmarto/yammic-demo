"""Small, explicit terminology map for the 15 demo eCRF fields.

This is deliberately not a full terminology server. It canonicalises the
wording the model or the regex rules produce into the values the synthetic data
uses, and attaches the eCRF field's target code (with its ``codeVerified``
flag untouched; an unverified placeholder must never look authoritative).
"""
from __future__ import annotations

import copy
import re
from datetime import date, datetime
from typing import Any

DISPLAY: dict[str, dict[str, str]] = {
    "SEX": {"F": "Female", "M": "Male"},
    "HISTOLOGY": {
        "glioblastoma_idh_wildtype": "Glioblastoma, IDH-wildtype",
        "glioblastoma_idh_mutant": "Glioblastoma, IDH-mutant",
    },
    "IDHSTAT": {"wildtype": "IDH-wildtype", "mutant": "IDH-mutant"},
    "MGMTPROM": {"methylated": "Methylated", "unmethylated": "Unmethylated"},
    "EXTRES": {
        "gross_total": "Gross total resection",
        "subtotal": "Subtotal resection",
        "biopsy": "Biopsy only",
    },
}

# Fields whose value is a code plus a human display string.
CODED = {"SEX", "HISTOLOGY", "IDHSTAT", "MGMTPROM", "EXTRES"}
INTEGER = {"AGE", "KPS", "RTFRAC", "TMZPLNC", "AEGRADE"}
NUMBER = {"RTDOSE"}

SITE_CODES = {
    "zuidhaven": "SITE-01",
    "northhaven": "SITE-02",
    "noordhaven": "SITE-02",
    "westpark": "SITE-03",
}

_UNMETHYLATED = ("unmethylated", "niet gemethyleerd", "niet-gemethyleerd", "not methylated",
                 "non-methylated", "negative for methylation", "geen methylatie")
_METHYLATED = ("methylated", "gemethyleerd", "methylatie aangetoond", "hypermethylated",
               "positive for methylation")


def _first_number(raw: str) -> float | None:
    m = re.search(r"-?\d+(?:[.,]\d+)?", raw)
    if not m:
        return None
    return float(m.group(0).replace(",", "."))


def _canonical_date(raw: str) -> str | None:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", raw)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return None
    return None


def canonicalize(field: str, raw: Any) -> tuple[Any | None, str | None]:
    """Return ``(normalized_value, display_value)`` for a raw provider answer."""
    if raw is None:
        return None, None
    text = str(raw).strip()
    if not text:
        return None, None
    key = field.upper()
    if key in DISPLAY and text in DISPLAY[key]:
        return text, DISPLAY[key][text]

    if key in INTEGER:
        n = _first_number(text)
        if n is None or n != int(n):
            return None, None
        return int(n), str(int(n))
    if key in NUMBER:
        n = _first_number(text)
        if n is None:
            return None, None
        return (int(n) if n == int(n) else n), (str(int(n)) if n == int(n) else str(n))
    if key == "MHSTDAT" or key == "PROGDAT":
        d = _canonical_date(text)
        return (d, d) if d else (None, None)
    if key == "SUBJID":
        m = re.search(r"\bGBM-NL-\d{3}\b", text, re.IGNORECASE)
        if not m:
            return None, None
        v = m.group(0).upper()
        return v, v
    if key == "SITEID":
        m = re.search(r"\bSITE-\d{2}\b", text, re.IGNORECASE)
        if m:
            v = m.group(0).upper()
            return v, v
        low = text.casefold()
        for name, site in SITE_CODES.items():
            if name in low:
                return site, site
        return None, None
    if key == "SEX":
        low = text.casefold()
        if re.search(r"\b(f|female|vrouw|v)\b", low):
            return "F", DISPLAY["SEX"]["F"]
        if re.search(r"\b(m|male|man)\b", low):
            return "M", DISPLAY["SEX"]["M"]
        return None, None
    if key == "HISTOLOGY":
        low = text.casefold()
        if "glioblast" not in low:
            return None, None
        if re.search(r"idh[\s-]*(?:wild|wt|negative|negatief)", low) or "wildtype" in low:
            return "glioblastoma_idh_wildtype", DISPLAY["HISTOLOGY"]["glioblastoma_idh_wildtype"]
        if re.search(r"idh[\s-]*(?:mutant|mutated|positive|positief)", low):
            return "glioblastoma_idh_mutant", DISPLAY["HISTOLOGY"]["glioblastoma_idh_mutant"]
        # histology without an IDH statement is still a glioblastoma
        return "glioblastoma_idh_wildtype", DISPLAY["HISTOLOGY"]["glioblastoma_idh_wildtype"]
    if key == "IDHSTAT":
        low = text.casefold()
        if any(w in low for w in ("mutant", "mutated", "mutation", "positief", "positive")):
            if not re.search(r"\b(?:no|geen|without)\b", low):
                return "mutant", DISPLAY["IDHSTAT"]["mutant"]
        if any(w in low for w in ("wildtype", "wild-type", "wild type", "negatief", "negative", "wt")):
            return "wildtype", DISPLAY["IDHSTAT"]["wildtype"]
        return None, None
    if key == "MGMTPROM":
        low = text.casefold()
        if any(w in low for w in _UNMETHYLATED):
            return "unmethylated", DISPLAY["MGMTPROM"]["unmethylated"]
        if any(w in low for w in _METHYLATED):
            return "methylated", DISPLAY["MGMTPROM"]["methylated"]
        return None, None
    if key == "EXTRES":
        low = text.casefold()
        if any(w in low for w in ("gross total", "gross-total", "complete resection", "gtr",
                                  "bruto totale", "totale resectie", "complete", "compleet")):
            return "gross_total", DISPLAY["EXTRES"]["gross_total"]
        if any(w in low for w in ("subtotal", "sub-total", "partial resection", "incomplete",
                                  "subtotale")):
            return "subtotal", DISPLAY["EXTRES"]["subtotal"]
        if any(w in low for w in ("biopsy", "biopsie")):
            return "biopsy", DISPLAY["EXTRES"]["biopsy"]
        return None, None
    # plain strings
    return text, text


def code_for(field: FieldLike) -> dict[str, Any] | None:
    """The eCRF target code for a field, copied so callers cannot mutate the source."""
    term = getattr(field, "terminology", None)
    return copy.deepcopy(term) if term else None


class FieldLike:  # structural hint only; FieldDef satisfies it
    id: str
    terminology: dict[str, Any] | None


def display_value(field: str, normalized: Any) -> str | None:
    if normalized is None:
        return None
    if field in DISPLAY and str(normalized) in DISPLAY[field]:
        return DISPLAY[field][str(normalized)]
    return str(normalized)


def known_normalized(field: str, normalized: Any) -> bool:
    if normalized is None:
        return False
    if field in CODED:
        return str(normalized) in DISPLAY.get(field, {})
    return True
