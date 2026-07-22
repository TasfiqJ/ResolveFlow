# ResolveFlow Replay status

**Last updated:** 2026-07-22

**Current branch:** `main`

**Product implementation:** Stage 07 technical-preview audit complete; publication verification pending

**Active work:** Stage 08 GitHub Pages publication and post-push verification

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
- The static product now exports `/`, `/demo`, `/replay`, `/results`, `/architecture`, `/methodology`, `/about`, `/review`, and one pre-generated `/runs/run_hero_foundation_001` audit page, plus a useful unknown-artifact page.
- Homepage and demo expose the synthetic case, authorized evidence, verified response, inert action, and observable trace. Replay exposes the frozen paired comparison; Results reports only exact development-fixture counts and explicit absent evidence.
- Canonical hero and Replay result JSON are stored with reconstructable canonical/file checksums and copied byte-for-byte into the browser asset tree. Generated-browser bundles are scanned for secret-like values and server-only credential names.
- Public live inference remains disabled. A local API boundary accepts one predefined case and five named mutations and enforces IP/session/global quotas, one active run per session, a bounded queue, deadline, and kill switch with a recorded fallback.
- Slack request HMAC/timestamp verification, challenge/event parsing, deduplication, immediate queued acknowledgement, canonical normalization, and safe audit events are implemented with synthetic signed contracts; no real Slack credential or request was used.
- Jira staging configuration validates one HTTPS development site/project and fixed issue/team/priority mappings, while the real adapter remains disabled and public mode cannot contain write authority.
- The private/static review workflow blinds and deterministically randomizes A/B outputs. Empty export and exact-count analysis commands report 0 reviewers/0 cases; no reviewer response, role evidence, percentage, or disagreement is invented.
- The exploratory French fixture is synthetic-agent-authored, pending fluent-human signoff, excluded from claimed results, and unable to expand public case/action authority. Public quality claims remain English-only.
- GitHub Pages static deployment is prepared but has not yet been triggered. No deployment/public URL is claimed before observation.

## Milestone status

| Milestone | Status | Evidence |
|---|---|---|
| Stage 00 executable planning | COMPLETE | Plan v1.1, 78 acceptance mappings, 12 ADRs, and source verifier |
| 1. foundation vertical slice | COMPLETE | `scripts/verify.sh` passed with shared path, API/worker/database/web scaffold, fixtures, snapshot, tests, static export, browser smoke, and reversible migration cycle |
| 2. evidence and retrieval | COMPLETE | Versioned corpus, immutable policy snapshots, pre-search authorization, PostgreSQL FTS/pgvector, hybrid fusion, fixture/Cohere adapters, traced ranks, role/cache security, and exact-count fixture metrics |
| 3. governed agent and safety | COMPLETE | Bounded typed tools/provider calls, fixture and Cohere adapters, verified graph closure, strict two-pass rendering, hostile-evidence boundary, effect scoring, linter, traces, migration, and fault/security tests |
| 4. actions, reliability and audit | COMPLETE | Verified-evidence proposals, exact approval states, durable leases/reclaim, bounded fault recovery, synthetic Jira reconciliation, append-only audit, public redaction/export/diff foundation, and approval UI |
| 5. Replay and release gate | COMPLETE | Versioned draft truths/manifests/builds, frozen deterministic materialization, shared-path pairing, run diff, hard-first exact-count scoring, uncertainty, three-way gate, checksummed bundles, API/CLI, migration, and CI smoke/negative workflows |
| 6. public product and validation | COMPLETE | Complete static route set, public views, checksummed snapshots, secret scan, outage fallback, bounded local-live controls, Slack/Jira staging boundaries, blinded review tooling, and unvalidated language structure |
| 7. final audit and release | COMPLETE | Truthful technical-preview profile, dependency/history/bundle audits, exact claims, pinned container build/startup, release documents, and full verifier |

## Stage 06 checks

| Command | Result |
|---|---|
| `uv run ruff check python tests` | PASS |
| `uv run ruff format --check python tests` | PASS |
| `uv run mypy python/resolveflow` | PASS, 79 source files |
| `uv run pytest -q tests/unit tests/integration tests/contract tests/security tests/replay` | PASS, 132 credential-free Stage 01-06 tests |
| `uv run pytest -q tests/postgres` | PASS, 4 real PostgreSQL retrieval/action concurrency and audit tests |
| `uv run resolveflow-corpus-validate` | PASS, 5 artifacts, 6 versions, 6 chunks, 6 embeddings |
| `uv run resolveflow-retrieval-fixture-eval` | PASS, development/calibration observations with exact N; not held-out/provider evidence |
| `pnpm --dir apps/web test` | PASS, 2 component/action-flow tests |
| `pnpm --dir apps/web build` | PASS, 9 public/static views plus one pre-generated run route and unknown-artifact page |
| `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web build` | PASS, GitHub Pages asset prefix and base path present |
| `uv run python scripts/scan_public_build.py --path apps/web/out --strict` | PASS, no secret-like value or server-only credential name |
| `uv run python scripts/verify_public_snapshots.py` | PASS, hero canonical hash and Replay canonical/file checksums verified |
| `node tests/browser/snapshot-smoke.mjs` | PASS, complete snapshot-first route/provenance/review/degradation smoke |
| `uv run resolveflow-review template ... && uv run resolveflow-review analyze ...` | PASS, honest empty export reports 0 responses with exact counts |
| `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` | PASS against local PostgreSQL |
| `uv run resolveflow-policy-lint` | PASS, versioned system prompt and four fixed tool descriptions |
| `uv run resolveflow-replay dry-run --manifest data/manifests/replay-role-downgrade-001.yaml` | PASS, no provider call; materialization `sha256:72146755...ca7a` |
| `uv run resolveflow-replay smoke --manifest data/manifests/replay-role-downgrade-001.yaml` | PASS, same shared path for unsafe-v0 and guarded-v1 |
| `uv run resolveflow-evaluation negative-gate --manifest data/manifests/replay-role-downgrade-001.yaml` | PASS, retained unsafe forbidden candidate blocks with `NO_SHIP` |
| `uv run resolveflow-evaluation evaluate ... --output /tmp/resolveflow-stage05-result.json` | PASS, canonical and file checksums verified; unsafe `NO_SHIP`, guarded `SHIP_WITH_LIMITS` |
| `scripts/verify.sh` | PASS, cumulative Stage 00-06 verification including PostgreSQL migration/concurrency checks |

Local checks do not imply GitHub Actions, provider, connector, deployment, or human evidence.

## Stage 07 checks

| Command | Result |
|---|---|
| `uv run --with pip-audit pip-audit` | PASS, no known vulnerabilities; unpublished local package explicitly skipped |
| `pnpm audit` | PASS, no known vulnerabilities |
| pinned Gitleaks 8.30.1 history scan | PASS, 18 reachable commits and no leaks |
| `scripts/verify.sh` | PASS, 134 Python tests, 2 web tests, 4 PostgreSQL tests, Replay gates, static export, strict preflight, snapshot/bundle checks, migrations, and pinned container startup |
| pinned Compose startup | PASS, database/API/worker/web running; API live/ready/version and homepage/About checks succeeded |
| isolated clean-clone restore | PASS at pushed commit `e30f567`; frozen install, Pages build, route smoke, and published hashes reproduced |

One Starlette TestClient transition warning is recorded in `docs/KNOWN_LIMITATIONS.md`; no test was skipped or muted.

## External work and credentials

- No Cohere key was available or required; no live model call was made.
- No Slack or Jira credential was accessed and no external write occurred.
- No paid resource was created.
- Milestone work through commit `fddb5aa` is pushed to `origin/main`; the final audit hardening changes are the next coherent checkpoint.
- No merge, deployment, tag, release, or publication is claimed yet.

## Immediate next action

Commit and push the verified audit checkpoint, prove a clean-clone restore, then enable and verify the GitHub Pages workflow and public URL.
