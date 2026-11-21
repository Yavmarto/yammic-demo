"""CDISC ODM 1.3.2 snapshot of verified eCRF data, with an AuditRecord on every ItemData."""
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from sqlalchemy import text

NS = "http://www.cdisc.org/ns/odm/v1.3"
ET.register_namespace("", NS)
DTYPE = {"integer": "integer", "number": "float", "date": "date"}
MDV, EVENT, FORM = "MDV.1", "SE.BASELINE", "F.ECRF_BASELINE"


def _e(parent, tag, **attrs):
    return ET.SubElement(parent, f"{{{NS}}}{tag}", {k: str(v) for k, v in attrs.items() if v is not None})


def _iso(ts):
    return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S%z").replace("+0000", "+00:00") if ts else None


def _oid(prefix, s):
    return f"{prefix}.{''.join(ch if ch.isalnum() else '_' for ch in s)}"


def build_odm(c, study_id: str) -> bytes | None:
    q = lambda sql, **p: [dict(x) for x in c.execute(text(sql), p).mappings()]
    st = (q("SELECT * FROM study WHERE id=:i", i=study_id) or [None])[0]
    if not st:
        return None
    fields = q("SELECT * FROM ecrf_field WHERE study_id=:s ORDER BY ord", s=study_id)
    sites = q("SELECT * FROM site WHERE study_id=:s ORDER BY id", s=study_id)
    vals = q("""SELECT v.*, p.site_id, e.provider, e.model, e.prompt_version, e.confidence, e.value AS proposed,
          (SELECT d.reason FROM review_decision d WHERE d.extraction_id=v.source_extraction_id ORDER BY d.id DESC LIMIT 1) AS reason,
          (SELECT d.decision FROM review_decision d WHERE d.extraction_id=v.source_extraction_id ORDER BY d.id DESC LIMIT 1) AS decision
        FROM ecrf_value v JOIN participant p ON p.id=v.participant_id
        LEFT JOIN extraction e ON e.id=v.source_extraction_id
        WHERE p.study_id=:s ORDER BY v.participant_id, v.field_id""", s=study_id)
    now = datetime.now(UTC)
    root = ET.Element(f"{{{NS}}}ODM", {
        "FileType": "Snapshot", "FileOID": f"ODM.{study_id}.{now:%Y%m%d%H%M%S}", "CreationDateTime": _iso(now),
        "ODMVersion": "1.3.2", "Granularity": "All", "Originator": "Yamicc demo platform (synthetic data)",
        "SourceSystem": "Yamicc demo backend", "SourceSystemVersion": "0.1.0",
        "Description": f"Verified eCRF data for {st['short_name']}. Synthetic data, not for clinical use."})
    # --- metadata ---
    s = _e(root, "Study", OID=study_id)
    g = _e(s, "GlobalVariables")
    _e(g, "StudyName").text = st["short_name"]
    _e(g, "StudyDescription").text = st["title"]
    _e(g, "ProtocolName").text = st["short_name"]
    m = _e(s, "MetaDataVersion", OID=MDV, Name="eCRF baseline v1")
    se = _e(m, "StudyEventDef", OID=EVENT, Name="Baseline", Repeating="No", Type="Scheduled")
    _e(se, "FormRef", FormOID=FORM, Mandatory="Yes", OrderNumber=1)
    domains: dict[str, list] = {}
    for f in fields:
        domains.setdefault((f["cdisc"] or {}).get("cdiscDomain") or "XX", []).append(f)
    fd = _e(m, "FormDef", OID=FORM, Name=fields[0]["form_id"] if fields else "eCRF", Repeating="No")
    for i, d in enumerate(domains, 1):
        _e(fd, "ItemGroupRef", ItemGroupOID=f"IG.{d}", Mandatory="Yes", OrderNumber=i)
    for d, fs in domains.items():
        ig = _e(m, "ItemGroupDef", OID=f"IG.{d}", Name=d, Repeating="No", Domain=d)
        for i, f in enumerate(fs, 1):
            _e(ig, "ItemRef", ItemOID=_oid("IT", f["id"]), Mandatory="Yes" if f["required"] else "No", OrderNumber=i)
    for f in fields:
        cd = f["cdisc"] or {}
        it = _e(m, "ItemDef", OID=_oid("IT", f["id"]), Name=f["id"], DataType=DTYPE.get(f["value_type"], "text"),
                SDSVarName=(cd.get("cdiscVariable") or "")[:8] or None)
        _e(_e(it, "Description"), "TranslatedText").set("{http://www.w3.org/XML/1998/namespace}lang", "en")
        it.find(f"{{{NS}}}Description/{{{NS}}}TranslatedText").text = f["label"]
        if cd.get("cdiscDomain"):
            _e(it, "Alias", Context="SDTM", Name=f"{cd['cdiscDomain']}.{cd.get('cdiscVariable')}")
    # --- admin data: users and sites referenced by the audit records ---
    ad = _e(root, "AdminData", StudyOID=study_id)
    names = {u["username"]: u["display_name"] for u in q("SELECT username, display_name FROM app_user")}
    used = sorted({v["verified_by"] for v in vals} | {v["sdv_by"] for v in vals if v["sdv_by"]})
    for u in used:
        us = _e(ad, "User", OID=_oid("USR", u))
        _e(us, "LoginName").text = u
        _e(us, "DisplayName").text = names.get(u, u)
    for si in sites:
        lo = _e(ad, "Location", OID=_oid("LOC", si["id"]), Name=si["name"])
        _e(lo, "MetaDataVersionRef", StudyOID=study_id, MetaDataVersionOID=MDV, EffectiveDate=now.strftime("%Y-%m-%d"))
    # --- clinical data ---
    cd_ = _e(root, "ClinicalData", StudyOID=study_id, MetaDataVersionOID=MDV)
    by_pid: dict[str, list] = {}
    for v in vals:
        by_pid.setdefault(v["participant_id"], []).append(v)
    dom_of = {f["id"]: (f["cdisc"] or {}).get("cdiscDomain") or "XX" for f in fields}
    for pid, vs in by_pid.items():
        sd = _e(cd_, "SubjectData", SubjectKey=pid)
        _e(sd, "SiteRef", LocationOID=_oid("LOC", vs[0]["site_id"]))
        sed = _e(sd, "StudyEventData", StudyEventOID=EVENT)
        fdd = _e(sed, "FormData", FormOID=FORM)
        groups: dict[str, ET.Element] = {}
        for v in vs:
            dom = dom_of[v["field_id"]]
            if dom not in groups:
                groups[dom] = _e(fdd, "ItemGroupData", ItemGroupOID=f"IG.{dom}")
            ig = groups[dom]
            idt = _e(ig, "ItemData", ItemOID=_oid("IT", v["field_id"]), Value=v["value"])
            ar = _e(idt, "AuditRecord", EditPoint="DataManagement", UsedImputationMethod="No")
            _e(ar, "UserRef", UserOID=_oid("USR", v["verified_by"]))
            _e(ar, "LocationRef", LocationOID=_oid("LOC", v["site_id"]))
            _e(ar, "DateTimeStamp").text = _iso(v["verified_at"])
            if v["decision"] == "correct" or v["reason"]:
                _e(ar, "ReasonForChange").text = (v["reason"] or f"Corrected from AI proposal {v['proposed']!r}")[:1000]
            if v["source_extraction_id"]:
                _e(ar, "SourceID").text = v["source_extraction_id"]
                origin = f"{v['provider']}/{v['model']} prompt {v['prompt_version']}, confidence {v['confidence']:.2f}"
                an = _e(idt, "Annotation", SeqNum=1)
                _e(an, "Comment", SponsorOrSite="Sponsor").text = (
                    f"Proposed by AI ({origin}); human decision: {v['decision'] or 'accept'} by {v['verified_by']}.")
            if v["sdv_at"]:
                ar2 = _e(idt, "Annotation", SeqNum=2)
                _e(ar2, "Comment", SponsorOrSite="Sponsor").text = (
                    f"Source data verified by {v['sdv_by']} at {_iso(v['sdv_at'])}.")
    ET.indent(root)
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")
