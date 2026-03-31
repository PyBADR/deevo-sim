"""
Insurance Intelligence Engine

Orchestrates all insurance intelligence components and provides unified assessment
interface with bilingual (EN/AR) narrative generation for policy and portfolio analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import numpy as np

from .gcc_insurance_config import GCC_INSURANCE_CONFIG, GCCInsuranceConfig
from .portfolio_exposure import (
    compute_portfolio_exposure,
    PolicyExposure,
    PortfolioExposureResult
)
from .claims_surge import compute_claims_surge_potential as compute_claims_surge, ClaimsSurgeResult
from .claims_uplift import compute_expected_claims_uplift as compute_claims_uplift, ClaimsUpliftResult
from .underwriting_watch import compute_underwriting_restriction as compute_underwriting_watch, UnderwritingResult
from .severity_projection import project_severity, SeverityProjection


class AssessmentLevel(str, Enum):
    """Assessment severity level."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PolicyAssessment:
    """Single policy insurance assessment result."""
    policy_id: str
    portfolio_exposure_score: float
    claims_surge_score: float
    claims_uplift: ClaimsUpliftResult
    underwriting_classification: str
    overall_risk_score: float
    risk_level: AssessmentLevel
    components: Dict[str, float] = field(default_factory=dict)
    narrative_en: str = ""
    narrative_ar: str = ""


@dataclass
class PortfolioAssessment:
    """Full portfolio insurance assessment result."""
    portfolio_size: int
    average_exposure: float
    concentration_index: float
    aggregate_surge_exposure: float
    aggregate_claims_uplift: float
    portfolio_risk_score: float
    risk_level: AssessmentLevel
    underwriting_summary: Dict[str, int] = field(default_factory=dict)
    exposure_concentration: PortfolioExposureResult = None
    policy_assessments: List[PolicyAssessment] = field(default_factory=list)
    narrative_en: str = ""
    narrative_ar: str = ""


@dataclass
class ScenarioImpact:
    """Impact assessment for hypothetical scenario."""
    scenario_name: str
    base_portfolio_score: float
    stressed_portfolio_score: float
    score_delta: float
    percentage_impact: float
    affected_policies: int
    most_vulnerable_policies: List[Tuple[str, float]] = field(default_factory=list)
    narrative_en: str = ""
    narrative_ar: str = ""


class InsuranceIntelligenceEngine:
    """
    Main orchestration engine for insurance intelligence assessments.
    
    Coordinates all five intelligence dimensions (portfolio exposure, claims surge,
    claims uplift, underwriting restrictions, severity projection) and produces
    unified assessments with bilingual narratives.
    """

    def __init__(self, config: Optional[GCCInsuranceConfig] = None):
        """
        Initialize insurance intelligence engine.
        
        Args:
            config: GCCInsuranceConfig instance (uses global default if None)
        """
        self.config = config or GCC_INSURANCE_CONFIG
        self.config.validate()

    def assess_policy(
        self,
        policy_id: str,
        tiv: float,
        base_claims: float,
        region: str,
        route_dependency: float,
        region_risk: float,
        claims_elasticity: float,
        risk_score: float,
        disruption_score: float,
        policy_sensitivity: float,
        system_stress: float,
        uncertainty: float,
        logistics_stress: float
    ) -> PolicyAssessment:
        """
        Assess individual policy across all insurance dimensions.
        
        Args:
            policy_id: Unique policy identifier
            tiv: Total Insured Value (normalized 0-1)
            base_claims: Expected base claims amount
            region: GCC country code
            route_dependency: Route dependency risk (0-1)
            region_risk: Regional risk factor (0-1)
            claims_elasticity: Claims elasticity coefficient (0-1)
            risk_score: Current risk assessment (0-1)
            disruption_score: Disruption impact score (0-1)
            policy_sensitivity: Policy sensitivity to external shocks (0-1)
            system_stress: System-wide stress level (0-1)
            uncertainty: Intelligence uncertainty level (0-1)
            logistics_stress: Logistics-specific stress (0-1)
        
        Returns:
            PolicyAssessment with scores across all dimensions and narratives
        
        Raises:
            ValueError: If inputs fail validation
        """
        # Validate region
        if region not in self.config.regional_multipliers:
            raise ValueError(
                f"region must be valid GCC country. "
                f"Valid: {list(self.config.regional_multipliers.keys())}"
            )
        
        # Portfolio exposure assessment
        policy_exposure = PolicyExposure(
            policy_id=policy_id,
            tiv=tiv,
            route_dependency=route_dependency,
            region_risk=region_risk,
            claims_elasticity=claims_elasticity
        )
        exposure_result = compute_portfolio_exposure([policy_exposure], self.config)
        exposure_score = exposure_result.per_policy_scores.get(policy_id, 0.0)
        
        # Claims surge assessment
        surge_result = compute_claims_surge(
            risk_score=risk_score,
            disruption_score=disruption_score,
            exposure=exposure_score,
            policy_sensitivity=policy_sensitivity,
            config=self.config
        )
        
        # Claims uplift assessment
        uplift_result = compute_claims_uplift(
            base_claims=base_claims,
            surge_score=surge_result.surge_score,
            system_stress=system_stress,
            uncertainty=uncertainty,
            config=self.config
        )
        
        # Underwriting watch assessment
        underwriting_result = compute_underwriting_watch(
            region_risk=region_risk,
            logistics_stress=logistics_stress,
            claims_surge=surge_result.surge_score,
            uncertainty=uncertainty,
            config=self.config
        )
        
        # Calculate overall policy risk score
        # Weighted combination of all dimension scores (normalized to 0-1)
        overall_risk_score = np.clip(
            0.25 * exposure_score +
            0.25 * surge_result.surge_score +
            0.20 * (uplift_result.uplift_percentage / 100.0) +
            0.30 * (underwriting_result.score / 100.0),
            0.0,
            1.0
        )
        
        # Determine risk level
        if overall_risk_score < 0.25:
            risk_level = AssessmentLevel.LOW
        elif overall_risk_score < 0.50:
            risk_level = AssessmentLevel.MODERATE
        elif overall_risk_score < 0.75:
            risk_level = AssessmentLevel.HIGH
        else:
            risk_level = AssessmentLevel.CRITICAL
        
        # Build components dictionary
        components = {
            "exposure_score": exposure_score,
            "surge_score": surge_result.surge_score,
            "uplift_percentage": uplift_result.uplift_percentage,
            "uplift_amount": uplift_result.uplift_amount,
            "underwriting_score": underwriting_result.score,
            "underwriting_classification": underwriting_result.classification.value
        }
        
        # Generate bilingual narratives
        narrative_en = self._generate_policy_narrative_en(
            policy_id, overall_risk_score, risk_level, surge_result,
            underwriting_result, uplift_result, region
        )
        narrative_ar = self._generate_policy_narrative_ar(
            policy_id, overall_risk_score, risk_level, surge_result,
            underwriting_result, uplift_result, region
        )
        
        return PolicyAssessment(
            policy_id=policy_id,
            portfolio_exposure_score=exposure_score,
            claims_surge_score=surge_result.surge_score,
            claims_uplift=uplift_result,
            underwriting_classification=underwriting_result.classification.value,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            components=components,
            narrative_en=narrative_en,
            narrative_ar=narrative_ar
        )

    def assess_portfolio(
        self,
        policies: List[Dict]
    ) -> PortfolioAssessment:
        """
        Assess entire insurance portfolio.
        
        Args:
            policies: List of policy dictionaries with assessment parameters
        
        Returns:
            PortfolioAssessment with aggregate metrics and individual policy assessments
        """
        policy_assessments = []
        
        for policy_dict in policies:
            assessment = self.assess_policy(**policy_dict)
            policy_assessments.append(assessment)
        
        # Calculate portfolio aggregates
        portfolio_size = len(policy_assessments)
        
        if portfolio_size == 0:
            return PortfolioAssessment(
                portfolio_size=0,
                average_exposure=0.0,
                concentration_index=0.0,
                aggregate_surge_exposure=0.0,
                aggregate_claims_uplift=0.0,
                portfolio_risk_score=0.0,
                risk_level=AssessmentLevel.LOW
            )
        
        # Aggregate metrics
        exposure_scores = [a.portfolio_exposure_score for a in policy_assessments]
        surge_scores = [a.claims_surge_score for a in policy_assessments]
        uplift_amounts = [a.claims_uplift.uplift_amount for a in policy_assessments]
        overall_scores = [a.overall_risk_score for a in policy_assessments]
        
        average_exposure = np.mean(exposure_scores)
        aggregate_surge = np.sum(surge_scores)
        aggregate_uplift = np.sum(uplift_amounts)
        portfolio_risk_score = np.mean(overall_scores)
        
        # Determine portfolio concentration from HHI equivalent
        # (simplified as std dev of exposure scores)
        concentration_index = float(np.std(exposure_scores)) if len(exposure_scores) > 1 else 0.0
        
        # Determine portfolio risk level
        if portfolio_risk_score < 0.25:
            risk_level = AssessmentLevel.LOW
        elif portfolio_risk_score < 0.50:
            risk_level = AssessmentLevel.MODERATE
        elif portfolio_risk_score < 0.75:
            risk_level = AssessmentLevel.HIGH
        else:
            risk_level = AssessmentLevel.CRITICAL
        
        # Count underwriting classifications
        underwriting_summary = {}
        for assessment in policy_assessments:
            classification = assessment.underwriting_classification
            underwriting_summary[classification] = underwriting_summary.get(classification, 0) + 1
        
        # Generate bilingual narratives
        narrative_en = self._generate_portfolio_narrative_en(
            portfolio_size, average_exposure, concentration_index,
            aggregate_surge, aggregate_uplift, portfolio_risk_score,
            underwriting_summary, risk_level
        )
        narrative_ar = self._generate_portfolio_narrative_ar(
            portfolio_size, average_exposure, concentration_index,
            aggregate_surge, aggregate_uplift, portfolio_risk_score,
            underwriting_summary, risk_level
        )
        
        return PortfolioAssessment(
            portfolio_size=portfolio_size,
            average_exposure=average_exposure,
            concentration_index=concentration_index,
            aggregate_surge_exposure=aggregate_surge,
            aggregate_claims_uplift=aggregate_uplift,
            portfolio_risk_score=portfolio_risk_score,
            risk_level=risk_level,
            underwriting_summary=underwriting_summary,
            policy_assessments=policy_assessments,
            narrative_en=narrative_en,
            narrative_ar=narrative_ar
        )

    def scenario_impact(
        self,
        scenario_name: str,
        base_portfolio: PortfolioAssessment,
        stress_factors: Dict[str, float]
    ) -> ScenarioImpact:
        """
        Assess portfolio impact under hypothetical stress scenario.
        
        Args:
            scenario_name: Name of scenario (e.g., "High Regional Unrest")
            base_portfolio: Baseline portfolio assessment
            stress_factors: Dictionary of stress parameter multipliers
                          (e.g., {"system_stress": 1.5, "disruption_score": 1.3})
        
        Returns:
            ScenarioImpact with score changes and affected policy analysis
        """
        stressed_policies = []
        vulnerable_changes = []
        
        for policy_assessment in base_portfolio.policy_assessments:
            # Apply stress factors to create stressed scenario
            # Reconstruct policy parameters with stress applied
            stressed_params = {}
            
            # This is a simplified stress application
            # In production, would need full parameter reconstruction
            base_score = policy_assessment.overall_risk_score
            
            # Apply stress multiplier
            stress_multiplier = stress_factors.get("system_stress", 1.0)
            stressed_score = min(1.0, base_score * stress_multiplier)
            
            vulnerable_changes.append((
                policy_assessment.policy_id,
                stressed_score - base_score
            ))
            
            stressed_policies.append(stressed_score)
        
        # Calculate aggregate stressed portfolio
        if stressed_policies:
            stressed_portfolio_score = np.mean(stressed_policies)
            affected_count = sum(1 for s in stressed_policies if s > 0.5)
        else:
            stressed_portfolio_score = 0.0
            affected_count = 0
        
        # Sort by impact magnitude
        vulnerable_changes.sort(key=lambda x: abs(x[1]), reverse=True)
        most_vulnerable = vulnerable_changes[:5]  # Top 5 affected
        
        # Calculate deltas
        score_delta = stressed_portfolio_score - base_portfolio.portfolio_risk_score
        percentage_impact = (score_delta / max(base_portfolio.portfolio_risk_score, 0.01)) * 100
        
        # Generate narratives
        narrative_en = self._generate_scenario_narrative_en(
            scenario_name, score_delta, percentage_impact, affected_count
        )
        narrative_ar = self._generate_scenario_narrative_ar(
            scenario_name, score_delta, percentage_impact, affected_count
        )
        
        return ScenarioImpact(
            scenario_name=scenario_name,
            base_portfolio_score=base_portfolio.portfolio_risk_score,
            stressed_portfolio_score=stressed_portfolio_score,
            score_delta=score_delta,
            percentage_impact=percentage_impact,
            affected_policies=affected_count,
            most_vulnerable_policies=most_vulnerable,
            narrative_en=narrative_en,
            narrative_ar=narrative_ar
        )

    # Narrative generation methods
    def _generate_policy_narrative_en(
        self, policy_id: str, risk_score: float, risk_level: AssessmentLevel,
        surge_result: ClaimsSurgeResult, underwriting: UnderwritingResult,
        uplift: ClaimsUpliftResult, region: str
    ) -> str:
        """Generate English narrative for policy assessment."""
        surge_desc = {
            "normal": "normal expected levels",
            "elevated": "elevated levels",
            "critical": "critical levels",
            "extreme": "extreme levels"
        }
        severity = surge_result.severity_level.value
        
        return (
            f"Policy {policy_id} in {region} assessed at {risk_level.value.upper()} risk "
            f"(score: {risk_score:.2f}). Claims surge potential at {surge_desc.get(severity, 'unknown')}. "
            f"Underwriting status: {underwriting.classification.value}. "
            f"Projected claims uplift: {uplift.uplift_percentage:.1f}%."
        )

    def _generate_policy_narrative_ar(
        self, policy_id: str, risk_score: float, risk_level: AssessmentLevel,
        surge_result: ClaimsSurgeResult, underwriting: UnderwritingResult,
        uplift: ClaimsUpliftResult, region: str
    ) -> str:
        """Generate Arabic narrative for policy assessment."""
        return (
            f"تم تقييم السياسة {policy_id} في {region} بمستوى مخاطر "
            f"{risk_level.value.upper()} (النقاط: {risk_score:.2f}). "
            f"حالة الاكتتاب: {underwriting.classification.value}. "
            f"الارتفاع المتوقع في الطلبات: {uplift.uplift_percentage:.1f}%."
        )

    def _generate_portfolio_narrative_en(
        self, size: int, avg_exposure: float, concentration: float,
        surge: float, uplift: float, risk_score: float,
        underwriting_summary: Dict[str, int], risk_level: AssessmentLevel
    ) -> str:
        """Generate English narrative for portfolio assessment."""
        return (
            f"Portfolio of {size} policies assessed at {risk_level.value.upper()} risk. "
            f"Average exposure: {avg_exposure:.2f}, concentration index: {concentration:.2f}. "
            f"Aggregate claims surge: {surge:.2f}, projected uplift: ${uplift:,.0f}. "
            f"Underwriting distribution: {underwriting_summary}."
        )

    def _generate_portfolio_narrative_ar(
        self, size: int, avg_exposure: float, concentration: float,
        surge: float, uplift: float, risk_score: float,
        underwriting_summary: Dict[str, int], risk_level: AssessmentLevel
    ) -> str:
        """Generate Arabic narrative for portfolio assessment."""
        return (
            f"تم تقييم محفظة {size} سياسة بمستوى مخاطر {risk_level.value.upper()}. "
            f"التعرض المتوسط: {avg_exposure:.2f}، معامل التركيز: {concentration:.2f}. "
            f"ارتفاع الطلبات الإجمالي: {surge:.2f}."
        )

    def _generate_scenario_narrative_en(
        self, scenario: str, delta: float, percentage: float, affected: int
    ) -> str:
        """Generate English narrative for scenario impact."""
        direction = "increase" if delta > 0 else "decrease"
        return (
            f"Under scenario '{scenario}', portfolio risk would {direction} by {abs(delta):.2f} "
            f"({abs(percentage):.1f}%), affecting {affected} policies."
        )

    def _generate_scenario_narrative_ar(
        self, scenario: str, delta: float, percentage: float, affected: int
    ) -> str:
        """Generate Arabic narrative for scenario impact."""
        return (
            f"تحت سيناريو '{scenario}'، ستتأثر {affected} سياسة بتغيير مخاطر يبلغ "
            f"{abs(percentage):.1f}%."
        )
