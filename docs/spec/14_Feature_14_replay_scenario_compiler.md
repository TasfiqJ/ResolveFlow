# Feature 14: replay scenario compiler

**DOCUMENT 14 / FEATURE 14**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Replay orchestration                                                                                                           |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.14, pages 37-38.                                                                                                     |
| **Primary phase**      | Week 4                                                                                                                         |
| **Core rule**          | Replay executes the production Resolve path with a frozen clock, identity, corpus, policy, connectors, and declared mutations. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.            |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 37-38. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                              |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Turn historical or synthetic incident conditions into repeatable deployment tests that can be run locally, in CI, and from the public website. |
| Primary modules          | replay, policy, synthetic adapters, evaluator, worker                                                                                          |
| Primary data/entities    | replay_scenarios, replay_runs, replay_expectations, snapshots, jobs                                                                            |
| API or interface surface | POST /v1/replays; GET /v1/replays/{id}                                                                                                         |
| Related features         | Feature 3, Feature 4, Feature 10, Feature 12, Feature 13, Feature 15, Feature 17                                                               |
| Implementation phase     | Week 4                                                                                                                                         |
| Non-negotiable control   | Replay executes the production Resolve path with a frozen clock, identity, corpus, policy, connectors, and declared mutations.                 |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Accept a versioned YAML manifest referencing a base truth and declared mutations.

- Validate mutation compatibility and expected invariants before execution.

- Materialize a frozen clock, identity, ACL, corpus, connectors, and model policy.

- Generate a run matrix without multiplying hidden degrees of freedom.

- Reuse the production Resolve path.

- Store a scenario checksum and exact rendered inputs.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Validate a versioned YAML manifest and referenced human-authored base truth.
>
> **2.** Materialize frozen clock, identity, ACL, corpus, connector state, model policy, and expected invariants.
>
> **3.** Apply one typed primary mutation and reject ambiguous or undeclared combinations.
>
> **4.** Run the production Resolve orchestrator and store exact rendered inputs plus non-model checksums.
>
> **5.** Score and compare results; allow public visitors to choose only predefined scenarios.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                          |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | replay, policy, synthetic adapters, evaluator, worker                                                                          |
| Persistent evidence            | replay_scenarios, replay_runs, replay_expectations, snapshots, jobs                                                            |
| External/public interface      | POST /v1/replays; GET /v1/replays/{id}                                                                                         |
| Dependencies                   | Feature 3, Feature 4, Feature 10, Feature 12, Feature 13, Feature 15, Feature 17                                               |
| Security/reliability invariant | Replay executes the production Resolve path with a frozen clock, identity, corpus, policy, connectors, and declared mutations. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Use a registry of typed mutation handlers.

- Render variants deterministically from human-authored base truths.

- Persist the complete materialized snapshot so a scenario can be re-run after corpus evolution.

- Prohibit arbitrary Python hooks in public manifests.

- Limit one primary mutation per core analysis; combination scenarios are a separate stress suite.

- Include a dry-run command that prints changed objects and expected gates without calling models.

### 5.1 Supported v1 mutation registry

| **Mutation**     | **Parameters**                           | **Example**                             |
|------------------|------------------------------------------|-----------------------------------------|
| role_override    | role; optional region                    | incident_commander → contractor         |
| add_artifact     | artifact version                         | hostile note inserted                   |
| hide_artifact    | artifact or chunk ID                     | decisive SQL row removed                |
| promote_stale    | artifact version                         | obsolete runbook appears current        |
| replace_image    | image version                            | dashboard contradicts text              |
| connector_state  | healthy, timeout, unavailable, uncertain | Jira outage after approval              |
| language_variant | validated variant ID                     | non-English query with English evidence |
| field_removal    | canonical field                          | cluster ID omitted                      |

## 6 Failure-safe behavior and security review

- Replay executes the production Resolve path with a frozen clock, identity, corpus, policy, connectors, and declared mutations.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

The public Replay page shows the manifest in plain language, the exact changed objects, and a side-by-side v0-v1 result. Visitors choose from predefined scenarios rather than writing arbitrary attacks.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                                                   |
|----------------|---------------------------------------------------------------------------------------------------------|
| Schema         | Unknown mutation, incompatible combination, missing fixture, checksum mismatch fail before model calls. |
| Determinism    | Same manifest/fixture yields same non-model hashes.                                                     |
| Architecture   | Replay invokes the same production orchestrator/verifier/actions code.                                  |
| Mutation       | Undeclared inputs remain unchanged; one primary mutation in core analysis.                              |

### 8.1 Acceptance criteria

| **Criterion**                 | **Pass condition**                                                    | **Failure behavior**     |
|-------------------------------|-----------------------------------------------------------------------|--------------------------|
| Deterministic materialization | Same manifest and fixture version produce identical non-model hashes. | Scenario invalid.        |
| Production parity             | Replay invokes the same orchestrator and verifier code.               | Architecture test fails. |
| Mutation isolation            | Undeclared inputs remain unchanged.                                   | Scenario invalidated.    |
| Invalid manifest              | Fails before provider calls.                                          | Clear validation report. |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 3, Feature 4, Feature 10, Feature 12, Feature 13, Feature 15, Feature 17                                                                           |
| Primary roadmap phase        | Week 4                                                                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Manifest versions and fixture hashes are generated during implementation.

- Combination scenarios are a separate stress suite and are not silently mixed into core analyses.

- Exact dependency patch versions are pinned from current supported releases in lockfiles and recorded in the SBOM.

- Observed latency, usage, cost, completion, quality, security-event counts, and human-review outcomes come from traces and evaluation artifacts only.

- Any changed external API field, model identifier, hosting capability, scope, or rate limit is rechecked against official documentation and recorded in an ADR or model-policy version.

| **NO FABRICATED RESULTS** | This specification intentionally contains no claimed improvement, latency, cost, reviewer percentage, or zero-failure result. Those values become publishable only after the locked evaluation is run. |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 11 Definition of done for this feature

- All authoritative required behavior is implemented through the shared production path.

- The feature is represented by typed schemas, stable states, persistent audit evidence, and sanitized public output where applicable.

- Every listed acceptance criterion has an automated test or explicitly identified human review/evidence artifact.

- At least one declared failure or adversarial condition is demonstrated and remains visible in the trace and result metrics.

- The feature participates correctly in a frozen Replay scenario and does not bypass authorization, verification, approval, or release-gate logic.

- Documentation, configuration, and operational runbook information are sufficient for another engineer to understand and reproduce the feature without relying on the builder’s narration.

### Verification register

The following external facts were checked against primary official sources on 15 July 2026. Recheck model identifiers, platform limits, provider fields, and patch versions on the implementation day and before publishing the final demo.

**PostgreSQL versioning:** PostgreSQL 17 remains supported; PostgreSQL 18 is current. The plan targets a 17-compatible managed service and can upgrade after compatibility tests. [Official source](https://www.postgresql.org/support/versioning/)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.14 of the uploaded ResolveFlow Replay Final Master Plan, pages 37-38. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
