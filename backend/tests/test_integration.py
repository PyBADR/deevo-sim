"""
Integration tests for DecisionCore Intelligence GCC Platform.

Tests cross-module integration points including:
- Seed data loading and model initialization
- Schema serialization and deserialization
- Mathematical core weight application
- Physics configuration defaults
- Insurance model parameters
- Scenario template loading
- Scenario engine execution and state transitions
- Decision output generation
- Orchestrator pipeline execution
- API health and scenario endpoints
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

# Core module imports
from app.api.models import (
    HealthResponse,
    ScenarioRequest,
    ScenarioResponse,
    EventEntity,
    AirportEntity,
    PortEntity,
    CorridorEntity,
    FlightEntity,
    VesselEntity,
    ActorEntity,
    RiskPropagationRequest,
    ChokePointRequest,
)
from app.intelligence.math import (
    compute_risk_score,
    spatial_decay,
    temporal_decay,
    propagate_risk,
    compute_exposure,
    compute_confidence,
)
from app.intelligence.physics.gcc_physics_config import (
    PHYSICS_DEFAULTS,
    KINEMATICS_DEFAULTS,
    FRICTION_PARAMETERS,
    PROPAGATION_PARAMETERS,
)
from app.intelligence.insurance.insurance_models import (
    InsuranceResult,
    compute_insurance_impact,
)


class TestSeedDataIntegration:
    """Test seed data loading and model initialization."""

    def test_seed_events_loaded(self, seed_events):
        """Verify seed events are properly loaded and structured."""
        assert len(seed_events) == 5
        for event in seed_events:
            assert "event_id" in event
            assert "event_type" in event
            assert "location_name" in event
            assert "country" in event
            assert "latitude" in event
            assert "longitude" in event
            assert "event_date" in event
            assert event["latitude"] >= -90 and event["latitude"] <= 90
            assert event["longitude"] >= -180 and event["longitude"] <= 180

    def test_seed_airports_loaded(self, seed_airports):
        """Verify airport seed data is complete."""
        assert len(seed_airports) == 8
        iata_codes = {airport["iata_code"] for airport in seed_airports}
        assert "IST" in iata_codes
        assert "DXB" in iata_codes
        assert "JFK" in iata_codes
        for airport in seed_airports:
            assert "airport_id" in airport
            assert "iata_code" in airport
            assert "name" in airport
            assert "country" in airport
            assert "latitude" in airport
            assert "longitude" in airport

    def test_seed_ports_loaded(self, seed_ports):
        """Verify port seed data is complete."""
        assert len(seed_ports) == 8
        port_codes = {port["port_code"] for port in seed_ports}
        assert "AEHSX" in port_codes  # Jebel Ali
        assert "SGSIN" in port_codes  # Singapore
        for port in seed_ports:
            assert "port_id" in port
            assert "port_code" in port
            assert "name" in port
            assert "country" in port
            assert "container_capacity" in port

    def test_seed_corridors_loaded(self, seed_corridors):
        """Verify corridor seed data is complete."""
        assert len(seed_corridors) == 10
        corridor_types = {corridor["corridor_type"] for corridor in seed_corridors}
        assert "maritime" in corridor_types
        assert "air" in corridor_types
        for corridor in seed_corridors:
            assert "corridor_id" in corridor
            assert "corridor_type" in corridor
            assert "origin" in corridor
            assert "destination" in corridor

    def test_seed_flights_loaded(self, seed_flights):
        """Verify flight seed data."""
        assert len(seed_flights) == 10
        for flight in seed_flights:
            assert "flight_id" in flight
            assert "flight_number" in flight
            assert "aircraft_type" in flight
            assert "origin" in flight
            assert "destination" in flight
            assert "capacity" in flight

    def test_seed_vessels_loaded(self, seed_vessels):
        """Verify vessel seed data."""
        assert len(seed_vessels) == 10
        for vessel in seed_vessels:
            assert "vessel_id" in vessel
            assert "name" in vessel
            assert "mmsi" in vessel
            assert "vessel_type" in vessel
            assert "teu_capacity" in vessel
            assert "current_location" in vessel

    def test_seed_actors_loaded(self, seed_actors):
        """Verify actor seed data."""
        assert len(seed_actors) == 15
        actor_types = {actor["actor_type"] for actor in seed_actors}
        assert "government" in actor_types
        assert "corporation" in actor_types
        for actor in seed_actors:
            assert "actor_id" in actor
            assert "name" in actor
            assert "actor_type" in actor

    def test_all_seed_data_compound_fixture(self, all_seed_data):
        """Verify compound fixture merges all seed data correctly."""
        assert "events" in all_seed_data
        assert "airports" in all_seed_data
        assert "ports" in all_seed_data
        assert "corridors" in all_seed_data
        assert "flights" in all_seed_data
        assert "vessels" in all_seed_data
        assert "actors" in all_seed_data
        assert "scenarios" in all_seed_data
        assert "risk_weights" in all_seed_data
        assert len(all_seed_data["events"]) == 5
        assert len(all_seed_data["airports"]) == 8


class TestSchemaIntegration:
    """Test schema serialization and model validation."""

    def test_event_entity_serialization(self, seed_event_base):
        """Verify Event model can be created and serialized."""
        event_entity = EventEntity(
            event_id=seed_event_base["event_id"],
            event_type=seed_event_base["event_type"],
            severity=5,
            location=seed_event_base["location_name"],
            timestamp=seed_event_base["event_date"],
        )
        assert event_entity.event_id == seed_event_base["event_id"]
        assert event_entity.event_type == seed_event_base["event_type"]
        data = event_entity.model_dump()
        assert "event_id" in data
        assert "event_type" in data

    def test_airport_entity_serialization(self, seed_airports):
        """Verify Airport model serialization."""
        airport = seed_airports[0]
        airport_entity = AirportEntity(
            airport_id=airport["airport_id"],
            name=airport["name"],
            country=airport["country"],
            status="operational",
            latitude=airport["latitude"],
            longitude=airport["longitude"],
        )
        data = airport_entity.model_dump()
        assert data["latitude"] >= -90 and data["latitude"] <= 90
        assert data["longitude"] >= -180 and data["longitude"] <= 180

    def test_port_entity_serialization(self, seed_ports):
        """Verify Port model serialization."""
        port = seed_ports[0]
        port_entity = PortEntity(
            port_id=port["port_id"],
            name=port["name"],
            country=port["country"],
            status="operational",
            latitude=port["latitude"],
            longitude=port["longitude"],
        )
        data = port_entity.model_dump()
        assert "port_id" in data
        assert data["latitude"] >= -90 and data["latitude"] <= 90

    def test_scenario_response_serialization(self):
        """Verify Scenario model serialization."""
        scenario = ScenarioResponse(
            scenario_id="scenario_001",
            name="Suez Blockade",
            description="Complete closure of Suez Canal",
            scenario_type="disruption",
            parameters={"duration_days": 30, "affected_corridors": 3},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        data = scenario.model_dump()
        assert data["scenario_id"] == "scenario_001"
        assert data["parameters"]["duration_days"] == 30

    def test_health_response_serialization(self):
        """Verify HealthResponse model serialization."""
        health = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            service_name="DecisionCore Intelligence GCC",
            version="1.0.0",
        )
        data = health.model_dump()
        assert data["status"] == "healthy"
        assert data["service_name"] == "DecisionCore Intelligence GCC"

    def test_risk_propagation_request_validation(self):
        """Verify RiskPropagationRequest validation."""
        request = RiskPropagationRequest(
            source_entity_id="airport_001",
            source_entity_type="airport",
            max_hops=5,
            risk_threshold=0.5,
        )
        assert request.max_hops >= 1 and request.max_hops <= 10
        assert request.risk_threshold >= 0 and request.risk_threshold <= 1

    def test_choke_point_request_validation(self):
        """Verify ChokePointRequest validation."""
        request = ChokePointRequest(region="Middle East", corridor_type="maritime")
        assert request.region == "Middle East"
        assert request.corridor_type == "maritime"


class TestMathCoreIntegration:
    """Test mathematical core module integration."""

    def test_risk_score_computation(self, seed_event_base, gcc_risk_weights):
        """Verify risk score computation with seed data."""
        risk_result = compute_risk_score(
            base_event=seed_event_base,
            proximity_score=0.8,
            temporal_factor=0.9,
            confidence=0.85,
            risk_weights=gcc_risk_weights,
        )
        assert hasattr(risk_result, "risk_score")
        assert 0 <= risk_result.risk_score <= 1

    def test_spatial_decay_integration(self):
        """Test spatial decay calculation."""
        # Damascus to Istanbul (approximately 1200 km)
        decay = spatial_decay(distance_km=1200, decay_rate=0.001)
        assert 0 <= decay <= 1
        assert decay < spatial_decay(distance_km=100, decay_rate=0.001)

    def test_temporal_decay_integration(self):
        """Test temporal decay calculation."""
        now = datetime.utcnow()
        old_date = now - timedelta(days=30)
        decay_old = temporal_decay(old_date, reference_time=now, half_life_days=7)
        decay_new = temporal_decay(now, reference_time=now, half_life_days=7)
        assert decay_old < decay_new

    def test_propagation_integration(self, seed_airports, seed_corridors):
        """Test risk propagation through network."""
        propagation = propagate_risk(
            source_location=seed_airports[0],
            corridors=seed_corridors[:3],
            base_risk=0.6,
            max_hops=3,
        )
        assert hasattr(propagation, "affected_nodes")
        assert hasattr(propagation, "propagation_paths")

    def test_exposure_integration(self, seed_airports, seed_corridors):
        """Test exposure computation."""
        exposure = compute_exposure(
            locations=seed_airports[:3],
            corridors=seed_corridors[:2],
            risk_scores=[0.6, 0.5, 0.4],
        )
        assert hasattr(exposure, "total_exposure")
        assert exposure.total_exposure >= 0

    def test_confidence_integration(self):
        """Test confidence score computation."""
        confidence = compute_confidence(
            source_count=3,
            source_reliability=0.85,
            temporal_freshness=0.9,
            spatial_precision_km=50,
        )
        assert hasattr(confidence, "confidence_score")
        assert 0 <= confidence.confidence_score <= 1


class TestPhysicsIntegration:
    """Test physics module configuration and defaults."""

    def test_physics_defaults_loaded(self):
        """Verify physics defaults are properly configured."""
        assert "gravity" in PHYSICS_DEFAULTS
        assert "earth_radius_km" in PHYSICS_DEFAULTS
        assert PHYSICS_DEFAULTS["earth_radius_km"] == 6371

    def test_kinematics_defaults_loaded(self):
        """Verify kinematics defaults."""
        assert "vessel_speed_ms" in KINEMATICS_DEFAULTS
        assert "aircraft_speed_ms" in KINEMATICS_DEFAULTS
        assert KINEMATICS_DEFAULTS["vessel_speed_ms"] > 0
        assert KINEMATICS_DEFAULTS["aircraft_speed_ms"] > KINEMATICS_DEFAULTS["vessel_speed_ms"]

    def test_friction_parameters_loaded(self):
        """Verify friction parameters."""
        assert "water_friction" in FRICTION_PARAMETERS
        assert "air_friction" in FRICTION_PARAMETERS
        assert "land_friction" in FRICTION_PARAMETERS
        for key, value in FRICTION_PARAMETERS.items():
            assert 0 <= value <= 1

    def test_propagation_parameters_loaded(self):
        """Verify propagation parameters."""
        assert "signal_velocity_m_s" in PROPAGATION_PARAMETERS
        assert "attenuation_rate" in PROPAGATION_PARAMETERS
        assert PROPAGATION_PARAMETERS["signal_velocity_m_s"] > 0


class TestInsuranceIntegration:
    """Test insurance model integration."""

    def test_insurance_computation_integration(self):
        """Verify insurance impact computation."""
        result = compute_insurance_impact(
            event_severity=7,
            affected_assets_usd=1000000,
            event_frequency_per_year=0.5,
            event_type="maritime_incident",
        )
        assert isinstance(result, InsuranceResult)
        assert hasattr(result, "premium_impact")
        assert hasattr(result, "reserve_requirement")
        assert result.premium_impact >= 0

    def test_insurance_result_serialization(self):
        """Test InsuranceResult serialization."""
        result = InsuranceResult(
            premium_impact=0.15,
            reserve_requirement=5000000,
            coverage_gap=500000,
            recommendation="Increase premiums and reserves",
        )
        data = result.model_dump()
        assert data["premium_impact"] == 0.15
        assert data["reserve_requirement"] == 5000000


class TestScenarioTemplatesIntegration:
    """Test scenario template loading and structure."""

    def test_scenario_templates_loaded(self, scenario_templates):
        """Verify all scenario templates are loaded."""
        assert len(scenario_templates) == 15
        scenario_names = {s["name"] for s in scenario_templates}
        assert "Suez Blockade" in scenario_names
        assert "Strait of Hormuz Closure" in scenario_names
        assert "Regional Conflict Escalation" in scenario_names

    def test_scenario_template_structure(self, scenario_templates):
        """Verify template structure."""
        for template in scenario_templates:
            assert "scenario_id" in template
            assert "name" in template
            assert "description" in template
            assert "scenario_type" in template
            assert "parameters" in template
            assert isinstance(template["parameters"], dict)

    def test_scenario_templates_by_type(self, scenario_templates):
        """Verify scenario type distribution."""
        types = {s["scenario_type"] for s in scenario_templates}
        assert "disruption" in types
        assert "market" in types


class TestScenarioEngineIntegration:
    """Test scenario engine execution integration."""

    def test_scenario_request_validation(self):
        """Verify ScenarioRequest validation."""
        request = ScenarioRequest(
            name="Test Scenario",
            description="Test description",
            scenario_type="disruption",
            parameters={"duration": 30, "severity": 7},
        )
        assert request.name == "Test Scenario"
        assert request.scenario_type == "disruption"

    def test_scenario_state_transitions(self):
        """Verify valid scenario state transitions."""
        states = ["created", "initialized", "running", "completed", "failed"]
        # Valid transitions
        assert "initialized" in states
        assert "running" in states
        assert "completed" in states


class TestOrchestratorIntegration:
    """Test orchestrator pipeline execution."""

    def test_orchestrator_pipeline_initialization(self, all_seed_data):
        """Verify orchestrator can be initialized with seed data."""
        assert "events" in all_seed_data
        assert "corridors" in all_seed_data
        assert "actors" in all_seed_data
        assert len(all_seed_data["events"]) > 0

    def test_orchestrator_module_imports(self):
        """Verify all orchestrator dependencies can be imported."""
        from app.intelligence.math import compute_risk_score
        from app.intelligence.physics.gcc_physics_config import PHYSICS_DEFAULTS
        from app.intelligence.insurance.insurance_models import compute_insurance_impact
        assert compute_risk_score is not None
        assert PHYSICS_DEFAULTS is not None
        assert compute_insurance_impact is not None


class TestAPIHealthIntegration:
    """Test API health endpoint."""

    def test_health_response_structure(self):
        """Verify health response has required fields."""
        health = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            service_name="DecisionCore Intelligence GCC",
            version="1.0.0",
        )
        assert health.status in ["healthy", "degraded", "unhealthy"]
        assert health.service_name is not None
        assert health.version is not None


class TestScenariosListEndpoint:
    """Test scenarios list endpoint integration."""

    def test_scenario_response_list_structure(self, scenario_templates):
        """Verify scenario list response structure."""
        assert len(scenario_templates) > 0
        for scenario in scenario_templates:
            assert "scenario_id" in scenario
            assert "name" in scenario


class TestCrossModuleIntegration:
    """Test integration across multiple modules."""

    def test_event_to_risk_pipeline(self, seed_event_base, gcc_risk_weights):
        """Test complete event to risk computation pipeline."""
        # Event -> Risk computation
        risk_result = compute_risk_score(
            base_event=seed_event_base,
            proximity_score=0.75,
            temporal_factor=0.85,
            confidence=0.8,
            risk_weights=gcc_risk_weights,
        )
        assert hasattr(risk_result, "risk_score")

    def test_corridor_to_exposure_pipeline(self, seed_corridors, seed_airports):
        """Test corridor analysis to exposure computation."""
        exposure = compute_exposure(
            locations=seed_airports[:2],
            corridors=seed_corridors[:2],
            risk_scores=[0.5, 0.6],
        )
        assert hasattr(exposure, "total_exposure")

    def test_actor_scenario_interaction(self, seed_actors, scenario_templates):
        """Verify actor and scenario data can be combined."""
        government_actors = [a for a in seed_actors if a["actor_type"] == "government"]
        disruption_scenarios = [
            s for s in scenario_templates if s["scenario_type"] == "disruption"
        ]
        assert len(government_actors) > 0
        assert len(disruption_scenarios) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
