# Credentials and Access

This guide defines how a developer, browser, API, worker, migration command,
and deployed service access the hosted Supabase development project. No real
credential belongs in Git, screenshots, issue text, chat, or demo recordings.

## Credential map

| Actor | Credentials | Where to store them | Capability |
|---|---|---|---|
| Developer using Supabase CLI | Supabase personal access token and project reference | The CLI's user configuration after `supabase login`; project link in ignored `supabase/.temp` | Link the repository and push migrations |
| Browser / Next.js | Project URL and publishable key | `apps/web/.env.local` locally; frontend host environment in deployment | Start Auth requests and call public Supabase endpoints; cannot bypass RLS |
| FastAPI normal request path | Project URL and publishable key | Root `.env` locally; API host secret/environment settings in deployment | Verify a user's token and forward that same caller identity to the Data API |
| Signed-in user | Email/password at sign-in, then short-lived access token and refresh token | Password manager for the human; Supabase client session storage for tokens | Act only as that user; PostgreSQL RLS evaluates `auth.uid()` |
| Background worker / controlled setup job | Project URL and service-role key | Worker or one-off job secret store only | Perform explicitly trusted jobs that may bypass RLS |
| Direct database tooling, if needed | Hosted database connection string/password | Local secret manager or migration CI secret store only | Direct PostgreSQL access; never available to browser code |
| LLM worker | Groq API key | Worker secret store only | Call `openai/gpt-oss-20b` after verified redaction |

The publishable key identifies the Supabase project and is expected to appear
in browser code. It is not authorization by itself. The service-role key and
database password are privileged secrets and must never use a `NEXT_PUBLIC_`
name.

## Obtain hosted values

In the Supabase dashboard for the development project:

1. Copy the project URL and current publishable key from the project's API
   settings (the dashboard may label an older equivalent as the `anon` key).
2. Copy the service-role key only when configuring the internal worker or a
   controlled setup job. Do not reveal it in the browser or FastAPI's normal
   request environment.
3. Find the project reference in the project URL or project settings; use it
   with `supabase link`.
4. Obtain the database connection string only if a direct database operation
   cannot be performed with the linked CLI workflow.

Do not send these values through chat. Enter them directly in the local files
or deployment secret UI described below.

## Local files

Create the backend/setup environment from the committed template:

```bash
cp .env.example .env
```

Set these hosted values in the root `.env`:

```dotenv
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_PUBLISHABLE_KEY=<publishable-key>
SUPABASE_SERVICE_ROLE_KEY=<worker-or-setup-only>
DATABASE_URL=<optional-direct-connection-string>
```

FastAPI finds the root `.env` when run from the repository root or
`services/backend`. Keep `SUPABASE_SERVICE_ROLE_KEY` empty when running only
the normal API.

Next.js loads its local environment from the application directory, so create
`apps/web/.env.local` separately:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<publishable-key>
```

Only these browser-safe values belong in `apps/web/.env.local`. Both files are
ignored by Git. Confirm before committing:

```bash
git status --short
git check-ignore -v .env apps/web/.env.local
```

## Developer and application access flow

Link and migrate the development project without putting a personal access
token in the application environment:

```bash
pnpm exec supabase login
pnpm exec supabase link --project-ref <project-ref>
pnpm exec supabase db push
```

At runtime:

1. The user enters email and password into Supabase Auth through the browser.
2. Supabase returns a short-lived access token and a refresh token to the
   Supabase browser client.
3. The browser calls FastAPI with `Authorization: Bearer <access-token>`.
4. FastAPI verifies the access token with Supabase Auth and forwards the same
   token to the Supabase Data API.
5. PostgreSQL RLS evaluates `auth.uid()` and the user's memberships. The API
   cannot silently broaden the caller's permissions.

### Browser-to-database boundary

The browser has no direct clinical Data API, database RPC, Storage, or Edge
Function access. All patient, timeline, task, comment, highlight, AI-job, and
preference reads and mutations go through FastAPI.

The Supabase browser client is intentionally retained for two narrow purposes:

1. **Auth:** sign in, refresh the caller's short-lived session, and sign out.
2. **Realtime invalidation:** receive an RLS-authorized change signal and then
   refetch the resource through FastAPI. The application does not treat the
   Realtime row payload as its clinical data source.

The publishable key is designed to be public and is not a database password.
RLS still protects the Realtime subscription. The service-role key and direct
database connection string must never enter `NEXT_PUBLIC_*` configuration.

Run the enforced boundary check with:

```bash
npm --prefix apps/web run check:supabase-boundary
```

It rejects raw Supabase SDK imports and browser calls to `.from(...)`,
`.rpc(...)`, Storage, or Edge Functions. If the product later needs one of
those capabilities, add a FastAPI endpoint instead of weakening the check.

Do not manually copy an access token into ordinary application code. The
Supabase client obtains and refreshes it. Short-lived tokens are exported only
for the opt-in live RBAC test described in `supabase-setup.md`.

## Deployment placement

Configure the frontend host with:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

Configure the FastAPI host with:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `API_CORS_ORIGINS` set to the exact deployed frontend origin

Configure the internal worker separately with:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_PROVIDER`
- `LLM_BASE_URL`

For the selected free provider, create the key in the Groq Console, enable Zero
Data Retention in **Data Controls** when available, and set these values only in
the ignored root `.env` or worker deployment secrets:

```dotenv
LLM_PROVIDER=groq
LLM_API_KEY=<groq-key>
LLM_MODEL=openai/gpt-oss-20b
LLM_BASE_URL=https://api.groq.com/openai/v1
```

The ordinary FastAPI settings class does not load the service-role or LLM key.
Those fields live in the separately imported worker settings module so a normal
API process does not receive privileged worker configuration.

If the API and worker share one hosting service, keep them as separate process
definitions with separate environment-variable scopes. The frontend must
never receive worker secrets. Migration CI, if added, gets only the CLI token,
project reference, and database secret required for that job.

## Demo users

Local accounts in `supabase/seed.sql` use a known disposable password and must
never be copied unchanged to the hosted project. `make seed-hosted
PROJECT_REF=<project-ref>` generates unique 32-character passwords, creates or
updates only the named synthetic accounts, and stores their email/password
pairs in the Git-ignored `.env.hosted-demo` file with mode `0600`. Copy that
file's values into your password manager if they must survive the workstation;
do not paste them into chat. The setup records only the generated Auth UUID
relationships in application tables.

## Rotation and incident response

- If a publishable key is rotated, update both frontend and API environments
  and redeploy them.
- If the service-role key or database password may have leaked, rotate it
  immediately in Supabase, update only the worker/setup secret, and inspect
  audit logs.
- Revoke a CLI personal access token from the Supabase account settings when a
  machine or session should lose management access.
- Disable or reset a demo user's password through Supabase Auth when that
  identity should lose access.
- Never preserve an exposed secret by merely deleting a committed file; rotate
  the secret because Git history and logs may retain it.
