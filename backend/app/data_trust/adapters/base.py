"""
Impact Observatory | مرصد الأثر — Base Adapter

Every external data source must implement this interface.

Contract:
    fetch()      → list of raw dicts from the source
    normalize()  → TrustedEventContract from a single raw dict
    validate()   → delegates to the validation layer

Concrete adapters override fetch() and normalize().
They MUST NOT override validate() — validation is centralized.

Error handling:
    AdapterFetchError     — source unreachable, auth failure, timeout
    AdapterNormalizeError — raw dict missing required fields, type mismatch

Both errors are caught by the orchestrator; failed records are quarantined.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ..contracts.event import TrustedEventContract
from ..validation.validator import validate_trusted_event

logger = logging.getLogger(__name__)


class AdapterFetchError(Exception):
    """Raised when the source cannot be reached or returns unusable data."""
    pass


class AdapterNormalizeError(Exception):
    """Raised when a raw record cannot be mapped to TrustedEventContract."""
    def __init__(self, message: str, raw: dict | None = None):
        super().__init__(message)
        self.raw = raw or {}


class BaseAdapter(ABC):
    """
    Abstract base for all data source adapters.

    Subclasses must implement:
        source_id: str  — unique identifier for this source
        domain: str     — business domain (used in contract.domain)
        fetch()         — returns list[dict] of raw records
        normalize()     — maps one raw dict → TrustedEventContract
    """

    # Subclasses must set these as class attributes
    source_id: str
    domain: str

    def fetch(self) -> list[dict]:
        """
        Retrieve raw records from the source.

        Returns
        -------
        list[dict]
            Raw records in source-native format.

        Raises
        ------
        AdapterFetchError
            If the source is unreachable, returns an error response,
            or returns data that cannot be parsed as a list of dicts.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement fetch()"
        )

    @abstractmethod
    def normalize(self, raw: dict) -> TrustedEventContract:
        """
        Convert one raw source record into a TrustedEventContract.

        Parameters
        ----------
        raw : dict
            A single record as returned by fetch().

        Returns
        -------
        TrustedEventContract
            Fully populated contract in pending validation state.

        Raises
        ------
        AdapterNormalizeError
            If the raw record is missing required fields or has invalid types.
        """
        ...

    def validate(self, contract: TrustedEventContract) -> dict:
        """
        Validate a TrustedEventContract.

        Delegates to the centralized validation layer.
        Adapters MUST NOT override this method.

        Returns
        -------
        dict
            {"valid": bool, "errors": list[str]}
        """
        return validate_trusted_event(contract)

    def source_metrics(self) -> dict[str, float]:
        """
        Return source quality metrics for trust scoring.

        Override in subclasses to provide real metrics.
        Default values are conservative but not punitive.

        Dimensions (all 0.0–1.0)
        -------------------------
        reliability   : Historical validation pass rate
        freshness     : How recent the data is (computed from fetch time)
        coverage      : Payload completeness ratio
        consistency   : Variance stability across events
        latency       : Delivery lag (source timestamp vs received_at)
        """
        return {
            "reliability": 0.70,   # Default: 70% historical pass rate
            "freshness":   0.80,   # Default: data is reasonably recent
            "coverage":    0.75,   # Default: 75% field completeness
            "consistency": 0.70,   # Default: moderate consistency
            "latency":     0.80,   # Default: acceptable delivery lag
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source_id={self.source_id!r}, domain={self.domain!r})"
