"""FHIR -> platform sync. Pull, pseudonymise, store, queue AI extraction, audit."""
import base64
import hashlib
import json
import time
from datetime import UTC, datetime

from sqlalchemy import text

from .. import audit as A
from ..db import engine
from . import fhir
from .pseudo import Scrubber, patient_terms, pseudonym
from .pseudo import mrn_hmac as _mrn_hmac

SUBJECT_SYS = "study-subject-id"
STUDY_SYS = "study-number"
FACT_TYPES = [t for t in fhir.TYPES if t != "Patient"]


def _cc(cc: dict | None):
    cc = cc or {}
    c = (cc.get("coding") or [{}])[0]
    return c.get("code"), cc.get("text") or c.get("display")


def _value(r: dict):
    for k, v in r.items():
        if k.startswith("value") and k != "valueSet":
            if isinstance(v, dict) and "value" in v:
                return f"{v['value']} {v.get('unit', '')}".strip()
            if isinstance(v, dict):
                return _cc(v)[1]
            return str(v)
    return None


def _effective(r: dict):
    for k in ("effectiveDateTime", "performedDateTime", "authoredOn", "onsetDateTime", "date", "issued", "recordedDate"):
        if r.get(k):
            return r[k]
    for k in ("performedPeriod", "effectivePeriod"):
        if r.get(k):
            return r[k].get("start")


def to_fact(r: dict) -> dict:
    """Whitelisted fields only, so nothing identifying can ride along in the stored fact."""
    t = r["resourceType"]
    code, display = _cc(r.get("code") or r.get("medicationCodeableConcept") or r.get("type"))
    value = _value(r)
    if t == "DiagnosticReport":
        value = r.get("conclusion")
    elif t.startswith("Medication") and r.get("dosageInstruction"):
        value = r["dosageInstruction"][0].get("text")
    elif t == "Condition":
        value = (r.get("bodySite") or [{}])[0].get("text")
    elif t == "Procedure":
        value = (r.get("outcome") or {}).get("text") or (r.get("bodySite") or [{}])[0].get("text")
    elif t == "DocumentReference":
        value = r.get("description")
    status = r.get("status") or _cc(r.get("verificationStatus"))[0]
    data = {"code": code, "display": display, "value": value, "effective": _effective(r), "status": status}
    if t == "Observation":
        data["interpretation"] = _cc((r.get("interpretation") or [None])[0])[0]
    return {**data, "type": t}


def _subject(r: dict) -> str | None:
    ref = ((r.get("subject") or r.get("patient") or {}).get("reference") or "")
    return ref.split("/", 1)[1] if ref.startswith("Patient/") else None


def _ident(p: dict, frag: str):
    return next((i["value"] for i in p.get("identifier", []) if frag in (i.get("system") or "")), None)


def _doc_type(r: dict) -> str:
    blob = " ".join(filter(None, [(r.get("type") or {}).get("text"), r.get("description"),
                                  *[(c or {}).get("text") for c in r.get("category", [])]])).lower()
    for keys, t in ((("patholog",), "pathology_report"), (("radiolog", "mri"), "radiology_report"),
                    (("operat", "surg"), "operative_report")):
        if any(k in blob for k in keys):
            return t
    return "discharge_letter"


def _age(birth: str | None):
    return datetime.now(UTC).year - int(birth[:4]) if birth and birth[:4].isdigit() else None


def _one(c, sql, **p):
    x = c.execute(text(sql), p).mappings().first()
    return dict(x) if x else None


def _bump(counts, key, field, n=1):
    counts.setdefault(key, {}).setdefault(field, 0)
    counts[key][field] += n


def status_of(c, source_id: str | None = None) -> dict | None:
    if source_id:
        return _one(c, "SELECT * FROM fhir_sync_run WHERE source_id=:s ORDER BY id DESC LIMIT 1", s=source_id)
    return _one(c, "SELECT * FROM fhir_sync_run ORDER BY id DESC LIMIT 1")


def run_sync(user: dict, source=None, *, full: bool = False, source_id: str = "hospital-1",
             source_name: str | None = None, default_site_id: str | None = None,
             after_participant=None) -> dict:
    source = source or fhir.HttpSource()
    t0, started = time.perf_counter(), datetime.now(UTC)
    with engine.connect() as c:
        last = _one(c, """SELECT cursor FROM fhir_sync_run
            WHERE source_id=:sid AND status IN ('completed','partial') AND cursor IS NOT NULL
            ORDER BY id DESC LIMIT 1""", sid=source_id)
    since = None if full or not last else last["cursor"]
    mode = "incremental" if since else "full"

    try:
        source.metadata()
        fetched = {t: source.search(t, since) for t in fhir.TYPES}
    except fhir.FhirError as e:
        return _record_failure(user, started, t0, mode, since, str(e), source_id=source_id, source_name=source_name)

    counts: dict = {t: {"fetched": len(v), "created": 0, "updated": 0, "unchanged": 0, "skipped": 0}
                    for t, v in fetched.items()}
    counts["participants"] = {"created": 0, "existing": 0}
    counts["documents"] = {"created": 0, "existing": 0}
    counts["extractionRuns"] = {"queued": 0}
    errors: list[dict] = []
    cursor = since
    for rs in fetched.values():
        for r in rs:
            lu = (r.get("meta") or {}).get("lastUpdated")
            if lu and (cursor is None or lu > cursor):
                cursor = lu

    with engine.begin() as c:
        c.execute(text("SELECT pg_advisory_xact_lock(7744)"))  # one sync at a time
        run_id = c.execute(text("""INSERT INTO fhir_sync_run (started_at, status, mode, since, triggered_by, source_id, source_name)
            VALUES (:s,'completed',:m,:since,:u,:sid,:sn) RETURNING id"""),
                           dict(s=started, m=mode, since=since, u=user["username"], sid=source_id, sn=source_name)).scalar()
        scrub: dict[str, Scrubber] = {}   # participant id -> scrubber
        pids: dict[str, str] = {}         # FHIR Patient.id -> participant id
        new: set[str] = set()             # participants created by this run
        touched: set[str] = set()         # participants whose facts/documents arrived in this run

        def err(rtype, rid, msg):
            errors.append({"resourceType": rtype, "id": rid, "error": msg[:300]})
            _bump(counts, rtype, "skipped")

        for p in fetched["Patient"]:
            with c.begin_nested():
                try:
                    pid = _patient(c, p, run_id, user, counts, scrub, new,
                                   source_id=source_id, default_site_id=default_site_id)
                    pids[p["id"]] = pid
                except Exception as e:  # one bad resource must not sink the sync
                    err("Patient", p.get("id"), repr(e))
        for t in FACT_TYPES:
            for r in fetched[t]:
                with c.begin_nested():
                    try:
                        ref = _subject(r)
                        pid = pids.get(ref) or (ref if ref and _one(c, "SELECT 1 FROM participant WHERE id=:i", i=ref) else None)
                        if not pid:
                            raise ValueError(f"no participant for subject {ref!r}")
                        touched.add(pid)
                        if pid not in scrub:
                            scrub[pid] = Scrubber(set(), "[pseudonymised]")
                        _fact(c, r, pid, run_id, user, counts, scrub[pid], source_id=source_id)
                    except Exception as e:
                        err(t, r.get("id"), repr(e))
        for pid in new:
            _describe(c, pid)
        if after_participant:
            for pid in set(pids.values()) | touched:
                after_participant(c, pid, user)
        ms = int((time.perf_counter() - t0) * 1000)
        status = "partial" if errors else "completed"
        c.execute(text("""UPDATE fhir_sync_run SET finished_at=now(), duration_ms=:d, status=:s, cursor=:cur,
            counts=CAST(:n AS jsonb), errors=CAST(:e AS jsonb) WHERE id=:i"""),
                  dict(d=ms, s=status, cur=cursor, n=json.dumps(counts), e=json.dumps(errors), i=run_id))
        A.record(c, user, "fhir.sync", "fhir_sync_run", run_id, source="human",
                 after={"sourceId": source_id, "mode": mode, "status": status, "durationMs": ms, "errors": len(errors),
                        "participantsCreated": counts["participants"]["created"],
                        "documentsCreated": counts["documents"]["created"],
                        "extractionRunsQueued": counts["extractionRuns"]["queued"]})
        return _one(c, "SELECT * FROM fhir_sync_run WHERE id=:i", i=run_id)


def _record_failure(user, started, t0, mode, since, msg, *, source_id="hospital-1", source_name=None):
    ms = int((time.perf_counter() - t0) * 1000)
    with engine.begin() as c:
        run = _one(c, """INSERT INTO fhir_sync_run (started_at, finished_at, duration_ms, status, mode, since, triggered_by, source_id, source_name, errors)
            VALUES (:s, now(), :d, 'failed', :m, :since, :u, :sid, :sn, CAST(:e AS jsonb)) RETURNING *""",
                   s=started, d=ms, m=mode, since=since, u=user["username"], sid=source_id, sn=source_name,
                   e=json.dumps([{"resourceType": None, "id": None, "error": msg[:300]}]))
        A.record(c, user, "fhir.sync", "fhir_sync_run", run["id"], after={"sourceId": source_id, "status": "failed", "error": msg[:300]})
    return run


def _patient(c, p, run_id, user, counts, scrub, new, *, source_id="hospital-1", default_site_id=None) -> str:
    pid = _ident(p, SUBJECT_SYS) or p["id"]
    mrn, terms = patient_terms(p)
    study = _one(c, "SELECT id FROM study WHERE id=:i", i=_ident(p, STUDY_SYS)) or _one(c, "SELECT id FROM study LIMIT 1")
    site_ref = ((p.get("managingOrganization") or {}).get("reference") or "").split("/")[-1] or default_site_id
    site = _one(c, "SELECT id FROM site WHERE id=:i AND study_id=:s", i=site_ref, s=study["id"] if study else None)
    if not site and default_site_id and study:
        site = _one(c, "SELECT id FROM site WHERE id=:i AND study_id=:s", i=default_site_id, s=study["id"])
    site_key = site["id"] if site else (site_ref or source_id)
    psn = pseudonym(mrn or p["id"], site_key)
    scrub[pid] = Scrubber(terms, psn)
    if _one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid):
        counts["participants"]["existing"] += 1
        _bump(counts, "Patient", "unchanged")
    else:
        if not study or not site:
            raise ValueError(f"unknown study/site for patient (site {site_ref!r})")
        c.execute(text("""INSERT INTO participant (id, study_id, site_id, status, status_detail, synced_from_fhir, age, sex, summary)
            VALUES (:i,:st,:si,'screening','synced_from_fhir',true,:age,:sex,:sum)"""),
                  dict(i=pid, st=study["id"], si=site["id"], age=_age(p.get("birthDate")),
                       sex={"male": "M", "female": "F"}.get(p.get("gender"), "U"),
                       sum="Synced from the hospital EHR. Clinical summary builds up as documents are reviewed."))
        counts["participants"]["created"] += 1
        new.add(pid)
        _bump(counts, "Patient", "created")
        A.record(c, user, "fhir.participant_created", "participant", pid, participant_id=pid,
                 after={"pseudonym": psn, "siteId": site["id"], "sourceId": source_id, "age": _age(p.get("birthDate"))})
    c.execute(text("""INSERT INTO pseudonym_map (pseudonym, mrn_hmac, participant_id, source_id) VALUES (:p,:h,:i,:sid)
        ON CONFLICT DO NOTHING"""), dict(p=psn, h=_mrn_hmac(mrn or p["id"], site_key), i=pid, sid=source_id))
    return pid


def _fact(c, r, pid, run_id, user, counts, sc: Scrubber, *, source_id="hospital-1"):
    t, rid = r["resourceType"], r["id"]
    if t == "DocumentReference":
        _document(c, r, pid, run_id, user, counts, sc, source_id=source_id)
    f = to_fact(r)
    data = json.loads(sc.text(json.dumps(f, ensure_ascii=False)))
    lu = (r.get("meta") or {}).get("lastUpdated")
    row = c.execute(text("""INSERT INTO fhir_fact (resource_type, fhir_id, participant_id, last_updated, code, display,
          value, effective, status, data, sync_run_id)
        VALUES (:t,:i,:p,:lu,:code,:disp,:val,:eff,:st,CAST(:d AS jsonb),:run)
        ON CONFLICT (resource_type, fhir_id) DO UPDATE SET last_updated=:lu, code=:code, display=:disp, value=:val,
          effective=:eff, status=:st, data=CAST(:d AS jsonb), sync_run_id=:run
          WHERE fhir_fact.data IS DISTINCT FROM EXCLUDED.data
        RETURNING (xmax = 0) AS inserted"""),
                    dict(t=t, i=rid, p=pid, lu=lu, code=data["code"], disp=data["display"], val=data["value"],
                         eff=data["effective"], st=data["status"], d=json.dumps(data), run=run_id)).first()
    _bump(counts, t, "unchanged" if row is None else "created" if row[0] else "updated")


def _document(c, r, pid, run_id, user, counts, sc: Scrubber, *, source_id="hospital-1"):
    mi = (r.get("masterIdentifier") or {}).get("value") or _ident(r, "hospital-document-id") or r["id"]
    if _one(c, "SELECT 1 FROM source_document WHERE id=:i", i=mi):
        counts["documents"]["existing"] += 1
        return
    att = next((x["attachment"] for x in r.get("content", []) if x["attachment"].get("contentType", "").startswith("text/plain")
                and x["attachment"].get("data")), None)
    if not att:
        raise ValueError("DocumentReference has no inline text/plain attachment")
    body = sc.text(base64.b64decode(att["data"]).decode("utf-8"))
    sha = hashlib.sha256(body.encode()).hexdigest()
    dd = (r.get("date") or "")[:10] or None
    c.execute(text("""INSERT INTO source_document (id, participant_id, doc_type, title, language, document_date, text, sha256,
          source_system, ingested_run_id) VALUES (:i,:p,:t,:ti,:l,:d,:x,:h,:sys,:run)"""),
              dict(i=mi, p=pid, t=_doc_type(r), ti=sc.text(r.get("description") or mi), l=att.get("language"),
                   d=dd, x=body, h=sha, sys=f"fhir:{source_id}", run=run_id))
    counts["documents"]["created"] += 1
    A.record(c, user, "fhir.document_ingested", "source_document", mi, participant_id=pid,
             after={"docType": _doc_type(r), "sha256": sha, "chars": len(body), "sourceId": source_id})
    # auto-trigger AI extraction (W4): the AI service polls queued runs
    rid = c.execute(text("""INSERT INTO extraction_run (participant_id, document_id, status, provider, created_by)
        VALUES (:p,:d,'queued','auto',:u) RETURNING id"""), dict(p=pid, d=mi, u=user["username"])).scalar()
    counts["extractionRuns"]["queued"] += 1
    A.record(c, user, "run.created", "extraction_run", rid, participant_id=pid,
             after={"documentId": mi, "provider": "auto", "trigger": "fhir.sync", "sourceId": source_id})


def _describe(c, pid):
    """Give a new participant a summary from its synced Condition. Every synced patient starts in
    screening, whatever the hospital's ResearchSubject/Condition status says; only the platform enrols."""
    cond = _one(c, "SELECT * FROM fhir_fact WHERE participant_id=:p AND resource_type='Condition' ORDER BY effective LIMIT 1", p=pid)
    if not cond:
        return
    provisional = (cond["status"] or "") == "provisional"
    onset = (cond["effective"] or "")[:10] or None
    c.execute(text("UPDATE participant SET diagnosis_date=:d, summary=:m WHERE id=:i"),
              dict(d=onset, i=pid,
                   m=f"Synced from the hospital EHR: {cond['display']}"
                     f"{', ' + cond['value'] if cond['value'] else ''}"
                     f"{' (provisional, histology pending)' if provisional else ''}."))
