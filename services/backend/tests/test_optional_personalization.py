from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from app.domain.prioritization import (
    FeedbackKind,
    PersonalFeedback,
    PersonalPreferenceState,
    apply_personal_feedback,
    decayed_weight,
    topic_embedding,
)

PROFILE_A = UUID("20000000-0000-0000-0000-000000000002")
PROFILE_B = UUID("20000000-0000-0000-0000-000000000003")


def test_personal_feedback_is_isolated_and_embedding_similarity_is_applied() -> None:
    occurred_at = datetime(2026, 8, 28, tzinfo=UTC)
    state = apply_personal_feedback(
        PersonalPreferenceState(),
        [
            PersonalFeedback(
                id=UUID("10000000-0000-0000-0000-000000000001"),
                profile_id=PROFILE_A,
                topic="nocturnal cough",
                kind=FeedbackKind.PIN,
                occurred_at=occurred_at,
            )
        ],
    )
    assert state.similar_weight(PROFILE_A, "nocturnal cough", now=occurred_at) > 0
    assert state.similar_weight(PROFILE_B, "nocturnal cough", now=occurred_at) == 0
    assert len(topic_embedding("nocturnal cough")) == 16


def test_preference_weight_has_documented_half_life() -> None:
    updated = datetime(2026, 1, 1, tzinfo=UTC)
    assert decayed_weight(8, updated, now=updated + timedelta(days=90)) == pytest.approx(4)
