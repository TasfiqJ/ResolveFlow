# Feature 13: complete audit trace and run diff

**DOCUMENT 13 / FEATURE 13**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Auditability and explainability                                                                                        |
|------------------------|------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.13, pages 37.                                                                                                |
| **Primary phase**      | Week 1 minimal trace; Week 3 full timeline; Week 4 diff                                                                |
| **Core rule**          | Critical state changes and audit events are committed together. Public views use a deterministic redaction projection. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.    |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 37. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                            |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Make the project inspectable to both technical and nontechnical reviewers. The trace is the evidence that the project is not prompt theater. |
| Primary modules          | telemetry, audit, trace viewer, redaction, diff engine                                                                                       |
| Primary data/entities    | audit_events, run_steps, retrieval_candidates, tool_calls, claims, citations, action_attempts                                                |
| API or interface surface | GET /v1/runs/{id}/events; GET /v1/runs/{id}/trace; export bundle                                                                             |
| Related features         | All features; especially Feature 14, Feature 15, Feature 18                                                                                  |
| Implementation phase     | Week 1 minimal trace; Week 3 full timeline; Week 4 diff                                                                                      |
| Non-negotiable control   | Critical state changes and audit events are committed together. Public views use a deterministic redaction projection.                       |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Display a chronological timeline of case states, retrieval, Rerank, model calls, tools, verification, approval, connector attempts, and verdicts.

- Link every event to sanitized structured details.

- Show duration, actor, component, outcome, and correlation IDs.

- Compare two runs by role, corpus, candidates, model policy, claims, actions, and metrics.

- Support a public redacted view and an authenticated full synthetic view.

- Export the run as JSON and a concise PDF or Markdown report.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Emit domain events in the same transaction as critical state changes.
>
> **2.** Map OpenTelemetry spans to stable run, step, and event identifiers.
>
> **3.** Store detailed synthetic/provider payloads under restricted access and generate a deterministic public-redaction projection.
>
> **4.** Render a chronological timeline and link each event to safe structured details.
>
> **5.** Compute v0-v1 or mutation diffs from immutable snapshots and export a checksummed run report.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                  |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | telemetry, audit, trace viewer, redaction, diff engine                                                                 |
| Persistent evidence            | audit_events, run_steps, retrieval_candidates, tool_calls, claims, citations, action_attempts                          |
| External/public interface      | GET /v1/runs/{id}/events; GET /v1/runs/{id}/trace; export bundle                                                       |
| Dependencies                   | All features; especially Feature 14, Feature 15, Feature 18                                                            |
| Security/reliability invariant | Critical state changes and audit events are committed together. Public views use a deterministic redaction projection. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Emit append-only domain events in the same transaction as critical state changes.

- Map OpenTelemetry span IDs to domain event IDs.

- Store large provider payloads separately with restricted access and retention.

- Generate a deterministic redaction projection for public snapshots.

- Compute diffs from immutable snapshots, not current database state.

- Include the git commit and all version hashes at the top of the trace.

## 6 Failure-safe behavior and security review

- Critical state changes and audit events are committed together. Public views use a deterministic redaction projection.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

The trace viewer should be a core public page, not buried in logs. During the hero demo, click the failed invariant and jump directly to the candidate, source, or action event that caused it.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                              |
|----------------|------------------------------------------------------------------------------------|
| Unit           | Stable event schema, canonical ordering, redaction projection, diff engine.        |
| Integration    | Critical state and audit event commit together; OTel IDs link correctly.           |
| Security       | Pattern/high-entropy scans; restricted data and secrets absent from public export. |
| Golden         | Known role/corpus mutation appears once; export hashes reproduce.                  |

### 8.1 Acceptance criteria

| **Criterion**      | **Pass condition**                                                              | **Evidence**               |
|--------------------|---------------------------------------------------------------------------------|----------------------------|
| Reconstructability | Maintainer can explain final route and action from stored events alone.         | Runbook exercise.          |
| Redaction          | Public trace exposes no secrets, tokens, hidden prompts, or restricted content. | Automated scan and review. |
| Ordering           | Event sequence is stable and timestamps are coherent.                           | Contract tests.            |
| Diff accuracy      | Known role or corpus mutation appears exactly once in comparison.               | Golden snapshot tests.     |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | All features; especially Feature 14, Feature 15, Feature 18                                                                                                |
| Primary roadmap phase        | Week 1 minimal trace; Week 3 full timeline; Week 4 diff                                                                                                    |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Retention and provider-payload storage periods are finalized after staging review.

- The PDF/Markdown export format is selected after the trace schema stabilizes.

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

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.13 of the uploaded ResolveFlow Replay Final Master Plan, pages 37. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
