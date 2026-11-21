"""Integration endpoints. No route returns an identifier: pseudonym_map is write-only from the API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from ..db import engine
from ..schemas import M
from ..security import current_user, require
from . import fhir, sync

r = APIRouter(tags=["integrations"])


class SyncRunOut(M):
    id: int
    started_at: str
    finished_at: str | None
    duration_ms: int | None
    status: str
    mode: str
    since: str | None
    cursor: str | None
    triggered_by: str
    counts: dict
    errors: list


def get_source():  # tests override this
    return fhir.HttpSource()


def _out(x: dict) -> SyncRunOut:
    return SyncRunOut(**{**x, "started_at": x["started_at"].isoformat(),
                         "finished_at": x["finished_at"].isoformat() if x["finished_at"] else None})


@r.get("/integrations")
def integrations(user=Depends(current_user)):
    """Connection status, probed live from the FHIR server's /metadata."""
    src = get_source()
    try:
        meta, state, error = src.metadata(), "connected", None
    except fhir.FhirError as e:
        meta, state, error = {}, "unreachable", str(e)[:200]
    with engine.connect() as c:
        last = sync.status_of(c)
        n = c.execute(text("SELECT count(*) FROM pseudonym_map")).scalar()
    return [{"id": "fhir", "name": "Hospital EHR (FHIR R4)", "kind": "fhir", "baseUrl": getattr(src, "base", None),
             "status": state, "error": error, **meta, "pseudonymisedPatients": n,
             "lastSync": _out(last).model_dump(by_alias=True) if last else None}]


@r.post("/integrations/fhir/sync", response_model=SyncRunOut)
def fhir_sync(full: bool = Query(False, description="Ignore the incremental cursor and pull everything"),
              user=Depends(require("nurse", "pi", "service"))):
    """Pull from the hospital FHIR server, pseudonymise, store, and queue AI extraction for new documents."""
    return _out(sync.run_sync(user, get_source(), full=full))


@r.get("/integrations/fhir/runs", response_model=list[SyncRunOut])
def fhir_runs(limit: int = Query(20, ge=1, le=200), user=Depends(current_user)):
    with engine.connect() as c:
        rows = c.execute(text("SELECT * FROM fhir_sync_run ORDER BY id DESC LIMIT :l"), {"l": limit}).mappings()
        return [_out(dict(x)) for x in rows]
