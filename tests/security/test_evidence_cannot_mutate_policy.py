from __future__ import annotations

from resolveflow.agent.security import (
    SYSTEM_PROMPT,
    detect_hostile_evidence,
    lint_policy,
    require_policy_lint_clean,
)
from resolveflow.agent.service import GovernedAgent
from resolveflow.agent.tools import ToolRegistry
from resolveflow.domain.hashing import checksum

from tests.agent_helpers import governed_inputs


def test_hostile_evidence_cannot_change_tool_or_policy_hash() -> None:
    case, context, corpus, _, retrieval = governed_inputs()
    registry = ToolRegistry(case, context)
    before = checksum({"prompt": SYSTEM_PROMPT, "tools": registry.definitions})
    documents = GovernedAgent._documents(retrieval, corpus)
    events = detect_hostile_evidence(documents)
    after = checksum({"prompt": SYSTEM_PROMPT, "tools": registry.definitions})
    assert events
    assert before == after
    assert all(item.outcome == "attempted_blocked" for item in events)


def test_policy_linter_rejects_accidental_broad_authority() -> None:
    case, context, _, _, _ = governed_inputs()
    tools = list(ToolRegistry(case, context).definitions)
    broadened = tools[0].model_copy(
        update={"description": "May execute arbitrary shell commands for the model."}
    )
    assert lint_policy(SYSTEM_PROMPT, (broadened,))
    require_policy_lint_clean(SYSTEM_PROMPT, tools)
