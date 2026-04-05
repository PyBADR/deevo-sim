"""
Impact Observatory | مرصد الأثر — Event Enrichment (Stage 5)

Adds graph context, GCC regional multipliers, and geospatial metadata.
Confidence is adjusted based on enrichment completeness.

Rules:
- Missing graph node matches: confidence reduced by 15%
- Enrichment completeness = matched_nodes / expected_nodes
- Regional multipliers applied from GCC constants
"""

from app.domain.models.raw_event import NormalizedEvent, EnrichedEvent
from app.graph.registry import get_node

# GCC regional multipliers (from gcc_constants.py)
REGIONAL_MULTIPLIERS: dict[str, float] = {
    "SA": 1.15,
    "UAE": 1.20,
    "KW": 1.05,
    "QA": 1.10,
    "OM": 0.95,
    "BH": 1.00,
}


def enrich_event(event: NormalizedEvent) -> EnrichedEvent:
    """Enrich a normalized event with graph context and regional data.

    Adds:
    - Matched graph node IDs from shock vector
    - Regional multipliers for geographic scope
    - Enrichment completeness score
    - Adjusted confidence
    """
    # Match shock vector node IDs against graph registry
    graph_node_ids: list[str] = []
    expected = len(event.shock_vector)
    matched = 0

    for shock in event.shock_vector:
        node_id = shock.get("node_id", "")
        node = get_node(node_id)
        if node:
            graph_node_ids.append(node_id)
            matched += 1

    # Enrichment completeness
    enrichment_completeness = matched / expected if expected > 0 else 1.0

    # Regional multipliers for geographic scope
    regional_multipliers = {
        cc: REGIONAL_MULTIPLIERS.get(cc, 1.0)
        for cc in event.geographic_scope
    }

    # Adjust confidence based on enrichment quality
    confidence = event.confidence
    if enrichment_completeness < 1.0:
        penalty = (1.0 - enrichment_completeness) * 0.15
        confidence = max(0.1, confidence - penalty)

    provenance = event.provenance_chain + [f"enrich:{matched}/{expected}_matched"]

    return EnrichedEvent(
        event_id=event.event_id,
        canonical_type=event.canonical_type,
        severity=event.severity,
        shock_vector=event.shock_vector,
        geographic_scope=event.geographic_scope,
        confidence=round(confidence, 4),
        provenance_chain=provenance,
        graph_node_ids=graph_node_ids,
        regional_multipliers=regional_multipliers,
        enrichment_completeness=round(enrichment_completeness, 4),
    )
