from __future__ import annotations

import json

from resolveflow.ingestion.fixtures import MANIFEST


def test_optional_image_condition_is_explicitly_unavailable() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["image_evidence"] == {
        "status": "unavailable",
        "reason": "optional_visual_not_shipped",
    }
