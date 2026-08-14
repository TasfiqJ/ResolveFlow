# ResolveFlow publication methodology

## Environment and scope

- OS: `Windows-11-10.0.26200-SP0`
- Clock source: `time.perf_counter monotonic clock`
- Python: `3.12.13 (main, Aug  7 2026, 02:26:41) [MSC v.1944 64 bit (AMD64)]`
- Cohere SDK: `7.0.5`
- Model: `command-a-plus-05-2026`
- Branch: `codex/demo-cohere-stress`
- Corpus: `data/corpus/hero-corpus-2.0.json`
- Corpus SHA-256: `sha256:26d40cb09e0acfdca2f394284e31a5f37ebe6d471bdb060e24f808356cf12c18`
- Live run start dates: `2026-08-14T20:49:48.842766+00:00, 2026-08-14T20:53:40.383478+00:00`
- Corpus embeddings were not invoked; the side-by-side demo uses recorded fixture traces.
- The public GitHub Pages export is recorded-only because it has no server-side secret boundary.

## Structured-output method

The retained stress artifact contains the complete synthetic requests and responses, per-call request/response SHA-256 values, token counts, durations, endpoint status, transport retry linkage, condition outcomes, and aggregates. Each condition used the same model, temperature, seed, response-format mechanism, and output allowance. The only intended changes were the schema/prompt/evidence condition named in the artifact.

The deterministic application fallback permits one schema-constrained repair call. It receives only the malformed draft and scenario identifier, not the original evidence, and it cannot invent missing facts. The retained stress run produced no malformed responses, so retry-to-valid, repair latency, and repair token cost are unmeasured.

## Voided run retained

The first execution used an output allowance that every clean and injected response exhausted. It is void for schema-reliability claims because truncation confounds the conditions. Its raw artifact remains committed. The repair pattern did not recover those truncations because the repair call had the same insufficient allowance.

- Voided calls: `68`
- Retained calls: `41`

## Reproduction

```powershell
git switch codex/demo-cohere-stress
powershell -ExecutionPolicy Bypass -File eval/run-structured-output-stress.ps1
.venv-live\Scripts\python.exe eval\build-publication-artifacts.py
$env:NEXT_PUBLIC_BASE_PATH='/ResolveFlow'; pnpm --dir apps/web build
```

## Artifact SHA-256 values

- `eval/results/side-by-side-demo.json` — `sha256:99931ff6b9b1ff50f9f2121c06f2369e6c5244f34ed6fe71f9b055358c63a374`
- `eval/results/structured-output-stress.json` — `sha256:e623c3188a83373e3bb9ce1135a4ab4ac92c2ddaef5858d875bcd4f972f3e622`
- `eval/results/structured-output-stress-voided-token-limit.json` — `sha256:baa0da573257873521bc1266dfde498617a9289bf36d496cb1bc7072a4f7b185`
- `eval/results/publication-manifest.json` — `sha256:8b389d5ad76fc3ddea2866024205041c6cee30f1b0decbc716a949c6b8849094`

## Non-claims

These artifacts do not support production reliability, customer outcomes, cost or spend, general model reliability, statistical independence beyond the recorded prompts, performance under other models or schemas, public live-provider availability, real Slack or Jira behavior, human-review outcomes, or a release-ready verdict. The demo is one synthetic scenario. The stress results are one model, one API account, one region as seen by the client, one run date, and repeated synthetic prompts.
