"""Replay scoring, uncertainty, and release decisions."""

from resolveflow.evaluation.gate import evaluate_release_gate
from resolveflow.evaluation.runner import evaluate_manifest_pair

__all__ = ["evaluate_manifest_pair", "evaluate_release_gate"]
