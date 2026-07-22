# ADR-005: Authorize before retrieval and verify after generation

**Status:** Accepted
**Date:** 2026-07-21

## Context

A prompt telling a model not to reveal restricted evidence does not prevent forbidden chunks from entering search results, Rerank requests, model context, caches, citations, or traces. Source authorization can also change by tenant, role, region, classification, and incident time.

## Options considered

1. Prompt-only access instructions.
2. Retrieve broadly and filter only final output.
3. Build an immutable run policy snapshot, restrict the candidate universe before every retrieval stage, and recheck every final citation/claim against that snapshot.

## Decision

Choose option 3. Application code and database queries enforce tenant/role/region/classification/effective-time eligibility before lexical rank, vector distance, fusion, Rerank, model input, caches, and public projections. The verifier independently rechecks cited sources after generation.

## Consequences

- Forbidden candidate/model-input/citation counts are hard release gates.
- Retrieval cache keys include tenant and policy version; role downgrade may never widen access.
- Unauthorized public traces must not reveal restricted titles or existence.
- Query-plan, property, and stage-spy tests are required.

## Rejected alternatives

- Prompt-only authorization makes the model the security boundary.
- Output-only filtering still discloses restricted data to providers and caches and cannot prove safe retrieval.

## Reversal trigger

None for the security principle. The policy implementation may change only if the replacement demonstrably enforces eligibility before every exposure and retains post-generation defense in depth.
