"""P1 Data Foundation — Manual Loader.

Accepts analyst-submitted data as Python dicts. Used for desk-entry,
corrections, and human-in-the-loop data that doesn't come from APIs or files.
"""

from __future__ import annotations

import logging
from typing import Any

from p1_foundation.ingestion.contracts import IngestionContract
from p1_foundation.ingestion.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class ManualLoader(BaseLoader):
    """Loads manually submitted records."""

    def __init__(self, contract: IngestionContract):
        super().__init__(contract)

    def fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Accept manually provided records.

        kwargs:
            records: list[dict] — analyst-submitted data
            analyst: str — who submitted the data
        """
        records = kwargs.get("records", [])
        analyst = kwargs.get("analyst", "unknown")

        if not records:
            logger.warning("ManualLoader: no records provided")
            return []

        for record in records:
            record["_submitted_by"] = analyst

        logger.info("ManualLoader: received %d records from %s", len(records), analyst)
        return records
