"""Tests for Data Reality Foundation connectors.

Tests cover:
  1. BaseConnector — pipeline mechanics, duplicate detection, revision handling
  2. CBKConnector — HTML parsing, normalization, field mapping
  3. EIAConnector — API v2 + STEO parsing, period handling, unit conversion
  4. IMFConnector — WEO data mapping, provisional flagging, multi-country

All tests use mock HTTP responses and an in-memory async session stub
to avoid real network calls and database dependencies.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# ═════════════════════════════════════════════════════════════════════════════
# Lightweight async session stub — no real database needed
# ═════════════════════════════════════════════════════════════════════════════


class FakeResult:
    """Mimics SQLAlchemy result for scalar_one_or_none / scalars().all()."""

    def __init__(self, rows=None):
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return self

    def all(self):
        return self._rows


class FakeAsyncSession:
    """In-memory async session stub that records ORM operations."""

    def __init__(self):
        self.added: list = []
        self.flushed: bool = False
        self._execute_results: list = []  # stack of FakeResult
        self._default_result = FakeResult()

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, objs):
        self.added.extend(objs)

    async def flush(self):
        self.flushed = True

    async def execute(self, stmt):
        if self._execute_results:
            return self._execute_results.pop(0)
        return self._default_result

    async def merge(self, obj):
        self.added.append(obj)
        return obj

    def push_result(self, result: FakeResult):
        """Push a result to be returned by the next execute() call."""
        self._execute_results.append(result)


# ═════════════════════════════════════════════════════════════════════════════
# Import connectors
# ═════════════════════════════════════════════════════════════════════════════

from src.data_foundation.connectors.base import (
    BaseConnector,
    ConnectorResult,
    NormalizedRecord,
    _content_hash,
)
from src.data_foundation.connectors.cbk import CBKConnector
from src.data_foundation.connectors.eia import EIAConnector
from src.data_foundation.connectors.imf import IMFConnector


# ═════════════════════════════════════════════════════════════════════════════
# Test: Base connector utilities
# ═════════════════════════════════════════════════════════════════════════════


class TestContentHash:
    def test_deterministic(self):
        payload = {"a": 1, "b": [2, 3]}
        assert _content_hash(payload) == _content_hash(payload)

    def test_key_order_independent(self):
        """SHA-256 must be same regardless of dict key insertion order."""
        h1 = _content_hash({"z": 1, "a": 2})
        h2 = _content_hash({"a": 2, "z": 1})
        assert h1 == h2

    def test_different_payloads(self):
        h1 = _content_hash({"x": 1})
        h2 = _content_hash({"x": 2})
        assert h1 != h2

    def test_is_sha256(self):
        h = _content_hash({"test": True})
        assert len(h) == 64  # SHA-256 hex digest length
        assert all(c in "0123456789abcdef" for c in h)


class TestNormalizedRecord:
    def test_create_basic(self):
        rec = NormalizedRecord(
            indicator_code="GDP_GROWTH_KW",
            indicator_id="ic-001",
            value=2.5,
            unit="percent",
            country="KW",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            frequency="ANNUAL",
            observation_date=date(2024, 6, 15),
        )
        assert rec.indicator_code == "GDP_GROWTH_KW"
        assert rec.confidence_score == 0.8  # default
        assert rec.is_provisional is False

    def test_defaults(self):
        rec = NormalizedRecord(
            indicator_code="TEST",
            indicator_id="ic-999",
            value=1.0,
            unit="test",
            country="KW",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            frequency="ANNUAL",
            observation_date=date.today(),
        )
        assert rec.confidence_method == "SOURCE_DECLARED"
        assert rec.entity_id is None


class TestBaseConnectorValidation:
    """Test the validate_record method from BaseConnector."""

    def _make_valid_record(self, **overrides) -> NormalizedRecord:
        defaults = dict(
            indicator_code="TEST",
            indicator_id="ic-999",
            value=1.0,
            unit="percent",
            country="KW",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            frequency="ANNUAL",
            observation_date=date.today(),
        )
        defaults.update(overrides)
        return NormalizedRecord(**defaults)

    def test_valid_record_passes(self):
        session = FakeAsyncSession()
        connector = CBKConnector(session)
        rec = self._make_valid_record()
        errors = connector.validate_record(rec)
        assert errors == []

    def test_empty_indicator_code(self):
        session = FakeAsyncSession()
        connector = CBKConnector(session)
        rec = self._make_valid_record(indicator_code="")
        errors = connector.validate_record(rec)
        assert any("indicator_code" in e for e in errors)

    def test_empty_country(self):
        session = FakeAsyncSession()
        connector = CBKConnector(session)
        rec = self._make_valid_record(country="")
        errors = connector.validate_record(rec)
        assert any("country" in e for e in errors)

    def test_period_start_after_end(self):
        session = FakeAsyncSession()
        connector = CBKConnector(session)
        rec = self._make_valid_record(
            period_start=date(2025, 1, 1),
            period_end=date(2024, 1, 1),
        )
        errors = connector.validate_record(rec)
        assert any("period_start" in e for e in errors)

    def test_confidence_out_of_range(self):
        session = FakeAsyncSession()
        connector = CBKConnector(session)
        rec = self._make_valid_record(confidence_score=1.5)
        errors = connector.validate_record(rec)
        assert any("confidence_score" in e for e in errors)


# ═════════════════════════════════════════════════════════════════════════════
# Test: CBK Connector
# ═════════════════════════════════════════════════════════════════════════════


class TestCBKConnector:
    """Tests for CBK exchange rate parsing and normalization."""

    def _make_connector(self) -> tuple[CBKConnector, FakeAsyncSession]:
        session = FakeAsyncSession()
        return CBKConnector(session), session

    def test_source_id(self):
        c, _ = self._make_connector()
        assert c.source_id == "src-cbk-bulletin"

    def test_source_url(self):
        c, _ = self._make_connector()
        assert "cbk.gov.kw" in c.source_url

    def test_parse_exchange_rate_html_with_rate(self):
        """CBK HTML containing a KWD/USD rate in the 0.30x range."""
        c, _ = self._make_connector()
        html = """
        <html><body>
        <table class="exchange-rates">
          <tr><td>USD</td><td>United States Dollar</td><td>0.3067</td></tr>
          <tr><td>EUR</td><td>Euro</td><td>0.2801</td></tr>
        </table>
        </body></html>
        """
        rates = c._parse_cbk_exchange_rates(html)
        assert "USD" in rates
        assert abs(rates["USD"]["rate"] - 0.3067) < 0.001

    def test_parse_exchange_rate_html_with_embedded_json(self):
        """CBK page with exchange rates in a JS variable."""
        c, _ = self._make_connector()
        html = """
        <script>
        var exchangeRates = [{"currency_code": "USD", "rate": 0.3068}];
        </script>
        """
        rates = c._parse_cbk_exchange_rates(html)
        assert "USD" in rates
        assert abs(rates["USD"]["rate"] - 0.3068) < 0.001

    def test_parse_exchange_rate_html_no_data(self):
        """Graceful handling when page has no exchange rate data."""
        c, _ = self._make_connector()
        rates = c._parse_cbk_exchange_rates("<html><body>No data</body></html>")
        assert rates == {}

    def test_normalize_fx_rate(self):
        """Normalize a raw payload with KWD/USD exchange rate."""
        c, _ = self._make_connector()
        payload = {
            "source": "cbk",
            "fetch_date": "2026-04-11",
            "exchange_rates": {
                "USD": {"rate": 0.3067, "buy": 0.3060, "sell": 0.3074},
            },
            "bulletin": {},
        }
        records = c.normalize(payload)
        assert len(records) >= 1
        fx_rec = next(r for r in records if r.indicator_code == "FX_KWD_USD")
        assert fx_rec.value == 0.3067
        assert fx_rec.unit == "KWD_per_USD"
        assert fx_rec.country == "KW"
        assert fx_rec.indicator_id == "ic-012"
        assert fx_rec.confidence_score == 0.95

    def test_normalize_with_bulletin(self):
        """Normalize a payload with both FX and bulletin data."""
        c, _ = self._make_connector()
        payload = {
            "source": "cbk",
            "fetch_date": "2026-04-11",
            "exchange_rates": {
                "USD": {"rate": 0.3067, "buy": None, "sell": None},
            },
            "bulletin": {
                "discount_rate": 4.25,
                "m2": 42500,
                "total_credit": 48200,
                "forex_reserves": 48500,
            },
        }
        records = c.normalize(payload)
        codes = {r.indicator_code for r in records}
        assert "FX_KWD_USD" in codes
        assert "CBK_DISCOUNT_RATE_KW" in codes
        assert "CBK_M2_KW" in codes
        assert "CBK_TOTAL_CREDIT_KW" in codes
        assert "CBK_FOREX_RESERVES_KW" in codes

        dr = next(r for r in records if r.indicator_code == "CBK_DISCOUNT_RATE_KW")
        assert dr.value == 4.25
        assert dr.unit == "percent"
        assert dr.indicator_id == "ic-006"

        m2 = next(r for r in records if r.indicator_code == "CBK_M2_KW")
        assert m2.value == 42500
        assert m2.unit == "KWD_mn"

    def test_normalize_empty_rates(self):
        """Empty exchange rates → no observations."""
        c, _ = self._make_connector()
        payload = {
            "source": "cbk",
            "fetch_date": "2026-04-11",
            "exchange_rates": {},
            "bulletin": {},
        }
        records = c.normalize(payload)
        assert records == []

    def test_monthly_period_boundaries(self):
        """Bulletin indicators should have proper month start/end periods."""
        c, _ = self._make_connector()
        payload = {
            "source": "cbk",
            "fetch_date": "2026-04-11",
            "exchange_rates": {},
            "bulletin": {"discount_rate": 4.0},
        }
        records = c.normalize(payload)
        dr = records[0]
        assert dr.period_start.day == 1  # Month start
        assert dr.period_end.month == dr.period_start.month  # Same month
        # Last day of month
        next_month = (dr.period_start + timedelta(days=32)).replace(day=1)
        expected_end = next_month - timedelta(days=1)
        assert dr.period_end == expected_end

    @pytest.mark.asyncio
    async def test_run_pipeline_success(self):
        """Full pipeline run with mocked HTTP."""
        c, session = self._make_connector()

        mock_payload = {
            "source": "cbk",
            "fetch_date": "2026-04-11",
            "exchange_rates": {"USD": {"rate": 0.3067, "buy": None, "sell": None}},
            "bulletin": {},
        }

        # Mock: no duplicate raw record, no existing observation, no source registry
        session.push_result(FakeResult())  # dup check
        session.push_result(FakeResult())  # existing obs lookup
        session.push_result(FakeResult())  # source registry

        with patch.object(c, "fetch_raw", return_value=mock_payload):
            result = await c.run(trigger_type="MANUAL", triggered_by="test")

        assert result.status in ("COMPLETED", "PARTIAL")
        assert result.source_id == "src-cbk-bulletin"
        assert result.records_fetched == 1
        assert result.records_new == 1
        assert result.observations_created >= 1

        # Check ORM objects were added to session
        added_types = {type(obj).__name__ for obj in session.added}
        assert "SourceFetchRunORM" in added_types
        assert "RawSourceRecordORM" in added_types
        assert "NormalizationRunORM" in added_types
        assert "CanonicalObservationORM" in added_types

    @pytest.mark.asyncio
    async def test_run_pipeline_duplicate(self):
        """Pipeline correctly detects duplicate content_hash."""
        c, session = self._make_connector()

        mock_payload = {
            "source": "cbk",
            "fetch_date": "2026-04-11",
            "exchange_rates": {"USD": {"rate": 0.3067, "buy": None, "sell": None}},
            "bulletin": {},
        }

        # Mock: existing raw record with same hash
        existing_raw = MagicMock()
        existing_raw.record_id = "raw-existing-001"
        session.push_result(FakeResult([existing_raw]))  # dup check returns match

        # Existing observation with same value → should be skipped
        existing_obs = MagicMock()
        existing_obs.value = 0.3067
        existing_obs.revision_number = 0
        session.push_result(FakeResult([existing_obs]))  # existing obs

        session.push_result(FakeResult())  # source registry

        with patch.object(c, "fetch_raw", return_value=mock_payload):
            result = await c.run()

        assert result.records_duplicate == 1
        assert result.observations_skipped >= 1

    @pytest.mark.asyncio
    async def test_run_pipeline_revision(self):
        """Pipeline updates an existing observation when value changes."""
        c, session = self._make_connector()

        mock_payload = {
            "source": "cbk",
            "fetch_date": "2026-04-11",
            "exchange_rates": {"USD": {"rate": 0.3070, "buy": None, "sell": None}},
            "bulletin": {},
        }

        # Not a duplicate payload
        session.push_result(FakeResult())  # dup check

        # Existing observation with different value
        existing_obs = MagicMock()
        existing_obs.value = 0.3067  # Old value
        existing_obs.revision_number = 0
        session.push_result(FakeResult([existing_obs]))  # existing obs

        session.push_result(FakeResult())  # source registry

        with patch.object(c, "fetch_raw", return_value=mock_payload):
            result = await c.run()

        assert result.observations_updated >= 1
        # Check the existing obs was mutated
        assert existing_obs.previous_value == 0.3067
        assert existing_obs.value == 0.3070
        assert existing_obs.revision_number == 1
        assert existing_obs.change_absolute is not None

    @pytest.mark.asyncio
    async def test_run_pipeline_fetch_failure(self):
        """Pipeline handles fetch errors gracefully."""
        c, session = self._make_connector()

        # No results needed since fetch will fail before queries
        with patch.object(c, "fetch_raw", side_effect=Exception("Network timeout")):
            result = await c.run()

        assert result.status == "FAILED"
        assert "Network timeout" in result.error_message

        # Fetch run should be marked FAILED
        fetch_runs = [o for o in session.added if type(o).__name__ == "SourceFetchRunORM"]
        assert len(fetch_runs) == 1
        assert fetch_runs[0].status == "FAILED"
        assert fetch_runs[0].error_code == "Exception"


# ═════════════════════════════════════════════════════════════════════════════
# Test: EIA Connector
# ═════════════════════════════════════════════════════════════════════════════


class TestEIAConnector:
    """Tests for EIA oil/energy data parsing and normalization."""

    def _make_connector(self, api_key: str = "") -> tuple[EIAConnector, FakeAsyncSession]:
        session = FakeAsyncSession()
        return EIAConnector(session, api_key=api_key), session

    def test_source_id(self):
        c, _ = self._make_connector()
        assert c.source_id == "src-opec-momr"

    def test_source_url_with_key(self):
        c, _ = self._make_connector(api_key="test-key-123")
        assert "api.eia.gov" in c.source_url

    def test_source_url_without_key(self):
        c, _ = self._make_connector()
        assert "eia.gov" in c.source_url

    def test_normalize_api_v2_brent(self):
        """Normalize EIA API v2 response for Brent crude."""
        c, _ = self._make_connector()
        payload = {
            "source": "eia",
            "fetch_date": "2026-04-11",
            "brent": {
                "response": {
                    "data": [
                        {"period": "2026-03", "value": 72.5},
                        {"period": "2026-02", "value": 78.3},
                        {"period": "2026-01", "value": 75.1},
                    ]
                }
            },
            "opec_basket": {},
            "production": {},
        }
        records = c.normalize(payload)
        brent_recs = [r for r in records if r.indicator_code == "BRENT_SPOT"]
        assert len(brent_recs) == 3

        # Most recent first
        latest = brent_recs[0]
        assert latest.value == 72.5
        assert latest.unit == "USD_per_bbl"
        assert latest.indicator_id == "ic-009"
        assert latest.period_start == date(2026, 3, 1)
        assert latest.period_end == date(2026, 3, 31)

    def test_normalize_api_v2_production(self):
        """Normalize Kuwait oil production with TBPD → mbpd conversion."""
        c, _ = self._make_connector()
        payload = {
            "source": "eia",
            "fetch_date": "2026-04-11",
            "brent": {},
            "opec_basket": {},
            "production": {
                "response": {
                    "data": [
                        {"period": "2026-01", "value": 2650},  # TBPD
                    ]
                }
            },
        }
        records = c.normalize(payload)
        prod_recs = [r for r in records if r.indicator_code == "KW_OIL_PRODUCTION"]
        assert len(prod_recs) == 1
        # 2650 TBPD → 2.650 mbpd
        assert prod_recs[0].value == 2.65
        assert prod_recs[0].unit == "mbpd"
        assert prod_recs[0].indicator_id == "ic-011"

    def test_normalize_steo_format(self):
        """Normalize EIA STEO response format."""
        c, _ = self._make_connector()
        payload = {
            "source": "eia",
            "fetch_date": "2026-04-11",
            "brent": {
                "BREPGP": {
                    "dates": ["2026-01", "2026-02", "2026-03"],
                    "values": [75.0, 78.0, 72.5],
                }
            },
            "opec_basket": {},
            "production": {},
        }
        records = c.normalize(payload)
        brent_recs = [r for r in records if r.indicator_code == "BRENT_SPOT"]
        assert len(brent_recs) == 3

    def test_normalize_list_format(self):
        """Normalize EIA data in list-of-pairs format."""
        c, _ = self._make_connector()
        payload = {
            "source": "eia",
            "fetch_date": "2026-04-11",
            "brent": {
                "prices": [
                    ["2026-01", 75.0],
                    ["2026-02", 78.0],
                ],
            },
            "opec_basket": {},
            "production": {},
        }
        records = c.normalize(payload)
        brent_recs = [r for r in records if r.indicator_code == "BRENT_SPOT"]
        assert len(brent_recs) == 2

    def test_parse_period_daily(self):
        c, _ = self._make_connector()
        s, e = c._parse_eia_period("2026-04-11")
        assert s == date(2026, 4, 11)
        assert e == date(2026, 4, 11)

    def test_parse_period_monthly(self):
        c, _ = self._make_connector()
        s, e = c._parse_eia_period("2026-03")
        assert s == date(2026, 3, 1)
        assert e == date(2026, 3, 31)

    def test_parse_period_quarterly(self):
        c, _ = self._make_connector()
        s, e = c._parse_eia_period("2026Q1")
        assert s == date(2026, 1, 1)
        assert e == date(2026, 3, 31)

    def test_parse_period_annual(self):
        c, _ = self._make_connector()
        s, e = c._parse_eia_period("2025")
        assert s == date(2025, 1, 1)
        assert e == date(2025, 12, 31)

    def test_parse_period_invalid(self):
        c, _ = self._make_connector()
        s, e = c._parse_eia_period("not-a-date")
        assert s is None
        assert e is None

    def test_normalize_with_none_values_skipped(self):
        """None values in API response should be silently skipped."""
        c, _ = self._make_connector()
        payload = {
            "source": "eia",
            "fetch_date": "2026-04-11",
            "brent": {
                "response": {
                    "data": [
                        {"period": "2026-03", "value": 72.5},
                        {"period": "2026-02", "value": None},  # Should skip
                        {"period": "2026-01", "value": 75.1},
                    ]
                }
            },
            "opec_basket": {},
            "production": {},
        }
        records = c.normalize(payload)
        brent_recs = [r for r in records if r.indicator_code == "BRENT_SPOT"]
        assert len(brent_recs) == 2

    def test_normalize_error_response(self):
        """Error responses should produce zero records."""
        c, _ = self._make_connector()
        payload = {
            "source": "eia",
            "fetch_date": "2026-04-11",
            "brent": {"error": "API key invalid"},
            "opec_basket": {"error": "timeout"},
            "production": {},
        }
        records = c.normalize(payload)
        assert records == []

    @pytest.mark.asyncio
    async def test_run_pipeline(self):
        """Full pipeline run with mocked HTTP data."""
        c, session = self._make_connector()

        mock_payload = {
            "source": "eia",
            "fetch_date": "2026-04-11",
            "brent": {
                "response": {
                    "data": [
                        {"period": "2026-03", "value": 72.5},
                    ]
                }
            },
            "opec_basket": {},
            "production": {},
        }

        # No duplicate, no existing obs, no source registry
        session.push_result(FakeResult())  # dup check
        session.push_result(FakeResult())  # existing obs
        session.push_result(FakeResult())  # source registry

        with patch.object(c, "fetch_raw", return_value=mock_payload):
            result = await c.run()

        assert result.status in ("COMPLETED", "PARTIAL")
        assert result.observations_created >= 1


# ═════════════════════════════════════════════════════════════════════════════
# Test: IMF Connector
# ═════════════════════════════════════════════════════════════════════════════


class TestIMFConnector:
    """Tests for IMF WEO data mapping and normalization."""

    def _make_connector(self) -> tuple[IMFConnector, FakeAsyncSession]:
        session = FakeAsyncSession()
        return IMFConnector(session), session

    def test_source_id(self):
        c, _ = self._make_connector()
        assert c.source_id == "src-imf-weo"

    def test_source_url(self):
        c, _ = self._make_connector()
        assert "imf.org" in c.source_url

    def test_normalize_gdp_growth(self):
        """Normalize IMF GDP growth data for GCC countries."""
        c, _ = self._make_connector()
        payload = {
            "source": "imf",
            "fetch_date": "2026-04-11",
            "series": {
                "NGDP_RPCH": {
                    "values": {
                        "NGDP_RPCH": {
                            "KWT": {"2023": -2.2, "2024": 2.5, "2025": 3.1, "2026": 2.8},
                            "SAU": {"2023": -0.8, "2024": 4.2, "2025": 3.5, "2026": 3.0},
                            "ARE": {"2023": 3.6, "2024": 3.9, "2025": 4.0, "2026": 3.8},
                        }
                    }
                },
                "PCPIPCH": {"values": {}},
                "LUR": {"values": {}},
            },
        }
        records = c.normalize(payload)

        # Should get 12 records (3 countries * 4 years)
        gdp_recs = [r for r in records if r.indicator_code.startswith("GDP_GROWTH")]
        assert len(gdp_recs) == 12

        kw_2024 = next(r for r in gdp_recs if r.indicator_code == "GDP_GROWTH_KW" and r.period_start.year == 2024)
        assert kw_2024.value == 2.5
        assert kw_2024.indicator_id == "ic-001"
        assert kw_2024.country == "KW"
        assert kw_2024.unit == "percent"
        assert kw_2024.period_start == date(2024, 1, 1)
        assert kw_2024.period_end == date(2024, 12, 31)

    def test_normalize_provisional_flagging(self):
        """Future years should be marked as provisional (forecasts)."""
        c, _ = self._make_connector()
        current_year = date.today().year
        future_year = current_year + 1

        payload = {
            "source": "imf",
            "fetch_date": str(date.today()),
            "series": {
                "NGDP_RPCH": {
                    "values": {
                        "NGDP_RPCH": {
                            "KWT": {
                                str(current_year - 1): 2.0,
                                str(current_year): 2.5,
                                str(future_year): 3.0,
                            },
                        }
                    }
                },
                "PCPIPCH": {"values": {}},
                "LUR": {"values": {}},
            },
        }
        records = c.normalize(payload)

        past = next(r for r in records if r.period_start.year == current_year - 1)
        assert past.is_provisional is False
        assert past.confidence_score == 0.95

        forecast = next(r for r in records if r.period_start.year == future_year)
        assert forecast.is_provisional is True
        assert forecast.confidence_score == 0.70

    def test_normalize_inflation(self):
        """Normalize CPI inflation data."""
        c, _ = self._make_connector()
        payload = {
            "source": "imf",
            "fetch_date": "2026-04-11",
            "series": {
                "NGDP_RPCH": {"values": {}},
                "PCPIPCH": {
                    "values": {
                        "PCPIPCH": {
                            "KWT": {"2024": 3.5, "2025": 2.8},
                            "SAU": {"2024": 2.1, "2025": 2.5},
                        }
                    }
                },
                "LUR": {"values": {}},
            },
        }
        records = c.normalize(payload)
        cpi_recs = [r for r in records if r.indicator_code.startswith("CPI_INFLATION")]
        assert len(cpi_recs) == 4

        kw_cpi = next(r for r in cpi_recs if r.indicator_code == "CPI_INFLATION_KW" and r.period_start.year == 2024)
        assert kw_cpi.value == 3.5
        assert kw_cpi.indicator_id == "ic-004"

        sa_cpi = next(r for r in cpi_recs if r.indicator_code == "CPI_INFLATION_SA" and r.period_start.year == 2024)
        assert sa_cpi.value == 2.1
        assert sa_cpi.indicator_id == "ic-018"

    def test_normalize_unemployment(self):
        """Normalize unemployment rate data."""
        c, _ = self._make_connector()
        payload = {
            "source": "imf",
            "fetch_date": "2026-04-11",
            "series": {
                "NGDP_RPCH": {"values": {}},
                "PCPIPCH": {"values": {}},
                "LUR": {
                    "values": {
                        "LUR": {
                            "KWT": {"2024": 2.1, "2025": 2.3},
                        }
                    }
                },
            },
        }
        records = c.normalize(payload)
        unemp = [r for r in records if r.indicator_code == "UNEMPLOYMENT_KW"]
        assert len(unemp) == 2
        assert unemp[0].indicator_id == "ic-005"

    def test_normalize_empty_data(self):
        """Empty IMF response → no records."""
        c, _ = self._make_connector()
        payload = {
            "source": "imf",
            "fetch_date": "2026-04-11",
            "series": {
                "NGDP_RPCH": {"values": {}},
                "PCPIPCH": {"values": {}},
                "LUR": {"values": {}},
            },
        }
        records = c.normalize(payload)
        assert records == []

    def test_normalize_error_series(self):
        """Error in one series should not break others."""
        c, _ = self._make_connector()
        payload = {
            "source": "imf",
            "fetch_date": "2026-04-11",
            "series": {
                "NGDP_RPCH": {"error": "timeout"},
                "PCPIPCH": {
                    "values": {
                        "PCPIPCH": {
                            "KWT": {"2024": 3.5},
                        }
                    }
                },
                "LUR": {"error": "not found"},
            },
        }
        records = c.normalize(payload)
        assert len(records) == 1
        assert records[0].indicator_code == "CPI_INFLATION_KW"

    def test_normalize_null_values_skipped(self):
        """None values in IMF data are skipped."""
        c, _ = self._make_connector()
        payload = {
            "source": "imf",
            "fetch_date": "2026-04-11",
            "series": {
                "NGDP_RPCH": {
                    "values": {
                        "NGDP_RPCH": {
                            "KWT": {"2024": 2.5, "2025": None, "2026": 3.0},
                        }
                    }
                },
                "PCPIPCH": {"values": {}},
                "LUR": {"values": {}},
            },
        }
        records = c.normalize(payload)
        assert len(records) == 2

    def test_normalize_non_gcc_countries_ignored(self):
        """Countries not in our mapping should be silently ignored."""
        c, _ = self._make_connector()
        payload = {
            "source": "imf",
            "fetch_date": "2026-04-11",
            "series": {
                "NGDP_RPCH": {
                    "values": {
                        "NGDP_RPCH": {
                            "KWT": {"2024": 2.5},
                            "USA": {"2024": 2.1},  # Not in our map
                            "CHN": {"2024": 5.5},  # Not in our map
                        }
                    }
                },
                "PCPIPCH": {"values": {}},
                "LUR": {"values": {}},
            },
        }
        records = c.normalize(payload)
        assert len(records) == 1
        assert records[0].country == "KW"

    @pytest.mark.asyncio
    async def test_run_pipeline(self):
        """Full pipeline run with mocked HTTP data."""
        c, session = self._make_connector()

        mock_payload = {
            "source": "imf",
            "fetch_date": "2026-04-11",
            "series": {
                "NGDP_RPCH": {
                    "values": {
                        "NGDP_RPCH": {
                            "KWT": {"2024": 2.5, "2025": 3.1},
                            "SAU": {"2024": 4.2},
                        }
                    }
                },
                "PCPIPCH": {"values": {}},
                "LUR": {"values": {}},
            },
        }

        # No dup, no existing obs (3 records), no source registry
        session.push_result(FakeResult())  # dup check
        for _ in range(3):
            session.push_result(FakeResult())  # existing obs per record
        session.push_result(FakeResult())  # source registry

        with patch.object(c, "fetch_raw", return_value=mock_payload):
            result = await c.run()

        assert result.status in ("COMPLETED", "PARTIAL")
        assert result.source_id == "src-imf-weo"
        assert result.observations_created == 3

        # Verify CanonicalObservationORM objects in session
        obs = [o for o in session.added if type(o).__name__ == "CanonicalObservationORM"]
        assert len(obs) == 3
        codes = {o.indicator_code for o in obs}
        assert "GDP_GROWTH_KW" in codes
        assert "GDP_GROWTH_SA" in codes


# ═════════════════════════════════════════════════════════════════════════════
# Test: Package imports
# ═════════════════════════════════════════════════════════════════════════════


class TestPackageImports:
    """Verify the connectors package exports."""

    def test_import_base(self):
        from src.data_foundation.connectors import BaseConnector
        assert BaseConnector is not None

    def test_import_cbk(self):
        from src.data_foundation.connectors import CBKConnector
        assert CBKConnector.source_id == "src-cbk-bulletin"

    def test_import_eia(self):
        from src.data_foundation.connectors import EIAConnector
        assert EIAConnector.source_id == "src-opec-momr"

    def test_import_imf(self):
        from src.data_foundation.connectors import IMFConnector
        assert IMFConnector.source_id == "src-imf-weo"

    def test_all_exports(self):
        from src.data_foundation import connectors
        assert "BaseConnector" in connectors.__all__
        assert "CBKConnector" in connectors.__all__
        assert "EIAConnector" in connectors.__all__
        assert "IMFConnector" in connectors.__all__


# ═════════════════════════════════════════════════════════════════════════════
# Test: Cross-connector indicator coverage
# ═════════════════════════════════════════════════════════════════════════════


class TestIndicatorCoverage:
    """Verify all indicator_catalog.json entries have a connector."""

    def test_all_catalog_indicators_mapped(self):
        """Every indicator in the catalog must be reachable by at least one connector."""
        import json
        from pathlib import Path

        catalog_path = Path(__file__).parent.parent / "src" / "data_foundation" / "seed" / "indicator_catalog.json"
        with open(catalog_path) as f:
            catalog = json.load(f)

        catalog_codes = {entry["indicator_code"] for entry in catalog}

        # Collect all codes handled by connectors
        from src.data_foundation.connectors.cbk import _INDICATOR_MAP as cbk_map
        from src.data_foundation.connectors.eia import _INDICATOR_MAP as eia_map
        from src.data_foundation.connectors.imf import _INDICATOR_MAP as imf_map

        connector_codes: set[str] = set()
        connector_codes.update(cbk_map.keys())
        connector_codes.update(eia_map.keys())
        for series_map in imf_map.values():
            for country_meta in series_map.values():
                connector_codes.add(country_meta["indicator_code"])

        # Every catalog indicator should be mapped to a connector
        unmapped = catalog_codes - connector_codes
        # These indicators are served by other sources not covered by our 3 connectors:
        # FX_SAR_USD, FX_AED_USD — Bloomberg FX feed
        # SAMA_REPO_RATE_SA — SAMA bulletin (separate source)
        # CBUAE_BASE_RATE_AE — CBUAE bulletin (separate source)
        other_source_indicators = {"FX_SAR_USD", "FX_AED_USD", "SAMA_REPO_RATE_SA", "CBUAE_BASE_RATE_AE"}
        truly_unmapped = unmapped - other_source_indicators
        assert truly_unmapped == set(), f"Unmapped indicators: {truly_unmapped}"

    def test_indicator_ids_match_catalog(self):
        """Indicator IDs in connector maps must match the catalog."""
        import json
        from pathlib import Path

        catalog_path = Path(__file__).parent.parent / "src" / "data_foundation" / "seed" / "indicator_catalog.json"
        with open(catalog_path) as f:
            catalog = json.load(f)

        code_to_id = {entry["indicator_code"]: entry["indicator_id"] for entry in catalog}

        from src.data_foundation.connectors.cbk import _INDICATOR_MAP as cbk_map
        from src.data_foundation.connectors.eia import _INDICATOR_MAP as eia_map
        from src.data_foundation.connectors.imf import _INDICATOR_MAP as imf_map

        # Check CBK
        for code, meta in cbk_map.items():
            if code in code_to_id:
                assert meta["indicator_id"] == code_to_id[code], f"CBK {code}: {meta['indicator_id']} != {code_to_id[code]}"

        # Check EIA
        for code, meta in eia_map.items():
            if code in code_to_id:
                assert meta["indicator_id"] == code_to_id[code], f"EIA {code}: {meta['indicator_id']} != {code_to_id[code]}"

        # Check IMF
        for series_map in imf_map.values():
            for country_meta in series_map.values():
                code = country_meta["indicator_code"]
                if code in code_to_id:
                    assert country_meta["indicator_id"] == code_to_id[code], f"IMF {code}: {country_meta['indicator_id']} != {code_to_id[code]}"

    def test_source_ids_match_registry(self):
        """Source IDs used by connectors must exist in source_truth_registry.json."""
        import json
        from pathlib import Path

        registry_path = Path(__file__).parent.parent / "src" / "data_foundation" / "seed" / "source_truth_registry.json"
        with open(registry_path) as f:
            registry = json.load(f)

        valid_source_ids = {entry["source_id"] for entry in registry}

        connector_source_ids = {
            CBKConnector.source_id,
            EIAConnector.source_id,
            IMFConnector.source_id,
        }

        for sid in connector_source_ids:
            assert sid in valid_source_ids, f"Connector source_id '{sid}' not in registry"
