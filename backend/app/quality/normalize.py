"""
Impact Observatory | مرصد الأثر — Event Normalization (Stage 3)

Maps validated events to canonical schema.
Resolves sector aliases, standardizes severity scale, assigns geographic scope.

Geographic scope is now derived from the canonical governance registry
(app.governance.registry.get_geo_scope). The old TEMPLATE_GEO_SCOPE dict
has been removed — it contained 17 dev-era scenario IDs that never matched
the 8 canonical catalog IDs, causing every run to default to ["SA", "UAE"].
"""

import uuid
from app.domain.models.raw_event import ValidatedEvent, NormalizedEvent
from app.graph.bridge import get_scenario_shock_vector
from app.governance.registry import get_geo_scope as _registry_geo_scope

# Sector alias resolution
SECTOR_ALIASES: dict[str, str] = {
    "bank": "banking",
    "banks": "banking",
    "finance": "banking",
    "insure": "insurance",
    "reinsurance": "insurance",
    "fintech_payments": "fintech",
    "payments": "fintech",
    "oil": "energy",
    "gas": "energy",
    "petroleum": "energy",
    "airline": "aviation",
    "airlines": "aviation",
    "air": "aviation",
    "port": "ports",
    "maritime": "shipping",
    "sea": "shipping",
    "food": "food_security",
    "water": "utilities",
    "power": "utilities",
    "electricity": "utilities",
    "telecom": "telecom",
    "communications": "telecom",
}

# Event type normalization
TYPE_ALIASES: dict[str, str] = {
    "geo": "geopolitical",
    "political": "geopolitical",
    "military": "geopolitical",
    "market": "economic",
    "financial": "economic",
    "climate": "natural",
    "weather": "natural",
    "earthquake": "natural",
    "hack": "cyber",
    "attack": "cyber",
}


def normalize_sector(sector: str) -> str:
    """Resolve sector aliases to canonical name."""
    return SECTOR_ALIASES.get(sector.lower(), sector.lower())


def normalize_event_type(event_type: str) -> str:
    """Resolve event type aliases to canonical name."""
    return TYPE_ALIASES.get(event_type.lower(), event_type.lower())


def normalize_event(validated: ValidatedEvent) -> NormalizedEvent:
    """Normalize a validated event to canonical schema.

    - Resolves sector aliases
    - Assigns geographic scope from template
    - Builds shock vector from template if available
    - Computes initial confidence
    """
    # Resolve sectors
    sectors = [normalize_sector(s) for s in validated.sectors_affected]

    # Get shock vector from scenario template
    shock_vector: list[dict] = []
    if validated.template_id:
        raw_shocks = get_scenario_shock_vector(validated.template_id)
        shock_vector = [
            {"node_id": s["node_id"], "impact": s["impact"] * validated.severity}
            for s in raw_shocks
        ]

    # Geographic scope — derived from canonical governance registry.
    # _registry_geo_scope() returns the correct multi-country scope for all 8
    # canonical scenarios, and falls back to ["SA", "UAE"] only for unknown IDs.
    geo_scope = _registry_geo_scope(validated.template_id or "", default=["SA", "UAE"])

    # Initial confidence = validation_score (will be adjusted by enrich stage)
    confidence = validated.validation_score

    return NormalizedEvent(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        canonical_type=normalize_event_type("geopolitical"),
        severity=validated.severity,
        shock_vector=shock_vector,
        geographic_scope=geo_scope,
        confidence=confidence,
        provenance_chain=["ingest", "validate", "normalize"],
    )
