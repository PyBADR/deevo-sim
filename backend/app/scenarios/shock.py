"""
Shock Injection Engine for Scenario Simulations.

Applies disruption shocks to specified network nodes with cascading effects.
Implements 1-hop cascade propagation and severity scaling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import datetime
import numpy as np
from enum import Enum


class CascadeType(Enum):
    """Types of cascade propagation."""
    NONE = "none"
    DIRECT_NEIGHBORS = "direct_neighbors"
    DISTANCE_WEIGHTED = "distance_weighted"


@dataclass
class ShockEvent:
    """
    Single shock event applied to a node.
    
    Attributes:
        node_id: Target node receiving the shock
        severity: Shock magnitude (0.0-1.0)
        impact_type: Category of impact (direct damage, congestion, uncertainty, etc.)
        timestamp: When shock occurs
        duration_hours: Expected duration of shock effect
        cascade_enabled: Whether shock cascades to neighbors
        cascade_depth: Hops for cascade propagation
    """
    node_id: str
    severity: float
    impact_type: str = "direct_disruption"
    timestamp: Optional[datetime] = None
    duration_hours: int = 24
    cascade_enabled: bool = True
    cascade_depth: int = 1
    cascade_type: CascadeType = CascadeType.DIRECT_NEIGHBORS
    cascade_attenuation: float = 0.7  # Severity reduction per hop
    
    def __post_init__(self):
        """Validate shock parameters."""
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError(f"Severity must be 0.0-1.0, got {self.severity}")
        if self.cascade_depth < 0:
            raise ValueError(f"Cascade depth must be >= 0, got {self.cascade_depth}")
        if not 0.0 <= self.cascade_attenuation <= 1.0:
            raise ValueError(f"Cascade attenuation must be 0.0-1.0")
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class CascadeEffect:
    """Effect of a cascading shock on a neighbor."""
    source_node: str
    target_node: str
    hop_distance: int
    attenuated_severity: float
    propagation_type: str = "cascade"


@dataclass
class ShockApplicationResult:
    """Result of applying a shock to the network."""
    shock_event: ShockEvent
    primary_impact_nodes: Set[str]
    cascading_impacts: List[CascadeEffect]
    affected_node_count: int
    total_impact_severity: float  # Aggregate severity across all affected nodes
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ShockInjector:
    """
    Engine for injecting shocks into network nodes.
    
    Handles direct shock application, cascade propagation, severity scaling,
    and impact aggregation.
    """
    
    def __init__(self, adjacency_matrix: np.ndarray, node_ids: List[str]):
        """
        Initialize shock injector.
        
        Args:
            adjacency_matrix: Network topology (NxN adjacency matrix)
            node_ids: Ordered list of node IDs
        """
        self.adjacency_matrix = adjacency_matrix
        self.node_ids = node_ids
        self.node_index_map = {nid: i for i, nid in enumerate(node_ids)}
        self._validate_matrix()
    
    def _validate_matrix(self):
        """Validate adjacency matrix dimensions."""
        n = len(self.node_ids)
        if self.adjacency_matrix.shape != (n, n):
            raise ValueError(
                f"Matrix shape {self.adjacency_matrix.shape} doesn't match "
                f"node count {n}"
            )
    
    def apply_shock(self, shock_event: ShockEvent) -> ShockApplicationResult:
        """
        Apply a single shock to the network.
        
        Args:
            shock_event: The shock to apply
            
        Returns:
            ShockApplicationResult with impact details
        """
        # Validate shock
        if shock_event.node_id not in self.node_index_map:
            return ShockApplicationResult(
                shock_event=shock_event,
                primary_impact_nodes=set(),
                cascading_impacts=[],
                affected_node_count=0,
                total_impact_severity=0.0,
                success=False,
                error_message=f"Node {shock_event.node_id} not found in network"
            )
        
        # Primary impact
        primary_nodes = {shock_event.node_id}
        total_severity = shock_event.severity
        cascading_impacts = []
        
        # Cascade propagation
        if shock_event.cascade_enabled and shock_event.cascade_depth > 0:
            cascade_effects = self._propagate_cascade(shock_event)
            cascading_impacts = cascade_effects['effects']
            primary_nodes.update(cascade_effects['affected_nodes'])
            total_severity += cascade_effects['total_cascade_severity']
        
        return ShockApplicationResult(
            shock_event=shock_event,
            primary_impact_nodes=primary_nodes,
            cascading_impacts=cascading_impacts,
            affected_node_count=len(primary_nodes),
            total_impact_severity=total_severity,
            success=True
        )
    
    def apply_multiple_shocks(self, shocks: List[ShockEvent]) -> List[ShockApplicationResult]:
        """
        Apply multiple shocks to the network.
        
        Args:
            shocks: List of shock events to apply
            
        Returns:
            List of results for each shock
        """
        results = []
        for shock in shocks:
            result = self.apply_shock(shock)
            results.append(result)
        return results
    
    def _propagate_cascade(self, shock: ShockEvent) -> Dict[str, Any]:
        """
        Propagate shock through cascade hops.
        
        Args:
            shock: Shock event
            
        Returns:
            Dict with cascading effects and affected nodes
        """
        effects = []
        affected_nodes = set()
        total_cascade_severity = 0.0
        
        # Get primary node index
        primary_idx = self.node_index_map[shock.node_id]
        
        # BFS for cascade propagation
        visited = {shock.node_id}
        current_level = {shock.node_id: shock.severity}
        
        for hop in range(shock.cascade_depth):
            next_level = {}
            
            for node_id, current_severity in current_level.items():
                node_idx = self.node_index_map[node_id]
                
                # Get neighbors (non-zero adjacency)
                neighbors = np.where(self.adjacency_matrix[node_idx] > 0)[0]
                
                for neighbor_idx in neighbors:
                    neighbor_id = self.node_ids[neighbor_idx]
                    
                    if neighbor_id in visited:
                        continue
                    
                    # Calculate attenuated severity
                    if shock.cascade_type == CascadeType.DIRECT_NEIGHBORS:
                        # Simple attenuation by hop count
                        attenuated = current_severity * (shock.cascade_attenuation ** (hop + 1))
                    elif shock.cascade_type == CascadeType.DISTANCE_WEIGHTED:
                        # Weight by connection strength
                        weight = self.adjacency_matrix[node_idx, neighbor_idx]
                        attenuated = current_severity * (shock.cascade_attenuation ** (hop + 1)) * weight
                    else:
                        attenuated = current_severity * (shock.cascade_attenuation ** (hop + 1))
                    
                    # Record cascade effect
                    effect = CascadeEffect(
                        source_node=node_id,
                        target_node=neighbor_id,
                        hop_distance=hop + 1,
                        attenuated_severity=attenuated,
                        propagation_type=shock.cascade_type.value
                    )
                    effects.append(effect)
                    affected_nodes.add(neighbor_id)
                    total_cascade_severity += attenuated
                    
                    # Add to next level if not visited
                    if neighbor_id not in visited:
                        next_level[neighbor_id] = attenuated
                        visited.add(neighbor_id)
            
            if not next_level:
                break
            
            current_level = next_level
        
        return {
            'effects': effects,
            'affected_nodes': affected_nodes,
            'total_cascade_severity': total_cascade_severity
        }
    
    def get_cascading_neighbors(self, node_id: str, depth: int = 1) -> Dict[int, List[str]]:
        """
        Get cascading neighbors at each hop distance.
        
        Args:
            node_id: Source node
            depth: Maximum hop distance
            
        Returns:
            Dict mapping hop distance -> list of neighbor node IDs
        """
        if node_id not in self.node_index_map:
            return {}
        
        neighbors_by_distance = {}
        visited = {node_id}
        current_level = [node_id]
        
        for hop in range(1, depth + 1):
            next_level = []
            
            for cnode_id in current_level:
                node_idx = self.node_index_map[cnode_id]
                neighbors = np.where(self.adjacency_matrix[node_idx] > 0)[0]
                
                for neighbor_idx in neighbors:
                    neighbor_id = self.node_ids[neighbor_idx]
                    if neighbor_id not in visited:
                        next_level.append(neighbor_id)
                        visited.add(neighbor_id)
            
            if next_level:
                neighbors_by_distance[hop] = next_level
            else:
                break
            
            current_level = next_level
        
        return neighbors_by_distance
    
    def scale_shock_severity(self, base_severity: float, 
                            scaling_factors: Dict[str, float]) -> float:
        """
        Scale shock severity based on contextual factors.
        
        Args:
            base_severity: Unscaled severity (0.0-1.0)
            scaling_factors: Dict of factor_name -> multiplier
            
        Returns:
            Scaled severity (clamped to 0.0-1.0)
        """
        scaled = base_severity
        
        # Apply scaling factors
        for factor_name, multiplier in scaling_factors.items():
            scaled *= multiplier
        
        # Clamp to valid range
        return max(0.0, min(1.0, scaled))
    
    def create_shock_vector(self, shocks: List[ShockEvent]) -> np.ndarray:
        """
        Create a shock vector from multiple shock events.
        
        Args:
            shocks: List of shock events
            
        Returns:
            Vector of shock impacts per node (length = number of nodes)
        """
        shock_vector = np.zeros(len(self.node_ids))
        
        for shock in shocks:
            if shock.node_id in self.node_index_map:
                idx = self.node_index_map[shock.node_id]
                shock_vector[idx] = max(shock_vector[idx], shock.severity)
        
        return shock_vector
    
    def get_vulnerability_profile(self, node_id: str) -> Dict[str, Any]:
        """
        Get vulnerability profile for a node (how exposed it is to shocks).
        
        Args:
            node_id: Target node
            
        Returns:
            Vulnerability metrics
        """
        if node_id not in self.node_index_map:
            return {}
        
        node_idx = self.node_index_map[node_id]
        
        # Degree (number of connections)
        degree = np.sum(self.adjacency_matrix[node_idx] > 0)
        
        # Betweenness-like metric (rough approximation)
        in_degree = np.sum(self.adjacency_matrix[:, node_idx] > 0)
        
        # Connection strength (sum of weights)
        connection_strength = np.sum(self.adjacency_matrix[node_idx])
        
        return {
            'node_id': node_id,
            'degree': int(degree),
            'in_degree': int(in_degree),
            'total_degree': int(degree + in_degree),
            'connection_strength': float(connection_strength),
            'vulnerability_index': float(min(1.0, connection_strength / max(1.0, float(degree))))
        }
