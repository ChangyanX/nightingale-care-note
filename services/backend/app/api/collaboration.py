import csv
import io
from typing import Annotated, Any
from uuid import UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.gateway import SupabaseGateway
from app.schemas import (
    AuditExportRow,
    BulkHighlightReviewRequest,
    CommentReactionRequest,
    CommentResponse,
    CreateCommentRequest,
    HighlightResponse,
    NotificationResponse,
    PatientSummaryReviewRequest,
    PatientSummaryReviewResponse,
)

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]
_DUPLICATE_NAMESPACE = UUID("b8cc1635-f714-4f0b-a31c-229399731d55")


def gateway(settings: Settings) -> SupabaseGateway:
    return SupabaseGateway(settings)


@router.get(
    "/patients/{patient_id}/comments", response_model=list[CommentResponse], tags=["collaboration"]
)
async def list_comments(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[CommentResponse]:
    rows = await gateway(settings).select(
        "comments",
        auth.access_token,
        {
            "select": (
                "id,clinic_id,patient_id,entry_id,section_id,parent_comment_id,author_id,body,"
                "body_format,status,assigned_to,source_version_id,source_start_offset,"
                "source_end_offset,quoted_text,created_at,resolved_at"
            ),
            "patient_id": f"eq.{patient_id}",
            "order": "created_at.asc,id.asc",
            "limit": str(limit),
        },
    )
    return [CommentResponse.model_validate(row) for row in rows]


@router.post(
    "/patients/{patient_id}/comments", response_model=CommentResponse, tags=["collaboration"]
)
async def create_comment(
    patient_id: UUID,
    request: CreateCommentRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> CommentResponse:
    row = await gateway(settings).rpc(
        "create_comment_with_collaboration",
        auth.access_token,
        {
            "p_patient_id": str(patient_id),
            "p_entry_id": str(request.entry_id) if request.entry_id else None,
            "p_section_id": str(request.section_id) if request.section_id else None,
            "p_parent_comment_id": str(request.parent_comment_id)
            if request.parent_comment_id
            else None,
            "p_body": request.body,
            "p_body_format": request.body_format,
            "p_mention_ids": [str(item) for item in request.mention_ids],
            "p_assignee_ids": [str(item) for item in request.assignee_ids],
            "p_source_version_id": str(request.source_version_id)
            if request.source_version_id
            else None,
            "p_source_start_offset": request.source_start_offset,
            "p_source_end_offset": request.source_end_offset,
            "p_quoted_text": request.quoted_text,
        },
    )
    return CommentResponse.model_validate(row)


@router.post("/comments/{comment_id}/reactions", tags=["collaboration"])
async def add_comment_reaction(
    comment_id: UUID,
    request: CommentReactionRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> dict[str, str]:
    client = gateway(settings)
    comments = await client.select(
        "comments",
        auth.access_token,
        {"select": "id,clinic_id,patient_id", "id": f"eq.{comment_id}", "limit": "1"},
    )
    if not comments:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment = comments[0]
    await client.mutate(
        "POST",
        "comment_reactions",
        auth.access_token,
        payload={
            "comment_id": str(comment_id),
            "clinic_id": str(comment["clinic_id"]),
            "patient_id": str(comment["patient_id"]),
            "profile_id": str(auth.user_id),
            "reaction": request.reaction,
        },
    )
    return {"status": "recorded", "reaction": request.reaction}


@router.delete("/comments/{comment_id}/reactions/{reaction}", tags=["collaboration"])
async def remove_comment_reaction(
    comment_id: UUID,
    reaction: str,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> dict[str, str]:
    if reaction not in {"acknowledged", "agree", "question"}:
        raise HTTPException(status_code=422, detail="Invalid reaction")
    await gateway(settings).mutate(
        "DELETE",
        "comment_reactions",
        auth.access_token,
        params={
            "comment_id": f"eq.{comment_id}",
            "profile_id": f"eq.{auth.user_id}",
            "reaction": f"eq.{reaction}",
        },
    )
    return {"status": "removed", "reaction": reaction}


@router.get(
    "/patients/{patient_id}/highlights", response_model=list[HighlightResponse], tags=["highlights"]
)
async def list_highlights(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[HighlightResponse]:
    params = {
        "select": (
            "id,clinic_id,patient_id,source_entry_id,source_version_id,source_start_offset,"
            "source_end_offset,quoted_text,normalized_claim,risk_level,category,risk_reason,score,"
            "status,generated_by,duplicate_group_id,reviewed_by,reviewed_at,created_at"
        ),
        "patient_id": f"eq.{patient_id}",
        "order": "score.desc,created_at.desc",
        "limit": "200",
    }
    if status_filter:
        params["status"] = f"eq.{status_filter}"
    rows = await gateway(settings).select("highlights", auth.access_token, params)
    return [HighlightResponse.model_validate(row) for row in rows]


@router.post("/highlights/bulk-review", response_model=list[HighlightResponse], tags=["highlights"])
async def bulk_review_highlights(
    request: BulkHighlightReviewRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[HighlightResponse]:
    value = await gateway(settings).rpc_value(
        "review_highlights_bulk",
        auth.access_token,
        {
            "p_highlight_ids": [str(item) for item in request.highlight_ids],
            "p_status": request.status,
        },
    )
    if not isinstance(value, list):
        raise HTTPException(status_code=502, detail="Unexpected highlight review response")
    return [HighlightResponse.model_validate(row) for row in value]


@router.get("/patients/{patient_id}/highlight-groups", tags=["highlights"])
async def duplicate_highlight_groups(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[dict[str, Any]]:
    highlights = await list_highlights(patient_id, auth, settings, None)
    groups: list[list[HighlightResponse]] = []
    for highlight in highlights:
        matching: list[int] = []
        claim_key = " ".join(highlight.normalized_claim.casefold().split())
        for index, group in enumerate(groups):
            if any(
                " ".join(item.normalized_claim.casefold().split()) == claim_key
                or (
                    item.source_version_id == highlight.source_version_id
                    and max(item.source_start_offset, highlight.source_start_offset)
                    < min(item.source_end_offset, highlight.source_end_offset)
                )
                for item in group
            ):
                matching.append(index)
        if not matching:
            groups.append([highlight])
            continue
        merged = [highlight]
        for index in reversed(matching):
            merged.extend(groups.pop(index))
        groups.append(merged)
    return [
        {
            "group_id": str(
                uuid5(_DUPLICATE_NAMESPACE, ":".join(sorted(str(item.id) for item in items)))
            ),
            "normalized_claim": items[0].normalized_claim,
            "highlight_ids": [str(item.id) for item in items],
            "count": len(items),
        }
        for items in sorted(groups, key=lambda group: str(min(item.id for item in group)))
    ]


@router.get("/highlight-taxonomy", tags=["highlights"])
async def highlight_taxonomy() -> list[dict[str, str]]:
    return [
        {"category": "risk", "description": "Potential safety or deterioration concern"},
        {"category": "symptom", "description": "Patient symptom or symptom change"},
        {"category": "medication", "description": "Medication use, change, or adherence"},
        {"category": "care_gap", "description": "Missing or overdue follow-through"},
        {"category": "patient_context", "description": "Relevant preference or context"},
        {"category": "follow_up", "description": "Planned review or monitoring"},
    ]


@router.get("/notifications", response_model=list[NotificationResponse], tags=["notifications"])
async def list_notifications(
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[NotificationResponse]:
    rows = await gateway(settings).select(
        "notification_outbox",
        auth.access_token,
        {
            "select": (
                "id,clinic_id,patient_id,recipient_id,event_type,resource_type,resource_id,"
                "status,created_at"
            ),
            "recipient_id": f"eq.{auth.user_id}",
            "order": "created_at.desc",
            "limit": "100",
        },
    )
    return [NotificationResponse.model_validate(row) for row in rows]


@router.post(
    "/notifications/{notification_id}/dismiss",
    response_model=NotificationResponse,
    tags=["notifications"],
)
async def dismiss_notification(
    notification_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> NotificationResponse:
    rows = await gateway(settings).mutate(
        "PATCH",
        "notification_outbox",
        auth.access_token,
        payload={"status": "dismissed"},
        params={"id": f"eq.{notification_id}"},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse.model_validate(rows[0])


@router.get(
    "/patients/{patient_id}/patient-summary-reviews",
    response_model=list[PatientSummaryReviewResponse],
    tags=["AI scribe review"],
)
async def list_patient_summary_reviews(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[PatientSummaryReviewResponse]:
    rows = await gateway(settings).select(
        "patient_summary_reviews",
        auth.access_token,
        {
            "select": (
                "id,clinic_id,patient_id,source_entry_id,summary_entry_id,proposed_content,"
                "status,reviewed_by,reviewed_at,created_at"
            ),
            "patient_id": f"eq.{patient_id}",
            "order": "created_at.desc",
            "limit": "50",
        },
    )
    return [PatientSummaryReviewResponse.model_validate(row) for row in rows]


@router.post(
    "/patient-summary-reviews/{review_id}/review",
    response_model=PatientSummaryReviewResponse,
    tags=["AI scribe review"],
)
async def review_patient_summary(
    review_id: UUID,
    request: PatientSummaryReviewRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> PatientSummaryReviewResponse:
    row = await gateway(settings).rpc(
        "review_patient_summary",
        auth.access_token,
        {"p_review_id": str(review_id), "p_status": request.status},
    )
    return PatientSummaryReviewResponse.model_validate(row)


@router.get("/patients/{patient_id}/audit.csv", tags=["audit"])
async def download_audit_report(
    patient_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> StreamingResponse:
    rows = await gateway(settings).select(
        "audit_events",
        auth.access_token,
        {
            "select": "id,action,resource_type,resource_id,actor_role,created_at,metadata",
            "patient_id": f"eq.{patient_id}",
            "order": "created_at.asc,id.asc",
            "limit": "1000",
        },
    )
    validated = [AuditExportRow.model_validate(row) for row in rows]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "action", "resource_type", "resource_id", "actor_role", "created_at"])
    for row in validated:
        writer.writerow(
            [
                row.id,
                row.action,
                row.resource_type,
                row.resource_id,
                row.actor_role,
                row.created_at.isoformat(),
            ]
        )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"content-disposition": f'attachment; filename="patient-{patient_id}-audit.csv"'},
    )
