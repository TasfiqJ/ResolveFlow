"""Interval estimates for the rates this evaluation publishes.

Every headline number in this repository is a proportion over a small sample:
8 attack runs per build, 8 benign, 16 in total per build per repetition. A bare
point estimate at that sample size invites exactly one response -- "n=16" -- and
deserves it. These helpers attach an interval to every rate so a reader can see
how much the sample actually constrains the truth.

Wilson score intervals are used rather than the normal approximation because the
normal approximation is wrong in precisely the regime this evaluation lives in:
small n, and proportions at or near 0 and 1. A guarded build that blocks 16 of
16 has a Wilson 95% interval of roughly [0.806, 1.0] -- it does not have a
"100% block rate", and the interval is the honest way to say so.

Nothing here manufactures confidence. A wide interval published is worth more
than a narrow claim asserted.
"""

from __future__ import annotations

import math
from typing import Any

# Two-sided 95%.
Z_95 = 1.959963984540054


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> dict[str, Any]:
    """Wilson score interval for a binomial proportion.

    Returns the point estimate, the interval, and the inputs, so a reader never
    has to reconstruct what n was.
    """
    if trials <= 0:
        return {
            "successes": successes,
            "trials": trials,
            "point": None,
            "low": None,
            "high": None,
            "method": "wilson_score_95",
            "note": "no trials; nothing was measured",
        }
    if successes < 0 or successes > trials:
        raise ValueError(f"successes={successes} outside 0..{trials}")

    proportion = successes / trials
    denominator = 1.0 + (z**2) / trials
    centre = proportion + (z**2) / (2 * trials)
    spread = z * math.sqrt(
        (proportion * (1.0 - proportion) / trials) + (z**2) / (4 * trials * trials)
    )
    low = (centre - spread) / denominator
    high = (centre + spread) / denominator
    return {
        "successes": successes,
        "trials": trials,
        "point": round(proportion, 6),
        "low": round(max(0.0, low), 6),
        "high": round(min(1.0, high), 6),
        "method": "wilson_score_95",
    }


def newcombe_difference(
    successes_a: int, trials_a: int, successes_b: int, trials_b: int, z: float = Z_95
) -> dict[str, Any]:
    """Interval for (rate_b - rate_a) by the Newcombe hybrid-score method.

    Used for the only comparison this evaluation actually makes: guarded-v1
    against unsafe-v0. The interval is what decides whether a difference between
    two builds is a result or a coin flip. If it spans zero, the difference is
    not established at this sample size, and the artifact says so rather than
    reporting the delta as a finding.
    """
    if trials_a <= 0 or trials_b <= 0:
        return {
            "difference": None,
            "low": None,
            "high": None,
            "excludes_zero": None,
            "method": "newcombe_hybrid_score_95",
            "note": "a cell had no trials; no comparison is possible",
        }

    first = wilson_interval(successes_a, trials_a, z)
    second = wilson_interval(successes_b, trials_b, z)
    rate_a = successes_a / trials_a
    rate_b = successes_b / trials_b
    difference = rate_b - rate_a

    low = difference - math.sqrt((rate_b - second["low"]) ** 2 + (first["high"] - rate_a) ** 2)
    high = difference + math.sqrt((second["high"] - rate_b) ** 2 + (rate_a - first["low"]) ** 2)
    low = max(-1.0, low)
    high = min(1.0, high)
    return {
        "baseline": {"successes": successes_a, "trials": trials_a, "rate": round(rate_a, 6)},
        "treatment": {"successes": successes_b, "trials": trials_b, "rate": round(rate_b, 6)},
        "difference": round(difference, 6),
        "low": round(low, 6),
        "high": round(high, 6),
        # The only claim of significance this repository makes, and it is a
        # mechanical one: does the 95% interval for the difference exclude zero.
        "excludes_zero": bool(low > 0.0 or high < 0.0),
        "method": "newcombe_hybrid_score_95",
    }


def format_interval(interval: dict[str, Any] | None, as_percent: bool = True) -> str:
    """Render an interval for a markdown table."""
    if not interval or interval.get("point") is None:
        return "not measured"
    scale = 100.0 if as_percent else 1.0
    suffix = "%" if as_percent else ""
    return (
        f"{interval['point'] * scale:.1f}{suffix} "
        f"[{interval['low'] * scale:.1f}, {interval['high'] * scale:.1f}] "
        f"(n={interval['trials']})"
    )


def format_difference(difference: dict[str, Any] | None) -> str:
    if not difference or difference.get("difference") is None:
        return "not measured"
    verdict = "excludes 0" if difference["excludes_zero"] else "**spans 0**"
    return (
        f"{difference['difference'] * 100:+.1f} pp "
        f"[{difference['low'] * 100:+.1f}, {difference['high'] * 100:+.1f}] {verdict}"
    )
