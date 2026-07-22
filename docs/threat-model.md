# Public product threat model

## Release profile

The published artifact is a technical preview. Passing repository-controlled security tests does not convert it into a production security certification or a human-validated release.

## Assets and boundaries

The public build contains only synthetic, sanitized, checksummed snapshots. It contains no Cohere, Slack, Jira, database, session, or write credential. Authorization, tool scope, exact approval, idempotency, and release gates are enforced in ordinary Python and database code.

## Primary threats

- restricted evidence entering retrieval or public projection;
- hostile evidence changing policy or tool authority;
- arbitrary public prompts, files, URLs, or connector requests;
- action execution before exact approval or duplicate execution after uncertainty;
- secrets leaking into browser bundles;
- live request storms, quota exhaustion, concurrent session runs, or stuck work;
- recorded results presented as live, held-out, human-reviewed, or final.

## Controls

The system filters before ranking, verifies citations again, treats retrieved content as untrusted, accepts only fixed public scenarios, keeps live mode off by default, caps session/IP/global use, enforces one active run per session, bounds the queue and deadline, and returns the matching recorded snapshot on outage. Public Jira is always synthetic.

## Residual risk

Automated checks do not constitute a production security certification. The current public evidence has not received an independent human security review, and external live integrations have not been exercised.
