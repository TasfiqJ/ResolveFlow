# ResolveFlow Replay status

**Last updated:** 2026-07-22

**Current branch:** `main`

**Product implementation:** Stage 03 governed agent and safety implemented

**Active work:** Stage 03 complete; ready for outer-loop handoff

## Current repository facts

- The foundation is a modular Python monolith, a separate worker runtime, one PostgreSQL 17-compatible development database, and a Next.js 16 static-exportable web app.
- A web-created, clearly synthetic HelioPay payments case follows the shared `ResolveOrchestrator` path through named context operations, a governed fixture-backed cited result, an explicit missing cluster ID, an inert Jira proposal, and eight chronological trace events.
- The public shell is snapshot-first and visibly labels its output `Recorded fixture` and its intake `Slack-style simulation`.
- FastAPI exposes `/health/live`, `/health/ready`, `/version`, `POST /v1/cases`, and the canonical recorded run.
- Alembic revision `0001_foundation` owns tenants, cases, agent runs, append-oriented audit rows, and job foundations. Its upgrade/downgrade/upgrade cycle passed against the Compose PostgreSQL service.
- The normal build and tests require no Cohere key. No live provider call, Slack/Jira write, deployment, evaluation, human review, cost claim, or release verdict occurred.
- The shared Resolve path now runs a deterministic fixture-backed bounded Command protocol with four typed allowlisted tools, strict local validation, authorization, per-tool timeout, and fixed round/provider-call/token/wall-clock budgets.
- Stage 02 adds a checksummed synthetic corpus with six immutable artifact versions/chunks, explicit parser/chunker provenance, effective intervals, data-quality validation, frozen corpus/identity/ACL snapshots, and deterministic re-ingestion.
- The shared Resolve path now performs authorization before lexical/vector ranking, reciprocal-rank fusion, deduplication, per-artifact diversity limits, deterministic reranking, and candidate-level rank/score/provenance tracing.
- Alembic revision `0002_evidence_retrieval` owns artifact/version/chunk/ACL/embedding/corpus/identity/retrieval schemas, PostgreSQL generated full-text vectors, and pgvector storage. A real PostgreSQL test proved FTS and vector queries share the materialized eligible relation.
- Cohere Embed v4 and Rerank v4 Fast/Pro adapters are dependency-injected behind ports and were not called. Official model/request contracts were rechecked on 2026-07-22; default verification uses deterministic fixture adapters.
- Development and calibration retrieval fixtures are explicitly `synthetic_agent_authored` and pending human review. Their deterministic metrics report exact fixture counts only; no held-out tuning or provider/retrieval improvement claim occurred.
- The official Cohere Python V2 Chat adapter is locked behind explicit live-off configuration; the ordinary build uses a deterministic two-round fixture adapter and makes no network call.
- Retrieved candidates enter a strongly typed untrusted-evidence envelope. Evidence text cannot modify the system prompt, tool registry, ACL snapshot, approval boundary, or effect scoring.
- First-pass findings become claim/citation/unknown/conflict nodes. The verifier rechecks citation existence, authorization, snapshot version, freshness, model-context membership, exact spans, deterministic support, conflicts, and independent non-hostile support.
- The second pass receives only the verified graph and JSON schema, with no documents or tools. It selects graph IDs only; deterministic code renders the response, and malformed/provider/budget failures use a fixed `needs_review` fallback.
- Provider/tool traces expose hashes, finish reasons, usage, status, safe errors, duration, and provenance without prompts, response text, hidden reasoning, credentials, or connector effects.
- The prompt-injection library covers visible, delimiter-like, multilingual, fake-system, and approval-bypass families. Observable effect scoring records blocked attempts separately from successful effects and makes no immunity claim.
- Alembic revision `0003_governed_agent_safety` adds provider/tool, evidence graph, claim, citation, verifier, and final-response records, including a database check that model tool calls cannot record an external write.

## Milestone status

| Milestone | Status | Evidence |
|---|---|---|
| Stage 00 executable planning | COMPLETE | Plan v1.1, 78 acceptance mappings, 12 ADRs, and source verifier |
| 1. foundation vertical slice | COMPLETE | `scripts/verify.sh` passed with shared path, API/worker/database/web scaffold, fixtures, snapshot, tests, static export, browser smoke, and reversible migration cycle |
| 2. evidence and retrieval | COMPLETE | Versioned corpus, immutable policy snapshots, pre-search authorization, PostgreSQL FTS/pgvector, hybrid fusion, fixture/Cohere adapters, traced ranks, role/cache security, and exact-count fixture metrics |
| 3. governed agent and safety | COMPLETE | Bounded typed tools/provider calls, fixture and Cohere adapters, verified graph closure, strict two-pass rendering, hostile-evidence boundary, effect scoring, linter, traces, migration, and fault/security tests |
| 4. actions, reliability and audit | NOT STARTED | Inert proposal and schema foundations only |
| 5. Replay and release gate | NOT STARTED | No evaluation or verdict |
| 6. public product and validation | NOT STARTED | Foundation snapshot shell only |
| 7. final audit and release | NOT STARTED | No deployment or publication |

## Stage 03 checks

| Command | Result |
|---|---|
| `uv run ruff check python tests` | PASS |
| `uv run ruff format --check python tests` | PASS |
| `uv run mypy python/resolveflow` | PASS, 44 source files |
| `uv run pytest -q tests/unit tests/integration tests/contract tests/security tests/replay` | PASS, 66 credential-free Stage 01-03 tests |
| `uv run pytest -q tests/postgres` | PASS, real PostgreSQL FTS/pgvector authorization integration |
| `uv run resolveflow-corpus-validate` | PASS, 5 artifacts, 6 versions, 6 chunks, 6 embeddings |
| `uv run resolveflow-retrieval-fixture-eval` | PASS, development/calibration observations with exact N; not held-out/provider evidence |
| `pnpm --dir apps/web test` | PASS, 1 component test |
| `pnpm --dir apps/web build` | PASS, static `/` and `/_not-found` export |
| `node tests/browser/snapshot-smoke.mjs` | PASS |
| `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` | PASS against local PostgreSQL |
| `uv run resolveflow-policy-lint` | PASS, versioned system prompt and four fixed tool descriptions |
| `scripts/verify.sh` | PASS, cumulative Stage 00-03 verification |

Local checks do not imply GitHub Actions, provider, connector, deployment, or human evidence.

## External work and credentials

- No Cohere key was available or required; no live model call was made.
- No Slack or Jira credential was accessed and no external write occurred.
- No paid resource was created.
- No branch, worktree, commit, push, merge, deployment, tag, release, or publication was performed. The outer loop owns commit and push.

## Immediate next action

The outer loop may inspect, commit, and push the coherent uncommitted Stage 03 slice. Do not begin Milestone 4 in this stage.
