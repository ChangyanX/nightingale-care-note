from dataclasses import dataclass

from app.domain.scribe.contracts import ScribeOutput


@dataclass(frozen=True, slots=True)
class PatientSummaryProposal:
    content: str
    source_summary: str
    requires_clinician_review: bool = True


def propose_patient_summary(output: ScribeOutput) -> PatientSummaryProposal:
    """Create a bounded draft; it remains invisible until clinician review."""

    sentences = [output.summary.strip()]
    if output.actions:
        action_titles = "; ".join(action.title for action in output.actions[:3])
        sentences.append(f"Next steps discussed: {action_titles}.")
    content = " ".join(sentences)
    if len(content) > 2_000:
        content = content[:1_999].rstrip() + "…"
    return PatientSummaryProposal(content=content, source_summary=output.summary)
