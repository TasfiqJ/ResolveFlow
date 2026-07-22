# ResolveFlow Replay decisions and discovery register

**Log version:** 1.2

**Last updated:** 2026-07-21

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
