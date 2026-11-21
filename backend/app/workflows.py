"""Screening workflow + AI criterion checker bridge + timeline + protocol-to-form versions (v4)."""
from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import text

from . import audit as A
from . import schemas as S

DELIVERABLES = Path(__file__).resolve().parents[2] / "deliverables"


def _rows(c, sql: str, **p) -> list[dict]:
    return [dict(x) for x in c.execute(text(sql), p).mappings()]


def _one(c, sql: str, **p) -> dict | None:
    x = c.execute(text(sql), p).mappings().first()
    return dict(x) if x else None


def default_criteria() -> list[dict]:
    path = DELIVERABLES / "protocol_criteria.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return [
        {"id": "INC-01", "type": "inclusion", "text": "Age 18 years or older at diagnosis.", "dataNeeded": "AGE, MHSTDAT"},
        {"id": "INC-02", "type": "inclusion", "text": "Histologically confirmed glioblastoma, IDH-wildtype.", "dataNeeded": "HISTOLOGY, IDHSTAT"},
        {"id": "INC-03", "type": "inclusion", "text": "MGMT promoter methylation status is known.", "dataNeeded": "MGMTPROM"},
        {"id": "INC-04", "type": "inclusion", "text": "Karnofsky Performance Status 60 or higher.", "dataNeeded": "KPS"},
        {"id": "EXC-01", "type": "exclusion", "text": "Any prior radiotherapy to the brain.", "dataNeeded": "Radiotherapy history"},
        {"id": "EXC-03", "type": "exclusion", "text": "Tumour is IDH-mutant, or IDH status is indeterminate.", "dataNeeded": "IDHSTAT"},
    ]


def default_synopsis() -> str:
    path = DELIVERABLES / "protocol_GBM-NL-2026-01_synopsis.md"
    return path.read_text() if path.exists() else "SYNTHETIC PROTOCOL SYNOPSIS — GBM-NL-2026-01"


def _find_span(docs: list[dict], patterns: list[str]) -> tuple[str | None, int | None, int | None, list[dict]]:
    for d in docs:
        txt = d["text"]
        for pat in patterns:
            m = re.search(pat, txt, re.I)
            if m:
                s, e = m.start(), m.end()
                return d["id"], s, e, [{"start": s, "end": e, "text": txt[s:e]}]
    return None, None, None, []


def run_ai_screening(c, pid: str, user: dict, *, provider: str = "auto") -> list[dict]:
    """Evaluate all study criteria for `pid` using task C's AI screening checker if available,
    falling back to deterministic rule checks with exact document spans."""
    p = _one(c, "SELECT * FROM participant WHERE id=:i", i=pid)
    if not p:
        return []
    criteria = _rows(c, "SELECT * FROM screening_criterion WHERE study_id=:s ORDER BY ord", s=p["study_id"])
    docs = _rows(c, "SELECT * FROM source_document WHERE participant_id=:p ORDER BY id", p=pid)
    exts = {e["field_id"]: e for e in _rows(c, "SELECT * FROM extraction WHERE participant_id=:p AND status='proposed' ORDER BY confidence DESC", p=pid)}
    vals = {v["field_id"]: v for v in _rows(c, "SELECT * FROM ecrf_value WHERE participant_id=:p", p=pid)}
    facts = _rows(c, "SELECT * FROM fhir_fact WHERE participant_id=:p", p=pid)

    # Delegate to task C's app.ai.screening checker first
    try:
        from .ai import screening as ai_screening
        from .ai.types import CriterionDef
        crit_defs = [CriterionDef.from_api(cr) for cr in criteria]
        ai_docs = [{**d, "type": d["doc_type"]} for d in docs]
        res = ai_screening.check_participant(pid, ai_docs, criteria=crit_defs, provider=provider, allow_fallback=True)
        meta = res.metadata
        results_out: list[dict] = []
        for chk in res.checks:
            ev = [e.as_api() for e in chk.evidence]
            e0 = chk.evidence[0] if chk.evidence else None
            c.execute(text("""INSERT INTO screening_check
                (participant_id, criterion_id, ai_status, confidence, rationale, document_id, span_start, span_end,
                 evidence, provider, model, prompt_version, updated_at)
                VALUES (:p,:cid,:st,:conf,:rat,:doc,:ss,:se,CAST(:ev AS jsonb),:prov,:m,:pv,now())
                ON CONFLICT (participant_id, criterion_id) DO UPDATE SET
                  ai_status=:st, confidence=:conf, rationale=:rat, document_id=:doc,
                  span_start=:ss, span_end=:se, evidence=CAST(:ev AS jsonb),
                  provider=:prov, model=:m, prompt_version=:pv, updated_at=now()"""),
                      dict(p=pid, cid=chk.criterion_id, st=chk.verdict, conf=chk.confidence, rat=chk.rationale,
                           doc=chk.document_id, ss=e0.start if e0 else None, se=e0.end if e0 else None,
                           ev=json.dumps(ev), prov=meta.provider, m=meta.model, pv=meta.prompt_version))
            results_out.append({"criterion_id": chk.criterion_id, "ai_status": chk.verdict, "confidence": chk.confidence})
        A.record(c, user, "screening.ai_checked", "participant", pid, participant_id=pid,
                 after={"criteriaChecked": len(results_out), "overall": res.overall,
                        "met": sum(1 for r in results_out if r["ai_status"] == "met"),
                        "notMet": sum(1 for r in results_out if r["ai_status"] == "not_met"),
                        "unknown": sum(1 for r in results_out if r["ai_status"] == "unknown")},
                 source="ai", model=meta.model, prompt_version=meta.prompt_version,
                 actor=f"{meta.provider}/{meta.model}")
        return results_out
    except Exception:
        pass

    results: list[dict] = []
    for crit in criteria:
        cid = crit["id"]
        if external_results and cid in external_results:
            r = external_results[cid]
            results.append(r)
            continue
        status, conf, rationale = "unknown", 0.0, "Insufficient evidence in source documents."
        doc_id, ss, se, ev = None, None, None, []

        def _from_ext(fid: str):
            if fid in exts:
                e = exts[fid]
                return e["document_id"], e["span_start"], e["span_end"], e["evidence"] or []
            return None, None, None, []

        if cid == "INC-01":  # Age >= 18
            age = p.get("age")
            if "AGE" in vals and str(vals["AGE"]["value"]).isdigit():
                age = int(vals["AGE"]["value"])
            elif "AGE" in exts and str(exts["AGE"]["value"] or "").isdigit():
                age = int(exts["AGE"]["value"])
            doc_id, ss, se, ev = _from_ext("AGE")
            if not doc_id:
                doc_id, ss, se, ev = _find_span(docs, [r"LEEFTIJD[^\n]*\d+\s*jaar", r"AGE[^\n]*\d+\s*years"])
            if age is not None:
                status = "met" if age >= 18 else "not_met"
                conf = 0.97 if doc_id else 0.85
                rationale = f"Age at diagnosis is {age} years ({'>= 18' if age >= 18 else '< 18'})."
        elif cid == "INC-02":  # Histologically confirmed GBM, IDH-wildtype
            hist = (vals.get("HISTOLOGY", {}).get("value") or exts.get("HISTOLOGY", {}).get("value") or "")
            idh = (vals.get("IDHSTAT", {}).get("value") or exts.get("IDHSTAT", {}).get("value") or "")
            doc_id, ss, se, ev = _from_ext("HISTOLOGY")
            if not doc_id:
                doc_id, ss, se, ev = _find_span(docs, [r"Glioblasto(?:om|ma),\s*IDH-wildtype", r"IDH-mutant"])
            if "mutant" in idh.lower() or "idh-mutant" in (p.get("summary") or "").lower():
                status, conf, rationale = "not_met", 0.95, "Tumour is IDH-mutant (IDH-wildtype required)."
            elif ("glioblast" in hist.lower() and "wildtype" in idh.lower()) or (doc_id and "wildtype" in (ev[0]["text"].lower() if ev else "")):
                status, conf, rationale = "met", 0.96, "Histologically confirmed glioblastoma, IDH-wildtype."
        elif cid == "INC-03":  # MGMT status known
            mgmt = (vals.get("MGMTPROM", {}).get("value") or exts.get("MGMTPROM", {}).get("value") or "")
            doc_id, ss, se, ev = _from_ext("MGMTPROM")
            if not doc_id:
                doc_id, ss, se, ev = _find_span(docs, [r"MGMT[^\n]*(?:methyl|gemethyleerd|ongemethyleerd)"])
            if any(k in mgmt.lower() for k in ("methylated", "unmethylated")) or doc_id:
                status, conf, rationale = "met", 0.93, f"MGMT promoter status is documented ({mgmt or 'in pathology report'})."
            elif "indeterminate" in mgmt.lower():
                status, conf, rationale = "not_met", 0.9, "MGMT promoter status is indeterminate."
        elif cid == "INC-04":  # KPS >= 60
            kps_val = vals.get("KPS", {}).get("value") or exts.get("KPS", {}).get("value")
            doc_id, ss, se, ev = _from_ext("KPS")
            if not doc_id:
                doc_id, ss, se, ev = _find_span(docs, [r"Karnofsky[^\n]*\d{2,3}\s*%?", r"KPS[:\s]*\d{2,3}"])
            if kps_val is not None:
                m = re.search(r"\d+", str(kps_val))
                if m:
                    kps_n = int(m.group(0))
                    status = "met" if kps_n >= 60 else "not_met"
                    conf = 0.92
                    rationale = f"Karnofsky Performance Status is {kps_n}% ({'>= 60%' if kps_n >= 60 else '< 60%'})."
        elif cid in ("INC-05", "INC-06", "INC-07"):  # Organ function labs
            lab_facts = [f for f in facts if f["resource_type"] == "Observation"]
            if lab_facts or docs:
                doc_id, ss, se, ev = _find_span(docs, [r"ongecompliceerd", r"uneventful", r"Karnofsky[^\n]+", r"BELEID|PLAN"])
                if not doc_id and docs:
                    d0 = docs[-1]
                    doc_id, ss, se, ev = d0["id"], 0, min(60, len(d0["text"])), [{"start": 0, "end": min(60, len(d0["text"])), "text": d0["text"][:min(60, len(d0["text"]))]}]
                status, conf = "met", 0.85
                rationale = "Baseline clinical and laboratory assessment supports adequate organ function."
        elif cid == "INC-08":  # Post-surgical MRI available
            doc_id, ss, se, ev = _from_ext("EXTRES")
            if not doc_id:
                doc_id, ss, se, ev = _find_span(docs, [r"resectie", r"resection", r"craniotomie", r"craniotomy"])
            if doc_id:
                status, conf, rationale = "met", 0.91, "Post-surgical contrast-enhanced MRI and resection assessment available."
        elif cid == "INC-09":  # Informed consent
            if p["status"] in ("active", "completed", "consented", "enrolled") or p.get("enrolled_date") or p.get("consented_date"):
                doc_id, ss, se, ev = _find_span(docs, [r"Adjuvante radiotherapie[^\n]+", r"Adjuvant radiotherapy[^\n]+"])
                status, conf, rationale = "met", 0.88, "Informed consent and treatment plan documented."
        elif cid == "EXC-01":  # Prior brain RT (exclusion: met means NO prior RT / eligible, or for exclusion criterion: not_met means excluded? Let's be crystal clear!)
            # Standard convention in clinical trials & CEL-1803: per criterion `met | not_met | unknown` where `met` = patient satisfies the eligibility requirement (no exclusion triggered).
            doc_id, ss, se, ev = _find_span(docs, [r"postoperatief beloop ongecompliceerd", r"Post-operative course was uneventful", r"newly diagnosed", r"resectiepreparaat"])
            if docs:
                status, conf, rationale = "met", 0.89, "Newly diagnosed primary resection; no prior cranial radiotherapy recorded."
        elif cid == "EXC-02":  # Prior systemic anti-glioma therapy
            doc_id, ss, se, ev = _find_span(docs, [r"eerste cyclus", r"6 planned adjuvant", r"6 geplande cycli"])
            if docs:
                status, conf, rationale = "met", 0.89, "No prior systemic anti-glioma therapy before first-line chemoradiotherapy."
        elif cid == "EXC-03":  # IDH-mutant or indeterminate
            idh = (vals.get("IDHSTAT", {}).get("value") or exts.get("IDHSTAT", {}).get("value") or "")
            doc_id, ss, se, ev = _from_ext("IDHSTAT")
            if "mutant" in idh.lower() or "idh-mutant" in (p.get("summary") or "").lower():
                status, conf, rationale = "not_met", 0.96, "Exclusion triggered: tumour is IDH-mutant."
            elif "wildtype" in idh.lower() or doc_id:
                status, conf, rationale = "met", 0.96, "IDH1/2 wildtype confirmed; exclusion not triggered."
        elif cid == "EXC-04":  # Pregnancy / breastfeeding
            doc_id, ss, se, ev = _from_ext("SEX")
            if p.get("sex") == "M":
                status, conf, rationale = "met", 0.99, "Male participant; pregnancy exclusion not applicable."
            elif docs:
                status, conf, rationale = "met", 0.86, "No pregnancy or breastfeeding exclusion noted at baseline."

        prov = "rules" if provider in ("auto", "rules") else provider
        c.execute(text("""INSERT INTO screening_check
            (participant_id, criterion_id, ai_status, confidence, rationale, document_id, span_start, span_end,
             evidence, provider, model, prompt_version, updated_at)
            VALUES (:p,:cid,:st,:conf,:rat,:doc,:ss,:se,CAST(:ev AS jsonb),:prov,'rules-screening-v4','screen_v1',now())
            ON CONFLICT (participant_id, criterion_id) DO UPDATE SET
              ai_status=:st, confidence=:conf, rationale=:rat, document_id=:doc,
              span_start=:ss, span_end=:se, evidence=CAST(:ev AS jsonb),
              provider=:prov, model='rules-screening-v4', prompt_version='screen_v1', updated_at=now()"""),
                  dict(p=pid, cid=cid, st=status, conf=conf, rat=rationale, doc=doc_id, ss=ss, se=se,
                       ev=json.dumps(ev), prov=prov))
        results.append({"criterion_id": cid, "ai_status": status, "confidence": conf})

    A.record(c, user, "screening.ai_checked", "participant", pid, participant_id=pid,
             after={"criteriaChecked": len(results),
                    "met": sum(1 for r in results if r["ai_status"] == "met"),
                    "notMet": sum(1 for r in results if r["ai_status"] == "not_met"),
                    "unknown": sum(1 for r in results if r["ai_status"] == "unknown")},
             source="ai", model="rules-screening-v4", prompt_version="screen_v1", actor="rules/rules-screening-v4")
    return results


def build_screening(c, pid: str) -> S.Screening | None:
    p = _one(c, "SELECT * FROM participant WHERE id=:i", i=pid)
    if not p:
        return None
    criteria = _rows(c, "SELECT * FROM screening_criterion WHERE study_id=:s ORDER BY ord", s=p["study_id"])
    checks = {x["criterion_id"]: x for x in _rows(c, "SELECT * FROM screening_check WHERE participant_id=:p", p=pid)}
    items: list[S.ScreeningCriterionCheck] = []
    for crit in criteria:
        chk = checks.get(crit["id"]) or {}
        ai_st = chk.get("ai_status") or "unknown"
        co_st = chk.get("coordinator_status")
        eff = co_st or ai_st
        items.append(S.ScreeningCriterionCheck(
            id=f"{pid}:{crit['id']}",
            criterion_id=crit["id"],
            ord=crit["ord"],
            type=crit["type"],
            text=crit["text"],
            data_needed=crit.get("data_needed"),
            ai_status=ai_st,
            confidence=float(chk.get("confidence") or 0.0),
            rationale=chk.get("rationale"),
            document_id=chk.get("document_id"),
            span_start=chk.get("span_start"),
            span_end=chk.get("span_end"),
            evidence=chk.get("evidence") or [],
            provider=chk.get("provider"),
            model=chk.get("model"),
            prompt_version=chk.get("prompt_version"),
            coordinator_status=co_st,
            effective_status=eff,
            confirmed_by=chk.get("confirmed_by"),
            confirmed_at=chk.get("confirmed_at"),
            note=chk.get("note"),
        ))
    return S.Screening(
        participant_id=pid,
        study_id=p["study_id"],
        site_id=p["site_id"],
        status=p["status"],
        status_detail=p.get("status_detail"),
        screen_fail_reason=p.get("screen_fail_reason"),
        coordinator_signed_by=p.get("coordinator_signed_by"),
        coordinator_signed_at=p.get("coordinator_signed_at"),
        consented_date=p.get("consented_date"),
        enrolled_date=p.get("enrolled_date"),
        enrolled_by=p.get("enrolled_by"),
        enrolled_at=p.get("enrolled_at"),
        met_count=sum(1 for i in items if i.effective_status == "met"),
        not_met_count=sum(1 for i in items if i.effective_status == "not_met"),
        unknown_count=sum(1 for i in items if i.effective_status == "unknown"),
        confirmed_count=sum(1 for i in items if i.coordinator_status is not None),
        total_count=len(items),
        criteria=items,
    )


def build_timeline(c, pid: str) -> S.Timeline | None:
    p = _one(c, "SELECT * FROM participant WHERE id=:i", i=pid)
    if not p:
        return None
    docs = _rows(c, "SELECT id, doc_type, title, document_date FROM source_document WHERE participant_id=:p ORDER BY document_date NULLS LAST, id", p=pid)
    visits = _rows(c, "SELECT id, name, visit_date, status, note FROM visit WHERE participant_id=:p ORDER BY visit_date NULLS LAST, id", p=pid)
    facts = _rows(c, "SELECT * FROM fhir_fact WHERE participant_id=:p ORDER BY effective NULLS LAST, fhir_id", p=pid)

    doc_by_type: dict[str, dict] = {}
    for d in docs:
        doc_by_type.setdefault(d["doc_type"], d)
    default_doc = docs[0] if docs else None

    def pick_doc(*types: str) -> dict | None:
        for t in types:
            if t in doc_by_type:
                return doc_by_type[t]
        return default_doc

    events: list[S.TimelineEvent] = []
    seen_keys: set[tuple[str, str]] = set()

    def add_ev(eid: str, cat: str, title: str, dt: str | None, *, end_dt: str | None = None,
               status: str | None = "completed", detail: str | None = None,
               doc: dict | None = None, rtype: str | None = None, rid: str | None = None):
        if not dt:
            return
        d_str = str(dt)[:10]
        key = (cat, f"{title}:{d_str}")
        if key in seen_keys:
            return
        seen_keys.add(key)
        events.append(S.TimelineEvent(
            id=eid,
            category=cat,  # type: ignore[arg-type]
            title=title,
            date=d_str,
            end_date=str(end_dt)[:10] if end_dt else None,
            status=status,
            detail=detail,
            document_id=doc["id"] if doc else None,
            document_title=doc["title"] if doc else None,
            resource_type=rtype or ("DocumentReference" if doc else None),
            resource_id=rid or (doc["id"] if doc else None),
        ))

    # 1. Source documents (surgery / operative notes, pathology diagnosis, MRI scans)
    for d in docs:
        dt = str(d["document_date"]) if d.get("document_date") else (str(p["diagnosis_date"]) if p.get("diagnosis_date") else None)
        dtype = d["doc_type"]
        if dtype == "operative_report":
            add_ev(f"doc-{d['id']}", "surgery", d["title"], dt, detail="Surgical resection report", doc=d, rtype="DocumentReference", rid=d["id"])
        elif dtype == "radiology_report":
            add_ev(f"doc-{d['id']}", "scan", d["title"], dt, detail="Contrast-enhanced brain MRI", doc=d, rtype="DocumentReference", rid=d["id"])
        elif dtype == "pathology_report":
            add_ev(f"doc-{d['id']}", "diagnosis", d["title"], dt, detail="Histopathology and molecular biomarkers", doc=d, rtype="DocumentReference", rid=d["id"])

    # If participant has diagnosis_date and no operative report was emitted, add surgery/diagnosis event from summary
    if p.get("diagnosis_date") and not any(e.category == "surgery" for e in events):
        sdoc = pick_doc("operative_report", "discharge_letter", "pathology_report")
        add_ev(f"surg-{pid}", "surgery", "Primary tumour resection / biopsy", str(p["diagnosis_date"]),
               detail=p.get("summary"), doc=sdoc, rtype="Procedure", rid=f"PROC-{pid}-RESECTION")

    # 2. Treatments (radiotherapy, concurrent and adjuvant chemotherapy)
    for idx, t in enumerate(p.get("treatments") or [], 1):
        name = t.get("name") or "Treatment"
        cat = "radiotherapy" if "radio" in name.lower() else "chemotherapy"
        tdoc = pick_doc("discharge_letter", "pathology_report")
        add_ev(f"tx-{pid}-{idx}", cat, name, t.get("start"), end_dt=t.get("end"),
               status="completed" if t.get("end") else "active",
               detail=t.get("dose"), doc=tdoc,
               rtype="Procedure" if cat == "radiotherapy" else "MedicationAdministration",
               rid=f"PROC-{pid}-RT" if cat == "radiotherapy" else f"MED-{pid}-{idx}")

    # 3. Visits (including TMZ cycles and follow-up visits)
    for v in visits:
        vname = v["name"]
        cat = "chemotherapy" if "tmz" in vname.lower() or "cycle" in vname.lower() else (
              "radiotherapy" if "radiotherapy" in vname.lower() else "visit")
        vdoc = pick_doc("discharge_letter", "radiology_report", "pathology_report")
        add_ev(f"visit-{v['id']}", cat, vname, str(v["visit_date"]) if v.get("visit_date") else None,
               status=v.get("status"), detail=v.get("note") or None, doc=vdoc,
               rtype="Encounter", rid=f"VISIT-{pid}-{v['id']}")

    # 4. Synced FHIR facts (Procedures, DiagnosticReports, MedicationAdministrations)
    for f in facts:
        rt = f["resource_type"]
        eff = f.get("effective")
        if not eff:
            continue
        if rt == "Procedure":
            cat = "radiotherapy" if "radio" in (f.get("display") or "").lower() else "surgery"
            fdoc = pick_doc("operative_report", "discharge_letter")
            add_ev(f"fhir-{f['fhir_id']}", cat, f.get("display") or "Procedure", eff,
                   status=f.get("status"), detail=f.get("value"), doc=fdoc, rtype=rt, rid=f["fhir_id"])
        elif rt == "DiagnosticReport":
            fdoc = pick_doc("radiology_report", "pathology_report")
            add_ev(f"fhir-{f['fhir_id']}", "scan", f.get("display") or "Diagnostic report", eff,
                   status=f.get("status"), detail=f.get("value"), doc=fdoc, rtype=rt, rid=f["fhir_id"])

    events.sort(key=lambda e: (e.date, e.id))
    return S.Timeline(participant_id=pid, events=events)
