import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.prioritization.importance import (
    MAX_PREFERENCE_WEIGHT,
    MIN_PREFERENCE_WEIGHT,
    FeedbackKind,
)

EMBEDDING_DIMENSIONS = 16
DEFAULT_HALF_LIFE_DAYS = 90.0
_DELTAS = {
    FeedbackKind.ACCEPT: 1.0,
    FeedbackKind.REJECT: -1.0,
    FeedbackKind.PIN: 1.5,
    FeedbackKind.EDIT: 0.5,
    FeedbackKind.COMMENT: 0.25,
}


def topic_embedding(topic: str) -> tuple[float, ...]:
    """Return a deterministic local embedding; no clinical text leaves the process."""

    normalized = " ".join(topic.casefold().split())
    if not normalized:
        raise ValueError("Topic must not be empty")
    vector = [0.0] * EMBEDDING_DIMENSIONS
    tokens = normalized.split()
    for token in tokens:
        digest = hashlib.blake2b(token.encode(), digest_size=16).digest()
        for index, byte in enumerate(digest):
            vector[index] += (byte - 127.5) / 127.5
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return tuple(value / magnitude for value in vector)


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("Embeddings must have equal non-zero dimensions")
    return sum(a * b for a, b in zip(left, right, strict=True))


def decayed_weight(
    weight: float,
    updated_at: datetime,
    *,
    now: datetime | None = None,
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
) -> float:
    if half_life_days <= 0:
        raise ValueError("Half-life must be positive")
    reference = now or datetime.now(UTC)
    age_days = max(0.0, (reference - updated_at).total_seconds() / 86400)
    return float(weight * (0.5 ** (age_days / half_life_days)))


@dataclass(frozen=True, slots=True)
class PersonalPreference:
    profile_id: UUID
    topic: str
    weight: float
    embedding: tuple[float, ...]
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PersonalFeedback:
    id: UUID
    profile_id: UUID
    topic: str
    kind: FeedbackKind
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class PersonalPreferenceState:
    preferences: tuple[PersonalPreference, ...] = ()
    applied_event_ids: frozenset[UUID] = frozenset()

    def similar_weight(
        self,
        profile_id: UUID,
        topic: str,
        *,
        now: datetime | None = None,
    ) -> float:
        target = topic_embedding(topic)
        contributions = []
        for preference in self.preferences:
            if preference.profile_id != profile_id:
                continue
            similarity = max(0.0, cosine_similarity(target, preference.embedding))
            contributions.append(
                similarity * decayed_weight(preference.weight, preference.updated_at, now=now)
            )
        return max(MIN_PREFERENCE_WEIGHT, min(MAX_PREFERENCE_WEIGHT, sum(contributions)))


def apply_personal_feedback(
    state: PersonalPreferenceState,
    events: list[PersonalFeedback] | tuple[PersonalFeedback, ...],
) -> PersonalPreferenceState:
    preferences = {(item.profile_id, item.topic): item for item in state.preferences}
    applied = set(state.applied_event_ids)
    for event in sorted(
        (item for item in events if item.id not in applied), key=lambda x: str(x.id)
    ):
        topic = " ".join(event.topic.casefold().split())
        key = (event.profile_id, topic)
        current = preferences.get(key)
        weight = (current.weight if current else 0.0) + _DELTAS[event.kind]
        preferences[key] = PersonalPreference(
            profile_id=event.profile_id,
            topic=topic,
            weight=max(MIN_PREFERENCE_WEIGHT, min(MAX_PREFERENCE_WEIGHT, weight)),
            embedding=topic_embedding(topic),
            updated_at=event.occurred_at,
        )
        applied.add(event.id)
    return PersonalPreferenceState(
        preferences=tuple(sorted(preferences.values(), key=lambda x: (str(x.profile_id), x.topic))),
        applied_event_ids=frozenset(applied),
    )
