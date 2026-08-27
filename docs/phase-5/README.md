# Phase 5 Task Breakdown — Proof and Presentation

Phase 5 turns implementation claims into reproducible evidence. It freezes
optional scope, inventories every release gate, runs automated and manual
verification, measures the Glance path, prepares the technical brief and demo,
and audits the final repository before submission.

| ID | Task | Status | Full estimate | 16-hour path | Depends on | Exit evidence |
|---|---|---|---:|---:|---|---|
| [P5-T01](task-01-scope-freeze-and-evidence-inventory.md) | Scope freeze and evidence inventory | Implemented; open gates recorded | 0.5 h | 15 min | Phases 1-4 | Honest release status and risk list |
| [P5-T02](task-02-unified-validation-and-required-tests.md) | Unified validation and required tests | Implemented locally; hosted checks remain | 1 h | 30 min | T01 | One release command and required test evidence |
| [P5-T03](task-03-security-role-and-repository-audit.md) | Security, role, and repository audit | Automated secret check implemented; manual/hosted checks pending | 0.75 h | 25 min | T02 | Role walkthrough and clean tracked files |
| [P5-T04](task-04-glance-performance-benchmark.md) | Glance performance benchmark | Pending | 0.75 h | 25 min | Stable Glance API, hosted/local data | Reproducible P50/P95/P99 report |
| [P5-T05](task-05-technical-brief-and-diagrams.md) | Technical brief and diagrams | Pending | 1.5 h | 40 min | T01-T04 | Reviewable 2-3 page technical brief |
| [P5-T06](task-06-readme-attribution-and-reproducibility.md) | README, attribution, and reproducibility | Partial | 0.75 h | 20 min | T02-T05 | Fresh-setup instructions and attribution |
| [P5-T07](task-07-demo-script-and-rehearsal.md) | Demo script and rehearsal | Pending | 1 h | 30 min | Stable demo path | Timed scenarios and recording fallback |
| [P5-T08](task-08-deployment-and-final-submission.md) | Deployment verification and handoff preparation | Pending | 1 h | 15 min | T01-T07 | Verified local handoff checklist |

**Full Phase 5 estimate:** approximately 7 hours  
**Critical-path allocation:** 3 hours

## Release rules

- Missing evidence is reported as missing; seeded fixtures do not count as a genuine LLM run.
- Hosted/manual/live checks remain separate from local contract tests.
- Required brief-named tests must exist under their exact filenames and pass.
- Performance evidence records dataset size, warm-up, request count, environment, and percentiles.
- No `.env`, API key, service-role secret, access token, real patient data, or raw prompt is committed.
- Demo content and accounts remain synthetic and replaceable.
- Admin is demonstrated read-only; patient and second-clinic denials are included.
- Required functionality is stabilized before Phase 6 bonus work or visual polish.
- The assistant must not submit or upload artifacts, change repository
  visibility, or send email; all external delivery actions are user-only.

## Recommended execution order

Run T01-T03 immediately and fix any credential or required-test issue before
benchmarking. Complete T04 on the same environment described in the report.
Write T05 from verified evidence, then finish T06. Rehearse T07 against the
exact build and complete the T08 handoff package with at least a 30-minute
deadline buffer for the user's own submission actions.

## Phase completion gate

Phase 5 is complete only when a reviewer can start the application from the
README, run the documented release checks, inspect the technical brief, follow
the deterministic demo, verify required security/provenance claims, and has a
clear checklist for personally completing any external delivery actions.
