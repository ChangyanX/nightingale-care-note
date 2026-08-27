import re
from difflib import SequenceMatcher, unified_diff
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.gateway import SupabaseGateway
from app.schemas import (
    BatchRevertRequest,
    MergeHintRequest,
    MergeHintResponse,
    NoteSectionResponse,
    RevertRequest,
    RevisionComparisonResponse,
    RevisionResponse,
    TimelineEntryResponse,
)

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]
ResourceType = Literal["entry", "section"]


def gateway(settings: Settings) -> SupabaseGateway:
    return SupabaseGateway(settings)


def _revision(row: dict[str, Any], resource_type: ResourceType) -> RevisionResponse:
    resource_key = "entry_id" if resource_type == "entry" else "section_id"
    return RevisionResponse(
        resource_type=resource_type,
        resource_id=row[resource_key],
        version_number=row["version_number"],
        content_snapshot=row["content_snapshot"],
        changed_by=row["changed_by"],
        changed_by_role=row["changed_by_role"],
        change_reason=row["change_reason"],
        created_at=row["created_at"],
    )


async def _version_rows(
    client: SupabaseGateway,
    access_token: str,
    resource_type: ResourceType,
    resource_id: UUID,
    *,
    version_number: int | None = None,
    limit: int = 100,
    before_version: int | None = None,
) -> list[dict[str, Any]]:
    table = "entry_versions" if resource_type == "entry" else "section_versions"
    resource_key = "entry_id" if resource_type == "entry" else "section_id"
    params = {
        "select": (
            f"{resource_key},version_number,content_snapshot,changed_by,"
            "changed_by_role,change_reason,created_at"
        ),
        resource_key: f"eq.{resource_id}",
        "order": "version_number.desc",
        "limit": str(limit),
    }
    if version_number is not None:
        params["version_number"] = f"eq.{version_number}"
        params["limit"] = "1"
    elif before_version is not None:
        params["version_number"] = f"lt.{before_version}"
    return await client.select(table, access_token, params)


async def _current_resource(
    client: SupabaseGateway,
    access_token: str,
    resource_type: ResourceType,
    resource_id: UUID,
) -> dict[str, Any]:
    table = "entries" if resource_type == "entry" else "note_sections"
    rows = await client.select(
        table,
        access_token,
        {
            "select": "id,content,current_version",
            "id": f"eq.{resource_id}",
            "limit": "1",
        },
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return rows[0]


async def _list_versions(
    client: SupabaseGateway,
    access_token: str,
    resource_type: ResourceType,
    resource_id: UUID,
    *,
    limit: int = 50,
    before_version: int | None = None,
) -> list[RevisionResponse]:
    rows = await _version_rows(
        client,
        access_token,
        resource_type,
        resource_id,
        limit=limit,
        before_version=before_version,
    )
    return [_revision(row, resource_type) for row in rows]


async def _comparison(
    client: SupabaseGateway,
    access_token: str,
    resource_type: ResourceType,
    resource_id: UUID,
    version_number: int,
) -> RevisionComparisonResponse:
    current = await _current_resource(
        client,
        access_token,
        resource_type,
        resource_id,
    )
    versions = await _version_rows(
        client,
        access_token,
        resource_type,
        resource_id,
        version_number=version_number,
    )
    if not versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")

    selected_content = str(versions[0]["content_snapshot"])
    current_content = str(current["content"])
    diff = "\n".join(
        unified_diff(
            selected_content.splitlines(),
            current_content.splitlines(),
            fromfile=f"version-{version_number}",
            tofile=f"version-{current['current_version']}",
            lineterm="",
        )
    )
    word_diff = _word_diff(selected_content, current_content)
    return RevisionComparisonResponse(
        resource_type=resource_type,
        resource_id=resource_id,
        selected_version=version_number,
        current_version=current["current_version"],
        selected_content=selected_content,
        current_content=current_content,
        has_changes=selected_content != current_content,
        unified_diff=diff,
        word_diff=word_diff,
    )


def _word_diff(previous: str, current: str) -> list[dict[str, str]]:
    def tokenize(value: str) -> list[str]:
        return re.findall(r"\s+|[\w'’-]+|[^\w\s]", value, flags=re.UNICODE)

    left = tokenize(previous)
    right = tokenize(current)
    result: list[dict[str, str]] = []
    for operation, left_start, left_end, right_start, right_end in SequenceMatcher(
        None, left, right, autojunk=False
    ).get_opcodes():
        if operation in ("equal", "delete", "replace") and left_start != left_end:
            result.append(
                {
                    "kind": "unchanged" if operation == "equal" else "removed",
                    "text": "".join(left[left_start:left_end]),
                }
            )
        if operation in ("insert", "replace") and right_start != right_end:
            result.append({"kind": "added", "text": "".join(right[right_start:right_end])})
    return result


@router.get(
    "/entries/{entry_id}/versions",
    response_model=list[RevisionResponse],
    tags=["revisions"],
)
async def list_entry_versions(
    entry_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
    limit: int = Query(default=50, ge=1, le=100),
    before_version: int | None = Query(default=None, gt=0),
) -> list[RevisionResponse]:
    return await _list_versions(
        gateway(settings),
        auth.access_token,
        "entry",
        entry_id,
        limit=limit,
        before_version=before_version,
    )


@router.get(
    "/entries/{entry_id}/versions/{version_number}/comparison",
    response_model=RevisionComparisonResponse,
    tags=["revisions"],
)
async def compare_entry_version(
    entry_id: UUID,
    version_number: int,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> RevisionComparisonResponse:
    return await _comparison(
        gateway(settings), auth.access_token, "entry", entry_id, version_number
    )


@router.post(
    "/entries/{entry_id}/revert",
    response_model=TimelineEntryResponse,
    tags=["revisions"],
)
async def revert_entry(
    entry_id: UUID,
    request: RevertRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> TimelineEntryResponse:
    row = await gateway(settings).rpc(
        "revert_entry",
        auth.access_token,
        {
            "p_entry_id": str(entry_id),
            "p_source_version": request.source_version,
            "p_expected_version": request.expected_version,
            "p_change_reason": request.change_reason,
        },
    )
    return TimelineEntryResponse.model_validate(row)


@router.get(
    "/sections/{section_id}/versions",
    response_model=list[RevisionResponse],
    tags=["revisions"],
)
async def list_section_versions(
    section_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
    limit: int = Query(default=50, ge=1, le=100),
    before_version: int | None = Query(default=None, gt=0),
) -> list[RevisionResponse]:
    return await _list_versions(
        gateway(settings),
        auth.access_token,
        "section",
        section_id,
        limit=limit,
        before_version=before_version,
    )


@router.get(
    "/sections/{section_id}/versions/{version_number}/comparison",
    response_model=RevisionComparisonResponse,
    tags=["revisions"],
)
async def compare_section_version(
    section_id: UUID,
    version_number: int,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> RevisionComparisonResponse:
    return await _comparison(
        gateway(settings), auth.access_token, "section", section_id, version_number
    )


@router.post(
    "/sections/{section_id}/revert",
    response_model=NoteSectionResponse,
    tags=["revisions"],
)
async def revert_section(
    section_id: UUID,
    request: RevertRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> NoteSectionResponse:
    row = await gateway(settings).rpc(
        "revert_section",
        auth.access_token,
        {
            "p_section_id": str(section_id),
            "p_source_version": request.source_version,
            "p_expected_version": request.expected_version,
            "p_change_reason": request.change_reason,
        },
    )
    return NoteSectionResponse.model_validate(row)


@router.post("/entries/{entry_id}/merge-hint", response_model=MergeHintResponse, tags=["revisions"])
async def entry_merge_hint(
    entry_id: UUID,
    request: MergeHintRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> MergeHintResponse:
    current = await _current_resource(gateway(settings), auth.access_token, "entry", entry_id)
    current_content = str(current["content"])
    if current_content == request.base_content:
        return MergeHintResponse(
            current_version=current["current_version"],
            merged_content=request.proposed_content,
            has_conflict=False,
            strategy="proposed",
        )
    if request.proposed_content == request.base_content:
        return MergeHintResponse(
            current_version=current["current_version"],
            merged_content=current_content,
            has_conflict=False,
            strategy="current",
        )
    merged = (
        "<<<<<<< YOUR EDIT\n"
        + request.proposed_content
        + "\n=======\n"
        + current_content
        + "\n>>>>>>> CURRENT VERSION"
    )
    return MergeHintResponse(
        current_version=current["current_version"],
        merged_content=merged,
        has_conflict=True,
        strategy="conflict_markers",
    )


@router.post(
    "/entries/batch-revert", response_model=list[TimelineEntryResponse], tags=["revisions"]
)
async def batch_revert_entries(
    request: BatchRevertRequest,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[TimelineEntryResponse]:
    value = await gateway(settings).rpc_value(
        "batch_revert_entries",
        auth.access_token,
        {"p_operations": request.model_dump(mode="json")["operations"]},
    )
    if not isinstance(value, list):
        raise HTTPException(status_code=502, detail="Unexpected batch revert response")
    return [TimelineEntryResponse.model_validate(row) for row in value]
