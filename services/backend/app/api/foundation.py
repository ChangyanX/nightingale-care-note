import unicodedata
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.gateway import SupabaseGateway
from app.schemas import (
    CreateEntryRequest,
    MembershipResponse,
    MeResponse,
    PatientResponse,
    TimelineEntryResponse,
    UpdateEntryRequest,
)

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def gateway(settings: Settings) -> SupabaseGateway:
    return SupabaseGateway(settings)


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
    rows = await gateway(settings).select(
        "patients",
        auth.access_token,
        {
            "select": "id,clinic_id,synthetic_identifier,display_name",
            "id": f"eq.{patient_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return PatientResponse.model_validate(rows[0])


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
    rows = await gateway(settings).select(
        "entries",
        auth.access_token,
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
    return [TimelineEntryResponse.model_validate(row) for row in rows]


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
