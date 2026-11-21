from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class M(BaseModel):
    """API models are camelCase on the wire (matches the Flutter models and the fixtures)."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


Role = Literal["nurse", "monitor", "pi", "service"]
Decision = Literal["accept", "correct", "reject", "defer"]
ReviewState = Literal["pending", "accepted", "corrected", "rejected", "deferred"]


class LoginIn(M):
    username: str
    password: str


class User(M):
    username: str
    role: Role
    name: str


class Token(M):
    access_token: str
    token_type: str = "bearer"
    user: User


class Health(M):
    status: str
    database: bool
    synthetic: bool = True
    disclaimer: str = "Synthetic data — prototype, not for clinical use"


class Site(M):
    id: str
    name: str
    short_name: str | None
    city: str | None
    principal_investigator: str | None
    target_enrolment: int | None
    enrolled: int
    open_queries: int


class Milestone(M):
    name: str
    date: str
    done: bool


class Alert(M):
    severity: str
    message: str


class Task(M):
    title: str
    due: str
    assignee: str
    participant_id: str | None = None


class Kpis(M):
    enrolled: int
    target: int
    participants_in_extraction_scope: int
    ecrf_fields_total: int
    ecrf_fields_verified: int
    ecrf_completeness: float
    extractions_total: int
    extractions_pending: int
    extractions_reviewed: int
    extractions_accepted: int
    extractions_corrected: int
    extractions_rejected: int
    extractions_deferred: int
    ai_acceptance_rate: float | None
    needs_attention: int  # pending and (abstained or confidence < 0.6)
    open_queries: int
    sdv_done: int
    sdv_pending: int
    audit_events: int


class Dashboard(M):
    study_id: str
    title: str
    phase: str | None
    status: str | None
    synthetic: bool = True
    disclaimer: str
    kpis: Kpis
    sites: list[Site]
    milestones: list[Milestone]
    alerts: list[Alert]
    tasks: list[Task]


class Visit(M):
    name: str
    date: date | None
    status: str | None
    note: str | None


class ParticipantSummary(M):
    id: str
    study_id: str
    site_id: str
    status: str
    status_detail: str | None
    age: int | None
    sex: str | None
    enrolled_date: date | None
    document_count: int
    extractions_pending: int
    ecrf_verified: int
    ecrf_total: int
    ecrf_complete_pct: int
    open_queries: int


class ParticipantDetail(ParticipantSummary):
    summary: str | None
    diagnosis_date: date | None
    visits: list[Visit]
    treatments: list[dict[str, Any]]
    document_ids: list[str]


class DocumentSummary(M):
    id: str
    participant_id: str
    type: str
    title: str
    language: str | None
    document_date: date | None
    char_length: int
    sha256: str
    extraction_count: int
    extractions_pending: int


class DocumentDetail(DocumentSummary):
    text: str


class Evidence(M):
    start: int
    end: int
    text: str


class LastDecision(M):
    decision: Decision
    corrected_value: str | None
    reason: str | None
    username: str
    role: str
    created_at: datetime


class Extraction(M):
    id: str
    run_id: int
    document_id: str
    document_type: str
    participant_id: str
    field: str
    field_label: str
    status: Literal["proposed", "abstained"]
    value: str | None
    normalized_value: Any | None
    unit: str | None
    confidence: float
    proposed_code: dict[str, Any] | None
    abstention_reason: str | None
    span_start: int | None
    span_end: int | None
    evidence: list[Evidence]
    provider: str
    model: str
    prompt_version: str
    review_state: ReviewState
    seeded_issue: Any | None
    last_decision: LastDecision | None


class DecisionIn(M):
    decision: Decision
    corrected_value: str | None = None  # required for "correct"
    reason: str | None = None  # required for "reject"


class EcrfValue(M):
    field: str
    value: str
    code: dict[str, Any] | None
    source_extraction_id: str | None
    verified_by: str
    verified_at: datetime
    sdv_by: str | None
    sdv_at: datetime | None


class EcrfField(M):
    id: str
    label: str
    section: str | None
    value_type: str | None
    required: bool
    unit: str | None
    terminology: dict[str, Any] | None
    help: str | None
    value: EcrfValue | None
    pending_extraction_id: str | None  # latest pending proposal for this field, if any


class Ecrf(M):
    participant_id: str
    form_id: str
    verified: int
    total: int
    complete_pct: int
    fields: list[EcrfField]


class AuditEvent(M):
    seq: int
    ts: datetime
    actor: str
    role: str
    action: str
    entity_type: str
    entity_id: str
    participant_id: str | None
    before: Any | None
    after: Any | None
    source: Literal["human", "ai"]
    model: str | None
    prompt_version: str | None
    prev_hash: str
    hash: str


class AuditPage(M):
    total: int
    items: list[AuditEvent]


class AuditVerify(M):
    ok: bool
    count: int
    broken_seq: int | None
    reason: str | None
    head_hash: str | None = None


class DataQuery(M):
    id: int
    participant_id: str
    site_id: str
    field_id: str | None
    status: Literal["open", "closed"]
    severity: str
    text: str
    opened_by: str
    created_at: datetime
    closed_by: str | None
    closed_at: datetime | None


class QueryIn(M):
    participant_id: str
    field_id: str | None = None
    severity: Literal["low", "medium", "high"] = "low"
    text: str


class Run(M):
    id: int
    participant_id: str
    document_id: str | None
    status: Literal["queued", "running", "completed", "failed"]
    total: int
    done: int
    error: str | None
    provider: str | None
    model: str | None
    prompt_version: str | None
    created_by: str | None
    created_at: datetime
    finished_at: datetime | None


class RunIn(M):
    document_id: str | None = None


class RunProgressIn(M):
    """Sent by the AI service (role 'service')."""
    status: Literal["running", "completed", "failed"] | None = None
    total: int | None = None
    done: int | None = None
    error: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None


class ExtractionIn(M):
    """One proposal from the AI service. Ingested via POST /runs/{id}/extractions."""
    id: str | None = None
    document_id: str
    field: str
    status: Literal["proposed", "abstained"] = "proposed"
    value: str | None = None
    normalized_value: Any | None = None
    unit: str | None = None
    confidence: float = 0
    proposed_code: dict[str, Any] | None = None
    abstention_reason: str | None = None
    evidence: list[Evidence] = []
    provider: str
    model: str
    prompt_version: str


class DecisionResult(M):
    extraction: Extraction
    ecrf_value: EcrfValue | None
