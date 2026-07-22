.PHONY: bootstrap dev seed-demo lint typecheck test-unit test-integration test-contract test-security test-replay test replay-smoke snapshot-hero evaluate-candidate report e2e preflight verify

export UV_CACHE_DIR ?= /tmp/resolveflow-uv-cache
export UV_LINK_MODE ?= copy
export PNPM_HOME ?= /tmp/resolveflow-pnpm

bootstrap:
	uv sync --frozen
	pnpm install --frozen-lockfile --store-dir /tmp/resolveflow-pnpm-store

dev:
	docker compose up --build

seed-demo:
	uv run resolveflow-seed

lint:
	uv run ruff check python tests
	uv run ruff format --check python tests
	pnpm --dir apps/web lint
	pnpm --dir apps/web format:check

typecheck:
	uv run mypy python/resolveflow
	pnpm --dir apps/web typecheck

test-unit:
	uv run pytest -q tests/unit
	pnpm --dir apps/web test

test-integration:
	uv run pytest -q tests/integration

test-contract:
	uv run pytest -q tests/contract

test-security:
	uv run pytest -q tests/security

test-replay:
	uv run pytest -q tests/replay

test: test-unit test-integration test-contract test-security

replay-smoke:
	uv run resolveflow-snapshot

snapshot-hero:
	uv run resolveflow-snapshot

evaluate-candidate:
	@echo "Candidate evaluation is intentionally unavailable before Milestone 5."; exit 2

report:
	@echo "Evaluation reporting is intentionally unavailable before Milestone 5."; exit 2

e2e: snapshot-hero
	pnpm --dir apps/web build
	node tests/browser/snapshot-smoke.mjs

preflight:
	uv run resolveflow-preflight

verify:
	./scripts/verify.sh
