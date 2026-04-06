"""
Impact Observatory | مرصد الأثر — Government Data Adapter

Normalizes government open data feeds into TrustedEventContract.

Source profile
--------------
source_id  : "government_open_data"
domain     : "government"
trust tier : HIGH — government statistical offices are verified publishers

fetch()
    Production: replace _mock_fetch() body with HTTP call to the real API.
    Current: returns deterministic mock records representing GCC government
    economic indicators (trade volumes, regulatory announcements, fiscal data).
    Mock records cover 3 GCC countries to exercise the geo + sector path.

normalize()
    Maps government-specific field names to TrustedEventContract.
    Government sources typically publish:
        - indicator_code, indicator_label
        - period (year-quarter), country_code
        - value (numeric), unit
    These are mapped to normalized_payload with canonical keys.

source_metrics()
    Government statistical offices have:
        - High reliability (official verified data)
        - Moderate freshness (quarterly publication cycles)
        - High coverage (standardized mandatory fields)
        - High consistency (stable methodology)
        - Moderate latency (publication lag vs event occurrence)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..contracts.event import TrustedEventContract, ValidationStatus
from .base import BaseAdapter, AdapterFetchError, AdapterNormalizeError

logger = logging.getLogger(__name__)

# ── Mock source records ───────────────────────────────────────────────────────
# Replace _mock_fetch() with a real HTTP call when the live feed is connected.
# Field names match the GCC Open Government Data Portal schema.

_MOCK_GOVERNMENT_RECORDS: list[dict] = [
    {
        "record_id": "GOV-SA-2026-Q1-001",
        "country_code": "SA",
        "country_name": "Saudi Arabia",
        "region": "Gulf",
        "indicator_code": "TRADE_BALANCE_USD",
        "indicator_label": "Trade Balance",
        "period": "2026-Q1",
        "value": -4_200_000_000.0,
        "unit": "USD",
        "severity_estimate": 0.45,
        "publication_ts": "2026-04-01T08:00:00Z",
        "sectors_affected": ["banking", "energy", "ports"],
        "source_confidence": 0.92,
    },
    {
        "record_id": "GOV-AE-2026-Q1-002",
        "country_code": "AE",
        "country_name": "United Arab Emirates",
        "region": "Gulf",
        "indicator_code": "REGULATORY_CAPITAL_RATIO",
        "indicator_label": "Banking Regulatory Capital Adequacy Ratio",
        "period": "2026-Q1",
        "value": 18.7,
        "unit": "PERCENT",
        "severity_estimate": 0.20,
        "publication_ts": "2026-04-02T10:30:00Z",
        "sectors_affected": ["banking", "insurance"],
        "source_confidence": 0.95,
    },
    {
        "record_id": "GOV-KW-2026-Q1-003",
        "country_code": "KW",
        "country_name": "Kuwait",
        "region": "Gulf",
        "indicator_code": "OIL_EXPORT_VOLUME",
        "indicator_label": "Crude Oil Export Volume",
        "period": "2026-Q1",
        "value": 2_350_000.0,
        "unit": "BARRELS_PER_DAY",
        "severity_estimate": 0.55,
        "publication_ts": "2026-04-03T06:00:00Z",
        "sectors_affected": ["energy", "shipping", "ports"],
        "source_confidence": 0.88,
    },
]


class GovernmentAdapter(BaseAdapter):
    """
    Adapter for GCC government open data feeds.

    In production, replace _mock_fetch() with the actual API call.
    The normalize() method and contract shape are production-ready as-is.
    """

    source_id: str = "government_open_data"
    domain: str = "government"

    def fetch(self) -> list[dict]:
        """
        Fetch government records.

        Returns mock records in development; replace with live HTTP call
        to the GCC government data API in production.

        Raises
        ------
        AdapterFetchError
            If the live API is unreachable (production path only).
        """
        try:
            return self._mock_fetch()
        except Exception as exc:
            raise AdapterFetchError(
                f"GovernmentAdapter.fetch() failed: {exc}"
            ) from exc

    def _mock_fetch(self) -> list[dict]:
        """Return deterministic mock government records."""
        logger.debug(
            "GovernmentAdapter: using mock fetch (%d records)",
            len(_MOCK_GOVERNMENT_RECORDS),
        )
        return list(_MOCK_GOVERNMENT_RECORDS)

    def normalize(self, raw: dict) -> TrustedEventContract:
        """
        Map a government API record to TrustedEventContract.

        Parameters
        ----------
        raw : dict
            Single record from fetch() in government source schema.

        Returns
        -------
        TrustedEventContract
            Normalized contract ready for validation.

        Raises
        ------
        AdapterNormalizeError
            If required government fields (record_id, country_code,
            indicator_code, value) are missing.
        """
        missing = [
            f for f in ("record_id", "country_code", "indicator_code", "value")
            if f not in raw
        ]
        if missing:
            raise AdapterNormalizeError(
                f"GovernmentAdapter.normalize(): missing required fields {missing}",
                raw=raw,
            )

        try:
            publication_ts = datetime.fromisoformat(
                raw["publication_ts"].replace("Z", "+00:00")
            )
        except (KeyError, ValueError):
            publication_ts = datetime.now(timezone.utc)

        geo = {
            "country": raw["country_code"],
            "country_name": raw.get("country_name", ""),
            "region": raw.get("region", "Gulf"),
        }

        normalized_payload = {
            "record_id":        raw["record_id"],
            "indicator_code":   raw["indicator_code"],
            "indicator_label":  raw.get("indicator_label", raw["indicator_code"]),
            "period":           raw.get("period", ""),
            "value":            float(raw["value"]),
            "unit":             raw.get("unit", ""),
            "sectors_affected": raw.get("sectors_affected", []),
            "country_code":     raw["country_code"],
            "source_confidence": float(raw.get("source_confidence", 0.80)),
        }

        impact_score_raw = raw.get("severity_estimate")
        impact_score = (
            float(impact_score_raw)
            if impact_score_raw is not None
            else None
        )

        return TrustedEventContract(
            timestamp=publication_ts,
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
        Government statistical offices — high-trust source profile.

        reliability   0.90 — official verified publications
        freshness     0.65 — quarterly publication cycle (not real-time)
        coverage      0.90 — standardized mandatory disclosure fields
        consistency   0.88 — stable methodology, audited annually
        latency       0.70 — publication lag: event occurs, data published weeks later
        """
        return {
            "reliability":  0.90,
            "freshness":    0.65,
            "coverage":     0.90,
            "consistency":  0.88,
            "latency":      0.70,
        }
