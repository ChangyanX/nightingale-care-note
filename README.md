# Nightingale Care Note

[![Micro-tests](https://github.com/ChangyanX/nightingale-care-note/actions/workflows/micro-tests.yml/badge.svg?branch=main)](https://github.com/ChangyanX/nightingale-care-note/actions/workflows/micro-tests.yml?query=branch%3Amain)

A provenance-first longitudinal Care Note for role-based clinical collaboration, AI-scribed timelines, revision history, and glanceable patient insights.

## Architecture

- `apps/web`: Next.js and TypeScript frontend
- `services/backend`: FastAPI orchestration API and later background worker
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

```bash
cp .env.example .env
make install
make db-start
make db-reset
make dev-api
make dev-web
```

The web application runs at `http://localhost:3000`; the API runs at `http://localhost:8000`; API documentation is available at `http://localhost:8000/docs`.

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

Run the database, API, and web application in separate terminals:

```bash
make db-start
make dev-api
make dev-web
```

| Surface | Local address | Purpose |
|---|---|---|
| Web application | [http://localhost:3000](http://localhost:3000) | Sign in and use the Care Note UI |
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
   operations appear under Swagger's **AI scribe jobs** tag; they enqueue work
   and never accept or return a raw transcript.

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
persisted; the durable worker path separately records job progress and
sanitized provider usage metadata.

For a fully local second adapter, set `LLM_PROVIDER=ollama`, point
`LLM_BASE_URL` at the loopback Ollama OpenAI-compatible endpoint, and choose a
locally installed model. Provider facts and runtime evidence are documented in
[Provider latency and cost](docs/provider-latency-and-cost.md).

## Security boundaries

Normal API requests forward the caller's Supabase JWT to the Data API so PostgreSQL RLS evaluates the real caller. The service-role credential is reserved for the internal worker and administrative setup. Patient-facing queries use dedicated endpoints, reduced response schemas, and RLS policies; they never fetch internal comments or raw AI-scribed notes.

All data in this repository is synthetic. Every LLM-bound path must pass through
the verified redaction guard in `services/backend/app/domain/redaction`; provider
adapters must not accept raw text. The deterministic guard covers configured
names and common labelled identifiers, but it is prototype protection rather
than production-grade de-identification. Deployed services use TLS; PostgreSQL
and private object storage use the selected provider's encryption-at-rest controls.

See [the build phases](docs/README.md), [Phase 1 tasks](docs/phase-1/README.md),
the [Phase 1–4 optional-deliverables audit](docs/phase-1-4-optional-deliverables.md),
and [Phase 4 AI task breakdown](docs/phase-4/README.md) for the implementation plan.

Role routing, account/session behavior, the non-negotiable patient-safe DTO/RLS
boundary, lightweight portal trade-offs, and both demo flows are documented in
[Role portals and privacy](docs/role-portals-and-privacy.md).

Supabase local and hosted setup is documented in [docs/supabase-setup.md](docs/supabase-setup.md). Credential ownership, local file placement, application token flow, deployment secrets, and rotation are documented in [docs/credentials-and-access.md](docs/credentials-and-access.md).
