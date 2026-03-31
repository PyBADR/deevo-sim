"""
Decision Output Generator for structured scenario impact assessment.

Produces DecisionOutput answering 5 mandatory questions with bilingual EN/AR support,
economic and insurance impact analysis, and actionable recommendations.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math

from app.scenarios.simulator import ScenarioSimulationResult
from app.intelligence.insurance.insurance_engine import InsuranceIntelligenceEngine
from app.intelligence.physics.system_stress import SystemStressResult


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactSeverity(Enum):
    """Severity classifications for impacts."""

    CATASTROPHIC = "catastrophic"  # >80% impact
    SEVERE = "severe"  # 60-80%
    MAJOR = "major"  # 40-60%
    MODERATE = "moderate"  # 20-40%
    MINOR = "minor"  # <20%


@dataclass
class BilingualText:
    """Bilingual text container for EN/AR content."""

    en: str = ""
    ar: str = ""

    def __init__(self, en: str = "", ar: str = ""):
        self.en = en
        self.ar = ar


@dataclass
class EconomicImpact:
    """Economic impact quantification."""

    estimated_gdp_impact_usd_millions: float = 0.0
    trade_volume_affected_percent: float = 0.0
    employment_impact_thousands: float = 0.0
    commodity_price_inflation_percent: float = 0.0
    export_revenue_loss_percent: float = 0.0
    import_cost_increase_percent: float = 0.0
    recovery_duration_days: int = 0
    economic_scenario: str = ""  # optimistic, baseline, pessimistic


@dataclass
class InsuranceImpact:
    """Insurance portfolio impact assessment."""

    policies_affected_count: int = 0
    estimated_claims_surge_percent: float = 0.0
    estimated_claims_uplift_usd_millions: float = 0.0
    underwriting_restrictions_implemented: bool = False
    premium_adjustment_percent: float = 0.0
    coverage_capacity_reduction_percent: float = 0.0
    portfolio_stress_level: str = ""  # nominal, elevated, high, critical


@dataclass
class Recommendation:
    """Individual recommendation with justification."""

    title: BilingualText = field(default_factory=BilingualText)
    description: BilingualText = field(default_factory=BilingualText)
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    timeline: BilingualText = field(default_factory=BilingualText)  # immediate, short-term, etc.
    responsible_party: BilingualText = field(
        default_factory=BilingualText
    )  # who should execute
    estimated_cost_usd_millions: Optional[float] = None
    expected_impact: BilingualText = field(default_factory=BilingualText)


@dataclass
class DecisionOutput:
    """
    Structured decision output answering 5 mandatory questions.

    Bilingual (EN/AR), includes economic/insurance impact, and actionable recommendations.
    """

    scenario_id: str = ""
    scenario_name: BilingualText = field(default_factory=BilingualText)

    # Question 1: What happened?
    what_happened: BilingualText = field(default_factory=BilingualText)

    # Question 2: What is the impact?
    what_is_impact: BilingualText = field(default_factory=BilingualText)
    impact_severity: ImpactSeverity = ImpactSeverity.MODERATE

    # Question 3: What is affected?
    what_is_affected: BilingualText = field(default_factory=BilingualText)
    affected_regions: List[str] = field(default_factory=list)
    affected_sectors: List[str] = field(default_factory=list)
    affected_populations_millions: float = 0.0

    # Question 4: How big is the risk?
    how_big_is_risk: BilingualText = field(default_factory=BilingualText)
    risk_score_0_100: float = 0.0
    risk_level: str = ""  # nominal, elevated, high, critical
    cascade_probability_percent: float = 0.0

    # Question 5: What to do?
    what_to_do: List[Recommendation] = field(default_factory=list)

    # Additional details
    economic_impact: EconomicImpact = field(default_factory=EconomicImpact)
    insurance_impact: InsuranceImpact = field(default_factory=InsuranceImpact)

    # Metadata
    created_at: str = ""
    model_version: str = "1.0"
    confidence_level: float = 0.85


class DecisionOutputGenerator:
    """
    Generates structured DecisionOutput from simulation results and intelligence layers.

    Orchestrates analysis of simulation outcomes, economic impacts, insurance effects,
    and produces bilingual recommendations.
    """

    def __init__(
        self,
        insurance_engine: Optional[InsuranceIntelligenceEngine] = None,
    ):
        """
        Initialize generator.

        Args:
            insurance_engine: InsuranceIntelligenceEngine for portfolio analysis
        """
        self.insurance_engine = insurance_engine

    def generate(
        self,
        scenario_id: str,
        scenario_name_en: str,
        scenario_name_ar: str,
        simulation_result: ScenarioSimulationResult,
        affected_countries: List[str],
        affected_regions: List[str],
        scenario_template_disruption_type: str = "disruption",
        scenario_template_severity: float = 0.5,
    ) -> DecisionOutput:
        """
        Generate complete DecisionOutput from simulation results.

        Args:
            scenario_id: Unique scenario identifier
            scenario_name_en: English scenario name
            scenario_name_ar: Arabic scenario name
            simulation_result: ScenarioSimulationResult from simulator
            affected_countries: List of affected country codes
            affected_regions: List of affected region names
            scenario_template_disruption_type: Type of disruption (closure, blockade, etc.)
            scenario_template_severity: [0,1] scenario severity

        Returns:
            Complete DecisionOutput structure
        """
        output = DecisionOutput(
            scenario_id=scenario_id,
            scenario_name=BilingualText(en=scenario_name_en, ar=scenario_name_ar),
            created_at=self._get_timestamp(),
        )

        # Question 1: What happened?
        output.what_happened = self._answer_what_happened(
            scenario_template_disruption_type,
            scenario_template_severity,
            affected_countries,
        )

        # Question 2: What is the impact?
        output.what_is_impact, output.impact_severity = self._answer_what_is_impact(
            simulation_result, scenario_template_severity
        )

        # Question 3: What is affected?
        (
            output.what_is_affected,
            output.affected_sectors,
        ) = self._answer_what_is_affected(
            simulation_result, affected_regions, scenario_template_disruption_type
        )
        output.affected_regions = affected_regions
        output.affected_populations_millions = self._estimate_affected_population(
            affected_countries, affected_regions
        )

        # Question 4: How big is the risk?
        (
            output.how_big_is_risk,
            output.risk_score_0_100,
            output.risk_level,
        ) = self._answer_how_big_is_risk(simulation_result)
        output.cascade_probability_percent = self._estimate_cascade_probability(
            simulation_result
        )

        # Economic impact analysis
        output.economic_impact = self._compute_economic_impact(
            simulation_result,
            scenario_template_severity,
            affected_countries,
            scenario_template_disruption_type,
        )

        # Insurance impact analysis
        output.insurance_impact = self._compute_insurance_impact(
            simulation_result,
            scenario_template_severity,
        )

        # Question 5: What to do?
        output.what_to_do = self._generate_recommendations(
            simulation_result,
            scenario_template_disruption_type,
            output.risk_level,
            output.economic_impact,
            output.insurance_impact,
        )

        return output

    def _answer_what_happened(
        self,
        disruption_type: str,
        severity: float,
        countries: List[str],
    ) -> BilingualText:
        """Generate answer to: What happened?"""
        severity_desc = (
            "major"
            if severity > 0.7
            else "significant" if severity > 0.4 else "moderate"
        )
        country_str = ", ".join(countries) if countries else "GCC region"

        en_text = (
            f"A {severity_desc} {disruption_type} event has occurred in {country_str}. "
            f"The disruption has triggered cascading effects across critical "
            f"infrastructure networks, affecting ports, airports, and supply routes."
        )

        ar_text = (
            f"حدث حدث {disruption_type} {severity_desc} في {country_str}. "
            f"أدى الاضطراب إلى آثار متسلسلة عبر شبكات البنية التحتية الحرجة، "
            f"مما أثر على الموانئ والمطارات ومسارات الإمداد."
        )

        return BilingualText(en=en_text, ar=ar_text)

    def _answer_what_is_impact(
        self, result: ScenarioSimulationResult, severity: float
    ) -> Tuple[BilingualText, ImpactSeverity]:
        """Generate answer to: What is the impact?"""
        # Compute aggregate impact metric
        max_risk = max(result.final_risk_scores.values())
        system_stress = result.system_stress_final or 0.0
        impact_score = (max_risk * 0.6 + system_stress * 0.4) * 100

        # Classify severity
        if impact_score > 80:
            severity_enum = ImpactSeverity.CATASTROPHIC
            severity_word = "catastrophic"
        elif impact_score > 60:
            severity_enum = ImpactSeverity.SEVERE
            severity_word = "severe"
        elif impact_score > 40:
            severity_enum = ImpactSeverity.MAJOR
            severity_word = "major"
        elif impact_score > 20:
            severity_enum = ImpactSeverity.MODERATE
            severity_word = "moderate"
        else:
            severity_enum = ImpactSeverity.MINOR
            severity_word = "minor"

        affected_count = len(result.critical_nodes_post_shock)
        total_nodes = len(result.final_risk_scores)

        en_text = (
            f"The scenario results in {severity_word} disruption impact "
            f"affecting {affected_count} of {total_nodes} critical nodes. "
            f"System stress level reached {system_stress:.1%}. "
            f"Trade flows through affected corridors are significantly impeded, "
            f"with cascading effects expected across dependent supply chains."
        )

        ar_text = (
            f"يؤدي السيناريو إلى تأثير اضطراب {severity_word} يؤثر على "
            f"{affected_count} من {total_nodes} عقدة حرجة. "
            f"وصل مستوى إجهاد النظام إلى {system_stress:.1%}. "
            f"يتم عرقلة تدفقات التجارة عبر الممرات المتأثرة بشكل كبير، "
            f"مع آثار متسلسلة متوقعة عبر سلاسل الإمداد المعتمدة."
        )

        return BilingualText(en=en_text, ar=ar_text), severity_enum

    def _answer_what_is_affected(
        self,
        result: ScenarioSimulationResult,
        regions: List[str],
        disruption_type: str,
    ) -> Tuple[BilingualText, List[str]]:
        """Generate answer to: What is affected?"""
        # Infer sectors from disruption type
        sectors_map = {
            "port_closure": ["Maritime Trade", "Container Shipping", "Refining"],
            "airspace_closure": ["Air Transport", "E-commerce", "Perishables"],
            "pipeline_disruption": ["Oil & Gas", "Energy", "Petrochemicals"],
            "conflict": ["All Sectors", "Maritime", "Aviation", "Land Routes"],
        }
        sectors = sectors_map.get(
            disruption_type, ["Maritime Trade", "Aviation", "Energy"]
        )

        region_str = ", ".join(regions) if regions else "multiple regions"
        sectors_str = ", ".join(sectors)

        en_text = (
            f"Directly affected areas: {region_str}. "
            f"Primary economic sectors impacted: {sectors_str}. "
            f"Secondary effects extend to: global supply chains, investment portfolios, "
            f"energy markets, and insurance markets. "
            f"{len(result.critical_nodes_post_shock)} critical infrastructure nodes "
            f"are in elevated risk state."
        )

        ar_text = (
            f"المناطق المتأثرة مباشرة: {region_str}. "
            f"القطاعات الاقتصادية الأساسية المتضررة: {sectors_str}. "
            f"تمتد التأثيرات الثانوية إلى سلاسل الإمداد العالمية وملفات الاستثمار "
            f"والأسواق المالية وأسواق التأمين. "
            f"عدد {len(result.critical_nodes_post_shock)} من عقد البنية التحتية الحرجة "
            f"في حالة خطر مرتفعة."
        )

        return BilingualText(en=en_text, ar=ar_text), sectors

    def _answer_how_big_is_risk(
        self, result: ScenarioSimulationResult
    ) -> Tuple[BilingualText, float, str]:
        """Generate answer to: How big is the risk?"""
        # Compute risk score 0-100
        max_risk = max(result.final_risk_scores.values())
        system_stress = result.system_stress_final or 0.0
        risk_score = (max_risk * 0.7 + system_stress * 0.3) * 100

        # Classify risk level
        if risk_score > 75:
            risk_level = "critical"
            risk_word = "Critical"
        elif risk_score > 50:
            risk_level = "high"
            risk_word = "High"
        elif risk_score > 25:
            risk_level = "elevated"
            risk_word = "Elevated"
        else:
            risk_level = "nominal"
            risk_word = "Nominal"

        recovery_days = result.recovery_time_estimate_hours / 24

        en_text = (
            f"{risk_word} Risk Level. Overall risk score: {risk_score:.0f}/100. "
            f"Maximum node risk: {max_risk:.1%}. "
            f"Estimated recovery time: {recovery_days:.0f} days. "
            f"Probability of cascading escalation: medium to high. "
            f"Impact duration expected: {result.recovery_time_estimate_hours/24:.0f}-{result.recovery_time_estimate_hours/24*1.5:.0f} days."
        )

        ar_text = (
            f"مستوى الخطر: {risk_word}. درجة الخطر الإجمالية: {risk_score:.0f}/100. "
            f"أقصى خطر على العقدة: {max_risk:.1%}. "
            f"الوقت المقدر للتعافي: {recovery_days:.0f} يوم. "
            f"احتمالية التصعيد المتسلسل: متوسط إلى مرتفع. "
            f"مدة التأثير المتوقعة: {recovery_days:.0f}-{recovery_days*1.5:.0f} يوم."
        )

        return BilingualText(en=en_text, ar=ar_text), risk_score, risk_level

    def _generate_recommendations(
        self,
        result: ScenarioSimulationResult,
        disruption_type: str,
        risk_level: str,
        econ_impact: "EconomicImpact",
        ins_impact: "InsuranceImpact",
    ) -> List[Recommendation]:
        """Generate actionable recommendations."""
        recommendations = []

        # Priority: depends on risk level
        priority_map = {
            "critical": RecommendationPriority.CRITICAL,
            "high": RecommendationPriority.HIGH,
            "elevated": RecommendationPriority.MEDIUM,
            "nominal": RecommendationPriority.LOW,
        }
        priority = priority_map.get(risk_level, RecommendationPriority.HIGH)

        # Recommendation 1: Immediate stabilization
        rec1 = Recommendation(
            title=BilingualText(
                en="Immediate Stabilization Response",
                ar="استجابة الاستقرار الفوري",
            ),
            description=BilingualText(
                en="Deploy emergency response teams to critical nodes. Establish alternative routing for high-priority cargo. Implement demand reduction measures.",
                ar="نشر فريق الاستجابة الطارئة للعقد الحرجة. وضع مسارات بديلة للشحنات ذات الأولوية العالية. تطبيق تدابير تقليل الطلب.",
            ),
            priority=RecommendationPriority.CRITICAL,
            timeline=BilingualText(
                en="Immediate (0-6 hours)",
                ar="فوري (0-6 ساعات)",
            ),
            responsible_party=BilingualText(
                en="Port Authority, Transport Ministry, Emergency Services",
                ar="هيئة الميناء وزارة النقل الخدمات الطارئة",
            ),
            estimated_cost_usd_millions=10.0,
            expected_impact=BilingualText(
                en="Reduce disruption duration by 20-30%",
                ar="تقليل مدة الاضطراب بنسبة 20-30%",
            ),
        )
        recommendations.append(rec1)

        # Recommendation 2: Supply chain diversification
        rec2 = Recommendation(
            title=BilingualText(
                en="Supply Chain Diversification",
                ar="تنويع سلسلة الإمداد",
            ),
            description=BilingualText(
                en="Activate pre-arranged alternative corridors. Increase inventory buffers at regional distribution hubs. Establish alternative logistics partnerships.",
                ar="تفعيل ممرات بديلة مُرتبة مسبقاً. زيادة مخزونات المخزن المؤقت في مراكز التوزيع الإقليمية. إنشاء شراكات لوجستية بديلة.",
            ),
            priority=priority,
            timeline=BilingualText(
                en="Short-term (1-7 days)",
                ar="قصير المدى (1-7 أيام)",
            ),
            responsible_party=BilingualText(
                en="Logistics Operators, Importers/Exporters",
                ar="مشغلو اللوجستيات المستوردون والمصدرون",
            ),
            estimated_cost_usd_millions=50.0,
            expected_impact=BilingualText(
                en="Restore 40-60% of normal flow capacity",
                ar="استعادة 40-60% من طاقة التدفق الطبيعية",
            ),
        )
        recommendations.append(rec2)

        # Recommendation 3: Insurance portfolio management
        if ins_impact.estimated_claims_surge_percent > 20:
            rec3 = Recommendation(
                title=BilingualText(
                    en="Insurance Portfolio Risk Management",
                    ar="إدارة مخاطر محفظة التأمين",
                ),
                description=BilingualText(
                    en="Implement premium adjustments for affected routes. Increase reinsurance coverage. Activate loss adjustment procedures. Review underwriting guidelines.",
                    ar="تطبيق تعديلات العلاوات للمسارات المتضررة. زيادة تغطية إعادة التأمين. تفعيل إجراءات تسوية الخسائر. مراجعة إرشادات الاكتتاب.",
                ),
                priority=RecommendationPriority.HIGH,
                timeline=BilingualText(
                    en="Medium-term (1-14 days)",
                    ar="متوسط المدى (1-14 يوم)",
                ),
                responsible_party=BilingualText(
                    en="Insurance Companies, Regulators",
                    ar="شركات التأمين والمنظمين",
                ),
                estimated_cost_usd_millions=econ_impact.estimated_gdp_impact_usd_millions
                * 0.05,
                expected_impact=BilingualText(
                    en="Stabilize portfolio losses within acceptable bounds",
                    ar="استقرار خسائر المحفظة ضمن الحدود المقبولة",
                ),
            )
            recommendations.append(rec3)

        # Recommendation 4: Economic recovery stimulus
        if econ_impact.estimated_gdp_impact_usd_millions > 1000:
            rec4 = Recommendation(
                title=BilingualText(
                    en="Economic Recovery Stimulus",
                    ar="تحفيز الانتعاش الاقتصادي",
                ),
                description=BilingualText(
                    en="Coordinate regional economic support programs. Provide liquidity assistance to affected businesses. Implement trade facilitation measures. Accelerate infrastructure repairs.",
                    ar="تنسيق برامج الدعم الاقتصادي الإقليمية. توفير مساعدة السيولة للشركات المتضررة. تطبيق تدابير تسهيل التجارة. تسريع إصلاح البنية التحتية.",
                ),
                priority=RecommendationPriority.HIGH,
                timeline=BilingualText(
                    en="Medium to long-term (2-30 days)",
                    ar="متوسط إلى طويل المدى (2-30 يوم)",
                ),
                responsible_party=BilingualText(
                    en="Governments, Central Banks, Development Agencies",
                    ar="الحكومات والبنوك المركزية ووكالات التنمية",
                ),
                estimated_cost_usd_millions=econ_impact.estimated_gdp_impact_usd_millions
                * 0.1,
                expected_impact=BilingualText(
                    en="Accelerate recovery by 30-40%",
                    ar="تسريع التعافي بنسبة 30-40%",
                ),
            )
            recommendations.append(rec4)

        # Recommendation 5: Long-term resilience
        rec5 = Recommendation(
            title=BilingualText(
                en="Long-term Resilience Enhancement",
                ar="تعزيز القدرة على المقاومة طويلة الأجل",
            ),
            description=BilingualText(
                en="Invest in redundant infrastructure. Develop regional cooperation frameworks. Establish shared crisis response capabilities. Implement predictive monitoring systems.",
                ar="الاستثمار في البنية التحتية الزائدة. تطوير أطر التعاون الإقليمي. إنشاء قدرات الاستجابة للأزمات المشتركة. تطبيق أنظمة المراقبة التنبؤية.",
            ),
            priority=RecommendationPriority.MEDIUM,
            timeline=BilingualText(
                en="Long-term (3-12 months)",
                ar="طويل المدى (3-12 شهر)",
            ),
            responsible_party=BilingualText(
                en="GCC Governments, Regional Organizations",
                ar="حكومات دول مجلس التعاون وللمنظمات الإقليمية",
            ),
            estimated_cost_usd_millions=500.0,
            expected_impact=BilingualText(
                en="Reduce future disruption vulnerability by 40-50%",
                ar="تقليل القابلية للاستضعاف من الاضطرابات المستقبلية بنسبة 40-50%",
            ),
        )
        recommendations.append(rec5)

        return recommendations

    def _compute_economic_impact(
        self,
        result: ScenarioSimulationResult,
        severity: float,
        countries: List[str],
        disruption_type: str,
    ) -> EconomicImpact:
        """Compute economic impact metrics."""
        # Base impact scales with severity and number of affected countries
        base_impact = severity * len(countries) * 1000  # USD millions

        # Adjust for disruption type
        type_multiplier = {
            "port_closure": 1.5,
            "airspace_closure": 1.3,
            "pipeline_disruption": 1.8,
            "conflict": 2.5,
        }.get(disruption_type, 1.0)

        gdp_impact = base_impact * type_multiplier

        return EconomicImpact(
            estimated_gdp_impact_usd_millions=gdp_impact,
            trade_volume_affected_percent=min(100.0, severity * 80.0),
            employment_impact_thousands=min(500.0, gdp_impact / 2),
            commodity_price_inflation_percent=min(30.0, severity * 25.0),
            export_revenue_loss_percent=min(100.0, severity * 70.0),
            import_cost_increase_percent=min(50.0, severity * 40.0),
            recovery_duration_days=int(
                result.recovery_time_estimate_hours / 24
                * (1.5 if severity > 0.7 else 1.2 if severity > 0.4 else 1.0)
            ),
            economic_scenario="baseline",
        )

    def _compute_insurance_impact(
        self, result: ScenarioSimulationResult, severity: float
    ) -> InsuranceImpact:
        """Compute insurance portfolio impact."""
        # If using real insurance engine
        if self.insurance_engine:
            # Note: In full implementation, pass actual portfolio data
            impact = self.insurance_engine.assess_scenario_impact(
                scenario_severity=severity,
                affected_corridors_count=len(result.critical_nodes_post_shock),
                system_stress=result.system_stress_final or 0.0,
            )

            return InsuranceImpact(
                policies_affected_count=int(impact.affected_policies),
                estimated_claims_surge_percent=min(
                    100.0, impact.claims_surge_score * 100
                ),
                estimated_claims_uplift_usd_millions=min(
                    5000.0, impact.claims_uplift * 50
                ),
                underwriting_restrictions_implemented=impact.claims_surge_score > 0.6,
                premium_adjustment_percent=min(50.0, impact.claims_surge_score * 40),
                coverage_capacity_reduction_percent=min(
                    40.0, impact.stressed_portfolio_score * 30
                ),
                portfolio_stress_level="high"
                if impact.stressed_portfolio_score > 0.6
                else "elevated"
                if impact.stressed_portfolio_score > 0.3
                else "nominal",
            )

        # Fallback: empirical estimation
        claims_surge = min(100.0, severity * 80.0)
        claims_uplift = severity * 500.0

        return InsuranceImpact(
            policies_affected_count=int(
                len(result.critical_nodes_post_shock) * 100
            ),
            estimated_claims_surge_percent=claims_surge,
            estimated_claims_uplift_usd_millions=claims_uplift,
            underwriting_restrictions_implemented=claims_surge > 60,
            premium_adjustment_percent=min(50.0, claims_surge * 0.4),
            coverage_capacity_reduction_percent=min(40.0, severity * 35.0),
            portfolio_stress_level="high"
            if severity > 0.6
            else "elevated"
            if severity > 0.3
            else "nominal",
        )

    def _estimate_affected_population(
        self, countries: List[str], regions: List[str]
    ) -> float:
        """Estimate affected population in millions."""
        # Simplified estimation: average region ~5M people per affected area
        return len(regions) * 5.0

    def _estimate_cascade_probability(self, result: ScenarioSimulationResult) -> float:
        """Estimate probability of cascading escalation."""
        # Based on number of critical nodes and system stress
        critical_ratio = (
            len(result.critical_nodes_post_shock) / len(result.final_risk_scores)
            if result.final_risk_scores
            else 0.0
        )
        system_stress = result.system_stress_final or 0.0

        # Higher stress and critical nodes = higher cascade probability
        cascade_prob = (
            (critical_ratio * 0.6 + system_stress * 0.4) * 100
        )  # Convert to percentage

        return min(100.0, max(0.0, cascade_prob))

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp as ISO 8601 string."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"
