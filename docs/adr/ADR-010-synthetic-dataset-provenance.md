# ADR-010: Label generated truth data as synthetic-agent-authored

**Status:** Accepted
**Date:** 2026-07-21

## Context

The original PDF calls for human-authored latent truths, but this build is autonomous and no human truth authors/reviewers are currently established. Calling generated data human-authored would fabricate provenance and weaken evaluation credibility.

## Options considered

1. Reuse the PDF wording and label generated truths human-authored.
2. Block all implementation until humans author the dataset.
3. Generate bounded candidate truths with explicit `synthetic_agent_authored` provenance, separate development/calibration/held-out splits, checksums, and pending human-review status.

## Decision

Choose option 3. Each truth records the authoring system, creation/version history, fixture renderer, and `human_review_status`. Human review may later add signoff or correction events but does not rewrite original authorship.

## Consequences

- Public copy discloses synthetic provenance and cannot claim customer or human-authored evidence.
- Held-out locks and evaluation mechanics can be implemented before reviewers exist.
- Strong workflow realism and human-utility claims remain unavailable until genuine reviews occur.
- Review disagreements and corrections are preserved as new evidence/version history.

## Rejected alternatives

- Mislabeling authorship is fabricated evidence.
- Waiting for humans would unnecessarily block provider-independent engineering and Replay infrastructure.

## Reversal trigger

A future dataset is genuinely authored independently by identified/consented human contributors. It receives a new dataset version and provenance; existing synthetic data is not relabeled.
