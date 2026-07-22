# ADR-012: Use GitHub Pages as the zero-cost public deployment

**Status:** Accepted
**Date:** 2026-07-21

## Context

The original master plan recommends Vercel, Railway, and managed PostgreSQL. The governing prompt requires exactly zero external spend, no billing instrument, GitHub Pages as the default public deployment, and a public product that works without a backend.

## Options considered

1. Follow the PDF hosting topology and rely on provider free tiers.
2. Delay all public experience until a free dynamic backend is available.
3. Export the public snapshot product as a static Next.js site to GitHub Pages; keep API/worker/PostgreSQL local and make any other host an optional future decision.

## Decision

Choose option 3. Configure static-compatible routes, repository base path, content-addressed JSON snapshots, useful 404 behavior, and pinned GitHub Actions. The expected Pages URL is never claimed until deployment and HTTP/private-browser checks succeed.

## Consequences

- Public operation has no provider, database, Slack, or Jira credential and creates no paid infrastructure.
- Dynamic operator/live capabilities remain local/staging and are not required for portfolio availability.
- All public run pages must be pre-generated and snapshots must contain the complete sanitized trace/result.
- This ADR supersedes the PDF's Vercel/Railway/Neon ADR for v1.

## Rejected alternatives

- Free-tier assumptions can change, may require billing, and violate the verified-zero-cost rule.
- Waiting for a backend would block the strongest outage-tolerant public story.

## Reversal trigger

The user explicitly approves a different deployment after its pricing, billing-instrument requirement, security boundary, operational ownership, and fallback have been verified. GitHub Pages remains the required fallback unless a new governing instruction changes that rule.
