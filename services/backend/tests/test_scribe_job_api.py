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


@pytest.mark.asyncio
async def test_patient_job_feed_includes_queue_position_and_safe_progress_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StatusGateway:
        async def select(
            self, table: str, access_token: str, params: dict[str, str]
        ) -> list[dict[str, Any]]:
            assert access_token == "caller-token"
            if table == "ai_jobs":
                assert params["patient_id"] == f"eq.{PATIENT_ID}"
                return [job_row()]
            assert table == "ai_job_events"
            return [
                {
                    "id": "e0000000-0000-0000-0000-000000000001",
                    "job_id": JOB_ID,
                    "event_kind": "generating",
                    "created_at": "2026-08-27T12:00:01+08:00",
                }
            ]

        async def rpc_value(
            self, function_name: str, access_token: str, payload: dict[str, Any]
        ) -> int:
            assert function_name == "ai_job_queue_position"
            assert access_token == "caller-token"
            assert payload == {"p_job_id": JOB_ID}
            return 2

    fake = StatusGateway()
    monkeypatch.setattr(scribe_jobs, "gateway", lambda settings: fake)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        jobs = await client.get(f"/patients/{PATIENT_ID}/scribe-jobs")
        events = await client.get(f"/patients/{PATIENT_ID}/scribe-job-events")

    assert jobs.status_code == 200
    assert jobs.json()[0]["queue_position"] == 2
    assert events.json()[0]["event_kind"] == "generating"
    assert "safe_metadata" not in events.json()[0]


@pytest.mark.asyncio
async def test_provider_usage_dashboard_aggregates_sanitized_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UsageGateway:
        async def select(
            self, table: str, access_token: str, params: dict[str, str]
        ) -> list[dict[str, Any]]:
            assert table == "ai_jobs"
            assert access_token == "caller-token"
            assert params["status"] == "eq.succeeded"
            return [
                {
                    "provider_name": "ollama",
                    "model_name": "gpt-oss:20b",
                    "input_tokens": 120,
                    "output_tokens": 40,
                    "estimated_cost_usd": 0,
                    "claimed_at": "2026-08-27T12:00:00+08:00",
                    "completed_at": "2026-08-27T12:00:02+08:00",
                }
            ]

    monkeypatch.setattr(scribe_jobs, "gateway", lambda settings: UsageGateway())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/provider-usage")

    assert response.status_code == 200
    assert response.json() == [
        {
            "provider": "ollama",
            "model": "gpt-oss:20b",
            "calls": 1,
            "input_tokens": 120,
            "output_tokens": 40,
            "average_latency_ms": 2000.0,
            "estimated_cost_usd": 0.0,
        }
    ]
