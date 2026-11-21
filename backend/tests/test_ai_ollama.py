"""Ollama provider behaviour without a live model: schema handling + span re-location."""
from __future__ import annotations

import json

from app.ai.providers.ollama import OllamaProvider
from app.ai.span import locate_quote, span_matches
from app.ai.types import FieldDef

from eval import gold as gold_mod

DOC = """SYNTHETIC DOCUMENT
Fictional University Medical Center Northhaven
SUBJECT CODE: GBM-NL-009
AGE: 52 years
Karnofsky Performance Status: 80%
MGMT promoter is unmethylated.
"""


def _fields():
    return [FieldDef.from_api(f) for f in gold_mod.load_fields()]


def _provider(monkeypatch, items):
    p = OllamaProvider()
    monkeypatch.setattr(p, "available", lambda: (True, "fake"))
    payload = json.dumps({"extractions": items})
    monkeypatch.setattr(p, "_chat", lambda *a, **k: {"message": {"content": payload}})
    return p


def test_quote_not_found_becomes_abstention(monkeypatch):
    p = _provider(monkeypatch, [
        {"field": "KPS", "status": "proposed", "value": "80",
         "evidenceQuote": "This sentence is not in the document.", "confidence": 0.9,
         "rationale": "x"},
    ])
    result = p.extract(DOC, "discharge_letter", _fields())
    kps = result.by_field()["KPS"]
    assert kps.status == "abstained" and kps.abstention_reason == "evidence_not_found"
    assert any("evidence quote not found" in w for w in result.metadata.warnings)


def test_every_accepted_span_is_relocated_exactly(monkeypatch):
    p = _provider(monkeypatch, [
        {"field": "MGMTPROM", "status": "proposed", "value": "unmethylated",
         "evidenceQuote": "MGMT promoter is unmethylated", "confidence": 0.9, "rationale": "x"},
        {"field": "SITEID", "status": "proposed", "value": "SITE-02",
         "evidenceQuote": "Fictional University Medical Center Northhaven", "confidence": 0.9,
         "rationale": "x"},
        {"field": "KPS", "status": "proposed", "value": "",
         "evidenceQuote": "Karnofsky Performance Status: 80%", "confidence": 0.9, "rationale": "x"},
    ])
    result = p.extract(DOC, "discharge_letter", _fields())
    by = result.by_field()
    assert by["MGMTPROM"].normalized_value == "unmethylated"
    assert by["SITEID"].normalized_value == "SITE-02"
    assert by["KPS"].normalized_value == 80  # recovered from the verified quote
    for field in ("MGMTPROM", "SITEID", "KPS"):
        assert by[field].evidence and span_matches(DOC, by[field].evidence[0])


def test_missing_field_is_an_abstention(monkeypatch):
    p = _provider(monkeypatch, [])
    result = p.extract(DOC, "note", _fields())
    assert all(x.status == "abstained" and x.abstention_reason == "not_reported"
               for x in result.proposals)


def test_whitespace_and_case_relocation():
    found = locate_quote(DOC, "mgmt promoter   is\nunmethylated")
    assert found is not None
    start, end, text = found
    assert DOC[start:end] == text and "unmethylated" in text.casefold()
