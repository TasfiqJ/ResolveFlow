from __future__ import annotations

import argparse
import json
from pathlib import Path

from resolveflow.replay.io import manifest_path
from resolveflow.replay.materialize import materialize_scenario
from resolveflow.replay.runner import run_paired_replay


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resolveflow-replay")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("dry-run", "run", "smoke"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    path = args.manifest or manifest_path("replay-role-downgrade-001")
    if args.command == "dry-run":
        materialized = materialize_scenario(path)
        print(
            json.dumps(
                {
                    "mode": "dry_run_no_provider_calls",
                    "manifest_id": materialized.manifest.manifest_id,
                    "scenario_id": materialized.manifest.scenario_id,
                    "content_label": materialized.manifest.content_label,
                    "mutation": materialized.manifest.mutations[0].model_dump(mode="json"),
                    "changed_objects": [
                        item.model_dump(mode="json") for item in materialized.changed_objects
                    ],
                    "expected_gates": materialized.manifest.expectations.hard_invariants,
                    "rendered_input_hashes": materialized.rendered_input_hashes,
                    "materialization_checksum": materialized.materialization_checksum,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    paired = run_paired_replay(path)
    if args.command == "smoke":
        if paired.baseline.run_inputs["authorization_mode"] != "prompt_only":
            raise SystemExit("unsafe-v0 did not use the declared prompt-only baseline")
        if paired.candidate.run_inputs["authorization_mode"] != "enforced":
            raise SystemExit("guarded-v1 did not enforce pre-retrieval authorization")
        print(f"Replay smoke passed: {paired.scenario_id} {paired.materialization_checksum}")
        return
    print(json.dumps(paired.model_dump(mode="json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
