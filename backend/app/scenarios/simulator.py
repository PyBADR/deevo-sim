"""
Scenario Simulator implementing the 10-step simulation pipeline.

Orchestrates the complete scenario simulation from baseline through impact assessment.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
from enum import Enum

from .templates import ScenarioTemplate
from .baseline import BaselineSnapshot, BaselineCaptureRequest, BaselineCaptureResult
from .shock import ShockEvent, ShockInjector, ShockApplicationResult, CascadeType

# Import actual math and physics modules
from app.intelligence.math.risk import compute_risk_score, RiskResult
from app.intelligence.math.propagation import propagate_risk, PropagationResult
from app.intelligence.math.exposure import compute_exposure
from app.intelligence.math.disruption import route_disruption_pressure
from app.intelligence.math.temporal import temporal_decay, freshness_score
from app.intelligence.math.confidence import compute_confidence
from app.intelligence.physics.threat_field import ThreatField, ThreatSource
from app.intelligence.physics.shockwave import ShockwaveEngine, ShockEvent as ShockwaveEvent
from app.intelligence.physics.pressure import PressureNode, accumulate_pressure
from app.intelligence.physics.system_stress import compute_system_stress


class SimulationStep(Enum):
    """Steps in the simulation pipeline."""
    BASELINE_CAPTURE = 1
    SHOCK_INJECTION = 2
    NETWORK_PROPAGATION = 3
    THREAT_FIELD_COMPUTATION = 4
    SHOCKWAVE_PROPAGATION = 5
    PRESSURE_REDISTRIBUTION = 6
    DISRUPTION_QUANTIFICATION = 7
    RISK_AGGREGATION = 8
    SYSTEM_STRESS_ASSESSMENT = 9
    IMPACT_FINALIZATION = 10


@dataclass
class SimulationStepResult:
    """Result of a single simulation step."""
    step: SimulationStep
    step_number: int
    success: bool
    duration_seconds: float
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScenarioSimulationResult:
    """Complete result of scenario simulation."""
    scenario_id: str
    scenario_template: ScenarioTemplate
    baseline_snapshot: BaselineSnapshot
    shock_applications: List[ShockApplicationResult]
    step_results: List[SimulationStepResult]
    final_risk_scores: Dict[str, float]
    risk_change_vector: np.ndarray
    system_stress_final: Dict[str, Any]
    critical_nodes_post_shock: List[str]
    recovery_time_estimate_hours: float
    simulation_duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ScenarioSimulator:
    """
    Scenario simulation engine implementing the 10-step deterministic pipeline.
    
    Pipeline:
    1. Baseline Capture: Snapshot system state pre-shock
    2. Shock Injection: Apply disruption to specified nodes with cascades
    3. Network Propagation: Risk spreading through network via matrix operations
    4. Threat Field Computation: Spatial threat intensity distribution
    5. Shockwave Propagation: Spatiotemporal shockwave dynamics
    6. Pressure Redistribution: Load redistribution through network
    7. Disruption Quantification: Impact quantification on flows and routes
    8. Risk Aggregation: Composite risk scoring with 8 components
    9. System Stress Assessment: Aggregate system-level stress evaluation
    10. Impact Finalization: Final metrics and recovery estimates
    """
    
    def __init__(self, 
                 adjacency_matrix: np.ndarray,
                 node_ids: List[str],
                 node_positions: Dict[str, Tuple[float, float]],
                 node_criticality: Dict[str, float]):
        """
        Initialize simulator.
        
        Args:
            adjacency_matrix: Network topology
            node_ids: List of node identifiers
            node_positions: Dict of node_id -> (latitude, longitude)
            node_criticality: Dict of node_id -> criticality score (0.0-1.0)
        """
        self.adjacency_matrix = adjacency_matrix
        self.node_ids = node_ids
        self.node_positions = node_positions
        self.node_criticality = node_criticality
        self.shock_injector = ShockInjector(adjacency_matrix, node_ids)
    
    def run_simulation(self, 
                      scenario_template: ScenarioTemplate,
                      baseline_snapshot: BaselineSnapshot,
                      scenario_id: str) -> ScenarioSimulationResult:
        """
        Run complete 10-step scenario simulation.
        
        Args:
            scenario_template: Template with shock parameters
            baseline_snapshot: Pre-shock system state
            scenario_id: Unique simulation identifier
            
        Returns:
            Complete simulation result with all metrics
        """
        start_time = datetime.utcnow()
        step_results = []
        current_risk_scores = baseline_snapshot.node_risk_scores.copy()
        
        try:
            # Step 1: Baseline Capture (already done, use provided snapshot)
            step1_result = SimulationStepResult(
                step=SimulationStep.BASELINE_CAPTURE,
                step_number=1,
                success=True,
                duration_seconds=0.0,
                description="Baseline snapshot provided",
                data={'baseline_snapshot_id': baseline_snapshot.snapshot_id}
            )
            step_results.append(step1_result)
            
            # Step 2: Shock Injection
            step2_result = self._step_shock_injection(scenario_template, baseline_snapshot)
            step_results.append(step2_result)
            shock_applications = step2_result.data.get('shock_applications', [])
            
            # Step 3: Network Propagation
            step3_result = self._step_network_propagation(
                baseline_snapshot,
                step2_result.data.get('shock_vector', np.zeros(len(self.node_ids))),
                scenario_template
            )
            step_results.append(step3_result)
            propagated_risks = step3_result.data.get('propagated_risks', current_risk_scores)
            
            # Step 4: Threat Field Computation
            step4_result = self._step_threat_field_computation(
                scenario_template,
                baseline_snapshot
            )
            step_results.append(step4_result)
            threat_intensities = step4_result.data.get('threat_intensities', {})
            
            # Step 5: Shockwave Propagation
            step5_result = self._step_shockwave_propagation(
                scenario_template,
                baseline_snapshot
            )
            step_results.append(step5_result)
            shockwave_impacts = step5_result.data.get('shockwave_impacts', {})
            
            # Step 6: Pressure Redistribution
            step6_result = self._step_pressure_redistribution(
                baseline_snapshot,
                propagated_risks
            )
            step_results.append(step6_result)
            pressure_scores = step6_result.data.get('pressure_scores', {})
            
            # Step 7: Disruption Quantification
            step7_result = self._step_disruption_quantification(
                baseline_snapshot,
                propagated_risks,
                scenario_template
            )
            step_results.append(step7_result)
            disruption_factors = step7_result.data.get('disruption_factors', {})
            
            # Step 8: Risk Aggregation
            step8_result = self._step_risk_aggregation(
                baseline_snapshot,
                propagated_risks,
                threat_intensities,
                pressure_scores,
                disruption_factors,
                scenario_template
            )
            step_results.append(step8_result)
            final_risk_scores = step8_result.data.get('final_risk_scores', {})
            
            # Step 9: System Stress Assessment
            step9_result = self._step_system_stress_assessment(
                final_risk_scores,
                pressure_scores,
                scenario_template
            )
            step_results.append(step9_result)
            system_stress_final = step9_result.data.get('system_stress', {})
            
            # Step 10: Impact Finalization
            step10_result = self._step_impact_finalization(
                final_risk_scores,
                baseline_snapshot,
                system_stress_final,
                scenario_template
            )
            step_results.append(step10_result)
            
            # Calculate metrics
            risk_change_vector = np.array([
                final_risk_scores.get(nid, 0.0) - baseline_snapshot.get_node_risk(nid)
                for nid in self.node_ids
            ])
            
            critical_nodes = [
                nid for nid, risk in final_risk_scores.items()
                if risk > 0.75
            ]
            
            recovery_estimate = self._estimate_recovery_time(
                final_risk_scores,
                baseline_snapshot,
                scenario_template
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return ScenarioSimulationResult(
                scenario_id=scenario_id,
                scenario_template=scenario_template,
                baseline_snapshot=baseline_snapshot,
                shock_applications=shock_applications,
                step_results=step_results,
                final_risk_scores=final_risk_scores,
                risk_change_vector=risk_change_vector,
                system_stress_final=system_stress_final,
                critical_nodes_post_shock=critical_nodes,
                recovery_time_estimate_hours=recovery_estimate,
                simulation_duration_seconds=duration,
                success=True
            )
        
        except Exception as e:
            end_time = datetime.utcnow()
            return ScenarioSimulationResult(
                scenario_id=scenario_id,
                scenario_template=scenario_template,
                baseline_snapshot=baseline_snapshot,
                shock_applications=[],
                step_results=step_results,
                final_risk_scores=current_risk_scores,
                risk_change_vector=np.zeros(len(self.node_ids)),
                system_stress_final={},
                critical_nodes_post_shock=[],
                recovery_time_estimate_hours=0.0,
                simulation_duration_seconds=(end_time - start_time).total_seconds(),
                success=False,
                error_message=str(e)
            )
    
    def _step_shock_injection(self, template: ScenarioTemplate, 
                             baseline: BaselineSnapshot) -> SimulationStepResult:
        """Step 2: Apply shocks to network nodes."""
        start = datetime.utcnow()
        
        try:
            shocks = []
            for node_id, severity in template.shock_event_locations.items():
                shock = ShockEvent(
                    node_id=node_id,
                    severity=min(1.0, severity * template.severity),
                    cascade_enabled=True,
                    cascade_depth=template.propagation_depth,
                    cascade_type=CascadeType.DIRECT_NEIGHBORS,
                    cascade_attenuation=template.propagation_coefficient
                )
                shocks.append(shock)
            
            applications = self.shock_injector.apply_multiple_shocks(shocks)
            shock_vector = self.shock_injector.create_shock_vector(shocks)
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.SHOCK_INJECTION,
                step_number=2,
                success=True,
                duration_seconds=duration,
                description=f"Applied {len(applications)} shocks with cascades",
                data={
                    'shock_applications': applications,
                    'shock_vector': shock_vector,
                    'affected_node_count': sum(r.affected_node_count for r in applications)
                }
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.SHOCK_INJECTION,
                step_number=2,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="Shock injection failed",
                error_message=str(e)
            )
    
    def _step_network_propagation(self, baseline: BaselineSnapshot,
                                 shock_vector: np.ndarray,
                                 template: ScenarioTemplate) -> SimulationStepResult:
        """Step 3: Propagate risk through network using math/propagation.py."""
        start = datetime.utcnow()
        
        try:
            risk_vector = baseline.get_risk_vector()
            
            # Use actual propagation module
            result = propagate_risk(
                adjacency_matrix=baseline.get_adjacency_matrix(),
                risk_vector=risk_vector,
                shock_vector=shock_vector,
                alpha=template.propagation_coefficient,
                beta=1.0 - template.propagation_coefficient,
                max_iterations=20,
                convergence_threshold=1e-6
            )
            
            # Convert back to node-indexed dict
            propagated_risks = {
                node_id: float(result.final_risk[idx])
                for idx, node_id in enumerate(baseline.node_ids)
            }
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.NETWORK_PROPAGATION,
                step_number=3,
                success=True,
                duration_seconds=duration,
                description=f"Risk propagated {result.steps_to_converge} iterations",
                data={
                    'propagated_risks': propagated_risks,
                    'iterations': result.steps_to_converge,
                    'converged': result.converged
                }
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.NETWORK_PROPAGATION,
                step_number=3,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="Network propagation failed",
                error_message=str(e)
            )
    
    def _step_threat_field_computation(self, template: ScenarioTemplate,
                                      baseline: BaselineSnapshot) -> SimulationStepResult:
        """Step 4: Compute threat field from shock sources."""
        start = datetime.utcnow()
        
        try:
            threat_field = ThreatField(decay_lambda=0.3)
            threat_intensities = {}
            
            for node_id, shock_severity in template.shock_event_locations.items():
                if node_id in self.node_positions:
                    lat, lon = self.node_positions[node_id]
                    source = ThreatSource(
                        lat=lat,
                        lon=lon,
                        magnitude=shock_severity,
                        decay_lambda=0.3,
                        event_id=node_id
                    )
                    threat_field.add_source(source)
            
            # Evaluate threat at all nodes
            for node_id in self.node_ids:
                if node_id in self.node_positions:
                    lat, lon = self.node_positions[node_id]
                    intensity = threat_field.evaluate(lat, lon)
                    threat_intensities[node_id] = float(intensity)
                else:
                    threat_intensities[node_id] = 0.0
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.THREAT_FIELD_COMPUTATION,
                step_number=4,
                success=True,
                duration_seconds=duration,
                description=f"Computed threat field from {len(template.shock_event_locations)} sources",
                data={'threat_intensities': threat_intensities}
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.THREAT_FIELD_COMPUTATION,
                step_number=4,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="Threat field computation failed",
                error_message=str(e)
            )
    
    def _step_shockwave_propagation(self, template: ScenarioTemplate,
                                   baseline: BaselineSnapshot) -> SimulationStepResult:
        """Step 5: Model shockwave spatiotemporal propagation."""
        start = datetime.utcnow()
        
        try:
            engine = ShockwaveEngine()
            shockwave_impacts = {}
            
            for node_id, shock_severity in template.shock_event_locations.items():
                if node_id in self.node_positions:
                    lat, lon = self.node_positions[node_id]
                    shockwave = ShockwaveEvent(
                        origin_lat=lat,
                        origin_lon=lon,
                        magnitude=shock_severity,
                        propagation_speed_kmh=500.0,
                        start_time=datetime.utcnow()
                    )
                    engine.add_shockwave(shockwave)
            
            # Evaluate shockwave at all nodes
            current_time = datetime.utcnow()
            for node_id in self.node_ids:
                if node_id in self.node_positions:
                    lat, lon = self.node_positions[node_id]
                    impact = engine.evaluate_impact(lat, lon, current_time)
                    shockwave_impacts[node_id] = float(impact)
                else:
                    shockwave_impacts[node_id] = 0.0
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.SHOCKWAVE_PROPAGATION,
                step_number=5,
                success=True,
                duration_seconds=duration,
                description=f"Modeled shockwave propagation with {len(template.shock_event_locations)} sources",
                data={'shockwave_impacts': shockwave_impacts}
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.SHOCKWAVE_PROPAGATION,
                step_number=5,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="Shockwave propagation failed",
                error_message=str(e)
            )
    
    def _step_pressure_redistribution(self, baseline: BaselineSnapshot,
                                     risk_scores: Dict[str, float]) -> SimulationStepResult:
        """Step 6: Redistribute load pressures through network."""
        start = datetime.utcnow()
        
        try:
            pressure_scores = {}
            
            for node_id in self.node_ids:
                node = PressureNode(
                    node_id=node_id,
                    node_type="infrastructure",
                    base_capacity=1.0,
                    current_load=baseline.node_load_factors.get(node_id, 0.5)
                )
                
                # Apply load redistribution based on risk
                risk_factor = risk_scores.get(node_id, 0.0)
                accumulated_pressure = accumulate_pressure(
                    node=node,
                    adjacent_pressures=[],
                    reroute_factor=1.0 + risk_factor * 0.5
                )
                
                pressure_scores[node_id] = accumulated_pressure
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.PRESSURE_REDISTRIBUTION,
                step_number=6,
                success=True,
                duration_seconds=duration,
                description="Redistributed pressures across network",
                data={'pressure_scores': pressure_scores}
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.PRESSURE_REDISTRIBUTION,
                step_number=6,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="Pressure redistribution failed",
                error_message=str(e)
            )
    
    def _step_disruption_quantification(self, baseline: BaselineSnapshot,
                                       risk_scores: Dict[str, float],
                                       template: ScenarioTemplate) -> SimulationStepResult:
        """Step 7: Quantify disruption impacts on flows."""
        start = datetime.utcnow()
        
        try:
            disruption_factors = {}
            
            for node_id in self.node_ids:
                risk = risk_scores.get(node_id, 0.0)
                load = baseline.node_load_factors.get(node_id, 0.5)
                vulnerability = 1.0 - baseline.node_network_centrality.get(node_id, 0.5)
                
                # Compute disruption pressure
                pressure = route_disruption_pressure(
                    flow_volume=load,
                    vulnerability=vulnerability,
                    threat_intensity=risk * template.severity
                )
                
                disruption_factors[node_id] = min(1.0, pressure)
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.DISRUPTION_QUANTIFICATION,
                step_number=7,
                success=True,
                duration_seconds=duration,
                description="Quantified disruption impacts",
                data={'disruption_factors': disruption_factors}
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.DISRUPTION_QUANTIFICATION,
                step_number=7,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="Disruption quantification failed",
                error_message=str(e)
            )
    
    def _step_risk_aggregation(self, baseline: BaselineSnapshot,
                              propagated_risks: Dict[str, float],
                              threat_intensities: Dict[str, float],
                              pressure_scores: Dict[str, float],
                              disruption_factors: Dict[str, float],
                              template: ScenarioTemplate) -> SimulationStepResult:
        """Step 8: Aggregate composite risk scores using 8 components."""
        start = datetime.utcnow()
        
        try:
            final_risk_scores = {}
            
            for node_id in self.node_ids:
                # Combine components: propagation, threat, pressure, disruption
                base_risk = propagated_risks.get(node_id, 0.0)
                threat = threat_intensities.get(node_id, 0.0)
                pressure = pressure_scores.get(node_id, 0.0)
                disruption = disruption_factors.get(node_id, 0.0)
                
                # Use actual risk computation from math module
                risk_result = compute_risk_score(
                    event_severity=base_risk * template.severity,
                    source_confidence=template.confidence_baseline,
                    spatial_proximity=threat,
                    network_centrality=baseline.node_network_centrality.get(node_id, 0.5),
                    route_dependency=baseline.node_criticality.get(node_id, 0.5),
                    temporal_recency=1.0,
                    congestion_pressure=pressure,
                    exposure_sensitivity=compute_exposure(
                        value_at_risk=baseline.node_criticality.get(node_id, 0.5),
                        dependency_weight=0.6,
                        operational_criticality=0.4
                    )
                )
                
                final_risk_scores[node_id] = risk_result.score
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.RISK_AGGREGATION,
                step_number=8,
                success=True,
                duration_seconds=duration,
                description="Aggregated composite risk scores",
                data={'final_risk_scores': final_risk_scores}
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.RISK_AGGREGATION,
                step_number=8,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="Risk aggregation failed",
                error_message=str(e)
            )
    
    def _step_system_stress_assessment(self, final_risks: Dict[str, float],
                                      pressure_scores: Dict[str, float],
                                      template: ScenarioTemplate) -> SimulationStepResult:
        """Step 9: Assess system-level stress."""
        start = datetime.utcnow()
        
        try:
            # Use actual system stress module
            result = compute_system_stress(
                pressure_scores=list(pressure_scores.values()),
                congestion_scores=[1.0 - v for v in pressure_scores.values()],
                unresolved_disruptions=sum(1 for r in final_risks.values() if r > 0.5),
                uncertainty_level=1.0 - template.confidence_baseline
            )
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.SYSTEM_STRESS_ASSESSMENT,
                step_number=9,
                success=True,
                duration_seconds=duration,
                description=f"System stress level: {result.level.value}",
                data={'system_stress': {
                    'stress_score': result.stress_score,
                    'level': result.level.value,
                    'narrative': result.narrative
                }}
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.SYSTEM_STRESS_ASSESSMENT,
                step_number=9,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="System stress assessment failed",
                error_message=str(e)
            )
    
    def _step_impact_finalization(self, final_risks: Dict[str, float],
                                 baseline: BaselineSnapshot,
                                 system_stress: Dict[str, Any],
                                 template: ScenarioTemplate) -> SimulationStepResult:
        """Step 10: Finalize impact metrics."""
        start = datetime.utcnow()
        
        try:
            critical_count = sum(1 for r in final_risks.values() if r > 0.75)
            high_count = sum(1 for r in final_risks.values() if 0.5 < r <= 0.75)
            
            duration = (datetime.utcnow() - start).total_seconds()
            
            return SimulationStepResult(
                step=SimulationStep.IMPACT_FINALIZATION,
                step_number=10,
                success=True,
                duration_seconds=duration,
                description="Impact assessment finalized",
                data={
                    'critical_nodes': critical_count,
                    'high_risk_nodes': high_count,
                    'avg_risk_increase': float(np.mean([
                        final_risks.get(nid, 0.0) - baseline.get_node_risk(nid)
                        for nid in baseline.node_ids
                    ]))
                }
            )
        except Exception as e:
            return SimulationStepResult(
                step=SimulationStep.IMPACT_FINALIZATION,
                step_number=10,
                success=False,
                duration_seconds=(datetime.utcnow() - start).total_seconds(),
                description="Impact finalization failed",
                error_message=str(e)
            )
    
    def _estimate_recovery_time(self, final_risks: Dict[str, float],
                               baseline: BaselineSnapshot,
                               template: ScenarioTemplate) -> float:
        """Estimate recovery time based on disruption severity."""
        max_disruption = max(final_risks.values()) if final_risks else 0.0
        
        # Recovery time proportional to max disruption and scenario duration
        recovery_hours = (max_disruption ** 1.5) * template.duration_hours * 2
        
        return min(recovery_hours, 336.0)  # Cap at 2 weeks
