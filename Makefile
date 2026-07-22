.PHONY: bootstrap dev seed-demo lint typecheck test-unit test-integration test-contract test-security test-replay test replay-smoke snapshot-hero evaluate-candidate report review-template review-analysis e2e preflight verify

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
	uv run resolveflow-replay dry-run --manifest data/manifests/replay-role-downgrade-001.yaml
	uv run resolveflow-replay smoke --manifest data/manifests/replay-role-downgrade-001.yaml
	uv run resolveflow-evaluation negative-gate --manifest data/manifests/replay-role-downgrade-001.yaml

snapshot-hero:
	uv run resolveflow-snapshot

evaluate-candidate:
	@test -n "$(CANDIDATE_BUILD)" -a -n "$(BASELINE_BUILD)" -a -n "$(DATASET_VERSION)" -a -n "$(MANIFEST_LOCK_HASH)" || { echo "CANDIDATE_BUILD, BASELINE_BUILD, DATASET_VERSION, and MANIFEST_LOCK_HASH are required" >&2; exit 2; }
	uv run resolveflow-evaluation evaluate --candidate "$(CANDIDATE_BUILD)" --baseline "$(BASELINE_BUILD)" --dataset "$(DATASET_VERSION)" --lock "$(MANIFEST_LOCK_HASH)" --manifest data/manifests/replay-role-downgrade-001.yaml --output eval/results/replay-development-result.json

report:
	@test -n "$(RESULT_BUNDLE)" || { echo "RESULT_BUNDLE is required" >&2; exit 2; }
	uv run resolveflow-evaluation report --bundle "$(RESULT_BUNDLE)" --output eval/reports

review-template:
	uv run resolveflow-review template --output /tmp/resolveflow-review-template.csv

review-analysis:
	@test -n "$(REVIEW_EXPORT)" || { echo "REVIEW_EXPORT is required" >&2; exit 2; }
	uv run resolveflow-review analyze --input "$(REVIEW_EXPORT)" --output /tmp/resolveflow-review-analysis.json

e2e: snapshot-hero
	pnpm --dir apps/web build
	node tests/browser/snapshot-smoke.mjs

preflight:
	uv run resolveflow-preflight

verify:
	./scripts/verify.sh
