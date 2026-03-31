"""
Bridge module connecting ScenarioTemplate/ScenarioSimulationResult to Mesa GCCModel.

Provides conversion utilities for instantiating Mesa models from scenarios and
extracting Delta metrics from Mesa simulation results.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import numpy as np

from app.scenarios.templates import ScenarioTemplate
from app.scenarios.shock import ShockEvent, ShockInjector, ShockApplicationResult
from app.intelligence.math_core.state_vector import EntityStateVector

from .mesa_model import GCCModel, InfrastructureAgent, EventAgent, FlowAgent


@dataclass
class MesaDeltaResult:
    """Extracted delta metrics from Mesa simulation results."""

    node_risk_delta: Dict[str, float]
    system_stress_delta: float
    critical_nodes_count: int
    affected_nodes_count: int
    mean_recovery_progress: float
    cascade_depth_reached: int
    event_duration_avg: float


class MesaBridge:
    """
    Bidirectional bridge between scenario execution and Mesa simulation.

    Converts ScenarioTemplate into GCCModel configuration, runs simulation,
    and extracts Delta metrics for integration with DecisionOutputGenerator.
    """

    def __init__(self):
        """Initialize bridge with standard configuration."""
        self.model: Optional[GCCModel] = None
        self.scenario_template: Optional[ScenarioTemplate] = None
        self.baseline_risk_scores: Dict[str, float] = {}

    def from_scenario_template(
        self,
        template: ScenarioTemplate,
        node_locations: Dict[str, Tuple[float, float]],
        adjacency_matrix: Dict[str, List[str]],
        node_criticality: Dict[str, float],
        node_exposure: Dict[str, float],
        baseline_risk_scores: Optional[Dict[str, float]] = None,
    ) -> GCCModel:
        """
        Create and initialize GCCModel from ScenarioTemplate.

        Args:
            template: ScenarioTemplate with scenario definition
            node_locations: Dict[node_id -> (lat, lon)]
            adjacency_matrix: Network topology
            node_criticality: Node criticality scores [0,1]
            node_exposure: Node exposure scores [0,1]
            baseline_risk_scores: Baseline risk for delta computation

        Returns:
            Initialized GCCModel ready for simulation
        """
        self.scenario_template = template
        self.baseline_risk_scores = baseline_risk_scores or {}

        # Create model with network topology
        self.model = GCCModel(
            node_locations=node_locations,
            adjacency_matrix=adjacency_matrix,
            node_criticality=node_criticality,
            node_exposure=node_exposure,
            cascade_attenuation=template.propagation_coefficient,
            max_cascade_depth=template.propagation_depth,
        )

        return self.model

    def run_and_convert(
        self, num_steps: int = 20, capture_intermediate: bool = False
    ) -> MesaDeltaResult:
        """
        Execute Mesa simulation and extract delta metrics.

        Args:
            num_steps: Number of simulation steps to run
            capture_intermediate: Whether to capture intermediate snapshots

        Returns:
            MesaDeltaResult with delta metrics from baseline
        """
        if not self.model:
            raise ValueError("Model not initialized. Call from_scenario_template first.")

        # Run simulation
        self.model.run_steps(num_steps)

        # Extract results
        return self.extract_delta()

    def inject_scenario_shocks(self):
        """
        Inject scenario shocks into model from template.

        Reads shock_event_locations from template and applies via ShockInjector.
        """
        if not self.model or not self.scenario_template:
            raise ValueError("Model and scenario template must be initialized first.")

        shock_injector = ShockInjector()

        # Create shock events from template
        for node_id, severity in self.scenario_template.shock_event_locations.items():
            shock = ShockEvent(
                node_id=node_id,
                severity=severity,
                impact_type=self.scenario_template.disruption_type,
                cascade_enabled=True,
                cascade_depth=self.scenario_template.propagation_depth,
                cascade_type="geometric",
                cascade_attenuation=self.scenario_template.propagation_coefficient,
            )

            # Inject shock into model
            self.model.inject_shock(
                shock_node_id=node_id,
                severity=severity,
                cascade_enabled=True,
                cascade_depth=self.scenario_template.propagation_depth,
            )

    def extract_delta(self) -> MesaDeltaResult:
        """
        Extract delta metrics from model state.

        Computes changes from baseline across all nodes and aggregated metrics.

        Returns:
            MesaDeltaResult with comprehensive delta information
        """
        if not self.model:
            raise ValueError("Model not initialized.")

        node_risk_delta = {}
        max_cascade_depth = 0
        total_recovery = 0.0
        event_age_sum = 0.0
        event_count = 0

        # Compute node-level deltas
        for node_id, agent in self.model.infrastructure_agents.items():
            baseline = self.baseline_risk_scores.get(node_id, 0.0)
            current = agent.state.risk_score
            node_risk_delta[node_id] = current - baseline

            # Track cascade depth
            max_cascade_depth = max(max_cascade_depth, agent.state.cascade_depth)
            total_recovery += agent.state.recovery_progress

        # Average recovery progress
        mean_recovery = (
            total_recovery / len(self.model.infrastructure_agents)
            if self.model.infrastructure_agents
            else 0.0
        )

        # Event metrics
        for event in self.model.event_agents:
            event_age_sum += event.age
            event_count += 1

        event_duration_avg = (
            event_age_sum / event_count if event_count > 0 else 0.0
        )

        # System stress delta
        current_system_stress = self.model._get_system_stress()
        baseline_system_stress = 0.0  # Baseline typically zero for fresh scenarios
        system_stress_delta = current_system_stress - baseline_system_stress

        # Critical and affected node counts
        critical_nodes_count = self.model._get_affected_count()
        affected_nodes_count = sum(
            1
            for agent in self.model.infrastructure_agents.values()
            if agent.state.is_affected
        )

        return MesaDeltaResult(
            node_risk_delta=node_risk_delta,
            system_stress_delta=system_stress_delta,
            critical_nodes_count=critical_nodes_count,
            affected_nodes_count=affected_nodes_count,
            mean_recovery_progress=float(mean_recovery),
            cascade_depth_reached=max_cascade_depth,
            event_duration_avg=float(event_duration_avg),
        )

    def get_network_stress_map(self) -> Dict[str, float]:
        """
        Get spatial map of stress across network.

        Returns:
            Dict[node_id -> stress_score] for visualization
        """
        if not self.model:
            raise ValueError("Model not initialized.")

        stress_map = {}
        for node_id, agent in self.model.infrastructure_agents.items():
            # Combine disruption and risk into stress metric
            stress = (
                agent.state.disruption_level * 0.5
                + agent.state.risk_score * 0.5
            )
            stress_map[node_id] = max(0.0, min(1.0, stress))

        return stress_map

    def get_flow_rerouting_summary(self) -> Dict:
        """
        Get summary of flow rerouting decisions and congestion.

        Returns:
            Dict with reroute counts, congestion statistics
        """
        if not self.model:
            raise ValueError("Model not initialized.")

        total_reroutes = sum(flow.reroute_counter for flow in self.model.flow_agents)
        congestion_levels = [flow.congestion_level for flow in self.model.flow_agents]

        return {
            "total_reroutes": total_reroutes,
            "num_flows": len(self.model.flow_agents),
            "mean_congestion": float(np.mean(congestion_levels))
            if congestion_levels
            else 0.0,
            "max_congestion": float(np.max(congestion_levels))
            if congestion_levels
            else 0.0,
        }

    def reset(self):
        """Reset bridge state for new scenario."""
        self.model = None
        self.scenario_template = None
        self.baseline_risk_scores = {}
