from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MIGRATION = (
    REPOSITORY_ROOT / "supabase" / "migrations" / "202608270002_collaboration_provenance.sql"
)
LOCAL_SEED = REPOSITORY_ROOT / "supabase" / "seed.sql"
HOSTED_SEED = REPOSITORY_ROOT / "services" / "backend" / "scripts" / "seed_hosted.py"


def migration_sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_comment_threads_and_mentions_are_tenant_bound() -> None:
    sql = migration_sql()

    assert "foreign key (parent_comment_id, clinic_id, patient_id)" in sql
    assert "Reply must share its parent target" in sql
    assert "foreign key (comment_id, clinic_id, patient_id)" in sql
    assert "public.is_profile_in_clinic(new.mentioned_profile_id, new.clinic_id)" in sql
    assert "public.is_profile_in_clinic(new.assigned_to, new.clinic_id)" in sql


def test_highlight_provenance_uses_entry_version_and_exact_span() -> None:
    sql = migration_sql()

    assert "foreign key (source_entry_id, clinic_id, patient_id)" in sql
    assert "foreign key (source_version_id, clinic_id, patient_id, source_entry_id)" in sql
    assert "new.source_start_offset + 1" in sql
    assert "new.source_end_offset - new.source_start_offset" in sql
    assert ") <> new.quoted_text" in sql
    assert "Highlight quote does not match source span" in sql


def test_highlight_provenance_and_comment_identity_are_immutable() -> None:
    sql = migration_sql()

    assert "create trigger protect_highlight_provenance_before_update" in sql
    assert "Highlight provenance is immutable" in sql
    assert "new.parent_comment_id" in sql
    assert "Comment ownership and target are immutable" in sql


def test_collaboration_rls_keeps_admin_read_only() -> None:
    sql = migration_sql()

    mention_insert = sql[sql.index("create policy mentions_insert_clinical") :]
    mention_insert = mention_insert[: mention_insert.index("create type public.highlight_status")]
    highlight_insert = sql[sql.index("create policy highlights_insert_clinician") :]
    highlight_insert = highlight_insert[
        : highlight_insert.index("create policy highlights_update_clinician_review")
    ]
    highlight_update = sql[sql.index("create policy highlights_update_clinician_review") :]
    highlight_update = highlight_update[: highlight_update.index("alter table public.comments")]

    assert "'admin'" not in mention_insert
    assert "'admin'" not in highlight_insert
    assert "'admin'" not in highlight_update
    assert "array['staff', 'clinician', 'admin']" in sql


def test_collaboration_tables_are_realtime_and_not_patient_readable() -> None:
    sql = migration_sql()

    assert "array['comments', 'mentions', 'highlights']" in sql
    assert "alter table public.comments replica identity full" in sql
    assert "alter table public.mentions replica identity full" in sql
    assert "alter table public.highlights replica identity full" in sql
    assert "is_linked_patient" not in sql


def test_local_and_hosted_seed_cover_threads_mentions_and_review_states() -> None:
    local = LOCAL_SEED.read_text(encoding="utf-8")
    hosted = HOSTED_SEED.read_text(encoding="utf-8")

    for fixture_id in (
        "90000000-0000-0000-0000-000000000002",
        "91000000-0000-0000-0000-000000000001",
        "d0000000-0000-0000-0000-000000000001",
        "d0000000-0000-0000-0000-000000000002",
    ):
        assert fixture_id in local
        assert fixture_id in hosted

    assert "nocturnal cough persists" in local
    assert "nocturnal cough persists" in hosted
