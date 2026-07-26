# ResolveFlow Replay status

**Last updated:** 2026-07-26

**Current branch:** `main`

**Product implementation:** Complete technical preview with credibility-hardened portfolio experience

**Active work:** None; CI cache-cleanup repair validated and deployed

## Current repository facts

- The foundation is a modular Python monolith, a separate worker runtime, one PostgreSQL 17-compatible development database, and a Next.js 16 static-exportable web app.
- A web-created, clearly synthetic HelioPay payments case follows the shared `ResolveOrchestrator` path through named context operations, a governed fixture-backed cited result, an explicit missing cluster ID, an inert Jira proposal, and 14 hash-linked chronological trace events.
- The public shell is snapshot-first and immediately labels the hero experience as a recorded synthetic case, technical preview, and no-external-write environment.
- FastAPI exposes health/version, canonical case/run, exact action approve/reject, chronological events, redacted/full trace, and deterministic JSON/Markdown export routes.
- Alembic revision `0001_foundation` owns tenants, cases, agent runs, append-oriented audit rows, and job foundations. Its upgrade/downgrade/upgrade cycle passed against the Compose PostgreSQL service.
- The normal build and tests require no Cohere key. One deterministic draft fixture evaluation and one static GitHub Pages deployment occurred; no live provider call, Slack/Jira write, human review, cost claim, held-out evaluation, or final release verdict occurred.
- The shared Resolve path now runs a deterministic fixture-backed bounded Command protocol with four typed allowlisted tools, strict local validation, authorization, per-tool timeout, and fixed round/provider-call/token/wall-clock budgets.
- Stage 02 adds a checksummed synthetic corpus with six immutable artifact versions/chunks, explicit parser/chunker provenance, effective intervals, data-quality validation, frozen corpus/identity/ACL snapshots, and deterministic re-ingestion.
- The shared Resolve path now performs authorization before lexical/vector ranking, reciprocal-rank fusion, deduplication, per-artifact diversity limits, deterministic reranking, and candidate-level rank/score/provenance tracing.
- Alembic revision `0002_evidence_retrieval` owns artifact/version/chunk/ACL/embedding/corpus/identity/retrieval schemas, PostgreSQL generated full-text vectors, and pgvector storage. A real PostgreSQL test proved FTS and vector queries share the materialized eligible relation.
- Cohere Chat, Embed v4, and Rerank v4 Fast/Pro adapters are composed as one live-only runtime choice behind explicit ports and were not called. Configured models and agent budgets now reach the shared orchestrator, live document embeddings are computed only over ACL-authorized snapshot candidates, and provider-derived provenance distinguishes live from recorded runs. Default verification uses deterministic fixture adapters.
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
- The draft catalog contains 36 synthetic-agent-authored IDs (18 development, 8 calibration, 10 held-out candidates), but the evaluation-integrity audit shows they collapse to 1 semantic truth template. Every entry remains `DRAFT_PENDING_HUMAN_REVIEW`; held-out candidates remain `DRAFT_NOT_LOCKED`.
- A separate draft deterministic security matrix declares 200 unique application-control scenarios across 10 base-truth clusters, five existing attack families, and four variants. It records zero live-provider calls and is not described as 200 independent live attacks.
- Hard-invariant observations are evaluated before quality/operations. Every proportion stores exact numerator/denominator and a 95% Wilson interval; paired route comparison uses a deterministic base-truth-cluster bootstrap with an explicit dependence caveat.
- The release gate implements `SHIP`, `SHIP_WITH_LIMITS`, and `NO_SHIP`, retains every failing Replay link, reports insufficient samples, and writes canonical/file checksummed JSON bundles plus a reproducible Markdown summary.
- Gate 1.1 produces `NO_SHIP` for both recorded builds. Unsafe-v0 admits one forbidden candidate. Guarded-v1 removes that exposure but is blocked because action/deployment hard invariants are unexercised or unverified, held-out data is unlocked, and dataset distinctness fails. This is not a final, held-out, live-provider, human-reviewed, or publishable release verdict.
- The 200-cell security matrix is now explicitly audited as a declaration: 0 cells have full Replay execution evidence, with 5 unique payloads for 20 declared family/variant slots. All 5 stored payloads exercise their expected deterministic forbidden-effect controls; those scanner results are not relabeled as full Replays.
- Public run snapshots retain event hashes, and the release scorer recomputes every event hash rather than trusting stored chain pointers.
- FastAPI now exposes only the predefined `POST /v1/replays`, `GET /v1/replays/{id}`, and `GET /v1/releases/{build}` fixture interfaces; arbitrary manifests/builds remain rejected.
- Alembic revision `0005_replay_release_gate` owns draft truth/scenario/expectation, paired Replay, metric, comparison, gate, and result-bundle records, including database guards against falsely locked truth rows or final-publication flags.
- The static product now exports `/`, `/demo`, `/replay`, `/results`, `/architecture`, `/methodology`, `/about`, `/audit`, `/review`, and one pre-generated `/runs/run_hero_foundation_001` audit page, plus a useful unknown-artifact page.
- Replay now uses a real accessible scenario explorer. Recorded snapshots and automated-test-only cases have distinct labels and evidence links; no test-only case is presented as a recorded or live run.
- The exported artifact has real Chromium coverage for core navigation, Replay state changes, keyboard skip navigation, WCAG A/AA rules, and mobile horizontal overflow. The browser suite found and drove fixes for 36 repeated low-contrast labels and one mobile overflow defect.
- GitHub Actions references are pinned to full commit SHAs, and the Pages deployment job now depends on the repository gates, browser suite, and strict preflight rather than building independently.
- Homepage engineering counters link directly to their workflow, trace, matrix, or migration evidence, and `/audit` publishes the senior-review verdict plus the remaining validation blockers.
- Homepage and demo now open as a technical control system: the first viewport names Tasfiq Jasimuddin as the end-to-end engineer, defines ResolveFlow as an AI-agent release gate, visualizes the Replay engine, and leads into a three-panel recorded control room, system architecture, engineering proof, ownership scope, and evidence routes. Replay exposes the frozen paired comparison; Results reports only exact development-fixture counts and explicit absent evidence.
- Canonical hero and Replay result JSON are stored with reconstructable canonical/file checksums and copied byte-for-byte into the browser asset tree. Generated-browser bundles are scanned for secret-like values and server-only credential names.
- Public live inference remains disabled. Limiter controls cover one predefined case, five named mutations, IP/session/global quotas, one active run per session, queue bounds, deadlines, and a kill switch. Because no bounded executor consumes accepted tickets, the API now fails live admission closed with `public_live_executor_unavailable` and the recorded fallback.
- Slack request HMAC/timestamp verification, challenge/event parsing, deduplication, immediate queued acknowledgement, canonical normalization, and safe audit events are implemented with synthetic signed contracts; no real Slack credential or request was used.
- Jira staging configuration validates one HTTPS development site/project and fixed issue/team/priority mappings, while the real adapter remains disabled and public mode cannot contain write authority.
- The private/static review workflow blinds and deterministically randomizes A/B outputs. Empty export and exact-count analysis commands report 0 reviewers/0 cases; no reviewer response, role evidence, percentage, or disagreement is invented.
- The exploratory French fixture is synthetic-agent-authored, pending fluent-human signoff, excluded from claimed results, and unable to expand public case/action authority. Public quality claims remain English-only.
- GitHub Pages published the credential-free static export at `https://tasfiqj.github.io/ResolveFlow/`; workflow run `29927371263`, nested-route checks, and both public snapshot hashes passed.

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
| `uv run resolveflow-evaluation evaluate ... --output /tmp/resolveflow-stage05-result.json` | Expected release block, canonical and file checksums verified; unsafe `NO_SHIP`, guarded `NO_SHIP` |
| `scripts/verify.sh` | PASS, cumulative Stage 00-06 verification including PostgreSQL migration/concurrency checks |

Local checks do not imply GitHub Actions, provider, connector, deployment, or human evidence.

## Stage 07 checks

| Command | Result |
|---|---|
| `uv run --with pip-audit pip-audit` | PASS, no known vulnerabilities; unpublished local package explicitly skipped |
| `pnpm audit --prod --audit-level high` | PASS, no known production vulnerabilities |
| `pnpm audit --dev --audit-level critical` | PASS at critical threshold; one documented high-severity development-only advisory remains |
| pinned Gitleaks 8.30.1 history scan | PASS, 18 reachable commits and no leaks |
| `scripts/verify.sh` | PASS, 134 Python tests, 2 web tests, 4 PostgreSQL tests, Replay gates, static export, strict preflight, snapshot/bundle checks, migrations, and pinned container startup |
| pinned Compose startup | PASS, database/API/worker/web running; API live/ready/version and homepage/About checks succeeded |
| isolated clean-clone restore | PASS at pushed commit `e30f567`; frozen install, Pages build, route smoke, and published hashes reproduced |

One Starlette TestClient transition warning is recorded in `docs/KNOWN_LIMITATIONS.md`; no test was skipped or muted.

## Post-release public UX refinement

| Command / review | Result |
|---|---|
| `pnpm --dir apps/web format:check` | PASS |
| `pnpm --dir apps/web test` | PASS, 2 story-first snapshot component tests |
| `pnpm --dir apps/web typecheck` | PASS |
| `pnpm --dir apps/web lint` | PASS, zero warnings |
| `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web build` | PASS, all public routes statically exported with GitHub Pages paths |
| `node tests/browser/snapshot-smoke.mjs` | PASS, guided homepage, honest evidence limits, and every public route present |
| `.venv/bin/python scripts/scan_public_build.py --path apps/web/out --strict` | PASS, no secret-like value or server-only credential name |
| `.venv/bin/python scripts/preflight.py --strict` | PASS, technical-preview claim requirements retained |
| In-app browser review at desktop width | PASS, product purpose, primary demo action, recorded boundaries, and laptop first viewport visually verified |
| GitHub `validate` workflow run `30175863829` | PASS, both `verify` and `replay-gates` jobs |
| GitHub Pages workflow run `30175863810` | PASS; production homepage, social image, Replay, Results, Architecture, and recorded-run routes returned HTTP 200 |

The redesign changes information architecture and presentation only. It does not add live-provider, connector, reviewer, held-out, or deployment evidence.

## Performance-led portfolio redesign

| Command / review | Result |
|---|---|
| `pnpm --dir apps/web format:check` | PASS |
| `pnpm --dir apps/web test` | PASS, 2 portfolio-story and evidence-boundary component tests |
| `pnpm --dir apps/web typecheck` | PASS |
| `pnpm --dir apps/web lint` | PASS, zero warnings |
| `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web build` | PASS, all public routes statically exported |
| `node tests/browser/snapshot-smoke.mjs` | PASS, builder attribution, release-gate definition, recorded provenance, proof limits, and every public route present |
| `.venv/bin/python scripts/scan_public_build.py --path apps/web/out --strict` | PASS, no secret-like value or server-only credential name |
| `.venv/bin/python scripts/preflight.py --strict` | PASS, technical-preview claim requirements retained |
| In-app browser review at desktop width | PASS, full first-viewport hierarchy, animated Replay engine, primary action, and recorded control room visually verified |
| GitHub `validate` workflow run `30176794288` | PASS, both `verify` and `replay-gates` jobs |
| GitHub Pages workflow run `30176794289` | PASS; production homepage, social image, Replay, Results, Architecture, and recorded-run routes returned HTTP 200 |
| Production browser review at `7b57e8b` | PASS, builder attribution, product definition, Replay visualization, recorded boundaries, and responsive first viewport verified on the published site |

The supplied dark technical reference was recreated with native HTML/CSS motion and deterministic content. No third-party animation runtime, hidden attribution, or runtime inference dependency was added.

## Post-release credibility hardening

| Command / review | Result |
|---|---|
| `pnpm --dir apps/web lint` | PASS, zero warnings |
| `pnpm --dir apps/web typecheck` | PASS |
| `pnpm --dir apps/web test` | PASS, 3 component tests |
| `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web build` | PASS, 12 exported HTML pages including the new audit route |
| `node tests/browser/snapshot-smoke.mjs` | PASS, all static routes and evidence-boundary copy |
| `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web e2e` | PASS, 9 Chromium core/nested navigation, interaction, keyboard, WCAG A/AA, and mobile-overflow tests |
| `.venv/bin/python -m pytest -q` | PASS, 134 tests; one documented Starlette transition warning |
| `.venv/bin/python scripts/scan_public_build.py --path apps/web/out --strict` | PASS |
| `.venv/bin/python scripts/verify_public_snapshots.py` | PASS |
| `.venv/bin/python scripts/preflight.py --strict` | PASS |
| `pnpm audit --prod --audit-level high` | PASS, no known production vulnerabilities |
| `pnpm audit --dev --audit-level critical` | PASS at the critical threshold; one high-severity development-only `brace-expansion` advisory remains documented |
| In-app browser review | PASS at desktop and 390px mobile widths for homepage, interactive Replay, and senior audit route |

These checks were local results for the source revision containing this record. Validation run
`30208242771` and Pages run `30208242773` later passed for the CI repair that includes this
hardening. No live provider call, connector write, or human validation is claimed.

## External work and credentials

- No Cohere key was available or required; no live model call was made.
- No Slack or Jira credential was accessed and no external write occurred.
- No paid resource was created.
- The performance-led portfolio redesign (`7b57e8b`) is pushed to `origin/main`; its validation and Pages publication workflows passed.
- The 2026-07-26 credibility-hardening revision passed validation run `30208242771` and Pages
  build/deploy run `30208242773` after the pnpm cache-cleanup repair.
- Static publication is verified at `https://tasfiqj.github.io/ResolveFlow/`. No live-provider/connector release or production-readiness verdict is claimed.

## Core evaluation-integrity audit

| Command / review | Result |
|---|---|
| `.venv/bin/ruff check python tests scripts/*.py` and format check | PASS |
| `.venv/bin/mypy python/resolveflow` | PASS, 81 source files |
| `.venv/bin/pytest -q tests/unit tests/integration tests/contract tests/security tests/replay` | PASS, 144 tests; one documented Starlette transition warning |
| `pnpm --dir apps/web lint`, format check, typecheck, and test | PASS, 3 component tests |
| `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web build` | PASS, 12 static pages |
| `node tests/browser/snapshot-smoke.mjs` | PASS |
| `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web e2e` | PASS, 9 Chromium/Axe tests |
| Replay smoke, negative gate, and integrity-audit reproduction | PASS; candidate remains `NO_SHIP`, audit is 1/36 truths, 0/200 full Replays, and 5/5 stored payload controls |
| public bundle scan, snapshot verifier, strict preflight | PASS |

These checks were local results for the source revision containing this record. Validation run
`30208242771` and Pages run `30208242773` passed after the CI repair. No current PostgreSQL,
container, dependency-audit, live-provider, connector, or human result is claimed.

## Immediate next action

Promote only after genuine human-authored truth review, locked held-out evidence, and the practitioner/language gates documented for `validated_release` are complete.
