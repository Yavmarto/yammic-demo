"""Pseudonymisation. The hospital MRN and the patient name never reach the database.

* `mrn_hmac` = HMAC-SHA256(key, "mrn:" + MRN): lets a re-sync recognise a patient without storing the MRN.
* `pseudonym` = "PSN-" + 12 hex chars of that HMAC: the study pseudonym used wherever an identifier
  would appear in free text.
* `Scrubber` removes the MRN and every name token from text before it is stored.
"""
import hashlib
import hmac
import os
import re

if len(os.environ.get("PSEUDONYM_KEY", "")) < 32:  # fail closed, no committed default
    raise RuntimeError("PSEUDONYM_KEY missing or shorter than 32 chars (run via make, or set it)")
KEY = os.environ["PSEUDONYM_KEY"].encode()


def mrn_hmac(mrn: str) -> str:
    return hmac.new(KEY, b"mrn:" + mrn.strip().encode(), hashlib.sha256).hexdigest()


def pseudonym(mrn: str) -> str:
    return "PSN-" + mrn_hmac(mrn)[:12].upper()


def patient_terms(p: dict) -> tuple[str | None, set[str]]:
    """(MRN, identifying strings) from a Patient resource."""
    mrn, terms = None, set()
    for i in p.get("identifier", []):
        if any(c.get("code") == "MR" for c in (i.get("type") or {}).get("coding", [])):
            mrn = i.get("value")
    if mrn:
        terms.add(mrn)
    for n in p.get("name", []):
        terms.update([n.get("family", ""), *n.get("given", []), re.sub(r"\s*\(.*?\)", "", n.get("text", ""))])
    return mrn, {t.strip() for t in terms if len(t.strip()) >= 3}


class Scrubber:
    def __init__(self, terms: set[str], replacement: str):
        parts = [re.escape(t) for t in sorted(terms, key=len, reverse=True)]
        parts.append(r"\bMRN[-\s:]*[A-Z0-9-]*\d[A-Z0-9-]*")  # any MRN-looking token
        self.rx, self.rep = re.compile("|".join(parts), re.I), replacement

    def text(self, s: str) -> str:
        return self.rx.sub(self.rep, s)
