import unicodedata
from dataclasses import dataclass
from typing import Any

from app.domain.scribe.contracts import ScribeInteractionType, ScribeOutput


@dataclass(frozen=True, slots=True)
class PreparedScribePersistence:
    content: str
    highlights: tuple[dict[str, Any], ...]


_ENTRY_LABELS = {
    ScribeInteractionType.DOCTOR_CONSULT: "AI-scribed doctor consult",
    ScribeInteractionType.NURSE_CONSULT: "AI-scribed nurse consult",
    ScribeInteractionType.AI_PATIENT_SESSION: "AI-patient session summary",
}


def prepare_scribe_persistence(output: ScribeOutput) -> PreparedScribePersistence:
    """Render one immutable entry and exact highlight offsets from validated output."""

    content = unicodedata.normalize(
        "NFC", f"{_ENTRY_LABELS[output.interaction_type]}\n\n{output.summary}"
    )
    prepared: list[dict[str, Any]] = []
    if output.highlights:
        content += "\n\nSupporting excerpts"

    for index, highlight in enumerate(output.highlights, start=1):
        quote = unicodedata.normalize("NFC", highlight.quoted_text)
        prefix = f"\n{index}. "
        start = len(content) + len(prefix)
        content += prefix + quote
        prepared.append(
            {
                "source_start_offset": start,
                "source_end_offset": start + len(quote),
                "quoted_text": quote,
                "normalized_claim": unicodedata.normalize("NFC", highlight.normalized_claim),
                "risk_level": highlight.risk_level.value,
                "risk_reason": unicodedata.normalize("NFC", highlight.risk_reason),
                "score": highlight.score,
            }
        )

    return PreparedScribePersistence(content=content, highlights=tuple(prepared))
