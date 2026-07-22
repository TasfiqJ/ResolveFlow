# Guarded candidate misses the citation evidence floor

## Summary

The actual deterministic development comparison returned `SHIP_WITH_LIMITS` for guarded-v1. All four observed citations were verified, but the draft release gate requires at least ten citation observations before making the secondary citation-quality decision.

## Impact

The guarded candidate cannot be presented as a final release verdict. The public scorecard must display the exact 4/4 count and the insufficient-sample limitation.

## Detection

The release-gate aggregator produced the limitation from the checksummed development result bundle. The condition is reproducible with the repository evaluation command and is retained instead of being removed from the report.

## Cause

Only one development fixture was executed. Its four citations are enough to exercise the verifier path but not enough to support the preregistered reporting floor.

## Resolution

The technical preview publishes the narrow result with its denominator and refuses to relabel it as held-out, human-reviewed, or final. A future validated release requires a locked dataset and a larger genuine evaluation sample.

## Regression protection

Evaluation tests assert exact numerators and denominators, insufficient-sample handling, failure-link retention, and reproducible verdict hashes. Public-copy checks assert that the result remains labeled as a development fixture.
