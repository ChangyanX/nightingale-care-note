from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MIGRATION = REPOSITORY_ROOT / "supabase/migrations/202608270004_ai_jobs.sql"


def test_job_table_has_no_raw_transcript_or_provider_payload_columns() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    table = sql.split("create table public.ai_jobs", 1)[1].split(");", 1)[0]

    assert "transcript" not in table
    assert "prompt" not in table
    assert "response_body" not in table
    assert "provider_error" not in table
    assert "safe_error_code" in table


def test_submission_is_idempotent_and_caller_scoped() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "unique (clinic_id, idempotency_key)" in sql
    assert "on conflict (clinic_id, idempotency_key)" in sql
    assert "do nothing" in sql
    assert "if submitted_job.id is null" in sql
    assert "security invoker" in sql
    assert "requested_by = (select auth.uid())" in sql
    assert "array['staff', 'clinician']" in sql
    assert "array['staff', 'clinician', 'admin']" in sql


def test_claim_uses_skip_locked_and_is_worker_only() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "for update skip locked" in sql
    assert "lease_expires_at <= now()" in sql
    assert "attempt_count < max_attempts" in sql
    assert "grant execute on function public.claim_ai_scribe_job(integer) to service_role" in sql
    assert (
        "grant execute on function public.claim_ai_scribe_job(integer) to authenticated" not in sql
    )


def test_worker_failure_transition_is_retry_bounded_and_sanitized() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "create function public.fail_ai_scribe_job" in sql
    assert "p_safe_error_code !~ '^[a-z0-9_]{1,64}$'" in sql
    assert "current_job.attempt_count < current_job.max_attempts" in sql
    assert "when p_retryable then 'dead_letter'" in sql
    assert "else 'failed'" in sql
    assert "grant execute on function public.fail_ai_scribe_job" in sql
    assert "to service_role" in sql


def test_source_type_mapping_and_patient_tenancy_are_database_enforced() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "foreign key (source_record_id, clinic_id, patient_id)" in sql
    assert "validate_ai_job_source_before_insert" in sql
    assert "interaction_type = 'doctor_consult' and source_kind <> 'doctor_consult'" in sql
    assert "interaction_type = 'nurse_consult' and source_kind <> 'nurse_consult'" in sql
    assert "interaction_type = 'ai_patient_session' and source_kind <> 'ai_patient_session'" in sql
