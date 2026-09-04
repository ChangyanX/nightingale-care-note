import json
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
from pglast import parse_sql

from app.domain.scribe import ScribeInteractionType, ScribeOutput, prepare_scribe_persistence
from app.infrastructure.llm import FakeScribeProvider
from app.worker import (
    ScribeJob,
    ScribeWorker,
    SourceDocument,
    SupabaseSourceDocumentLoader,
    SupabaseWorkerBackend,
    WorkerBackendError,
)
from app.worker.config import WorkerSettings

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MIGRATION = REPOSITORY_ROOT / "supabase/migrations/202608280003_ai_persistence.sql"
FIXTURES = Path(__file__).parent / "fixtures"

JOB_ID = "d0000000-0000-0000-0000-000000000001"
CLINIC_ID = "10000000-0000-0000-0000-000000000001"
PATIENT_ID = "40000000-0000-0000-0000-000000000001"
SOURCE_ID = "60000000-0000-0000-0000-000000000003"


def load_output(name: str) -> ScribeOutput:
    return ScribeOutput.model_validate_json(
        (FIXTURES / f"scribe_{name}.json").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize(
    "fixture_name",
    ["doctor_consult", "nurse_consult", "ai_patient_session"],
)
def test_prepared_entry_has_exact_nfc_highlight_offsets(fixture_name: str) -> None:
    prepared = prepare_scribe_persistence(load_output(fixture_name))

    for highlight in prepared.highlights:
        start = highlight["source_start_offset"]
        end = highlight["source_end_offset"]
        assert prepared.content[start:end] == highlight["quoted_text"]


def test_atomic_persistence_migration_parses_and_owns_the_complete_transition() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    lowered = sql.lower()

    assert parse_sql(sql)
    assert "for update" in lowered
    assert "if current_job.status = 'succeeded'" in lowered
    assert "return current_job" in lowered
    assert "insert into public.entries" in lowered
    assert "insert into public.entry_versions" in lowered
    assert "insert into public.highlights" in lowered
    assert "insert into public.audit_events" in lowered
    assert "set status = 'succeeded'" in lowered
    assert "output_entry_id = output_entry.id" in lowered
    assert "to service_role" in lowered
    assert "to authenticated" not in lowered


@pytest.mark.parametrize(
    ("interaction_type", "entry_type"),
    [
        ("doctor_consult", "ai_doctor_consult_summary"),
        ("nurse_consult", "ai_nurse_consult_summary"),
        ("ai_patient_session", "ai_patient_session_summary"),
    ],
)
def test_database_maps_job_interaction_to_required_entry_type(
    interaction_type: str,
    entry_type: str,
) -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert f"when '{interaction_type}' then '{entry_type}'::public.entry_type" in sql


class SyntheticSourceLoader:
    async def load(self, job: ScribeJob) -> SourceDocument:
        assert str(job.source_record_id) == SOURCE_ID
        return SourceDocument(
            "Parker Patient says the cough is still waking me at night.",
            known_names=("Parker Patient",),
        )


@pytest.mark.asyncio
async def test_worker_reports_database_authorization_failure_without_response_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/rpc/claim_ai_scribe_job")
        return httpx.Response(
            403,
            json={"message": "permission denied for table ai_jobs", "secret": "not surfaced"},
        )

    settings = WorkerSettings(
        supabase_url="http://supabase.test",
        supabase_service_role_key="synthetic-service-role-key",
    )
    backend = SupabaseWorkerBackend(
        settings,
        SyntheticSourceLoader(),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(WorkerBackendError) as captured:
        await backend.claim()

    assert captured.value.code == "worker_database_authorization_failed"
    assert captured.value.retryable is False
    assert "permission denied" not in str(captured.value)


@pytest.mark.asyncio
async def test_worker_treats_all_null_composite_claim_as_empty_queue() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/rpc/claim_ai_scribe_job")
        return httpx.Response(
            200,
            json={
                "id": None,
                "clinic_id": None,
                "patient_id": None,
                "source_record_id": None,
                "interaction_type": None,
                "attempt_count": None,
                "max_attempts": None,
            },
        )

    settings = WorkerSettings(
        supabase_url="http://supabase.test",
        supabase_service_role_key="synthetic-service-role-key",
    )
    backend = SupabaseWorkerBackend(
        settings,
        SyntheticSourceLoader(),
        transport=httpx.MockTransport(handler),
    )

    assert await backend.claim() is None


@pytest.mark.asyncio
async def test_production_source_loader_reads_only_role_authored_source_text() -> None:
    requested_tables: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["apikey"] == "synthetic-service-role-key"
        requested_tables.append(request.url.path)
        if request.url.path.endswith("/source_records"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": SOURCE_ID,
                        "clinic_id": CLINIC_ID,
                        "patient_id": PATIENT_ID,
                        "created_by": "20000000-0000-0000-0000-000000000003",
                    }
                ],
            )
        if request.url.path.endswith("/entries"):
            assert request.url.params["author_role"] == "neq.system"
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "70000000-0000-0000-0000-000000000001",
                        "content_plaintext": "Parker Patient reports improved breathing.",
                        "author_role": "clinician",
                        "created_at": "2026-08-28T12:00:00+08:00",
                    }
                ],
            )
        if request.url.path.endswith("/patients"):
            return httpx.Response(200, json=[{"display_name": "Parker Patient"}])
        if request.url.path.endswith("/profiles"):
            return httpx.Response(
                200,
                json=[{"display_name": "Dr. Casey Clinician", "preferred_name": "Casey"}],
            )
        raise AssertionError(f"Unexpected source-loader request: {request.url.path}")

    settings = WorkerSettings(
        supabase_url="http://supabase.test",
        supabase_service_role_key="synthetic-service-role-key",
    )
    loader = SupabaseSourceDocumentLoader(
        settings,
        transport=httpx.MockTransport(handler),
    )
    source = await loader.load(
        ScribeJob(
            id=UUID(JOB_ID),
            clinic_id=UUID(CLINIC_ID),
            patient_id=UUID(PATIENT_ID),
            source_record_id=UUID(SOURCE_ID),
            interaction_type=ScribeInteractionType.DOCTOR_CONSULT,
            attempt_count=1,
            max_attempts=3,
        )
    )

    assert source.text == "Parker Patient reports improved breathing."
    assert source.known_names == ("Parker Patient", "Dr. Casey Clinician", "Casey")
    assert len(requested_tables) == 4


@pytest.mark.asyncio
async def test_production_backend_commits_validated_output_through_atomic_rpc() -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["apikey"] == "synthetic-service-role-key"
        payload = json.loads(request.content) if request.content else {}
        calls.append((request.url.path, payload))
        if request.url.path.endswith("/rpc/claim_ai_scribe_job"):
            return httpx.Response(
                200,
                json={
                    "id": JOB_ID,
                    "clinic_id": CLINIC_ID,
                    "patient_id": PATIENT_ID,
                    "source_record_id": SOURCE_ID,
                    "interaction_type": "doctor_consult",
                    "attempt_count": 1,
                    "max_attempts": 3,
                },
            )
        if request.url.path.endswith("/rpc/complete_ai_scribe_job"):
            return httpx.Response(200, json={"id": JOB_ID, "status": "succeeded"})
        if request.url.path.endswith("/ai_job_events"):
            return httpx.Response(201, json={})
        raise AssertionError(f"Unexpected worker request: {request.url.path}")

    settings = WorkerSettings(
        supabase_url="http://supabase.test",
        supabase_service_role_key="synthetic-service-role-key",
        llm_provider="fake",
    )
    backend = SupabaseWorkerBackend(
        settings,
        SyntheticSourceLoader(),
        transport=httpx.MockTransport(handler),
    )

    processed = await ScribeWorker(
        backend,
        FakeScribeProvider(load_output("doctor_consult")),
    ).run_once()

    assert processed is True
    complete_calls = [item for item in calls if item[0].endswith("complete_ai_scribe_job")]
    assert len(complete_calls) == 1
    payload = complete_calls[0][1]
    assert payload["p_job_id"] == JOB_ID
    assert payload["p_provider_name"] == "fake"
    assert payload["p_schema_version"] == "1.0"
    assert "Parker Patient" not in payload["p_content"]
    assert payload["p_highlights"]
    for highlight in payload["p_highlights"]:
        assert (
            payload["p_content"][
                highlight["source_start_offset"] : highlight["source_end_offset"]
            ]
            == highlight["quoted_text"]
        )
        assert "clinic_id" not in highlight
        assert "patient_id" not in highlight
        assert "status" not in highlight
