#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 2
  }
}

need git
need python3
need uv
need pnpm
need node
need docker

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/resolveflow-uv-cache}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
export PNPM_HOME="${PNPM_HOME:-/tmp/resolveflow-pnpm}"

if [[ "$(git branch --show-current)" != "main" ]]; then
  echo "Verification must run on main." >&2
  exit 1
fi

git diff --check
bash -n scripts/verify.sh
bash -n automation/run-resolveflow-loop.sh
[[ -x scripts/verify.sh ]] || {
  echo "scripts/verify.sh is not executable." >&2
  exit 1
}

python3 - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

root = Path.cwd()
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


required = [
    "AGENTS.md",
    "docs/CODEX_MASTER_PROMPT_ResolveFlow.md",
    "docs/IMPLEMENTATION_PLAN.md",
    "docs/ACCEPTANCE_MATRIX.md",
    "docs/CODEX_STATUS.md",
    "docs/DECISIONS.md",
    "docs/reference/ResolveFlow_Replay_Master_Plan.pdf",
    "automation/COMMON.md",
    "automation/codex-result.schema.json",
    "automation/run-resolveflow-loop.sh",
    "docs/HUMAN_SIGNOFF.example.json",
    "scripts/verify.sh",
]
for relative in required:
    require((root / relative).is_file(), f"missing required file: {relative}")

specs = sorted((root / "docs/spec").glob("[0-9][0-9]_*.md"))
require(len(specs) == 19, f"expected 19 numbered specification documents, found {len(specs)}")
for index, path in enumerate(specs):
    require(path.name.startswith(f"{index:02d}_"), f"unexpected specification order/name: {path.name}")

checksum_doc = (root / "docs/spec/SHA256SUMS.md").read_text(encoding="utf-8")
checksum_rows = re.findall(r"\| `([0-9a-f]{64})` \| `([^`]+)` \|", checksum_doc)
require(len(checksum_rows) == 23, f"expected 23 specification checksum rows, found {len(checksum_rows)}")
for expected, relative in checksum_rows:
    path = root / "docs/spec" / relative
    if not path.is_file():
        errors.append(f"checksum target missing: docs/spec/{relative}")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    require(actual == expected, f"checksum mismatch: docs/spec/{relative}")

pdf = root / "docs/reference/ResolveFlow_Replay_Master_Plan.pdf"
if pdf.is_file():
    pdf_bytes = pdf.read_bytes()
    expected_pdf_hash = "4d3b59808ff1de93a05d15a131ba3a4c11db35694c12cc97bdfecff6149febe2"
    require(hashlib.sha256(pdf_bytes).hexdigest() == expected_pdf_hash, "master-plan PDF checksum mismatch")
    require(pdf_bytes.startswith(b"%PDF-"), "master-plan reference is not a PDF")
    require(b"%%EOF" in pdf_bytes[-2048:], "master-plan PDF has no terminal EOF marker")

matrix_path = root / "docs/ACCEPTANCE_MATRIX.md"
matrix = matrix_path.read_text(encoding="utf-8") if matrix_path.is_file() else ""
matrix_rows: dict[str, list[str]] = {}
for line in matrix.splitlines():
    cells = [cell.strip() for cell in line.split("|")[1:-1]] if line.startswith("|") else []
    if cells and re.fullmatch(r"F\d{2}-AC\d{2}", cells[0]):
        require(len(cells) == 6, f"acceptance row {cells[0]} does not have six fields")
        if len(cells) == 6:
            require(cells[5] in {"PLANNED", "IN PROGRESS", "PASS", "FAIL", "BLOCKED", "NOT APPLICABLE"}, f"invalid status on {cells[0]}")
            require(bool(cells[1]), f"missing criterion text on {cells[0]}")
            require(bool(cells[3]), f"missing evidence description on {cells[0]}")
            require(bool(cells[4]), f"missing exact command or human item on {cells[0]}")
        require(cells[0] not in matrix_rows, f"duplicate acceptance-matrix ID: {cells[0]}")
        matrix_rows[cells[0]] = cells
matrix_ids = list(matrix_rows)
require(len(matrix_ids) == 78, f"expected 78 acceptance-matrix rows, found {len(matrix_ids)}")

source_total = 0
for feature in range(1, 19):
    feature_path = specs[feature] if len(specs) == 19 else None
    if feature_path is None:
        continue
    feature_text = feature_path.read_text(encoding="utf-8")
    match = re.search(r"### 8\.1 Acceptance criteria\n(.*?)\n## 9 ", feature_text, re.DOTALL)
    if not match:
        errors.append(f"acceptance table not found in {feature_path.name}")
        continue
    table_lines = [line for line in match.group(1).splitlines() if line.startswith("|")]
    source_rows = [
        line
        for line in table_lines
        if not re.match(r"^\|[-: ]+\|", line) and not line.lower().startswith("| **criterion")
    ]
    source_count = len(source_rows)
    mapped = sorted(identifier for identifier in matrix_rows if int(identifier[1:3]) == feature)
    expected_ids = [f"F{feature:02d}-AC{criterion:02d}" for criterion in range(1, source_count + 1)]
    require(mapped == expected_ids, f"feature {feature:02d} source/matrix acceptance mapping differs")
    for identifier, source_row in zip(expected_ids, source_rows):
        source_criterion = source_row.split("|")[1].strip().replace("**", "")
        mapped_criterion = matrix_rows.get(identifier, ["", ""])[1]
        require(
            mapped_criterion.lower().startswith(source_criterion.lower()),
            f"{identifier} criterion does not match source criterion {source_criterion!r}",
        )
    source_total += source_count
require(source_total == 78, f"expected 78 source acceptance criteria, found {source_total}")

plan_path = root / "docs/IMPLEMENTATION_PLAN.md"
plan = plan_path.read_text(encoding="utf-8") if plan_path.is_file() else ""
milestone_positions = [plan.find(f"### Milestone {index} -") for index in range(1, 8)]
require(all(position >= 0 for position in milestone_positions), "one or more milestone headings are missing")
require(milestone_positions == sorted(milestone_positions), "milestones are not in dependency order")
for phrase in [
    "make bootstrap",
    "make lint",
    "make typecheck",
    "make test-unit",
    "make test-integration",
    "make test-contract",
    "make test-security",
    "make test-replay",
    "make e2e",
    "make replay-smoke",
    "make evaluate-candidate",
    "make preflight",
    "Migration ownership",
    "Rollback and migration policy",
    "Verification expansion contract",
]:
    require(phrase in plan, f"implementation plan is missing required contract: {phrase}")

adr_paths = sorted((root / "docs/adr").glob("ADR-*.md"))
require(len(adr_paths) >= 12, f"expected at least 12 ADRs, found {len(adr_paths)}")
adr_sections = [
    "## Context",
    "## Options considered",
    "## Decision",
    "## Consequences",
    "## Rejected alternatives",
    "## Reversal trigger",
]
for path in adr_paths:
    text = path.read_text(encoding="utf-8")
    for section in adr_sections:
        require(section in text, f"{path.relative_to(root)} is missing {section}")

ignored_markdown_parts = {".git", ".venv", "node_modules", ".next", "out", "tmp"}
markdown_paths: list[Path] = []
for directory, child_directories, filenames in os.walk(root):
    child_directories[:] = [
        child for child in child_directories if child not in ignored_markdown_parts
    ]
    markdown_paths.extend(
        Path(directory) / filename for filename in filenames if filename.endswith(".md")
    )
link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
for path in markdown_paths:
    text = path.read_text(encoding="utf-8")
    fences = sum(1 for line in text.splitlines() if line.lstrip().startswith("```"))
    require(fences % 2 == 0, f"unbalanced fenced code block: {path.relative_to(root)}")
    for raw_target in link_pattern.findall(text):
        target = raw_target.strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        elif " \"" in target:
            target = target.split(" \"", 1)[0]
        target = unquote(target.split("#", 1)[0])
        if not target:
            continue
        linked = (path.parent / target).resolve()
        require(linked.exists(), f"broken local link in {path.relative_to(root)}: {raw_target}")

planning_paths = [
    root / "docs/IMPLEMENTATION_PLAN.md",
    root / "docs/ACCEPTANCE_MATRIX.md",
    root / "docs/CODEX_STATUS.md",
    root / "docs/DECISIONS.md",
    *adr_paths,
]
unfinished_pattern = re.compile(r"\b(?:PLACEHOLDER|TODO|TBD)\b")
for path in planning_paths:
    if path.is_file():
        require(not unfinished_pattern.search(path.read_text(encoding="utf-8")), f"unfinished marker in {path.relative_to(root)}")

for relative in ["automation/codex-result.schema.json", "docs/HUMAN_SIGNOFF.example.json"]:
    try:
        json.loads((root / relative).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON in {relative}: {exc}")

tracked = subprocess.run(
    ["git", "ls-files"], check=True, capture_output=True, text=True
).stdout.splitlines()
for relative in tracked:
    lowered = relative.lower()
    secret_file = lowered.endswith((".pem", ".p12", ".pfx", ".key"))
    environment_file = bool(re.search(r"(^|/)\.env(?:\.|$)", lowered)) and not lowered.endswith(".env.example")
    if secret_file or environment_file:
        errors.append(f"likely secret-bearing file is tracked: {relative}")

secret_pattern = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|ghp_[A-Za-z0-9]{30,}|ATATT[0-9A-Za-z_-]{20,})"
)
for relative in tracked:
    path = root / relative
    if not path.is_file() or path.stat().st_size > 1_000_000:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    require(not secret_pattern.search(text), f"secret-like token found in tracked file: {relative}")

if errors:
    print("Stage 00 verification failed:")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("Stage 00 verification passed: sources, checksums, plan, 78 acceptance mappings, ADRs, links, JSON, shell syntax, and secret hygiene.")
PY

echo "Stage 01: validating locked setup and runtime configuration"
uv lock --check
pnpm install --frozen-lockfile --offline --store-dir /tmp/resolveflow-pnpm-store
docker compose config --quiet

for required in \
  pyproject.toml uv.lock package.json pnpm-lock.yaml docker-compose.yml alembic.ini \
  python/resolveflow/api/main.py python/resolveflow/worker/main.py \
  migrations/versions/0001_foundation.py data/truths/hero-payments-001.json \
  data/published/hero-foundation.json apps/web/public/snapshots/hero-foundation.json; do
  [[ -f "$required" ]] || {
    echo "Missing Stage 01 artifact: $required" >&2
    exit 1
  }
done

for required in \
  python/resolveflow/intake/slack.py python/resolveflow/public/live.py \
  python/resolveflow/evaluation/review.py python/resolveflow/evaluation/review_cli.py \
  scripts/scan_public_build.py scripts/verify_public_snapshots.py \
  data/published/replay-development-result.json \
  apps/web/public/snapshots/replay-development-result.json \
  data/languages/exploratory-fr-1.0.json data/languages/LANGUAGE_SIGNOFF.schema.json \
  apps/web/app/replay/page.tsx apps/web/app/results/page.tsx \
  apps/web/app/architecture/page.tsx apps/web/app/methodology/page.tsx \
  apps/web/app/about/page.tsx apps/web/app/review/page.tsx \
  apps/web/app/runs/'[run_id]'/page.tsx .github/workflows/pages.yml \
  docs/customer-brief.md docs/threat-model.md docs/deployment-runbook.md \
  docs/privacy.md docs/demo-script.md; do
  [[ -f "$required" ]] || {
    echo "Missing Stage 06 artifact: $required" >&2
    exit 1
  }
done

for required in \
  python/resolveflow/actions/models.py python/resolveflow/actions/service.py \
  python/resolveflow/actions/dispatcher.py python/resolveflow/actions/connectors.py \
  python/resolveflow/actions/postgres.py python/resolveflow/worker/actions.py \
  python/resolveflow/telemetry/audit.py python/resolveflow/telemetry/projection.py \
  python/resolveflow/telemetry/export.py python/resolveflow/telemetry/diff.py \
  migrations/versions/0004_actions_reliability_audit.py \
  apps/web/app/approval-panel.tsx; do
  [[ -f "$required" ]] || {
    echo "Missing Stage 04 artifact: $required" >&2
    exit 1
  }
done

for required in \
  python/resolveflow/replay/models.py python/resolveflow/replay/io.py \
  python/resolveflow/replay/mutations.py python/resolveflow/replay/materialize.py \
  python/resolveflow/replay/runner.py python/resolveflow/evaluation/models.py \
  python/resolveflow/evaluation/statistics.py python/resolveflow/evaluation/scoring.py \
  python/resolveflow/evaluation/gate.py python/resolveflow/evaluation/runner.py \
  migrations/versions/0005_replay_release_gate.py \
  data/truths/replay-base-truths-1.0.yaml \
  data/manifests/replay-role-downgrade-001.yaml \
  data/manifests/security-scenario-candidates-1.0.yaml \
  eval/configs/replay-builds-1.0.yaml eval/configs/release-gate-1.0.yaml \
  .github/workflows/release-evaluation.yml; do
  [[ -f "$required" ]] || {
    echo "Missing Stage 05 artifact: $required" >&2
    exit 1
  }
done

for required in \
  python/resolveflow/agent/contracts.py python/resolveflow/agent/service.py \
  python/resolveflow/agent/cohere.py python/resolveflow/agent/fixture.py \
  python/resolveflow/agent/tools.py python/resolveflow/agent/security.py \
  python/resolveflow/verifier/engine.py python/resolveflow/agent/renderer.py \
  migrations/versions/0003_governed_agent_safety.py \
  data/security/prompt-injection-fixtures.json; do
  [[ -f "$required" ]] || {
    echo "Missing Stage 03 artifact: $required" >&2
    exit 1
  }
done

echo "Stage 01: Python lint, formatting, and types"
uv run ruff check python tests
uv run ruff format --check python tests
uv run mypy python/resolveflow

echo "Stage 01: web lint, formatting, and types"
pnpm --dir apps/web lint
pnpm --dir apps/web format:check
pnpm --dir apps/web typecheck

echo "Stage 01: unit and vertical-slice integration tests"
uv run pytest -q tests/unit tests/integration tests/contract tests/security tests/replay
pnpm --dir apps/web test

echo "Stage 03: governed-agent policy and fixture validation"
uv run resolveflow-policy-lint
python3 -m json.tool data/security/prompt-injection-fixtures.json >/dev/null

echo "Stage 05: Replay materialization, shared-path pairing, and release gates"
uv run resolveflow-replay dry-run --manifest data/manifests/replay-role-downgrade-001.yaml >/tmp/resolveflow-replay-dry-run.json
uv run resolveflow-replay smoke --manifest data/manifests/replay-role-downgrade-001.yaml
uv run resolveflow-evaluation negative-gate --manifest data/manifests/replay-role-downgrade-001.yaml
uv run resolveflow-evaluation evaluate \
  --candidate guarded-v1 \
  --baseline unsafe-v0 \
  --dataset replay-development-draft-1.0 \
  --lock sha256:b312f320243a4a3a3e34f664f5d55f9586f7273b1a5daf203eaf1febc3ca7f7a \
  --manifest data/manifests/replay-role-downgrade-001.yaml \
  --output /tmp/resolveflow-stage05-result.json
uv run resolveflow-evaluation report \
  --bundle /tmp/resolveflow-stage05-result.json \
  --output /tmp/resolveflow-stage05-report

echo "Stage 01: deterministic snapshot and static browser smoke"
uv run resolveflow-snapshot
pnpm --dir apps/web build
uv run python scripts/scan_public_build.py --path apps/web/out --strict
uv run python scripts/verify_public_snapshots.py
node tests/browser/snapshot-smoke.mjs
uv run resolveflow-preflight

echo "Stage 06: exact-count review tooling and multilingual claim boundary"
uv run resolveflow-review template --output /tmp/resolveflow-review-template.csv
uv run resolveflow-review analyze \
  --input /tmp/resolveflow-review-template.csv \
  --output /tmp/resolveflow-review-analysis.json
python3 -m json.tool data/languages/exploratory-fr-1.0.json >/dev/null
python3 -m json.tool data/languages/LANGUAGE_SIGNOFF.schema.json >/dev/null

echo "Stage 01: reversible PostgreSQL migration cycle"
docker compose up -d db
for attempt in $(seq 1 30); do
  db_state="$(docker inspect --format '{{.State.Health.Status}}' resolveflow-db-1 2>/dev/null || true)"
  [[ "$db_state" == "healthy" ]] && break
  sleep 1
done
[[ "$(docker inspect --format '{{.State.Health.Status}}' resolveflow-db-1)" == "healthy" ]] || {
  echo "PostgreSQL did not become healthy." >&2
  exit 1
}
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run pytest -q tests/postgres

echo "Stage 06 verification passed: prior controls plus complete static routes, snapshot integrity, bundle secret scan, bounded local-live controls, Slack contracts, review tooling, and honest language status."
