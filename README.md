# ResolveFlow Replay

ResolveFlow Replay is a deployment gate for enterprise agents.

The current credential-free build demonstrates one clearly labeled synthetic payments incident
moving through authorized hybrid retrieval, a bounded fixture-backed tool loop, claim-level
verification, exact approval controls, deterministic Replay, paired unsafe/guarded comparison,
and a hard-invariant-first release gate. The public page is snapshot-first: it needs no Cohere
key, database, Slack workspace, or Jira site.

Current status: Stage 06 public product and validation tooling. One actual deterministic development fixture
blocks unsafe-v0 with `NO_SHIP`; guarded-v1 receives `SHIP_WITH_LIMITS` because the draft
citation sample is below its minimum N. This is not a held-out, live-provider, human-reviewed, or
final release result. No external write is represented by the fixture.

## Snapshot quick start

Prerequisites: Node.js 24, pnpm 10, Python 3.10+ and uv.

```bash
make bootstrap
make snapshot-hero
pnpm --dir apps/web dev
```

Open `http://localhost:3000`. The UI says **Recorded run** and **Slack-style simulation** so
its provenance is unambiguous.

The static route set includes `/demo`, `/replay`, the published run trace, `/results`,
`/architecture`, `/methodology`, `/about`, and a private/static `/review` workflow. Public live
mode is disabled; a complete recorded fallback remains available without an API.

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

The worker and synthetic connector implement durable leases, bounded recovery, idempotency, and
reconciliation. The real Jira boundary remains disabled and public mode cannot write.

## Replay and draft evaluation

All Codex-created truth/scenario content is `DRAFT_PENDING_HUMAN_REVIEW`; held-out candidates are
not locked.

```bash
make replay-smoke
CANDIDATE_BUILD=guarded-v1 \
BASELINE_BUILD=unsafe-v0 \
DATASET_VERSION=replay-development-draft-1.0 \
MANIFEST_LOCK_HASH=sha256:b312f320243a4a3a3e34f664f5d55f9586f7273b1a5daf203eaf1febc3ca7f7a \
make evaluate-candidate
```

The local API exposes only predefined fixture inputs at `POST /v1/replays`,
`GET /v1/replays/{id}`, and `GET /v1/releases/{build}`. It accepts no arbitrary prompt, manifest,
attack payload, or connector write.

## Human review and language status

The review workflow is blinded and deterministic but contains no reviewer responses. Generate a
private empty export and exact-count analysis with:

```bash
make review-template
REVIEW_EXPORT=/path/to/genuine-private-export.csv make review-analysis
```

An exploratory French fixture and fluent-human signoff schema exist under `data/languages/`, but
no signoff exists and no French or broad multilingual quality claim is made. Public claims remain
English-only.

## Verification

```bash
scripts/verify.sh
```

The verifier runs source-integrity checks, locked setup validation, Python and web lint/types,
unit/integration/Replay tests, deterministic bundle reproduction, negative release gates,
reversible PostgreSQL migrations, all static routes, snapshot checksums, browser-bundle secret
scan, and browser smoke. It never calls Cohere, Slack, Jira, or a paid service.

## Fixture and interfaces

- Canonical truth: `data/truths/hero-payments-001.json`
- Synthetic sources: `data/artifacts/`
- Recorded snapshot: `data/published/hero-foundation.json`
- Checksummed Replay result: `data/published/replay-development-result.json`
- Shared Resolve path: `python/resolveflow/orchestrator.py`
- Replay manifest: `data/manifests/replay-role-downgrade-001.yaml`
- Draft gate: `eval/configs/release-gate-1.0.yaml`

Synthetic data is not customer evidence. The cited result is a deterministic recorded fixture,
not a live model result. Human review, provider performance, cost, integration success, held-out
performance, and a final release verdict have not been measured.
