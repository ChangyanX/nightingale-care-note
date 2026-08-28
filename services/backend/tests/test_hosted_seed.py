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
        ("PATIENT_A2", "patient.a2@nightingale-demo.invalid"),
        ("PATIENT_B", "patient.b@nightingale-demo.invalid"),
        ("PATIENT_A3", "patient.a3@nightingale-demo.invalid"),
        ("PATIENT_B2", "patient.b2@nightingale-demo.invalid"),
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
    assert len([request for request in requests if request.method == "POST"]) == 9
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
                calls.setdefault(table, []).extend(rows)

    user_ids = {
        "ADMIN_A": "20000000-0000-0000-0000-000000000001",
        "STAFF_A": "20000000-0000-0000-0000-000000000002",
        "CLINICIAN_A": "20000000-0000-0000-0000-000000000003",
        "PATIENT_A": "20000000-0000-0000-0000-000000000004",
        "STAFF_B": "20000000-0000-0000-0000-000000000005",
        "CLINICIAN_B": "20000000-0000-0000-0000-000000000006",
        "PATIENT_A2": "20000000-0000-0000-0000-000000000007",
        "PATIENT_B": "20000000-0000-0000-0000-000000000008",
        "PATIENT_A3": "20000000-0000-0000-0000-000000000009",
        "PATIENT_B2": "20000000-0000-0000-0000-000000000010",
    }

    seed_foundation(RecordingClient(), user_ids)  # type: ignore[arg-type]

    assert len({row["occurred_at"] for row in calls["entries"]}) >= 3
    assert {row["status"] for row in calls["care_tasks"]} == {"open", "completed"}
    assert {row["category"] for row in calls["care_tasks"]} == {
        "clinical_review",
        "monitoring",
    }
    assert {row["patient_visible"] for row in calls["care_tasks"]} == {False, True}
    assert any("Secondary concern" in str(row["content"]) for row in calls["entries"])
    assert {row["status"] for row in calls["comments"]} == {"open", "resolved"}
    assert {row["status"] for row in calls["highlights"]} == {"accepted", "rejected"}
    assert any(row["generated_by"] == "ai" for row in calls["highlights"])
    assert len(calls["patients"]) == 5
    assert all(row["linked_profile_id"] for row in calls["patients"])
    assert all("SYN-" in str(row["synthetic_identifier"]) for row in calls["patients"])
    required_types = {
        "patient_insight",
        "staff_note",
        "clinician_note",
        "patient_summary",
        "patient_instruction",
        "ai_doctor_consult_summary",
        "ai_nurse_consult_summary",
        "ai_patient_session_summary",
    }
    for patient in calls["patients"]:
        patient_types = {
            row["entry_type"]
            for row in calls["entries"]
            if row["patient_id"] == patient["id"]
        }
        assert required_types <= patient_types
    revised_entries = {
        row["entry_id"]
        for row in calls["entry_versions"]
        if row["version_number"] == 2
    }
    assert len(revised_entries) == 5
    assert len(calls["note_sections"]) == 20
    assert {row["status"] for row in calls["patient_reports"]} == {
        "available",
        "preparing",
    }
    assert all("content" not in row for row in calls["notification_outbox"])
    for row in calls["highlights"]:
        entry = next(entry for entry in calls["entries"] if entry["id"] == row["source_entry_id"])
        content = str(entry["content"])
        assert content[row["source_start_offset"] : row["source_end_offset"]] == row["quoted_text"]
