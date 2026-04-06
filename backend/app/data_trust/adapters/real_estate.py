"""
Impact Observatory | مرصد الأثر — Real Estate Market Adapter

Normalizes real estate transaction and market index feeds into TrustedEventContract.

Source profile
--------------
source_id  : "real_estate_feed"
domain     : "real_estate"
trust tier : MEDIUM — commercial data providers, variable methodology

fetch()
    Production: replace _mock_fetch() with the real API call.
    Current: returns deterministic mock records representing GCC real estate
    market indices — Dubai, Riyadh, Abu Dhabi property transaction data.

normalize()
    Maps real estate schema to TrustedEventContract.
    Real estate sources typically publish:
        - transaction_id, transaction_date
        - property_type, location (emirate / governorate)
        - price_aed/sar, price_change_pct
        - volume (number of transactions)
    These map to normalized_payload with canonical keys.

source_metrics()
    Commercial real estate data providers have:
        - Medium reliability (commercial, not government-audited)
        - High freshness (daily/weekly transaction data)
        - Medium coverage (some fields optional or vendor-specific)
        - Medium consistency (methodology changes between vendors)
        - High latency score (near real-time transaction data)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..contracts.event import TrustedEventContract, ValidationStatus
from .base import BaseAdapter, AdapterFetchError, AdapterNormalizeError

logger = logging.getLogger(__name__)

# ── Mock source records ───────────────────────────────────────────────────────

_MOCK_REAL_ESTATE_RECORDS: list[dict] = [
    {
        "tx_id": "RE-DXB-2026-04-0081",
        "city": "Dubai",
        "country_code": "AE",
        "region": "Gulf",
        "property_type": "commercial",
        "district": "DIFC",
        "transaction_date": "2026-04-05T12:00:00Z",
        "price_usd": 8_400_000.0,
        "price_change_pct": -3.2,
        "volume_txns": 47,
        "market_index": 142.8,
        "market_index_prev": 147.5,
        "severity_estimate": 0.32,
        "sectors_affected": ["banking", "fintech"],
    },
    {
        "tx_id": "RE-RUH-2026-04-0022",
        "city": "Riyadh",
        "country_code": "SA",
        "region": "Gulf",
        "property_type": "mixed",
        "district": "King Abdullah Financial District",
        "transaction_date": "2026-04-04T09:30:00Z",
        "price_usd": 12_700_000.0,
        "price_change_pct": 1.8,
        "volume_txns": 91,
        "market_index": 161.3,
        "market_index_prev": 158.5,
        "severity_estimate": 0.18,
        "sectors_affected": ["banking", "insurance", "sovereign"],
    },
    {
        # Intentionally thin record — tests coverage scoring
        "tx_id": "RE-AUH-2026-04-0007",
        "city": "Abu Dhabi",
        "country_code": "AE",
        "region": "Gulf",
        "property_type": "residential",
        "transaction_date": "2026-04-05T14:00:00Z",
        "price_usd": 3_100_000.0,
        "volume_txns": 23,
        # price_change_pct intentionally absent — tests missing field handling
        # market_index intentionally absent
        "sectors_affected": ["banking"],
    },
]


class RealEstateAdapter(BaseAdapter):
    """
    Adapter for GCC real estate market data feeds.

    In production, replace _mock_fetch() with the actual API call.
    The normalize() method handles optional fields gracefully with explicit defaults.
    """

    source_id: str = "real_estate_feed"
    domain: str = "real_estate"

    def fetch(self) -> list[dict]:
        """
        Fetch real estate market records.

        Raises
        ------
        AdapterFetchError
            If the live feed is unreachable (production path only).
        """
        try:
            return self._mock_fetch()
        except Exception as exc:
            raise AdapterFetchError(
                f"RealEstateAdapter.fetch() failed: {exc}"
            ) from exc

    def _mock_fetch(self) -> list[dict]:
        """Return deterministic mock real estate records."""
        logger.debug(
            "RealEstateAdapter: using mock fetch (%d records)",
            len(_MOCK_REAL_ESTATE_RECORDS),
        )
        return list(_MOCK_REAL_ESTATE_RECORDS)

    def normalize(self, raw: dict) -> TrustedEventContract:
        """
        Map a real estate feed record to TrustedEventContract.

        Raises
        ------
        AdapterNormalizeError
            If required fields (tx_id, country_code, transaction_date, price_usd)
            are missing.
        """
        missing = [
            f for f in ("tx_id", "country_code", "transaction_date", "price_usd")
            if f not in raw
        ]
        if missing:
            raise AdapterNormalizeError(
                f"RealEstateAdapter.normalize(): missing required fields {missing}",
                raw=raw,
            )

        try:
            transaction_date = datetime.fromisoformat(
                raw["transaction_date"].replace("Z", "+00:00")
            )
        except (KeyError, ValueError):
            transaction_date = datetime.now(timezone.utc)

        geo = {
            "country": raw["country_code"],
            "city": raw.get("city", ""),
            "district": raw.get("district", ""),
            "region": raw.get("region", "Gulf"),
        }

        # Optional fields handled with explicit None / 0 defaults
        price_change_pct = raw.get("price_change_pct")   # May be absent
        market_index     = raw.get("market_index")        # May be absent

        normalized_payload = {
            "tx_id":             raw["tx_id"],
            "property_type":     raw.get("property_type", "unknown"),
            "city":              raw.get("city", ""),
            "country_code":      raw["country_code"],
            "price_usd":         float(raw["price_usd"]),
            "price_change_pct":  float(price_change_pct) if price_change_pct is not None else None,
            "volume_txns":       int(raw.get("volume_txns", 0)),
            "market_index":      float(market_index) if market_index is not None else None,
            "sectors_affected":  raw.get("sectors_affected", []),
        }

        impact_score_raw = raw.get("severity_estimate")
        impact_score = (
            float(impact_score_raw)
            if impact_score_raw is not None
            else None
        )

        return TrustedEventContract(
            timestamp=transaction_date,
            source=self.source_id,
            domain=self.domain,
            geo=geo,
            raw_payload=dict(raw),
            normalized_payload=normalized_payload,
            impact_score=impact_score,
            validation_status=ValidationStatus.PENDING,
        )

    def source_metrics(self) -> dict[str, float]:
        """
        Commercial real estate data providers — medium-trust profile.

        reliability   0.72 — commercial vendor, not government-audited
        freshness     0.90 — daily/weekly transaction feeds, near real-time
        coverage      0.70 — some optional fields missing from thin records
        consistency   0.68 — methodology varies by vendor and property type
        latency       0.88 — transactions reported within 24-48h of closing
        """
        return {
            "reliability":  0.72,
            "freshness":    0.90,
            "coverage":     0.70,
            "consistency":  0.68,
            "latency":      0.88,
        }
