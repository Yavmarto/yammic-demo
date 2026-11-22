"""AI service loop: consume queued runs, extract, post proposals, log the run.

The service is a separate process (``python -m app.ai``). It holds no database
credentials: it logs in as the ``ai`` service user, reads through the REST API,
and posts proposals through the API so the span checks and the audit chain stay
in one place.

    uv run python -m app.ai --provider auto          # poll queued runs
    uv run python -m app.ai --provider rules --once   # one pass, for tests
    uv run python -m app.ai --run-id 12 --provider ollama
"""
from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from typing import Any

from . import providers, registry
from .client import ApiError, HttpApiClient
from .providers import rules as rules_mod
from .types import FieldDef, ProviderError, ProviderUnavailable

PROVIDERS = ("rules", "ollama")


def log(event: str, **fields: Any) -> None:
    print(json.dumps({"ts": datetime.now(UTC).isoformat(), "event": event, **fields},
                     ensure_ascii=False), flush=True)


def _provider_meta(provider, prompt_version: str | None) -> tuple[str, str]:
    if provider.name == "rules":
        return rules_mod.PROMPT_TAG, rules_mod.PROMPT_HASH
    prompt = registry.get(prompt_version)
    return prompt.tag, prompt.sha256


def _choose(provider_name: str, run: dict) -> str:
    name = (provider_name or "auto").lower()
    if name == "auto":
        pref = (run.get("provider") or "").lower()
        if pref in PROVIDERS:
            return pref
        return providers.resolve("auto")
    return name


def _documents(client, run: dict) -> list[dict]:
    if run.get("documentId"):
        return [client.get_document(run["documentId"])]
    return client.documents(run["participantId"])


def process_run(client, run: dict, *, provider: str = "auto",
                prompt_version: str | None = None, allow_fallback: bool = True) -> dict:
    """Process one queued run. Returns a durable summary suitable for a log line."""
    run_id = run["id"]
    participant = run["participantId"]
    t0 = time.perf_counter()
    fields = [FieldDef.from_api(f) for f in client.ecrf_fields(participant)]
    docs = _documents(client, run)
    if not docs:
        raise ProviderError(f"participant {participant} has no source documents")

    requested = _choose(provider, run)
    impl = providers.get_provider(requested)
    warnings: list[str] = []
    fallback_from: str | None = None

    ok, reason = impl.available()
    if not ok:
        if allow_fallback and requested != "rules":
            warnings.append(f"{requested} unavailable, falling back to rules: {reason}")
            fallback_from = requested
            impl = providers.get_provider("rules")
            requested = "rules"
        else:
            raise ProviderUnavailable(reason)

    prompt_tag, prompt_hash = _provider_meta(impl, prompt_version)
    total = len(docs) * len(fields)
    client.update_run(run_id, {"status": "running", "total": total, "provider": impl.name,
                               "model": impl.model, "promptVersion": prompt_tag})

    posted = 0
    abstained = 0
    processed: set[str] = set()
    doc_meta: list[dict] = []
    try:
        for doc in docs:
            text = doc.get("text")
            if text is None:  # a summary endpoint was used
                text = client.get_document(doc["id"])["text"]
            doc_type = doc.get("type") or "unknown"
            result = impl.extract(text, doc_type, fields, prompt_version=prompt_version)
            if result.metadata.fallback_from is None:
                result.metadata.fallback_from = fallback_from
            payloads = [p.as_api(document_id=doc["id"], provider=impl.name, model=impl.model,
                                 prompt_version=result.metadata.prompt_version or prompt_tag)
                        for p in result.proposals if p.field in {f.id for f in fields}]
            client.post_extractions(run_id, payloads)
            processed.add(doc["id"])
            posted += len(payloads)
            abstained += sum(1 for p in result.proposals if p.status == "abstained")
            warnings.extend(result.metadata.warnings)
            meta = result.metadata.as_dict()
            meta.update({
                "documentId": doc["id"],
                "proposals": len(payloads),
                "abstained": sum(1 for p in result.proposals if p.status == "abstained"),
                "lowConfidence": sum(1 for p in result.proposals
                                     if p.status == "proposed" and p.confidence < 0.6),
            })
            doc_meta.append(meta)
            log("ai.document", runId=run_id, **meta)
    except (ProviderUnavailable, ProviderError) as exc:
        if impl.name != "rules" and allow_fallback:
            warnings.append(f"{impl.name} failed mid-run, falling back to rules: {exc}")
            fallback_from = impl.name
            impl = providers.get_provider("rules")
            prompt_tag, prompt_hash = _provider_meta(impl, None)
            client.update_run(run_id, {"provider": impl.name, "model": impl.model,
                                       "promptVersion": prompt_tag})
            for doc in docs:
                if doc["id"] in processed:
                    continue
                text = doc.get("text") or client.get_document(doc["id"])["text"]
                result = impl.extract(text, doc.get("type") or "unknown", fields)
                payloads = [p.as_api(document_id=doc["id"], provider=impl.name, model=impl.model,
                                     prompt_version=prompt_tag) for p in result.proposals]
                client.post_extractions(run_id, payloads)
                processed.add(doc["id"])
                posted += len(payloads)
                abstained += sum(1 for p in result.proposals if p.status == "abstained")
                meta = result.metadata.as_dict()
                meta.update({"documentId": doc["id"], "proposals": len(payloads),
                             "abstained": sum(1 for p in result.proposals if p.status == "abstained"),
                             "lowConfidence": 0})
                doc_meta.append(meta)
                log("ai.document", runId=run_id, **meta)
        else:
            duration = int((time.perf_counter() - t0) * 1000)
            client.update_run(run_id, {"status": "failed", "error": str(exc)[:900],
                                       "provider": impl.name, "model": impl.model,
                                       "promptVersion": prompt_tag})
            outcome = {"runId": run_id, "status": "failed", "provider": impl.name,
                       "model": impl.model, "promptVersion": prompt_tag,
                       "promptHash": prompt_hash, "error": str(exc), "durationMs": duration,
                       "warnings": warnings}
            log("ai.run", **outcome)
            return outcome

    duration = int((time.perf_counter() - t0) * 1000)
    client.update_run(run_id, {"status": "completed", "done": posted, "total": total})
    outcome = {
        "runId": run_id,
        "status": "completed",
        "participantId": participant,
        "provider": impl.name,
        "model": impl.model,
        "promptVersion": doc_meta[0]["promptVersion"] if doc_meta else prompt_tag,
        "promptHash": prompt_hash,
        "fallbackFrom": fallback_from,
        "documents": len(docs),
        "proposals": posted,
        "abstained": abstained,
        "durationMs": duration,
        "warnings": warnings,
        "documentMeta": doc_meta,
    }
    log("ai.run", **outcome)
    return outcome


def process_queued(client, *, provider: str = "auto", once: bool = False,
                   poll_interval: float = 2.0, prompt_version: str | None = None) -> list[dict]:
    outcomes: list[dict] = []
    while True:
        try:
            runs = client.queued_runs()
        except ApiError as exc:
            log("ai.poll_error", error=str(exc))
            runs = []
        for run in runs:
            log("ai.run_start", runId=run["id"], participantId=run.get("participantId"),
                requestedProvider=run.get("provider") or provider)
            try:
                outcomes.append(process_run(client, run, provider=provider,
                                            prompt_version=prompt_version))
            except (ApiError, ProviderUnavailable, ProviderError) as exc:
                log("ai.run_error", runId=run["id"], error=str(exc))
                try:
                    client.update_run(run["id"], {"status": "failed", "error": str(exc)[:900]})
                except ApiError:
                    pass
        if once:
            return outcomes
        time.sleep(poll_interval)


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Yamicc AI extraction service")
    ap.add_argument("--api", default=None, help="API base URL (default YAMICC_API_URL or 127.0.0.1:8002)")
    ap.add_argument("--provider", default="auto", choices=["auto", *PROVIDERS],
                    help="auto = Ollama when available, else rules")
    ap.add_argument("--prompt-version", default=None, help="prompt file version, e.g. extract_v1")
    ap.add_argument("--once", action="store_true", help="process the queued runs once and exit")
    ap.add_argument("--run-id", type=int, default=None, help="process one specific run")
    ap.add_argument("--check", action="store_true", help="print provider and prompt registry status")
    args = ap.parse_args(argv)

    if args.check:
        print(json.dumps({"providers": providers.describe(),
                          "prompts": [{"version": p.version, "sha256": p.sha256, "tag": p.tag}
                                      for p in registry.all_prompts()]}, indent=2))
        return 0

    client = HttpApiClient(args.api) if args.api else HttpApiClient()
    client.login()
    if args.run_id is not None:
        run = client.get_run(args.run_id)
        if run["status"] not in ("queued", "running"):
            log("ai.run_skip", runId=run["id"], status=run["status"])
            return 0
        outcome = process_run(client, run, provider=args.provider,
                              prompt_version=args.prompt_version)
        return 0 if outcome["status"] == "completed" else 1
    process_queued(client, provider=args.provider, once=args.once,
                   prompt_version=args.prompt_version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
