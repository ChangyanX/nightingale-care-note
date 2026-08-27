# P4-T03 — Structured Scribe Contract

**Status:** Implemented locally  
**Full estimate:** 1 hour  
**16-hour path:** 25 minutes  
**Dependencies:** P4-T01

## Objective

Define the only model-output shape accepted by the worker for doctor, nurse,
and AI-patient interactions.

## Required work, in order

1. Define strict Pydantic models for summary, extracted facts, open questions,
   actions, and proposed highlights.
2. Require interaction type and schema version.
3. Bound list counts and every text field.
4. Require highlight quote, normalized claim, risk level, risk reason, and score.
5. Reject unknown fields, invalid enums, empty claims, duplicate facts, and out-of-range scores.
6. Define a provider-neutral JSON schema and deterministic fixtures for all three interaction types.
7. Add validation and serialization tests.

## Must be done

- The model cannot choose clinic, patient, author, visibility, entry IDs, or review status.
- Model-provided offsets are treated as hints; server-side exact mapping is authoritative.
- Output is not persisted until the full object validates.
- Doctor, nurse, and AI-patient outputs share one versioned contract.

## Optional

- Medication-specific structured submodels.
- Model confidence separate from application importance score.
- Multilingual source-language metadata.

## Acceptance criteria

- [x] Valid fixtures for all interaction types parse identically.
- [x] Unknown fields and oversized content are rejected.
- [x] Invalid risk level or score is rejected.
- [ ] The JSON schema can be supplied to the chosen provider's structured-output feature.
- [x] No output field can grant authorization or mark a suggestion accepted.

## Done when

The worker can treat provider output as untrusted JSON and accept it only through
one strict, versioned application contract.
