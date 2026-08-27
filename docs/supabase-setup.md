# Supabase Setup

The credential ownership and request flow are documented in
[Credentials and Access](credentials-and-access.md). Read that guide before
copying any hosted key into a local or deployment environment.

## Local development

Local Supabase requires Docker Desktop.

```bash
pnpm install
pnpm exec supabase start
pnpm exec supabase db reset
```

`db reset` applies all files in `supabase/migrations` and then runs `supabase/seed.sql`. The seed is local-only and creates fictional users with the password `NightingaleDemo2026!`.

Copy the backend values printed by `supabase start` into the root `.env`. Copy
the browser-safe `NEXT_PUBLIC_*` values into `apps/web/.env.local`; Next.js does
not automatically load the repository-root `.env`. Never expose or commit the
service-role key.

## Hosted development project

1. Create a development project in the Supabase dashboard.
2. Choose a region near the API deployment region.
3. Authenticate and link the repository. `supabase login` stores the personal
   access token in the CLI's own user configuration; do not add it to `.env`:

   ```bash
   pnpm exec supabase login
   pnpm exec supabase link --project-ref <project-ref>
   pnpm exec supabase db push
   ```

4. Put the service-role key temporarily in the root `.env`, run the controlled
   hosted seed, and then remove that value from the normal API environment:

   ```bash
   make seed-hosted PROJECT_REF=<project-ref>
   ```

   The command creates or updates only the six named synthetic demo identities,
   inserts their matching profiles, memberships, and two-clinic demonstration
   records, and writes their generated passwords to `.env.hosted-demo` with
   owner-only (`0600`) permissions. The explicit project-reference argument
   prevents accidentally seeding a different project.
5. Back up `.env.hosted-demo` in your password manager if another session or
   developer needs the credentials. Never run the local `supabase/seed.sql`
   unchanged against a persistent hosted project.
6. Create a root `.env` from `.env.example` for FastAPI and controlled setup
   scripts. Create `apps/web/.env.local` with only the two `NEXT_PUBLIC_*`
   values for local Next.js development.
7. Store the hosted URL and publishable key in each deployment environment as
   described in [Credentials and Access](credentials-and-access.md).
9. Store the service-role key only in the worker's or setup job's secret
   environment; the web application and normal API request path do not use it.

## Authorization request path

1. The browser authenticates with Supabase Auth.
2. It sends the access token to FastAPI.
3. FastAPI verifies the token through Supabase Auth.
4. FastAPI forwards the same caller token to the Supabase Data API.
5. PostgreSQL RLS evaluates `auth.uid()` for the real caller.

The `create_manual_entry` and `update_entry` database functions are security-invoker functions. Their entry, version, and audit mutations remain subject to RLS and occur in one database transaction.

## Live RLS verification

The always-running tests inspect the policy contract. Full live tests require a migrated and seeded Supabase environment plus short-lived user tokens:

```bash
export NIGHTINGALE_RUN_RLS_INTEGRATION=1
export NIGHTINGALE_TEST_STAFF_A_TOKEN='<token>'
export NIGHTINGALE_TEST_CLINICIAN_A_TOKEN='<token>'
export NIGHTINGALE_TEST_PATIENT_A_TOKEN='<token>'
export NIGHTINGALE_TEST_ADMIN_A_TOKEN='<token>'

cd services/backend
uv run pytest tests/test_rbac_scope.py
```

The tokens must remain local and expire normally. Do not place populated values in `.env.example`, test fixtures, screenshots, or Git history.

## Transport and storage security

- Hosted Supabase endpoints use TLS.
- The deployed web and API endpoints must redirect HTTP to HTTPS.
- LLM traffic must use HTTPS.
- Supabase provides provider-managed encryption at rest for PostgreSQL and private object storage; the technical brief records the selected plan and platform guarantees.
- The `consult-recordings` bucket is private. Phase 1 only reserves it; voice capture remains outside the current scope.
