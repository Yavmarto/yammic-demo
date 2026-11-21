"""Eval harness: rules provider must score cleanly and the hard cases must pass."""
from __future__ import annotations

import json

from app.ai import protocol, screening
from app.ai.providers import ollama as ollama_mod
from app.ai.providers.ollama import OllamaProvider
from app.ai.span import span_matches
from app.ai.types import ProviderError, ProviderUnavailable
from eval import harness, screening_eval


def test_rules_eval_is_perfect_and_hard_cases_pass(tmp_path):
    result = harness.evaluate("rules", dataset="all")
    s = result["summary"]
    assert s["spanErrors"] == 0
    assert s["precision"] == 1.0
    assert s["recall"] == 1.0
    assert s["f1"] == 1.0
    assert result["hardCases"]["allPass"] is True, result["hardCases"]
    # every field with gold proposals has a defined metric
    fields = {f["field"]: f for f in result["fields"]}
    assert fields["PROGDAT"]["abstentionRate"] == 1.0
    assert fields["EXTRES"]["support"] == 5


def test_eval_result_is_written_and_servable(tmp_path):
    result = harness.evaluate("rules", dataset="arrivals")
    run_path, md_path = harness.save(result, tmp_path)
    assert run_path.exists() and md_path.exists()
    assert (tmp_path / "latest-rules.json").exists()
    assert (tmp_path / "latest.json").exists()
    stored = json.loads((tmp_path / "latest-rules.json").read_text())
    assert stored["provider"]["name"] == "rules"
    assert stored["prompt"]["sha256"]
    assert stored["dataset"]["documents"] == 3
    assert len(stored["fields"]) == 15


def test_screening_eval_against_seeded_truth(tmp_path):
    res = screening_eval.evaluate_screening("rules")
    s = res["summary"]
    assert s["spanErrors"] == 0
    assert s["criterionAccuracy"] == 1.0, res["mismatches"]
    assert s["overallAccuracy"] == 1.0, res["patients"]
    path = screening_eval.save_screening_eval(res, tmp_path)
    assert path.exists() and (tmp_path / "latest-screening.json").exists()


def test_screening_checker_spans_abstention_and_ollama_relocation(monkeypatch):
    docs_by_patient = screening_eval.load_patient_documents()
    # Eligible patient GBM-NL-201
    docs_201 = docs_by_patient["GBM-NL-201"]
    docs_map = {d["id"]: d["text"] for d in docs_201}
    res_201 = screening.check_participant("GBM-NL-201", docs_201, provider="rules")
    assert res_201.overall == "eligible"
    assert all(c.verdict == "met" for c in res_201.checks)
    for c in res_201.checks:
        assert c.evidence and c.document_id in docs_map
        assert span_matches(docs_map[c.document_id], c.evidence[0])

    # Screen-fail patient GBM-NL-203 (KPS 50%)
    res_203 = screening.check_participant("GBM-NL-203", docs_by_patient["GBM-NL-203"], provider="rules")
    assert res_203.overall == "screen_fail"
    assert res_203.by_criterion()["INC-04"].verdict == "not_met"

    # Unknown criterion patient GBM-NL-204 (MGMT pending)
    res_204 = screening.check_participant("GBM-NL-204", docs_by_patient["GBM-NL-204"], provider="rules")
    assert res_204.overall == "unknown"
    inc03 = res_204.by_criterion()["INC-03"]
    assert inc03.verdict == "unknown" and inc03.confidence == 0.0

    # Ollama span relocation and unverified-quote abstention
    fake_ollama = OllamaProvider()
    monkeypatch.setattr(fake_ollama, "available", lambda: (True, "fake"))
    fake_payload = json.dumps({
        "checks": [
            {
                "criterionId": "INC-04",
                "verdict": "met",
                "documentId": "DOC-201-DIS",
                "evidenceQuote": "Karnofsky Performance Status bij ontslag: 80%",
                "confidence": 0.94,
                "rationale": "KPS is 80%",
            },
            {
                "criterionId": "INC-03",
                "verdict": "met",
                "documentId": "DOC-201-PATH",
                "evidenceQuote": "Hallucinated sentence not in the document",
                "confidence": 0.92,
                "rationale": "Hallucinated",
            },
        ]
    })
    monkeypatch.setattr(ollama_mod, "_post", lambda *a, **k: {"message": {"content": fake_payload}})
    ollama_res = screening.check_participant(
        "GBM-NL-201", docs_201, provider="ollama", ollama_provider=fake_ollama
    )
    by_id = ollama_res.by_criterion()
    assert by_id["INC-04"].verdict == "met"
    assert span_matches(docs_map["DOC-201-DIS"], by_id["INC-04"].evidence[0])
    # Hallucinated quote must abstain to unknown
    assert by_id["INC-03"].verdict == "unknown"
    assert by_id["INC-03"].abstention_reason == "evidence_not_found"
    # Unreported criteria must abstain to unknown
    assert by_id["INC-01"].verdict == "unknown"
    assert by_id["INC-01"].abstention_reason == "not_reported"


def test_screening_fallback_when_ollama_is_down(monkeypatch):
    docs_201 = screening_eval.load_patient_documents()["GBM-NL-201"]
    down_ollama = OllamaProvider()
    monkeypatch.setattr(down_ollama, "available", lambda: (False, "ollama is down"))
    res = screening.check_participant(
        "GBM-NL-201", docs_201, provider="ollama", allow_fallback=True, ollama_provider=down_ollama
    )
    assert res.overall == "eligible"
    assert res.metadata.provider == "rules"
    assert res.metadata.fallback_from == "ollama"
    assert any("falling back to rules" in w for w in res.metadata.warnings)


def test_protocol_to_form_proposals_spans_and_fallback(monkeypatch):
    synopsis = protocol.load_synopsis()
    res = protocol.propose_from_synopsis(synopsis, provider="rules")
    assert len(res.fields) == 15
    assert len(res.criteria) == 13
    for f in res.fields:
        assert f.source_sentence and f.evidence
        assert span_matches(synopsis, f.evidence[0])
        assert f.source_sentence == f.evidence[0].text
    for c in res.criteria:
        assert c.source_sentence and c.evidence
        assert span_matches(synopsis, c.evidence[0])
        assert c.source_sentence == c.evidence[0].text

    # Ollama unverified quote is dropped; Ollama error falls back to rules
    fake_ollama = OllamaProvider()
    monkeypatch.setattr(fake_ollama, "available", lambda: (True, "fake"))
    bad_payload = json.dumps({
        "fields": [
            {
                "id": "KPS",
                "label": "Karnofsky Performance Status",
                "type": "integer",
                "unit": "%",
                "sourceSentence": "| KPS | Karnofsky Performance Status | integer, % | QS.QSORRES |",
                "confidence": 0.95,
            },
            {
                "id": "FAKE",
                "label": "Fake field",
                "type": "string",
                "sourceSentence": "Not in synopsis at all",
                "confidence": 0.9,
            },
        ],
        "criteria": [
            {
                "id": "INC-01",
                "type": "inclusion",
                "text": "Age >=18 years at diagnosis.",
                "sourceSentence": "1. **INC-01 — Age.** Age ≥18 years at diagnosis.",
                "confidence": 0.95,
            }
        ],
    })
    monkeypatch.setattr(ollama_mod, "_post", lambda *a, **k: {"message": {"content": bad_payload}})
    o_res = protocol.propose_from_synopsis(synopsis, provider="ollama", ollama_provider=fake_ollama)
    assert [f.id for f in o_res.fields] == ["KPS"]
    assert span_matches(synopsis, o_res.fields[0].evidence[0])
    assert [c.id for c in o_res.criteria] == ["INC-01"]
    assert span_matches(synopsis, o_res.criteria[0].evidence[0])

    # Fallback when Ollama fails mid-call
    monkeypatch.setattr(ollama_mod, "_post", lambda *a, **k: (_ for _ in ()).throw(ProviderError("boom")))
    fb_res = protocol.propose_from_synopsis(synopsis, provider="ollama", ollama_provider=fake_ollama)
    assert fb_res.metadata.provider == "rules"
    assert fb_res.metadata.fallback_from == "ollama"
    assert len(fb_res.fields) == 15 and len(fb_res.criteria) == 13


def test_screening_and_protocol_api_endpoints(client, auth, monkeypatch):
    nurse = auth("nurse")
    # 1. GET /ai/criteria
    crit_res = client.get("/ai/criteria", headers=nurse)
    assert crit_res.status_code == 200
    assert len(crit_res.json()["criteria"]) == 13

    # 2. POST /ai/participants/GBM-NL-001/screen (and /participants/GBM-NL-001/screening/check)
    scr_res = client.post("/ai/participants/GBM-NL-001/screen?provider=rules", headers=nurse)
    assert scr_res.status_code == 200
    scr_body = scr_res.json()
    assert scr_body["participantId"] == "GBM-NL-001"
    assert len(scr_body["criteria"]) == 13
    by_cid = {c["criterionId"]: c for c in scr_body["criteria"]}
    assert by_cid["INC-01"]["verdict"] == "met"
    assert by_cid["INC-02"]["verdict"] == "met"
    assert by_cid["INC-04"]["verdict"] == "met"

    # 3. GET & POST /ai/protocol/proposals
    prop_get = client.get("/ai/protocol/proposals?provider=rules", headers=nurse)
    assert prop_get.status_code == 200
    assert len(prop_get.json()["fields"]) == 15
    assert len(prop_get.json()["criteria"]) == 13

    prop_post = client.post("/ai/protocol/proposals?provider=rules", json={}, headers=nurse)
    assert prop_post.status_code == 200
    assert len(prop_post.json()["fields"]) == 15

    # 4. GET /ai/screening/eval
    eval_res = client.get("/ai/screening/eval?provider=rules", headers=nurse)
    assert eval_res.status_code == 200
    assert eval_res.json()["summary"]["criterionAccuracy"] == 1.0
