"""P1 Data Foundation — API Loader.

Loads data from REST/JSON API endpoints. In P1 this is a structured stub
that accepts pre-fetched JSON; P2 will add httpx-based HTTP fetching.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from p1_foundation.ingestion.contracts import IngestionContract
from p1_foundation.ingestion.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class APILoader(BaseLoader):
    """Loads data from API responses (JSON)."""

    def __init__(self, contract: IngestionContract):
        super().__init__(contract)

    def fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Accept pre-fetched JSON data.

        kwargs:
            json_data: list[dict] — pre-fetched records
            json_path: str — path to a JSON file
            response_key: str — key to extract from JSON root (e.g., 'data', 'results')
        """
        json_data = kwargs.get("json_data")
        json_path = kwargs.get("json_path")
        response_key = kwargs.get("response_key")

        if json_data is not None:
            records = json_data
        elif json_path is not None:
            path = Path(json_path)
            if not path.exists():
                logger.error("JSON file not found: %s", json_path)
                return []
            with open(path) as f:
                records = json.load(f)
        else:
            logger.warning("APILoader: no json_data or json_path provided")
            return []

        if response_key and isinstance(records, dict):
            records = records.get(response_key, [])

        if isinstance(records, dict):
            records = [records]

        return records
