PNPM ?= pnpm
UV ?= uv

.PHONY: install dev-web dev-api test test-api lint typecheck db-start db-stop db-reset seed-hosted smoke-llm release-status release-check

install:
	$(PNPM) install
	cd services/backend && $(UV) sync --dev

dev-web:
	$(PNPM) dev:web

dev-api:
	cd services/backend && $(UV) run uvicorn app.main:app --reload --port 8000

test: test-api typecheck

test-api:
	cd services/backend && $(UV) run pytest

lint:
	$(PNPM) lint:web
	cd services/backend && $(UV) run ruff check .

typecheck:
	$(PNPM) typecheck:web
	cd services/backend && $(UV) run mypy app

db-start:
	pnpm exec supabase start

db-stop:
	pnpm exec supabase stop

db-reset:
	pnpm exec supabase db reset

seed-hosted:
	@test -n "$(PROJECT_REF)" || (echo "Set PROJECT_REF to the hosted Supabase project reference" && exit 1)
	cd services/backend && $(UV) run python -m scripts.seed_hosted --project-ref "$(PROJECT_REF)"

smoke-llm:
	cd services/backend && $(UV) run python -m scripts.run_groq_smoke

release-status:
	cd services/backend && $(UV) run python -m scripts.release_audit

release-check: lint typecheck test-api
	cd services/backend && $(UV) run python -m scripts.release_audit --strict
