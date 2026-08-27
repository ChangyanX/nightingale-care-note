"""Create hosted synthetic users and seed the Phase 1 demonstration dataset."""

from __future__ import annotations

import argparse
import os
import secrets
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CREDENTIAL_FILE = REPOSITORY_ROOT / ".env.hosted-demo"

CLINIC_A_ID = "10000000-0000-0000-0000-000000000001"
CLINIC_B_ID = "10000000-0000-0000-0000-000000000002"
PATIENT_A_ID = "40000000-0000-0000-0000-000000000001"
PATIENT_A2_ID = "40000000-0000-0000-0000-000000000002"
PATIENT_B_ID = "40000000-0000-0000-0000-000000000003"
CARE_NOTE_A_ID = "50000000-0000-0000-0000-000000000001"
CARE_NOTE_A2_ID = "50000000-0000-0000-0000-000000000002"
CARE_NOTE_B_ID = "50000000-0000-0000-0000-000000000003"


class HostedSeedSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPOSITORY_ROOT / ".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str
    supabase_service_role_key: str


@dataclass(frozen=True)
class DemoIdentity:
    key: str
    email: str
    display_name: str


IDENTITIES = (
    DemoIdentity("ADMIN_A", "admin.a@nightingale-demo.invalid", "Avery Admin"),
    DemoIdentity("STAFF_A", "staff.a@nightingale-demo.invalid", "Sam Staff"),
    DemoIdentity(
        "CLINICIAN_A",
        "clinician.a@nightingale-demo.invalid",
        "Dr. Casey Clinician",
    ),
    DemoIdentity("PATIENT_A", "patient.a@nightingale-demo.invalid", "Parker Patient"),
    DemoIdentity("STAFF_B", "staff.b@nightingale-demo.invalid", "Taylor Staff"),
    DemoIdentity(
        "CLINICIAN_B",
        "clinician.b@nightingale-demo.invalid",
        "Dr. Jordan Clinician",
    ),
)


def generate_password() -> str:
    alphabet = string.ascii_letters + string.digits + "-_.!"
    return "".join(secrets.choice(alphabet) for _ in range(32))


def parse_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip("'\"")
    return values


def prepare_credentials(path: Path) -> dict[str, str]:
    existing = parse_dotenv(path)
    credentials: dict[str, str] = {}
    lines = [
        "# Generated hosted synthetic demo credentials. Never commit this file.",
        "# Store a backup in your password manager if other developers need access.",
    ]
    for identity in IDENTITIES:
        email_key = f"NIGHTINGALE_DEMO_{identity.key}_EMAIL"
        password_key = f"NIGHTINGALE_DEMO_{identity.key}_PASSWORD"
        credentials[email_key] = identity.email
        credentials[password_key] = existing.get(password_key) or generate_password()
        lines.extend(
            (
                f"{email_key}={credentials[email_key]}",
                f"{password_key}={credentials[password_key]}",
            )
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as credential_file:
        credential_file.write("\n".join(lines) + "\n")
    path.chmod(0o600)
    return credentials


class SupabaseAdminClient:
    def __init__(
        self,
        url: str,
        service_role_key: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.client = httpx.Client(
            base_url=url.rstrip("/"),
            headers={
                "apikey": service_role_key,
                "authorization": f"Bearer {service_role_key}",
            },
            timeout=20.0,
            transport=transport,
        )

    def __enter__(self) -> SupabaseAdminClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            detail = response.text[:500]
            raise RuntimeError(
                f"Supabase setup request failed with {response.status_code}: {detail}"
            ) from error

    def list_users(self) -> dict[str, dict[str, Any]]:
        response = self.client.get("/auth/v1/admin/users", params={"page": 1, "per_page": 1000})
        self._raise_for_status(response)
        payload = response.json()
        users = payload.get("users", payload if isinstance(payload, list) else [])
        return {str(user["email"]).lower(): user for user in users if user.get("email")}

    def ensure_users(self, credentials: dict[str, str]) -> dict[str, str]:
        existing = self.list_users()
        user_ids: dict[str, str] = {}
        for identity in IDENTITIES:
            email = credentials[f"NIGHTINGALE_DEMO_{identity.key}_EMAIL"]
            password = credentials[f"NIGHTINGALE_DEMO_{identity.key}_PASSWORD"]
            user = existing.get(email.lower())
            payload = {
                "password": password,
                "email_confirm": True,
                "user_metadata": {"display_name": identity.display_name, "synthetic": True},
            }
            if user is None:
                response = self.client.post(
                    "/auth/v1/admin/users",
                    json={"email": email, **payload},
                )
            else:
                response = self.client.put(f"/auth/v1/admin/users/{user['id']}", json=payload)
            self._raise_for_status(response)
            user_ids[identity.key] = str(response.json()["id"])
        return user_ids

    def upsert(self, table: str, rows: list[dict[str, Any]], conflict: str) -> None:
        response = self.client.post(
            f"/rest/v1/{table}",
            params={"on_conflict": conflict},
            headers={"prefer": "resolution=merge-duplicates,return=minimal"},
            json=rows,
        )
        self._raise_for_status(response)


def seed_foundation(client: SupabaseAdminClient, users: dict[str, str]) -> None:
    client.upsert(
        "clinics",
        [
            {"id": CLINIC_A_ID, "name": "Harbour Family Clinic"},
            {"id": CLINIC_B_ID, "name": "Orchard Community Clinic"},
        ],
        "id",
    )
    client.upsert(
        "profiles",
        [
            {"id": users[identity.key], "display_name": identity.display_name}
            for identity in IDENTITIES
        ],
        "id",
    )
    client.upsert(
        "clinic_memberships",
        [
            {"clinic_id": CLINIC_A_ID, "profile_id": users["ADMIN_A"], "role": "admin"},
            {"clinic_id": CLINIC_A_ID, "profile_id": users["STAFF_A"], "role": "staff"},
            {
                "clinic_id": CLINIC_A_ID,
                "profile_id": users["CLINICIAN_A"],
                "role": "clinician",
            },
            {"clinic_id": CLINIC_B_ID, "profile_id": users["STAFF_B"], "role": "staff"},
            {
                "clinic_id": CLINIC_B_ID,
                "profile_id": users["CLINICIAN_B"],
                "role": "clinician",
            },
        ],
        "clinic_id,profile_id,role",
    )
    client.upsert(
        "patients",
        [
            {
                "id": PATIENT_A_ID,
                "clinic_id": CLINIC_A_ID,
                "linked_profile_id": users["PATIENT_A"],
                "synthetic_identifier": "SYN-A-001",
                "display_name": "Parker Patient",
            },
            {
                "id": PATIENT_A2_ID,
                "clinic_id": CLINIC_A_ID,
                "linked_profile_id": None,
                "synthetic_identifier": "SYN-A-002",
                "display_name": "Morgan Example",
            },
            {
                "id": PATIENT_B_ID,
                "clinic_id": CLINIC_B_ID,
                "linked_profile_id": None,
                "synthetic_identifier": "SYN-B-001",
                "display_name": "Riley Example",
            },
        ],
        "id",
    )
    client.upsert(
        "care_notes",
        [
            {"id": CARE_NOTE_A_ID, "clinic_id": CLINIC_A_ID, "patient_id": PATIENT_A_ID},
            {"id": CARE_NOTE_A2_ID, "clinic_id": CLINIC_A_ID, "patient_id": PATIENT_A2_ID},
            {"id": CARE_NOTE_B_ID, "clinic_id": CLINIC_B_ID, "patient_id": PATIENT_B_ID},
        ],
        "id",
    )

    sources = [
        (
            "60000000-0000-0000-0000-000000000001",
            CLINIC_A_ID,
            PATIENT_A_ID,
            "manual",
            "staff-note-001",
            users["STAFF_A"],
            "2026-08-24T09:00:00+08:00",
        ),
        (
            "60000000-0000-0000-0000-000000000002",
            CLINIC_A_ID,
            PATIENT_A_ID,
            "manual",
            "clinician-note-001",
            users["CLINICIAN_A"],
            "2026-08-24T09:30:00+08:00",
        ),
        (
            "60000000-0000-0000-0000-000000000003",
            CLINIC_A_ID,
            PATIENT_A_ID,
            "doctor_consult",
            "doctor-consult-001",
            None,
            "2026-08-24T09:30:00+08:00",
        ),
        (
            "60000000-0000-0000-0000-000000000004",
            CLINIC_A_ID,
            PATIENT_A_ID,
            "nurse_consult",
            "nurse-consult-001",
            None,
            "2026-08-25T10:00:00+08:00",
        ),
        (
            "60000000-0000-0000-0000-000000000005",
            CLINIC_A_ID,
            PATIENT_A_ID,
            "ai_patient_session",
            "ai-session-001",
            None,
            "2026-08-26T08:00:00+08:00",
        ),
        (
            "60000000-0000-0000-0000-000000000006",
            CLINIC_A_ID,
            PATIENT_A_ID,
            "manual",
            "patient-instruction-001",
            users["CLINICIAN_A"],
            "2026-08-24T09:40:00+08:00",
        ),
        (
            "60000000-0000-0000-0000-000000000007",
            CLINIC_A_ID,
            PATIENT_A_ID,
            "manual",
            "patient-insight-001",
            users["PATIENT_A"],
            "2026-08-26T07:50:00+08:00",
        ),
        (
            "60000000-0000-0000-0000-000000000008",
            CLINIC_B_ID,
            PATIENT_B_ID,
            "manual",
            "clinic-b-note-001",
            users["STAFF_B"],
            "2026-08-25T11:00:00+08:00",
        ),
    ]
    client.upsert(
        "source_records",
        [
            {
                "id": source_id,
                "clinic_id": clinic_id,
                "patient_id": patient_id,
                "source_type": source_type,
                "external_reference": reference,
                "occurred_at": occurred_at,
                "created_by": creator,
                "metadata": {"synthetic": True},
            }
            for (
                source_id,
                clinic_id,
                patient_id,
                source_type,
                reference,
                creator,
                occurred_at,
            ) in sources
        ],
        "id",
    )

    entries = [
        (
            "70000000-0000-0000-0000-000000000001",
            CLINIC_A_ID,
            PATIENT_A_ID,
            CARE_NOTE_A_ID,
            users["STAFF_A"],
            "staff",
            "staff_note",
            "internal",
            "Patient called to report that the cough is more frequent at night.",
            "60000000-0000-0000-0000-000000000001",
            "2026-08-24T09:00:00+08:00",
        ),
        (
            "70000000-0000-0000-0000-000000000002",
            CLINIC_A_ID,
            PATIENT_A_ID,
            CARE_NOTE_A_ID,
            users["CLINICIAN_A"],
            "clinician",
            "clinician_note",
            "internal",
            "Assessment: persistent nocturnal cough; review inhaler technique "
            "and follow up after peak-flow diary.",
            "60000000-0000-0000-0000-000000000002",
            "2026-08-24T09:30:00+08:00",
        ),
        (
            "70000000-0000-0000-0000-000000000003",
            CLINIC_A_ID,
            PATIENT_A_ID,
            CARE_NOTE_A_ID,
            None,
            "system",
            "ai_doctor_consult_summary",
            "internal",
            "Doctor consult summary: nocturnal cough persists; inhaler technique "
            "review and a seven-day peak-flow diary were agreed.",
            "60000000-0000-0000-0000-000000000003",
            "2026-08-24T09:30:00+08:00",
        ),
        (
            "70000000-0000-0000-0000-000000000004",
            CLINIC_A_ID,
            PATIENT_A_ID,
            CARE_NOTE_A_ID,
            None,
            "system",
            "ai_nurse_consult_summary",
            "internal",
            "Nurse consult summary: technique coaching completed; patient "
            "demonstrated correct inhaler use.",
            "60000000-0000-0000-0000-000000000004",
            "2026-08-25T10:00:00+08:00",
        ),
        (
            "70000000-0000-0000-0000-000000000005",
            CLINIC_A_ID,
            PATIENT_A_ID,
            CARE_NOTE_A_ID,
            None,
            "system",
            "ai_patient_session_summary",
            "internal",
            "AI-patient session: patient asks whether the new nighttime symptoms "
            "require an earlier review.",
            "60000000-0000-0000-0000-000000000005",
            "2026-08-26T08:00:00+08:00",
        ),
        (
            "70000000-0000-0000-0000-000000000006",
            CLINIC_A_ID,
            PATIENT_A_ID,
            CARE_NOTE_A_ID,
            users["CLINICIAN_A"],
            "clinician",
            "patient_instruction",
            "patient_facing",
            "Record peak-flow readings each morning and evening for seven days. "
            "Contact the clinic sooner if breathing worsens.",
            "60000000-0000-0000-0000-000000000006",
            "2026-08-24T09:40:00+08:00",
        ),
        (
            "70000000-0000-0000-0000-000000000007",
            CLINIC_A_ID,
            PATIENT_A_ID,
            CARE_NOTE_A_ID,
            users["PATIENT_A"],
            "patient",
            "patient_insight",
            "internal",
            "The cough woke me twice last night and seems worse when the room is cold.",
            "60000000-0000-0000-0000-000000000007",
            "2026-08-26T07:50:00+08:00",
        ),
        (
            "70000000-0000-0000-0000-000000000008",
            CLINIC_B_ID,
            PATIENT_B_ID,
            CARE_NOTE_B_ID,
            users["STAFF_B"],
            "staff",
            "staff_note",
            "internal",
            "Synthetic Clinic B note used to prove tenant isolation.",
            "60000000-0000-0000-0000-000000000008",
            "2026-08-25T11:00:00+08:00",
        ),
    ]
    entry_rows = [
        {
            "id": entry_id,
            "clinic_id": clinic_id,
            "patient_id": patient_id,
            "care_note_id": note_id,
            "author_id": author_id,
            "author_role": author_role,
            "entry_type": entry_type,
            "visibility": visibility,
            "content": content,
            "content_plaintext": content,
            "source_record_id": source_id,
            "occurred_at": occurred_at,
        }
        for (
            entry_id,
            clinic_id,
            patient_id,
            note_id,
            author_id,
            author_role,
            entry_type,
            visibility,
            content,
            source_id,
            occurred_at,
        ) in entries
    ]
    client.upsert("entries", entry_rows, "id")
    client.upsert(
        "entry_versions",
        [
            {
                "id": f"c{str(row['id'])[1:]}",
                "clinic_id": row["clinic_id"],
                "patient_id": row["patient_id"],
                "entry_id": row["id"],
                "version_number": 1,
                "content_snapshot": row["content"],
                "changed_by": row["author_id"],
                "changed_by_role": row["author_role"],
                "change_reason": "Initial hosted synthetic version",
            }
            for row in entry_rows
        ],
        "entry_id,version_number",
    )
    client.upsert(
        "comments",
        [
            {
                "id": "90000000-0000-0000-0000-000000000001",
                "clinic_id": CLINIC_A_ID,
                "patient_id": PATIENT_A_ID,
                "entry_id": "70000000-0000-0000-0000-000000000003",
                "author_id": users["STAFF_A"],
                "body": "Internal synthetic comment: please confirm the follow-up interval.",
                "status": "open",
                "assigned_to": users["CLINICIAN_A"],
                "resolved_at": None,
            },
            {
                "id": "90000000-0000-0000-0000-000000000002",
                "clinic_id": CLINIC_A_ID,
                "patient_id": PATIENT_A_ID,
                "entry_id": "70000000-0000-0000-0000-000000000003",
                "parent_comment_id": "90000000-0000-0000-0000-000000000001",
                "author_id": users["CLINICIAN_A"],
                "body": (
                    "Synthetic reply: review after the seven-day diary unless symptoms worsen."
                ),
                "status": "open",
                "assigned_to": None,
                "resolved_at": None,
            },
            {
                "id": "90000000-0000-0000-0000-000000000003",
                "clinic_id": CLINIC_A_ID,
                "patient_id": PATIENT_A_ID,
                "entry_id": "70000000-0000-0000-0000-000000000004",
                "author_id": users["STAFF_A"],
                "body": ("Synthetic resolved comment: inhaler-technique coaching confirmed."),
                "status": "resolved",
                "assigned_to": None,
                "resolved_at": "2026-08-25T10:20:00+08:00",
            },
        ],
        "id",
    )
    client.upsert(
        "mentions",
        [
            {
                "id": "91000000-0000-0000-0000-000000000001",
                "clinic_id": CLINIC_A_ID,
                "patient_id": PATIENT_A_ID,
                "comment_id": "90000000-0000-0000-0000-000000000001",
                "mentioned_profile_id": users["CLINICIAN_A"],
                "created_by": users["STAFF_A"],
            }
        ],
        "comment_id,mentioned_profile_id",
    )
    entries_by_id = {str(row["id"]): row for row in entry_rows}
    highlight_specs = [
        {
            "id": "d0000000-0000-0000-0000-000000000001",
            "entry_id": "70000000-0000-0000-0000-000000000003",
            "quoted_text": "nocturnal cough persists",
            "normalized_claim": "Persistent nocturnal cough requires planned follow-up",
            "risk_level": "attention",
            "risk_reason": "Persistent night symptoms and an unresolved monitoring plan",
            "score": 82.0,
            "status": "accepted",
            "generated_by": "ai",
        },
        {
            "id": "d0000000-0000-0000-0000-000000000002",
            "entry_id": "70000000-0000-0000-0000-000000000007",
            "quoted_text": "worse when the room is cold",
            "normalized_claim": "Cold-room association may be relevant",
            "risk_level": "information",
            "risk_reason": (
                "Patient-reported context with limited independent clinical significance"
            ),
            "score": 42.0,
            "status": "rejected",
            "generated_by": "rule",
        },
    ]
    highlight_rows: list[dict[str, Any]] = []
    for spec in highlight_specs:
        entry = entries_by_id[spec["entry_id"]]
        content = str(entry["content"])
        quote = str(spec["quoted_text"])
        start = content.index(quote)
        highlight_rows.append(
            {
                **spec,
                "clinic_id": entry["clinic_id"],
                "patient_id": entry["patient_id"],
                "source_entry_id": entry["id"],
                "source_version_id": f"c{str(entry['id'])[1:]}",
                "source_start_offset": start,
                "source_end_offset": start + len(quote),
                "reviewed_by": users["CLINICIAN_A"],
                "reviewed_at": "2026-08-26T09:00:00+08:00",
            }
        )
    client.upsert("highlights", highlight_rows, "id")
    client.upsert(
        "care_tasks",
        [
            {
                "id": "b0000000-0000-0000-0000-000000000001",
                "clinic_id": CLINIC_A_ID,
                "patient_id": PATIENT_A_ID,
                "source_entry_id": "70000000-0000-0000-0000-000000000002",
                "title": "Review seven-day peak-flow diary and reassess nocturnal cough",
                "assigned_to": users["CLINICIAN_A"],
                "created_by": users["STAFF_A"],
                "status": "open",
                "priority": "high",
                "due_at": "2026-08-31T17:00:00+08:00",
                "completed_at": None,
            },
            {
                "id": "b0000000-0000-0000-0000-000000000002",
                "clinic_id": CLINIC_A_ID,
                "patient_id": PATIENT_A_ID,
                "source_entry_id": "70000000-0000-0000-0000-000000000004",
                "title": "Confirm inhaler-technique coaching was completed",
                "assigned_to": users["STAFF_A"],
                "created_by": users["CLINICIAN_A"],
                "status": "completed",
                "priority": "normal",
                "due_at": "2026-08-25T17:00:00+08:00",
                "completed_at": "2026-08-25T10:15:00+08:00",
            },
        ],
        "id",
    )


def project_ref_from_url(url: str) -> str:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".supabase.co")
    ):
        raise ValueError("Hosted seeding requires an https://<project-ref>.supabase.co URL")
    return parsed.hostname.removesuffix(".supabase.co")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-ref",
        required=True,
        help="Explicit confirmation of the hosted Supabase project reference",
    )
    parser.add_argument("--credential-file", type=Path, default=DEFAULT_CREDENTIAL_FILE)
    args = parser.parse_args()

    settings = HostedSeedSettings()  # type: ignore[call-arg]
    actual_ref = project_ref_from_url(settings.supabase_url)
    if args.project_ref != actual_ref:
        raise SystemExit(
            f"Refusing to seed: --project-ref {args.project_ref!r} does not match {actual_ref!r}"
        )

    credentials = prepare_credentials(args.credential_file)
    with SupabaseAdminClient(
        settings.supabase_url,
        settings.supabase_service_role_key,
    ) as client:
        users = client.ensure_users(credentials)
        seed_foundation(client, users)

    print(f"Hosted synthetic data seeded for {actual_ref}.")
    print(f"Demo sign-in credentials are stored locally at {args.credential_file} (mode 0600).")


if __name__ == "__main__":
    main()
