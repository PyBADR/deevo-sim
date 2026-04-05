"""
Impact Observatory | مرصد الأثر — V4 End-to-End Test Suite
Tests the complete pipeline from POST /runs through all GET endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture(scope="module")
def admin_headers():
    return {"X-IO-API-Key": "io_master_key_2026"}


@pytest.fixture(scope="module")
def viewer_headers():
    return {"X-IO-API-Key": "io_viewer_key_2026"}


@pytest.fixture(scope="module")
def run_id(client, admin_headers):
    """Execute a Hormuz pipeline run and return the run_id."""
    r = client.post(
        "/api/v1/runs",
        json={"template_id": "hormuz-closure-v1"},
        headers=admin_headers,
    )
    assert r.status_code == 202
    data = r.json()["data"]
    assert data["status"] == "completed"
    return data["run_id"]


# ── Boot tests ─────────────────────────────────────────────────────────

class TestBoot:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["service"] == "Impact Observatory | مرصد الأثر"

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_version(self, client):
        r = client.get("/version")
        assert r.status_code == 200
        assert r.json()["version"] == "4.0.0"

    def test_openapi(self, client):
        r = client.get("/api/openapi.json")
        assert r.status_code == 200
        paths = list(r.json()["paths"].keys())
        assert len(paths) >= 20


# ── Pipeline tests ─────────────────────────────────────────────────────

class TestPipeline:
    def test_run_completes(self, client, admin_headers):
        r = client.post(
            "/api/v1/runs",
            json={"template_id": "hormuz-closure-v1"},
            headers=admin_headers,
        )
        assert r.status_code == 202
        data = r.json()["data"]
        assert data["status"] == "completed"
        assert data["stages_completed"] >= 9

    def test_run_unknown_template(self, client, admin_headers):
        r = client.post(
            "/api/v1/runs",
            json={"template_id": "nonexistent"},
            headers=admin_headers,
        )
        assert r.status_code == 202
        assert r.json()["data"]["status"] == "failed"

    def test_run_performance(self, client, admin_headers):
        r = client.post(
            "/api/v1/runs",
            json={"template_id": "hormuz-closure-v1"},
            headers=admin_headers,
        )
        ms = r.json()["data"].get("computed_in_ms", 99999)
        assert ms < 5000, f"Pipeline too slow: {ms}ms"


# ── Status endpoint ────────────────────────────────────────────────────

class TestStatus:
    def test_status_found(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/status", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["status"] == "completed"
        assert data["stages_completed"] >= 9

    def test_status_not_found(self, client, admin_headers):
        r = client.get("/api/v1/runs/nonexistent/status", headers=admin_headers)
        assert r.status_code == 404

    def test_status_has_audit_hash(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/status", headers=admin_headers)
        audit = r.json()["data"].get("audit_hash", "")
        assert len(audit) > 10


# ── Financial endpoint ─────────────────────────────────────────────────

class TestFinancial:
    def test_financial_returns_data(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/financial", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["count"] == 12
        assert data["aggregate"]["total_loss"] > 0

    def test_financial_has_entities(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/financial", headers=admin_headers)
        entities = r.json()["data"]["entities"]
        assert len(entities) == 12


# ── Banking endpoint ───────────────────────────────────────────────────

class TestBanking:
    def test_banking_returns_data(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/banking", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["data"]["count"] >= 1


# ── Insurance endpoint ─────────────────────────────────────────────────

class TestInsurance:
    def test_insurance_returns_data(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/insurance", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["data"]["count"] >= 1


# ── Fintech endpoint ───────────────────────────────────────────────────

class TestFintech:
    def test_fintech_returns_data(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/fintech", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["data"]["count"] >= 1


# ── Decision endpoint ──────────────────────────────────────────────────

class TestDecision:
    def test_decision_returns_actions(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/decision", headers=admin_headers)
        assert r.status_code == 200
        actions = r.json()["data"].get("actions", [])
        assert len(actions) == 3

    def test_decision_blocked_for_viewer(self, client, viewer_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/decision", headers=viewer_headers)
        assert r.status_code == 403


# ── Business Impact endpoint ───────────────────────────────────────────

class TestBusinessImpact:
    def test_business_impact_returns_data(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/business-impact", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["business_severity"] in ("low", "medium", "high", "severe")

    def test_business_impact_has_peak_loss(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/business-impact", headers=admin_headers)
        assert r.json()["data"]["peak_cumulative_loss"] > 0


# ── Timeline endpoint ──────────────────────────────────────────────────

class TestTimeline:
    def test_timeline_has_14_steps(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/timeline", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)
        assert len(data) == 14


# ── Regulatory Timeline endpoint ───────────────────────────────────────

class TestRegulatoryTimeline:
    def test_regulatory_returns_data(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/regulatory-timeline", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["data"]  # non-empty


# ── Executive Explanation endpoint ─────────────────────────────────────

class TestExecutiveExplanation:
    def test_executive_returns_data(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/executive-explanation", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["data"]


# ── RBAC tests ─────────────────────────────────────────────────────────

class TestRBAC:
    def test_viewer_can_read_financial(self, client, viewer_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/financial", headers=viewer_headers)
        assert r.status_code == 200

    def test_viewer_blocked_from_decision(self, client, viewer_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/decision", headers=viewer_headers)
        assert r.status_code == 403

    def test_viewer_can_read_explanation(self, client, viewer_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/explanation", headers=viewer_headers)
        assert r.status_code == 200

    def test_viewer_can_read_business_impact(self, client, viewer_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/business-impact", headers=viewer_headers)
        assert r.status_code == 200


# ── v4 Envelope format tests ──────────────────────────────────────────

class TestEnvelope:
    def test_success_envelope(self, client, admin_headers, run_id):
        r = client.get(f"/api/v1/runs/{run_id}/financial", headers=admin_headers)
        body = r.json()
        assert "trace_id" in body
        assert "generated_at" in body
        assert "data" in body
        assert "warnings" in body

    def test_error_envelope(self, client, admin_headers):
        r = client.get("/api/v1/runs/nonexistent/financial", headers=admin_headers)
        body = r.json()
        assert "error" in body
        assert body["error"]["code"] == "RUN_NOT_FOUND"
