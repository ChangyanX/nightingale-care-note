from pathlib import Path

import httpx

from scripts.seed_hosted import (
    SupabaseAdminClient,
    prepare_credentials,
    project_ref_from_url,
    seed_foundation,
)


def test_hosted_url_requires_supabase_https() -> None:
    assert project_ref_from_url("https://abc123.supabase.co") == "abc123"


def test_credentials_are_owner_only_and_reused(tmp_path: Path) -> None:
    path = tmp_path / ".env.hosted-demo"
    first = prepare_credentials(path)
    second = prepare_credentials(path)

    assert first == second
    assert path.stat().st_mode & 0o777 == 0o600
    assert "NIGHTINGALE_DEMO_ADMIN_A_PASSWORD=" in path.read_text(encoding="utf-8")


def test_ensure_users_creates_missing_and_rotates_existing_passwords() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "users": [
                        {
                            "id": "existing-admin-id",
                            "email": "admin.a@nightingale-demo.invalid",
                        }
                    ]
                },
            )
        if request.method == "PUT":
            return httpx.Response(
                200,
                json={"id": "existing-admin-id", "email": "admin.a@nightingale-demo.invalid"},
            )
        email = str(request.content).split('"email":"', 1)[1].split('"', 1)[0]
        return httpx.Response(200, json={"id": f"new-{email}", "email": email})

    credentials: dict[str, str] = {}
    for key, email in (
        ("ADMIN_A", "admin.a@nightingale-demo.invalid"),
        ("STAFF_A", "staff.a@nightingale-demo.invalid"),
        ("CLINICIAN_A", "clinician.a@nightingale-demo.invalid"),
        ("PATIENT_A", "patient.a@nightingale-demo.invalid"),
        ("STAFF_B", "staff.b@nightingale-demo.invalid"),
        ("CLINICIAN_B", "clinician.b@nightingale-demo.invalid"),
    ):
        credentials[f"NIGHTINGALE_DEMO_{key}_EMAIL"] = email
        credentials[f"NIGHTINGALE_DEMO_{key}_PASSWORD"] = "generated-password"

    with SupabaseAdminClient(
        "https://project.supabase.co",
        "service-role-test-key",
        transport=httpx.MockTransport(handler),
    ) as client:
        user_ids = client.ensure_users(credentials)

    assert user_ids["ADMIN_A"] == "existing-admin-id"
    assert len([request for request in requests if request.method == "POST"]) == 5
    assert len([request for request in requests if request.method == "PUT"]) == 1


def test_hosted_foundation_seed_preserves_story_dates_and_tasks() -> None:
    calls: dict[str, list[dict[str, object]]] = {}

    class RecordingClient:
        def upsert(
            self,
            table: str,
            rows: list[dict[str, object]],
            conflict: str,
        ) -> None:
            assert conflict
            calls[table] = rows

    user_ids = {
        "ADMIN_A": "20000000-0000-0000-0000-000000000001",
        "STAFF_A": "20000000-0000-0000-0000-000000000002",
        "CLINICIAN_A": "20000000-0000-0000-0000-000000000003",
        "PATIENT_A": "20000000-0000-0000-0000-000000000004",
        "STAFF_B": "20000000-0000-0000-0000-000000000005",
        "CLINICIAN_B": "20000000-0000-0000-0000-000000000006",
    }

    seed_foundation(RecordingClient(), user_ids)  # type: ignore[arg-type]

    assert len({row["occurred_at"] for row in calls["entries"]}) >= 3
    assert {row["status"] for row in calls["care_tasks"]} == {"open", "completed"}
