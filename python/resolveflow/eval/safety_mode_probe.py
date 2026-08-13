"""Probe how Cohere's ``safety_mode`` behaves when ``tools`` or ``documents`` are set.

Cohere's documentation states that ``safety_mode`` defaults to ``CONTEXTUAL``
whenever the ``tools`` or ``documents`` parameters are used, and that ``OFF`` is
unavailable on newer Command models. If that is so, then any evaluation that
advertises ``STRICT`` versus ``OFF`` as an experimental variable on a tool-using
RAG agent is running a silent no-op and reporting the result as a finding.

This module does not take the documentation's word for it. It sends a small
matrix of requests -- three safety modes across four parameter shapes -- and
records, per cell, whether the API accepted the request, rejected it, and with
what error type. Acceptance and rejection are mechanical facts about the API. No
model judges anything, and no cell's result depends on reading a generation.

What this probe can and cannot establish:

* It CAN establish which (safety_mode, parameter-shape) combinations the API
  accepts and which it refuses, and what it refuses them with.
* It CANNOT establish that an accepted ``STRICT`` request was honoured as STRICT
  rather than silently coerced to CONTEXTUAL. The API does not echo the
  effective safety mode. Acceptance is not evidence of effect, and this module
  never reports it as such.

Cost: one call per matrix cell. With the default matrix that is 12 calls.

    python -m resolveflow.eval.safety_mode_probe
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from resolveflow.eval.budget import BudgetedCohereClient
from resolveflow.ingestion.fixtures import ROOT

RESULTS_DIR = ROOT / "eval" / "results"
OUTPUT = RESULTS_DIR / "safety-mode-probe-cohere.json"

SAFETY_MODES: tuple[str, ...] = ("CONTEXTUAL", "STRICT", "OFF")

# A benign, neutral prompt. The probe is about parameter acceptance, not about
# what the model says, so the prompt is deliberately uninteresting.
PROMPT = "Reply with the single word: acknowledged."

DOCUMENT = {
    "id": "probe-doc-1",
    "data": {
        "title": "Probe document",
        "snippet": "The escalation owner for issuer-routing failures is Payments Platform.",
    },
}

TOOL = {
    "type": "function",
    "function": {
        "name": "probe_lookup",
        "description": "A tool that is never actually invoked by this probe.",
        "parameters": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    },
}


def _shapes() -> dict[str, dict[str, Any]]:
    return {
        "plain": {},
        "documents": {"documents": [DOCUMENT]},
        "tools": {"tools": [TOOL]},
        "tools_and_documents": {"tools": [TOOL], "documents": [DOCUMENT]},
    }


def probe(client: BudgetedCohereClient, model: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for shape_name, shape_kwargs in _shapes().items():
        for mode in SAFETY_MODES:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": [{"role": "user", "content": PROMPT}],
                "safety_mode": mode,
                "max_tokens": 16,
                "temperature": 0.0,
                **shape_kwargs,
            }
            client.scenario_id = f"safety_mode_probe/{shape_name}"
            client.build_id = mode
            cell: dict[str, Any] = {
                "parameter_shape": shape_name,
                "safety_mode_requested": mode,
                "sent_tools": "tools" in shape_kwargs,
                "sent_documents": "documents" in shape_kwargs,
            }
            try:
                client.chat(**kwargs)
            except Exception as exc:  # noqa: BLE001 - the rejection IS the measurement
                cell["accepted"] = False
                cell["error_type"] = type(exc).__name__
                # Message text is recorded because the distinction between "this
                # model does not support OFF" and a transport failure is the
                # whole point, and it cannot be recovered from a type name.
                cell["error_message"] = str(exc)[:400]
            else:
                cell["accepted"] = True
                cell["error_type"] = None
                cell["error_message"] = None
            print(
                f"[probe] shape={cell['parameter_shape']:<20} "
                f"mode={mode:<11} accepted={cell['accepted']}"
                + (f"  ({cell['error_type']})" if not cell["accepted"] else "")
            )
            results.append(cell)
    return results


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    model = argv[0] if argv else os.environ.get(
        "RESOLVEFLOW_COHERE_COMMAND_MODEL", "command-a-plus-05-2026"
    )
    api_key = os.environ.get("RESOLVEFLOW_COHERE_API_KEY")
    if not api_key:
        raise SystemExit("RESOLVEFLOW_COHERE_API_KEY is not set; refusing to run")

    import cohere

    client = BudgetedCohereClient(cohere.ClientV2(api_key=api_key), max_calls=40)
    cells = probe(client, model)

    accepted = [cell for cell in cells if cell["accepted"]]
    rejected = [cell for cell in cells if not cell["accepted"]]
    payload = {
        "schema_version": "1.0",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "matrix": cells,
        "cells": len(cells),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "rejected_cells": [
            {
                "parameter_shape": cell["parameter_shape"],
                "safety_mode_requested": cell["safety_mode_requested"],
                "error_type": cell["error_type"],
            }
            for cell in rejected
        ],
        "ledger": client.ledger().model_dump(mode="json"),
        "interpretation_limits": [
            "Acceptance of a safety_mode value is not evidence that the value took "
            "effect. The API does not echo the effective safety mode, so a request "
            "accepted with STRICT may have been coerced to CONTEXTUAL. This probe "
            "cannot distinguish those cases and does not claim to.",
            "A rejection is a hard fact about the API surface and is reported as one.",
            "Safety modes govern generated output content. They are not an "
            "input-channel defence and this probe implies nothing about prompt "
            "injection resistance.",
        ],
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\n[probe] {len(accepted)}/{len(cells)} cells accepted; wrote {OUTPUT}")
    print(f"[probe] provider calls consumed: {client.total_calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
