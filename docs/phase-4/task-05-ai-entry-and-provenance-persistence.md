# P4-T05 — AI Entry and Provenance Persistence

**Status:** Implemented locally; migration and genuine hosted run pending
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

- [x] Each successful job resolves to exactly one AI entry.
- [x] Entry author role is `system` and type matches interaction type.
- [x] Initial history and source pointer resolve.
- [x] Patient and cross-clinic reads are denied.
- [x] Retrying after an uncertain commit produces no duplicate.

## Implementation evidence

- `202608280003_ai_persistence.sql` owns the transaction that locks and
  re-resolves the job, source record, and Care Note; creates the system entry,
  version-one snapshot, exact-span suggested highlights, and safe audit event;
  links `output_entry_id`; and only then marks the job succeeded.
- `prepare_scribe_persistence(...)` produces deterministic NFC content and
  Unicode code-point offsets from the validated structured result. The
  database highlight trigger independently verifies every quote/span pair.
- `SupabaseSourceDocumentLoader` resolves the exact source record and loads only
  linked, non-system entry text plus names required for deterministic redaction.
  `SupabaseWorkerBackend.complete(...)` then sends only the validated
  persistence payload to the transaction RPC. Both run in the separate worker;
  ordinary FastAPI requests never receive the service-role credential.
- `202608280006_live_scribe_sessions.sql` creates role-owned clinical or patient
  sources and durable jobs atomically. Patients receive a separate status-only
  projection without restricted source/output IDs.
- `test_scribe_persistence.py` covers all three interaction mappings, SQL
  parsing and transaction ownership, exact offsets, service-role RPC wiring,
  and the complete worker-to-writer path using synthetic fixtures only.

Local genuine-provider completion is now evidenced: the durable job linked one
system-authored output entry, one immutable initial version, and two exact-span
suggested highlights. Migrations `202608280007` and `202608280008` grant the
service-role worker only the table operations and row-lock privileges required
by the invoker-security source/claim/completion path. Hosted repetition remains
open.

## Done when

A fixture-backed result is proven locally. The task becomes fully evidenced
when a genuine synthetic result appears as a clearly labelled, source-linked AI
timeline entry in the hosted environment without weakening caller RLS.
