# ADR-008: Bind approval to an exact digest and execute idempotently

**Status:** Accepted
**Date:** 2026-07-21

## Context

The only v1 write action is a Jira create proposal. A human must know exactly what is approved, and timeouts/crashes must not duplicate the external issue. Model intent or a UI click alone is insufficient.

## Options considered

1. Let the model call Jira after a broad user confirmation.
2. Approve an editable proposal record without a content digest.
3. Create an inert verified proposal, approve its canonical digest, independently reconstruct/validate the payload in the worker, and pair an application idempotency ledger with remote reconciliation.

## Decision

Choose option 3. Any proposal change or expiry invalidates approval. Only a worker identity may dispatch, and it cannot approve. Uncertain acknowledgement enters reconciliation using a remote marker/correlation before any create retry.

## Consequences

- Unapproved write, payload mismatch, and duplicate action are hard `NO_SHIP` events.
- Canonical serialization/hashing is a security-critical shared contract.
- Synthetic Jira implements the complete state/fault model; real Jira stays disabled absent explicit authorization.
- Concurrency, double-click, crash, timeout-before/after-send, and acknowledgement-loss tests are mandatory.

## Rejected alternatives

- Direct model writes collapse proposal, approval, and execution authority.
- Record-level approval permits post-approval mutation and cannot prove exact payload identity.

## Reversal trigger

A connector supplies a verified server-side idempotency primitive and approval object that is at least as strong. Application-side exact approval validation and audit remain required.
