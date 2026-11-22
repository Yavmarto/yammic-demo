"""v4 backend tests: multi-site sync, screening workflow, data-quality rules + queries/SDV, timeline, form versions."""
import json
from pathlib import Path

from sqlalchemy import text

from app.db import engine
from app.ingest import fhir, pseudo
from app.ingest import routes as ingest_routes

SEED = Path(__file__).resolve().parents[2] / "fhir-seed"
STUDY = "GBM-NL-2026-01"


def _bundle_resources(subpath: str) -> list[dict]:
    out = []
    for f in sorted((SEED / subpath).glob("patient-*.json")):
        out += [e["resource"] for e in json.loads(f.read_text())["entry"]]
    return out


def test_multi_site_sync_and_site_comparison(client, auth, monkeypatch):
    nurse, pi = auth("nurse"), auth("pi")
    h1_src = fhir.BundleSource(_bundle_resources("arrivals"), stamp="2026-11-21T11:00:00.000+00:00")
    h2_src = fhir.BundleSource(_bundle_resources("hospital2/baseline"), stamp="2026-11-21T11:30:00.000+00:00")

    monkeypatch.setattr(ingest_routes, "get_sources", lambda: [
        {"id": "hospital-1", "name": "Hospital 1", "url": "http://localhost:8091/fhir", "siteId": "SITE-01", "client": h1_src},
        {"id": "hospital-2", "name": "Hospital 2", "url": "http://localhost:8092/fhir", "siteId": "SITE-02", "client": h2_src},
    ])

    integ = client.get("/integrations", headers=nurse).json()
    assert {i["id"] for i in integ} == {"hospital-1", "hospital-2"}
    assert client.post("/integrations/fhir/fhir/sync", headers=nurse).status_code == 404

    # Sync hospital-2 specifically
    r2 = client.post("/integrations/fhir/hospital-2/sync", headers=nurse)
    assert r2.status_code == 200
    assert r2.json()["sourceId"] == "hospital-2"
    assert r2.json()["counts"]["participants"]["created"] == 5

    # Sync all sources (hospital-1 gets synced now, hospital-2 is incremental/unchanged)
    r_all = client.post("/integrations/fhir/sync", headers=nurse)
    assert r_all.status_code == 200
    runs = client.get("/integrations/fhir/runs", headers=nurse).json()
    assert {r["sourceId"] for r in runs} >= {"hospital-1", "hospital-2"}

    # Per-site pseudonymisation uses distinct HMAC keys per site
    assert pseudo.pseudonym("MRN-99999", "SITE-01") != pseudo.pseudonym("MRN-99999", "SITE-02")

    # Dashboard KPIs per site + site comparison
    dash_all = client.get(f"/studies/{STUDY}/dashboard", headers=pi).json()
    assert len(dash_all["siteComparison"]) == 3
    site2 = next(s for s in dash_all["sites"] if s["id"] == "SITE-02")
    assert site2["enrolled"] >= 8  # 3 baseline + 5 synced from hospital-2
    assert site2["kpis"]["enrolled"] == site2["enrolled"]

    dash_s2 = client.get(f"/studies/{STUDY}/dashboard?siteId=SITE-02", headers=pi).json()
    assert dash_s2["siteId"] == "SITE-02"
    assert dash_s2["kpis"]["enrolled"] == site2["enrolled"]
    assert dash_s2["kpis"]["target"] == site2["targetEnrolment"]

    cmp_list = client.get(f"/studies/{STUDY}/sites/compare?ids=SITE-01,SITE-02", headers=pi).json()
    assert [s["id"] for s in cmp_list] == ["SITE-01", "SITE-02"]
    assert client.get("/audit/verify", headers=pi).json()["ok"] is True


def test_screening_workflow_and_role_checks(client, auth):
    nurse, monitor, pi = auth("nurse"), auth("monitor"), auth("pi")

    # Run AI screening check on GBM-NL-001 (rules provider for deterministic unit test)
    scr = client.post("/participants/GBM-NL-001/screening/check?provider=rules", headers=nurse)
    assert scr.status_code == 200
    body = scr.json()
    assert body["participantId"] == "GBM-NL-001"
    assert body["totalCount"] == 13
    assert body["metCount"] >= 4

    # Monitor cannot confirm criteria or sign off
    assert client.post("/participants/GBM-NL-001/screening/criteria/INC-01/confirm",
                       json={"status": "met"}, headers=monitor).status_code == 403
    assert client.post("/participants/GBM-NL-001/screening/sign-off",
                       json={"outcome": "eligible"}, headers=monitor).status_code == 403

    # Coordinator (nurse) confirms criteria and signs off -> status becomes 'eligible'
    c_res = client.post("/participants/GBM-NL-001/screening/criteria/INC-01/confirm",
                        json={"status": "met", "note": "Verified birth year in clinic letter"}, headers=nurse)
    assert c_res.status_code == 200
    inc01 = next(c for c in c_res.json()["criteria"] if c["criterionId"] == "INC-01")
    assert inc01["coordinatorStatus"] == "met" and inc01["confirmedBy"] == "nurse"

    blocked = client.post("/participants/GBM-NL-001/screening/sign-off", json={"outcome": "eligible"}, headers=nurse)
    assert blocked.status_code == 422 and "unknown" in blocked.json()["detail"]
    for crit in c_res.json()["criteria"]:
        if crit["coordinatorStatus"] is None:
            resolved = client.post(f"/participants/GBM-NL-001/screening/criteria/{crit['criterionId']}/confirm",
                                   json={"status": "met", "note": "Checked against source"}, headers=nurse)
            assert resolved.status_code == 200

    so_res = client.post("/participants/GBM-NL-001/screening/sign-off",
                         json={"outcome": "eligible"}, headers=nurse)
    assert so_res.status_code == 200, so_res.text
    assert so_res.json()["status"] == "eligible"
    assert so_res.json()["coordinatorSignedBy"] == "nurse"

    # Coordinator records consent -> status becomes 'consented'
    con_res = client.post("/participants/GBM-NL-001/screening/consent",
                          json={"consentedDate": "2026-11-21"}, headers=nurse)
    assert con_res.status_code == 200
    assert con_res.json()["status"] == "consented"

    # Nurse/monitor cannot enrol; only PI can enrol -> status becomes 'enrolled'
    assert client.post("/participants/GBM-NL-001/screening/enrol", json={}, headers=nurse).status_code == 403
    assert client.post("/participants/GBM-NL-001/screening/enrol", json={}, headers=monitor).status_code == 403
    enr_res = client.post("/participants/GBM-NL-001/screening/enrol",
                          json={"enrolledDate": "2026-11-21"}, headers=pi)
    assert enr_res.status_code == 200
    assert enr_res.json()["status"] == "enrolled"
    assert enr_res.json()["enrolledBy"] == "pi"

    # Screen-fail flow on GBM-NL-004 requires reason
    assert client.post("/participants/GBM-NL-004/screening/screen-fail",
                       json={"reason": "   "}, headers=nurse).status_code == 422
    sf_res = client.post("/participants/GBM-NL-004/screening/screen-fail",
                         json={"reason": "IDH-mutant on central review"}, headers=nurse)
    assert sf_res.status_code == 200
    assert sf_res.json()["status"] == "screen_fail"
    assert sf_res.json()["screenFailReason"] == "IDH-mutant on central review"
    assert client.get("/audit/verify", headers=pi).json()["ok"] is True


def test_data_quality_rules_auto_queries_lifecycle_and_sdv(client, auth):
    nurse, monitor, pi = auth("nurse"), auth("monitor"), auth("pi")

    # 1. At least 5 rules registered
    rules = client.get("/data-quality/rules", headers=monitor).json()
    assert len(rules) >= 5
    assert {r["id"] for r in rules} >= {"DQ-01", "DQ-02", "DQ-03", "DQ-04", "DQ-05"}

    # 2. Correcting KPS to an out-of-range value (120) or < 60 (50) triggers DQ-04 / DQ-05 auto-queries
    dec = client.post("/extractions/EXT-0011/decision",
                      json={"decision": "correct", "correctedValue": "120", "reason": "test range"}, headers=nurse)
    assert dec.status_code == 200
    qs = client.get("/queries", params={"participant_id": "GBM-NL-001", "field_id": "KPS"}, headers=monitor).json()
    assert any(q["ruleId"] == "DQ-04" and q["status"] == "open" for q in qs)
    dq_q = next(q for q in qs if q["ruleId"] == "DQ-04")

    # 3. Query lifecycle: open -> answered (nurse) -> closed (monitor)
    assert client.post(f"/queries/{dq_q['id']}/answer", json={"answer": "Fixed to 80"}, headers=monitor).status_code == 403
    ans = client.post(f"/queries/{dq_q['id']}/answer", json={"answer": "Typo corrected to 80%"}, headers=nurse)
    assert ans.status_code == 200
    assert ans.json()["status"] == "answered"
    assert ans.json()["answeredBy"] == "nurse"
    assert ans.json()["answer"] == "Typo corrected to 80%"

    cls = client.post(f"/queries/{dq_q['id']}/close", headers=monitor)
    assert cls.status_code == 200
    assert cls.json()["status"] == "closed"
    assert cls.json()["closedBy"] == "monitor"

    # 4. Per-field SDV tick and untick (monitor only)
    sdv1 = client.post("/participants/GBM-NL-001/ecrf/KPS/sdv", headers=monitor)
    assert sdv1.status_code == 200 and sdv1.json()["sdvBy"] == "monitor"
    sdv0 = client.post("/participants/GBM-NL-001/ecrf/KPS/sdv", json={"sdv": False}, headers=monitor)
    assert sdv0.status_code == 200 and sdv0.json()["sdvBy"] is None

    # 5. Manual data-quality run on GBM-NL-001 checks all 5 rules
    dq_run = client.post("/participants/GBM-NL-001/data-quality/run", headers=monitor)
    assert dq_run.status_code == 200
    assert dq_run.json()["checked"] >= 5
    assert client.get("/audit/verify", headers=pi).json()["ok"] is True


def test_participant_timeline_events_and_links(client, auth):
    nurse = auth("nurse")
    res = client.get("/participants/GBM-NL-002/timeline", headers=nurse)
    assert res.status_code == 200
    tl = res.json()
    assert tl["participantId"] == "GBM-NL-002"
    events = tl["events"]
    assert len(events) >= 10
    # Ordered chronologically
    dates = [e["date"] for e in events]
    assert dates == sorted(dates)
    categories = {e["category"] for e in events}
    assert {"surgery", "radiotherapy", "chemotherapy", "scan", "visit"} <= categories
    # Every event is linked to a source document or FHIR resource
    assert all(e["documentId"] or e["resourceId"] for e in events)
    surg = next(e for e in events if e["category"] == "surgery")
    assert surg["documentId"] == "DOC-002-SURG"


def test_form_versions_propose_approve_and_value_version_preservation(client, auth):
    nurse, pi = auth("nurse"), auth("pi")

    # Capture a value under form version 1
    r1 = client.post("/extractions/EXT-0001/decision", json={"decision": "accept"}, headers=nurse)
    assert r1.status_code == 200
    assert r1.json()["ecrfValue"]["formVersion"] == 1

    # Propose a new form version (v2) with an extra field
    prop = client.post(f"/studies/{STUDY}/forms/propose", json={
        "formId": "ECRF-GBM-BASELINE",
        "note": "Add RANO target lesion diameter",
        "fields": [
            {"id": "SUBJID", "label": "Subject identifier", "section": "identification", "valueType": "string", "required": True},
            {"id": "KPS", "label": "Karnofsky Performance Status", "section": "clinical_status", "valueType": "integer", "required": True, "unit": "%", "min": 0, "max": 100},
            {"id": "RANOMM", "label": "RANO target lesion diameter", "section": "outcome", "valueType": "number", "required": False, "unit": "mm"},
        ],
    }, headers=nurse)
    assert prop.status_code == 201
    v2 = prop.json()
    assert v2["version"] == 2 and v2["status"] == "proposed"

    # Nurse cannot approve; only PI can approve
    assert client.post(f"/studies/{STUDY}/forms/2/approve", json={}, headers=nurse).status_code == 403
    app_res = client.post(f"/studies/{STUDY}/forms/2/approve", json={"note": "Approved by PI"}, headers=pi)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved" and app_res.json()["approvedBy"] == "pi"

    # Capture a new value under form version 2
    r2 = client.post("/extractions/EXT-0011/decision", json={"decision": "accept"}, headers=nurse)
    assert r2.status_code == 200
    assert r2.json()["ecrfValue"]["formVersion"] == 2

    # Verify SUBJID kept formVersion=1 while KPS has formVersion=2, and new field RANOMM is in the eCRF
    ecrf = client.get("/participants/GBM-NL-001/ecrf", headers=nurse).json()
    assert ecrf["formVersion"] == 2
    by_id = {f["id"]: f for f in ecrf["fields"]}
    assert "RANOMM" in by_id
    assert by_id["SUBJID"]["value"]["formVersion"] == 1
    assert by_id["KPS"]["value"]["formVersion"] == 2
    assert client.get("/audit/verify", headers=pi).json()["ok"] is True


def _sign_off_eligible(client, nurse, pid):
    for crit in client.get(f"/participants/{pid}/screening", headers=nurse).json()["criteria"]:
        if crit["coordinatorStatus"] is None:
            r = client.post(f"/participants/{pid}/screening/criteria/{crit['criterionId']}/confirm",
                            json={"status": "met", "note": "Checked against source"}, headers=nurse)
            assert r.status_code == 200
    assert client.post(f"/participants/{pid}/screening/sign-off", json={"outcome": "eligible"}, headers=nurse).status_code == 200


def _consent_and_enrol_dates(pid):
    with engine.connect() as c:
        row = c.execute(text("SELECT consented_date, enrolled_date FROM participant WHERE id=:i"), {"i": pid}).one()
    return row[0], row[1]


def test_enrolment_requires_recorded_consent_and_keeps_consent_date(client, auth):
    nurse, pi = auth("nurse"), auth("pi")
    _sign_off_eligible(client, nurse, "GBM-NL-001")

    early = client.post("/participants/GBM-NL-001/screening/enrol", json={"enrolledDate": "2026-11-21"}, headers=pi)
    assert early.status_code == 409 and "consent" in early.json()["detail"]
    assert client.get("/participants/GBM-NL-001/screening", headers=nurse).json()["status"] == "eligible"
    assert _consent_and_enrol_dates("GBM-NL-001")[0] is None

    client.post("/participants/GBM-NL-001/screening/consent", json={"consentedDate": "2026-11-20"}, headers=nurse)
    assert client.post("/participants/GBM-NL-001/screening/enrol", json={"enrolledDate": "2026-11-21"}, headers=pi).status_code == 200
    consented, enrolled = _consent_and_enrol_dates("GBM-NL-001")
    assert str(consented) == "2026-11-20" and str(enrolled) == "2026-11-21"


def test_get_screening_performs_no_writes(client, auth):
    nurse = auth("nurse")
    with engine.begin() as c:
        c.execute(text("DELETE FROM screening_check WHERE participant_id='GBM-NL-004'"))

    def _write_counts():
        with engine.connect() as c:
            return (c.execute(text("SELECT count(*) FROM audit_event")).scalar(),
                    c.execute(text("SELECT count(*) FROM screening_check WHERE participant_id='GBM-NL-004'")).scalar())

    before = _write_counts()
    assert client.get("/screening", headers=nurse).status_code == 200
    assert client.get("/participants/GBM-NL-004/screening", headers=nurse).status_code == 200
    assert _write_counts() == before


def test_screening_falls_back_to_rules_when_ai_checker_is_down(client, auth, monkeypatch):
    from app.ai import screening as ai_screening

    def _ollama_down(*args, **kwargs):
        raise RuntimeError("ollama is down (test)")

    monkeypatch.setattr(ai_screening, "check_participant", _ollama_down)
    r = client.post("/participants/GBM-NL-001/screening/check?provider=ollama", headers=auth("nurse"))
    assert r.status_code == 200 and r.json()["totalCount"] == 13


def test_humans_cannot_write_ai_screening_results(client, auth):
    body = [{"criterionId": "INC-01", "status": "met", "confidence": 0.99}]
    for who in ("nurse", "pi", "monitor"):
        assert client.post("/participants/GBM-NL-001/screening/checks", json=body, headers=auth(who)).status_code == 403


def test_query_field_must_exist_in_participant_study(client, auth):
    r = client.post("/queries", json={"participantId": "GBM-NL-001", "text": "Check", "fieldId": "NOT_A_FIELD"},
                    headers=auth("monitor"))
    assert r.status_code == 422
