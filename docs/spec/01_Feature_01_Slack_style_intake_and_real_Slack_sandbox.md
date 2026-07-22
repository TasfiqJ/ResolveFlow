# Feature 1: Slack-style intake and real Slack sandbox

**DOCUMENT 01 / FEATURE 1**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Workflow entry and integration                                                                                      |
|------------------------|---------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.1, pages 29.                                                                                              |
| **Primary phase**      | Week 1: simulation and canonical schema; Week 5: real Slack sandbox                                                 |
| **Core rule**          | Slack authenticity and deduplication are ordinary-code controls. Model latency never blocks the acknowledgement.    |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions. |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 29. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                                                                                                                                                       |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Show that the system enters through an existing operational workflow rather than a generic chatbot. The public website uses a Slack-like interface because visitors cannot be added to a private workspace; the recorded and interview demo uses an actual Slack development workspace. |
| Primary modules          | intake, identity, API, Slack adapter, telemetry                                                                                                                                                                                                                                         |
| Primary data/entities    | cases, case_messages, users, role_bindings, audit_events                                                                                                                                                                                                                                |
| API or interface surface | POST /integrations/slack/events; POST /v1/cases; action interaction callbacks                                                                                                                                                                                                           |
| Related features         | Feature 2, Feature 11, Feature 13, Feature 18                                                                                                                                                                                                                                           |
| Implementation phase     | Week 1: simulation and canonical schema; Week 5: real Slack sandbox                                                                                                                                                                                                                     |
| Non-negotiable control   | Slack authenticity and deduplication are ordinary-code controls. Model latency never blocks the acknowledgement.                                                                                                                                                                        |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- A message or shortcut creates a canonical case with reporter, tenant, channel, timestamp, language hint, severity hint, and raw text.

- A Slack acknowledgement appears immediately; expensive work begins asynchronously.

- The app displays extracted fields and asks at most one targeted clarification when a required field cannot be fetched.

- Repeated Slack delivery events are deduplicated by Slack event ID and message timestamp.

- Interactive buttons open the trace, approve or reject the proposal when authorized, and show the Jira outcome.

- The public simulation uses the identical canonical case schema and backend execution path.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Receive a Slack event or public simulation request.
>
> **2.** Verify authenticity for real Slack and normalize both paths into the same canonical case schema.
>
> **3.** Persist the case and deduplication key, acknowledge immediately, and enqueue enrichment.
>
> **4.** Map the Slack user to an internal user/role binding, then expose only authorized controls.
>
> **5.** Stream queued/running/completed states and link the case to the trace and action state.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                            |
|--------------------------------|------------------------------------------------------------------------------------------------------------------|
| Ownership                      | intake, identity, API, Slack adapter, telemetry                                                                  |
| Persistent evidence            | cases, case_messages, users, role_bindings, audit_events                                                         |
| External/public interface      | POST /integrations/slack/events; POST /v1/cases; action interaction callbacks                                    |
| Dependencies                   | Feature 2, Feature 11, Feature 13, Feature 18                                                                    |
| Security/reliability invariant | Slack authenticity and deduplication are ordinary-code controls. Model latency never blocks the acknowledgement. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Use Bolt for Python in the FastAPI service or its official adapter.

- Verify every request using the signing secret and raw body; reject timestamps outside the accepted replay window.

- Return acknowledgement inside Slack's required response window, then enqueue enrichment.

- Store raw payload in a short-retention encrypted field or sanitized fixture; use only synthetic data in this project.

- Map Slack user IDs to ResolveFlow users and role bindings through a small synthetic directory.

- Use Block Kit for case cards, evidence summary, and approval state.

## 6 Failure-safe behavior and security review

- Slack authenticity and deduplication are ordinary-code controls. Model latency never blocks the acknowledgement.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

Record event ID, signature decision, acknowledgement latency, normalization errors, deduplication outcome, and case ID. In the private demo, start from Slack; on the public site, label the interface “Slack-style simulation” and link to the recorded real integration.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                               |
|----------------|-------------------------------------------------------------------------------------|
| Unit           | Canonical normalization, deduplication key, user mapping, permission checks.        |
| Contract       | Valid/invalid signatures, stale timestamps, challenge response, duplicate delivery. |
| Browser        | Slack-style simulation creates equivalent canonical case and visible queued state.  |
| Fault          | Model/provider delay does not delay acknowledgement.                                |

### 8.1 Acceptance criteria

| **Criterion**   | **Pass condition**                                                  | **Failure behavior**                       |
|-----------------|---------------------------------------------------------------------|--------------------------------------------|
| Authenticity    | Invalid signatures and stale requests are rejected.                 | HTTP rejection and security audit event.   |
| Idempotency     | Duplicate event delivery creates one case.                          | Existing case reference is returned.       |
| Responsiveness  | Slack acknowledgement is independent of model latency.              | Case remains queued with a visible status. |
| Schema fidelity | Web and Slack intake produce equivalent canonical cases.            | Contract test fails CI.                    |
| Authorization   | Approval controls do nothing for users without approval permission. | Ephemeral denial and audit event.          |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 2, Feature 11, Feature 13, Feature 18                                                                                                              |
| Primary roadmap phase        | Week 1: simulation and canonical schema; Week 5: real Slack sandbox                                                                                        |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Exact Slack app scopes and workspace IDs are installation-time facts.

- Observed acknowledgement latency is measured; no value is invented.

- Retention period for raw payloads is selected after reviewing the sandbox policy.

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

**Slack Bolt for Python:** Official Python framework for Slack apps and event handling. [Official source](https://docs.slack.dev/tools/bolt-python/)

**Slack request verification:** Sign requests with HMAC; verification requires the raw body and timestamp replay checks. [Official source](https://docs.slack.dev/authentication/verifying-requests-from-slack/)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.1 of the uploaded ResolveFlow Replay Final Master Plan, pages 29. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
