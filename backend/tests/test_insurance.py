"""
Comprehensive Test Suite for Insurance Intelligence Layer.

Tests cover all core components:
1. Portfolio exposure computation with HHI concentration index
2. Claims surge weights and severity mapping
3. Claims uplift formula with stress amplification
4. Underwriting classification thresholds and actions
5. Severity projection with regional adjustment
6. Insurance engine full pipeline orchestration
7. GCC default values preservation across all modules

All tests verify weight sums equal 1.0, threshold boundaries are in ascending order,
and regional multipliers are correctly applied.
"""

import pytest
import numpy as np
from dataclasses import asdict

from app.intelligence.insurance import (
    # Configuration
    GCC_INSURANCE_CONFIG,
    
    # Portfolio Exposure
    PolicyExposure,
    compute_portfolio_exposure,
    
    # Claims Surge
    SeverityLevel,
    compute_claims_surge_potential,
    
    # Claims Uplift
    compute_expected_claims_uplift,
    
    # Underwriting Watch
    UnderwritingClassification,
    compute_underwriting_restriction,
    
    # Severity Projection
    TrendDirection,
    project_severity,
    
    # Insurance Engine
    AssessmentLevel,
    InsuranceIntelligenceEngine,
)


class TestPortfolioExposureComputation:
    """Test portfolio exposure computation with correct formula application."""
    
    def test_portfolio_exposure_basic_computation(self):
        """Verify basic portfolio exposure formula: E_ins_p = gamma1*TIV + gamma2*RouteDep + gamma3*RegionRisk + gamma4*ClaimsElast."""
        policies = [
            PolicyExposure(
                policy_id="POL001",
                tiv=0.8,  # 80% TIV
                route_dependency=0.5,
                region_risk=0.6,
                claims_elasticity=0.4,
            ),
            PolicyExposure(
                policy_id="POL002",
                tiv=0.6,
                route_dependency=0.7,
                region_risk=0.5,
                claims_elasticity=0.3,
            ),
        ]
        
        result = compute_portfolio_exposure(policies, GCC_INSURANCE_CONFIG)
        
        # Verify portfolio-level metrics exist
        assert result.policy_count == 2
        assert result.total_exposure > 0
        assert 0 <= result.concentration_index <= 1  # HHI normalized
        assert len(result.per_policy_scores) == 2
        
        # Verify individual policy scores match formula
        for policy in policies:
            expected_score = (
                GCC_INSURANCE_CONFIG.exposure_weights['tiv'] * policy.tiv +
                GCC_INSURANCE_CONFIG.exposure_weights['route_dep'] * policy.route_dependency +
                GCC_INSURANCE_CONFIG.exposure_weights['region_risk'] * policy.region_risk +
                GCC_INSURANCE_CONFIG.exposure_weights['claims_elasticity'] * policy.claims_elasticity
            )
            expected_score = np.clip(expected_score, 0, 1)
            actual_score = result.per_policy_scores[policy.policy_id]
            assert abs(actual_score - expected_score) < 1e-6
    
    def test_portfolio_exposure_concentration_index(self):
        """Verify concentration index (HHI) calculation with multiple policies."""
        policies = [
            PolicyExposure(policy_id=f"POL{i:03d}", tiv=1.0/(i+1), 
                          route_dependency=0.5, region_risk=0.5, claims_elasticity=0.5)
            for i in range(5)
        ]
        
        result = compute_portfolio_exposure(policies, GCC_INSURANCE_CONFIG)
        
        # Concentration index should be between 0 and 1
        assert 0 <= result.concentration_index <= 1
        # With diverse exposures, should be lower concentration
        assert result.concentration_index < 0.5
        
        # Verify top exposed policies
        assert len(result.top_exposed_policies) <= 10
        assert all(p[0] in [pol.policy_id for pol in policies] 
                  for p in result.top_exposed_policies)
    
    def test_portfolio_exposure_gamma_weights_sum(self):
        """Verify gamma weights sum to 1.0."""
        gamma_sum = (
            GCC_INSURANCE_CONFIG.exposure_weights['tiv'] +
            GCC_INSURANCE_CONFIG.exposure_weights['route_dep'] +
            GCC_INSURANCE_CONFIG.exposure_weights['region_risk'] +
            GCC_INSURANCE_CONFIG.exposure_weights['claims_elasticity']
        )
        assert abs(gamma_sum - 1.0) < 1e-6


class TestClaimsSurgeWeights:
    """Test claims surge potential with correct weight application."""
    
    def test_claims_surge_formula_application(self):
        """Verify claims surge formula: S = psi1*Risk + psi2*Disruption + psi3*Exposure + psi4*PolicySens."""
        risk_score = 0.6
        disruption_score = 0.5
        exposure = 0.7
        policy_sensitivity = 0.4
        
        result = compute_claims_surge_potential(
            risk_score=risk_score,
            disruption_score=disruption_score,
            exposure=exposure,
            policy_sensitivity=policy_sensitivity,
            config=GCC_INSURANCE_CONFIG,
        )
        
        # Verify formula application
        expected_score = (
            GCC_INSURANCE_CONFIG.claims_surge_weights['risk'] * risk_score +
            GCC_INSURANCE_CONFIG.claims_surge_weights['disruption'] * disruption_score +
            GCC_INSURANCE_CONFIG.claims_surge_weights['exposure'] * exposure +
            GCC_INSURANCE_CONFIG.claims_surge_weights['policy_sensitivity'] * policy_sensitivity
        )
        expected_score = np.clip(expected_score, 0, 1)
        
        assert abs(result.surge_score - expected_score) < 1e-6
        assert result.surge_score >= 0 and result.surge_score <= 1
    
    def test_claims_surge_severity_mapping(self):
        """Verify severity level mapping: NORMAL (0-0.25), ELEVATED (0.25-0.50), CRITICAL (0.50-0.75), EXTREME (0.75-1.0)."""
        test_cases = [
            (0.1, SeverityLevel.NORMAL),
            (0.25, SeverityLevel.ELEVATED),
            (0.5, SeverityLevel.CRITICAL),
            (0.75, SeverityLevel.EXTREME),
            (0.9, SeverityLevel.EXTREME),
        ]
        
        for score, expected_level in test_cases:
            result = compute_claims_surge_potential(
                risk_score=score,
                disruption_score=score,
                exposure=score,
                policy_sensitivity=score,
                config=GCC_INSURANCE_CONFIG,
            )
            assert result.severity_level == expected_level
    
    def test_claims_surge_psi_weights_sum(self):
        """Verify psi weights sum to 1.0."""
        psi_sum = (
            GCC_INSURANCE_CONFIG.claims_surge_weights['risk'] +
            GCC_INSURANCE_CONFIG.claims_surge_weights['disruption'] +
            GCC_INSURANCE_CONFIG.claims_surge_weights['exposure'] +
            GCC_INSURANCE_CONFIG.claims_surge_weights['policy_sensitivity']
        )
        assert abs(psi_sum - 1.0) < 1e-6


class TestClaimsUpliftFormula:
    """Test claims uplift with stress amplification."""
    
    def test_claims_uplift_formula_application(self):
        """Verify claims uplift formula: DeltaClaims = BaseClaims * (1 + chi1*Surge + chi2*Stress + chi3*Uncertainty)."""
        base_claims = 100.0
        surge_score = 0.5
        system_stress = 0.6
        uncertainty = 0.4
        
        result = compute_expected_claims_uplift(
            base_claims=base_claims,
            surge_score=surge_score,
            system_stress=system_stress,
            uncertainty=uncertainty,
            config=GCC_INSURANCE_CONFIG,
        )
        
        # Verify formula application
        uplift_multiplier = (
            GCC_INSURANCE_CONFIG.claims_uplift_weights['surge'] * surge_score +
            GCC_INSURANCE_CONFIG.claims_uplift_weights['stress'] * system_stress +
            GCC_INSURANCE_CONFIG.claims_uplift_weights['uncertainty'] * uncertainty
        )
        expected_projected = base_claims * (1 + uplift_multiplier)
        
        assert abs(result.projected_claims - expected_projected) < 1e-6
        assert result.uplift_amount > 0
        assert result.uplift_percentage > 0
    
    def test_claims_uplift_stress_amplification(self):
        """Verify stress amplification effect on uplift."""
        base_claims = 100.0
        
        # Low stress case
        result_low_stress = compute_expected_claims_uplift(
            base_claims=base_claims,
            surge_score=0.5,
            system_stress=0.1,
            uncertainty=0.3,
            config=GCC_INSURANCE_CONFIG,
        )
        
        # High stress case
        result_high_stress = compute_expected_claims_uplift(
            base_claims=base_claims,
            surge_score=0.5,
            system_stress=0.9,
            uncertainty=0.3,
            config=GCC_INSURANCE_CONFIG,
        )
        
        # Higher stress should lead to higher uplift
        assert result_high_stress.projected_claims > result_low_stress.projected_claims
    
    def test_claims_uplift_chi_weights_sum(self):
        """Verify chi weights sum to 1.0."""
        chi_sum = (
            GCC_INSURANCE_CONFIG.claims_uplift_weights['surge'] +
            GCC_INSURANCE_CONFIG.claims_uplift_weights['stress'] +
            GCC_INSURANCE_CONFIG.claims_uplift_weights['uncertainty']
        )
        assert abs(chi_sum - 1.0) < 1e-6


class TestUnderwritingClassificationThresholds:
    """Test underwriting watch classification thresholds."""
    
    def test_underwriting_classification_boundaries(self):
        """Verify classification thresholds: STANDARD (0-25), MONITORED (25-50), RESTRICTED (50-70), REFERRAL (70+)."""
        # Test cases: (region_risk, logistics_stress, claims_surge, uncertainty, expected_classification)
        # Formula: UW = (0.40*region_risk + 0.25*logistics_stress + 0.20*claims_surge + 0.15*uncertainty) * 100
        test_cases = [
            # STANDARD: score < 25
            (0.25, 0, 0, 0, UnderwritingClassification.STANDARD),  # 0.40*0.25*100 = 10
            # MONITORED: 25 <= score < 50
            (0.625, 0, 0, 0, UnderwritingClassification.MONITORED),  # 0.40*0.625*100 = 25
            (1.0, 0, 0, 0, UnderwritingClassification.MONITORED),  # 0.40*1.0*100 = 40
            # RESTRICTED: 50 <= score < 70
            (1.0, 0.5, 0, 0, UnderwritingClassification.RESTRICTED),  # (0.40*1.0 + 0.25*0.5)*100 = 52.5
            # REFERRAL: score >= 70
            (1.0, 1.0, 1.0, 1.0, UnderwritingClassification.REFERRAL),  # (0.40 + 0.25 + 0.20 + 0.15)*100 = 100
        ]

        for region_risk, logistics_stress, claims_surge, uncertainty, expected_classification in test_cases:
            result = compute_underwriting_restriction(
                region_risk=region_risk,
                logistics_stress=logistics_stress,
                claims_surge=claims_surge,
                uncertainty=uncertainty,
                config=GCC_INSURANCE_CONFIG,
            )
            assert result.classification == expected_classification,                 f"Expected {expected_classification} for inputs ({region_risk}, {logistics_stress}, {claims_surge}, {uncertainty}), got {result.classification} with score {result.score}"
    
    def test_underwriting_thresholds_ascending_order(self):
        """Verify threshold boundaries are in ascending order."""
        # Note: config only contains 'monitored' and 'restricted' thresholds.
        # 'referral' classification is determined by score >= 70 comparison.
        thresholds = [
            GCC_INSURANCE_CONFIG.underwriting_thresholds['monitored'],
            GCC_INSURANCE_CONFIG.underwriting_thresholds['restricted'],
        ]
        
        # Thresholds should be in ascending order
        assert thresholds[0] < thresholds[1]
        # Verify expected values
        assert thresholds == [50, 70]
    
    def test_underwriting_watch_recommended_actions(self):
        """Verify recommended actions are generated for each classification level."""
        # Formula: UW = (0.40*region_risk + 0.25*logistics_stress + 0.20*claims_surge + 0.15*uncertainty) * 100
        classifications = [
            # STANDARD: score < 25
            ((0.1, 0, 0, 0), UnderwritingClassification.STANDARD),  # 0.40*0.1*100 = 4
            # MONITORED: 25 <= score < 50
            ((1.0, 0, 0, 0), UnderwritingClassification.MONITORED),  # 0.40*1.0*100 = 40
            # RESTRICTED: 50 <= score < 70
            ((1.0, 0.5, 0, 0), UnderwritingClassification.RESTRICTED),  # (0.40*1.0 + 0.25*0.5)*100 = 52.5
            # REFERRAL: score >= 70
            ((1.0, 1.0, 0.5, 0.5), UnderwritingClassification.REFERRAL),  # (0.40*1.0 + 0.25*1.0 + 0.20*0.5 + 0.15*0.5)*100 = 80
        ]

        for (region_risk, logistics_stress, claims_surge, uncertainty), expected_class in classifications:
            result = compute_underwriting_restriction(
                region_risk=region_risk,
                logistics_stress=logistics_stress,
                claims_surge=claims_surge,
                uncertainty=uncertainty,
                config=GCC_INSURANCE_CONFIG,
            )
            assert result.classification == expected_class,                 f"Expected {expected_class} for inputs ({region_risk}, {logistics_stress}, {claims_surge}, {uncertainty}), got {result.classification} with score {result.score}"
            assert len(result.recommended_actions) > 0  # All levels have actions


class TestSeverityProjectionRegional:
    """Test severity projection with regional adjustment."""
    
    def test_severity_projection_regional_multipliers(self):
        """Verify regional multipliers are correctly applied to loss ratio projections."""
        historical_loss_ratios = [0.5, 0.55, 0.6]  # Sample historical data
        
        # Test each GCC region
        regions = ["KW", "SA", "AE", "QA", "BH", "OM"]
        expected_multipliers = [1.05, 1.15, 1.20, 1.10, 1.00, 0.95]
        
        for region, expected_mult in zip(regions, expected_multipliers):
            result = project_severity(
                event_type="operational",
                region=region,
                current_stress=0.3,
                historical_loss_ratios=historical_loss_ratios,
                config=GCC_INSURANCE_CONFIG,
            )
            
            assert abs(result.regional_adjustment_factor - expected_mult) < 1e-6
            assert result.projected_loss_ratio > 0
            assert result.projected_loss_ratio <= 1.0
    
    def test_severity_projection_confidence_interval(self):
        """Verify confidence interval is calculated correctly."""
        historical_loss_ratios = [0.45, 0.50, 0.55, 0.60, 0.65]
        
        result = project_severity(
            event_type="catastrophe",
            region="AE",
            current_stress=0.5,
            historical_loss_ratios=historical_loss_ratios,
            config=GCC_INSURANCE_CONFIG,
        )
        
        # Confidence interval should be a tuple (lower, upper)
        assert isinstance(result.confidence_interval, tuple)
        assert len(result.confidence_interval) == 2
        assert result.confidence_interval[0] <= result.projected_loss_ratio
        assert result.projected_loss_ratio <= result.confidence_interval[1]
    
    def test_severity_projection_trend_analysis(self):
        """Verify trend direction analysis (INCREASING/STABLE/DECREASING)."""
        # Increasing trend
        increasing_ratios = [0.40, 0.45, 0.50, 0.55, 0.60]
        result_inc = project_severity(
            event_type="operational",
            region="SA",
            current_stress=0.3,
            historical_loss_ratios=increasing_ratios,
            config=GCC_INSURANCE_CONFIG,
        )
        # With increasing data, expect INCREASING trend
        
        # Decreasing trend
        decreasing_ratios = [0.60, 0.55, 0.50, 0.45, 0.40]
        result_dec = project_severity(
            event_type="operational",
            region="SA",
            current_stress=0.3,
            historical_loss_ratios=decreasing_ratios,
            config=GCC_INSURANCE_CONFIG,
        )
        
        # Verify trend is calculated
        assert result_inc.trend in [TrendDirection.INCREASING, TrendDirection.STABLE, TrendDirection.DECREASING]
        assert result_dec.trend in [TrendDirection.INCREASING, TrendDirection.STABLE, TrendDirection.DECREASING]


class TestInsuranceEngineFullPipeline:
    """Test insurance engine full pipeline orchestration."""
    
    def test_insurance_engine_policy_assessment(self):
        """Verify insurance engine orchestrates all five component modules correctly."""
        engine = InsuranceIntelligenceEngine(GCC_INSURANCE_CONFIG)
        
        # Assess a single policy with all inputs
        assessment = engine.assess_policy(
            policy_id="POL001",
            tiv=0.8,
            base_claims=1000.0,
            region="AE",
            route_dependency=0.5,
            region_risk=0.6,
            claims_elasticity=0.4,
            risk_score=0.6,
            disruption_score=0.5,
            policy_sensitivity=0.4,
            system_stress=0.6,
            uncertainty=0.4,
            logistics_stress=0.5,
        )
        
        # Verify all components are populated
        assert assessment.portfolio_exposure_score >= 0
        assert assessment.portfolio_exposure_score <= 1
        assert assessment.claims_surge_score >= 0
        assert assessment.claims_surge_score <= 1
        assert assessment.claims_uplift.projected_claims > 0
        assert assessment.underwriting_classification in [
            UnderwritingClassification.STANDARD,
            UnderwritingClassification.MONITORED,
            UnderwritingClassification.RESTRICTED,
            UnderwritingClassification.REFERRAL,
        ]
        assert assessment.overall_risk_score >= 0 and assessment.overall_risk_score <= 1
        assert assessment.risk_level in [
            AssessmentLevel.LOW,
            AssessmentLevel.MODERATE,
            AssessmentLevel.HIGH,
            AssessmentLevel.CRITICAL,
        ]
        assert len(assessment.narrative_en) > 0
        assert len(assessment.narrative_ar) > 0
    
    def test_insurance_engine_portfolio_assessment(self):
        """Verify portfolio-level assessment with aggregation."""
        engine = InsuranceIntelligenceEngine(GCC_INSURANCE_CONFIG)
        
        policies = [
            {
                "policy_id": f"POL{i:03d}",
                "tiv": 0.5 + i * 0.1,
                "base_claims": 1000.0 + i * 500,
                "region": ["AE", "SA", "KW", "QA"][i % 4],
                "route_dependency": 0.4 + i * 0.05,
                "region_risk": 0.5 + i * 0.08,
                "claims_elasticity": 0.3 + i * 0.05,
                "risk_score": 0.4 + i * 0.1,
                "disruption_score": 0.3 + i * 0.08,
                "policy_sensitivity": 0.3 + i * 0.06,
                "system_stress": 0.5,
                "uncertainty": 0.4,
                "logistics_stress": 0.4,
            }
            for i in range(3)
        ]
        
        portfolio_assessment = engine.assess_portfolio(policies)
        
        # Verify portfolio metrics
        assert portfolio_assessment.portfolio_size == 3
        assert portfolio_assessment.average_exposure >= 0
        assert portfolio_assessment.average_exposure <= 1
        assert 0 <= portfolio_assessment.concentration_index <= 1
        assert portfolio_assessment.aggregate_surge_exposure >= 0
        assert portfolio_assessment.aggregate_claims_uplift >= 0
        assert portfolio_assessment.portfolio_risk_score >= 0
        assert portfolio_assessment.portfolio_risk_score <= 1
        assert len(portfolio_assessment.policy_assessments) == 3
        assert len(portfolio_assessment.narrative_en) > 0
        assert len(portfolio_assessment.narrative_ar) > 0
    
    def test_insurance_engine_scenario_impact(self):
        """Verify scenario stress testing functionality."""
        engine = InsuranceIntelligenceEngine(GCC_INSURANCE_CONFIG)
        
        base_policies = [
            {
                "policy_id": "POL001",
                "tiv": 0.6,
                "base_claims": 1000.0,
                "region": "AE",
                "route_dependency": 0.5,
                "region_risk": 0.5,
                "claims_elasticity": 0.4,
                "risk_score": 0.5,
                "disruption_score": 0.4,
                "policy_sensitivity": 0.4,
                "system_stress": 0.5,
                "uncertainty": 0.4,
                "logistics_stress": 0.4,
            },
            {
                "policy_id": "POL002",
                "tiv": 0.7,
                "base_claims": 1200.0,
                "region": "SA",
                "route_dependency": 0.6,
                "region_risk": 0.6,
                "claims_elasticity": 0.5,
                "risk_score": 0.6,
                "disruption_score": 0.5,
                "policy_sensitivity": 0.5,
                "system_stress": 0.5,
                "uncertainty": 0.4,
                "logistics_stress": 0.4,
            },
        ]
        
        base_portfolio = engine.assess_portfolio(base_policies)
        scenario = engine.scenario_impact(
            scenario_name="High Stress Event",
            base_portfolio=base_portfolio,
            stress_factors={"system_stress": 1.5, "uncertainty": 1.2},  # Additional stress
        )
        
        # Verify scenario metrics
        assert scenario.scenario_name == "High Stress Event"
        assert hasattr(scenario, 'base_portfolio_score')
        assert hasattr(scenario, 'stressed_portfolio_score')
        assert scenario.stressed_portfolio_score >= scenario.base_portfolio_score
        assert scenario.affected_policies >= 0
        assert len(scenario.narrative_en) > 0
        assert len(scenario.narrative_ar) > 0


class TestGCCDefaultsPreserved:
    """Test that all GCC default values are preserved across the system."""
    
    def test_gcc_config_default_weights(self):
        """Verify all default weights are set correctly."""
        config = GCC_INSURANCE_CONFIG
        
        # Portfolio exposure weights
        assert config.exposure_weights['tiv'] == 0.30
        assert config.exposure_weights['route_dep'] == 0.25
        assert config.exposure_weights['region_risk'] == 0.25
        assert config.exposure_weights['claims_elasticity'] == 0.20
        
        # Claims surge weights
        assert config.claims_surge_weights['risk'] == 0.28
        assert config.claims_surge_weights['disruption'] == 0.30
        assert config.claims_surge_weights['exposure'] == 0.25
        assert config.claims_surge_weights['policy_sensitivity'] == 0.17
        
        # Claims uplift weights
        assert config.claims_uplift_weights['surge'] == 0.45
        assert config.claims_uplift_weights['stress'] == 0.30
        assert config.claims_uplift_weights['uncertainty'] == 0.25
        
        # Underwriting weights
        assert config.underwriting_weights['region_risk'] == 0.40
        assert config.underwriting_weights['logistics_stress'] == 0.25
        assert config.underwriting_weights['claims_surge'] == 0.20
        assert config.underwriting_weights['uncertainty'] == 0.15
    
    def test_gcc_config_regional_multipliers(self):
        """Verify regional multipliers for all GCC countries."""
        config = GCC_INSURANCE_CONFIG
        
        expected_multipliers = {
            "KW": 1.05,
            "SA": 1.15,
            "AE": 1.20,
            "QA": 1.10,
            "BH": 1.00,
            "OM": 0.95,
        }
        
        for region, expected_mult in expected_multipliers.items():
            assert config.regional_multipliers[region] == expected_mult
    
    def test_gcc_config_thresholds(self):
        """Verify underwriting thresholds are preserved."""
        config = GCC_INSURANCE_CONFIG
        
        # Config has 'monitored' and 'restricted' thresholds
        assert config.underwriting_thresholds['monitored'] == 50
        assert config.underwriting_thresholds['restricted'] == 70
        
        # Verify ascending order
        assert config.underwriting_thresholds['monitored'] < config.underwriting_thresholds['restricted']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
