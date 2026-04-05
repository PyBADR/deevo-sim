"""
Impact Observatory | مرصد الأثر — Confidence Aggregation

Computes composite pipeline confidence from per-stage confidence scores.

Formula: C = 1 / (1 + variance) × min(stage_confidences)
  - variance = var([stage_confidences])
  - Penalizes inconsistency across stages
  - Floor at 0.1 (never fake certainty)
"""

import statistics


def aggregate_confidence(stage_confidences: list[float]) -> float:
    """Compute composite confidence from per-stage scores.

    Parameters
    ----------
    stage_confidences : list[float]
        Confidence scores from each pipeline stage (0.0-1.0 each).

    Returns
    -------
    float
        Composite confidence in [0.1, 1.0].
    """
    if not stage_confidences:
        return 0.1  # No data = minimum confidence

    if len(stage_confidences) == 1:
        return max(0.1, stage_confidences[0])

    variance = statistics.variance(stage_confidences)
    min_conf = min(stage_confidences)
    mean_conf = statistics.mean(stage_confidences)

    # C = 1/(1+variance) × mean, floored by min
    composite = (1.0 / (1.0 + variance)) * mean_conf
    composite = min(composite, min_conf + 0.1)  # Don't exceed min by more than 0.1

    return round(max(0.1, min(1.0, composite)), 4)
