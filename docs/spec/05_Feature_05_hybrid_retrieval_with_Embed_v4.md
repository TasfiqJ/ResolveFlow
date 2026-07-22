# Feature 5: hybrid retrieval with Embed v4

**DOCUMENT 05 / FEATURE 5**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Retrieval engineering                                                                                               |
|------------------------|---------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.5, pages 31-32.                                                                                           |
| **Primary phase**      | Week 2                                                                                                              |
| **Core rule**          | Only authorized candidates enter vector, lexical, fusion, or Rerank stages.                                         |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions. |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 31-32. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                                                                             |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Show retrieval engineering rather than “send everything to the model.” The selected domain contains semantic paraphrases and exact identifiers, so vector and lexical retrieval have complementary strengths. |
| Primary modules          | retrieval, corpus, policy, Cohere adapter, evaluation                                                                                                                                                         |
| Primary data/entities    | embeddings, retrieval_candidates, run_steps, metric_observations                                                                                                                                              |
| API or interface surface | Resolve-run retrieval stage; trace view exposes ranks and provenance                                                                                                                                          |
| Related features         | Feature 3, Feature 4, Feature 6, Feature 9, Feature 13, Feature 15                                                                                                                                            |
| Implementation phase     | Week 2                                                                                                                                                                                                        |
| Non-negotiable control   | Only authorized candidates enter vector, lexical, fusion, or Rerank stages.                                                                                                                                   |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Build a query from the incident text, normalized error code, service, region, rollout window, and known context.

- Execute eligible vector and lexical searches in parallel.

- Deduplicate by chunk and cap chunks per artifact.

- Fuse ranks, retain component scores, and create a bounded candidate set.

- Support the dashboard image in the vector index while preserving modality.

- Produce Recall at 10 and nDCG at 10 against decisive-evidence labels.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Construct a query from incident text, exact identifiers, service, region, rollout window, and deterministic context.
>
> **2.** Run authorized vector and full-text searches in parallel.
>
> **3.** Deduplicate and apply per-artifact diversity caps.
>
> **4.** Fuse ranks with a preregistered reciprocal-rank-fusion constant.
>
> **5.** Persist component scores and the bounded candidate set for Rerank and evaluation.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                       |
|--------------------------------|-----------------------------------------------------------------------------|
| Ownership                      | retrieval, corpus, policy, Cohere adapter, evaluation                       |
| Persistent evidence            | embeddings, retrieval_candidates, run_steps, metric_observations            |
| External/public interface      | Resolve-run retrieval stage; trace view exposes ranks and provenance        |
| Dependencies                   | Feature 3, Feature 4, Feature 6, Feature 9, Feature 13, Feature 15          |
| Security/reliability invariant | Only authorized candidates enter vector, lexical, fusion, or Rerank stages. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Embed the natural-language query with \`embed-v4.0\` and \`search_query\` input type.

- Store 1024-dimensional float vectors with an index appropriate to the corpus size; exact search is acceptable for a tiny corpus if it improves reproducibility.

- Use PostgreSQL \`tsvector\` fields for exact error codes, identifiers, headings, and terms.

- Apply reciprocal-rank fusion with a pre-registered constant.

- Add query fixtures that intentionally defeat lexical-only and vector-only retrieval.

- Do not tune on held-out truths.

## 6 Failure-safe behavior and security review

- Only authorized candidates enter vector, lexical, fusion, or Rerank stages.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

Show the candidate list before Rerank and highlight why the decisive rollout record is present but not yet first. Avoid animated score theater; use actual stored ranks and source metadata.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                     |
|----------------|---------------------------------------------------------------------------|
| Unit           | Query construction, reciprocal-rank fusion, deduplication, diversity cap. |
| Integration    | Authorized vector/full-text search over seeded PostgreSQL corpus.         |
| Evaluation     | Lexical, vector, hybrid, hybrid+Rerank Recall@10 and nDCG@10.             |
| Regression     | Exact error codes and semantic paraphrases both remain retrievable.       |

### 8.1 Acceptance criteria

| **Criterion**           | **Pass condition**                                                                                                           | **Evidence**                     |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| Decisive evidence       | Held-out Recall@10 is measured against the preregistered baseline; the report publishes the result whether it passes or not. | Raw case-level results.          |
| Identifier preservation | Exact error-code evidence remains retrievable.                                                                               | Targeted tests.                  |
| Authorization           | Search plans include the eligibility predicate.                                                                              | Query review and security tests. |
| Trace completeness      | Every candidate retains vector, lexical, and fused ranks when applicable.                                                    | Run trace.                       |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 3, Feature 4, Feature 6, Feature 9, Feature 13, Feature 15                                                                                         |
| Primary roadmap phase        | Week 2                                                                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Index type is selected after corpus-size measurement; exact search is acceptable for the small corpus.

- Fusion constant and top-K are frozen on calibration, not tuned on held-out cases.

- Actual retrieval gains remain unclaimed until evaluation.

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

**Cohere Embed v4:** Model ID embed-v4.0; text, image, mixed input; configurable dimensions; 128k context. [Official source](https://docs.cohere.com/docs/cohere-embed)

**Cohere Rerank v4:** Fast and Pro variants; multilingual text and semi-structured JSON; quality-versus-throughput positioning. [Official source](https://docs.cohere.com/docs/rerank)

**PostgreSQL versioning:** PostgreSQL 17 remains supported; PostgreSQL 18 is current. The plan targets a 17-compatible managed service and can upgrade after compatibility tests. [Official source](https://www.postgresql.org/support/versioning/)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.5 of the uploaded ResolveFlow Replay Final Master Plan, pages 31-32. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
