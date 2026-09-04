from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest

from app.api import account, collaboration, foundation, patient_portal, revisions
from app.auth import AuthContext, get_auth_context
from app.main import app

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "supabase/migrations/202608280002_role_portal_enhancements.sql"
OPTIONAL_MIGRATION = ROOT / "supabase/migrations/202608280001_optional_deliverables.sql"
USER_ID = UUID("20000000-0000-0000-0000-000000000004")
PATIENT_ID = "40000000-0000-0000-0000-000000000001"
CLINIC_ID = "10000000-0000-0000-0000-000000000001"


async def patient_auth() -> AuthContext:
    return AuthContext(
        user_id=USER_ID,
        email="patient.a@nightingale.local",
        access_token="patient-token",
    )


@pytest.fixture(autouse=True)
def override_auth() -> None:
    app.dependency_overrides[get_auth_context] = patient_auth
    yield
    app.dependency_overrides.clear()


def profile_row() -> dict[str, Any]:
    return {
        "id": str(USER_ID),
        "display_name": "Parker Patient",
        "preferred_name": "Parker",
        "birth_date": "1992-04-18",
        "avatar_path": None,
        "avatar_mime_type": None,
    }


class IdentityGateway:
    def __init__(self, *, memberships: list[dict[str, Any]] | None = None) -> None:
        self.memberships = memberships or []
        self.selected: list[str] = []

    async def select(
        self, table: str, access_token: str, params: dict[str, str]
    ) -> list[dict[str, Any]]:
        assert access_token == "patient-token"
        self.selected.append(table)
        if table == "profiles":
            return [profile_row()]
        if table == "clinic_memberships":
            assert params["profile_id"] == f"eq.{USER_ID}"
            return self.memberships
        if table == "patients":
            return [{"id": PATIENT_ID}]
        raise AssertionError(f"Unexpected table {table}")


@pytest.mark.asyncio
async def test_patient_identity_lands_on_dashboard_and_patient_list_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = IdentityGateway()
    monkeypatch.setattr(foundation, "gateway", lambda settings: fake)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        identity = await client.get("/me")
        patient_list = await client.get("/patients")
        clinical_detail = await client.get(f"/patients/{PATIENT_ID}")
        clinical_timeline = await client.get(f"/patients/{PATIENT_ID}/timeline")
        clinical_glance = await client.get(f"/patients/{PATIENT_ID}/glance")

    assert identity.status_code == 200
    assert identity.json()["account_kind"] == "patient"
    assert identity.json()["landing_path"] == "/patient"
    assert patient_list.status_code == 403
    assert clinical_detail.status_code == 403
    assert clinical_timeline.status_code == 403
    assert clinical_glance.status_code == 403
    assert set(fake.selected) == {"profiles", "clinic_memberships", "patients"}


class PortalGateway:
    def __init__(self) -> None:
        self.selected: list[tuple[str, dict[str, str]]] = []
        self.rpc_payload: dict[str, Any] | None = None

    async def select(
        self, table: str, access_token: str, params: dict[str, str]
    ) -> list[dict[str, Any]]:
        assert access_token == "patient-token"
        self.selected.append((table, params))
        if table == "patients":
            assert params["linked_profile_id"] == f"eq.{USER_ID}"
            return [
                {
                    "id": PATIENT_ID,
                    "clinic_id": CLINIC_ID,
                    "synthetic_identifier": "SYN-A-001",
                    "display_name": "Parker Patient",
                }
            ]
        if table == "entries" and params.get("visibility") == "eq.patient_facing":
            assert params["entry_type"] == "in.(patient_summary,patient_instruction)"
            return [
                {
                    "id": "70000000-0000-0000-0000-000000000006",
                    "entry_type": "patient_instruction",
                    "content": "Record morning and evening peak flow.",
                    "occurred_at": "2026-08-24T09:40:00+08:00",
                }
            ]
        if table == "entries":
            assert params["author_id"] == f"eq.{USER_ID}"
            assert params["entry_type"] == "eq.patient_insight"
            return [
                {
                    "id": "70000000-0000-0000-0000-000000000007",
                    "entry_type": "patient_insight",
                    "content": "Synthetic symptom update.",
                    "occurred_at": "2026-08-26T07:50:00+08:00",
                }
            ]
        if table in {
            "appointment_requests",
            "patient_reports",
            "patient_observations",
            "care_tasks",
        }:
            if table == "patient_reports":
                assert params["status"] == "eq.available"
            if table == "care_tasks":
                assert params["patient_visible"] == "eq.true"
            return []
        raise AssertionError(f"Restricted table was queried: {table}")

    async def rpc(
        self, function_name: str, access_token: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        assert access_token == "patient-token"
        self.rpc_payload = payload
        entry = {
            "id": "70000000-0000-0000-0000-000000000010",
            "entry_type": "patient_insight",
            "content": payload["p_content"],
            "occurred_at": "2026-08-28T12:00:00+08:00",
        }
        if function_name == "create_patient_portal_entry":
            return entry
        assert function_name == "submit_patient_ai_session"
        return {
            "entry": entry,
            "job": {
                "id": "d0000000-0000-0000-0000-000000000004",
                "status": "queued",
                "created_at": "2026-08-28T12:00:00+08:00",
                "updated_at": "2026-08-28T12:00:00+08:00",
                "completed_at": None,
                "safe_error_code": None,
            },
        }


@pytest.mark.asyncio
async def test_patient_dashboard_uses_reduced_safe_queries_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = PortalGateway()
    monkeypatch.setattr(patient_portal, "gateway", lambda settings: fake)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/patient/dashboard")

    assert response.status_code == 200
    body = response.json()
    serialized = response.text
    assert body["instructions"][0]["entry_type"] == "patient_instruction"
    assert "source_record_id" not in serialized
    assert "author_id" not in serialized
    assert "risk_reason" not in serialized
    assert "comment" not in {table for table, _ in fake.selected}
    assert {table for table, _ in fake.selected}.isdisjoint(
        {"comments", "highlights", "audit_events", "entry_versions", "ai_jobs"}
    )


@pytest.mark.asyncio
async def test_guessed_restricted_resource_ids_resolve_to_no_patient_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RlsFilteredGateway:
        def __init__(self) -> None:
            self.queries: list[tuple[str, dict[str, str]]] = []

        async def select(
            self, table: str, access_token: str, params: dict[str, str]
        ) -> list[dict[str, Any]]:
            assert access_token == "patient-token"
            self.queries.append((table, params))
            return []

    fake = RlsFilteredGateway()
    monkeypatch.setattr(collaboration, "gateway", lambda settings: fake)
    monkeypatch.setattr(revisions, "gateway", lambda settings: fake)
    guessed_entry = "70000000-0000-0000-0000-000000000003"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        comments = await client.get(f"/patients/{PATIENT_ID}/comments")
        highlights = await client.get(f"/patients/{PATIENT_ID}/highlights")
        versions = await client.get(f"/entries/{guessed_entry}/versions")
        comparison = await client.get(f"/entries/{guessed_entry}/versions/1/comparison")

    assert comments.status_code == 200 and comments.json() == []
    assert highlights.status_code == 200 and highlights.json() == []
    assert versions.status_code == 200 and versions.json() == []
    assert comparison.status_code == 404
    assert {table for table, _ in fake.queries} == {
        "comments",
        "highlights",
        "entry_versions",
        "entries",
    }


@pytest.mark.asyncio
async def test_patient_question_runs_redaction_verification_before_recording(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = PortalGateway()
    monkeypatch.setattr(patient_portal, "gateway", lambda settings: fake)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/patient/ai-question",
            json={
                "question": "Name: Parker Patient; NRIC S1234567D; phone 9123 4567. Is this urgent?"
            },
        )

    assert response.status_code == 201
    assert "not a diagnosis" in response.json()["message"]
    assert response.json()["job"]["status"] == "queued"
    metadata = fake.rpc_payload["p_structured"]  # type: ignore[index]
    assert metadata["redaction_verified"] is True
    assert metadata["redaction_counts"]["phone"] == 1
    assert metadata["redaction_counts"]["identity_number"] >= 1


@pytest.mark.asyncio
async def test_patient_ai_status_excludes_restricted_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class PatientStatusGateway:
        async def rpc_value(
            self, function_name: str, access_token: str, payload: dict[str, Any]
        ) -> list[dict[str, Any]]:
            assert function_name == "list_own_patient_ai_jobs"
            assert access_token == "patient-token"
            assert payload == {}
            return [
                {
                    "id": "d0000000-0000-0000-0000-000000000004",
                    "status": "succeeded",
                    "created_at": "2026-08-28T12:00:00+08:00",
                    "updated_at": "2026-08-28T12:00:04+08:00",
                    "completed_at": "2026-08-28T12:00:04+08:00",
                    "safe_error_code": None,
                }
            ]

    monkeypatch.setattr(patient_portal, "gateway", lambda settings: PatientStatusGateway())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/patient/ai-jobs")

    assert response.status_code == 200
    serialized = response.text
    assert response.json()[0]["status"] == "succeeded"
    assert "source_record_id" not in serialized
    assert "output_entry_id" not in serialized
    assert "provider_name" not in serialized


class AccountGateway:
    def __init__(self) -> None:
        self.rpc_payload: dict[str, Any] | None = None

    async def rpc(
        self, function_name: str, access_token: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        assert function_name == "update_own_profile"
        assert access_token == "patient-token"
        self.rpc_payload = payload
        return {**profile_row(), "preferred_name": payload["p_changes"]["preferred_name"]}

    async def select(
        self, table: str, access_token: str, params: dict[str, str]
    ) -> list[dict[str, Any]]:
        if table == "clinic_memberships":
            return []
        if table == "patients":
            return [{"id": PATIENT_ID}]
        raise AssertionError(table)


@pytest.mark.asyncio
async def test_profile_updates_are_own_field_allowlisted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = AccountGateway()
    monkeypatch.setattr(account, "gateway", lambda settings: fake)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        valid = await client.patch("/me/profile", json={"preferred_name": "Park"})
        forbidden = await client.patch(
            "/me/profile", json={"preferred_name": "Park", "role": "admin"}
        )

    assert valid.status_code == 200
    assert fake.rpc_payload == {"p_changes": {"preferred_name": "Park"}}
    assert forbidden.status_code == 422


@pytest.mark.asyncio
async def test_avatar_rejects_mime_spoof_before_storage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = AccountGateway()
    monkeypatch.setattr(account, "gateway", lambda settings: fake)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/me/avatar",
            json={
                "filename": "avatar.png",
                "content_type": "image/png",
                "data_base64": "bm90LXBuZw==",
            },
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_notifications_are_always_filtered_to_authenticated_recipient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class NotificationGateway:
        async def select(
            self, table: str, access_token: str, params: dict[str, str]
        ) -> list[dict[str, Any]]:
            assert table == "notification_outbox"
            assert params["recipient_id"] == f"eq.{USER_ID}"
            return [
                {
                    "id": "f1000000-0000-0000-0000-000000000001",
                    "clinic_id": CLINIC_ID,
                    "patient_id": PATIENT_ID,
                    "recipient_id": str(USER_ID),
                    "event_type": "care_update",
                    "resource_type": "patient_instruction",
                    "resource_id": "70000000-0000-0000-0000-000000000006",
                    "status": "delivered",
                    "read_at": None,
                    "created_at": "2026-08-28T10:00:00+08:00",
                }
            ]

    monkeypatch.setattr(collaboration, "gateway", lambda settings: NotificationGateway())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/notifications")
    assert response.status_code == 200
    assert response.json()[0]["recipient_id"] == str(USER_ID)


@pytest.mark.asyncio
async def test_notification_dismiss_uses_ownership_checked_rpc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notification_id = "f1000000-0000-0000-0000-000000000001"

    class NotificationGateway:
        async def rpc(
            self, function_name: str, access_token: str, payload: dict[str, Any]
        ) -> dict[str, Any]:
            assert function_name == "dismiss_own_notification"
            assert access_token == "patient-token"
            assert payload == {"p_notification_id": notification_id}
            return {
                "id": notification_id,
                "clinic_id": CLINIC_ID,
                "patient_id": PATIENT_ID,
                "recipient_id": str(USER_ID),
                "event_type": "care_update",
                "resource_type": "patient_instruction",
                "resource_id": "70000000-0000-0000-0000-000000000006",
                "status": "dismissed",
                "read_at": "2026-08-28T10:05:00+08:00",
                "created_at": "2026-08-28T10:00:00+08:00",
            }

    monkeypatch.setattr(collaboration, "gateway", lambda settings: NotificationGateway())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(f"/notifications/{notification_id}/dismiss")
    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"


def test_portal_migration_enforces_rls_and_patient_safe_policies() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    prior_sql = OPTIONAL_MIGRATION.read_text(encoding="utf-8")
    for table in ("appointment_requests", "patient_reports", "patient_observations"):
        assert f"alter table public.{table} enable row level security" in sql
    assert "status = 'available' and released_at is not null" in sql
    assert "patient_visible and public.is_linked_patient" in sql
    assert "create function public.update_own_profile" in sql
    assert "create function public.dismiss_own_notification" in sql
    assert "revoke update on public.notification_outbox from authenticated" in sql
    assert "linked_profile_id = auth.uid()" in sql
    assert "security definer set search_path = ''" in sql
    assert "where id = p_notification_id and recipient_id = auth.uid()" in sql
    assert "create function public.validate_notification_recipient_scope" in sql
    assert "Notification recipient is outside clinic scope" in sql
    assert "Patient notification target is restricted" in sql
    assert "create policy optional_own_notifications" in prior_sql
    assert "for select to authenticated using (recipient_id = auth.uid())" in prior_sql
