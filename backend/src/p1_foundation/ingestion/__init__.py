"""P1 Data Foundation — Ingestion Layer."""

from p1_foundation.ingestion.contracts import IngestionContract, FieldMapping, QualityGate
from p1_foundation.ingestion.loaders.base_loader import BaseLoader, IngestionResult
from p1_foundation.ingestion.loaders.api_loader import APILoader
from p1_foundation.ingestion.loaders.csv_loader import CSVLoader
from p1_foundation.ingestion.loaders.manual_loader import ManualLoader

__all__ = [
    "IngestionContract",
    "FieldMapping",
    "QualityGate",
    "BaseLoader",
    "IngestionResult",
    "APILoader",
    "CSVLoader",
    "ManualLoader",
]
