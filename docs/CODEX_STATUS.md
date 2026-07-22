# ResolveFlow Replay status

**Last updated:** 2026-07-21

**Current branch:** `main`

**Product implementation:** Stage 01 foundation vertical slice implemented

**Active work:** Stage 01 verification and outer-loop handoff

## Current repository facts

- The foundation is a modular Python monolith, a separate worker runtime, one PostgreSQL 17-compatible development database, and a Next.js 16 static-exportable web app.
- A web-created, clearly synthetic HelioPay payments case follows the shared `ResolveOrchestrator` path through named context operations, a fixture-backed cited result, an explicit missing cluster ID, an inert Jira proposal, and six chronological trace events.
- The public shell is snapshot-first and visibly labels its output `Recorded fixture` and its intake `Slack-style simulation`.
- FastAPI exposes `/health/live`, `/health/ready`, `/version`, `POST /v1/cases`, and the canonical recorded run.
- Alembic revision `0001_foundation` owns tenants, cases, agent runs, append-oriented audit rows, and job foundations. Its upgrade/downgrade/upgrade cycle passed against the Compose PostgreSQL service.
- The normal build and tests require no Cohere key. No provider call, Slack/Jira write, deployment, evaluation, human review, cost claim, or release verdict occurred.
- Retrieval, full bounded Command execution, complete claim verification, real Slack/Jira adapters, Replay, and release gates remain in their later named milestones.

## Milestone status

| Milestone | Status | Evidence |
|---|---|---|
| Stage 00 executable planning | COMPLETE | Plan v1.1, 78 acceptance mappings, 12 ADRs, and source verifier |
| 1. foundation vertical slice | IMPLEMENTED; FINAL VERIFY IN PROGRESS | Shared path, API/worker/database/web scaffold, fixtures, snapshot, tests |
| 2. evidence and retrieval | NOT STARTED | Typed `RetrievalPort` boundary only |
| 3. governed agent and safety | NOT STARTED | Typed agent/verifier boundaries and fixture response only |
| 4. actions, reliability and audit | NOT STARTED | Inert proposal and schema foundations only |
| 5. Replay and release gate | NOT STARTED | No evaluation or verdict |
| 6. public product and validation | NOT STARTED | Foundation snapshot shell only |
| 7. final audit and release | NOT STARTED | No deployment or publication |

## Stage 01 checks observed so far

| Command | Result |
|---|---|
| `uv run ruff check python tests` | PASS |
| `uv run ruff format --check python tests` | PASS |
| `uv run mypy python/resolveflow` | PASS, 21 source files |
| `uv run pytest -q tests/unit tests/integration` | PASS, 10 tests |
| `pnpm --dir apps/web test` | PASS, 1 component test |
| `pnpm --dir apps/web build` | PASS, static `/` and `/_not-found` export |
| `node tests/browser/snapshot-smoke.mjs` | PASS |
| `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` | PASS against local PostgreSQL |

The cumulative `scripts/verify.sh` result is recorded after its final run. Local checks do not imply GitHub Actions, provider, connector, deployment, or human evidence.

## External work and credentials

- No Cohere key was available or required; no live model call was made.
- No Slack or Jira credential was accessed and no external write occurred.
- No paid resource was created.
- No branch, worktree, commit, push, merge, deployment, tag, release, or publication was performed. The outer loop owns commit and push.

## Immediate next action

Complete `scripts/verify.sh`, inspect the final diff and working tree, then hand the coherent uncommitted Stage 01 slice to the outer loop. Do not begin Milestone 2 in this stage.
