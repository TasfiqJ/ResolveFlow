# ResolveFlow Replay

ResolveFlow Replay is a deployment gate for enterprise agents.

**Live technical preview:** [tasfiqj.github.io/ResolveFlow](https://tasfiqj.github.io/ResolveFlow/)

The current credential-free build demonstrates one clearly labeled synthetic payments incident
moving through authorized hybrid retrieval, a bounded fixture-backed tool loop, claim-level
verification, exact approval controls, deterministic Replay, paired unsafe/guarded comparison,
and a hard-invariant-first release gate. The public page is snapshot-first: it needs no Cohere
key, database, Slack workspace, or Jira site.

Current status: technical preview with a fail-closed `NO_SHIP` decision for both builds. Unsafe-v0
admits a forbidden candidate. Guarded-v1 fixes that authorization failure, but the gate now refuses
to credit unexercised action/deployment invariants as zero failures and detects that 36 draft truth
IDs collapse to one semantic template. This is not a held-out, live-provider, human-reviewed, or
final release result. No external write is represented by the fixture.

The integrity artifact also separates 5/5 stored attack payloads exercising their deterministic
controls from a 200/200 executed recorded-fixture Replay matrix (200 passed, 0 open issues). The
matrix still reuses one hostile artifact across its declared family/variant labels and is not a
live-model attack suite. Live mode is contract-wired as one
Chat/Embed/Rerank composition with provider-derived provenance and ACL filtering before document
embedding, but no live call or provider result is claimed.

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
`/architecture`, `/methodology`, `/about`, `/audit`, and a private/static `/review` workflow.
Public live mode is disabled; a complete recorded fallback remains available without an API.

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
MANIFEST_LOCK_HASH=sha256:f09b20e24727f952d2499ac8e35bfa9c47a3791ac71689c7e3c940abd01bb990 \
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

The release contract has two profiles. `validated_release` retains the full human-authorship,
held-out-lock, and practitioner-review gates. The active `technical_preview` profile permits the
snapshot site to publish while those items remain visibly incomplete and while no final
production-readiness verdict is claimed.

## Verification

```bash
scripts/verify.sh
```

The verifier runs source-integrity checks, locked setup validation, Python and web lint/types,
unit/integration/Replay tests, deterministic bundle reproduction, negative release gates,
reversible PostgreSQL migrations, all static routes, snapshot checksums, browser-bundle secret
scan, static artifact smoke, and real Chromium journeys with WCAG A/AA checks. It never calls
Cohere, Slack, Jira, or a paid service.

## Fixture and interfaces

- Canonical truth: `data/truths/hero-payments-001.json`
- Synthetic sources: `data/artifacts/`
- Recorded snapshot: `data/published/hero-foundation.json`
- Checksummed Replay result: `data/published/replay-development-result.json`
- Shared Resolve path: `python/resolveflow/orchestrator.py`
- Replay manifest: `data/manifests/replay-role-downgrade-001.yaml`
- Current fail-closed draft gate: `eval/configs/release-gate-1.1.yaml`
- Evaluation integrity audit: `data/published/evaluation-integrity-audit.json`
- Release profile: `docs/HUMAN_SIGNOFF.json`
- Release checklist and limits: `docs/RELEASE_CHECKLIST.md`, `docs/KNOWN_LIMITATIONS.md`

Synthetic data is not customer evidence. The cited result is a deterministic recorded fixture,
not a live model result. Human review, provider performance, cost, integration success, held-out
performance, and a final release verdict have not been measured.

## License

ResolveFlow Replay is available under the MIT License. Synthetic project fixtures are not customer
evidence; third-party dependencies and referenced materials retain their own licenses.
