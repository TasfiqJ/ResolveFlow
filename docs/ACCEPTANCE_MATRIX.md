# ResolveFlow Replay acceptance matrix

**Matrix version:** 1.1

**Planning date:** 2026-07-21

**Current evidence state:** Milestones 1-4 implemented; later held-out, Replay, and human evidence remains planned

This matrix maps every acceptance criterion in Features 1-18 to a future automated test or explicit human/operational evidence item. A path is a planned contract, not proof that the test exists or passes. Rows become `PASS` only when the cited command has run successfully against the recorded build and the evidence artifact is committed or linked.

Status values: `PLANNED`, `IN PROGRESS`, `PASS`, `FAIL`, `BLOCKED`, `NOT APPLICABLE` (reason required).

## Command conventions

- Python commands run from the repository root in the locked `uv` environment.
- Web browser commands run through the web workspace with `pnpm --dir apps/web exec playwright test <path>`.
- Evaluation commands require explicit versioned environment variables and never infer a candidate or dataset.
- Human evidence is stored under `eval/reports/evidence/<milestone>/<evidence-id>/` and includes method, date, build/dataset, reviewer context, privacy status, and exact counts.
- CI, live-provider, external-connector, deployment, latency, cost, and human-review success may not be inferred from a local fixture test.

## Functional-requirement coverage

| Requirement | Primary acceptance rows |
|---|---|
| FR-01 canonical web/Slack case | F01-AC01 through F01-AC05 |
| FR-02 named read-only context | F02-AC01 through F02-AC04 |
| FR-03 authorization before retrieval | F03-AC02; F04-AC01 through F04-AC05 |
| FR-04 hybrid retrieval and Rerank trace | F05-AC01 through F06-AC04 |
| FR-05 bounded Command and citations | F07-AC01 through F07-AC05 |
| FR-06 citation/ACL/version/freshness verification | F09-AC01 through F09-AC04 |
| FR-07 separate verified structuring | F08-AC01 through F08-AC04 |
| FR-08 approval and idempotent Jira proposal | F11-AC01 through F12-AC05 |
| FR-09 append-only trace | F13-AC01 through F13-AC04 |
| FR-10 frozen Replay and v0/v1 | F14-AC01 through F14-AC04 |
| FR-11 metrics, uncertainty, verdict | F15-AC01 through F15-AC04; F16-AC01 through F16-AC04 |
| FR-12 snapshots and bounded live mode | F18-AC01 through F18-AC05 |

## Feature 1 - Slack-style intake and real Slack sandbox

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F01-AC01 | Authenticity: invalid signatures and stale requests are rejected with an HTTP rejection and security audit event. | 4 | Slack signature/timestamp contract tests | `uv run pytest -q tests/contract/test_slack_events.py -k "invalid_signature or stale_timestamp"` | PLANNED |
| F01-AC02 | Idempotency: duplicate event delivery creates one case and returns the existing case reference. | 4 | concurrent/deduplicated intake integration test | `uv run pytest -q tests/integration/test_slack_intake.py -k duplicate_delivery` | PLANNED |
| F01-AC03 | Responsiveness: acknowledgement is independent of model latency; the case remains visibly queued. | 4 | delayed-provider contract test plus browser state | `uv run pytest -q tests/contract/test_slack_events.py -k acknowledgement_independent` and `pnpm --dir apps/web exec playwright test tests/browser/slack-style-queued.spec.ts` | PLANNED |
| F01-AC04 | Schema fidelity: web and Slack intake produce equivalent canonical cases. | 4 | golden canonical-case contract | `uv run pytest -q tests/contract/test_intake_parity.py` | PLANNED |
| F01-AC05 | Authorization: approval controls are ineffective for users without approval permission and emit an audit event. | 4 | API security and browser denial tests | `uv run pytest -q tests/security/test_action_authorization.py -k slack_control_denied` | PLANNED |

## Feature 2 - deterministic context enrichment

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F02-AC01 | No arbitrary SQL: tool input contains only a named query and typed values. | 4 | schema/allowlist negative tests | `uv run pytest -q tests/unit/context/test_query_contracts.py -k no_arbitrary_sql` | PLANNED |
| F02-AC02 | Replay fidelity: identical snapshot/as-of time yields identical structured tool-data hash. | 4 | canonical hash replay test | `uv run pytest -q tests/replay/test_context_fidelity.py` | PLANNED |
| F02-AC03 | Failure clarity: not-found, denied, timeout, and malformed data have distinct codes visible in UI/trace. | 4 | parameterized unit test and golden public trace | `uv run pytest -q tests/unit/context/test_result_codes.py tests/unit/telemetry/test_context_projection.py` | PLANNED |
| F02-AC04 | Tenant isolation: cross-tenant identifiers return no data. | 4 | two-tenant real-PostgreSQL integration test | `uv run pytest -q tests/integration/test_context_tenant_isolation.py` | PLANNED |

## Feature 3 - corpus ingestion, versioning, and effective time

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F03-AC01 | Reproducibility: re-ingestion yields identical chunk checksums. | 2 | idempotent ingestion integration test | `uv run pytest -q tests/integration/test_ingestion.py -k reingestion_checksums` | PASS |
| F03-AC02 | Temporal correctness: Replay at T0 sees only effective versions. | 2 | effective-time security replay | `uv run pytest -q tests/replay/test_effective_time.py` | PASS |
| F03-AC03 | Provenance: every chunk resolves to an artifact version and source position; otherwise it is excluded. | 2 | corpus quality and foreign-key test | `uv run pytest -q tests/integration/test_corpus_provenance.py` | PASS |
| F03-AC04 | Multimodal trace: shipped image evidence retains original image and metadata; otherwise the visual case is marked unavailable. | 2 | modality contract test or recorded feature-disabled result | `uv run pytest -q tests/contract/test_image_artifact.py` | PASS |

## Feature 4 - pre-retrieval authorization and role switch

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F04-AC01 | Forbidden candidate exposure is zero across declared held-out role replays. | 2/5 | stage-by-stage security results with exact N | `uv run pytest -q tests/security/test_forbidden_candidate.py` and `uv run python -m resolveflow.evaluation.cli invariant --id no_forbidden_candidate --bundle "$RESULT_BUNDLE"` | IN PROGRESS |
| F04-AC02 | Forbidden model input is zero. | 2/5 | model-request projection scan | `uv run pytest -q tests/security/test_forbidden_model_input.py` | PASS |
| F04-AC03 | Forbidden citation is zero. | 2/5 | verifier security test and held-out invariant | `uv run pytest -q tests/security/test_forbidden_citation.py` | IN PROGRESS |
| F04-AC04 | Cache isolation: role or tenant change cannot reuse ineligible candidates. | 2 | property and integration cache tests | `uv run pytest -q tests/security/test_retrieval_cache_isolation.py` | PASS |
| F04-AC05 | Explainability: trace shows a safe policy reason without leaking source title/content. | 2 | golden redaction projection plus reviewer check | `uv run pytest -q tests/unit/policy/test_public_reason_codes.py tests/security/test_restricted_title_redaction.py` | PASS |

## Feature 5 - hybrid retrieval with Embed v4

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F05-AC01 | Decisive evidence: held-out Recall@10 is measured against the preregistered baseline and published whether it passes or fails. | 2/5 | raw case-level retrieval bundle | `uv run python -m resolveflow.evaluation.cli retrieval --dataset "$DATASET_VERSION" --builds lexical,embed,hybrid,hybrid-rerank --output "$RESULT_DIR"` | IN PROGRESS |
| F05-AC02 | Identifier preservation: exact error-code evidence remains retrievable. | 2 | targeted lexical/hybrid regression | `uv run pytest -q tests/integration/test_retrieval_identifiers.py` | PASS |
| F05-AC03 | Authorization: search plans include the eligibility predicate. | 2 | SQL/query-plan security test | `uv run pytest -q tests/integration/test_authorized_search_plan.py` | PASS |
| F05-AC04 | Trace completeness: candidates retain vector, lexical, and fused ranks where applicable. | 2 | candidate serialization test | `uv run pytest -q tests/integration/test_retrieval_trace.py` | PASS |

## Feature 6 - Rerank v4 Fast-Pro decision policy

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F06-AC01 | Pairing: Fast and Pro receive identical authorized candidate payloads. | 2/5 | payload-ID/order/hash contract test | `uv run pytest -q tests/contract/test_rerank_pairing.py` | PASS |
| F06-AC02 | Statistical honesty: results show estimates, exact N, and uncertainty, not selected winners. | 5 | result-schema/report validation | `uv run pytest -q tests/unit/evaluation/test_paired_intervals.py tests/unit/evaluation/test_report_claims.py` | PLANNED |
| F06-AC03 | Policy clarity: every Pro call has a declared escalation reason. | 2 | model-policy unit/telemetry test | `uv run pytest -q tests/unit/retrieval/test_rerank_policy.py -k escalation_reason` | PASS |
| F06-AC04 | Operational budget: public live mode never makes an uncontrolled double call. | 6 | live-budget security test | `uv run pytest -q tests/security/test_public_rerank_budget.py` | PLANNED |

## Feature 7 - bounded Command A+ agent loop

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F07-AC01 | Tool schema validity: every accepted call conforms locally; invalid calls are failures. | 3 | property/schema tests | `uv run pytest -q tests/unit/agent/test_tool_validation.py` | PASS |
| F07-AC02 | Tool authorization: unauthorized attempts reach no adapter. | 3 | spy-adapter security test | `uv run pytest -q tests/security/test_tool_authorization.py` | PASS |
| F07-AC03 | Bounded execution: every run terminates within configured rounds and timeout. | 3 | fake-clock budget tests | `uv run pytest -q tests/unit/agent/test_budgets.py` | PASS |
| F07-AC04 | Direct writes: zero model-triggered Jira writes. | 3/4 | architecture and adapter-call security test | `uv run pytest -q tests/security/test_no_model_connector_write.py` | PASS |
| F07-AC05 | Unknown handling: missing decisive evidence yields abstention or review. | 3 | replay and browser test | `uv run pytest -q tests/replay/test_missing_decisive_evidence.py` | PASS |

## Feature 8 - evidence graph and two-pass structured response

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F08-AC01 | Source closure: every final material claim maps to a verified evidence-graph fact. | 3 | graph traversal invariant | `uv run pytest -q tests/unit/verifier/test_source_closure.py` | PASS |
| F08-AC02 | Schema validity is measured; invalid output never appears as normal success. | 3/5 | structure contract results and status test | `uv run pytest -q tests/contract/test_structured_pass.py -k invalid_output` | IN PROGRESS |
| F08-AC03 | No new tool access: the second pass has no tools or original documents. | 3 | provider-request contract fixture | `uv run pytest -q tests/contract/test_structured_pass.py -k no_tools_no_documents` | PASS |
| F08-AC04 | Deterministic renderer: identical validated JSON renders identically. | 3 | snapshot/golden test | `uv run pytest -q tests/unit/agent/test_renderer.py` | PASS |

## Feature 9 - claim-level citation and freshness verifier

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F09-AC01 | Unauthorized citation count is zero. | 3/5 | verifier security invariant | `uv run pytest -q tests/security/test_forbidden_citation.py` | IN PROGRESS |
| F09-AC02 | Missing source: no material claim ships without a source or explicit unknown; unsupported action claims block. | 3 | material-claim gate tests | `uv run pytest -q tests/unit/verifier/test_material_claims.py` | PASS |
| F09-AC03 | Stale support: stale evidence cannot support a current action when current evidence is required. | 3 | freshness replay | `uv run pytest -q tests/replay/test_stale_action_support.py` | PASS |
| F09-AC04 | Human agreement: a stratified reviewed sample reports verifier precision and disputed cases before a strong grounding claim. | 6 | HUMAN-F09-VERIFIER-REVIEW | Human item: exact claim sample, independent labels, adjudication/disagreements, build/dataset, and signed publication scope | PLANNED |

## Feature 10 - indirect prompt-injection defense

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F10-AC01 | Forbidden effect: zero successful forbidden disclosures/writes in the declared held-out security replays, with exact N/interval. | 3/5 | attack-family invariant bundle | `uv run python -m resolveflow.evaluation.cli security --dataset "$DATASET_VERSION" --lock "$MANIFEST_LOCK_HASH" --output "$RESULT_DIR"` | IN PROGRESS |
| F10-AC02 | Policy mutation: evidence text never changes tool list, ACL, approval, or gates. | 3 | immutable-control security tests | `uv run pytest -q tests/security/test_evidence_cannot_mutate_policy.py` | PASS |
| F10-AC03 | Attack observability: scenario and attempted concrete effect appear in the trace. | 3 | golden hostile trace | `uv run pytest -q tests/replay/test_attack_observability.py` | PASS |
| F10-AC04 | Legitimate evidence use: safe technical facts from a hostile source may remain usable only when independently verified. | 3 | mixed-content verifier test | `uv run pytest -q tests/replay/test_hostile_mixed_content.py` | PASS |

## Feature 11 - approval-gated Jira proposal

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F11-AC01 | Unapproved write count is zero. | 4/5 | state-machine and hard-gate test | `uv run pytest -q tests/security/test_no_unapproved_write.py` | PASS |
| F11-AC02 | Payload integrity: dispatched payload hash equals the approved proposal hash. | 4 | digest/reconstruction and tamper tests | `uv run pytest -q tests/unit/actions/test_proposal_state.py tests/integration/test_action_faults.py` | PASS |
| F11-AC03 | Authorization: only `approve_jira` users can approve. | 4 | permission matrix and API test | `uv run pytest -q tests/unit/actions/test_proposal_state.py tests/integration/test_api.py -k action` | PASS |
| F11-AC04 | Expiration: expired proposals cannot dispatch. | 4 | fake-clock state and dispatch test | `uv run pytest -q tests/unit/actions/test_proposal_state.py tests/integration/test_action_faults.py -k expired` | PASS |
| F11-AC05 | Public safety: public production has no credential capable of Jira write. | 4/6 | startup configuration and disabled adapter tests | `uv run pytest -q tests/unit/test_config.py tests/security/test_no_unapproved_write.py` | PASS |

## Feature 12 - idempotent connector execution and recovery

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F12-AC01 | Duplicate issue count is zero across forced timeout and retry tests. | 4 | forced timeout/ack-loss reconciliation suite | `uv run pytest -q tests/integration/test_action_faults.py -k uncertain_send` | PASS |
| F12-AC02 | Lost approved action count is zero in restart tests within configured retention. | 4 | durable lease/reclaim PostgreSQL suite | `uv run pytest -q tests/postgres/test_action_jobs.py -k reclaim` | PASS |
| F12-AC03 | Backoff is bounded and observable. | 4 | fake-clock retry unit test | `uv run pytest -q tests/unit/actions/test_retry_policy.py` | PASS |
| F12-AC04 | Dead letter: permanent failures reach dead letter with an operator-readable reason. | 4 | fault/dead-letter integration test | `uv run pytest -q tests/integration/test_action_faults.py -k "dead_letter or permission"` | PASS |
| F12-AC05 | Worker crash: another worker safely reclaims expired work after a crash. | 4 | concurrent PostgreSQL lease test | `uv run pytest -q tests/postgres/test_action_jobs.py -k reclaim` | PASS |

## Feature 13 - complete audit trace and run diff

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F13-AC01 | Reconstructability: a maintainer can explain final route/action from stored events alone. | 4 | deterministic event-only reconstruction test | `uv run pytest -q tests/unit/telemetry/test_audit_export_diff.py -k reconstructable` | PASS |
| F13-AC02 | Redaction: public trace exposes no secrets, tokens, hidden prompts, restricted content, or private paths. | 4/6 | deterministic redaction and export tests | `uv run pytest -q tests/security/test_public_trace_redaction.py tests/unit/telemetry/test_audit_export_diff.py` | PASS |
| F13-AC03 | Ordering: event sequence is stable and timestamps are coherent. | 4 | hash-chain/order plus database append-only tests | `uv run pytest -q tests/unit/telemetry/test_audit_export_diff.py tests/postgres/test_action_jobs.py -k audit` | PASS |
| F13-AC04 | Diff accuracy: a known role/corpus mutation appears exactly once in the comparison. | 4/5 | immutable foundation diff test | `uv run pytest -q tests/unit/telemetry/test_audit_export_diff.py -k diff` | PASS |

## Feature 14 - Replay scenario compiler

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F14-AC01 | Deterministic materialization: same manifest/fixture yields identical non-model hashes. | 5 | repeat materialization test | `uv run pytest -q tests/replay/test_materialization_determinism.py` | PLANNED |
| F14-AC02 | Production parity: Replay invokes the same orchestrator and verifier. | 5 | architecture spy/contract test | `uv run pytest -q tests/replay/test_production_path_parity.py` | PLANNED |
| F14-AC03 | Mutation isolation: undeclared inputs remain unchanged. | 5 | before/after canonical snapshot property test | `uv run pytest -q tests/replay/test_mutation_isolation.py` | PLANNED |
| F14-AC04 | Invalid manifests fail before any provider call with a clear report. | 5 | spy-provider schema tests | `uv run pytest -q tests/replay/test_manifest_validation.py` | PLANNED |

## Feature 15 - readiness gate and CI release decision

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F15-AC01 | Pre-registration: gate-file commit predates final held-out results. | 5 | Git chronology integrity test | `uv run pytest -q tests/replay/test_evaluation_chronology.py` | PLANNED |
| F15-AC02 | Hard-gate behavior: a seeded forbidden citation blocks release. | 5 | negative gate test and CI artifact | `uv run pytest -q tests/replay/test_release_gate_negative.py -k forbidden_citation` | PLANNED |
| F15-AC03 | Reproducibility: local and CI aggregation produce identical verdict/hash from identical records. | 5 | reproducibility test | `uv run pytest -q tests/replay/test_verdict_reproducibility.py` | PLANNED |
| F15-AC04 | Failure evidence: verdict links to every failing replay. | 5/6 | bundle schema and results-page test | `uv run pytest -q tests/unit/evaluation/test_failure_links.py` | PLANNED |

## Feature 16 - human review and practitioner scoring

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F16-AC01 | Blinding: review UX exposes no build/model labels and gold route is hidden until submission. | 6 | browser and export-schema tests | `pnpm --dir apps/web exec playwright test tests/browser/review-blinding.spec.ts` | PLANNED |
| F16-AC02 | Domain fit: relevant reviewer roles are genuinely collected and disclosed in aggregate. | 6 | HUMAN-F16-DOMAIN-FIT | Human item: consented aggregate role/familiarity table with exact reviewer/case counts | PLANNED |
| F16-AC03 | No fabricated scale: exact reviewer and case counts appear beside every percentage. | 6 | report assertion plus real review export | `uv run pytest -q tests/unit/evaluation/test_human_review_reporting.py -k exact_counts` | PLANNED |
| F16-AC04 | Disagreements: at least one genuine reviewer disagreement is discussed. | 6 | HUMAN-F16-DISAGREEMENT | Human item: disagreement excerpt/adjudication linked to anonymized review IDs; if none occurs, report that fact rather than inventing one and keep this row unmet | PLANNED |

## Feature 17 - one validated multilingual slice

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F17-AC01 | Human validation: a fluent reviewer signs the query, terminology, and gold meaning. | 6 | HUMAN-F17-LANGUAGE-SIGNOFF | Human item: reviewer fluency basis, signed variant checksums, terminology/gold review, date | PLANNED |
| F17-AC02 | Slice reporting: results are reported separately by language configuration. | 6 | result-schema/report test | `uv run pytest -q tests/unit/evaluation/test_language_slice_reporting.py` | PLANNED |
| F17-AC03 | Security parity: identical ACL and action hard gates apply to every language condition. | 6 | parameterized security replay | `uv run pytest -q tests/security/test_language_security_parity.py` | PLANNED |
| F17-AC04 | Scope honesty: public copy says `validated <language> slice`, never broad multilingual performance. | 6 | public-copy preflight | `uv run pytest -q tests/security/test_public_claims.py -k multilingual_scope` | PLANNED |

## Feature 18 - snapshot-first public mode and rate-limited live mode

| ID | Criterion / pass condition | Milestone | Planned evidence | Exact command or human item | Status |
|---|---|---:|---|---|---|
| F18-AC01 | First load: hero scenario works without any provider call. | 1/6 | network-spy browser test | `pnpm --dir apps/web exec playwright test tests/browser/snapshot-first.spec.ts` | PLANNED |
| F18-AC02 | Secret isolation: the browser bundle contains no Cohere, Slack, Jira, database, token, cookie, or secret material. | 6 | build scan | `uv run python scripts/scan_public_build.py --path apps/web/out --strict` | PLANNED |
| F18-AC03 | Abuse resistance: only predefined input is accepted and rate/concurrency limits are enforced when local live mode is enabled. | 6 | API security/load contract | `uv run pytest -q tests/security/test_public_live_limits.py` | PLANNED |
| F18-AC04 | Honest provenance: snapshot and live runs are unmistakably distinguished. | 6 | browser accessibility/provenance assertions | `pnpm --dir apps/web exec playwright test tests/browser/run-provenance.spec.ts` | PLANNED |
| F18-AC05 | Graceful degradation: provider/API/database/connector degradation leaves a complete honest snapshot demo. | 6 | chaos browser journey | `pnpm --dir apps/web exec playwright test tests/browser/degraded-snapshot.spec.ts` | PLANNED |

## Cross-cutting milestone evidence

| ID | Evidence | Exact command/item | Milestone | Status |
|---|---|---|---:|---|
| X-00 | Planning sources, checksums, all 78 acceptance mappings, ADR structure, links, JSON/shell syntax, and secret hygiene validate without external credentials | `scripts/verify.sh` | 0 | PASS |
| X-01 | Credential-free foundation verification: locked setup, seed/snapshot, static/unit/integration/browser checks, preflight, and local PostgreSQL migration cycle | `scripts/verify.sh` | 1 | PASS |
| X-02 | Empty-to-head and reversible migration check | `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` | 1+ | PASS |
| X-03 | Repository and public-build secret scan | `gitleaks detect --source . --no-banner --redact` and `uv run python scripts/scan_public_build.py --path apps/web/out --strict` | every milestone / 7 | PLANNED |
| X-04 | Locked candidate evaluation | `uv run python -m resolveflow.evaluation.cli evaluate --candidate "$CANDIDATE_BUILD" --baseline "$BASELINE_BUILD" --dataset "$DATASET_VERSION" --lock "$MANIFEST_LOCK_HASH"` | 5/7 | PLANNED |
| X-05 | Report regenerated without provider calls | `uv run python -m resolveflow.evaluation.cli report --bundle "$RESULT_BUNDLE" --output eval/reports` | 5/7 | PLANNED |
| X-06 | Restore snapshot experience on a clean machine | OPS-X06-RESTORE with machine/runtime, commands, hashes, observed result, and discrepancies | 7 | PLANNED |
| X-07 | Every public link/private-browser/mobile route checked | `pnpm --dir apps/web exec playwright test tests/browser/public-release.spec.ts` | 7 | PLANNED |
| X-08 | Final claim and placeholder audit | `uv run python scripts/preflight.py --strict` | 7 | PLANNED |

## Update rules

1. Change a row to `IN PROGRESS` only in the active milestone.
2. `PASS` requires the exact command result or named human artifact and the build/commit it applies to.
3. A command changed during implementation requires a same-commit update to this matrix and `docs/IMPLEMENTATION_PLAN.md`.
4. A hard-gate failure stays `FAIL` and is linked from the verdict; it is never removed by deleting the scenario.
5. Credential-dependent live evidence supplements but does not replace deterministic/contract coverage.
6. Human-only rows remain `PLANNED` or `BLOCKED` when genuine reviewers are absent; no synthetic substitute is accepted.
7. After each milestone, record the commands actually run and their results in `docs/CODEX_STATUS.md` without inventing unrun checks.
