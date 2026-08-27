# P4-T08 — Required Tests and Handoff

**Status:** Pending  
**Full estimate:** 1 hour  
**16-hour path:** 10 minutes  
**Dependencies:** P4-T01 through P4-T07

## Objective

Prove the redacted AI pipeline is durable, idempotent, exact-provenance,
human-reviewed, and reproducible without requiring live credentials in CI.

## Required work, in order

1. Run redaction, schema, structured-output, worker, idempotency, provenance,
   review, ranking, RBAC, lint, and type checks.
2. Run one live synthetic doctor-consult generation and record sanitized evidence.
3. Exercise nurse and AI-patient fixtures through the same validated ingestion contract.
4. Force a provider retry and an uncertain persistence retry.
5. Verify logs and job status contain no raw bodies, secrets, or provider error payloads.
6. Verify patient/admin/cross-clinic boundaries against AI jobs, entries, and highlights.
7. Record exact source-navigation and fast-review UI evidence.
8. Update task statuses, README commands, credential guidance, traceability, and demo script.

## Must be done

- Offline tests are deterministic and use the fake provider.
- Live tests are explicitly opted in and skipped when credentials are absent.
- Evidence names the model and run time but contains only synthetic/redacted content.
- Genuine execution is distinguishable from seeded/pre-generated fixtures.
- Known limitations of deterministic redaction are documented.

## Optional

- Provider latency/cost table.
- Realtime completion animation.
- A second genuine interaction type.

## Acceptance criteria

- [ ] `test_redaction.py` passes.
- [ ] `test_job_idempotency.py` passes.
- [ ] `test_highlight_provenance.py` passes.
- [ ] `test_self_learning_importance.py` passes.
- [ ] Full backend/web/static validation passes.
- [ ] One genuine run and two typed fixture runs persist correctly.
- [ ] No sensitive values appear in inspected logs or committed files.
- [ ] Setup and credential instructions reproduce the flow.

## Done when

The Phase 4 completion gate is evidenced locally and, where credentials are
required, by one sanitized genuine-provider run.
