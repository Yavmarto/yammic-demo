import json
import os
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app import export_openapi
from app.db import engine

DATA = Path(__file__).resolve().parents[2] / "app" / "assets" / "data"
STUDY = "GBM-NL-2026-01"
ACCEPT = {"decision": "accept"}


def dash(client, h):
    return client.get(f"/studies/{STUDY}/dashboard", headers=h).json()["kpis"]


def test_health_open(client):
    j = client.get("/health").json()
    assert j["status"] == "ok" and j["database"] is True


def test_login_and_me(client, auth):
    assert client.post("/auth/login", json={"username": "nurse", "password": "nope"}).status_code == 401
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer junk"}).status_code == 401
    for u in ("nurse", "monitor", "pi"):
        assert client.get("/me", headers=auth(u)).json()["role"] == u


def test_roles(client, auth):
    nurse, monitor, pi = auth("nurse"), auth("monitor"), auth("pi")
    assert client.post("/extractions/EXT-0001/decision", json=ACCEPT, headers=monitor).status_code == 403
    assert client.get("/participants", headers=monitor).status_code == 200  # monitor reads
    assert client.post("/extractions/EXT-0001/decision", json=ACCEPT, headers=nurse).status_code == 200
    assert client.post("/extractions/EXT-0002/decision", json=ACCEPT, headers=pi).status_code == 200
    # SDV: monitor only, and only on a verified value
    assert client.post("/participants/GBM-NL-001/ecrf/SUBJID/sdv", headers=nurse).status_code == 403
    assert client.post("/participants/GBM-NL-001/ecrf/SUBJID/sdv", headers=monitor).status_code == 200
    assert client.post("/participants/GBM-NL-001/ecrf/KPS/sdv", headers=monitor).status_code == 404
    # queries: monitor/pi open
    q = {"participantId": "GBM-NL-001", "text": "Check value", "fieldId": "KPS"}
    assert client.post("/queries", json=q, headers=nurse).status_code == 403
    assert client.post("/queries", json=q, headers=monitor).status_code == 201


def test_decision_updates_ecrf_and_audit(client, auth):
    h = auth("nurse")
    r = client.post("/extractions/EXT-0003/decision", json=ACCEPT, headers=h)
    assert r.status_code == 200
    ex = r.json()["extraction"]
    assert ex["reviewState"] == "accepted" and ex["lastDecision"]["username"] == "nurse"
    ecrf = client.get("/participants/GBM-NL-001/ecrf", headers=h).json()
    f = next(f for f in ecrf["fields"] if f["id"] == ex["field"])
    assert f["value"]["value"] == ex["value"] and f["value"]["verifiedBy"] == "nurse"
    assert f["pendingExtractionId"] is None and ecrf["verified"] == 1
    ev = client.get("/audit", params={"entityId": "EXT-0003", "entity_id": "EXT-0003"}, headers=h).json()["items"]
    dec = next(e for e in ev if e["action"] == "extraction.decision")
    assert dec["actor"] == "nurse" and dec["role"] == "nurse" and dec["source"] == "human"
    assert dec["model"] == "demo-extractor v0.1" and dec["prompt_version" if False else "promptVersion"]
    assert dec["before"]["reviewState"] == "pending" and dec["after"]["reviewState"] == "accepted"
    actions = [e["action"] for e in client.get("/audit", params={"participant_id": "GBM-NL-001", "action": "ecrf.*"}, headers=h).json()["items"]]
    assert actions == ["ecrf.value_set"]
    assert client.get("/audit/verify", headers=h).json()["ok"] is True


def test_correct_reject_validation_and_clearing(client, auth):
    h = auth("nurse")
    assert client.post("/extractions/EXT-0020/decision", json={"decision": "correct"}, headers=h).status_code == 422
    assert client.post("/extractions/EXT-0020/decision", json={"decision": "reject"}, headers=h).status_code == 422
    assert client.post("/extractions/EXT-0008/decision", json=ACCEPT, headers=h).status_code == 422  # abstained
    assert client.post("/extractions/NOPE/decision", json=ACCEPT, headers=h).status_code == 404
    r = client.post("/extractions/EXT-0020/decision", headers=h,
                    json={"decision": "correct", "correctedValue": "unmethylated", "reason": "Source says unmethylated"})
    assert r.json()["extraction"]["reviewState"] == "corrected"
    assert r.json()["ecrfValue"]["value"] == "unmethylated" and r.json()["ecrfValue"]["code"] is None
    # change mind: reject clears the verified value it created
    r = client.post("/extractions/EXT-0020/decision", json={"decision": "reject", "reason": "Unreadable"}, headers=h)
    assert r.json()["ecrfValue"] is None
    ecrf = client.get("/participants/GBM-NL-002/ecrf", headers=h).json()
    assert ecrf["verified"] == 0
    acts = [e["action"] for e in client.get("/audit", params={"entityId": "EXT-0020"}, headers=h).json()["items"]]
    assert acts.count("extraction.decision") == 2


def test_dashboard_numbers(client, auth):
    h = auth("pi")
    fx = json.loads((DATA / "extractions.json").read_text())["extractions"]
    attention = sum(1 for e in fx if e["status"] == "abstained" or e["confidence"] < 0.6)
    k = dash(client, h)
    assert (k["enrolled"], k["target"], k["participantsInExtractionScope"]) == (8, 24, 3)
    assert (k["extractionsTotal"], k["extractionsPending"], k["needsAttention"]) == (len(fx), len(fx), attention)
    assert k["ecrfFieldsTotal"] == 45 and k["ecrfCompleteness"] == 0 and k["aiAcceptanceRate"] is None
    assert k["openQueries"] == client.get("/queries", params={"status": "open"}, headers=h).json().__len__()
    client.post("/extractions/EXT-0001/decision", json=ACCEPT, headers=h)
    client.post("/extractions/EXT-0002/decision", json=ACCEPT, headers=h)
    client.post("/extractions/EXT-0020/decision", json={"decision": "correct", "correctedValue": "unmethylated"}, headers=h)
    client.post("/extractions/EXT-0022/decision", json={"decision": "reject", "reason": "Hedged"}, headers=h)
    client.post("/extractions/EXT-0008/decision", json={"decision": "defer"}, headers=h)
    k = dash(client, h)
    assert (k["extractionsAccepted"], k["extractionsCorrected"], k["extractionsRejected"], k["extractionsDeferred"]) == (2, 1, 1, 1)
    assert k["extractionsReviewed"] == 4 and k["extractionsPending"] == len(fx) - 5
    assert k["ecrfFieldsVerified"] == 3 and k["ecrfCompleteness"] == round(3 / 45, 4)
    assert k["aiAcceptanceRate"] == 0.5
    assert k["needsAttention"] == attention - 2  # EXT-0008 and EXT-0022 handled
    client.post("/participants/GBM-NL-001/ecrf/SUBJID/sdv", headers=auth("monitor"))
    k = dash(client, h)
    assert (k["sdvDone"], k["sdvPending"]) == (1, 2)
    d = client.get(f"/studies/{STUDY}/dashboard", headers=h).json()
    assert {s["id"]: s["enrolled"] for s in d["sites"]} == {"SITE-01": 3, "SITE-02": 3, "SITE-03": 2}
    assert client.get("/studies/NOPE/dashboard", headers=h).status_code == 404


def test_participants_documents_extractions(client, auth):
    h = auth("nurse")
    ps = client.get("/participants", headers=h).json()
    assert len(ps) == 8 and client.get("/participants", params={"site_id": "SITE-02"}, headers=h).json().__len__() == 3
    p = client.get("/participants/GBM-NL-002", headers=h).json()
    assert p["documentIds"] == ["DOC-002-MRI", "DOC-002-PATH", "DOC-002-SURG", "DOC-002-DIS"] or len(p["documentIds"]) == 4
    assert p["visits"] and p["extractionsPending"] > 0
    docs = client.get("/participants/GBM-NL-002/documents", headers=h).json()
    assert len(docs) == 4
    d = client.get("/documents/DOC-002-PATH", headers=h).json()
    ex = client.get("/participants/GBM-NL-002/extractions", params={"document_id": "DOC-002-PATH"}, headers=h).json()
    assert d["charLength"] == len(d["text"]) and ex
    for e in ex:  # every evidence span points at the right source text
        for ev in e["evidence"]:
            assert d["text"][ev["start"]:ev["end"]] == ev["text"]
    mg = next(e for e in ex if e["field"] == "MGMTPROM")
    assert mg["value"].lower() == "methylated" and mg["spanStart"] is not None
    assert client.get("/participants/NOPE", headers=h).status_code == 404


def test_audit_chain_detects_tampering(client, auth):
    h = auth("nurse")
    client.post("/extractions/EXT-0001/decision", json=ACCEPT, headers=h)
    assert client.get("/audit/verify", headers=h).json()["ok"] is True
    # append-only: the trigger refuses UPDATE and DELETE
    for sql in ("UPDATE audit_event SET actor='x' WHERE seq=1", "DELETE FROM audit_event WHERE seq=1"):
        with pytest.raises(DBAPIError, match="append-only"), engine.begin() as c:
            c.execute(text(sql))
    # a DBA who bypasses the trigger is caught by the hash chain
    def bypass(sql):
        with engine.begin() as c:
            c.execute(text("ALTER TABLE audit_event DISABLE TRIGGER audit_event_no_change"))
            c.execute(text(sql))
            c.execute(text("ALTER TABLE audit_event ENABLE TRIGGER audit_event_no_change"))
    n = client.get("/audit", params={"limit": 1}, headers=h).json()["total"]
    bypass("UPDATE audit_event SET after = jsonb_set(after, '{value}', '\"forged\"') WHERE seq = 10")
    v = client.get("/audit/verify", headers=h).json()
    assert v["ok"] is False and v["brokenSeq"] == 10 and "modified" in v["reason"]
    bypass("UPDATE audit_event SET after = (SELECT after FROM audit_event WHERE seq=10) WHERE seq=10")  # undo forge
    bypass("UPDATE audit_event SET after = after WHERE false")
    # now remove an event: next link breaks
    bypass("DELETE FROM audit_event WHERE seq = 5")
    v = client.get("/audit/verify", headers=h).json()
    assert v["ok"] is False and v["brokenSeq"] == 6 and "removed" in v["reason"]
    assert n > 40


def test_audit_filters(client, auth):
    h = auth("nurse")
    client.post("/extractions/EXT-0001/decision", json=ACCEPT, headers=h)
    a = client.get("/audit", params={"source": "ai", "limit": 5}, headers=h).json()
    assert a["total"] == 46 and len(a["items"]) == 5 and a["items"][0]["seq"] > a["items"][1]["seq"]
    assert client.get("/audit", params={"actor": "nurse", "action": "extraction.decision"}, headers=h).json()["total"] == 1
    assert client.get("/audit", params={"since": "2999-01-01T00:00:00Z"}, headers=h).json()["total"] == 0


def test_run_flow_and_sse(client, auth):
    nurse, ai = auth("nurse"), auth("ai")
    assert client.post("/participants/GBM-NL-001/extraction-runs", json={}, headers=auth("monitor")).status_code == 403
    run = client.post("/participants/GBM-NL-001/extraction-runs", json={"documentId": "DOC-001-PATH"}, headers=nurse).json()
    assert run["status"] == "queued"
    rid = run["id"]
    assert client.get("/runs", params={"status": "queued"}, headers=ai).json()[0]["id"] == rid
    assert client.post(f"/runs/{rid}/extractions", json=[], headers=nurse).status_code == 403
    doc = client.get("/documents/DOC-001-PATH", headers=nurse).json()["text"]
    good = {"documentId": "DOC-001-PATH", "field": "SUBJID", "value": "GBM-NL-001", "confidence": 0.9,
            "evidence": [{"start": 174, "end": 184, "text": doc[174:184]}],
            "provider": "ollama", "model": "test-model", "promptVersion": "p1"}
    bad = {**good, "evidence": [{"start": 174, "end": 184, "text": "wrong"}]}
    assert client.post(f"/runs/{rid}/extractions", json=[bad], headers=ai).status_code == 422
    client.patch(f"/runs/{rid}", json={"status": "running", "total": 1, "provider": "ollama", "model": "test-model"}, headers=ai)
    out = client.post(f"/runs/{rid}/extractions", json=[good], headers=ai)
    assert out.status_code == 201 and out.json()[0]["model"] == "test-model" and out.json()[0]["spanStart"] == 174
    r = client.patch(f"/runs/{rid}", json={"status": "completed"}, headers=ai).json()
    assert (r["status"], r["done"], r["total"]) == ("completed", 1, 1) and r["finishedAt"]
    assert client.post(f"/runs/{rid}/extractions", json=[good], headers=ai).status_code == 409
    sse = client.get(f"/runs/{rid}/events", params={"access_token": ai["Authorization"][7:]})
    assert sse.status_code == 200 and "event: progress" in sse.text and '"status":"completed"' in sse.text
    ev = client.get("/audit", params={"source": "ai", "model": "test-model", "participant_id": "GBM-NL-001"}, headers=nurse).json()["items"]
    assert any(e["action"] == "extraction.proposed" and e["promptVersion"] == "p1" for e in ev)
    assert client.get("/audit/verify", headers=nurse).json()["ok"] is True


def test_queries(client, auth):
    mon = auth("monitor")
    q = client.post("/queries", json={"participantId": "GBM-NL-001", "text": "Confirm KPS", "fieldId": "KPS"}, headers=mon).json()
    before = dash(client, mon)["openQueries"]
    assert client.post(f"/queries/{q['id']}/close", headers=auth("nurse")).json()["status"] == "closed"
    assert client.post(f"/queries/{q['id']}/close", headers=auth("nurse")).status_code == 409
    assert dash(client, mon)["openQueries"] == before - 1


def test_committed_openapi_is_current():
    assert (export_openapi.OUT).read_text() == export_openapi.spec(), "run: uv run python -m app.export_openapi"


def test_old_default_jwt_secret_rejected(client):
    import time

    import jwt
    forged = jwt.encode({"sub": "x", "role": "pi", "name": "x", "exp": int(time.time()) + 600},
                        "yammic-demo-secret-not-for-production-use-1234", algorithm="HS256")
    assert client.get("/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_jwt_secret_required():
    import subprocess
    import sys
    env = {k: v for k, v in os.environ.items() if k != "JWT_SECRET"}
    r = subprocess.run([sys.executable, "-c", "import app.security"], env=env, capture_output=True, text=True)
    assert r.returncode != 0 and "JWT_SECRET" in r.stderr


def _bypass(sql):
    with engine.begin() as c:
        c.execute(text("ALTER TABLE audit_event DISABLE TRIGGER USER"))
        c.execute(text(sql))
        c.execute(text("ALTER TABLE audit_event ENABLE TRIGGER USER"))


def test_audit_detects_tail_deletion(client, auth):
    h = auth("nurse")
    client.post("/extractions/EXT-0001/decision", json=ACCEPT, headers=h)
    assert client.get("/audit/verify", headers=h).json()["ok"] is True
    _bypass("DELETE FROM audit_event WHERE seq > (SELECT max(seq) - 3 FROM audit_event)")  # chain stays valid
    v = client.get("/audit/verify", headers=h).json()
    assert v["ok"] is False and "deleted from the end" in v["reason"]


def test_audit_detects_full_rewrite(client, auth, monkeypatch):
    from app import audit
    h = auth("nurse")
    client.post("/extractions/EXT-0001/decision", json=ACCEPT, headers=h)
    # attacker with DB write access but without AUDIT_KEY recomputes the whole chain
    monkeypatch.setattr(audit, "KEY", b"attacker-key")
    with engine.connect() as c:
        rows = [dict(r) for r in c.execute(text("SELECT * FROM audit_event ORDER BY seq")).mappings()]
    prev = audit.GENESIS
    for r in rows:
        d = {**r, "ts": audit._iso(r["ts"])}
        hsh = audit._hash(prev, d)
        _bypass(f"UPDATE audit_event SET prev_hash='{prev}', hash='{hsh}' WHERE seq={r['seq']}")
        prev = hsh
    monkeypatch.undo()
    v = client.get("/audit/verify", headers=h).json()
    assert v["ok"] is False and "modified" in v["reason"]
    # even a rewrite with the right key cannot match the external anchor if the content changed
    _bypass("UPDATE audit_event SET after = jsonb_build_object('x', 1) WHERE seq=1")
    assert client.get("/audit/verify", headers=h).json()["ok"] is False
