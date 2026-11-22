"""W5: FHIR ingestion, pseudonymisation, ODM 1.3.2 + FHIR exports.

Offline tests read the committed fhir-seed bundles through `BundleSource`.
Tests marked `live` need the HAPI server from `make up` and skip when it is down.
"""
import json
import re
import socket
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from lxml import etree
from sqlalchemy import text

from app.db import engine
from app.export import fhir_export
from app.ingest import fhir
from app.ingest import routes as ingest_routes
from test_ai_service import ApiAdapter

SEED = Path(__file__).resolve().parents[2] / "fhir-seed"
XSD = Path(__file__).resolve().parents[1] / "app" / "export" / "xsd" / "ODM1-3-2.xsd"
MRNS = {f"MRN-01-001{n:02d}" for n in range(1, 12)} | {f"MRN-01-0010{n}" for n in range(1, 10)}


def _resources(set_name):
    out = []
    for f in sorted((SEED / set_name).glob("patient-*.json")):
        out += [e["resource"] for e in json.load(open(f))["entry"]]
    return out


def _live():
    target = urlsplit(fhir.BASE)
    port = target.port or (443 if target.scheme == "https" else 80)
    try:
        socket.create_connection((target.hostname, port), timeout=1).close()
        return True
    except OSError:
        return False


live = pytest.mark.skipif(not _live(), reason=f"HAPI FHIR not reachable at {fhir.BASE}")


@pytest.fixture
def two_phase(monkeypatch):
    """baseline first, arrivals 'arrive' later (later meta.lastUpdated)."""
    base = fhir.BundleSource(_resources("baseline"), stamp="2026-11-21T10:00:00.000+00:00")
    arr = fhir.BundleSource(_resources("baseline") + _resources("arrivals"), stamp="2026-11-21T10:00:00.000+00:00")
    for r in arr.res:  # arrivals get a later stamp
        if "-009" in r["id"] or "-010" in r["id"] or "-011" in r["id"] or r["resourceType"] in ("Patient",) and r["id"][-3:] in ("009", "010", "011"):
            r["meta"]["lastUpdated"] = "2026-11-21T11:00:00.000+00:00"
    state = {"src": base}
    monkeypatch.setattr(ingest_routes, "get_source", lambda: state["src"])
    state["arrive"] = lambda: state.update(src=arr)
    return state


def _sync(client, auth, full=False):
    res = client.post(f"/integrations/fhir/sync?full={str(full).lower()}", headers=auth("nurse"))
    assert res.status_code == 200, res.text
    return res.json()


def _all_text(c):
    """Every stored string in every table a sync can write."""
    tables = ["participant", "source_document", "fhir_fact", "pseudonym_map", "audit_event", "fhir_sync_run",
              "extraction_run"]
    return "\n".join(c.execute(text(f"SELECT t::text FROM {t} t")).scalars().all()[i] for t in tables
                     for i in range(c.execute(text(f"SELECT count(*) FROM {t}")).scalar()))


def test_sync_creates_arrivals_and_queues_extraction(client, auth, two_phase):
    first = _sync(client, auth)
    assert first["status"] == "completed" and first["mode"] == "full"
    assert first["counts"]["documents"] == {"created": 0, "existing": 12}  # baseline docs are already bundled
    two_phase["arrive"]()
    run = _sync(client, auth)
    assert run["mode"] == "incremental" and run["since"] == first["cursor"]
    assert run["counts"]["participants"]["created"] == 3
    assert run["counts"]["documents"]["created"] == 7
    assert run["counts"]["extractionRuns"]["queued"] == 7
    assert run["counts"]["Patient"]["fetched"] == 3  # incremental: only what changed
    with engine.connect() as c:
        queued = c.execute(text("SELECT count(*) FROM extraction_run WHERE status='queued' AND created_by='nurse'")).scalar()
        status = dict(c.execute(text("SELECT id, status FROM participant WHERE id LIKE 'GBM-NL-0%' AND id >= 'GBM-NL-009'")).all())
    assert queued == 7
    assert status == {"GBM-NL-009": "screening", "GBM-NL-010": "screening", "GBM-NL-011": "screening"}


def test_sync_is_idempotent(client, auth, two_phase):
    two_phase["arrive"]()
    _sync(client, auth, full=True)
    with engine.connect() as c:
        before = {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                  for t in ("participant", "source_document", "fhir_fact", "extraction_run", "pseudonym_map")}
    again = _sync(client, auth, full=True)
    with engine.connect() as c:
        after = {t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in before}
    assert before == after
    assert again["counts"]["participants"]["created"] == 0 and again["counts"]["documents"]["created"] == 0
    assert again["counts"]["extractionRuns"]["queued"] == 0
    assert all(v["created"] == 0 and v["updated"] == 0 for k, v in again["counts"].items()
               if k in fhir.TYPES and v.get("fetched"))
    third = _sync(client, auth)  # incremental with nothing new
    assert third["counts"]["Observation"]["fetched"] == 0


def test_pseudonymisation_leaks_no_mrn_or_name(client, auth, two_phase):
    two_phase["arrive"]()
    # plant the identifiers inside a report body to prove the text is scrubbed too
    import base64
    for r in two_phase["src"].res:
        if r["id"] == "DOC-009-PATH":
            body = "Patient India Proefpersoon (MRN-01-00109) onderzocht. Dossier MRN 99887766. KPS 90.\n"
            r["content"][0]["attachment"]["data"] = base64.b64encode(body.encode()).decode()
    _sync(client, auth, full=True)
    with engine.connect() as c:
        blob = _all_text(c)
        doc = c.execute(text("SELECT text FROM source_document WHERE id='DOC-009-PATH'")).scalar()
        mapped = c.execute(text("SELECT pseudonym, mrn_hmac FROM pseudonym_map WHERE participant_id='GBM-NL-009'")).first()
    assert not (MRNS & set(re.findall(r"MRN-\d\d-\d{5}", blob)))
    assert "Proefpersoon" not in blob and "99887766" not in blob and "India" not in blob
    assert mapped.pseudonym in doc and "KPS 90" in doc
    assert re.fullmatch(r"PSN-[0-9A-F]{12}", mapped.pseudonym) and len(mapped.mrn_hmac) == 64
    # and no API response carries them
    for path in ("/integrations", "/integrations/fhir/runs", "/participants/GBM-NL-009",
                 "/participants/GBM-NL-009/documents", "/audit?limit=500"):
        body = client.get(path, headers=auth("nurse")).text
        assert "Proefpersoon" not in body and not re.search(r"MRN-\d\d-\d{5}", body), path
        assert "mrn_hmac" not in body and "mrnHmac" not in body


def test_sync_failure_is_recorded_not_raised(client, auth, monkeypatch):
    class Down(fhir.BundleSource):
        def metadata(self):
            raise fhir.FhirError("connection refused")
    monkeypatch.setattr(ingest_routes, "get_source", lambda: Down([]))
    run = _sync(client, auth)
    assert run["status"] == "failed" and "connection refused" in run["errors"][0]["error"]
    assert client.get("/integrations", headers=auth("nurse")).json()[0]["status"] == "unreachable"
    assert client.get("/integrations/fhir/runs", headers=auth("nurse")).json()[0]["id"] == run["id"]


def test_sync_end_to_end_with_ai_service(client, auth, two_phase):
    """Arrival sync queues runs; the AI service (rules provider) turns them into proposals."""
    from app.ai.service import process_queued
    two_phase["arrive"]()
    _sync(client, auth)
    out = process_queued(ApiAdapter(client, auth("ai")), provider="rules", once=True)
    done = [o for o in out if o["status"] == "completed"]
    assert len(done) == 7 and sum(o["proposals"] for o in done) > 20
    ex = client.get("/participants/GBM-NL-009/extractions", headers=auth("nurse")).json()
    assert {e["field"] for e in ex if e["status"] == "proposed"} >= {"KPS", "MGMTPROM"}
    assert all(e["provider"] == "rules" for e in ex)


def test_roles_and_audit(client, auth, two_phase):
    assert client.post("/integrations/fhir/sync", headers=auth("monitor")).status_code == 403
    _sync(client, auth)
    two_phase["arrive"]()
    _sync(client, auth)
    acts = {a["action"] for a in client.get("/audit?limit=500", headers=auth("pi")).json()["items"]}
    assert {"fhir.sync", "fhir.participant_created", "fhir.document_ingested", "run.created"} <= acts
    assert client.get("/audit/verify", headers=auth("pi")).json()["ok"] is True


# ---------- exports ----------
def _verify_some(client, auth, pid="GBM-NL-001", n=4):
    ex = [e for e in client.get(f"/participants/{pid}/extractions", headers=auth("nurse")).json()
          if e["status"] == "proposed"][:n]
    assert len(ex) == n
    for i, e in enumerate(ex):
        body = {"decision": "accept"} if i else {"decision": "correct", "correctedValue": e["value"] + " ",
                                                 "reason": "typo"}
        assert client.post(f"/extractions/{e['id']}/decision", json=body, headers=auth("nurse")).status_code == 200
    client.post(f"/participants/{pid}/ecrf/{ex[1]['field']}/sdv", headers=auth("monitor"))
    return ex


def test_odm_validates_against_xsd(client, auth):
    _verify_some(client, auth)
    _verify_some(client, auth, "GBM-NL-002", 3)
    res = client.get("/studies/GBM-NL-2026-01/export/odm", headers=auth("monitor"))
    assert res.status_code == 200 and res.headers["content-type"].startswith("application/xml")
    schema = etree.XMLSchema(etree.parse(str(XSD)))
    doc = etree.fromstring(res.content)
    schema.assertValid(doc)
    ns = {"o": "http://www.cdisc.org/ns/odm/v1.3"}
    assert doc.get("ODMVersion") == "1.3.2" and doc.get("FileType") == "Snapshot"
    assert len(doc.xpath("//o:SubjectData", namespaces=ns)) == 2
    items = doc.xpath("//o:ItemData", namespaces=ns)
    assert len(items) == 7
    assert all(i.xpath("o:AuditRecord/o:UserRef", namespaces=ns) for i in items)
    assert any("Proposed by AI" in (a.text or "") for a in doc.xpath("//o:Annotation/o:Comment", namespaces=ns))
    assert any("Source data verified" in (a.text or "") for a in doc.xpath("//o:Annotation/o:Comment", namespaces=ns))
    assert doc.xpath("//o:ReasonForChange", namespaces=ns)


def test_odm_is_xsd_invalid_when_tampered(client, auth):
    """Guard: the validator is really checking (a broken file must fail)."""
    _verify_some(client, auth)
    xml = client.get("/studies/GBM-NL-2026-01/export/odm", headers=auth("pi")).content
    bad = xml.replace(b'ODMVersion="1.3.2"', b'ODMVersion="9.9"').replace(b"<ItemGroupData", b"<ItemGroupDataX", 1)
    schema = etree.XMLSchema(etree.parse(str(XSD)))
    with pytest.raises(etree.XMLSyntaxError):
        schema.assertValid(etree.fromstring(bad.replace(b"</ItemGroupDataX>", b"</ItemGroupDataX>")))


def test_odm_unknown_study_and_audited(client, auth):
    assert client.get("/studies/NOPE/export/odm", headers=auth("pi")).status_code == 404
    assert client.get("/studies/GBM-NL-2026-01/export/odm", headers=auth("nurse")).status_code == 403
    client.get("/studies/GBM-NL-2026-01/export/odm", headers=auth("pi"))
    items = client.get("/audit?action=export.*", headers=auth("pi")).json()["items"]
    assert [i["action"] for i in items] == ["export.odm"]


def test_fhir_bundle_shape(client, auth):
    ex = _verify_some(client, auth)
    b = client.get("/participants/GBM-NL-001/export/fhir", headers=auth("pi")).json()
    kinds = [e["resource"]["resourceType"] for e in b["entry"]]
    assert kinds[:2] == ["QuestionnaireResponse", "Provenance"] and "AuditEvent" in kinds
    qr, prov = b["entry"][0]["resource"], b["entry"][1]["resource"]
    assert len(qr["item"]) == 4 and qr["subject"]["reference"] == "Patient/GBM-NL-001"
    who = [a["who"]["display"] for a in prov["agent"]]
    assert any(w.startswith("AI ") for w in who) and "nurse" in who
    assert {a["type"]["coding"][0]["code"] for a in prov["agent"]} == {"author", "verifier"}
    assert client.get("/participants/NOPE/export/fhir", headers=auth("pi")).status_code == 404
    assert ex  # silence unused


@live
def test_fhir_bundle_validates_on_hapi_and_pushes(client, auth):
    _verify_some(client, auth)
    src = fhir.HttpSource()
    b = client.get("/participants/GBM-NL-001/export/fhir", headers=auth("pi")).json()
    for e in b["entry"]:
        out = src.validate(e["resource"])
        errs = [i for i in out["issue"] if i["severity"] in ("error", "fatal")]
        assert not errs, (e["fullUrl"], errs)
    res = client.post("/participants/GBM-NL-001/export/fhir/push", headers=auth("pi"))
    assert res.status_code == 200, res.text
    assert res.json()["pushed"] >= len(b["entry"])  # +1 AuditEvent: the GET above was audited
    back = fhir._get(f"{fhir.BASE}/QuestionnaireResponse/qr-GBM-NL-001")
    assert len(back["item"]) == 4
    assert client.post("/participants/GBM-NL-003/export/fhir/push", headers=auth("pi")).status_code == 409


@live
def test_live_sync_connection_status(client, auth, monkeypatch):
    monkeypatch.setattr(ingest_routes, "get_source", fhir.HttpSource)
    info = client.get("/integrations", headers=auth("nurse")).json()[0]
    assert info["status"] == "connected" and info["fhirVersion"].startswith("4.")
    run = _sync(client, auth, full=True)
    assert run["status"] in ("completed", "partial") and run["counts"]["Patient"]["fetched"] >= 8
