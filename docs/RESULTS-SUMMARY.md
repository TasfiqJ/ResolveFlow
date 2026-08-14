# ResolveFlow Replay live Cohere A/B: final result

## Decision

The live Command A+ and Rerank v4 A/B reached the provider, but the quality metrics are
**void**. The harness diagnostic completion rates were 1/32 for `guarded-v1` (3.125%, Wilson
95% [0.5538%, 15.7443%]) and 4/32 for `unsafe-v0` (12.5%, Wilson 95% [4.9701%,
28.0683%]). These rates describe structured-output friction under the fixed four-tool-round,
32,768-token harness budget; they are not model-quality results. Citation precision, route
accuracy, and completion rate must not be used as quality claims. [A][B]

The provider ledger records 197 Chat calls and 36 Rerank calls, 233 calls in total against the
fixed 300-call cap, with no retries. Across the five build/scenario pairs that completed, all 35
associated Chat records have nonzero input and output token counts and status `ok`; there were
no token voids where completion succeeded. [A][C]

## Valid live A/B result: authorization before retrieval

Pre-retrieval authorization eliminated forbidden-evidence retrieval in this A/B:

- `unsafe-v0`: 32/32 retrieved forbidden evidence, 100% (Wilson 95% [89.2821%, 100%]). [A]
- `guarded-v1`: 0/32 retrieved forbidden evidence, 0% (Wilson 95% [0%, 10.7179%]). [A]
- Guarded minus unguarded difference: -100 percentage points, Newcombe hybrid-score 95%
  [-100, -84.8426] percentage points. The interval excludes zero. [A]

This result is computed before model completion and is unaffected by the quality-validity void.
[A][B]

## Measured completion friction

The strict terminal-reason histograms were: [A]

- `guarded-v1` (32 runs): `complete` 1; `evidence_findings_invalid` 1;
  `provider_finish_max_tokens` 2; `structured_response_invalid` 10;
  `tool_round_budget_exhausted` 18. [A]
- `unsafe-v0` (32 runs): `complete` 4; `evidence_findings_invalid` 5;
  `provider_finish_max_tokens` 3; `structured_response_invalid` 3;
  `token_budget_exhausted` 2; `tool_round_budget_exhausted` 15. [A]

The markdown-fence-stripping change did not produce representative completion in the final
published aggregate. The honest result is that Command A+ satisfied the harness's strict
structured-output contract in only the diagnostic rates above under the fixed budget. No rerun
or target-driven tuning was performed. [A][B]

## Offline context

The deterministic signature detector fired on 2/8 original authored attacks: 25.0% recall
(Wilson 95% [7.1%, 59.1%]). Meaning-preserving synonym, zero-width, and separator variants
each measured 0/8; the homoglyph variant measured 1/8. False positives were 0/20 benign
documents (Wilson 95% [0%, 16.1%]). This supports treating signatures as observability, not as
the security boundary. [D][E]

Cohere Embed v4 separation measured AUC 0.887 (bootstrap 95% [0.6964, 1.0], 2,000
replicates). At the zero-false-positive operating point, embedding-distance recall was 62%
(Wilson 95% [31%, 86%]) versus 25% for the regex detector (Wilson 95% [7%, 59%]), with
n=8 attacks and 0/21 false positives for both. This is evidence of signal in this small authored
corpus, not a shippable novel-attack detector. [F][G]

## Evidence and SHA-256 register

- [A] `eval/results/ab-summary-cohere.json` —
  `50865f7366f2d8359e55e053cf9c0d0d3df72c990a2d7f3a86292f98fa951265`
- [B] `eval/results/ab-site-cohere.json` —
  `99d674b1dbb364f8636cd4388eb9bf833921304b77b8ee7d6d7acd50e0c78f11`
- [C] `eval/results/provider-calls-cohere.json` —
  `8a55c8d49c103849b395d5e80dc744652c7d4dde2f6b2c16ad08e9780a6fbf8d`
- [D] `eval/results/detector-eval.md` —
  `e9fb92009db52f284a7e392c62d1715774eba7d834c4483dc756f1c2060c773e`
- [E] `eval/results/detector-eval.json` —
  `68b7d67e19355112f0a9debc813cdee7b444abb6d336afa8f5a7e5854ec34044`
- [F] `eval/results/embedding-separation.md` —
  `3e5255e4a0236c6f7cd8caa457933c3927d0c47d9a6281b70d4bac2ab84532b2`
- [G] `eval/results/embedding-separation.json` —
  `bbb74b5920e04d4d8cacdf33855e958d26a4556c81e984fa683f66793e5ca01f`
- Published checksum manifest: `eval/results/SHA256SUMS-cohere.md` —
  `6a19fa5874b94106060c99c9f3834b12627cc783a4c1821ef744d589b72616bc`

`resolveflow.eval.verify_checksums cohere` verified all 103 rows in the published checksum
manifest before this summary was added. The summary does not alter any artifact listed above.
