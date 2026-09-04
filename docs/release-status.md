# Release Status

**Last reviewed:** August 28, 2026 (SGT)  
**Overall state:** Role-portal enhancements pass local verification; final release artifacts and hosted evidence remain open.

This report separates local automated evidence from hosted, live-provider,
performance, and manual evidence. A skipped or contract-only check is not a live pass.

The assistant's work stops at local preparation and verification. Submission,
uploads, repository-visibility changes, and email are exclusively user actions.

## Current evidence

| Gate | State | Current evidence | Remaining action |
|---|---|---|---|
| Backend unit/contract tests | Passed locally | 193 passed, 5 hosted checks skipped | Rerun unified suite after every release change |
| Python lint/type checks | Passed locally | Ruff and mypy pass for application and new release modules | Preserve in final release check |
| Web lint/type/build | Passed locally | ESLint, TypeScript, and the production Next.js build pass | Rerun on final tree |
| Frontend data boundary | Passed locally | Automated check permits browser Supabase Auth/Realtime invalidation but rejects direct Data API, RPC, Storage, and Functions access | Preserve the boundary check in CI/pre-commit |
| Browser visual/keyboard checks | Passed locally | 32 desktop/mobile Chromium checks pass, including patient/clinician live AI triggers, role routing, timeline authoring, collaboration, logout, password visibility, and theme persistence | Recheck after UI changes |
| Phase 1-4 optional deliverables | Implemented locally | Consolidated evidence matrix covers every optional item | Run hosted/live-provider gates separately |
| SQL parse/contracts | Passed locally | Migrations through `202608280008` applied to local PostgreSQL; `supabase db lint --local` reports no schema errors | Apply the same migrations to the hosted environment and rerun `db lint` |
| Tracked secret patterns | Passed after remediation | No current tracked Groq-key-like value detected | Rotate the previously exposed Groq key before any live run |
| RBAC/RLS | Partial | Local tests deny patients the clinical list/detail/timeline/Glance surface and enforce the reduced patient DTO; five hosted tests remain skipped | Run patient/staff/clinician/admin/second-clinic hosted walkthrough |
| Revisions/concurrency | Partial | Local API/SQL contracts pass | Run live same-resource and different-resource concurrency checks |
| Exact highlight provenance | Implemented locally | Exact resolver, manual/AI tests, database contracts, review API/UI, bulk review, and source navigation exist | Run hosted pointer walkthrough |
| Adaptive importance | Implemented locally | Bounded/idempotent ranking, per-user event persistence, local embeddings, decay, authenticated API, reset, and UI feedback exist | Run hosted behavior walkthrough |
| Genuine Groq generation | Passed local durable gate | A redacted synthetic doctor consult completed against `openai/gpt-oss-20b` through the durable worker; safe token/timing/count evidence is recorded without clinical text | Repeat the durable job in the hosted environment |
| AI entry/highlight persistence | Passed local durable gate | A genuine synthetic job produced one linked system entry/version and two exact-span highlights through the atomic RPC; worker service-role grants are versioned and locally linted | Apply/configure the same worker in the hosted environment |
| Realtime collaboration | Implemented locally | Published tables, refetch/status/toast UI, comments, tasks, highlight review, job stages, and durable notifications exist | Capture two-session hosted evidence |
| Glance performance | Partial | A 120-request in-process guard passes; timeline/task reads are parallel; the authenticated live benchmark records P50/P95/P99 and enforces P95 <= 300 ms | Run `make benchmark-glance` against the final hosted warm path and retain its output |
| Technical brief | Missing | Blueprint and task plans exist | Produce and visually verify required 2-3 page PDF |
| Attribution | Missing | Dependencies are declared in manifests | Create and review `ATTRIBUTION.txt` |
| Demo video | Missing | Demo patient story exists | Write/rehearse script, record, upload, and test signed-out access |
| Deployment/TLS | Missing | Provider responsibilities are documented conceptually | Verify exact deployed origins, TLS, storage, and encryption controls |

## Immediate critical path

1. Rotate the Groq key that appeared in the tracked template; place the new key only in ignored `.env`.
2. Deploy/configure the hosted worker and repeat the locally passed genuine durable flow.
3. Run hosted RLS/concurrency/two-session checks.
4. Run the live Glance benchmark, prepare the technical brief/attribution, and rehearse the demo.
5. Run strict `make release-check` on a clean final commit.

## Commands

```bash
make release-status
make release-check
```

`release-status` is informational and reports open gates. `release-check` is
strict and must remain nonzero while required tests, artifacts, tracked-secret
safety, or clean repository state are incomplete.
