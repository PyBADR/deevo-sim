"""
Impact Observatory | مرصد الأثر — Source Registry

Known event sources and their trust weights.
Higher trust weight = higher confidence in downstream outputs.
"""

KNOWN_SOURCES: dict[str, dict] = {
    "scenario_catalog": {
        "label": "Built-in Scenario Catalog",
        "trust_weight": 1.0,
        "description": "17 canonical GCC scenarios with calibrated shock vectors",
    },
    "manual": {
        "label": "Manual Entry",
        "trust_weight": 0.7,
        "description": "User-defined scenario via API",
    },
    "crucix": {
        "label": "Crucix External Feed",
        "trust_weight": 0.5,
        "description": "External intelligence feed — requires validation",
    },
    "external_api": {
        "label": "External API Source",
        "trust_weight": 0.4,
        "description": "Third-party API integration — low trust by default",
    },
}


def get_source_trust_weight(source: str) -> float:
    """Return trust weight for a source. Unknown sources get 0.3."""
    entry = KNOWN_SOURCES.get(source)
    return entry["trust_weight"] if entry else 0.3


def is_known_source(source: str) -> bool:
    return source in KNOWN_SOURCES
