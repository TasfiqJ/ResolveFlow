# ResolveFlow Replay status

**Last updated:** 2026-07-22

**Current branch:** `main`

**Product implementation:** Stage 05 Replay and release gate implemented

**Active work:** Stage 05 complete; ready for outer-loop handoff

## Current repository facts

- The foundation is a modular Python monolith, a separate worker runtime, one PostgreSQL 17-compatible development database, and a Next.js 16 static-exportable web app.
- A web-created, clearly synthetic HelioPay payments case follows the shared `ResolveOrchestrator` path through named context operations, a governed fixture-backed cited result, an explicit missing cluster ID, an inert Jira proposal, and 14 hash-linked chronological trace events.
- The public shell is snapshot-first and visibly labels its output `Recorded fixture` and its intake `Slack-style simulation`.
- FastAPI exposes health/version, canonical case/run, exact action approve/reject, chronological events, redacted/full trace, and deterministic JSON/Markdown export routes.
- Alembic revision `0001_foundation` owns tenants, cases, agent runs, append-oriented audit rows, and job foundations. Its upgrade/downgrade/upgrade cycle passed against the Compose PostgreSQL service.
- The normal build and tests require no Cohere key. One deterministic draft fixture evaluation occurred; no live provider call, Slack/Jira write, deployment, human review, cost claim, held-out evaluation, or final release verdict occurred.
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
- Verified action claims are the only source of inert Jira proposals. Canonical payload digests cover the human-visible fields; permissions, exact digest, expiry, rejection, revision invalidation, and worker-only dispatch are ordinary-code controls.
- The synthetic Jira connector models pre-send timeout, uncertain accepted sends, acknowledgement loss, 429, 5xx, and permission denial. Uncertain outcomes reconcile the stable logical-action idempotency marker before any retry; the real adapter remains disabled.
- Alembic revision `0004_actions_reliability_audit` owns exact proposals/approvals, idempotency, attempts, durable job leases, bounded retries, and database append-only audit enforcement. Real PostgreSQL tests cover concurrent `SKIP LOCKED` claims, crash reclaim, one approval/job/ledger, atomic attempt/audit state, and immutable audit rows.
- The public projection deterministically removes restricted or sensitive fields, secret-like values, hidden prompts/reasoning, raw payloads, stack data, and private paths. Event-only reconstruction, checksummed JSON/Markdown exports, and immutable run-diff foundations are tested.
- The static action panel displays the exact digest, evidence, unknowns, risk, expiry, approve/reject states, and a clearly labeled synthetic completion. It cannot reach Jira.
- Replay schema 1.0 loads checksummed YAML manifests, validates one typed primary mutation, and freezes clock, identity, ACL policy, corpus snapshot, model policy, connector behavior, and feature flags before any provider call.
- The registry has fixed handlers for role override, artifact addition/removal, stale promotion, image replacement, connector state, language variant, and field removal. Unsupported fixtures and arbitrary hooks fail before execution.
- Both `unsafe-v0` and `guarded-v1` call the same `ResolveOrchestrator.run` production entrypoint. The unsafe fixture is confined to Replay, disables pre-retrieval ACL only, retains approval, and cannot perform an external write.
- The draft catalog contains exactly 36 synthetic-agent-authored candidates (18 development, 8 calibration, 10 held-out candidates). Every truth/scenario is `DRAFT_PENDING_HUMAN_REVIEW`; held-out candidates remain `DRAFT_NOT_LOCKED` and no human authorship is claimed.
- A separate draft deterministic security matrix declares 200 unique application-control scenarios across 10 base-truth clusters, five existing attack families, and four variants. It records zero live-provider calls and is not described as 200 independent live attacks.
- Hard-invariant observations are evaluated before quality/operations. Every proportion stores exact numerator/denominator and a 95% Wilson interval; paired route comparison uses a deterministic base-truth-cluster bootstrap with an explicit dependence caveat.
- The release gate implements `SHIP`, `SHIP_WITH_LIMITS`, and `NO_SHIP`, retains every failing Replay link, reports insufficient samples, and writes canonical/file checksummed JSON bundles plus a reproducible Markdown summary.
- One actual deterministic development-fixture pair produced unsafe-v0 `NO_SHIP` for one forbidden candidate and guarded-v1 `SHIP_WITH_LIMITS` because citation precision N=4 is below the draft minimum N=10. This is not a final, held-out, live-provider, human-reviewed, or publishable release verdict.
- FastAPI now exposes only the predefined `POST /v1/replays`, `GET /v1/replays/{id}`, and `GET /v1/releases/{build}` fixture interfaces; arbitrary manifests/builds remain rejected.
- Alembic revision `0005_replay_release_gate` owns draft truth/scenario/expectation, paired Replay, metric, comparison, gate, and result-bundle records, including database guards against falsely locked truth rows or final-publication flags.

## Milestone status

| Milestone | Status | Evidence |
|---|---|---|
| Stage 00 executable planning | COMPLETE | Plan v1.1, 78 acceptance mappings, 12 ADRs, and source verifier |
| 1. foundation vertical slice | COMPLETE | `scripts/verify.sh` passed with shared path, API/worker/database/web scaffold, fixtures, snapshot, tests, static export, browser smoke, and reversible migration cycle |
| 2. evidence and retrieval | COMPLETE | Versioned corpus, immutable policy snapshots, pre-search authorization, PostgreSQL FTS/pgvector, hybrid fusion, fixture/Cohere adapters, traced ranks, role/cache security, and exact-count fixture metrics |
| 3. governed agent and safety | COMPLETE | Bounded typed tools/provider calls, fixture and Cohere adapters, verified graph closure, strict two-pass rendering, hostile-evidence boundary, effect scoring, linter, traces, migration, and fault/security tests |
| 4. actions, reliability and audit | COMPLETE | Verified-evidence proposals, exact approval states, durable leases/reclaim, bounded fault recovery, synthetic Jira reconciliation, append-only audit, public redaction/export/diff foundation, and approval UI |
| 5. Replay and release gate | COMPLETE | Versioned draft truths/manifests/builds, frozen deterministic materialization, shared-path pairing, run diff, hard-first exact-count scoring, uncertainty, three-way gate, checksummed bundles, API/CLI, migration, and CI smoke/negative workflows |
| 6. public product and validation | NOT STARTED | Foundation snapshot shell only |
| 7. final audit and release | NOT STARTED | No deployment or publication |

## Stage 05 checks

| Command | Result |
|---|---|
| `uv run ruff check python tests` | PASS |
| `uv run ruff format --check python tests` | PASS |
| `uv run mypy python/resolveflow` | PASS, 74 source files |
| `uv run pytest -q tests/unit tests/integration tests/contract tests/security tests/replay` | PASS, 109 credential-free Stage 01-05 tests |
| `uv run pytest -q tests/replay tests/unit/evaluation tests/integration/test_api.py` | PASS, 29 focused Replay/gate/API tests |
| `uv run pytest -q tests/postgres` | PASS, 4 real PostgreSQL retrieval/action concurrency and audit tests |
| `uv run resolveflow-corpus-validate` | PASS, 5 artifacts, 6 versions, 6 chunks, 6 embeddings |
| `uv run resolveflow-retrieval-fixture-eval` | PASS, development/calibration observations with exact N; not held-out/provider evidence |
| `pnpm --dir apps/web test` | PASS, 2 component/action-flow tests |
| `pnpm --dir apps/web build` | PASS, static `/` and `/_not-found` export |
| `node tests/browser/snapshot-smoke.mjs` | PASS |
| `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` | PASS against local PostgreSQL |
| `uv run resolveflow-policy-lint` | PASS, versioned system prompt and four fixed tool descriptions |
| `uv run resolveflow-replay dry-run --manifest data/manifests/replay-role-downgrade-001.yaml` | PASS, no provider call; materialization `sha256:72146755...ca7a` |
| `uv run resolveflow-replay smoke --manifest data/manifests/replay-role-downgrade-001.yaml` | PASS, same shared path for unsafe-v0 and guarded-v1 |
| `uv run resolveflow-evaluation negative-gate --manifest data/manifests/replay-role-downgrade-001.yaml` | PASS, retained unsafe forbidden candidate blocks with `NO_SHIP` |
| `uv run resolveflow-evaluation evaluate ... --output /tmp/resolveflow-stage05-result.json` | PASS, canonical and file checksums verified; unsafe `NO_SHIP`, guarded `SHIP_WITH_LIMITS` |
| `scripts/verify.sh` | PASS, cumulative Stage 00-05 verification |

Local checks do not imply GitHub Actions, provider, connector, deployment, or human evidence.

## External work and credentials

- No Cohere key was available or required; no live model call was made.
- No Slack or Jira credential was accessed and no external write occurred.
- No paid resource was created.
- No branch, worktree, commit, push, merge, deployment, tag, release, or publication was performed. The outer loop owns commit and push.

## Immediate next action

The outer loop may inspect, commit, and push the coherent uncommitted Stage 05 slice. Do not begin Milestone 6 in this stage.
