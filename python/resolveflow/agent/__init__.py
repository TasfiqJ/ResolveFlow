from __future__ import annotations

from typing import TYPE_CHECKING, Any

from resolveflow.agent.fixture import FixtureChatAdapter

if TYPE_CHECKING:
    from resolveflow.agent.service import GovernedAgent as GovernedAgent

__all__ = ["FixtureChatAdapter", "GovernedAgent"]


def __getattr__(name: str) -> Any:
    """Load the service export without creating an agent/verifier import cycle."""

    if name == "GovernedAgent":
        from resolveflow.agent.service import GovernedAgent

        return GovernedAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
