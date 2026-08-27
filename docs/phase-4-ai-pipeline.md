# Phase 4 — AI Pipeline

The ordered implementation status, task-level acceptance criteria, estimates,
and handoff evidence are maintained in [the Phase 4 task breakdown](phase-4/README.md).

**Full-quality estimate:** 7-9 hours  
**16-hour critical-path allocation:** 3.5 hours  
**Goal:** Add AI-generated summaries and highlight suggestions without bypassing privacy, provenance, or human review.

## Description

The AI pipeline creates a genuine LLM-generated consult summary, clearly labelled system-authored entries, and suggested highlights. It is not allowed to silently rewrite the clinical record or send prohibited identifiers to an LLM. Use durable jobs, structured output, exact provenance, transparent scoring, and fast clinician accept/reject controls.

## Required deliverables

- Deterministic PHI-redaction module before every LLM request.
- Redaction verification and safe logging policy.
- Durable Postgres-backed `jobs` table and Python worker.
- Idempotent AI-scribe job lifecycle with retry state.
- Structured LLM output validated with Pydantic.
- One genuine end-to-end doctor-patient LLM-generated AI-scribe flow; the same typed ingestion contract supports nurse-patient and AI-patient sessions.
- Distinct AI-scribed timeline entries for doctor consults, nurse consults, and AI-patient sessions.
- Provenance from AI output to its sanitized source session or source entry.
- Suggested highlight creation with short risk reason.
- Clinician accept/reject interaction.
- Explainable importance scoring.
- Lightweight adaptive preference weights and a passing `test_self_learning_importance.py`.

## Optional deliverables

- Realtime completion status.
- Source-file storage and synthetic audio workflow.
- Actual transcription or voice capture.
- Embedding-based clustering or semantic retrieval.

## Implementation order

1. **Implement redaction first.** Redact names, IDs, phone numbers, email addresses, dates of birth, and addresses where present; test it independently.
2. **Create job storage and worker.** Implement job claiming, retry count, failures, and idempotency before calling a model.
3. **Define the structured contract.** Specify Pydantic models for summary, extracted facts, proposed highlights, risk reason, exact quoted source text, and source pointers.
4. **Integrate one LLM provider.** Send only redacted text, perform one genuine doctor-patient end-to-end generation flow, and reject invalid model output. Exercise the nurse-patient and AI-patient types with deterministic fixtures through the same ingestion contract.
5. **Persist AI entries.** Mark them with `author_role = system`, the exact required interaction type, and a resolvable `source_record_id`; ensure patient visibility is restricted.
6. **Generate highlight suggestions.** Deterministically map every accepted model quote to an exact source entry, historical version, and source span. Reject a suggestion if exact mapping fails.
7. **Implement review controls.** A clinician can accept or reject a suggestion in one or two interactions.
8. **Add transparent adaptive ranking.** Rank by risk, unresolved tasks, recency, clinical entities, clinician confirmation, and feedback. Update small deterministic preference weights from accepts, rejects, pins, edits, and comments.
9. **Test idempotency, redaction, exact provenance, and learning behavior.**

## Acceptance criteria

- [ ] Raw clinical text is not sent to the LLM before redaction succeeds.
- [ ] Redaction tests cover names, identity numbers, phone numbers, and email addresses.
- [ ] Raw request bodies and secrets do not appear in application logs.
- [ ] A submitted source creates one durable job with visible status.
- [ ] Retrying a job does not create duplicate AI entries or highlights.
- [ ] The worker stores a valid AI-scribed entry only after structured output validation.
- [ ] At least one demo flow invokes a genuine LLM and persists its validated structured result.
- [ ] Every AI entry is visibly system-authored and typed correctly.
- [ ] Every AI entry points to its originating interaction/source record.
- [ ] Every AI-derived highlight carries an exact source entry, historical version, source span, quoted-text match, and short risk reason.
- [ ] An AI suggestion without exact source resolution is rejected and never appears in the Glance View.
- [ ] A clinician can accept or reject each highlight quickly.
- [ ] Accepted clinician information outranks conflicting AI information; unresolved conflicts are flagged.
- [ ] Ranking factors are inspectable in the UI or API response.
- [ ] Learned weight adjustments are deterministic, explainable, bounded, and resettable.
- [ ] High-risk safety floors cannot be reduced by interaction feedback.
- [ ] `test_redaction.py`, `test_job_idempotency.py`, and `test_self_learning_importance.py` pass.

## What "self-learning" means here

This is not reinforcement learning. The system does not train a model, explore clinical actions, or optimize an opaque reward. It records explicit interaction events and applies a bounded online weight update to similar future topics. Clinical risk rules remain deterministic, visible, and dominant.

## Time budget

| Work item | Estimate |
|---|---:|
| Redaction and tests | 1-2 h |
| Job table, worker, and retries | 1-2 h |
| Structured LLM integration | 1-2 h |
| AI entry and exact highlight persistence | 1-2 h |
| Review UI and adaptive ranking | 2 h |

## Do not proceed until

The system visibly distinguishes AI suggestions from confirmed clinical content and every AI-derived result can be traced back to its source.
