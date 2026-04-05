"""
Impact Observatory | مرصد الأثر — Signal Clustering (Stage 6)

Groups related enriched events into signal clusters based on
affected node overlap (Jaccard similarity > threshold).

For single-event pipelines (most common), this is a pass-through
that wraps the event into a single-member cluster.
"""

import uuid
from app.domain.models.raw_event import EnrichedEvent
from app.domain.models.signal import SignalCluster

JACCARD_THRESHOLD = 0.5


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union > 0 else 0.0


def cluster_signals(events: list[EnrichedEvent]) -> list[SignalCluster]:
    """Cluster enriched events by affected-node overlap.

    Parameters
    ----------
    events : list[EnrichedEvent]
        One or more enriched events from the quality pipeline.

    Returns
    -------
    list[SignalCluster]
        Clusters of related events. Single events produce single-member clusters.
    """
    if not events:
        return []

    if len(events) == 1:
        # Single event — wrap as single-member cluster (fast path)
        e = events[0]
        return [SignalCluster(
            cluster_id=f"clust_{uuid.uuid4().hex[:8]}",
            signals=[e.event_id],
            composite_strength=e.severity * e.confidence,
            theme=e.canonical_type,
            affected_nodes=e.graph_node_ids,
        )]

    # Multi-event clustering via greedy Jaccard overlap
    assigned: set[int] = set()
    clusters: list[SignalCluster] = []

    for i, event_i in enumerate(events):
        if i in assigned:
            continue

        cluster_events = [event_i]
        assigned.add(i)
        nodes_i = set(event_i.graph_node_ids)

        for j, event_j in enumerate(events):
            if j in assigned:
                continue
            nodes_j = set(event_j.graph_node_ids)
            if _jaccard(nodes_i, nodes_j) >= JACCARD_THRESHOLD:
                cluster_events.append(event_j)
                assigned.add(j)
                nodes_i |= nodes_j

        # Compute composite strength
        strengths = [e.severity * e.confidence for e in cluster_events]
        composite = sum(strengths) / len(strengths) if strengths else 0.0

        all_nodes = list(set(
            nid for e in cluster_events for nid in e.graph_node_ids
        ))

        clusters.append(SignalCluster(
            cluster_id=f"clust_{uuid.uuid4().hex[:8]}",
            signals=[e.event_id for e in cluster_events],
            composite_strength=round(composite, 4),
            theme=cluster_events[0].canonical_type,
            affected_nodes=all_nodes,
        ))

    return clusters
