from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
from pglast import parse_sql

from app.api import foundation
from app.auth import AuthContext, get_auth_context
from app.main import app

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "supabase/migrations/202608280005_entry_visibility_boundaries.sql"
USER_ID = UUID("20000000-0000-0000-0000-000000000003")
PATIENT_ID = "40000000-0000-0000-0000-000000000001"


async def clinician_auth() -> AuthContext:
    return AuthContext(user_id=USER_ID, email="clinician@example.test", access_token="test-token")


@pytest.fixture(autouse=True)
def override_auth() -> None:
    app.dependency_overrides[get_auth_context] = clinician_auth
    yield
    app.dependency_overrides.clear()


class EntryGateway:
    def __init__(self) -> None:
        self.rpc_calls: list[tuple[str, dict[str, Any]]] = []

    async def rpc(
        self, function_name: str, access_token: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        assert access_token == "test-token"
        self.rpc_calls.append((function_name, payload))
        return {
            "id": "70000000-0000-0000-0000-000000000099",
            "clinic_id": "10000000-0000-0000-0000-000000000001",
            "patient_id": PATIENT_ID,
            "author_id": str(USER_ID),
            "author_role": "clinician",
            "entry_type": payload["p_entry_type"],
            "visibility": payload["p_visibility"],
            "content": payload["p_content"],
            "source_record_id": "60000000-0000-0000-0000-000000000099",
            "current_version": 1,
            "occurred_at": payload["p_occurred_at"],
        }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("entry_type", "visibility"),
    [
        ("clinician_note", "internal"),
        ("staff_note", "internal"),
        ("patient_summary", "patient_facing"),
        ("patient_instruction", "patient_facing"),
    ],
)
async def test_manual_entry_passes_valid_visibility_to_atomic_rpc(
    monkeypatch: pytest.MonkeyPatch,
    entry_type: str,
    visibility: str,
) -> None:
    fake = EntryGateway()
    monkeypatch.setattr(foundation, "gateway", lambda settings: fake)
    body = {
        "patient_id": PATIENT_ID,
        "entry_type": entry_type,
        "visibility": visibility,
        "content": "  Synthetic clinical update.  ",
        "occurred_at": "2026-08-28T14:30:00+08:00",
    }

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/entries", json=body)

    assert response.status_code == 201
    assert fake.rpc_calls[0][0] == "create_manual_entry"
    assert fake.rpc_calls[0][1]["p_visibility"] == visibility
    assert fake.rpc_calls[0][1]["p_content"] == "Synthetic clinical update."


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("entry_type", "visibility"),
    [
        ("clinician_note", "patient_facing"),
        ("staff_note", "patient_facing"),
        ("patient_summary", "internal"),
        ("patient_instruction", "internal"),
    ],
)
async def test_manual_entry_rejects_unsafe_visibility_before_rpc(
    monkeypatch: pytest.MonkeyPatch,
    entry_type: str,
    visibility: str,
) -> None:
    fake = EntryGateway()
    monkeypatch.setattr(foundation, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/entries",
            json={
                "patient_id": PATIENT_ID,
                "entry_type": entry_type,
                "visibility": visibility,
                "content": "Synthetic update",
            },
        )

    assert response.status_code == 422
    assert fake.rpc_calls == []


def test_entry_visibility_migration_enforces_clinical_publication_boundary() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert parse_sql(sql)
    assert "entry_type = 'clinician_note' and visibility = 'internal'" in sql
    assert "entry_type in ('patient_summary', 'patient_instruction')" in sql
    assert "visibility = 'patient_facing'" in sql
    assert "array['clinician']" in sql
    assert "'staff'" not in sql
