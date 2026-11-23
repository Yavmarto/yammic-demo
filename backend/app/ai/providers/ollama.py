"""Local Ollama provider.

Talks to the Ollama HTTP API on ``localhost:11434`` (override with
``OLLAMA_HOST``). No paid API, no data leaves the machine. The model output is
constrained by a JSON schema, then every quoted span is re-located in the source
text; a proposal whose evidence cannot be found becomes an abstention.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

from .. import registry, terminology
from ..span import locate_quote, make_evidence
from ..types import Evidence, ExtractionResult, FieldDef, Proposal, ProviderError, ProviderUnavailable, RunMetadata

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

_NUMERIC = {"AGE", "KPS", "RTFRAC", "TMZPLNC", "AEGRADE", "RTDOSE"}
_HEDGE = re.compile(r"\b(probably|probable|possibly|waarschijnlijk|may be|cannot be excluded|"
                    r"niet uit te sluiten|vermoedelijk)\b", re.I)


def _post(url: str, payload: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode())


def _get(url: str, timeout: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as res:
        return json.loads(res.read().decode())


def _schema(field_ids: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "extractions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string", "enum": field_ids},
                        "status": {"type": "string", "enum": ["proposed", "abstained"]},
                        "value": {"anyOf": [{"type": "string"}, {"type": "number"}]},
                        "evidenceQuote": {"type": "string"},
                        "confidence": {"type": "number"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["field", "status", "value", "evidenceQuote", "confidence", "rationale"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["extractions"],
        "additionalProperties": False,
    }


_RECOVERY = {
    "AGE": r"(\d{1,3})",
    "KPS": r"(\d{1,3})\s*%",
    "RTDOSE": r"(\d+(?:[.,]\d+)?)\s*Gy",
    "RTFRAC": r"(\d+)\s*(?:fractions|fracties)",
    "TMZPLNC": r"(\d+)\s+(?:planned\s+)?[^.\n]{0,40}?(?:cycles|cycli)",
    "AEGRADE": r"(?:maximaal|maximum|max\.)\s+(?:graad|grade)\s+(\d)|(?:graad|grade)\s+(\d)",
}


def _recover_from_evidence(field: str, evidence_text: str) -> tuple[object, str] | None:
    """Read the value from a verified quote when the model left ``value`` empty or garbled."""
    if field in _RECOVERY:
        m = re.search(_RECOVERY[field], evidence_text, re.I)
        if m:
            raw = m.group(1) or m.group(2)
            return terminology.canonicalize(field, raw)
        return None
    if field == "HISTOLOGY" and re.search(r"9440/3", evidence_text):
        return "glioblastoma_idh_wildtype", terminology.DISPLAY["HISTOLOGY"]["glioblastoma_idh_wildtype"]
    normalized, display = terminology.canonicalize(field, evidence_text)
    if normalized is not None:
        return normalized, display
    return None


def _supports(field: str, normalized, evidence_text: str, raw_value: str) -> bool:
    """Cheap sanity check that the quote plausibly contains the value."""
    low = evidence_text.casefold()
    raw = (raw_value or "").casefold()
    if field in _NUMERIC:
        if field == "RTDOSE":
            m = re.search(r"\d+(?:[.,]\d+)?", evidence_text)
            return bool(m) and abs(float(m.group(0).replace(",", ".")) - float(normalized)) < 0.01
        return str(normalized) in evidence_text
    if field == "SITEID":
        return ("site-" in low
                or any(name in low for name, code in terminology.SITE_CODES.items() if code == normalized))
    if field in ("SUBJID", "MHSTDAT", "PROGDAT"):
        return str(normalized).casefold() in low or raw in low
    if field == "SEX":
        return any(w in low for w in ("female", "male", "vrouw", "man", "geslacht", "sex"))
    if field == "HISTOLOGY":
        return "glioblast" in low
    if field == "IDHSTAT":
        return "idh" in low
    if field == "MGMTPROM":
        return "methyl" in low
    if field == "EXTRES":
        return any(w in low for w in ("resect", "subtotal", "gross", "biopsy", "biopsie"))
    return True


class OllamaProvider:
    name = "ollama"
    paid = False

    def __init__(self, model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST, timeout: float = 240.0):
        self.model = model
        self.host = host
        self.timeout = timeout

    def available(self) -> tuple[bool, str]:
        try:
            tags = _get(f"{self.host}/api/tags", timeout=2.0)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return False, f"Ollama not reachable at {self.host}: {exc}"
        names = {m.get("name", "") for m in tags.get("models", [])}
        if self.model not in names:
            return False, f"model {self.model!r} not pulled (have: {', '.join(sorted(names)) or 'none'})"
        return True, f"local Ollama model {self.model}"

    def _chat(self, system: str, user: str, field_ids: list[str]) -> dict:
        payload = {
            "model": self.model,
            "stream": False,
            "format": _schema(field_ids),
            "options": {"temperature": 0, "seed": 42, "num_ctx": 8192},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            return _post(f"{self.host}/api/chat", payload, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:300]
            raise ProviderError(f"Ollama HTTP {exc.code}: {body}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderUnavailable(f"Ollama call failed: {exc}") from exc

    def extract(self, document_text: str, document_type: str,
                fields: list[FieldDef], *, prompt_version: str | None = None) -> ExtractionResult:
        ok, reason = self.available()
        if not ok:
            raise ProviderUnavailable(reason)

        prompt = registry.get(prompt_version)
        field_dicts = [{"id": f.id, "label": f.label, "valueType": f.value_type, "unit": f.unit,
                        "terminology": f.terminology, "help": f.help} for f in fields]
        system = prompt.render(field_dicts, document_type)
        user = ("Extract the eCRF fields from this source document. Return JSON only.\n\n"
                "----- BEGIN DOCUMENT -----\n" + document_text + "\n----- END DOCUMENT -----")

        t0 = time.perf_counter()
        response = self._chat(system, user, [f.id for f in fields])
        content = (response.get("message") or {}).get("content") or ""
        try:
            parsed = json.loads(_strip_fences(content))
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Ollama returned invalid JSON: {exc}: {content[:200]!r}") from exc
        items = parsed.get("extractions")
        if not isinstance(items, list):
            raise ProviderError("Ollama response has no 'extractions' list")

        by_field: dict[str, dict] = {}
        for item in items:
            if isinstance(item, dict) and item.get("field") in {f.id for f in fields}:
                by_field.setdefault(item["field"], item)

        warnings: list[str] = []
        proposals: list[Proposal] = []
        for field in fields:
            item = by_field.get(field.id)
            if not item:
                proposals.append(_abstain(field, "not_reported",
                                          "Model did not return this field; abstained."))
                continue
            status = item.get("status")
            confidence = _clamp(item.get("confidence"))
            rationale = (item.get("rationale") or "").strip() or None
            if status != "proposed":
                proposals.append(_abstain(field, "not_stated", rationale))
                continue
            raw_value = str(item.get("value") or "").strip()
            quote = str(item.get("evidenceQuote") or "").strip()
            # ponytail: a trailing full stop is a model habit, not part of the source phrase; the
            # phrase must match the document, so drop it before locating. Ceiling: clause-tail trimming
            # (e.g. "volgens RANO") is left to the prompt.
            quote = quote.rstrip(" .;,")
            found = locate_quote(document_text, quote)
            if not found:
                warnings.append(f"{field.id}: evidence quote not found in document; abstained")
                proposals.append(_abstain(field, "evidence_not_found",
                                          f"Model quoted {quote[:60]!r}, which is not in the document."))
                continue
            start, end, matched = found
            evidence = make_evidence(document_text, start, end)
            normalized, display = (terminology.canonicalize(field.id, raw_value)
                                   if raw_value else (None, None))
            if normalized is None:
                recovered = _recover_from_evidence(field.id, evidence.text)
                if recovered is not None:
                    normalized, display = recovered
                    warnings.append(f"{field.id}: model value {raw_value!r} was empty or garbled; "
                                    f"read {display!r} from the verified evidence quote")
            if normalized is None:
                if not raw_value:
                    proposals.append(_abstain(field, "no_value", rationale))
                    continue
                warnings.append(f"{field.id}: value {raw_value!r} is not canonical; abstained")
                proposals.append(_abstain(field, "unparsed_value",
                                          f"Model value {raw_value!r} could not be normalised."))
                continue
            if _HEDGE.search(evidence.text) and confidence >= 0.6:
                confidence = 0.45
                warnings.append(f"{field.id}: hedged evidence; confidence capped at 0.45")
            supported = _supports(field.id, normalized, evidence.text, raw_value)
            if not supported:
                confidence = min(confidence, 0.35)
                warnings.append(f"{field.id}: quote does not contain the value; confidence capped at 0.35")
            proposals.append(Proposal(
                field=field.id, status="proposed", value=display, normalized_value=normalized,
                unit=field.unit, confidence=confidence,
                proposed_code=terminology.code_for(field), evidence=[evidence],
                rationale=rationale,
            ))

        duration = int((time.perf_counter() - t0) * 1000)
        return ExtractionResult(
            proposals=proposals,
            metadata=RunMetadata(
                provider=self.name, model=self.model, prompt_version=prompt.tag,
                prompt_hash=prompt.sha256, duration_ms=duration,
                document_type=document_type, warnings=warnings,
            ),
        )


def _clamp(raw) -> float:
    try:
        return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError):
        return 0.0


def _abstain(field: FieldDef, reason: str, rationale: str | None) -> Proposal:
    return Proposal(field=field.id, status="abstained", value="Not stated", confidence=0.0,
                    abstention_reason=reason, rationale=rationale)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()
