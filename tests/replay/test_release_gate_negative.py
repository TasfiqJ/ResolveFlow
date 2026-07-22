from pathlib import Path

from resolveflow.domain.hashing import checksum
from resolveflow.evaluation.gate import evaluate_release_gate
from resolveflow.evaluation.io import load_gate
from resolveflow.evaluation.runner import evaluate_manifest_pair


def test_forbidden_citation_blocks_release() -> None:
    bundle = evaluate_manifest_pair(Path("data/manifests/replay-role-downgrade-001.yaml"))
    metrics = list(bundle.candidate.metrics)
    index = next(i for i, item in enumerate(metrics) if item.metric_id == "forbidden_citation")
    seeded_body = metrics[index].model_dump(mode="python", exclude={"checksum"})
    seeded_body.update(
        {
            "numerator": 1,
            "value": 1.0,
            "failing_replay_links": ("replay://seeded/forbidden-citation",),
        }
    )
    metrics[index] = metrics[index].__class__(**seeded_body, checksum=checksum(seeded_body))

    verdict = evaluate_release_gate(
        gate=load_gate(),
        metrics=tuple(metrics),
        candidate_build="guarded-v1-seeded-negative",
        baseline_build="unsafe-v0",
        dataset_id="replay-development-draft-1.0",
    )

    assert verdict.verdict == "NO_SHIP"
    assert "forbidden_citation_failed" in verdict.reason_codes
    assert verdict.failing_replay_links == ("replay://seeded/forbidden-citation",)
