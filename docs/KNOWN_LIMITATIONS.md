# Known limitations

## Release status

This release is a technical preview, not a production-readiness verdict. It publishes automated evidence from deterministic synthetic fixtures and makes no claim of human validation.

## Evidence limits

- The 36 truth-catalog IDs are synthetic-agent-authored drafts, and the integrity audit shows they collapse to 1 unique semantic template. They are scaffolding, not 36 independent cases. Human-authored truth count is 0.
- Practitioner review is incomplete at 0 reviewers and 0 reviewed cases.
- Held-out candidates and final gate rules are not locked, so no held-out or final verdict is available.
- The published comparison contains one deterministic development-fixture pair. Guarded-v1 has 4 verified citations, below the draft reporting minimum of 10.
- Only the role-downgrade comparison and its baseline have public recorded snapshots. The other Replay explorer cases link to automated test evidence and are not presented as recorded or live runs.
- The security matrix now materializes and executes all 200 Cartesian cells through guarded-v1's recorded-fixture production path; the 2026-08-12 snapshot records 200 passes and 0 open cell failures. This is execution coverage, not independent attack diversity: every cell references the same `artifact_hostile_note_v1` payload despite 20 declared family/variant labels, the 10 selected truth IDs collapse into the duplicated draft truth template, and none is a live-model result. The independent attack families in `data/security/attack-families-1.0.yaml` address the payload-diversity half of this limitation; the 200-cell matrix and its duplicated truth template remain as described.
- The published paired Replay stops at an inert proposal. Unapproved-write, payload-mismatch, duplicate-action, and deployment-credential hard gates are therefore unexercised or unverified in that result and are release-blocking under gate 1.1.
- Automated checks do not constitute an independent security assessment or usability study.
- Claim support is decided by unordered token overlap between the claim text and the model's own `exact_quote`, and `span_exact` accepts any substring of the source document, including the whole document. The model therefore chooses its own evidence window and the check has no locality, ordering, or negation handling. A claim that contradicts its cited passage can still be scored `supported` when it shares enough vocabulary with a wide quote, and an action claim built that way can mint a Jira proposal. Hostile documents are still refused by the `non_hostile_support` rule, so this affects authorized, non-hostile evidence only. Entailment-grade support checking is not implemented and no claim of it is made.

## Measured A/B run (2026-08-12, fixture provider)

- The 32-run guarded/unguarded A/B in `eval/results/` did **not** call Cohere. It ran against
  `FixtureChatAdapter`, a recorded deterministic responder, with the fixture reranker and a local
  hash embedder. It measures the deterministic control layer -- pre-retrieval authorization, ACL
  and tenant enforcement, the citation verifier, the tool registry, the approval gate, and
  per-stage latency -- and measures nothing about whether a language model resists these attacks.
  Route accuracy in that table is a property of the fixture responder and is not a model result.
- Cohere was not reachable from the environment the run was performed in. No live-provider A/B
  exists. The harness and a one-command reproduction are committed; the run was not performed.
- The corpus is 20 synthetic documents across 2 tenants and 5 roles, 6 of them restricted. It is
  agent-authored and no human has reviewed it for realism or coverage.
- The attack catalog is 4 families of 2 variants, 8 independent artifacts, replacing the single
  reused `artifact_hostile_note_v1` payload. All 8 were confirmed delivered to the model in the
  recorded run. Each variant is a single scenario against a single query: one trial is not a
  resistance rate, and no confidence interval is claimed.
- **Open: the hostile-evidence detector is silent on 6 of the 8 attack mechanisms.** Only variants
  `a1` and `d1` produced a security event. Variants `a2`, `b1`, `b2`, `c1`, `c2`, and `d2` were
  delivered and produced none. Those six were contained by authorization and verification rather
  than by detection, which means an operator watching security events would not have seen them.
  The `ATTACK_PATTERNS` regex set has no signature for authority-precedence forgery, covert
  channels in citation metadata, in-band role assertion, false cross-tenant scope rules, or
  parameter smuggling on a permitted tool.
- An earlier execution found the two tool-smuggling variants were never retrieved into the
  candidate set, so they were not actually tested. They were rewritten with topical anchoring and
  re-run. Delivery is now recorded per run so an undelivered attack can never be counted as a pass.
- Latency was measured in a single pass on one machine. No percentile in `eval/results/` is a
  service level objective and none should be quoted as one.

## Integration limits

- No live Cohere run, provider latency, usage, quality, or cost result is claimed.
- The optional public-live admission endpoint fails closed with
  `public_live_executor_unavailable`; limiter controls exist, but no ticket is accepted until a
  bounded persistent executor is implemented.
- Slack handling is verified with signed synthetic contracts; no real workspace result is claimed.
- Jira dispatch is disabled outside the synthetic connector; no real Jira write result is claimed.
- Fixture API action, Replay, and Slack state is process-local memory. Durable PostgreSQL action repositories and worker behavior are separately implemented and tested, but they are not the current API runtime composition.
- Public mode is static, snapshot-first, English-only, and has no runtime backend or external write credential.

## Scope limits

- One fictional payments workflow and one inert Jira proposal are included.
- Image evidence remains outside the evaluated core.
- The exploratory French fixture is excluded from quality claims because no fluent-human signoff exists.

## Tooling note

- The passing Python suite currently reports one Starlette TestClient deprecation warning while the ecosystem transitions from `httpx` to `httpx2`. No test is skipped or muted.
- Production JavaScript dependencies pass a high-severity audit. The ESLint 9 development toolchain still contains one high-severity transitive `brace-expansion` advisory through `eslint-plugin-import`/`minimatch` 3; forcing the patched major globally breaks that plugin stack, and ESLint 10 is not yet supported by the installed React/import accessibility plugins. The verifier therefore fails on high production findings and critical development findings while this explicit development-only exception remains open.
