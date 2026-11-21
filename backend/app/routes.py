import asyncio
from typing import Literal
import json
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text
from sse_starlette.sse import EventSourceResponse

from . import audit as A
from . import schemas as S
from .db import engine
from .security import check_password, current_user, make_token, require

r = APIRouter()
ANY = Depends(current_user)
DISCLAIMER = "Synthetic data — prototype, not for clinical use"
LOW_CONF = 0.6


def _q(sql):  # "(:x IS NULL OR ...)" optional filters need a typed NULL for Postgres
    return text(re.sub(r"\(:(\w+) IS NULL", r"(CAST(:\1 AS text) IS NULL", sql))


def rows(c, sql, **p):
    return [dict(x) for x in c.execute(_q(sql), p).mappings()]


def one(c, sql, **p):
    x = c.execute(_q(sql), p).mappings().first()
    return dict(x) if x else None


def must(x, what):
    if x is None:
        raise HTTPException(404, f"{what} not found")
    return x


# ---------- health / auth ----------
@r.get("/health", response_model=S.Health, tags=["system"])
def health():
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return S.Health(status="ok", database=True)
    except Exception:
        return S.Health(status="degraded", database=False)


@r.post("/auth/login", response_model=S.Token, tags=["auth"])
def login(body: S.LoginIn):
    with engine.begin() as c:
        u = one(c, "SELECT * FROM app_user WHERE username = :u", u=body.username.strip().lower())
        if not u or not check_password(body.password, u["password_hash"]):
            raise HTTPException(401, "Wrong username or password")
        user = {"username": u["username"], "role": u["role"], "name": u["display_name"]}
        A.record(c, user, "auth.login", "user", u["username"])
    return S.Token(access_token=make_token(**user), user=S.User(**user))


@r.get("/me", response_model=S.User, tags=["auth"])
def me(user=ANY):
    return user


# ---------- dashboard ----------
@r.get("/studies/{study_id}/dashboard", response_model=S.Dashboard, tags=["study"])
def dashboard(study_id: str, user=ANY):
    with engine.connect() as c:
        st = must(one(c, "SELECT * FROM study WHERE id = :i", i=study_id), "Study")
        k = one(c, """
          SELECT
           (SELECT count(*) FROM participant WHERE study_id=:s) enrolled,
           (SELECT count(DISTINCT p.id) FROM participant p JOIN source_document d ON d.participant_id=p.id WHERE p.study_id=:s) scope,
           (SELECT count(*) FROM ecrf_field WHERE study_id=:s) fields,
           (SELECT count(*) FROM ecrf_value v JOIN participant p ON p.id=v.participant_id WHERE p.study_id=:s) verified,
           (SELECT count(*) FROM ecrf_value v JOIN participant p ON p.id=v.participant_id WHERE p.study_id=:s AND v.sdv_at IS NOT NULL) sdv,
           (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id WHERE p.study_id=:s) ex_total,
           (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id WHERE p.study_id=:s AND review_state='pending') ex_pending,
           (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id WHERE p.study_id=:s AND review_state='accepted') ex_acc,
           (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id WHERE p.study_id=:s AND review_state='corrected') ex_cor,
           (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id WHERE p.study_id=:s AND review_state='rejected') ex_rej,
           (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id WHERE p.study_id=:s AND review_state='deferred') ex_def,
           (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id WHERE p.study_id=:s AND review_state='pending'
              AND (e.status='abstained' OR e.confidence < :lc)) attention,
           (SELECT count(*) FROM data_query q JOIN site s ON s.id=q.site_id WHERE s.study_id=:s AND q.status='open') queries,
           (SELECT count(*) FROM audit_event) audit
        """, s=study_id, lc=LOW_CONF)
        sites = rows(c, """
          SELECT s.*, (SELECT count(*) FROM participant p WHERE p.site_id=s.id) enrolled,
                 (SELECT count(*) FROM data_query q WHERE q.site_id=s.id AND q.status='open') open_queries
          FROM site s WHERE s.study_id=:s ORDER BY s.id""", s=study_id)
    reviewed = k["ex_acc"] + k["ex_cor"] + k["ex_rej"]
    denom = k["scope"] * k["fields"]
    kp = S.Kpis(
        enrolled=k["enrolled"], target=st["target_enrolment"] or 0,
        participants_in_extraction_scope=k["scope"], ecrf_fields_total=denom,
        ecrf_fields_verified=k["verified"],
        ecrf_completeness=round(k["verified"] / denom, 4) if denom else 0.0,
        extractions_total=k["ex_total"], extractions_pending=k["ex_pending"],
        extractions_reviewed=reviewed, extractions_accepted=k["ex_acc"],
        extractions_corrected=k["ex_cor"], extractions_rejected=k["ex_rej"],
        extractions_deferred=k["ex_def"],
        ai_acceptance_rate=round(k["ex_acc"] / reviewed, 4) if reviewed else None,
        needs_attention=k["attention"], open_queries=k["queries"], sdv_done=k["sdv"],
        sdv_pending=k["verified"] - k["sdv"], audit_events=k["audit"])
    meta = st["meta"] or {}
    return S.Dashboard(
        study_id=st["id"], title=st["short_name"], phase=st["phase"], status=st["status"],
        disclaimer=DISCLAIMER, kpis=kp, sites=[S.Site(**s) for s in sites],
        milestones=meta.get("milestones", []), alerts=meta.get("alerts", []), tasks=meta.get("tasks", []))


# ---------- participants ----------
PSUM = """
SELECT p.id, p.study_id, p.site_id, p.status, p.status_detail, p.age, p.sex, p.enrolled_date,
  p.summary, p.diagnosis_date,
  (SELECT count(*) FROM source_document d WHERE d.participant_id=p.id) document_count,
  (SELECT count(*) FROM extraction e WHERE e.participant_id=p.id AND e.review_state='pending') extractions_pending,
  (SELECT count(*) FROM ecrf_value v WHERE v.participant_id=p.id) ecrf_verified,
  (SELECT count(*) FROM ecrf_field f WHERE f.study_id=p.study_id) ecrf_total,
  (SELECT count(*) FROM data_query q WHERE q.participant_id=p.id AND q.status='open') open_queries
FROM participant p"""


def _pct(x):
    x["ecrf_complete_pct"] = round(100 * x["ecrf_verified"] / x["ecrf_total"]) if x["ecrf_total"] else 0
    return x


@r.get("/participants", response_model=list[S.ParticipantSummary], tags=["participants"])
def participants(site_id: str | None = None, status: str | None = None, user=ANY):
    with engine.connect() as c:
        xs = rows(c, PSUM + " WHERE (:site IS NULL OR p.site_id=:site) AND (:st IS NULL OR p.status=:st) ORDER BY p.id",
                  site=site_id, st=status)
    return [_pct(x) for x in xs]


@r.get("/participants/{pid}", response_model=S.ParticipantDetail, tags=["participants"])
def participant(pid: str, user=ANY):
    with engine.connect() as c:
        x = must(one(c, PSUM + " WHERE p.id=:i", i=pid), "Participant")
        x["treatments"] = one(c, "SELECT treatments FROM participant WHERE id=:i", i=pid)["treatments"]
        x["visits"] = rows(c, "SELECT name, visit_date AS date, status, note FROM visit WHERE participant_id=:i ORDER BY id", i=pid)
        x["document_ids"] = [d["id"] for d in rows(c, "SELECT id FROM source_document WHERE participant_id=:i ORDER BY id", i=pid)]
    return _pct(x)


DOCSUM = """
SELECT d.id, d.participant_id, d.doc_type AS type, d.title, d.language, d.document_date,
  length(d.text) char_length, d.sha256, {text}
  (SELECT count(*) FROM extraction e WHERE e.document_id=d.id) extraction_count,
  (SELECT count(*) FROM extraction e WHERE e.document_id=d.id AND e.review_state='pending') extractions_pending
FROM source_document d"""


@r.get("/participants/{pid}/documents", response_model=list[S.DocumentSummary], tags=["documents"])
def documents(pid: str, user=ANY):
    with engine.connect() as c:
        must(one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid), "Participant")
        return rows(c, DOCSUM.format(text="") + " WHERE d.participant_id=:i ORDER BY d.id", i=pid)


@r.get("/documents/{did}", response_model=S.DocumentDetail, tags=["documents"])
def document(did: str, user=ANY):
    with engine.connect() as c:
        return must(one(c, DOCSUM.format(text="d.text,") + " WHERE d.id=:i", i=did), "Document")


# ---------- extractions & review ----------
EXSEL = """
SELECT e.id, e.run_id, e.document_id, d.doc_type document_type, e.participant_id, e.field_id AS field,
  f.label field_label, e.status, e.value, e.normalized_value, e.unit, e.confidence, e.proposed_code,
  e.abstention_reason, e.span_start, e.span_end, e.evidence, e.provider, e.model, e.prompt_version,
  e.review_state, e.seeded_issue,
  (SELECT to_jsonb(x) FROM (SELECT decision, corrected_value, reason, username, role, created_at
     FROM review_decision rd WHERE rd.extraction_id=e.id ORDER BY rd.id DESC LIMIT 1) x) last_decision
FROM extraction e JOIN source_document d ON d.id=e.document_id JOIN ecrf_field f ON f.id=e.field_id"""


def _ex(x):
    return x  # last_decision keys are snake_case; the model accepts them by name


@r.get("/participants/{pid}/extractions", response_model=list[S.Extraction], tags=["extractions"])
def extractions(pid: str, document_id: str | None = None, review_state: S.ReviewState | None = None,
                field: str | None = None, user=ANY):
    with engine.connect() as c:
        must(one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid), "Participant")
        xs = rows(c, EXSEL + """ WHERE e.participant_id=:p AND (:d IS NULL OR e.document_id=:d)
          AND (:rs IS NULL OR e.review_state=:rs) AND (:f IS NULL OR e.field_id=:f)
          ORDER BY e.document_id, e.created_at, e.id""", p=pid, d=document_id, rs=review_state, f=field)
    return [_ex(x) for x in xs]


@r.post("/extractions/{eid}/decision", response_model=S.DecisionResult, tags=["extractions"])
def decide(eid: str, body: S.DecisionIn, user=Depends(require("nurse", "pi"))):
    with engine.begin() as c:
        e = must(one(c, "SELECT * FROM extraction WHERE id=:i FOR UPDATE", i=eid), "Extraction")
        corrected = (body.corrected_value or "").strip()
        reason = (body.reason or "").strip() or None
        if body.decision == "correct" and not corrected:
            raise HTTPException(422, "correctedValue is required for 'correct'")
        if body.decision == "reject" and not reason:
            raise HTTPException(422, "reason is required for 'reject'")
        if body.decision == "accept" and e["status"] == "abstained":
            raise HTTPException(422, "An abstained extraction has no value to accept; use correct, reject or defer")
        pid, fid = e["participant_id"], e["field_id"]
        prev_val = one(c, "SELECT value, code, source_extraction_id FROM ecrf_value WHERE participant_id=:p AND field_id=:f", p=pid, f=fid)
        state = {"accept": "accepted", "correct": "corrected", "reject": "rejected", "defer": "deferred"}[body.decision]
        c.execute(text("""INSERT INTO review_decision (extraction_id, decision, corrected_value, reason, username, role)
          VALUES (:e,:d,:cv,:r,:u,:ro)"""), dict(e=eid, d=body.decision, cv=corrected or None, r=reason,
                                                  u=user["username"], ro=user["role"]))
        c.execute(text("UPDATE extraction SET review_state=:s WHERE id=:i"), dict(s=state, i=eid))
        A.record(c, user, "extraction.decision", "extraction", eid, participant_id=pid,
                 before={"reviewState": e["review_state"]},
                 after={"reviewState": state, "decision": body.decision, "field": fid,
                        "proposedValue": e["value"], "correctedValue": corrected or None, "reason": reason},
                 source="human", model=e["model"], prompt_version=e["prompt_version"])
        new_val = None
        if body.decision in ("accept", "correct"):
            v = e["value"] if body.decision == "accept" else corrected
            code = json.dumps(e["proposed_code"]) if body.decision == "accept" and e["proposed_code"] else None
            c.execute(text("""INSERT INTO ecrf_value (participant_id, field_id, value, code, source_extraction_id, verified_by)
              VALUES (:p,:f,:v,CAST(:c AS jsonb),:e,:u)
              ON CONFLICT (participant_id, field_id) DO UPDATE SET value=:v, code=CAST(:c AS jsonb),
                source_extraction_id=:e, verified_by=:u, verified_at=now(), sdv_by=NULL, sdv_at=NULL"""),
                      dict(p=pid, f=fid, v=v, c=code, e=eid, u=user["username"]))
            new_val = {"value": v, "code": e["proposed_code"] if code else None}
        elif prev_val and prev_val["source_extraction_id"] == eid:
            c.execute(text("DELETE FROM ecrf_value WHERE participant_id=:p AND field_id=:f"), dict(p=pid, f=fid))
        old = {"value": prev_val["value"], "code": prev_val["code"]} if prev_val else None
        if old != new_val:
            A.record(c, user, "ecrf.value_set" if new_val else "ecrf.value_cleared", "ecrf_value", f"{pid}/{fid}",
                     participant_id=pid, before=old, after=new_val, source="human",
                     model=e["model"], prompt_version=e["prompt_version"])
        ex = _ex(one(c, EXSEL + " WHERE e.id=:i", i=eid))
        val = one(c, ECRFVAL + " WHERE participant_id=:p AND field_id=:f", p=pid, f=fid)
    return S.DecisionResult(extraction=ex, ecrf_value=val)


# ---------- eCRF ----------
ECRFVAL = """SELECT field_id AS field, value, code, source_extraction_id, verified_by, verified_at, sdv_by, sdv_at FROM ecrf_value"""


@r.get("/participants/{pid}/ecrf", response_model=S.Ecrf, tags=["ecrf"])
def ecrf(pid: str, user=ANY):
    with engine.connect() as c:
        p = must(one(c, "SELECT study_id FROM participant WHERE id=:i", i=pid), "Participant")
        fs = rows(c, "SELECT * FROM ecrf_field WHERE study_id=:s ORDER BY ord", s=p["study_id"])
        vals = {v["field"]: v for v in rows(c, ECRFVAL + " WHERE participant_id=:p", p=pid)}
        pend = {x["field_id"]: x["id"] for x in rows(c, """SELECT DISTINCT ON (field_id) field_id, id FROM extraction
            WHERE participant_id=:p AND review_state='pending' ORDER BY field_id, created_at DESC, id DESC""", p=pid)}
    out = [S.EcrfField(id=f["id"], label=f["label"], section=f["section"], value_type=f["value_type"],
                       required=f["required"], unit=f["unit"], terminology=f["terminology"], help=f["help"],
                       value=vals.get(f["id"]), pending_extraction_id=pend.get(f["id"])) for f in fs]
    n = sum(1 for f in out if f.value)
    return S.Ecrf(participant_id=pid, form_id=fs[0]["form_id"] if fs else "", verified=n, total=len(out),
                  complete_pct=round(100 * n / len(out)) if out else 0, fields=out)


@r.post("/participants/{pid}/ecrf/{field}/sdv", response_model=S.EcrfValue, tags=["ecrf"])
def sdv(pid: str, field: str, user=Depends(require("monitor"))):
    """Monitor marks a verified eCRF value as source-data verified."""
    with engine.begin() as c:
        v = must(one(c, ECRFVAL + " WHERE participant_id=:p AND field_id=:f FOR UPDATE", p=pid, f=field), "Verified eCRF value")
        c.execute(text("UPDATE ecrf_value SET sdv_by=:u, sdv_at=now() WHERE participant_id=:p AND field_id=:f"),
                  dict(u=user["username"], p=pid, f=field))
        A.record(c, user, "ecrf.sdv", "ecrf_value", f"{pid}/{field}", participant_id=pid,
                 before={"sdv": v["sdv_at"] is not None}, after={"sdv": True, "value": v["value"]})
        return one(c, ECRFVAL + " WHERE participant_id=:p AND field_id=:f", p=pid, f=field)


# ---------- data queries ----------
@r.get("/queries", response_model=list[S.DataQuery], tags=["queries"])
def queries(participant_id: str | None = None, site_id: str | None = None, status: str | None = None, user=ANY):
    with engine.connect() as c:
        return rows(c, """SELECT * FROM data_query WHERE (:p IS NULL OR participant_id=:p)
          AND (:s IS NULL OR site_id=:s) AND (:st IS NULL OR status=:st) ORDER BY id""", p=participant_id, s=site_id, st=status)


@r.post("/queries", response_model=S.DataQuery, status_code=201, tags=["queries"])
def open_query(body: S.QueryIn, user=Depends(require("monitor", "pi"))):
    with engine.begin() as c:
        p = must(one(c, "SELECT site_id FROM participant WHERE id=:i", i=body.participant_id), "Participant")
        q = one(c, """INSERT INTO data_query (participant_id, site_id, field_id, severity, text, opened_by)
          VALUES (:p,:s,:f,:sev,:t,:u) RETURNING *""", p=body.participant_id, s=p["site_id"], f=body.field_id,
                sev=body.severity, t=body.text, u=user["username"])
        A.record(c, user, "query.opened", "data_query", q["id"], participant_id=body.participant_id, after={"text": body.text, "field": body.field_id})
    return q


@r.post("/queries/{qid}/close", response_model=S.DataQuery, tags=["queries"])
def close_query(qid: int, user=Depends(require("nurse", "pi", "monitor"))):
    with engine.begin() as c:
        q = must(one(c, "SELECT * FROM data_query WHERE id=:i FOR UPDATE", i=qid), "Query")
        if q["status"] == "closed":
            raise HTTPException(409, "Query is already closed")
        q = one(c, "UPDATE data_query SET status='closed', closed_by=:u, closed_at=now() WHERE id=:i RETURNING *", i=qid, u=user["username"])
        A.record(c, user, "query.closed", "data_query", qid, participant_id=q["participant_id"], before={"status": "open"}, after={"status": "closed"})
    return q


# ---------- audit ----------
@r.get("/audit", response_model=S.AuditPage, tags=["audit"])
def audit(actor: str | None = None, action: str | None = None, entity_type: str | None = None,
          entity_id: str | None = None, participant_id: str | None = None,
          source: Literal["human", "ai"] | None = None, since: str | None = None, until: str | None = None,
          limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), user=ANY):
    """Newest first. `action` matches exactly or as a prefix when it ends with '*'."""
    where = """(:actor IS NULL OR actor=:actor) AND (:ap IS NULL OR action LIKE :ap) AND (:et IS NULL OR entity_type=:et)
      AND (:ei IS NULL OR entity_id=:ei) AND (:p IS NULL OR participant_id=:p) AND (:src IS NULL OR source=:src)
      AND (:since IS NULL OR ts >= CAST(:since AS timestamptz)) AND (:until IS NULL OR ts <= CAST(:until AS timestamptz))"""
    prm = dict(actor=actor, ap=action.replace("*", "%") if action else None, et=entity_type, ei=entity_id,
               p=participant_id, src=source, since=since, until=until)
    with engine.connect() as c:
        total = one(c, f"SELECT count(*) n FROM audit_event WHERE {where}", **prm)["n"]
        items = rows(c, f"SELECT * FROM audit_event WHERE {where} ORDER BY seq DESC LIMIT :l OFFSET :o", **prm, l=limit, o=offset)
    return S.AuditPage(total=total, items=items)


@r.get("/audit/verify", response_model=S.AuditVerify, tags=["audit"])
def audit_verify(user=ANY):
    with engine.connect() as c:
        return A.verify(c)


# ---------- extraction runs (the AI service plugs in here) ----------
RUNSEL = "SELECT * FROM extraction_run"


@r.post("/participants/{pid}/extraction-runs", response_model=S.Run, status_code=201, tags=["runs"])
def create_run(pid: str, body: S.RunIn, user=Depends(require("nurse", "pi"))):
    """Queue an extraction run. The AI service picks up `queued` runs (GET /runs?status=queued)."""
    with engine.begin() as c:
        must(one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid), "Participant")
        if body.document_id:
            d = must(one(c, "SELECT participant_id FROM source_document WHERE id=:i", i=body.document_id), "Document")
            if d["participant_id"] != pid:
                raise HTTPException(422, "Document belongs to another participant")
        run = one(c, "INSERT INTO extraction_run (participant_id, document_id, status, created_by) VALUES (:p,:d,'queued',:u) RETURNING *",
                  p=pid, d=body.document_id, u=user["username"])
        A.record(c, user, "run.created", "extraction_run", run["id"], participant_id=pid, after={"documentId": body.document_id})
    return run


@r.get("/runs", response_model=list[S.Run], tags=["runs"])
def runs(status: str | None = None, participant_id: str | None = None, user=ANY):
    with engine.connect() as c:
        return rows(c, RUNSEL + " WHERE (:s IS NULL OR status=:s) AND (:p IS NULL OR participant_id=:p) ORDER BY id", s=status, p=participant_id)


@r.get("/runs/{rid}", response_model=S.Run, tags=["runs"])
def get_run(rid: int, user=ANY):
    with engine.connect() as c:
        return must(one(c, RUNSEL + " WHERE id=:i", i=rid), "Run")


@r.get("/runs/{rid}/events", tags=["runs"])
async def run_events(rid: int, user=ANY):
    """Server-sent events: `progress` whenever status/done/total change; closes when the run ends.
    EventSource cannot set headers, so `?access_token=<jwt>` is also accepted."""
    def fetch():
        with engine.connect() as c:
            return one(c, RUNSEL + " WHERE id=:i", i=rid)
    if not await run_in_threadpool(fetch):
        raise HTTPException(404, "Run not found")

    async def gen():
        last = None
        while True:
            run = await run_in_threadpool(fetch)
            snap = (run["status"], run["done"], run["total"])
            if snap != last:
                last = snap
                yield {"event": "progress", "data": S.Run(**run).model_dump_json(by_alias=True)}
            if run["status"] in ("completed", "failed"):
                return
            await asyncio.sleep(0.5)
    return EventSourceResponse(gen())


@r.patch("/runs/{rid}", response_model=S.Run, tags=["runs"])
def update_run(rid: int, body: S.RunProgressIn, user=Depends(require("service"))):
    with engine.begin() as c:
        run = must(one(c, RUNSEL + " WHERE id=:i FOR UPDATE", i=rid), "Run")
        new = {**run, **body.model_dump(exclude_none=True)}
        if new["status"] in ("completed", "failed"):
            fin = "now()"
        else:
            fin = "NULL"
        run = one(c, f"""UPDATE extraction_run SET status=:status, total=:total, done=:done, error=:error, provider=:provider,
          model=:model, prompt_version=:prompt_version, finished_at={fin} WHERE id=:id RETURNING *""", **{k: new[k] for k in
          ("status", "total", "done", "error", "provider", "model", "prompt_version", "id")})
        if body.status:
            A.record(c, user, f"run.{body.status}", "extraction_run", rid, participant_id=run["participant_id"],
                     after={"done": run["done"], "total": run["total"], "error": run["error"]}, source="ai",
                     model=run["model"], prompt_version=run["prompt_version"])
    return run


@r.post("/runs/{rid}/extractions", response_model=list[S.Extraction], status_code=201, tags=["runs"])
def ingest(rid: int, body: list[S.ExtractionIn], user=Depends(require("service"))):
    """AI service posts proposals. Evidence spans are checked against the stored document text."""
    ids = []
    with engine.begin() as c:
        run = must(one(c, RUNSEL + " WHERE id=:i FOR UPDATE", i=rid), "Run")
        if run["status"] in ("completed", "failed"):
            raise HTTPException(409, f"Run is {run['status']}")
        for x in body:
            d = must(one(c, "SELECT participant_id, text FROM source_document WHERE id=:i", i=x.document_id), "Document")
            if d["participant_id"] != run["participant_id"]:
                raise HTTPException(422, f"Document {x.document_id} belongs to another participant")
            must(one(c, "SELECT 1 FROM ecrf_field WHERE id=:i", i=x.field), f"eCRF field {x.field}")
            for ev in x.evidence:
                if d["text"][ev.start:ev.end] != ev.text:
                    raise HTTPException(422, f"Evidence span {ev.start}-{ev.end} does not match document text")
            if x.status == "proposed" and not x.value:
                raise HTTPException(422, "A proposed extraction needs a value")
            eid = x.id or f"EXT-R{rid}-{uuid.uuid4().hex[:8]}"
            e0 = x.evidence[0] if x.evidence else None
            c.execute(text("""INSERT INTO extraction (id, run_id, document_id, participant_id, field_id, status, value,
              normalized_value, unit, confidence, proposed_code, abstention_reason, span_start, span_end, evidence,
              provider, model, prompt_version) VALUES (:id,:run,:doc,:p,:f,:st,:v,CAST(:nv AS jsonb),:u,:conf,
              CAST(:code AS jsonb),:ar,:ss,:se,CAST(:ev AS jsonb),:prov,:model,:pv)"""),
                      dict(id=eid, run=rid, doc=x.document_id, p=run["participant_id"], f=x.field, st=x.status,
                           v=x.value, nv=json.dumps(x.normalized_value), u=x.unit, conf=x.confidence,
                           code=json.dumps(x.proposed_code) if x.proposed_code else None, ar=x.abstention_reason,
                           ss=e0.start if e0 else None, se=e0.end if e0 else None,
                           ev=json.dumps([e.model_dump() for e in x.evidence]), prov=x.provider, model=x.model, pv=x.prompt_version))
            A.record(c, user, "extraction.proposed", "extraction", eid, participant_id=run["participant_id"],
                     after={"field": x.field, "status": x.status, "value": x.value, "confidence": x.confidence},
                     source="ai", model=x.model, prompt_version=x.prompt_version, actor=f"{x.provider}/{x.model}")
            ids.append(eid)
        c.execute(text("UPDATE extraction_run SET done=done+:n, total=GREATEST(total, done+:n) WHERE id=:i"), dict(n=len(ids), i=rid))
        out = [_ex(e) for e in rows(c, EXSEL + " WHERE e.id = ANY(:ids) ORDER BY e.created_at, e.id", ids=ids)]
    return out
