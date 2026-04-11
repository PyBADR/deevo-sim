"""P1 Data Foundation — CSV Loader.

Loads data from CSV files or CSV strings.
"""

from __future__ import annotations

import csv
import io
import logging
from pathlib import Path
from typing import Any

from p1_foundation.ingestion.contracts import IngestionContract
from p1_foundation.ingestion.loaders.base_loader import BaseLoader

logger = logging.getLogger(__name__)


class CSVLoader(BaseLoader):
    """Loads data from CSV files or strings."""

    def __init__(self, contract: IngestionContract):
        super().__init__(contract)

    def fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Load records from CSV.

        kwargs:
            csv_path: str — path to CSV file
            csv_string: str — raw CSV content
            delimiter: str — field delimiter (default ',')
            encoding: str — file encoding (default 'utf-8')
        """
        csv_path = kwargs.get("csv_path")
        csv_string = kwargs.get("csv_string")
        delimiter = kwargs.get("delimiter", ",")
        encoding = kwargs.get("encoding", "utf-8")

        if csv_string is not None:
            reader = csv.DictReader(io.StringIO(csv_string), delimiter=delimiter)
            return list(reader)

        if csv_path is not None:
            path = Path(csv_path)
            if not path.exists():
                logger.error("CSV file not found: %s", csv_path)
                return []
            with open(path, encoding=encoding, newline="") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader)

        logger.warning("CSVLoader: no csv_path or csv_string provided")
        return []
