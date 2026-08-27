from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.gateway import SupabaseGateway
from app.schemas import CreateScribeJobRequest, ScribeJobResponse

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def gateway(settings: Settings) -> SupabaseGateway:
    return SupabaseGateway(settings)


@router.post(
    "/patients/{patient_id}/scribe-jobs",
    response_model=ScribeJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["AI scribe jobs"],
)
async def create_scribe_job(
    patient_id: UUID,
    request: CreateScribeJobRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> ScribeJobResponse:
    row = await gateway(settings).rpc(
        "submit_ai_scribe_job",
        auth.access_token,
        {
            "p_patient_id": str(patient_id),
            "p_source_record_id": str(request.source_record_id),
            "p_interaction_type": request.interaction_type,
            "p_idempotency_key": request.idempotency_key,
        },
    )
    return ScribeJobResponse.model_validate(row)


@router.get(
    "/scribe-jobs/{job_id}",
    response_model=ScribeJobResponse,
    tags=["AI scribe jobs"],
)
async def get_scribe_job(
    job_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> ScribeJobResponse:
    rows = await gateway(settings).select(
        "ai_jobs",
        auth.access_token,
        {
            "select": (
                "id,clinic_id,patient_id,source_record_id,interaction_type,requested_by,"
                "idempotency_key,status,attempt_count,max_attempts,available_at,claimed_at,"
                "lease_expires_at,completed_at,safe_error_code,output_entry_id,created_at,updated_at"
            ),
            "id": f"eq.{job_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scribe job not found")
    return ScribeJobResponse.model_validate(rows[0])
