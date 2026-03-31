"""
Baseline Snapshot Capture for Scenario Simulations.

Captures and manages the system state before shock application,
providing a reference point for delta analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import numpy as np


@dataclass
class BaselineSnapshot:
    """
    Snapshot of system state before shock application.
    
    Captures all node-level risk scores, network topology, and system-wide
    metrics that serve as the baseline for before/after comparison.
    
    Attributes:
        snapshot_id: Unique identifier for this snapshot
        scenario_id: Associated scenario ID
        timestamp: When snapshot was captured
        node_risk_scores: Dict of node_id -> risk_score (0.0-1.0)
        node_network_centrality: Dict of node_id -> centrality measure
        node_criticality: Dict of node_id -> criticality score
        node_load_factors: Dict of node_id -> current load (0.0-1.0)
        adjacency_matrix: Network topology as 2D array or sparse representation
        node_ids: Ordered list of node IDs matching matrix indices
        system_aggregate_risk: Overall system risk score
        system_connectivity: Network connectivity metric
        corridor_utilization: Dict of corridor_id -> utilization rate
        regional_risk_distribution: Dict of region -> aggregate risk
        risk_distribution_vector: Vector form of all node risks
        metadata: Additional context about the baseline state
    """
    
    snapshot_id: str
    scenario_id: str
    timestamp: datetime
    node_risk_scores: Dict[str, float]
    node_network_centrality: Dict[str, float]
    node_criticality: Dict[str, float]
    node_load_factors: Dict[str, float]
    adjacency_matrix: np.ndarray
    node_ids: List[str]
    system_aggregate_risk: float
    system_connectivity: float
    corridor_utilization: Dict[str, float]
    regional_risk_distribution: Dict[str, float]
    risk_distribution_vector: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_node_risk(self, node_id: str) -> float:
        """Get risk score for a specific node."""
        return self.node_risk_scores.get(node_id, 0.0)
    
    def get_node_centrality(self, node_id: str) -> float:
        """Get network centrality for a specific node."""
        return self.node_network_centrality.get(node_id, 0.0)
    
    def get_adjacency_matrix(self) -> np.ndarray:
        """Get the network adjacency matrix."""
        return self.adjacency_matrix.copy()
    
    def get_risk_vector(self) -> np.ndarray:
        """Get risk vector from nodes in matrix order."""
        return self.risk_distribution_vector.copy()
    
    def get_top_risk_nodes(self, k: int = 10) -> List[tuple]:
        """Get top-k nodes by risk score. Returns list of (node_id, risk_score) tuples."""
        sorted_nodes = sorted(
            self.node_risk_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_nodes[:k]
    
    def get_top_centrality_nodes(self, k: int = 10) -> List[tuple]:
        """Get top-k nodes by network centrality. Returns list of (node_id, centrality) tuples."""
        sorted_nodes = sorted(
            self.node_network_centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_nodes[:k]
    
    def get_corridor_status(self) -> Dict[str, Dict[str, float]]:
        """Get status of all corridors with utilization and derived metrics."""
        return {
            corridor_id: {
                'utilization': util,
                'available_capacity': 1.0 - util,
                'congestion_risk': util ** 2  # Quadratic relationship
            }
            for corridor_id, util in self.corridor_utilization.items()
        }
    
    def get_regional_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get risk summary by region."""
        result = {}
        for region, risk in self.regional_risk_distribution.items():
            result[region] = {
                'aggregate_risk': risk,
                'risk_level': self._classify_risk_level(risk),
                'node_count': sum(1 for r in self.metadata.get('node_regions', {}).values() if r == region)
            }
        return result
    
    def _classify_risk_level(self, risk_score: float) -> str:
        """Classify risk score into levels."""
        if risk_score >= 0.75:
            return "CRITICAL"
        elif risk_score >= 0.50:
            return "HIGH"
        elif risk_score >= 0.25:
            return "MODERATE"
        else:
            return "LOW"
    
    def serialize_to_dict(self) -> Dict[str, Any]:
        """Serialize snapshot to dictionary (for storage/transmission)."""
        return {
            'snapshot_id': self.snapshot_id,
            'scenario_id': self.scenario_id,
            'timestamp': self.timestamp.isoformat(),
            'node_risk_scores': self.node_risk_scores,
            'node_network_centrality': self.node_network_centrality,
            'node_criticality': self.node_criticality,
            'node_load_factors': self.node_load_factors,
            'adjacency_matrix': self.adjacency_matrix.tolist(),
            'node_ids': self.node_ids,
            'system_aggregate_risk': float(self.system_aggregate_risk),
            'system_connectivity': float(self.system_connectivity),
            'corridor_utilization': self.corridor_utilization,
            'regional_risk_distribution': self.regional_risk_distribution,
            'risk_distribution_vector': self.risk_distribution_vector.tolist(),
            'metadata': self.metadata
        }
    
    def serialize_to_json(self) -> str:
        """Serialize snapshot to JSON string."""
        return json.dumps(self.serialize_to_dict(), indent=2, default=str)
    
    @classmethod
    def deserialize_from_dict(cls, data: Dict[str, Any]) -> 'BaselineSnapshot':
        """Deserialize snapshot from dictionary."""
        return cls(
            snapshot_id=data['snapshot_id'],
            scenario_id=data['scenario_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            node_risk_scores=data['node_risk_scores'],
            node_network_centrality=data['node_network_centrality'],
            node_criticality=data['node_criticality'],
            node_load_factors=data['node_load_factors'],
            adjacency_matrix=np.array(data['adjacency_matrix']),
            node_ids=data['node_ids'],
            system_aggregate_risk=data['system_aggregate_risk'],
            system_connectivity=data['system_connectivity'],
            corridor_utilization=data['corridor_utilization'],
            regional_risk_distribution=data['regional_risk_distribution'],
            risk_distribution_vector=np.array(data['risk_distribution_vector']),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def deserialize_from_json(cls, json_str: str) -> 'BaselineSnapshot':
        """Deserialize snapshot from JSON string."""
        data = json.loads(json_str)
        return cls.deserialize_from_dict(data)
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of the baseline state."""
        risk_values = np.array(list(self.node_risk_scores.values()))
        centrality_values = np.array(list(self.node_network_centrality.values()))
        load_values = np.array(list(self.node_load_factors.values()))
        
        return {
            'timestamp': self.timestamp.isoformat(),
            'node_count': len(self.node_ids),
            'risk_statistics': {
                'mean': float(np.mean(risk_values)),
                'std': float(np.std(risk_values)),
                'min': float(np.min(risk_values)),
                'max': float(np.max(risk_values)),
                'median': float(np.median(risk_values))
            },
            'centrality_statistics': {
                'mean': float(np.mean(centrality_values)),
                'std': float(np.std(centrality_values)),
                'min': float(np.min(centrality_values)),
                'max': float(np.max(centrality_values))
            },
            'load_statistics': {
                'mean': float(np.mean(load_values)),
                'std': float(np.std(load_values)),
                'max': float(np.max(load_values))
            },
            'system_aggregate_risk': self.system_aggregate_risk,
            'system_connectivity': self.system_connectivity,
            'corridors_at_high_utilization': sum(1 for u in self.corridor_utilization.values() if u > 0.75),
            'high_risk_nodes': sum(1 for r in self.node_risk_scores.values() if r > 0.75),
            'critical_centrality_nodes': sum(1 for c in self.node_network_centrality.values() if c > 0.80)
        }


@dataclass
class BaselineCaptureRequest:
    """Request to capture a baseline snapshot."""
    scenario_id: str
    include_network_topology: bool = True
    include_corridor_metrics: bool = True
    include_regional_distribution: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaselineCaptureResult:
    """Result of baseline capture operation."""
    success: bool
    snapshot: Optional[BaselineSnapshot] = None
    error_message: Optional[str] = None
    capture_duration_seconds: float = 0.0
    nodes_captured: int = 0
    correlations: Optional[Dict[str, float]] = None
