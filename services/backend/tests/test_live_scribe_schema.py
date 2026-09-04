from pathlib import Path

from pglast import parse_sql

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "supabase/migrations/202608280006_live_scribe_sessions.sql"
WORKER_GRANTS = ROOT / "supabase/migrations/202608280007_worker_service_role_grants.sql"
WORKER_LOCK_GRANTS = ROOT / "supabase/migrations/202608280008_worker_lock_grants.sql"


def test_live_scribe_migration_parses_and_owns_source_job_transaction() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    lowered = sql.lower()

    assert parse_sql(sql)
    assert "create function public.create_clinical_scribe_session" in lowered
    assert "create function public.submit_patient_ai_session" in lowered
    assert "insert into public.source_records" in lowered
    assert "insert into public.entries" in lowered
    assert "insert into public.entry_versions" in lowered
    assert "insert into public.ai_jobs" in lowered
    assert "p_interaction_type not in ('doctor_consult', 'nurse_consult')" in lowered
    assert "array['clinician']::public.clinic_role[]" in lowered
    assert "array['staff']::public.clinic_role[]" in lowered


def test_patient_status_function_returns_only_safe_job_fields() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    status_function = sql.split("create function public.list_own_patient_ai_jobs()", 1)[1]
    status_function = status_function.split("$$;", 1)[0]

    assert "patient.linked_profile_id = auth.uid()" in status_function
    assert "job.requested_by = auth.uid()" in status_function
    assert "job.interaction_type = 'ai_patient_session'" in status_function
    assert "source_record_id" not in status_function
    assert "output_entry_id" not in status_function
    assert "provider_name" not in status_function


def test_patient_session_is_internal_and_admin_cannot_create_clinical_session() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    clinical_function = sql.split("create function public.create_clinical_scribe_session", 1)[1]
    clinical_function = clinical_function.split(
        "create function public.submit_patient_ai_session", 1
    )[0]
    patient_function = sql.split("create function public.submit_patient_ai_session", 1)[1]
    patient_function = patient_function.split(
        "create function public.list_own_patient_ai_jobs", 1
    )[0]

    assert "'admin'" not in clinical_function
    assert "'patient', 'patient_insight', 'internal'" in patient_function
    assert "'ai_patient_session'" in patient_function
    assert "'patient_summary'" not in patient_function


def test_worker_service_role_has_least_privilege_table_grants() -> None:
    sql = WORKER_GRANTS.read_text(encoding="utf-8")
    lowered = sql.lower()

    assert parse_sql(sql)
    assert "grant select on table" in lowered
    assert "public.ai_jobs" in lowered
    assert "public.source_records" in lowered
    assert "public.entries" in lowered
    assert "public.entry_versions" in lowered
    assert "public.patients" in lowered
    assert "public.profiles" in lowered
    assert "public.care_notes" in lowered
    assert "grant update on table public.ai_jobs to service_role" in lowered
    assert "public.highlights" in lowered
    assert "public.audit_events" in lowered
    assert "public.ai_job_events" in lowered
    assert "grant all" not in lowered
    assert "to authenticated" not in lowered


def test_worker_can_take_completion_row_locks() -> None:
    sql = WORKER_LOCK_GRANTS.read_text(encoding="utf-8")
    lowered = sql.lower()

    assert parse_sql(sql)
    assert "grant update on table" in lowered
    assert "public.source_records" in lowered
    assert "public.care_notes" in lowered
    assert "to service_role" in lowered
    assert "grant all" not in lowered
