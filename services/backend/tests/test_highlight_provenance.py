from pathlib import Path
from uuid import UUID

import pytest

from app.domain.provenance import (
    HistoricalEntrySource,
    ProvenanceError,
    resolve_highlight_source,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MIGRATION = REPOSITORY_ROOT / "supabase/migrations/202608270002_collaboration_provenance.sql"
SEED = REPOSITORY_ROOT / "supabase/seed.sql"


@pytest.mark.parametrize(
    ("entry_type", "content", "quote"),
    [
        (
            "clinician_note",
            "Clinician confirmed that 夜间咳嗽 requires follow-up.",
            "夜间咳嗽 requires follow-up",
        ),
        (
            "ai_doctor_consult_summary",
            "Doctor consult summary: nocturnal cough persists; review agreed.",
            "nocturnal cough persists",
        ),
    ],
)
def test_manual_and_ai_scribed_highlights_resolve_exact_historical_span(
    entry_type: str,
    content: str,
    quote: str,
) -> None:
    source = HistoricalEntrySource(
        entry_id=UUID("70000000-0000-0000-0000-000000000003"),
        version_id=UUID("c0000000-0000-0000-0000-000000000003"),
        entry_type=entry_type,
        content_snapshot=content,
    )

    pointer = resolve_highlight_source(source, quote)

    assert pointer.source_entry_id == source.entry_id
    assert pointer.source_version_id == source.version_id
    assert pointer.source_entry_type == entry_type
    assert content[pointer.source_start_offset : pointer.source_end_offset] == quote


def test_unicode_offsets_are_zero_based_half_open_over_nfc_content() -> None:
    decomposed_content = "Cafe\u0301 trigger followed by 夜间咳嗽."
    normalized_content = "Café trigger followed by 夜间咳嗽."
    source = HistoricalEntrySource(
        entry_id=UUID("70000000-0000-0000-0000-000000000007"),
        version_id=UUID("c0000000-0000-0000-0000-000000000007"),
        entry_type="patient_insight",
        content_snapshot=decomposed_content,
    )

    pointer = resolve_highlight_source(source, "夜间咳嗽")

    assert normalized_content[pointer.source_start_offset : pointer.source_end_offset] == "夜间咳嗽"


def test_ambiguous_quote_requires_occurrence_hint() -> None:
    content = "cough improved, then cough returned"
    source = HistoricalEntrySource(
        entry_id=UUID("70000000-0000-0000-0000-000000000002"),
        version_id=UUID("c0000000-0000-0000-0000-000000000002"),
        entry_type="clinician_note",
        content_snapshot=content,
    )

    with pytest.raises(ProvenanceError, match="ambiguous"):
        resolve_highlight_source(source, "cough")

    pointer = resolve_highlight_source(source, "cough", occurrence_hint=1)
    assert content[pointer.source_start_offset : pointer.source_end_offset] == "cough"
    assert pointer.source_start_offset == content.rindex("cough")


@pytest.mark.parametrize(
    ("quote", "hint", "message"),
    [
        ("", -1, "must not be empty"),
        ("missing phrase", -1, "not present"),
        ("cough", -2, "invalid"),
        ("cough", 4, "out of range"),
    ],
)
def test_invalid_exact_source_resolution_fails_closed(
    quote: str,
    hint: int,
    message: str,
) -> None:
    source = HistoricalEntrySource(
        entry_id=UUID("70000000-0000-0000-0000-000000000003"),
        version_id=UUID("c0000000-0000-0000-0000-000000000003"),
        entry_type="ai_doctor_consult_summary",
        content_snapshot="cough occurred once",
    )

    with pytest.raises(ProvenanceError, match=message):
        resolve_highlight_source(source, quote, occurrence_hint=hint)


def test_database_pointer_is_tenant_bound_immutable_and_quote_validated() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "foreign key (source_version_id, clinic_id, patient_id, source_entry_id)" in sql
    assert "create trigger validate_highlight_provenance_before_write" in sql
    assert "create trigger protect_highlight_provenance_before_update" in sql
    assert "Highlight quote does not match source span" in sql


def test_seeded_ai_highlight_points_to_ai_scribed_historical_version() -> None:
    seed = SEED.read_text(encoding="utf-8")

    assert "'70000000-0000-0000-0000-000000000003'::uuid" in seed
    assert "'nocturnal cough persists'" in seed
    assert "'ai'::public.highlight_generator" in seed
    assert "join public.entry_versions version" in seed
    assert "version.version_number = 1" in seed
