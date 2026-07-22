# ADR-007: Use a PostgreSQL durable queue

**Status:** Accepted
**Date:** 2026-07-21

## Context

Ingestion, Replay, evaluation, snapshot generation, and connector actions need durable background execution, leases, cancellation, retry, dead letter, and transaction access to action/audit state. The expected throughput is small.

## Options considered

1. Redis/Celery.
2. Kafka or a hosted queue.
3. PostgreSQL jobs table with `FOR UPDATE SKIP LOCKED`, leases, bounded retries, and advisory locks for singleton work.

## Decision

Choose option 3. Jobs are versioned domain records in the system-of-record database. Workers claim transactionally, renew long leases, observe cancellation, and make terminal/failure state visible.

## Consequences

- No additional paid or operational dependency is required.
- Concurrency, lease expiry/reclaim, transaction rollback, fairness, and dead-letter behavior need real-database tests.
- Queue load must remain bounded; interactive request work stays out of the worker.
- Action dispatch also locks/checks its action and idempotency rows.

## Rejected alternatives

- Redis/Celery duplicates durability and introduces another state system at this scale.
- Kafka/hosted queues are disproportionate and weaken single-transaction action/audit reasoning.

## Reversal trigger

Measured queue throughput, isolation, scheduling, or operational requirements exceed PostgreSQL and a replacement preserves durable semantics, exact-once business controls, Replay reproducibility, and zero-cost constraints.
