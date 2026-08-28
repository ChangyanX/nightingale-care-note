from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
from pglast import parse_sql

from app.api import collaboration
from app.auth import AuthContext, get_auth_context
from app.main import app

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "supabase/migrations/202608280004_comment_actions.sql"
USER_ID = UUID("20000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("20000000-0000-0000-0000-000000000002")
PATIENT_ID = UUID("40000000-0000-0000-0000-000000000001")
COMMENT_ID = UUID("90000000-0000-0000-0000-000000000001")


async def clinician_auth() -> AuthContext:
    return AuthContext(user_id=USER_ID, email="clinician@example.test", access_token="test-token")


@pytest.fixture(autouse=True)
def override_auth() -> None:
    app.dependency_overrides[get_auth_context] = clinician_auth
    yield
    app.dependency_overrides.clear()


def comment_row() -> dict[str, Any]:
    return {
        "id": str(COMMENT_ID),
        "clinic_id": "10000000-0000-0000-0000-000000000001",
        "patient_id": str(PATIENT_ID),
        "entry_id": "70000000-0000-0000-0000-000000000001",
        "section_id": None,
        "parent_comment_id": None,
        "author_id": str(USER_ID),
        "body": "Please confirm the follow-up interval.",
        "body_format": "plain",
        "status": "open",
        "assigned_to": None,
        "source_version_id": None,
        "source_start_offset": None,
        "source_end_offset": None,
        "quoted_text": None,
        "created_at": "2026-08-28T09:00:00+08:00",
        "resolved_at": None,
    }


class CommentGateway:
    def __init__(self) -> None:
        self.rpc_call: tuple[str, dict[str, Any]] | None = None

    async def select(
        self, table: str, access_token: str, params: dict[str, str]
    ) -> list[dict[str, Any]]:
        assert access_token == "test-token"
        if table == "comments":
            assert params["deleted_at"] == "is.null"
            return [comment_row()]
        if table == "comment_reactions":
            assert params["patient_id"] == f"eq.{PATIENT_ID}"
            return [
                {
                    "comment_id": str(COMMENT_ID),
                    "profile_id": str(USER_ID),
                    "reaction": "acknowledged",
                },
                {
                    "comment_id": str(COMMENT_ID),
                    "profile_id": str(OTHER_USER_ID),
                    "reaction": "acknowledged",
                },
                {
                    "comment_id": str(COMMENT_ID),
                    "profile_id": str(OTHER_USER_ID),
                    "reaction": "question",
                },
            ]
        raise AssertionError(f"Unexpected table: {table}")

    async def rpc(
        self, function_name: str, access_token: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        assert access_token == "test-token"
        self.rpc_call = (function_name, payload)
        return comment_row()


@pytest.mark.asyncio
async def test_comment_list_includes_counts_and_current_user_reactions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = CommentGateway()
    monkeypatch.setattr(collaboration, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/patients/{PATIENT_ID}/comments")

    assert response.status_code == 200
    comment = response.json()[0]
    assert comment["reaction_counts"] == {"acknowledged": 2, "agree": 0, "question": 1}
    assert comment["my_reactions"] == ["acknowledged"]


@pytest.mark.asyncio
async def test_delete_comment_uses_author_checked_soft_delete_rpc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = CommentGateway()
    monkeypatch.setattr(collaboration, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(f"/comments/{COMMENT_ID}")

    assert response.status_code == 204
    assert fake.rpc_call == ("delete_own_comment", {"p_comment_id": str(COMMENT_ID)})


def test_comment_action_migration_preserves_audit_context_and_authorization() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert parse_sql(sql)
    assert "target.author_id <> auth.uid()" in sql
    assert "Only the author can delete this comment" in sql
    assert "security definer" in sql
    assert "set body = '[Comment deleted by author]'" in sql
    assert "deleted_at = now()" in sql
    assert "delete from public.comments" not in sql
    assert "profile_id = auth.uid()" in sql
    assert "array['staff', 'clinician', 'admin']" in sql
    assert "alter publication supabase_realtime add table public.comment_reactions" in sql
