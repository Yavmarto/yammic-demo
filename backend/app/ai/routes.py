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
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import text

from .. import schemas as S
from ..audit import record as audit_record
from ..db import engine
from ..security import current_user, require
from . import protocol, providers, registry, screening
from .types import CriterionDef

r = APIRouter()
RESULTS = Path(__file__).resolve().parents[2] / "eval" / "results"
PROVIDER_CHOICES = {"auto", "rules", "ollama"}


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
            body = {"available": True, "source": path.name, "results": data,
                    "providers": _all_latest()}
            return body
    raise HTTPException(404, "No eval results yet. Run `make eval` (or `python -m eval.run_eval`).")


def _all_latest() -> dict:
    out = {}
    for path in sorted(RESULTS.glob("latest-*.json")):
        name = path.name.removeprefix("latest-").removesuffix(".json")
        try:
            out[name] = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
    return out


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


class _AiBody(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ScreeningIn(_AiBody):
    criteria: list[dict] | None = None
    documents: list[dict] | None = None


class ProtocolProposalsIn(_AiBody):
    synopsis_text: str | None = None
    study_id: str = "GBM-NL-2026-01"
    form_id: str = "ECRF-GBM-BASELINE"
    proposed_version: str = "1.1"


@r.get("/ai/criteria", tags=["ai"])
def ai_criteria(user=Depends(current_user)):
    """Return the protocol entry criteria from deliverables/protocol_criteria.json."""
    return {"criteria": [c.as_api() for c in screening.load_criteria()]}


@r.get("/ai/screening/eval", tags=["ai"])
def ai_screening_eval(provider: str = Query(default="rules"), user=Depends(current_user)):
    """Run or return the screening checker evaluation against seeded truth."""
    provider = provider.lower()
    if provider not in {"rules", "ollama"}:
        raise HTTPException(422, "provider must be 'rules' or 'ollama'")
    from eval import screening_eval

    try:
        res = screening_eval.evaluate_screening(provider)
    except Exception as exc:
        raise HTTPException(503, f"Screening eval unavailable for {provider}: {exc}") from exc
    return res


@r.post("/ai/participants/{pid}/screen", tags=["ai"])
@r.post("/ai/participants/{pid}/screening/check", tags=["ai"])
def screen_participant(pid: str, body: ScreeningIn | None = None,
                       provider: str = Query(default="auto"),
                       user=Depends(require("nurse", "pi", "service"))):
    """Check a participant against protocol entry criteria (`met | not_met | unknown` with evidence spans)."""
    provider = provider.lower()
    if provider not in PROVIDER_CHOICES:
        raise HTTPException(422, f"provider must be one of {sorted(PROVIDER_CHOICES)}")

    crit_list = (
        [CriterionDef.from_api(c) for c in body.criteria]
        if body and body.criteria
        else screening.load_criteria()
    )

    with engine.begin() as c:
        if body and body.documents is not None:
            docs = body.documents
        else:
            _must(_one(c, "SELECT 1 FROM participant WHERE id=:i", i=pid), "Participant")
            rows = c.execute(
                text("SELECT id, participant_id, doc_type AS type, title, language, document_date, text "
                     "FROM source_document WHERE participant_id=:p ORDER BY id"),
                {"p": pid},
            ).mappings().all()
            docs = [dict(r) for r in rows]

        result = screening.check_participant(
            pid, docs, criteria=crit_list, provider=provider, allow_fallback=True
        )
        payload = result.as_api()
        audit_record(
            c,
            user,
            "screening.checked",
            "participant",
            pid,
            participant_id=pid,
            after={
                "overall": result.overall,
                "counts": payload["counts"],
                "provider": result.metadata.provider,
                "fallbackFrom": result.metadata.fallback_from,
            },
            source="ai",
            model=result.metadata.model,
            prompt_version=result.metadata.prompt_version,
        )
    return payload


@r.get("/ai/protocol/proposals", tags=["ai"])
def get_protocol_proposals(provider: str = Query(default="auto"),
                           study_id: str = Query(default="GBM-NL-2026-01"),
                           form_id: str = Query(default="ECRF-GBM-BASELINE"),
                           proposed_version: str = Query(default="1.1"),
                           user=Depends(current_user)):
    """Propose eCRF fields and entry criteria from the default protocol synopsis."""
    provider = provider.lower()
    if provider not in PROVIDER_CHOICES:
        raise HTTPException(422, f"provider must be one of {sorted(PROVIDER_CHOICES)}")
    result = protocol.propose_from_synopsis(
        None,
        provider=provider,
        allow_fallback=True,
        study_id=study_id,
        form_id=form_id,
        proposed_version=proposed_version,
    )
    return {**result.as_api(), "synopsisText": protocol.load_synopsis()}


@r.post("/ai/protocol/proposals", tags=["ai"])
@r.post("/ai/protocol-to-form", tags=["ai"])
def post_protocol_proposals(body: ProtocolProposalsIn | None = None,
                            provider: str = Query(default="auto"),
                            user=Depends(require("nurse", "pi", "service"))):
    """Propose eCRF fields and entry criteria from supplied or default protocol synopsis text."""
    provider = provider.lower()
    if provider not in PROVIDER_CHOICES:
        raise HTTPException(422, f"provider must be one of {sorted(PROVIDER_CHOICES)}")
    synopsis_text = body.synopsis_text if body and body.synopsis_text else protocol.load_synopsis()
    study_id = body.study_id if body else "GBM-NL-2026-01"
    form_id = body.form_id if body else "ECRF-GBM-BASELINE"
    proposed_version = body.proposed_version if body else "1.1"

    result = protocol.propose_from_synopsis(
        synopsis_text,
        provider=provider,
        allow_fallback=True,
        study_id=study_id,
        form_id=form_id,
        proposed_version=proposed_version,
    )
    payload = result.as_api()
    with engine.begin() as c:
        audit_record(
            c,
            user,
            "protocol.form_proposed",
            "study",
            study_id,
            after={
                "formId": form_id,
                "proposedVersion": proposed_version,
                "fieldCount": len(result.fields),
                "criteriaCount": len(result.criteria),
                "provider": result.metadata.provider,
                "fallbackFrom": result.metadata.fallback_from,
            },
            source="ai",
            model=result.metadata.model,
            prompt_version=result.metadata.prompt_version,
        )
    return {**payload, "synopsisText": synopsis_text}
