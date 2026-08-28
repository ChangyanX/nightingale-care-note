from typing import Any
from uuid import UUID

import httpx
import pytest

from app.api import foundation
from app.auth import AuthContext, get_auth_context
from app.main import app

PATIENT_ID = "40000000-0000-0000-0000-000000000001"
CLINIC_ID = "10000000-0000-0000-0000-000000000001"
USER_ID = UUID("20000000-0000-0000-0000-000000000002")


class PatientReadGateway:
    def __init__(self, *, patient_visible: bool = True) -> None:
        self.patient_visible = patient_visible
        self.selected_tables: list[str] = []

    async def select(
        self,
        table: str,
        access_token: str,
        params: dict[str, str],
    ) -> list[dict[str, Any]]:
        assert access_token == "caller-token"
        self.selected_tables.append(table)
        if table == "clinic_memberships":
            assert params["profile_id"] == f"eq.{USER_ID}"
            return [{"clinic_id": CLINIC_ID, "role": "staff"}]
        if table == "patients":
            if not self.patient_visible:
                return []
            return [
                {
                    "id": PATIENT_ID,
                    "clinic_id": CLINIC_ID,
                    "synthetic_identifier": "SYN-A-001",
                    "display_name": "Parker Patient",
                }
            ]
        if table == "entries":
            return [
                self._entry(
                    "70000000-0000-0000-0000-000000000005",
                    "ai_patient_session_summary",
                    "system",
                    "Does the worsening nighttime cough require an earlier review?",
                    "2026-08-26T08:00:00+08:00",
                    "60000000-0000-0000-0000-000000000005",
                ),
                self._entry(
                    "70000000-0000-0000-0000-000000000007",
                    "patient_insight",
                    "patient",
                    "The cough woke me twice and seems worse in a cold room.",
                    "2026-08-26T07:50:00+08:00",
                    "60000000-0000-0000-0000-000000000007",
                    author_id="20000000-0000-0000-0000-000000000004",
                ),
                self._entry(
                    "70000000-0000-0000-0000-000000000002",
                    "clinician_note",
                    "clinician",
                    "Persistent nocturnal cough; review inhaler technique and diary.",
                    "2026-08-24T09:30:00+08:00",
                    "60000000-0000-0000-0000-000000000002",
                    author_id="20000000-0000-0000-0000-000000000003",
                ),
            ]
        if table == "source_records":
            return [
                {
                    "id": source_id,
                    "source_type": source_type,
                    "external_reference": reference,
                    "occurred_at": occurred_at,
                }
                for source_id, source_type, reference, occurred_at in (
                    (
                        "60000000-0000-0000-0000-000000000005",
                        "ai_patient_session",
                        "ai-session-001",
                        "2026-08-26T08:00:00+08:00",
                    ),
                    (
                        "60000000-0000-0000-0000-000000000007",
                        "manual",
                        "patient-insight-001",
                        "2026-08-26T07:50:00+08:00",
                    ),
                    (
                        "60000000-0000-0000-0000-000000000002",
                        "manual",
                        "clinician-note-001",
                        "2026-08-24T09:30:00+08:00",
                    ),
                )
            ]
        if table == "care_tasks":
            assert params["patient_id"] == f"eq.{PATIENT_ID}"
            return [
                {
                    "id": "b0000000-0000-0000-0000-000000000001",
                    "clinic_id": CLINIC_ID,
                    "patient_id": PATIENT_ID,
                    "source_entry_id": "70000000-0000-0000-0000-000000000002",
                    "title": "Review seven-day peak-flow diary",
                    "assigned_to": "20000000-0000-0000-0000-000000000003",
                    "created_by": "20000000-0000-0000-0000-000000000002",
                    "status": "open",
                    "priority": "high",
                    "due_at": "2026-08-31T17:00:00+08:00",
                    "completed_at": None,
                    "created_at": "2026-08-24T09:35:00+08:00",
                    "updated_at": "2026-08-24T09:35:00+08:00",
                }
            ]
        raise AssertionError(f"Unexpected table: {table}")

    @staticmethod
    def _entry(
        entry_id: str,
        entry_type: str,
        author_role: str,
        content: str,
        occurred_at: str,
        source_record_id: str,
        *,
        author_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "id": entry_id,
            "clinic_id": CLINIC_ID,
            "patient_id": PATIENT_ID,
            "author_id": author_id,
            "author_role": author_role,
            "entry_type": entry_type,
            "visibility": "internal",
            "content": content,
            "source_record_id": source_record_id,
            "current_version": 1,
            "occurred_at": occurred_at,
        }


async def auth_override() -> AuthContext:
    return AuthContext(user_id=USER_ID, email="staff@example.invalid", access_token="caller-token")


@pytest.fixture(autouse=True)
def override_auth() -> None:
    app.dependency_overrides[get_auth_context] = auth_override
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_timeline_includes_resolvable_source_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = PatientReadGateway()
    monkeypatch.setattr(foundation, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/patients/{PATIENT_ID}/timeline")

    assert response.status_code == 200
    assert response.json()[0]["source"] == {
        "id": "60000000-0000-0000-0000-000000000005",
        "source_type": "ai_patient_session",
        "external_reference": "ai-session-001",
        "occurred_at": "2026-08-26T08:00:00+08:00",
    }


@pytest.mark.asyncio
async def test_glance_is_bounded_ordered_and_source_linked(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = PatientReadGateway()
    monkeypatch.setattr(foundation, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/patients/{PATIENT_ID}/glance")

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) <= 6
    assert [item["kind"] for item in items] == [
        "current_concern",
        "recent_change",
        "open_action",
        "patient_question",
    ]
    assert items[2]["task_id"] == "b0000000-0000-0000-0000-000000000001"
    assert all(item["source_entry_id"] for item in items)


@pytest.mark.asyncio
async def test_tasks_return_bounded_patient_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = PatientReadGateway()
    monkeypatch.setattr(foundation, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/patients/{PATIENT_ID}/tasks")

    assert response.status_code == 200
    assert response.json()[0]["status"] == "open"
    assert response.json()[0]["priority"] == "high"


@pytest.mark.asyncio
async def test_inaccessible_patient_stops_before_internal_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = PatientReadGateway(patient_visible=False)
    monkeypatch.setattr(foundation, "gateway", lambda settings: fake)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(f"/patients/{PATIENT_ID}/glance")

    assert response.status_code == 404
    assert response.json() == {"detail": "Patient not found"}
    assert fake.selected_tables == ["clinic_memberships", "patients"]
