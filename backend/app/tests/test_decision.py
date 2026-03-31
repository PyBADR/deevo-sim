"""
Tests for the Decision Output Layer (Phase 10).

Comprehensive test coverage for DecisionOutput generation, bilingual support,
economic/insurance impact computation, and recommendation generation.
"""

import pytest
from datetime import datetime, timedelta
from app.decision import DecisionOutputGenerator, DecisionOutput, ImpactSeverity, RecommendationPriority, BilingualText
from app.scenarios import (
    ScenarioSimulationResult, 
    ScenarioTemplate,
    DisruptionType,
    EventType,
    ShockLocation
)


class TestDecisionOutputStructure:
    """Test that DecisionOutput has all required fields and structure."""
    
    def test_decision_output_has_all_mandatory_fields(self):
        """Verify DecisionOutput contains all 5 question answers + supporting fields."""
        # Create minimal ScenarioSimulationResult
        result = ScenarioSimulationResult(
            scenario_id="test_scenario",
            simulation_timestamp=datetime.now(),
            max_risk_score=65.0,
            mean_risk_score=45.0,
            system_stress=0.55,
            affected_node_count=12,
            critical_node_count=4,
            mean_recovery_progress=0.3,
            cascade_depth_reached=3,
            event_duration_steps=10,
            disruption_type=DisruptionType.CYBER_ATTACK,
            geographic_extent_affected_km2=5000.0,
            estimated_affected_population_millions=8.5,
            network_topology_nodes=50,
            network_topology_edges=120
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        # Test all 5 question fields exist and are populated
        assert output.what_happened is not None
        assert isinstance(output.what_happened, BilingualText)
        assert len(output.what_happened.en) > 0
        assert len(output.what_happened.ar) > 0
        
        assert output.what_is_impact is not None
        assert isinstance(output.what_is_impact, BilingualText)
        assert output.impact_severity in ImpactSeverity
        
        assert output.what_is_affected is not None
        assert isinstance(output.what_is_affected, BilingualText)
        assert isinstance(output.affected_regions, list)
        assert isinstance(output.affected_sectors, list)
        assert output.affected_populations_millions > 0
        
        assert output.how_big_is_risk is not None
        assert isinstance(output.how_big_is_risk, BilingualText)
        assert 0 <= output.risk_score_0_100 <= 100
        assert output.risk_level in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
        assert 0 <= output.cascade_probability_percent <= 100
        
        assert output.what_to_do is not None
        assert isinstance(output.what_to_do, list)
        assert len(output.what_to_do) > 0


class TestAll5QuestionsAnswered:
    """Test that all 5 mandatory questions are answered with substantive content."""
    
    def test_what_happened_is_substantive(self):
        """Verify what_happened includes event type and key metrics."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=70.0,
            mean_risk_score=50.0,
            system_stress=0.60,
            affected_node_count=15,
            critical_node_count=5,
            mean_recovery_progress=0.25,
            cascade_depth_reached=4,
            event_duration_steps=12,
            disruption_type=DisruptionType.FLOODING,
            geographic_extent_affected_km2=8000.0,
            estimated_affected_population_millions=12.0,
            network_topology_nodes=60,
            network_topology_edges=150
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        # Check that what_happened contains meaningful content
        assert len(output.what_happened.en) >= 50  # Non-trivial length
        assert len(output.what_happened.ar) >= 30  # Arabic may be shorter
        assert "flooding" in output.what_happened.en.lower() or "disruption" in output.what_happened.en.lower()
    
    def test_what_is_impact_includes_severity(self):
        """Verify impact answer includes severity classification."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=85.0,  # High severity
            mean_risk_score=70.0,
            system_stress=0.75,
            affected_node_count=25,
            critical_node_count=8,
            mean_recovery_progress=0.15,
            cascade_depth_reached=5,
            event_duration_steps=15,
            disruption_type=DisruptionType.CYBER_ATTACK,
            geographic_extent_affected_km2=15000.0,
            estimated_affected_population_millions=20.0,
            network_topology_nodes=100,
            network_topology_edges=300
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        assert output.impact_severity == ImpactSeverity.CATASTROPHIC
        assert len(output.what_is_impact.en) >= 50
        assert "catastrophic" in output.what_is_impact.en.lower() or "severe" in output.what_is_impact.en.lower()
    
    def test_what_is_affected_includes_sectors_and_regions(self):
        """Verify affected answer includes affected sectors and regions."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=55.0,
            mean_risk_score=40.0,
            system_stress=0.50,
            affected_node_count=10,
            critical_node_count=3,
            mean_recovery_progress=0.35,
            cascade_depth_reached=2,
            event_duration_steps=8,
            disruption_type=DisruptionType.SUPPLY_CHAIN_DISRUPTION,
            geographic_extent_affected_km2=3000.0,
            estimated_affected_population_millions=5.0,
            network_topology_nodes=40,
            network_topology_edges=100
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        assert len(output.affected_sectors) > 0
        assert len(output.affected_regions) > 0
        assert output.affected_populations_millions > 0
        assert any(sector.lower() in output.what_is_affected.en.lower() for sector in output.affected_sectors)
    
    def test_how_big_is_risk_includes_score_and_probability(self):
        """Verify risk answer includes numerical risk score and cascade probability."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=72.0,
            mean_risk_score=55.0,
            system_stress=0.65,
            affected_node_count=18,
            critical_node_count=6,
            mean_recovery_progress=0.28,
            cascade_depth_reached=4,
            event_duration_steps=11,
            disruption_type=DisruptionType.EARTHQUAKE,
            geographic_extent_affected_km2=10000.0,
            estimated_affected_population_millions=15.0,
            network_topology_nodes=80,
            network_topology_edges=200
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        assert 0 <= output.risk_score_0_100 <= 100
        assert output.risk_score_0_100 > 50  # Should be HIGH given inputs
        assert output.risk_level == 'HIGH'
        assert output.cascade_probability_percent > 0
        assert len(output.how_big_is_risk.en) >= 50
    
    def test_what_to_do_has_actionable_recommendations(self):
        """Verify recommendations include title, description, priority, timeline."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=68.0,
            mean_risk_score=48.0,
            system_stress=0.58,
            affected_node_count=14,
            critical_node_count=4,
            mean_recovery_progress=0.32,
            cascade_depth_reached=3,
            event_duration_steps=10,
            disruption_type=DisruptionType.PANDEMIC,
            geographic_extent_affected_km2=7000.0,
            estimated_affected_population_millions=10.0,
            network_topology_nodes=50,
            network_topology_edges=120
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        assert len(output.what_to_do) >= 3
        for rec in output.what_to_do:
            assert rec.title is not None
            assert isinstance(rec.title, BilingualText)
            assert len(rec.title.en) > 0
            assert rec.description is not None
            assert isinstance(rec.description, BilingualText)
            assert rec.priority in RecommendationPriority
            assert rec.timeline is not None
            assert rec.responsible_party is not None
            assert rec.estimated_cost_usd_millions >= 0
            assert rec.expected_impact is not None


class TestBilingualOutput:
    """Test bilingual EN/AR support across all output sections."""
    
    def test_all_bilingual_text_fields_populated(self):
        """Verify all BilingualText fields have both EN and AR content."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=62.0,
            mean_risk_score=46.0,
            system_stress=0.52,
            affected_node_count=11,
            critical_node_count=3,
            mean_recovery_progress=0.34,
            cascade_depth_reached=2,
            event_duration_steps=9,
            disruption_type=DisruptionType.VOLCANIC_ERUPTION,
            geographic_extent_affected_km2=4000.0,
            estimated_affected_population_millions=6.0,
            network_topology_nodes=45,
            network_topology_edges=110
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        # Check main answers
        assert output.what_happened.en and output.what_happened.ar
        assert output.what_is_impact.en and output.what_is_impact.ar
        assert output.what_is_affected.en and output.what_is_affected.ar
        assert output.how_big_is_risk.en and output.how_big_is_risk.ar
        
        # Check recommendations
        for rec in output.what_to_do:
            assert rec.title.en and rec.title.ar
            assert rec.description.en and rec.description.ar
    
    def test_bilingual_text_length_reasonable(self):
        """Verify Arabic and English translations have reasonable lengths."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=58.0,
            mean_risk_score=42.0,
            system_stress=0.48,
            affected_node_count=9,
            critical_node_count=2,
            mean_recovery_progress=0.38,
            cascade_depth_reached=2,
            event_duration_steps=8,
            disruption_type=DisruptionType.HURRICANE,
            geographic_extent_affected_km2=2500.0,
            estimated_affected_population_millions=3.5,
            network_topology_nodes=35,
            network_topology_edges=85
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        # English should be somewhat longer than Arabic
        en_len = len(output.what_happened.en)
        ar_len = len(output.what_happened.ar)
        assert en_len > 0 and ar_len > 0
        # Arabic might be shorter due to script efficiency


class TestRecommendationsGenerated:
    """Test recommendation generation with appropriate priorities and costs."""
    
    def test_recommendations_count_appropriate(self):
        """Verify 3-5 recommendations are generated."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=75.0,
            mean_risk_score=58.0,
            system_stress=0.68,
            affected_node_count=20,
            critical_node_count=7,
            mean_recovery_progress=0.20,
            cascade_depth_reached=4,
            event_duration_steps=13,
            disruption_type=DisruptionType.CYBER_ATTACK,
            geographic_extent_affected_km2=12000.0,
            estimated_affected_population_millions=18.0,
            network_topology_nodes=90,
            network_topology_edges=280
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        assert 3 <= len(output.what_to_do) <= 5
    
    def test_critical_severity_has_critical_recommendations(self):
        """Verify CATASTROPHIC impact triggers CRITICAL priority recommendations."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=88.0,
            mean_risk_score=75.0,
            system_stress=0.82,
            affected_node_count=40,
            critical_node_count=15,
            mean_recovery_progress=0.10,
            cascade_depth_reached=6,
            event_duration_steps=18,
            disruption_type=DisruptionType.NUCLEAR_ACCIDENT,
            geographic_extent_affected_km2=25000.0,
            estimated_affected_population_millions=30.0,
            network_topology_nodes=150,
            network_topology_edges=500
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        assert output.impact_severity == ImpactSeverity.CATASTROPHIC
        # At least one recommendation should be CRITICAL
        assert any(rec.priority == RecommendationPriority.CRITICAL for rec in output.what_to_do)
    
    def test_recommendations_have_realistic_costs(self):
        """Verify estimated costs scale with severity."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=82.0,
            mean_risk_score=68.0,
            system_stress=0.75,
            affected_node_count=28,
            critical_node_count=10,
            mean_recovery_progress=0.18,
            cascade_depth_reached=5,
            event_duration_steps=14,
            disruption_type=DisruptionType.CYBER_ATTACK,
            geographic_extent_affected_km2=18000.0,
            estimated_affected_population_millions=22.0,
            network_topology_nodes=110,
            network_topology_edges=350
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        total_cost = sum(rec.estimated_cost_usd_millions for rec in output.what_to_do)
        assert total_cost > 0
        # High severity should have substantial total costs
        assert total_cost >= 100  # At least 100M USD for SEVERE scenario


class TestEconomicImpactComputed:
    """Test economic impact calculation."""
    
    def test_economic_impact_scales_with_severity(self):
        """Verify GDP impact increases with severity."""
        # Low severity scenario
        low_result = ScenarioSimulationResult(
            scenario_id="test_low",
            simulation_timestamp=datetime.now(),
            max_risk_score=25.0,
            mean_risk_score=15.0,
            system_stress=0.25,
            affected_node_count=3,
            critical_node_count=0,
            mean_recovery_progress=0.60,
            cascade_depth_reached=1,
            event_duration_steps=4,
            disruption_type=DisruptionType.MINOR_DISRUPTION,
            geographic_extent_affected_km2=500.0,
            estimated_affected_population_millions=0.5,
            network_topology_nodes=20,
            network_topology_edges=40
        )
        
        # High severity scenario
        high_result = ScenarioSimulationResult(
            scenario_id="test_high",
            simulation_timestamp=datetime.now(),
            max_risk_score=85.0,
            mean_risk_score=72.0,
            system_stress=0.78,
            affected_node_count=35,
            critical_node_count=12,
            mean_recovery_progress=0.12,
            cascade_depth_reached=5,
            event_duration_steps=16,
            disruption_type=DisruptionType.CYBER_ATTACK,
            geographic_extent_affected_km2=20000.0,
            estimated_affected_population_millions=25.0,
            network_topology_nodes=120,
            network_topology_edges=400
        )
        
        generator = DecisionOutputGenerator()
        low_output = generator.generate(low_result)
        high_output = generator.generate(high_result)
        
        # High severity should have higher economic impact
        low_impact = low_output.economic_impact.estimated_gdp_impact_usd_millions
        high_impact = high_output.economic_impact.estimated_gdp_impact_usd_millions
        
        assert low_impact > 0
        assert high_impact > low_impact
    
    def test_economic_impact_includes_all_fields(self):
        """Verify EconomicImpact has all required fields."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=65.0,
            mean_risk_score=50.0,
            system_stress=0.58,
            affected_node_count=16,
            critical_node_count=5,
            mean_recovery_progress=0.25,
            cascade_depth_reached=3,
            event_duration_steps=11,
            disruption_type=DisruptionType.SUPPLY_CHAIN_DISRUPTION,
            geographic_extent_affected_km2=9000.0,
            estimated_affected_population_millions=14.0,
            network_topology_nodes=70,
            network_topology_edges=180
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        assert output.economic_impact.estimated_gdp_impact_usd_millions > 0
        assert output.economic_impact.trade_volume_affected_percent > 0
        assert output.economic_impact.employment_impact_thousands > 0
        assert output.economic_impact.commodity_price_inflation_percent >= 0
        assert output.economic_impact.export_revenue_loss_percent >= 0
        assert output.economic_impact.import_cost_increase_percent >= 0
        assert output.economic_impact.recovery_duration_days > 0
        assert len(output.economic_impact.economic_scenario) > 0


class TestInsuranceImpactComputed:
    """Test insurance impact calculation."""
    
    def test_insurance_impact_includes_all_fields(self):
        """Verify InsuranceImpact has all required fields."""
        result = ScenarioSimulationResult(
            scenario_id="test",
            simulation_timestamp=datetime.now(),
            max_risk_score=70.0,
            mean_risk_score=55.0,
            system_stress=0.62,
            affected_node_count=18,
            critical_node_count=6,
            mean_recovery_progress=0.22,
            cascade_depth_reached=4,
            event_duration_steps=12,
            disruption_type=DisruptionType.EARTHQUAKE,
            geographic_extent_affected_km2=11000.0,
            estimated_affected_population_millions=16.0,
            network_topology_nodes=85,
            network_topology_edges=220
        )
        
        generator = DecisionOutputGenerator()
        output = generator.generate(result)
        
        assert output.insurance_impact.policies_affected_count >= 0
        assert output.insurance_impact.estimated_claims_surge_percent > 0
        assert output.insurance_impact.estimated_claims_uplift_usd_millions > 0
        assert isinstance(output.insurance_impact.underwriting_restrictions_implemented, bool)
        assert output.insurance_impact.premium_adjustment_percent >= 0
        assert output.insurance_impact.coverage_capacity_reduction_percent >= 0
        assert len(output.insurance_impact.portfolio_stress_level) > 0
    
    def test_insurance_impact_scales_with_affected_population(self):
        """Verify insurance claims scale with population impact."""
        # Small affected population
        small_result = ScenarioSimulationResult(
            scenario_id="test_small",
            simulation_timestamp=datetime.now(),
            max_risk_score=40.0,
            mean_risk_score=30.0,
            system_stress=0.35,
            affected_node_count=5,
            critical_node_count=1,
            mean_recovery_progress=0.50,
            cascade_depth_reached=1,
            event_duration_steps=6,
            disruption_type=DisruptionType.MINOR_DISRUPTION,
            geographic_extent_affected_km2=1000.0,
            estimated_affected_population_millions=1.0,
            network_topology_nodes=25,
            network_topology_edges=60
        )
        
        # Large affected population
        large_result = ScenarioSimulationResult(
            scenario_id="test_large",
            simulation_timestamp=datetime.now(),
            max_risk_score=80.0,
            mean_risk_score=68.0,
            system_stress=0.73,
            affected_node_count=32,
            critical_node_count=11,
            mean_recovery_progress=0.14,
            cascade_depth_reached=5,
            event_duration_steps=15,
            disruption_type=DisruptionType.PANDEMIC,
            geographic_extent_affected_km2=19000.0,
            estimated_affected_population_millions=28.0,
            network_topology_nodes=105,
            network_topology_edges=320
        )
        
        generator = DecisionOutputGenerator()
        small_output = generator.generate(small_result)
        large_output = generator.generate(large_result)
        
        # Larger population should have higher claims uplift
        small_claims = small_output.insurance_impact.estimated_claims_uplift_usd_millions
        large_claims = large_output.insurance_impact.estimated_claims_uplift_usd_millions
        
        assert small_claims > 0
        assert large_claims > small_claims


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
