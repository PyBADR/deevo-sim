"""
Impact Observatory | مرصد الأثر — Graph Traversal

BFS/DFS traversal, subgraph extraction, shortest path, impact propagation.
Operates on the in-memory registry — no external database required.
"""

from collections import deque
from typing import Optional
from .registry import NODES, EDGES, get_node, get_adjacency, _ensure_indexes


def get_subgraph(center_id: str, depth: int = 2) -> dict:
    """Extract ego-network around a center node up to given depth.
    Returns {"nodes": [...], "edges": [...]}."""
    _ensure_indexes()
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(center_id, 0)])
    result_nodes: list[dict] = []
    result_edges: list[dict] = []
    seen_edges: set[str] = set()

    while queue:
        node_id, d = queue.popleft()
        if node_id in visited or d > depth:
            continue
        visited.add(node_id)
        node = get_node(node_id)
        if node:
            result_nodes.append(node)

        if d < depth:
            # Forward edges
            for edge in get_adjacency(node_id):
                if edge["id"] not in seen_edges:
                    seen_edges.add(edge["id"])
                    result_edges.append(edge)
                if edge["target"] not in visited:
                    queue.append((edge["target"], d + 1))
            # Reverse edges
            for e in EDGES:
                if e["target"] == node_id and e["source"] not in visited:
                    if e["id"] not in seen_edges:
                        seen_edges.add(e["id"])
                        result_edges.append(e)
                    queue.append((e["source"], d + 1))

    return {"nodes": result_nodes, "edges": result_edges}


def get_impacted_nodes(
    shock_vector: list[dict],
    max_depth: int = 3,
    min_threshold: float = 0.01,
) -> list[dict]:
    """Given a shock vector [{node_id, impact}], BFS propagate impacts.

    Propagation formula per edge:
        transmitted = parent_impact × edge_weight × (1 - target_damping_factor)

    Returns list of {node_id, label, label_ar, lat, lng, layer, impact}.
    Sorted by descending impact.
    """
    _ensure_indexes()
    impacts: dict[str, float] = {}
    for shock in shock_vector:
        impacts[shock["node_id"]] = shock.get("impact", 0.5)

    queue: deque[tuple[str, int, float]] = deque()
    for shock in shock_vector:
        queue.append((shock["node_id"], 0, shock.get("impact", 0.5)))

    visited: set[str] = set()
    while queue:
        node_id, depth, impact = queue.popleft()
        if node_id in visited or depth > max_depth:
            continue
        visited.add(node_id)

        for edge in get_adjacency(node_id):
            target = edge["target"]
            target_node = get_node(target)
            damping = target_node.get("damping_factor", 0.05) if target_node else 0.05
            transmitted = impact * edge["weight"] * (1.0 - damping)

            if transmitted > min_threshold:
                existing = impacts.get(target, 0.0)
                impacts[target] = max(existing, transmitted)
                if target not in visited:
                    queue.append((target, depth + 1, transmitted))

    result = []
    for nid, imp in sorted(impacts.items(), key=lambda x: -x[1]):
        node = get_node(nid)
        if node:
            result.append({
                "node_id": nid,
                "label": node["label"],
                "label_ar": node.get("label_ar", ""),
                "lat": node["lat"],
                "lng": node["lng"],
                "layer": node["layer"],
                "impact": round(imp, 4),
            })
    return result


def shortest_path(source_id: str, target_id: str) -> Optional[list[str]]:
    """BFS shortest path by hop count. Returns list of node IDs or None."""
    _ensure_indexes()
    if source_id == target_id:
        return [source_id]

    queue: deque[tuple[str, list[str]]] = deque([(source_id, [source_id])])
    visited = {source_id}

    while queue:
        current, path = queue.popleft()
        for edge in get_adjacency(current):
            next_node = edge["target"]
            if next_node == target_id:
                return path + [next_node]
            if next_node not in visited:
                visited.add(next_node)
                queue.append((next_node, path + [next_node]))
    return None
