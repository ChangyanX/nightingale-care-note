# P4-T05 — AI Entry and Provenance Persistence

**Status:** Pending  
**Full estimate:** 1 hour  
**16-hour path:** 30 minutes  
**Dependencies:** P4-T03, P4-T04, Phase 3 provenance schema

## Objective

Persist each validated scribe result as exactly one immutable, system-authored
timeline entry linked to the originating source record.

## Required work, in order

1. Map interaction types to the three required AI entry types.
2. Re-resolve job, source, patient, clinic, and care note inside one transaction.
3. Create a system-authored internal entry and version-one snapshot.
4. Link job output to the created entry with a uniqueness constraint.
5. Create safe audit metadata containing IDs, schema/model version, and action only.
6. Mark the job completed only after output persistence commits.
7. Return an existing output on retry rather than creating a duplicate.
8. Add parity fixtures and transactional tests.

## Must be done

- The model never supplies identity, author, visibility, timestamps, or database IDs.
- Doctor, nurse, and AI-patient types cannot be interchanged accidentally.
- AI entries remain internal and unavailable to patient responses.
- The source pointer resolves to the exact originating interaction record.
- Job completion, entry, initial version, and audit evidence commit atomically.

## Optional

- A separately reviewed patient-facing summary derived from the internal AI entry.
- Storage of encrypted provider request IDs for support diagnostics.

## Acceptance criteria

- [ ] Each successful job resolves to exactly one AI entry.
- [ ] Entry author role is `system` and type matches interaction type.
- [ ] Initial history and source pointer resolve.
- [ ] Patient and cross-clinic reads are denied.
- [ ] Retrying after an uncertain commit produces no duplicate.

## Done when

A genuine and a fixture-backed result appear as clearly labelled, source-linked
AI timeline entries without weakening the ordinary caller RLS model.
