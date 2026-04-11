"""P1 Data Foundation — Enumerations.

All typed enums for the P1 layer. Used across models, ingestion, and validation.
"""

from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    """How data enters the system."""
    API = "api"
    CSV = "csv"
    MANUAL = "manual"
    DERIVED = "derived"
    SCRAPER = "scraper"


class Confidence(str, Enum):
    """Data confidence level."""
    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class Country(str, Enum):
    """GCC member states + regional."""
    KW = "KW"  # Kuwait
    SA = "SA"  # Saudi Arabia
    AE = "AE"  # UAE
    QA = "QA"  # Qatar
    BH = "BH"  # Bahrain
    OM = "OM"  # Oman
    GCC = "GCC"  # Pan-GCC aggregate


class Sector(str, Enum):
    """Economic sectors tracked by the observatory."""
    BANKING = "banking"
    INSURANCE = "insurance"
    ENERGY = "energy"
    LOGISTICS = "logistics"
    REAL_ESTATE = "real_estate"
    TELECOM = "telecom"
    SOVEREIGN = "sovereign"
    FINTECH = "fintech"
    CONSTRUCTION = "construction"
    MULTI = "multi"


class Currency(str, Enum):
    """GCC currencies + major pairs."""
    KWD = "KWD"
    SAR = "SAR"
    AED = "AED"
    QAR = "QAR"
    BHD = "BHD"
    OMR = "OMR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"


class Severity(str, Enum):
    """Event/signal severity classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DecisionAction(str, Enum):
    """What a decision rule proposes."""
    ALERT = "alert"
    MONITOR = "monitor"
    HEDGE = "hedge"
    DIVEST = "divest"
    REBALANCE = "rebalance"
    ESCALATE = "escalate"
    HOLD = "hold"
    EXECUTE = "execute"


class DecisionStatus(str, Enum):
    """Lifecycle status of a decision log entry."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class SignalDirection(str, Enum):
    """Directional movement of a signal."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"


class FrequencyType(str, Enum):
    """Data update frequency."""
    REAL_TIME = "real_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ON_DEMAND = "on_demand"


class DataQuality(str, Enum):
    """Quality tier for ingested data."""
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    RAW = "raw"
