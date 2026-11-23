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
        for field, expected in gold.get(doc["id"], {}).items():  # screening-only docs have no gold fields
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


def test_mgmt_addendum_supersedes_earlier_result_with_exact_span():
    text = "MGMT-promotor: gemethyleerd. Addendum: herbeoordeling toont geen methylatie; eerste uitslag vervalt."
    p = RulesProvider().extract(text, "pathology_report", _fields()).by_field()["MGMTPROM"]
    assert p.status == "proposed"
    assert p.normalized_value == "unmethylated"
    assert [ev.text for ev in p.evidence] == ["Addendum: herbeoordeling toont geen methylatie"]


def test_mgmt_first_stated_result_still_used_without_addendum():
    text = "MGMT-promotor: niet gemethyleerd."
    p = RulesProvider().extract(text, "pathology_report", _fields()).by_field()["MGMTPROM"]
    assert p.normalized_value == "unmethylated"
    assert [ev.text for ev in p.evidence] == ["MGMT-promotor: niet gemethyleerd"]


def test_progression_evidence_covers_clause_after_date():
    text = "Progressie werd op 2026-03-01 bevestigd; eerdere verdenking was onzeker."
    p = RulesProvider().extract(text, "oncology_note", _fields()).by_field()["PROGDAT"]
    assert p.normalized_value == "2026-03-01"
    assert [ev.text for ev in p.evidence] == ["Progressie werd op 2026-03-01 bevestigd"]


def test_hedged_resection_abstains_when_operative_note_is_missing():
    text = "Resectie: waarschijnlijk subtotale resectie. Definitieve operatienotitie ontbreekt."
    p = RulesProvider().extract(text, "radiology_report", _fields()).by_field()["EXTRES"]
    assert p.status == "abstained"


def test_progression_date_span_stops_before_attribution():
    text = "Progressie vastgesteld op 2026-02-14 volgens RANO."
    p = RulesProvider().extract(text, "oncology_note", _fields()).by_field()["PROGDAT"]
    assert p.normalized_value == "2026-02-14"
    assert [ev.text for ev in p.evidence] == ["Progressie vastgesteld op 2026-02-14"]


def test_planned_subtotal_resection_abstains():
    text = "Planning: subtotale resectie gepland op 2026-04-02. Operatie nog niet uitgevoerd."
    p = RulesProvider().extract(text, "radiology_report", _fields()).by_field()["EXTRES"]
    assert p.status == "abstained"


def test_extent_not_assessable_hedge_abstains():
    text = "Possibly subtotal resection; extent cannot be assessed on this MRI."
    p = RulesProvider().extract(text, "radiology_report", _fields()).by_field()["EXTRES"]
    assert p.status == "abstained"


def test_idh_negative_word_after_semicolon_does_not_attach_to_idh():
    text = "IDH1 R132H: niet getest; ATRX-expressie positief."
    p = RulesProvider().extract(text, "pathology_report", _fields()).by_field()["IDHSTAT"]
    assert p.status == "abstained"


def test_idh_positive_control_still_proposed_with_exact_span():
    text = "IDH1 R132H immunohistochemie: positief."
    p = RulesProvider().extract(text, "pathology_report", _fields()).by_field()["IDHSTAT"]
    assert p.normalized_value == "mutant"
    assert [ev.text for ev in p.evidence] == ["IDH1 R132H immunohistochemie: positief"]
