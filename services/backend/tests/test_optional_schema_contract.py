from pathlib import Path

from pglast import parse_sql

ROOT = Path(__file__).resolve().parents[3]
MIGRATION = ROOT / "supabase/migrations/202608280001_optional_deliverables.sql"


def test_optional_migration_parses_and_contains_cross_phase_capabilities() -> None:
    sql = MIGRATION.read_text()
    assert parse_sql(sql)
    for required in (
        "search_document tsvector generated always",
        "create table public.care_task_events",
        "patient_acknowledged_at",
        "create table public.comment_reactions",
        "create table public.comment_assignees",
        "create table public.notification_outbox",
        "create table public.ai_job_events",
        "create function public.cancel_ai_scribe_job",
        "create function public.review_highlights_bulk",
        "create function public.record_importance_feedback",
        "create function public.reset_importance_preferences",
        "create table public.pseudonym_mappings",
        "create table public.importance_preferences",
        "embedding extensions.vector(16)",
        "create function public.decayed_preference_weight",
    ):
        assert required in sql


def test_optional_sensitive_tables_are_rls_protected() -> None:
    sql = MIGRATION.read_text()
    for table in (
        "notification_outbox",
        "patient_summary_reviews",
        "pseudonym_mappings",
        "importance_preferences",
    ):
        assert f"alter table public.{table} enable row level security" in sql
    assert "grant" not in " ".join(
        line for line in sql.splitlines() if "pseudonym_mappings" in line and "grant" in line
    )
