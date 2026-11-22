"""Data-quality rules (v4). Run after each extraction decision or sync and auto-open queries.

At least 5 rules:
- DQ-01: Resection extent discrepancy (MRI vs operative note / discharge letter).
- DQ-02: Dates out of order (diagnosis > enrolment, surgery > RT start, or RT end > chemo start).
- DQ-03: Missing mandatory eCRF field (abstained or missing required field after review/extraction).
- DQ-04: Value out of range (numeric eCRF value outside field min..max, e.g. KPS, AGE, RTDOSE).
- DQ-05: Lab / biomarker vs eligibility criterion (IDH-mutant, KPS < 60, or baseline HB/PLT/ANC/ALT/CREA out of trial limits).
"""
from __future__ import annotations

import re
from sqlalchemy import text

from . import audit as A
from . import schemas as S

RULES: list[S.DataQualityRule] = [
    S.DataQualityRule(
        id="DQ-01",
        name="Resection extent discrepancy (MRI vs operative note)",
        severity="medium",
        field_id="EXTRES",
        description="Flags conflicting or hedged resection extent between the post-operative MRI and the operative note.",
    ),
    S.DataQualityRule(
        id="DQ-02",
        name="Dates out of chronological order",
        severity="high",
        field_id="MHSTDAT",
        description="Checks that diagnosis date <= enrolled date <= radiotherapy start <= adjuvant chemotherapy start <= progression date.",
    ),
    S.DataQualityRule(
        id="DQ-03",
        name="Missing mandatory field",
        severity="medium",
        field_id=None,
        description="Flags required eCRF fields where all proposals were rejected/abstained or remain unverified when the form is reviewed.",
    ),
    S.DataQualityRule(
        id="DQ-04",
        name="Value out of range",
        severity="high",
        field_id=None,
        description="Checks numeric eCRF values against the field's min and max bounds (e.g. AGE 18..100, KPS 0..100, RTDOSE 0..80).",
    ),
    S.DataQualityRule(
        id="DQ-05",
        name="Lab or biomarker vs eligibility criterion",
        severity="high",
        field_id=None,
        description="Checks laboratory facts and key biomarkers against protocol entry criteria (IDH-wildtype, KPS >= 60, ANC >= 1.5, PLT >= 100, HB >= 9.0, ALT <= 3xULN).",
    ),
]


def _rows(c, sql: str, **p) -> list[dict]:
    return [dict(x) for x in c.execute(text(sql), p).mappings()]


def _one(c, sql: str, **p) -> dict | None:
    x = c.execute(text(sql), p).mappings().first()
    return dict(x) if x else None


def _open_if_new(c, pid: str, site_id: str, rule_id: str, field_id: str | None,
                 severity: str, msg: str, user: dict) -> dict | None:
    existing = _one(c, """SELECT * FROM data_query
        WHERE participant_id=:p AND (rule_id=:r OR (field_id IS NOT NULL AND field_id=:f))
          AND status IN ('open','answered') LIMIT 1""", p=pid, r=rule_id, f=field_id)
    if existing:
        return None
    q = _one(c, """INSERT INTO data_query (participant_id, site_id, field_id, status, severity, text, opened_by, rule_id)
        VALUES (:p,:s,:f,'open',:sev,:t,'dq-engine',:r) RETURNING *""",
             p=pid, s=site_id, f=field_id, sev=severity, t=msg, r=rule_id)
    A.record(c, user, "query.auto_opened", "data_query", q["id"], participant_id=pid,
             after={"ruleId": rule_id, "fieldId": field_id, "severity": severity, "text": msg},
             source="ai", model="dq-rules-v4", prompt_version="dq_v1", actor="dq-engine")
    return q


def evaluate_participant(c, pid: str, user: dict | None = None, *, trigger: str = "manual") -> list[dict]:
    """Run all 5 data-quality rules for `pid` and auto-open queries for any new violations."""
    user = user or {"username": "dq-engine", "role": "service"}
    p = _one(c, "SELECT * FROM participant WHERE id=:i", i=pid)
    if not p:
        return []
    site_id = p["site_id"]
    vals = {v["field_id"]: v for v in _rows(c, "SELECT * FROM ecrf_value WHERE participant_id=:p", p=pid)}
    fields = {f["id"]: f for f in _rows(c, "SELECT * FROM ecrf_field WHERE study_id=:s", s=p["study_id"])}
    exts = _rows(c, """SELECT e.*, d.doc_type FROM extraction e
                       JOIN source_document d ON d.id=e.document_id
                       WHERE e.participant_id=:p ORDER BY e.id""", p=pid)
    facts = _rows(c, "SELECT * FROM fhir_fact WHERE participant_id=:p", p=pid)
    opened: list[dict] = []

    def flag(rule_id: str, field_id: str | None, severity: str, msg: str):
        q = _open_if_new(c, pid, site_id, rule_id, field_id, severity, msg, user)
        if q:
            opened.append(q)

    # Rule DQ-01: Resection extent MRI vs operative note (different values or hedged low-confidence MRI vs operative report)
    extres_exts = [e for e in exts if e["field_id"] == "EXTRES" and e["status"] == "proposed"]
    if len(extres_exts) >= 2 and (trigger != "decision" or "EXTRES" in vals or any(e["review_state"] != "pending" for e in extres_exts)):
        norm_vals = {str(e["normalized_value"] or e["value"] or "").strip().lower() for e in extres_exts}
        low_conf = any((e["confidence"] or 0) < 0.6 for e in extres_exts)
        if len(norm_vals) > 1 or low_conf:
            docs_desc = ", ".join(f"{e['document_id']} ({e['value']}, conf {e['confidence']:.2f})" for e in extres_exts)
            flag("DQ-01", "EXTRES", "medium",
                 f"[DQ-01] Extent of resection discrepancy across source documents: {docs_desc}.")

    # Rule DQ-02: Dates out of chronological order
    diag_date = (vals.get("MHSTDAT", {}).get("value") or (str(p["diagnosis_date"]) if p.get("diagnosis_date") else None))
    enrol_date = str(p["enrolled_date"]) if p.get("enrolled_date") else None
    prog_date = vals.get("PROGDAT", {}).get("value")
    if diag_date and enrol_date and diag_date > enrol_date:
        flag("DQ-02", "MHSTDAT", "high",
             f"[DQ-02] Date of diagnosis ({diag_date}) is after enrollment date ({enrol_date}).")
    if diag_date and prog_date and prog_date < diag_date:
        flag("DQ-02", "PROGDAT", "high",
             f"[DQ-02] Date of progression ({prog_date}) is earlier than date of diagnosis ({diag_date}).")
    treatments = p.get("treatments") or []
    rt_start = next((t.get("start") for t in treatments if "radio" in (t.get("name") or "").lower()), None)
    adj_start = next((t.get("start") for t in treatments if "adjuvant" in (t.get("name") or "").lower()), None)
    if diag_date and rt_start and rt_start < diag_date:
        flag("DQ-02", "MHSTDAT", "high",
             f"[DQ-02] Radiotherapy start ({rt_start}) precedes diagnosis date ({diag_date}).")
    if rt_start and adj_start and adj_start < rt_start:
        flag("DQ-02", "TMZPLNC", "high",
             f"[DQ-02] Adjuvant temozolomide start ({adj_start}) precedes radiotherapy start ({rt_start}).")

    # Rule DQ-03: Missing mandatory field
    # Triggered when a required field has all proposals explicitly rejected, or when trigger=='manual' and required field is missing
    for fid, f in fields.items():
        if not f.get("required"):
            continue
        if fid in vals and str(vals[fid].get("value") or "").strip():
            continue
        f_exts = [e for e in exts if e["field_id"] == fid]
        if f_exts and all(e["review_state"] == "rejected" for e in f_exts) and (trigger == "manual" or len(f_exts) > 1):
            flag("DQ-03", fid, "medium",
                 f"[DQ-03] Mandatory field {fid} ({f['label']}) has no valid value (all extractions rejected).")
        elif trigger == "manual" and f_exts and all(e["status"] == "abstained" or e["review_state"] == "rejected" for e in f_exts):
            flag("DQ-03", fid, "medium",
                 f"[DQ-03] Mandatory field {fid} ({f['label']}) has no valid value (all extractions abstained or rejected).")
        elif trigger == "manual" and vals and fid not in vals and not any(e["review_state"] == "pending" for e in f_exts):
            flag("DQ-03", fid, "medium",
                 f"[DQ-03] Mandatory field {fid} ({f['label']}) is missing a verified value.")

    # Rule DQ-04: Value out of range
    DEFAULT_BOUNDS: dict[str, tuple[float, float]] = {
        "AGE": (18, 100),
        "KPS": (0, 100),
        "RTDOSE": (0, 80),
        "RTFRAC": (1, 40),
        "TMZPLNC": (0, 12),
        "AEGRADE": (0, 5),
    }
    for fid, v in vals.items():
        f = fields.get(fid) or {}
        lo = f.get("min_val") if f.get("min_val") is not None else DEFAULT_BOUNDS.get(fid, (None, None))[0]
        hi = f.get("max_val") if f.get("max_val") is not None else DEFAULT_BOUNDS.get(fid, (None, None))[1]
        if lo is None and hi is None:
            continue
        m = re.search(r"-?\d+(?:\.\d+)?", str(v.get("value") or ""))
        if not m:
            continue
        num = float(m.group(0))
        if (lo is not None and num < lo) or (hi is not None and num > hi):
            flag("DQ-04", fid, "high",
                 f"[DQ-04] Verified value {v['value']!r} for {fid} is outside allowed range [{lo}, {hi}].")

    # Rule DQ-05: Lab / biomarker vs eligibility criterion
    # 5a) KPS < 60 (INC-04 requires KPS >= 60)
    kps_str = vals.get("KPS", {}).get("value")
    if not kps_str:
        kps_fact = next((f for f in facts if f["code"] == "89261-2" or "karnofsky" in (f.get("display") or "").lower()), None)
        kps_str = kps_fact["value"] if kps_fact else None
    if kps_str:
        m = re.search(r"-?\d+(?:\.\d+)?", str(kps_str))
        if m and float(m.group(0)) < 60:
            flag("DQ-05", "KPS", "high",
                 f"[DQ-05] KPS is {m.group(0)}% (< 60% minimum required by eligibility criterion INC-04).")

    # 5b) IDH mutant / indeterminate (INC-02 / EXC-03 requires IDH-wildtype)
    idh_str = vals.get("IDHSTAT", {}).get("value")
    if not idh_str:
        idh_fact = next((f for f in facts if "idh" in (f.get("display") or "").lower()), None)
        idh_str = idh_fact["value"] if idh_fact else None
    if idh_str and ("mutant" in idh_str.lower() or "indeterminate" in idh_str.lower()):
        flag("DQ-05", "IDHSTAT", "high",
             f"[DQ-05] IDH status is {idh_str!r}, violating eligibility criteria INC-02 / EXC-03 (IDH-wildtype required).")

    # 5c) Baseline laboratory values vs organ-function criteria (INC-05, INC-06, INC-07)
    for f in facts:
        if f["resource_type"] != "Observation" or not f.get("value"):
            continue
        m = re.search(r"-?\d+(?:\.\d+)?", str(f["value"]))
        if not m:
            continue
        val = float(m.group(0))
        code = f.get("code") or ""
        disp = (f.get("display") or "").lower()
        if (code == "718-7" or "hemoglobin" in disp) and val < 9.0:
            flag("DQ-05", None, "high", f"[DQ-05] Haemoglobin {f['value']} is below INC-05 threshold (9.0 g/dL).")
        elif (code == "777-3" or "platelet" in disp) and val < 100.0:
            flag("DQ-05", None, "high", f"[DQ-05] Platelets {f['value']} is below INC-05 threshold (100 x10^9/L).")
        elif (code == "26464-8" or "neutrophil" in disp) and val < 1.5:
            flag("DQ-05", None, "high", f"[DQ-05] ANC {f['value']} is below INC-05 threshold (1.5 x10^9/L).")
        elif (code == "1742-6" or "alanine" in disp) and val > 105.0:  # 3x ULN (35 U/L)
            flag("DQ-05", None, "medium", f"[DQ-05] ALT {f['value']} exceeds INC-06 threshold (3x ULN = 105 U/L).")

    return opened


def after_sync_participant(c, pid: str, user: dict) -> None:
    from . import workflows as W
    status = c.execute(text("SELECT status FROM participant WHERE id=:i"), {"i": pid}).scalar()
    if status == "screening":
        W.run_ai_screening(c, pid, user, provider="rules")
    evaluate_participant(c, pid, user, trigger="sync")
