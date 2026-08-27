from pathlib import Path

import pytest
from pglast import parse_sql

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_DIRECTORY = REPOSITORY_ROOT / "supabase" / "migrations"


@pytest.mark.parametrize(
    "sql_file",
    sorted(MIGRATION_DIRECTORY.glob("*.sql")) + [REPOSITORY_ROOT / "supabase" / "seed.sql"],
    ids=lambda path: path.name,
)
def test_sql_file_parses(sql_file: Path) -> None:
    statements = parse_sql(sql_file.read_text(encoding="utf-8"))

    assert statements, f"{sql_file.name} contains no SQL statements"
