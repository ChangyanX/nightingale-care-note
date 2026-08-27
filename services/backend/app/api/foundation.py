import unicodedata
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.gateway import SupabaseGateway
from app.schemas import (
    CareTaskResponse,
    CreateEntryRequest,
    GlanceItemResponse,
    GlanceResponse,
    MembershipResponse,
    MeResponse,
    PatientResponse,
    SourceRecordResponse,
    TimelineEntryResponse,
    UpdateEntryRequest,
)

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]
PRIORITY_ORDER = {"urgent": 0, "high": 1, "normal": 2, "low": 3}


def gateway(settings: Settings) -> SupabaseGateway:
    return SupabaseGateway(settings)


async def _get_patient_row(
    patient_id: UUID,
    access_token: str,
    client: SupabaseGateway,
) -> dict[str, Any]:
    rows = await client.select(
        "patients",
        access_token,
        {
            "select": "id,clinic_id,synthetic_identifier,display_name",
            "id": f"eq.{patient_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return rows[0]


async def _get_timeline_rows(
    patient_id: UUID,
    access_token: str,
    client: SupabaseGateway,
) -> list[dict[str, Any]]:
    rows = await client.select(
        "entries",
        access_token,
        {
            "select": (
                "id,clinic_id,patient_id,author_id,author_role,entry_type,visibility,"
                "content,source_record_id,current_version,occurred_at"
            ),
            "patient_id": f"eq.{patient_id}",
            "order": "occurred_at.desc,id.desc",
            "limit": "200",
        },
    )
    source_ids = sorted({str(row["source_record_id"]) for row in rows})
    if not source_ids:
        return rows
    sources = await client.select(
        "source_records",
        access_token,
        {
            "select": "id,source_type,external_reference,occurred_at",
            "id": f"in.({','.join(source_ids)})",
            "limit": "200",
        },
    )
    sources_by_id = {str(source["id"]): source for source in sources}
    for row in rows:
        row["source"] = sources_by_id.get(str(row["source_record_id"]))
    return rows


async def _get_task_rows(
    patient_id: UUID,
    access_token: str,
    client: SupabaseGateway,
    *,
    open_only: bool = False,
) -> list[dict[str, Any]]:
    params = {
        "select": (
            "id,clinic_id,patient_id,source_entry_id,title,assigned_to,created_by,"
            "status,priority,due_at,completed_at,created_at,updated_at"
        ),
        "patient_id": f"eq.{patient_id}",
        "order": "updated_at.desc,id.asc",
        "limit": "100",
    }
    if open_only:
        params["status"] = "in.(open,in_progress)"
    return await client.select("care_tasks", access_token, params)


def _bounded_claim(content: object, *, limit: int = 300) -> str:
    claim = str(content).strip()
    return claim if len(claim) <= limit else f"{claim[: limit - 1].rstrip()}…"


@router.get("/me", response_model=MeResponse, tags=["identity"])
async def me(auth: AuthDependency, settings: SettingsDependency) -> MeResponse:
    client = gateway(settings)
    profiles = await client.select(
        "profiles",
        auth.access_token,
        {"select": "id,display_name", "id": f"eq.{auth.user_id}", "limit": "1"},
    )
    if not profiles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    memberships = await client.select(
        "clinic_memberships",
        auth.access_token,
        {"select": "clinic_id,role", "profile_id": f"eq.{auth.user_id}"},
    )
    return MeResponse(
        id=auth.user_id,
        email=auth.email,
        display_name=str(profiles[0]["display_name"]),
        memberships=[MembershipResponse.model_validate(item) for item in memberships],
    )


@router.get("/patients", response_model=list[PatientResponse], tags=["patients"])
async def list_patients(
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[PatientResponse]:
    rows = await gateway(settings).select(
        "patients",
        auth.access_token,
        {
            "select": "id,clinic_id,synthetic_identifier,display_name",
            "order": "display_name.asc",
            "limit": "100",
        },
    )
    return [PatientResponse.model_validate(row) for row in rows]


@router.get("/patients/{patient_id}", response_model=PatientResponse, tags=["patients"])
async def get_patient(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> PatientResponse:
    row = await _get_patient_row(patient_id, auth.access_token, gateway(settings))
    return PatientResponse.model_validate(row)


@router.get(
    "/patients/{patient_id}/timeline",
    response_model=list[TimelineEntryResponse],
    tags=["patients"],
)
async def get_timeline(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[TimelineEntryResponse]:
    client = gateway(settings)
    await _get_patient_row(patient_id, auth.access_token, client)
    rows = await _get_timeline_rows(patient_id, auth.access_token, client)
    return [TimelineEntryResponse.model_validate(row) for row in rows]


@router.get(
    "/patients/{patient_id}/tasks",
    response_model=list[CareTaskResponse],
    tags=["patients"],
)
async def get_tasks(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[CareTaskResponse]:
    client = gateway(settings)
    await _get_patient_row(patient_id, auth.access_token, client)
    rows = await _get_task_rows(patient_id, auth.access_token, client)
    return [CareTaskResponse.model_validate(row) for row in rows]


@router.get(
    "/patients/{patient_id}/glance",
    response_model=GlanceResponse,
    tags=["patients"],
)
async def get_glance(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> GlanceResponse:
    client = gateway(settings)
    await _get_patient_row(patient_id, auth.access_token, client)
    timeline_rows = await _get_timeline_rows(patient_id, auth.access_token, client)
    open_tasks = await _get_task_rows(patient_id, auth.access_token, client, open_only=True)
    entries_by_type: dict[str, dict[str, Any]] = {}
    entries_by_id: dict[str, dict[str, Any]] = {}
    for row in timeline_rows:
        entries_by_id[str(row["id"])] = row
        entries_by_type.setdefault(str(row["entry_type"]), row)

    items: list[GlanceItemResponse] = []
    concern = entries_by_type.get("clinician_note") or entries_by_type.get("staff_note")
    if concern:
        items.append(
            GlanceItemResponse(
                kind="current_concern",
                claim=_bounded_claim(concern["content"]),
                importance_reason="Latest clinician/staff assessment of the active concern",
                status="documented",
                occurred_at=concern["occurred_at"],
                source_entry_id=concern["id"],
                source=SourceRecordResponse.model_validate(concern["source"])
                if concern.get("source")
                else None,
            )
        )

    recent_change = entries_by_type.get("patient_insight")
    if recent_change:
        items.append(
            GlanceItemResponse(
                kind="recent_change",
                claim=_bounded_claim(recent_change["content"]),
                importance_reason="Newest patient-provided change since the assessment",
                status="patient_reported",
                occurred_at=recent_change["occurred_at"],
                source_entry_id=recent_change["id"],
                source=SourceRecordResponse.model_validate(recent_change["source"])
                if recent_change.get("source")
                else None,
            )
        )

    if open_tasks:
        open_tasks.sort(
            key=lambda task: (
                PRIORITY_ORDER.get(str(task["priority"]), 99),
                str(task.get("due_at") or "9999"),
                str(task["id"]),
            )
        )
        task = open_tasks[0]
        source_entry = entries_by_id.get(str(task.get("source_entry_id")))
        if source_entry:
            items.append(
                GlanceItemResponse(
                    kind="open_action",
                    claim=_bounded_claim(task["title"]),
                    importance_reason=(
                        f"{str(task['priority']).capitalize()}-priority unresolved care task"
                    ),
                    status=str(task["status"]),
                    occurred_at=task["updated_at"],
                    source_entry_id=source_entry["id"],
                    task_id=task["id"],
                    source=SourceRecordResponse.model_validate(source_entry["source"])
                    if source_entry.get("source")
                    else None,
                )
            )

    patient_question = entries_by_type.get("ai_patient_session_summary")
    if patient_question:
        items.append(
            GlanceItemResponse(
                kind="patient_question",
                claim=_bounded_claim(patient_question["content"]),
                importance_reason="Unresolved question captured from the AI-patient session",
                status="unresolved",
                occurred_at=patient_question["occurred_at"],
                source_entry_id=patient_question["id"],
                source=SourceRecordResponse.model_validate(patient_question["source"])
                if patient_question.get("source")
                else None,
            )
        )

    return GlanceResponse(patient_id=patient_id, items=items[:6])


@router.post(
    "/entries",
    response_model=TimelineEntryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["entries"],
)
async def create_entry(
    request: CreateEntryRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> TimelineEntryResponse:
    normalized_content = unicodedata.normalize("NFC", request.content.strip())
    payload: dict[str, Any] = {
        "p_patient_id": str(request.patient_id),
        "p_entry_type": request.entry_type,
        "p_visibility": request.visibility,
        "p_content": normalized_content,
    }
    if request.occurred_at is not None:
        payload["p_occurred_at"] = request.occurred_at.isoformat()
    row = await gateway(settings).rpc("create_manual_entry", auth.access_token, payload)
    return TimelineEntryResponse.model_validate(row)


@router.patch("/entries/{entry_id}", response_model=TimelineEntryResponse, tags=["entries"])
async def update_entry(
    entry_id: UUID,
    request: UpdateEntryRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> TimelineEntryResponse:
    row = await gateway(settings).rpc(
        "update_entry",
        auth.access_token,
        {
            "p_entry_id": str(entry_id),
            "p_expected_version": request.expected_version,
            "p_content": unicodedata.normalize("NFC", request.content.strip()),
            "p_change_reason": request.change_reason,
        },
    )
    return TimelineEntryResponse.model_validate(row)
