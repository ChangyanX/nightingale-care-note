# P5-T03 — Security, Role, and Repository Audit

**Status:** Automated secret check implemented; manual/hosted checks pending
**Full estimate:** 0.75 hours
**16-hour path:** 25 minutes
**Dependencies:** P5-T02

## Objective

Verify role boundaries, synthetic-data discipline, clean logs, credential
placement, and repository hygiene before anything is shared or recorded.

## Required work, in order

1. Rotate any key ever placed in a tracked file, terminal output, or shared artifact.
2. Scan tracked files for provider keys, JWTs, populated secret assignments, and forbidden env files.
3. Verify `.gitignore` covers local env, hosted demo credentials, caches, recordings, and database artifacts.
4. Walk patient, staff, clinician, admin, and second-clinic identities against the hosted API.
5. Verify worker secrets are absent from browser and ordinary API configuration.
6. Inspect worker/API logs after success and failure paths.
7. Confirm all patient/sample content is synthetic and labelled.
8. Record TLS and encryption-at-rest responsibilities for each deployed provider.

## Must be done

- A detected secret is removed and rotated; deleting it alone is insufficient.
- Patient cannot receive raw AI entries, internal comments, jobs, highlights, or audit data.
- Admin cannot mutate clinical content.
- Cross-clinic reads and writes are denied.
- Logs contain identifiers/status codes only, not raw bodies or credentials.

## Optional

- Dependency vulnerability scan.
- Browser security-header report.

## Acceptance criteria

- [x] Tracked secret audit reports no current key-like value.
- [x] Worker-only keys are absent from ordinary API/browser configuration tests.
- [ ] Previously exposed Groq key is rotated.
- [ ] Hosted five-role walkthrough passes.
- [ ] Clean-log walkthrough passes with genuine provider success/failure.
- [ ] TLS and encryption-at-rest evidence is recorded for deployment.

## Done when

Sharing the repository, screenshots, logs, and demo cannot expose credentials or unauthorized data.
