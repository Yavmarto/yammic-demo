"""AI protocol-to-form proposals.

Reads the protocol synopsis text (default ``deliverables/protocol_GBM-NL-2026-01_synopsis.md``)
and proposes:
1. eCRF fields (``id``, ``label``, ``type``, ``unit``, ``coding``, ``sourceSentence``)
2. Entry criteria (``id``, ``type`` = ``inclusion|exclusion``, ``text``, ``dataNeeded``, ``sourceSentence``)

Every proposed field and criterion carries its exact ``sourceSentence`` and
verified character span ``[start, end)`` in the protocol synopsis text. Supports
``rules`` and ``ollama`` providers with automatic fallback when Ollama is down.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from . import providers, registry
from .providers import rules as rules_mod
from .span import locate_quote, make_evidence
from .types import (
    Evidence,
    ProposedCriterion,
    ProposedFormField,
    ProtocolFormProposalResult,
    ProviderError,
    ProviderUnavailable,
    RunMetadata,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SYNOPSIS_PATH = REPO_ROOT / "deliverables" / "protocol_GBM-NL-2026-01_synopsis.md"
STUDY_JSON_PATH = REPO_ROOT / "app" / "assets" / "data" / "study.json"

FIELD_METADATA: dict[str, dict[str, Any]] = {
    "SUBJID": {
        "section": "identification",
        "valueType": "string",
        "required": True,
        "unit": None,
        "coding": None,
    },
    "SITEID": {
        "section": "identification",
        "valueType": "string",
        "required": True,
        "unit": None,
        "coding": None,
    },
    "SEX": {
        "section": "demographics",
        "valueType": "coded",
        "required": True,
        "unit": None,
        "coding": {
            "system": "SNOMED CT",
            "codes": [
                {"value": "F", "code": "248152002", "display": "Female"},
                {"value": "M", "code": "248153007", "display": "Male"},
            ],
        },
    },
    "AGE": {
        "section": "demographics",
        "valueType": "integer",
        "required": True,
        "unit": "years",
        "coding": None,
    },
    "MHSTDAT": {
        "section": "diagnosis",
        "valueType": "date",
        "required": True,
        "unit": None,
        "coding": None,
    },
    "HISTOLOGY": {
        "section": "diagnosis",
        "valueType": "coded",
        "required": True,
        "unit": None,
        "coding": {
            "system": "ICD-O-3",
            "code": "9440/3",
            "display": "Glioblastoma, NOS",
            "codeVerified": True,
        },
    },
    "IDHSTAT": {
        "section": "diagnosis",
        "valueType": "coded",
        "required": True,
        "unit": None,
        "coding": {
            "system": "SNOMED CT",
            "code": "445048000",
            "display": "IDH1 wild type",
            "codeVerified": False,
        },
    },
    "MGMTPROM": {
        "section": "diagnosis",
        "valueType": "coded",
        "required": True,
        "unit": None,
        "coding": {
            "system": "LOINC",
            "code": "88199-1",
            "display": "MGMT promoter methylation [Presence] in Tissue",
            "codeVerified": False,
        },
    },
    "KPS": {
        "section": "clinical_status",
        "valueType": "integer",
        "required": True,
        "unit": "%",
        "coding": {
            "system": "LOINC",
            "code": "89261-2",
            "display": "Karnofsky Performance Status score",
            "codeVerified": False,
        },
    },
    "EXTRES": {
        "section": "surgery",
        "valueType": "coded",
        "required": True,
        "unit": None,
        "coding": {
            "system": "SNOMED CT",
            "code": "262143007",
            "display": "Extent of surgical resection",
            "codeVerified": False,
        },
    },
    "RTDOSE": {
        "section": "treatment",
        "valueType": "number",
        "required": True,
        "unit": "Gy",
        "coding": {
            "system": "UCUM",
            "code": "Gy",
            "display": "gray",
            "codeVerified": True,
        },
    },
    "RTFRAC": {
        "section": "treatment",
        "valueType": "integer",
        "required": True,
        "unit": "fractions",
        "coding": None,
    },
    "TMZPLNC": {
        "section": "treatment",
        "valueType": "integer",
        "required": True,
        "unit": "cycles",
        "coding": {
            "system": "ATC",
            "code": "L01AX03",
            "display": "temozolomide",
            "codeVerified": True,
        },
    },
    "AEGRADE": {
        "section": "safety",
        "valueType": "integer",
        "required": False,
        "unit": "grade",
        "coding": None,
    },
    "PROGDAT": {
        "section": "outcome",
        "valueType": "date",
        "required": False,
        "unit": None,
        "coding": None,
    },
}


def load_synopsis(path: Path | None = None) -> str:
    target = path or DEFAULT_SYNOPSIS_PATH
    if target.exists():
        return target.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Protocol synopsis not found at {target}")


def _parse_type_and_unit(type_unit: str, field_id: str) -> tuple[str, str | None, bool, dict[str, Any] | None]:
    meta = FIELD_METADATA.get(field_id, {})
    low = type_unit.casefold()
    required = "optional" not in low and meta.get("required", True)
    if "integer" in low:
        vtype = "integer"
    elif "number" in low:
        vtype = "number"
    elif "date" in low:
        vtype = "date"
    elif "coded" in low:
        vtype = "coded"
    else:
        vtype = meta.get("valueType", "string")

    unit = meta.get("unit")
    if not unit:
        for u in ("years", "%", "Gy", "fractions", "cycles"):
            if u.casefold() in low:
                unit = u
                break

    coding = meta.get("coding")
    if not coding and "icd-o-3" in low:
        m = re.search(r"ICD-O-3\s+([0-9/]+)", type_unit, re.I)
        if m:
            coding = {"system": "ICD-O-3", "code": m.group(1), "display": "Glioblastoma, NOS"}
    return vtype, unit, required, coding


def propose_with_rules(
    synopsis_text: str,
    *,
    study_id: str = "GBM-NL-2026-01",
    form_id: str = "ECRF-GBM-BASELINE",
    proposed_version: str = "1.1",
) -> ProtocolFormProposalResult:
    t0 = time.perf_counter()
    fields: list[ProposedFormField] = []
    criteria: list[ProposedCriterion] = []

    # 1. Extract criteria lines from Section 5 (numbered items with INC-XX or EXC-XX)
    crit_rx = re.compile(
        r"^\s*\d+\.\s+\*\*((?:INC|EXC)-\d{2})\s+—\s+([^*]+)\*\*\s*(.+)$",
        re.MULTILINE,
    )
    for m in crit_rx.finditer(synopsis_text):
        cid = m.group(1).strip()
        rest = m.group(3).strip()
        ctype = "inclusion" if cid.startswith("INC") else "exclusion"
        parts = re.split(r"\s*\*Check:\*\s*", rest, maxsplit=1)
        ctext = parts[0].strip()
        data_needed = parts[1].strip() if len(parts) > 1 else None
        line_start = m.start(0)
        # Skip leading newline/spaces so evidence span is clean
        while line_start < m.end(0) and synopsis_text[line_start] in ("\n", "\r"):
            line_start += 1
        ev = make_evidence(synopsis_text, line_start, m.end(0))
        criteria.append(
            ProposedCriterion(
                id=cid,
                type=ctype,
                text=ctext,
                data_needed=data_needed,
                source_sentence=ev.text,
                evidence=[ev],
                confidence=0.97,
                rationale=f"Deterministic rule matched {ctype} criterion {cid} in protocol synopsis.",
            )
        )

    # 2. Extract eCRF field rows from Section 8 markdown table
    field_rx = re.compile(
        r"^\|\s*([A-Z]{2,12})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([A-Z]{2}\.[A-Z0-9]+)\s*\|$",
        re.MULTILINE,
    )
    for m in field_rx.finditer(synopsis_text):
        fid = m.group(1).strip()
        label = m.group(2).strip()
        type_unit = m.group(3).strip()
        cdisc = m.group(4).strip()
        domain, var = (cdisc.split(".", 1) + [None])[:2]
        vtype, unit, required, coding = _parse_type_and_unit(type_unit, fid)
        meta = FIELD_METADATA.get(fid, {})
        ev = make_evidence(synopsis_text, m.start(0), m.end(0))
        fields.append(
            ProposedFormField(
                id=fid,
                label=label,
                value_type=vtype,
                section=meta.get("section"),
                required=required,
                unit=unit,
                coding=coding,
                cdisc_domain=domain,
                cdisc_variable=var,
                source_sentence=ev.text,
                evidence=[ev],
                confidence=0.97,
                rationale=f"Deterministic rule extracted eCRF field {fid} ({cdisc}) from synopsis table.",
            )
        )

    # Fallback: if synopsis text uses prose mentions of eCRF fields (`AGE`, `KPS`, etc.) without a table
    if not fields:
        seen_fids: set[str] = set()
        for fid, meta in FIELD_METADATA.items():
            m = re.search(rf"[^\n.]*\b`?{fid}`?\b[^\n.]*\.?", synopsis_text)
            if m and fid not in seen_fids:
                seen_fids.add(fid)
                ev = make_evidence(synopsis_text, m.start(0), m.end(0))
                fields.append(
                    ProposedFormField(
                        id=fid,
                        label=fid.capitalize(),
                        value_type=meta.get("valueType", "string"),
                        section=meta.get("section"),
                        required=meta.get("required", True),
                        unit=meta.get("unit"),
                        coding=meta.get("coding"),
                        source_sentence=ev.text,
                        evidence=[ev],
                        confidence=0.88,
                        rationale=f"Deterministic rule matched prose mention of `{fid}`.",
                    )
                )

    duration = int((time.perf_counter() - t0) * 1000)
    return ProtocolFormProposalResult(
        study_id=study_id,
        form_id=form_id,
        proposed_version=proposed_version,
        fields=fields,
        criteria=criteria,
        metadata=RunMetadata(
            provider="rules",
            model=rules_mod.RulesProvider.model,
            prompt_version=rules_mod.PROMPT_TAG,
            prompt_hash=rules_mod.PROMPT_HASH,
            duration_ms=duration,
        ),
    )


def _protocol_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "type": {"type": "string"},
                        "unit": {"type": "string"},
                        "codingSystem": {"type": "string"},
                        "codingCode": {"type": "string"},
                        "codingDisplay": {"type": "string"},
                        "sourceSentence": {"type": "string"},
                        "confidence": {"type": "number"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["id", "label", "type", "sourceSentence", "confidence"],
                    "additionalProperties": False,
                },
            },
            "criteria": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["inclusion", "exclusion"]},
                        "text": {"type": "string"},
                        "dataNeeded": {"type": "string"},
                        "sourceSentence": {"type": "string"},
                        "confidence": {"type": "number"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["id", "type", "text", "sourceSentence", "confidence"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["fields", "criteria"],
        "additionalProperties": False,
    }


def propose_with_ollama(
    synopsis_text: str,
    *,
    study_id: str = "GBM-NL-2026-01",
    form_id: str = "ECRF-GBM-BASELINE",
    proposed_version: str = "1.1",
    ollama_provider=None,
) -> ProtocolFormProposalResult:
    impl = ollama_provider or providers.get_provider("ollama")
    ok, reason = impl.available()
    if not ok:
        raise ProviderUnavailable(reason)

    prompt = registry.get_protocol_prompt()
    user = (
        "Propose eCRF fields and entry criteria from this protocol synopsis. Return JSON only.\n\n"
        "----- BEGIN PROTOCOL SYNOPSIS -----\n"
        + synopsis_text
        + "\n----- END PROTOCOL SYNOPSIS -----"
    )
    t0 = time.perf_counter()
    payload = {
        "model": impl.model,
        "stream": False,
        "format": _protocol_schema(),
        "options": {"temperature": 0, "seed": 42, "num_ctx": 8192},
        "messages": [
            {"role": "system", "content": prompt.text},
            {"role": "user", "content": user},
        ],
    }
    try:
        from .providers import ollama as ollama_mod

        response = ollama_mod._post(f"{impl.host}/api/chat", payload, timeout=impl.timeout)
    except Exception as exc:
        if isinstance(exc, (ProviderError, ProviderUnavailable)):
            raise
        raise ProviderUnavailable(f"Ollama protocol proposal call failed: {exc}") from exc

    content = (response.get("message") or {}).get("content") or ""
    try:
        from .providers.ollama import _strip_fences

        parsed = json.loads(_strip_fences(content))
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Ollama returned invalid protocol JSON: {exc}: {content[:200]!r}") from exc

    raw_fields = parsed.get("fields")
    raw_criteria = parsed.get("criteria")
    if not isinstance(raw_fields, list) or not isinstance(raw_criteria, list):
        raise ProviderError("Ollama protocol response missing 'fields' or 'criteria' list")

    warnings: list[str] = []
    fields: list[ProposedFormField] = []
    for item in raw_fields:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        fid = str(item["id"]).strip().upper()
        quote = str(item.get("sourceSentence") or "").strip()
        found = locate_quote(synopsis_text, quote)
        if not found:
            warnings.append(f"field {fid}: sourceSentence not found in synopsis; dropped")
            continue
        ev = make_evidence(synopsis_text, found[0], found[1])
        meta = FIELD_METADATA.get(fid, {})
        coding = meta.get("coding")
        if not coding and item.get("codingSystem") and item.get("codingCode"):
            coding = {
                "system": str(item["codingSystem"]),
                "code": str(item["codingCode"]),
                "display": str(item.get("codingDisplay") or ""),
            }
        unit = str(item.get("unit") or "").strip() or meta.get("unit")
        try:
            conf = max(0.0, min(1.0, float(item.get("confidence", 0.9))))
        except (TypeError, ValueError):
            conf = 0.9
        fields.append(
            ProposedFormField(
                id=fid,
                label=str(item.get("label") or fid).strip(),
                value_type=str(item.get("type") or meta.get("valueType") or "string").strip(),
                section=meta.get("section"),
                required=meta.get("required", True),
                unit=unit,
                coding=coding,
                source_sentence=ev.text,
                evidence=[ev],
                confidence=conf,
                rationale=str(item.get("rationale") or "").strip() or None,
            )
        )

    criteria: list[ProposedCriterion] = []
    for item in raw_criteria:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        cid = str(item["id"]).strip().upper()
        quote = str(item.get("sourceSentence") or "").strip()
        found = locate_quote(synopsis_text, quote)
        if not found:
            warnings.append(f"criterion {cid}: sourceSentence not found in synopsis; dropped")
            continue
        ev = make_evidence(synopsis_text, found[0], found[1])
        ctype_raw = str(item.get("type") or "inclusion").lower()
        ctype = "exclusion" if ctype_raw == "exclusion" or cid.startswith("EXC") else "inclusion"
        try:
            conf = max(0.0, min(1.0, float(item.get("confidence", 0.9))))
        except (TypeError, ValueError):
            conf = 0.9
        criteria.append(
            ProposedCriterion(
                id=cid,
                type=ctype,
                text=str(item.get("text") or "").strip(),
                data_needed=str(item.get("dataNeeded") or "").strip() or None,
                source_sentence=ev.text,
                evidence=[ev],
                confidence=conf,
                rationale=str(item.get("rationale") or "").strip() or None,
            )
        )

    duration = int((time.perf_counter() - t0) * 1000)
    return ProtocolFormProposalResult(
        study_id=study_id,
        form_id=form_id,
        proposed_version=proposed_version,
        fields=fields,
        criteria=criteria,
        metadata=RunMetadata(
            provider="ollama",
            model=impl.model,
            prompt_version=prompt.tag,
            prompt_hash=prompt.sha256,
            duration_ms=duration,
            warnings=warnings,
        ),
    )


def propose_from_synopsis(
    synopsis_text: str | None = None,
    *,
    provider: str = "auto",
    allow_fallback: bool = True,
    study_id: str = "GBM-NL-2026-01",
    form_id: str = "ECRF-GBM-BASELINE",
    proposed_version: str = "1.1",
    ollama_provider=None,
) -> ProtocolFormProposalResult:
    """Propose eCRF fields and entry criteria from protocol synopsis text."""
    text = synopsis_text if synopsis_text is not None else load_synopsis()
    requested = (provider or "auto").lower()
    if requested == "auto":
        if ollama_provider is not None:
            ok, _ = ollama_provider.available()
            requested = "ollama" if ok else "rules"
        else:
            requested = providers.resolve("auto")

    if requested == "rules":
        return propose_with_rules(
            text, study_id=study_id, form_id=form_id, proposed_version=proposed_version
        )

    if requested == "ollama":
        try:
            return propose_with_ollama(
                text,
                study_id=study_id,
                form_id=form_id,
                proposed_version=proposed_version,
                ollama_provider=ollama_provider,
            )
        except (ProviderUnavailable, ProviderError) as exc:
            if not allow_fallback:
                raise
            result = propose_with_rules(
                text, study_id=study_id, form_id=form_id, proposed_version=proposed_version
            )
            result.metadata.fallback_from = "ollama"
            result.metadata.warnings.append(f"ollama unavailable or failed, falling back to rules: {exc}")
            return result

    raise KeyError(f"unknown provider {provider!r}; choose from rules, ollama, auto")
