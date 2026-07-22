# Feature 8: evidence graph and two-pass structured response

**DOCUMENT 08 / FEATURE 8**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Evidence closure and response contract                                                                                           |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.8, pages 33-34.                                                                                                        |
| **Primary phase**      | Week 3                                                                                                                           |
| **Core rule**          | The second model pass has no documents or tools and can only structure verified state; deterministic code renders the user view. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.              |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 33-34. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                                                    |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Separate discovery and reasoning from final product schema, while adapting to the current API constraint that structured response format cannot be combined with tools or documents. |
| Primary modules          | agent, verifier, domain schemas, deterministic renderer                                                                                                                              |
| Primary data/entities    | claims, citations, verifier_results, evidence_graphs, final_responses                                                                                                                |
| API or interface surface | Run response schema and evidence graph in trace                                                                                                                                      |
| Related features         | Feature 7, Feature 9, Feature 11, Feature 13                                                                                                                                         |
| Implementation phase     | Week 3                                                                                                                                                                               |
| Non-negotiable control   | The second model pass has no documents or tools and can only structure verified state; deterministic code renders the user view.                                                     |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- The first pass may use documents and tools and produces evidence-linked findings.

- The verifier constructs a machine-readable graph of facts, unknowns, conflicts, routes, and permitted proposals.

- The second pass receives only verified graph content and a JSON schema.

- The final renderer is deterministic and cannot add new facts.

- Schema failure is visible and recoverable without an unconstrained hidden rewrite.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Parse the first-pass draft and tool results into candidate facts, unknowns, conflicts, route candidates, and permitted proposal state.
>
> **2.** Verify each evidence node and compute a canonical evidence-graph hash.
>
> **3.** Call the second pass with only the verified graph and a strict response schema; supply no tools or original documents.
>
> **4.** Validate locally with Pydantic and reject unknown fields.
>
> **5.** Render deterministically; on structure failure, show a minimal verified needs_review response.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                            |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | agent, verifier, domain schemas, deterministic renderer                                                                          |
| Persistent evidence            | claims, citations, verifier_results, evidence_graphs, final_responses                                                            |
| External/public interface      | Run response schema and evidence graph in trace                                                                                  |
| Dependencies                   | Feature 7, Feature 9, Feature 11, Feature 13                                                                                     |
| Security/reliability invariant | The second model pass has no documents or tools and can only structure verified state; deterministic code renders the user view. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Define Pydantic models for every evidence node and final response.

- Hash the graph before the second call and record the hash in the final response.

- Set \`additionalProperties=false\` where the provider schema supports it and enforce it locally regardless.

- Keep final field text concise enough to audit.

- Use a deterministic minimal response when the structure call fails: disposition, verified facts, unknowns, and \`needs_review\`.

- Test that inserting an unsupported fact into the second-pass input is impossible through the normal code path.

## 6 Failure-safe behavior and security review

- The second model pass has no documents or tools and can only structure verified state; deterministic code renders the user view.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

Show the evidence graph as a compact panel and the final answer beside it. Explain the architectural constraint in the README and interview, not as a complaint but as a deliberate adaptation.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                         |
|----------------|-------------------------------------------------------------------------------|
| Unit           | Evidence-node schemas, graph hash, source closure, fallback response.         |
| Contract       | Second-pass request contains no tools/documents and matches current Chat API. |
| Snapshot       | Identical validated JSON renders identically.                                 |
| Negative       | Unsupported fact cannot enter second-pass input through normal code.          |

### 8.1 Acceptance criteria

| **Criterion**          | **Pass condition**                                                         | **Evidence**               |
|------------------------|----------------------------------------------------------------------------|----------------------------|
| Source closure         | Every final material claim maps to a verified evidence-graph fact.         | Automated graph traversal. |
| Schema validity        | Validity rate is measured; invalid output never appears as normal success. | Held-out results.          |
| No new tool access     | Second pass has no tools or original documents.                            | Provider request trace.    |
| Deterministic renderer | The same validated JSON renders identically.                               | Snapshot tests.            |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 7, Feature 9, Feature 11, Feature 13                                                                                                               |
| Primary roadmap phase        | Week 3                                                                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Schema-valid rate is measured, not assumed.

- Fallback wording is fixed and tested before held-out evaluation.

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

**Cohere Chat V2:** Tools, documents, citations and structured response; response_format limitation with documents/tools; seed best-effort; strict tools beta. [Official source](https://docs.cohere.com/reference/chat)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.8 of the uploaded ResolveFlow Replay Final Master Plan, pages 33-34. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
