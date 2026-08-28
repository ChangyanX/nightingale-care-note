"""Create hosted synthetic users and seed the Phase 1 demonstration dataset."""

from __future__ import annotations

import argparse
import os
import secrets
import string
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CREDENTIAL_FILE = REPOSITORY_ROOT / ".env.hosted-demo"

CLINIC_A_ID = "10000000-0000-0000-0000-000000000001"
CLINIC_B_ID = "10000000-0000-0000-0000-000000000002"
PATIENT_A_ID = "40000000-0000-0000-0000-000000000001"
PATIENT_A2_ID = "40000000-0000-0000-0000-000000000002"
PATIENT_B_ID = "40000000-0000-0000-0000-000000000003"
PATIENT_A3_ID = "40000000-0000-0000-0000-000000000004"
PATIENT_B2_ID = "40000000-0000-0000-0000-000000000005"
CARE_NOTE_A_ID = "50000000-0000-0000-0000-000000000001"
CARE_NOTE_A2_ID = "50000000-0000-0000-0000-000000000002"
CARE_NOTE_B_ID = "50000000-0000-0000-0000-000000000003"
CARE_NOTE_A3_ID = "50000000-0000-0000-0000-000000000004"
CARE_NOTE_B2_ID = "50000000-0000-0000-0000-000000000005"


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


@dataclass(frozen=True)
class PatientStory:
    key: str
    patient_id: str
    clinic_id: str
    care_note_id: str
    patient_user_key: str
    staff_user_key: str
    clinician_user_key: str
    patient_update: str
    staff_note: str
    clinician_note_v1: str
    clinician_note_v2: str
    doctor_summary: str
    nurse_summary: str
    ai_patient_summary: str
    patient_instruction: str
    patient_summary: str
    risk_quote: str
    risk_reason: str
    task_title: str


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
    DemoIdentity(
        "PATIENT_A2",
        "patient.a2@nightingale-demo.invalid",
        "Morgan Example (Synthetic)",
    ),
    DemoIdentity(
        "PATIENT_B",
        "patient.b@nightingale-demo.invalid",
        "Riley Example (Synthetic)",
    ),
    DemoIdentity(
        "PATIENT_A3",
        "patient.a3@nightingale-demo.invalid",
        "Jamie Sample (Synthetic)",
    ),
    DemoIdentity(
        "PATIENT_B2",
        "patient.b2@nightingale-demo.invalid",
        "Quinn Sample (Synthetic)",
    ),
)


RICH_STORIES = (
    PatientStory(
        "parker",
        PATIENT_A_ID,
        CLINIC_A_ID,
        CARE_NOTE_A_ID,
        "PATIENT_A",
        "STAFF_A",
        "CLINICIAN_A",
        "Synthetic patient update: the cough woke me twice during the night.",
        "Synthetic staff note: the peak-flow diary follow-up remains open.",
        "Synthetic clinician draft: review nocturnal cough and inhaler technique.",
        "Synthetic clinician note: review cough, technique, and the seven-day diary.",
        "Doctor consult summary: nocturnal cough persists and needs planned follow-up.",
        "Nurse consult summary: inhaler technique coaching was completed.",
        "AI-patient session summary: patient asked whether to request earlier review.",
        "Record morning and evening peak flow for seven synthetic days.",
        "Your care team is reviewing the synthetic nighttime cough pattern.",
        "nocturnal cough persists and needs planned follow-up",
        "The synthetic nighttime pattern remains unresolved.",
        "Review seven-day peak-flow diary",
    ),
    PatientStory(
        "morgan",
        PATIENT_A2_ID,
        CLINIC_A_ID,
        CARE_NOTE_A2_ID,
        "PATIENT_A2",
        "STAFF_A",
        "CLINICIAN_A",
        "Synthetic patient update: morning headaches have occurred on three days this week.",
        "Synthetic staff note: the home-reading diary was received for follow-up.",
        "Synthetic clinician draft: review variable morning readings.",
        "Synthetic clinician note: review morning readings and repeat the validated diary.",
        "Doctor consult summary: elevated morning readings require timely review.",
        "Nurse consult summary: cuff positioning and diary technique were reviewed.",
        "AI-patient session summary: patient asked how to record readings consistently.",
        "Record morning readings after five minutes seated rest for seven days.",
        "Your care team is reviewing your synthetic home-reading diary.",
        "elevated morning readings require timely review",
        "Repeated synthetic readings remain unresolved.",
        "Review repeat home-reading diary",
    ),
    PatientStory(
        "riley",
        PATIENT_B_ID,
        CLINIC_B_ID,
        CARE_NOTE_B_ID,
        "PATIENT_B",
        "STAFF_B",
        "CLINICIAN_B",
        "Synthetic patient update: knee stiffness settles after gentle movement.",
        "Synthetic staff note: afternoon physiotherapy availability was checked.",
        "Synthetic clinician draft: mechanical symptoms without acute injury.",
        "Synthetic clinician note: assess function after the activity trial.",
        "Doctor consult summary: difficulty on stairs needs planned functional review.",
        "Nurse consult summary: pacing and the symptom diary were reviewed.",
        "AI-patient session summary: patient asked which activities to record.",
        "Use gentle movement and record a daily synthetic symptom score.",
        "Your care team recommends a short activity and symptom diary.",
        "difficulty on stairs needs planned functional review",
        "Synthetic functional change remains unresolved.",
        "Review knee symptom and activity diary",
    ),
    PatientStory(
        "jamie",
        PATIENT_A3_ID,
        CLINIC_A_ID,
        CARE_NOTE_A3_ID,
        "PATIENT_A3",
        "STAFF_A",
        "CLINICIAN_A",
        "Synthetic patient update: sleep averaged five hours during a study week.",
        "Synthetic staff note: a non-urgent wellbeing check was requested.",
        "Synthetic clinician draft: short sleep after schedule disruption.",
        "Synthetic clinician note: review sleep trend and daytime impact.",
        "Doctor consult summary: daytime fatigue should be reassessed after the log.",
        "Nurse consult summary: sleep-log instructions were discussed.",
        "AI-patient session summary: patient asked how to track daytime energy.",
        "Keep a seven-night synthetic sleep and daytime-energy log.",
        "Your care team is reviewing a temporary synthetic sleep change.",
        "daytime fatigue should be reassessed",
        "The synthetic fatigue trend remains unconfirmed.",
        "Review seven-night sleep and energy log",
    ),
    PatientStory(
        "quinn",
        PATIENT_B2_ID,
        CLINIC_B_ID,
        CARE_NOTE_B2_ID,
        "PATIENT_B2",
        "STAFF_B",
        "CLINICIAN_B",
        "Synthetic patient update: seasonal nasal symptoms are worse outdoors.",
        "Synthetic staff note: the non-prescription product list was collected.",
        "Synthetic clinician draft: seasonal pattern without breathing difficulty.",
        "Synthetic clinician note: review response to the agreed measures.",
        "Doctor consult summary: symptoms disrupting sleep need follow-up.",
        "Nurse consult summary: trigger diary instructions were reviewed.",
        "AI-patient session summary: patient asked when to contact the clinic.",
        "Follow the released synthetic plan and record seasonal triggers.",
        "Your care team has released a synthetic seasonal-symptom plan.",
        "symptoms disrupting sleep need follow-up",
        "Synthetic sleep disruption remains unresolved.",
        "Review seasonal symptom and trigger diary",
    ),
)


def demo_uuid(label: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"nightingale-care-note:{label}"))


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
            {
                "id": users[identity.key],
                "display_name": identity.display_name,
                "preferred_name": identity.display_name,
                "birth_date": {
                    "PATIENT_A": "1991-04-12",
                    "PATIENT_A2": "1986-09-03",
                    "PATIENT_B": "1978-01-21",
                    "PATIENT_A3": "2001-06-17",
                    "PATIENT_B2": "1994-11-28",
                }.get(identity.key),
            }
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
                "linked_profile_id": users["PATIENT_A2"],
                "synthetic_identifier": "SYN-A-002",
                "display_name": "Morgan Example (Synthetic)",
            },
            {
                "id": PATIENT_B_ID,
                "clinic_id": CLINIC_B_ID,
                "linked_profile_id": users["PATIENT_B"],
                "synthetic_identifier": "SYN-B-001",
                "display_name": "Riley Example (Synthetic)",
            },
            {
                "id": PATIENT_A3_ID,
                "clinic_id": CLINIC_A_ID,
                "linked_profile_id": users["PATIENT_A3"],
                "synthetic_identifier": "SYN-A-003",
                "display_name": "Jamie Sample (Synthetic)",
            },
            {
                "id": PATIENT_B2_ID,
                "clinic_id": CLINIC_B_ID,
                "linked_profile_id": users["PATIENT_B2"],
                "synthetic_identifier": "SYN-B-002",
                "display_name": "Quinn Sample (Synthetic)",
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
            {"id": CARE_NOTE_A3_ID, "clinic_id": CLINIC_A_ID, "patient_id": PATIENT_A3_ID},
            {"id": CARE_NOTE_B2_ID, "clinic_id": CLINIC_B_ID, "patient_id": PATIENT_B2_ID},
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
        (
            "60000000-0000-0000-0000-000000000009",
            CLINIC_A_ID,
            PATIENT_A_ID,
            "manual",
            "staff-note-002",
            users["STAFF_A"],
            "2026-08-25T16:00:00+08:00",
        ),
    ]
    source_specs = (
        ("patient_update", "manual", "patient", "2026-08-18T08:10:00+08:00"),
        ("staff_note", "manual", "staff", "2026-08-19T10:20:00+08:00"),
        ("clinician_note", "manual", "clinician", "2026-08-20T14:00:00+08:00"),
        ("doctor_session", "doctor_consult", "system", "2026-08-20T14:05:00+08:00"),
        ("nurse_session", "nurse_consult", "system", "2026-08-21T11:15:00+08:00"),
        (
            "ai_patient_session",
            "ai_patient_session",
            "system",
            "2026-08-22T19:30:00+08:00",
        ),
        (
            "patient_instruction",
            "manual",
            "clinician",
            "2026-08-20T14:15:00+08:00",
        ),
        ("patient_summary", "manual", "clinician", "2026-08-23T09:00:00+08:00"),
    )
    for story in RICH_STORIES:
        author_ids = {
            "patient": users[story.patient_user_key],
            "staff": users[story.staff_user_key],
            "clinician": users[story.clinician_user_key],
            "system": None,
        }
        for kind, source_type, author_kind, occurred_at in source_specs:
            sources.append(
                (
                    demo_uuid(f"{story.key}:source:{kind}"),
                    story.clinic_id,
                    story.patient_id,
                    source_type,
                    f"synthetic-{story.key}-{kind}",
                    author_ids[author_kind],
                    occurred_at,
                )
            )
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
        (
            "70000000-0000-0000-0000-000000000009",
            CLINIC_A_ID,
            PATIENT_A_ID,
            CARE_NOTE_A_ID,
            users["STAFF_A"],
            "staff",
            "staff_note",
            "internal",
            "Secondary concern: sleep disruption is affecting daytime concentration, "
            "but there are no synthetic red-flag symptoms.",
            "60000000-0000-0000-0000-000000000009",
            "2026-08-25T16:00:00+08:00",
        ),
    ]
    entry_specs = (
        ("patient_update", "patient", "patient_insight", "internal", "patient_update"),
        ("staff_note", "staff", "staff_note", "internal", "staff_note"),
        (
            "clinician_note",
            "clinician",
            "clinician_note",
            "internal",
            "clinician_note_v2",
        ),
        (
            "doctor_session",
            "system",
            "ai_doctor_consult_summary",
            "internal",
            "doctor_summary",
        ),
        (
            "nurse_session",
            "system",
            "ai_nurse_consult_summary",
            "internal",
            "nurse_summary",
        ),
        (
            "ai_patient_session",
            "system",
            "ai_patient_session_summary",
            "internal",
            "ai_patient_summary",
        ),
        (
            "patient_instruction",
            "clinician",
            "patient_instruction",
            "patient_facing",
            "patient_instruction",
        ),
        (
            "patient_summary",
            "clinician",
            "patient_summary",
            "patient_facing",
            "patient_summary",
        ),
    )
    occurred_by_kind = {spec[0]: spec[3] for spec in source_specs}
    revised_entry_ids: set[str] = set()
    for story in RICH_STORIES:
        author_ids = {
            "patient": users[story.patient_user_key],
            "staff": users[story.staff_user_key],
            "clinician": users[story.clinician_user_key],
            "system": None,
        }
        for kind, author_role, entry_type, visibility, content_field in entry_specs:
            entry_id = demo_uuid(f"{story.key}:entry:{kind}")
            if kind == "clinician_note":
                revised_entry_ids.add(entry_id)
            entries.append(
                (
                    entry_id,
                    story.clinic_id,
                    story.patient_id,
                    story.care_note_id,
                    author_ids[author_role],
                    author_role,
                    entry_type,
                    visibility,
                    getattr(story, content_field),
                    demo_uuid(f"{story.key}:source:{kind}"),
                    occurred_by_kind[kind],
                )
            )
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
            "current_version": 2 if entry_id in revised_entry_ids else 1,
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
    entry_versions = [
            {
                "id": f"c{str(row['id'])[1:]}",
                "clinic_id": row["clinic_id"],
                "patient_id": row["patient_id"],
                "entry_id": row["id"],
                "version_number": 1,
                "content_snapshot": next(
                    (
                        story.clinician_note_v1
                        for story in RICH_STORIES
                        if row["id"] == demo_uuid(f"{story.key}:entry:clinician_note")
                    ),
                    row["content"],
                ),
                "changed_by": row["author_id"],
                "changed_by_role": row["author_role"],
                "change_reason": "Initial hosted synthetic version",
            }
            for row in entry_rows
        ]
    for story in RICH_STORIES:
        entry_versions.append(
            {
                "id": demo_uuid(f"{story.key}:entry-version:clinician_note:2"),
                "clinic_id": story.clinic_id,
                "patient_id": story.patient_id,
                "entry_id": demo_uuid(f"{story.key}:entry:clinician_note"),
                "version_number": 2,
                "content_snapshot": story.clinician_note_v2,
                "changed_by": users[story.clinician_user_key],
                "changed_by_role": "clinician",
                "change_reason": "Synthetic revision: added explicit follow-up detail",
            }
        )
    client.upsert("entry_versions", entry_versions, "entry_id,version_number")
    section_rows: list[dict[str, Any]] = []
    for story in RICH_STORIES:
        section_specs = (
            (
                "staff_note",
                "staff",
                users[story.staff_user_key],
                "internal",
                "Synthetic coordination status: the follow-up workflow is open.",
            ),
            (
                "assessment",
                "clinician",
                users[story.clinician_user_key],
                "internal",
                story.clinician_note_v2,
            ),
            (
                "plan",
                "clinician",
                users[story.clinician_user_key],
                "internal",
                f"{story.task_title}; confirm at the next review.",
            ),
            (
                "patient_instruction",
                "clinician",
                users[story.clinician_user_key],
                "patient_facing",
                story.patient_instruction,
            ),
        )
        for section_type, owner_role, creator, visibility, content in section_specs:
            section_rows.append(
                {
                    "id": demo_uuid(f"{story.key}:section:{section_type}"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "care_note_id": story.care_note_id,
                    "section_type": section_type,
                    "owner_role": owner_role,
                    "created_by": creator,
                    "visibility": visibility,
                    "content": content,
                }
            )
    client.upsert("note_sections", section_rows, "id")
    client.upsert(
        "section_versions",
        [
            {
                "clinic_id": row["clinic_id"],
                "patient_id": row["patient_id"],
                "section_id": row["id"],
                "version_number": 1,
                "content_snapshot": row["content"],
                "changed_by": row["created_by"],
                "changed_by_role": row["owner_role"],
                "change_reason": "Initial hosted synthetic version",
            }
            for row in section_rows
        ],
        "section_id,version_number",
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
    rich_comment_rows: list[dict[str, Any]] = []
    for story in RICH_STORIES:
        rich_comment_rows.extend(
            (
                {
                    "id": demo_uuid(f"{story.key}:comment:open"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "entry_id": demo_uuid(f"{story.key}:entry:doctor_session"),
                    "author_id": users[story.staff_user_key],
                    "body": "Internal synthetic comment: confirm review timing after the diary.",
                    "status": "open",
                    "assigned_to": users[story.clinician_user_key],
                    "resolved_at": None,
                },
                {
                    "id": demo_uuid(f"{story.key}:comment:resolved"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "entry_id": demo_uuid(f"{story.key}:entry:nurse_session"),
                    "author_id": users[story.clinician_user_key],
                    "body": "Internal synthetic comment: education step confirmed.",
                    "status": "resolved",
                    "assigned_to": None,
                    "resolved_at": "2026-08-21T12:00:00+08:00",
                },
            )
        )
    client.upsert("comments", rich_comment_rows, "id")
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
    highlight_specs: list[dict[str, Any]] = [
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
    rich_highlights: list[dict[str, Any]] = []
    for story in RICH_STORIES:
        entry_id = demo_uuid(f"{story.key}:entry:doctor_session")
        content = story.doctor_summary
        start = content.index(story.risk_quote)
        rich_highlights.append(
            {
                "id": demo_uuid(f"{story.key}:highlight:attention"),
                "clinic_id": story.clinic_id,
                "patient_id": story.patient_id,
                "source_entry_id": entry_id,
                "source_version_id": f"c{entry_id[1:]}",
                "source_start_offset": start,
                "source_end_offset": start + len(story.risk_quote),
                "quoted_text": story.risk_quote,
                "normalized_claim": story.risk_reason,
                "risk_level": "attention",
                "risk_reason": story.risk_reason,
                "score": 78.0,
                "status": "accepted",
                "generated_by": "ai",
                "reviewed_by": users[story.clinician_user_key],
                "reviewed_at": "2026-08-23T10:00:00+08:00",
                "category": "risk",
            }
        )
    client.upsert("highlights", rich_highlights, "id")
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
                "category": "monitoring",
                "patient_visible": True,
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
                "category": "clinical_review",
                "patient_visible": False,
                "due_at": "2026-08-25T17:00:00+08:00",
                "completed_at": "2026-08-25T10:15:00+08:00",
            },
        ],
        "id",
    )
    rich_tasks: list[dict[str, Any]] = []
    for story in RICH_STORIES:
        rich_tasks.extend(
            (
                {
                    "id": demo_uuid(f"{story.key}:task:open"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "source_entry_id": demo_uuid(f"{story.key}:entry:clinician_note"),
                    "title": story.task_title,
                    "assigned_to": users[story.clinician_user_key],
                    "created_by": users[story.staff_user_key],
                    "status": "open",
                    "priority": "high",
                    "category": "monitoring",
                    "patient_visible": True,
                    "due_at": "2026-09-04T17:00:00+08:00",
                    "completed_at": None,
                },
                {
                    "id": demo_uuid(f"{story.key}:task:complete"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "source_entry_id": demo_uuid(f"{story.key}:entry:nurse_session"),
                    "title": "Confirm synthetic coaching step",
                    "assigned_to": users[story.staff_user_key],
                    "created_by": users[story.clinician_user_key],
                    "status": "completed",
                    "priority": "normal",
                    "category": "clinical_review",
                    "patient_visible": False,
                    "due_at": "2026-08-22T17:00:00+08:00",
                    "completed_at": "2026-08-21T12:00:00+08:00",
                },
            )
        )
    client.upsert("care_tasks", rich_tasks, "id")

    client.upsert(
        "appointment_requests",
        [
            {
                "id": demo_uuid(f"{story.key}:appointment"),
                "clinic_id": story.clinic_id,
                "patient_id": story.patient_id,
                "requested_by": users[story.patient_user_key],
                "preferred_date": (date.today() + timedelta(days=7)).isoformat(),
                "time_preference": "afternoon" if story.key in {"riley", "quinn"} else "morning",
                "reason_category": "follow_up",
                "note": "Synthetic demo appointment request; no real health information.",
                "status": "requested",
            }
            for story in RICH_STORIES
        ],
        "id",
    )
    report_rows: list[dict[str, Any]] = []
    for story in RICH_STORIES:
        report_rows.extend(
            (
                {
                    "id": demo_uuid(f"{story.key}:report:available"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "title": "Synthetic care-plan summary",
                    "report_type": "care_plan",
                    "status": "available",
                    "released_at": "2026-08-23T09:00:00+08:00",
                    "released_by": users[story.clinician_user_key],
                    "patient_safe_summary": f"Released synthetic report: {story.patient_summary}",
                },
                {
                    "id": demo_uuid(f"{story.key}:report:preparing"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "title": "Synthetic follow-up report",
                    "report_type": "other",
                    "status": "preparing",
                    "released_at": None,
                    "released_by": None,
                    "patient_safe_summary": None,
                },
            )
        )
    client.upsert("patient_reports", report_rows, "id")
    client.upsert(
        "patient_observations",
        [
            {
                "id": demo_uuid(f"{story.key}:observation:{day}"),
                "clinic_id": story.clinic_id,
                "patient_id": story.patient_id,
                "recorded_by": users[story.patient_user_key],
                "observation_type": "symptom_score",
                "value": value,
                "unit": "score/10",
                "observed_at": f"2026-08-{20 + day:02d}T08:00:00+08:00",
            }
            for story in RICH_STORIES
            for day, value in ((0, 6), (1, 5), (2, 4))
        ],
        "id",
    )
    notification_rows: list[dict[str, Any]] = []
    for story in RICH_STORIES:
        notification_rows.extend(
            (
                {
                    "id": demo_uuid(f"{story.key}:notification:staff"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "recipient_id": users[story.staff_user_key],
                    "event_type": "care_update",
                    "resource_type": "patient",
                    "resource_id": story.patient_id,
                    "status": "delivered",
                    "delivered_at": "2026-08-23T09:05:00+08:00",
                    "read_at": None,
                },
                {
                    "id": demo_uuid(f"{story.key}:notification:clinician"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "recipient_id": users[story.clinician_user_key],
                    "event_type": "assignment",
                    "resource_type": "care_task",
                    "resource_id": demo_uuid(f"{story.key}:task:open"),
                    "status": "delivered",
                    "delivered_at": "2026-08-23T09:06:00+08:00",
                    "read_at": None,
                },
                {
                    "id": demo_uuid(f"{story.key}:notification:patient"),
                    "clinic_id": story.clinic_id,
                    "patient_id": story.patient_id,
                    "recipient_id": users[story.patient_user_key],
                    "event_type": "care_update",
                    "resource_type": "patient_summary",
                    "resource_id": demo_uuid(f"{story.key}:entry:patient_summary"),
                    "status": "delivered",
                    "delivered_at": "2026-08-23T09:07:00+08:00",
                    "read_at": None,
                },
            )
        )
    client.upsert(
        "notification_outbox",
        notification_rows,
        "recipient_id,event_type,resource_id",
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

    settings = HostedSeedSettings()
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
