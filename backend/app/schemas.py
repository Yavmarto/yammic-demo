from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
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
    screening: int = 0
    eligible: int = 0
    consented: int = 0
    screen_fail: int = 0
    ecrf_completeness: float = 0.0
    ai_acceptance_rate: float | None = None
    sdv_done: int = 0
    sdv_pending: int = 0
    kpis: "Kpis | None" = None


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
    site_id: str | None = None
    kpis: Kpis
    sites: list[Site]
    site_comparison: list[Site] = []
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
    screen_fail_reason: str | None = None
    coordinator_signed_by: str | None = None
    coordinator_signed_at: datetime | None = None
    consented_date: date | None = None
    enrolled_by: str | None = None
    enrolled_at: datetime | None = None


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


class ManualEntryIn(M):
    value: str
    document_id: str
    evidence: str


class EcrfValue(M):
    field: str
    value: str
    code: dict[str, Any] | None
    source_extraction_id: str | None
    entry_source: Literal["human", "ai"] = "ai"
    verified_by: str
    verified_at: datetime
    sdv_by: str | None
    sdv_at: datetime | None
    form_version: int = 1


class EcrfField(M):
    id: str
    label: str
    section: str | None
    value_type: str | None
    required: bool
    unit: str | None
    terminology: dict[str, Any] | None
    help: str | None
    min: float | None = None
    max: float | None = None
    allowed_values: list[dict[str, Any]] | None = None
    form_version: int = 1
    value: EcrfValue | None
    pending_extraction_id: str | None  # latest pending proposal for this field, if any


class Ecrf(M):
    participant_id: str
    form_id: str
    form_version: int = 1
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
    status: Literal["open", "answered", "closed"]
    severity: str
    text: str
    opened_by: str
    created_at: datetime
    rule_id: str | None = None
    answer: str | None = None
    answered_by: str | None = None
    answered_at: datetime | None = None
    closed_by: str | None
    closed_at: datetime | None


class QueryIn(M):
    participant_id: str = Field(min_length=1, max_length=64)
    field_id: str | None = Field(default=None, max_length=64)
    severity: Literal["low", "medium", "high"] = "low"
    text: str = Field(min_length=1, max_length=2000)
    rule_id: str | None = Field(default=None, max_length=32)


class QueryAnswerIn(M):
    answer: str | None = Field(default=None, max_length=2000)
    text: str | None = Field(default=None, max_length=2000)


class SdvIn(M):
    sdv: bool | None = None


class DataQualityRule(M):
    id: str
    name: str
    severity: Literal["low", "medium", "high"]
    field_id: str | None
    description: str


class DataQualityResult(M):
    participant_id: str
    checked: int
    opened: list[DataQuery]


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


CriterionStatus = Literal["met", "not_met", "unknown"]


class ScreeningCriterionCheck(M):
    id: str
    criterion_id: str
    ord: int
    type: Literal["inclusion", "exclusion"]
    text: str
    data_needed: str | None = None
    ai_status: CriterionStatus = "unknown"
    confidence: float = 0.0
    rationale: str | None = None
    document_id: str | None = None
    span_start: int | None = None
    span_end: int | None = None
    evidence: list[Evidence] = []
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    coordinator_status: CriterionStatus | None = None
    effective_status: CriterionStatus = "unknown"
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    note: str | None = None


class Screening(M):
    participant_id: str
    study_id: str
    site_id: str
    status: str
    status_detail: str | None
    screen_fail_reason: str | None = None
    coordinator_signed_by: str | None = None
    coordinator_signed_at: datetime | None = None
    consented_date: date | None = None
    enrolled_date: date | None = None
    enrolled_by: str | None = None
    enrolled_at: datetime | None = None
    met_count: int
    not_met_count: int
    unknown_count: int
    confirmed_count: int
    total_count: int
    criteria: list[ScreeningCriterionCheck]


class ScreeningCriterionConfirmIn(M):
    status: CriterionStatus | None = None
    state: CriterionStatus | None = None
    note: str | None = None


class ScreeningChecksIn(M):
    criterion_id: str
    status: CriterionStatus = "unknown"
    confidence: float = 0.0
    rationale: str | None = None
    document_id: str | None = None
    evidence: list[Evidence] = []
    provider: str = "rules"
    model: str = "rules-v4"
    prompt_version: str = "screen_v1"


class ScreeningSignOffIn(M):
    outcome: Literal["eligible", "screen_fail"] | None = None
    decision: Literal["eligible", "screen_fail"] | None = None
    reason: str | None = None


class ScreeningConsentIn(M):
    consented_date: date | None = None
    note: str | None = None


class ScreeningEnrolIn(M):
    enrolled_date: date | None = None
    note: str | None = None


class ScreenFailIn(M):
    reason: str


class TimelineEvent(M):
    id: str
    category: Literal["surgery", "radiotherapy", "chemotherapy", "scan", "visit", "diagnosis", "lab"]
    title: str
    date: str
    end_date: str | None = None
    status: str | None = None
    detail: str | None = None
    document_id: str | None = None
    document_title: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None


class Timeline(M):
    participant_id: str
    events: list[TimelineEvent]


class FormFieldProposal(M):
    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=256)
    section: str | None = "clinical_status"
    value_type: str | None = "string"
    required: bool = True
    unit: str | None = None
    terminology: dict[str, Any] | None = None
    cdisc: dict[str, Any] | None = None
    min: float | None = None
    max: float | None = None
    allowed_values: list[dict[str, Any]] | None = None
    help: str | None = None
    source_sentence: str | None = None


class CriterionProposal(M):
    id: str = Field(min_length=1, max_length=64)
    type: Literal["inclusion", "exclusion"] = "inclusion"
    text: str = Field(min_length=1, max_length=2000)
    data_needed: str | None = None
    source_sentence: str | None = None


class FormVersionIn(M):
    form_id: str = Field(default="ECRF-GBM-BASELINE", min_length=1, max_length=64)
    protocol_text: str | None = Field(default=None, max_length=200_000)
    fields: list[FormFieldProposal] = []
    criteria: list[CriterionProposal] = []
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    note: str | None = Field(default=None, max_length=2000)


class FormApproveIn(M):
    note: str | None = None


class FormVersion(M):
    id: int
    study_id: str
    form_id: str
    version: int
    status: Literal["proposed", "approved", "rejected"]
    fields: list[dict[str, Any]]
    criteria: list[dict[str, Any]]
    protocol_text: str | None = None
    proposed_by: str
    proposed_at: datetime
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    note: str | None = None

