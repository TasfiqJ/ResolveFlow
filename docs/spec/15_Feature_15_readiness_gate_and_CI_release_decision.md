# Feature 15: readiness gate and CI release decision

**DOCUMENT 15 / FEATURE 15**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Evaluation and release governance                                                                                    |
|------------------------|----------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.15, pages 38-39.                                                                                           |
| **Primary phase**      | Week 4 gate plumbing; Week 6 final locked evaluation                                                                 |
| **Core rule**          | Hard safety invariants are evaluated before quality and operations. Gate definitions predate final held-out results. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.  |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 38-39. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                 |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Make “safe enough to ship” a real automated decision with explicit invariants, not a dashboard label chosen after seeing results. |
| Primary modules          | evaluation, replay, metrics, CI, reporting                                                                                        |
| Primary data/entities    | metric_observations, experiment_comparisons, release_gates, result_bundles                                                        |
| API or interface surface | GET /v1/releases/{build}; CI verdict artifacts                                                                                    |
| Related features         | Feature 13, Feature 14, Feature 16, Feature 17, Feature 18                                                                        |
| Implementation phase     | Week 4 gate plumbing; Week 6 final locked evaluation                                                                              |
| Non-negotiable control   | Hard safety invariants are evaluated before quality and operations. Gate definitions predate final held-out results.              |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Evaluate hard safety invariants first.

- Evaluate quality and operational thresholds second.

- Compare candidate and baseline on paired cases.

- Produce \`SHIP\`, \`SHIP_WITH_LIMITS\`, or \`NO_SHIP\` with machine-readable reasons.

- Attach case-level failures, uncertainty intervals, and known limitations.

- Block a tagged release in GitHub Actions when a hard gate fails.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Load a versioned gate definition whose commit predates final held-out results.
>
> **2.** Aggregate run records without silently excluding infrastructure failures.
>
> **3.** Evaluate hard invariants first; stop on any forbidden exposure, approval breach, duplicate effect, missing audit, public write credential, or held-out integrity issue.
>
> **4.** Evaluate quality and operations targets with exact N and uncertainty, then compare against the pinned baseline.
>
> **5.** Write a JSON verdict and human-readable summary, block release when required, and publish every failing replay link.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------|
| Ownership                      | evaluation, replay, metrics, CI, reporting                                                                           |
| Persistent evidence            | metric_observations, experiment_comparisons, release_gates, result_bundles                                           |
| External/public interface      | GET /v1/releases/{build}; CI verdict artifacts                                                                       |
| Dependencies                   | Feature 13, Feature 14, Feature 16, Feature 17, Feature 18                                                           |
| Security/reliability invariant | Hard safety invariants are evaluated before quality and operations. Gate definitions predate final held-out results. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Store gate definitions in versioned YAML reviewed before held-out execution.

- Require minimum sample sizes for each claim.

- Treat infrastructure failures as failures or report them separately; never remove them silently.

- Produce a JSON verdict artifact and Markdown summary in CI.

- Sign or checksum public result bundles and publish their commit SHA.

- Require a maintainer override to be explicit, time-limited, and visible; for the portfolio project, do not override a hard safety failure.

### 5.1 Verdict logic

| **Verdict**      | **Conditions**                                                                                                      | **Meaning**                                                        |
|------------------|---------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| SHIP             | All hard invariants pass; required quality/operations gates pass; no undeclared exclusions.                         | Ready for the declared synthetic project deployment profile.       |
| SHIP WITH LIMITS | Hard invariants pass, but a secondary quality or latency gate misses and rollout limits are explicit.               | Safe only for a constrained pilot, not a blanket production claim. |
| NO SHIP          | Any forbidden exposure, unapproved write, duplicate action, missing audit evidence, or critical quality regression. | Release is blocked.                                                |

## 6 Failure-safe behavior and security review

- Hard safety invariants are evaluated before quality and operations. Gate definitions predate final held-out results.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

| **HARD-GATE SENSITIVITY** | This feature protects a release-blocking invariant. Deliberately removing the control must make at least one deterministic or replay test fail. |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|

## 7 Telemetry and demo proof

The hero moment is the red NO SHIP verdict for an answer that initially looks convincing. The improved build must pass because of changed controls and measured behavior, not because the scenario was removed.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                                       |
|----------------|---------------------------------------------------------------------------------------------|
| Unit           | Numerators, denominators, Wilson intervals, cluster grouping, verdict logic.                |
| CI negative    | Seeded forbidden citation, unapproved write, duplicate action, missing audit block release. |
| Integrity      | Gate commit predates held-out results; excluded runs and retries are visible.               |
| Reproduction   | Local and CI aggregation from identical records yields identical bundle/verdict.            |

### 8.1 Acceptance criteria

| **Criterion**      | **Pass condition**                                                        | **Evidence**         |
|--------------------|---------------------------------------------------------------------------|----------------------|
| Pre-registration   | Gate-file commit predates final held-out results.                         | Git history.         |
| Hard-gate behavior | A seeded forbidden citation blocks release.                               | CI negative test.    |
| Reproducibility    | Local and CI aggregation produce the same verdict from identical records. | Hash comparison.     |
| Failure evidence   | Verdict links to every failing replay.                                    | Public results page. |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 13, Feature 14, Feature 16, Feature 17, Feature 18                                                                                                 |
| Primary roadmap phase        | Week 4 gate plumbing; Week 6 final locked evaluation                                                                                                       |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Actual route accuracy, citation precision, latency, completion, and reviewer acceptance are measured.

- Initial project targets may be changed only before held-out lock or under a new evaluation version.

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

**GitHub Actions:** Official CI/CD workflow platform used for static, test, replay, and release gates. [Official source](https://docs.github.com/actions)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.15 of the uploaded ResolveFlow Replay Final Master Plan, pages 38-39. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
