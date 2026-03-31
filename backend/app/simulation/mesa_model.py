"""
Mesa Agent-Based Model Implementation for GCC Infrastructure Simulation

Implements core agents (InfrastructureAgent, EventAgent, FlowAgent) and the
GCCModel orchestrator for spatial-temporal disruption propagation and impact
assessment using Mesa 3.x SimultaneousActivation scheduler and DataCollector.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
import math
import numpy as np

from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

from app.intelligence.math_core.state_vector import (
    EntityStateVector,
    compute_state_vector,
)
from app.intelligence.physics.system_stress import compute_system_stress


class AgentType(Enum):
    """Agent type enumeration."""
    INFRASTRUCTURE = "infrastructure"
    EVENT = "event"
    FLOW = "flow"


@dataclass
class AgentState:
    """Mutable agent state container."""
    risk_score: float = 0.0
    disruption_level: float = 0.0
    resilience_capacity: float = 0.9
    criticality: float = 0.5
    exposure: float = 0.5
    uncertainty: float = 0.3
    recovery_progress: float = 0.0
    neighbors: List[int] = field(default_factory=list)
    is_affected: bool = False
    shock_severity: float = 0.0
    cascade_depth: int = 0


class InfrastructureAgent(Agent):
    """
    Represents critical infrastructure node (port, airport, pipeline, etc.).
    Maintains state vector, risk dynamics, recovery progress, and cascade effects.
    """

    def __init__(
        self,
        model: "GCCModel",
        node_id: str,
        node_type: str,
        criticality: float = 0.5,
        exposure: float = 0.5,
        lat: float = 0.0,
        lon: float = 0.0,
    ):
        """
        Initialize infrastructure agent.

        Args:
            model: Parent GCCModel instance
            node_id: Unique infrastructure identifier
            node_type: Type of infrastructure (port, airport, pipeline, etc.)
            criticality: [0,1] criticality score
            exposure: [0,1] exposure to disruption
            lat: Latitude coordinate
            lon: Longitude coordinate
        """
        super().__init__(model)
        self.node_id = node_id
        self.node_type = node_type
        self.lat = lat
        self.lon = lon
        self.agent_type = AgentType.INFRASTRUCTURE

        self.state = AgentState(
            criticality=max(0.0, min(1.0, criticality)),
            exposure=max(0.0, min(1.0, exposure)),
        )

    def step(self):
        """Execute infrastructure agent step: update risk, propagate cascade, recover."""
        # Update internal state vector based on current disruption/resilience
        self._update_state_vector()

        # Propagate disruption to neighboring nodes if cascading is enabled
        if self.state.is_affected and self.state.cascade_depth > 0:
            self._propagate_cascade()

        # Recover progressively toward baseline resilience
        self._recover()

    def _update_state_vector(self):
        """Compute and update entity state vector from current conditions."""
        resilience = self.state.resilience_capacity * (1.0 - self.state.recovery_progress)
        disruption = self.state.disruption_level
        criticality = self.state.criticality
        exposure = self.state.exposure
        uncertainty = self.state.uncertainty
        shock_susceptibility = self.state.shock_severity * exposure

        state_vec = compute_state_vector(
            resilience=resilience,
            disruption=disruption,
            criticality=criticality,
            exposure=exposure,
            uncertainty=uncertainty,
            shock_susceptibility=shock_susceptibility,
        )

        # Update risk score from state vector profile
        risk_profile = state_vec.compute_risk_profile()
        self.state.risk_score = risk_profile.get("overall_risk", 0.0)

    def _propagate_cascade(self):
        """Propagate cascading disruption to neighboring infrastructure nodes."""
        neighbors = self.state.neighbors
        cascade_attenuation = self.model.cascade_attenuation
        cascade_depth = self.state.cascade_depth

        for neighbor_id in neighbors:
            if neighbor_id not in self.model.schedule._agents:
                continue

            neighbor = self.model.schedule._agents[neighbor_id]
            if not isinstance(neighbor, InfrastructureAgent):
                continue

            # Attenuate shock severity as it propagates
            attenuated_severity = (
                self.state.shock_severity * (cascade_attenuation ** cascade_depth)
            )

            if attenuated_severity > 0.01:  # Only propagate if above threshold
                neighbor.state.is_affected = True
                neighbor.state.shock_severity = max(
                    neighbor.state.shock_severity, attenuated_severity
                )
                neighbor.state.disruption_level = max(
                    neighbor.state.disruption_level, attenuated_severity * 0.8
                )
                neighbor.state.cascade_depth = max(
                    neighbor.state.cascade_depth, cascade_depth - 1
                )

    def _recover(self):
        """Advance recovery toward baseline resilience."""
        recovery_rate = 0.05  # 5% per step toward baseline
        self.state.recovery_progress = min(
            1.0, self.state.recovery_progress + recovery_rate
        )
        self.state.disruption_level = max(
            0.0, self.state.disruption_level - recovery_rate
        )
        self.state.shock_severity = max(
            0.0, self.state.shock_severity - recovery_rate
        )


class EventAgent(Agent):
    """
    Represents a disruption event (shock, emergency, incident).
    Manages event decay, spatial spread, and interaction with infrastructure.
    """

    def __init__(
        self,
        model: "GCCModel",
        event_id: str,
        event_type: str,
        severity: float,
        primary_node_id: str,
        duration_steps: int = 10,
        spatial_radius: float = 50.0,
    ):
        """
        Initialize event agent.

        Args:
            model: Parent GCCModel instance
            event_id: Unique event identifier
            event_type: Type of event (shock, blockade, etc.)
            severity: [0,1] initial severity
            primary_node_id: Primary node affected by event
            duration_steps: Number of steps until event decay
            spatial_radius: Radius of effect in km
        """
        super().__init__(model)
        self.event_id = event_id
        self.event_type = event_type
        self.primary_node_id = primary_node_id
        self.agent_type = AgentType.EVENT

        self.severity = max(0.0, min(1.0, severity))
        self.duration_steps = duration_steps
        self.spatial_radius = spatial_radius
        self.age = 0

    def step(self):
        """Execute event agent step: age event, decay severity, remove if expired."""
        self.age += 1

        # Exponential decay of event severity over time
        decay_rate = 0.1
        self.severity = max(0.0, self.severity * (1.0 - decay_rate))

        # Remove event if expired or decayed
        if self.age >= self.duration_steps or self.severity < 0.01:
            self.model.event_agents.remove(self)

    def get_affected_nodes(self) -> List[str]:
        """Return list of infrastructure node IDs within spatial radius."""
        affected = []
        primary = self.model.node_locations.get(self.primary_node_id)

        if not primary:
            return affected

        primary_lat, primary_lon = primary

        for node_id, (lat, lon) in self.model.node_locations.items():
            distance = self._haversine_distance(primary_lat, primary_lon, lat, lon)
            if distance <= self.spatial_radius:
                affected.append(node_id)

        return affected

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute great-circle distance between two points in km."""
        R = 6371  # Earth radius in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (
            math.sin(dLat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dLon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return R * c


class FlowAgent(Agent):
    """
    Represents movement of cargo/traffic through infrastructure network.
    Manages routing decisions, congestion, and rerouting around disruptions.
    """

    def __init__(
        self,
        model: "GCCModel",
        flow_id: str,
        origin_node: str,
        destination_node: str,
        flow_volume: float,
        flow_type: str = "cargo",
    ):
        """
        Initialize flow agent.

        Args:
            model: Parent GCCModel instance
            flow_id: Unique flow identifier
            origin_node: Source node ID
            destination_node: Destination node ID
            flow_volume: [0,1] normalized flow volume
            flow_type: Type of flow (cargo, traffic, etc.)
        """
        super().__init__(model)
        self.flow_id = flow_id
        self.origin_node = origin_node
        self.destination_node = destination_node
        self.flow_volume = max(0.0, min(1.0, flow_volume))
        self.flow_type = flow_type
        self.agent_type = AgentType.FLOW

        self.current_route: List[str] = []
        self.congestion_level = 0.0
        self.reroute_counter = 0

    def step(self):
        """Execute flow agent step: evaluate route, assess congestion, reroute if needed."""
        # Compute congestion on current path based on infrastructure disruption
        self._update_congestion()

        # Decide whether to reroute based on congestion and alternatives
        if self.congestion_level > 0.6:
            self._attempt_reroute()

    def _update_congestion(self):
        """Assess congestion on current route from infrastructure state."""
        if not self.current_route:
            self.congestion_level = 0.0
            return

        total_disruption = 0.0
        for node_id in self.current_route:
            if node_id in self.model.schedule._agents:
                agent = self.model.schedule._agents[node_id]
                if isinstance(agent, InfrastructureAgent):
                    total_disruption += agent.state.disruption_level

        # Average disruption across route segments
        self.congestion_level = (
            total_disruption / len(self.current_route)
            if self.current_route
            else 0.0
        )

    def _attempt_reroute(self):
        """Reroute flow around disrupted infrastructure."""
        # Simple greedy reroute: find least-disrupted path (simplified)
        self.reroute_counter += 1

        # In full implementation, use A* or Dijkstra with disruption costs
        # For now, mark reroute occurred and reduce congestion slightly
        self.congestion_level = max(0.3, self.congestion_level - 0.2)


class GCCModel(Model):
    """
    Master orchestrator for GCC infrastructure agent-based simulation.

    Manages scheduler, data collection, scenario injection, and aggregation
    of results from multiple agent types into unified system stress metrics.
    """

    def __init__(
        self,
        node_locations: Dict[str, Tuple[float, float]],
        adjacency_matrix: Dict[str, List[str]],
        node_criticality: Dict[str, float],
        node_exposure: Dict[str, float],
        cascade_attenuation: float = 0.7,
        max_cascade_depth: int = 3,
    ):
        """
        Initialize GCCModel.

        Args:
            node_locations: Dict[node_id -> (lat, lon)]
            adjacency_matrix: Dict[node_id -> List[neighbor_ids]]
            node_criticality: Dict[node_id -> criticality_score]
            node_exposure: Dict[node_id -> exposure_score]
            cascade_attenuation: Attenuation factor for cascading shocks (0.0-1.0)
            max_cascade_depth: Maximum depth for cascade propagation
        """
        super().__init__()

        self.node_locations = node_locations
        self.adjacency_matrix = adjacency_matrix
        self.node_criticality = node_criticality
        self.node_exposure = node_exposure
        self.cascade_attenuation = cascade_attenuation
        self.max_cascade_depth = max_cascade_depth

        # Core scheduling and data collection
        self.schedule = SimultaneousActivation(self)
        self.datacollector = DataCollector(
            model_reporters={
                "mean_risk_score": self._get_mean_risk,
                "max_risk_score": self._get_max_risk,
                "affected_node_count": self._get_affected_count,
                "system_stress": self._get_system_stress,
            },
            agent_reporters={"risk_score": "state" if hasattr(self, "state") else None},
        )

        self.infrastructure_agents: Dict[str, InfrastructureAgent] = {}
        self.event_agents: List[EventAgent] = []
        self.flow_agents: List[FlowAgent] = []

        # Initialize infrastructure agents
        self._initialize_infrastructure()

    def _initialize_infrastructure(self):
        """Create infrastructure agents for all nodes."""
        for node_id in self.node_locations:
            lat, lon = self.node_locations[node_id]
            criticality = self.node_criticality.get(node_id, 0.5)
            exposure = self.node_exposure.get(node_id, 0.5)

            agent = InfrastructureAgent(
                model=self,
                node_id=node_id,
                node_type="infrastructure",
                criticality=criticality,
                exposure=exposure,
                lat=lat,
                lon=lon,
            )

            # Set neighbors from adjacency matrix
            agent.state.neighbors = self.adjacency_matrix.get(node_id, [])

            self.infrastructure_agents[node_id] = agent
            self.schedule.add(agent)

    def inject_shock(
        self,
        shock_node_id: str,
        severity: float,
        cascade_enabled: bool = True,
        cascade_depth: int = 2,
        cascade_type: str = "geometric",
    ):
        """
        Inject a shock event into the model at specified node.

        Args:
            shock_node_id: Target node for shock
            severity: [0,1] shock severity
            cascade_enabled: Whether cascading is enabled
            cascade_depth: Maximum depth for cascade propagation
            cascade_type: Type of cascade (geometric, linear, etc.)
        """
        if shock_node_id not in self.infrastructure_agents:
            return

        # Apply direct shock to primary node
        infra_agent = self.infrastructure_agents[shock_node_id]
        infra_agent.state.is_affected = True
        infra_agent.state.shock_severity = max(0.0, min(1.0, severity))
        infra_agent.state.disruption_level = max(0.0, min(1.0, severity * 0.9))

        if cascade_enabled:
            infra_agent.state.cascade_depth = min(
                cascade_depth, self.max_cascade_depth
            )

        # Create event agent to track event duration and decay
        event = EventAgent(
            model=self,
            event_id=f"event_{shock_node_id}_{self.schedule.steps}",
            event_type="shock",
            severity=severity,
            primary_node_id=shock_node_id,
            duration_steps=20,
        )
        self.event_agents.append(event)
        self.schedule.add(event)

    def add_flow(
        self,
        flow_id: str,
        origin: str,
        destination: str,
        volume: float,
        flow_type: str = "cargo",
    ):
        """Add a flow agent to the model."""
        flow = FlowAgent(
            model=self,
            flow_id=flow_id,
            origin_node=origin,
            destination_node=destination,
            flow_volume=volume,
            flow_type=flow_type,
        )
        self.flow_agents.append(flow)
        self.schedule.add(flow)

    def step(self):
        """Execute one simulation step."""
        self.datacollector.collect(self)
        self.schedule.step()

    def run_steps(self, num_steps: int):
        """Run simulation for specified number of steps."""
        for _ in range(num_steps):
            self.step()

    def _get_mean_risk(self) -> float:
        """Compute mean risk score across all infrastructure agents."""
        if not self.infrastructure_agents:
            return 0.0
        risk_scores = [
            agent.state.risk_score for agent in self.infrastructure_agents.values()
        ]
        return float(np.mean(risk_scores)) if risk_scores else 0.0

    def _get_max_risk(self) -> float:
        """Compute maximum risk score across all infrastructure agents."""
        if not self.infrastructure_agents:
            return 0.0
        risk_scores = [
            agent.state.risk_score for agent in self.infrastructure_agents.values()
        ]
        return float(np.max(risk_scores)) if risk_scores else 0.0

    def _get_affected_count(self) -> int:
        """Count number of affected infrastructure nodes."""
        return sum(
            1
            for agent in self.infrastructure_agents.values()
            if agent.state.is_affected
        )

    def _get_system_stress(self) -> float:
        """Compute system-wide stress metric."""
        # Aggregate pressure, congestion, disruptions, uncertainty
        pressures = []
        congestion_scores = []
        disruptions = []
        uncertainties = []

        for agent in self.infrastructure_agents.values():
            pressures.append(agent.state.risk_score)
            disruptions.append(agent.state.disruption_level)
            uncertainties.append(agent.state.uncertainty)

        for flow in self.flow_agents:
            congestion_scores.append(flow.congestion_level)

        avg_pressure = float(np.mean(pressures)) if pressures else 0.0
        avg_congestion = float(np.mean(congestion_scores)) if congestion_scores else 0.0
        unresolved_disruptions = sum(disruptions)
        avg_uncertainty = float(np.mean(uncertainties)) if uncertainties else 0.0

        stress_result = compute_system_stress(
            pressures=[avg_pressure] * len(self.infrastructure_agents),
            congestion_scores=[avg_congestion] * len(self.flow_agents)
            if self.flow_agents
            else [],
            unresolved_disruptions=unresolved_disruptions,
            uncertainty=avg_uncertainty,
        )

        return stress_result.stress_score

    def get_results(self) -> Dict:
        """
        Extract final model results.

        Returns dict with:
        - final_risk_scores: Dict[node_id -> risk_score]
        - critical_nodes: List of highly affected node IDs
        - system_stress: Final system stress metric
        - mean_recovery_progress: Average recovery progress
        """
        final_risk_scores = {
            node_id: agent.state.risk_score
            for node_id, agent in self.infrastructure_agents.items()
        }

        critical_nodes = [
            node_id
            for node_id, agent in self.infrastructure_agents.items()
            if agent.state.risk_score > 0.7
        ]

        recovery_progress_list = [
            agent.state.recovery_progress
            for agent in self.infrastructure_agents.values()
        ]
        mean_recovery = (
            float(np.mean(recovery_progress_list))
            if recovery_progress_list
            else 0.0
        )

        return {
            "final_risk_scores": final_risk_scores,
            "critical_nodes": critical_nodes,
            "system_stress": self._get_system_stress(),
            "mean_recovery_progress": mean_recovery,
            "total_steps": self.schedule.steps,
            "affected_node_count": self._get_affected_count(),
        }
