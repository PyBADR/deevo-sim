"""
Impact Observatory | مرصد الأثر — Warning Collection

Collects and deduplicates warnings from all pipeline stages.
Computes quality impact score from accumulated warnings.
"""


def collect_warnings(*warning_lists: list[str]) -> list[str]:
    """Merge and deduplicate warnings from multiple stages.

    Parameters
    ----------
    *warning_lists : list[str]
        Warning lists from each stage.

    Returns
    -------
    list[str]
        Deduplicated, ordered warning list.
    """
    seen: set[str] = set()
    result: list[str] = []
    for wl in warning_lists:
        for w in wl:
            if w not in seen:
                seen.add(w)
                result.append(w)
    return result


def quality_impact_score(warnings: list[str]) -> float:
    """Estimate how much warnings degrade output quality.

    Returns a penalty in [0.0, 0.5] — subtracted from confidence.
    Each warning contributes 0.03 penalty, capped at 0.5.
    """
    return min(0.5, len(warnings) * 0.03)
