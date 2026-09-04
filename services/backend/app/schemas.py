from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "nightingale-api"


ClinicRole = Literal["staff", "clinician", "admin"]
EntryVisibility = Literal["internal", "patient_facing"]
CareTaskStatus = Literal["open", "in_progress", "completed", "cancelled"]
CareTaskPriority = Literal["low", "normal", "high", "urgent"]
ManualEntryType = Literal[
    "staff_note",
    "clinician_note",
    "patient_insight",
    "patient_summary",
    "patient_instruction",
]


class MembershipResponse(BaseModel):
    clinic_id: UUID
    role: ClinicRole


class MeResponse(BaseModel):
    id: UUID
    email: str | None
    display_name: str
    preferred_name: str
    memberships: list[MembershipResponse]
    linked_patient_id: UUID | None = None
    account_kind: Literal["clinic_user", "patient"]
    landing_path: Literal["/patients", "/patient"]


class AccountProfileResponse(BaseModel):
    id: UUID
    email: str | None
    display_name: str
    preferred_name: str
    birth_date: date | None
    avatar_path: str | None
    avatar_url: str | None = None
    memberships: list[MembershipResponse]
    linked_patient_id: UUID | None = None


class UpdateAccountProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferred_name: str | None = Field(default=None, min_length=1, max_length=80)
    birth_date: date | None = None


class AvatarUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=120)
    content_type: Literal["image/png", "image/jpeg", "image/webp"]
    data_base64: str = Field(min_length=4, max_length=1_500_000)


class AvatarUploadResponse(BaseModel):
    avatar_path: str
    avatar_url: str


class PatientResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    synthetic_identifier: str
    display_name: str


class SourceRecordResponse(BaseModel):
    id: UUID
    source_type: str
    external_reference: str | None
    occurred_at: datetime


class TimelineEntryResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    author_id: UUID | None
    author_role: Literal["patient", "staff", "clinician", "system"]
    entry_type: str
    visibility: EntryVisibility
    content: str
    source_record_id: UUID
    current_version: int
    occurred_at: datetime
    source: SourceRecordResponse | None = None


class CareTaskResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    source_entry_id: UUID | None
    title: str
    assigned_to: UUID | None
    created_by: UUID
    status: CareTaskStatus
    priority: CareTaskPriority
    category: Literal[
        "clinical_review", "medication", "monitoring", "administrative", "follow_up"
    ] = "follow_up"
    patient_visible: bool = False
    patient_acknowledged_at: datetime | None = None
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class GlanceItemResponse(BaseModel):
    kind: Literal["current_concern", "recent_change", "open_action", "patient_question"]
    claim: str
    importance_reason: str
    status: str
    occurred_at: datetime
    source_entry_id: UUID
    task_id: UUID | None = None
    source: SourceRecordResponse | None = None


class GlanceResponse(BaseModel):
    patient_id: UUID
    items: list[GlanceItemResponse] = Field(max_length=6)


class CreateEntryRequest(BaseModel):
    patient_id: UUID
    entry_type: ManualEntryType
    visibility: EntryVisibility = "internal"
    content: str = Field(min_length=1, max_length=20_000)
    occurred_at: datetime | None = None


class UpdateEntryRequest(BaseModel):
    expected_version: int = Field(gt=0)
    content: str = Field(min_length=1, max_length=20_000)
    change_reason: str | None = Field(default=None, max_length=500)


class NoteSectionResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    care_note_id: UUID
    section_type: str
    owner_role: Literal["staff", "clinician", "system"]
    created_by: UUID | None
    visibility: EntryVisibility
    content: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class RevisionResponse(BaseModel):
    resource_type: Literal["entry", "section"]
    resource_id: UUID
    version_number: int
    content_snapshot: str
    changed_by: UUID | None
    changed_by_role: Literal["patient", "staff", "clinician", "system"]
    change_reason: str | None
    created_at: datetime


class RevisionComparisonResponse(BaseModel):
    resource_type: Literal["entry", "section"]
    resource_id: UUID
    selected_version: int
    current_version: int
    selected_content: str
    current_content: str
    has_changes: bool
    unified_diff: str
    word_diff: list[dict[str, str]] = Field(default_factory=list)


class MergeHintRequest(BaseModel):
    base_content: str = Field(max_length=20_000)
    proposed_content: str = Field(max_length=20_000)


class MergeHintResponse(BaseModel):
    current_version: int
    merged_content: str
    has_conflict: bool
    strategy: Literal["proposed", "current", "conflict_markers"]


class RevertRequest(BaseModel):
    source_version: int = Field(gt=0)
    expected_version: int = Field(gt=0)
    change_reason: str | None = Field(default=None, max_length=500)


class UpdateCareTaskRequest(BaseModel):
    status: CareTaskStatus | None = None
    priority: CareTaskPriority | None = None
    category: (
        Literal["clinical_review", "medication", "monitoring", "administrative", "follow_up"] | None
    ) = None
    assigned_to: UUID | None = None
    due_at: datetime | None = None
    patient_visible: bool | None = None


class CommentReactionCounts(BaseModel):
    acknowledged: int = Field(default=0, ge=0)
    agree: int = Field(default=0, ge=0)
    question: int = Field(default=0, ge=0)


class CommentResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    entry_id: UUID | None
    section_id: UUID | None
    parent_comment_id: UUID | None
    author_id: UUID
    body: str
    body_format: Literal["plain", "markdown"] = "plain"
    status: Literal["open", "resolved"]
    assigned_to: UUID | None
    source_version_id: UUID | None = None
    source_start_offset: int | None = None
    source_end_offset: int | None = None
    quoted_text: str | None = None
    created_at: datetime
    resolved_at: datetime | None
    reaction_counts: CommentReactionCounts = Field(default_factory=CommentReactionCounts)
    my_reactions: list[Literal["acknowledged", "agree", "question"]] = Field(
        default_factory=list
    )


class CreateCommentRequest(BaseModel):
    entry_id: UUID | None = None
    section_id: UUID | None = None
    parent_comment_id: UUID | None = None
    body: str = Field(min_length=1, max_length=5_000)
    body_format: Literal["plain", "markdown"] = "plain"
    mention_ids: list[UUID] = Field(default_factory=list, max_length=20)
    assignee_ids: list[UUID] = Field(default_factory=list, max_length=20)
    source_version_id: UUID | None = None
    source_start_offset: int | None = Field(default=None, ge=0)
    source_end_offset: int | None = Field(default=None, gt=0)
    quoted_text: str | None = Field(default=None, max_length=1_000)


class CommentReactionRequest(BaseModel):
    reaction: Literal["acknowledged", "agree", "question"]


class HighlightResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    source_entry_id: UUID
    source_version_id: UUID
    source_start_offset: int
    source_end_offset: int
    quoted_text: str
    normalized_claim: str
    risk_level: Literal["information", "attention", "critical"]
    category: Literal[
        "risk", "symptom", "medication", "care_gap", "patient_context", "follow_up"
    ] = "risk"
    risk_reason: str
    score: float
    status: Literal["suggested", "accepted", "rejected"]
    generated_by: Literal["rule", "ai", "clinician"]
    duplicate_group_id: UUID | None = None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class BulkHighlightReviewRequest(BaseModel):
    highlight_ids: list[UUID] = Field(min_length=1, max_length=100)
    status: Literal["accepted", "rejected"]


class BatchRevertOperation(BaseModel):
    entry_id: UUID
    source_version: int = Field(gt=0)
    expected_version: int = Field(gt=0)
    change_reason: str | None = Field(default=None, max_length=500)


class BatchRevertRequest(BaseModel):
    operations: list[BatchRevertOperation] = Field(min_length=1, max_length=20)


class NotificationResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID | None
    recipient_id: UUID
    event_type: Literal[
        "mention",
        "assignment",
        "ai_job_completed",
        "care_update",
        "appointment_update",
        "report_released",
    ]
    resource_type: str
    resource_id: UUID
    status: Literal["pending", "delivered", "failed", "dismissed"]
    read_at: datetime | None = None
    created_at: datetime


class PatientSafeEntryResponse(BaseModel):
    id: UUID
    entry_type: Literal["patient_summary", "patient_instruction", "patient_insight"]
    content: str
    occurred_at: datetime


class AppointmentRequestResponse(BaseModel):
    id: UUID
    preferred_date: date
    time_preference: Literal["morning", "afternoon", "either"]
    reason_category: Literal["follow_up", "new_symptom", "medication", "other"]
    note: str | None
    status: Literal["requested", "confirmed", "declined", "cancelled"]
    created_at: datetime


class CreateAppointmentRequest(BaseModel):
    preferred_date: date
    time_preference: Literal["morning", "afternoon", "either"] = "either"
    reason_category: Literal["follow_up", "new_symptom", "medication", "other"]
    note: str | None = Field(default=None, max_length=500)


class PatientReportResponse(BaseModel):
    id: UUID
    title: str
    report_type: Literal["lab", "imaging", "care_plan", "other"]
    status: Literal["preparing", "available", "withdrawn"]
    released_at: datetime | None
    patient_safe_summary: str | None


class PatientObservationResponse(BaseModel):
    observation_type: Literal["peak_flow", "sleep_hours", "symptom_score"]
    value: float
    unit: str
    observed_at: datetime


class PatientVisibleTaskResponse(BaseModel):
    id: UUID
    title: str
    status: CareTaskStatus
    due_at: datetime | None
    patient_acknowledged_at: datetime | None


class PatientDashboardResponse(BaseModel):
    patient_id: UUID
    display_name: str
    synthetic_identifier: str
    clinic_id: UUID
    summaries: list[PatientSafeEntryResponse]
    instructions: list[PatientSafeEntryResponse]
    history: list[PatientSafeEntryResponse]
    appointments: list[AppointmentRequestResponse]
    reports: list[PatientReportResponse]
    observations: list[PatientObservationResponse]
    visible_tasks: list[PatientVisibleTaskResponse]


class SymptomLogRequest(BaseModel):
    symptom: str = Field(min_length=1, max_length=120)
    severity: int = Field(ge=0, le=10)
    started_at: datetime
    notes: str | None = Field(default=None, max_length=1000)


class PatientAiQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    idempotency_key: str | None = Field(
        default=None,
        min_length=8,
        max_length=200,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )


class PatientPortalEntryResponse(BaseModel):
    entry: PatientSafeEntryResponse
    message: str


class PatientSummaryReviewResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    source_entry_id: UUID
    summary_entry_id: UUID | None
    proposed_content: str
    status: Literal["suggested", "accepted", "rejected"]
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class PatientSummaryReviewRequest(BaseModel):
    status: Literal["accepted", "rejected"]


class AuditExportRow(BaseModel):
    id: UUID
    action: str
    resource_type: str
    resource_id: UUID
    actor_role: str
    created_at: datetime
    metadata: dict[str, Any]


AiInteractionType = Literal["doctor_consult", "nurse_consult", "ai_patient_session"]
AiJobStatus = Literal["queued", "processing", "succeeded", "failed", "dead_letter", "cancelled"]


class CreateScribeJobRequest(BaseModel):
    source_record_id: UUID
    interaction_type: AiInteractionType
    idempotency_key: str = Field(min_length=8, max_length=200, pattern=r"^[A-Za-z0-9._:-]+$")


class CreateLiveScribeSessionRequest(BaseModel):
    interaction_type: Literal["doctor_consult", "nurse_consult"]
    transcript: str = Field(min_length=20, max_length=12_000)
    idempotency_key: str = Field(min_length=8, max_length=200, pattern=r"^[A-Za-z0-9._:-]+$")


class ScribeJobResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_id: UUID
    source_record_id: UUID
    interaction_type: AiInteractionType
    requested_by: UUID
    idempotency_key: str
    status: AiJobStatus
    attempt_count: int
    max_attempts: int
    available_at: datetime
    claimed_at: datetime | None
    lease_expires_at: datetime | None
    completed_at: datetime | None
    safe_error_code: str | None
    output_entry_id: UUID | None
    created_at: datetime
    updated_at: datetime
    queue_position: int | None = None
    provider_name: str | None = None
    model_name: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None


class ScribeJobEventResponse(BaseModel):
    id: UUID
    job_id: UUID
    event_kind: Literal[
        "generating", "validating", "persisting", "completed", "retrying", "cancelled"
    ]
    created_at: datetime


class PatientScribeJobResponse(BaseModel):
    id: UUID
    status: AiJobStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    safe_error_code: str | None


class PatientAiSessionResponse(BaseModel):
    entry: PatientSafeEntryResponse
    job: PatientScribeJobResponse
    message: str


class ProviderUsageResponse(BaseModel):
    provider: str
    model: str
    calls: int
    input_tokens: int
    output_tokens: int
    average_latency_ms: float
    estimated_cost_usd: float


FeedbackKind = Literal["accept", "reject", "pin", "edit", "comment"]


class ImportanceFeedbackRequest(BaseModel):
    event_id: UUID
    clinic_id: UUID
    topic: str = Field(min_length=1, max_length=120)
    feedback_kind: FeedbackKind


class ImportancePreferenceResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    profile_id: UUID
    topic: str
    weight: float
    updated_at: datetime
