"""Graph Ingestion Service - Phase 3

Handles ingestion of various entity types into the Neo4j graph database.
Provides async methods for batch importing events, infrastructure, and transport entities.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

from app.graph.client import GraphClient
from app.graph.nodes import (
    EventNode, AirportNode, PortNode, CorridorNode, RouteNode,
    FlightNode, VesselNode, ActorNode, RegionNode
)
from app.graph.edges import (
    OccurredInEdge, LocatedAtEdge, InvolvesEdge, OperatedByEdge,
    ConnectsEdge, TravelsInEdge, CallsAtEdge, AdjacentToEdge
)

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of ingestion operation"""
    entity_type: str
    records_processed: int
    nodes_created: int
    edges_created: int
    errors: List[str]
    duration_ms: float


class GraphIngestionService:
    """Service for ingesting entities into Neo4j graph database"""

    def __init__(self, graph_client: GraphClient):
        """Initialize with graph client"""
        self.client = graph_client

    async def ingest_events(
        self,
        events: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> IngestionResult:
        """
        Ingest events into graph database
        
        Args:
            events: List of event dictionaries with keys: id, name, event_type, severity,
                   location (dict with lat/lon), timestamp, actors (list), affected_entities (dict)
            batch_size: Number of events to process per transaction
            
        Returns:
            IngestionResult with statistics
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            entity_type="Event",
            records_processed=len(events),
            nodes_created=0,
            edges_created=0,
            errors=[]
        )

        try:
            for i in range(0, len(events), batch_size):
                batch = events[i:i + batch_size]
                
                async with self.client.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for event_data in batch:
                            try:
                                # Create event node
                                event_node = EventNode(
                                    id=event_data.get("id", f"event_{datetime.utcnow().timestamp()}"),
                                    name=event_data.get("name", ""),
                                    event_type=event_data.get("event_type", "unknown"),
                                    severity=float(event_data.get("severity", 0.5)),
                                    latitude=float(event_data.get("location", {}).get("lat", 0)),
                                    longitude=float(event_data.get("location", {}).get("lon", 0)),
                                    timestamp=datetime.fromisoformat(event_data.get("timestamp", datetime.utcnow().isoformat())),
                                    description=event_data.get("description", "")
                                )

                                # Create event node
                                cypher = f"""
                                MERGE (e:{event_node.label()} {{{event_node.to_cypher_properties()}}})
                                RETURN id(e) as node_id
                                """
                                await tx.run(cypher)
                                result.nodes_created += 1

                                # Create INVOLVES relationships with actors
                                for actor_id in event_data.get("actors", []):
                                    involves_cypher = f"""
                                    MATCH (e:{event_node.label()} {{id: "{event_node.id}"}})
                                    MATCH (a:Actor {{id: "{actor_id}"}})
                                    MERGE (e)-[:INVOLVES]->(a)
                                    """
                                    await tx.run(involves_cypher)
                                    result.edges_created += len(event_data.get("actors", []))

                                # Create OCCURRED_IN relationship with region if location provided
                                if "location" in event_data:
                                    region_cypher = f"""
                                    MATCH (e:{event_node.label()} {{id: "{event_node.id}"}})
                                    MATCH (r:Region {{contains_point: point({{latitude: {event_node.latitude}, longitude: {event_node.longitude}}})}}))
                                    MERGE (e)-[:OCCURRED_IN]->(r)
                                    """
                                    try:
                                        await tx.run(region_cypher)
                                        result.edges_created += 1
                                    except Exception as e:
                                        logger.debug(f"Region lookup failed for event {event_node.id}: {e}")

                            except Exception as e:
                                error_msg = f"Error ingesting event {event_data.get('id', 'unknown')}: {str(e)}"
                                logger.error(error_msg)
                                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Batch transaction failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def ingest_airports(
        self,
        airports: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> IngestionResult:
        """
        Ingest airports into graph database
        
        Args:
            airports: List of airport dicts with id, iata, name, location (lat/lon), country, status
            batch_size: Batch processing size
            
        Returns:
            IngestionResult with statistics
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            entity_type="Airport",
            records_processed=len(airports),
            nodes_created=0,
            edges_created=0,
            errors=[]
        )

        try:
            for i in range(0, len(airports), batch_size):
                batch = airports[i:i + batch_size]
                
                async with self.client.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for airport_data in batch:
                            try:
                                airport_node = AirportNode(
                                    id=airport_data.get("id", airport_data.get("iata", "")),
                                    iata=airport_data.get("iata", ""),
                                    name=airport_data.get("name", ""),
                                    latitude=float(airport_data.get("location", {}).get("lat", 0)),
                                    longitude=float(airport_data.get("location", {}).get("lon", 0)),
                                    country=airport_data.get("country", ""),
                                    status=airport_data.get("status", "operational")
                                )

                                cypher = f"""
                                MERGE (a:{airport_node.label()} {{{airport_node.to_cypher_properties()}}})
                                RETURN id(a) as node_id
                                """
                                await tx.run(cypher)
                                result.nodes_created += 1

                            except Exception as e:
                                error_msg = f"Error ingesting airport {airport_data.get('id', 'unknown')}: {str(e)}"
                                logger.error(error_msg)
                                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Airport batch transaction failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def ingest_ports(
        self,
        ports: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> IngestionResult:
        """
        Ingest ports into graph database
        
        Args:
            ports: List of port dicts with id, unlocode, name, location (lat/lon), country, status
            batch_size: Batch processing size
            
        Returns:
            IngestionResult with statistics
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            entity_type="Port",
            records_processed=len(ports),
            nodes_created=0,
            edges_created=0,
            errors=[]
        )

        try:
            for i in range(0, len(ports), batch_size):
                batch = ports[i:i + batch_size]
                
                async with self.client.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for port_data in batch:
                            try:
                                port_node = PortNode(
                                    id=port_data.get("id", port_data.get("unlocode", "")),
                                    unlocode=port_data.get("unlocode", ""),
                                    name=port_data.get("name", ""),
                                    latitude=float(port_data.get("location", {}).get("lat", 0)),
                                    longitude=float(port_data.get("location", {}).get("lon", 0)),
                                    country=port_data.get("country", ""),
                                    status=port_data.get("status", "operational")
                                )

                                cypher = f"""
                                MERGE (p:{port_node.label()} {{{port_node.to_cypher_properties()}}})
                                RETURN id(p) as node_id
                                """
                                await tx.run(cypher)
                                result.nodes_created += 1

                            except Exception as e:
                                error_msg = f"Error ingesting port {port_data.get('id', 'unknown')}: {str(e)}"
                                logger.error(error_msg)
                                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Port batch transaction failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def ingest_corridors(
        self,
        corridors: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> IngestionResult:
        """
        Ingest corridors into graph database
        
        Args:
            corridors: List of corridor dicts with id, name, origin_id, destination_id, type, distance
            batch_size: Batch processing size
            
        Returns:
            IngestionResult with statistics
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            entity_type="Corridor",
            records_processed=len(corridors),
            nodes_created=0,
            edges_created=0,
            errors=[]
        )

        try:
            for i in range(0, len(corridors), batch_size):
                batch = corridors[i:i + batch_size]
                
                async with self.client.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for corridor_data in batch:
                            try:
                                corridor_node = CorridorNode(
                                    id=corridor_data.get("id", f"corridor_{datetime.utcnow().timestamp()}"),
                                    name=corridor_data.get("name", ""),
                                    corridor_type=corridor_data.get("type", "sea"),
                                    distance_km=float(corridor_data.get("distance", 0))
                                )

                                cypher = f"""
                                MERGE (c:{corridor_node.label()} {{{corridor_node.to_cypher_properties()}}})
                                RETURN id(c) as node_id
                                """
                                await tx.run(cypher)
                                result.nodes_created += 1

                                # Create CONNECTS relationships
                                origin_id = corridor_data.get("origin_id")
                                dest_id = corridor_data.get("destination_id")
                                if origin_id and dest_id:
                                    connects_cypher = f"""
                                    MATCH (c:{corridor_node.label()} {{id: "{corridor_node.id}"}})
                                    MATCH (origin {{id: "{origin_id}"}})
                                    MATCH (dest {{id: "{dest_id}"}})
                                    MERGE (origin)-[:CONNECTS {{distance_km: {corridor_node.distance_km}}}]->(c)
                                    MERGE (c)-[:CONNECTS {{distance_km: {corridor_node.distance_km}}}]->(dest)
                                    """
                                    try:
                                        await tx.run(connects_cypher)
                                        result.edges_created += 2
                                    except Exception as e:
                                        logger.debug(f"Failed to create corridor connections: {e}")

                            except Exception as e:
                                error_msg = f"Error ingesting corridor {corridor_data.get('id', 'unknown')}: {str(e)}"
                                logger.error(error_msg)
                                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Corridor batch transaction failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def ingest_flights(
        self,
        flights: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> IngestionResult:
        """
        Ingest flights into graph database
        
        Args:
            flights: List of flight dicts with id, callsign, origin_id, destination_id, 
                    aircraft_type, departure_time, arrival_time, status, operator_id
            batch_size: Batch processing size
            
        Returns:
            IngestionResult with statistics
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            entity_type="Flight",
            records_processed=len(flights),
            nodes_created=0,
            edges_created=0,
            errors=[]
        )

        try:
            for i in range(0, len(flights), batch_size):
                batch = flights[i:i + batch_size]
                
                async with self.client.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for flight_data in batch:
                            try:
                                flight_node = FlightNode(
                                    id=flight_data.get("id", flight_data.get("callsign", "")),
                                    callsign=flight_data.get("callsign", ""),
                                    aircraft_type=flight_data.get("aircraft_type", ""),
                                    departure_time=datetime.fromisoformat(flight_data.get("departure_time", datetime.utcnow().isoformat())),
                                    arrival_time=datetime.fromisoformat(flight_data.get("arrival_time", (datetime.utcnow() + timedelta(hours=5)).isoformat())),
                                    status=flight_data.get("status", "scheduled")
                                )

                                cypher = f"""
                                MERGE (f:{flight_node.label()} {{{flight_node.to_cypher_properties()}}})
                                RETURN id(f) as node_id
                                """
                                await tx.run(cypher)
                                result.nodes_created += 1

                                # Create DEPARTS_FROM and ARRIVES_AT relationships
                                origin_id = flight_data.get("origin_id")
                                dest_id = flight_data.get("destination_id")
                                if origin_id:
                                    depart_cypher = f"""
                                    MATCH (f:{flight_node.label()} {{id: "{flight_node.id}"}})
                                    MATCH (origin:Airport {{id: "{origin_id}"}})
                                    MERGE (f)-[:DEPARTS_FROM]->(origin)
                                    """
                                    try:
                                        await tx.run(depart_cypher)
                                        result.edges_created += 1
                                    except Exception as e:
                                        logger.debug(f"Failed to create DEPARTS_FROM: {e}")

                                if dest_id:
                                    arrive_cypher = f"""
                                    MATCH (f:{flight_node.label()} {{id: "{flight_node.id}"}})
                                    MATCH (dest:Airport {{id: "{dest_id}"}})
                                    MERGE (f)-[:ARRIVES_AT]->(dest)
                                    """
                                    try:
                                        await tx.run(arrive_cypher)
                                        result.edges_created += 1
                                    except Exception as e:
                                        logger.debug(f"Failed to create ARRIVES_AT: {e}")

                                # Create OPERATED_BY relationship
                                operator_id = flight_data.get("operator_id")
                                if operator_id:
                                    op_cypher = f"""
                                    MATCH (f:{flight_node.label()} {{id: "{flight_node.id}"}})
                                    MATCH (org:Organization {{id: "{operator_id}"}})
                                    MERGE (f)-[:OPERATED_BY]->(org)
                                    """
                                    try:
                                        await tx.run(op_cypher)
                                        result.edges_created += 1
                                    except Exception as e:
                                        logger.debug(f"Failed to create OPERATED_BY: {e}")

                            except Exception as e:
                                error_msg = f"Error ingesting flight {flight_data.get('id', 'unknown')}: {str(e)}"
                                logger.error(error_msg)
                                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Flight batch transaction failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def ingest_vessels(
        self,
        vessels: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> IngestionResult:
        """
        Ingest vessels into graph database
        
        Args:
            vessels: List of vessel dicts with id, mmsi, imo, name, vessel_type, flag_state, status, operator_id
            batch_size: Batch processing size
            
        Returns:
            IngestionResult with statistics
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            entity_type="Vessel",
            records_processed=len(vessels),
            nodes_created=0,
            edges_created=0,
            errors=[]
        )

        try:
            for i in range(0, len(vessels), batch_size):
                batch = vessels[i:i + batch_size]
                
                async with self.client.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for vessel_data in batch:
                            try:
                                vessel_node = VesselNode(
                                    id=vessel_data.get("id", vessel_data.get("mmsi", "")),
                                    mmsi=vessel_data.get("mmsi", ""),
                                    imo=vessel_data.get("imo", ""),
                                    name=vessel_data.get("name", ""),
                                    vessel_type=vessel_data.get("vessel_type", "general_cargo"),
                                    flag_state=vessel_data.get("flag_state", ""),
                                    status=vessel_data.get("status", "in_transit")
                                )

                                cypher = f"""
                                MERGE (v:{vessel_node.label()} {{{vessel_node.to_cypher_properties()}}})
                                RETURN id(v) as node_id
                                """
                                await tx.run(cypher)
                                result.nodes_created += 1

                                # Create OPERATED_BY relationship
                                operator_id = vessel_data.get("operator_id")
                                if operator_id:
                                    op_cypher = f"""
                                    MATCH (v:{vessel_node.label()} {{id: "{vessel_node.id}"}})
                                    MATCH (org:Organization {{id: "{operator_id}"}})
                                    MERGE (v)-[:OPERATED_BY]->(org)
                                    """
                                    try:
                                        await tx.run(op_cypher)
                                        result.edges_created += 1
                                    except Exception as e:
                                        logger.debug(f"Failed to create OPERATED_BY: {e}")

                            except Exception as e:
                                error_msg = f"Error ingesting vessel {vessel_data.get('id', 'unknown')}: {str(e)}"
                                logger.error(error_msg)
                                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Vessel batch transaction failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def ingest_actors(
        self,
        actors: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> IngestionResult:
        """
        Ingest actors into graph database
        
        Args:
            actors: List of actor dicts with id, name, actor_type, country, risk_level, status
            batch_size: Batch processing size
            
        Returns:
            IngestionResult with statistics
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            entity_type="Actor",
            records_processed=len(actors),
            nodes_created=0,
            edges_created=0,
            errors=[]
        )

        try:
            for i in range(0, len(actors), batch_size):
                batch = actors[i:i + batch_size]
                
                async with self.client.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        for actor_data in batch:
                            try:
                                actor_node = ActorNode(
                                    id=actor_data.get("id", f"actor_{datetime.utcnow().timestamp()}"),
                                    name=actor_data.get("name", ""),
                                    actor_type=actor_data.get("actor_type", "unknown"),
                                    country=actor_data.get("country", ""),
                                    risk_level=float(actor_data.get("risk_level", 0.5)),
                                    status=actor_data.get("status", "active")
                                )

                                cypher = f"""
                                MERGE (a:{actor_node.label()} {{{actor_node.to_cypher_properties()}}})
                                RETURN id(a) as node_id
                                """
                                await tx.run(cypher)
                                result.nodes_created += 1

                            except Exception as e:
                                error_msg = f"Error ingesting actor {actor_data.get('id', 'unknown')}: {str(e)}"
                                logger.error(error_msg)
                                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Actor batch transaction failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def build_topology(
        self,
        connectivity_map: Dict[str, List[str]]
    ) -> IngestionResult:
        """
        Build topology by creating ADJACENT_TO and CONNECTED_TO relationships between infrastructure nodes
        
        Args:
            connectivity_map: Dict mapping node IDs to lists of connected node IDs
            
        Returns:
            IngestionResult with statistics
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            entity_type="Topology",
            records_processed=len(connectivity_map),
            nodes_created=0,
            edges_created=0,
            errors=[]
        )

        try:
            async with self.client.driver.session() as session:
                async with session.begin_transaction() as tx:
                    for node_id, connected_ids in connectivity_map.items():
                        for connected_id in connected_ids:
                            try:
                                # Create bidirectional ADJACENT_TO relationship
                                cypher = f"""
                                MATCH (a {{id: "{node_id}"}})
                                MATCH (b {{id: "{connected_id}"}})
                                MERGE (a)-[:ADJACENT_TO]->(b)
                                MERGE (b)-[:ADJACENT_TO]->(a)
                                """
                                await tx.run(cypher)
                                result.edges_created += 2

                            except Exception as e:
                                error_msg = f"Failed to create topology link {node_id} -> {connected_id}: {str(e)}"
                                logger.debug(error_msg)
                                result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Topology build transaction failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result
