# Feature 18: snapshot-first public mode and rate-limited live mode

**DOCUMENT 18 / FEATURE 18**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Public reliability and cost control                                                                                                                |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.18, pages 40-41.                                                                                                                         |
| **Primary phase**      | Week 1 snapshot shell; Week 5 complete public product                                                                                              |
| **Core rule**          | The public experience is complete without provider availability. Live mode is predefined, rate-limited, read-only, and removable by a kill switch. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.                                |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 40-41. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                                  |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Give any visitor an immediate, reliable product experience while still proving that real Cohere inference exists.                                  |
| Primary modules          | Next.js web, API sessions, replay snapshots, rate limits, telemetry                                                                                |
| Primary data/entities    | published snapshots, public tokens, usage counters, release bundles                                                                                |
| API or interface surface | Public cases/runs/replays/releases plus health and version endpoints                                                                               |
| Related features         | Feature 13, Feature 14, Feature 15                                                                                                                 |
| Implementation phase     | Week 1 snapshot shell; Week 5 complete public product                                                                                              |
| Non-negotiable control   | The public experience is complete without provider availability. Live mode is predefined, rate-limited, read-only, and removable by a kill switch. |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Every public scenario loads a stored run snapshot instantly.

- The page clearly displays snapshot date, build, commit, model policy, and corpus version.

- A “Run live with Cohere” control is available only under current budget and security conditions.

- Live mode accepts predefined synthetic cases and mutations only.

- No arbitrary file upload, URL retrieval, custom prompt injection text, or external connector write is exposed.

- Live failure falls back to the snapshot with an honest status message.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Load a signed stored run snapshot immediately and display its date, build, commit, model policy, corpus version, and recorded badge.
>
> **2.** Allow optional live execution only for predefined synthetic cases and mutations under server-side session/IP/global limits.
>
> **3.** Keep provider keys server-side, enforce one active run per session, queue limits, timeout, and kill switch.
>
> **4.** Fall back to the matching snapshot on provider, budget, or dependency failure with an honest status message.
>
> **5.** Publish sanitized traces and keep the complete public product usable with Cohere, Slack, Jira, or live API unavailable.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                                              |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | Next.js web, API sessions, replay snapshots, rate limits, telemetry                                                                                |
| Persistent evidence            | published snapshots, public tokens, usage counters, release bundles                                                                                |
| External/public interface      | Public cases/runs/replays/releases plus health and version endpoints                                                                               |
| Dependencies                   | Feature 13, Feature 14, Feature 15                                                                                                                 |
| Security/reliability invariant | The public experience is complete without provider availability. Live mode is predefined, rate-limited, read-only, and removable by a kill switch. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Publish signed JSON result bundles with the web build or read them from the API.

- Use server-side rate limiting by IP hash, session, and global daily counter.

- Add a queue and estimated status rather than allowing request storms.

- Disable live mode with a feature flag when limits or budget are reached.

- Sanitize all trace fields before public rendering.

- Keep a prerecorded two-minute video and animated hero clip available without JavaScript-dependent inference.

## 6 Failure-safe behavior and security review

- The public experience is complete without provider availability. Live mode is predefined, rate-limited, read-only, and removable by a kill switch.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

| **HARD-GATE SENSITIVITY** | This feature protects a release-blocking invariant. Deliberately removing the control must make at least one deterministic or replay test fail. |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|

## 7 Telemetry and demo proof

The website should default to the strongest stored v0-v1 comparison. The live button is supporting evidence, not the central experience. This prevents a recruiter's first click from becoming a rate-limit error.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                                      |
|----------------|--------------------------------------------------------------------------------------------|
| Browser        | First load uses snapshot; recorded/live labels unmistakable; degraded API still works.     |
| Build scan     | No provider, connector, database, token, cookie, or secret in browser bundle.              |
| Abuse          | Predefined inputs, per-session/IP/global quotas, concurrency, queue, timeout, kill switch. |
| Chaos          | Cohere/DB/API/connector degradation falls back honestly to complete snapshot.              |

### 8.1 Acceptance criteria

| **Criterion**        | **Pass condition**                                                           | **Evidence**    |
|----------------------|------------------------------------------------------------------------------|-----------------|
| First load           | Hero scenario works without a provider call.                                 | Browser test.   |
| Secret isolation     | Browser bundle contains no Cohere, Slack, Jira, or database secret.          | Build scan.     |
| Abuse resistance     | Only predefined input is accepted; rate and concurrency limits are enforced. | Security tests. |
| Honest provenance    | Snapshot and live runs are visually distinct.                                | UI review.      |
| Graceful degradation | Provider outage still leaves a complete demo.                                | Chaos test.     |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 13, Feature 14, Feature 15                                                                                                                         |
| Primary roadmap phase        | Week 1 snapshot shell; Week 5 complete public product                                                                                                      |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Daily spend stop is set from measured cost.

- Exact public concurrency and quota are adjusted after observation.

- No public Slack or Jira write credential is ever present.

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

**Next.js App Router:** Official Next.js application framework and App Router documentation. [Official source](https://nextjs.org/docs/app)

**Next.js on Vercel:** Official deployment path with Git-based and preview deployments. [Official source](https://vercel.com/docs/frameworks/full-stack/nextjs)

**Railway deployments:** Official container/service deployment documentation. [Official source](https://docs.railway.com/reference/deployments)

**Neon pgvector:** Official pgvector extension documentation for managed PostgreSQL. [Official source](https://neon.com/docs/extensions/pgvector)

**WCAG 2.2:** W3C accessibility standard referenced by the public-site acceptance criteria. [Official source](https://www.w3.org/TR/WCAG22/)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.18 of the uploaded ResolveFlow Replay Final Master Plan, pages 40-41. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
