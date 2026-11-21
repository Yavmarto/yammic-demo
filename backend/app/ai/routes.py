"""Read/queue endpoints owned by the AI workstream.

These are additive to the CTO contract: the extraction flow itself is
``POST /participants/{id}/extraction-runs`` + the AI service + ``/runs``. The
endpoints here expose the provider/prompt registry, the eval table, and a
convenience queue endpoint that records the requested provider on the run.

All paths are additive; no existing route changes.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from .. import schemas as S
from ..audit import record as audit_record
from ..db import engine
from ..security import current_user, require
from . import providers, registry

r = APIRouter()
RESULTS = Path(__file__).resolve().parents[2] / "eval" / "results"
PROVIDER_CHOICES = {"auto", "rules", "ollama", "claude"}


def _one(c, sql: str, **p):
    x = c.execute(text(sql), p).mappings().first()
    return dict(x) if x else None


def _must(x, what: str):
    if x is None:
        raise HTTPException(404, f"{what} not found")
    return x


@r.get("/ai/providers", tags=["ai"])
def ai_providers(user=Depends(current_user)):
    """Provider availability. `rules` is always on; `ollama` checks localhost:11434."""
    return {"providers": providers.describe(), "default": providers.resolve("auto")}


@r.get("/ai/prompts", tags=["ai"])
def ai_prompts(user=Depends(current_user)):
    """Versioned prompt files with the SHA-256 hash recorded in each run."""
    prompts = registry.all_prompts()
    active = prompts[-1] if prompts else None
    return {"prompts": [{"version": p.version, "sha256": p.sha256, "tag": p.tag,
                         "path": str(p.path.relative_to(p.path.parents[3])), "active": p == active}
                        for p in prompts]}


@r.get("/ai/runs", response_model=list[S.Run], tags=["ai"])
def ai_runs(status: str | None = None, participant_id: str | None = None,
            user=Depends(current_user)):
    """Same rows as GET /runs, exposed under /ai for the AI quality screen."""
    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT * FROM extraction_run WHERE (CAST(:s AS text) IS NULL OR status=:s) "
            "AND (CAST(:p AS text) IS NULL OR participant_id=:p) ORDER BY id DESC LIMIT 200"),
            {"s": status, "p": participant_id}).mappings().all()
        return [dict(x) for x in rows]


@r.get("/ai/eval", tags=["ai"])
def ai_eval(provider: str | None = Query(default=None), user=Depends(current_user)):
    """Latest eval harness result (precision/recall/F1/abstention per field)."""
    candidates = []
    if provider:
        candidates.append(RESULTS / f"latest-{provider}.json")
    candidates.append(RESULTS / "latest.json")
    for path in candidates:
        if path.exists():
            data = json.loads(path.read_text())
            return {"available": True, "source": path.name, "results": data}
    raise HTTPException(404, "No eval results yet. Run `make eval` (or `python -m eval.run_eval`).")


@r.post("/participants/{pid}/extract", response_model=S.Run, status_code=201, tags=["ai"])
def queue_provider_run(pid: str, body: S.RunIn | None = None,
                       provider: str = Query(default="auto"),
                       user=Depends(require("nurse", "pi", "service"))):
    """Queue a run and record the requested provider on it (`rules`, `ollama`, `auto`).

    The AI service picks the run up from `GET /runs?status=queued` and uses the
    recorded provider; `auto` means Ollama when it is up, else rules.
    """
    provider = provider.lower()
    if provider not in PROVIDER_CHOICES:
        raise HTTPException(422, f"provider must be one of {sorted(PROVIDER_CHOICES)}")
    document_id = body.document_id if body else None
    with engine.begin() as c:
        _must(_one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid), "Participant")
        if document_id:
            d = _must(_one(c, "SELECT participant_id FROM source_document WHERE id=:i", i=document_id),
                      "Document")
            if d["participant_id"] != pid:
                raise HTTPException(422, "Document belongs to another participant")
        run = _one(c, """INSERT INTO extraction_run (participant_id, document_id, status, provider, created_by)
                         VALUES (:p,:d,'queued',:prov,:u) RETURNING *""",
                   p=pid, d=document_id, prov=provider, u=user["username"])
        audit_record(c, user, "run.created", "extraction_run", run["id"], participant_id=pid,
                     after={"documentId": document_id, "provider": provider})
    return run
