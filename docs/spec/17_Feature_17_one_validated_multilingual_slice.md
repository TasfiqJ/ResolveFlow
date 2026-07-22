# Feature 17: one validated multilingual slice

**DOCUMENT 17 / FEATURE 17**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Scoped multilingual validation                                                                                      |
|------------------------|---------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.17, pages 40.                                                                                             |
| **Primary phase**      | Week 5 only when a fluent reviewer is committed                                                                     |
| **Core rule**          | One language is claimed only after human validation; all authorization and action invariants remain identical.      |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions. |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 40. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                                         |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Demonstrate that multilingual capability is tested in an operationally realistic way rather than by machine-translating a benchmark and claiming broad language coverage. |
| Primary modules          | truth data, retrieval, agent, verifier, evaluation                                                                                                                        |
| Primary data/entities    | language variants, truth signoffs, per-slice metrics                                                                                                                      |
| API or interface surface | Predefined language scenario; result-page slice breakdown                                                                                                                 |
| Related features         | Feature 3, Feature 5, Feature 6, Feature 7, Feature 9, Feature 14, Feature 16                                                                                             |
| Implementation phase     | Week 5 only when a fluent reviewer is committed                                                                                                                           |
| Non-negotiable control   | One language is claimed only after human validation; all authorization and action invariants remain identical.                                                            |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Select one language for which a fluent reviewer is available; French is appropriate only if this condition is met.

- Author or human-verify incident text, terminology, and expected output.

- Test query-language and evidence-language combinations separately.

- Keep source IDs, error codes, product names, and structured facts stable across variants.

- Measure route, decisive evidence, grounding, abstention, and reviewer utility.

- Report sample size and uncertainty; do not generalize to all languages supported by the model.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Commit a fluent reviewer before generating the slice; otherwise remove the quality claim.
>
> **2.** Human-author or human-verify incident text, terminology, gold meaning, and expected behavior.
>
> **3.** Create declared query-language/evidence-language conditions while preserving IDs, codes, and structured facts.
>
> **4.** Run the same ACL, retrieval, verifier, action, and Replay gates as English.
>
> **5.** Report per-condition route, evidence, grounding, abstention, and reviewer utility without generalizing beyond the validated slice.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                          |
|--------------------------------|----------------------------------------------------------------------------------------------------------------|
| Ownership                      | truth data, retrieval, agent, verifier, evaluation                                                             |
| Persistent evidence            | language variants, truth signoffs, per-slice metrics                                                           |
| External/public interface      | Predefined language scenario; result-page slice breakdown                                                      |
| Dependencies                   | Feature 3, Feature 5, Feature 6, Feature 7, Feature 9, Feature 14, Feature 16                                  |
| Security/reliability invariant | One language is claimed only after human validation; all authorization and action invariants remain identical. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

Build four declared conditions where feasible:

1\. English query and English evidence;

2\. validated non-English query and English evidence;

3\. validated non-English query and mixed evidence;

4\. English query and validated non-English evidence.

Use human review to catch translation artifacts and culturally odd support language. Do not use an automated translation system as the sole validator.

## 6 Failure-safe behavior and security review

- One language is claimed only after human validation; all authorization and action invariants remain identical.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

Use the non-English case in the live demo only when pronunciation, labels, and reviewer validation are ready. Otherwise use English live and present the validated slice on the results page.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                   |
|----------------|-------------------------------------------------------------------------|
| Content review | Fluent reviewer signs query, terminology, and gold meaning.             |
| Pairing        | Stable IDs/codes/structured facts across language conditions.           |
| Evaluation     | Per-condition route, decisive evidence, grounding, abstention, utility. |
| Security       | Same ACL/action hard gates; violation is immediate NO SHIP.             |

### 8.1 Acceptance criteria

| **Criterion**    | **Pass condition**                                                    | **Failure behavior**                              |
|------------------|-----------------------------------------------------------------------|---------------------------------------------------|
| Human validation | A fluent reviewer signs off on query and gold meaning.                | Remove multilingual quality claim if unavailable. |
| Slice reporting  | Results are broken out by language configuration.                     | Results page blocks aggregate-only claim.         |
| Security parity  | The same ACL and action invariants apply.                             | Immediate NO SHIP on violation.                   |
| Scope honesty    | README says “validated \[language\] slice,” not “fully multilingual.” | Required.                                         |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 3, Feature 5, Feature 6, Feature 7, Feature 9, Feature 14, Feature 16                                                                              |
| Primary roadmap phase        | Week 5 only when a fluent reviewer is committed                                                                                                            |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Language is not locked until a fluent reviewer is available.

- If no reviewer is available, the quality claim is removed rather than guessed.

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

**Cohere Command A+:** Model ID command-a-plus-05-2026; 128k context; reasoning, tool use, citations, structured output, multilingual and image input. [Official source](https://docs.cohere.com/docs/command-a-plus)

**Cohere Embed v4:** Model ID embed-v4.0; text, image, mixed input; configurable dimensions; 128k context. [Official source](https://docs.cohere.com/docs/cohere-embed)

**Cohere Rerank v4:** Fast and Pro variants; multilingual text and semi-structured JSON; quality-versus-throughput positioning. [Official source](https://docs.cohere.com/docs/rerank)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.17 of the uploaded ResolveFlow Replay Final Master Plan, pages 40. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
