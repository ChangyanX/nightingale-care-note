# Nightingale Care Note

[![Micro-tests](https://github.com/ChangyanX/nightingale-care-note/actions/workflows/micro-tests.yml/badge.svg?branch=main)](https://github.com/ChangyanX/nightingale-care-note/actions/workflows/micro-tests.yml?query=branch%3Amain)

A provenance-first longitudinal Care Note for role-based clinical collaboration, AI-scribed timelines, revision history, and glanceable patient insights.

## Architecture

- `apps/web`: Next.js and TypeScript frontend
- `services/backend`: FastAPI orchestration API and durable AI-scribe worker
- `supabase`: PostgreSQL migrations, Row-Level Security policies, and synthetic seed data
- `packages/design-tokens`: shared web design tokens
- `containers` and `.devcontainer`: reproducible container/development environments
- `docs`: blueprint, phase plans, requirements traceability, and submission checklist

The application is a modular monolith. Web, API, and worker processes are independently runnable but share one domain model and one PostgreSQL database.

Clinical data follows `browser → FastAPI → Supabase`. The browser uses the
Supabase publishable client only for Auth session lifecycle and RLS-authorized
Realtime invalidation; it does not call tables, database RPCs, Storage, or Edge
Functions directly. Run `npm --prefix apps/web run check:supabase-boundary` to
verify this constraint.

## Prerequisites

- Node.js 20.9 or newer
- pnpm 11
- Python 3.12
- uv
- Docker Desktop for the local Supabase stack

## Quick start

For the disposable local stack, the committed template contains localhost
defaults. Create the ignored backend and browser environment files before
starting the services:

```bash
cp .env.example .env
grep '^NEXT_PUBLIC_' .env.example > apps/web/.env.local
make install
make db-start
make db-reset
make dev-api
make dev-web
# After configuring the worker-only service-role and LLM keys:
make dev-worker
```

If `pnpm exec supabase status -o env` reports values different from the
template, update the corresponding Supabase URL and publishable-key entries in
both files. Next.js reads `apps/web/.env.local`; it does not load the root
`.env`.

For a hosted environment, obtain and enter values as follows:

| Value | Local file | Obtain from | Required when |
|---|---|---|---|
| `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` | `.env` | Supabase project API settings | Running the API |
| `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | `apps/web/.env.local` | Same browser-safe Supabase URL and publishable key | Running the web app |
| `NEXT_PUBLIC_API_URL` | `apps/web/.env.local` | URL where FastAPI is deployed | Web app calls a non-local API |
| `SUPABASE_SERVICE_ROLE_KEY` | `.env` or a worker secret store | Supabase project API settings | Controlled setup or worker jobs only; otherwise leave empty |
| `DATABASE_URL` | `.env` or a migration secret store | Supabase database connection settings | Direct database access only |
| `LLM_API_KEY` | `.env` or a worker secret store | Groq API Keys | Genuine AI calls only |

Record variable names and where to obtain them, but never record real keys,
passwords, connection strings, or tokens in this README, `.env.example`, Git,
issues, screenshots, or chat. Keep real values only in ignored environment
files, deployment secret stores, or a password manager. See
[Credentials and Access](docs/credentials-and-access.md) for the full boundary.

The web application runs at `http://localhost:3000`; the API runs at `http://localhost:8000`; API documentation is available at `http://localhost:8000/docs`. The conventional clinic sign-in is `/sign-in`. Synthetic persona shortcuts are deliberately isolated to `/demo`; selecting a persona fills its email but authentication still establishes the server-authorized role and clinic scope.

Alternatively, open the repository in a Dev Container or build the isolated
services with `docker compose build`. Compose never supplies secrets; it reads
an ignored `.env` only for the backend service.

Local synthetic accounts use the password `NightingaleDemo2026!` and the `@nightingale.local` email addresses declared in `supabase/seed.sql`. These credentials are for the disposable local stack only; do not reuse them in a hosted project.

| Demo role | Clinic A | Clinic B |
|---|---|---|
| Admin | `admin.a@nightingale.local` | — |
| Staff | `staff.a@nightingale.local` | `staff.b@nightingale.local` |
| Clinician | `clinician.a@nightingale.local` | `clinician.b@nightingale.local` |
| Patient | `patient.a@nightingale.local`, `patient.a2@nightingale.local`, `patient.a3@nightingale.local` | `patient.b@nightingale.local`, `patient.b2@nightingale.local` |

Every identity and care record is fictional. Staff, clinicians, and admins land
on the clinic patient list; patients land on their own `/patient` dashboard and
are explicitly denied the patient-list API.

Hosted demo identities use generated passwords and are seeded only after an
explicit project-reference check; see the hosted section of
[docs/supabase-setup.md](docs/supabase-setup.md).

## Inspect the running system

Run the database, API, worker, and web application in separate terminals:

```bash
make db-start
make dev-api
make dev-web
# In the fourth terminal after configuring worker-only secrets:
make dev-worker
```

For local development, obtain the disposable service-role value from
`pnpm exec supabase status -o env` and place it only in the ignored root `.env`
as `SUPABASE_SERVICE_ROLE_KEY`; never copy the command output into Git or a
shared message. Add the Groq key there as `LLM_API_KEY`. Hosted deployments use
their secret store rather than committed files.

| Surface | Local address | Purpose |
|---|---|---|
| Web application | [http://localhost:3000/sign-in](http://localhost:3000/sign-in) | Production-style clinic sign-in without persona shortcuts |
| Synthetic demo access | [http://localhost:3000/demo](http://localhost:3000/demo) | Choose a synthetic persona, then authenticate as that server-authorized account |
| Swagger UI | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Browse and execute API requests |
| ReDoc | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Read-only API reference |
| OpenAPI document | [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | Import into Postman, Insomnia, or another client |
| API health check | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Confirm FastAPI is running |
| Local Supabase Studio | [http://127.0.0.1:54323](http://127.0.0.1:54323) | Inspect local tables, Auth users, storage, and SQL |
| Local Supabase API | [http://127.0.0.1:54321](http://127.0.0.1:54321) | Local Auth, Data API, Realtime, and Storage endpoint |

`GET /` on port 8000 intentionally returns `404`; the API does not serve a
homepage. Use `/docs` or `/health` instead. A browser request for
`/favicon.ico` may also return `404` and is harmless.

### Test authenticated APIs in Swagger

`GET /health` needs no authorization. The patient, timeline, Glance, task, and
mutation endpoints require a short-lived Supabase user access token:

1. Sign in through the web application with a synthetic demo identity.
2. Obtain that session's `access_token` from the Supabase Auth response for the
   local development session.
3. In Swagger, select **Authorize** and paste the access token only. Swagger
   adds the `Bearer` prefix.
4. Execute `/me` first to verify the identity and clinic memberships, then test
   `/patients` and the patient-specific endpoints. Phase 4 job submission/status
   operations appear under Swagger's **AI scribe jobs** tag. The live-session
   endpoint accepts synthetic interaction text and returns sanitized job status;
   status endpoints never return a transcript or provider response.

For the disposable local stack only, request a token directly from Supabase
Auth using the local publishable key printed by `pnpm exec supabase status`:

```bash
curl --request POST \
  'http://127.0.0.1:54321/auth/v1/token?grant_type=password' \
  --header 'apikey: <local-publishable-key>' \
  --header 'content-type: application/json' \
  --data '{"email":"staff.a@nightingale.local","password":"NightingaleDemo2026!"}'
```

Copy only the response's `access_token` into Swagger. Do not adapt this command
with a hosted password in shared shell history.

Do not paste the Supabase publishable key, service-role key, refresh token, or
database password into Swagger. Do not place an access token in a URL, Git
file, screenshot, or shared terminal output. The token is intentionally
short-lived and should expire normally.

## Inspect and access the database

### Local Supabase

Start the local stack and inspect its connection information:

```bash
make db-start
pnpm exec supabase status
```

The versioned local ports are defined in `supabase/config.toml`:

- PostgreSQL: `127.0.0.1:54322`
- Supabase Studio: `http://127.0.0.1:54323`
- Supabase API/Auth/Realtime: `http://127.0.0.1:54321`

Use Studio for convenient read-only inspection, viewing Auth users, and
running temporary development queries. With PostgreSQL's `psql` client
installed, connect to the disposable local database using the versioned local
connection:

```bash
psql 'postgresql://postgres:postgres@127.0.0.1:54322/postgres'
```

Resetting the disposable local database applies every migration and reloads
the synthetic seed:

```bash
make db-reset
```

`db-reset` destroys local database contents. Do not run it against a hosted or
persistent environment. Schema and policy changes belong in
`supabase/migrations`; do not rely on unrecorded Studio edits.

### Hosted Supabase

Open the project in the [Supabase dashboard](https://supabase.com/dashboard)
to inspect the Table Editor, SQL Editor, Authentication users, Storage, logs,
and project settings. For repository-managed migrations:

```bash
pnpm exec supabase login
pnpm exec supabase link --project-ref <project-ref>
pnpm exec supabase migration list
pnpm exec supabase db push
```

The dashboard's **Connect** panel supplies hosted PostgreSQL connection
strings when direct tooling is necessary. Store such a connection string only
in the ignored root `.env` or a deployment secret store as `DATABASE_URL`.
Never expose it to `apps/web`, a `NEXT_PUBLIC_*` variable, Swagger, or Git.

Dashboard SQL and direct PostgreSQL access are privileged and may bypass the
application's normal RLS user context. Use caller-authenticated API requests
and the live RLS tests—not a successful dashboard query—as authorization
evidence.

For key placement, hosted seeding, rotation, and the complete caller-token
flow, see [Supabase setup](docs/supabase-setup.md) and
[Credentials and access](docs/credentials-and-access.md).

## Validation

```bash
make lint
make typecheck
make test
make generate-api
pnpm test:visual
```

`make generate-api` exports FastAPI OpenAPI and regenerates the committed
TypeScript `paths` contract used by the generated API client. Visual regression
runs desktop/mobile Chromium snapshots plus keyboard navigation. Install local
hooks with `pre-commit install` if desired; every hook check is also runnable
directly.

For a non-strict inventory of release evidence and open gates:

```bash
make release-status
```

Before submission, run the strict aggregate check from a clean final commit:

```bash
make release-check
```

The strict command intentionally fails while a required test/artifact is
missing, a tracked credential pattern is detected, or the working tree is dirty.
Current gate state is documented in
[docs/release-status.md](docs/release-status.md).

For a reproducible warm-path Top Card benchmark, start the API, export or paste
a short-lived staff/clinician token without placing it in command arguments,
then run:

```bash
make benchmark-glance PATIENT_ID=40000000-0000-0000-0000-000000000001
```

The command performs 10 warm-ups and 120 sequential measured requests, reports
errors plus P50/P95/P99, and enforces the 300 ms P95 target. The automated suite
also has a 120-request in-process approximation; only the script includes real
network, authentication, Supabase Data API, and RLS overhead.

### Opt-in genuine AI smoke test

Phase 4 uses Groq's free plan with `openai/gpt-oss-20b`. Create a Groq API key,
enable Zero Data Retention in Groq Data Controls when available, and put the key
only in the Git-ignored root `.env` as `LLM_API_KEY`. Do not paste it into
Swagger, browser configuration, Git, chat, or terminal arguments.

Run one genuine call over the committed synthetic transcript:

```bash
make smoke-llm
make smoke-llm-nurse
make smoke-llm-patient
```

The commands perform deterministic redaction before invoking Groq strict JSON
schema mode. Output contains only provider/model/request/token/count metadata
and never prints source or generated clinical text. Smoke responses are not
persisted. Durable jobs use the worker's service-role backend and the atomic
`complete_ai_scribe_job` RPC to create one internal system entry, its immutable
first version, exact-span suggested highlights, safe audit metadata, and the
completed job link in one transaction.

For a fully local second adapter, set `LLM_PROVIDER=ollama`, point
`LLM_BASE_URL` at the loopback Ollama OpenAI-compatible endpoint, and choose a
locally installed model. Provider facts and runtime evidence are documented in
[Provider latency and cost](docs/provider-latency-and-cost.md).

### Complete live AI timeline flow

Apply migrations through `202608280008`, configure the worker-only
`SUPABASE_SERVICE_ROLE_KEY` and `LLM_API_KEY`, and keep `make dev-worker`
running alongside the API and web app. The worker command continuously claims
durable jobs; `make worker-once` processes at most one queued job for debugging.

- A clinician opens a patient, selects **Generate AI summary**, enters or loads
  a synthetic doctor-consult example, and submits. Staff have the equivalent
  nurse-consult path. The source note and job are created atomically.
- A patient uses **Chat with AI** to submit a non-emergency question. The
  patient sees only queued/processing/completed status; the generated raw AI
  summary remains internal and appears live in authorized clinic timelines.
- Admins can monitor job status and generated timeline entries but remain
  read-only and cannot trigger clinical generation.
- Realtime invalidation refreshes clinic timelines when the worker persists the
  system-authored entry, version, highlights, audit metadata, and completed job
  link in one database transaction.

See [Live AI timeline flow](docs/live-ai-timeline-flow.md) for the process,
privacy boundary, failure behavior, and two-session demo steps.

If jobs remain queued, confirm `make dev-worker` is running. The status panel
polls active jobs every two seconds and also subscribes to `ai_jobs` and
`ai_job_events`; it shows the safe failure code when a job stops. A local 403
from `claim_ai_scribe_job` or `complete_ai_scribe_job` means the worker grant
migrations through `202608280008` have not been applied—run
`pnpm exec supabase db push --local`, then restart the worker.

If the UI says a job was **not queued**, first confirm `make dev-api` is running
and inspect the sanitized reason shown beside the generator. Authorization or
validation errors come from the API; a connection failure means the browser
could not confirm the response from `NEXT_PUBLIC_API_URL`. Retrying the
unchanged form reuses the same idempotency key, so even if the server accepted
an interrupted request it cannot create a duplicate job. Once a job appears in
the status panel, use `make worker-once` or `make dev-worker` to diagnose
processing separately.

## Security boundaries

### Where redaction happens

All repository data is synthetic. Even so, every LLM-bound text path is
redacted inside the backend before a provider can receive it:

1. `services/backend/app/worker/scribe.py` loads the source record and calls
   `redact_for_llm(...)` before `provider.generate(...)`.
2. `services/backend/app/domain/redaction/service.py` normalizes the text,
   replaces configured names plus supported names, IC/ID numbers, phone
   numbers, email addresses, dates of birth, addresses, locations, and
   organization identifiers, and then verifies that supported patterns no
   longer remain.
3. The redactor returns a `VerifiedRedaction` value. The provider interface in
   `services/backend/app/infrastructure/llm/base.py` accepts that verified type,
   not a raw string. Groq, Ollama, and fake adapters implement this interface.
4. Empty input or residual supported identifiers fail closed. Worker logs and
   stored errors contain job IDs, counts, model/request metadata, and sanitized
   error codes only; they do not contain prompts or note bodies.

This deterministic guard is prototype protection, not a claim of production-
grade de-identification. Tests are in
`services/backend/tests/test_redaction.py`,
`services/backend/tests/test_scribe_worker.py`, and provider contract tests.
Run the focused checks with:

```bash
cd services/backend
uv run pytest tests/test_redaction.py tests/test_scribe_worker.py
```

### How RBAC is enforced

Authorization is enforced at the server and database layers, not by hidden UI
controls:

1. `services/backend/app/auth.py` validates the bearer token with Supabase Auth
   and creates the request's authenticated user context.
2. `services/backend/app/gateway.py` forwards that same caller JWT to the
   Supabase Data API. Normal user routes never substitute the service-role key,
   so PostgreSQL evaluates every query as the signed-in user.
3. `supabase/migrations/202608260001_foundation.sql` enables RLS on exposed
   clinical tables. Its `has_clinic_role(...)` and `is_linked_patient(...)`
   helpers enforce clinic membership and patient ownership. Separate policies
   prevent staff from writing clinician entries/sections and clinicians from
   writing staff-owned content; admins have oversight without clinical-write
   authority.
4. Patient reads are allowlisted to linked, patient-facing summaries,
   instructions, and their own patient insights. Patients have no comments
   policy and cannot read raw AI-scribed entries, internal versions, audit
   events, or restricted provenance targets. Dedicated patient endpoints and
   reduced response schemas provide an additional API boundary.
5. Later migrations preserve the same boundary for collaboration/provenance,
   revision/revert operations, optional portal data, and private consult
   recordings. Privileged service credentials are confined to worker/setup
   configuration and are never exposed to browser code.

The always-on RBAC tests inspect the complete policy contract; optional live
tests exercise the policies against a migrated Supabase instance with real
short-lived synthetic-user tokens. Run the focused always-on checks with:

```bash
cd services/backend
uv run pytest tests/test_rbac_scope.py tests/test_patient_read_api.py
```

See [Supabase setup](docs/supabase-setup.md) for the environment variables that
enable the live RLS integration cases. Deployed services use TLS; PostgreSQL
and private object storage use the selected provider's encryption-at-rest
controls.

See [the build phases](docs/README.md), [Phase 1 tasks](docs/phase-1/README.md),
the [Phase 1–4 optional-deliverables audit](docs/phase-1-4-optional-deliverables.md),
and [Phase 4 AI task breakdown](docs/phase-4/README.md) for the implementation plan.

Role routing, account/session behavior, the non-negotiable patient-safe DTO/RLS
boundary, lightweight portal trade-offs, and both demo flows are documented in
[Role portals and privacy](docs/role-portals-and-privacy.md).

Supabase local and hosted setup is documented in [docs/supabase-setup.md](docs/supabase-setup.md). Credential ownership, local file placement, application token flow, deployment secrets, and rotation are documented in [docs/credentials-and-access.md](docs/credentials-and-access.md).
