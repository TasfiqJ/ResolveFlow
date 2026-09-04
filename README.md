# ResolveFlow Replay

ResolveFlow Replay is a deployment gate for enterprise agents.

**Deployed technical preview:**
[tasfiqj.github.io/ResolveFlow](https://tasfiqj.github.io/ResolveFlow/)

The deployed site now includes the Cohere integration receipt at `/cohere`, the retained live A/B
at `/results/ab`, and the credibility corrections from the current main branch. It remains a
snapshot-first technical preview, not a public inference endpoint or production release.

The current local credential-free build demonstrates one clearly labeled synthetic payments
incident moving through authorized hybrid retrieval, a bounded fixture-backed tool loop, claim-level
verification, payload-digest approval checks, deterministic Replay, paired unsafe/guarded comparison,
and a hard-invariant-first release gate. The public page is snapshot-first: it needs no Cohere
key, database, Slack workspace, or Jira site.

The approval state machine binds an accepted decision to the exact proposal payload, but the local
API does not authenticate callers. Actor identity and permission scopes must therefore come from a
trusted upstream identity layer before this is an end-to-end human-approval boundary.

Current status: technical preview with a fail-closed `NO_SHIP` decision for both builds. Unsafe-v0
admits a forbidden candidate. Guarded-v1 fixes that authorization failure, but the gate now refuses
to credit unexercised action/deployment invariants as zero failures and detects that 36 draft truth
IDs collapse to one semantic template. This is not a held-out, human-reviewed, or final release
result. No external write is represented by the fixture.

The integrity artifact also separates 5/5 stored attack payloads exercising their deterministic
controls from a 200/200 executed recorded-fixture Replay matrix (200 passed, 0 open issues). The
matrix still reuses one hostile artifact across its declared family/variant labels and is not a
live-model attack suite.

A separate live Cohere A/B exercised Command A+ and Rerank v4 over one coherent 32-run
repetition (16 per build). Its reconciled ledger records 197 Chat calls and 36 Rerank calls: 206
for the selected full pass and 27 for the required four-run dry pass, with no retries. It reused an
Embed v4 cache produced by an earlier single pass. Low completion (1/16 guarded, 3/16 unsafe)
makes citation precision, route accuracy, and completion rate **VOID** as quality metrics. One
pre-completion result remains valid: unsafe-v0 retrieved forbidden evidence in 16/16 runs while
guarded-v1 retrieved it in 0/16, a -100 percentage-point difference with a descriptive Newcombe
95% interval of [-100, -72.6197]. Offline recovery excluded 63 snapshots from other timestamps
instead of combining them into a mixed cohort and spent zero provider calls. A later, reduced
11-scenario completion-budget follow-up consumed 161 attempts, including 27 retries, and did not
improve guarded completion (0/11). These are narrow synthetic-run findings, not a cost, general
robustness, independent-sample inference, or release claim. See `docs/RESULTS-SUMMARY.md`.

The provider-call, agent-round, and tool-call limits are hard admission caps. By contrast,
`max_total_tokens` combines preflight sizing with a post-response check of observed usage: it can
stop the next call, but it cannot prevent one in-flight response from crossing the threshold and
is not a billing ceiling. Remaining time is passed into deadline-aware operations and checked
again after they return, so the wall-clock/request timeout is cooperative and per operation, not
a guaranteed hard end-to-end deadline or proof that remote processing stopped.

## Snapshot quick start

Prerequisites: Node.js 24, pnpm 10, Python 3.10+ and uv.

```bash
make bootstrap
make snapshot-hero
pnpm --dir apps/web dev
```

Open `http://localhost:3000`. The UI says **Recorded run** and **Slack-style simulation** so
its provenance is unambiguous.

The static route set includes `/demo`, `/replay`, the Cohere integration receipt at `/cohere`,
the published run trace, `/results`, `/architecture`, `/methodology`, `/about`, `/audit`, and a
private/static `/review` workflow.
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

Synthetic data is not customer evidence. The paired product Replay is a deterministic recorded
fixture; the separate live Cohere A/B supports only the explicitly bounded result above. Human
review, cost, real-integration success, held-out performance, and a final release verdict have not
been measured.

## License

ResolveFlow Replay is available under the MIT License. Synthetic project fixtures are not customer
evidence; third-party dependencies and referenced materials retain their own licenses.
