# Phase 5 — Proof and Presentation

**Full-quality estimate:** 5-7 hours  
**16-hour critical-path allocation:** 3 hours  
**Goal:** Turn the working prototype into a reproducible, testable, and persuasive challenge submission.

## Description

Phase 5 integrates all features, removes demo-risk, measures performance, and prepares the required handoff materials. This phase is not cosmetic: it is where the team proves that security, provenance, and collaboration claims are true.

## Required deliverables

- All required automated tests passing.
- Reproducible local setup and run instructions in `README.md`.
- Clear documentation of RBAC enforcement and the redaction path.
- P95 warm-path Glance View measurement and documented method.
- 2-3 page technical brief with architecture; the complete Entries ↔ Comments ↔ Versions ↔ Highlights ↔ Provenance ↔ AI-scribed-notes ↔ learning linkage; assumptions; and trade-offs.
- `ATTRIBUTION.txt` listing external libraries, models, and licenses.
- Recorded demo video covering core scenarios.
- Final synthetic-data and secrets review.
- TLS-in-transit and encryption-at-rest verification for the deployed stack.
- Clean commit history and deployable repository.

## Optional deliverables

- CI status badge.
- Deployed public demo environment with restricted demo accounts.
- Architecture video overlay or animated system diagram.
- Accessibility audit.
- UI polishing beyond the required demo paths.
- Backup or export verification.

## Implementation order

1. **Freeze scope.** Stop adding unproven optional features; create a short bug and demo-risk list.
2. **Run the complete test suite.** Fix every required test failure and add regression coverage for discovered defects.
3. **Verify role boundaries manually.** Use patient, staff, clinician, admin, and second-clinic accounts.
4. **Benchmark the Glance View.** Seed a realistic history, warm the endpoint, make at least 100 requests, and record P50/P95/P99.
5. **Prepare the technical brief.** Explain the architecture, entity relationships, RLS request path, revision model, genuine AI flow, redaction, exact provenance, adaptive ranking, encryption controls, and trade-offs.
6. **Finalize README and attribution.** A reviewer must be able to run tests and understand data safety without asking questions.
7. **Script and record the demo.** Use deterministic synthetic data and pre-seeded user states.
8. **Deploy and rehearse.** Test the exact deployed flow and keep a local fallback available for recording.
9. **Perform final repository review.** Check for secrets, real data, broken links, untracked artifacts, and undocumented dependencies.

## Acceptance criteria

- [ ] `test_rbac_scope.py` passes.
- [ ] `test_revision_history.py` passes.
- [ ] `test_highlight_provenance.py` passes.
- [ ] `test_concurrent_edits.py` passes.
- [ ] `test_self_learning_importance.py` passes.
- [ ] Test commands are documented and succeed from a fresh setup.
- [ ] The README explains setup, run, test, redaction, RBAC, and synthetic-data constraints.
- [ ] The technical brief includes an architecture diagram and linked data schema.
- [ ] The data diagram explicitly links entries, comments, versions, highlights, source/provenance records, AI-scribed entries, and adaptive feedback.
- [ ] The technical brief names assumptions and scope trade-offs honestly.
- [ ] The performance method states dataset size, warm/cold condition, request count, region assumptions, and P50/P95/P99.
- [ ] The recorded demo shows Glance View, provenance navigation, collaboration/revision history, and longitudinal context.
- [ ] The demo includes or explains the security boundary and AI-review behavior.
- [ ] `ATTRIBUTION.txt` lists every external library, model, and applicable license.
- [ ] Deployed web, API, database, storage, and LLM connections use TLS, and encryption-at-rest responsibilities are documented.
- [ ] Git history is understandable and the repository contains no secrets or non-synthetic patient data.

## Time budget

| Work item | Estimate |
|---|---:|
| Full integration and regression tests | 1-2 h |
| Performance measurement and fixes | 1 h |
| Technical brief, README, attribution | 1-2 h |
| Demo script, recording, and retakes | 1-2 h |
| Deployment verification and final audit | 1 h |

## Final submission checklist

- [ ] Repository link or zip is accessible.
- [ ] Application starts from documented instructions.
- [ ] Automated tests pass.
- [ ] Demo accounts or a demo procedure are available.
- [ ] Technical brief is attached or linked.
- [ ] Demo video is accessible.
- [ ] Attribution is complete.
- [ ] Resume and requested contact details are prepared separately from source code where appropriate.
- [ ] Every item in [the submission checklist](submission-checklist.md) is complete before the deadline.

## Definition of done

The submission is complete when a reviewer can independently reproduce the main flows, verify the required tests, understand every high-value claim's provenance, and see that AI assists clinical review rather than replacing it.
