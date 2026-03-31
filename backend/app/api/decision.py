"""
Decision output and explanation endpoints for DecisionCore Intelligence GCC platform.

Provides decision generation, explainability, and recommendation capabilities
for supply chain risk scenarios.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.auth import api_key_auth
from app.api.models import (
    DecisionOutputResponse,
    ExplanationResponse,
    RecommendationResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory decision storage
decisions_db = {
    "DEC001": {
        "id": "DEC001",
        "scenario_id": "SCEN001",
        "decision_type": "supply_chain_mitigation",
        "decision": "Activate alternative suppliers in East Asia",
        "confidence": 0.87,
        "timestamp": datetime(2026, 3, 28, 14, 30),
        "reasoning": [
            "Primary supplier at 85% risk level",
            "Inventory buffer at 2.1 weeks",
            "Alternative suppliers available with 3-day lead time",
        ],
        "recommended_actions": [
            "Shift 30% volume to Thailand supplier",
            "Increase safety stock by 15%",
            "Establish backup logistics contract",
        ],
        "risk_reduction": 0.42,
        "implementation_timeline_days": 5,
    },
    "DEC002": {
        "id": "DEC002",
        "scenario_id": "SCEN002",
        "decision_type": "insurance_adjustment",
        "decision": "Increase maritime cargo coverage by 25%",
        "confidence": 0.79,
        "timestamp": datetime(2026, 3, 27, 10, 15),
        "reasoning": [
            "Geopolitical risks elevated in Strait of Hormuz",
            "Current coverage at 70% of exposed value",
            "Claim history shows 1.8x exposure ratio",
        ],
        "recommended_actions": [
            "Add $50M maritime cargo coverage",
            "Negotiate premium of 4.2% base rate",
            "Review policy terms for clarity",
        ],
        "risk_reduction": 0.28,
        "implementation_timeline_days": 14,
    },
    "DEC003": {
        "id": "DEC003",
        "scenario_id": "SCEN003",
        "decision_type": "demand_adjustment",
        "decision": "Reduce intake volume by 20% temporarily",
        "confidence": 0.72,
        "timestamp": datetime(2026, 3, 26, 16, 45),
        "reasoning": [
            "Transshipment hub disruption expected 4-6 weeks",
            "Current order book at 145% capacity",
            "Demand can be deferred without customer impact",
        ],
        "recommended_actions": [
            "Contact top 20 customers for schedule adjustments",
            "Halt new orders for 3-week period",
            "Establish priority queue for existing commitments",
        ],
        "risk_reduction": 0.55,
        "implementation_timeline_days": 2,
    },
}

# Explanation database
explanations_db = {
    "DEC001": {
        "decision_id": "DEC001",
        "factors": [
            {"factor": "Supplier Risk", "weight": 0.35, "value": 0.85},
            {"factor": "Inventory Position", "weight": 0.25, "value": 0.42},
            {"factor": "Alternative Availability", "weight": 0.20, "value": 0.88},
            {"factor": "Cost Impact", "weight": 0.15, "value": 0.30},
            {"factor": "Lead Time", "weight": 0.05, "value": 0.95},
        ],
        "key_constraints": ["Budget allocation", "Customer commitments"],
        "model_confidence": 0.87,
    },
    "DEC002": {
        "decision_id": "DEC002",
        "factors": [
            {"factor": "Geopolitical Risk", "weight": 0.40, "value": 0.78},
            {"factor": "Coverage Gap", "weight": 0.30, "value": 0.70},
            {"factor": "Premium Cost", "weight": 0.20, "value": 0.45},
            {"factor": "Claim History", "weight": 0.10, "value": 0.82},
        ],
        "key_constraints": ["Premium affordability", "Underwriting capacity"],
        "model_confidence": 0.79,
    },
    "DEC003": {
        "decision_id": "DEC003",
        "factors": [
            {"factor": "Hub Disruption Risk", "weight": 0.40, "value": 0.85},
            {"factor": "Capacity Utilization", "weight": 0.25, "value": 0.70},
            {"factor": "Customer Flexibility", "weight": 0.20, "value": 0.65},
            {"factor": "Demand Elasticity", "weight": 0.15, "value": 0.55},
        ],
        "key_constraints": ["Customer satisfaction", "Revenue impact"],
        "model_confidence": 0.72,
    },
}

# Recommendation database
recommendations_db = {
    "DEC001": [
        {
            "rank": 1,
            "title": "Diversify supplier base",
            "description": "Reduce single-supplier dependency from 60% to 40%",
            "priority": "high",
            "timeline_days": 30,
            "estimated_cost_usd": 500000,
        },
        {
            "rank": 2,
            "title": "Increase inventory buffer",
            "description": "Build safety stock to 4-week coverage",
            "priority": "high",
            "timeline_days": 60,
            "estimated_cost_usd": 2000000,
        },
        {
            "rank": 3,
            "title": "Establish redundant logistics",
            "description": "Contract with secondary 3PL provider",
            "priority": "medium",
            "timeline_days": 45,
            "estimated_cost_usd": 300000,
        },
    ],
    "DEC002": [
        {
            "rank": 1,
            "title": "Expand maritime coverage",
            "description": "Add $50M cargo coverage for high-value routes",
            "priority": "high",
            "timeline_days": 14,
            "estimated_cost_usd": 2100000,
        },
        {
            "rank": 2,
            "title": "Review coverage terms",
            "description": "Clarify policy exclusions and claim procedures",
            "priority": "medium",
            "timeline_days": 7,
            "estimated_cost_usd": 0,
        },
        {
            "rank": 3,
            "title": "Negotiate better rates",
            "description": "Leverage multi-year commitment for 3.8% rate",
            "priority": "medium",
            "timeline_days": 21,
            "estimated_cost_usd": -100000,
        },
    ],
    "DEC003": [
        {
            "rank": 1,
            "title": "Pause new orders",
            "description": "Halt intake for 3-week period to reduce pressure",
            "priority": "critical",
            "timeline_days": 1,
            "estimated_cost_usd": -500000,
        },
        {
            "rank": 2,
            "title": "Communicate with customers",
            "description": "Notify top 20 accounts of schedule adjustments",
            "priority": "high",
            "timeline_days": 2,
            "estimated_cost_usd": 0,
        },
        {
            "rank": 3,
            "title": "Optimize fulfillment",
            "description": "Prioritize high-margin orders during constraint period",
            "priority": "medium",
            "timeline_days": 3,
            "estimated_cost_usd": 100000,
        },
    ],
}


@router.post(
    "/decisions/output",
    response_model=DecisionOutputResponse,
    tags=["Decisions"],
    summary="Generate decision output",
)
async def generate_decision(
    api_key: str = Depends(api_key_auth),
    scenario_id: str = Query(..., description="Scenario ID to generate decision for"),
    decision_context: str = Query(
        "supply_chain_risk", description="Context for decision generation"
    ),
) -> DecisionOutputResponse:
    """
    Generate decision output for a given scenario.

    Creates decision recommendations based on scenario analysis and risk factors.

    Args:
        api_key: API key for authentication (injected via header)
        scenario_id: ID of the scenario to generate decision for
        decision_context: Context or domain for decision

    Returns:
        DecisionOutputResponse with generated decision

    Raises:
        HTTPException: If API authentication fails
    """
    try:
        # Simulate decision generation
        decision_options = list(decisions_db.values())

        # Select decision based on scenario
        selected_decision = decision_options[hash(scenario_id) % len(decision_options)]

        logger.info(f"Generated decision for scenario {scenario_id} with context {decision_context}")

        return DecisionOutputResponse(
            decision_id=selected_decision["id"],
            scenario_id=scenario_id,
            decision_type=selected_decision["decision_type"],
            decision=selected_decision["decision"],
            confidence=selected_decision["confidence"],
            timestamp=selected_decision["timestamp"],
            reasoning=selected_decision["reasoning"],
            recommended_actions=selected_decision["recommended_actions"],
            risk_reduction_potential=selected_decision["risk_reduction"],
            implementation_timeline_days=selected_decision["implementation_timeline_days"],
        )
    except Exception as e:
        logger.error(f"Error generating decision: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate decision")


@router.get(
    "/decisions/latest",
    response_model=DecisionOutputResponse,
    tags=["Decisions"],
    summary="Get latest decision",
)
async def get_latest_decision(
    api_key: str = Depends(api_key_auth),
    scenario_id: Optional[str] = Query(None, description="Filter by scenario ID"),
) -> DecisionOutputResponse:
    """
    Retrieve the most recent decision output.

    Args:
        api_key: API key for authentication (injected via header)
        scenario_id: Optional filter by scenario ID

    Returns:
        DecisionOutputResponse with latest decision

    Raises:
        HTTPException: If no decisions found
    """
    try:
        decisions = list(decisions_db.values())

        if scenario_id:
            decisions = [d for d in decisions if d["scenario_id"] == scenario_id]

        if not decisions:
            logger.warning(f"No decisions found for scenario {scenario_id}")
            raise HTTPException(status_code=404, detail="No decisions found")

        # Get most recent
        latest = max(decisions, key=lambda d: d["timestamp"])

        logger.info(f"Retrieved latest decision {latest['id']}")

        return DecisionOutputResponse(
            decision_id=latest["id"],
            scenario_id=latest["scenario_id"],
            decision_type=latest["decision_type"],
            decision=latest["decision"],
            confidence=latest["confidence"],
            timestamp=latest["timestamp"],
            reasoning=latest["reasoning"],
            recommended_actions=latest["recommended_actions"],
            risk_reduction_potential=latest["risk_reduction"],
            implementation_timeline_days=latest["implementation_timeline_days"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving latest decision: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve decision")


@router.post(
    "/decisions/explain",
    response_model=ExplanationResponse,
    tags=["Decisions"],
    summary="Explain decision reasoning",
)
async def explain_decision(
    api_key: str = Depends(api_key_auth),
    decision_id: str = Query(..., description="Decision ID to explain"),
) -> ExplanationResponse:
    """
    Provide detailed explanation of decision reasoning.

    Breaks down the factors, weights, and constraints that influenced the decision.

    Args:
        api_key: API key for authentication (injected via header)
        decision_id: ID of the decision to explain

    Returns:
        ExplanationResponse with detailed reasoning

    Raises:
        HTTPException: If decision not found
    """
    try:
        if decision_id not in explanations_db:
            logger.warning(f"Explanation not found for decision {decision_id}")
            raise HTTPException(status_code=404, detail="Decision explanation not found")

        explanation = explanations_db[decision_id]
        decision = decisions_db[decision_id]

        logger.info(f"Generated explanation for decision {decision_id}")

        return ExplanationResponse(
            decision_id=decision_id,
            summary=decision["decision"],
            factors=explanation["factors"],
            key_constraints=explanation["key_constraints"],
            model_confidence=explanation["model_confidence"],
            supporting_evidence=decision["reasoning"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining decision: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to explain decision")


@router.post(
    "/decisions/recommend",
    response_model=RecommendationResponse,
    tags=["Decisions"],
    summary="Get decision recommendations",
)
async def get_recommendations(
    api_key: str = Depends(api_key_auth),
    decision_id: str = Query(..., description="Decision ID to get recommendations for"),
    include_costs: bool = Query(True, description="Include cost estimates"),
) -> RecommendationResponse:
    """
    Get prioritized recommendations for implementing a decision.

    Provides ranked action items with timelines, costs, and priorities.

    Args:
        api_key: API key for authentication (injected via header)
        decision_id: ID of the decision to get recommendations for
        include_costs: Whether to include cost estimates

    Returns:
        RecommendationResponse with ranked recommendations

    Raises:
        HTTPException: If decision not found
    """
    try:
        if decision_id not in recommendations_db:
            logger.warning(f"Recommendations not found for decision {decision_id}")
            raise HTTPException(status_code=404, detail="Decision recommendations not found")

        decision = decisions_db[decision_id]
        recs = recommendations_db[decision_id]

        # Filter cost if not requested
        recommendations = []
        for rec in recs:
            rec_item = {
                "rank": rec["rank"],
                "title": rec["title"],
                "description": rec["description"],
                "priority": rec["priority"],
                "timeline_days": rec["timeline_days"],
            }
            if include_costs:
                rec_item["estimated_cost_usd"] = rec["estimated_cost_usd"]
            recommendations.append(rec_item)

        logger.info(f"Generated {len(recommendations)} recommendations for decision {decision_id}")

        return RecommendationResponse(
            decision_id=decision_id,
            decision_summary=decision["decision"],
            recommendations=recommendations,
            total_timeline_days=max(r["timeline_days"] for r in recommendations),
            total_estimated_cost_usd=(
                sum(r["estimated_cost_usd"] for r in recs) if include_costs else None
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")
