"""
Entity Graph Layer — backend/app/graph/

76-node, 191-edge GCC knowledge graph with traversal,
subgraph extraction, scenario-to-shock mapping, and snapshot building.
"""

from .registry import (
    NODES,
    EDGES,
    get_node,
    get_nodes_by_layer,
    get_edge,
    get_adjacency,
    get_all_layers,
    get_node_count,
    get_edge_count,
)
from .traversal import get_subgraph, get_impacted_nodes, shortest_path
from .bridge import apply_scenario_shocks, get_scenario_shock_vector, get_available_scenarios, scenario_exists
from .builder import build_graph_snapshot

__all__ = [
    "NODES", "EDGES",
    "get_node", "get_nodes_by_layer", "get_edge", "get_adjacency",
    "get_all_layers", "get_node_count", "get_edge_count",
    "get_subgraph", "get_impacted_nodes", "shortest_path",
    "apply_scenario_shocks", "get_scenario_shock_vector",
    "get_available_scenarios", "scenario_exists",
    "build_graph_snapshot",
]
