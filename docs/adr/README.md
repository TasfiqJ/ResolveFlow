# ResolveFlow Replay architecture decision records

Accepted ADRs define the v1 architecture. They are planning decisions, not implementation evidence. A later change supersedes an ADR explicitly; accepted history is not rewritten.

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](ADR-001-replay-is-the-product-center.md) | Replay is the product center and uses the Resolve production path | Accepted |
| [ADR-002](ADR-002-modular-monolith-plus-worker.md) | Modular monolith plus one worker | Accepted |
| [ADR-003](ADR-003-postgresql-pgvector-and-fts.md) | PostgreSQL, pgvector, and full-text search | Accepted |
| [ADR-004](ADR-004-direct-cohere-sdk.md) | Direct Cohere SDK behind a narrow adapter | Accepted |
| [ADR-005](ADR-005-authorization-before-retrieval.md) | Authorization before retrieval plus verification after generation | Accepted |
| [ADR-006](ADR-006-two-pass-evidence-graph.md) | Two-pass response through a verified evidence graph | Accepted |
| [ADR-007](ADR-007-postgresql-durable-queue.md) | PostgreSQL durable queue | Accepted |
| [ADR-008](ADR-008-approval-digest-and-idempotency.md) | Exact approval digest and idempotency ledger | Accepted |
| [ADR-009](ADR-009-snapshot-first-and-staging-connectors.md) | Snapshot-first public mode and disabled real connectors | Accepted |
| [ADR-010](ADR-010-synthetic-dataset-provenance.md) | Synthetic-agent-authored dataset provenance | Accepted |
| [ADR-011](ADR-011-english-first-claims.md) | English-first public claim scope | Accepted |
| [ADR-012](ADR-012-github-pages-zero-cost.md) | GitHub Pages zero-cost public deployment | Accepted |

Every ADR must include context, options, decision, consequences, rejected alternatives, and a reversal trigger.
