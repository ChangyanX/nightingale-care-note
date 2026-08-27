# P2-T01 — Demo Patient Story and Contracts

**Status:** Implemented  
**Full estimate:** 30 minutes  
**16-hour path:** 10 minutes  
**Dependencies:** Phase 1 foundation schema and synthetic data

## Objective

Define one coherent synthetic patient story and the exact bounded data the
selector, Glance View, timeline, and actions need before UI implementation.

## Required work, in order

1. Define the primary patient's current concern, recent change, material risk,
   clinician-confirmed plan, and unresolved action.
2. Map each claim to a seeded source record and timeline entry.
3. Include multiple dates and all required perspectives: staff, clinician,
   patient, doctor-consult AI, nurse-consult AI, and AI-patient session.
4. Define the Glance response shape and a maximum item count.
5. Define timeline and task response shapes, including provenance metadata.
6. Record which roles may see each item and which controls each role receives.

## Must be done

- The story must be understandable without generating new AI output.
- At least one open action must have a clear owner or unassigned state.
- Patient-provided context and the AI-patient key question must be explicit.
- No assertion may rely on real patient data.
- Glance items must explain why they matter and identify their source.

## Optional

- Add a second concern to demonstrate prioritization.
- Add a resolved historical task to contrast with the open action.
- Add mobile-specific content-length guidance.

## Acceptance criteria

- [ ] A reviewer can answer “what matters, what changed, and what needs action?”
  from the written contract.
- [ ] Every planned Glance item resolves to a source entry or care task.
- [ ] The primary timeline spans at least three timestamps and multiple roles.
- [ ] The patient-safe subset is explicitly distinguished from internal content.
- [ ] API response shapes are bounded and do not require the browser to infer
  permissions from hidden fields.
- [ ] The contract fits the existing Phase 1 provenance and ownership model.

## Evidence

- `docs/demo-patient-story.md`
- Response models in `services/backend/app/schemas.py`
- Synthetic rows in `supabase/seed.sql` and the hosted seed helper

## Done when

The narrative and response contract are stable enough that database, API, and
UI work can proceed without inventing clinical meaning independently.
