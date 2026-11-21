"""Load the synthetic dataset (app/assets/data/*.json) into Postgres.

    uv run python -m app.seed          # load into an empty database
    uv run python -m app.seed --reset  # drop everything, re-migrate, reload
"""
import hashlib
import json
import sys
from pathlib import Path

from sqlalchemy import text

from . import audit as A
from . import workflows as W
from .db import engine, migrate
from .security import hash_password

DATA = Path(__file__).resolve().parents[2] / "app" / "assets" / "data"
USERS = [("nurse", "Research nurse (demo)", "nurse"), ("monitor", "Clinical monitor (demo)", "monitor"),
         ("pi", "Principal investigator (demo)", "pi"), ("ai", "AI extraction service", "service")]
SYSTEM = {"username": "system", "role": "service"}


def J(name):
    return json.loads((DATA / name).read_text())


JSONB = {"meta", "treatments", "terminology", "cdisc", "normalized_value", "proposed_code", "evidence", "seeded_issue",
         "allowed_values", "fields", "criteria"}


def ins(c, table, **row):
    cols = ", ".join(row)
    vals = ", ".join(f"CAST(:{k} AS jsonb)" if k in JSONB else f":{k}" for k in row)
    c.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"),
              {k: json.dumps(v) if k in JSONB else v for k, v in row.items()})


def load(eng=None):
    eng = eng or engine
    study_j, parts_j, docs_j, ex_j, dash_j = (J(f) for f in (
        "study.json", "participants.json", "documents.json", "extractions.json", "dashboard.json"))
    st = study_j["study"]
    with eng.begin() as c:
        meta = {k: [x for x in dash_j[k] if x.get("studyId") == st["id"]] for k in ("milestones", "alerts", "tasks")}
        meta = {k: [{kk: vv for kk, vv in x.items() if kk != "studyId"} for x in v] for k, v in meta.items()}
        ins(c, "study", id=st["id"], short_name=st["shortName"], title=st["title"], phase=st["phase"],
            status=st["status"], target_enrolment=st["targetEnrolment"], meta=meta)
        for s in study_j["sites"]:
            ins(c, "site", id=s["id"], study_id=st["id"], name=s["name"], short_name=s["shortName"], city=s["city"],
                principal_investigator=s["principalInvestigator"], target_enrolment=s["targetEnrolment"])
        form = study_j["ecrf"]["formId"]
        for i, f in enumerate(study_j["ecrf"]["fields"]):
            ins(c, "ecrf_field", id=f["id"], study_id=st["id"], form_id=form, ord=i, label=f["label"],
                section=f["section"], value_type=f["valueType"], required=f["required"], unit=f["unit"],
                terminology=f["terminology"], help=f["help"], min_val=f.get("min"), max_val=f.get("max"),
                allowed_values=f.get("allowedValues"), form_version=1,
                cdisc={k: f[k] for k in ("cdiscDomain", "cdiscVariable", "cdiscVerified")})
        criteria = W.default_criteria()
        for i, cr in enumerate(criteria):
            ins(c, "screening_criterion", study_id=st["id"], id=cr["id"], ord=i, type=cr["type"],
                text=cr["text"], data_needed=cr.get("dataNeeded"), version=1)
        ins(c, "ecrf_form_version", study_id=st["id"], form_id=form, version=1, status="approved",
            fields=study_j["ecrf"]["fields"], criteria=criteria, protocol_text=W.default_synopsis(),
            proposed_by="system", provider="fixture", model="protocol-v1", prompt_version="v1.0",
            approved_by="pi", approved_at="2026-06-01T09:00:00Z", note="Baseline approved eCRF v1")
        for u, name, role in USERS:
            ins(c, "app_user", username=u, display_name=name, role=role, password_hash=hash_password("demo"))
        for p in parts_j["participants"]:
            ins(c, "participant", id=p["id"], study_id=p["studyId"], site_id=p["siteId"], status=p["status"],
                status_detail=p.get("statusDetail"), age=p.get("age"), sex=p.get("sex"), summary=p.get("summary"),
                diagnosis_date=p.get("diagnosisDate"), enrolled_date=p.get("enrolledDate"),
                treatments=p.get("treatments", []))
            for v in p.get("visits", []):
                ins(c, "visit", participant_id=p["id"], name=v["name"], visit_date=v["date"], status=v["status"], note=v["note"])
            for q in p.get("issues", []):
                ins(c, "data_query", participant_id=p["id"], site_id=p["siteId"], field_id=q.get("field"),
                    severity=q["severity"], text=q["message"], opened_by="monitor")
        for d in docs_j["documents"]:
            body = (DATA / "documents" / f"{d['id']}.txt").read_text()
            sha = hashlib.sha256(body.encode()).hexdigest()
            assert sha == d["sha256"], f"sha256 mismatch for {d['id']}"
            ins(c, "source_document", id=d["id"], participant_id=d["participantId"], doc_type=d["type"],
                title=d["title"], language=d["language"], document_date=d["documentDate"], text=body, sha256=sha)
        gen = ex_j["generator"]
        by_doc = {}
        for e in ex_j["extractions"]:
            by_doc.setdefault(e["documentId"], []).append(e)
        for d in docs_j["documents"]:
            es = by_doc.get(d["id"], [])
            run = c.execute(text("""INSERT INTO extraction_run (participant_id, document_id, status, total, done, provider,
              model, prompt_version, created_by, finished_at) VALUES (:p,:d,'completed',:n,:n,'fixture',:m,:pv,'system',now())
              RETURNING id"""), dict(p=d["participantId"], d=d["id"], n=len(es), m=gen["modelId"], pv=gen["promptVersion"])).scalar()
            for e in es:
                ins(c, "extraction", id=e["id"], run_id=run, document_id=e["documentId"], participant_id=e["participantId"],
                    field_id=e["field"], status=e["status"], value=e["value"], normalized_value=e["normalizedValue"],
                    unit=e["unit"], confidence=e["confidence"], proposed_code=e["proposedCode"],
                    abstention_reason=e["abstentionReason"], span_start=e["spanStart"], span_end=e["spanEnd"],
                    evidence=e["evidence"], provider="fixture", model=e["model"], prompt_version=e["promptVersion"],
                    seeded_issue=e["seededIssue"])
                A.record(c, SYSTEM, "extraction.proposed", "extraction", e["id"], participant_id=e["participantId"],
                         after={"field": e["field"], "status": e["status"], "value": e["value"], "confidence": e["confidence"]},
                         source="ai", model=e["model"], prompt_version=e["promptVersion"], actor=f"fixture/{e['model']}")
        c.execute(text("SELECT setval(pg_get_serial_sequence('extraction_run','id'), (SELECT max(id) FROM extraction_run))"))
        c.execute(text("SELECT setval(pg_get_serial_sequence('ecrf_form_version','id'), (SELECT max(id) FROM ecrf_form_version))"))


if __name__ == "__main__":
    if "--reset" in sys.argv:
        with engine.begin() as c:
            c.execute(text("DROP SCHEMA public CASCADE"))
            c.execute(text("CREATE SCHEMA public"))
            c.execute(text("""DO $$ BEGIN
              IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'yamicc_app') THEN
                GRANT USAGE ON SCHEMA public TO yamicc_app;
                ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO yamicc_app;
                ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO yamicc_app;
              END IF;
            END $$"""))
    migrate()
    load()
    print("seeded")
