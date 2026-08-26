# Phase 6 — Hybrid Storage and Data Decay

**Full-quality estimate:** 4-6 hours  
**16-hour critical-path allocation:** Post-core; do not consume the initial 16-hour MVP budget  
**Goal:** Compress older low-value context without deleting the source of truth or weakening provenance.

## Description

Data decay is a separate bonus milestone. It reduces the cost and cognitive burden of old timeline data while preserving safety-critical information, audit history, and exact source retrieval. "Decay" means changing the default representation and storage tier, not silently forgetting the clinical record.

## Required deliverables

- Documented hot, warm, and archived tiers.
- Deterministic eligibility rules based on age, risk, task state, clinician confirmation, and provenance dependencies.
- Immutable roll-up summaries for eligible older entries.
- Archive metadata containing object location, checksum, source IDs, date range, and schema version.
- Background job that identifies eligible entries, creates a roll-up, verifies archive integrity, and only then changes the active tier.
- Retrieval flow that expands a roll-up and resolves the original source entry/span.
- Audit event for every tier transition and restoration.
- `test_data_decay.py` proving preservation and restoration behavior.

## Optional deliverables

- Actual compressed archive objects in private Supabase Storage.
- Scheduled decay runs using `pg_cron` or a platform scheduler.
- Admin preview and approval before archival.
- Storage-size and glance-query benchmark before and after decay.
- Multiple roll-up levels for very old data.

## Tier policy

### Hot

Keep fully active and queryable:

- Recent entries, initially 90 days
- Critical or high-risk items
- Unresolved tasks
- Unresolved comments
- Accepted highlights and their exact sources
- Clinician-confirmed facts
- Entries involved in an unresolved conflict

### Warm

Keep fully retrievable but omit from default Glance View queries:

- Entries between 91 and 365 days old
- Resolved low-risk tasks and comments
- Superseded context that is still useful longitudinally

### Archived

Eligible after 365 days only when all safety gates pass:

- Low-risk and resolved
- Not referenced by an active task, comment, conflict, or accepted highlight
- Included in a verified roll-up summary
- Stored with a checksum and resolvable archive pointer

The initial thresholds are configuration, not medical truth, and must be documented as prototype assumptions.

## Data model additions

```text
timeline_rollups
- id
- clinic_id
- patient_id
- period_start
- period_end
- summary
- source_entry_ids
- model_id nullable
- prompt_version nullable
- generated_at
- approved_by nullable
- approved_at nullable

archive_manifests
- id
- clinic_id
- patient_id
- rollup_id
- storage_object_path
- content_hash
- schema_version
- entry_count
- created_at
- verified_at

entries
- data_tier: hot | warm | archived
- rollup_id nullable
- archive_manifest_id nullable
- archived_at nullable
```

Original source IDs, entry versions, audit events, and provenance references remain immutable. If the implementation stores archived content outside the primary tables, the database retains a source stub sufficient to authorize and retrieve it.

## Implementation order

1. Define tier thresholds and non-decay safety gates.
2. Add roll-up, manifest, and tier metadata migrations.
3. Implement a dry-run eligibility query that explains why each entry is or is not eligible.
4. Generate a deterministic or LLM-assisted roll-up from redacted content; validate its source list.
5. Write and checksum a private archive object.
6. Read the object back and verify checksum before changing any tier.
7. Mark eligible entries archived and create audit events in one controlled workflow.
8. Implement on-demand restoration and exact provenance navigation.
9. Add automated tests and document the policy in the technical brief.

## Acceptance criteria

- [ ] Critical risks, unresolved tasks/comments, accepted-highlight sources, clinician-confirmed facts, and unresolved conflicts never decay.
- [ ] Eligibility is deterministic and returns a human-readable reason.
- [ ] A roll-up lists every source entry it summarizes.
- [ ] Archive content is written to private storage and checksum-verified before tier transition.
- [ ] Failed archival leaves the original active state unchanged.
- [ ] Every tier transition and restoration creates an audit event.
- [ ] An authorized user can expand a roll-up and retrieve the original entry and historical span.
- [ ] RLS and clinic isolation apply to archive manifests and archive objects.
- [ ] A patient cannot use an archive path to retrieve internal content.
- [ ] `test_data_decay.py` passes.

## Test cases

`test_data_decay.py` should prove:

- An old, low-risk, fully resolved entry becomes eligible.
- A recent entry remains hot.
- A critical-risk entry never becomes eligible, regardless of age.
- An entry referenced by an accepted highlight never becomes eligible.
- An unresolved task or comment blocks decay.
- A checksum or upload failure leaves the original entry unchanged.
- A successful archive remains retrievable and provenance-resolvable.
- Cross-clinic and patient-facing archive access is denied.

## Time budget

| Work item | Estimate |
|---|---:|
| Policy, schema, and dry-run eligibility | 1-2 h |
| Roll-up and archive workflow | 1-2 h |
| Retrieval, restoration, and UI explanation | 1 h |
| Tests and technical-brief documentation | 1 h |

## Definition of done

The milestone is complete when older low-value content can leave the active read path without losing its authoritative source, access controls, auditability, or exact provenance.
