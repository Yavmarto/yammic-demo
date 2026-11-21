import asyncio
from datetime import UTC, date, datetime
from typing import Literal
import json
import re
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text
from sse_starlette.sse import EventSourceResponse

from . import audit as A
from . import quality as Q
from . import schemas as S
from . import workflows as W
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
def _kpis_for(c, study_id: str, site_id: str | None = None, target: int = 0) -> S.Kpis:
    k = one(c, """
      SELECT
       (SELECT count(*) FROM participant p WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si)) enrolled,
       (SELECT count(DISTINCT p.id) FROM participant p JOIN source_document d ON d.participant_id=p.id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si)) scope,
       (SELECT count(*) FROM ecrf_field WHERE study_id=:s) fields,
       (SELECT count(*) FROM ecrf_value v JOIN participant p ON p.id=v.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si)) verified,
       (SELECT count(*) FROM ecrf_value v JOIN participant p ON p.id=v.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si) AND v.sdv_at IS NOT NULL) sdv,
       (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si)) ex_total,
       (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si) AND review_state='pending') ex_pending,
       (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si) AND review_state='accepted') ex_acc,
       (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si) AND review_state='corrected') ex_cor,
       (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si) AND review_state='rejected') ex_rej,
       (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si) AND review_state='deferred') ex_def,
       (SELECT count(*) FROM extraction e JOIN participant p ON p.id=e.participant_id
          WHERE p.study_id=:s AND (:si IS NULL OR p.site_id=:si) AND review_state='pending'
          AND (e.status='abstained' OR e.confidence < :lc)) attention,
       (SELECT count(*) FROM data_query q JOIN site s ON s.id=q.site_id
          WHERE s.study_id=:s AND (:si IS NULL OR q.site_id=:si) AND q.status IN ('open','answered')) queries,
       (SELECT count(*) FROM audit_event) audit
    """, s=study_id, si=site_id, lc=LOW_CONF)
    reviewed = k["ex_acc"] + k["ex_cor"] + k["ex_rej"]
    denom = k["scope"] * k["fields"]
    return S.Kpis(
        enrolled=k["enrolled"], target=target,
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


def _sites_for(c, study_id: str) -> list[S.Site]:
    raw = rows(c, """
      SELECT s.*,
        (SELECT count(*) FROM participant p WHERE p.site_id=s.id) enrolled,
        (SELECT count(*) FROM participant p WHERE p.site_id=s.id AND p.status='screening') screening,
        (SELECT count(*) FROM participant p WHERE p.site_id=s.id AND p.status='eligible') eligible,
        (SELECT count(*) FROM participant p WHERE p.site_id=s.id AND p.status='consented') consented,
        (SELECT count(*) FROM participant p WHERE p.site_id=s.id AND (p.status='screen_fail' OR p.status_detail='screen_failure')) screen_fail,
        (SELECT count(*) FROM data_query q WHERE q.site_id=s.id AND q.status IN ('open','answered')) open_queries
      FROM site s WHERE s.study_id=:s ORDER BY s.id""", s=study_id)
    out: list[S.Site] = []
    for s in raw:
        sk = _kpis_for(c, study_id, s["id"], s["target_enrolment"] or 0)
        out.append(S.Site(**s, ecrf_completeness=sk.ecrf_completeness,
                          ai_acceptance_rate=sk.ai_acceptance_rate,
                          sdv_done=sk.sdv_done, sdv_pending=sk.sdv_pending, kpis=sk))
    return out


@r.get("/studies/{study_id}/dashboard", response_model=S.Dashboard, tags=["study"])
def dashboard(study_id: str, site_id: str | None = Query(None, alias="siteId"),
              site_param: str | None = Query(None, alias="site", include_in_schema=False),
              site_id_snake: str | None = Query(None, alias="site_id", include_in_schema=False), user=ANY):
    sid = site_id or site_param or site_id_snake
    if sid and sid.lower() == "all":
        sid = None
    with engine.connect() as c:
        st = must(one(c, "SELECT * FROM study WHERE id = :i", i=study_id), "Study")
        if sid:
            site_row = must(one(c, "SELECT * FROM site WHERE id=:i AND study_id=:s", i=sid, s=study_id), "Site")
            target = site_row["target_enrolment"] or 0
        else:
            target = st["target_enrolment"] or 0
        kp = _kpis_for(c, study_id, sid, target)
        sites = _sites_for(c, study_id)
    meta = st["meta"] or {}
    return S.Dashboard(
        study_id=st["id"], title=st["short_name"], phase=st["phase"], status=st["status"],
        disclaimer=DISCLAIMER, site_id=sid, kpis=kp, sites=sites, site_comparison=sites,
        milestones=meta.get("milestones", []), alerts=meta.get("alerts", []), tasks=meta.get("tasks", []))


@r.get("/studies/{study_id}/sites/compare", response_model=list[S.Site], tags=["study"], include_in_schema=False)
@r.get("/studies/{study_id}/sites", response_model=list[S.Site], tags=["study"])
def study_sites(study_id: str, ids: str | None = None, user=ANY):
    with engine.connect() as c:
        must(one(c, "SELECT 1 FROM study WHERE id=:i", i=study_id), "Study")
        sites = _sites_for(c, study_id)
        if ids:
            wanted = {x.strip() for x in ids.split(",") if x.strip()}
            sites = [s for s in sites if s.id in wanted]
        return sites


# ---------- participants ----------
PSUM = """
SELECT p.id, p.study_id, p.site_id, p.status, p.status_detail, p.age, p.sex, p.enrolled_date,
  p.summary, p.diagnosis_date, p.screen_fail_reason, p.coordinator_signed_by, p.coordinator_signed_at,
  p.consented_date, p.enrolled_by, p.enrolled_at,
  (SELECT count(*) FROM source_document d WHERE d.participant_id=p.id) document_count,
  (SELECT count(*) FROM extraction e WHERE e.participant_id=p.id AND e.review_state='pending') extractions_pending,
  (SELECT count(*) FROM ecrf_value v WHERE v.participant_id=p.id) ecrf_verified,
  (SELECT count(*) FROM ecrf_field f WHERE f.study_id=p.study_id) ecrf_total,
  (SELECT count(*) FROM data_query q WHERE q.participant_id=p.id AND q.status IN ('open','answered')) open_queries
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


@r.get("/participants/{pid}/timeline", response_model=S.Timeline, tags=["participants"])
def participant_timeline(pid: str, user=ANY):
    """Ordered clinical timeline (surgery, radiotherapy, chemotherapy cycles, scans, visits), each linked to its source document/resource."""
    with engine.connect() as c:
        return must(W.build_timeline(c, pid), "Participant")


# ---------- screening workflow ----------
@r.get("/screening", response_model=list[S.Screening], tags=["screening"])
def list_screenings(site_id: str | None = None, status: str | None = None, user=ANY):
    """Screening queue across participants (optionally filtered by site_id or status)."""
    with engine.begin() as c:
        ps = rows(c, "SELECT id FROM participant WHERE (:s IS NULL OR site_id=:s) AND (:st IS NULL OR status=:st) ORDER BY id",
                  s=site_id, st=status)
        out: list[S.Screening] = []
        for p in ps:
            if not one(c, "SELECT 1 FROM screening_check WHERE participant_id=:p LIMIT 1", p=p["id"]):
                W.run_ai_screening(c, p["id"], user)
            out.append(W.build_screening(c, p["id"]))
        return out


@r.get("/screening/{pid}", response_model=S.Screening, tags=["screening"], include_in_schema=False)
@r.get("/participants/{pid}/screening", response_model=S.Screening, tags=["screening"])
def get_screening(pid: str, user=ANY):
    with engine.begin() as c:
        must(one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid), "Participant")
        if not one(c, "SELECT 1 FROM screening_check WHERE participant_id=:p LIMIT 1", p=pid):
            W.run_ai_screening(c, pid, user)
        return W.build_screening(c, pid)


@r.post("/participants/{pid}/screening/check", response_model=S.Screening, tags=["screening"])
def run_screening_check(pid: str, provider: str = Query("auto"), user=Depends(require("nurse", "pi", "service"))):
    """Run the AI screening checker against all trial entry criteria for a participant."""
    with engine.begin() as c:
        must(one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid), "Participant")
        W.run_ai_screening(c, pid, user, provider=provider)
        return W.build_screening(c, pid)


@r.post("/participants/{pid}/screening/checks", response_model=S.Screening, tags=["screening"])
def post_screening_checks(pid: str, body: list[S.ScreeningChecksIn], user=Depends(require("service", "nurse", "pi"))):
    """Ingest per-criterion AI screening results (from task C worker or test harness)."""
    with engine.begin() as c:
        p = must(one(c, "SELECT * FROM participant WHERE id=:i", i=pid), "Participant")
        for x in body:
            must(one(c, "SELECT 1 FROM screening_criterion WHERE study_id=:s AND id=:c", s=p["study_id"], c=x.criterion_id),
                 f"Criterion {x.criterion_id}")
            if x.document_id:
                d = must(one(c, "SELECT participant_id, text FROM source_document WHERE id=:i", i=x.document_id), "Document")
                if d["participant_id"] != pid:
                    raise HTTPException(422, f"Document {x.document_id} belongs to another participant")
                for ev in x.evidence:
                    if d["text"][ev.start:ev.end] != ev.text:
                        raise HTTPException(422, f"Evidence span {ev.start}-{ev.end} does not match document text")
            e0 = x.evidence[0] if x.evidence else None
            c.execute(text("""INSERT INTO screening_check
                (participant_id, criterion_id, ai_status, confidence, rationale, document_id, span_start, span_end,
                 evidence, provider, model, prompt_version, updated_at)
                VALUES (:p,:cid,:st,:conf,:rat,:doc,:ss,:se,CAST(:ev AS jsonb),:prov,:model,:pv,now())
                ON CONFLICT (participant_id, criterion_id) DO UPDATE SET
                  ai_status=:st, confidence=:conf, rationale=:rat, document_id=:doc,
                  span_start=:ss, span_end=:se, evidence=CAST(:ev AS jsonb),
                  provider=:prov, model=:model, prompt_version=:pv, updated_at=now()"""),
                      dict(p=pid, cid=x.criterion_id, st=x.status, conf=x.confidence, rat=x.rationale,
                           doc=x.document_id, ss=e0.start if e0 else None, se=e0.end if e0 else None,
                           ev=json.dumps([e.model_dump() for e in x.evidence]),
                           prov=x.provider, model=x.model, pv=x.prompt_version))
        A.record(c, user, "screening.ai_ingested", "participant", pid, participant_id=pid,
                 after={"count": len(body)}, source="ai",
                 model=body[0].model if body else None, prompt_version=body[0].prompt_version if body else None)
        return W.build_screening(c, pid)


@r.post("/screening/{pid}/criteria/{cid}", response_model=S.Screening, tags=["screening"], include_in_schema=False)
@r.post("/participants/{pid}/screening/criteria/{cid}/confirm", response_model=S.Screening, tags=["screening"])
def confirm_criterion(pid: str, cid: str, body: S.ScreeningCriterionConfirmIn,
                      user=Depends(require("nurse", "pi"))):
    """Coordinator (nurse or PI) confirms or overrides one criterion check."""
    st = body.status or body.state
    if not st:
        raise HTTPException(422, "status is required")
    with engine.begin() as c:
        p = must(one(c, "SELECT * FROM participant WHERE id=:i FOR UPDATE", i=pid), "Participant")
        must(one(c, "SELECT 1 FROM screening_criterion WHERE study_id=:s AND id=:c", s=p["study_id"], c=cid), "Criterion")
        prev = one(c, "SELECT * FROM screening_check WHERE participant_id=:p AND criterion_id=:c", p=pid, c=cid)
        c.execute(text("""INSERT INTO screening_check
            (participant_id, criterion_id, ai_status, coordinator_status, confirmed_by, confirmed_at, note, updated_at)
            VALUES (:p,:cid,:st,:st,:u,now(),:n,now())
            ON CONFLICT (participant_id, criterion_id) DO UPDATE SET
              coordinator_status=:st, confirmed_by=:u, confirmed_at=now(), note=:n, updated_at=now()"""),
                  dict(p=pid, cid=cid, st=st, u=user["username"], n=body.note))
        A.record(c, user, "screening.criterion_confirmed", "screening_check", f"{pid}/{cid}", participant_id=pid,
                 before={"coordinatorStatus": prev["coordinator_status"] if prev else None,
                         "aiStatus": prev["ai_status"] if prev else None},
                 after={"coordinatorStatus": st, "note": body.note})
        return W.build_screening(c, pid)


@r.post("/screening/{pid}/signoff", response_model=S.Screening, tags=["screening"], include_in_schema=False)
@r.post("/participants/{pid}/screening/sign-off", response_model=S.Screening, tags=["screening"])
def sign_off_screening(pid: str, body: S.ScreeningSignOffIn | None = Body(default=None),
                       user=Depends(require("nurse", "pi"))):
    """Coordinator signs off on the criteria checklist (`screening -> eligible` or `screen_fail`)."""
    body = body or S.ScreeningSignOffIn()
    with engine.begin() as c:
        p = must(one(c, "SELECT * FROM participant WHERE id=:i FOR UPDATE", i=pid), "Participant")
        if not one(c, "SELECT 1 FROM screening_check WHERE participant_id=:p LIMIT 1", p=pid):
            W.run_ai_screening(c, pid, user)
        scr = W.build_screening(c, pid)
        outcome = body.outcome or body.decision
        if outcome is None:
            outcome = "screen_fail" if scr.not_met_count > 0 else "eligible"
        if outcome == "screen_fail":
            reason = (body.reason or "").strip() or "Failed one or more eligibility criteria"
            c.execute(text("""UPDATE participant SET status='screen_fail', status_detail='screen_failure',
                screen_fail_reason=:r, coordinator_signed_by=:u, coordinator_signed_at=now() WHERE id=:i"""),
                      dict(r=reason, u=user["username"], i=pid))
            A.record(c, user, "screening.screen_fail", "participant", pid, participant_id=pid,
                     before={"status": p["status"]},
                     after={"status": "screen_fail", "reason": reason, "signedBy": user["username"]})
        else:
            if scr.not_met_count > 0:
                raise HTTPException(422, "Cannot mark eligible while any criterion is not_met")
            c.execute(text("""UPDATE participant SET status='eligible', status_detail='eligible',
                screen_fail_reason=NULL, coordinator_signed_by=:u, coordinator_signed_at=now() WHERE id=:i"""),
                      dict(u=user["username"], i=pid))
            A.record(c, user, "screening.signed_off", "participant", pid, participant_id=pid,
                     before={"status": p["status"]},
                     after={"status": "eligible", "signedBy": user["username"], "metCount": scr.met_count})
        return W.build_screening(c, pid)


@r.post("/participants/{pid}/screening/consent", response_model=S.Screening, tags=["screening"])
def record_consent(pid: str, body: S.ScreeningConsentIn | None = Body(default=None),
                   user=Depends(require("nurse", "pi"))):
    """Coordinator records written informed consent (`eligible -> consented`)."""
    body = body or S.ScreeningConsentIn()
    with engine.begin() as c:
        p = must(one(c, "SELECT * FROM participant WHERE id=:i FOR UPDATE", i=pid), "Participant")
        if p["status"] not in ("eligible", "consented"):
            raise HTTPException(409, f"Participant must be 'eligible' before consent (current: {p['status']})")
        cdate = body.consented_date or date.today()
        c.execute(text("""UPDATE participant SET status='consented', status_detail='consented',
            consented_date=:d WHERE id=:i"""), dict(d=cdate, i=pid))
        A.record(c, user, "screening.consented", "participant", pid, participant_id=pid,
                 before={"status": p["status"]}, after={"status": "consented", "consentedDate": str(cdate), "note": body.note})
        return W.build_screening(c, pid)


@r.post("/participants/{pid}/screening/enrol", response_model=S.Screening, tags=["screening"])
def enrol_participant(pid: str, body: S.ScreeningEnrolIn | None = Body(default=None),
                      user=Depends(require("pi"))):
    """Only the PI may enrol a participant (`eligible | consented -> enrolled`)."""
    body = body or S.ScreeningEnrolIn()
    with engine.begin() as c:
        p = must(one(c, "SELECT * FROM participant WHERE id=:i FOR UPDATE", i=pid), "Participant")
        if p["status"] not in ("eligible", "consented", "enrolled"):
            raise HTTPException(409, f"Participant must be signed off ('eligible' or 'consented') before PI enrolment (current: {p['status']})")
        edate = body.enrolled_date or date.today()
        cdate = p.get("consented_date") or edate
        c.execute(text("""UPDATE participant SET status='enrolled', status_detail='enrolled',
            consented_date=:cd, enrolled_date=:ed, enrolled_by=:u, enrolled_at=now() WHERE id=:i"""),
                  dict(cd=cdate, ed=edate, u=user["username"], i=pid))
        A.record(c, user, "screening.enrolled", "participant", pid, participant_id=pid,
                 before={"status": p["status"]},
                 after={"status": "enrolled", "enrolledDate": str(edate), "enrolledBy": user["username"], "note": body.note})
        return W.build_screening(c, pid)


@r.post("/participants/{pid}/screening/screen-fail", response_model=S.Screening, tags=["screening"])
def screen_fail_participant(pid: str, body: S.ScreenFailIn, user=Depends(require("nurse", "pi"))):
    """Mark a participant as `screen_fail` with a mandatory reason."""
    reason = (body.reason or "").strip()
    if not reason:
        raise HTTPException(422, "reason is required for screen_fail")
    with engine.begin() as c:
        p = must(one(c, "SELECT * FROM participant WHERE id=:i FOR UPDATE", i=pid), "Participant")
        c.execute(text("""UPDATE participant SET status='screen_fail', status_detail='screen_failure',
            screen_fail_reason=:r, coordinator_signed_by=:u, coordinator_signed_at=now() WHERE id=:i"""),
                  dict(r=reason, u=user["username"], i=pid))
        A.record(c, user, "screening.screen_fail", "participant", pid, participant_id=pid,
                 before={"status": p["status"]}, after={"status": "screen_fail", "reason": reason})
        return W.build_screening(c, pid)


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
        f_row = one(c, "SELECT form_version FROM ecrf_field WHERE id=:f", f=fid)
        f_ver = (f_row["form_version"] if f_row else 1) or 1
        if body.decision in ("accept", "correct"):
            v = e["value"] if body.decision == "accept" else corrected
            code = json.dumps(e["proposed_code"]) if body.decision == "accept" and e["proposed_code"] else None
            c.execute(text("""INSERT INTO ecrf_value (participant_id, field_id, value, code, source_extraction_id, verified_by, form_version)
              VALUES (:p,:f,:v,CAST(:c AS jsonb),:e,:u,:fv)
              ON CONFLICT (participant_id, field_id) DO UPDATE SET value=:v, code=CAST(:c AS jsonb),
                source_extraction_id=:e, verified_by=:u, verified_at=now(), sdv_by=NULL, sdv_at=NULL, form_version=:fv"""),
                      dict(p=pid, f=fid, v=v, c=code, e=eid, u=user["username"], fv=f_ver))
            new_val = {"value": v, "code": e["proposed_code"] if code else None, "formVersion": f_ver}
        elif prev_val and prev_val["source_extraction_id"] == eid:
            c.execute(text("DELETE FROM ecrf_value WHERE participant_id=:p AND field_id=:f"), dict(p=pid, f=fid))
        old = {"value": prev_val["value"], "code": prev_val["code"]} if prev_val else None
        if old != new_val:
            A.record(c, user, "ecrf.value_set" if new_val else "ecrf.value_cleared", "ecrf_value", f"{pid}/{fid}",
                     participant_id=pid, before=old, after=new_val, source="human",
                     model=e["model"], prompt_version=e["prompt_version"])
        Q.evaluate_participant(c, pid, user, trigger="decision")
        ex = _ex(one(c, EXSEL + " WHERE e.id=:i", i=eid))
        val = one(c, ECRFVAL + " WHERE participant_id=:p AND field_id=:f", p=pid, f=fid)
    return S.DecisionResult(extraction=ex, ecrf_value=val)


# ---------- eCRF ----------
ECRFVAL = """SELECT field_id AS field, value, code, source_extraction_id, verified_by, verified_at, sdv_by, sdv_at, form_version FROM ecrf_value"""


@r.get("/participants/{pid}/ecrf", response_model=S.Ecrf, tags=["ecrf"])
def ecrf(pid: str, user=ANY):
    with engine.connect() as c:
        p = must(one(c, "SELECT study_id FROM participant WHERE id=:i", i=pid), "Participant")
        fs = rows(c, "SELECT * FROM ecrf_field WHERE study_id=:s ORDER BY ord", s=p["study_id"])
        vals = {v["field"]: v for v in rows(c, ECRFVAL + " WHERE participant_id=:p", p=pid)}
        pend = {x["field_id"]: x["id"] for x in rows(c, """SELECT DISTINCT ON (field_id) field_id, id FROM extraction
            WHERE participant_id=:p AND review_state='pending' ORDER BY field_id, created_at DESC, id DESC""", p=pid)}
        cur_v = one(c, "SELECT coalesce(max(version), 1) v FROM ecrf_form_version WHERE study_id=:s AND status='approved'", s=p["study_id"])["v"]
    out = [S.EcrfField(id=f["id"], label=f["label"], section=f["section"], value_type=f["value_type"],
                       required=f["required"], unit=f["unit"], terminology=f["terminology"], help=f["help"],
                       min=f.get("min_val"), max=f.get("max_val"), allowed_values=f.get("allowed_values"),
                       form_version=f.get("form_version") or 1,
                       value=vals.get(f["id"]), pending_extraction_id=pend.get(f["id"])) for f in fs]
    n = sum(1 for f in out if f.value)
    return S.Ecrf(participant_id=pid, form_id=fs[0]["form_id"] if fs else "", form_version=cur_v,
                  verified=n, total=len(out),
                  complete_pct=round(100 * n / len(out)) if out else 0, fields=out)


@r.post("/participants/{pid}/ecrf/{field}/sdv", response_model=S.EcrfValue, tags=["ecrf"])
def sdv(pid: str, field: str, body: S.SdvIn | None = Body(default=None), user=Depends(require("monitor"))):
    """Monitor marks or unmarks a verified eCRF value as source-data verified."""
    with engine.begin() as c:
        v = must(one(c, ECRFVAL + " WHERE participant_id=:p AND field_id=:f FOR UPDATE", p=pid, f=field), "Verified eCRF value")
        want_sdv = True if (body is None or body.sdv is None) else body.sdv
        if want_sdv:
            c.execute(text("UPDATE ecrf_value SET sdv_by=:u, sdv_at=now() WHERE participant_id=:p AND field_id=:f"),
                      dict(u=user["username"], p=pid, f=field))
            A.record(c, user, "ecrf.sdv", "ecrf_value", f"{pid}/{field}", participant_id=pid,
                     before={"sdv": v["sdv_at"] is not None}, after={"sdv": True, "value": v["value"]})
        else:
            c.execute(text("UPDATE ecrf_value SET sdv_by=NULL, sdv_at=NULL WHERE participant_id=:p AND field_id=:f"),
                      dict(p=pid, f=field))
            A.record(c, user, "ecrf.sdv_cleared", "ecrf_value", f"{pid}/{field}", participant_id=pid,
                     before={"sdv": v["sdv_at"] is not None}, after={"sdv": False, "value": v["value"]})
        return one(c, ECRFVAL + " WHERE participant_id=:p AND field_id=:f", p=pid, f=field)


# ---------- data queries & data-quality rules ----------
@r.get("/data-quality/rules", response_model=list[S.DataQualityRule], tags=["queries"])
def list_data_quality_rules(user=ANY):
    """Catalog of automated data-quality rules (>=5 rules)."""
    return Q.RULES


@r.post("/participants/{pid}/data-quality/run", response_model=S.DataQualityResult, tags=["queries"])
def run_data_quality(pid: str, user=Depends(require("monitor", "nurse", "pi", "service"))):
    """Evaluate all data-quality rules for `pid` and auto-open queries for any new discrepancies."""
    with engine.begin() as c:
        must(one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid), "Participant")
        opened = Q.evaluate_participant(c, pid, user, trigger="manual")
    return S.DataQualityResult(participant_id=pid, checked=len(Q.RULES), opened=opened)


@r.get("/queries", response_model=list[S.DataQuery], tags=["queries"])
def queries(participant_id: str | None = None, site_id: str | None = None, field_id: str | None = None,
            status: str | None = None, user=ANY):
    with engine.connect() as c:
        return rows(c, """SELECT * FROM data_query WHERE (:p IS NULL OR participant_id=:p)
          AND (:s IS NULL OR site_id=:s) AND (:f IS NULL OR field_id=:f)
          AND (:st IS NULL OR status=:st) ORDER BY id""",
                    p=participant_id, s=site_id, f=field_id, st=status)


@r.post("/queries", response_model=S.DataQuery, status_code=201, tags=["queries"])
def open_query(body: S.QueryIn, user=Depends(require("monitor", "pi"))):
    with engine.begin() as c:
        p = must(one(c, "SELECT site_id FROM participant WHERE id=:i", i=body.participant_id), "Participant")
        q = one(c, """INSERT INTO data_query (participant_id, site_id, field_id, severity, text, opened_by, rule_id)
          VALUES (:p,:s,:f,:sev,:t,:u,:r) RETURNING *""", p=body.participant_id, s=p["site_id"], f=body.field_id,
                sev=body.severity, t=body.text, u=user["username"], r=body.rule_id)
        A.record(c, user, "query.opened", "data_query", q["id"], participant_id=body.participant_id,
                 after={"text": body.text, "field": body.field_id, "ruleId": body.rule_id})
    return q


@r.post("/queries/{qid}/reply", response_model=S.DataQuery, tags=["queries"], include_in_schema=False)
@r.post("/queries/{qid}/answer", response_model=S.DataQuery, tags=["queries"])
def answer_query(qid: int, body: S.QueryAnswerIn, user=Depends(require("nurse", "pi"))):
    """Nurse (or PI) answers an open query (`open -> answered`)."""
    ans = (body.answer or body.text or "").strip()
    if not ans:
        raise HTTPException(422, "answer is required")
    with engine.begin() as c:
        q = must(one(c, "SELECT * FROM data_query WHERE id=:i FOR UPDATE", i=qid), "Query")
        if q["status"] == "closed":
            raise HTTPException(409, "Query is already closed")
        q_new = one(c, """UPDATE data_query SET status='answered', answer=:a, answered_by=:u, answered_at=now()
                          WHERE id=:i RETURNING *""", i=qid, a=ans, u=user["username"])
        A.record(c, user, "query.answered", "data_query", qid, participant_id=q["participant_id"],
                 before={"status": q["status"], "answer": q.get("answer")},
                 after={"status": "answered", "answer": ans})
    return q_new


@r.post("/queries/{qid}/close", response_model=S.DataQuery, tags=["queries"])
def close_query(qid: int, user=Depends(require("nurse", "pi", "monitor"))):
    with engine.begin() as c:
        q = must(one(c, "SELECT * FROM data_query WHERE id=:i FOR UPDATE", i=qid), "Query")
        if q["status"] == "closed":
            raise HTTPException(409, "Query is already closed")
        prev_status = q["status"]
        q = one(c, "UPDATE data_query SET status='closed', closed_by=:u, closed_at=now() WHERE id=:i RETURNING *", i=qid, u=user["username"])
        A.record(c, user, "query.closed", "data_query", qid, participant_id=q["participant_id"],
                 before={"status": prev_status}, after={"status": "closed"})
    return q


# ---------- form versions (protocol-to-form) ----------
@r.get("/studies/{study_id}/form-versions", response_model=list[S.FormVersion], tags=["forms"], include_in_schema=False)
@r.get("/studies/{study_id}/forms", response_model=list[S.FormVersion], tags=["forms"])
def list_form_versions(study_id: str, status: str | None = None, user=ANY):
    with engine.connect() as c:
        must(one(c, "SELECT 1 FROM study WHERE id=:i", i=study_id), "Study")
        return rows(c, """SELECT * FROM ecrf_form_version
                          WHERE study_id=:s AND (:st IS NULL OR status=:st)
                          ORDER BY version DESC, id DESC""", s=study_id, st=status)


@r.get("/studies/{study_id}/forms/current", response_model=S.FormVersion, tags=["forms"])
def current_form_version(study_id: str, user=ANY):
    with engine.connect() as c:
        must(one(c, "SELECT 1 FROM study WHERE id=:i", i=study_id), "Study")
        return must(one(c, """SELECT * FROM ecrf_form_version WHERE study_id=:s AND status='approved'
                              ORDER BY version DESC, id DESC LIMIT 1""", s=study_id), "Approved form version")


@r.post("/studies/{study_id}/form-versions", response_model=S.FormVersion, status_code=201, tags=["forms"], include_in_schema=False)
@r.post("/studies/{study_id}/forms/propose", response_model=S.FormVersion, status_code=201, tags=["forms"])
def propose_form_version(study_id: str, body: S.FormVersionIn | None = Body(default=None),
                         user=Depends(require("nurse", "pi", "service"))):
    """Create a proposed eCRF form version (from AI protocol-to-form extraction or coordinator draft)."""
    body = body or S.FormVersionIn()
    with engine.begin() as c:
        must(one(c, "SELECT 1 FROM study WHERE id=:i", i=study_id), "Study")
        nxt = one(c, "SELECT coalesce(max(version), 0) + 1 v FROM ecrf_form_version WHERE study_id=:s AND form_id=:f",
                  s=study_id, f=body.form_id)["v"]
        fields_payload = [f.model_dump(by_alias=True) for f in body.fields]
        criteria_payload = [cr.model_dump(by_alias=True) for cr in body.criteria]
        proto = body.protocol_text or W.default_synopsis()
        prov = body.provider or "rules"
        mod = body.model or "protocol-rules-v4"
        pv = body.prompt_version or "form_v1"
        if not fields_payload and not criteria_payload:
            try:
                from .ai import protocol as ai_protocol
                ai_prop = ai_protocol.propose_from_synopsis(
                    proto, provider=body.provider or "auto", allow_fallback=True,
                    study_id=study_id, form_id=body.form_id, proposed_version=f"1.{nxt - 1}"
                )
                fields_payload = [f.as_api() for f in ai_prop.fields]
                criteria_payload = [cr.as_api() for cr in ai_prop.criteria]
                prov, mod, pv = ai_prop.metadata.provider, ai_prop.metadata.model, ai_prop.metadata.prompt_version
            except Exception:
                pass
        if not fields_payload:
            cur = one(c, "SELECT fields FROM ecrf_form_version WHERE study_id=:s AND status='approved' ORDER BY version DESC LIMIT 1", s=study_id)
            fields_payload = list(cur["fields"]) if cur else []
        if not criteria_payload:
            criteria_payload = W.default_criteria()
        fv = one(c, """INSERT INTO ecrf_form_version
            (study_id, form_id, version, status, fields, criteria, protocol_text, proposed_by, provider, model, prompt_version, note)
            VALUES (:s,:f,:v,'proposed',CAST(:fs AS jsonb),CAST(:cs AS jsonb),:pt,:u,:prov,:m,:pv,:n)
            RETURNING *""",
                 s=study_id, f=body.form_id, v=nxt, fs=json.dumps(fields_payload), cs=json.dumps(criteria_payload),
                 pt=proto, u=user["username"], prov=prov, m=mod,
                 pv=pv, n=body.note)
        A.record(c, user, "form.version_proposed", "ecrf_form_version", fv["id"],
                 after={"studyId": study_id, "formId": body.form_id, "version": nxt,
                        "fieldCount": len(fields_payload), "criteriaCount": len(criteria_payload)},
                 source="ai" if user["role"] == "service" else "human",
                 model=fv["model"], prompt_version=fv["prompt_version"])
    return fv


@r.post("/studies/{study_id}/form-versions/{version}/approve", response_model=S.FormVersion, tags=["forms"], include_in_schema=False)
@r.post("/studies/{study_id}/forms/{version}/approve", response_model=S.FormVersion, tags=["forms"])
def approve_form_version(study_id: str, version: int, body: S.FormApproveIn | None = Body(default=None),
                         user=Depends(require("pi"))):
    """Only the PI may approve a proposed eCRF version. Existing `ecrf_value` rows keep the version they were captured under."""
    body = body or S.FormApproveIn()
    with engine.begin() as c:
        must(one(c, "SELECT 1 FROM study WHERE id=:i", i=study_id), "Study")
        fv = must(one(c, """SELECT * FROM ecrf_form_version
                            WHERE study_id=:s AND (version=:v OR id=:v)
                            ORDER BY version DESC LIMIT 1 FOR UPDATE""", s=study_id, v=version), "Form version")
        ver_num = fv["version"]
        fv = one(c, """UPDATE ecrf_form_version SET status='approved', approved_by=:u, approved_at=now(),
                       note=coalesce(:n, note) WHERE id=:i RETURNING *""",
                 u=user["username"], n=body.note, i=fv["id"])
        # Apply newly approved fields to ecrf_field with form_version=ver_num (values already captured keep their own form_version)
        max_ord = one(c, "SELECT coalesce(max(ord), -1) m FROM ecrf_field WHERE study_id=:s", s=study_id)["m"]
        for idx, f in enumerate(fv["fields"] or []):
            fid = f.get("id")
            if not fid:
                continue
            existing = one(c, "SELECT ord FROM ecrf_field WHERE id=:id AND study_id=:s", id=fid, s=study_id)
            ord_num = existing["ord"] if existing else (max_ord + 1 + idx)
            c.execute(text("""INSERT INTO ecrf_field
                (id, study_id, form_id, ord, label, section, value_type, required, unit, terminology, help, cdisc, min_val, max_val, allowed_values, form_version)
                VALUES (:id,:s,:fm,:ord,:l,:sec,:vt,:req,:u,CAST(:term AS jsonb),:h,CAST(:cd AS jsonb),:mi,:ma,CAST(:av AS jsonb),:fv)
                ON CONFLICT (id) DO UPDATE SET
                  label=:l, section=coalesce(:sec, ecrf_field.section), value_type=coalesce(:vt, ecrf_field.value_type),
                  required=:req, unit=coalesce(:u, ecrf_field.unit),
                  terminology=coalesce(CAST(:term AS jsonb), ecrf_field.terminology),
                  help=coalesce(:h, ecrf_field.help), min_val=coalesce(:mi, ecrf_field.min_val),
                  max_val=coalesce(:ma, ecrf_field.max_val),
                  allowed_values=coalesce(CAST(:av AS jsonb), ecrf_field.allowed_values),
                  form_version=:fv"""),
                      dict(id=fid, s=study_id, fm=fv["form_id"], ord=ord_num,
                           l=f.get("label") or fid, sec=f.get("section") or "clinical_status",
                           vt=f.get("valueType") or f.get("value_type") or "string",
                           req=bool(f.get("required", True)), u=f.get("unit"),
                           term=json.dumps(f["terminology"]) if f.get("terminology") else None,
                           h=f.get("help") or f.get("sourceSentence") or f.get("source_sentence"),
                           cd=json.dumps(f["cdisc"]) if f.get("cdisc") else None,
                           mi=f.get("min"), ma=f.get("max"),
                           av=json.dumps(f.get("allowedValues") or f.get("allowed_values")) if (f.get("allowedValues") or f.get("allowed_values")) else None,
                           fv=ver_num))
        # Apply criteria from the approved version
        for idx, cr in enumerate(fv["criteria"] or []):
            cid = cr.get("id")
            if not cid:
                continue
            c.execute(text("""INSERT INTO screening_criterion (study_id, id, ord, type, text, data_needed, version)
                VALUES (:s,:id,:ord,:t,:txt,:dn,:v)
                ON CONFLICT (study_id, id) DO UPDATE SET
                  type=:t, text=:txt, data_needed=coalesce(:dn, screening_criterion.data_needed), version=:v"""),
                      dict(s=study_id, id=cid, ord=idx, t=cr.get("type") or "inclusion",
                           txt=cr.get("text") or cid, dn=cr.get("dataNeeded") or cr.get("data_needed"), v=ver_num))
        A.record(c, user, "form.version_approved", "ecrf_form_version", fv["id"],
                 before={"status": "proposed"},
                 after={"status": "approved", "version": ver_num, "approvedBy": user["username"],
                        "fields": len(fv["fields"] or []), "criteria": len(fv["criteria"] or [])})
    return fv


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
