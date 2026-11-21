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
    source_id: str = "hospital-1"
    source_name: str | None = None
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


def _default_get_source(url: str | None = None):
    return fhir.HttpSource(url) if url else fhir.HttpSource()


get_source = _default_get_source


def get_sources() -> list[dict]:
    """Configured FHIR sources from `FHIR_SOURCES` (or single `FHIR_BASE_URL`)."""
    if get_source is not _default_get_source:
        src = get_source()
        return [{"id": "hospital-1", "name": "Hospital 1 (FHIR R4)",
                 "url": getattr(src, "base", fhir.BASE), "siteId": "SITE-01", "client": src}]
    cfg = fhir.parse_sources()
    return [{**s, "client": get_source(s["url"])} for s in cfg]


def _out(x: dict) -> SyncRunOut:
    return SyncRunOut(**{**x, "started_at": x["started_at"].isoformat(),
                         "finished_at": x["finished_at"].isoformat() if x["finished_at"] else None})


def _probe(entry: dict, c) -> dict:
    src = entry["client"]
    try:
        meta, state, error = src.metadata(), "connected", None
    except fhir.FhirError as e:
        meta, state, error = {}, "unreachable", str(e)[:200]
    sid = entry["id"]
    last = sync.status_of(c, sid) or (sync.status_of(c) if sid == "hospital-1" else None)
    n = c.execute(text("SELECT count(*) FROM pseudonym_map WHERE source_id=:s"), {"s": sid}).scalar()
    if sid == "hospital-1" and n == 0:
        n = c.execute(text("SELECT count(*) FROM pseudonym_map")).scalar()
    return {"id": sid, "sourceId": sid, "siteId": entry.get("siteId"), "name": entry["name"], "kind": "fhir",
            "baseUrl": getattr(src, "base", entry.get("url")), "status": state, "error": error, **meta,
            "pseudonymisedPatients": n, "lastSync": _out(last).model_dump(by_alias=True) if last else None}


@r.get("/integrations")
def integrations(user=Depends(current_user)):
    """Connection status for all configured FHIR sources (`FHIR_SOURCES`), plus legacy `id='fhir'` alias."""
    sources = get_sources()
    with engine.connect() as c:
        probed = [_probe(s, c) for s in sources]
    # Keep first item aliased as id='fhir' if only 1 source or prepend legacy alias alongside named sources
    if len(probed) == 1 and probed[0]["id"] == "hospital-1":
        first = {**probed[0], "id": "fhir", "name": "Hospital EHR (FHIR R4)"}
        return [first, probed[0]]
    first_alias = {**probed[0], "id": "fhir"}
    return [first_alias, *probed]


def _after_sync_hook():
    try:
        from .. import quality
        return quality.after_sync_participant
    except Exception:
        return None


@r.post("/integrations/fhir/sync", response_model=SyncRunOut)
def fhir_sync(full: bool = Query(False, description="Ignore the incremental cursor and pull everything"),
              source_id: str | None = Query(None, alias="sourceId", description="Specific FHIR source id to sync (default: all)"),
              user=Depends(require("nurse", "pi", "service"))):
    """Pull from the hospital FHIR server(s), pseudonymise, store, queue AI extraction, and run data-quality rules."""
    sources = get_sources()
    if source_id:
        sources = [s for s in sources if s["id"] == source_id or s.get("siteId") == source_id]
        if not sources:
            from fastapi import HTTPException
            raise HTTPException(404, f"FHIR source {source_id!r} not found")
    hook = _after_sync_hook()
    runs = [sync.run_sync(user, s["client"], full=full, source_id=s["id"], source_name=s["name"],
                          default_site_id=s.get("siteId"), after_participant=hook) for s in sources]
    return _out(runs[-1])


@r.post("/integrations/fhir/{source_id}/sync", response_model=SyncRunOut)
def fhir_sync_one(source_id: str, full: bool = Query(False), user=Depends(require("nurse", "pi", "service"))):
    """Sync one specific hospital FHIR source by id."""
    return fhir_sync(full=full, source_id=source_id, user=user)


@r.get("/integrations/fhir/runs", response_model=list[SyncRunOut])
def fhir_runs(limit: int = Query(20, ge=1, le=200), source_id: str | None = Query(None, alias="sourceId"),
              user=Depends(current_user)):
    with engine.connect() as c:
        if source_id:
            rows = c.execute(text("SELECT * FROM fhir_sync_run WHERE source_id=:s ORDER BY id DESC LIMIT :l"),
                             {"s": source_id, "l": limit}).mappings()
        else:
            rows = c.execute(text("SELECT * FROM fhir_sync_run ORDER BY id DESC LIMIT :l"), {"l": limit}).mappings()
        return [_out(dict(x)) for x in rows]
