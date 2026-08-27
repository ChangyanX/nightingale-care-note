# P5-T01 — Scope Freeze and Evidence Inventory

**Status:** Implemented; open gates recorded
**Full estimate:** 0.5 hours
**16-hour path:** 15 minutes
**Dependencies:** Phases 1-4

## Objective

Freeze the release claim set and record what is proven locally, what needs a
hosted environment, what needs a live model, and what remains incomplete.

## Required work, in order

1. List every required brief claim and exact evidence location.
2. Classify each item as passed, partial, missing, hosted-only, live-provider, or manual.
3. Record current automated test counts without converting skipped tests into passes.
4. List demo-breaking gaps separately from optional enhancements.
5. Freeze Phase 6 and nonessential UI polish until core release gates pass.
6. Assign an owner/action and estimated completion time to each open blocker.

## Must be done

- Genuine LLM generation is distinct from seeded AI entries and fake-provider tests.
- Contract tests are distinct from direct live RLS/concurrency verification.
- Missing exact required test files are visible.
- The inventory never contains passwords, keys, tokens, or raw clinical bodies.
- Scope statements match the requirements traceability matrix.

## Optional

- GitHub issue labels mirroring release-gate states.
- A generated HTML status dashboard.

## Acceptance criteria

- [x] `docs/release-status.md` identifies local and external evidence separately.
- [x] Required missing tests and deliverables are listed.
- [x] Phase 6 remains deferred until the core submission is stable.
- [ ] Every open core gate has passed or has a precise limitation in the final brief.

## Done when

No reviewer-facing claim depends on an unstated assumption or an unavailable environment.
