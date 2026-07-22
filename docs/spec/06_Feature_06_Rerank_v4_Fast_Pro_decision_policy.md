# Feature 6: Rerank v4 Fast-Pro decision policy

**DOCUMENT 06 / FEATURE 6**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Quality-latency policy                                                                                                             |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.6, pages 32-33.                                                                                                          |
| **Primary phase**      | Week 2 adapters; Week 4 evaluation and policy lock                                                                                 |
| **Core rule**          | Fast and Pro comparisons are paired over identical authorized payloads. The project may choose Fast if Pro adds no material value. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.                |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 32-33. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Turn a Cohere product feature into an enterprise tradeoff decision. The project should not merely call both models; it should measure when the quality-latency exchange is justified. |
| Primary modules          | retrieval, model policy, evaluation, telemetry                                                                                                                                        |
| Primary data/entities    | retrieval_candidates, model_policy_versions, metric_observations, experiment_comparisons                                                                                              |
| API or interface surface | Model policy object; result page Fast/Pro comparison                                                                                                                                  |
| Related features         | Feature 5, Feature 7, Feature 14, Feature 15                                                                                                                                          |
| Implementation phase     | Week 2 adapters; Week 4 evaluation and policy lock                                                                                                                                    |
| Non-negotiable control   | Fast and Pro comparisons are paired over identical authorized payloads. The project may choose Fast if Pro adds no material value.                                                    |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Rerank a bounded authorized candidate set.

- Run Fast by default and Pro for declared escalation conditions or controlled experiments.

- Persist reorderings and relevance scores.

- Compare paired results on the same held-out cases.

- Expose the policy and its observed tradeoff on the results page.

- Never claim Pro is universally superior or Fast is always sufficient without evidence.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Receive the same authorized candidate payload for every paired comparison.
>
> **2.** Run Fast by default and record scores, order, latency, usage, and escalation reason.
>
> **3.** Escalate to Pro only under a locked severity/ambiguity policy or explicit experiment.
>
> **4.** Compute paired quality and operations differences at the base-truth level.
>
> **5.** Publish the observed frontier and selected policy without claiming a universal winner.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                              |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | retrieval, model policy, evaluation, telemetry                                                                                     |
| Persistent evidence            | retrieval_candidates, model_policy_versions, metric_observations, experiment_comparisons                                           |
| External/public interface      | Model policy object; result page Fast/Pro comparison                                                                               |
| Dependencies                   | Feature 5, Feature 7, Feature 14, Feature 15                                                                                       |
| Security/reliability invariant | Fast and Pro comparisons are paired over identical authorized payloads. The project may choose Fast if Pro adds no material value. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Format each candidate with source type, date, title, section, and content.

- Keep candidate order and payload hashes for replay.

- Use the same top-N across paired comparisons unless the experiment explicitly tests N.

- Bootstrap paired differences by base truth.

- Define an ambiguity proxy on the calibration split, such as small score margin or conflicting top sources.

- Lock the escalation rule before the held-out evaluation.

## 6 Failure-safe behavior and security review

- Fast and Pro comparisons are paired over identical authorized payloads. The project may choose Fast if Pro adds no material value.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

The public page shows a simple cost-quality-latency frontier with the number of cases, uncertainty interval, and selected policy. In the live demo, show one before-and-after reorder, not an entire benchmark lecture.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                 |
|----------------|-----------------------------------------------------------------------|
| Contract       | Fast and Pro adapters map scores and errors correctly.                |
| Pairing        | Identical candidate IDs, text payloads, order input, and top-N.       |
| Evaluation     | Paired base-truth bootstrap for quality, p95 latency, and usage/cost. |
| Budget         | Public path never makes an uncontrolled double call.                  |

### 8.1 Acceptance criteria

| **Criterion**       | **Pass condition**                                                     | **Failure behavior**                  |
|---------------------|------------------------------------------------------------------------|---------------------------------------|
| Pairing             | Fast and Pro receive identical authorized candidate payloads.          | Comparison invalidated.               |
| Statistical honesty | Report estimates and uncertainty intervals, not only winning examples. | Results page blocks publication mode. |
| Policy clarity      | Every Pro call has an escalation reason.                               | Telemetry warning and test failure.   |
| Operational budget  | No uncontrolled double-call occurs in public live mode.                | Fast result or snapshot fallback.     |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 5, Feature 7, Feature 14, Feature 15                                                                                                               |
| Primary roadmap phase        | Week 2 adapters; Week 4 evaluation and policy lock                                                                                                         |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Escalation threshold is calibrated and then locked.

- Cost and latency use actual provider usage and timestamps.

- No statement that Pro is better is made before paired results.

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

**Cohere Rerank v4:** Fast and Pro variants; multilingual text and semi-structured JSON; quality-versus-throughput positioning. [Official source](https://docs.cohere.com/docs/rerank)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.6 of the uploaded ResolveFlow Replay Final Master Plan, pages 32-33. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
