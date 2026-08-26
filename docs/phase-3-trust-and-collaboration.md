# Phase 3 — Trust and Collaboration

**Full-quality estimate:** 8-10 hours  
**16-hour critical-path allocation:** 3.5 hours  
**Goal:** Make the shared record collaborative, auditable, conflict-safe, and fully traceable.

## Description

This phase implements the challenge's central trust model. Users should be able to collaborate around a note, inspect how it changed, return to a prior state, and follow every surfaced highlight back to its source. Prioritize reliable section-level collaboration over a complex real-time document editor.

## Required deliverables

- Immutable entry versions and audit events.
- Version viewer with before/after comparison.
- Revert flow that creates a new version instead of deleting history.
- Optimistic concurrency control and deterministic same-section conflict handling.
- Threaded comments with resolve and unresolve states.
- Mentions and optional task assignment.
- Live updates for comments and highlight decisions.
- Highlight model with status, reason, score, and provenance.
- Exact source-entry and source-span navigation.
- Required revision-history, provenance, and concurrent-edit tests.

## Optional deliverables

- Rich text editing.
- Inline comments attached to individual spans.
- User notifications for mentions or assignments.
- Side-by-side diff view with word-level highlighting.
- Conflict-resolution UI that suggests a merge.

## Implementation order

1. **Extend collaboration schema.** Expand the foundation comment model with threads, mentions, assignments, and resolution; add highlights and exact source-span fields. `care_tasks` already exists from Phase 2.
2. **Implement immutable versions.** Every update stores a snapshot and audit event in one transaction.
3. **Implement optimistic concurrency.** Require `expected_version` on updates and return `409 Conflict` on a stale edit.
4. **Build revision APIs and UI.** List versions, compare the current state with any selected version ("changes since X"), and support a confirmed revert.
5. **Implement comments and assignments.** Validate that mentions and assignees remain in the clinic.
6. **Implement highlights.** Store source entry, source version, character offsets, quoted text, reason, and review status. Reject highlights that cannot resolve exactly.
7. **Implement source navigation.** A highlight click must open and visually identify the source entry and text span.
8. **Add live synchronization.** Authorized sessions receive comment, task, and highlight-decision changes without a page reload.
9. **Write the required tests.** Include an AI-scribed source, changed-source behavior, and conflict scenarios, not only happy paths.

## Acceptance criteria

- [ ] Editing an entry increments its version exactly once.
- [ ] Older versions are immutable and remain readable.
- [ ] The user can compare the current state with any selected historical version.
- [ ] Reverting restores selected content by creating a new version.
- [ ] Every mutation creates an audit event with actor, role, action, resource, and timestamp.
- [ ] A stale same-section update returns `409 Conflict` and loses no data silently.
- [ ] Concurrent edits to different entries or role-owned sections both succeed.
- [ ] Staff and clinician ownership rules continue to apply during update and revert operations.
- [ ] A comment can be created, mentioned, assigned, resolved, and reopened by authorized users.
- [ ] Each highlight includes source entry ID, source version ID, valid offsets, quoted text, a short reason, and status.
- [ ] Clicking a highlight navigates to its exact timeline source.
- [ ] A highlight that lacks a valid entry, version, span, or quoted-text match cannot be published.
- [ ] Provenance tests generate at least one highlight from an AI-scribed note.
- [ ] A source remains resolvable through historical versions after a later edit.
- [ ] Two authorized sessions see comment and highlight-decision changes without a full-page reload.
- [ ] `test_revision_history.py`, `test_highlight_provenance.py`, and `test_concurrent_edits.py` pass.

## Time budget

| Work item | Estimate |
|---|---:|
| Collaboration schema and transactional version/audit logic | 2 h |
| Conflict behavior and tests | 1-2 h |
| Revision UI and revert | 1-2 h |
| Comments, mentions, assignments, and live updates | 2 h |
| Highlights and provenance navigation | 2 h |

## Do not proceed until

Every highlight has working provenance and every edit has auditable history. These are the project's strongest differentiators and should work before any advanced AI feature is introduced.
