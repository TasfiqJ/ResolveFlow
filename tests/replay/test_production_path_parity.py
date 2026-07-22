from pathlib import Path

from pytest import MonkeyPatch
from resolveflow.orchestrator import ResolveOrchestrator
from resolveflow.replay.runner import run_paired_replay


def test_replay_invokes_shared_resolve_orchestrator(monkeypatch: MonkeyPatch) -> None:
    calls: list[str] = []
    original = ResolveOrchestrator.run

    def spy(self: ResolveOrchestrator, case, configuration=None):  # type: ignore[no-untyped-def]
        calls.append(configuration.build_id)
        return original(self, case, configuration)

    monkeypatch.setattr(ResolveOrchestrator, "run", spy)
    paired = run_paired_replay(Path("data/manifests/replay-role-downgrade-001.yaml"))

    assert calls == ["unsafe-v0", "guarded-v1"]
    assert paired.baseline.evidence_graph["schema_version"] == "1.0"
    assert paired.candidate.evidence_graph["schema_version"] == "1.0"
    assert any(item.event_name == "evidence_graph.observed" for item in paired.baseline.trace)
    assert any(item.event_name == "evidence_graph.verified" for item in paired.candidate.trace)
    assert all(
        "unsafe_observe_only" in item["verifier_codes"]
        for item in paired.baseline.evidence_graph["claims"]
    )
    assert all(
        "unsafe_observe_only" not in item["verifier_codes"]
        for item in paired.candidate.evidence_graph["claims"]
    )
