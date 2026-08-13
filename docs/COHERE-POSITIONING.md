# Positioning ResolveFlow for Cohere

**This document contains no measurements.** It is strategy and sourced research,
kept deliberately separate from `eval/results/`, which contains only numbers
produced by an execution. Nothing here should be cited as a result.

Research date: 2026-08-13. Every claim below carries a source URL; where a
claim could not be sourced, it says so.

## The wedge

In June 2026 Cohere published *Creating a Security Agent with Cohere North and
Wiz* — an incident-response triage agent built on North with a custom MCP
server, emphasising strict system prompts, exact-field-value data fidelity,
server-side credentials, and humans reviewing the agent's assessment.
<https://cohere.com/blog/cohere-security-ai-agent-north-wiz>

In July 2026 Cohere shipped **North Automations**, whose pitch is governance:
human-in-the-loop approval checkpoints, per-step model selection, versioning,
sandbox testing before production, and input/output logging for complete audit
trails.
<https://cohere.com/blog/introducing-north-automations-ai-workflows>

Both make governance *claims*. Neither publishes an adversarial evaluation of
those claims. ResolveFlow is shaped exactly like the missing artifact: a
snapshot-first harness that A/Bs a governed build against an ungoverned one over
benign and attack scenarios, with per-run JSON, a provider-call ledger, checksums,
and per-stage latency.

Equally relevant: Cohere's docs have **no prompt-injection guidance page** and
**no general evaluation guide** (the only eval-flavoured page found is narrow —
<https://docs.cohere.com/v2/page/summarization-evals>). That is a documented gap
this project is unusually well positioned to fill.

**Recommended framing:** "I built the evaluation artifact your North security
agent post is missing, and here is the reproducible evidence." Not "I built a
benchmark."

## What would make a Cohere engineer skeptical

Ranked. Items 1–3 are the ones that sink credibility fastest.

1. **A two-arm A/B with a fixed attack set measures little that lasts.**
   AgentDojo's design premise is that static suites are obsolete on arrival and
   that adaptive attacks — authored *with knowledge of* the defence — are what
   matter. A guarded build scoring 0% against payloads written before the guard
   existed is close to a tautology. <https://arxiv.org/abs/2406.13352>
   *Status in this repo: acknowledged in `docs/THREAT_MODEL.md` under "Not
   tested", and published on the results page. Not yet fixed.*

2. **Benign utility must be reported as prominently as attack outcomes.** The
   cheapest route to a perfect security score is an agent that refuses
   everything. AgentDojo found SOTA models fail many tasks with no attacker
   present at all, so utility and security have to be separated.
   *Status: the harness already splits `by_build_and_kind` into benign and
   attack cells. The results page should lead with the benign delta.*

3. **Attack success needs a pre-registered, mechanical definition, and
   delivery must be verified separately.** *Status: done — `attack_delivered`
   and `attack_rerank_rank` are recorded per run, undelivered variants are
   reported as "not exercised" rather than as passes, and all oracles are
   mechanical (no model judges another model).*

4. **Sample size and significance.** SHA-256 checksums prove integrity, not
   statistical validity. n per cell, and Wilson or bootstrap intervals on every
   proportion, are what a reviewer looks for. *Status: not done — one
   repetition per cell, no intervals. Disclosed.*

5. **Safety-mode claims are the likeliest factual error in a Cohere project.**
   Per Cohere's docs, `safety_mode` **always defaults to `CONTEXTUAL` when the
   `tools` or `documents` parameters are used**, and RAG/tool-use paths on
   Command A only support `CONTEXTUAL`. Any ablation that advertises `STRICT`
   vs `OFF` on a tool-using RAG agent is silently a no-op.
   <https://docs.cohere.com/docs/safety-modes>
   *Status: this repository does not currently vary `safety_mode`. Verifying
   the coercion empirically and publishing the finding would be a genuinely
   useful contribution and proof the docs were read.*

6. **Do not conflate output safety with input-channel security.** Safety Modes
   govern what the model says. Prompt injection is about whose instructions it
   follows. Cohere does not claim the former mitigates the latter.

## Model IDs — verified current

Checked against <https://docs.cohere.com/docs/models>. All four IDs used in this
repository are Live: `command-a-plus-05-2026` (current flagship, MoE, Apache 2.0,
released 2026-05-20), `embed-v4.0`, `rerank-v4.0-fast`, `rerank-v4.0-pro`.

Retired or deprecated IDs that must not appear anywhere in code, docs or
diagrams: `command`, `command-light`, `command-r`, `command-r-plus`,
`command-r-03-2024`, `command-r-plus-04-2024` (deprecated 2025-09-15);
`c4ai-aya-expanse-8b`, `c4ai-aya-vision-8b`, `embed-english-v2.0` and other v2.0
embeds (retired 2026-04-04). No deprecation date is published for
`rerank-v3.5` — do not claim one.

## Ranked recommendations

**Tier 1 — credibility, do before showing anyone**

1. Add one **adaptive attack** per family, authored against `guarded-v1`'s
   actual defences. One that partially succeeds is worth more than twenty that
   fail, and it pre-empts the strongest objection. <https://arxiv.org/abs/2406.13352>
2. Add **repetitions and Wilson confidence intervals** to every published
   proportion. This is the cheapest remaining rigour upgrade.
3. Run the **live A/B** under the fixed token budget. Until then every
   model-dependent number in the repo is a property of a stub.
4. **Map every scenario to OWASP Top 10 for Agentic Applications 2026 IDs**
   (download the PDF; the landing page omits the enumerated list) and
   cross-reference LLM01 from the 2025 LLM Top 10. A reviewer in mid-2026 will
   notice which list was used.
   <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/>

**Tier 2 — differentiation**

5. Publish a **"governance tax" table**: added latency, added tokens, added
   provider calls for `guarded-v1` vs `unsafe-v0`. Per-stage latency is already
   collected. This aligns with Cohere's total-cost-of-ownership messaging and
   almost no open-source eval reports it.
6. **Empirically verify the `safety_mode` coercion** under `tools`/`documents`
   and publish what happens. <https://docs.cohere.com/docs/safety-modes>
7. **Surface citation groundedness as a measured defence.** Cohere's
   fine-grained citations return text spans with start/end offsets per claim;
   an uncited assertion in an IR report is a measurable hallucination event.
   This uses a Cohere-specific capability. <https://docs.cohere.com/docs/rag-citations>
8. Add a **North Automations comparison**: which of North's governance
   primitives (approval checkpoints, versioning, sandbox testing, I/O audit
   logging) ResolveFlow reimplements in the open, and which it does not.
   Positions the project as complementary, not competing.
9. Document a **private / VPC / on-prem path** — at minimum a base-URL override,
   ideally local Command A+ weights under Apache 2.0. Sovereign deployment is
   Cohere's core differentiator and a SaaS-only demo under-sells the fit.
   <https://cohere.com/deployment-options>

**Tier 3 — distribution**

10. Join the **Cohere Labs Open Science Community** and present in the "Privacy,
    Security & Policy" or "ML Agents" group's lightning talks. This is the only
    currently open, documented path to Cohere researchers that could be
    verified. <https://labscommunity.cohere.com/get-started>
11. Submit a distilled **cookbook PR** to `cohere-ai/cohere-developer-experience`
    — contributions are explicitly welcomed (Black 24.10.0; run the snippet
    checker and `make dev`). A merged cookbook is a durable, verifiable
    artifact. <https://github.com/cohere-ai/cohere-developer-experience>
12. Watch the **Cohere Labs Scholars** window (historically opens around August
    for a January start; publications not required, engineering strength
    explicitly valued). Verify dates on the page itself.
    <https://cohere.com/research/scholars-program>

## Could not be sourced — do not assume

- Any official Cohere prompt-injection guidance page.
- Any general Cohere evaluation / eval-harness doc.
- A current "Built with Cohere" showcase, ambassador programme, or
  Cohere-run 2026 hackathon submission funnel. The cookbook PR path and the
  Labs community appear to be the only documented routes.
- Whether the Build Small Hackathon is still accepting entries.
- The full enumerated OWASP Agentic Top 10 2026 list (PDF download required).
