from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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
    memberships: list[MembershipResponse]


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
