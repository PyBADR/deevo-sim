"""
Regression test suite for seeded GCC scenario execution.
Validates all 15 predefined scenarios against expected outputs using ScenarioRunner.
"""

import pytest
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scenarios.runner import ScenarioRunner
from seeds.scenario_seeds import list_scenario_ids

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@pytest.fixture
def scenario_runner():
    """Initialize ScenarioRunner with expected outputs."""
    expected_outputs_dir = Path(__file__).parent.parent / "seeds" / "expected_outputs"
    return ScenarioRunner(expected_outputs_dir=str(expected_outputs_dir))


class TestScenarioExecution:
    """Test execution and validation of all 15 seeded scenarios."""

    def test_hormuz_closure_affects_gulf_ports(self, scenario_runner):
        """Test hormuz_closure scenario - NAVAL_BLOCKADE affecting critical maritime corridor."""
        result = scenario_runner.run_seeded_scenario("hormuz_closure")
        
        assert result.scenario_id == "hormuz_closure"
        assert 0.30 <= result.risk_increase <= 0.55
        assert result.time_horizon_status == 168
        assert result.affected_ports >= 3
        assert result.affected_corridors >= 2
        assert 2 <= result.cascade_depth <= 4
        
        validation_passed, errors = scenario_runner.validate_against_expected("hormuz_closure", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_gcc_airspace_closure_reroutes_flights(self, scenario_runner):
        """Test gcc_airspace_closure scenario - AIRSPACE_CLOSURE disruption."""
        result = scenario_runner.run_seeded_scenario("gcc_airspace_closure")
        
        assert result.scenario_id == "gcc_airspace_closure"
        assert 0.25 <= result.risk_increase <= 0.48
        assert result.time_horizon_status == 96
        assert result.affected_airports >= 3
        assert result.confidence_adjustment < 0
        assert 1 <= result.cascade_depth <= 3
        
        validation_passed, errors = scenario_runner.validate_against_expected("gcc_airspace_closure", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_missile_escalation_damages_infrastructure(self, scenario_runner):
        """Test missile_escalation scenario - MISSILE_THREAT direct impact."""
        result = scenario_runner.run_seeded_scenario("missile_escalation")
        
        assert result.scenario_id == "missile_escalation"
        assert 0.32 <= result.risk_increase <= 0.58
        assert result.time_horizon_status == 72
        assert result.nodes_affected_total >= 5
        assert result.critical_nodes_impacted > 0
        assert 2 <= result.cascade_depth <= 4
        
        validation_passed, errors = scenario_runner.validate_against_expected("missile_escalation", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_airport_shutdown_disrupts_aviation(self, scenario_runner):
        """Test airport_shutdown scenario - AIRPORT_SHUTDOWN cascading effects."""
        result = scenario_runner.run_seeded_scenario("airport_shutdown")
        
        assert result.scenario_id == "airport_shutdown"
        assert 0.28 <= result.risk_increase <= 0.52
        assert result.time_horizon_status == 48
        assert result.affected_airports >= 2
        assert result.logistics_delay_hours > 0
        assert 1 <= result.cascade_depth <= 3
        
        validation_passed, errors = scenario_runner.validate_against_expected("airport_shutdown", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_port_congestion_delays_logistics(self, scenario_runner):
        """Test port_congestion scenario - PORT_DAMAGE with extended impact."""
        result = scenario_runner.run_seeded_scenario("port_congestion")
        
        assert result.scenario_id == "port_congestion"
        assert 0.18 <= result.risk_increase <= 0.38
        assert result.time_horizon_status == 336
        assert result.affected_ports >= 3
        assert result.logistics_delay_hours >= 50
        assert 2 <= result.cascade_depth <= 3
        
        validation_passed, errors = scenario_runner.validate_against_expected("port_congestion", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_conflict_spillover_multi_domain(self, scenario_runner):
        """Test conflict_spillover scenario - CONFLICT_SPILLOVER affecting multiple domains."""
        result = scenario_runner.run_seeded_scenario("conflict_spillover")
        
        assert result.scenario_id == "conflict_spillover"
        assert 0.30 <= result.risk_increase <= 0.52
        assert result.time_horizon_status == 240
        assert result.affected_ports >= 2
        assert result.affected_airports >= 2
        assert 2 <= result.cascade_depth <= 4
        
        validation_passed, errors = scenario_runner.validate_against_expected("conflict_spillover", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_maritime_risk_surge_insurance(self, scenario_runner):
        """Test maritime_risk_surge scenario - VESSEL_DIVERSION with insurance impacts."""
        result = scenario_runner.run_seeded_scenario("maritime_risk_surge")
        
        assert result.scenario_id == "maritime_risk_surge"
        assert 0.22 <= result.risk_increase <= 0.42
        assert result.time_horizon_status == 504
        assert result.affected_corridors >= 2
        assert result.insurance_surge > 0
        assert 2 <= result.cascade_depth <= 3
        
        validation_passed, errors = scenario_runner.validate_against_expected("maritime_risk_surge", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_combined_disruption_cascades(self, scenario_runner):
        """Test combined_disruption scenario - Combined geopolitical and maritime impacts."""
        result = scenario_runner.run_seeded_scenario("combined_disruption")
        
        assert result.scenario_id == "combined_disruption"
        assert 0.38 <= result.risk_increase <= 0.62
        assert result.time_horizon_status == 168
        assert result.affected_ports >= 3
        assert result.affected_airports >= 2
        assert result.affected_corridors >= 2
        assert 3 <= result.cascade_depth <= 5
        assert result.nodes_affected_total >= 10
        
        validation_passed, errors = scenario_runner.validate_against_expected("combined_disruption", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_insurance_surge_rate_spike(self, scenario_runner):
        """Test insurance_surge scenario - INSURANCE_RATE_SPIKE systemic impact."""
        result = scenario_runner.run_seeded_scenario("insurance_surge")
        
        assert result.scenario_id == "insurance_surge"
        assert 0.16 <= result.risk_increase <= 0.35
        assert result.time_horizon_status == 240
        assert result.insurance_surge >= 0.15
        assert result.nodes_affected_total >= 5
        assert 1 <= result.cascade_depth <= 2
        
        validation_passed, errors = scenario_runner.validate_against_expected("insurance_surge", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_executive_board_economic_pressure(self, scenario_runner):
        """Test executive_board scenario - ECONOMIC_PRESSURE lowest severity."""
        result = scenario_runner.run_seeded_scenario("executive_board")
        
        assert result.scenario_id == "executive_board"
        assert 0.12 <= result.risk_increase <= 0.28
        assert result.time_horizon_status == 720
        assert result.nodes_affected_total >= 5
        assert 1 <= result.cascade_depth <= 2
        
        validation_passed, errors = scenario_runner.validate_against_expected("executive_board", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_red_sea_diversion_corridor(self, scenario_runner):
        """Test red_sea_diversion scenario - CORRIDOR_RESTRICTION maritime route diversion."""
        result = scenario_runner.run_seeded_scenario("red_sea_diversion")
        
        assert result.scenario_id == "red_sea_diversion"
        assert 0.25 <= result.risk_increase <= 0.45
        assert result.time_horizon_status == 336
        assert result.affected_corridors >= 2
        assert result.logistics_delay_hours > 0
        assert 2 <= result.cascade_depth <= 3
        
        validation_passed, errors = scenario_runner.validate_against_expected("red_sea_diversion", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_dual_disruption_maritime_air(self, scenario_runner):
        """Test dual_disruption scenario - VESSEL_DIVERSION and FLIGHT_DIVERSION."""
        result = scenario_runner.run_seeded_scenario("dual_disruption")
        
        assert result.scenario_id == "dual_disruption"
        assert 0.28 <= result.risk_increase <= 0.50
        assert result.time_horizon_status == 240
        assert result.affected_ports >= 2
        assert result.affected_airports >= 2
        assert 2 <= result.cascade_depth <= 3
        
        validation_passed, errors = scenario_runner.validate_against_expected("dual_disruption", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_oil_corridor_risk_fuel(self, scenario_runner):
        """Test oil_corridor_risk scenario - FUEL_SHORTAGE cascading effects."""
        result = scenario_runner.run_seeded_scenario("oil_corridor_risk")
        
        assert result.scenario_id == "oil_corridor_risk"
        assert 0.20 <= result.risk_increase <= 0.40
        assert result.time_horizon_status == 672
        assert result.affected_corridors >= 2
        assert result.nodes_affected_total >= 6
        assert 2 <= result.cascade_depth <= 3
        
        validation_passed, errors = scenario_runner.validate_against_expected("oil_corridor_risk", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_false_signal_minimal_impact(self, scenario_runner):
        """Test false_signal scenario - Minimal cascading impact false alarm."""
        result = scenario_runner.run_seeded_scenario("false_signal")
        
        assert result.scenario_id == "false_signal"
        assert 0.05 <= result.risk_increase <= 0.18
        assert result.time_horizon_status == 24
        assert result.nodes_affected_total >= 2
        assert 0 <= result.cascade_depth <= 1
        
        validation_passed, errors = scenario_runner.validate_against_expected("false_signal", result)
        assert validation_passed, f"Validation errors: {errors}"

    def test_cascading_reroute_secondary_effects(self, scenario_runner):
        """Test cascading_reroute scenario - Secondary rerouting cascades."""
        result = scenario_runner.run_seeded_scenario("cascading_reroute")
        
        assert result.scenario_id == "cascading_reroute"
        assert 0.26 <= result.risk_increase <= 0.48
        assert result.time_horizon_status == 72
        assert result.affected_ports >= 2
        assert result.affected_airports >= 2
        assert 2 <= result.cascade_depth <= 4
        
        validation_passed, errors = scenario_runner.validate_against_expected("cascading_reroute", result)
        assert validation_passed, f"Validation errors: {errors}"


class TestScenarioValidation:
    """Test validation framework against expected outputs."""

    def test_all_scenarios_list(self, scenario_runner):
        """Verify all 15 scenario IDs are available."""
        scenario_ids = list_scenario_ids()
        assert len(scenario_ids) == 15
        expected_ids = [
            "hormuz_closure",
            "gcc_airspace_closure",
            "missile_escalation",
            "airport_shutdown",
            "port_congestion",
            "conflict_spillover",
            "maritime_risk_surge",
            "combined_disruption",
            "insurance_surge",
            "executive_board",
            "red_sea_diversion",
            "dual_disruption",
            "oil_corridor_risk",
            "false_signal",
            "cascading_reroute",
        ]
        assert sorted(scenario_ids) == sorted(expected_ids)

    def test_scenario_result_has_required_fields(self, scenario_runner):
        """Verify ScenarioResult contains all required fields."""
        result = scenario_runner.run_seeded_scenario("hormuz_closure")
        
        required_fields = [
            "scenario_id",
            "risk_increase",
            "confidence_adjustment",
            "system_stress_level",
            "affected_ports",
            "affected_airports",
            "affected_corridors",
            "insurance_surge",
            "logistics_delay_hours",
            "cascade_depth",
            "cascade_events",
            "propagation_factor",
            "nodes_affected_total",
            "critical_nodes_impacted",
            "time_horizon_status",
            "validation_passed",
            "validation_errors",
        ]
        
        for field in required_fields:
            assert hasattr(result, field), f"Missing field: {field}"

    def test_cascade_events_structure(self, scenario_runner):
        """Verify cascade events have proper structure."""
        result = scenario_runner.run_seeded_scenario("combined_disruption")
        
        assert len(result.cascade_events) > 0
        for event in result.cascade_events:
            assert hasattr(event, "event_type")
            assert hasattr(event, "source_node")
            assert hasattr(event, "affected_nodes")
            assert hasattr(event, "propagation_distance")
            assert hasattr(event, "stress_increase")
            assert hasattr(event, "timestamp")

    def test_confidence_adjustment_decreases_with_cascade(self, scenario_runner):
        """Verify confidence adjustment is negative and scales with cascade depth."""
        high_cascade_result = scenario_runner.run_seeded_scenario("combined_disruption")
        low_cascade_result = scenario_runner.run_seeded_scenario("false_signal")
        
        assert high_cascade_result.confidence_adjustment < 0
        assert low_cascade_result.confidence_adjustment < 0
        assert high_cascade_result.confidence_adjustment < low_cascade_result.confidence_adjustment


class TestRunAllScenarios:
    """Test batch execution of all scenarios."""

    def test_run_all_scenarios(self, scenario_runner):
        """Execute all 15 scenarios and verify results."""
        results = scenario_runner.run_all_scenarios()
        
        assert len(results) == 15
        assert all(isinstance(scenario_id, str) for scenario_id in results.keys())
        assert all(hasattr(result, "scenario_id") for result in results.values())
        
        logger.info(f"Executed {len(results)} scenarios successfully")
        for scenario_id, result in results.items():
            logger.info(f"{scenario_id}: risk_increase={result.risk_increase:.3f}, cascade_depth={result.cascade_depth}")

    def test_export_results_to_json(self, scenario_runner, tmp_path):
        """Test exporting results to JSON file."""
        results = scenario_runner.run_all_scenarios()
        output_file = tmp_path / "scenario_results.json"
        
        scenario_runner.export_results_json(results, str(output_file))
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        logger.info(f"Exported results to {output_file}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
