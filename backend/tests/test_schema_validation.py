"""
Schema validation tests for DecisionCore Intelligence GCC Platform.

Tests Pydantic v2 schema validation including:
- Event model field validation
- IATA airport code validation
- Port coordinate validation
- Corridor structure validation
- Flight status validation
- Vessel MMSI validation
- Actor type validation
- Risk score range validation
- Geospatial bounds validation
- Bilingual field validation
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError, BaseModel, Field
from typing import Optional


# Test model definitions that mirror production schemas
class EventModel(BaseModel):
    """Event schema with validation."""
    event_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    event_date: datetime
    location_name: str = Field(..., min_length=1)
    country: str = Field(..., min_length=2, max_length=3)
    admin1: Optional[str] = None
    admin2: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    fatalities: int = Field(default=0, ge=0)
    wounded: int = Field(default=0, ge=0)
    description: str
    source_id: str
    source_type: str
    confidence: float = Field(..., ge=0, le=1)
    tags: list[str] = Field(default_factory=list)


class AirportModel(BaseModel):
    """Airport schema with IATA validation."""
    airport_id: str
    iata_code: str = Field(..., min_length=3, max_length=3)
    name: str
    country: str = Field(..., min_length=2, max_length=3)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    annual_passengers: int = Field(ge=0)
    annual_cargo_tonnes: int = Field(ge=0)


class PortModel(BaseModel):
    """Port schema with coordinate validation."""
    port_id: str
    port_code: str = Field(..., min_length=5, max_length=5)
    name: str
    country: str = Field(..., min_length=2, max_length=3)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    container_capacity: int = Field(ge=0)
    berth_count: int = Field(ge=1)


class CorridorModel(BaseModel):
    """Corridor schema validation."""
    corridor_id: str
    name: str
    corridor_type: str = Field(..., pattern="^(maritime|air|ground|pipeline)$")
    origin: str
    destination: str
    distance_km: float = Field(ge=0)
    annual_cargo_volume: int = Field(ge=0)


class FlightModel(BaseModel):
    """Flight schema with status validation."""
    flight_id: str
    flight_number: str
    aircraft_type: str
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    capacity: int = Field(gt=0)
    status: str = Field(..., pattern="^(scheduled|departed|airborne|delayed|cancelled|landed)$")


class VesselModel(BaseModel):
    """Vessel schema with MMSI validation."""
    vessel_id: str
    name: str
    mmsi: int = Field(..., ge=100000000, le=999999999)
    vessel_type: str
    teu_capacity: int = Field(ge=0)
    current_location: str


class ActorModel(BaseModel):
    """Actor schema with type validation."""
    actor_id: str
    name: str
    actor_type: str = Field(..., pattern="^(government|corporation|ngo|non_state|organization)$")
    country_of_origin: Optional[str] = None
    influence_score: float = Field(ge=0, le=100)
    specialization: str


class RiskScoreModel(BaseModel):
    """Risk score schema."""
    risk_score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    severity: int = Field(..., ge=0, le=10)


class GeoPointModel(BaseModel):
    """Geographic point validation."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_name: str


class BilingualFieldModel(BaseModel):
    """Bilingual field schema."""
    name_en: str = Field(..., min_length=1)
    name_ar: str = Field(..., min_length=1)


class TestEventModelValidation:
    """Test Event model schema validation."""

    def test_event_valid_minimal(self, seed_event_base):
        """Test valid minimal event."""
        event = EventModel(**seed_event_base)
        assert event.event_id == seed_event_base["event_id"]
        assert event.latitude >= -90 and event.latitude <= 90

    def test_event_latitude_out_of_bounds(self, seed_event_base):
        """Test event with invalid latitude."""
        invalid_event = seed_event_base.copy()
        invalid_event["latitude"] = 95  # Out of bounds
        with pytest.raises(ValidationError):
            EventModel(**invalid_event)

    def test_event_longitude_out_of_bounds(self, seed_event_base):
        """Test event with invalid longitude."""
        invalid_event = seed_event_base.copy()
        invalid_event["longitude"] = 185  # Out of bounds
        with pytest.raises(ValidationError):
            EventModel(**invalid_event)

    def test_event_negative_fatalities_invalid(self, seed_event_base):
        """Test event with negative fatalities."""
        invalid_event = seed_event_base.copy()
        invalid_event["fatalities"] = -5
        with pytest.raises(ValidationError):
            EventModel(**invalid_event)

    def test_event_confidence_out_of_bounds(self, seed_event_base):
        """Test event with invalid confidence."""
        invalid_event = seed_event_base.copy()
        invalid_event["confidence"] = 1.5  # Out of 0-1 range
        with pytest.raises(ValidationError):
            EventModel(**invalid_event)

    def test_event_missing_required_field(self, seed_event_base):
        """Test event missing required field."""
        incomplete_event = seed_event_base.copy()
        del incomplete_event["event_type"]
        with pytest.raises(ValidationError):
            EventModel(**incomplete_event)

    def test_event_country_code_validation(self, seed_event_base):
        """Test country code must be 2-3 chars."""
        valid_event = seed_event_base.copy()
        valid_event["country"] = "US"
        event = EventModel(**valid_event)
        assert event.country == "US"

        invalid_event = seed_event_base.copy()
        invalid_event["country"] = "COUNTRY"
        with pytest.raises(ValidationError):
            EventModel(**invalid_event)


class TestIATACodeValidation:
    """Test IATA airport code validation."""

    def test_valid_iata_codes(self, seed_airports):
        """Test valid IATA codes from seed data."""
        for airport in seed_airports:
            airport_model = AirportModel(**airport)
            assert len(airport_model.iata_code) == 3

    def test_iata_code_too_short(self):
        """Test IATA code with insufficient length."""
        invalid_airport = {
            "airport_id": "apt_001",
            "iata_code": "JF",
            "name": "Test Airport",
            "country": "US",
            "latitude": 40.6413,
            "longitude": -74.0060,
            "annual_passengers": 50000000,
            "annual_cargo_tonnes": 2000000,
        }
        with pytest.raises(ValidationError):
            AirportModel(**invalid_airport)

    def test_iata_code_too_long(self):
        """Test IATA code with excessive length."""
        invalid_airport = {
            "airport_id": "apt_001",
            "iata_code": "JFKA",
            "name": "Test Airport",
            "country": "US",
            "latitude": 40.6413,
            "longitude": -74.0060,
            "annual_passengers": 50000000,
            "annual_cargo_tonnes": 2000000,
        }
        with pytest.raises(ValidationError):
            AirportModel(**invalid_airport)


class TestPortCoordinateValidation:
    """Test port coordinate validation."""

    def test_valid_port_coordinates(self, seed_ports):
        """Test valid port coordinates."""
        for port in seed_ports:
            port_model = PortModel(**port)
            assert port_model.latitude >= -90 and port_model.latitude <= 90
            assert port_model.longitude >= -180 and port_model.longitude <= 180

    def test_port_latitude_out_of_bounds(self):
        """Test port with invalid latitude."""
        invalid_port = {
            "port_id": "port_001",
            "port_code": "AEHSX",
            "name": "Jebel Ali",
            "country": "AE",
            "latitude": 91,  # Out of bounds
            "longitude": 55.1,
            "container_capacity": 15000000,
            "berth_count": 67,
        }
        with pytest.raises(ValidationError):
            PortModel(**invalid_port)

    def test_port_code_format(self):
        """Test port code format validation."""
        valid_port = {
            "port_id": "port_001",
            "port_code": "AEHSX",
            "name": "Jebel Ali",
            "country": "AE",
            "latitude": 25.0,
            "longitude": 55.1,
            "container_capacity": 15000000,
            "berth_count": 67,
        }
        port = PortModel(**valid_port)
        assert port.port_code == "AEHSX"

        invalid_port = valid_port.copy()
        invalid_port["port_code"] = "AE"
        with pytest.raises(ValidationError):
            PortModel(**invalid_port)


class TestCorridorValidation:
    """Test corridor structure validation."""

    def test_valid_corridor_types(self, seed_corridors):
        """Test valid corridor types."""
        for corridor in seed_corridors:
            corridor_model = CorridorModel(**corridor)
            assert corridor_model.corridor_type in ["maritime", "air", "ground", "pipeline"]

    def test_invalid_corridor_type(self):
        """Test invalid corridor type."""
        invalid_corridor = {
            "corridor_id": "corr_001",
            "name": "Test Corridor",
            "corridor_type": "underwater",  # Invalid type
            "origin": "A",
            "destination": "B",
            "distance_km": 500,
            "annual_cargo_volume": 100000,
        }
        with pytest.raises(ValidationError):
            CorridorModel(**invalid_corridor)

    def test_negative_distance(self):
        """Test corridor with negative distance."""
        invalid_corridor = {
            "corridor_id": "corr_001",
            "name": "Test Corridor",
            "corridor_type": "maritime",
            "origin": "A",
            "destination": "B",
            "distance_km": -500,  # Invalid
            "annual_cargo_volume": 100000,
        }
        with pytest.raises(ValidationError):
            CorridorModel(**invalid_corridor)


class TestFlightStatusValidation:
    """Test flight status validation."""

    def test_valid_flight_statuses(self, seed_flights):
        """Test valid flight statuses."""
        for flight in seed_flights:
            flight_model = FlightModel(**flight)
            assert flight_model.status in [
                "scheduled", "departed", "airborne", "delayed", "cancelled", "landed"
            ]

    def test_invalid_flight_status(self):
        """Test invalid flight status."""
        invalid_flight = {
            "flight_id": "flt_001",
            "flight_number": "BA123",
            "aircraft_type": "Boeing 777",
            "origin": "LHR",
            "destination": "JFK",
            "capacity": 350,
            "status": "flying",  # Invalid status
        }
        with pytest.raises(ValidationError):
            FlightModel(**invalid_flight)

    def test_iata_code_validation_in_flight(self):
        """Test IATA code validation in flight."""
        valid_flight = {
            "flight_id": "flt_001",
            "flight_number": "BA123",
            "aircraft_type": "Boeing 777",
            "origin": "LHR",
            "destination": "JFK",
            "capacity": 350,
            "status": "scheduled",
        }
        flight = FlightModel(**valid_flight)
        assert len(flight.origin) == 3


class TestVesselMMSIValidation:
    """Test vessel MMSI validation."""

    def test_valid_mmsi(self, seed_vessels):
        """Test valid MMSI numbers."""
        for vessel in seed_vessels:
            vessel_model = VesselModel(**vessel)
            assert 100000000 <= vessel_model.mmsi <= 999999999

    def test_mmsi_too_small(self):
        """Test MMSI below minimum."""
        invalid_vessel = {
            "vessel_id": "ves_001",
            "name": "Test Vessel",
            "mmsi": 99999999,  # Below minimum
            "vessel_type": "container_ship",
            "teu_capacity": 20000,
            "current_location": "Singapore",
        }
        with pytest.raises(ValidationError):
            VesselModel(**invalid_vessel)

    def test_mmsi_too_large(self):
        """Test MMSI above maximum."""
        invalid_vessel = {
            "vessel_id": "ves_001",
            "name": "Test Vessel",
            "mmsi": 1000000000,  # Above maximum
            "vessel_type": "container_ship",
            "teu_capacity": 20000,
            "current_location": "Singapore",
        }
        with pytest.raises(ValidationError):
            VesselModel(**invalid_vessel)


class TestActorTypeValidation:
    """Test actor type validation."""

    def test_valid_actor_types(self, seed_actors):
        """Test valid actor types."""
        for actor in seed_actors:
            actor_model = ActorModel(**actor)
            assert actor_model.actor_type in [
                "government", "corporation", "ngo", "non_state", "organization"
            ]

    def test_invalid_actor_type(self):
        """Test invalid actor type."""
        invalid_actor = {
            "actor_id": "act_001",
            "name": "Test Actor",
            "actor_type": "individual",  # Invalid type
            "country_of_origin": "US",
            "influence_score": 50,
            "specialization": "maritime",
        }
        with pytest.raises(ValidationError):
            ActorModel(**invalid_actor)

    def test_influence_score_bounds(self):
        """Test actor influence score bounds."""
        valid_actor = {
            "actor_id": "act_001",
            "name": "Test Actor",
            "actor_type": "government",
            "country_of_origin": "US",
            "influence_score": 75,
            "specialization": "maritime",
        }
        actor = ActorModel(**valid_actor)
        assert 0 <= actor.influence_score <= 100

        invalid_actor = valid_actor.copy()
        invalid_actor["influence_score"] = 150
        with pytest.raises(ValidationError):
            ActorModel(**invalid_actor)


class TestRiskScoreValidation:
    """Test risk score range validation."""

    def test_valid_risk_scores(self):
        """Test valid risk scores."""
        risk_scores = [
            {"risk_score": 0, "confidence": 0.5, "severity": 0},
            {"risk_score": 0.5, "confidence": 0.75, "severity": 5},
            {"risk_score": 1.0, "confidence": 0.95, "severity": 10},
        ]
        for risk_data in risk_scores:
            risk = RiskScoreModel(**risk_data)
            assert 0 <= risk.risk_score <= 1
            assert 0 <= risk.confidence <= 1
            assert 0 <= risk.severity <= 10

    def test_risk_score_exceeds_bounds(self):
        """Test risk score exceeding upper bound."""
        invalid_risk = {"risk_score": 1.5, "confidence": 0.8, "severity": 5}
        with pytest.raises(ValidationError):
            RiskScoreModel(**invalid_risk)

    def test_severity_exceeds_bounds(self):
        """Test severity exceeding bounds."""
        invalid_risk = {"risk_score": 0.7, "confidence": 0.8, "severity": 15}
        with pytest.raises(ValidationError):
            RiskScoreModel(**invalid_risk)


class TestGeoPointBoundsValidation:
    """Test geospatial bounds validation."""

    def test_valid_geo_points(self, seed_airports):
        """Test valid geographic points."""
        for airport in seed_airports:
            geo = GeoPointModel(
                latitude=airport["latitude"],
                longitude=airport["longitude"],
                location_name=airport["name"],
            )
            assert -90 <= geo.latitude <= 90
            assert -180 <= geo.longitude <= 180

    def test_latitude_exceeds_north_pole(self):
        """Test latitude exceeding north pole."""
        invalid_geo = {
            "latitude": 90.1,
            "longitude": 0,
            "location_name": "Invalid Location",
        }
        with pytest.raises(ValidationError):
            GeoPointModel(**invalid_geo)

    def test_latitude_exceeds_south_pole(self):
        """Test latitude exceeding south pole."""
        invalid_geo = {
            "latitude": -90.1,
            "longitude": 0,
            "location_name": "Invalid Location",
        }
        with pytest.raises(ValidationError):
            GeoPointModel(**invalid_geo)

    def test_longitude_exceeds_dateline_east(self):
        """Test longitude exceeding east dateline."""
        invalid_geo = {
            "latitude": 0,
            "longitude": 180.1,
            "location_name": "Invalid Location",
        }
        with pytest.raises(ValidationError):
            GeoPointModel(**invalid_geo)

    def test_longitude_exceeds_dateline_west(self):
        """Test longitude exceeding west dateline."""
        invalid_geo = {
            "latitude": 0,
            "longitude": -180.1,
            "location_name": "Invalid Location",
        }
        with pytest.raises(ValidationError):
            GeoPointModel(**invalid_geo)


class TestBilingualFieldValidation:
    """Test bilingual field validation."""

    def test_valid_bilingual_fields(self):
        """Test valid bilingual fields."""
        bilingual = {
            "name_en": "Suez Canal",
            "name_ar": "قناة السويس",
        }
        model = BilingualFieldModel(**bilingual)
        assert model.name_en == "Suez Canal"
        assert model.name_ar == "قناة السويس"

    def test_missing_english_field(self):
        """Test missing English field."""
        incomplete = {
            "name_ar": "قناة السويس",
        }
        with pytest.raises(ValidationError):
            BilingualFieldModel(**incomplete)

    def test_missing_arabic_field(self):
        """Test missing Arabic field."""
        incomplete = {
            "name_en": "Suez Canal",
        }
        with pytest.raises(ValidationError):
            BilingualFieldModel(**incomplete)

    def test_empty_bilingual_field(self):
        """Test empty bilingual field."""
        invalid = {
            "name_en": "",
            "name_ar": "قناة السويس",
        }
        with pytest.raises(ValidationError):
            BilingualFieldModel(**invalid)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
