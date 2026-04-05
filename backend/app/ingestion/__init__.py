"""
Ingestion Layer — backend/app/ingestion/

Stage 1: Accept raw events from scenario catalog or external feeds.
Hidden backend source only — no UI identity exposure.
"""

from .ingest import ingest_scenario, ingest_raw_event
from .sources import KNOWN_SOURCES, get_source_trust_weight

__all__ = [
    "ingest_scenario",
    "ingest_raw_event",
    "KNOWN_SOURCES",
    "get_source_trust_weight",
]
