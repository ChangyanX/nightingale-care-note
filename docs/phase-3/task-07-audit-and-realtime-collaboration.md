# P3-T07 — Audit and Realtime Collaboration

**Status:** Implemented locally; hosted two-session evidence pending
**Full estimate:** 1 hour
**16-hour path:** 20 minutes
**Dependencies:** P3-T02 through P3-T06

## Objective

Make collaboration changes visible across authorized sessions and ensure every
mutation has a minimal, useful, non-clinical audit record.

## Required work, in order

1. Audit entry/section edits, reverts, comments, task changes, mentions, and highlight reviews.
2. Standardize action/resource/version/source identifiers in metadata.
3. Add comments, mentions, tasks, and highlights to Realtime publication.
4. Subscribe by active patient and invalidate only affected authorized queries.
5. Tear down channels when patient/session changes.
6. Handle reconnects and duplicate events without duplicated UI rows.
7. Verify two authorized sessions and a denied patient/cross-clinic session.

## Must be done

- Audit rows do not duplicate note, comment, or quote bodies.
- Realtime uses the signed-in user session, never service-role credentials.
- Event payloads trigger caller-authorized refetches.
- Loss of Realtime does not prevent manual refresh or normal mutations.

## Optional

- Collaborator activity toast.
- Durable notifications for mentions.
- Reconnect status indicator.

## Acceptance criteria

- [ ] Each required mutation creates one sanitized audit event.
- [ ] Comment/task/highlight decision appears in another authorized session without reload.
- [ ] Duplicate/replayed events do not duplicate visible rows.
- [ ] Patient and cross-clinic sessions receive no internal collaboration content.
- [ ] Channel teardown prevents stale-patient updates.

## Evidence

- Audit contract tests
- Realtime subscription module/tests
- Two-session verification note

## Done when

Collaboration is timely for users and reconstructable for reviewers without leaking content in logs.
