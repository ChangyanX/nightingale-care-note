PNPM ?= pnpm
UV ?= uv

.PHONY: install dev-web dev-api dev-worker worker-once test test-api lint typecheck generate-api db-start db-stop db-reset seed-hosted smoke-llm benchmark-glance release-status release-check

install:
	$(PNPM) install
	cd services/backend && $(UV) sync --dev

dev-web:
	$(PNPM) dev:web

dev-api:
	cd services/backend && $(UV) run uvicorn app.main:app --reload --port 8000

dev-worker:
	cd services/backend && $(UV) run python -m scripts.run_scribe_worker

worker-once:
	cd services/backend && $(UV) run python -m scripts.run_scribe_worker --once

test: test-api typecheck

test-api:
	cd services/backend && $(UV) run pytest

lint:
	$(PNPM) lint:web
	cd services/backend && $(UV) run ruff check .

typecheck:
	$(PNPM) typecheck:web
	cd services/backend && $(UV) run mypy app

generate-api:
	$(PNPM) generate:api

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

smoke-llm-nurse:
	cd services/backend && $(UV) run python -m scripts.run_groq_smoke --interaction-type nurse_consult

smoke-llm-patient:
	cd services/backend && $(UV) run python -m scripts.run_groq_smoke --interaction-type ai_patient_session

benchmark-glance:
	@test -n "$(PATIENT_ID)" || (echo "Set PATIENT_ID to a synthetic demo patient UUID" && exit 1)
	cd services/backend && $(UV) run python -m scripts.benchmark_glance --patient-id "$(PATIENT_ID)" --enforce-target

release-status:
	cd services/backend && $(UV) run python -m scripts.release_audit

release-check: lint typecheck test-api
	cd services/backend && $(UV) run python -m scripts.release_audit --strict
