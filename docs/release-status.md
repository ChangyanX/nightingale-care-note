# Release Status

**Last reviewed:** August 28, 2026 (SGT)  
**Overall state:** Not release-ready; core implementation and external evidence remain open.

This report separates local automated evidence from hosted, live-provider,
performance, and manual evidence. A skipped or contract-only check is not a live pass.

The assistant's work stops at local preparation and verification. Submission,
uploads, repository-visibility changes, and email are exclusively user actions.

## Current evidence

| Gate | State | Current evidence | Remaining action |
|---|---|---|---|
| Backend unit/contract tests | Passed locally | 130 passed, 5 hosted checks skipped | Rerun unified suite after every release change |
| Python lint/type checks | Passed locally | Ruff and mypy pass for application and new release modules | Preserve in final release check |
| Web lint/type checks | Passed locally | ESLint and TypeScript pass on the current Phase 5 tree | Rerun on final tree and perform production build |
| SQL parse/contracts | Passed locally | Versioned migrations parse and contract tests pass | Apply all pending migrations locally/hosted |
| Tracked secret patterns | Passed after remediation | No current tracked Groq-key-like value detected | Rotate the previously exposed Groq key before any live run |
| RBAC/RLS | Partial | Local SQL/API contracts plus five hosted tests currently skipped | Run patient/staff/clinician/admin/second-clinic hosted walkthrough |
| Revisions/concurrency | Partial | Local API/SQL contracts pass | Run live same-resource and different-resource concurrency checks |
| Exact highlight provenance | Partial | Exact resolver plus required manual/AI test and database provenance contracts exist | Complete review API/UI and hosted pointer walkthrough |
| Adaptive importance | Partial | Pure bounded/idempotent ranking plus required test exists | Persist feedback events and expose factor evidence through API/UI |
| Genuine Groq generation | Partial | Adapter, fake-provider tests, and safe smoke command exist | Configure a newly rotated key and run genuine validated call |
| AI entry/highlight persistence | Missing | Job schema and worker core exist | Complete P4-T05/P4-T06 atomic persistence and review flow |
| Realtime collaboration | Partial | Tables are published in migration contracts | Complete APIs/UI and two-session live evidence |
| Glance performance | Missing | Bounded API exists | Add benchmark and record 100+ warm requests with P50/P95/P99 |
| Technical brief | Missing | Blueprint and task plans exist | Produce and visually verify required 2-3 page PDF |
| Attribution | Missing | Dependencies are declared in manifests | Create and review `ATTRIBUTION.txt` |
| Demo video | Missing | Demo patient story exists | Write/rehearse script, record, upload, and test signed-out access |
| Deployment/TLS | Missing | Provider responsibilities are documented conceptually | Verify exact deployed origins, TLS, storage, and encryption controls |

## Immediate critical path

1. Rotate the Groq key that appeared in the tracked template; place the new key only in ignored `.env`.
2. Finish Phase 3 comment/highlight review paths required by the demo.
3. Finish Phase 4 atomic AI persistence and run one genuine synthetic flow.
4. Persist adaptive-feedback events and expose factor evidence through the API/UI.
5. Apply migrations and run hosted RLS/concurrency/two-session checks.
6. Benchmark Glance, prepare the technical brief/attribution, and rehearse the demo.
7. Run strict `make release-check` on a clean final commit.

## Commands

```bash
make release-status
make release-check
```

`release-status` is informational and reports open gates. `release-check` is
strict and must remain nonzero while required tests, artifacts, tracked-secret
safety, or clean repository state are incomplete.
