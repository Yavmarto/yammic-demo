"""Service flow through the real API (TestClient): queue, process, fallback."""
from __future__ import annotations

import json

import pytest

from app.ai import routes as ai_routes
from app.ai.client import ApiError
from app.ai.providers.ollama import OllamaProvider
from app.ai.service import process_run
from app.ai.types import ProviderError, ProviderUnavailable


class ApiAdapter:
    """Adapter so the service can use TestClient exactly like the HTTP client."""

    def __init__(self, client, headers):
        self.client = client
        self.headers = headers

    def _check(self, res):
        if res.status_code >= 400:
            raise ApiError(res.status_code, res.text, res.request.url)
        return res.json()

    def get(self, path):
        return self._check(self.client.get(path, headers=self.headers))

    def post(self, path, payload):
        return self._check(self.client.post(path, json=payload, headers=self.headers))

    def patch(self, path, payload):
        return self._check(self.client.patch(path, json=payload, headers=self.headers))

    # same domain helpers as HttpApiClient
    def queued_runs(self):
        return self.get("/runs?status=queued")

    def get_run(self, run_id):
        return self.get(f"/runs/{run_id}")

    def get_document(self, document_id):
        return self.get(f"/documents/{document_id}")

    def documents(self, participant_id):
        return self.get(f"/participants/{participant_id}/documents")

    def ecrf_fields(self, participant_id):
        return self.get(f"/participants/{participant_id}/ecrf")["fields"]

    def update_run(self, run_id, payload):
        return self.patch(f"/runs/{run_id}", payload)

    def post_extractions(self, run_id, payloads):
        return self.post(f"/runs/{run_id}/extractions", payloads)


def _ai_adapter(client, ai_headers):
    return ApiAdapter(client, ai_headers)


def _queue(client, headers, provider="rules", doc="DOC-001-PATH", pid="GBM-NL-001"):
    r = client.post(f"/participants/{pid}/extract?provider={provider}",
                    json={"documentId": doc}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_live_run_with_rules_through_api(client, auth):
    nurse, service = auth("nurse"), auth("ai")
    run = _queue(client, nurse, "rules")
    assert run["status"] == "queued" and run["provider"] == "rules"

    outcome = process_run(_ai_adapter(client, service), run, provider="rules")
    assert outcome["status"] == "completed"
    assert outcome["provider"] == "rules"
    assert outcome["proposals"] == 15
    assert outcome["documents"] == 1

    stored = client.get(f"/runs/{run['id']}", headers=nurse).json()
    assert stored["status"] == "completed" and stored["done"] == 15 and stored["total"] == 15
    assert stored["provider"] == "rules" and stored["promptVersion"].startswith("rules_v1")

    xs = client.get(f"/participants/GBM-NL-001/extractions?documentId=DOC-001-PATH",
                    headers=nurse).json()
    mine = [x for x in xs if x["runId"] == run["id"]]
    assert len(mine) == 15
    proposed = [x for x in mine if x["status"] == "proposed"]
    assert proposed
    for x in proposed:
        assert x["evidence"], x
        assert x["provider"] == "rules" and x["promptVersion"].startswith("rules_v1")
        assert x["spanStart"] is not None and x["spanEnd"] is not None


def test_ollama_down_falls_back_to_rules(client, auth, monkeypatch):
    monkeypatch.setattr(OllamaProvider, "available",
                        lambda self: (False, "ollama is down (test)"))
    monkeypatch.setattr(OllamaProvider, "extract",
                        lambda self, *a, **k: (_ for _ in ()).throw(ProviderUnavailable("down")))
    nurse, service = auth("nurse"), auth("ai")
    run = _queue(client, nurse, "ollama")
    outcome = process_run(_ai_adapter(client, service), run, provider="ollama")
    assert outcome["status"] == "completed"
    assert outcome["provider"] == "rules"
    assert outcome["fallbackFrom"] == "ollama"
    assert any("falling back to rules" in w for w in outcome["warnings"])
    stored = client.get(f"/runs/{run['id']}", headers=nurse).json()
    assert stored["status"] == "completed" and stored["provider"] == "rules"


def test_ollama_mid_run_error_falls_back_to_rules(client, auth, monkeypatch):
    monkeypatch.setattr(OllamaProvider, "available", lambda self: (True, "fake"))
    monkeypatch.setattr(OllamaProvider, "extract",
                        lambda self, *a, **k: (_ for _ in ()).throw(ProviderError("bad json")))
    nurse, service = auth("nurse"), auth("ai")
    run = _queue(client, nurse, "ollama")
    outcome = process_run(_ai_adapter(client, service), run, provider="ollama")
    assert outcome["status"] == "completed"
    assert outcome["provider"] == "rules"
    assert outcome["fallbackFrom"] == "ollama"
    assert outcome["proposals"] == 15
    xs = client.get(f"/participants/GBM-NL-001/extractions?documentId=DOC-001-PATH",
                    headers=nurse).json()
    assert len([x for x in xs if x["runId"] == run["id"]]) == 15


def test_extract_endpoint_roles_and_provider_validation(client, auth):
    monitor, nurse = auth("monitor"), auth("nurse")
    assert client.post("/participants/GBM-NL-001/extract?provider=rules", json={},
                       headers=monitor).status_code == 403
    assert client.post("/participants/GBM-NL-001/extract?provider=openai", json={},
                       headers=nurse).status_code == 422
    assert client.post("/participants/NOPE/extract?provider=rules", json={},
                       headers=nurse).status_code == 404


def test_ai_registry_and_eval_endpoints(client, auth, monkeypatch, tmp_path):
    h = auth("nurse")
    providers = client.get("/ai/providers", headers=h).json()
    by_name = {p["name"]: p for p in providers["providers"]}
    assert by_name["rules"]["available"] is True
    assert by_name["claude"]["available"] is False and by_name["claude"]["paid"] is True

    prompts = client.get("/ai/prompts", headers=h).json()["prompts"]
    assert prompts and prompts[-1]["active"] is True
    assert len(prompts[-1]["sha256"]) == 64

    monkeypatch.setattr(ai_routes, "RESULTS", tmp_path)
    assert client.get("/ai/eval", headers=h).status_code == 404
    (tmp_path / "latest.json").write_text(json.dumps({"summary": {"f1": 0.9}, "provider": {"name": "rules"}}))
    body = client.get("/ai/eval", headers=h).json()
    assert body["available"] is True and body["results"]["summary"]["f1"] == 0.9

    runs = client.get("/ai/runs", headers=h).json()
    assert isinstance(runs, list) and runs
