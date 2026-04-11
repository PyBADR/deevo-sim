"""Data Reality Foundation — Production connectors for real-world data sources.

Three connectors fetching live data from:
  - CBK: Central Bank of Kuwait exchange rates & monetary statistics
  - EIA: U.S. Energy Information Administration oil & energy data
  - IMF: International Monetary Fund GDP, inflation, and macro data
"""

from src.data_foundation.connectors.base import BaseConnector  # noqa: F401
from src.data_foundation.connectors.cbk import CBKConnector  # noqa: F401
from src.data_foundation.connectors.eia import EIAConnector  # noqa: F401
from src.data_foundation.connectors.imf import IMFConnector  # noqa: F401

__all__ = ["BaseConnector", "CBKConnector", "EIAConnector", "IMFConnector"]
