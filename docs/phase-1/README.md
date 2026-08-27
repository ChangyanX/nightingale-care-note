# Phase 1 Task Breakdown — Foundation

All Phase 1 optional deliverables are implemented and mapped in the
[Phase 1–4 optional-deliverables audit](../phase-1-4-optional-deliverables.md).

Phase 1 establishes a runnable and testable security foundation. Tasks are ordered by dependency and should be completed sequentially unless a task explicitly permits parallel work.

| ID | Task | Status | Full estimate | 16-hour path | Depends on | Exit evidence |
|---|---|---|---:|---:|---|---|
| [P1-T01](task-01-repository-baseline.md) | Repository baseline | Implemented | 30 min | 15 min | None | Clean root conventions and documented commands |
| [P1-T02](task-02-application-scaffolds.md) | Web and API scaffolds | Locally verified | 1 h | 25 min | T01 | Both applications start and expose health UI/API |
| [P1-T03](task-03-supabase-environment.md) | Supabase environment | Runtime pending | 1 h | 15 min | T01 | Reproducible local/hosted configuration |
| [P1-T04](task-04-foundation-schema.md) | Foundation schema | SQL parsed; apply pending | 2 h | 35 min | T03 | Versioned schema with tenancy, provenance, and ownership |
| [P1-T05](task-05-authentication-and-rls.md) | Authentication and RLS | Contract verified; live pending | 1.5 h | 35 min | T04 | Caller-scoped policies enforce role and clinic boundaries |
| [P1-T06](task-06-foundation-api.md) | Foundation API | Locally verified; live Auth pending | 1 h | 20 min | T02, T05 | Authenticated identity/patient/timeline endpoints |
| [P1-T07](task-07-synthetic-seed-data.md) | Synthetic seed data | SQL parsed; reset pending | 30 min | 15 min | T04 | Repeatable two-clinic dataset |
| [P1-T08](task-08-rbac-tests-and-handoff.md) | RBAC tests and handoff | 24 pass; 5 live checks pending | 1 h | 20 min | T05-T07 | Required denials pass and setup is documented |

**Full Phase 1 estimate:** approximately 8.5 focused hours  
**Critical-path allocation:** 3 hours

## Phase rules

- Do not use the Supabase service-role credential for ordinary user requests.
- All database changes are migrations; avoid dashboard-only schema edits.
- Use synthetic data only.
- Keep patient-facing reads structurally separate from internal reads.
- Write denial tests for every authorization rule.
- Preserve existing staged files and unrelated user work.

## Phase completion gate

Phase 1 is complete only when a fresh setup can start the web and API applications, apply migrations, load deterministic seed data, and pass the documented RBAC test command.
