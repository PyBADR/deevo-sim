"""EIA Connector — U.S. Energy Information Administration oil & energy data.

Fetches from EIA's public JSON API v2:
  https://api.eia.gov/v2/petroleum/pri/spt/data/

EIA provides free API access (API key required but free registration).
When no API key is configured, falls back to fetching from the EIA
open-data STEO (Short-Term Energy Outlook) JSON endpoint.

Maps to indicators:
  - BRENT_SPOT        (ic-009) — Brent crude spot price USD/bbl
  - OPEC_BASKET       (ic-010) — OPEC basket price USD/bbl
  - KW_OIL_PRODUCTION (ic-011) — Kuwait crude production mbpd

Source ID: src-opec-momr (EIA is a secondary/cross-validation source for OPEC data)
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import httpx

from src.data_foundation.connectors.base import BaseConnector, NormalizedRecord

logger = logging.getLogger(__name__)

# EIA API v2 — petroleum spot prices
# Series: PET.RBRTE.D = Europe Brent Spot Price FOB (Daily)
# Series: PET.RBRTE.M = Europe Brent Spot Price FOB (Monthly)
_EIA_API_BASE = "https://api.eia.gov/v2"
_EIA_BRENT_ENDPOINT = f"{_EIA_API_BASE}/petroleum/pri/spt/data/"
_EIA_PRODUCTION_ENDPOINT = f"{_EIA_API_BASE}/international/data/"

# Fallback: EIA STEO (Short-Term Energy Outlook) — no API key needed
_EIA_STEO_URL = "https://www.eia.gov/outlooks/steo/data/browser/data/getSeriesData"

_INDICATOR_MAP = {
    "BRENT_SPOT": {
        "indicator_id": "ic-009",
        "unit": "USD_per_bbl",
        "country": "KW",  # Global but GCC-relevant
        "frequency": "DAILY",
        "confidence": 0.95,
        "eia_series": "RBRTE",
        "eia_product": "EPC0",
    },
    "OPEC_BASKET": {
        "indicator_id": "ic-010",
        "unit": "USD_per_bbl",
        "country": "KW",
        "frequency": "DAILY",
        "confidence": 0.90,
        "eia_series": "ROPEC",
    },
    "KW_OIL_PRODUCTION": {
        "indicator_id": "ic-011",
        "unit": "mbpd",
        "country": "KW",
        "frequency": "MONTHLY",
        "confidence": 0.85,
    },
}


class EIAConnector(BaseConnector):
    """Connector for EIA petroleum and energy data.

    Uses EIA API v2 when an API key is available, otherwise falls back
    to the STEO open-data endpoint.
    """

    source_id = "src-opec-momr"

    def __init__(self, session, *, api_key: Optional[str] = None, timeout: float = 30.0):
        super().__init__(session)
        self._api_key = api_key or ""
        self._timeout = timeout

    @property
    def source_url(self) -> str:
        if self._api_key:
            return _EIA_BRENT_ENDPOINT
        return _EIA_STEO_URL

    async def fetch_raw(self) -> Dict[str, Any]:
        """Fetch oil price and production data from EIA."""
        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "ImpactObservatory/1.0 (research; eia-data-feed)",
                "Accept": "application/json",
            },
        ) as client:
            result: Dict[str, Any] = {
                "source": "eia",
                "fetch_date": str(date.today()),
                "brent": {},
                "opec_basket": {},
                "production": {},
            }

            if self._api_key:
                result["brent"] = await self._fetch_eia_api(client, "brent")
                result["opec_basket"] = await self._fetch_eia_api(client, "opec")
                result["production"] = await self._fetch_eia_api(client, "production")
            else:
                result["brent"] = await self._fetch_steo(client, "BREPGP")
                result["opec_basket"] = await self._fetch_steo(client, "COPRPOP")
                result["production"] = await self._fetch_steo(client, "COPR_KUW")

            return result

    async def _fetch_eia_api(self, client: httpx.AsyncClient, data_type: str) -> Dict[str, Any]:
        """Fetch from EIA API v2 with API key."""
        try:
            if data_type == "brent":
                params = {
                    "api_key": self._api_key,
                    "frequency": "monthly",
                    "data[0]": "value",
                    "facets[series][]": "RBRTE",
                    "sort[0][column]": "period",
                    "sort[0][direction]": "desc",
                    "length": 12,
                }
                resp = await client.get(_EIA_BRENT_ENDPOINT, params=params)
            elif data_type == "opec":
                params = {
                    "api_key": self._api_key,
                    "frequency": "monthly",
                    "data[0]": "value",
                    "facets[series][]": "R_OPEC",
                    "sort[0][column]": "period",
                    "sort[0][direction]": "desc",
                    "length": 12,
                }
                resp = await client.get(_EIA_BRENT_ENDPOINT, params=params)
            else:  # production
                params = {
                    "api_key": self._api_key,
                    "frequency": "monthly",
                    "data[0]": "value",
                    "facets[activityId][]": "1",  # Production
                    "facets[productId][]": "53",  # Crude oil
                    "facets[countryRegionId][]": "KWT",  # Kuwait
                    "facets[unit][]": "TBPD",
                    "sort[0][column]": "period",
                    "sort[0][direction]": "desc",
                    "length": 12,
                }
                resp = await client.get(_EIA_PRODUCTION_ENDPOINT, params=params)

            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning("EIA API v2 %s request failed: %s", data_type, exc)
            return {"error": str(exc)}

    async def _fetch_steo(self, client: httpx.AsyncClient, series: str) -> Dict[str, Any]:
        """Fetch from EIA STEO open-data endpoint (no API key needed).

        STEO provides Short-Term Energy Outlook data including:
          BREPGP — Brent crude oil price, Europe
          COPRPOP — OPEC crude oil production
          COPR_KUW — Kuwait crude production
        """
        try:
            params = {
                "series": series,
                "region": "global" if "KUW" not in series else "KUW",
            }
            resp = await client.get(_EIA_STEO_URL, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.warning("EIA STEO %s request failed: %s", series, exc)
            return {"error": str(exc)}

    def normalize(self, raw_payload: Dict[str, Any]) -> List[NormalizedRecord]:
        """Map EIA raw response into canonical observations."""
        records: List[NormalizedRecord] = []
        today = date.today()

        # Normalize Brent spot price
        brent_data = raw_payload.get("brent", {})
        brent_obs = self._extract_eia_observations(brent_data, "BRENT_SPOT")
        records.extend(brent_obs)

        # Normalize OPEC basket price
        opec_data = raw_payload.get("opec_basket", {})
        opec_obs = self._extract_eia_observations(opec_data, "OPEC_BASKET")
        records.extend(opec_obs)

        # Normalize Kuwait production
        prod_data = raw_payload.get("production", {})
        prod_obs = self._extract_eia_observations(prod_data, "KW_OIL_PRODUCTION")
        records.extend(prod_obs)

        return records

    def _extract_eia_observations(
        self, data: Dict[str, Any], indicator_code: str
    ) -> List[NormalizedRecord]:
        """Extract observations from EIA API v2 or STEO response format."""
        records: List[NormalizedRecord] = []
        meta = _INDICATOR_MAP[indicator_code]

        if "error" in data:
            return records

        # EIA API v2 format: {"response": {"data": [{"period": "2024-01", "value": 82.5}, ...]}}
        api_data = data.get("response", {}).get("data", [])
        if api_data:
            for item in api_data:
                period_str = item.get("period", "")
                value = item.get("value")
                if not period_str or value is None:
                    continue
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue

                period_start, period_end = self._parse_eia_period(period_str)
                if period_start is None:
                    continue

                # Convert TBPD to mbpd for production
                if indicator_code == "KW_OIL_PRODUCTION" and value > 100:
                    value = value / 1000.0

                records.append(NormalizedRecord(
                    indicator_code=indicator_code,
                    indicator_id=meta["indicator_id"],
                    value=round(value, 3),
                    unit=meta["unit"],
                    country=meta["country"],
                    period_start=period_start,
                    period_end=period_end,
                    frequency=meta["frequency"],
                    observation_date=period_end,
                    confidence_score=meta["confidence"],
                    confidence_method="SOURCE_DECLARED",
                ))
            return records

        # STEO format: {"series_name": {"dates": [...], "values": [...]}}
        # or {"data": {"series_name": [["2024-01", 82.5], ...]}}
        for key, series_data in data.items():
            if key in ("error", "source", "fetch_date"):
                continue

            if isinstance(series_data, dict):
                dates = series_data.get("dates", [])
                values = series_data.get("values", [])
                for d, v in zip(dates, values):
                    if v is None:
                        continue
                    try:
                        value = float(v)
                    except (ValueError, TypeError):
                        continue
                    period_start, period_end = self._parse_eia_period(str(d))
                    if period_start is None:
                        continue

                    if indicator_code == "KW_OIL_PRODUCTION" and value > 100:
                        value = value / 1000.0

                    records.append(NormalizedRecord(
                        indicator_code=indicator_code,
                        indicator_id=meta["indicator_id"],
                        value=round(value, 3),
                        unit=meta["unit"],
                        country=meta["country"],
                        period_start=period_start,
                        period_end=period_end,
                        frequency=meta["frequency"],
                        observation_date=period_end,
                        confidence_score=meta["confidence"],
                        confidence_method="SOURCE_DECLARED",
                    ))

            elif isinstance(series_data, list):
                for entry in series_data:
                    if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                        d, v = entry[0], entry[1]
                        if v is None:
                            continue
                        try:
                            value = float(v)
                        except (ValueError, TypeError):
                            continue
                        period_start, period_end = self._parse_eia_period(str(d))
                        if period_start is None:
                            continue

                        if indicator_code == "KW_OIL_PRODUCTION" and value > 100:
                            value = value / 1000.0

                        records.append(NormalizedRecord(
                            indicator_code=indicator_code,
                            indicator_id=meta["indicator_id"],
                            value=round(value, 3),
                            unit=meta["unit"],
                            country=meta["country"],
                            period_start=period_start,
                            period_end=period_end,
                            frequency=meta["frequency"],
                            observation_date=period_end,
                            confidence_score=meta["confidence"],
                            confidence_method="SOURCE_DECLARED",
                        ))

        return records

    def _parse_eia_period(self, period_str: str) -> tuple[date | None, date | None]:
        """Parse EIA period string into (start, end) dates.

        Formats: '2024-01' (monthly), '2024-01-15' (daily), '2024Q1' (quarterly)
        """
        try:
            period_str = period_str.strip()

            # Daily: 2024-01-15
            if len(period_str) == 10 and period_str[4] == "-" and period_str[7] == "-":
                d = date.fromisoformat(period_str)
                return d, d

            # Monthly: 2024-01
            if len(period_str) == 7 and period_str[4] == "-":
                year, month = int(period_str[:4]), int(period_str[5:7])
                start = date(year, month, 1)
                if month == 12:
                    end = date(year, 12, 31)
                else:
                    end = date(year, month + 1, 1) - timedelta(days=1)
                return start, end

            # Quarterly: 2024Q1
            if "Q" in period_str.upper():
                parts = period_str.upper().split("Q")
                year = int(parts[0])
                quarter = int(parts[1])
                start_month = (quarter - 1) * 3 + 1
                start = date(year, start_month, 1)
                end_month = start_month + 2
                if end_month == 12:
                    end = date(year, 12, 31)
                else:
                    end = date(year, end_month + 1, 1) - timedelta(days=1)
                return start, end

            # Annual: 2024
            if len(period_str) == 4 and period_str.isdigit():
                year = int(period_str)
                return date(year, 1, 1), date(year, 12, 31)

        except (ValueError, IndexError):
            logger.warning("Could not parse EIA period: %s", period_str)

        return None, None

    def _extract_period(self, raw_payload: Dict[str, Any]) -> tuple[date, date]:
        """Determine the broadest period covered by this fetch."""
        today = date.today()
        # Look at the data to find the date range
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        return year_start, today
