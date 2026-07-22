# Feature 12: idempotent connector execution and recovery

**DOCUMENT 12 / FEATURE 12**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Connector reliability                                                                                                   |
|------------------------|-------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.12, pages 36-37.                                                                                              |
| **Primary phase**      | Week 3                                                                                                                  |
| **Core rule**          | The system models uncertain send outcomes, reconciles before retrying, and uses one idempotency key per logical action. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.     |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 36-37. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Turn one action into production-quality evidence. A reliable single connector is more impressive than five shallow integrations. |
| Primary modules          | actions, worker, jobs, Jira adapter, telemetry                                                                                   |
| Primary data/entities    | jobs, action_attempts, idempotency ledger, audit_events                                                                          |
| API or interface surface | Background worker contract; action status read through case/run APIs                                                             |
| Related features         | Feature 11, Feature 13, Feature 14, Feature 15                                                                                   |
| Implementation phase     | Week 3                                                                                                                           |
| Non-negotiable control   | The system models uncertain send outcomes, reconciles before retrying, and uses one idempotency key per logical action.          |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Approved actions are claimed from a durable queue transactionally.

- Retries use exponential backoff with jitter and a maximum attempt count.

- The system distinguishes pre-send failure, uncertain send outcome, acknowledgement, and permanent rejection.

- Duplicate dispatch is prevented through an application idempotency key and a Jira-side marker or reconciliation query.

- An operator can retry, cancel where safe, or dead-letter an action.

- Connector outage and recovery appear in the run trace and replay result.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Claim an approved action from the durable jobs table transactionally.
>
> **2.** Confirm approval, exact proposal digest, expiry, authorization, and unused idempotency key.
>
> **3.** Dispatch through the Jira adapter and record a normalized attempt.
>
> **4.** If the send outcome is uncertain, reconcile with a Jira-side marker or remote correlation before retrying.
>
> **5.** Use bounded backoff, surface dead letters, and allow a reclaimed lease to continue safely after worker crash.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                   |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | actions, worker, jobs, Jira adapter, telemetry                                                                          |
| Persistent evidence            | jobs, action_attempts, idempotency ledger, audit_events                                                                 |
| External/public interface      | Background worker contract; action status read through case/run APIs                                                    |
| Dependencies                   | Feature 11, Feature 13, Feature 14, Feature 15                                                                          |
| Security/reliability invariant | The system models uncertain send outcomes, reconciles before retrying, and uses one idempotency key per logical action. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

Use a PostgreSQL jobs table and \`SELECT ... FOR UPDATE SKIP LOCKED\` to claim work. Each attempt records:

- action and idempotency key;

- proposal hash;

- attempt number;

- started and finished time;

- request fingerprint;

- provider response or normalized error;

- retry decision;

- reconciliation result. For Jira, include a unique marker in a dedicated field, label, or description footer and search before retrying an uncertain request. If the selected Jira plan or API cannot guarantee a safe server-side idempotency mechanism, implement reconciliation and state the limitation explicitly.

## 6 Failure-safe behavior and security review

- The system models uncertain send outcomes, reconciles before retrying, and uses one idempotency key per logical action.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

| **HARD-GATE SENSITIVITY** | This feature protects a release-blocking invariant. Deliberately removing the control must make at least one deterministic or replay test fail. |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|

## 7 Telemetry and demo proof

Disable the synthetic Jira connector after approval, show \`retry_wait\`, restore it, and show one completed issue with the same idempotency key. Keep the live outage sequence under 20 seconds by using a demo retry policy separate from the production- like documented policy.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                                                |
|----------------|------------------------------------------------------------------------------------------------------|
| Unit           | Retry classification, backoff, reconciliation state, idempotency key.                                |
| Integration    | SKIP LOCKED lease, reclaim, unique constraints, restart safety.                                      |
| Fault          | Timeout before send, after accepted write, 429, 5xx, permission denial, crash after acknowledgement. |
| Gate           | No duplicate issue and no lost approved action.                                                      |

### 8.1 Acceptance criteria

| **Criterion**        | **Pass condition**                                            | **Release impact** |
|----------------------|---------------------------------------------------------------|--------------------|
| Duplicate issue      | Zero across forced timeout and retry tests.                   | Immediate NO SHIP. |
| Lost approved action | Zero in restart tests within the configured retention window. | Reliability gate.  |
| Backoff              | Retry schedule is bounded and observable.                     | Operational gate.  |
| Dead letter          | Permanent failures surface to an operator with a reason.      | Required.          |
| Worker crash         | Another worker safely reclaims expired work.                  | Integration test.  |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 11, Feature 13, Feature 14, Feature 15                                                                                                             |
| Primary roadmap phase        | Week 3                                                                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Jira-side marker mechanism depends on the development project capabilities.

- Retry intervals and maximum attempts are configured and tested; demo timing may use a shorter documented policy.

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

**Jira Cloud REST API v3 - Issues:** Official issue-create and issue-query API surface. [Official source](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/)

**PostgreSQL versioning:** PostgreSQL 17 remains supported; PostgreSQL 18 is current. The plan targets a 17-compatible managed service and can upgrade after compatibility tests. [Official source](https://www.postgresql.org/support/versioning/)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.12 of the uploaded ResolveFlow Replay Final Master Plan, pages 36-37. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
