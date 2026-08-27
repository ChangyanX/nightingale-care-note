from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ENTRY_RPCS = REPOSITORY_ROOT / "supabase" / "migrations" / "202608260002_entry_rpcs.sql"
REVISION_RPCS = REPOSITORY_ROOT / "supabase" / "migrations" / "202608270003_revision_revert.sql"


def revision_sql() -> str:
    return REVISION_RPCS.read_text(encoding="utf-8")


def test_entry_and_section_mutations_append_versions_and_audits() -> None:
    sql = ENTRY_RPCS.read_text(encoding="utf-8") + revision_sql()

    assert sql.count("insert into public.entry_versions") >= 3
    assert sql.count("insert into public.section_versions") >= 2
    assert sql.count("insert into public.audit_events") >= 5
    assert "current_version = current_version + 1" in sql


def test_revert_uses_historical_snapshot_and_creates_new_version() -> None:
    sql = revision_sql()

    assert "create function public.revert_entry" in sql
    assert "create function public.revert_section" in sql
    assert "content = source_snapshot.content_snapshot" in sql
    assert "'source_version', p_source_version" in sql
    assert "'new_version', reverted_entry.current_version" in sql
    assert "'new_version', reverted_section.current_version" in sql


def test_revert_rechecks_entry_owner_and_section_role() -> None:
    sql = revision_sql()

    assert "current_entry.author_id <> auth.uid()" in sql
    assert "Only the owning author can revert" in sql
    assert "array['staff']::public.clinic_role[]" in sql
    assert "array['clinician']::public.clinic_role[]" in sql
    assert "Role cannot revert this section" in sql


def test_revert_rpc_is_security_invoker_and_granted_only_to_authenticated() -> None:
    sql = revision_sql()

    assert sql.count("security invoker") == 3
    assert "revoke all on function public.revert_entry" in sql
    assert "grant execute on function public.revert_entry" in sql
    assert "grant execute on function public.revert_section" in sql
