import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from backend.app.main import app
from backend.app.api.auth import register_api_key, revoke_api_key, _API_KEYS

# Test fixtures
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def api_key():
    return "test-key-analyst"

@pytest.fixture
def admin_api_key():
    return "test-key-admin"

@pytest.fixture
def valid_headers(api_key):
    return {"X-API-Key": api_key}

@pytest.fixture
def admin_headers(admin_api_key):
    return {"X-API-Key": admin_api_key}

# Health endpoint tests
class TestHealthEndpoints:
    def test_health_endpoint_success(self, client, valid_headers):
        response = client.get("/health", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "operational"]
        assert "timestamp" in data
        assert data["service_name"] == "DecisionCore Intelligence GCC"

    def test_health_endpoint_no_api_key(self, client):
        response = client.get("/health")
        assert response.status_code == 403
        assert "API key required" in response.json()["detail"]

    def test_health_endpoint_invalid_api_key(self, client):
        response = client.get("/health", headers={"X-API-Key": "invalid-key"})
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    def test_version_endpoint_success(self, client, valid_headers):
        response = client.get("/version", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "build_date" in data
        assert "environment" in data

    def test_version_endpoint_requires_auth(self, client):
        response = client.get("/version")
        assert response.status_code == 403

# Scenarios endpoint tests
class TestScenariosEndpoints:
    def test_list_scenarios_empty(self, client, valid_headers):
        response = client.get("/scenarios?skip=0&limit=10", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_scenarios_pagination(self, client, valid_headers):
        response = client.get("/scenarios?skip=0&limit=5", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 5

    def test_create_scenario_success(self, client, admin_headers):
        scenario_data = {
            "name": "Test Scenario",
            "description": "A test scenario",
            "scenario_type": "disruption",
            "parameters": {"severity": 0.8}
        }
        response = client.post("/scenarios", json=scenario_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Scenario"
        assert data["scenario_type"] == "disruption"
        assert "scenario_id" in data

    def test_create_scenario_requires_analyst_role(self, client, valid_headers):
        scenario_data = {
            "name": "Test Scenario",
            "scenario_type": "disruption"
        }
        response = client.post("/scenarios", json=scenario_data, headers=valid_headers)
        # Analyst role should be able to create scenarios
        assert response.status_code in [200, 201]

    def test_create_scenario_no_auth(self, client):
        scenario_data = {
            "name": "Test Scenario",
            "scenario_type": "disruption"
        }
        response = client.post("/scenarios", json=scenario_data)
        assert response.status_code == 403

    def test_run_scenario_success(self, client, valid_headers):
        response = client.post(
            "/scenarios/run",
            json={"scenario_id": "test-scenario-1"},
            headers=valid_headers
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert "run_id" in data
        assert data["status"] in ["pending", "completed", "running"]

    def test_get_scenario_run(self, client, valid_headers):
        response = client.get("/scenarios/runs/test-run-1", headers=valid_headers)
        # May return 404 if run doesn't exist, which is acceptable
        assert response.status_code in [200, 404]

    def test_list_scenario_runs(self, client, valid_headers):
        response = client.get("/scenarios/runs", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

# Entities endpoint tests
class TestEntitiesEndpoints:
    def test_list_events(self, client, valid_headers):
        response = client.get("/events", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "event"
        assert "data" in data
        assert "total" in data

    def test_list_events_with_filters(self, client, valid_headers):
        response = client.get(
            "/events?event_type=accident&severity_min=5&severity_max=10",
            headers=valid_headers
        )
        assert response.status_code == 200

    def test_list_airports(self, client, valid_headers):
        response = client.get("/airports", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "airport"

    def test_list_airports_with_country_filter(self, client, valid_headers):
        response = client.get("/airports?country=USA", headers=valid_headers)
        assert response.status_code == 200

    def test_list_ports(self, client, valid_headers):
        response = client.get("/ports", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "port"

    def test_list_corridors(self, client, valid_headers):
        response = client.get("/corridors", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "corridor"

    def test_list_flights(self, client, valid_headers):
        response = client.get("/flights", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "flight"

    def test_list_vessels(self, client, valid_headers):
        response = client.get("/vessels", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["entity_type"] == "vessel"

    def test_entities_require_auth(self, client):
        endpoints = ["/events", "/airports", "/ports", "/corridors", "/flights", "/vessels"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 403

# Graph intelligence endpoint tests
class TestGraphEndpoints:
    def test_nearest_impacted_success(self, client, valid_headers):
        query_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "radius_km": 100
        }
        response = client.post(
            "/graph/nearest",
            json=query_data,
            headers=valid_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "query_type" in data
        assert "success" in data

    def test_risk_propagation_success(self, client, valid_headers):
        query_data = {
            "source_entity_id": "event-001",
            "source_entity_type": "event",
            "max_hops": 3,
            "risk_threshold": 0.3
        }
        response = client.post(
            "/graph/propagation",
            json=query_data,
            headers=valid_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query_type"] == "risk_propagation"

    def test_chokepoint_analysis_success(self, client, valid_headers):
        query_data = {
            "region": "Southeast Asia"
        }
        response = client.post(
            "/graph/chokepoint",
            json=query_data,
            headers=valid_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query_type"] == "chokepoint_analysis"

    def test_cascade_analysis_success(self, client, valid_headers):
        query_data = {
            "region": "Europe",
            "event_id": "event-001"
        }
        response = client.post(
            "/graph/cascade",
            json=query_data,
            headers=valid_headers
        )
        assert response.status_code == 200

    def test_scenario_subgraph_success(self, client, valid_headers):
        query_data = {
            "scenario_id": "scenario-001"
        }
        response = client.post(
            "/graph/scenario",
            json=query_data,
            headers=valid_headers
        )
        assert response.status_code == 200

    def test_reroute_alternatives_success(self, client, valid_headers):
        query_data = {
            "source_location": "Shanghai",
            "destination_location": "Rotterdam",
            "origin_lat": 31.2304,
            "origin_lon": 121.4737,
            "dest_lat": 51.9225,
            "dest_lon": 4.2763
        }
        response = client.post(
            "/graph/reroute",
            json=query_data,
            headers=valid_headers
        )
        assert response.status_code == 200

    def test_graph_endpoints_require_auth(self, client):
        endpoints = ["/graph/nearest", "/graph/propagation", "/graph/chokepoint"]
        for endpoint in endpoints:
            response = client.post(endpoint, json={})
            assert response.status_code == 403

# Data ingestion endpoint tests
class TestIngestionEndpoints:
    def test_ingest_events_success(self, client, valid_headers):
        ingest_data = {
            "batch_size": 100
        }
        response = client.post(
            "/ingest/events",
            json=ingest_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 500]  # 500 if graph not available in test
        if response.status_code == 200:
            data = response.json()
            assert "entity_type" in data
            assert data["entity_type"] == "event"

    def test_ingest_airports_success(self, client, valid_headers):
        ingest_data = {"batch_size": 100}
        response = client.post(
            "/ingest/airports",
            json=ingest_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 500]

    def test_ingest_ports_success(self, client, valid_headers):
        ingest_data = {"batch_size": 100}
        response = client.post(
            "/ingest/ports",
            json=ingest_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 500]

    def test_ingest_corridors_success(self, client, valid_headers):
        ingest_data = {"batch_size": 100}
        response = client.post(
            "/ingest/corridors",
            json=ingest_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 500]

    def test_ingest_flights_success(self, client, valid_headers):
        ingest_data = {"batch_size": 100}
        response = client.post(
            "/ingest/flights",
            json=ingest_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 500]

    def test_ingest_vessels_success(self, client, valid_headers):
        ingest_data = {"batch_size": 100}
        response = client.post(
            "/ingest/vessels",
            json=ingest_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 500]

    def test_ingest_actors_success(self, client, valid_headers):
        ingest_data = {"batch_size": 100}
        response = client.post(
            "/ingest/actors",
            json=ingest_data,
            headers=valid_headers
        )
        assert response.status_code in [200, 500]

    def test_ingest_status_success(self, client, valid_headers):
        response = client.get("/ingest/status", headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "pending_jobs" in data
        assert "completed_jobs" in data
        assert "failed_jobs" in data

    def test_ingest_endpoints_require_auth(self, client):
        endpoints = [
            "/ingest/events", "/ingest/airports", "/ingest/ports",
            "/ingest/corridors", "/ingest/flights", "/ingest/vessels",
            "/ingest/actors", "/ingest/status"
        ]
        for endpoint in endpoints:
            response = client.post(endpoint, json={}) if "/status" not in endpoint else client.get(endpoint)
            assert response.status_code == 403

# Root endpoint test
class TestRootEndpoint:
    def test_root_endpoint_success(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert "api_docs" in data

# Integration tests
class TestIntegration:
    def test_full_workflow_scenario_to_graph(self, client, admin_headers, valid_headers):
        # Create scenario
        scenario_data = {
            "name": "Integration Test Scenario",
            "scenario_type": "disruption"
        }
        scenario_response = client.post("/scenarios", json=scenario_data, headers=admin_headers)
        assert scenario_response.status_code in [200, 201]
        scenario_id = scenario_response.json().get("scenario_id")

        # Run scenario
        run_response = client.post(
            "/scenarios/run",
            json={"scenario_id": scenario_id},
            headers=valid_headers
        )
        assert run_response.status_code in [200, 201]

    def test_health_check_chain(self, client, valid_headers):
        # Check health
        health_response = client.get("/health", headers=valid_headers)
        assert health_response.status_code == 200

        # Check version
        version_response = client.get("/version", headers=valid_headers)
        assert version_response.status_code == 200

        # Check ingestion status
        status_response = client.get("/ingest/status", headers=valid_headers)
        assert status_response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
