from __future__ import annotations

import math
import random

from resolveflow.evaluation.models import PairedBootstrapInterval, WilsonInterval


def wilson_interval(
    numerator: int, denominator: int, z: float = 1.959963984540054
) -> WilsonInterval:
    if denominator <= 0 or numerator < 0 or numerator > denominator:
        raise ValueError("Wilson interval requires 0 <= numerator <= denominator")
    p = numerator / denominator
    z2 = z * z
    scale = 1 + z2 / denominator
    center = (p + z2 / (2 * denominator)) / scale
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * denominator)) / denominator) / scale
    lower = 0.0 if numerator == 0 else max(0.0, center - margin)
    upper = 1.0 if numerator == denominator else min(1.0, center + margin)
    return WilsonInterval(lower=lower, upper=upper)


def paired_cluster_bootstrap(
    paired_by_cluster: dict[str, tuple[float, float]], *, resamples: int = 2000, seed: int = 1701
) -> PairedBootstrapInterval:
    if not paired_by_cluster:
        raise ValueError("paired bootstrap requires at least one base-truth cluster")
    keys = tuple(sorted(paired_by_cluster))
    deltas = {key: paired_by_cluster[key][1] - paired_by_cluster[key][0] for key in keys}
    estimate = sum(deltas.values()) / len(keys)
    rng = random.Random(seed)
    samples = []
    for _ in range(resamples):
        draw = [deltas[rng.choice(keys)] for _ in keys]
        samples.append(sum(draw) / len(draw))
    samples.sort()
    lower = samples[int(0.025 * (resamples - 1))]
    upper = samples[int(0.975 * (resamples - 1))]
    return PairedBootstrapInterval(
        estimate=estimate,
        lower=lower,
        upper=upper,
        cluster_count=len(keys),
        resamples=resamples,
        seed=seed,
        caveat=(
            "Procedural siblings are clustered under base truth; small cluster counts produce "
            "coarse uncertainty and are not independent live-model trials."
        ),
    )
