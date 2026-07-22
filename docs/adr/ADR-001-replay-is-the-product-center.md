# ADR-001: Replay is the product center

**Status:** Accepted
**Date:** 2026-07-21

## Context

A normal incident copilot can produce an impressive answer while still retrieving forbidden evidence, following hostile source instructions, citing stale material, or duplicating an external action. The project needs a single memorable product claim and must avoid becoming a broad support assistant.

## Options considered

1. Build an incident-resolution copilot and add an evaluation dashboard later.
2. Build a generic agent benchmark disconnected from an operational workflow.
3. Make Replay the deployment-gate product and use one incident workflow as its realistic test subject.

## Decision

Choose option 3. Resolve is one complete incident workflow. Replay freezes its inputs, applies a declared mutation, executes the same production orchestrator and controls, scores deterministic invariants before quality/operations, compares versioned builds, and emits a release verdict.

## Consequences

- The public narrative leads with the release decision, not chat capability.
- Replay cannot have a shortcut retrieval, verifier, action, or audit implementation.
- Feature breadth is cut before Replay, authorization, approval integrity, auditability, or honest evaluation.
- A plausible unsafe-v0 failure is retained as evidence; guarded-v1 must run the identical manifest.

## Rejected alternatives

- Copilot-first makes Replay a reporting add-on and weakens the differentiator.
- Benchmark-only Replay lacks deployment realism and can diverge from production behavior.

## Reversal trigger

None for v1. A future product may add workflows, but each must still use the shared Replay-controlled production path.
