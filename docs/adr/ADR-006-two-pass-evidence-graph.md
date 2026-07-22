# ADR-006: Use a verified evidence graph and two-pass response

**Status:** Accepted
**Date:** 2026-07-21

## Context

The evidence/tool pass needs documents, citations, and narrow tools. The final product needs a stable strict schema. Current model API constraints and the security requirement for source closure make one unconstrained all-in-one response difficult to audit.

## Options considered

1. One free-form model response parsed after generation.
2. One structured model call with all documents/tools if supported later.
3. First evidence/tool pass, deterministic verification into an evidence graph, then a no-tools/no-documents structuring pass and deterministic renderer.

## Decision

Choose option 3. The second pass receives only verified facts, unknowns, conflicts, supported route candidates, permitted proposal state, and a strict schema. Local validation rejects extra fields. Structure failure produces a fixed visible `needs_review` response.

## Consequences

- Every final material claim must close over a verified graph node.
- The structuring pass cannot discover evidence, grant access, or invoke tools.
- An extra model call may add latency/usage; snapshot mode and bounded policies mitigate this.
- Graph hashing and deterministic renderer snapshot tests are required.

## Rejected alternatives

- Free-form parsing permits unsupported facts and unstable product contracts.
- A future combined API call would still need deterministic verification and source closure even if technically supported.

## Reversal trigger

The provider offers a stable combined schema/tools/documents capability and measured evidence shows a simpler design preserves strict source closure, policy separation, failure visibility, and auditability.
