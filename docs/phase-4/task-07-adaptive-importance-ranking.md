# P4-T07 — Adaptive Importance Ranking

**Status:** Implemented end-to-end locally; hosted walkthrough pending
**Full estimate:** 1.25 hours  
**16-hour path:** 35 minutes  
**Dependencies:** P4-T06

## Objective

Add transparent, bounded preference adjustments from explicit review behavior
without training a model or allowing feedback to reduce safety-critical ranking.

## Required work, in order

1. Define inspectable base factors: risk, unresolved task, recency, clinical
   entities, clinician confirmation, conflict, and feedback.
2. Define interaction events for accept, reject, pin, edit, and comment.
3. Store per-clinic/topic preference weights with bounded min/max values.
4. Apply deterministic update deltas and idempotent event processing.
5. Define non-negotiable safety floors for critical and clinician-confirmed items.
6. Add a reset operation and record weight-version metadata.
7. Return factor contributions and a short importance reason from ranking.
8. Add learning, reset, idempotency, and safety-floor tests.

## Must be done

- No model training, exploration, hidden reward, or clinical-action optimization.
- The same state and events always produce the same ranking.
- Replaying an event does not update a weight twice.
- Learned values remain bounded and cannot demote a critical safety item below its floor.
- Clinician-confirmed information outranks conflicting unreviewed AI suggestions.

## Optional

- Per-user rather than clinic-level preferences.
- Similarity learned from embeddings.
- Time-decay of preference weights.

## Acceptance criteria

- [x] Accepting a topic modestly increases similar future ranking.
- [x] Rejecting reduces only the bounded feedback component.
- [x] Critical safety and clinician-confirmed floors remain intact.
- [x] Reset restores documented defaults.
- [x] Factor contributions are inspectable; authenticated per-user feedback persistence, reset, and UI controls are exposed.
- [x] `test_self_learning_importance.py` passes.

## Done when

The bonus behavior is credibly “self-learning” while remaining deterministic,
explainable, bounded, resettable, and subordinate to clinical safety rules.
