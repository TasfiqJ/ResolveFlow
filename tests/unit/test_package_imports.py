from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_verifier_and_agent_public_exports_import_in_a_fresh_interpreter() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from resolveflow.verifier.models import EvidenceGraph; "
                "from resolveflow.verifier import EvidenceVerifier; "
                "from resolveflow.agent import GovernedAgent; "
                "assert EvidenceGraph.__name__ == 'EvidenceGraph'; "
                "assert EvidenceVerifier.__name__ == 'EvidenceVerifier'; "
                "assert GovernedAgent.__name__ == 'GovernedAgent'"
            ),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
