# Feature 2: deterministic context enrichment

**DOCUMENT 02 / FEATURE 2**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Deterministic context and tools                                                                                      |
|------------------------|----------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.2, pages 29-30.                                                                                            |
| **Primary phase**      | Week 1 minimal path; Week 3 complete typed tool layer                                                                |
| **Core rule**          | The language model chooses from named operations but never receives database credentials or free-form SQL authority. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.  |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 29-30. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                       |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Demonstrate that an FDE maps a messy business workflow into reliable tool contracts rather than asking the language model to improvise database access. |
| Primary modules          | context repositories, policy, tool adapters, telemetry                                                                                                  |
| Primary data/entities    | case_context_snapshots, tool_calls, tenant data records                                                                                                 |
| API or interface surface | Internal named read-only tool contracts; exposed through run trace, not arbitrary SQL endpoints                                                         |
| Related features         | Feature 1, Feature 4, Feature 7, Feature 13, Feature 14                                                                                                 |
| Implementation phase     | Week 1 minimal path; Week 3 complete typed tool layer                                                                                                   |
| Non-negotiable control   | The language model chooses from named operations but never receives database credentials or free-form SQL authority.                                    |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Fetch synthetic customer tier, region, active cluster list, recent rollout, and open incident flags.

- Each operation is a named read-only query with typed parameters and a stable response schema.

- Data is read as of the case timestamp in replay mode.

- Missing context is distinguished from connector failure and authorization denial.

- The model sees normalized results, not database credentials or arbitrary SQL access.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Read the immutable case-time and identity snapshot.
>
> **2.** Execute named repository functions through a read-only database role.
>
> **3.** Normalize success, not-found, denied, timeout, and malformed-data results into distinct schemas.
>
> **4.** Attach provenance IDs and include only normalized results in the model tool response.
>
> **5.** Cache only immutable replay results by snapshot; never cache live authorization across users.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------|
| Ownership                      | context repositories, policy, tool adapters, telemetry                                                               |
| Persistent evidence            | case_context_snapshots, tool_calls, tenant data records                                                              |
| External/public interface      | Internal named read-only tool contracts; exposed through run trace, not arbitrary SQL endpoints                      |
| Dependencies                   | Feature 1, Feature 4, Feature 7, Feature 13, Feature 14                                                              |
| Security/reliability invariant | The language model chooses from named operations but never receives database credentials or free-form SQL authority. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

Create repository functions or stored queries such as:

- \`get_customer_profile(customer_id, as_of)\`

- \`get_active_clusters(customer_id, region, as_of)\`

- \`get_rollouts(customer_id, region, start, end)\`

- \`get_open_incidents(customer_id, service, as_of)\`

Use a dedicated read-only database role for runtime tools. Apply tenant filters in SQL and verify returned tenant IDs before serialization. Cache immutable replay tool results by snapshot ID; do not cache live role decisions across users.

## 6 Failure-safe behavior and security review

- The language model chooses from named operations but never receives database credentials or free-form SQL authority.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

Show one context field appearing automatically, one legitimately missing field, and the exact read-only tool result in the trace. Do not display fake “thinking”; display observable tool activity and returned data.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                           |
|----------------|---------------------------------------------------------------------------------|
| Unit           | Typed query schemas and normalized error codes.                                 |
| Integration    | Read-only DB role, tenant filter, cross-tenant no-data behavior, as-of queries. |
| Replay         | Same snapshot/time produces identical tool-data hash.                           |
| Fault          | Timeout, denied, not found, and malformed data remain distinguishable.          |

### 8.1 Acceptance criteria

| **Criterion**    | **Pass condition**                                                   | **Evidence**                     |
|------------------|----------------------------------------------------------------------|----------------------------------|
| No arbitrary SQL | Tool input contains only a named query and typed values.             | Tool schema plus negative tests. |
| Replay fidelity  | Same snapshot and as-of time produce identical structured tool data. | Hash comparison.                 |
| Failure clarity  | Not found, denied, timeout, and malformed data use separate codes.   | UI and trace screenshots.        |
| Tenant isolation | Cross-tenant identifiers return no data.                             | Two-tenant integration tests.    |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 1, Feature 4, Feature 7, Feature 13, Feature 14                                                                                                    |
| Primary roadmap phase        | Week 1 minimal path; Week 3 complete typed tool layer                                                                                                      |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Exact synthetic customer fields are fixed in the truth-data schema before evaluation.

- Connector timeout values are measured and budgeted during staging.

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

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.2 of the uploaded ResolveFlow Replay Final Master Plan, pages 29-30. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
