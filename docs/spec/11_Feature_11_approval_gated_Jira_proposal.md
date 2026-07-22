# Feature 11: approval-gated Jira proposal

**DOCUMENT 11 / FEATURE 11**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Human approval boundary                                                                                             |
|------------------------|---------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.11, pages 35-36.                                                                                          |
| **Primary phase**      | Week 3                                                                                                              |
| **Core rule**          | Approval binds an authorized human to the exact proposal digest. The worker can dispatch but cannot approve.        |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions. |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 35-36. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                                           |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Show a safe human-agent collaboration boundary. The model may prepare a useful action, but only an authorized human can approve the exact payload that is later dispatched. |
| Primary modules          | actions, identity, policy, verifier, Jira adapter                                                                                                                           |
| Primary data/entities    | action_proposals, approvals, action_attempts, audit_events                                                                                                                  |
| API or interface surface | POST /v1/actions/{id}/approve; POST /v1/actions/{id}/reject                                                                                                                 |
| Related features         | Feature 7, Feature 8, Feature 9, Feature 12, Feature 13, Feature 15                                                                                                         |
| Implementation phase     | Week 3                                                                                                                                                                      |
| Non-negotiable control   | Approval binds an authorized human to the exact proposal digest. The worker can dispatch but cannot approve.                                                                |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- The model can create an inert proposal containing summary, team, priority, verified description, and cited evidence links.

- Proposal UI displays what will be sent, why, risk level, evidence, unknowns, and expiration.

- Approval requires an authenticated user with the correct permission.

- Approval is bound to a proposal content hash; any edit invalidates it.

- Rejection records a reason and can generate a revised proposal through a new run.

- Public mode simulates dispatch; staging can create an issue in a Jira development project.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Create an inert action proposal from verified evidence only.
>
> **2.** Show exact summary, team, priority, description source, evidence, unknowns, risk, expiry, and proposal digest.
>
> **3.** Require recent authenticated approval from a user with approve_jira.
>
> **4.** Invalidate approval on any payload change or expiry.
>
> **5.** Let only the worker service identity dispatch the approved digest; simulate in public and use a Jira development project in staging.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                        |
|--------------------------------|--------------------------------------------------------------------------------------------------------------|
| Ownership                      | actions, identity, policy, verifier, Jira adapter                                                            |
| Persistent evidence            | action_proposals, approvals, action_attempts, audit_events                                                   |
| External/public interface      | POST /v1/actions/{id}/approve; POST /v1/actions/{id}/reject                                                  |
| Dependencies                   | Feature 7, Feature 8, Feature 9, Feature 12, Feature 13, Feature 15                                          |
| Security/reliability invariant | Approval binds an authorized human to the exact proposal digest. The worker can dispatch but cannot approve. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Use a two-step domain API: \`create_proposal\` and \`approve_proposal\`.

- The dispatcher reads only approved rows and independently reconstructs or validates the Jira payload.

- Keep Jira field mapping in configuration, not model output.

- Use Atlassian OAuth 2.0 3LO for a user-installed development integration or a narrowly scoped development credential if 3LO setup is disproportionate; document the choice.

- Store Jira issue key, request ID if available, response status, and synthetic idempotency marker.

- Disallow attachments, arbitrary labels, watchers, comments, transitions, and cross-project writes in v1.

## 6 Failure-safe behavior and security review

- Approval binds an authorized human to the exact proposal digest. The worker can dispatch but cannot approve.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

| **HARD-GATE SENSITIVITY** | This feature protects a release-blocking invariant. Deliberately removing the control must make at least one deterministic or replay test fail. |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|

## 7 Telemetry and demo proof

Show the pending proposal, the human click, the resulting audit events, and the Jira issue in the private demo. On the public site, show a clearly labeled synthetic connector response so a visitor cannot create external tickets.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                                     |
|----------------|-------------------------------------------------------------------------------------------|
| Unit/state     | Proposal, approval, rejection, expiry, content change, double click.                      |
| Security       | Unauthorized approver denied; public deployment startup fails if Jira writes are enabled. |
| Integration    | Approved digest equals dispatched payload; staging Jira issue key recorded.               |
| Concurrency    | Only one approval/dispatch transition succeeds.                                           |

### 8.1 Acceptance criteria

| **Criterion**     | **Pass condition**                                         | **Release impact** |
|-------------------|------------------------------------------------------------|--------------------|
| Unapproved write  | Zero.                                                      | Immediate NO SHIP. |
| Payload integrity | Dispatched payload hash equals approved proposal hash.     | Immediate NO SHIP. |
| Authorization     | Only users with approve_jira can approve.                  | Immediate NO SHIP. |
| Expiration        | Expired proposals cannot dispatch.                         | Security gate.     |
| Public safety     | Public production has no credential capable of Jira write. | Deployment gate.   |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 7, Feature 8, Feature 9, Feature 12, Feature 13, Feature 15                                                                                        |
| Primary roadmap phase        | Week 3                                                                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Exact Jira project and field mapping are discovered from the development site.

- OAuth 2.0 3LO versus a narrowly scoped development credential is documented after setup.

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

**Atlassian OAuth 2.0 (3LO):** Official authorization option for user-installed Jira Cloud apps. [Official source](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)

**Jira Cloud REST API v3 - Issues:** Official issue-create and issue-query API surface. [Official source](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.11 of the uploaded ResolveFlow Replay Final Master Plan, pages 35-36. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
