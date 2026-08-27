from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ENTRY_RPCS = REPOSITORY_ROOT / "supabase" / "migrations" / "202608260002_entry_rpcs.sql"
REVISION_RPCS = REPOSITORY_ROOT / "supabase" / "migrations" / "202608270003_revision_revert.sql"


def mutation_sql() -> str:
    return ENTRY_RPCS.read_text(encoding="utf-8") + REVISION_RPCS.read_text(encoding="utf-8")


def test_mutations_lock_only_the_target_resource() -> None:
    sql = mutation_sql()

    assert sql.count("for update;") >= 4
    assert "where id = p_entry_id\n  for update;" in sql
    assert "where id = p_section_id\n  for update;" in sql


def test_stale_writes_raise_deterministic_serialization_conflict() -> None:
    sql = mutation_sql()

    assert sql.count("current_version <> p_expected_version") >= 4
    assert sql.count("errcode = '40001'") >= 4
    assert "Entry version conflict" in sql
    assert "Section version conflict" in sql


def test_successful_mutations_increment_once_inside_the_locked_transaction() -> None:
    sql = mutation_sql()

    assert sql.count("current_version = current_version + 1") >= 4
    assert "insert into public.entry_versions" in sql
    assert "insert into public.section_versions" in sql
