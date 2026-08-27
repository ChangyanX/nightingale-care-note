# P1-T03 — Supabase Environment

**Status:** Repository and credential-flow documentation complete; hosted project validation pending
**Full estimate:** 1 hour  
**16-hour path:** 15 minutes  
**Dependencies:** P1-T01

## Objective

Make database, authentication, storage, and realtime configuration reproducible without relying on undocumented dashboard state.

## Required work

1. Create `supabase/config.toml` for local development.
2. Establish ordered SQL migration naming.
3. Document hosted-project creation and environment variables.
4. Configure email/password authentication for demo users.
5. Reserve a private `consult-recordings` bucket; actual voice capture remains out of scope.
6. Document that hosted web/API/database/storage/LLM traffic uses TLS and that Supabase provides encryption at rest.
7. Define how local migrations are linked and pushed to the hosted development project.
8. Document credential ownership, local/deployment placement, runtime token flow, and rotation without storing a live secret in Git.

## External/manual actions

- Sign in to Supabase.
- Create or select the hosted development project.
- Record the project URL and publishable key locally.
- Keep service-role and database credentials outside Git.

## Acceptance criteria

- [ ] Supabase configuration is versioned.
- [ ] A developer can apply migrations using documented commands.
- [ ] Hosted secrets are represented only by placeholders in `.env.example`.
- [ ] The private storage bucket and access-policy plan are documented.
- [ ] TLS and encryption-at-rest ownership are documented.

## Evidence

- `supabase/config.toml`
- Setup section in README
- `docs/credentials-and-access.md`
- Successful local status or hosted migration output
