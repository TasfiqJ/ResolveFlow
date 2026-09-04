# ResolveFlow Replay live Cohere A/B: final result

## Decision

The retained live Command A+ and Rerank v4 cohort reached the provider, but its model-quality
metrics are **VOID**. The cohort contains one coherent 32-run repetition: 16 runs per build over
the same 16 authored synthetic scenarios. Diagnostic completion was 1/16 for `guarded-v1`
(6.25%, Wilson 95% [1.1119%, 28.3287%]) and 3/16 for `unsafe-v0` (18.75%, Wilson 95%
[6.5916%, 43.0089%]). These rates describe strict structured-output friction under the recorded
four-tool-round harness and 32,768-token observed-usage stop threshold; that threshold is checked
after provider-reported usage and is not a hard billing ceiling. Citation precision, route
accuracy, and completion rate must not be used as model-quality claims. [A][B]

The reconciled provider ledger contains 197 Chat calls and 36 Rerank calls, 233 calls in total
against the historical 300-call cap, with no retries. The selected full pass accounts for 206
calls (174 Chat traces bound by response-ID fingerprint plus 32 Rerank calls). The required
four-run dry pass accounts for the other 27 calls (23 Chat and 4 Rerank). The A/B reused an
on-disk Embed v4 cache from a separate earlier pass, so no Embed call appears in this ledger.
The historical ledger predates Rerank search-unit capture, and the legacy Embed receipt predates
non-Chat billed-token capture. Those usage values are unavailable, not measured zeroes. [A][C]

## Cohort and provenance boundary

The original execution material contained snapshots from different invocation timestamps.
Offline recovery selected the only complete 32-cell cohort sharing one timestamp and common
execution identity, recomputed every snapshot hash and metric, and excluded 63 snapshots from
other timestamps instead of combining them into a misleading aggregate. Recovery spent zero
provider calls. [A]

The selected snapshots record their execution git state as `uncommitted`; the exact dirty diff
was not retained. The static publication records
`b97e874761ace754d8a641ec420cd00b5971e3e1` separately as its publication base commit and does
not present that value as the execution commit. [A][B]

## Valid live A/B result: authorization before retrieval

Pre-retrieval authorization eliminated forbidden-evidence retrieval in this authored cohort:

- `unsafe-v0`: 16/16 retrieved forbidden evidence, 100% (Wilson 95% [80.6392%, 100%]). [A]
- `guarded-v1`: 0/16 retrieved forbidden evidence, 0% (Wilson 95% [0%, 19.3608%]). [A]
- Guarded minus unsafe: -100 percentage points, Newcombe hybrid-score 95%
  [-100, -72.6197] percentage points. [A]

This result is computed before model completion and is unaffected by the quality-validity void.
The intervals are descriptive over repeated executions of authored scenarios; they are not
independent-sample inferential evidence or a claim of general prompt-injection robustness. [A][B]

## Measured completion friction

The strict terminal-reason histograms were: [A]

- `guarded-v1` (16 runs): `complete` 1; `evidence_findings_invalid` 1;
  `provider_finish_max_tokens` 2; `structured_response_invalid` 10;
  `tool_round_budget_exhausted` 2.
- `unsafe-v0` (16 runs): `complete` 3; `evidence_findings_invalid` 5;
  `provider_finish_max_tokens` 3; `structured_response_invalid` 2;
  `token_budget_exhausted` 2; `tool_round_budget_exhausted` 1.

The defensible conclusion is that the strict graph-bound output contract produced too few
completed runs for a representative quality result. The offline recovery did not call the
provider, alter snapshots, or tune toward a preferred outcome. [A][B]

## Offline context

The deterministic signature detector fired on 2/8 original authored attacks: 25.0% recall
(Wilson 95% [7.1%, 59.1%]). Meaning-preserving synonym, zero-width, and separator variants each
measured 0/8; the homoglyph variant measured 1/8. False positives were 0/20 benign documents
(Wilson 95% [0%, 16.1%]). This supports treating signatures as observability, not as the security
boundary. [D][E]

Cohere Embed v4 separation measured AUC 0.887 (bootstrap 95% [0.6964, 1.0], 2,000 replicates).
At the zero-false-positive operating point, embedding-distance recall was 62% (Wilson 95%
[31%, 86%]) versus 25% for the regex detector (Wilson 95% [7%, 59%]), with n=8 attacks and 0/21
false positives for both. This is evidence of signal in this small authored corpus, not a
shippable novel-attack detector. [F][G]

## Evidence and SHA-256 register

- [A] `eval/results/ab-summary-cohere.json` —
  `7eff4ea78d064bf6391141f9a98ee4ed2e982f1451352d6cbb57d52bf7c6a1a9`
- [B] `eval/results/ab-site-cohere.json` —
  `5686a7d44cd0dc5eb458426315d82994512ae8be57a1d258a116e7bf4fbbc70b`
- [C] `eval/results/provider-calls-cohere.json` —
  `c7bb06d9a0cc8a0671318ace44d8022b2ff93d538058375cec1641bd319e72e5`
- [D] `eval/results/detector-eval.md` —
  `e9fb92009db52f284a7e392c62d1715774eba7d834c4483dc756f1c2060c773e`
- [E] `eval/results/detector-eval.json` —
  `68b7d67e19355112f0a9debc813cdee7b444abb6d336afa8f5a7e5854ec34044`
- [F] `eval/results/embedding-separation.md` —
  `3e5255e4a0236c6f7cd8caa457933c3927d0c47d9a6281b70d4bac2ab84532b2`
- [G] `eval/results/embedding-separation.json` —
  `bbb74b5920e04d4d8cacdf33855e958d26a4556c81e984fa683f66793e5ca01f`
- Published checksum manifest: `eval/results/SHA256SUMS-cohere.md` —
  `4798b8f8be8be9e77cd5db35140d48ccf24069aa70ad7479f540560cfccdf069`

`resolveflow.eval.verify_checksums cohere` verified all 103 rows in the published checksum
manifest before this summary was added. The summary does not alter any artifact listed above.
