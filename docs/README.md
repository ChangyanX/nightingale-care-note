# Build Phases

The consolidated [Phase 1–4 optional-deliverables audit](phase-1-4-optional-deliverables.md)
maps every optional item to implementation evidence and separates local
completion from hosted/live-provider verification.

This folder turns the project blueprint into five implementation milestones. Work through the phases in order; each phase reduces risk for the next one.

| Phase | Focus | Estimate | Exit condition |
|---|---|---:|---|
| [1. Foundation](phase-1-foundation.md) | Repository, database, auth, RBAC, seed data | 8-10 hours | Security boundaries are proven by automated tests. |
| [2. Core Patient Experience](phase-2-core-patient-experience.md) ([tasks](phase-2/README.md)) | Timeline, patient page, Top Card, tasks, live updates | 7-9 hours | A clinician can understand a synthetic patient record quickly. |
| [3. Trust and Collaboration](phase-3-trust-and-collaboration.md) ([tasks](phase-3/README.md)) | Comments, versions, provenance, conflicts | 8-10 hours | Every highlight and edit is explainable and traceable. |
| [4. AI Pipeline](phase-4-ai-pipeline.md) ([tasks](phase-4/README.md)) | Redaction, durable jobs, genuine AI summaries, adaptive ranking | 7-9 hours | AI output is safe, structured, traceable, and human-reviewable. |
| [5. Proof and Presentation](phase-5-proof-and-presentation.md) ([tasks](phase-5/README.md)) | Tests, benchmark, documentation, demo | 5-7 hours | The submission can be reproduced and demonstrated reliably. |
| [6. Hybrid Storage and Data Decay](phase-6-data-decay.md) | Roll-ups, tiers, archive retrieval, decay policy | 4-6 hours | Older context is compressed without breaking trust or provenance. |

The full-quality core estimate for Phases 1-5 is 35-45 focused hours; Phase 6 adds 4-6 hours. The user currently has an approximately 16-hour initial budget, so each phase file also contains a critical-path allocation totalling 16 hours. That track requires strict scope control, pre-seeded demo data, one genuine AI flow, and minimal visual polish. Phase 6 begins only after the core submission is stable.

The adaptive importance mechanism in Phase 4 is not reinforcement learning. It uses bounded, explainable weight updates from explicit accept, reject, pin, edit, and comment events. Ambient voice capture and CRDT-style simultaneous text editing remain out of scope.

For architecture, data-model, and security details, see [the project blueprint](blueprint.md).
Role routing, Account Settings, notification/session behavior, the patient-safe
DTO/RLS boundary, and the intentionally lightweight portal scope are in
[Role Portals, Account Security, and Patient Privacy](role-portals-and-privacy.md).

Hosted Supabase setup and the credential boundary are defined in
[Supabase Setup](supabase-setup.md) and
[Credentials and Access](credentials-and-access.md).

Use [the requirements traceability matrix](requirements-traceability.md) during implementation and [the submission checklist](submission-checklist.md) before delivery.
