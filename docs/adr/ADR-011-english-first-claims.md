# ADR-011: Keep public quality claims English-first

**Status:** Accepted
**Date:** 2026-07-21

## Context

Cohere supports multilingual workloads, and the original hero sometimes uses French. No fluent reviewer has been established. Machine translation or model self-review cannot support an operational multilingual quality claim.

## Options considered

1. Claim multilingual performance from provider capability and translated fixtures.
2. Remove all non-English schema/test readiness.
3. Use English for the canonical public hero and claims; allow an exploratory unvalidated fixture, then add one narrowly named validated language slice only after fluent human signoff.

## Decision

Choose option 3. Authorization, action, and other deterministic invariants are language-independent and may be tested across fixtures. Quality/utility claims remain English-only until the review evidence in the acceptance matrix exists.

## Consequences

- No broad `multilingual` quality wording appears in README/results.
- A later slice reports each query/evidence language configuration separately with exact N.
- Stable IDs, codes, names, and structured facts remain paired across variants.
- Lack of a reviewer removes the claim, not the core release path.

## Rejected alternatives

- Translation-only evidence is theater and risks cultural/terminology artifacts.
- Removing schema readiness makes a later honest slice needlessly expensive.

## Reversal trigger

A fluent reviewer signs the query, terminology, gold meaning, and output-review method for one declared slice. The ADR is superseded only for that named language/version and does not authorize generalization.
