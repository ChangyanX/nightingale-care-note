import unicodedata
from dataclasses import dataclass
from uuid import UUID


class ProvenanceError(ValueError):
    """Exact-source resolution failure that never echoes clinical text."""


@dataclass(frozen=True, slots=True)
class HistoricalEntrySource:
    entry_id: UUID
    version_id: UUID
    entry_type: str
    content_snapshot: str


@dataclass(frozen=True, slots=True)
class HighlightSourcePointer:
    source_entry_id: UUID
    source_version_id: UUID
    source_entry_type: str
    source_start_offset: int
    source_end_offset: int
    quoted_text: str


def _occurrences(content: str, quote: str) -> list[int]:
    starts: list[int] = []
    search_from = 0
    while True:
        found = content.find(quote, search_from)
        if found < 0:
            return starts
        starts.append(found)
        search_from = found + 1


def resolve_highlight_source(
    source: HistoricalEntrySource,
    quoted_text: str,
    *,
    occurrence_hint: int = -1,
) -> HighlightSourcePointer:
    """Resolve a quote against an NFC historical snapshot using code-point offsets."""

    content = unicodedata.normalize("NFC", source.content_snapshot)
    quote = unicodedata.normalize("NFC", quoted_text)
    if not quote:
        raise ProvenanceError("Highlight quote must not be empty")
    if occurrence_hint < -1:
        raise ProvenanceError("Highlight occurrence hint is invalid")

    starts = _occurrences(content, quote)
    if not starts:
        raise ProvenanceError("Highlight quote is not present in the source version")
    if occurrence_hint == -1:
        if len(starts) != 1:
            raise ProvenanceError("Highlight quote is ambiguous in the source version")
        selected_start = starts[0]
    else:
        if occurrence_hint >= len(starts):
            raise ProvenanceError("Highlight occurrence hint is out of range")
        selected_start = starts[occurrence_hint]

    return HighlightSourcePointer(
        source_entry_id=source.entry_id,
        source_version_id=source.version_id,
        source_entry_type=source.entry_type,
        source_start_offset=selected_start,
        source_end_offset=selected_start + len(quote),
        quoted_text=quote,
    )
