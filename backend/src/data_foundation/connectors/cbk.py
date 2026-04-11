"""CBK Connector — Central Bank of Kuwait exchange rates & monetary statistics.

Fetches from CBK's public API endpoints:
  - Exchange rates: https://www.cbk.gov.kw/api/exchange-rates
  - The CBK publishes daily exchange rates and monthly monetary statistics.

Maps to indicators:
  - FX_KWD_USD      (ic-012) — KWD/USD exchange rate
  - CBK_DISCOUNT_RATE_KW (ic-006) — CBK discount rate
  - CBK_M2_KW       (ic-015) — Money supply M2
  - CBK_TOTAL_CREDIT_KW (ic-016) — Total bank credit
  - CBK_FOREX_RESERVES_KW (ic-017) — Foreign exchange reserves

Source ID: src-cbk-bulletin
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List

import httpx

from src.data_foundation.connectors.base import BaseConnector, NormalizedRecord

logger = logging.getLogger(__name__)

# CBK publishes exchange rates as JSON at this endpoint.
# The page at /en/statistics/exchange-rates serves HTML that loads from an API.
_CBK_EXCHANGE_RATE_URL = "https://www.cbk.gov.kw/en/statistics/exchange-rates"

# CBK also publishes monetary/banking data via statistical bulletins.
# We combine the exchange rate fetch with the latest bulletin data.
_CBK_STATS_API = "https://www.cbk.gov.kw/api/v1/statistical-bulletin"

# Indicator catalog mappings (must match indicator_catalog.json)
_INDICATOR_MAP = {
    "FX_KWD_USD": {
        "indicator_id": "ic-012",
        "unit": "KWD_per_USD",
        "country": "KW",
        "frequency": "DAILY",
        "confidence": 0.95,
    },
    "CBK_DISCOUNT_RATE_KW": {
        "indicator_id": "ic-006",
        "unit": "percent",
        "country": "KW",
        "frequency": "MONTHLY",
        "confidence": 0.95,
    },
    "CBK_M2_KW": {
        "indicator_id": "ic-015",
        "unit": "KWD_mn",
        "country": "KW",
        "frequency": "MONTHLY",
        "confidence": 0.95,
    },
    "CBK_TOTAL_CREDIT_KW": {
        "indicator_id": "ic-016",
        "unit": "KWD_mn",
        "country": "KW",
        "frequency": "MONTHLY",
        "confidence": 0.95,
    },
    "CBK_FOREX_RESERVES_KW": {
        "indicator_id": "ic-017",
        "unit": "USD_mn",
        "country": "KW",
        "frequency": "MONTHLY",
        "confidence": 0.90,
    },
}


class CBKConnector(BaseConnector):
    """Connector for the Central Bank of Kuwait public data.

    Fetches exchange rates from CBK's website and extracts KWD/USD rate
    plus monetary statistics from the statistical bulletin data.
    """

    source_id = "src-cbk-bulletin"

    def __init__(self, session, *, timeout: float = 30.0):
        super().__init__(session)
        self._timeout = timeout
        self._fetch_url = _CBK_EXCHANGE_RATE_URL

    @property
    def source_url(self) -> str:
        return self._fetch_url

    async def fetch_raw(self) -> Dict[str, Any]:
        """Fetch CBK exchange rate data and statistical bulletin.

        CBK's exchange rate page returns HTML containing rate data.
        We parse the structured data from the page.
        Falls back to scraping the HTML table if no JSON API is available.
        """
        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "ImpactObservatory/1.0 (research; cbk-data-feed)",
                "Accept": "text/html,application/json",
            },
        ) as client:
            # Fetch exchange rates page
            resp = await client.get(_CBK_EXCHANGE_RATE_URL)
            resp.raise_for_status()

            exchange_data = self._parse_cbk_exchange_rates(resp.text)

            # Attempt to fetch statistical bulletin data
            bulletin_data = {}
            try:
                stats_resp = await client.get(
                    _CBK_STATS_API,
                    headers={"Accept": "application/json"},
                )
                if stats_resp.status_code == 200:
                    try:
                        bulletin_data = stats_resp.json()
                    except Exception:
                        bulletin_data = self._parse_bulletin_fallback(stats_resp.text)
            except httpx.HTTPError:
                logger.info("CBK statistical bulletin API not available; using exchange rates only")

            return {
                "source": "cbk",
                "fetch_date": str(date.today()),
                "exchange_rates": exchange_data,
                "bulletin": bulletin_data,
            }

    def _parse_cbk_exchange_rates(self, html: str) -> Dict[str, Any]:
        """Extract exchange rate data from CBK HTML page.

        CBK publishes a table with currency codes, buying/selling rates.
        We extract the USD row to get KWD/USD rate.
        """
        rates: Dict[str, Any] = {}

        # Parse the HTML for exchange rate table rows
        # CBK format: currency code | transfer rate | cash rate
        lines = html.split("\n")
        for i, line in enumerate(lines):
            # Look for USD in the exchange rate table
            if "USD" in line and ("United States" in line or "US Dollar" in line or "usd" in line.lower()):
                # Extract numeric values from surrounding lines
                rate = self._extract_rate_from_context(lines, i)
                if rate:
                    rates["USD"] = rate

            # Also look for structured data attributes
            if 'data-currency="USD"' in line or 'currency-code="USD"' in line:
                rate = self._extract_rate_from_context(lines, i)
                if rate:
                    rates["USD"] = rate

        # If HTML parsing didn't find rates, look for JSON embedded in page
        if not rates:
            import re
            json_patterns = re.findall(r'exchangeRates["\s:=]+(\[.*?\])', html, re.DOTALL)
            if json_patterns:
                try:
                    import json
                    data = json.loads(json_patterns[0])
                    for item in data:
                        code = item.get("currency_code") or item.get("code") or ""
                        if code.upper() == "USD":
                            rates["USD"] = {
                                "rate": float(item.get("rate") or item.get("transfer_rate") or 0),
                                "buy": float(item.get("buy") or item.get("buying_rate") or 0),
                                "sell": float(item.get("sell") or item.get("selling_rate") or 0),
                            }
                except (ValueError, KeyError):
                    pass

        # Look for meta tags or script variables containing rates
        if not rates:
            import re
            # Common patterns for CBK rate display
            usd_patterns = [
                r'USD[^0-9]*?(\d+\.\d{3,6})',
                r'dollar[^0-9]*?(\d+\.\d{3,6})',
                r'KWD/USD[^0-9]*?(\d+\.\d{3,6})',
            ]
            for pattern in usd_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    rate_val = float(match.group(1))
                    # KWD/USD is typically ~0.3067
                    if 0.2 < rate_val < 0.4:
                        rates["USD"] = {"rate": rate_val, "buy": None, "sell": None}
                        break

        return rates

    def _extract_rate_from_context(self, lines: list, index: int) -> Dict[str, Any] | None:
        """Extract numeric rate value from lines surrounding a currency match."""
        import re
        context = " ".join(lines[max(0, index - 1):min(len(lines), index + 3)])
        # Find decimal numbers that look like exchange rates (0.2-0.4 for KWD/USD)
        numbers = re.findall(r"(\d+\.\d{3,6})", context)
        for num_str in numbers:
            val = float(num_str)
            if 0.2 < val < 0.4:  # KWD/USD range
                return {"rate": val, "buy": None, "sell": None}
        return None

    def _parse_bulletin_fallback(self, text: str) -> Dict[str, Any]:
        """Attempt to extract bulletin data from non-JSON response."""
        return {}

    def normalize(self, raw_payload: Dict[str, Any]) -> List[NormalizedRecord]:
        """Map CBK raw data into canonical observations."""
        records: List[NormalizedRecord] = []
        today = date.today()

        exchange_rates = raw_payload.get("exchange_rates", {})
        bulletin = raw_payload.get("bulletin", {})

        # 1. KWD/USD exchange rate
        usd_data = exchange_rates.get("USD", {})
        if usd_data and usd_data.get("rate"):
            meta = _INDICATOR_MAP["FX_KWD_USD"]
            records.append(NormalizedRecord(
                indicator_code="FX_KWD_USD",
                indicator_id=meta["indicator_id"],
                value=round(float(usd_data["rate"]), 4),
                unit=meta["unit"],
                country=meta["country"],
                period_start=today,
                period_end=today,
                frequency=meta["frequency"],
                observation_date=today,
                confidence_score=meta["confidence"],
                confidence_method="SOURCE_DECLARED",
            ))

        # 2. CBK Discount Rate (from bulletin or embedded data)
        discount_rate = (
            bulletin.get("discount_rate")
            or bulletin.get("policy_rate")
            or bulletin.get("discountRate")
        )
        if discount_rate is not None:
            meta = _INDICATOR_MAP["CBK_DISCOUNT_RATE_KW"]
            # Monthly period: first to last day of current month
            month_start = today.replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_month - timedelta(days=1)
            records.append(NormalizedRecord(
                indicator_code="CBK_DISCOUNT_RATE_KW",
                indicator_id=meta["indicator_id"],
                value=round(float(discount_rate), 2),
                unit=meta["unit"],
                country=meta["country"],
                period_start=month_start,
                period_end=month_end,
                frequency=meta["frequency"],
                observation_date=today,
                confidence_score=meta["confidence"],
            ))

        # 3. M2 Money Supply
        m2 = bulletin.get("m2") or bulletin.get("money_supply_m2") or bulletin.get("M2")
        if m2 is not None:
            meta = _INDICATOR_MAP["CBK_M2_KW"]
            month_start = today.replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_month - timedelta(days=1)
            records.append(NormalizedRecord(
                indicator_code="CBK_M2_KW",
                indicator_id=meta["indicator_id"],
                value=round(float(m2), 0),
                unit=meta["unit"],
                country=meta["country"],
                period_start=month_start,
                period_end=month_end,
                frequency=meta["frequency"],
                observation_date=today,
                confidence_score=meta["confidence"],
            ))

        # 4. Total Credit
        credit = bulletin.get("total_credit") or bulletin.get("totalCredit") or bulletin.get("bank_credit")
        if credit is not None:
            meta = _INDICATOR_MAP["CBK_TOTAL_CREDIT_KW"]
            month_start = today.replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_month - timedelta(days=1)
            records.append(NormalizedRecord(
                indicator_code="CBK_TOTAL_CREDIT_KW",
                indicator_id=meta["indicator_id"],
                value=round(float(credit), 0),
                unit=meta["unit"],
                country=meta["country"],
                period_start=month_start,
                period_end=month_end,
                frequency=meta["frequency"],
                observation_date=today,
                confidence_score=meta["confidence"],
            ))

        # 5. Forex Reserves
        reserves = (
            bulletin.get("forex_reserves")
            or bulletin.get("foreign_reserves")
            or bulletin.get("reserves")
        )
        if reserves is not None:
            meta = _INDICATOR_MAP["CBK_FOREX_RESERVES_KW"]
            month_start = today.replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_month - timedelta(days=1)
            records.append(NormalizedRecord(
                indicator_code="CBK_FOREX_RESERVES_KW",
                indicator_id=meta["indicator_id"],
                value=round(float(reserves), 0),
                unit=meta["unit"],
                country=meta["country"],
                period_start=month_start,
                period_end=month_end,
                frequency=meta["frequency"],
                observation_date=today,
                confidence_score=meta["confidence"],
            ))

        return records

    def _extract_period(self, raw_payload: Dict[str, Any]) -> tuple[date, date]:
        """CBK data is daily for FX, monthly for bulletin."""
        today = date.today()
        month_start = today.replace(day=1)
        return month_start, today
