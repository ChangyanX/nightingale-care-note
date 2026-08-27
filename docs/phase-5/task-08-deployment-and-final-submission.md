# P5-T08 — Deployment Verification and Handoff Preparation

**Status:** Pending
**Full estimate:** 1 hour
**16-hour path:** 15 minutes
**Dependencies:** P5-T01 through P5-T07

## Objective

Verify the exact deployed/reviewer experience, perform the final repository
audit, and prepare a local handoff package. The assistant must not submit or
upload artifacts, change repository visibility, or send email.

## Required work, in order

1. Deploy or prepare a complete local reviewer path and verify environment separation.
2. Apply migrations, seed synthetic demo accounts, and run hosted role/live checks.
3. Verify HTTPS/TLS for web, API, Supabase, storage, and Groq endpoints.
4. Run strict `make release-check` on the final commit.
5. Prepare a checklist for the user to confirm repository visibility/zip,
   technical brief, video, and README links.
6. Inspect `git status`, ignored secret files, history, license, and attribution.
7. Stop after reporting the verified artifacts and remaining user-only actions.


## Must be done

- No migration or seed command targets an unverified hosted project.
- Demo credentials are replaceable and shared only through an appropriate channel.
- Every link is tested in a signed-out/private browsing context.
- The final commit contains no generated secrets, local DB data, or real patient content.
- Repository visibility, uploads, submission, and email sending are exclusively
  user-controlled; the assistant performs none of these actions.

## Optional

- Public hosted demo if access can be safely restricted.
- Signed release tag/archive checksum.

## Acceptance criteria

- [ ] Final strict release check passes.
- [ ] Deployed/local reviewer flow works from documented instructions.
- [ ] Repository, PDF, video, and resume/contact deliverables are accessible.
- [ ] Final secret/synthetic-data/license audit passes.
- [ ] A user-facing handoff checklist identifies every remaining submission action.

## Done when

The user receives a verified handoff package and checklist while retaining sole
control of every external upload, visibility change, submission, and email.
