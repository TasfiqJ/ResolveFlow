# ResolveFlow Replay

ResolveFlow Replay is a deployment gate for enterprise agents.

This Stage 01 foundation demonstrates one clearly labeled synthetic payments incident moving
through web intake, deterministic context enrichment, a fixture-backed cited result, an inert
action proposal, and a chronological public trace. The public page is snapshot-first: it needs no
Cohere key, database, Slack workspace, or Jira site.

Current status: foundation vertical slice. Retrieval, the complete bounded agent/verifier, real
Slack/Jira adapters, Replay evaluation, and release gates belong to later milestones and are not
claimed here.

## Snapshot quick start

Prerequisites: Node.js 24, pnpm 10, Python 3.10+ and uv.

```bash
make bootstrap
make snapshot-hero
pnpm --dir apps/web dev
```

Open `http://localhost:3000`. The UI says **Recorded fixture** and **Slack-style simulation** so
its provenance is unambiguous.

## Full local development

Docker Desktop or Docker Engine with Compose is required.

```bash
cp .env.example .env
docker compose up --build
```

- Web: `http://localhost:3000`
- API documentation: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/health/live`
- Readiness: `http://localhost:8000/health/ready`
- Version: `http://localhost:8000/version`

Apply the database migration from the host after the database is healthy:

```bash
uv run alembic upgrade head
```

The worker is a deliberately idle Stage 01 runtime skeleton. Durable leases and connector
dispatch arrive in their named milestone; it performs no external write.

## Verification

```bash
scripts/verify.sh
```

The verifier runs source-integrity checks, locked setup validation, Python and web lint/types,
unit/integration tests, reversible PostgreSQL migration checks, static export, and a basic browser
snapshot smoke. It never calls Cohere, Slack, Jira, or a paid service.

## Fixture and interfaces

- Canonical truth: `data/truths/hero-payments-001.json`
- Synthetic sources: `data/artifacts/`
- Recorded snapshot: `data/published/hero-foundation.json`
- Shared Resolve path: `python/resolveflow/orchestrator.py`
- Future boundaries: `python/resolveflow/agent/ports.py`

Synthetic data is not customer evidence. The cited result is a deterministic recorded fixture,
not a live model result. Human review, provider performance, cost, integration success, and a
release verdict have not been measured.

