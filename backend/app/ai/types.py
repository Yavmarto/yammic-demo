"""Provider-agnostic types for the AI extraction service.

The wire contract is in ``backend/openapi.json`` (``ExtractionIn`` / ``Run``).
These dataclasses are the in-process interface between the API service
(``app.ai.service``), the providers, and the eval harness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Status = Literal["proposed", "abstained"]
ScreeningVerdict = Literal["met", "not_met", "unknown"]
CriterionType = Literal["inclusion", "exclusion"]


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


@dataclass(frozen=True)
class CriterionDef:
    id: str
    type: CriterionType
    text: str
    data_needed: str | None = None

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "CriterionDef":
        return cls(
            id=raw["id"],
            type=raw.get("type", "inclusion"),
            text=raw["text"],
            data_needed=raw.get("dataNeeded") or raw.get("data_needed"),
        )

    def as_api(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "dataNeeded": self.data_needed,
        }


@dataclass
class CriterionCheck:
    criterion_id: str
    type: CriterionType
    text: str
    verdict: ScreeningVerdict
    confidence: float = 0.0
    rationale: str | None = None
    document_id: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
    abstention_reason: str | None = None

    def as_api(self) -> dict[str, Any]:
        e0 = self.evidence[0] if self.evidence else None
        return {
            "criterionId": self.criterion_id,
            "id": self.criterion_id,
            "type": self.type,
            "text": self.text,
            "verdict": self.verdict,
            "status": self.verdict,
            "confidence": round(max(0.0, min(1.0, float(self.confidence))), 4),
            "rationale": self.rationale,
            "documentId": self.document_id,
            "spanStart": e0.start if e0 else None,
            "spanEnd": e0.end if e0 else None,
            "evidence": [e.as_api() for e in self.evidence],
            "abstentionReason": self.abstention_reason,
        }


@dataclass
class ScreeningResult:
    participant_id: str
    overall: Literal["eligible", "screen_fail", "unknown"]
    checks: list[CriterionCheck]
    metadata: RunMetadata

    def by_criterion(self) -> dict[str, CriterionCheck]:
        return {c.criterion_id: c for c in self.checks}

    def as_api(self) -> dict[str, Any]:
        counts = {
            "met": sum(1 for c in self.checks if c.verdict == "met"),
            "notMet": sum(1 for c in self.checks if c.verdict == "not_met"),
            "unknown": sum(1 for c in self.checks if c.verdict == "unknown"),
            "total": len(self.checks),
        }
        return {
            "participantId": self.participant_id,
            "overall": self.overall,
            "counts": counts,
            "criteria": [c.as_api() for c in self.checks],
            "checks": [c.as_api() for c in self.checks],
            "metadata": self.metadata.as_dict(),
        }


@dataclass
class ProposedFormField:
    id: str
    label: str
    value_type: str
    section: str | None = None
    required: bool = True
    unit: str | None = None
    coding: dict[str, Any] | None = None
    cdisc_domain: str | None = None
    cdisc_variable: str | None = None
    source_sentence: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    confidence: float = 0.95
    rationale: str | None = None

    def as_api(self) -> dict[str, Any]:
        e0 = self.evidence[0] if self.evidence else None
        return {
            "id": self.id,
            "label": self.label,
            "type": self.value_type,
            "valueType": self.value_type,
            "section": self.section,
            "required": self.required,
            "unit": self.unit,
            "coding": self.coding,
            "terminology": self.coding,
            "cdiscDomain": self.cdisc_domain,
            "cdiscVariable": self.cdisc_variable,
            "sourceSentence": self.source_sentence,
            "spanStart": e0.start if e0 else None,
            "spanEnd": e0.end if e0 else None,
            "evidence": [e.as_api() for e in self.evidence],
            "confidence": round(max(0.0, min(1.0, float(self.confidence))), 4),
            "rationale": self.rationale,
        }


@dataclass
class ProposedCriterion:
    id: str
    type: CriterionType
    text: str
    data_needed: str | None = None
    source_sentence: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    confidence: float = 0.95
    rationale: str | None = None

    def as_api(self) -> dict[str, Any]:
        e0 = self.evidence[0] if self.evidence else None
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "dataNeeded": self.data_needed,
            "sourceSentence": self.source_sentence,
            "spanStart": e0.start if e0 else None,
            "spanEnd": e0.end if e0 else None,
            "evidence": [e.as_api() for e in self.evidence],
            "confidence": round(max(0.0, min(1.0, float(self.confidence))), 4),
            "rationale": self.rationale,
        }


@dataclass
class ProtocolFormProposalResult:
    study_id: str
    form_id: str
    proposed_version: str
    fields: list[ProposedFormField]
    criteria: list[ProposedCriterion]
    metadata: RunMetadata

    def as_api(self) -> dict[str, Any]:
        return {
            "studyId": self.study_id,
            "formId": self.form_id,
            "proposedVersion": self.proposed_version,
            "fields": [f.as_api() for f in self.fields],
            "criteria": [c.as_api() for c in self.criteria],
            "metadata": self.metadata.as_dict(),
        }


class ProviderUnavailable(RuntimeError):
    """The provider cannot run (for example Ollama is not installed or down)."""


class ProviderError(RuntimeError):
    """The provider ran but failed (bad response, timeout, schema violation)."""
