# Primary Demo Patient Story

All people, events, identifiers, and clinical statements in this story are
synthetic. The fixture demonstrates information organization and authorization;
it is not medical advice and must not be presented as a diagnostic workflow.

## Ten-second orientation

**Patient:** Parker Patient (`SYN-A-001`), Harbour Family Clinic  
**Current concern:** A persistent cough is more frequent at night.  
**Secondary concern:** Sleep disruption is affecting daytime concentration,
without synthetic red-flag symptoms. This remains below the primary concern in
the bounded importance ordering.
**Recent change:** The patient reports being woken twice and noticing worse
symptoms in a cold room.  
**Watch item:** Night-time symptoms have worsened since the initial staff call;
the fixture records no synthetic emergency features.  
**Clinician-confirmed plan:** Review inhaler technique, record morning and
evening peak-flow readings for seven days, then reassess.  
**Open action:** Review the seven-day diary and symptom pattern.  
**Patient question:** Do the new night-time symptoms require an earlier review?

The intended reviewer answers are:

1. What matters now? Persistent, worsening nocturnal cough.
2. What changed? Sleep disruption and cold-room association were newly reported.
3. What needs action? Complete and review the peak-flow diary, with earlier
   contact if breathing worsens.

## Source map

| Story element | Source entry | Source record | Perspective | Patient-safe? |
|---|---|---|---|---:|
| Initial night-time cough report | `700…001` | `600…001` | Staff manual note | No |
| Assessment and diary plan | `700…002` | `600…002` | Clinician manual note | No |
| Doctor-consult summary | `700…003` | `600…003` | AI-generated doctor consult | No |
| Inhaler coaching completed | `700…004` | `600…004` | AI-generated nurse consult | No |
| Earlier-review question | `700…005` | `600…005` | AI-generated patient session | No raw AI note |
| Peak-flow instructions | `700…006` | `600…006` | Clinician patient instruction | Yes |
| Sleep/cold-room observation | `700…007` | `600…007` | Patient-provided insight | Own entry only |

The complete UUIDs remain in `supabase/seed.sql`. The shortened identifiers
above are for readable documentation only.

## Glance View contract

The Phase 2 Glance response is deterministic and returns at most six items. The
primary fixture initially uses four:

| Order | Kind | Claim | Why it matters | Link target |
|---:|---|---|---|---|
| 1 | `current_concern` | Persistent cough is more frequent at night | Active concern documented by staff and clinician | Entry `700…002` |
| 2 | `recent_change` | Woke twice; worse in a cold room | New patient-reported change after the initial consult | Entry `700…007` |
| 3 | `open_action` | Review seven-day peak-flow diary and symptoms | High-priority unresolved follow-up | Open care task and Entry `700…002` |
| 4 | `patient_question` | Do night symptoms require earlier review? | Unresolved question from the AI-patient session | Entry `700…005` |

Each item contains a stable kind, concise claim, importance reason, status,
occurrence time, optional task ID, source entry ID, and source-record summary.
Phase 3/4 provenance adds historical version and exact text offsets before a
highlight can be accepted or published as an exact-source highlight.

## Mobile content guidance

- Glance claims target 120 characters and remain understandable without truncation.
- Importance reasons target 180 characters; assistive technology retains the full value.
- Task titles target 120 characters and never duplicate raw clinical-note bodies.
- Timeline text wraps naturally and is not clipped to a fixed number of lines.
- Source, role, status, and risk remain text-labelled rather than color-only.

## API response boundaries

### Clinical patient summary

Contains patient ID, clinic ID, synthetic identifier, display name, and the
caller's clinic role. It does not contain raw authentication metadata.

### Timeline entry

Contains entry identity, author identity/role, type, visibility, content,
version, occurrence time, and a nested source summary:

```json
{
  "id": "source-record-uuid",
  "type": "doctor_consult",
  "external_reference": "doctor-consult-001",
  "occurred_at": "2026-08-24T09:30:00+08:00"
}
```

The clinical response may contain internal and AI-generated entries because RLS
has already proved clinic membership. The patient-facing response uses a
separate schema and selects only patient summaries/instructions plus the
patient's own submitted insights.

### Care task

Contains task ID, patient ID, title, status, priority, optional assignee and due
time, optional source entry, and timestamps. Phase 2 tasks are internal and are
not returned to patients.

## Role controls

| Control | Staff | Clinician | Admin | Patient |
|---|---:|---:|---:|---:|
| View clinic Glance/timeline/tasks | Yes | Yes | Yes | No |
| Add staff note | Yes | No | No | No |
| Add clinician note/instruction | No | Yes | No | No |
| Update internal care task | Yes | Yes | No | No |
| Add patient insight | No | No | No | Yes, own record |
| View raw AI summaries | Yes | Yes | Yes, read-only | No |

These controls describe the UI. FastAPI and PostgreSQL RLS independently
enforce the same boundary when an endpoint is called directly.

## Seed consistency requirement

The local `supabase/seed.sql` and hosted `scripts.seed_hosted` helper must
produce the same story, source dates, and task states even though hosted Auth
user UUIDs and passwords are generated dynamically.
