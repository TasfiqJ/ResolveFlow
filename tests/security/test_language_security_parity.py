from __future__ import annotations

import pytest
from resolveflow.config import Settings
from resolveflow.public.live import LiveRequest, PublicLiveLimiter, PublicLiveRejected


@pytest.mark.parametrize("mutation", ["baseline", "role_downgrade"])
def test_language_fixture_does_not_expand_public_inputs_or_actions(mutation: str) -> None:
    limiter = PublicLiveLimiter(enabled=True)
    with pytest.raises(PublicLiveRejected, match="input_not_allowed"):
        limiter.submit(LiveRequest("session-fr", "ip-fr", "exploratory-fr-hero-1.0", mutation))
    with pytest.raises(ValueError, match="public mode"):
        Settings(environment="public", action_dispatch_enabled=True)
