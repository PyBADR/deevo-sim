"""
Explanation Generator Module - Scenario Engine Phase 6
Generates bilingual (English/Arabic) narrative explanations of scenario impacts
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from app.scenarios.baseline import BaselineSnapshot
from app.scenarios.simulator import ScenarioSimulationResult
from app.scenarios.delta import NodeDeltaAnalysis, DeltaMetrics, DeltaCalculator


@dataclass
class ScenarioExplanation:
    """Bilingual scenario explanation"""
    scenario_name: str
    english_summary: str
    arabic_summary: str
    english_detailed: str
    arabic_detailed: str
    key_findings_en: List[str]
    key_findings_ar: List[str]
    critical_nodes_en: List[str]
    critical_nodes_ar: List[str]
    recommendations_en: List[str]
    recommendations_ar: List[str]
    timestamp: datetime


class ExplanationGenerator:
    """Generates bilingual narrative explanations for scenario impacts"""
    
    def __init__(self):
        self.delta_calculator = DeltaCalculator()
    
    def generate_explanation(
        self,
        scenario_name: str,
        baseline: BaselineSnapshot,
        simulation_result: ScenarioSimulationResult,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        delta_metrics: DeltaMetrics,
        scenario_description: Optional[str] = None
    ) -> ScenarioExplanation:
        """
        Generate comprehensive bilingual explanation of scenario impact
        
        Args:
            scenario_name: Name of the scenario
            baseline: Pre-shock baseline snapshot
            simulation_result: Post-shock simulation results
            node_deltas: Node-level delta analysis
            delta_metrics: Aggregate delta metrics
            scenario_description: Optional detailed scenario description
        
        Returns:
            ScenarioExplanation with English and Arabic narratives
        """
        
        # Generate summaries
        en_summary = self._generate_executive_summary_en(
            scenario_name, delta_metrics, simulation_result
        )
        ar_summary = self._generate_executive_summary_ar(
            scenario_name, delta_metrics, simulation_result
        )
        
        # Generate detailed explanations
        en_detailed = self._generate_detailed_explanation_en(
            scenario_name, baseline, simulation_result, node_deltas, delta_metrics
        )
        ar_detailed = self._generate_detailed_explanation_ar(
            scenario_name, baseline, simulation_result, node_deltas, delta_metrics
        )
        
        # Extract key findings
        key_findings_en = self._extract_key_findings_en(node_deltas, delta_metrics)
        key_findings_ar = self._extract_key_findings_ar(node_deltas, delta_metrics)
        
        # Identify critical nodes
        critical_en = self._format_critical_nodes_en(node_deltas)
        critical_ar = self._format_critical_nodes_ar(node_deltas)
        
        # Generate recommendations
        rec_en = self._generate_recommendations_en(node_deltas, delta_metrics)
        rec_ar = self._generate_recommendations_ar(node_deltas, delta_metrics)
        
        return ScenarioExplanation(
            scenario_name=scenario_name,
            english_summary=en_summary,
            arabic_summary=ar_summary,
            english_detailed=en_detailed,
            arabic_detailed=ar_detailed,
            key_findings_en=key_findings_en,
            key_findings_ar=key_findings_ar,
            critical_nodes_en=critical_en,
            critical_nodes_ar=critical_ar,
            recommendations_en=rec_en,
            recommendations_ar=rec_ar,
            timestamp=datetime.utcnow()
        )
    
    def _generate_executive_summary_en(
        self,
        scenario_name: str,
        delta_metrics: DeltaMetrics,
        simulation_result: ScenarioSimulationResult
    ) -> str:
        """Generate executive summary in English"""
        
        template = (
            f"Scenario Analysis: {scenario_name}\n\n"
            f"Impact Assessment:\n"
            f"- Total nodes affected: {delta_metrics.total_nodes_affected}\n"
            f"- Critical nodes at risk: {delta_metrics.critical_nodes}\n"
            f"- High-impact nodes: {delta_metrics.high_impact_nodes}\n"
            f"- Average risk increase: {delta_metrics.mean_risk_increase:.2%}\n"
            f"- Maximum risk increase: {delta_metrics.max_risk_increase:.2%}\n"
            f"- System stress level: {simulation_result.system_stress_final:.2%}\n"
            f"- Estimated recovery time: {delta_metrics.recovery_time_estimate_hours:.1f} hours\n"
        )
        
        if delta_metrics.affected_corridors:
            template += f"- Affected corridors: {', '.join(delta_metrics.affected_corridors)}\n"
        
        if delta_metrics.affected_regions:
            template += f"- Affected regions: {', '.join(delta_metrics.affected_regions)}\n"
        
        return template
    
    def _generate_executive_summary_ar(
        self,
        scenario_name: str,
        delta_metrics: DeltaMetrics,
        simulation_result: ScenarioSimulationResult
    ) -> str:
        """Generate executive summary in Arabic"""
        
        template = (
            f"تحليل السيناريو: {scenario_name}\n\n"
            f"تقييم التأثير:\n"
            f"- العقد المتأثرة الإجمالية: {delta_metrics.total_nodes_affected}\n"
            f"- العقد الحرجة المعرضة للخطر: {delta_metrics.critical_nodes}\n"
            f"- العقد عالية التأثير: {delta_metrics.high_impact_nodes}\n"
            f"- متوسط زيادة المخاطر: {delta_metrics.mean_risk_increase:.2%}\n"
            f"- الحد الأقصى لزيادة المخاطر: {delta_metrics.max_risk_increase:.2%}\n"
            f"- مستوى الضغط على النظام: {simulation_result.system_stress_final:.2%}\n"
            f"- وقت التعافي المتوقع: {delta_metrics.recovery_time_estimate_hours:.1f} ساعات\n"
        )
        
        if delta_metrics.affected_corridors:
            template += f"- الممرات المتأثرة: {', '.join(delta_metrics.affected_corridors)}\n"
        
        if delta_metrics.affected_regions:
            template += f"- المناطق المتأثرة: {', '.join(delta_metrics.affected_regions)}\n"
        
        return template
    
    def _generate_detailed_explanation_en(
        self,
        scenario_name: str,
        baseline: BaselineSnapshot,
        simulation_result: ScenarioSimulationResult,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        delta_metrics: DeltaMetrics
    ) -> str:
        """Generate detailed explanation in English"""
        
        explanation = f"Detailed Analysis: {scenario_name}\n\n"
        
        # Impact distribution
        critical_count = sum(1 for nd in node_deltas.values() if nd.impact_severity == 'critical')
        high_count = sum(1 for nd in node_deltas.values() if nd.impact_severity == 'high')
        medium_count = sum(1 for nd in node_deltas.values() if nd.impact_severity == 'medium')
        low_count = sum(1 for nd in node_deltas.values() if nd.impact_severity == 'low')
        
        explanation += (
            f"Impact Distribution:\n"
            f"- Critical severity: {critical_count} nodes\n"
            f"- High severity: {high_count} nodes\n"
            f"- Medium severity: {medium_count} nodes\n"
            f"- Low severity: {low_count} nodes\n\n"
        )
        
        # Cascade effects
        cascade_affected = sum(1 for nd in node_deltas.values() if nd.affected_by_cascade)
        explanation += (
            f"Cascade Propagation:\n"
            f"- Nodes affected by cascade: {cascade_affected}\n"
            f"- System stress from cascades: {simulation_result.system_stress_final:.2%}\n\n"
        )
        
        # Risk dynamics
        explanation += (
            f"Risk Dynamics:\n"
            f"- System risk increase: {delta_metrics.system_risk_delta:.2%}\n"
            f"- Mean node risk increase: {delta_metrics.mean_risk_increase:.2%}\n"
            f"- Maximum isolated impact: {delta_metrics.max_risk_increase:.2%}\n\n"
        )
        
        # Recovery outlook
        explanation += (
            f"Recovery Outlook:\n"
            f"- Estimated recovery time: {delta_metrics.recovery_time_estimate_hours:.1f} hours\n"
            f"- System resilience assessment: "
        )
        
        if simulation_result.system_stress_final < 0.3:
            explanation += "Resilient - system can absorb impact\n"
        elif simulation_result.system_stress_final < 0.6:
            explanation += "Moderate - controlled recovery expected\n"
        else:
            explanation += "Vulnerable - extended recovery period anticipated\n"
        
        return explanation
    
    def _generate_detailed_explanation_ar(
        self,
        scenario_name: str,
        baseline: BaselineSnapshot,
        simulation_result: ScenarioSimulationResult,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        delta_metrics: DeltaMetrics
    ) -> str:
        """Generate detailed explanation in Arabic"""
        
        explanation = f"التحليل التفصيلي: {scenario_name}\n\n"
        
        critical_count = sum(1 for nd in node_deltas.values() if nd.impact_severity == 'critical')
        high_count = sum(1 for nd in node_deltas.values() if nd.impact_severity == 'high')
        
        explanation += (
            f"توزيع التأثير:\n"
            f"- الشدة الحرجة: {critical_count} عقدة\n"
            f"- الشدة العالية: {high_count} عقدة\n\n"
            f"الانتشار المتسلسل:\n"
            f"- مستوى الضغط على النظام: {simulation_result.system_stress_final:.2%}\n\n"
            f"ديناميكيات المخاطر:\n"
            f"- زيادة مخاطر النظام: {delta_metrics.system_risk_delta:.2%}\n"
            f"- وقت التعافي المتوقع: {delta_metrics.recovery_time_estimate_hours:.1f} ساعات\n"
        )
        
        return explanation
    
    def _extract_key_findings_en(
        self,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        delta_metrics: DeltaMetrics
    ) -> List[str]:
        """Extract key findings in English"""
        
        findings = []
        
        # Severity findings
        if delta_metrics.critical_nodes > 0:
            findings.append(
                f"{delta_metrics.critical_nodes} critical nodes identified exceeding "
                f"75% risk threshold"
            )
        
        if delta_metrics.high_impact_nodes > 0:
            findings.append(
                f"{delta_metrics.high_impact_nodes} nodes showing high-impact disruption "
                f"with 50-75% risk increase"
            )
        
        # Cascade findings
        cascade_nodes = sum(1 for nd in node_deltas.values() if nd.affected_by_cascade)
        if cascade_nodes > 0:
            findings.append(
                f"Cascade propagation affected {cascade_nodes} nodes, indicating "
                f"significant network vulnerability"
            )
        
        # Regional findings
        if delta_metrics.affected_regions:
            findings.append(
                f"Geographic impact spans {len(delta_metrics.affected_regions)} regions: "
                f"{', '.join(delta_metrics.affected_regions)}"
            )
        
        # Recovery findings
        findings.append(
            f"Recovery trajectory indicates {delta_metrics.recovery_time_estimate_hours:.1f} "
            f"hour recovery window under standard conditions"
        )
        
        return findings
    
    def _extract_key_findings_ar(
        self,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        delta_metrics: DeltaMetrics
    ) -> List[str]:
        """Extract key findings in Arabic"""
        
        findings = []
        
        if delta_metrics.critical_nodes > 0:
            findings.append(
                f"تم تحديد {delta_metrics.critical_nodes} عقد حرجة تتجاوز عتبة المخاطر"
            )
        
        if delta_metrics.affected_regions:
            findings.append(
                f"التأثير الجغرافي يمتد عبر {len(delta_metrics.affected_regions)} منطقة"
            )
        
        findings.append(
            f"وقت التعافي المتوقع: {delta_metrics.recovery_time_estimate_hours:.1f} ساعات"
        )
        
        return findings
    
    def _format_critical_nodes_en(
        self,
        node_deltas: Dict[str, NodeDeltaAnalysis]
    ) -> List[str]:
        """Format critical nodes list in English"""
        
        critical = [
            f"{nd.node_id}: {nd.impact_severity.upper()} "
            f"(baseline {nd.baseline_risk:.1%} -> {nd.post_shock_risk:.1%}, "
            f"Δ {nd.risk_delta_pct:+.1f}%)"
            for nd in node_deltas.values()
            if nd.impact_severity in ['critical', 'high']
        ]
        return sorted(critical)[:10]  # Top 10
    
    def _format_critical_nodes_ar(
        self,
        node_deltas: Dict[str, NodeDeltaAnalysis]
    ) -> List[str]:
        """Format critical nodes list in Arabic"""
        
        critical = [
            f"{nd.node_id}: {self._translate_severity_ar(nd.impact_severity)} "
            f"({nd.post_shock_risk:.1%})"
            for nd in node_deltas.values()
            if nd.impact_severity in ['critical', 'high']
        ]
        return sorted(critical)[:10]
    
    def _generate_recommendations_en(
        self,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        delta_metrics: DeltaMetrics
    ) -> List[str]:
        """Generate recommendations in English"""
        
        recommendations = []
        
        critical_nodes = [nd for nd in node_deltas.values() if nd.impact_severity == 'critical']
        if critical_nodes:
            recommendations.append(
                f"Prioritize protection and contingency planning for {len(critical_nodes)} "
                f"critical nodes"
            )
        
        cascade_nodes = [nd for nd in node_deltas.values() if nd.affected_by_cascade]
        if cascade_nodes:
            recommendations.append(
                f"Implement cascade-breaking measures at {len(cascade_nodes)} vulnerable nodes "
                f"to prevent network-wide propagation"
            )
        
        recommendations.append(
            f"Activate recovery protocols with {delta_metrics.recovery_time_estimate_hours:.0f} "
            f"hour mobilization timeframe"
        )
        
        if delta_metrics.affected_corridors:
            recommendations.append(
                f"Establish alternative route planning for {len(delta_metrics.affected_corridors)} "
                f"affected corridors"
            )
        
        recommendations.append(
            "Monitor affected regions for secondary impacts and cascading failures"
        )
        
        return recommendations
    
    def _generate_recommendations_ar(
        self,
        node_deltas: Dict[str, NodeDeltaAnalysis],
        delta_metrics: DeltaMetrics
    ) -> List[str]:
        """Generate recommendations in Arabic"""
        
        recommendations = []
        recommendations.append("تنشيط بروتوكولات التعافي الفورية")
        recommendations.append("مراقبة المناطق المتأثرة للتأثيرات الثانوية")
        recommendations.append("تطوير خطط الطوارئ للعقد الحرجة")
        
        return recommendations
    
    def _translate_severity_ar(self, severity: str) -> str:
        """Translate severity levels to Arabic"""
        
        translations = {
            'critical': 'حرج',
            'high': 'عالي',
            'medium': 'متوسط',
            'low': 'منخفض',
            'none': 'لا يوجد'
        }
        return translations.get(severity, severity)
    
    def export_explanation(self, explanation: ScenarioExplanation) -> Dict:
        """Export explanation to dictionary format"""
        
        return {
            'scenario_name': explanation.scenario_name,
            'timestamp': explanation.timestamp.isoformat(),
            'english': {
                'summary': explanation.english_summary,
                'detailed': explanation.english_detailed,
                'key_findings': explanation.key_findings_en,
                'critical_nodes': explanation.critical_nodes_en,
                'recommendations': explanation.recommendations_en
            },
            'arabic': {
                'summary': explanation.arabic_summary,
                'detailed': explanation.arabic_detailed,
                'key_findings': explanation.key_findings_ar,
                'critical_nodes': explanation.critical_nodes_ar,
                'recommendations': explanation.recommendations_ar
            }
        }
