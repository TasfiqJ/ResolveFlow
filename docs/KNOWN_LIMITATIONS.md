# Known limitations

## Release status

This release is a technical preview, not a production-readiness verdict. It publishes automated evidence from deterministic synthetic fixtures and makes no claim of human validation.

## Evidence limits

- The 36 truth-catalog IDs are synthetic-agent-authored drafts, and the integrity audit shows they collapse to 1 unique semantic template. They are scaffolding, not 36 independent cases. Human-authored truth count is 0.
- Practitioner review is incomplete at 0 reviewers and 0 reviewed cases.
- Held-out candidates and final gate rules are not locked, so no held-out or final verdict is available.
- The published comparison contains one deterministic development-fixture pair. Guarded-v1 has 4 verified citations, below the draft reporting minimum of 10.
- Among the Replay explorer cases, only the role-downgrade comparison and its baseline have public recorded snapshots. The other Replay explorer cases link to automated test evidence and are not presented as recorded or live runs.
- The security matrix now materializes and executes all 200 Cartesian cells through guarded-v1's recorded-fixture production path; the 2026-08-12 snapshot records 200 passes and 0 open cell failures. This is execution coverage, not independent attack diversity: every cell references the same `artifact_hostile_note_v1` payload despite 20 declared family/variant labels, the 10 selected truth IDs collapse into the duplicated draft truth template, and none is a live-model result. The independent attack families in `data/security/attack-families-1.0.yaml` address the payload-diversity half of this limitation; the 200-cell matrix and its duplicated truth template remain as described.
- The published paired Replay stops at an inert proposal. Unapproved-write, payload-mismatch, duplicate-action, and deployment-credential hard gates are therefore unexercised or unverified in that result and are release-blocking under gate 1.1.
- Automated checks do not constitute an independent security assessment or usability study.
- Claim support still uses deterministic token overlap rather than semantic entailment. The cited
  quote must occur exactly in the authorized source (and, for tool evidence, inside the explicitly
  allowlisted canonical data projection), but the model still chooses that quote and the overlap
  check has limited ordering and negation awareness. Hostile evidence cannot independently support
  a claim, tool evidence is fact-only, and only verified `ACTION` claims can support an inert
  proposal; these controls reduce impact but do not turn the verifier into an entailment model.

## Recorded-fixture A/B context (2026-08-12)

- The 32-run guarded/unguarded A/B in `eval/results/` did **not** call Cohere. It ran against
  `FixtureChatAdapter`, a recorded deterministic responder, with the fixture reranker and a local
  hash embedder. It measures the deterministic control layer -- pre-retrieval authorization, ACL
  and tenant enforcement, the citation verifier, the tool registry, the approval gate, and
  per-stage latency -- and measures nothing about whether a language model resists these attacks.
  Route accuracy in that table is a property of the fixture responder and is not a model result.
- Cohere was not reachable from the environment used for that fixture run. That statement is
  historical context for the recorded-fixture artifact, not the current repository status; a
  separate live Cohere A/B was subsequently completed and is bounded below.
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

## Live Cohere evidence (2026-08-14)

- The published live A/B contains one coherent 32-run repetition, 16 runs for each build across
  16 synthetic scenarios. Offline recovery selected snapshots sharing one execution timestamp
  and excluded 63 snapshots from earlier invocations rather than combining a mixed cohort. The
  recovery spent zero provider calls. The execution git state was `uncommitted`, and its exact
  dirty diff was not retained; the separately recorded publication base is not presented as the
  execution commit.
- The reconciled provider ledger records 197 Chat calls and 36 Rerank calls (233 total, with no
  retries): 206 calls belong to the selected full pass and 27 to its required four-run dry pass.
  It reused the on-disk Embed v4 cache produced by a separate earlier single pass; the 233-call
  ledger does not include a new Embed call.
- Completion was 1/16 for guarded-v1 and 3/16 for unsafe-v0. Citation precision, route accuracy,
  and completion rate are therefore **VOID** as quality metrics. The run does not establish
  Command A+ quality or general prompt-injection robustness.
- One result remains valid because it is computed before model completion: unsafe-v0 retrieved
  forbidden evidence in 16/16 runs (Wilson 95% [80.6392%, 100%]), while guarded-v1 retrieved it
  in 0/16 (Wilson 95% [0%, 19.3608%]). The guarded-minus-unsafe difference is -100 percentage
  points, Newcombe hybrid-score 95% [-100, -72.6197], which excludes zero. These are descriptive
  intervals over this authored execution cohort, not independent-sample inferential evidence.
- A later completion-budget follow-up deliberately reduced the live set to 11 scenarios. It
  consumed 161 attempts, including 27 retries, and did not improve guarded completion (0/11).
  Provider rate limits and schema-valid but unsupported graph references became binding. The
  follow-up is diagnostic evidence, not a replacement A/B or a quality result.
- No live execution performed an external Slack or Jira write. Neither artifact measures monetary
  cost, human judgment, held-out performance, production behavior, or final release readiness.

## Integration limits

- The live Cohere artifacts report run-specific calls, tokens, and timing for reproducibility, but
  make no model-quality, service-level, monetary-cost, or production-performance claim.
- Provider-call, agent-round, and tool-call limits are hard pre-dispatch caps. `max_total_tokens`
  is not: preflight sizing may reject a call, and observed usage is checked after a response before
  another call starts, but one in-flight response can cross the threshold. It is therefore a soft
  stop for subsequent work, not a hard token or billing ceiling.
- The remaining wall-clock allowance is passed to deadline-aware provider, retrieval, and tool
  operations, and elapsed time is checked again after each operation returns. This is cooperative,
  per-operation timeout handling, not forcible cancellation or a guaranteed hard total deadline.
  A remote request may continue after client timeout, so its attempt remains counted.
- Current accounting uses either a complete Chat token pair or a complete billed-token pair and
  never mixes those units; Embed input tokens and Rerank search units are recorded when Cohere
  returns them. The retained live A/B ledger predates the search-unit field and is preserved rather
  than backfilled, so its 36 Rerank calls do not establish billable search-unit usage or cost.
- The local action API has no built-in caller authentication. It accepts actor IDs and permission
  scopes from caller-supplied request data, so its exact proposal-state and payload-digest checks
  require a trusted upstream identity and authorization layer before they form an end-to-end human
  approval boundary. The static public site exposes no action endpoint.
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

- The passing Python suite currently reports two dependency deprecation warnings: Starlette's
  TestClient is transitioning from `httpx` to `httpx2`, and Starlette still references the
  deprecated `anyio.abc.BlockingPortal` alias. No test is skipped or muted.
- Production JavaScript dependencies pass a high-severity audit. The ESLint 9 development toolchain still contains one high-severity transitive `brace-expansion` advisory through `eslint-plugin-import`/`minimatch` 3; forcing the patched major globally breaks that plugin stack, and ESLint 10 is not yet supported by the installed React/import accessibility plugins. The verifier therefore fails on high production findings and critical development findings while this explicit development-only exception remains open.
