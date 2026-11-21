"""Provider-agnostic types for the AI extraction service.

The wire contract is in ``backend/openapi.json`` (``ExtractionIn`` / ``Run``).
These dataclasses are the in-process interface between the API service
(``app.ai.service``), the providers, and the eval harness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Status = Literal["proposed", "abstained"]


@dataclass(frozen=True)
class FieldDef:
    """One eCRF field, as returned by ``GET /participants/{id}/ecrf``."""

    id: str
    label: str
    value_type: str | None = None
    unit: str | None = None
    section: str | None = None
    terminology: dict[str, Any] | None = None
    help: str | None = None

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "FieldDef":
        return cls(
            id=raw["id"],
            label=raw.get("label") or raw["id"],
            value_type=raw.get("valueType"),
            unit=raw.get("unit"),
            section=raw.get("section"),
            terminology=raw.get("terminology"),
            help=raw.get("help"),
        )


@dataclass(frozen=True)
class Evidence:
    start: int
    end: int
    text: str

    def as_api(self) -> dict[str, Any]:
        return {"start": self.start, "end": self.end, "text": self.text}


@dataclass
class Proposal:
    """One extraction proposal. Mirrors ``ExtractionIn`` plus ``rationale``."""

    field: str
    status: Status
    value: str | None = None
    normalized_value: Any | None = None
    unit: str | None = None
    confidence: float = 0.0
    proposed_code: dict[str, Any] | None = None
    abstention_reason: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    rationale: str | None = None

    def as_api(self, *, document_id: str, provider: str, model: str, prompt_version: str) -> dict[str, Any]:
        """The exact payload accepted by ``POST /runs/{id}/extractions``."""
        payload: dict[str, Any] = {
            "documentId": document_id,
            "field": self.field,
            "status": self.status,
            "value": self.value,
            "normalizedValue": self.normalized_value,
            "unit": self.unit,
            "confidence": round(max(0.0, min(1.0, float(self.confidence))), 4),
            "proposedCode": self.proposed_code,
            "abstentionReason": self.abstention_reason,
            "evidence": [e.as_api() for e in self.evidence],
            "provider": provider,
            "model": model,
            "promptVersion": prompt_version,
        }
        return payload


@dataclass
class RunMetadata:
    provider: str
    model: str
    prompt_version: str
    prompt_hash: str
    duration_ms: int
    document_id: str | None = None
    document_type: str | None = None
    fallback_from: str | None = None
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "promptVersion": self.prompt_version,
            "promptHash": self.prompt_hash,
            "durationMs": self.duration_ms,
            "documentId": self.document_id,
            "documentType": self.document_type,
            "fallbackFrom": self.fallback_from,
            "warnings": list(self.warnings),
        }


@dataclass
class ExtractionResult:
    proposals: list[Proposal]
    metadata: RunMetadata

    def by_field(self) -> dict[str, Proposal]:
        return {p.field: p for p in self.proposals}


class ProviderUnavailable(RuntimeError):
    """The provider cannot run (for example Ollama is not installed or down)."""


class ProviderError(RuntimeError):
    """The provider ran but failed (bad response, timeout, schema violation)."""
