from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

BoundedText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ScribeInteractionType(StrEnum):
    DOCTOR_CONSULT = "doctor_consult"
    NURSE_CONSULT = "nurse_consult"
    AI_PATIENT_SESSION = "ai_patient_session"


class ScribeRiskLevel(StrEnum):
    INFORMATION = "information"
    ATTENTION = "attention"
    CRITICAL = "critical"


class _StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ExtractedFact(_StrictContract):
    category: Literal["symptom", "medication", "plan", "risk", "patient_context"]
    claim: BoundedText = Field(max_length=500)
    source_quote: BoundedText = Field(max_length=1_000)


class ProposedAction(_StrictContract):
    title: BoundedText = Field(max_length=300)
    owner_role: Literal["staff", "clinician"] | None = None
    urgency: Literal["low", "normal", "high", "urgent"] = "normal"
    source_quote: BoundedText = Field(max_length=1_000)


class ProposedHighlight(_StrictContract):
    quoted_text: BoundedText = Field(max_length=1_000)
    normalized_claim: BoundedText = Field(max_length=1_000)
    risk_level: ScribeRiskLevel = Field(strict=False)
    risk_reason: BoundedText = Field(max_length=500)
    score: float = Field(ge=0, le=100)
    occurrence_hint: int | None = Field(default=None, ge=0)


class ScribeOutput(_StrictContract):
    schema_version: Literal["1.0"]
    interaction_type: ScribeInteractionType = Field(strict=False)
    summary: BoundedText = Field(max_length=4_000)
    facts: list[ExtractedFact] = Field(default_factory=list, max_length=20)
    open_questions: list[BoundedText] = Field(default_factory=list, max_length=10)
    actions: list[ProposedAction] = Field(default_factory=list, max_length=10)
    highlights: list[ProposedHighlight] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def reject_duplicates(self) -> Self:
        fact_keys = [(fact.category, fact.claim.casefold()) for fact in self.facts]
        if len(fact_keys) != len(set(fact_keys)):
            raise ValueError("Duplicate extracted facts are not allowed")

        highlight_keys = [
            (highlight.quoted_text.casefold(), highlight.normalized_claim.casefold())
            for highlight in self.highlights
        ]
        if len(highlight_keys) != len(set(highlight_keys)):
            raise ValueError("Duplicate proposed highlights are not allowed")
        return self
