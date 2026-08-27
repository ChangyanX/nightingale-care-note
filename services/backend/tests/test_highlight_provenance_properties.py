import unicodedata
from uuid import UUID

from hypothesis import given
from hypothesis import strategies as st

from app.domain.provenance import HistoricalEntrySource, resolve_highlight_source


@given(
    prefix=st.text(min_size=0, max_size=40),
    quote=st.text(min_size=1, max_size=30).filter(lambda value: bool(value.strip())),
    suffix=st.text(min_size=0, max_size=40),
)
def test_unicode_codepoint_spans_round_trip(prefix: str, quote: str, suffix: str) -> None:
    normalized_quote = unicodedata.normalize("NFC", quote)
    source = HistoricalEntrySource(
        entry_id=UUID("70000000-0000-0000-0000-000000000001"),
        version_id=UUID("c0000000-0000-0000-0000-000000000001"),
        entry_type="staff_note",
        content_snapshot=prefix + quote + suffix,
    )
    pointer = resolve_highlight_source(source, quote, occurrence_hint=0)
    normalized_content = unicodedata.normalize("NFC", source.content_snapshot)
    assert (
        normalized_content[pointer.source_start_offset : pointer.source_end_offset]
        == normalized_quote
    )
