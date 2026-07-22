# Feature 7: bounded Command A+ agent loop

**DOCUMENT 07 / FEATURE 7**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Governed agent orchestration                                                                                             |
|------------------------|--------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.7, pages 33.                                                                                                   |
| **Primary phase**      | Week 1 basic cited read path; Week 3 bounded tool loop                                                                   |
| **Core rule**          | Tools are typed and allowlisted. The model cannot write directly, expand tool scope, or exceed fixed rounds/time/budget. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.      |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 33. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                                 |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Demonstrate practical agent engineering: tools are narrow, execution is bounded, evidence is explicit, and the model cannot directly write to an external system. |
| Primary modules          | agent, tools, adapters, verifier, actions, telemetry                                                                                                              |
| Primary data/entities    | agent_runs, run_steps, tool_calls, claims, citations                                                                                                              |
| API or interface surface | POST /v1/cases/{id}/runs; GET /v1/runs/{id}; SSE run events                                                                                                       |
| Related features         | Feature 2, Feature 5, Feature 6, Feature 8, Feature 9, Feature 10, Feature 11                                                                                     |
| Implementation phase     | Week 1 basic cited read path; Week 3 bounded tool loop                                                                                                            |
| Non-negotiable control   | Tools are typed and allowlisted. The model cannot write directly, expand tool scope, or exceed fixed rounds/time/budget.                                          |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Command A+ can request customer context, rollout records, incident records, and an inert Jira proposal.

- Tool calls are validated, authorized, timed, and logged.

- The loop has maximum rounds, total wall-clock, and provider-call budgets.

- Retrieved instructions are treated as data.

- Unknown or failed tools produce explicit errors.

- The response separates verified facts, unknowns, conflicts, route, recommended steps, and proposal.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Create the first Chat request with case state, authorized documents, narrow tools, and untrusted-content rules.
>
> **2.** Validate and authorize each returned tool call locally.
>
> **3.** Execute read or inert-proposal tools with independent timeouts and normalized results.
>
> **4.** Append tool results and repeat only within the fixed round/time/token budget.
>
> **5.** Persist provider responses, citations, usage, and observable decisions, then hand the draft to the verifier.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                    |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | agent, tools, adapters, verifier, actions, telemetry                                                                     |
| Persistent evidence            | agent_runs, run_steps, tool_calls, claims, citations                                                                     |
| External/public interface      | POST /v1/cases/{id}/runs; GET /v1/runs/{id}; SSE run events                                                              |
| Dependencies                   | Feature 2, Feature 5, Feature 6, Feature 8, Feature 9, Feature 10, Feature 11                                            |
| Security/reliability invariant | Tools are typed and allowlisted. The model cannot write directly, expand tool scope, or exceed fixed rounds/time/budget. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Use the official V2 Chat API and \`strict_tools=true\` after current compatibility is verified.

- Keep the system prompt versioned in plain text with tests for required clauses.

- Serialize tool results in compact JSON and include provenance IDs.

- Refuse URL fetching, arbitrary SQL, arbitrary Jira fields, and shell execution.

- Set a low temperature for operational consistency and record the seed.

- Preserve provider response IDs, finish reasons, citations, usage, and tool-call payloads.

## 6 Failure-safe behavior and security review

- Tools are typed and allowlisted. The model cannot write directly, expand tool scope, or exceed fixed rounds/time/budget.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

| **HARD-GATE SENSITIVITY** | This feature protects a release-blocking invariant. Deliberately removing the control must make at least one deterministic or replay test fail. |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|

## 7 Telemetry and demo proof

The trace shows tool name, validated inputs, duration, result status, and evidence IDs. Do not reveal hidden model reasoning. Show observable messages, tool calls, and decisions only.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                                      |
|----------------|--------------------------------------------------------------------------------------------|
| Unit           | Tool schemas, local validation, authorization, budget termination, failure objects.        |
| Contract       | Tool call, citation, finish reason, usage, throttling, malformed output, timeout fixtures. |
| Security       | Unknown tool, extra fields, arbitrary URL/SQL/Jira/shell attempts rejected.                |
| Fault          | Provider/tool timeout terminates visibly and never dispatches an action.                   |

### 8.1 Acceptance criteria

| **Criterion**        | **Pass condition**                                         | **Release impact**                            |
|----------------------|------------------------------------------------------------|-----------------------------------------------|
| Tool schema validity | 100% of accepted calls conform locally.                    | Invalid calls count as failures.              |
| Tool authorization   | Zero unauthorized execution attempts reach adapters.       | NO SHIP if any write or data access succeeds. |
| Bounded execution    | Every run terminates within configured rounds and timeout. | Operational gate failure.                     |
| Direct writes        | Zero model-triggered Jira writes.                          | Immediate NO SHIP.                            |
| Unknown handling     | Missing decisive evidence yields abstention or review.     | Quality gate.                                 |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 2, Feature 5, Feature 6, Feature 8, Feature 9, Feature 10, Feature 11                                                                              |
| Primary roadmap phase        | Week 1 basic cited read path; Week 3 bounded tool loop                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Final time/token limits are measured in staging and encoded in model policy.

- Provider strict-tool compatibility is rechecked before enablement.

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

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.7 of the uploaded ResolveFlow Replay Final Master Plan, pages 33. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
