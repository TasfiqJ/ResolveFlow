from __future__ import annotations

from resolveflow.agent.fixture import FixtureChatAdapter
from resolveflow.agent.service import GovernedAgent
from resolveflow.context.fixture import FixtureContextRepository
from resolveflow.intake.web import canonical_hero_case
from resolveflow.orchestrator import ResolveOrchestrator
from resolveflow.telemetry.audit import make_audit_record, verify_audit_chain
from resolveflow.telemetry.diff import diff_runs
from resolveflow.telemetry.export import (
    export_is_reproducible,
    export_run_json,
    export_run_markdown,
)
from resolveflow.telemetry.reconstruct import reconstruct_from_events

from tests.action_helpers import NOW


def test_audit_chain_order_and_hashes_are_verified() -> None:
    first = make_audit_record(
        run_id="run_1",
        sequence=1,
        occurred_at=NOW,
        actor_id="resolveflow-service",
        actor_type="service",
        component="actions",
        event_name="proposal.created",
        outcome="ok",
        safe_detail={"digest": "sha256:safe"},
    )
    second = make_audit_record(
        run_id="run_1",
        sequence=2,
        occurred_at=NOW,
        actor_id="human_1",
        actor_type="human",
        component="actions",
        event_name="approval.granted",
        outcome="ok",
        safe_detail={"permission": "approve_jira"},
        previous_event_hash=first.event_hash,
    )
    assert verify_audit_chain((first, second))
    assert not verify_audit_chain((second, first))


def test_public_json_markdown_exports_and_run_diff_are_reproducible() -> None:
    before = {
        "run_id": "run_before",
        "build_id": "guarded-v1",
        "identity_snapshot": {"active_role": "incident_commander", "region": "ca-central"},
        "corpus_version": "corpus-1",
        "model_policy": "policy-1",
        "retrieval": {"candidates": ["allowed"]},
        "response": {"claim_ids": ["claim-1"]},
        "action": {"state": "pending_approval", "payload_digest": "sha256:a"},
        "authorization": "Bearer do-not-export-123456",
        "trace": [],
    }
    after = {
        **before,
        "run_id": "run_after",
        "identity_snapshot": {"active_role": "contractor", "region": "ca-central"},
    }
    diff = diff_runs(before, after)
    assert [entry.path for entry in diff.entries] == ["identity_snapshot.active_role"]
    exported = export_run_json(before, public=True)
    assert "do-not-export" not in exported
    assert "export_checksum" in exported
    assert "## Timeline" in export_run_markdown(before, public=True)
    assert export_is_reproducible(before, public=True)


def test_route_and_action_are_reconstructable_from_events_alone() -> None:
    snapshot = ResolveOrchestrator(
        FixtureContextRepository(), GovernedAgent(FixtureChatAdapter())
    ).run(canonical_hero_case())
    reconstructed = reconstruct_from_events(snapshot.trace)
    assert reconstructed.complete
    assert reconstructed.route == "Payments Platform"
    assert reconstructed.action_state == "pending_approval"
    assert reconstructed.payload_digest == snapshot.action.payload_digest
