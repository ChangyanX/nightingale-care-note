from uuid import UUID

from app.domain.prioritization import (
    FeedbackEvent,
    FeedbackKind,
    ImportanceCandidate,
    PreferenceState,
    apply_feedback,
    rank_importance,
    reset_preferences,
)


def event(number: int, kind: FeedbackKind, topic: str = "nocturnal cough") -> FeedbackEvent:
    return FeedbackEvent(
        id=UUID(f"e0000000-0000-0000-0000-{number:012d}"),
        topic=topic,
        kind=kind,
    )


def candidate(**overrides: object) -> ImportanceCandidate:
    values: dict[str, object] = {
        "topic": "Nocturnal Cough",
        "risk_level": "attention",
        "age_hours": 24.0,
        "has_unresolved_task": False,
        "clinical_entity_count": 1,
        "clinician_confirmed": False,
        "has_conflict": False,
    }
    values.update(overrides)
    return ImportanceCandidate(**values)  # type: ignore[arg-type]


def test_acceptance_increases_similar_future_topic_priority() -> None:
    before = rank_importance(candidate(), PreferenceState())
    learned = apply_feedback(PreferenceState(), [event(1, FeedbackKind.ACCEPT)])
    after = rank_importance(candidate(topic="  nocturnal   cough "), learned)

    assert after.score == before.score + 1.0
    assert after.factor_map()["feedback"] == 1.0


def test_event_replay_is_idempotent() -> None:
    accepted = event(1, FeedbackKind.ACCEPT)
    once = apply_feedback(PreferenceState(), [accepted])
    replayed = apply_feedback(once, [accepted, accepted])

    assert replayed == once
    assert replayed.weight_for("nocturnal cough") == 1.0


def test_feedback_weights_are_bounded_and_deterministic() -> None:
    accepts = [event(number, FeedbackKind.PIN) for number in range(1, 30)]
    rejects = [event(number + 100, FeedbackKind.REJECT) for number in range(1, 50)]

    positive = apply_feedback(PreferenceState(), accepts)
    negative = apply_feedback(positive, rejects)

    assert positive.weight_for("nocturnal cough") == 10.0
    assert negative.weight_for("nocturnal cough") == -10.0
    assert apply_feedback(PreferenceState(), list(reversed(accepts))) == positive


def test_critical_safety_floor_cannot_be_reduced_by_rejections() -> None:
    rejected = apply_feedback(
        PreferenceState(),
        [event(number, FeedbackKind.REJECT) for number in range(1, 30)],
    )

    result = rank_importance(candidate(risk_level="critical"), rejected)

    assert result.score >= 90.0
    assert result.safety_floor == 90.0
    assert result.factor_map()["feedback"] == -10.0


def test_clinician_confirmed_information_outranks_conflicting_unreviewed_ai() -> None:
    state = apply_feedback(PreferenceState(), [event(1, FeedbackKind.ACCEPT)])
    clinician = rank_importance(
        candidate(risk_level="information", clinician_confirmed=True),
        state,
    )
    unreviewed_ai = rank_importance(
        candidate(risk_level="attention", has_conflict=True),
        state,
    )

    assert clinician.score > unreviewed_ai.score
    assert clinician.safety_floor == 80.0
    assert unreviewed_ai.factor_map()["unresolved_conflict"] == 8.0


def test_reset_restores_documented_defaults() -> None:
    learned = apply_feedback(PreferenceState(), [event(1, FeedbackKind.PIN)])

    reset = reset_preferences()

    assert learned.weight_for("nocturnal cough") > 0
    assert reset == PreferenceState()
    assert reset.weight_for("nocturnal cough") == 0.0


def test_factor_contributions_and_reason_are_inspectable() -> None:
    result = rank_importance(
        candidate(has_unresolved_task=True, clinical_entity_count=3),
        PreferenceState(),
    )

    assert result.factor_map() == {
        "risk": 40.0,
        "unresolved_task": 15.0,
        "recency": 9.0,
        "clinical_entities": 6.0,
        "clinician_confirmation": 0.0,
        "unresolved_conflict": 0.0,
        "feedback": 0.0,
    }
    assert "risk" in result.reason
    assert "unresolved_task" in result.reason
