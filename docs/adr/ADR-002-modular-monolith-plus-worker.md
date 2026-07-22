# ADR-002: Use a modular monolith plus one worker

**Status:** Accepted
**Date:** 2026-07-21

## Context

The system needs interactive APIs, background ingestion/evaluation/action work, transactionally consistent policy/audit state, and an architecture one engineer can run and explain. The expected portfolio load does not justify distributed service complexity.

## Options considered

1. A microservice per capability with a message broker.
2. One in-process web/API/worker runtime.
3. One Python modular monolith used by separate API and worker processes, plus one Next.js app and one database.

## Decision

Choose option 3. The API and worker import the same application/domain modules and run from the same versioned artifact with different start commands. Module boundaries are enforced in code; the worker separates background latency/failure from request handling.

## Consequences

- Critical state and audit events can share database transactions.
- Local operation and trace reconstruction stay simple.
- Worker leases/retries must be explicit because no external broker supplies them.
- Module dependency tests and ownership rules are required to prevent a monolithic tangle.

## Rejected alternatives

- Microservices, Kafka, and a service mesh add failure modes and infrastructure without measured need.
- One process couples request latency and lifecycle to replay/action workloads.

## Reversal trigger

Measured load, isolation requirements, independent deployment cadence, or team ownership demonstrates that a boundary must become a separate service. Extraction requires preserved typed contracts and production/Replay parity tests.
