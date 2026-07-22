# ADR-004: Use the direct Cohere SDK behind a narrow adapter

**Status:** Accepted
**Date:** 2026-07-21

## Context

The project must expose exact model IDs, document payloads, tool calls, citations, usage, errors, retries, and current API constraints. General agent frameworks can add hidden transformations and retry behavior that weaken the audit story.

## Options considered

1. LangChain, LlamaIndex, or another agent framework.
2. Direct HTTP calls throughout application modules.
3. Official Cohere SDK isolated behind typed adapter ports and fixture implementations.

## Decision

Choose option 3. Application modules depend on provider-neutral ports sized only to ResolveFlow's operations. The Cohere adapter uses the current official SDK/V2 APIs after implementation-time verification; fixture/recorded adapters are the default in tests and snapshots.

## Consequences

- Provider behavior and telemetry remain visible and testable.
- API drift is localized to contract tests and the adapter.
- This is not multi-provider portability; the port exists for safety/testing, not a generic model abstraction.
- Live use remains disabled by default and bounded by verified zero-charge limits.

## Rejected alternatives

- Agent frameworks obscure the exact boundaries the portfolio must demonstrate.
- Scattered direct HTTP calls duplicate auth/error/telemetry logic and complicate contract updates.

## Reversal trigger

A later, measured need for multiple providers or a framework produces less complexity while retaining complete native request/response visibility, deterministic fixture support, and all safety boundaries.
