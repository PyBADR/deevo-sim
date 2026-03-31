"""Graph Query Service - Phase 3

Provides async methods for complex graph queries and intelligence analysis.
Supports risk propagation, chokepoint analysis, rerouting, and scenario impact analysis.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.graph.client import GraphClient
from app.graph.queries import GraphQueries

logger = logging.getLogger(__name__)


@dataclass
class PathNode:
    """Node in a path result"""
    id: str
    label: str
    properties: Dict[str, Any]


@dataclass
class PathEdge:
    """Edge in a path result"""
    type: str
    properties: Dict[str, Any]


@dataclass
class Path:
    """A path of connected nodes"""
    nodes: List[PathNode]
    edges: List[PathEdge]
    total_distance: float = 0.0
    risk_score: float = 0.0


@dataclass
class GraphQueryResult:
    """Result of a graph query"""
    query_type: str
    success: bool
    data: Any
    error: Optional[str] = None
    duration_ms: float = 0.0


class GraphQueryService:
    """Service for querying the Neo4j graph database"""

    def __init__(self, graph_client: GraphClient):
        """Initialize with graph client"""
        self.client = graph_client

    async def get_nearest_impacted(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 100,
        impact_threshold: float = 0.3
    ) -> GraphQueryResult:
        """
        Get nearest infrastructure impacted by risk at location
        
        Args:
            latitude: Search center latitude
            longitude: Search center longitude
            radius_km: Search radius in kilometers
            impact_threshold: Minimum risk impact threshold (0-1)
            
        Returns:
            GraphQueryResult with list of impacted infrastructure nodes
        """
        start_time = datetime.utcnow()
        result = GraphQueryResult(
            query_type="nearest_impacted",
            success=False,
            data=None
        )

        try:
            query = GraphQueries.nearest_impacted_assets(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                min_impact=impact_threshold
            )

            async with self.client.driver.session() as session:
                records = await session.run(query)
                impacted = []
                async for record in records:
                    impacted.append({
                        "id": record.get("id"),
                        "type": record.get("type"),
                        "name": record.get("name"),
                        "distance_km": record.get("distance_km"),
                        "impact_score": record.get("impact_score")
                    })

                result.data = impacted
                result.success = True

        except Exception as e:
            error_msg = f"Nearest impacted query failed: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def get_risk_propagation_path(
        self,
        source_node_id: str,
        max_hops: int = 5,
        risk_threshold: float = 0.1
    ) -> GraphQueryResult:
        """
        Get risk propagation paths from a source event/disruption
        
        Args:
            source_node_id: ID of source event node
            max_hops: Maximum relationship hops to follow
            risk_threshold: Minimum risk to include in path
            
        Returns:
            GraphQueryResult with propagation paths
        """
        start_time = datetime.utcnow()
        result = GraphQueryResult(
            query_type="risk_propagation",
            success=False,
            data=None
        )

        try:
            query = GraphQueries.risk_propagation_path(
                source_id=source_node_id,
                max_hops=max_hops,
                min_risk=risk_threshold
            )

            async with self.client.driver.session() as session:
                records = await session.run(query)
                paths = []
                async for record in records:
                    path_data = {
                        "path_id": record.get("path_id"),
                        "source": record.get("source"),
                        "target": record.get("target"),
                        "hops": record.get("hops"),
                        "cumulative_risk": record.get("cumulative_risk"),
                        "nodes": record.get("nodes"),
                        "relationships": record.get("relationships")
                    }
                    paths.append(path_data)

                result.data = paths
                result.success = True

        except Exception as e:
            error_msg = f"Risk propagation query failed: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def get_chokepoint_analysis(
        self,
        minimum_criticality: float = 0.5
    ) -> GraphQueryResult:
        """
        Analyze chokepoints in supply chain corridors
        
        Args:
            minimum_criticality: Minimum criticality score (0-1) for inclusion
            
        Returns:
            GraphQueryResult with chokepoint analysis results
        """
        start_time = datetime.utcnow()
        result = GraphQueryResult(
            query_type="chokepoint_analysis",
            success=False,
            data=None
        )

        try:
            query = GraphQueries.chokepoint_concentration(
                min_criticality=minimum_criticality
            )

            async with self.client.driver.session() as session:
                records = await session.run(query)
                chokepoints = []
                async for record in records:
                    chokepoint = {
                        "node_id": record.get("node_id"),
                        "node_type": record.get("node_type"),
                        "node_name": record.get("node_name"),
                        "criticality_score": record.get("criticality_score"),
                        "throughput_volume": record.get("throughput_volume"),
                        "alternative_routes": record.get("alternative_routes"),
                        "dependency_count": record.get("dependency_count"),
                        "risk_concentration": record.get("risk_concentration")
                    }
                    chokepoints.append(chokepoint)

                result.data = {
                    "chokepoints": chokepoints,
                    "total_identified": len(chokepoints),
                    "average_criticality": (
                        sum(c["criticality_score"] for c in chokepoints) / len(chokepoints)
                        if chokepoints else 0
                    )
                }
                result.success = True

        except Exception as e:
            error_msg = f"Chokepoint analysis query failed: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def get_region_cascade(
        self,
        region_id: str,
        cascade_depth: int = 3
    ) -> GraphQueryResult:
        """
        Get cascading impact analysis for a region
        
        Args:
            region_id: ID of the region to analyze
            cascade_depth: Depth of cascading impact to follow
            
        Returns:
            GraphQueryResult with cascade impact details
        """
        start_time = datetime.utcnow()
        result = GraphQueryResult(
            query_type="region_cascade",
            success=False,
            data=None
        )

        try:
            query = GraphQueries.region_cascade(
                region_id=region_id,
                depth=cascade_depth
            )

            async with self.client.driver.session() as session:
                records = await session.run(query)
                cascade_data = {
                    "region_id": region_id,
                    "levels": []
                }
                
                current_level = 0
                current_level_nodes = []

                async for record in records:
                    node_level = record.get("level", 0)
                    
                    if node_level > current_level:
                        if current_level_nodes:
                            cascade_data["levels"].append({
                                "level": current_level,
                                "nodes": current_level_nodes
                            })
                        current_level = node_level
                        current_level_nodes = []

                    current_level_nodes.append({
                        "id": record.get("id"),
                        "type": record.get("type"),
                        "impact_severity": record.get("impact_severity"),
                        "affected_entities": record.get("affected_entities")
                    })

                if current_level_nodes:
                    cascade_data["levels"].append({
                        "level": current_level,
                        "nodes": current_level_nodes
                    })

                result.data = cascade_data
                result.success = True

        except Exception as e:
            error_msg = f"Region cascade query failed: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def get_scenario_subgraph(
        self,
        scenario_id: str,
        include_impacts: bool = True
    ) -> GraphQueryResult:
        """
        Get subgraph related to a scenario
        
        Args:
            scenario_id: ID of the scenario
            include_impacts: Whether to include impact relationships
            
        Returns:
            GraphQueryResult with scenario subgraph
        """
        start_time = datetime.utcnow()
        result = GraphQueryResult(
            query_type="scenario_subgraph",
            success=False,
            data=None
        )

        try:
            query = GraphQueries.scenario_impact_subgraph(
                scenario_id=scenario_id,
                include_impacts=include_impacts
            )

            async with self.client.driver.session() as session:
                records = await session.run(query)
                
                nodes = {}
                edges = []

                async for record in records:
                    # Collect unique nodes
                    source_id = record.get("source_id")
                    target_id = record.get("target_id")
                    
                    if source_id and source_id not in nodes:
                        nodes[source_id] = {
                            "id": source_id,
                            "type": record.get("source_type"),
                            "properties": record.get("source_properties", {})
                        }
                    
                    if target_id and target_id not in nodes:
                        nodes[target_id] = {
                            "id": target_id,
                            "type": record.get("target_type"),
                            "properties": record.get("target_properties", {})
                        }

                    # Collect edges
                    if source_id and target_id:
                        edges.append({
                            "source": source_id,
                            "target": target_id,
                            "type": record.get("relationship_type"),
                            "properties": record.get("relationship_properties", {})
                        })

                result.data = {
                    "scenario_id": scenario_id,
                    "nodes": list(nodes.values()),
                    "edges": edges
                }
                result.success = True

        except Exception as e:
            error_msg = f"Scenario subgraph query failed: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def get_actor_influence(
        self,
        actor_id: str,
        influence_depth: int = 3
    ) -> GraphQueryResult:
        """
        Get influence chain of an actor through supply networks
        
        Args:
            actor_id: ID of the actor
            influence_depth: Depth of influence chain to follow
            
        Returns:
            GraphQueryResult with actor influence details
        """
        start_time = datetime.utcnow()
        result = GraphQueryResult(
            query_type="actor_influence",
            success=False,
            data=None
        )

        try:
            query = GraphQueries.actor_influence_chain(
                actor_id=actor_id,
                depth=influence_depth
            )

            async with self.client.driver.session() as session:
                records = await session.run(query)
                
                influence_chain = {
                    "actor_id": actor_id,
                    "chains": []
                }

                async for record in records:
                    chain = {
                        "chain_id": record.get("chain_id"),
                        "length": record.get("length"),
                        "target_id": record.get("target_id"),
                        "target_type": record.get("target_type"),
                        "influence_strength": record.get("influence_strength"),
                        "path": record.get("path", [])
                    }
                    influence_chain["chains"].append(chain)

                result.data = influence_chain
                result.success = True

        except Exception as e:
            error_msg = f"Actor influence query failed: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result

    async def get_reroute_alternatives(
        self,
        origin_id: str,
        destination_id: str,
        current_path_length: float,
        max_detour_percent: float = 20.0
    ) -> GraphQueryResult:
        """
        Get alternative routes for supply chain rerouting
        
        Args:
            origin_id: ID of origin infrastructure
            destination_id: ID of destination infrastructure
            current_path_length: Current path distance in km
            max_detour_percent: Maximum acceptable detour percentage
            
        Returns:
            GraphQueryResult with alternative routes
        """
        start_time = datetime.utcnow()
        result = GraphQueryResult(
            query_type="reroute_alternatives",
            success=False,
            data=None
        )

        try:
            max_distance = current_path_length * (1 + max_detour_percent / 100)
            query = GraphQueries.reroute_alternatives(
                origin_id=origin_id,
                destination_id=destination_id,
                max_distance=max_distance
            )

            async with self.client.driver.session() as session:
                records = await session.run(query)
                
                alternatives = []

                async for record in records:
                    alternative = {
                        "route_id": record.get("route_id"),
                        "path_length": record.get("path_length"),
                        "detour_percent": (
                            (record.get("path_length", 0) - current_path_length) / current_path_length * 100
                            if current_path_length > 0 else 0
                        ),
                        "nodes_in_path": record.get("nodes_in_path"),
                        "intermediate_hubs": record.get("intermediate_hubs", []),
                        "risk_score": record.get("risk_score", 0),
                        "availability": record.get("availability", 1.0)
                    }
                    alternatives.append(alternative)

                # Sort by detour percentage
                alternatives.sort(key=lambda x: x["detour_percent"])

                result.data = {
                    "origin_id": origin_id,
                    "destination_id": destination_id,
                    "current_distance": current_path_length,
                    "alternatives": alternatives[:5]  # Return top 5 alternatives
                }
                result.success = True

        except Exception as e:
            error_msg = f"Reroute alternatives query failed: {str(e)}"
            logger.error(error_msg)
            result.error = error_msg

        result.duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return result
