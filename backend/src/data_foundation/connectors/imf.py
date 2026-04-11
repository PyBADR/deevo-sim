"""IMF Connector — International Monetary Fund World Economic Outlook data.

Fetches from the IMF JSON RESTful API (no authentication required):
  https://www.imf.org/external/datamapper/api/v1/

Indicators available:
  NGDP_RPCH  — Real GDP growth (annual percent change)
  PCPIPCH    — Inflation, average consumer prices (annual percent change)
  LUR        — Unemployment rate (percent of total labor force)

GCC country codes in IMF system:
  KWT (Kuwait), SAU (Saudi Arabia), ARE (UAE),
  QAT (Qatar), BHR (Bahrain), OMN (Oman)

Maps to indicators:
  - GDP_GROWTH_KW     (ic-001) — Kuwait real GDP growth
  - GDP_GROWTH_SA     (ic-002) — Saudi Arabia real GDP growth
  - GDP_GROWTH_AE     (ic-003) — UAE real GDP growth
  - CPI_INFLATION_KW  (ic-004) — Kuwait CPI inflation
  - CPI_INFLATION_SA  (ic-018) — Saudi Arabia CPI inflation
  - UNEMPLOYMENT_KW   (ic-005) — Kuwait unemployment rate

Source ID: src-imf-weo
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

import httpx

from src.data_foundation.connectors.base import BaseConnector, NormalizedRecord

logger = logging.getLogger(__name__)

_IMF_API_BASE = "https://www.imf.org/external/datamapper/api/v1"

# IMF country code → GCC country code mapping
_IMF_TO_GCC = {
    "KWT": "KW",
    "SAU": "SA",
    "ARE": "AE",
    "QAT": "QA",
    "BHR": "BH",
    "OMN": "OM",
}
_GCC_TO_IMF = {v: k for k, v in _IMF_TO_GCC.items()}

# IMF indicator → our indicator catalog mapping
_INDICATOR_MAP: Dict[str, Dict[str, Dict[str, Any]]] = {
    # IMF series code → country → our indicator
    "NGDP_RPCH": {
        "KWT": {
            "indicator_code": "GDP_GROWTH_KW",
            "indicator_id": "ic-001",
            "unit": "percent",
            "frequency": "QUARTERLY",
        },
        "SAU": {
            "indicator_code": "GDP_GROWTH_SA",
            "indicator_id": "ic-002",
            "unit": "percent",
            "frequency": "QUARTERLY",
        },
        "ARE": {
            "indicator_code": "GDP_GROWTH_AE",
            "indicator_id": "ic-003",
            "unit": "percent",
            "frequency": "QUARTERLY",
        },
    },
    "PCPIPCH": {
        "KWT": {
            "indicator_code": "CPI_INFLATION_KW",
            "indicator_id": "ic-004",
            "unit": "percent",
            "frequency": "MONTHLY",
        },
        "SAU": {
            "indicator_code": "CPI_INFLATION_SA",
            "indicator_id": "ic-018",
            "unit": "percent",
            "frequency": "MONTHLY",
        },
    },
    "LUR": {
        "KWT": {
            "indicator_code": "UNEMPLOYMENT_KW",
            "indicator_id": "ic-005",
            "unit": "percent",
            "frequency": "QUARTERLY",
        },
    },
}

# All IMF series we fetch
_IMF_SERIES = ["NGDP_RPCH", "PCPIPCH", "LUR"]

# All GCC countries we fetch for
_IMF_COUNTRIES = ["KWT", "SAU", "ARE"]


class IMFConnector(BaseConnector):
    """Connector for IMF World Economic Outlook data.

    Fetches real GDP growth, inflation, and unemployment forecasts/actuals
    for GCC countries from the IMF DataMapper API.
    The API is public and requires no authentication.
    """

    source_id = "src-imf-weo"

    def __init__(self, session, *, timeout: float = 30.0):
        super().__init__(session)
        self._timeout = timeout

    @property
    def source_url(self) -> str:
        return f"{_IMF_API_BASE}/NGDP_RPCH,PCPIPCH,LUR"

    async def fetch_raw(self) -> Dict[str, Any]:
        """Fetch GDP growth, inflation, and unemployment data from IMF API.

        IMF DataMapper API format:
          GET /api/v1/{indicator}?periods={years}&countries={codes}
          Returns: {"values": {"indicator": {"country": {"year": value}}}}
        """
        current_year = date.today().year
        # Fetch historical + forecast years
        periods = ",".join(str(y) for y in range(current_year - 3, current_year + 3))
        countries = ",".join(_IMF_COUNTRIES)

        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "ImpactObservatory/1.0 (research; imf-weo-feed)",
                "Accept": "application/json",
            },
        ) as client:
            result: Dict[str, Any] = {
                "source": "imf",
                "fetch_date": str(date.today()),
                "series": {},
            }

            for series_code in _IMF_SERIES:
                url = f"{_IMF_API_BASE}/{series_code}"
                try:
                    resp = await client.get(
                        url,
                        params={
                            "periods": periods,
                            "countries": countries,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    result["series"][series_code] = data
                    logger.info("IMF %s fetched successfully", series_code)
                except httpx.HTTPError as exc:
                    logger.warning("IMF %s fetch failed: %s", series_code, exc)
                    result["series"][series_code] = {"error": str(exc)}

            return result

    def normalize(self, raw_payload: Dict[str, Any]) -> List[NormalizedRecord]:
        """Map IMF WEO data into canonical observations.

        IMF DataMapper response format:
        {
          "values": {
            "NGDP_RPCH": {
              "KWT": {"2022": 8.9, "2023": -2.2, "2024": 2.5, ...},
              "SAU": {...},
              ...
            }
          }
        }
        """
        records: List[NormalizedRecord] = []
        series_data = raw_payload.get("series", {})
        current_year = date.today().year

        for imf_series, payload in series_data.items():
            if "error" in payload:
                continue

            # IMF API wraps data in {"values": {series: {country: {year: val}}}}
            values = payload.get("values", {})
            series_values = values.get(imf_series, {})

            if not series_values:
                # Some responses omit the wrapper: {series: {country: {year: val}}}
                series_values = payload.get(imf_series, {})

            if not series_values:
                logger.info("No data for IMF series %s", imf_series)
                continue

            country_map = _INDICATOR_MAP.get(imf_series, {})

            for imf_country, year_values in series_values.items():
                if imf_country not in country_map:
                    continue

                meta = country_map[imf_country]
                gcc_country = _IMF_TO_GCC.get(imf_country, imf_country)

                if not isinstance(year_values, dict):
                    continue

                for year_str, value in year_values.items():
                    if value is None:
                        continue
                    try:
                        year = int(year_str)
                        value = float(value)
                    except (ValueError, TypeError):
                        continue

                    # Determine if this is forecast (provisional) or actual
                    is_provisional = year >= current_year

                    # Annual period
                    period_start = date(year, 1, 1)
                    period_end = date(year, 12, 31)

                    records.append(NormalizedRecord(
                        indicator_code=meta["indicator_code"],
                        indicator_id=meta["indicator_id"],
                        value=round(value, 2),
                        unit=meta["unit"],
                        country=gcc_country,
                        period_start=period_start,
                        period_end=period_end,
                        frequency="ANNUAL",
                        observation_date=date.today(),
                        confidence_score=0.95 if not is_provisional else 0.70,
                        confidence_method="SOURCE_DECLARED",
                        is_provisional=is_provisional,
                    ))

        return records

    def _extract_period(self, raw_payload: Dict[str, Any]) -> tuple[date, date]:
        """IMF WEO covers multi-year range."""
        current_year = date.today().year
        return date(current_year - 3, 1, 1), date(current_year + 2, 12, 31)
