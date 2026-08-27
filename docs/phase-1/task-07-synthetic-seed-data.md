# P1-T07 — Synthetic Seed Data

**Status:** Implemented and parser-verified; database reset/seed pending  
**Full estimate:** 30 minutes  
**16-hour path:** 15 minutes  
**Dependencies:** P1-T04

## Objective

Provide deterministic, obviously synthetic fixtures that exercise every Phase 1 authorization boundary.

## Required fixtures

- Clinic A and Clinic B
- One read-only admin for Clinic A
- At least one staff and clinician account in each clinic
- One patient-linked account in Clinic A
- At least two patients in Clinic A and one in Clinic B
- Staff and clinician-owned sections
- Internal and patient-facing entries
- One entry for each required AI-scribed type with `author_role = system`
- Source records for manual and AI entries
- At least one internal comment
- Initial immutable versions and audit metadata

## Rules

- Use unmistakably fictional names and identifiers.
- Make the seed idempotent or document reset-before-seed behavior.
- Do not commit usable hosted-user passwords; use local placeholders or a setup script reading environment variables.
- Include data that proves cross-clinic denial, not only happy paths.

## Acceptance criteria

- [ ] Reset and seed produce the same logical dataset.
- [ ] Every role required by the brief is represented.
- [ ] Both allowed and denied test cases have fixtures.
- [ ] No real person or patient data is present.
- [ ] AI entries have correct types, system authorship, and provenance.

## Evidence

- `supabase/seed.sql` or documented seed command
- Fixture inventory
- Repeat seed/reset output
