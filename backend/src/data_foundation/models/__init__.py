"""P2 Data Foundation — SQLAlchemy ORM Models.

These models are the persistent storage layer for the P1 Pydantic schemas.
Each ORM model maps 1:1 to a Pydantic schema in schemas/.

Architecture Layer: Data (Layer 1) — Persistence
Owner: Data Engineering
"""

from src.data_foundation.models.tables import (  # noqa: F401
    EntityRegistryORM,
    EventSignalORM,
    MacroIndicatorORM,
    InterestRateSignalORM,
    OilEnergySignalORM,
    FXSignalORM,
    CBKIndicatorORM,
    BankingProfileORM,
    InsuranceProfileORM,
    LogisticsNodeORM,
    DecisionRuleORM,
    DecisionLogORM,
)

from src.data_foundation.models.reality_tables import (  # noqa: F401
    SourceTruthRegistryORM,
    RawSourceRecordORM,
    IndicatorCatalogORM,
    CanonicalObservationORM,
    SourceFetchRunORM,
    NormalizationRunORM,
)

__all__ = [
    # Existing P2 tables
    "EntityRegistryORM",
    "EventSignalORM",
    "MacroIndicatorORM",
    "InterestRateSignalORM",
    "OilEnergySignalORM",
    "FXSignalORM",
    "CBKIndicatorORM",
    "BankingProfileORM",
    "InsuranceProfileORM",
    "LogisticsNodeORM",
    "DecisionRuleORM",
    "DecisionLogORM",
    # Data Reality Foundation tables
    "SourceTruthRegistryORM",
    "RawSourceRecordORM",
    "IndicatorCatalogORM",
    "CanonicalObservationORM",
    "SourceFetchRunORM",
    "NormalizationRunORM",
]
