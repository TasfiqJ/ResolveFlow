# ResolveFlow Replay technical-preview report

**Audit date:** 2026-07-22  
**Branch:** `main`  
**Release profile:** `technical_preview`  
**Rollback target:** `724f53c9a5aee3b90da339e5717e6b5cb767bc81`

## Outcome

ResolveFlow Replay is prepared as a zero-cost, snapshot-first technical preview. The implemented product uses one shared Resolve path for interactive and Replay execution, keeps public writes disabled, publishes only synthetic recorded evidence, and identifies missing human validation instead of manufacturing it.

This is not a final deployment-readiness verdict. The validated-release profile remains closed because the repository has 0 human-authored truths, 0 practitioners, 0 reviewed cases, no locked held-out evaluation, and no fluent-language signoff.

## Implemented product

- Nine static routes covering Resolve, Replay, results, architecture, methodology, project context, blinded review tooling, and a recorded audit trace.
- Authorization before retrieval, deterministic context tools, hybrid retrieval boundaries, bounded agent execution, claim-level verification, and hostile-evidence controls.
- Exact-digest approval, disabled real Jira dispatch, idempotent synthetic execution, retry/reconciliation behavior, and append-only audit projection.
- Versioned Replay materialization, shared production-path comparison, hard-invariant-first release decisions, exact-count statistics, and retained failure links.
- Snapshot checksums, public redaction, strict browser-bundle secret scanning, recorded/live provenance, and outage-independent static behavior.

## Measured evidence

The currently published result is one deterministic development-fixture pair:

- unsafe-v0: `NO_SHIP`, with 1 forbidden candidate out of 1 scenario;
- guarded-v1: 0 forbidden candidates out of 1 scenario and 4 verified citations out of 4;
- guarded-v1 verdict: `SHIP_WITH_LIMITS` because citation N=4 is below the draft minimum N=10.

These values are not held-out, live-provider, human-reviewed, or final results.

## Verification

Release verification is pending in this report until the complete repository-controlled verifier runs on the final audit changes. Exact observed commands and outcomes will replace this paragraph before publication.

## External systems and spend

No live Cohere request, real Slack event, real Jira write, paid infrastructure purchase, or billing claim is part of the technical preview. Public mode contains no external write credential. Exact billed spend cannot be queried from the repository; no monetary result is claimed.

## Limitations and next promotion gate

The complete limitation register is in `docs/KNOWN_LIMITATIONS.md`. Promotion to `validated_release` requires genuine human-authored truths, locked gate and held-out artifacts, at least three relevant practitioners across at least ten cases, and either a fluent-human language signoff or continued removal of multilingual quality claims.

## Publication

Publication has not yet been verified. The final commit, workflow result, public URL, and post-push checks will be recorded only after they are observed.
