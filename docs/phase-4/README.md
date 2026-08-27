# Phase 4 Task Breakdown — AI Pipeline

Phase 4 adds one genuine AI-scribe path without allowing model output to bypass
redaction, validation, provenance, authorization, or human review. The worker is
a separate process in the existing Python backend, not a new microservice.

| ID | Task | Status | Full estimate | 16-hour path | Depends on | Exit evidence |
|---|---|---|---:|---:|---|---|
| [P4-T01](task-01-redaction-and-safe-logging.md) | Redaction and safe logging | Implemented locally | 1.25 h | 30 min | Backend foundation | Deterministic redaction and residual-PHI rejection |
| [P4-T02](task-02-durable-job-schema-and-api.md) | Durable job schema and API | Submission/claim implemented; hosted concurrency pending | 1.25 h | 30 min | T01, Phase 1 RLS | Idempotent submission and caller-visible status |
| [P4-T03](task-03-structured-scribe-contract.md) | Structured scribe contract | Implemented locally | 1 h | 25 min | T01 | Strict summary/fact/highlight validation |
| [P4-T04](task-04-provider-gateway-and-worker.md) | Provider gateway and worker | Pending | 1.5 h | 45 min | T02-T03 | Redacted genuine invocation with retry-safe worker |
| [P4-T05](task-05-ai-entry-and-provenance-persistence.md) | AI entry and provenance persistence | Pending | 1 h | 30 min | T03-T04, Phase 3 schema | Atomic system entry and exact source linkage |
| [P4-T06](task-06-highlight-review-and-explainability.md) | Highlight review and explainability | Pending | 1 h | 25 min | T05, Phase 3 highlights | Exact suggestions with fast clinician review |
| [P4-T07](task-07-adaptive-importance-ranking.md) | Adaptive importance ranking | Pending | 1.25 h | 35 min | T06 | Bounded, resettable feedback weights and safety floor |
| [P4-T08](task-08-required-tests-and-handoff.md) | Required tests and handoff | Pending | 1 h | 10 min | T01-T07 | Genuine-run, idempotency, provenance, and learning evidence |

**Full Phase 4 estimate:** approximately 8-9 hours  
**Critical-path allocation:** 3.5 hours

## Phase rules

- Redaction succeeds before any provider request is constructed or sent.
- No raw transcript, prompt, response body, secret, or clinical content is logged.
- Only synthetic demo data is used; this is not a production PHI processor.
- The API submits durable jobs; it never waits synchronously for model generation.
- The service-role key is worker-only and never enters browser or ordinary API flows.
- Structured output is rejected unless its type, lengths, source quote, and enums validate.
- AI entries are system-authored, visibly AI-labelled, and linked to their source record.
- A highlight is discarded unless its quote resolves exactly to an immutable source version.
- Suggested highlights cannot affect confirmed care state until a clinician reviews them.
- Adaptive ranking is bounded arithmetic over explicit feedback, not reinforcement learning.
- Deterministic clinical safety floors always dominate learned preference adjustments.

## Recommended execution order

Complete T01-T03 before wiring a live provider. T02 and T03 may proceed in
parallel conceptually, but both must be complete before T04. T05 must commit AI
entries and their first versions atomically before T06 exposes review controls.
T07 is bonus-oriented and may be reduced to a documented deterministic module
after the genuine flow and exact provenance pass.

## Phase completion gate

Phase 4 is complete when a synthetic doctor-consult transcript is redacted,
submitted once, processed durably by a genuine model call, validated, and
persisted as one source-linked AI entry with exact highlight suggestions. A
clinician can accept or reject each suggestion, retries create no duplicates,
and ranking behavior remains inspectable, bounded, and covered by tests.
