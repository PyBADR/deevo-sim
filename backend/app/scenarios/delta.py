"""
Delta Analysis Module - Scenario Engine Phase 6
Computes before/after changes in risk scores and system metrics
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import numpy as np
from datetime import datetime

from app.scenarios.baseline import BaselineSnapshot
from app.scenarios.simulator import ScenarioSimulationResult


@dataclass
class NodeDeltaAnalysis:
    """Analysis of delta changes for a single node"""
    node_id: str
    baseline_risk: float
    post_shock_risk: float
    risk_delta: float  # post - baseline
    risk_delta_pct: float  # percentage change
    baseline_centrality: float
    baseline_load: float
    impact_severity: str  # 'critical', 'high', 'medium', 'low', 'none'
    affected_by_cascade: bool
    cascade_hop_distance: Optional[int] = None


@dataclass
class DeltaMetrics:
    """Aggregate delta metrics across entire system"""
    timestamp: datetime
    total_nodes_affected: int
    critical_nodes: int
    high_impact_nodes: int
    mean_risk_increase: float
    max_risk_increase: float
    system_risk_delta: float
    connectivity_delta: float
    system_stress_delta: float
    recovery_time_estimate_hours: float
    affected_corridors: List[str] = field(default_factory=list)
    affected_regions: List[str] = field(default_factory=list)


class DeltaCalculator:
    """Computes before/after deltas for scenario analysis"""
    
    def __init__(self):
        self.critical_threshold = 0.75
        self.high_threshold = 0.50
        self.medium_threshold = 0.25
    
    def calculate_node_deltas(
        self,
        baseline: BaselineSnapshot,
        simulation_result: ScenarioSimulationResult,
        cascade_info: Optional[Dict] = None
    ) -> Dict[str, NodeDeltaAnalysis]:
        """
        Calculate delta analysis for each node
        
        Args:
            baseline: Pre-shock baseline snapshot
            simulation_result: Post-shock simulation results
            cascade_info: Optional cascade propagation information
        
        Returns:
            Dictionary mapping node_id to NodeDeltaAnalysis
        """
        node_deltas = {}
        cascade_info = cascade_info or {}
        
        for node_id in baseline.node_ids:
            baseline_risk = baseline.get_node_risk(node_id)
            post_shock_risk = simulation_result.final_risk_scores.get(node_id, baseline_risk)
            
            risk_delta = post_shock_risk - baseline_risk
            risk_delta_pct = (risk_delta / baseline_risk * 100) if baseline_risk > 0 else 0.0
            
            # Determine impact severity
            if post_shock_risk >= self.critical_threshold:
                impact_severity = 'critical'
            elif post_shock_risk >= self.high_threshold:
                impact_severity = 'high'
            elif post_shock_risk >= self.medium_threshold:
                impact_severity = 'medium'
            elif risk_delta > 0.01:
                impact_severity = 'low'
            else:
                impact_severity = 'none'
            
            # Check cascade involvement
            cascade_data = cascade_info.get(node_id, {})
            affected_by_cascade = cascade_data.get('affected', False)
            cascade_hop = cascade_data.get('hop_distance')
            
            node_deltas[node_id] = NodeDeltaAnalysis(
                node_id=node_id,
                baseline_risk=baseline_risk,
                post_shock_risk=post_shock_risk,
                risk_delta=risk_delta,
                risk_delta_pct=risk_delta_pct,
                baseline_centrality=baseline.get_node_centrality(node_id),
                baseline_load=baseline.node_load_factors.get(node_id, 0.0),
                impact_severity=impact_severity,
                affected_by_cascade=affected_by_cascade,
                cascade_hop_distance=cascade_hop
            )
        
        return node_deltas
    
    def calculate_aggregate_deltas(
        self,
        baseline: BaselineSnapshot,
        simulation_result: ScenarioSimulationResult,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        corridor_mapping: Optional[Dict[str, List[str]]] = None,
        region_mapping: Optional[Dict[str, List[str]]] = None
    ) -> DeltaMetrics:
        """
        Calculate aggregate system-level delta metrics
        
        Args:
            baseline: Pre-shock baseline
            simulation_result: Post-shock simulation results
            node_deltas: Node-level delta analysis
            corridor_mapping: Optional mapping of node_id to corridors
            region_mapping: Optional mapping of node_id to regions
        
        Returns:
            DeltaMetrics with system-level aggregates
        """
        corridor_mapping = corridor_mapping or {}
        region_mapping = region_mapping or {}
        
        # Count affected nodes by severity
        total_affected = sum(1 for nd in node_deltas.values() if nd.impact_severity != 'none')
        critical_nodes = sum(1 for nd in node_deltas.values() if nd.impact_severity == 'critical')
        high_impact = sum(1 for nd in node_deltas.values() if nd.impact_severity == 'high')
        
        # Calculate risk statistics
        risk_deltas = [nd.risk_delta for nd in node_deltas.values()]
        mean_risk_increase = np.mean(risk_deltas) if risk_deltas else 0.0
        max_risk_increase = np.max(risk_deltas) if risk_deltas else 0.0
        
        # System-level deltas
        system_risk_delta = simulation_result.final_risk_scores.get('__system__', 0.0) - baseline.system_aggregate_risk
        connectivity_delta = 0.0  # Connectivity maintained in scenarios
        system_stress_delta = simulation_result.system_stress_final - 0.0  # Baseline stress assumed 0
        
        # Identify affected corridors and regions
        affected_nodes = {nd.node_id for nd in node_deltas.values() if nd.impact_severity != 'none'}
        affected_corridors = list(set(
            corridor for node_id in affected_nodes
            for corridor in corridor_mapping.get(node_id, [])
        ))
        affected_regions = list(set(
            region for node_id in affected_nodes
            for region in region_mapping.get(node_id, [])
        ))
        
        return DeltaMetrics(
            timestamp=datetime.utcnow(),
            total_nodes_affected=total_affected,
            critical_nodes=critical_nodes,
            high_impact_nodes=high_impact,
            mean_risk_increase=mean_risk_increase,
            max_risk_increase=max_risk_increase,
            system_risk_delta=system_risk_delta,
            connectivity_delta=connectivity_delta,
            system_stress_delta=system_stress_delta,
            recovery_time_estimate_hours=simulation_result.recovery_time_estimate_hours,
            affected_corridors=affected_corridors,
            affected_regions=affected_regions
        )
    
    def identify_critical_nodes(
        self,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        threshold: Optional[float] = None
    ) -> List[Tuple[str, NodeDeltaAnalysis]]:
        """
        Identify critical nodes exceeding severity threshold
        
        Returns:
            Sorted list of (node_id, delta_analysis) tuples by risk delta descending
        """
        threshold = threshold or self.critical_threshold
        critical = [
            (node_id, delta)
            for node_id, delta in node_deltas.items()
            if delta.post_shock_risk >= threshold
        ]
        return sorted(critical, key=lambda x: x[1].risk_delta, reverse=True)
    
    def calculate_recovery_trajectory(
        self,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        recovery_hours: float,
        decay_rate: float = 0.1
    ) -> Dict[str, List[float]]:
        """
        Project recovery trajectory for affected nodes
        
        Args:
            node_deltas: Node delta analysis
            recovery_hours: Total estimated recovery time
            decay_rate: Exponential decay rate per hour
        
        Returns:
            Dictionary mapping node_id to list of projected risk scores over time
        """
        time_steps = int(recovery_hours)
        trajectories = {}
        
        for node_id, delta in node_deltas.items():
            if delta.impact_severity == 'none':
                trajectories[node_id] = [delta.baseline_risk] * time_steps
            else:
                trajectory = []
                for t in range(time_steps):
                    # Exponential decay back to baseline
                    progress = 1.0 - np.exp(-decay_rate * t)
                    recovered_risk = delta.baseline_risk + (delta.risk_delta * (1.0 - progress))
                    trajectory.append(max(delta.baseline_risk, recovered_risk))
                trajectories[node_id] = trajectory
        
        return trajectories
    
    def compare_scenarios(
        self,
        baseline: BaselineSnapshot,
        scenario1_result: ScenarioSimulationResult,
        scenario2_result: ScenarioSimulationResult,
        scenario1_name: str = "Scenario 1",
        scenario2_name: str = "Scenario 2"
    ) -> Dict:
        """
        Compare impacts of two different scenarios
        
        Returns:
            Dictionary with comparative metrics
        """
        delta1 = scenario1_result.risk_change_vector
        delta2 = scenario2_result.risk_change_vector
        
        # Calculate comparative statistics
        mean_delta1 = np.mean(delta1) if isinstance(delta1, np.ndarray) else 0.0
        mean_delta2 = np.mean(delta2) if isinstance(delta2, np.ndarray) else 0.0
        
        return {
            scenario1_name: {
                'mean_impact': mean_delta1,
                'max_impact': float(np.max(delta1)) if isinstance(delta1, np.ndarray) else 0.0,
                'system_stress': scenario1_result.system_stress_final,
                'recovery_hours': scenario1_result.recovery_time_estimate_hours,
                'critical_nodes': len([c for c in scenario1_result.critical_nodes_post_shock if c is not None])
            },
            scenario2_name: {
                'mean_impact': mean_delta2,
                'max_impact': float(np.max(delta2)) if isinstance(delta2, np.ndarray) else 0.0,
                'system_stress': scenario2_result.system_stress_final,
                'recovery_hours': scenario2_result.recovery_time_estimate_hours,
                'critical_nodes': len([c for c in scenario2_result.critical_nodes_post_shock if c is not None])
            },
            'more_severe_scenario': scenario1_name if mean_delta1 > mean_delta2 else scenario2_name,
            'severity_ratio': max(mean_delta1, mean_delta2) / min(mean_delta1, mean_delta2) if min(mean_delta1, mean_delta2) > 0 else 1.0
        }
    
    def serialize_deltas(self, node_deltas: Dict[str, NodeDeltaAnalysis]) -> Dict:
        """Serialize node deltas to dictionary format"""
        return {
            node_id: {
                'node_id': delta.node_id,
                'baseline_risk': delta.baseline_risk,
                'post_shock_risk': delta.post_shock_risk,
                'risk_delta': delta.risk_delta,
                'risk_delta_pct': delta.risk_delta_pct,
                'baseline_centrality': delta.baseline_centrality,
                'baseline_load': delta.baseline_load,
                'impact_severity': delta.impact_severity,
                'affected_by_cascade': delta.affected_by_cascade,
                'cascade_hop_distance': delta.cascade_hop_distance
            }
            for node_id, delta in node_deltas.items()
        }
    
    def serialize_metrics(self, metrics: DeltaMetrics) -> Dict:
        """Serialize delta metrics to dictionary format"""
        return {
            'timestamp': metrics.timestamp.isoformat(),
            'total_nodes_affected': metrics.total_nodes_affected,
            'critical_nodes': metrics.critical_nodes,
            'high_impact_nodes': metrics.high_impact_nodes,
            'mean_risk_increase': metrics.mean_risk_increase,
            'max_risk_increase': metrics.max_risk_increase,
            'system_risk_delta': metrics.system_risk_delta,
            'connectivity_delta': metrics.connectivity_delta,
            'system_stress_delta': metrics.system_stress_delta,
            'recovery_time_estimate_hours': metrics.recovery_time_estimate_hours,
            'affected_corridors': metrics.affected_corridors,
            'affected_regions': metrics.affected_regions
        }
