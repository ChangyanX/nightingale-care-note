from typing import Any
from uuid import UUID

import httpx
import pytest

from app.api import scribe_jobs
from app.auth import AuthContext, get_auth_context
from app.main import app

PATIENT_ID = "40000000-0000-0000-0000-000000000001"
SOURCE_ID = "60000000-0000-0000-0000-000000000003"
JOB_ID = "d0000000-0000-0000-0000-000000000001"
CLINIC_ID = "10000000-0000-0000-0000-000000000001"
USER_ID = UUID("20000000-0000-0000-0000-000000000003")


def job_row() -> dict[str, Any]:
    return {
        "id": JOB_ID,
        "clinic_id": CLINIC_ID,
        "patient_id": PATIENT_ID,
        "source_record_id": SOURCE_ID,
        "interaction_type": "doctor_consult",
        "requested_by": str(USER_ID),
        "idempotency_key": "doctor-consult-20260827",
        "status": "queued",
        "attempt_count": 0,
        "max_attempts": 3,
        "available_at": "2026-08-27T12:00:00+08:00",
        "claimed_at": None,
        "lease_expires_at": None,
        "completed_at": None,
        "safe_error_code": None,
        "output_entry_id": None,
        "created_at": "2026-08-27T12:00:00+08:00",
        "updated_at": "2026-08-27T12:00:00+08:00",
    }


class ScribeJobGateway:
    def __init__(self, *, visible: bool = True) -> None:
        self.visible = visible
        self.rpc_calls: list[tuple[str, dict[str, Any]]] = []

    async def rpc(
        self,
        function_name: str,
        access_token: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        assert access_token == "caller-token"
        self.rpc_calls.append((function_name, payload))
        return job_row()

    async def select(
        self,
        table: str,
        access_token: str,
        params: dict[str, str],
    ) -> list[dict[str, Any]]:
        assert table == "ai_jobs"
        assert access_token == "caller-token"
        assert params["id"] == f"eq.{JOB_ID}"
        return [job_row()] if self.visible else []


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
async def test_submit_scribe_job_uses_idempotent_rpc(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = ScribeJobGateway()
    monkeypatch.setattr(scribe_jobs, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/patients/{PATIENT_ID}/scribe-jobs",
            json={
                "source_record_id": SOURCE_ID,
                "interaction_type": "doctor_consult",
                "idempotency_key": "doctor-consult-20260827",
            },
        )

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert fake.rpc_calls == [
        (
            "submit_ai_scribe_job",
            {
                "p_patient_id": PATIENT_ID,
                "p_source_record_id": SOURCE_ID,
                "p_interaction_type": "doctor_consult",
                "p_idempotency_key": "doctor-consult-20260827",
            },
        )
    ]


@pytest.mark.asyncio
async def test_status_response_is_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = ScribeJobGateway()
    monkeypatch.setattr(scribe_jobs, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/scribe-jobs/{JOB_ID}")

    assert response.status_code == 200
    body = response.json()
    assert "transcript" not in body
    assert "prompt" not in body
    assert "provider_response" not in body
    assert body["safe_error_code"] is None


@pytest.mark.asyncio
async def test_inaccessible_job_is_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = ScribeJobGateway(visible=False)
    monkeypatch.setattr(scribe_jobs, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/scribe-jobs/{JOB_ID}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Scribe job not found"}


@pytest.mark.asyncio
async def test_invalid_idempotency_key_fails_before_rpc(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = ScribeJobGateway()
    monkeypatch.setattr(scribe_jobs, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/patients/{PATIENT_ID}/scribe-jobs",
            json={
                "source_record_id": SOURCE_ID,
                "interaction_type": "doctor_consult",
                "idempotency_key": "bad key",
            },
        )

    assert response.status_code == 422
    assert fake.rpc_calls == []
