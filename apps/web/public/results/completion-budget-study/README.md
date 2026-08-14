# ResolveFlow completion-budget study

This bundle preserves the old published live result, a zero-provider-call fixture
measurement before the budget change, the fixture rerun after the change, the
reduced-scope live confirmation, every invalid structure output, and the final
fixture validation after the render-contract correction.

The historical completion rates are retained as before-values, but their source
artifact combines trials whose observed tool-round terminals are inconsistent
with its single declared budget block. They are not a clean controlled baseline.

The new live run did not clear the completion target. No budget was raised after
that result. Persistent provider rate limits, token exhaustion, and semantic
graph-selection failures are published as the next binding constraints.

## Environment and reproduction

- Branch: `codex/fix-agent-completion`
- OS: Windows
- Duration clock: Python `time.perf_counter`
- Wall clock: Python `datetime.now().astimezone`
- Live recorded at: `2026-08-14T22:06:21.958550+00:00`
- Live generated at: `2026-08-14T21:57:05.831329+00:00`
- Python: `3.12.13 (main, Aug  7 2026, 02:26:41) [MSC v.1944 64 bit (AMD64)]`
- Command model: `command-a-plus-05-2026`
- Rerank model: `rerank-v4.0-fast`
- Cached embedding model: `embed-v4.0`
- Observed live corpus hashes: `sha256:686c0848fff6ee9206fcab40fb92b2a9ba75f846814c27dc3efadc6678b0f474, sha256:79a1868a4394313aa409ebbd727e897d7e8fb049b07d444e585b5d0382bebf9c, sha256:7c6b44ede552205996538a37a25e55372942e03d3d7d8dff4ae496940fca2999, sha256:84c3243adfa545a3542f4671fa8b5917d26221835e5135e1a0b3325e4a375812, sha256:905b20e989a9aa6fcb933ad3260725b4dbba4393db4038b82527b62a719a25e8, sha256:c1db002cdebaf0bf392900108642c78d6f6f4a8819a91b36cbed14deb10f3642, sha256:d30ea09955180c15264c936d333c77ab7da3a87e12a377dc19bb6f549fcd9a8f, sha256:f5df5a183f41dc647cc5f9657a08aa5fa372a17492d2dca8c31abf2137606aa0, sha256:f7d8a2de3737efda2b60dfc5cd44d1c0419b29bd8bb7cb9db84e10ce39f6dbd9`
- Live reproduction: `powershell -ExecutionPolicy Bypass -File eval/run-completion-live.ps1`
- Fixture before: `.venv-live\Scripts\python.exe -m resolveflow.eval.ab_cli`
  `--provider fixture --skip-dry-pass --repetitions 1`
  `--output eval\results\completion-budget-study\before-fixture`
- Fixture after: `.venv-live\Scripts\python.exe -m resolveflow.eval.ab_cli`
  `--provider fixture --skip-dry-pass --repetitions 1`
  `--output eval\results\completion-budget-study\after-fixture`
- Report: `.venv-live\Scripts\python.exe eval\build_completion_budget_report.py`

Every top-level JSON and Markdown artifact has an adjacent SHA-256 sidecar. The
live call ledger records every attempt, retry, duration, status, request hash,
response hash, and provider-reported token count. No corpus embedding call was
performed in this task.
