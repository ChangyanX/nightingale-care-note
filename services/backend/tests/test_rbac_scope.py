import os
from pathlib import Path
from typing import Any

import httpx
import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FOUNDATION_MIGRATION = (
    REPOSITORY_ROOT / "supabase" / "migrations" / "202608260001_foundation.sql"
)

CLINIC_A_ID = "10000000-0000-0000-0000-000000000001"
CLINIC_B_ID = "10000000-0000-0000-0000-000000000002"
STAFF_ENTRY_ID = "70000000-0000-0000-0000-000000000001"
CLINICIAN_ENTRY_ID = "70000000-0000-0000-0000-000000000002"


def migration_sql() -> str:
    return FOUNDATION_MIGRATION.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "table",
    [
        "clinics",
        "profiles",
        "clinic_memberships",
        "patients",
        "source_records",
        "care_notes",
        "entries",
        "note_sections",
        "entry_versions",
        "section_versions",
        "comments",
        "audit_events",
    ],
)
def test_every_exposed_table_enables_rls(table: str) -> None:
    assert f"alter table public.{table} enable row level security;" in migration_sql()


def test_patient_entry_policy_explicitly_excludes_raw_ai_notes() -> None:
    sql = migration_sql()
    policy_start = sql.index("create policy entries_select_scoped")
    policy_end = sql.index("create policy entries_insert_staff")
    patient_read_policy = sql[policy_start:policy_end]

    assert "entry_type in ('patient_summary', 'patient_instruction')" in patient_read_policy
    assert "ai_doctor_consult_summary" not in patient_read_policy
    assert "ai_nurse_consult_summary" not in patient_read_policy
    assert "ai_patient_session_summary" not in patient_read_policy


def test_patient_has_no_comment_policy() -> None:
    sql = migration_sql()
    comments_start = sql.index("create policy comments_select_clinical")
    comments_end = sql.index("create policy audit_select_clinical")

    assert "is_linked_patient" not in sql[comments_start:comments_end]


def test_role_owned_write_policies_are_separate() -> None:
    sql = migration_sql()

    assert "create policy entries_update_staff" in sql
    assert "author_role = 'staff'" in sql
    assert "create policy entries_update_clinician" in sql
    assert "author_role = 'clinician'" in sql
    assert "create policy sections_update_staff" in sql
    assert "create policy sections_update_clinician" in sql


def test_admin_has_no_clinical_write_policy() -> None:
    sql = migration_sql()
    clinical_write_policy_lines = [
        line
        for line in sql.splitlines()
        if line.startswith("create policy")
        and any(table in line for table in ("entries", "note_sections", "comments"))
        and any(operation in line for operation in ("insert", "update", "delete"))
    ]

    assert clinical_write_policy_lines
    assert all("admin" not in line for line in clinical_write_policy_lines)


def test_backend_does_not_reference_service_role_for_user_routes() -> None:
    app_directory = REPOSITORY_ROOT / "services" / "backend" / "app"
    combined_source = "\n".join(
        source.read_text(encoding="utf-8") for source in app_directory.rglob("*.py")
    )

    assert "SUPABASE_SERVICE_ROLE_KEY" not in combined_source
    assert "supabase_service_role_key" not in combined_source


class LiveRlsClient:
    def __init__(self) -> None:
        self.base_url = os.environ["SUPABASE_URL"].rstrip("/")
        self.publishable_key = os.environ["SUPABASE_PUBLISHABLE_KEY"]

    def request(
        self,
        method: str,
        path: str,
        token: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        return httpx.request(
            method,
            f"{self.base_url}/rest/v1/{path}",
            headers={
                "apikey": self.publishable_key,
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "prefer": "return=representation",
            },
            params=params,
            json=json,
            timeout=10.0,
        )


def live_token(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"Set {name} to run live RLS integration tests")
    return value


@pytest.fixture
def live_client() -> LiveRlsClient:
    if os.getenv("NIGHTINGALE_RUN_RLS_INTEGRATION") != "1":
        pytest.skip("Set NIGHTINGALE_RUN_RLS_INTEGRATION=1 to run live RLS tests")
    return LiveRlsClient()


def test_live_staff_cannot_read_other_clinic(live_client: LiveRlsClient) -> None:
    response = live_client.request(
        "GET",
        "patients",
        live_token("NIGHTINGALE_TEST_STAFF_A_TOKEN"),
        params={"select": "id,clinic_id"},
    )

    assert response.status_code == 200
    assert response.json()
    assert {row["clinic_id"] for row in response.json()} == {CLINIC_A_ID}
    assert CLINIC_B_ID not in {row["clinic_id"] for row in response.json()}


def test_live_patient_cannot_read_internal_comments_or_ai_notes(
    live_client: LiveRlsClient,
) -> None:
    token = live_token("NIGHTINGALE_TEST_PATIENT_A_TOKEN")
    comments = live_client.request("GET", "comments", token, params={"select": "id"})
    entries = live_client.request(
        "GET",
        "entries",
        token,
        params={"select": "entry_type,visibility"},
    )

    assert comments.status_code == 200
    assert comments.json() == []
    assert entries.status_code == 200
    assert all(not row["entry_type"].startswith("ai_") for row in entries.json())


@pytest.mark.parametrize(
    ("token_name", "entry_id"),
    [
        ("NIGHTINGALE_TEST_STAFF_A_TOKEN", CLINICIAN_ENTRY_ID),
        ("NIGHTINGALE_TEST_CLINICIAN_A_TOKEN", STAFF_ENTRY_ID),
        ("NIGHTINGALE_TEST_ADMIN_A_TOKEN", CLINICIAN_ENTRY_ID),
    ],
)
def test_live_roles_cannot_overwrite_each_other(
    live_client: LiveRlsClient,
    token_name: str,
    entry_id: str,
) -> None:
    response = live_client.request(
        "PATCH",
        "entries",
        live_token(token_name),
        params={"id": f"eq.{entry_id}"},
        json={"content": "This unauthorized synthetic update must not be stored."},
    )

    assert response.status_code in (200, 204)
    if response.status_code == 200:
        assert response.json() == []
    else:
        assert not response.content
