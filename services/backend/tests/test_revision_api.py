from typing import Any
from uuid import UUID

import httpx
import pytest

from app.api import revisions
from app.auth import AuthContext, get_auth_context
from app.main import app

ENTRY_ID = "70000000-0000-0000-0000-000000000002"
SECTION_ID = "80000000-0000-0000-0000-000000000001"
CLINIC_ID = "10000000-0000-0000-0000-000000000001"
PATIENT_ID = "40000000-0000-0000-0000-000000000001"
USER_ID = UUID("20000000-0000-0000-0000-000000000003")


class RevisionGateway:
    def __init__(self, *, expose_versions: bool = True) -> None:
        self.expose_versions = expose_versions
        self.rpc_calls: list[tuple[str, dict[str, Any]]] = []

    async def select(
        self,
        table: str,
        access_token: str,
        params: dict[str, str],
    ) -> list[dict[str, Any]]:
        assert access_token == "caller-token"
        if table in ("entries", "note_sections"):
            return [
                {
                    "id": params["id"].removeprefix("eq."),
                    "content": "Current text",
                    "current_version": 2,
                }
            ]
        if table in ("entry_versions", "section_versions"):
            if not self.expose_versions:
                return []
            resource_key = "entry_id" if table == "entry_versions" else "section_id"
            resource_id = params[resource_key].removeprefix("eq.")
            rows = [
                {
                    resource_key: resource_id,
                    "version_number": 2,
                    "content_snapshot": "Current text",
                    "changed_by": str(USER_ID),
                    "changed_by_role": "clinician",
                    "change_reason": "Clarified",
                    "created_at": "2026-08-27T10:00:00+08:00",
                },
                {
                    resource_key: resource_id,
                    "version_number": 1,
                    "content_snapshot": "Earlier text",
                    "changed_by": str(USER_ID),
                    "changed_by_role": "clinician",
                    "change_reason": "Initial version",
                    "created_at": "2026-08-26T10:00:00+08:00",
                },
            ]
            requested = params.get("version_number")
            return (
                rows
                if requested is None
                else [row for row in rows if requested == f"eq.{row['version_number']}"]
            )
        raise AssertionError(f"Unexpected table: {table}")

    async def rpc(
        self,
        function_name: str,
        access_token: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        assert access_token == "caller-token"
        self.rpc_calls.append((function_name, payload))
        if function_name == "revert_entry":
            return {
                "id": ENTRY_ID,
                "clinic_id": CLINIC_ID,
                "patient_id": PATIENT_ID,
                "author_id": str(USER_ID),
                "author_role": "clinician",
                "entry_type": "clinician_note",
                "visibility": "internal",
                "content": "Earlier text",
                "source_record_id": "60000000-0000-0000-0000-000000000002",
                "current_version": 3,
                "occurred_at": "2026-08-24T09:30:00+08:00",
            }
        return {
            "id": SECTION_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": PATIENT_ID,
            "care_note_id": "50000000-0000-0000-0000-000000000001",
            "section_type": "assessment",
            "owner_role": "clinician",
            "created_by": str(USER_ID),
            "visibility": "internal",
            "content": "Earlier text",
            "current_version": 3,
            "created_at": "2026-08-26T10:00:00+08:00",
            "updated_at": "2026-08-27T10:00:00+08:00",
        }


async def auth_override() -> AuthContext:
    return AuthContext(
        user_id=USER_ID, email="clinician@example.invalid", access_token="caller-token"
    )


@pytest.fixture(autouse=True)
def override_auth() -> None:
    app.dependency_overrides[get_auth_context] = auth_override
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_entry_history_is_bounded_and_newest_first(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = RevisionGateway()
    monkeypatch.setattr(revisions, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/entries/{ENTRY_ID}/versions")

    assert response.status_code == 200
    assert [item["version_number"] for item in response.json()] == [2, 1]
    assert response.json()[0]["resource_type"] == "entry"


@pytest.mark.asyncio
async def test_comparison_uses_only_authorized_snapshots(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = RevisionGateway()
    monkeypatch.setattr(revisions, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/entries/{ENTRY_ID}/versions/1/comparison")

    assert response.status_code == 200
    assert response.json()["has_changes"] is True
    assert "-Earlier text" in response.json()["unified_diff"]
    assert "+Current text" in response.json()["unified_diff"]


@pytest.mark.asyncio
async def test_hidden_revision_returns_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = RevisionGateway(expose_versions=False)
    monkeypatch.setattr(revisions, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/entries/{ENTRY_ID}/versions/1/comparison")

    assert response.status_code == 404
    assert response.json() == {"detail": "Revision not found"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "function_name", "resource_parameter"),
    [
        (f"/entries/{ENTRY_ID}/revert", "revert_entry", "p_entry_id"),
        (f"/sections/{SECTION_ID}/revert", "revert_section", "p_section_id"),
    ],
)
async def test_revert_delegates_atomic_version_check(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    function_name: str,
    resource_parameter: str,
) -> None:
    fake = RevisionGateway()
    monkeypatch.setattr(revisions, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            path,
            json={"source_version": 1, "expected_version": 2, "change_reason": "Restore"},
        )

    assert response.status_code == 200
    assert response.json()["current_version"] == 3
    assert fake.rpc_calls == [
        (
            function_name,
            {
                resource_parameter: ENTRY_ID if function_name == "revert_entry" else SECTION_ID,
                "p_source_version": 1,
                "p_expected_version": 2,
                "p_change_reason": "Restore",
            },
        )
    ]


@pytest.mark.asyncio
async def test_revert_rejects_non_positive_versions_before_rpc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = RevisionGateway()
    monkeypatch.setattr(revisions, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/entries/{ENTRY_ID}/revert",
            json={"source_version": 0, "expected_version": 2},
        )

    assert response.status_code == 422
    assert fake.rpc_calls == []
