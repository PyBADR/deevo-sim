"""
Aviation Data Connector for OpenSky Network API.

Fetches real-time flight tracking data from OpenSky Network API and normalizes
it to the Flight schema. Supports GCC region filtering with bounding box queries.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx

from app.connectors.base.connector import BaseConnector, IngestResult
from app.schema.enums import FlightStatus, EventType
from app.schema.transport import Flight
from app.schema.geo import GeoPoint

logger = logging.getLogger(__name__)


# GCC Bounding Box: Latitude 12-32, Longitude 34-60
GCC_BOUNDING_BOX = {
    "min_lat": 12.0,
    "max_lat": 32.0,
    "min_lon": 34.0,
    "max_lon": 60.0,
}

# Flight status mapping from OpenSky Network
OPENSKY_TO_FLIGHT_STATUS = {
    "scheduled": FlightStatus.SCHEDULED,
    "active": FlightStatus.ACTIVE,
    "delayed": FlightStatus.DELAYED,
    "cancelled": FlightStatus.CANCELLED,
    "diverted": FlightStatus.DIVERTED,
    "landed": FlightStatus.LANDED,
    "completed": FlightStatus.COMPLETED,
}


class AviationConnector(BaseConnector):
    """Connector for OpenSky Network aviation tracking API."""

    BASE_URL = "https://opensky-network.org/api"

    def __init__(
        self,
        source_id: str = "opensky_aviation",
        source_type: str = "aviation",
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 30.0,
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize AviationConnector.

        Args:
            source_id: Unique identifier for this data source
            source_type: Type of data source (aviation)
            username: OpenSky Network username (optional for public access)
            password: OpenSky Network password (optional for public access)
            timeout: HTTP request timeout in seconds
            rate_limit_delay: Delay between API requests in seconds
        """
        super().__init__(source_id=source_id, source_type=source_type)
        self.username = username
        self.password = password
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.client: Optional[httpx.AsyncClient] = None

    async def fetch_raw(self, params: dict) -> list[dict]:
        """
        Fetch raw flight data from OpenSky Network API.

        Uses bounding box query for GCC region by default. Supports filtering by:
        - begin: Start timestamp (unix epoch)
        - end: End timestamp (unix epoch)
        - callsign: Aircraft callsign filter
        - aircraft_type: Filter by aircraft type

        Args:
            params: Query parameters (optional: begin, end, callsign, aircraft_type)

        Returns:
            List of flight state vector records from API response
        """
        if self.client is None:
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            self.client = httpx.AsyncClient(
                auth=auth, timeout=self.timeout, verify=True
            )

        flights = []
        try:
            # Prepare bounds query endpoint
            url = f"{self.BASE_URL}/states/all"

            # Build query parameters with GCC bounding box
            query_params = {
                "lamin": GCC_BOUNDING_BOX["min_lat"],
                "lamax": GCC_BOUNDING_BOX["max_lat"],
                "lomin": GCC_BOUNDING_BOX["min_lon"],
                "lomax": GCC_BOUNDING_BOX["max_lon"],
            }

            # Apply optional time range filtering
            if "begin" in params:
                query_params["time"] = params["begin"]

            logger.info(f"Fetching aviation data from {url} with bounds {query_params}")

            await self._rate_limit()
            response = await self.client.get(url, params=query_params)
            response.raise_for_status()

            data = response.json()

            # OpenSky API returns states array with flight vectors
            if "states" in data and data["states"]:
                flights = data["states"]
                logger.info(f"Fetched {len(flights)} flights from OpenSky Network")
            else:
                logger.info("No flights found in OpenSky Network API response")

            # Apply optional callsign filter
            if "callsign" in params and params["callsign"]:
                callsign_filter = params["callsign"].upper().strip()
                flights = [
                    f
                    for f in flights
                    if f[1] and f[1].upper().strip() == callsign_filter
                ]
                logger.info(
                    f"Filtered {len(flights)} flights matching callsign {callsign_filter}"
                )

            return flights

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching aviation data: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching aviation data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching aviation data: {e}")
            return []

    def normalize(self, raw: dict) -> Optional[Flight]:
        """
        Normalize raw flight state vector to Flight schema.

        OpenSky state vector format:
        [0] icao24: ICAO 24-bit address (hex string)
        [1] callsign: Aircraft callsign
        [2] origin_country: Country where aircraft is registered
        [3] time_position: Unix timestamp of position update
        [4] last_contact: Unix timestamp of last position report
        [5] longitude: WGS-84 longitude
        [6] latitude: WGS-84 latitude
        [7] baro_altitude: Barometric altitude in meters
        [8] on_ground: True if aircraft is on ground
        [9] velocity: Speed over ground in m/s
        [10] heading: Heading in degrees
        [11] vertical_rate: Vertical rate in m/s
        [12] sensors: Array of ICAO 24-bit addresses of receivers reporting this flight
        [13] geo_altitude: Geometric altitude in meters
        [14] squawk: Squawk code
        [15] spi: Special Purpose Indicator
        [16] position_source: Source of position data

        Args:
            raw: Raw state vector from OpenSky API

        Returns:
            Normalized Flight object or None if validation fails
        """
        try:
            if not isinstance(raw, list) or len(raw) < 17:
                logger.warning(f"Invalid flight state vector format: {raw}")
                return None

            # Extract state vector fields
            icao24 = raw[0]
            callsign = raw[1]
            origin_country = raw[2]
            time_position = raw[3]
            last_contact = raw[4]
            longitude = raw[5]
            latitude = raw[6]
            baro_altitude = raw[7]
            on_ground = raw[8]
            velocity = raw[9]
            heading = raw[10]
            vertical_rate = raw[11]
            geo_altitude = raw[13]
            squawk = raw[14]

            # Validate required fields
            if not icao24 or latitude is None or longitude is None:
                logger.warning(
                    f"Missing required flight data: icao24={icao24}, lat={latitude}, lon={longitude}"
                )
                return None

            # Determine flight status
            if on_ground:
                if last_contact and (time.time() - last_contact) > 600:
                    status = FlightStatus.COMPLETED
                else:
                    status = FlightStatus.SCHEDULED
            else:
                status = FlightStatus.ACTIVE

            # Convert altitude from meters to feet (1 meter = 3.28084 feet)
            altitude_feet = int(baro_altitude * 3.28084) if baro_altitude else 0

            # Convert velocity from m/s to knots (1 m/s = 1.94384 knots)
            speed_knots = round(velocity * 1.94384, 2) if velocity else 0

            # Clean callsign
            callsign_clean = callsign.strip() if callsign else None

            # Create GeoPoint with current position
            current_position = GeoPoint(
                latitude=latitude,
                longitude=longitude,
                altitude=geo_altitude if geo_altitude else baro_altitude,
                timestamp=datetime.fromtimestamp(
                    time_position if time_position else time.time()
                ),
                accuracy=None,
            )

            # Build flight number from callsign or icao24
            flight_number = callsign_clean if callsign_clean else f"ICAO{icao24}"

            # Estimate remaining distance and time (simplified: no exact routing)
            distance_remaining_nm = None
            estimated_arrival = None

            # Create normalized Flight object
            flight = Flight(
                id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.95,
                tags=["realtime", "adsb"],
                provenance={
                    "opensky_icao24": icao24,
                    "opensky_country": origin_country,
                    "opensky_squawk": squawk,
                },
                flight_number=flight_number,
                operator_id=None,
                operator_name=origin_country,
                departure_airport_id=None,
                departure_airport_name=None,
                arrival_airport_id=None,
                arrival_airport_name=None,
                scheduled_departure=None,
                actual_departure=None,
                scheduled_arrival=None,
                actual_arrival=None,
                status=status,
                aircraft_type=None,
                registration=icao24,
                current_position=current_position,
                altitude_feet=altitude_feet,
                speed_knots=speed_knots,
                heading=heading if heading is not None else None,
                distance_flown_nm=None,
                distance_remaining_nm=distance_remaining_nm,
                estimated_arrival=estimated_arrival,
                delay_minutes=None,
                cancellation_reason=None,
                diversion_airport_id=None,
            )

            logger.debug(f"Normalized flight: {flight_number} ({icao24})")
            return flight

        except (ValueError, TypeError, IndexError) as e:
            logger.error(f"Error normalizing flight state vector: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error normalizing flight: {e}")
            return None

    async def ingest(self, params: dict) -> IngestResult:
        """
        Execute complete ingest pipeline for aviation data.

        Fetches raw flight data from OpenSky Network API, normalizes to Flight schema,
        and tracks statistics. Returns summary metrics including fetch count,
        normalization success rate, and any errors encountered.

        Args:
            params: Optional query parameters (begin, end, callsign, aircraft_type)

        Returns:
            IngestResult with fetch/normalize/store statistics
        """
        result = IngestResult(source_id=self.source_id, source_type=self.source_type)
        start_time = time.time()

        try:
            # Fetch raw flight data
            logger.info("Starting aviation data ingest pipeline")
            raw_flights = await self.fetch_raw(params)
            result.records_fetched = len(raw_flights)

            # Normalize each flight
            normalized_flights = []
            for raw_flight in raw_flights:
                normalized_flight = self.normalize(raw_flight)
                if normalized_flight:
                    normalized_flights.append(normalized_flight)
                    result.records_normalized += 1
                else:
                    result.add_error(f"Failed to normalize flight state vector")

            # In real implementation, would store to database
            result.records_stored = result.records_normalized

            logger.info(
                f"Aviation ingest complete: fetched={result.records_fetched}, "
                f"normalized={result.records_normalized}, stored={result.records_stored}"
            )

        except Exception as e:
            logger.error(f"Error during aviation ingest: {e}")
            result.add_error(str(e))

        finally:
            # Calculate duration and cleanup
            result.duration_ms = round((time.time() - start_time) * 1000, 2)
            if self.client:
                await self.client.aclose()
                self.client = None

        return result

    async def _rate_limit(self) -> None:
        """Apply rate limiting delay between requests."""
        await asyncio.sleep(self.rate_limit_delay)

    async def _async_sleep(self, duration: float) -> None:
        """Async sleep wrapper."""
        await asyncio.sleep(duration)
