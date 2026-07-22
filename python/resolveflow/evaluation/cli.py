from __future__ import annotations

import argparse
from pathlib import Path

from resolveflow.evaluation.io import verify_bundle_file, write_bundle
from resolveflow.evaluation.models import ResultBundle
from resolveflow.evaluation.runner import evaluate_manifest_pair
from resolveflow.replay.io import load_manifest, manifest_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resolveflow-evaluation")
    commands = parser.add_subparsers(dest="command", required=True)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--candidate", required=True)
    evaluate.add_argument("--baseline", required=True)
    evaluate.add_argument("--dataset", required=True)
    evaluate.add_argument("--lock", required=True)
    evaluate.add_argument("--manifest", type=Path)
    evaluate.add_argument("--output", type=Path, required=True)
    report = commands.add_parser("report")
    report.add_argument("--bundle", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    negative = commands.add_parser("negative-gate")
    negative.add_argument("--manifest", type=Path)
    return parser


def _evaluate(path: Path) -> ResultBundle:
    return evaluate_manifest_pair(path)


def main() -> None:
    args = _parser().parse_args()
    if args.command == "report":
        bundle = verify_bundle_file(args.bundle)
        args.output.mkdir(parents=True, exist_ok=True)
        report = args.output / f"{bundle.bundle_id}.md"
        report.write_text(
            "\n".join(
                (
                    f"# Replay result: {bundle.bundle_id}",
                    "",
                    f"- Provenance: `{bundle.provenance}`",
                    f"- Content: `{bundle.content_label}`",
                    f"- Dataset: `{bundle.dataset_id}` (`{bundle.dataset_lock_status}`)",
                    f"- Unsafe baseline: `{bundle.baseline.verdict.verdict}`",
                    f"- Guarded candidate: `{bundle.candidate.verdict.verdict}`",
                    f"- Bundle checksum: `{bundle.checksum}`",
                    "",
                    "This deterministic development-fixture report is not held-out, live-provider, "
                    "human-reviewed, or publishable as a final release result.",
                    "",
                )
            ),
            encoding="utf-8",
        )
        print(f"Report written: {report}")
        return
    path = args.manifest or manifest_path("replay-role-downgrade-001")
    bundle = _evaluate(path)
    if args.command == "negative-gate":
        forbidden = next(
            item for item in bundle.baseline.metrics if item.metric_id == "forbidden_candidate"
        )
        if bundle.baseline.verdict.verdict != "NO_SHIP" or forbidden.numerator == 0:
            raise SystemExit("seeded unsafe baseline was not blocked")
        print("Negative gate passed: unsafe-v0 produced a retained forbidden candidate and NO_SHIP")
        return
    manifest = load_manifest(path)
    if args.candidate != "guarded-v1" or args.baseline != "unsafe-v0":
        raise SystemExit("only the pinned unsafe-v0/guarded-v1 pair is registered")
    if args.dataset != "replay-development-draft-1.0":
        raise SystemExit("held-out candidate data is DRAFT_NOT_LOCKED and cannot be evaluated")
    if args.lock != manifest.checksum:
        raise SystemExit("explicit manifest checksum does not match the selected scenario")
    paths = write_bundle(bundle, args.output)
    print(f"Result bundle: {paths[0]}")
    print(f"Result checksum: {paths[1]}")
    print(f"Candidate verdict: {bundle.candidate.verdict.verdict}")
    if bundle.candidate.verdict.verdict == "NO_SHIP":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
