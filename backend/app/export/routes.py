"""Standards exports. Every call is audited (hash-chained)."""
import json

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text

from .. import audit as A
from ..db import engine
from ..ingest import fhir
from ..ingest import routes as ingest_routes
from ..security import require
from . import fhir_export, odm

r = APIRouter(tags=["export"])
READERS = require("pi", "monitor", "service")


@r.get("/studies/{study_id}/export/odm", response_class=Response,
       responses={200: {"content": {"application/xml": {}}}})
def export_odm(study_id: str, user=Depends(READERS)):
    """CDISC ODM 1.3.2 snapshot: eCRF metadata plus every verified value with an AuditRecord."""
    with engine.begin() as c:
        xml = odm.build_odm(c, study_id)
        if xml is None:
            raise HTTPException(404, "Study not found")
        n = c.execute(text("""SELECT count(*) FROM ecrf_value v JOIN participant p ON p.id=v.participant_id
                              WHERE p.study_id=:s"""), {"s": study_id}).scalar()
        A.record(c, user, "export.odm", "study", study_id, after={"format": "CDISC ODM 1.3.2", "verifiedValues": n,
                                                                  "bytes": len(xml)})
    return Response(xml, media_type="application/xml",
                    headers={"Content-Disposition": f'attachment; filename="{study_id}-odm-1.3.2.xml"'})


def _bundle(c, pid):
    b = fhir_export.build_bundle(c, pid)
    if b is None:
        raise HTTPException(404, "Participant not found")
    return b


@r.get("/participants/{pid}/export/fhir", response_class=Response,
       responses={200: {"content": {"application/fhir+json": {}}}})
def export_fhir(pid: str, user=Depends(READERS)):
    """FHIR R4 bundle: QuestionnaireResponse + Provenance (AI vs human agents) + AuditEvents."""
    with engine.begin() as c:
        b = _bundle(c, pid)
        A.record(c, user, "export.fhir", "participant", pid, participant_id=pid,
                 after={"resources": len(b["entry"]), "format": "FHIR R4 collection"})
    return Response(json.dumps(b), media_type="application/fhir+json")


@r.post("/participants/{pid}/export/fhir/push")
def push_fhir(pid: str, user=Depends(require("pi", "monitor"))):
    """Validate the bundle on the FHIR server, then write it back as one transaction."""
    src = ingest_routes.get_source()
    with engine.connect() as c:
        b = _bundle(c, pid)
    if not any(e["resource"]["resourceType"] == "QuestionnaireResponse" and e["resource"]["item"] for e in b["entry"]):
        raise HTTPException(409, "No verified eCRF values to export yet")
    try:
        bad = []
        for e in b["entry"]:
            out = src.validate(e["resource"])
            bad += [f"{e['fullUrl']}: {i.get('diagnostics') or i.get('details', {}).get('text')}"
                    for i in out.get("issue", []) if i["severity"] in ("error", "fatal")]
        if bad:
            raise HTTPException(422, {"message": "FHIR server rejected the bundle", "issues": bad[:10]})
        res = src.transaction(fhir_export.to_transaction(b))
    except fhir.FhirError as e:
        raise HTTPException(502, f"FHIR server unreachable or refused the write: {e}")
    written = [x["response"]["location"] for x in res.get("entry", [])]
    with engine.begin() as c:
        A.record(c, user, "export.fhir_push", "participant", pid, participant_id=pid,
                 after={"resources": len(written), "target": getattr(src, "base", "fhir")})
    return {"pushed": len(written), "resources": written}
