"""P2 Data Foundation — Repository Layer.

Async repository pattern over SQLAlchemy ORM models.
Each repository provides typed CRUD + domain-specific queries.
"""

from src.data_foundation.repositories.base import BaseRepository  # noqa: F401
from src.data_foundation.repositories.entity_repo import EntityRepository  # noqa: F401
from src.data_foundation.repositories.event_repo import EventRepository  # noqa: F401
from src.data_foundation.repositories.macro_repo import MacroRepository  # noqa: F401
from src.data_foundation.repositories.rule_repo import RuleRepository  # noqa: F401
from src.data_foundation.repositories.dlog_repo import DecisionLogRepository  # noqa: F401

# Data Reality Foundation repositories
from src.data_foundation.repositories.source_truth_repo import SourceTruthRepository  # noqa: F401
from src.data_foundation.repositories.raw_record_repo import RawSourceRecordRepository  # noqa: F401
from src.data_foundation.repositories.indicator_catalog_repo import IndicatorCatalogRepository  # noqa: F401
from src.data_foundation.repositories.observation_repo import CanonicalObservationRepository  # noqa: F401
from src.data_foundation.repositories.fetch_run_repo import SourceFetchRunRepository  # noqa: F401
from src.data_foundation.repositories.normalization_run_repo import NormalizationRunRepository  # noqa: F401
