from difflib import unified_diff
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthDependency
from app.config import Settings, get_settings
from app.gateway import SupabaseGateway
from app.schemas import (
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
        "limit": "100",
    }
    if version_number is not None:
        params["version_number"] = f"eq.{version_number}"
        params["limit"] = "1"
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
) -> list[RevisionResponse]:
    rows = await _version_rows(client, access_token, resource_type, resource_id)
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
    return RevisionComparisonResponse(
        resource_type=resource_type,
        resource_id=resource_id,
        selected_version=version_number,
        current_version=current["current_version"],
        selected_content=selected_content,
        current_content=current_content,
        has_changes=selected_content != current_content,
        unified_diff=diff,
    )


@router.get(
    "/entries/{entry_id}/versions",
    response_model=list[RevisionResponse],
    tags=["revisions"],
)
async def list_entry_versions(
    entry_id: UUID,
    auth: AuthDependency,
    settings: SettingsDependency,
) -> list[RevisionResponse]:
    return await _list_versions(gateway(settings), auth.access_token, "entry", entry_id)


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
) -> list[RevisionResponse]:
    return await _list_versions(gateway(settings), auth.access_token, "section", section_id)


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
