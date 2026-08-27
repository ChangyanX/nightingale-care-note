# P4-T04 — Provider Gateway and Worker

**Status:** Pending; live provider/model selection required before genuine run  
**Full estimate:** 1.5 hours  
**16-hour path:** 45 minutes  
**Dependencies:** P4-T02, P4-T03

## Objective

Run durable jobs through one guarded provider interface that accepts verified
redacted text, requests structured output, and records only safe operational metadata.

## Required work, in order

1. Define a provider protocol returning the structured scribe contract.
2. Add a deterministic fake provider for tests and fixtures.
3. Add one live provider adapter configured only through deployment secrets.
4. Require a verified redaction result at the provider boundary.
5. Implement a worker loop that claims, processes, completes, or reschedules one job atomically.
6. Classify validation, rate-limit, timeout, authentication, and permanent provider failures.
7. Add capped exponential backoff with deterministic jitter or no jitter in tests.
8. Log only job/request IDs, model name, timing, token counts if available, status, and safe error codes.
9. Execute and retain evidence of one genuine synthetic doctor-consult run.

## Must be done

- `LLM_API_KEY` and model configuration stay server/worker-side and out of Git.
- The provider method cannot be called with raw text or an unverified result.
- Provider responses and exception bodies are never logged verbatim.
- A crash before completion leaves the job recoverable and idempotent.
- Tests use the fake provider; CI does not require live credentials.

## Optional

- A second provider adapter.
- Streaming status beyond queued/processing/completed/failed.
- Token-cost dashboard.

## Acceptance criteria

- [ ] Fake-provider worker tests run fully offline.
- [ ] No provider call occurs when redaction verification fails.
- [ ] Transient failures reschedule; permanent failures terminate safely.
- [ ] A stopped claim becomes eligible after the recovery timeout.
- [ ] One genuine run records provider/model/time evidence without recording raw content.

## Decision needed before live run

Choose the live provider/model and supply its key through the ignored root `.env`
or deployment secret store. This decision is intentionally isolated to the adapter.

## Done when

The same worker code passes deterministic tests and successfully completes one
genuine redacted, structured synthetic doctor-consult generation.
