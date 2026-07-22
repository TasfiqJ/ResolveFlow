# ResolveFlow Replay decisions and discovery register

**Log version:** 1.3

**Last updated:** 2026-07-22

This file records reversible planning assumptions, contradictions, blockers, and implementation-time facts that must be discovered. Architecture decisions with long-lived consequences are expanded in `docs/adr/`.

## 1. Decisions made during planning

| ID | Decision | Reason | Reversal trigger |
|---|---|---|---|
| D-001 | Use the seven user-named milestones in order. | The current task is authoritative over the PDF's week/phase labels. | User supplies a replacement milestone sequence. |
| D-002 | Keep Resolve and Replay on one orchestrator, policy, retrieval, verifier, action, and audit path. | Replay must test production behavior, not a benchmark shortcut. | None for v1; a future architecture would need parity evidence. |
| D-003 | Use a modular Python monolith, one worker process, one PostgreSQL/pgvector database, and one Next.js app. | Small workload, inspectability, transaction safety, and zero-cost local operation. | Measured scaling/isolation/team boundary makes an additional service necessary. |
| D-004 | Make GitHub Pages static snapshots the only required public deployment. | The governing prompt requires zero spend and no public write credential. | A later task approves a verified zero-cost backend with no billing instrument and no launch risk. |
| D-005 | Use fixture/synthetic adapters by default; real Slack/Jira adapters are implemented but disabled. | Credentials are unavailable by default and real writes need explicit authorization. | Existing sandbox credentials plus an explicit task authorizing the exact external write. |
| D-006 | Treat generated truth data as `synthetic_agent_authored` with `human_review_status: pending`. | The autonomous prompt forbids calling model/agent-generated data human-authored. | Genuine human review updates provenance without rewriting the original author field. |
| D-007 | Default all public quality claims and the hero case to English. | A fluent reviewer is not established. | A fluent reviewer signs a bounded language slice. |
| D-008 | Keep image evidence optional after the typed modality boundary exists. | Core safety/evaluation work has priority and the master prompt explicitly permits this cut. | Text/PDF/SQL/ticket core is complete and the image adds a measured contradiction case. |
| D-009 | Do not select final hero IDs/error codes during planning. | Source documents conflict (`E-417` and `PYM-431`; HelioPay and Northstar-style IDs). | Milestone 1 records a single coherent fixture decision before implementation. |
| D-010 | Use uppercase planning filenames requested by the task (`DECISIONS.md`, etc.). | Explicit current-task output contract. | Repository later adopts and migrates to a documented naming convention. |
| D-011 | Preserve all measured values as unknown until artifacts exist. | No tests, provider calls, reviewers, or deployments have occurred. | Actual evidence with build/dataset/method/date exists. |
| D-012 | Store the discovered 87-page master PDF at the required repository path and record its checksum. | The repository bundle initially omitted the named path, but the authoritative file existed in the supplied local build pack. | A verified newer master-plan version supersedes it with an explicit source record. |
| D-013 | Work on `main` only. | Latest user instruction explicitly prohibits subbranches. | User explicitly changes the Git workflow again. |
| D-014 | Do not add product code in this planning task. | Explicit task boundary. | A later task names Milestone 1. |
| D-015 | Make `scripts/verify.sh` dependency-light in Stage 00 and expand it cumulatively with each milestone. | The outer loop needs an executable verifier now, while product toolchains and lockfiles do not exist yet. | Milestone 1 expands it with locked toolchain commands while preserving all current checks and the no-credential default. |
| D-016 | Lock the canonical hero to fictional HelioPay, `PYM-431`, `rollout-payments-2026-07-15`, `payments-api`, `ca-central`, and Payments Platform. | This is internally consistent with the governing master prompt and preserves the deliberately missing cluster ID. | A new versioned fixture supersedes the hero before evaluation lock. |
| D-017 | Use deterministic string IDs in the Stage 01 fixture and defer the production sortable-ID generator choice. | Recorded fixture identifiers must be stable; UUIDv7/ULID behavior is not needed until runtime persistence creates arbitrary objects. | Milestone 2 or 4 introduces runtime-generated persisted identifiers. |
| D-018 | Canonicalize JSON with sorted keys, compact UTF-8, NFC strings, and UTC timestamps at second precision; prefix hashes with `sha256:`. | The foundation snapshot needs reproducible, explainable content hashes without security-sensitive floating point values. | A versioned canonicalization schema is required for additional numeric evidence. |
| D-019 | Keep the Stage 01 verifier fixture-backed and explicitly label it `fixture_supported`. | A complete no-key vertical slice is required, while claim-level semantic verification belongs to Milestone 3. | Milestone 3 replaces the fixture verifier behind the same typed boundary. |
| D-020 | Use Python 3.13 in containers and lockfiles while retaining Python 3.10 source compatibility for the current development host. | uv verified Python 3.13.14 and all selected dependencies; broader developer compatibility remains useful for the package. | A dependency or language feature requires raising the minimum after compatibility tests. |

## 2. Contradiction register

| ID | Sources in tension | Planning treatment | Status |
|---|---|---|---|
| C-001 | PDF/overview: Vercel + Railway + Neon; master prompt: zero spend + GitHub Pages | Higher-priority master prompt wins; dynamic stack is local, public is static Pages. | RESOLVED BY ADR-012 |
| C-002 | Feature docs: real Slack/Jira demonstration required; master prompt: treat credentials unavailable and keep adapters disabled | Implement full boundaries/contracts/synthetic state machines; live evidence is optional and credential/task-authorized. | RESOLVED BY ADR-009 |
| C-003 | PDF: 36 human-authored truths; master prompt: autonomous output must not be called human-authored | Use synthetic-agent-authored candidates with pending human review. | RESOLVED BY ADR-010 |
| C-004 | PDF/master docs use English/French hero variations and different error/customer IDs | Milestone 1 locked the English HelioPay/PYM-431 fixture in D-016. | RESOLVED IN M1 |

## 2.1 Milestone 1 discovered facts

| Fact IDs | Recorded value | Evidence |
|---|---|---|
| U-001 | Node 24.18.0, pnpm 10.32.0, Next.js 16.2.11, React 19.2.8, TypeScript 5.9.2, Vitest 3.2.4 are locked for the foundation. | Runtime output, npm registry metadata retrieved 2026-07-21, `pnpm-lock.yaml` |
| U-002 | Python 3.13.14 lock environment; FastAPI 0.116.1, Pydantic 2.13.4, SQLAlchemy 2.0.43, Alembic 1.16.5, asyncpg 0.30.0, Ruff 0.12.11, mypy 1.17.1, pytest 8.4.1. | `uv.lock`, successful local checks on 2026-07-21 |
| U-003 | PostgreSQL 17-compatible pgvector development image `pgvector/pgvector:pg17`; tag is locked but its immutable digest remains a Milestone 7 hardening item. | Successful Compose health and reversible migration cycle on 2026-07-21 |
| U-008-U-010 | Fictional HelioPay tenant/customer, values in D-016, canonical web case schema, and only one missing-field clarification (`cluster_id`). | `data/truths/hero-payments-001.json`, domain tests |
| U-012-U-013 | Canonicalization is D-018; schema version is `1.0`; initial event names are the six public trace events in the fixture. | Hash and orchestration tests |
| U-067 | Liveness is process health; readiness validates configuration. Database dependency readiness remains for the persistence milestone. | FastAPI integration tests |
| C-005 | Overview treats image evidence as shipped; master prompt calls it optional after core | Keep schema/adapter boundary; ship only if core and accessibility gates are complete. | RESOLVED FOR PLAN |
| C-006 | PDF permits public live mode with daily spend stop; hard rule is spend exactly zero | Live is off; only a confirmed zero-charge key and hard call counter may enable a bounded local/staging subset. | RESOLVED BY ADR-009/012 |
| C-007 | PDF phase/week sequence differs from the task's seven milestone names | Task milestone names/order govern; features are remapped without changing their dependencies. | RESOLVED |
| C-008 | PDF ADR-012 recommends Vercel/Railway/managed PostgreSQL; master prompt requires GitHub Pages | This plan's ADR-012 supersedes the PDF recommendation for this repository. | RESOLVED |
| C-009 | Feature 14 says human-authored base truth; governing prompt requires synthetic-agent-authored truth | Replay schema uses neutral `truth` terminology; provenance carries the accurate authoring status. | RESOLVED |
| C-010 | PDF suggests measured service objectives before evidence exists | Keep them as unverified candidate targets; do not publish until observation windows and methods exist. | OPEN FOR CALIBRATION |

## 3. Blockers and stop conditions

| ID | Condition | Effect | Required action |
|---|---|---|---|
| B-001 | Any task would spend money or require a billing instrument. | Stop that path. | Record the optional capability and use local/static fallback. |
| B-002 | Real Slack/Jira write is not explicitly authorized in the active task. | Connector remains disabled/synthetic. | Do not request or use write credentials. |
| B-003 | Held-out data has been locked and a change is proposed. | Existing results become non-comparable. | Stop, create a new dataset/evaluation version, and document why. |
| B-004 | A public claim lacks actual source artifact, method, build, and exact N where applicable. | Publication is blocked. | Remove or narrow the claim. |
| B-005 | A secret, restricted content, or real customer data is found. | Commit/publication is blocked. | Preserve evidence safely, rotate/revoke if necessary, remove from output/history using an explicitly approved safe process. |
| B-006 | A hard invariant fails. | Candidate verdict is `NO_SHIP`; no override for portfolio release. | Retain the scenario/evidence and fix in the correct milestone or publish the failure. |
| B-007 | No genuine reviewer exists for a human-only criterion. | Corresponding claim stays unevidenced. | Ship the workflow/rubric and disclose `not yet completed`. |

## 4. Implementation-time fact register

Every entry must be filled with `value`, `source`, `retrieved/measured date`, `owner`, and affected configuration/ADR. Values are never guessed.

### 4.1 Repository and toolchain

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-001 | Current stable compatible Node.js, Next.js, React, TypeScript, pnpm, Tailwind, UI primitives, Playwright, and Vitest versions | 1 |
| U-002 | Current stable compatible Python, uv, FastAPI, Pydantic, SQLAlchemy, Alembic, asyncpg, Ruff, Pyright, pytest, and Testcontainers versions | 1 |
| U-003 | Supported PostgreSQL/pgvector versions and pinned local container digest | 1 |
| U-004 | GitHub Actions versions/commit SHAs, Pages configuration, repository settings, default branch rules, free allowance, and artifact retention | 1/6 |
| U-005 | License selection and dependency-license compatibility | 1/7 |
| U-006 | Availability and locked versions of gitleaks, pip-audit, JavaScript audit, SBOM, and container scanning tools | 1/7 |
| U-007 | Windows/Linux/macOS developer support boundary and exact clean-clone bootstrap prerequisites | 1 |

### 4.2 Canonical product fixture and schemas

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-008 | Canonical fictional tenant/customer ID and display name | 1 |
| U-009 | Canonical hero error code, rollout ID, service/team enum, region enum, severity enum, and timestamps | 1 |
| U-010 | Final canonical case required/optional fields and the one allowable clarification rule | 1 |
| U-011 | Exact stable-ID format choice (UUIDv7 vs ULID) and library behavior | 1 |
| U-012 | Canonical JSON/hashing rules, time precision, Unicode normalization, numeric normalization, and checksum prefix format | 1 |
| U-013 | Initial schema versions, error-code catalog, audit event names, and public-safe reason codes | 1 |
| U-014 | Final case/run/job/action state transition tables and cancellation/expiry edge cases | 1/4 |
| U-015 | Session/auth mechanism for local maintainer mode; public snapshots require no auth | 1/6 |

### 4.3 Corpus and retrieval

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-016 | Exact synthetic artifact inventory, titles, owners, classifications, regions, effective intervals, and license/provenance | 2 |
| U-017 | Parser/chunker libraries and versions, chunk target/overlap, parser quality codes, and whether OCR is genuinely needed | 2 |
| U-018 | Corpus size, embedding count/storage, and whether exact vector search or an index is appropriate | 2 |
| U-019 | Current Cohere Embed model ID, supported input fields/types/dimensions, limits, and SDK response shape | 2 before adapter |
| U-020 | Selected embedding dimension after development/calibration evidence | 2 |
| U-021 | Query template, candidate K, diversity cap, reciprocal-rank-fusion constant, and tie handling | 2 |
| U-022 | Retrieval cache scope/TTL and immutable cache-key fields | 2 |
| U-023 | Development/calibration decisive-evidence labels and lexical/vector failure fixtures | 2 |
| U-024 | Actual Recall@5/10, nDCG@10, rank movement, and retrieval latency; unknown until evaluation | 2/5 |
| U-025 | Whether the image condition ships and, if so, its accessible description and human gold interpretation | 2/6 |

### 4.4 Cohere model orchestration

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-026 | Current Command, Rerank Fast, and Rerank Pro model IDs and supported request/response fields | 3 before adapter |
| U-027 | Current official SDK version, V2 citations/tools/documents/strict-tools behavior, structured-output constraint, errors, retries, and usage fields | 3 |
| U-028 | Confirmed zero-charge key status, request/monthly quotas, rate limits, billing observability, and whether any live calls are safe | 3/5; before first live call |
| U-029 | Maximum calls per run, total call cap, wall-clock/tool/round/token limits, timeout classes, and retry policy | 3 calibration |
| U-030 | Final prompt bundle, tool descriptions, schema hashes, low-temperature settings, and seed semantics | 3 |
| U-031 | Rerank top-N, Fast/Pro identical payload contract, ambiguity proxy, escalation threshold, and paired subset | 2/5 |
| U-032 | Actual provider latency, usage, cost/billing evidence, schema-valid rate, completion, and error distribution | 5/7 after real calls, if any |

### 4.5 Authorization, verification, and security

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-033 | Synthetic role/classification/region policy table, deny precedence, and monotonicity expectations | 2 |
| U-034 | Exact data-access database roles/views/assertions and query-plan verification method | 2 |
| U-035 | Material-claim taxonomy, deterministic support/freshness/contradiction rules, and required-current-source classes | 3 |
| U-036 | Whether any secondary semantic entailment helper is needed; if used, its rubric/model/limits/human sample | 3/6 |
| U-037 | Attack-family taxonomy, split strategy, held-out payload authorship, and exact observable forbidden-effect schema | 3/5 |
| U-038 | Public redaction patterns, entropy threshold, approved synthetic identifiers, and retention/purge policy | 4/6 |
| U-039 | Threat-model residual risks and dependency/container findings at release | 6/7 |

### 4.6 Slack and Jira

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-040 | Current Slack signature/timestamp/event/challenge contract and official SDK/Bolt versions | 4 before adapter |
| U-041 | Slack app scopes, workspace/app/user mappings, acknowledgement timing, raw-payload retention, and revoked-token behavior if a sandbox exists | 4/6 credential-dependent |
| U-042 | Current Jira Cloud issue-create/query/OAuth fields and API versions | 4 before adapter |
| U-043 | Jira development project ID/key, field mapping, allowed priority/team values, scopes, credential type, and token handling if credentials exist | 4/6 credential-dependent |
| U-044 | Jira-side idempotency marker/reconciliation query supported by the selected project and its limitations | 4 credential-dependent |
| U-045 | Retry intervals, maximum attempts, lease duration/renewal, dead-letter retention, demo retry timing, and operator cancellation safety | 4 |
| U-046 | Real Slack/Jira integration results; none may be claimed until run evidence exists | 6/7 |

### 4.7 Replay, evaluation, and gates

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-047 | Final truth schema, 36 candidate truth contents, provenance, split IDs, and lock date | 5 |
| U-048 | Manifest schema version, mutation compatibility rules, fixture hashes, model/retry modes, and dry-run output | 5 |
| U-049 | Final baseline/candidate build definitions and immutable build hashes | 5 |
| U-050 | Calibration results used to freeze thresholds, metric version, missing-run/retry/exclusion policy, and minimum claim sample sizes | 5 |
| U-051 | Final hard/quality/operations gate values after calibration and before held-out inspection | 5 |
| U-052 | Exact number and cluster distribution of deterministic security, contract, and live scenarios | 5 |
| U-053 | Actual route accuracy, abstention, citation, schema, reliability, latency, and completion results with intervals | 5/7 |
| U-054 | Actual verdict and every failing case; no verdict exists during planning | 5/7 |
| U-055 | Genuine guarded-candidate failure selected for the postmortem | 7 |

### 4.8 Human validation and public product

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-056 | Practitioner/reviewer availability, roles, consent, dates, sample size, and feedback | 6 |
| U-057 | Truth-label, verifier-sample, and blinded-review human results and disagreements | 6 |
| U-058 | Whether a fluent reviewer exists, chosen language, fluency basis, signed variants, and exact per-condition sample | 6 |
| U-059 | Accessibility review results, supported browsers/viewports, reduced-motion behavior, and human usability findings | 6 |
| U-060 | Static asset base path, final public bundle size/pagination threshold, and measured performance | 6 |
| U-061 | Whether optional live mode is enabled locally/staging, with rate/concurrency/global limits and verified zero-charge budget | 6 |
| U-062 | Actual public URL, Pages workflow result, HTTP/private-browser/link verification, and observation window | 6/7 only if deployment authorized |
| U-063 | Demo-media tooling/output format, captions/transcript, recording integrity, size, and hosting path | 6 |
| U-064 | Privacy/analytics choice, session/log retention, IP hashing/rotating salt, contact/reporting route | 6 |
| U-065 | Real human-review acceptance/edit-effort results; absent until collected | 6 |

### 4.9 Operations and release

| ID | Fact to discover | Earliest milestone |
|---|---|---:|
| U-066 | Local container base digests, non-root/read-only compatibility, termination grace behavior, and SBOM output | 1/7 |
| U-067 | Health/readiness dependency semantics, startup validation, kill-switch behavior, and operator incident-ID format | 1/4 |
| U-068 | Backup/export/restore artifact set, rollback window, irreversible migration decisions, and recovery time observed | 7 |
| U-069 | Log/trace/provider-payload retention, purge/revoke commands, credential inventory, and rotation drill results | 6/7 |
| U-070 | GitHub Actions results, required-check settings, artifact retention, Pages status, tag/release state | 7 |
| U-071 | Actual dependency/secret/container scan findings and resolution status | every milestone / 7 |
| U-072 | Exact billed spend; may be stated only from billing evidence. Otherwise use the mandated inability-to-query wording. | 7 |
| U-073 | Final commit SHA, remote synchronization, release tag, rollback target, and public artifact checksums | 7 |

## 5. Discovery update template

```text
Fact ID:
Value:
Source or measurement artifact:
Retrieved/measured at:
Owner:
Affected files/configuration:
Decision or ADR impact:
Remaining uncertainty:
```

Do not delete resolved unknowns. Add the value and evidence so the decision history remains auditable.

## 6. Milestone 2 decisions and discovered facts

| ID | Decision / fact | Rationale / evidence | Reversal trigger |
|---|---|---|---|
| D-021 | Use one deterministic source-record chunk per small synthetic artifact version for Stage 02, with parser/chunker provenance `resolveflow_fixture:1.0.0` and `source_record:1.0.0`. | The corpus is deliberately small and structured; this preserves exact source positions and makes idempotence inspectable without inventing a retrieval ablation. | Development/calibration evidence supports a versioned multi-chunk policy. |
| D-022 | Use a 32-dimensional signed token-hash fixture embedding and term-overlap fixture reranker only for credential-free tests. | Stable offline vectors exercise pgvector, fusion, caching, and trace contracts without presenting fixture scores as Cohere results. | Never replace fixture evidence retroactively; add separately labeled live-provider observations when a confirmed zero-charge key is explicitly enabled. |
| D-023 | Use reciprocal-rank fusion with `k=60`, candidate `K=10`, deterministic ID tie-breaking, checksum deduplication, and a per-artifact cap of two for the initial fixture policy. | These are versioned safe defaults for implementation tests, not tuned or claimed-optimal retrieval settings. | Calibration data supports a new policy version before held-out lock. |
| D-024 | Keep optional image evidence explicitly unavailable in corpus v1.0. | Core text/JSON/CSV evidence, security boundaries, and PostgreSQL retrieval are complete; no meaningful reviewed visual contradiction fixture exists yet. | A later milestone adds an accessible, checksummed image with genuine gold interpretation. |
| U-016-U-018 | Corpus v1.0 contains 5 synthetic artifacts, 6 immutable versions/chunks/embeddings, including current/stale, restricted, hostile, JSON, and CSV evidence; exact search is appropriate at this size. | `data/corpus/hero-corpus-1.0.json`; `resolveflow-corpus-validate` on 2026-07-22. | A larger versioned corpus justifies an approximate vector index after measurement. |
| U-019 | Official Cohere documentation checked 2026-07-22 identifies `embed-v4.0`, search document/query input types, float embeddings, and supported output dimensions 256/512/1024/1536. | Official Cohere embedding documentation; adapter contract tests. | Recheck before any live call or publication. |
| U-021-U-022 | Fixture retrieval policy uses K=10, RRF k=60, cap=2; cache identity includes tenant, role, region, policy, identity snapshot, corpus snapshot, and query. No TTL is needed for immutable in-process fixture entries. | `HybridRetriever` and cache-isolation security test. | Persistent cache introduction requires an explicit expiry/retention policy. |
| U-026-U-031 | Official Cohere documentation checked 2026-07-22 identifies `rerank-v4.0-fast` and `rerank-v4.0-pro`; paired payloads are identical and every Pro request requires a declared escalation reason. No winner or threshold is selected. | Official Cohere Rerank documentation; paired adapter/policy tests. | Calibration locks an ambiguity rule before held-out evaluation. |
| U-033-U-034 | Synthetic policy grants restricted evidence only to incident commanders; contractors are capped at internal. Tenant/role/region/policy/effective-time/corpus predicates are materialized before PostgreSQL FTS/vector ranking. | Real PostgreSQL FTS/pgvector test and negative security suite on 2026-07-22. | A new policy version changes the explicit table and snapshots, not prompt text. |

## 7. Milestone 3 decisions and discovered facts

| ID | Decision / fact | Rationale / evidence | Reversal trigger |
|---|---|---|---|
| D-025 / U-029 | Governed-agent policy `governed-agent-1.0` fixes two tool rounds, four total provider calls including structuring, 4,096 observed tokens, 1,024 output tokens per call, a 30-second wall deadline, and a two-second per-tool timeout. | These conservative fixture-safe limits make termination deterministic and leave one provider call reserved for the structure pass. They are implementation controls, not measured production targets. | Staging measurements support a new versioned policy before held-out lock; prior traces retain the old policy ID. |
| D-026 | The structure pass selects only verified claim, unknown, and conflict IDs plus the exact graph hash; it does not generate final factual prose. | ID-only selection is stricter than accepting provider-authored field text and makes source closure and deterministic rendering mechanically testable. | A later schema version demonstrates an equally enforceable closure rule for richer wording. |
| D-027 / U-035 | Deterministic support requires an existing authorized current in-context document, exact normalized span containment, all structured value terms, at least 45% non-stopword overlap, and independent non-hostile support when hostile evidence is cited. | Stage 03 needs a reproducible provider-independent verifier without claiming semantic entailment precision. Exact authorization/version/freshness failures and conflicts are preserved as codes. | Human-reviewed verifier evidence in Milestone 6 supports a versioned rule or narrowly scoped secondary entailment helper. |
| D-028 / U-037 | The synthetic attack library covers visible instructions, delimiter-like text, multilingual instructions, fake-system messages, and approval bypass. Security scoring counts observable attempted-blocked and succeeded effects, never verbal refusal. | This implements the declared boundary without claiming prompt-injection immunity or mislabeling deterministic fixtures as live attacks. | Milestone 5 versions and locks the held-out family split and exact scenario counts. |
| U-026-U-027 | Official Cohere documentation rechecked 2026-07-22 identifies `command-a-plus-05-2026`, V2 `messages`, `documents`, `tools`, `strict_tools`, citations, usage, finish reasons, and JSON-schema `response_format`; the official Python SDK is locked at `cohere==7.0.5`. | Official Cohere V2 Chat, tool-use, structured-output documentation and PyPI package metadata; sanitized client contract tests cover request/response mapping. No live call occurred. | Recheck before any live call or publication, and version the adapter if fields or model support change. |
| U-028 / U-032 | Live Cohere allowance, billing state, latency, usage distribution, schema-valid rate, and provider error distribution remain unknown. | The loop intentionally withheld `COHERE_API_KEY`; all Stage 03 evidence is fixture/contract evidence and is labeled accordingly. | Only actual credential/billing evidence and bounded live traces may fill these facts. |
| U-036 | No secondary semantic entailment model is used in Stage 03. | Deterministic exact-span/value/overlap checks are sufficient for the declared fixture contracts and avoid self-grading or unmeasured semantic claims. | A reviewed disputed-claim sample shows a material deterministic gap and defines a bounded helper rubric. |

## 8. Milestone 4 decisions and discovered facts

| ID | Decision / fact | Rationale / evidence | Reversal trigger |
|---|---|---|---|
| D-029 / U-014 | A content revision creates a new proposal revision, marks the prior proposal `invalidated`, requires a new approval, and retains one idempotency key for the unchanged logical action. | Approval is bound to canonical payload fields only; exact-digest, permission, rejection, expiry, invalidation, double-click, and worker-identity tests pass. | A new action schema requires a versioned state transition and digest contract. |
| D-030 / U-045 | Action retry policy `action-retry-1.0` uses at most five attempts, five-second exponential base, 300-second cap, and deterministic ±20% jitter; connector `Retry-After` is also capped. Leases default to 30 seconds in the durable worker. | Bounded fake-clock tests and real PostgreSQL claim/reclaim tests passed on 2026-07-22. These are safe operational defaults, not measured production optima. | Staging evidence supports a new versioned retry/lease policy before held-out lock. |
| D-031 / U-038 | Public projection recursively removes sensitive-key values, restricted objects, secret-like values, hidden prompts/reasoning, raw payloads, stack data, and private filesystem paths, then hashes the deterministic projection. | Redaction, reproducible JSON/Markdown export, and restricted-data tests pass without publishing unrestricted provider content. | Security review adds patterns or a typed field-level disclosure policy supersedes the initial conservative projection. |
| D-032 / U-042-U-044 | Stage 04 implements no live Jira request fields. The real Jira Cloud boundary always raises `real_jira_connector_disabled`; the synthetic connector uses the application idempotency key as its remote marker and reconciles it before retry. Real project fields, auth, and marker support remain unknown. | The active task forbids every real Jira write and no credential was accessed. Synthetic timeout-after-accept and acknowledgement-loss tests produce one issue. | A later explicitly authorized task provides a development site, discovers supported fields/marker behavior, and records contract evidence without changing public mode. |

## 9. Milestone 5 decisions and discovered facts

| ID | Decision / fact | Rationale / evidence | Reversal trigger |
|---|---|---|---|
| D-033 / U-047 | Store 36 synthetic-agent-authored candidate truths as 18 development, 8 calibration, and 10 held-out candidates, all labeled `DRAFT_PENDING_HUMAN_REVIEW`, `pending`, and `DRAFT_NOT_LOCKED`. | The active task prohibits calling Codex content human-authored or locking held-out data. The typed catalog validates exact counts and the review workflow requires a later signed human artifact. | A qualified human completes the documented review and a later authorized stage creates a new version and held-out lock without overwriting this draft. |
| D-034 / U-048 | Replay manifest schema 1.0 permits exactly one typed primary mutation, freezes clock/identity/ACL/corpus/model policy/connector/flags, and stores canonical hashes for every rendered input. | Repeated dry runs produce the same materialization checksum, invalid or incompatible manifests fail before provider calls, and all eight v1 mutation names map to fixed handlers without arbitrary hooks. | A separately versioned combination stress-suite schema is justified; core paired analysis retains one primary mutation. |
| D-035 / U-049 | `unsafe-v0` disables pre-retrieval authorization and makes verifier outcomes observe-only inside deterministic Replay; `guarded-v1` enforces both. Both retain approval and prohibit external writes. | The retained role-downgrade fixture makes unsafe-v0 expose one restricted candidate while guarded-v1 uses the same `ResolveOrchestrator.run` path with enforced ACL/verifier. Keeping the action boundary prevents a deliberately unsafe comparison from becoming a write capability. | A new versioned unsafe fixture adds further control removals without exposing a live/public unsafe service or weakening the production default. |
| D-036 / U-050-U-051 | Gate `release-gate-1.0` evaluates nine hard failure rates first at zero tolerance, then route/completion requirements and secondary citation precision. It remains `DRAFT_PRE_REGISTERED_NO_HELD_OUT_RESULTS`; the declaration commit is honestly `uncommitted-stage-05`. | Hard-first order and `SHIP`, `SHIP_WITH_LIMITS`, and `NO_SHIP` branches are tested. The outer loop owns the commit, and held-out data is intentionally not locked, so final Git chronology is not claimed. | The outer commit exists and a later reviewed calibration creates a new gate version before any held-out lock/results. |
| D-037 / U-052 | Declare a deterministic 200-scenario draft security matrix as 10 base-truth clusters × 5 existing attack families × 4 variants, with zero live-provider calls. | Typed expansion proves 200 unique IDs and keeps deterministic application-control, sanitized contract, and disabled bounded-live suites separate. These are not described as independent live model attacks. | Reviewed payload variants or a confirmed zero-charge live allowance create separately reported suite versions. |
| U-053-U-054 | One actual deterministic development-fixture pair produced unsafe-v0 `NO_SHIP` and guarded-v1 `SHIP_WITH_LIMITS`; guarded limits are caused only by citation precision N=4 being below the draft minimum N=10. No final release verdict exists. | The checksummed `/tmp/resolveflow-stage05-result.json` artifact was generated locally from the shared path. It is explicitly non-final, non-held-out, non-live, non-human-reviewed, and not publishable as a final release result. | A later locked, reviewed evaluation generates a new immutable bundle and actual final verdict; this development artifact is never relabeled. |

## 10. Milestone 6 decisions and discovered facts

| ID | Decision / fact | Rationale / evidence | Reversal trigger |
|---|---|---|---|
| D-038 / U-060-U-061 | The static public product ships nine credential-free routes plus one pre-generated run. Public live mode remains off; the local API accepts only the hero case and five named mutations, enforces session/IP/global daily quotas, one active run per session, a bounded queue, a 45-second deadline, and a kill switch. | No zero-charge Cohere allowance or provider billing evidence exists. Static export, route smoke, bundle scan, limiter tests, and stored fallback evidence pass without a provider or backend. | A future explicitly authorized task verifies billing/quota evidence and separately enables a bounded local/staging live profile; GitHub Pages remains snapshot-first. |
| D-039 / U-040-U-044 | Slack HMAC/timestamp verification, challenge/event parsing, event-ID plus message-timestamp deduplication, queued acknowledgement, and canonical intake are implemented. Jira staging configuration fixes one HTTPS development site/project, issue type, team field, and complete priority mapping, while the real connector stays disabled. | Contract/API tests use synthetic signed deliveries and configuration only. No Slack or Jira credential was accessed and no external request/write occurred. | An explicitly authorized private staging task supplies credentials, discovers actual scopes/field IDs, and records real integration evidence. |
| D-040 / U-056-U-058 | Human review is a blinded static workflow with deterministic A/B order, private CSV template, and exact-count analyzer. Results remain `human review not yet completed` at 0 reviewers/0 cases. The French fixture is exploratory, synthetic-agent-authored, unvalidated, and excluded from claims. | No genuine reviewer or fluent-human signoff exists. Public copy states English-only claims and publishes no reviewer percentage or multilingual quality result. | Genuine consented review exports or a fluent signoff matching the versioned checksum schema create new evidence; prior absence is not overwritten. |
| D-041 | Published hero and development-result snapshots are canonical/file checksummed and duplicated byte-for-byte into the static public tree. Snapshot verification now hashes the actual serialized `RunSnapshot` projection rather than the richer pre-projection audit objects. | The prior hash was computed before `AuditEvent` objects were projected to public `TraceEvent` fields, so it could not be independently reconstructed from the published JSON. The corrected implementation and regression verifier pass. | A versioned snapshot schema changes the public projection and supplies a migration/compatibility verifier. |
