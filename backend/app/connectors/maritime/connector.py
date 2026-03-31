"""
Maritime Data Connector for AIS Vessel Tracking.

Fetches real-time vessel tracking data from AIS (Automatic Identification System)
and normalizes it to the Vessel schema. Supports Gulf waters region filtering.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

import httpx

from app.connectors.base.connector import BaseConnector, IngestResult
from app.schema.enums import VesselType
from app.schema.transport import Vessel
from app.schema.geo import GeoPoint

logger = logging.getLogger(__name__)


# Gulf Waters Bounding Box: Latitude 23-30, Longitude 47-57
GULF_BOUNDING_BOX = {
    "min_lat": 23.0,
    "max_lat": 30.0,
    "min_lon": 47.0,
    "max_lon": 57.0,
}

# AIS vessel type mapping to VesselType enum
AIS_TO_VESSEL_TYPE = {
    30: VesselType.FISHING_VESSEL,
    31: VesselType.FISHING_VESSEL,
    32: VesselType.FISHING_VESSEL,
    36: VesselType.PASSENGER,
    37: VesselType.PASSENGER,
    38: VesselType.PASSENGER,
    39: VesselType.PASSENGER,
    52: VesselType.TUG,
    53: VesselType.TUG,
    54: VesselType.TUG,
    55: VesselType.TUG,
    56: VesselType.TUG,
    57: VesselType.TUG,
    58: VesselType.BARGE,
    59: VesselType.BARGE,
    60: VesselType.PASSENGER,
    61: VesselType.PASSENGER,
    62: VesselType.PASSENGER,
    63: VesselType.PASSENGER,
    64: VesselType.PASSENGER,
    66: VesselType.PASSENGER,
    67: VesselType.PASSENGER,
    68: VesselType.PASSENGER,
    69: VesselType.PASSENGER,
    70: VesselType.CONTAINER_SHIP,
    71: VesselType.CONTAINER_SHIP,
    72: VesselType.CONTAINER_SHIP,
    73: VesselType.CONTAINER_SHIP,
    74: VesselType.CONTAINER_SHIP,
    75: VesselType.BULK_CARRIER,
    76: VesselType.BULK_CARRIER,
    77: VesselType.BULK_CARRIER,
    78: VesselType.BULK_CARRIER,
    79: VesselType.BULK_CARRIER,
    80: VesselType.TANKER,
    81: VesselType.TANKER,
    82: VesselType.TANKER,
    83: VesselType.TANKER,
    84: VesselType.TANKER,
    85: VesselType.TANKER,
    86: VesselType.TANKER,
    87: VesselType.TANKER,
    88: VesselType.TANKER,
    89: VesselType.TANKER,
}


class MaritimeConnector(BaseConnector):
    """Connector for AIS-based vessel tracking data."""

    BASE_URL = "https://data.aismessages.com"

    def __init__(
        self,
        source_id: str = "ais_maritime",
        source_type: str = "maritime",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize MaritimeConnector.

        Args:
            source_id: Unique identifier for this data source
            source_type: Type of data source (maritime)
            api_key: API key for AIS data provider (optional)
            timeout: HTTP request timeout in seconds
            rate_limit_delay: Delay between API requests in seconds
        """
        super().__init__(source_id=source_id, source_type=source_type)
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.client: Optional[httpx.AsyncClient] = None

    async def fetch_raw(self, params: dict) -> list[dict]:
        """
        Fetch raw vessel data from AIS API.

        Queries vessels in Gulf waters region by bounding box. Supports filtering by:
        - mmsi: Maritime Mobile Service Identity number
        - flag_state: Flag state country code
        - vessel_type: AIS vessel type code
        - min_speed: Minimum speed in knots
        - max_speed: Maximum speed in knots

        Args:
            params: Query parameters (optional: mmsi, flag_state, vessel_type, speeds)

        Returns:
            List of vessel records from API response
        """
        if self.client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.client = httpx.AsyncClient(
                headers=headers, timeout=self.timeout, verify=True
            )

        vessels = []
        try:
            # Query vessels in bounding box
            url = f"{self.BASE_URL}/v1/vessels"

            # Build query parameters with Gulf bounding box
            query_params = {
                "bbox": f"{GULF_BOUNDING_BOX['min_lon']},{GULF_BOUNDING_BOX['min_lat']},{GULF_BOUNDING_BOX['max_lon']},{GULF_BOUNDING_BOX['max_lat']}",
                "limit": params.get("limit", 1000),
                "format": "json",
            }

            # Apply optional MMSI filter
            if "mmsi" in params:
                query_params["mmsi"] = params["mmsi"]

            # Apply optional flag state filter
            if "flag_state" in params:
                query_params["flag"] = params["flag_state"]

            # Apply optional vessel type filter
            if "vessel_type" in params:
                query_params["type"] = params["vessel_type"]

            logger.info(f"Fetching maritime data from {url} with bounds")

            await self._rate_limit()
            response = await self.client.get(url, params=query_params)
            response.raise_for_status()

            data = response.json()

            # API returns vessels array or data wrapper
            if isinstance(data, list):
                vessels = data
            elif isinstance(data, dict) and "vessels" in data:
                vessels = data["vessels"]
            elif isinstance(data, dict) and "data" in data:
                vessels = data["data"]
            else:
                vessels = []

            logger.info(f"Fetched {len(vessels)} vessels from AIS API")

            # Apply optional speed range filter
            if "min_speed" in params or "max_speed" in params:
                min_speed = params.get("min_speed", 0)
                max_speed = params.get("max_speed", 1000)
                vessels = [
                    v
                    for v in vessels
                    if min_speed <= (v.get("speed", 0) or 0) <= max_speed
                ]
                logger.info(
                    f"Filtered {len(vessels)} vessels by speed {min_speed}-{max_speed} knots"
                )

            return vessels

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching maritime data: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error fetching maritime data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching maritime data: {e}")
            return []

    def normalize(self, raw: dict) -> Optional[Vessel]:
        """
        Normalize raw AIS vessel record to Vessel schema.

        AIS vessel record format includes:
        - mmsi: Maritime Mobile Service Identity (unique vessel identifier)
        - imo: International Maritime Organization number
        - vessel_name: Official vessel name
        - callsign: Radio call sign
        - vessel_type: AIS type code (determines VesselType)
        - flag_state: Country flag (ISO 3166-1 alpha-2)
        - year_built: Construction year
        - length: Length overall in meters
        - beam: Beam (width) in meters
        - draft: Draft (depth) in meters
        - gross_tonnage: Gross tonnage
        - deadweight_tonnage: Deadweight tonnage
        - cargo_type: Cargo description
        - latitude: Current latitude
        - longitude: Current longitude
        - speed: Speed over ground in knots
        - heading: Course over ground in degrees
        - status: Navigation status (0-15)
        - destination: Destination port name
        - eta: Estimated time of arrival (Unix timestamp or string)

        Args:
            raw: Raw AIS vessel record from API

        Returns:
            Normalized Vessel object or None if validation fails
        """
        try:
            if not isinstance(raw, dict):
                logger.warning(f"Invalid vessel record format: {raw}")
                return None

            # Extract vessel fields
            mmsi = raw.get("mmsi")
            imo = raw.get("imo")
            vessel_name = raw.get("vessel_name") or raw.get("name")
            callsign = raw.get("callsign")
            vessel_type_code = raw.get("vessel_type") or raw.get("type")
            flag_state = raw.get("flag_state") or raw.get("flag")
            year_built = raw.get("year_built")
            length_meters = raw.get("length") or raw.get("length_m")
            beam_meters = raw.get("beam") or raw.get("width_m")
            draft_meters = raw.get("draft") or raw.get("draft_m")
            gross_tonnage = raw.get("gross_tonnage") or raw.get("gt")
            deadweight_tonnage = raw.get("deadweight_tonnage") or raw.get("dwt")
            cargo_type = raw.get("cargo_type") or raw.get("cargo")
            latitude = raw.get("latitude") or raw.get("lat")
            longitude = raw.get("longitude") or raw.get("lon")
            speed_knots = raw.get("speed")
            heading = raw.get("heading") or raw.get("course")
            nav_status = raw.get("status") or raw.get("nav_status")
            destination = raw.get("destination") or raw.get("dest_port")
            eta = raw.get("eta")

            # Validate required fields
            if not mmsi or latitude is None or longitude is None:
                logger.warning(
                    f"Missing required vessel data: mmsi={mmsi}, lat={latitude}, lon={longitude}"
                )
                return None

            # Map AIS vessel type to enum
            vessel_type = VesselType.OTHER
            if vessel_type_code in AIS_TO_VESSEL_TYPE:
                vessel_type = AIS_TO_VESSEL_TYPE[vessel_type_code]
            elif isinstance(vessel_type_code, str):
                # Try string mapping
                type_upper = vessel_type_code.upper()
                for vtype in VesselType:
                    if type_upper in vtype.name:
                        vessel_type = vtype
                        break

            # Create GeoPoint with current position
            current_position = GeoPoint(
                latitude=latitude,
                longitude=longitude,
                altitude=None,
                timestamp=datetime.utcnow(),
                accuracy=None,
            )

            # Parse ETA if provided
            estimated_arrival = None
            if eta:
                try:
                    if isinstance(eta, int):
                        estimated_arrival = datetime.fromtimestamp(eta)
                    elif isinstance(eta, str):
                        estimated_arrival = datetime.fromisoformat(eta)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid ETA format: {eta}")

            # Create normalized Vessel object
            vessel = Vessel(
                id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.90,
                tags=["ais", "realtime"],
                provenance={
                    "mmsi": mmsi,
                    "ais_type_code": vessel_type_code,
                    "nav_status": nav_status,
                },
                mmsi=str(mmsi),
                imo=str(imo) if imo else None,
                vessel_name=vessel_name,
                callsign=callsign,
                vessel_type=vessel_type,
                flag_state=flag_state,
                owner_id=None,
                operator_id=None,
                operator_name=None,
                year_built=year_built,
                length_meters=length_meters,
                beam_meters=beam_meters,
                draft_meters=draft_meters,
                gross_tonnage=gross_tonnage,
                deadweight_tonnage=deadweight_tonnage,
                teu_capacity=None,
                current_position=current_position,
                destination_port_id=None,
                destination_port_name=destination,
                estimated_arrival=estimated_arrival,
                speed_knots=speed_knots if speed_knots is not None else 0.0,
                heading=heading if heading is not None else None,
                status="underway" if speed_knots and speed_knots > 0 else "moored",
                cargo_description=cargo_type,
                imo_hazmat=raw.get("hazmat", False),
            )

            logger.debug(f"Normalized vessel: {vessel_name} (MMSI: {mmsi})")
            return vessel

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error normalizing vessel record: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error normalizing vessel: {e}")
            return None

    async def ingest(self, params: dict) -> IngestResult:
        """
        Execute complete ingest pipeline for maritime data.

        Fetches raw AIS vessel data, normalizes to Vessel schema, and tracks
        statistics. Returns summary metrics including fetch count, normalization
        success rate, and any errors encountered.

        Args:
            params: Optional query parameters (mmsi, flag_state, vessel_type, speeds)

        Returns:
            IngestResult with fetch/normalize/store statistics
        """
        result = IngestResult(source_id=self.source_id, source_type=self.source_type)
        start_time = time.time()

        try:
            # Fetch raw vessel data
            logger.info("Starting maritime data ingest pipeline")
            raw_vessels = await self.fetch_raw(params)
            result.records_fetched = len(raw_vessels)

            # Normalize each vessel
            normalized_vessels = []
            for raw_vessel in raw_vessels:
                normalized_vessel = self.normalize(raw_vessel)
                if normalized_vessel:
                    normalized_vessels.append(normalized_vessel)
                    result.records_normalized += 1
                else:
                    result.add_error(f"Failed to normalize vessel record")

            # In real implementation, would store to database
            result.records_stored = result.records_normalized

            logger.info(
                f"Maritime ingest complete: fetched={result.records_fetched}, "
                f"normalized={result.records_normalized}, stored={result.records_stored}"
            )

        except Exception as e:
            logger.error(f"Error during maritime ingest: {e}")
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
