from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from uuid import UUID

MIN_PREFERENCE_WEIGHT = -10.0
MAX_PREFERENCE_WEIGHT = 10.0
CRITICAL_SAFETY_FLOOR = 90.0
CLINICIAN_CONFIRMED_FLOOR = 80.0


class FeedbackKind(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    PIN = "pin"
    EDIT = "edit"
    COMMENT = "comment"


_FEEDBACK_DELTAS = {
    FeedbackKind.ACCEPT: 1.0,
    FeedbackKind.REJECT: -1.0,
    FeedbackKind.PIN: 1.5,
    FeedbackKind.EDIT: 0.5,
    FeedbackKind.COMMENT: 0.25,
}


@dataclass(frozen=True, slots=True)
class FeedbackEvent:
    id: UUID
    topic: str
    kind: FeedbackKind


@dataclass(frozen=True, slots=True)
class PreferenceState:
    topic_weights: tuple[tuple[str, float], ...] = ()
    applied_event_ids: frozenset[UUID] = frozenset()

    def weight_for(self, topic: str) -> float:
        normalized_topic = _normalize_topic(topic)
        return dict(self.topic_weights).get(normalized_topic, 0.0)


@dataclass(frozen=True, slots=True)
class ImportanceCandidate:
    topic: str
    risk_level: Literal["information", "attention", "critical"]
    age_hours: float
    has_unresolved_task: bool = False
    clinical_entity_count: int = 0
    clinician_confirmed: bool = False
    has_conflict: bool = False


@dataclass(frozen=True, slots=True)
class ImportanceScore:
    score: float
    factors: tuple[tuple[str, float], ...]
    safety_floor: float
    reason: str

    def factor_map(self) -> dict[str, float]:
        return dict(self.factors)


def _normalize_topic(topic: str) -> str:
    normalized = " ".join(topic.casefold().split())
    if not normalized:
        raise ValueError("Importance topic must not be empty")
    return normalized


def _bounded_weight(value: float) -> float:
    return max(MIN_PREFERENCE_WEIGHT, min(MAX_PREFERENCE_WEIGHT, value))


def apply_feedback(
    state: PreferenceState,
    events: list[FeedbackEvent] | tuple[FeedbackEvent, ...],
) -> PreferenceState:
    weights = dict(state.topic_weights)
    applied_ids = set(state.applied_event_ids)
    new_events = sorted(
        (event for event in events if event.id not in applied_ids),
        key=lambda event: str(event.id),
    )
    for event in new_events:
        topic = _normalize_topic(event.topic)
        weights[topic] = _bounded_weight(weights.get(topic, 0.0) + _FEEDBACK_DELTAS[event.kind])
        applied_ids.add(event.id)
    return PreferenceState(
        topic_weights=tuple(sorted(weights.items())),
        applied_event_ids=frozenset(applied_ids),
    )


def reset_preferences() -> PreferenceState:
    return PreferenceState()


def rank_importance(
    candidate: ImportanceCandidate,
    state: PreferenceState,
) -> ImportanceScore:
    if candidate.age_hours < 0 or candidate.clinical_entity_count < 0:
        raise ValueError("Importance inputs must not be negative")

    risk_score = {"information": 10.0, "attention": 40.0, "critical": 80.0}[candidate.risk_level]
    factors = {
        "risk": risk_score,
        "unresolved_task": 15.0 if candidate.has_unresolved_task else 0.0,
        "recency": max(0.0, 10.0 - candidate.age_hours / 24.0),
        "clinical_entities": min(10.0, candidate.clinical_entity_count * 2.0),
        "clinician_confirmation": 20.0 if candidate.clinician_confirmed else 0.0,
        "unresolved_conflict": 8.0 if candidate.has_conflict else 0.0,
        "feedback": state.weight_for(candidate.topic),
    }
    safety_floor = 0.0
    if candidate.risk_level == "critical":
        safety_floor = CRITICAL_SAFETY_FLOOR
    if candidate.clinician_confirmed:
        safety_floor = max(safety_floor, CLINICIAN_CONFIRMED_FLOOR)
    score = max(safety_floor, min(100.0, sum(factors.values())))

    active_factors = [name for name, value in factors.items() if value > 0]
    reason = "Priority reflects " + ", ".join(active_factors[:3])
    if safety_floor:
        reason += " and a deterministic safety floor"
    return ImportanceScore(
        score=round(score, 3),
        factors=tuple(factors.items()),
        safety_floor=safety_floor,
        reason=reason,
    )
