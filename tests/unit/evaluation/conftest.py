from pathlib import Path

import pytest
from resolveflow.evaluation.models import ResultBundle
from resolveflow.evaluation.runner import evaluate_manifest_pair


@pytest.fixture(scope="module")
def candidate_bundle() -> ResultBundle:
    return evaluate_manifest_pair(Path("data/manifests/replay-role-downgrade-001.yaml"))
