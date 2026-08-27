# P1-T02 — Web and API Scaffolds

**Status:** Implemented and locally verified  
**Full estimate:** 1 hour  
**16-hour path:** 25 minutes  
**Dependencies:** P1-T01

## Objective

Create minimal typed applications that start independently and provide fast health checks without committing to Phase 2 UI details.

## Required work

### Web

1. Create a Next.js TypeScript application under `apps/web`.
2. Enable strict TypeScript and linting.
3. Add a minimal home page that identifies the project and API status boundary.
4. Add a frontend health route or deterministic render test.
5. Keep Supabase browser configuration isolated in `lib` and expose only publishable values.

### API

1. Create a Python package under `services/backend`.
2. Configure FastAPI, Pydantic settings, pytest, Ruff, and type checking.
3. Add `GET /health` returning a typed response.
4. Add consistent API error and request-ID handling without logging request bodies.
5. Add a unit test for `/health`.

## Optional work

- Generate a TypeScript client from OpenAPI.
- Add a shared design-token package.
- Add container files.

## Acceptance criteria

- [ ] Web app starts using the documented command.
- [ ] TypeScript strict checking succeeds.
- [ ] API starts using the documented command.
- [ ] `GET /health` returns HTTP 200 with a stable JSON shape.
- [ ] API test command discovers and passes the health test.
- [ ] Neither application requires a real secret merely to start its health surface.

## Evidence

- Web type-check/lint output
- Backend pytest/Ruff output
- Health response example
