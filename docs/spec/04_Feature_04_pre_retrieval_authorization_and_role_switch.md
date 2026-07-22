# Feature 4: pre-retrieval authorization and role switch

**DOCUMENT 04 / FEATURE 4**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Authorization and enterprise security                                                                                   |
|------------------------|-------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.4, pages 31.                                                                                                  |
| **Primary phase**      | Week 2                                                                                                                  |
| **Core rule**          | Authorization is applied before lexical or vector search and rechecked after generation. The model never grants access. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.     |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 31. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Provide the strongest enterprise-security moment in the demo: change the operator role and prove that restricted evidence disappears before retrieval rather than relying on a prompt to hide it. |
| Primary modules          | identity, policy, retrieval, verifier, cache                                                                                                                                                      |
| Primary data/entities    | role_bindings, chunk_acls, ACL snapshots, retrieval_candidates, verifier_results                                                                                                                  |
| API or interface surface | Policy decision service; role selector on predefined public scenarios                                                                                                                             |
| Related features         | Feature 3, Feature 5, Feature 9, Feature 13, Feature 14, Feature 15                                                                                                                               |
| Implementation phase     | Week 2                                                                                                                                                                                            |
| Non-negotiable control   | Authorization is applied before lexical or vector search and rechecked after generation. The model never grants access.                                                                           |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Eligibility uses tenant, active role, region, classification, case time, and source lifecycle.

- The authorization decision is computed per run and stored as an immutable snapshot.

- Restricted chunks are absent from vector search, lexical search, Rerank, Command documents, caches, and public traces.

- A role downgrade in Replay changes the candidate universe and produces a clear diff.

- The final citation verifier repeats the authorization check against the original run snapshot.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Materialize tenant, role, region, classification rules, and case time for the run.
>
> **2.** Build an eligible-chunk relation before vector distance or full-text rank.
>
> **3.** Use the same eligible IDs for lexical, vector, fusion, Rerank, Command documents, caches, and trace projection.
>
> **4.** Recheck every cited source against the immutable ACL snapshot.
>
> **5.** In Replay, switch role/region and compare the candidate universe without leaking restricted titles or content.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                   |
|--------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | identity, policy, retrieval, verifier, cache                                                                            |
| Persistent evidence            | role_bindings, chunk_acls, ACL snapshots, retrieval_candidates, verifier_results                                        |
| External/public interface      | Policy decision service; role selector on predefined public scenarios                                                   |
| Dependencies                   | Feature 3, Feature 5, Feature 9, Feature 13, Feature 14, Feature 15                                                     |
| Security/reliability invariant | Authorization is applied before lexical or vector search and rechecked after generation. The model never grants access. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Model role permissions as explicit data, not string matching inside prompts.

- Join eligible chunk IDs before applying vector distance and full-text rank.

- Include tenant and policy version in retrieval-cache keys.

- Use property-based tests across role, region, and classification combinations.

- Add a database assertion or view that makes accidental unfiltered retrieval difficult.

- Redact restricted source titles from unauthorized public traces; revealing that a secret document exists may itself be sensitive.

## 6 Failure-safe behavior and security review

- Authorization is applied before lexical or vector search and rechecked after generation. The model never grants access.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

| **HARD-GATE SENSITIVITY** | This feature protects a release-blocking invariant. Deliberately removing the control must make at least one deterministic or replay test fail. |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|

## 7 Telemetry and demo proof

Display candidate counts before and after the role switch, but never expose restricted content to the downgraded user. The audit view for an authorized maintainer may show a source ID and policy code. The public demo should use synthetic classifications so no real secret exists.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                                           |
|----------------|-------------------------------------------------------------------------------------------------|
| Unit/property  | Authorization monotonicity across role, region, classification, and time.                       |
| Integration    | Eligibility predicate is applied before vector/full-text ranking.                               |
| Security       | Forbidden source absent from candidates, Rerank, model payload, cache, citation, trace, export. |
| Replay         | Role downgrade/region mismatch changes access without leaking restricted title.                 |

### 8.1 Acceptance criteria

| **Criterion**                | **Pass condition**                                               | **Release impact**              |
|------------------------------|------------------------------------------------------------------|---------------------------------|
| Forbidden candidate exposure | Zero across all held-out role replays.                           | Immediate NO SHIP.              |
| Forbidden model input        | Zero.                                                            | Immediate NO SHIP.              |
| Forbidden citation           | Zero.                                                            | Immediate NO SHIP.              |
| Cache isolation              | Role or tenant change cannot reuse ineligible candidates.        | Immediate NO SHIP.              |
| Explainability               | Trace shows a safe policy reason without leaking source content. | Required for portfolio quality. |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 3, Feature 5, Feature 9, Feature 13, Feature 14, Feature 15                                                                                        |
| Primary roadmap phase        | Week 2                                                                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Role-to-classification policy is explicit synthetic project data.

- Cache TTL is chosen after measuring use; cache keys always include tenant and policy version.

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

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.4 of the uploaded ResolveFlow Replay Final Master Plan, pages 31. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
