"""ACLED data connector for conflict and protest events."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from app.connectors.base.connector import BaseConnector, IngestResult
from app.schema.events import Event
from app.schema.enums import EventType
from app.schema.geo import GeoPoint

logger = logging.getLogger(__name__)

# GCC countries and surrounding regions for context
GCC_COUNTRIES = ["Saudi Arabia", "United Arab Emirates", "Kuwait", "Qatar", "Bahrain", "Oman"]
REGION_COUNTRIES = GCC_COUNTRIES + ["Iraq", "Iran", "Yemen"]

# Map ACLED event types to EventType enum
ACLED_TO_EVENT_TYPE = {
    "Protests": EventType.SECURITY,
    "Riots": EventType.SECURITY,
    "Strategic developments": EventType.GEOPOLITICAL,
    "Violence against civilians": EventType.SECURITY,
    "Explosions/Remote violence": EventType.SECURITY,
    "Battle-related events": EventType.SECURITY,
    "Armed clash": EventType.SECURITY,
    "Headquarters or office attacked": EventType.SECURITY,
    "Government regains territory": EventType.GEOPOLITICAL,
    "Non-violent transfer of territory": EventType.GEOPOLITICAL,
}


class ACLEDConnector(BaseConnector):
    """Connector for ACLED (Armed Conflict Location & Event Data) API.

    Fetches conflict and protest events from the Middle East/GCC region.
    """

    BASE_URL = "https://api.acleddata.com/acled/read"

    def __init__(
        self,
        source_id: str = "acled_gcc",
        source_type: str = "acled",
        api_key: Optional[str] = None,
        email: Optional[str] = None,
        timeout: float = 30.0,
        rate_limit_delay: float = 1.0,
    ):
        """Initialize ACLED connector.

        Args:
            source_id: Unique identifier for the source
            source_type: Type of source
            api_key: ACLED API key (optional for public access)
            email: Email for API access (optional)
            timeout: Request timeout in seconds
            rate_limit_delay: Delay between requests in seconds
        """
        super().__init__(source_id, source_type)
        self.api_key = api_key
        self.email = email
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async def fetch_raw(self, params: dict) -> list[dict]:
        """Fetch raw events from ACLED API.

        Args:
            params: Query parameters including:
                - event_date (YYYY-MM-DD): Start date
                - end_date (YYYY-MM-DD): End date
                - limit (int): Max records per request (default 100)
                - page (int): Page number for pagination

        Returns:
            List of raw ACLED event records

        Raises:
            httpx.RequestError: If API request fails
        """
        # Build query parameters
        query_params: dict[str, Any] = {
            "region": "Middle East",
            "page": params.get("page", 1),
            "limit": min(params.get("limit", 100), 10000),
            "output": "json",
        }

        # Add date range if provided
        if "event_date" in params:
            query_params["event_date"] = params["event_date"]
        if "end_date" in params:
            query_params["end_date"] = params["end_date"]

        # Add country filter for GCC region
        if "countries" in params:
            query_params["country"] = ",".join(params["countries"])
        else:
            query_params["country"] = ",".join(REGION_COUNTRIES)

        # Add API credentials if provided
        if self.api_key:
            query_params["api_key"] = self.api_key
        if self.email:
            query_params["email"] = self.email

        logger.info(f"Fetching ACLED events with params: {query_params}")

        try:
            response = await self.client.get(self.BASE_URL, params=query_params)
            response.raise_for_status()
            data = response.json()

            # ACLED returns data in 'data' key
            records = data.get("data", [])
            logger.info(f"Fetched {len(records)} ACLED records")

            # Rate limiting
            await self._rate_limit()

            return records

        except httpx.HTTPError as e:
            logger.error(f"ACLED API error: {e}")
            raise

    def normalize(self, raw: dict) -> Optional[Event]:
        """Normalize ACLED raw record to Event schema.

        Args:
            raw: Raw ACLED event record

        Returns:
            Normalized Event or None if validation fails
        """
        try:
            # Validate required fields
            is_valid, error_msg = self.validate_raw_record(raw)
            if not is_valid:
                logger.warning(f"Invalid ACLED record: {error_msg}")
                return None

            # Extract core event data
            event_id = raw.get("data_id", f"acled_{raw.get('iso', 0)}")
            event_date_str = raw.get("event_date")

            if not event_date_str:
                logger.warning("ACLED record missing event_date")
                return None

            # Parse date (format: DD MMM YYYY)
            try:
                event_date = datetime.strptime(event_date_str, "%d %B %Y")
            except ValueError:
                logger.warning(f"Failed to parse ACLED date: {event_date_str}")
                return None

            # Map event type
            event_type_raw = raw.get("event_type", "")
            event_type = ACLED_TO_EVENT_TYPE.get(event_type_raw, EventType.OTHER)

            # Extract location
            latitude = raw.get("latitude")
            longitude = raw.get("longitude")

            if latitude is None or longitude is None:
                logger.warning(f"ACLED record missing coordinates: {event_id}")
                return None

            location = GeoPoint(latitude=float(latitude), longitude=float(longitude))

            # Calculate severity from fatalities
            fatalities = raw.get("fatalities", 0)
            severity = min(float(fatalities) / 100.0, 1.0)

            # Build bilingual description
            description = raw.get("notes", "")
            description_ar = raw.get("notes_ar") or f"حدث أمني في {raw.get('location', 'منطقة غير محددة')}"

            # Create Event
            event = Event(
                name=f"{raw.get('event_type', 'Event')} in {raw.get('location', 'Unknown')}",
                description=description,
                description_ar=description_ar,
                event_type=event_type,
                severity=severity,
                location=location,
                start_time=event_date,
                end_time=None,
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.8,
                tags=[
                    raw.get("country", ""),
                    raw.get("region", ""),
                    event_type_raw,
                ],
            )

            logger.debug(f"Normalized ACLED event: {event.id}")
            return event

        except Exception as e:
            logger.error(f"Error normalizing ACLED record: {e}")
            return None

    async def ingest(self, params: dict) -> IngestResult:
        """Full data ingestion pipeline.

        Args:
            params: Query parameters for fetch_raw

        Returns:
            IngestResult with statistics
        """
        start_time = time.time()
        result = IngestResult(
            source_id=self.source_id,
            source_type=self.source_type,
        )

        try:
            # Set default date range if not provided
            if "event_date" not in params:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                params["event_date"] = start_date.strftime("%Y-%m-%d")
                params["end_date"] = end_date.strftime("%Y-%m-%d")

            # Fetch raw data
            raw_records = await self.fetch_raw(params)
            result.records_fetched = len(raw_records)

            # Normalize records
            normalized_events = []
            for raw_record in raw_records:
                event = self.normalize(raw_record)
                if event:
                    normalized_events.append(event)
                    result.records_normalized += 1
                else:
                    result.add_error(
                        "Failed to normalize ACLED record",
                        record=raw_record,
                    )

            # Store records (in-memory for now, would persist in real implementation)
            result.records_stored = len(normalized_events)
            logger.info(
                f"Ingested {result.records_stored} events from {result.records_fetched} fetched"
            )

        except Exception as e:
            logger.error(f"ACLED ingestion error: {e}")
            result.add_error(f"Ingestion failed: {str(e)}")

        finally:
            result.duration_ms = (time.time() - start_time) * 1000
            await self.client.aclose()

        return result

    async def _rate_limit(self):
        """Apply rate limiting delay."""
        await self._async_sleep(self.rate_limit_delay)

    async def _async_sleep(self, duration: float):
        """Async sleep wrapper."""
        import asyncio
        await asyncio.sleep(duration)
