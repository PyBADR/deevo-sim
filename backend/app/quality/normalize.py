"""
Impact Observatory | مرصد الأثر — Event Normalization (Stage 3)

Maps validated events to canonical schema.
Resolves sector aliases, standardizes severity scale, assigns geographic scope.
"""

import uuid
from app.domain.models.raw_event import ValidatedEvent, NormalizedEvent
from app.graph.bridge import get_scenario_shock_vector

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

# Template → geographic scope mapping
TEMPLATE_GEO_SCOPE: dict[str, list[str]] = {
    "hormuz_closure": ["SA", "UAE", "KW", "QA", "OM", "BH"],
    "us_iran_escalation": ["SA", "UAE", "KW", "QA", "OM", "BH"],
    "military_repositioning": ["SA", "UAE", "KW"],
    "gcc_aviation_disruption": ["SA", "UAE", "QA", "KW", "OM", "BH"],
    "dubai_airport_shutdown": ["UAE"],
    "jebel_ali_blockade": ["UAE"],
    "saudi_oil_shock": ["SA"],
    "qatar_gas_disruption": ["QA"],
    "gcc_banking_crisis": ["SA", "UAE", "KW", "QA", "BH"],
    "insurance_cat_event": ["SA", "UAE", "KW", "QA", "OM", "BH"],
    "fintech_payment_failure": ["SA", "UAE"],
    "regional_cyber_attack": ["SA", "UAE", "KW", "QA", "OM", "BH"],
    "desalination_failure": ["SA", "UAE", "KW", "QA", "BH"],
    "food_supply_disruption": ["SA", "UAE", "KW", "QA", "OM", "BH"],
    "hajj_crisis": ["SA"],
    "sovereign_downgrade": ["SA", "UAE", "KW", "QA", "OM", "BH"],
    "telecom_outage": ["SA", "UAE", "KW", "QA"],
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

    # Geographic scope
    geo_scope = TEMPLATE_GEO_SCOPE.get(validated.template_id or "", ["SA", "UAE"])

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
