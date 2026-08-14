from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
PUBLIC_RESULTS = ROOT / "apps" / "web" / "public" / "results"
UNSAFE_RUN = (
    RESULTS / "runs" / "fixture" / ("run-run_attack-c1-role_escalation_cross_tenant_unsafe-v0.json")
)
GUARDED_RUN = (
    RESULTS
    / "runs"
    / "fixture"
    / ("run-run_attack-c1-role_escalation_cross_tenant_guarded-v1.json")
)
STRESS = RESULTS / "structured-output-stress.json"
VOIDED_STRESS = RESULTS / "structured-output-stress-voided-token-limit.json"
CORPUS = ROOT / "data" / "corpus" / "hero-corpus-2.0.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    write_sha(path)


def write_sha(path: Path) -> None:
    path.with_suffix(path.suffix + ".sha256").write_bytes(f"{sha256(path)}  {path.name}\n".encode())


def normalize_lf(path: Path) -> None:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    path.write_bytes(text.encode("utf-8"))
    write_sha(path)


def branch_name() -> str:
    return subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_side_by_side() -> Path:
    unsafe = read_json(UNSAFE_RUN)
    guarded = read_json(GUARDED_RUN)
    assert unsafe["case"]["raw_text"] == guarded["case"]["raw_text"]
    assert unsafe["scenario_id"] == guarded["scenario_id"]
    assert unsafe["corpus_version"] == guarded["corpus_version"]

    unsafe_titles = [item["title"] for item in unsafe["retrieval"]["candidates"]]
    guarded_titles = [item["title"] for item in guarded["retrieval"]["candidates"]]
    blocked_titles = [title for title in unsafe_titles if title not in guarded_titles]
    restricted_title = "Refund processing runbook"
    assert restricted_title in unsafe_titles
    assert restricted_title not in guarded_titles

    def build_view(run: dict[str, Any], blocked: list[str]) -> dict[str, Any]:
        return {
            "build_id": run["build_id"],
            "run_id": run["run_id"],
            "retrieved_evidence": [
                {
                    "artifact_id": item["artifact_id"],
                    "title": item["title"],
                    "content_sha256": item["content_checksum"],
                }
                for item in run["retrieval"]["candidates"]
            ],
            "blocked_by_acl": blocked,
            "citations": run["response"]["citations"],
            "final_verdict": {
                "status": run["response"]["status"],
                "route": run["response"]["route"],
                "summary": run["response"]["summary"],
                "unknowns": run["response"]["unknowns"],
            },
        }

    output = RESULTS / "side-by-side-demo.json"
    write_json(
        output,
        {
            "schema": "resolveflow.side-by-side-demo",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "recorded_fixture",
            "live_mode": {
                "available": False,
                "reason": (
                    "The public site is a static GitHub Pages export with no server-side "
                    "credential boundary. Recorded-only avoids exposing the Cohere key."
                ),
            },
            "scenario_id": unsafe["scenario_id"],
            "query": unsafe["case"]["raw_text"],
            "corpus_version": unsafe["corpus_version"],
            "corpus_sha256": "sha256:" + sha256(CORPUS),
            "restricted_document": {
                "title": restricted_title,
                "unsafe_state": "admitted_to_retrieval",
                "guarded_state": "refused_before_retrieval",
            },
            "source_traces": [
                {
                    "path": UNSAFE_RUN.relative_to(ROOT).as_posix(),
                    "sha256": "sha256:" + sha256(UNSAFE_RUN),
                },
                {
                    "path": GUARDED_RUN.relative_to(ROOT).as_posix(),
                    "sha256": "sha256:" + sha256(GUARDED_RUN),
                },
            ],
            "builds": {
                "unsafe-v0": build_view(unsafe, []),
                "guarded-v1": build_view(guarded, blocked_titles),
            },
        },
    )
    return output


def build_manifest(side_by_side: Path) -> Path:
    stress = read_json(STRESS)
    voided = read_json(VOIDED_STRESS)
    artifacts = [side_by_side, STRESS, VOIDED_STRESS]
    total_calls = stress["budget"]["total_calls"] + voided["budget"]["total_calls"]
    input_tokens = stress["budget"]["input_tokens"] + voided["budget"]["input_tokens"]
    output_tokens = stress["budget"]["output_tokens"] + voided["budget"]["output_tokens"]
    application_repairs = sum(
        condition["retry_attempt_count"] for condition in voided["conditions"].values()
    ) + sum(condition["retry_attempt_count"] for condition in stress["conditions"].values())
    manifest = RESULTS / "publication-manifest.json"
    write_json(
        manifest,
        {
            "schema": "resolveflow.publication-manifest",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "branch": branch_name(),
            "environment": {
                "os": platform.platform(),
                "clock_source": "time.perf_counter monotonic clock",
                "python_version": sys.version,
                "model": stress["methodology"]["model"],
                "cohere_sdk_version": stress["methodology"]["cohere_sdk_version"],
                "corpus_path": CORPUS.relative_to(ROOT).as_posix(),
                "corpus_sha256": "sha256:" + sha256(CORPUS),
                "run_dates": [
                    voided["methodology"]["run_started_at"],
                    stress["methodology"]["run_started_at"],
                ],
            },
            "api_usage_all_task_runs": {
                "calls_by_endpoint": {"chat": total_calls},
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "transport_retries": (
                    stress["budget"]["retry_calls"] + voided["budget"]["retry_calls"]
                ),
                "application_repair_attempts": application_repairs,
                "abort_guard_fired": (
                    stress["budget"]["abort_guard_fired"] or voided["budget"]["abort_guard_fired"]
                ),
            },
            "reproduction_commands": [
                "git switch " + branch_name(),
                "powershell -ExecutionPolicy Bypass -File eval/run-structured-output-stress.ps1",
                ".venv-live\\Scripts\\python.exe eval\\build-publication-artifacts.py",
                "$env:NEXT_PUBLIC_BASE_PATH='/ResolveFlow'; pnpm --dir apps/web build",
            ],
            "artifacts": [
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": "sha256:" + sha256(path),
                }
                for path in artifacts
            ],
        },
    )
    return manifest


def write_methodology(manifest_path: Path) -> Path:
    manifest = read_json(manifest_path)
    stress = read_json(STRESS)
    voided = read_json(VOIDED_STRESS)
    lines = [
        "# ResolveFlow publication methodology",
        "",
        "## Environment and scope",
        "",
        f"- OS: `{manifest['environment']['os']}`",
        f"- Clock source: `{manifest['environment']['clock_source']}`",
        f"- Python: `{manifest['environment']['python_version']}`",
        f"- Cohere SDK: `{manifest['environment']['cohere_sdk_version']}`",
        f"- Model: `{manifest['environment']['model']}`",
        f"- Branch: `{manifest['branch']}`",
        f"- Corpus: `{manifest['environment']['corpus_path']}`",
        f"- Corpus SHA-256: `{manifest['environment']['corpus_sha256']}`",
        f"- Live run start dates: `{', '.join(manifest['environment']['run_dates'])}`",
        "- Corpus embeddings were not invoked; the side-by-side demo uses recorded fixture traces.",
        "- The public GitHub Pages export is recorded-only because it has no server-side "
        "secret boundary.",
        "",
        "## Structured-output method",
        "",
        "The retained stress artifact contains the complete synthetic requests and responses, "
        "per-call request/response SHA-256 values, token counts, durations, endpoint status, "
        "transport retry linkage, condition outcomes, and aggregates. Each condition used the "
        "same model, temperature, seed, response-format mechanism, and output allowance. The "
        "only intended changes were the schema/prompt/evidence condition named in the artifact.",
        "",
        "The deterministic application fallback permits one schema-constrained repair call. It "
        "receives only the malformed draft and scenario identifier, not the original evidence, "
        "and it cannot invent missing facts. The retained stress run produced no malformed "
        "responses, so retry-to-valid, repair latency, and repair token cost are unmeasured.",
        "",
        "## Voided run retained",
        "",
        "The first execution used an output allowance that every clean and injected response "
        "exhausted. It is void for schema-reliability claims because truncation confounds the "
        "conditions. Its raw artifact remains committed. The repair pattern did not recover those "
        "truncations because the repair call had the same insufficient allowance.",
        "",
        f"- Voided calls: `{voided['budget']['total_calls']}`",
        f"- Retained calls: `{stress['budget']['total_calls']}`",
        "",
        "## Reproduction",
        "",
        "```powershell",
        *manifest["reproduction_commands"],
        "```",
        "",
        "## Artifact SHA-256 values",
        "",
        *[f"- `{item['path']}` — `{item['sha256']}`" for item in manifest["artifacts"]],
        f"- `{manifest_path.relative_to(ROOT).as_posix()}` — `sha256:{sha256(manifest_path)}`",
        "",
        "## Non-claims",
        "",
        "These artifacts do not support production reliability, customer outcomes, cost or spend, "
        "general model reliability, statistical independence beyond the recorded prompts, "
        "performance under other models or schemas, public live-provider availability, real Slack "
        "or Jira behavior, human-review outcomes, or a release-ready verdict. The demo is one "
        "synthetic scenario. The stress results are one model, one API account, one region as seen "
        "by the client, one run date, and repeated synthetic prompts.",
    ]
    output = RESULTS / "METHODOLOGY.md"
    output.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    write_sha(output)
    return output


def publish_files(paths: list[Path]) -> None:
    PUBLIC_RESULTS.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, PUBLIC_RESULTS / path.name)
        sha_path = path.with_suffix(path.suffix + ".sha256")
        if sha_path.exists():
            shutil.copy2(sha_path, PUBLIC_RESULTS / sha_path.name)


def main() -> int:
    normalize_lf(STRESS)
    normalize_lf(VOIDED_STRESS)
    side_by_side = build_side_by_side()
    manifest = build_manifest(side_by_side)
    methodology = write_methodology(manifest)
    publish_files([side_by_side, STRESS, VOIDED_STRESS, manifest, methodology])
    print(
        json.dumps(
            {
                "side_by_side_sha256": sha256(side_by_side),
                "stress_sha256": sha256(STRESS),
                "voided_stress_sha256": sha256(VOIDED_STRESS),
                "manifest_sha256": sha256(manifest),
                "methodology_sha256": sha256(methodology),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
