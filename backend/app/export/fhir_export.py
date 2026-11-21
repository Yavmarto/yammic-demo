"""Participant FHIR bundle: QuestionnaireResponse (verified eCRF) + Provenance (AI vs human) + AuditEvent."""
from datetime import UTC, datetime

from sqlalchemy import text

SYS = {"ICD-O-3": "http://terminology.hl7.org/CodeSystem/icd-o-3", "SNOMED CT": "http://snomed.info/sct",
       "LOINC": "http://loinc.org", "ATC": "http://www.whocc.no/atc", "UCUM": "http://unitsofmeasure.org"}
DOC_SYS = "https://yamicc.example/fhir/NamingSystem/hospital-document-id"
PTYPE = "http://terminology.hl7.org/CodeSystem/provenance-participant-type"
Q_URL = "https://yamicc.example/fhir/Questionnaire/"
TAG = {"system": "https://yamicc.example/fhir/CodeSystem/data-provenance", "code": "SYNTHETIC",
       "display": "Synthetic demo data"}


def _instant(ts) -> str:
    return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"


def _answer(f: dict, v: dict) -> dict:
    t, val = f["value_type"], v["value"]
    try:
        if t == "integer":
            return {"valueInteger": int(val)}
        if t == "number":
            return {"valueDecimal": float(val)}
    except ValueError:
        pass  # fall through: keep the text rather than lose the value
    if t == "date":
        return {"valueDate": val}
    if t == "coded" and v["code"]:
        c = v["code"]
        return {"valueCoding": {"system": SYS.get(c.get("system"), f"urn:yamicc:codesystem:{c.get('system')}"),
                                "code": c["code"], "display": c.get("display") or val}}
    return {"valueString": val}


def _action(a: str) -> str:
    if "export" in a:
        return "R"
    if a.endswith("cleared"):
        return "D"
    return "C" if a.endswith(("created", "set", "ingested", "proposed", "login")) else "U"


def build_bundle(c, pid: str) -> dict | None:
    q = lambda sql, **p: [dict(x) for x in c.execute(text(sql), p).mappings()]
    part = (q("SELECT * FROM participant WHERE id=:i", i=pid) or [None])[0]
    if not part:
        return None
    vals = q("""SELECT v.*, f.label, f.value_type, f.form_id, e.provider, e.model, e.prompt_version, e.confidence,
          e.document_id, (SELECT d.decision FROM review_decision d WHERE d.extraction_id=v.source_extraction_id
                          ORDER BY d.id DESC LIMIT 1) AS decision
        FROM ecrf_value v JOIN ecrf_field f ON f.id=v.field_id LEFT JOIN extraction e ON e.id=v.source_extraction_id
        WHERE v.participant_id=:p ORDER BY f.ord""", p=pid)
    fmap = {x["id"]: x for x in q("SELECT * FROM ecrf_field WHERE study_id=:s", s=part["study_id"])}
    now = _instant(datetime.now(UTC))
    qr_id, form = f"qr-{pid}", (vals[0]["form_id"] if vals else "ECRF")
    qr = {"resourceType": "QuestionnaireResponse", "id": qr_id, "meta": {"tag": [TAG]},
          "questionnaire": Q_URL + form, "status": "completed", "subject": {"reference": f"Patient/{pid}"},
          "authored": now,
          "item": [{"linkId": v["field_id"], "text": v["label"], "answer": [_answer(fmap[v["field_id"]], v)]}
                   for v in vals]}
    agents, seen = [], set()
    for v in vals:
        if v["source_extraction_id"]:
            key = ("ai", v["provider"], v["model"], v["prompt_version"])
            if key not in seen:
                seen.add(key)
                agents.append({"type": {"coding": [{"system": PTYPE, "code": "author", "display": "Author"}]},
                               "role": [{"text": "AI extraction proposal"}],
                               "who": {"display": f"AI {v['provider']}/{v['model']} (prompt {v['prompt_version']})"}})
        key = ("human", v["verified_by"])
        if key not in seen:
            seen.add(key)
            agents.append({"type": {"coding": [{"system": PTYPE, "code": "verifier", "display": "Verifier"}]},
                           "role": [{"text": "human review of AI proposal"}],
                           "who": {"display": v["verified_by"]}})
    docs = sorted({v["document_id"] for v in vals if v["document_id"]})
    prov = {"resourceType": "Provenance", "id": f"prov-{pid}", "meta": {"tag": [TAG]},
            "target": [{"reference": f"QuestionnaireResponse/{qr_id}"}], "recorded": now,
            "agent": agents or [{"who": {"display": "unknown"}}],
            "entity": [{"role": "source", "what": {"identifier": {"system": DOC_SYS, "value": d}}} for d in docs]}
    events = q("""SELECT * FROM audit_event WHERE participant_id=:p AND action <> 'extraction.proposed'
                  ORDER BY seq DESC LIMIT 200""", p=pid)
    aes = []
    for e in reversed(events):
        agent = [{"who": {"display": e["actor"]}, "requestor": True, "role": [{"text": e["role"]}]}]
        if e["source"] == "ai":
            agent.append({"who": {"display": f"AI {e['model']}"}, "requestor": False})
        aes.append({"resourceType": "AuditEvent", "id": f"ae-{pid}-{e['seq']}", "meta": {"tag": [TAG]},
                    "type": {"system": "http://terminology.hl7.org/CodeSystem/audit-event-type", "code": "rest",
                             "display": "RESTful Operation"},
                    "subtype": [{"system": "https://yamicc.example/fhir/CodeSystem/audit-action", "code": e["action"]}],
                    "action": _action(e["action"]), "recorded": _instant(e["ts"]), "outcome": "0",
                    "agent": agent, "source": {"observer": {"display": "Yamicc demo platform"}},
                    "entity": [{"what": {"identifier": {"system": "https://yamicc.example/fhir/NamingSystem/yamicc-entity",
                                                         "value": f"{e['entity_type']}/{e['entity_id']}"}},
                                "detail": [{"type": "audit-hash", "valueString": e["hash"]}]}]})
    res = [qr, prov, *aes]
    return {"resourceType": "Bundle", "id": f"export-{pid}", "type": "collection", "timestamp": now,
            "entry": [{"fullUrl": f"{r['resourceType']}/{r['id']}", "resource": r} for r in res]}


def to_transaction(bundle: dict) -> dict:
    return {**bundle, "type": "transaction", "entry": [
        {"resource": e["resource"], "request": {"method": "PUT", "url": f"{e['resource']['resourceType']}/{e['resource']['id']}"}}
        for e in bundle["entry"]]}
