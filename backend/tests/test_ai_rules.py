"""Rules provider: span integrity, gold values, abstention behaviour."""
from __future__ import annotations

from app.ai.providers.rules import VERSION, RulesProvider
from app.ai.span import span_matches
from app.ai.types import FieldDef

from eval import gold as gold_mod


def _fields():
    return [FieldDef.from_api(f) for f in gold_mod.load_fields()]


def test_every_span_matches_source_text():
    fields = _fields()
    provider = RulesProvider()
    for doc in gold_mod.load_documents():
        result = provider.extract(doc["text"], doc["type"], fields)
        assert len(result.proposals) == len(fields) == 15
        for p in result.proposals:
            for ev in p.evidence:
                assert span_matches(doc["text"], ev), (doc["id"], p.field, ev)
        assert result.metadata.provider == "rules"
        assert result.metadata.prompt_version.startswith(VERSION)


def test_rules_match_gold_on_every_document():
    fields = _fields()
    gold = gold_mod.load_gold()
    provider = RulesProvider()
    for doc in gold_mod.load_documents():
        pred = provider.extract(doc["text"], doc["type"], fields).by_field()
        for field, expected in gold[doc["id"]].items():
            p = pred[field]
            if expected["status"] == "abstained":
                assert p.status == "abstained", (doc["id"], field, p)
            else:
                assert p.status == "proposed", (doc["id"], field, p)
                assert str(p.normalized_value).casefold() == str(expected["normalizedValue"]).casefold(), \
                    (doc["id"], field, p.normalized_value, expected["normalizedValue"])


def test_hard_cases_are_reproducible():
    fields = _fields()
    provider = RulesProvider()
    docs = {d["id"]: d for d in gold_mod.load_documents()}
    wrong = provider.extract(docs["DOC-002-PATH"]["text"], "pathology_report", fields).by_field()
    assert wrong["MGMTPROM"].normalized_value == "unmethylated"
    assert wrong["MGMTPROM"].confidence >= 0.6
    low = provider.extract(docs["DOC-002-MRI"]["text"], "radiology_report", fields).by_field()
    assert low["EXTRES"].normalized_value == "subtotal"
    assert low["EXTRES"].confidence < 0.6
    abst = provider.extract(docs["DOC-003-MRI"]["text"], "radiology_report", fields).by_field()
    assert abst["PROGDAT"].status == "abstained"
    assert abst["PROGDAT"].abstention_reason == "not_stated"
    assert abst["PROGDAT"].value == "Not stated"


def test_abstention_has_no_value_and_no_code():
    fields = _fields()
    doc = next(d for d in gold_mod.load_documents() if d["id"] == "DOC-001-MRI")
    result = RulesProvider().extract(doc["text"], doc["type"], fields)
    p = result.by_field()["PROGDAT"]
    assert p.status == "abstained"
    assert p.normalized_value is None
    assert p.proposed_code is None
    assert p.confidence == 0.0
    assert p.evidence and span_matches(doc["text"], p.evidence[0])


def test_unmatched_field_abstains():
    fields = _fields()
    result = RulesProvider().extract("Only a cover page. No clinical content.", "note", fields)
    assert all(p.status == "abstained" for p in result.proposals)
    assert all(p.abstention_reason == "not_stated" for p in result.proposals)
