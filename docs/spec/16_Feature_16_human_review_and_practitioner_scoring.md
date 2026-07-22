# Feature 16: human review and practitioner scoring

**DOCUMENT 16 / FEATURE 16**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Human-centered evaluation                                                                                                            |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.16, pages 39-40.                                                                                                           |
| **Primary phase**      | Week 5 review collection; Week 6 analysis                                                                                            |
| **Core rule**          | Outputs are blinded and randomized. Objective correctness is separated from reviewer preference; exact counts accompany percentages. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.                  |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 39-40. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                      |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Measure practical usefulness without outsourcing truth to an LLM judge. FDE work succeeds when operators can use and trust the output. |
| Primary modules          | review app, evaluation, reporting, public results                                                                                      |
| Primary data/entities    | review_assignments, review_scores, reviewer metadata, comparison results                                                               |
| API or interface surface | Private/static review flow; aggregate result export                                                                                    |
| Related features         | Feature 15, Feature 17, Feature 18                                                                                                     |
| Implementation phase     | Week 5 review collection; Week 6 analysis                                                                                              |
| Non-negotiable control   | Outputs are blinded and randomized. Objective correctness is separated from reviewer preference; exact counts accompany percentages.   |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Present blind, randomized pairs of baseline and candidate outputs.

- Ask reviewers to score routing usefulness, evidence sufficiency, action safety, clarity, and edit effort.

- Capture reviewer role, familiarity, and optional rationale without collecting confidential employer data.

- Separate objective correctness from preference.

- Report inter-reviewer agreement and disagreement examples.

- Use reviewers fluent in the non-English slice.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Create blind randomized A/B assignments over paired case outputs.
>
> **2.** Show the case and allowed T0 evidence without revealing build or model labels.
>
> **3.** Collect route usefulness, evidence sufficiency, action safety, clarity, edit effort, categorical decision, optional rationale, role, familiarity, and timing.
>
> **4.** Separate objective correctness from preference and calculate agreement/disagreement with exact counts.
>
> **5.** Publish a modest qualitative claim sized to the actual reviewer and case sample.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                                |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | review app, evaluation, reporting, public results                                                                                    |
| Persistent evidence            | review_assignments, review_scores, reviewer metadata, comparison results                                                             |
| External/public interface      | Private/static review flow; aggregate result export                                                                                  |
| Dependencies                   | Feature 15, Feature 17, Feature 18                                                                                                   |
| Security/reliability invariant | Outputs are blinded and randomized. Objective correctness is separated from reviewer preference; exact counts accompany percentages. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

Create a small review application or static form with:

- case information available at T0;

- output A and B without model or build labels;

- gold route hidden until submission;

- five-point usefulness rubric plus accept, minor edit, major edit, reject;

- field for unsafe or unsupported claims;

- timing from open to submission. For a solo project, three to five reviewers across at least ten cases is useful qualitative evidence but not a population-level claim. Report exact counts.

## 6 Failure-safe behavior and security review

- Outputs are blinded and randomized. Objective correctness is separated from reviewer preference; exact counts accompany percentages.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

Show one compact reviewer result in the final metrics and link to the full rubric. Do not let a tiny reviewer sample dominate the headline.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                          |
|----------------|--------------------------------------------------------------------------------|
| Unit           | Randomization, blinding, rubric validation, exact counts.                      |
| Review UX      | Build/model labels absent; gold route hidden until submission.                 |
| Analysis       | Agreement, disagreements, accept/minor/major/reject, timing, role/familiarity. |
| Privacy        | No confidential employer data; publish aggregate roles and exact sample.       |

### 8.1 Acceptance criteria

| **Criterion**       | **Pass condition**                                        | **Publication rule**           |
|---------------------|-----------------------------------------------------------|--------------------------------|
| Blinding            | Reviewers cannot see build labels.                        | Required for comparison claim. |
| Domain fit          | Reviewer roles are relevant and disclosed in aggregate.   | Required.                      |
| No fabricated scale | Exact reviewer and case counts appear beside percentages. | Required.                      |
| Disagreements       | At least one disagreement is discussed.                   | Required for credibility.      |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 15, Feature 17, Feature 18                                                                                                                         |
| Primary roadmap phase        | Week 5 review collection; Week 6 analysis                                                                                                                  |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Reviewer identities are not predetermined in the document.

- Sample size is reported exactly and never inflated into a population claim.

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

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.16 of the uploaded ResolveFlow Replay Final Master Plan, pages 39-40. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
