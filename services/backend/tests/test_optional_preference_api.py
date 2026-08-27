from typing import Any
from uuid import UUID

import httpx
import pytest

from app.api import scribe_jobs
from app.auth import AuthContext, get_auth_context
from app.main import app

CLINIC_ID = "10000000-0000-0000-0000-000000000001"
USER_ID = UUID("20000000-0000-0000-0000-000000000003")
EVENT_ID = "f0000000-0000-0000-0000-000000000001"


def preference_row() -> dict[str, Any]:
    return {
        "id": "e0000000-0000-0000-0000-000000000001",
        "clinic_id": CLINIC_ID,
        "profile_id": str(USER_ID),
        "topic": "current_concern",
        "weight": 1.0,
        "updated_at": "2026-08-28T12:00:00+08:00",
    }


class PreferenceGateway:
    def __init__(self) -> None:
        self.rpc_calls: list[tuple[str, dict[str, Any]]] = []

    async def rpc(
        self, function_name: str, access_token: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        assert access_token == "caller-token"
        self.rpc_calls.append((function_name, payload))
        return preference_row()

    async def rpc_value(
        self, function_name: str, access_token: str, payload: dict[str, Any]
    ) -> int:
        assert access_token == "caller-token"
        self.rpc_calls.append((function_name, payload))
        return 1

    async def select(
        self, table: str, access_token: str, params: dict[str, str]
    ) -> list[dict[str, Any]]:
        assert table == "importance_preferences"
        assert access_token == "caller-token"
        assert params["profile_id"] == f"eq.{USER_ID}"
        return [preference_row()]


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
async def test_feedback_uses_server_delta_and_local_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = PreferenceGateway()
    monkeypatch.setattr(scribe_jobs, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/importance-feedback",
            json={
                "event_id": EVENT_ID,
                "clinic_id": CLINIC_ID,
                "topic": "current_concern",
                "feedback_kind": "accept",
            },
        )

    assert response.status_code == 200
    function, payload = fake.rpc_calls[0]
    assert function == "record_importance_feedback"
    assert payload["p_event_id"] == EVENT_ID
    assert len(payload["p_embedding"]) == 16
    assert "p_delta" not in payload


@pytest.mark.asyncio
async def test_preferences_are_caller_scoped_and_resettable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = PreferenceGateway()
    monkeypatch.setattr(scribe_jobs, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        listed = await client.get(f"/importance-preferences?clinic_id={CLINIC_ID}")
        reset = await client.delete(f"/importance-preferences/{CLINIC_ID}")

    assert listed.status_code == 200
    assert listed.json()[0]["profile_id"] == str(USER_ID)
    assert reset.json() == {"deleted_preferences": 1}
    assert fake.rpc_calls[-1] == (
        "reset_importance_preferences",
        {"p_clinic_id": CLINIC_ID},
    )
