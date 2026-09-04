import unicodedata
from datetime import date
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.domain.redaction import redact_for_llm
from app.gateway import SupabaseGateway
from app.schemas import (
    AppointmentRequestResponse,
    CreateAppointmentRequest,
    PatientAiQuestionRequest,
    PatientAiSessionResponse,
    PatientDashboardResponse,
    PatientObservationResponse,
    PatientPortalEntryResponse,
    PatientReportResponse,
    PatientSafeEntryResponse,
    PatientScribeJobResponse,
    PatientVisibleTaskResponse,
    SymptomLogRequest,
)

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def gateway(settings: Settings) -> SupabaseGateway:
    return SupabaseGateway(settings)


async def _own_patient(auth: AuthDependency, client: SupabaseGateway) -> dict[str, Any]:
    rows = await client.select(
        "patients",
        auth.access_token,
        {
            "select": "id,clinic_id,synthetic_identifier,display_name",
            "linked_profile_id": f"eq.{auth.user_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient dashboard is available only to a linked patient account",
        )
    return rows[0]


@router.get("/patient/dashboard", response_model=PatientDashboardResponse, tags=["patient portal"])
async def patient_dashboard(
    auth: AuthDependency,
    settings: SettingsDependency,
) -> PatientDashboardResponse:
    client = gateway(settings)
    patient = await _own_patient(auth, client)
    patient_id = str(patient["id"])
    safe_entries = await client.select(
        "entries",
        auth.access_token,
        {
            "select": "id,entry_type,content,occurred_at",
            "patient_id": f"eq.{patient_id}",
            "visibility": "eq.patient_facing",
            "entry_type": "in.(patient_summary,patient_instruction)",
            "order": "occurred_at.desc,id.desc",
            "limit": "100",
        },
    )
    own_updates = await client.select(
        "entries",
        auth.access_token,
        {
            "select": "id,entry_type,content,occurred_at",
            "patient_id": f"eq.{patient_id}",
            "author_id": f"eq.{auth.user_id}",
            "entry_type": "eq.patient_insight",
            "order": "occurred_at.desc,id.desc",
            "limit": "100",
        },
    )
    appointments = await client.select(
        "appointment_requests",
        auth.access_token,
        {
            "select": "id,preferred_date,time_preference,reason_category,note,status,created_at",
            "patient_id": f"eq.{patient_id}",
            "requested_by": f"eq.{auth.user_id}",
            "order": "created_at.desc",
            "limit": "25",
        },
    )
    reports = await client.select(
        "patient_reports",
        auth.access_token,
        {
            "select": "id,title,report_type,status,released_at,patient_safe_summary",
            "patient_id": f"eq.{patient_id}",
            "status": "eq.available",
            "order": "released_at.desc",
            "limit": "25",
        },
    )
    observations = await client.select(
        "patient_observations",
        auth.access_token,
        {
            "select": "observation_type,value,unit,observed_at",
            "patient_id": f"eq.{patient_id}",
            "order": "observed_at.desc",
            "limit": "30",
        },
    )
    tasks = await client.select(
        "care_tasks",
        auth.access_token,
        {
            "select": "id,title,status,due_at,patient_acknowledged_at",
            "patient_id": f"eq.{patient_id}",
            "patient_visible": "eq.true",
            "order": "due_at.asc.nullslast",
            "limit": "25",
        },
    )
    parsed_entries = [PatientSafeEntryResponse.model_validate(row) for row in safe_entries]
    return PatientDashboardResponse(
        patient_id=patient["id"],
        display_name=str(patient["display_name"]),
        synthetic_identifier=str(patient["synthetic_identifier"]),
        clinic_id=patient["clinic_id"],
        summaries=[item for item in parsed_entries if item.entry_type == "patient_summary"],
        instructions=[item for item in parsed_entries if item.entry_type == "patient_instruction"],
        history=[PatientSafeEntryResponse.model_validate(row) for row in own_updates],
        appointments=[AppointmentRequestResponse.model_validate(row) for row in appointments],
        reports=[PatientReportResponse.model_validate(row) for row in reports],
        observations=[PatientObservationResponse.model_validate(row) for row in observations],
        visible_tasks=[PatientVisibleTaskResponse.model_validate(row) for row in tasks],
    )


@router.post(
    "/patient/appointments",
    response_model=AppointmentRequestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["patient portal"],
)
async def create_appointment(
    request: CreateAppointmentRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> AppointmentRequestResponse:
    if request.preferred_date < date.today():
        raise HTTPException(status_code=422, detail="Preferred date cannot be in the past")
    client = gateway(settings)
    patient = await _own_patient(auth, client)
    rows = await client.mutate(
        "POST",
        "appointment_requests",
        auth.access_token,
        payload={
            "clinic_id": str(patient["clinic_id"]),
            "patient_id": str(patient["id"]),
            "requested_by": str(auth.user_id),
            **request.model_dump(mode="json"),
        },
    )
    if not rows:
        raise HTTPException(status_code=502, detail="Appointment request was not created")
    return AppointmentRequestResponse.model_validate(rows[0])


@router.post(
    "/patient/symptoms",
    response_model=PatientPortalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["patient portal"],
)
async def log_symptoms(
    request: SymptomLogRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> PatientPortalEntryResponse:
    client = gateway(settings)
    await _own_patient(auth, client)
    notes = f" Notes: {request.notes.strip()}" if request.notes else ""
    content = unicodedata.normalize(
        "NFC",
        f"Symptom update: {request.symptom.strip()}; severity {request.severity}/10; "
        f"started {request.started_at.isoformat()}.{notes}",
    )
    row = await client.rpc(
        "create_patient_portal_entry",
        auth.access_token,
        {
            "p_kind": "symptom_update",
            "p_content": content,
            "p_structured": {
                "symptom": request.symptom.strip(),
                "severity": request.severity,
                "started_at": request.started_at.isoformat(),
            },
        },
    )
    return PatientPortalEntryResponse(
        entry=PatientSafeEntryResponse.model_validate(row),
        message="Your synthetic symptom update is now visible to your care team.",
    )


@router.post(
    "/patient/ai-question",
    response_model=PatientAiSessionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["patient portal"],
)
async def record_ai_question(
    request: PatientAiQuestionRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> PatientAiSessionResponse:
    client = gateway(settings)
    patient = await _own_patient(auth, client)
    question = unicodedata.normalize("NFC", request.question.strip())
    verified = redact_for_llm(question, known_names=(str(patient["display_name"]),))
    result = await client.rpc(
        "submit_patient_ai_session",
        auth.access_token,
        {
            "p_content": f"Patient question for care team: {question}",
            "p_idempotency_key": request.idempotency_key or f"patient-session:{uuid4()}",
            "p_structured": {
                "redaction_verified": verified.verified,
                "redaction_counts": verified.safe_metadata(),
                "prototype": "non_diagnostic",
            },
        },
    )
    return PatientAiSessionResponse(
        entry=PatientSafeEntryResponse.model_validate(result["entry"]),
        job=PatientScribeJobResponse.model_validate(result["job"]),
        message=(
            "Your question was recorded and AI generation was queued for your care team. "
            "The generated clinical summary remains internal and is not a diagnosis."
        ),
    )


@router.get(
    "/patient/ai-jobs",
    response_model=list[PatientScribeJobResponse],
    tags=["patient portal"],
)
async def list_own_ai_jobs(
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[PatientScribeJobResponse]:
    """Return status-only records without restricted source or output identifiers."""
    value = await gateway(settings).rpc_value(
        "list_own_patient_ai_jobs",
        auth.access_token,
        {},
    )
    if not isinstance(value, list):
        raise HTTPException(status_code=502, detail="AI generation status is unavailable")
    return [PatientScribeJobResponse.model_validate(item) for item in value]
