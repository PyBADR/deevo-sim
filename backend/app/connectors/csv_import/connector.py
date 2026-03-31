"""
CSV/JSON Import Connector for generic data ingestion.

Supports importing data from CSV and JSON files with auto-detection and
schema validation. Handles events, airports, ports, corridors, flights, and vessels.
"""

import asyncio
import csv
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Type

import httpx

from app.connectors.base.connector import BaseConnector, IngestResult
from app.schema.enums import (
    EventType,
    SeverityLevel,
    FlightStatus,
    VesselType,
    AssetType,
)
from app.schema.events import Event
from app.schema.transport import Flight, Vessel, Operator
from app.schema.infrastructure import Airport, Port, Corridor, Route
from app.schema.geo import GeoPoint

logger = logging.getLogger(__name__)


# Schema mapping for auto-detection
SCHEMA_MAPPING = {
    "events": Event,
    "airports": Airport,
    "ports": Port,
    "corridors": Corridor,
    "routes": Route,
    "flights": Flight,
    "vessels": Vessel,
}


class CSVImportConnector(BaseConnector):
    """Connector for importing data from CSV and JSON files."""

    def __init__(
        self,
        source_id: str = "csv_import",
        source_type: str = "csv",
        timeout: float = 30.0,
    ):
        """
        Initialize CSVImportConnector.

        Args:
            source_id: Unique identifier for this data source
            source_type: Type of data source (csv)
            timeout: HTTP request timeout in seconds
        """
        super().__init__(source_id=source_id, source_type=source_type)
        self.timeout = timeout

    async def fetch_raw(self, params: dict) -> list[dict]:
        """
        Fetch raw data from CSV or JSON file.

        Supports both local file paths and remote URLs. Auto-detects format based
        on file extension or content inspection.

        Args:
            params: Required - 'file_path' (str) or 'url' (str)
                   Optional - 'format' ('csv' or 'json'), 'delimiter' (for CSV)

        Returns:
            List of records (dict objects) from the file
        """
        records = []

        try:
            # Get file source - prioritize url over file_path
            file_source = params.get("url") or params.get("file_path")
            if not file_source:
                logger.error("Missing file_path or url in params")
                return []

            # Auto-detect format if not specified
            file_format = params.get("format", "").lower()
            if not file_format:
                if file_source.startswith("http://") or file_source.startswith(
                    "https://"
                ):
                    file_format = "json" if ".json" in file_source else "csv"
                else:
                    file_format = (
                        "json" if file_source.endswith(".json") else "csv"
                    )

            logger.info(f"Importing {file_format.upper()} from {file_source}")

            # Fetch data based on source type
            if file_source.startswith("http://") or file_source.startswith("https://"):
                records = await self._fetch_from_url(file_source, file_format)
            else:
                records = self._fetch_from_file(file_source, file_format, params)

            logger.info(f"Fetched {len(records)} records from {file_source}")
            return records

        except Exception as e:
            logger.error(f"Error fetching data from file: {e}")
            return []

    async def _fetch_from_url(
        self, url: str, file_format: str
    ) -> list[dict]:
        """
        Fetch records from remote URL.

        Args:
            url: Remote URL to fetch from
            file_format: Format ('csv' or 'json')

        Returns:
            List of records
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.text

            if file_format == "json":
                data = json.loads(content)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "records" in data:
                    return data["records"]
                elif isinstance(data, dict) and "data" in data:
                    return data["data"]
                else:
                    return [data]
            else:  # CSV
                lines = content.strip().split("\n")
                reader = csv.DictReader(lines)
                return list(reader) if reader else []

        except httpx.RequestError as e:
            logger.error(f"Failed to fetch from URL {url}: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching from URL: {e}")
            return []

    def _fetch_from_file(
        self, file_path: str, file_format: str, params: dict
    ) -> list[dict]:
        """
        Fetch records from local file.

        Args:
            file_path: Path to local file
            file_format: Format ('csv' or 'json')
            params: Optional parameters (delimiter for CSV)

        Returns:
            List of records
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return []

            if file_format == "json":
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "records" in data:
                    return data["records"]
                elif isinstance(data, dict) and "data" in data:
                    return data["data"]
                else:
                    return [data]
            else:  # CSV
                delimiter = params.get("delimiter", ",")
                records = []
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    records = list(reader) if reader else []
                return records

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []

    def normalize(self, raw: dict) -> Optional[Any]:
        """
        Normalize raw record based on inferred schema.

        Auto-detects the appropriate schema (Event, Flight, Vessel, etc.) based
        on field presence and attempts validation. Returns normalized object or
        None if validation fails.

        Args:
            raw: Raw record (dict) from CSV or JSON

        Returns:
            Normalized object matching detected schema or None if validation fails
        """
        try:
            if not isinstance(raw, dict):
                logger.warning(f"Invalid record format: {raw}")
                return None

            # Infer schema from available fields
            schema_class = self._infer_schema(raw)
            if not schema_class:
                logger.warning(f"Unable to infer schema for record: {raw}")
                return None

            # Build normalized object based on schema
            if schema_class == Event:
                return self._normalize_event(raw)
            elif schema_class == Flight:
                return self._normalize_flight(raw)
            elif schema_class == Vessel:
                return self._normalize_vessel(raw)
            elif schema_class == Airport:
                return self._normalize_airport(raw)
            elif schema_class == Port:
                return self._normalize_port(raw)
            elif schema_class == Corridor:
                return self._normalize_corridor(raw)
            else:
                logger.warning(f"Unsupported schema: {schema_class}")
                return None

        except Exception as e:
            logger.error(f"Error normalizing record: {e}")
            return None

    def _infer_schema(self, record: dict) -> Optional[Type]:
        """
        Infer the appropriate schema class based on record fields.

        Args:
            record: Raw record

        Returns:
            Schema class (Event, Flight, Vessel, Airport, Port, Corridor) or None
        """
        keys = {k.lower() for k in record.keys()}

        # Check for Event fields
        if any(
            k in keys for k in ["event_type", "severity", "event_date", "fatalities"]
        ):
            return Event

        # Check for Flight fields
        if any(
            k in keys
            for k in ["flight_number", "aircraft_type", "altitude", "speed_knots"]
        ):
            return Flight

        # Check for Vessel fields
        if any(k in keys for k in ["mmsi", "imo", "vessel_type", "draft_meters"]):
            return Vessel

        # Check for Airport fields
        if any(k in keys for k in ["icao_code", "iata_code", "runways", "elevation"]):
            return Airport

        # Check for Port fields
        if any(
            k in keys
            for k in ["port_code", "un_locode", "berth_count", "annual_throughput"]
        ):
            return Port

        # Check for Corridor fields
        if any(k in keys for k in ["corridor_type", "origin_location", "waypoints"]):
            return Corridor

        return None

    def _normalize_event(self, raw: dict) -> Optional[Event]:
        """Normalize record to Event schema."""
        try:
            event = Event(
                id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.85,
                tags=["csv_import"],
                provenance=raw,
                name=raw.get("name") or raw.get("event_type", "Unknown Event"),
                description=raw.get("description", ""),
                description_ar=raw.get("description_ar", ""),
                event_type=EventType[
                    (raw.get("event_type", "OTHER")).upper().replace(" ", "_")
                ]
                if raw.get("event_type")
                else EventType.OTHER,
                severity=float(raw.get("severity", 0.5)),
                location=GeoPoint(
                    latitude=float(raw.get("latitude", 0)),
                    longitude=float(raw.get("longitude", 0)),
                    altitude=None,
                    timestamp=datetime.utcnow(),
                    accuracy=None,
                ),
                start_time=datetime.utcnow(),
                end_time=None,
                actors=[],
                affected_entities=[],
                sources=[],
                impact_summary="",
                external_references=[],
            )
            return event
        except Exception as e:
            logger.error(f"Error normalizing event: {e}")
            return None

    def _normalize_flight(self, raw: dict) -> Optional[Flight]:
        """Normalize record to Flight schema."""
        try:
            flight = Flight(
                id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.85,
                tags=["csv_import"],
                provenance=raw,
                flight_number=raw.get("flight_number", ""),
                operator_id=None,
                operator_name=raw.get("operator_name", ""),
                departure_airport_id=raw.get("departure_airport_id"),
                departure_airport_name=raw.get("departure_airport_name", ""),
                arrival_airport_id=raw.get("arrival_airport_id"),
                arrival_airport_name=raw.get("arrival_airport_name", ""),
                scheduled_departure=None,
                actual_departure=None,
                scheduled_arrival=None,
                actual_arrival=None,
                status=FlightStatus.SCHEDULED,
                aircraft_type=raw.get("aircraft_type"),
                registration=raw.get("registration"),
                current_position=GeoPoint(
                    latitude=float(raw.get("latitude", 0)),
                    longitude=float(raw.get("longitude", 0)),
                    altitude=None,
                    timestamp=datetime.utcnow(),
                    accuracy=None,
                ),
                altitude_feet=int(raw.get("altitude_feet", 0)),
                speed_knots=float(raw.get("speed_knots", 0)),
                heading=float(raw.get("heading", 0)) if raw.get("heading") else None,
                distance_flown_nm=None,
                distance_remaining_nm=None,
                estimated_arrival=None,
                delay_minutes=None,
                cancellation_reason=None,
                diversion_airport_id=None,
            )
            return flight
        except Exception as e:
            logger.error(f"Error normalizing flight: {e}")
            return None

    def _normalize_vessel(self, raw: dict) -> Optional[Vessel]:
        """Normalize record to Vessel schema."""
        try:
            vessel = Vessel(
                id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.85,
                tags=["csv_import"],
                provenance=raw,
                mmsi=raw.get("mmsi", ""),
                imo=raw.get("imo"),
                vessel_name=raw.get("vessel_name", ""),
                callsign=raw.get("callsign"),
                vessel_type=VesselType.OTHER,
                flag_state=raw.get("flag_state"),
                owner_id=None,
                operator_id=None,
                operator_name=raw.get("operator_name"),
                year_built=int(raw.get("year_built", 0)) if raw.get("year_built") else None,
                length_meters=float(raw.get("length_meters", 0)) if raw.get("length_meters") else None,
                beam_meters=float(raw.get("beam_meters", 0)) if raw.get("beam_meters") else None,
                draft_meters=float(raw.get("draft_meters", 0)) if raw.get("draft_meters") else None,
                gross_tonnage=float(raw.get("gross_tonnage", 0)) if raw.get("gross_tonnage") else None,
                deadweight_tonnage=float(raw.get("deadweight_tonnage", 0)) if raw.get("deadweight_tonnage") else None,
                teu_capacity=None,
                current_position=GeoPoint(
                    latitude=float(raw.get("latitude", 0)),
                    longitude=float(raw.get("longitude", 0)),
                    altitude=None,
                    timestamp=datetime.utcnow(),
                    accuracy=None,
                ),
                destination_port_id=None,
                destination_port_name=raw.get("destination_port_name"),
                estimated_arrival=None,
                speed_knots=float(raw.get("speed_knots", 0)) if raw.get("speed_knots") else 0.0,
                heading=float(raw.get("heading", 0)) if raw.get("heading") else None,
                status=raw.get("status", "moored"),
                cargo_description=raw.get("cargo_description"),
                imo_hazmat=False,
            )
            return vessel
        except Exception as e:
            logger.error(f"Error normalizing vessel: {e}")
            return None

    def _normalize_airport(self, raw: dict) -> Optional[Airport]:
        """Normalize record to Airport schema."""
        try:
            airport = Airport(
                id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.85,
                tags=["csv_import"],
                provenance=raw,
                name=raw.get("name", ""),
                name_ar=raw.get("name_ar", ""),
                asset_type=AssetType.AIRPORT,
                location=GeoPoint(
                    latitude=float(raw.get("latitude", 0)),
                    longitude=float(raw.get("longitude", 0)),
                    altitude=None,
                    timestamp=datetime.utcnow(),
                    accuracy=None,
                ),
                country_code=raw.get("country_code"),
                operational_status="operational",
                capacity=None,
                critical_infrastructure=True,
                inspection_date=None,
                maintenance_schedule=None,
                icao_code=raw.get("icao_code"),
                iata_code=raw.get("iata_code"),
                city=raw.get("city", ""),
                runways=int(raw.get("runways", 1)) if raw.get("runways") else 1,
                elevation_meters=float(raw.get("elevation_meters", 0)) if raw.get("elevation_meters") else None,
                max_capacity_daily=None,
                airlines=[],
                international_airport=True,
            )
            return airport
        except Exception as e:
            logger.error(f"Error normalizing airport: {e}")
            return None

    def _normalize_port(self, raw: dict) -> Optional[Port]:
        """Normalize record to Port schema."""
        try:
            port = Port(
                id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.85,
                tags=["csv_import"],
                provenance=raw,
                name=raw.get("name", ""),
                name_ar=raw.get("name_ar", ""),
                asset_type=AssetType.PORT,
                location=GeoPoint(
                    latitude=float(raw.get("latitude", 0)),
                    longitude=float(raw.get("longitude", 0)),
                    altitude=None,
                    timestamp=datetime.utcnow(),
                    accuracy=None,
                ),
                country_code=raw.get("country_code"),
                operational_status="operational",
                capacity=None,
                critical_infrastructure=True,
                inspection_date=None,
                maintenance_schedule=None,
                port_code=raw.get("port_code"),
                un_locode=raw.get("un_locode"),
                berth_count=int(raw.get("berth_count", 1)) if raw.get("berth_count") else 1,
                max_draft_meters=None,
                annual_throughput_teu=None,
                annual_throughput_tons=None,
                container_capable=True,
                ro_ro_capable=False,
                bulk_capable=False,
            )
            return port
        except Exception as e:
            logger.error(f"Error normalizing port: {e}")
            return None

    def _normalize_corridor(self, raw: dict) -> Optional[Corridor]:
        """Normalize record to Corridor schema."""
        try:
            corridor = Corridor(
                id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                source_id=self.source_id,
                source_type=self.source_type,
                confidence=0.85,
                tags=["csv_import"],
                provenance=raw,
                name=raw.get("name", ""),
                name_ar=raw.get("name_ar", ""),
                corridor_type=raw.get("corridor_type", "maritime"),
                origin_location=GeoPoint(
                    latitude=float(raw.get("origin_latitude", 0)),
                    longitude=float(raw.get("origin_longitude", 0)),
                    altitude=None,
                    timestamp=datetime.utcnow(),
                    accuracy=None,
                ),
                destination_location=GeoPoint(
                    latitude=float(raw.get("dest_latitude", 0)),
                    longitude=float(raw.get("dest_longitude", 0)),
                    altitude=None,
                    timestamp=datetime.utcnow(),
                    accuracy=None,
                ),
                waypoints=[],
                distance_nm=float(raw.get("distance_nm", 0)) if raw.get("distance_nm") else None,
                distance_km=float(raw.get("distance_km", 0)) if raw.get("distance_km") else None,
                expected_transit_hours=None,
                annual_traffic_volume=None,
                critical_corridor=True,
                bottleneck_zones=[],
            )
            return corridor
        except Exception as e:
            logger.error(f"Error normalizing corridor: {e}")
            return None

    async def ingest(self, params: dict) -> IngestResult:
        """
        Execute complete ingest pipeline for CSV/JSON data.

        Fetches data from file or URL, normalizes records based on inferred schema,
        and tracks statistics. Returns summary metrics including fetch count,
        normalization success rate, and any errors encountered.

        Args:
            params: Required - 'file_path' or 'url'
                   Optional - 'format' ('csv' or 'json'), 'delimiter'

        Returns:
            IngestResult with fetch/normalize/store statistics
        """
        result = IngestResult(source_id=self.source_id, source_type=self.source_type)
        start_time = time.time()

        try:
            logger.info("Starting CSV/JSON import pipeline")
            raw_records = await self.fetch_raw(params)
            result.records_fetched = len(raw_records)

            # Normalize each record
            normalized_records = []
            for raw_record in raw_records:
                normalized_record = self.normalize(raw_record)
                if normalized_record:
                    normalized_records.append(normalized_record)
                    result.records_normalized += 1
                else:
                    result.add_error(f"Failed to normalize record")

            # In real implementation, would store to database
            result.records_stored = result.records_normalized

            logger.info(
                f"CSV/JSON import complete: fetched={result.records_fetched}, "
                f"normalized={result.records_normalized}, stored={result.records_stored}"
            )

        except Exception as e:
            logger.error(f"Error during CSV/JSON import: {e}")
            result.add_error(str(e))

        finally:
            result.duration_ms = round((time.time() - start_time) * 1000, 2)

        return result
