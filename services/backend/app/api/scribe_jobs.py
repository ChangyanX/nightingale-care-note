from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.domain.prioritization.personalization import topic_embedding
from app.gateway import SupabaseGateway
from app.infrastructure.llm.usage import aggregate_usage
from app.schemas import (
    CreateScribeJobRequest,
    ImportanceFeedbackRequest,
    ImportancePreferenceResponse,
    ProviderUsageResponse,
    ScribeJobEventResponse,
    ScribeJobResponse,
)

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def gateway(settings: Settings) -> SupabaseGateway:
    return SupabaseGateway(settings)


_JOB_SELECT = (
    "id,clinic_id,patient_id,source_record_id,interaction_type,requested_by,idempotency_key,"
    "status,attempt_count,max_attempts,available_at,claimed_at,lease_expires_at,completed_at,"
    "safe_error_code,output_entry_id,created_at,updated_at,provider_name,model_name,input_tokens,"
    "output_tokens,estimated_cost_usd"
)


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
            "select": _JOB_SELECT,
            "id": f"eq.{job_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scribe job not found")
    return ScribeJobResponse.model_validate(rows[0])


@router.get(
    "/patients/{patient_id}/scribe-jobs",
    response_model=list[ScribeJobResponse],
    tags=["AI scribe jobs"],
)
async def list_patient_scribe_jobs(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[ScribeJobResponse]:
    rows = await gateway(settings).select(
        "ai_jobs",
        auth.access_token,
        {
            "select": _JOB_SELECT,
            "patient_id": f"eq.{patient_id}",
            "order": "created_at.desc",
            "limit": "20",
        },
    )
    responses: list[ScribeJobResponse] = []
    client = gateway(settings)
    for row in rows:
        queue_position = None
        if row.get("status") == "queued":
            value = await client.rpc_value(
                "ai_job_queue_position", auth.access_token, {"p_job_id": str(row["id"])}
            )
            queue_position = value if isinstance(value, int) else None
        responses.append(
            ScribeJobResponse.model_validate({**row, "queue_position": queue_position})
        )
    return responses


@router.get(
    "/patients/{patient_id}/scribe-job-events",
    response_model=list[ScribeJobEventResponse],
    tags=["AI scribe jobs"],
)
async def list_patient_scribe_job_events(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[ScribeJobEventResponse]:
    rows = await gateway(settings).select(
        "ai_job_events",
        auth.access_token,
        {
            "select": "id,job_id,event_kind,created_at",
            "patient_id": f"eq.{patient_id}",
            "order": "created_at.asc",
            "limit": "200",
        },
    )
    return [ScribeJobEventResponse.model_validate(row) for row in rows]


@router.post(
    "/scribe-jobs/{job_id}/cancel",
    response_model=ScribeJobResponse,
    tags=["AI scribe jobs"],
)
async def cancel_scribe_job(
    job_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> ScribeJobResponse:
    row = await gateway(settings).rpc(
        "cancel_ai_scribe_job", auth.access_token, {"p_job_id": str(job_id)}
    )
    return ScribeJobResponse.model_validate(row)


@router.get("/scribe-jobs/{job_id}/queue-position", tags=["AI scribe jobs"])
async def get_scribe_job_queue_position(
    job_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> dict[str, int | None]:
    value = await gateway(settings).rpc_value(
        "ai_job_queue_position", auth.access_token, {"p_job_id": str(job_id)}
    )
    return {"queue_position": value if isinstance(value, int) else None}


@router.get(
    "/provider-usage",
    response_model=list[ProviderUsageResponse],
    tags=["AI scribe jobs"],
)
async def provider_usage_dashboard(
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[dict[str, str | int | float]]:
    rows = await gateway(settings).select(
        "ai_jobs",
        auth.access_token,
        {
            "select": (
                "provider_name,model_name,input_tokens,output_tokens,estimated_cost_usd,"
                "claimed_at,completed_at"
            ),
            "status": "eq.succeeded",
            "limit": "1000",
        },
    )
    usage_rows: list[dict[str, object]] = []
    for row in rows:
        claimed = row.get("claimed_at")
        completed = row.get("completed_at")
        latency_ms = 0.0
        if isinstance(claimed, str) and isinstance(completed, str):
            from datetime import datetime

            latency_ms = (
                datetime.fromisoformat(completed) - datetime.fromisoformat(claimed)
            ).total_seconds() * 1000
        usage_rows.append(
            {
                "provider": row.get("provider_name"),
                "model": row.get("model_name"),
                "input_tokens": row.get("input_tokens"),
                "output_tokens": row.get("output_tokens"),
                "estimated_cost_usd": row.get("estimated_cost_usd"),
                "latency_ms": latency_ms,
            }
        )
    return [
        {
            "provider": item.provider,
            "model": item.model,
            "calls": item.calls,
            "input_tokens": item.input_tokens,
            "output_tokens": item.output_tokens,
            "average_latency_ms": item.average_latency_ms,
            "estimated_cost_usd": item.estimated_cost_usd,
        }
        for item in aggregate_usage(usage_rows)
    ]


@router.get(
    "/importance-preferences",
    response_model=list[ImportancePreferenceResponse],
    tags=["adaptive importance"],
)
async def list_importance_preferences(
    clinic_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[ImportancePreferenceResponse]:
    rows = await gateway(settings).select(
        "importance_preferences",
        auth.access_token,
        {
            "select": "id,clinic_id,profile_id,topic,weight,updated_at",
            "clinic_id": f"eq.{clinic_id}",
            "profile_id": f"eq.{auth.user_id}",
            "order": "updated_at.desc",
            "limit": "100",
        },
    )
    return [ImportancePreferenceResponse.model_validate(row) for row in rows]


@router.post(
    "/importance-feedback",
    response_model=ImportancePreferenceResponse,
    tags=["adaptive importance"],
)
async def record_importance_feedback(
    request: ImportanceFeedbackRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> ImportancePreferenceResponse:
    row = await gateway(settings).rpc(
        "record_importance_feedback",
        auth.access_token,
        {
            "p_event_id": str(request.event_id),
            "p_clinic_id": str(request.clinic_id),
            "p_topic": request.topic,
            "p_feedback_kind": request.feedback_kind,
            "p_embedding": list(topic_embedding(request.topic)),
        },
    )
    return ImportancePreferenceResponse.model_validate(row)


@router.delete(
    "/importance-preferences/{clinic_id}",
    tags=["adaptive importance"],
)
async def reset_importance_preferences(
    clinic_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> dict[str, int]:
    value = await gateway(settings).rpc_value(
        "reset_importance_preferences",
        auth.access_token,
        {"p_clinic_id": str(clinic_id)},
    )
    return {"deleted_preferences": value if isinstance(value, int) else 0}
