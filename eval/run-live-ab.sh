#!/usr/bin/env bash
# Run the live Cohere A/B end to end. macOS / Linux / WSL / Git Bash.
#
#   bash eval/run-live-ab.sh
#
# Reads RESOLVEFLOW_COHERE_API_KEY from .env in the repository root. The runner
# enforces its own budget: a 2-scenario dry pass runs first, the projection is
# printed, and the full pass is refused if the projection exceeds the cap.
# Retries against a 429 count against the budget. It aborts rather than
# overspending.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo"
echo "== ResolveFlow live A/B =="
echo "repo: $repo"

python_bin="$(command -v python3 || command -v python)"
[ -n "$python_bin" ] || { echo "No Python found on PATH." >&2; exit 1; }
echo "python: $python_bin"

venv="$repo/.venv-live"
[ -x "$venv/bin/python" ] || { echo "creating $venv ..."; "$python_bin" -m venv "$venv"; }
vpy="$venv/bin/python"

echo "installing dependencies ..."
"$vpy" -m pip install --upgrade pip --quiet
"$vpy" -m pip install -e . --quiet

# Credentials are loaded into this process only. They are never written to any
# artifact, log, or commit.
[ -f "$repo/.env" ] || { echo "No .env found at $repo/.env" >&2; exit 1; }
set -a
# shellcheck disable=SC1091
. "$repo/.env"
set +a
[ -n "${RESOLVEFLOW_COHERE_API_KEY:-}" ] || { echo "RESOLVEFLOW_COHERE_API_KEY is not set in .env" >&2; exit 1; }
echo "api key: loaded (not displayed)"

export PYTHONPATH="python:."

echo
echo "== step 1/3: Embed v4 pass (cached; skipped if already complete) =="
"$vpy" -m resolveflow.eval.embed_corpus

echo
echo "== step 2/3: live A/B, 16 scenarios x 2 builds =="
echo "This sleeps to respect the per-minute limits and will take several minutes."
set +e
"$vpy" -m resolveflow.eval.ab_cli --provider cohere --max-calls 400
ab_exit=$?
set -e
case "$ab_exit" in
  4) echo; echo "ABORTED: the dry pass projected more calls than the cap allows." >&2
     echo "See eval/results/dry-pass-abort.json. No full run was performed." >&2; exit 4 ;;
  3) echo; echo "ABORTED: the call budget was exhausted mid-run." >&2; exit 3 ;;
  0) ;;
  *) echo "the A/B failed with exit code $ab_exit" >&2; exit "$ab_exit" ;;
esac

echo
echo "== step 3/3: regenerate published documents =="
"$vpy" -m resolveflow.eval.publish cohere
cp eval/results/ab-site-cohere.json apps/web/public/snapshots/

echo
echo "== done =="
echo "Artifacts written to eval/results/:"
echo "  ab-summary-cohere.json      full result, every run"
echo "  provider-calls-cohere.json  every provider call, hashed"
echo "  results-table-cohere.md     the table"
echo "  README.md                   methodology, regenerated"
echo "  SHA256SUMS-cohere.md        checksums"
echo "  runs/                       32 per-run snapshots"
