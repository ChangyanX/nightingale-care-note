from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MIGRATION = REPOSITORY_ROOT / "supabase" / "migrations" / "202608270001_care_tasks_and_realtime.sql"
LOCAL_SEED = REPOSITORY_ROOT / "supabase" / "seed.sql"
HOSTED_SEED = REPOSITORY_ROOT / "services" / "backend" / "scripts" / "seed_hosted.py"


def migration_sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_care_tasks_enable_rls_and_have_no_admin_write_policy() -> None:
    sql = migration_sql()

    assert "alter table public.care_tasks enable row level security;" in sql
    assert "create policy care_tasks_select_clinical" in sql
    assert "create policy care_tasks_insert_clinical" in sql
    assert "create policy care_tasks_update_clinical" in sql

    insert_policy = sql[sql.index("create policy care_tasks_insert_clinical") :]
    insert_policy = insert_policy[: insert_policy.index("create policy care_tasks_update_clinical")]
    update_policy = sql[sql.index("create policy care_tasks_update_clinical") :]
    update_policy = update_policy[: update_policy.index("create function public.protect")]

    assert "'admin'" not in insert_policy
    assert "'admin'" not in update_policy


def test_task_tenancy_and_identity_are_database_enforced() -> None:
    sql = migration_sql()

    assert "foreign key (patient_id, clinic_id)" in sql
    assert "foreign key (source_entry_id, clinic_id, patient_id)" in sql
    assert "create trigger protect_care_task_identity_before_update" in sql
    assert "public.is_profile_in_clinic(assigned_to, clinic_id)" in sql


def test_entries_and_tasks_are_migration_managed_realtime_tables() -> None:
    sql = migration_sql()

    assert "alter table public.entries replica identity full;" in sql
    assert "alter table public.care_tasks replica identity full;" in sql
    assert "add table public.entries" in sql
    assert "add table public.care_tasks" in sql


def test_local_and_hosted_seed_paths_include_same_task_fixtures() -> None:
    local = LOCAL_SEED.read_text(encoding="utf-8")
    hosted = HOSTED_SEED.read_text(encoding="utf-8")

    for task_id in (
        "b0000000-0000-0000-0000-000000000001",
        "b0000000-0000-0000-0000-000000000002",
    ):
        assert task_id in local
        assert task_id in hosted

    assert "Review seven-day peak-flow diary" in local
    assert "Review seven-day peak-flow diary" in hosted
