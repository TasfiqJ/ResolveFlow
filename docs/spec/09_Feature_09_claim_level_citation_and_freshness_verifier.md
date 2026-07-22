# Feature 9: claim-level citation and freshness verifier

**DOCUMENT 09 / FEATURE 9**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Grounding and freshness control                                                                                                            |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.9, pages 34.                                                                                                                     |
| **Primary phase**      | Week 3                                                                                                                                     |
| **Core rule**          | Provider citations are mappings, not final proof. Authorization, version, freshness, and material support are checked in application code. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.                        |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 34. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                          |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Make citations a control rather than decoration. A cited answer can still be wrong, stale, unauthorized, or unsupported by the cited span. |
| Primary modules          | verifier, policy, corpus, evaluation                                                                                                       |
| Primary data/entities    | claims, citations, verifier_results, artifact_versions                                                                                     |
| API or interface surface | Run trace claim/citation detail; final-response gate                                                                                       |
| Related features         | Feature 4, Feature 8, Feature 10, Feature 11, Feature 13, Feature 15                                                                       |
| Implementation phase     | Week 3                                                                                                                                     |
| Non-negotiable control   | Provider citations are mappings, not final proof. Authorization, version, freshness, and material support are checked in application code. |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Identify material claims in route, root-cause hypothesis, timeline, recommended steps, and action fields.

- Require one or more source spans for each material factual claim.

- Recheck ACL, source version, effective time, and presence in model context.

- Detect exact contradictions for structured fields and declared scenario truths.

- Block unsupported action proposals.

- Render unresolved claims as unknowns or reviewer warnings, not confident prose.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Resolve every provider citation to an exact artifact version and span.
>
> **2.** Recheck tenant, role, region, classification, effective time, and presence in the model context.
>
> **3.** Split the response into material claims and map each to one or more evidence spans.
>
> **4.** Apply deterministic checks first, then use a narrowly scoped secondary semantic check only when necessary.
>
> **5.** Block forbidden, stale, contradicted, or unsupported action-relevant claims and render unresolved content as unknown/review.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                                      |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | verifier, policy, corpus, evaluation                                                                                                       |
| Persistent evidence            | claims, citations, verifier_results, artifact_versions                                                                                     |
| External/public interface      | Run trace claim/citation detail; final-response gate                                                                                       |
| Dependencies                   | Feature 4, Feature 8, Feature 10, Feature 11, Feature 13, Feature 15                                                                       |
| Security/reliability invariant | Provider citations are mappings, not final proof. Authorization, version, freshness, and material support are checked in application code. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

Use three layers:

1\. deterministic checks for IDs, dates, route labels, tenant, role, and action fields;

2\. span containment and source-version checks;

3\. a narrowly scoped semantic entailment check only where deterministic checks cannot decide, with human review on the final

held-out sample. Do not let the same generation response self-grade. If a model-based entailment helper is used, treat it as secondary evidence and publish the exact rubric and disagreement rate.

## 6 Failure-safe behavior and security review

- Provider citations are mappings, not final proof. Authorization, version, freshness, and material support are checked in application code.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

| **HARD-GATE SENSITIVITY** | This feature protects a release-blocking invariant. Deliberately removing the control must make at least one deterministic or replay test fail. |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|

## 7 Telemetry and demo proof

The UI lets a reviewer click a claim and see the exact supporting span, source time, role decision, and verifier code. One failed claim should appear in the postmortem to demonstrate honest limitations.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                   |
|----------------|-------------------------------------------------------------------------|
| Unit           | Span resolution, exact IDs/dates/routes/action fields, freshness rules. |
| Security       | Unauthorized or absent-in-context citation always rejected.             |
| Human review   | Stratified material-claim sample and disputed cases.                    |
| Regression     | One genuine final-candidate verifier failure becomes a replay.          |

### 8.1 Acceptance criteria

| **Criterion**         | **Pass condition**                                                                | **Release impact**                        |
|-----------------------|-----------------------------------------------------------------------------------|-------------------------------------------|
| Unauthorized citation | Zero.                                                                             | Immediate NO SHIP.                        |
| Missing source        | No material claim ships without a source or explicit unknown label.               | NO SHIP for action-supporting claims.     |
| Stale support         | A stale source cannot support a current action when a current source is required. | Scenario failure.                         |
| Human agreement       | Reviewer sample documents verifier precision and disputed cases.                  | Required before a strong grounding claim. |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 4, Feature 8, Feature 10, Feature 11, Feature 13, Feature 15                                                                                       |
| Primary roadmap phase        | Week 3                                                                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Any semantic entailment helper is secondary and human-reviewed.

- Verifier precision is reported from a reviewed sample before strong grounding claims.

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

**Cohere Chat V2:** Tools, documents, citations and structured response; response_format limitation with documents/tools; seed best-effort; strict tools beta. [Official source](https://docs.cohere.com/reference/chat)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.9 of the uploaded ResolveFlow Replay Final Master Plan, pages 34. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
