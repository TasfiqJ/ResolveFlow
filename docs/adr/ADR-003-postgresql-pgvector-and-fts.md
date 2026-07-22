# ADR-003: Use PostgreSQL, pgvector, and full-text search

**Status:** Accepted
**Date:** 2026-07-21

## Context

ResolveFlow needs transactional case/action state, effective-time evidence, ACL filtering before ranking, lexical and vector retrieval, durable jobs, append-only audit events, metrics, and reproducible snapshots. Splitting these across databases would make authorization and frozen-world consistency harder to inspect.

## Options considered

1. PostgreSQL for transactions plus separate vector and search services.
2. A document/vector database for most state.
3. PostgreSQL with native FTS, pgvector, relational policy data, jobs, audit, and metrics.

## Decision

Choose option 3. Use one PostgreSQL system of record. Build the eligible-ID relation before FTS/vector rank, then fuse and rerank only authorized candidates. Exact vector search is allowed for the small corpus when it improves reproducibility.

## Consequences

- Authorization, versioning, retrieval, action uniqueness, and audit can be tested transactionally.
- Integration tests require real PostgreSQL with pgvector; SQLite is not an equivalent substitute.
- Index type is deferred until corpus size is measured.
- Source binaries may remain repository files; database rows store provenance/checksums.

## Rejected alternatives

- A separate vector/search service fragments policy enforcement and snapshot consistency.
- A document database weakens relational uniqueness, approval, and job-lease constraints for this workload.

## Reversal trigger

Measured corpus scale, latency, modality requirements, or operational constraints exceed PostgreSQL while an alternative can preserve pre-retrieval authorization, immutable snapshots, and complete traces.
