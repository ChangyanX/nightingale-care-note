from time import perf_counter_ns

import httpx
import pytest

from app.api import foundation
from app.auth import AuthContext, get_auth_context
from app.main import app
from scripts.benchmark_glance import percentile
from tests.test_patient_read_api import PATIENT_ID, USER_ID, PatientReadGateway


async def auth_override() -> AuthContext:
    return AuthContext(user_id=USER_ID, email="staff@example.invalid", access_token="caller-token")


@pytest.fixture(autouse=True)
def override_auth() -> None:
    app.dependency_overrides[get_auth_context] = auth_override
    yield
    app.dependency_overrides.clear()


def test_nearest_rank_percentile_is_deterministic() -> None:
    values = [float(value) for value in range(1, 101)]
    assert percentile(values, 50) == 50
    assert percentile(values, 95) == 95
    assert percentile(values, 99) == 99


@pytest.mark.asyncio
async def test_warm_glance_in_process_p95_approximation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guard app/auth/serialization cost; the reproducible script measures real I/O."""
    monkeypatch.setattr(foundation, "gateway", lambda settings: PatientReadGateway())
    timings: list[float] = []
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        for _ in range(10):
            assert (await client.get(f"/patients/{PATIENT_ID}/glance")).status_code == 200
        for _ in range(120):
            started = perf_counter_ns()
            response = await client.get(f"/patients/{PATIENT_ID}/glance")
            timings.append((perf_counter_ns() - started) / 1_000_000)
            assert response.status_code == 200

    assert percentile(timings, 95) <= 300.0
