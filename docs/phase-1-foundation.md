# Phase 1 — Foundation

**Full-quality estimate:** 8-10 hours  
**16-hour critical-path allocation:** 3 hours  
**Goal:** Establish a runnable, secure skeleton before building patient-facing features.

## Description

Phase 1 creates the project boundaries that are expensive to retrofit: authentication, clinic isolation, role-based access control, database migrations, and deterministic synthetic data. At the end, the application does not need a polished patient page, but it must correctly decide who is allowed to read and change data.

## Required deliverables

- A clean repository layout with `apps/web`, `services/backend`, `supabase`, `docs`, and test folders.
- Next.js TypeScript frontend that starts locally.
- FastAPI Python backend with `/health` and authenticated `/me` endpoints.
- Supabase development project or documented local Supabase setup.
- Versioned migrations for `clinics`, `profiles`, `clinic_memberships`, `patients`, `source_records`, `care_notes`, `entries`, `note_sections`, `entry_versions`, `section_versions`, minimal `comments`, and `audit_events`.
- Row-Level Security enabled on every exposed application table.
- Server-side RBAC checks in FastAPI.
- Caller-scoped database access that preserves the authenticated JWT for RLS; service-role access is reserved for the worker and setup.
- Synthetic seed data for at least two clinics, each with users and patients.
- `.env.example`, `.gitignore`, README setup instructions, and no committed secrets.
- Documented TLS-in-transit and provider-managed encryption-at-rest controls for the selected hosted services.
- Passing `test_rbac_scope.py`.

## Optional deliverables

- Docker Compose for one-command local startup.
- CI workflow running frontend checks and backend tests.
- Local Supabase CLI development environment.
- Development-only role switcher backed by actual authenticated sessions.
- API contract generation and typed frontend API client.

## Implementation order

1. **Normalize repository layout.** Avoid a nested application directory within the Git root. Add ignore rules before installing dependencies.
2. **Scaffold applications.** Create the Next.js app and FastAPI package with format, lint, and test commands.
3. **Configure configuration.** Add `.env.example`; document which values belong to frontend, API, worker, and local development.
4. **Create the database project.** Configure Supabase Auth and write the first migration; do not rely on manual dashboard-only changes.
5. **Implement identity, tenancy, and provenance foundations.** Add clinic, profile, membership, patient, source, entry, section, minimal comment, version, and audit models.
6. **Implement role and visibility rules.** Create explicit RLS policies for read and write operations; add matching API authorization dependencies. Ordinary user requests run with the caller's JWT, not the service role.
7. **Seed deterministic synthetic data.** Include Clinic A and Clinic B, staff, clinicians, an admin, a patient user, and initial note entries.
8. **Build minimal APIs.** Implement `/health`, `/me`, patient list, patient detail, timeline read, entry creation, and entry update endpoints.
9. **Write and run RBAC tests.** Test direct API access and database policy boundaries before adding UI workflows.
10. **Document setup.** A new reviewer should be able to start services, seed data, and run tests from the README.

## Acceptance criteria

- [ ] A fresh clone can install dependencies using documented commands.
- [ ] The web app and API start locally without modifying source code.
- [ ] A health request returns a successful response.
- [ ] A valid user can retrieve their own authenticated identity and role.
- [ ] All seed data is synthetic and repeatable.
- [ ] Clinic A users cannot read or mutate Clinic B records.
- [ ] Staff can create staff-owned entries but cannot create or modify clinician-owned entries.
- [ ] Clinicians can create clinician-owned entries but cannot create or modify staff-owned entries.
- [ ] A patient can access only their own patient-facing resources.
- [ ] A patient cannot retrieve internal comments, internal notes, or raw AI-scribed content.
- [ ] Admin access remains limited to the admin's clinic.
- [ ] Admin is read-only for clinical content and can manage clinic membership.
- [ ] RLS protects tables independently of UI state.
- [ ] `test_rbac_scope.py` passes in one documented command.
- [ ] No service role key or LLM key is available to browser code.
- [ ] Normal API requests do not use service-role credentials to bypass RLS.
- [ ] Deployment documentation identifies TLS and encryption-at-rest responsibilities.

## Suggested artifacts

```text
apps/web/
services/backend/app/
services/backend/tests/test_rbac_scope.py
supabase/migrations/0001_foundation.sql
supabase/seed.sql
.env.example
README.md
```

## Time budget

| Work item | Estimate |
|---|---:|
| Repository and app scaffolding | 1-2 h |
| Supabase configuration and migrations | 2 h |
| RBAC and RLS policies | 2-3 h |
| Seed data and minimal APIs | 1-2 h |
| Tests, documentation, debugging | 2 h |

## Do not proceed until

The required RBAC tests are green. A fast visual prototype without enforced clinic and role boundaries will make the later work harder to trust and demonstrate.
