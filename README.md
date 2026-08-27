# Nightingale Care Note

A provenance-first longitudinal Care Note for role-based clinical collaboration, AI-scribed timelines, revision history, and glanceable patient insights.

## Architecture

- `apps/web`: Next.js and TypeScript frontend
- `services/backend`: FastAPI orchestration API and later background worker
- `supabase`: PostgreSQL migrations, Row-Level Security policies, and synthetic seed data
- `docs`: blueprint, phase plans, requirements traceability, and submission checklist

The application is a modular monolith. Web, API, and worker processes are independently runnable but share one domain model and one PostgreSQL database.

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

Local synthetic accounts use the password `NightingaleDemo2026!` and the `@nightingale.local` email addresses declared in `supabase/seed.sql`. These credentials are for the disposable local stack only; do not reuse them in a hosted project.

Hosted demo identities use generated passwords and are seeded only after an
explicit project-reference check; see the hosted section of
[docs/supabase-setup.md](docs/supabase-setup.md).

## Validation

```bash
make lint
make typecheck
make test
```

## Security boundaries

Normal API requests forward the caller's Supabase JWT to the Data API so PostgreSQL RLS evaluates the real caller. The service-role credential is reserved for the internal worker and administrative setup. Patient-facing queries use dedicated restricted views and never fetch internal comments or raw AI-scribed notes.

All data in this repository is synthetic. Every LLM-bound path must pass through the redaction gateway added in Phase 4. Deployed services use TLS; PostgreSQL and private object storage use the selected provider's encryption-at-rest controls.

See [the build phases](docs/README.md) and [Phase 1 tasks](docs/phase-1/README.md) for the implementation plan.

Supabase local and hosted setup is documented in [docs/supabase-setup.md](docs/supabase-setup.md). Credential ownership, local file placement, application token flow, deployment secrets, and rotation are documented in [docs/credentials-and-access.md](docs/credentials-and-access.md).
