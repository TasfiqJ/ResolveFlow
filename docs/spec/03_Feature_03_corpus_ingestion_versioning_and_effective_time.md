# Feature 3: corpus ingestion, versioning, and effective time

**DOCUMENT 03 / FEATURE 3**

*Standalone implementation, security, testing, and acceptance specification*

| **Capability area**    | Evidence corpus and temporal fidelity                                                                                  |
|------------------------|------------------------------------------------------------------------------------------------------------------------|
| **Master-plan source** | Section 9.3, pages 30-31.                                                                                              |
| **Primary phase**      | Week 2                                                                                                                 |
| **Core rule**          | Evidence is immutable or versioned. Historical replay uses an exact corpus snapshot rather than current mutable state. |
| **Status**             | Required for v1 unless the master plan explicitly permits the feature to be removed under its cut-order conditions.    |

| **SOURCE INTEGRITY** | This document is derived from the 87-page ResolveFlow Replay Final Master Plan. Current external product and API facts were rechecked against official sources on 15 July 2026. Design decisions and project gates remain explicitly labeled; no unmeasured result is presented as fact. |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 1 Feature at a glance

| **MASTER PLAN SOURCE** | Authoritative feature specification: ResolveFlow Replay Final Master Plan, Section 9, pages 30-31. Broader architecture, security, evaluation, and operations requirements are cross-referenced throughout this document. |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

| **Field**                | **Specification**                                                                                                                               |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose                  | Make stale and contradictory enterprise knowledge testable. A vector index without document versions cannot support credible historical replay. |
| Primary modules          | corpus, ingestion, worker, storage adapter, telemetry                                                                                           |
| Primary data/entities    | artifacts, artifact_versions, chunks, chunk_acls, embeddings, corpus_snapshots                                                                  |
| API or interface surface | Ingestion/administration commands; source resolution from trace and citation views                                                              |
| Related features         | Feature 4, Feature 5, Feature 13, Feature 14, Feature 17                                                                                        |
| Implementation phase     | Week 2                                                                                                                                          |
| Non-negotiable control   | Evidence is immutable or versioned. Historical replay uses an exact corpus snapshot rather than current mutable state.                          |

### No-guesswork rules

| **Status**               | **How it is used**                                                                                                                                                                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| VERIFIED FACT            | Current product, API, standard, or research claim checked against a primary source and dated. Recheck before implementation because external facts can change.                              |
| DESIGN DECISION          | Recommended architecture or implementation choice for this project. It is not presented as a universal fact.                                                                                |
| PROJECT GATE             | A pass/fail target selected for ResolveFlow Replay. It is not an industry standard.                                                                                                         |
| IMPLEMENTATION-TIME FACT | A value that must be discovered or measured during implementation, such as exact Jira field IDs, current patch versions, observed latency, cost, or reviewer results. It is never invented. |

## 2 Authoritative required behavior

- Ingest Markdown, text, PDF, JSON or CSV ticket exports, SQL-derived records, and one PNG dashboard screenshot.

- Preserve source title, version, owner, classification, language, timestamp, effective interval, page or row position, and checksum.

- Keep obsolete versions rather than overwriting them.

- Mark parsing quality and failed pages explicitly.

- Re-ingestion is idempotent by checksum and parser version.

- A corpus snapshot freezes the exact artifact versions and embeddings used by a run.

## 3 End-to-end feature workflow

| **DESIGN DECOMPOSITION** | The ordered workflow below is a faithful implementation decomposition of the master-plan requirement. It does not add product scope or invent results. |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|

> **1.** Load a source file or structured record as a versioned artifact.
>
> **2.** Parse deterministically, record parser/chunker versions, and preserve source positions.
>
> **3.** Assign classification, role, region, language, owner, and effective interval before chunk publication.
>
> **4.** Generate stable chunk IDs and embeddings keyed by model, dimension, preprocessing version, and checksum.
>
> **5.** Publish a checksummed corpus snapshot and fail data-quality validation on missing or orphaned state.

## 4 System contracts and boundaries

| **Contract**                   | **Required boundary**                                                                                                  |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------|
| Ownership                      | corpus, ingestion, worker, storage adapter, telemetry                                                                  |
| Persistent evidence            | artifacts, artifact_versions, chunks, chunk_acls, embeddings, corpus_snapshots                                         |
| External/public interface      | Ingestion/administration commands; source resolution from trace and citation views                                     |
| Dependencies                   | Feature 4, Feature 5, Feature 13, Feature 14, Feature 17                                                               |
| Security/reliability invariant | Evidence is immutable or versioned. Historical replay uses an exact corpus snapshot rather than current mutable state. |

### 4.1 State and audit obligations

- Record the immutable run/build/configuration identifiers needed to reproduce the feature behavior.

- Persist every material state transition and failure with a stable safe code, actor or service identity, timestamp, request/run correlation, and relevant hash.

- Keep model/provider text, connector payloads, and unrestricted trace data behind the full-trace boundary; generate a deterministic sanitized public projection.

- Never overwrite a prior terminal run or action attempt; corrections are new events or a new run/version.

## 5 Implementation blueprint

| **MASTER-PLAN IMPLEMENTATION** | The following requirements are preserved from the source feature specification. Exact patch versions, IDs, measured thresholds, costs, and results are implementation-time facts and must be recorded rather than guessed. |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- Use deterministic local parsers for the small synthetic corpus. Prefer PyMuPDF for PDF text and page boundaries; no OCR unless the source genuinely requires it.

- Store source files under versioned fixture paths or object storage keys.

- Generate chunk IDs from artifact version, page or section, and chunk ordinal.

- Create a manifest containing source checksum, parser version, chunker version, embedding policy, and expected chunk count.

- Validate that current and obsolete runbooks have non-overlapping effective intervals unless a deliberate contradiction scenario says otherwise.

- Build a data-quality command that fails on missing ACLs, invalid dates, duplicate IDs, empty chunks, or orphaned embeddings.

## 6 Failure-safe behavior and security review

- Evidence is immutable or versioned. Historical replay uses an exact corpus snapshot rather than current mutable state.

- A provider, connector, schema, policy, verification, or persistence failure must become an explicit state; it must not silently broaden access, invent evidence, mark an action complete, or hide the failed run from metrics.

- Public mode uses only synthetic data and a sanitized trace. It has no write credential and exposes no arbitrary file, URL, SQL, prompt, tool, or connector surface.

- Any hard-gate violation is retained as evidence and linked from the release verdict. It is not repaired by removing the scenario after results are visible.

## 7 Telemetry and demo proof

The trace should let a reviewer click from a citation to the exact PDF page, ticket field, SQL row, or image. The replay diff should visibly show the stale runbook being introduced or removed.

| **Telemetry dimension** | **Required record**                                                                                                                                |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Identity and version    | run_id, case_id, build_id, git SHA, model policy, prompt/tool hashes, corpus/ACL snapshot, feature flags.                                          |
| Timing and outcome      | start/end, duration, retry/attempt, normalized status, safe error code, terminal state.                                                            |
| Decision evidence       | inputs or identifiers relevant to the feature, policy/verifier result, proposal/action digest, scenario mutation, or metric numerator/denominator. |
| Public proof            | A sanitized trace panel or replay diff that demonstrates the control and the failure state without exposing secrets or restricted content.         |

## 8 Test plan

| **Test layer** | **Required coverage**                                                                        |
|----------------|----------------------------------------------------------------------------------------------|
| Unit           | Stable IDs, checksums, effective interval validation, parser/chunker versioning.             |
| Integration    | Real PostgreSQL, pgvector, full-text fields, idempotent re-ingestion.                        |
| Data quality   | Missing ACL, invalid dates, empty chunks, duplicate IDs, orphaned embeddings fail the build. |
| Replay         | T0 sees exact versions; image/source links resolve.                                          |

### 8.1 Acceptance criteria

| **Criterion**        | **Pass condition**                                               | **Failure behavior**               |
|----------------------|------------------------------------------------------------------|------------------------------------|
| Reproducibility      | Re-ingestion yields identical chunk checksums.                   | CI data build fails.               |
| Temporal correctness | Replay at T0 sees only effective versions.                       | Hard invariant failure.            |
| Provenance           | Every chunk resolves to an artifact version and source position. | Chunk is excluded.                 |
| Multimodal trace     | Image evidence retains the original image and metadata.          | Visual case is marked unavailable. |

## 9 Dependencies and sequencing

| **Dependency type**          | **Specification**                                                                                                                                          |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Upstream/downstream features | Feature 4, Feature 5, Feature 13, Feature 14, Feature 17                                                                                                   |
| Primary roadmap phase        | Week 2                                                                                                                                                     |
| Integration rule             | Build against typed interfaces and stored snapshots so the feature can be tested deterministically before live provider or connector setup is complete.    |
| Release rule                 | The feature is not complete when only the happy path works. Its failure state, telemetry, test evidence, and public or private demo proof must also exist. |

## 10 Implementation-time facts that must not be guessed

- Parser and chunker versions are pinned on implementation day.

- Chunk size is validated by retrieval ablation rather than assumed.

- OCR is omitted unless a selected source genuinely requires it.

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

**PostgreSQL versioning:** PostgreSQL 17 remains supported; PostgreSQL 18 is current. The plan targets a 17-compatible managed service and can upgrade after compatibility tests. [Official source](https://www.postgresql.org/support/versioning/)

### Source traceability

The feature purpose, required behavior, implementation requirements, acceptance criteria, and telemetry/demo proof originate from Section 9.3 of the uploaded ResolveFlow Replay Final Master Plan, pages 30-31. The broader contracts in this document are cross-checked against Sections 3-8 and 10-18 of the same plan.

| **FEATURE COMPLETE** | A feature is complete only when its behavior, failure states, telemetry, test coverage, and live or recorded demonstration are all present. |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
