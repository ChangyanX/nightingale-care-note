# P5-T06 — README, Attribution, and Reproducibility

**Status:** Partial
**Full estimate:** 0.75 hours
**16-hour path:** 20 minutes
**Dependencies:** P5-T02 through P5-T05

## Objective

Make the repository independently runnable and credit every external dependency,
model, design asset, and copied/adapted source appropriately.

## Required work, in order

1. Verify prerequisites and fresh-install commands.
2. Document local database reset, API/web/worker processes, Swagger, tests, and genuine-call opt-in.
3. Explain synthetic-data constraints, RLS boundary, redaction limitations, and worker secrets.
4. Add troubleshooting for Node runtime, Supabase/Docker, ports, and missing keys.
5. Create `ATTRIBUTION.txt` from direct dependencies and external assets/models.
6. Record names, versions, licenses, project URLs, and usage.
7. Check every Markdown link and documented command.
8. Reproduce setup in a clean clone or temporary worktree without copying local secrets.

## Must be done

- README never tells users to put secrets in `.env.example` or browser variables.
- The genuine model command is opt-in and safe when no key exists.
- Attribution includes Groq and `openai/gpt-oss-20b` plus their applicable terms/license.
- Generated output and user-authored code are distinguished from third-party assets.

## Optional

- CI badge.
- Troubleshooting screenshots without credentials.

## Acceptance criteria

- [ ] Fresh setup succeeds from committed instructions.
- [ ] API, web, worker, database, tests, and Swagger are documented.
- [ ] RBAC/redaction/synthetic limitations are clear.
- [ ] `ATTRIBUTION.txt` is complete and reviewed.
- [ ] Links and commands pass automated/manual checks.

## Done when

A reviewer can reproduce the project and understand third-party usage without contacting the author.
