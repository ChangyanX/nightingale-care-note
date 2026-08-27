# Phase 2 — Core Patient Experience

**Full-quality estimate:** 7-9 hours  
**16-hour critical-path allocation:** 3 hours  
**Goal:** Build the shared patient page: a fast Glance View and a usable longitudinal timeline.

## Description

Phase 2 makes the core product visible. The main page must turn a fragmented record into a readable clinical story. It should be useful without AI: manually seeded and created entries must already support fast orientation, filtering, and action.

The implementation-level task sequence is maintained in
[the Phase 2 task breakdown](phase-2/README.md). The primary fixture and bounded
UI/API contract are defined in [the demo patient story](demo-patient-story.md).

## Required deliverables

- Clinic-scoped patient selector.
- Patient page with a Glance View / Top Card.
- Longitudinal timeline containing manual and AI-scribed entry types.
- Patient-provided insights and AI-patient session summaries/key questions.
- Distinct author-role, entry-type, timestamp, and provenance labels.
- Basic `care_tasks` model and open actions displayed in the Top Card.
- Lightweight live updates for entries and tasks.
- Server-filtered role-specific response shapes.
- Basic manual note creation for permitted roles.
- Clear empty, loading, unauthorized, and error states.
- Synthetic primary patient with a coherent multi-visit history.

## Optional deliverables

- Timeline filters by role, entry type, or date.
- URL deep links to an entry.
- Keyboard navigation and accessibility polish.
- Responsive mobile layout.
- Read-model cache or materialized summary for the glance endpoint.

## Implementation order

1. **Define the primary demo patient story.** Decide the concern, a historic event, a recent change, a risk, and an unresolved action.
2. **Create read APIs.** Add patient list, patient detail, timeline, and glance endpoints with authorization applied on the server.
3. **Create the clinical layout.** Build a patient header, compact Top Card, and timeline shell.
4. **Render timeline entries.** Show date, author role, source type, content, and AI/system badges. AI entries use `author_role = system`, one of the three required AI types, and a source-record pointer.
5. **Build the Glance View.** Use deterministic seeded data or a simple rule-based selector; show only the most important few items.
6. **Add care tasks and permitted note creation.** Present only the task and editor actions that the user's role may use.
7. **Add live synchronization.** Subscribe authorized clients to entry and task changes and invalidate or update the relevant queries.
8. **Add role-specific response handling.** Patient routes must request patient-safe data only.
9. **Add visual states and polish.** Confirm that a reviewer sees meaningful information in under ten seconds.

## Acceptance criteria

- [ ] An authorized staff member or clinician sees only patients in their clinic.
- [ ] Opening the primary patient shows a usable Top Card without scrolling.
- [ ] The Top Card contains a current concern, critical flag or risk where applicable, and at least one open action.
- [ ] The timeline displays entries from multiple dates and roles.
- [ ] The timeline contains patient-provided context and AI-patient key questions.
- [ ] AI-scribed entries are visibly distinct from staff and clinician entries.
- [ ] AI-scribed entries use `author_role = system`, the required interaction type, and a resolvable original source record.
- [ ] Every entry displays author role, type, timestamp, and source/provenance metadata.
- [ ] Staff and clinicians can view clinic-scoped staff notes and AI-scribed notes; patients cannot.
- [ ] The user can create a permitted manual entry and see it in the timeline.
- [ ] A staff user is never offered clinician-only editing controls.
- [ ] A patient-facing route returns no internal data, even when called directly.
- [ ] Empty, loading, error, and forbidden states are understandable.
- [ ] Two authorized browser sessions see new entries and task-state changes without a full-page reload.
- [ ] The primary flow works at desktop width without visual overlap or clipped content.

## Time budget

| Work item | Estimate |
|---|---:|
| Demo patient narrative and seed expansion | 1 h |
| Read APIs and role-filtered serializers | 1-2 h |
| Patient-page layout and timeline | 2 h |
| Glance View, tasks, and note creation | 2 h |
| Live updates, state handling, and fixes | 1-2 h |

## Do not proceed until

The primary synthetic patient can be understood from the Glance View and timeline alone. AI must improve this foundation, not compensate for an unclear core interface.
