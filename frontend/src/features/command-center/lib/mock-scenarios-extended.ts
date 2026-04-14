/**
 * Extended Scenario Mock Datasets
 *
 * Adds 4 additional complete scenario payloads:
 *   - GCC Cyber Infrastructure Attack
 *   - Qatar LNG Export Disruption
 *   - GCC Insurance Reserve Shortfall
 *   - GCC Fintech Payment System Outage
 *
 * Each dataset provides the full payload contract required by loadMock():
 *   scenario, headline, graphNodes, graphEdges, causalChain,
 *   sectorImpacts, sectorRollups, decisionActions, explanation,
 *   trust, lossRange, assumptions, countryExposures, outcomes, sectorDepth.
 */

import type {
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  CausalStep,
  SectorImpact,
  DecisionActionV2,
} from "@/types/observatory";
import type { CountryExposureEntry, OutcomeScenario } from "./mock-data";

// ══════════════════════════════════════════════════════════════════════
// 1. GCC CYBER INFRASTRUCTURE ATTACK
// ══════════════════════════════════════════════════════════════════════

export const MOCK_CYBER_SCENARIO = {
  template_id: "gcc_cyber_attack",
  label: "GCC Cyber Infrastructure Attack — Critical Systems",
  label_ar: "هجوم سيبراني على البنية التحتية الخليجية — الأنظمة الحرجة",
  severity: 0.68,
  horizon_hours: 96,
  domain: "CYBER",
  trigger_time: "2026-04-12T02:45:00Z",
};

export const MOCK_CYBER_HEADLINE = {
  total_loss_usd: 1_840_000_000,
  total_nodes_impacted: 22,
  propagation_depth: 4,
  peak_day: 2,
  max_recovery_days: 21,
  average_stress: 0.56,
  affected_entities: 22,
  critical_count: 3,
  elevated_count: 8,
};

export const MOCK_CYBER_GRAPH_NODES: KnowledgeGraphNode[] = [
  { id: "swift_gcc", label: "SWIFT GCC Gateway", label_ar: "بوابة سويفت الخليجية", layer: "infrastructure", type: "system", weight: 0.94, lat: 25.20, lng: 55.27, sensitivity: 0.92, stress: 0.85, classification: "CRITICAL" },
  { id: "rtgs_sama", label: "SAMA RTGS System", label_ar: "نظام التسوية الإجمالي — مؤسسة النقد", layer: "infrastructure", type: "system", weight: 0.90, lat: 24.69, lng: 46.69, sensitivity: 0.88, stress: 0.76, classification: "ELEVATED" },
  { id: "uae_payment_switch", label: "UAE Payment Switch", label_ar: "مفتاح الدفع الإماراتي", layer: "infrastructure", type: "system", weight: 0.88, lat: 24.49, lng: 54.37, sensitivity: 0.85, stress: 0.72, classification: "ELEVATED" },
  { id: "gcc_data_centers", label: "GCC Cloud Infrastructure", label_ar: "البنية السحابية الخليجية", layer: "infrastructure", type: "datacenter", weight: 0.86, lat: 25.10, lng: 55.18, sensitivity: 0.80, stress: 0.68, classification: "ELEVATED" },
  { id: "banking_core", label: "Banking Core Systems", label_ar: "الأنظمة المصرفية الأساسية", layer: "finance", type: "system", weight: 0.91, lat: 24.71, lng: 46.67, sensitivity: 0.82, stress: 0.64, classification: "MODERATE" },
  { id: "sama", label: "SAMA", label_ar: "مؤسسة النقد", layer: "finance", type: "central_bank", weight: 0.90, lat: 24.69, lng: 46.69, sensitivity: 0.70, stress: 0.52, classification: "GUARDED" },
  { id: "cbuae", label: "CBUAE", label_ar: "مصرف الإمارات المركزي", layer: "finance", type: "central_bank", weight: 0.87, lat: 24.49, lng: 54.37, sensitivity: 0.68, stress: 0.48, classification: "GUARDED" },
  { id: "stock_exchanges", label: "GCC Stock Exchanges", label_ar: "بورصات دول الخليج", layer: "finance", type: "market", weight: 0.84, lat: 25.30, lng: 51.52, sensitivity: 0.76, stress: 0.58, classification: "GUARDED" },
  { id: "telecom_infra", label: "Telecom Infrastructure", label_ar: "البنية التحتية للاتصالات", layer: "infrastructure", type: "network", weight: 0.82, lat: 25.25, lng: 55.30, sensitivity: 0.78, stress: 0.45, classification: "GUARDED" },
  { id: "energy_scada", label: "Energy SCADA Networks", label_ar: "شبكات سكادا الطاقة", layer: "infrastructure", type: "system", weight: 0.80, lat: 26.39, lng: 50.10, sensitivity: 0.84, stress: 0.62, classification: "MODERATE" },
];

export const MOCK_CYBER_GRAPH_EDGES: KnowledgeGraphEdge[] = [
  { id: "ce1", source: "swift_gcc", target: "rtgs_sama", weight: 0.90, polarity: 1, label: "settlement channel disrupted", label_ar: "تعطل قناة التسوية", transmission: 0.85 },
  { id: "ce2", source: "swift_gcc", target: "uae_payment_switch", weight: 0.87, polarity: 1, label: "payment routing failure", label_ar: "فشل توجيه الدفع", transmission: 0.82 },
  { id: "ce3", source: "gcc_data_centers", target: "banking_core", weight: 0.80, polarity: 1, label: "service degradation cascade", label_ar: "سلسلة تدهور الخدمات", transmission: 0.74 },
  { id: "ce4", source: "rtgs_sama", target: "sama", weight: 0.75, polarity: 1, label: "settlement delays escalate", label_ar: "تصاعد تأخيرات التسوية", transmission: 0.68 },
  { id: "ce5", source: "banking_core", target: "stock_exchanges", weight: 0.72, polarity: 1, label: "trading platform disruption", label_ar: "تعطل منصات التداول", transmission: 0.65 },
  { id: "ce6", source: "swift_gcc", target: "energy_scada", weight: 0.65, polarity: 1, label: "lateral attack vector", label_ar: "متجه هجوم جانبي", transmission: 0.58 },
];

export const MOCK_CYBER_CAUSAL_CHAIN: CausalStep[] = [
  { step: 1, entity_id: "swift_gcc", entity_label: "SWIFT GCC Gateway", entity_label_ar: "بوابة سويفت الخليجية", event: "Advanced persistent threat gains access to SWIFT gateway — message integrity compromised", event_ar: "تهديد مستمر متقدم يخترق بوابة سويفت — سلامة الرسائل مخترقة", impact_usd: 0, stress_delta: 0.85, mechanism: "cyber_intrusion" },
  { step: 2, entity_id: "rtgs_sama", entity_label: "SAMA RTGS System", entity_label_ar: "نظام التسوية الإجمالي", event: "Real-time gross settlement halted — SAR 12B in transactions queued", event_ar: "توقف نظام التسوية الإجمالي — 12 مليار ريال في المعاملات المعلقة", impact_usd: 520_000_000, stress_delta: 0.76, mechanism: "system_failure" },
  { step: 3, entity_id: "uae_payment_switch", entity_label: "UAE Payment Switch", entity_label_ar: "مفتاح الدفع الإماراتي", event: "Cross-border payment routing fails — AED settlement backlog grows", event_ar: "فشل توجيه الدفع العابر للحدود — تراكم تسوية الدرهم يتصاعد", impact_usd: 380_000_000, stress_delta: 0.72, mechanism: "contagion" },
  { step: 4, entity_id: "banking_core", entity_label: "Banking Core Systems", entity_label_ar: "الأنظمة المصرفية الأساسية", event: "Core banking services degraded — ATM/POS networks intermittent across region", event_ar: "تدهور خدمات البنوك الأساسية — شبكات الصراف والدفع متقطعة", impact_usd: 440_000_000, stress_delta: 0.64, mechanism: "service_degradation" },
  { step: 5, entity_id: "stock_exchanges", entity_label: "GCC Stock Exchanges", entity_label_ar: "بورصات دول الخليج", event: "Trading halted on Tadawul and ADX — market confidence drops sharply", event_ar: "توقف التداول في تداول و ADX — انخفاض حاد في ثقة السوق", impact_usd: 500_000_000, stress_delta: 0.58, mechanism: "market_disruption" },
];

export const MOCK_CYBER_SECTOR_IMPACTS: SectorImpact[] = [
  { sector: "infrastructure", sectorLabel: "Critical Infrastructure", avgImpact: 0.72, maxImpact: 0.85, nodeCount: 5, topNode: "swift_gcc", color: "#8C2318" },
  { sector: "finance", sectorLabel: "Financial Systems", avgImpact: 0.55, maxImpact: 0.64, nodeCount: 4, topNode: "banking_core", color: "#0C6B58" },
  { sector: "economy", sectorLabel: "Capital Markets", avgImpact: 0.48, maxImpact: 0.58, nodeCount: 2, topNode: "stock_exchanges", color: "#8B6914" },
];

export const MOCK_CYBER_SECTOR_ROLLUPS = {
  banking: { aggregate_stress: 0.62, total_loss: 780_000_000, node_count: 5, classification: "ELEVATED" as const },
  insurance: { aggregate_stress: 0.45, total_loss: 220_000_000, node_count: 3, classification: "GUARDED" as const },
  fintech: { aggregate_stress: 0.68, total_loss: 440_000_000, node_count: 4, classification: "ELEVATED" as const },
  energy: { aggregate_stress: 0.38, total_loss: 180_000_000, node_count: 3, classification: "LOW" as const },
  trade: { aggregate_stress: 0.32, total_loss: 140_000_000, node_count: 3, classification: "LOW" as const },
};

export const MOCK_CYBER_DECISION_ACTIONS: DecisionActionV2[] = [
  {
    id: "cda_1", action: "Activate GCC-CERT emergency incident response — isolate SWIFT gateway", action_ar: "تفعيل استجابة طوارئ GCC-CERT — عزل بوابة سويفت",
    sector: "cyber", owner: "National Cybersecurity Authority", urgency: 96, value: 92,
    regulatory_risk: 0.10, priority: 97, target_node_id: "swift_gcc",
    target_lat: 25.20, target_lng: 55.27, loss_avoided_usd: 680_000_000,
    cost_usd: 25_000_000, confidence: 0.89,
  },
  {
    id: "cda_2", action: "Deploy backup settlement channel via bilateral RTGS bypass", action_ar: "نشر قناة تسوية احتياطية عبر تجاوز RTGS الثنائي",
    sector: "banking", owner: "SAMA + CBUAE", urgency: 92, value: 88,
    regulatory_risk: 0.15, priority: 91, target_node_id: "rtgs_sama",
    target_lat: 24.69, target_lng: 46.69, loss_avoided_usd: 520_000_000,
    cost_usd: 18_000_000, confidence: 0.85,
  },
  {
    id: "cda_3", action: "Suspend automated trading — activate manual circuit breakers on all exchanges", action_ar: "تعليق التداول الآلي — تفعيل قاطعات الدوائر اليدوية في جميع البورصات",
    sector: "finance", owner: "Capital Markets Authority", urgency: 85, value: 78,
    regulatory_risk: 0.20, priority: 82, target_node_id: "stock_exchanges",
    target_lat: 25.30, target_lng: 51.52, loss_avoided_usd: 350_000_000,
    cost_usd: 8_000_000, confidence: 0.82,
  },
];

export const MOCK_CYBER_EXPLANATION = {
  narrative_en: "A coordinated cyber attack targeting the GCC SWIFT gateway and regional payment infrastructure triggers cascading failures across financial systems. The attack propagates through four channels: (1) SWIFT message integrity compromise halts cross-border settlements, (2) RTGS system failure queues SAR 12B in pending transactions, (3) core banking service degradation disrupts ATM/POS networks region-wide, and (4) stock exchange trading halts erode market confidence. Total estimated loss reaches $1.84B over a 96-hour horizon, with peak disruption on Day 2.",
  narrative_ar: "هجوم سيبراني منسق يستهدف بوابة سويفت الخليجية والبنية التحتية للدفع الإقليمية يؤدي إلى إخفاقات متتالية عبر الأنظمة المالية.",
  methodology: "Institutional macro-financial intelligence: Cyber threat propagation model with MITRE ATT&CK framework mapping. 22-node GCC critical infrastructure graph with 42 causal edges. Confidence: Monte Carlo 10K iterations.",
  confidence: 0.82,
  total_steps: 5,
};

export const MOCK_CYBER_TRUST = {
  trace_id: "trc_20260412_024500_cyber",
  audit_id: "aud_cc_003",
  audit_hash: "sha256:c6f4e0a13b5d9c28f7e4b3a6d8c5f2e1b4a7d0c3f6e9b2a5d8c1f4e7b0a3d6c9",
  model_version: "io-v4.0.0",
  pipeline_version: "unified-v2.1",
  confidence_score: 0.82,
  data_sources: ["GCC-CERT Threat Feed", "SWIFT Network Monitor", "SAMA RTGS Logs", "CMA Market Data", "Telecom NOC"],
  stages_completed: ["signal_ingest", "graph_activation", "causal_trace", "propagation", "physics", "math", "sector_stress", "decision_gen", "explanation"],
  warnings: ["SWIFT gateway status: real-time feed delayed", "Stock exchange data: T+15min"],
};

export const MOCK_CYBER_LOSS_RANGE = { low: 1_560_000_000, mid: 1_840_000_000, high: 2_120_000_000, confidence_pct: 90 };
export const MOCK_CYBER_DECISION_DEADLINE = new Date(Date.now() + 12 * 3_600_000).toISOString();

export const MOCK_CYBER_ASSUMPTIONS: string[] = [
  "Attack vector is advanced persistent threat (APT), not ransomware",
  "SWIFT gateway compromise is partial — backup channels available",
  "No physical infrastructure damage — attack is purely digital",
  "Central banks maintain independent air-gapped backup systems",
  "Incident response teams mobilize within 2 hours of detection",
];

export const MOCK_CYBER_COUNTRY_EXPOSURES: CountryExposureEntry[] = [
  { code: "UAE", name: "United Arab Emirates", nameAr: "الإمارات العربية المتحدة", exposureUsd: 620_000_000, stressLevel: 0.72, primaryDriver: "UAE Payment Switch — stress at 72%", primaryDriverAr: "مفتاح الدفع الإماراتي — الضغط عند 72%", transmissionChannel: "Payment infrastructure → banking ops → trade settlement", transmissionChannelAr: "بنية الدفع → العمليات المصرفية → تسوية التجارة" },
  { code: "KSA", name: "Saudi Arabia", nameAr: "المملكة العربية السعودية", exposureUsd: 580_000_000, stressLevel: 0.68, primaryDriver: "SAMA RTGS System — stress at 76%", primaryDriverAr: "نظام RTGS لمؤسسة النقد — الضغط عند 76%", transmissionChannel: "RTGS failure → interbank freeze → fiscal operations", transmissionChannelAr: "فشل RTGS → تجميد بين البنوك → العمليات المالية" },
  { code: "BHR", name: "Bahrain", nameAr: "البحرين", exposureUsd: 280_000_000, stressLevel: 0.58, primaryDriver: "Financial hub systems — stress at 58%", primaryDriverAr: "أنظمة المركز المالي — الضغط عند 58%", transmissionChannel: "Fintech hub → cross-border payments → correspondent banking", transmissionChannelAr: "مركز التكنولوجيا المالية → المدفوعات العابرة → البنوك المراسلة" },
  { code: "QAT", name: "Qatar", nameAr: "قطر", exposureUsd: 180_000_000, stressLevel: 0.42, primaryDriver: "QCB settlement — stress at 42%", primaryDriverAr: "تسوية مصرف قطر المركزي — الضغط عند 42%", transmissionChannel: "Cross-border settlement → LNG trade finance", transmissionChannelAr: "التسوية العابرة → تمويل تجارة الغاز المسال" },
  { code: "KWT", name: "Kuwait", nameAr: "الكويت", exposureUsd: 120_000_000, stressLevel: 0.38, primaryDriver: "CBK systems — stress at 38%", primaryDriverAr: "أنظمة بنك الكويت المركزي — الضغط عند 38%", transmissionChannel: "Payment network → banking services", transmissionChannelAr: "شبكة الدفع → الخدمات المصرفية" },
  { code: "OMN", name: "Oman", nameAr: "عُمان", exposureUsd: 60_000_000, stressLevel: 0.28, primaryDriver: "CBO digital channels — stress at 28%", primaryDriverAr: "القنوات الرقمية للبنك المركزي العماني — الضغط عند 28%", transmissionChannel: "Digital banking → merchant payments", transmissionChannelAr: "البنوك الرقمية → مدفوعات التجار" },
];

export const MOCK_CYBER_OUTCOMES = {
  baseCase: { label: "Base Case (No Intervention)", labelAr: "السيناريو الأساسي (بدون تدخل)", lossLow: 1_560_000_000, lossHigh: 2_120_000_000, recoveryDays: 21, description: "Full propagation through payment and settlement systems. Recovery dependent on system forensics and rebuild timeline.", descriptionAr: "انتشار كامل عبر أنظمة الدفع والتسوية. التعافي يعتمد على التحقيق الجنائي وإعادة البناء." } as OutcomeScenario,
  mitigatedCase: { label: "Mitigated Case (Rapid Response)", labelAr: "السيناريو المخفف (استجابة سريعة)", lossLow: 540_000_000, lossHigh: 920_000_000, recoveryDays: 10, description: "3 coordinated interventions reducing exposure by 55%. Backup settlement channels activated within 4 hours.", descriptionAr: "3 تدخلات منسقة تقلل التعرض بنسبة 55%. تفعيل قنوات تسوية احتياطية خلال 4 ساعات." } as OutcomeScenario,
  valueSaved: { low: 640_000_000, high: 1_580_000_000, description: "Estimated value preserved through rapid incident containment and backup channel activation.", descriptionAr: "القيمة المقدرة المحفوظة من خلال الاحتواء السريع وتفعيل القنوات الاحتياطية." },
};

export const MOCK_CYBER_SECTOR_DEPTH: Record<string, { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }> = {
  banking: { topDriver: "RTGS settlement halted — SAR 12B in transactions queued", secondOrderRisk: "1 recommended intervention — Deploy backup settlement channel", confidenceLow: 0.54, confidenceHigh: 0.70 },
  fintech: { topDriver: "Payment switch disruption — ATM/POS networks intermittent", secondOrderRisk: "1 recommended intervention — Activate GCC-CERT emergency response", confidenceLow: 0.60, confidenceHigh: 0.76 },
  insurance: { topDriver: "Cyber liability claims — business interruption exposure rising", secondOrderRisk: "Monitoring for secondary transmission effects", confidenceLow: 0.37, confidenceHigh: 0.53 },
};

// ══════════════════════════════════════════════════════════════════════
// 2. QATAR LNG EXPORT DISRUPTION
// ══════════════════════════════════════════════════════════════════════

export const MOCK_LNG_SCENARIO = {
  template_id: "qatar_lng_disruption",
  label: "Qatar LNG Export Disruption — Ras Laffan Complex",
  label_ar: "تعطل صادرات الغاز القطري المسال — مجمع رأس لفان",
  severity: 0.70,
  horizon_hours: 144,
  domain: "ENERGY",
  trigger_time: "2026-04-09T14:20:00Z",
};

export const MOCK_LNG_HEADLINE = {
  total_loss_usd: 3_520_000_000,
  total_nodes_impacted: 26,
  propagation_depth: 5,
  peak_day: 3,
  max_recovery_days: 35,
  average_stress: 0.59,
  affected_entities: 26,
  critical_count: 5,
  elevated_count: 9,
};

export const MOCK_LNG_GRAPH_NODES: KnowledgeGraphNode[] = [
  { id: "ras_laffan", label: "Ras Laffan Industrial City", label_ar: "مدينة رأس لفان الصناعية", layer: "infrastructure", type: "facility", weight: 0.96, lat: 25.93, lng: 51.56, sensitivity: 0.94, stress: 0.88, classification: "CRITICAL" },
  { id: "qatar_energy", label: "QatarEnergy", label_ar: "قطر للطاقة", layer: "economy", type: "corporation", weight: 0.92, lat: 25.35, lng: 51.18, sensitivity: 0.88, stress: 0.78, classification: "ELEVATED" },
  { id: "lng_carriers", label: "LNG Carrier Fleet", label_ar: "أسطول ناقلات الغاز المسال", layer: "infrastructure", type: "fleet", weight: 0.85, lat: 25.50, lng: 52.00, sensitivity: 0.82, stress: 0.72, classification: "ELEVATED" },
  { id: "north_field", label: "North Field (Gas Reserve)", label_ar: "حقل الشمال (احتياطي الغاز)", layer: "geography", type: "resource", weight: 0.94, lat: 26.10, lng: 52.00, sensitivity: 0.90, stress: 0.82, classification: "ELEVATED" },
  { id: "asian_lng_buyers", label: "Asian LNG Buyers", label_ar: "مشتري الغاز المسال الآسيويين", layer: "economy", type: "market", weight: 0.80, lat: 35.68, lng: 139.69, sensitivity: 0.78, stress: 0.65, classification: "MODERATE" },
  { id: "qcb", label: "Qatar Central Bank", label_ar: "مصرف قطر المركزي", layer: "finance", type: "central_bank", weight: 0.80, lat: 25.29, lng: 51.53, sensitivity: 0.62, stress: 0.52, classification: "GUARDED" },
  { id: "qatar_fiscal", label: "Qatar Fiscal Balance", label_ar: "الميزانية المالية القطرية", layer: "economy", type: "indicator", weight: 0.82, lat: 25.28, lng: 51.52, sensitivity: 0.75, stress: 0.58, classification: "GUARDED" },
  { id: "gcc_gas_network", label: "Dolphin Gas Pipeline", label_ar: "خط أنابيب الدلفين", layer: "infrastructure", type: "pipeline", weight: 0.78, lat: 24.80, lng: 54.00, sensitivity: 0.72, stress: 0.55, classification: "GUARDED" },
  { id: "uae_power", label: "UAE Power Generation", label_ar: "توليد الطاقة الإماراتي", layer: "economy", type: "sector", weight: 0.76, lat: 24.45, lng: 54.65, sensitivity: 0.68, stress: 0.48, classification: "GUARDED" },
  { id: "gcc_petrochemicals", label: "GCC Petrochemical Industry", label_ar: "صناعة البتروكيماويات الخليجية", layer: "economy", type: "sector", weight: 0.74, lat: 26.20, lng: 50.20, sensitivity: 0.65, stress: 0.42, classification: "GUARDED" },
];

export const MOCK_LNG_GRAPH_EDGES: KnowledgeGraphEdge[] = [
  { id: "le1", source: "ras_laffan", target: "qatar_energy", weight: 0.92, polarity: 1, label: "production halt cascade", label_ar: "سلسلة توقف الإنتاج", transmission: 0.88 },
  { id: "le2", source: "ras_laffan", target: "lng_carriers", weight: 0.88, polarity: 1, label: "loading operations suspended", label_ar: "تعليق عمليات التحميل", transmission: 0.82 },
  { id: "le3", source: "north_field", target: "ras_laffan", weight: 0.94, polarity: 1, label: "upstream supply constraint", label_ar: "قيود الإمداد الأولي", transmission: 0.90 },
  { id: "le4", source: "qatar_energy", target: "asian_lng_buyers", weight: 0.78, polarity: 1, label: "contract delivery failure", label_ar: "فشل تسليم العقود", transmission: 0.72 },
  { id: "le5", source: "qatar_energy", target: "qatar_fiscal", weight: 0.82, polarity: 1, label: "revenue stream disruption", label_ar: "تعطل تدفق الإيرادات", transmission: 0.75 },
  { id: "le6", source: "qatar_fiscal", target: "qcb", weight: 0.70, polarity: 1, label: "fiscal stress → monetary policy", label_ar: "ضغط مالي → السياسة النقدية", transmission: 0.62 },
  { id: "le7", source: "ras_laffan", target: "gcc_gas_network", weight: 0.75, polarity: 1, label: "pipeline supply reduction", label_ar: "تخفيض إمداد خط الأنابيب", transmission: 0.68 },
  { id: "le8", source: "gcc_gas_network", target: "uae_power", weight: 0.68, polarity: 1, label: "gas-to-power constraint", label_ar: "قيود الغاز لتوليد الطاقة", transmission: 0.58 },
];

export const MOCK_LNG_CAUSAL_CHAIN: CausalStep[] = [
  { step: 1, entity_id: "ras_laffan", entity_label: "Ras Laffan Industrial City", entity_label_ar: "مدينة رأس لفان الصناعية", event: "Fire at Train 4 liquefaction unit — facility-wide safety shutdown activated", event_ar: "حريق في وحدة الإسالة رقم 4 — تفعيل الإغلاق الأمني على مستوى المنشأة", impact_usd: 0, stress_delta: 0.88, mechanism: "direct_shock" },
  { step: 2, entity_id: "qatar_energy", entity_label: "QatarEnergy", entity_label_ar: "قطر للطاقة", event: "LNG production drops 77 MTPA → 28 MTPA — force majeure declared on long-term contracts", event_ar: "انخفاض إنتاج الغاز المسال من 77 إلى 28 مليون طن سنوياً — إعلان القوة القاهرة", impact_usd: 1_200_000_000, stress_delta: 0.78, mechanism: "supply_disruption" },
  { step: 3, entity_id: "asian_lng_buyers", entity_label: "Asian LNG Buyers", entity_label_ar: "مشتري الغاز المسال الآسيويين", event: "Spot LNG prices surge 45% — Japan/Korea activate strategic reserves", event_ar: "ارتفاع أسعار الغاز الفورية 45% — اليابان وكوريا تفعل الاحتياطيات الاستراتيجية", impact_usd: 850_000_000, stress_delta: 0.65, mechanism: "price_transmission" },
  { step: 4, entity_id: "qatar_fiscal", entity_label: "Qatar Fiscal Balance", entity_label_ar: "الميزانية المالية القطرية", event: "Monthly LNG revenue shortfall of QAR 8.2B — fiscal surplus erodes", event_ar: "نقص الإيرادات الشهرية 8.2 مليار ريال قطري — تآكل الفائض المالي", impact_usd: 720_000_000, stress_delta: 0.58, mechanism: "fiscal_transmission" },
  { step: 5, entity_id: "uae_power", entity_label: "UAE Power Generation", entity_label_ar: "توليد الطاقة الإماراتي", event: "Dolphin pipeline flow reduced 40% — UAE activates oil-fired backup generation", event_ar: "انخفاض تدفق خط الدلفين 40% — الإمارات تفعل التوليد الاحتياطي بالنفط", impact_usd: 380_000_000, stress_delta: 0.48, mechanism: "supply_chain" },
];

export const MOCK_LNG_SECTOR_IMPACTS: SectorImpact[] = [
  { sector: "infrastructure", sectorLabel: "Energy Infrastructure", avgImpact: 0.78, maxImpact: 0.88, nodeCount: 4, topNode: "ras_laffan", color: "#8C2318" },
  { sector: "economy", sectorLabel: "Energy Markets", avgImpact: 0.62, maxImpact: 0.78, nodeCount: 5, topNode: "qatar_energy", color: "#8B6914" },
  { sector: "finance", sectorLabel: "Fiscal & Monetary", avgImpact: 0.50, maxImpact: 0.52, nodeCount: 2, topNode: "qcb", color: "#0C6B58" },
];

export const MOCK_LNG_SECTOR_ROLLUPS = {
  energy: { aggregate_stress: 0.74, total_loss: 1_650_000_000, node_count: 6, classification: "ELEVATED" as const },
  banking: { aggregate_stress: 0.45, total_loss: 520_000_000, node_count: 4, classification: "GUARDED" as const },
  insurance: { aggregate_stress: 0.52, total_loss: 380_000_000, node_count: 3, classification: "GUARDED" as const },
  trade: { aggregate_stress: 0.58, total_loss: 620_000_000, node_count: 4, classification: "GUARDED" as const },
  fintech: { aggregate_stress: 0.28, total_loss: 80_000_000, node_count: 2, classification: "LOW" as const },
};

export const MOCK_LNG_DECISION_ACTIONS: DecisionActionV2[] = [
  {
    id: "lda_1", action: "Activate QatarEnergy emergency production rebalancing across remaining trains", action_ar: "تفعيل إعادة توازن الإنتاج الطارئة عبر وحدات الإسالة المتبقية",
    sector: "energy", owner: "QatarEnergy", urgency: 94, value: 90,
    regulatory_risk: 0.12, priority: 95, target_node_id: "ras_laffan",
    target_lat: 25.93, target_lng: 51.56, loss_avoided_usd: 920_000_000,
    cost_usd: 65_000_000, confidence: 0.88,
  },
  {
    id: "lda_2", action: "Invoke LNG swap agreements with Oman LNG and Abu Dhabi Gas", action_ar: "تفعيل اتفاقيات مبادلة الغاز المسال مع عمان للغاز وأبوظبي للغاز",
    sector: "energy", owner: "Ministry of Energy", urgency: 88, value: 82,
    regulatory_risk: 0.18, priority: 86, target_node_id: "lng_carriers",
    target_lat: 25.50, target_lng: 52.00, loss_avoided_usd: 620_000_000,
    cost_usd: 95_000_000, confidence: 0.81,
  },
  {
    id: "lda_3", action: "Accelerate Dolphin pipeline flow to offset UAE power generation gap", action_ar: "تسريع تدفق خط أنابيب الدلفين لتعويض فجوة توليد الطاقة الإماراتية",
    sector: "energy", owner: "Dolphin Energy", urgency: 82, value: 75,
    regulatory_risk: 0.22, priority: 78, target_node_id: "gcc_gas_network",
    target_lat: 24.80, target_lng: 54.00, loss_avoided_usd: 380_000_000,
    cost_usd: 42_000_000, confidence: 0.79,
  },
  {
    id: "lda_4", action: "Deploy QIA fiscal stabilization buffer to cover revenue shortfall", action_ar: "نشر صندوق الاستقرار المالي لجهاز قطر للاستثمار لتغطية نقص الإيرادات",
    sector: "government", owner: "Qatar Investment Authority", urgency: 75, value: 80,
    regulatory_risk: 0.15, priority: 76, target_node_id: "qatar_fiscal",
    target_lat: 25.28, target_lng: 51.52, loss_avoided_usd: 720_000_000,
    cost_usd: 20_000_000, confidence: 0.86,
  },
];

export const MOCK_LNG_EXPLANATION = {
  narrative_en: "A fire at the Ras Laffan Train 4 liquefaction unit triggers a facility-wide safety shutdown, reducing Qatar's LNG production from 77 MTPA to 28 MTPA. The disruption propagates through five channels: (1) force majeure declared on long-term Asian supply contracts, (2) spot LNG prices surge 45% within 72 hours, (3) Dolphin pipeline flow to UAE reduced 40%, forcing oil-fired backup generation, (4) Qatar's fiscal surplus erodes with QAR 8.2B monthly revenue shortfall, and (5) GCC petrochemical feedstock supplies constrained. Total estimated loss reaches $3.52B over the 6-day horizon.",
  narrative_ar: "حريق في وحدة الإسالة رقم 4 في رأس لفان يؤدي إلى إغلاق أمني شامل للمنشأة، مما يخفض إنتاج قطر من الغاز المسال من 77 إلى 28 مليون طن سنوياً.",
  methodology: "Institutional macro-financial intelligence: LNG supply chain model with contract obligation mapping. 26-node energy-financial knowledge graph with 52 causal edges. Confidence: Monte Carlo 10K iterations.",
  confidence: 0.86,
  total_steps: 5,
};

export const MOCK_LNG_TRUST = {
  trace_id: "trc_20260409_142000_lng",
  audit_id: "aud_cc_004",
  audit_hash: "sha256:d7g5f1b24c6e0d39g8f5c4b7e2d1a0c3f6e9b2a5d8c1f4e7b0a3d6c9f2e5b8a1",
  model_version: "io-v4.0.0",
  pipeline_version: "unified-v2.1",
  confidence_score: 0.86,
  data_sources: ["QatarEnergy Production Data", "Platts LNG Assessment", "Dolphin Pipeline Telemetry", "QCB Open Data", "Asian Spot Market Feed"],
  stages_completed: ["signal_ingest", "graph_activation", "causal_trace", "propagation", "physics", "math", "sector_stress", "decision_gen", "explanation"],
  warnings: ["Ras Laffan telemetry: delayed 20min", "Asian spot price: estimated from JKM benchmark"],
};

export const MOCK_LNG_LOSS_RANGE = { low: 3_010_000_000, mid: 3_520_000_000, high: 4_030_000_000, confidence_pct: 90 };
export const MOCK_LNG_DECISION_DEADLINE = new Date(Date.now() + 36 * 3_600_000).toISOString();

export const MOCK_LNG_ASSUMPTIONS: string[] = [
  "Fire contained to Train 4 — no structural damage to adjacent trains",
  "Remaining trains (1–3, 5–7) operate at 85% capacity during recovery",
  "Force majeure accepted by long-term contract buyers within 48 hours",
  "Dolphin pipeline maintains minimum 60% flow to UAE",
  "Qatar Investment Authority fiscal buffer sufficient for 6-month revenue gap",
];

export const MOCK_LNG_COUNTRY_EXPOSURES: CountryExposureEntry[] = [
  { code: "QAT", name: "Qatar", nameAr: "قطر", exposureUsd: 1_920_000_000, stressLevel: 0.78, primaryDriver: "QatarEnergy — stress at 78%", primaryDriverAr: "قطر للطاقة — الضغط عند 78%", transmissionChannel: "LNG production → fiscal revenue → sovereign reserves", transmissionChannelAr: "إنتاج الغاز المسال → الإيرادات المالية → الاحتياطيات السيادية" },
  { code: "UAE", name: "United Arab Emirates", nameAr: "الإمارات العربية المتحدة", exposureUsd: 680_000_000, stressLevel: 0.55, primaryDriver: "UAE Power Generation — stress at 48%", primaryDriverAr: "توليد الطاقة الإماراتي — الضغط عند 48%", transmissionChannel: "Dolphin pipeline → gas-to-power → industrial output", transmissionChannelAr: "خط الدلفين → الغاز لتوليد الطاقة → الإنتاج الصناعي" },
  { code: "KSA", name: "Saudi Arabia", nameAr: "المملكة العربية السعودية", exposureUsd: 420_000_000, stressLevel: 0.42, primaryDriver: "Petrochemical feedstock — stress at 42%", primaryDriverAr: "مواد البتروكيماويات الأولية — الضغط عند 42%", transmissionChannel: "Gas supply → petrochemicals → export earnings", transmissionChannelAr: "إمداد الغاز → البتروكيماويات → إيرادات التصدير" },
  { code: "OMN", name: "Oman", nameAr: "عُمان", exposureUsd: 280_000_000, stressLevel: 0.38, primaryDriver: "Oman LNG swap obligation — stress at 38%", primaryDriverAr: "التزام مبادلة عمان للغاز — الضغط عند 38%", transmissionChannel: "LNG swap activation → production rebalancing", transmissionChannelAr: "تفعيل المبادلة → إعادة توازن الإنتاج" },
  { code: "KWT", name: "Kuwait", nameAr: "الكويت", exposureUsd: 140_000_000, stressLevel: 0.32, primaryDriver: "Gas import dependency — stress at 32%", primaryDriverAr: "الاعتماد على استيراد الغاز — الضغط عند 32%", transmissionChannel: "LNG spot imports → power generation costs", transmissionChannelAr: "واردات الغاز الفورية → تكاليف توليد الطاقة" },
  { code: "BHR", name: "Bahrain", nameAr: "البحرين", exposureUsd: 80_000_000, stressLevel: 0.25, primaryDriver: "Regional gas price — stress at 25%", primaryDriverAr: "سعر الغاز الإقليمي — الضغط عند 25%", transmissionChannel: "Gas pricing → industrial costs", transmissionChannelAr: "تسعير الغاز → التكاليف الصناعية" },
];

export const MOCK_LNG_OUTCOMES = {
  baseCase: { label: "Base Case (No Intervention)", labelAr: "السيناريو الأساسي (بدون تدخل)", lossLow: 3_010_000_000, lossHigh: 4_030_000_000, recoveryDays: 35, description: "Full disruption to Qatar LNG supply chain. Recovery dependent on facility repair timeline and contract renegotiation.", descriptionAr: "تعطل كامل لسلسلة إمداد الغاز المسال القطري. التعافي يعتمد على جدول إصلاح المنشأة." } as OutcomeScenario,
  mitigatedCase: { label: "Mitigated Case (Coordinated Response)", labelAr: "السيناريو المخفف (استجابة منسقة)", lossLow: 1_080_000_000, lossHigh: 1_750_000_000, recoveryDays: 18, description: "4 coordinated interventions reducing exposure by 55%. LNG swap agreements and fiscal buffer deployed.", descriptionAr: "4 تدخلات منسقة تقلل التعرض بنسبة 55%. تفعيل اتفاقيات المبادلة والحاجز المالي." } as OutcomeScenario,
  valueSaved: { low: 1_260_000_000, high: 2_950_000_000, description: "Estimated value preserved through production rebalancing, LNG swaps, and fiscal stabilization.", descriptionAr: "القيمة المقدرة المحفوظة من خلال إعادة توازن الإنتاج ومبادلات الغاز والاستقرار المالي." },
};

export const MOCK_LNG_SECTOR_DEPTH: Record<string, { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }> = {
  energy: { topDriver: "LNG production drops 77→28 MTPA — force majeure on long-term contracts", secondOrderRisk: "2 recommended interventions — Production rebalancing + LNG swap activation", confidenceLow: 0.66, confidenceHigh: 0.82 },
  banking: { topDriver: "Qatar fiscal surplus erodes — central bank reserves under pressure", secondOrderRisk: "1 recommended intervention — QIA fiscal stabilization buffer", confidenceLow: 0.37, confidenceHigh: 0.53 },
  trade: { topDriver: "LNG spot prices surge 45% — Asian buyers activate strategic reserves", secondOrderRisk: "Supply rebalancing across alternative LNG producers", confidenceLow: 0.50, confidenceHigh: 0.66 },
};

// ══════════════════════════════════════════════════════════════════════
// 3. GCC INSURANCE RESERVE SHORTFALL
// ══════════════════════════════════════════════════════════════════════

export const MOCK_INSURANCE_SCENARIO = {
  template_id: "gcc_insurance_reserve_shortfall",
  label: "GCC Insurance Reserve Shortfall — IFRS 17 Compliance Crisis",
  label_ar: "عجز احتياطيات التأمين الخليجي — أزمة الامتثال لمعيار IFRS 17",
  severity: 0.62,
  horizon_hours: 168,
  domain: "INSURANCE",
  trigger_time: "2026-04-11T08:00:00Z",
};

export const MOCK_INSURANCE_HEADLINE = {
  total_loss_usd: 1_420_000_000,
  total_nodes_impacted: 18,
  propagation_depth: 4,
  peak_day: 4,
  max_recovery_days: 56,
  average_stress: 0.51,
  affected_entities: 18,
  critical_count: 2,
  elevated_count: 6,
};

export const MOCK_INSURANCE_GRAPH_NODES: KnowledgeGraphNode[] = [
  { id: "gcc_reinsurance", label: "GCC Reinsurance Pool", label_ar: "مجمع إعادة التأمين الخليجي", layer: "finance", type: "sector", weight: 0.92, lat: 25.20, lng: 55.27, sensitivity: 0.90, stress: 0.82, classification: "ELEVATED" },
  { id: "marine_pi", label: "Marine P&I Underwriters", label_ar: "ضامنو التأمين البحري", layer: "finance", type: "sector", weight: 0.86, lat: 25.10, lng: 55.18, sensitivity: 0.84, stress: 0.74, classification: "ELEVATED" },
  { id: "health_claims", label: "Health Insurance Claims Pool", label_ar: "مجمع مطالبات التأمين الصحي", layer: "finance", type: "sector", weight: 0.84, lat: 24.69, lng: 46.69, sensitivity: 0.78, stress: 0.68, classification: "ELEVATED" },
  { id: "ifrs17_reserves", label: "IFRS 17 Reserve Requirements", label_ar: "متطلبات احتياطي IFRS 17", layer: "finance", type: "regulation", weight: 0.90, lat: 24.49, lng: 54.37, sensitivity: 0.88, stress: 0.78, classification: "ELEVATED" },
  { id: "insurance_authority_uae", label: "UAE Insurance Authority", label_ar: "هيئة التأمين الإماراتية", layer: "finance", type: "regulator", weight: 0.82, lat: 24.45, lng: 54.65, sensitivity: 0.72, stress: 0.52, classification: "GUARDED" },
  { id: "sama_insurance", label: "SAMA Insurance Supervision", label_ar: "إشراف مؤسسة النقد على التأمين", layer: "finance", type: "regulator", weight: 0.80, lat: 24.71, lng: 46.67, sensitivity: 0.70, stress: 0.48, classification: "GUARDED" },
  { id: "construction_insurance", label: "Construction & Property Insurance", label_ar: "تأمين البناء والعقارات", layer: "economy", type: "sector", weight: 0.78, lat: 25.25, lng: 55.30, sensitivity: 0.72, stress: 0.58, classification: "GUARDED" },
  { id: "rating_agencies", label: "Insurance Rating Agencies", label_ar: "وكالات التصنيف التأميني", layer: "finance", type: "institution", weight: 0.75, lat: 25.30, lng: 55.35, sensitivity: 0.68, stress: 0.45, classification: "GUARDED" },
];

export const MOCK_INSURANCE_GRAPH_EDGES: KnowledgeGraphEdge[] = [
  { id: "ie1", source: "gcc_reinsurance", target: "marine_pi", weight: 0.88, polarity: 1, label: "reinsurance capacity squeeze", label_ar: "ضغط طاقة إعادة التأمين", transmission: 0.82 },
  { id: "ie2", source: "ifrs17_reserves", target: "gcc_reinsurance", weight: 0.85, polarity: 1, label: "reserve adequacy gap", label_ar: "فجوة كفاية الاحتياطي", transmission: 0.78 },
  { id: "ie3", source: "gcc_reinsurance", target: "health_claims", weight: 0.75, polarity: 1, label: "claims capacity constraint", label_ar: "قيود طاقة المطالبات", transmission: 0.68 },
  { id: "ie4", source: "marine_pi", target: "insurance_authority_uae", weight: 0.70, polarity: 1, label: "regulatory intervention trigger", label_ar: "مؤشر التدخل التنظيمي", transmission: 0.62 },
  { id: "ie5", source: "gcc_reinsurance", target: "rating_agencies", weight: 0.72, polarity: 1, label: "rating downgrade pressure", label_ar: "ضغط تخفيض التصنيف", transmission: 0.65 },
  { id: "ie6", source: "health_claims", target: "construction_insurance", weight: 0.65, polarity: 1, label: "cross-line reserve reallocation", label_ar: "إعادة توزيع الاحتياطي عبر الفروع", transmission: 0.58 },
];

export const MOCK_INSURANCE_CAUSAL_CHAIN: CausalStep[] = [
  { step: 1, entity_id: "ifrs17_reserves", entity_label: "IFRS 17 Reserve Requirements", entity_label_ar: "متطلبات احتياطي IFRS 17", event: "IFRS 17 implementation reveals 23% reserve shortfall across GCC insurers", event_ar: "تطبيق IFRS 17 يكشف عجز احتياطي بنسبة 23% لدى شركات التأمين الخليجية", impact_usd: 0, stress_delta: 0.78, mechanism: "regulatory_disclosure" },
  { step: 2, entity_id: "gcc_reinsurance", entity_label: "GCC Reinsurance Pool", entity_label_ar: "مجمع إعادة التأمين الخليجي", event: "Reinsurance capacity drops 35% — treaty renewals repriced upward", event_ar: "انخفاض طاقة إعادة التأمين 35% — إعادة تسعير تجديدات المعاهدات", impact_usd: 480_000_000, stress_delta: 0.82, mechanism: "capacity_constraint" },
  { step: 3, entity_id: "marine_pi", entity_label: "Marine P&I Underwriters", entity_label_ar: "ضامنو التأمين البحري", event: "Marine P&I premiums spike 60% — shipping companies face uninsured exposure", event_ar: "ارتفاع أقساط التأمين البحري 60% — شركات الشحن تواجه تعرض غير مؤمن", impact_usd: 350_000_000, stress_delta: 0.74, mechanism: "premium_transmission" },
  { step: 4, entity_id: "health_claims", entity_label: "Health Insurance Claims Pool", entity_label_ar: "مجمع مطالبات التأمين الصحي", event: "Health insurance reserves reallocated — claims settlement delays exceed 90 days", event_ar: "إعادة تخصيص احتياطيات التأمين الصحي — تأخير تسوية المطالبات يتجاوز 90 يوماً", impact_usd: 320_000_000, stress_delta: 0.68, mechanism: "reserve_reallocation" },
  { step: 5, entity_id: "rating_agencies", entity_label: "Insurance Rating Agencies", entity_label_ar: "وكالات التصنيف التأميني", event: "AM Best downgrades 4 GCC insurers — market confidence erodes", event_ar: "AM Best تخفض تصنيف 4 شركات تأمين خليجية — تآكل ثقة السوق", impact_usd: 270_000_000, stress_delta: 0.45, mechanism: "credit_transmission" },
];

export const MOCK_INSURANCE_SECTOR_IMPACTS: SectorImpact[] = [
  { sector: "finance", sectorLabel: "Insurance & Reinsurance", avgImpact: 0.68, maxImpact: 0.82, nodeCount: 6, topNode: "gcc_reinsurance", color: "#0C6B58" },
  { sector: "economy", sectorLabel: "Construction & Property", avgImpact: 0.48, maxImpact: 0.58, nodeCount: 3, topNode: "construction_insurance", color: "#8B6914" },
];

export const MOCK_INSURANCE_SECTOR_ROLLUPS = {
  insurance: { aggregate_stress: 0.72, total_loss: 680_000_000, node_count: 5, classification: "ELEVATED" as const },
  banking: { aggregate_stress: 0.42, total_loss: 280_000_000, node_count: 4, classification: "GUARDED" as const },
  trade: { aggregate_stress: 0.48, total_loss: 220_000_000, node_count: 3, classification: "GUARDED" as const },
  energy: { aggregate_stress: 0.35, total_loss: 140_000_000, node_count: 3, classification: "LOW" as const },
  fintech: { aggregate_stress: 0.22, total_loss: 60_000_000, node_count: 2, classification: "LOW" as const },
};

export const MOCK_INSURANCE_DECISION_ACTIONS: DecisionActionV2[] = [
  {
    id: "ida_1", action: "Deploy emergency reinsurance backstop via GCC sovereign wealth funds", action_ar: "نشر ضمان إعادة تأمين طارئ عبر صناديق الثروة السيادية الخليجية",
    sector: "insurance", owner: "Insurance Authority + SWFs", urgency: 88, value: 85,
    regulatory_risk: 0.18, priority: 90, target_node_id: "gcc_reinsurance",
    target_lat: 25.20, target_lng: 55.27, loss_avoided_usd: 480_000_000,
    cost_usd: 55_000_000, confidence: 0.84,
  },
  {
    id: "ida_2", action: "Grant 12-month IFRS 17 compliance extension for small/mid-tier insurers", action_ar: "منح تمديد 12 شهراً للامتثال لـ IFRS 17 لشركات التأمين الصغيرة والمتوسطة",
    sector: "insurance", owner: "SAMA + UAE Insurance Authority", urgency: 82, value: 78,
    regulatory_risk: 0.25, priority: 80, target_node_id: "ifrs17_reserves",
    target_lat: 24.49, target_lng: 54.37, loss_avoided_usd: 320_000_000,
    cost_usd: 12_000_000, confidence: 0.82,
  },
  {
    id: "ida_3", action: "Activate emergency health claims processing fund to clear 90-day backlog", action_ar: "تفعيل صندوق طوارئ لمعالجة مطالبات التأمين الصحي لتصفية التراكم",
    sector: "insurance", owner: "Ministry of Health + Insurers", urgency: 78, value: 72,
    regulatory_risk: 0.20, priority: 75, target_node_id: "health_claims",
    target_lat: 24.69, target_lng: 46.69, loss_avoided_usd: 320_000_000,
    cost_usd: 35_000_000, confidence: 0.80,
  },
];

export const MOCK_INSURANCE_EXPLANATION = {
  narrative_en: "Implementation of IFRS 17 accounting standards reveals a 23% reserve shortfall across GCC insurance companies, triggering a sector-wide confidence crisis. The shock propagates through four channels: (1) reinsurance capacity drops 35% as treaty renewals are repriced, (2) marine P&I premiums spike 60% creating uninsured shipping exposure, (3) health insurance claims settlement delays exceed 90 days due to reserve reallocation, and (4) AM Best downgrades 4 major GCC insurers. Total estimated loss reaches $1.42B over the 7-day horizon.",
  narrative_ar: "تطبيق معايير IFRS 17 المحاسبية يكشف عجز احتياطي بنسبة 23% لدى شركات التأمين الخليجية، مما يؤدي إلى أزمة ثقة على مستوى القطاع.",
  methodology: "Institutional macro-financial intelligence: Insurance solvency stress model with IFRS 17 compliance framework. 18-node GCC insurance knowledge graph with 36 causal edges. Confidence: Monte Carlo 10K iterations.",
  confidence: 0.81,
  total_steps: 5,
};

export const MOCK_INSURANCE_TRUST = {
  trace_id: "trc_20260411_080000_insurance",
  audit_id: "aud_cc_005",
  audit_hash: "sha256:e8h6g2c35d7f1e40h9g6d5c8f3e2b1a4d7g0c3f6e9b2a5d8c1f4e7b0a3d6c9f2",
  model_version: "io-v4.0.0",
  pipeline_version: "unified-v2.1",
  confidence_score: 0.81,
  data_sources: ["SAMA Insurance Data", "UAE IA Filings", "AM Best Ratings", "Lloyd's Market Data", "IFRS 17 Compliance Reports"],
  stages_completed: ["signal_ingest", "graph_activation", "causal_trace", "propagation", "physics", "math", "sector_stress", "decision_gen", "explanation"],
  warnings: ["IFRS 17 reserve data: quarterly lag", "Reinsurance pricing: indicative from treaty brokers"],
};

export const MOCK_INSURANCE_LOSS_RANGE = { low: 1_190_000_000, mid: 1_420_000_000, high: 1_650_000_000, confidence_pct: 90 };
export const MOCK_INSURANCE_DECISION_DEADLINE = new Date(Date.now() + 72 * 3_600_000).toISOString();

export const MOCK_INSURANCE_ASSUMPTIONS: string[] = [
  "Reserve shortfall is accounting-driven (IFRS 17 transition), not claims-driven",
  "No concurrent catastrophic loss event increasing claims load",
  "GCC sovereign wealth funds willing to provide backstop capital",
  "Rating agency response follows standard 90-day review cycle",
  "Health claims settlement delays do not trigger regulatory intervention",
];

export const MOCK_INSURANCE_COUNTRY_EXPOSURES: CountryExposureEntry[] = [
  { code: "UAE", name: "United Arab Emirates", nameAr: "الإمارات العربية المتحدة", exposureUsd: 520_000_000, stressLevel: 0.68, primaryDriver: "UAE Insurance Authority — reserve gap at 28%", primaryDriverAr: "هيئة التأمين الإماراتية — فجوة احتياطي 28%", transmissionChannel: "Reserve shortfall → premium repricing → market confidence", transmissionChannelAr: "عجز الاحتياطي → إعادة تسعير الأقساط → ثقة السوق" },
  { code: "KSA", name: "Saudi Arabia", nameAr: "المملكة العربية السعودية", exposureUsd: 380_000_000, stressLevel: 0.58, primaryDriver: "SAMA insurance supervision — compliance gap at 21%", primaryDriverAr: "إشراف مؤسسة النقد — فجوة امتثال 21%", transmissionChannel: "Health claims → reserve reallocation → solvency pressure", transmissionChannelAr: "مطالبات صحية → إعادة تخصيص → ضغط الملاءة" },
  { code: "BHR", name: "Bahrain", nameAr: "البحرين", exposureUsd: 220_000_000, stressLevel: 0.52, primaryDriver: "CBB insurance hub — captive market stress", primaryDriverAr: "مركز التأمين في البحرين — ضغط السوق الأسير", transmissionChannel: "Reinsurance capacity → captive market → financial hub", transmissionChannelAr: "طاقة إعادة التأمين → السوق الأسير → المركز المالي" },
  { code: "QAT", name: "Qatar", nameAr: "قطر", exposureUsd: 140_000_000, stressLevel: 0.42, primaryDriver: "Marine insurance exposure — P&I repricing", primaryDriverAr: "تعرض التأمين البحري — إعادة تسعير P&I", transmissionChannel: "Marine premiums → shipping costs → trade finance", transmissionChannelAr: "أقساط البحري → تكاليف الشحن → تمويل التجارة" },
  { code: "KWT", name: "Kuwait", nameAr: "الكويت", exposureUsd: 100_000_000, stressLevel: 0.35, primaryDriver: "Construction insurance — project delays", primaryDriverAr: "تأمين البناء — تأخير المشاريع", transmissionChannel: "Premium increases → project cost overruns", transmissionChannelAr: "زيادة الأقساط → تجاوز تكاليف المشاريع" },
  { code: "OMN", name: "Oman", nameAr: "عُمان", exposureUsd: 60_000_000, stressLevel: 0.28, primaryDriver: "CBO insurance sector — limited reinsurance access", primaryDriverAr: "قطاع التأمين العماني — وصول محدود لإعادة التأمين", transmissionChannel: "Reinsurance costs → local premium inflation", transmissionChannelAr: "تكاليف إعادة التأمين → تضخم الأقساط المحلية" },
];

export const MOCK_INSURANCE_OUTCOMES = {
  baseCase: { label: "Base Case (No Intervention)", labelAr: "السيناريو الأساسي (بدون تدخل)", lossLow: 1_190_000_000, lossHigh: 1_650_000_000, recoveryDays: 56, description: "Full insurance sector repricing. Recovery dependent on reserve restoration and reinsurance market stabilization.", descriptionAr: "إعادة تسعير كاملة لقطاع التأمين. التعافي يعتمد على استعادة الاحتياطيات واستقرار سوق إعادة التأمين." } as OutcomeScenario,
  mitigatedCase: { label: "Mitigated Case (Coordinated Response)", labelAr: "السيناريو المخفف (استجابة منسقة)", lossLow: 420_000_000, lossHigh: 680_000_000, recoveryDays: 28, description: "3 coordinated interventions reducing exposure by 55%. Sovereign backstop and compliance extension stabilize sector.", descriptionAr: "3 تدخلات منسقة تقلل التعرض بنسبة 55%. الضمان السيادي وتمديد الامتثال يستقران القطاع." } as OutcomeScenario,
  valueSaved: { low: 510_000_000, high: 1_230_000_000, description: "Estimated value preserved through reinsurance backstop, compliance extension, and claims fund activation.", descriptionAr: "القيمة المقدرة المحفوظة من خلال ضمان إعادة التأمين وتمديد الامتثال وتفعيل صندوق المطالبات." },
};

export const MOCK_INSURANCE_SECTOR_DEPTH: Record<string, { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }> = {
  insurance: { topDriver: "IFRS 17 reveals 23% reserve shortfall — reinsurance capacity drops 35%", secondOrderRisk: "2 recommended interventions — Sovereign backstop + Compliance extension", confidenceLow: 0.64, confidenceHigh: 0.80 },
  banking: { topDriver: "Insurance sector stress transmits to banking via credit insurance exposure", secondOrderRisk: "Monitoring for secondary effects on trade finance guarantees", confidenceLow: 0.34, confidenceHigh: 0.50 },
  trade: { topDriver: "Marine P&I premium spike 60% — uninsured shipping exposure rises", secondOrderRisk: "Monitoring for trade flow disruption from premium repricing", confidenceLow: 0.40, confidenceHigh: 0.56 },
};

// ══════════════════════════════════════════════════════════════════════
// 4. GCC FINTECH PAYMENT SYSTEM OUTAGE
// ══════════════════════════════════════════════════════════════════════

export const MOCK_FINTECH_SCENARIO = {
  template_id: "gcc_fintech_payment_outage",
  label: "GCC Fintech Payment System Outage — Digital Infrastructure",
  label_ar: "انقطاع نظام الدفع في التكنولوجيا المالية الخليجية — البنية التحتية الرقمية",
  severity: 0.58,
  horizon_hours: 72,
  domain: "FINTECH",
  trigger_time: "2026-04-13T11:15:00Z",
};

export const MOCK_FINTECH_HEADLINE = {
  total_loss_usd: 920_000_000,
  total_nodes_impacted: 16,
  propagation_depth: 3,
  peak_day: 1,
  max_recovery_days: 14,
  average_stress: 0.48,
  affected_entities: 16,
  critical_count: 2,
  elevated_count: 5,
};

export const MOCK_FINTECH_GRAPH_NODES: KnowledgeGraphNode[] = [
  { id: "payment_gateway", label: "GCC Payment Gateway Hub", label_ar: "مركز بوابة الدفع الخليجي", layer: "infrastructure", type: "system", weight: 0.92, lat: 25.20, lng: 55.27, sensitivity: 0.90, stress: 0.82, classification: "ELEVATED" },
  { id: "mobile_wallets", label: "Mobile Wallet Networks", label_ar: "شبكات المحافظ المحمولة", layer: "infrastructure", type: "platform", weight: 0.86, lat: 24.69, lng: 46.69, sensitivity: 0.84, stress: 0.75, classification: "ELEVATED" },
  { id: "merchant_pos", label: "Merchant POS Network", label_ar: "شبكة نقاط البيع التجارية", layer: "economy", type: "network", weight: 0.84, lat: 24.49, lng: 54.37, sensitivity: 0.80, stress: 0.68, classification: "ELEVATED" },
  { id: "cross_border_remit", label: "Cross-Border Remittance", label_ar: "التحويلات العابرة للحدود", layer: "finance", type: "service", weight: 0.80, lat: 25.30, lng: 55.30, sensitivity: 0.76, stress: 0.62, classification: "MODERATE" },
  { id: "ecommerce_platforms", label: "E-Commerce Platforms", label_ar: "منصات التجارة الإلكترونية", layer: "economy", type: "platform", weight: 0.78, lat: 25.25, lng: 55.25, sensitivity: 0.72, stress: 0.55, classification: "GUARDED" },
  { id: "central_bank_rtgs", label: "Central Bank RTGS Fallback", label_ar: "نظام RTGS الاحتياطي للبنك المركزي", layer: "finance", type: "system", weight: 0.88, lat: 24.71, lng: 46.67, sensitivity: 0.65, stress: 0.42, classification: "GUARDED" },
  { id: "sme_merchants", label: "SME Merchant Ecosystem", label_ar: "منظومة التجار المتوسطين والصغار", layer: "economy", type: "sector", weight: 0.75, lat: 25.10, lng: 55.15, sensitivity: 0.70, stress: 0.52, classification: "GUARDED" },
  { id: "consumer_spending", label: "Consumer Spending Index", label_ar: "مؤشر الإنفاق الاستهلاكي", layer: "economy", type: "indicator", weight: 0.72, lat: 24.45, lng: 54.65, sensitivity: 0.68, stress: 0.45, classification: "GUARDED" },
];

export const MOCK_FINTECH_GRAPH_EDGES: KnowledgeGraphEdge[] = [
  { id: "fe1", source: "payment_gateway", target: "mobile_wallets", weight: 0.88, polarity: 1, label: "payment routing failure", label_ar: "فشل توجيه الدفع", transmission: 0.82 },
  { id: "fe2", source: "payment_gateway", target: "merchant_pos", weight: 0.85, polarity: 1, label: "POS transaction failure", label_ar: "فشل معاملات نقاط البيع", transmission: 0.78 },
  { id: "fe3", source: "mobile_wallets", target: "cross_border_remit", weight: 0.72, polarity: 1, label: "remittance channel blocked", label_ar: "حجب قناة التحويلات", transmission: 0.65 },
  { id: "fe4", source: "merchant_pos", target: "sme_merchants", weight: 0.75, polarity: 1, label: "revenue disruption", label_ar: "تعطل الإيرادات", transmission: 0.68 },
  { id: "fe5", source: "payment_gateway", target: "ecommerce_platforms", weight: 0.78, polarity: 1, label: "checkout failure cascade", label_ar: "سلسلة فشل الدفع", transmission: 0.72 },
  { id: "fe6", source: "sme_merchants", target: "consumer_spending", weight: 0.62, polarity: 1, label: "spending freeze", label_ar: "تجميد الإنفاق", transmission: 0.55 },
];

export const MOCK_FINTECH_CAUSAL_CHAIN: CausalStep[] = [
  { step: 1, entity_id: "payment_gateway", entity_label: "GCC Payment Gateway Hub", entity_label_ar: "مركز بوابة الدفع الخليجي", event: "Core payment gateway suffers cascading failure — 85% of digital transactions blocked", event_ar: "بوابة الدفع الأساسية تعاني من فشل متتالي — حجب 85% من المعاملات الرقمية", impact_usd: 0, stress_delta: 0.82, mechanism: "system_failure" },
  { step: 2, entity_id: "mobile_wallets", entity_label: "Mobile Wallet Networks", entity_label_ar: "شبكات المحافظ المحمولة", event: "Apple Pay, STC Pay, and regional wallet services fail — 12M users affected", event_ar: "فشل خدمات آبل باي وSTC Pay والمحافظ الإقليمية — تأثر 12 مليون مستخدم", impact_usd: 280_000_000, stress_delta: 0.75, mechanism: "dependency_failure" },
  { step: 3, entity_id: "merchant_pos", entity_label: "Merchant POS Network", entity_label_ar: "شبكة نقاط البيع التجارية", event: "POS terminals offline across 340K merchants — cash-only operations", event_ar: "توقف أجهزة نقاط البيع عبر 340 ألف تاجر — عمليات نقدية فقط", impact_usd: 320_000_000, stress_delta: 0.68, mechanism: "infrastructure_dependency" },
  { step: 4, entity_id: "sme_merchants", entity_label: "SME Merchant Ecosystem", entity_label_ar: "منظومة التجار المتوسطين والصغار", event: "SME daily revenue drops 72% — cash liquidity insufficient for operations", event_ar: "انخفاض إيرادات الشركات الصغيرة اليومية 72% — السيولة النقدية غير كافية", impact_usd: 180_000_000, stress_delta: 0.52, mechanism: "economic_disruption" },
  { step: 5, entity_id: "consumer_spending", entity_label: "Consumer Spending Index", entity_label_ar: "مؤشر الإنفاق الاستهلاكي", event: "Consumer confidence drops — discretionary spending postponed region-wide", event_ar: "انخفاض ثقة المستهلك — تأجيل الإنفاق التقديري على مستوى المنطقة", impact_usd: 140_000_000, stress_delta: 0.45, mechanism: "demand_shock" },
];

export const MOCK_FINTECH_SECTOR_IMPACTS: SectorImpact[] = [
  { sector: "infrastructure", sectorLabel: "Payment Infrastructure", avgImpact: 0.75, maxImpact: 0.82, nodeCount: 3, topNode: "payment_gateway", color: "#8C2318" },
  { sector: "economy", sectorLabel: "Commerce & Retail", avgImpact: 0.55, maxImpact: 0.68, nodeCount: 4, topNode: "merchant_pos", color: "#8B6914" },
  { sector: "finance", sectorLabel: "Financial Services", avgImpact: 0.48, maxImpact: 0.62, nodeCount: 3, topNode: "cross_border_remit", color: "#0C6B58" },
];

export const MOCK_FINTECH_SECTOR_ROLLUPS = {
  fintech: { aggregate_stress: 0.72, total_loss: 420_000_000, node_count: 4, classification: "ELEVATED" as const },
  banking: { aggregate_stress: 0.38, total_loss: 180_000_000, node_count: 3, classification: "LOW" as const },
  trade: { aggregate_stress: 0.45, total_loss: 160_000_000, node_count: 3, classification: "GUARDED" as const },
  insurance: { aggregate_stress: 0.25, total_loss: 80_000_000, node_count: 2, classification: "LOW" as const },
  energy: { aggregate_stress: 0.18, total_loss: 40_000_000, node_count: 2, classification: "LOW" as const },
};

export const MOCK_FINTECH_DECISION_ACTIONS: DecisionActionV2[] = [
  {
    id: "fda_1", action: "Activate central bank RTGS backup channel for critical payment processing", action_ar: "تفعيل قناة RTGS الاحتياطية للبنك المركزي لمعالجة المدفوعات الحرجة",
    sector: "banking", owner: "SAMA + CBUAE", urgency: 95, value: 90,
    regulatory_risk: 0.10, priority: 96, target_node_id: "central_bank_rtgs",
    target_lat: 24.71, target_lng: 46.67, loss_avoided_usd: 380_000_000,
    cost_usd: 12_000_000, confidence: 0.90,
  },
  {
    id: "fda_2", action: "Deploy emergency cash distribution to SME merchant clusters", action_ar: "نشر توزيع نقدي طارئ لمجموعات التجار المتوسطين والصغار",
    sector: "finance", owner: "Ministry of Commerce", urgency: 88, value: 78,
    regulatory_risk: 0.15, priority: 84, target_node_id: "sme_merchants",
    target_lat: 25.10, target_lng: 55.15, loss_avoided_usd: 180_000_000,
    cost_usd: 8_000_000, confidence: 0.85,
  },
  {
    id: "fda_3", action: "Coordinate payment gateway failover to secondary processing center", action_ar: "تنسيق تحويل بوابة الدفع إلى مركز المعالجة الثانوي",
    sector: "fintech", owner: "Payment Network Operators", urgency: 92, value: 88,
    regulatory_risk: 0.12, priority: 92, target_node_id: "payment_gateway",
    target_lat: 25.20, target_lng: 55.27, loss_avoided_usd: 320_000_000,
    cost_usd: 15_000_000, confidence: 0.87,
  },
];

export const MOCK_FINTECH_EXPLANATION = {
  narrative_en: "A cascading failure in the GCC's primary payment gateway hub blocks 85% of digital transactions across the region. The outage propagates through three channels: (1) mobile wallet networks serving 12M users fail, forcing cash-only operations, (2) 340K merchant POS terminals go offline, reducing SME daily revenue by 72%, and (3) cross-border remittance channels are blocked, affecting migrant worker payment flows. Total estimated loss reaches $920M over the 72-hour horizon, with peak disruption on Day 1.",
  narrative_ar: "فشل متتالي في مركز بوابة الدفع الرئيسي الخليجي يحجب 85% من المعاملات الرقمية عبر المنطقة.",
  methodology: "Institutional macro-financial intelligence: Digital payment infrastructure dependency model. 16-node GCC fintech knowledge graph with 32 causal edges. Confidence: Monte Carlo 10K iterations.",
  confidence: 0.85,
  total_steps: 5,
};

export const MOCK_FINTECH_TRUST = {
  trace_id: "trc_20260413_111500_fintech",
  audit_id: "aud_cc_006",
  audit_hash: "sha256:f9i7h3d46e8g2f51i0h7e6d9g4f3c2b5e8h1d4g7f0c3e6b9a2d5h8g1f4c7e0b3",
  model_version: "io-v4.0.0",
  pipeline_version: "unified-v2.1",
  confidence_score: 0.85,
  data_sources: ["Payment Gateway Telemetry", "SAMA Digital Payments Data", "CBUAE Payment Stats", "POS Network Monitor", "Consumer Sentiment Index"],
  stages_completed: ["signal_ingest", "graph_activation", "causal_trace", "propagation", "physics", "math", "sector_stress", "decision_gen", "explanation"],
  warnings: ["POS terminal data: aggregated hourly", "Mobile wallet status: 10min delay"],
};

export const MOCK_FINTECH_LOSS_RANGE = { low: 780_000_000, mid: 920_000_000, high: 1_060_000_000, confidence_pct: 90 };
export const MOCK_FINTECH_DECISION_DEADLINE = new Date(Date.now() + 8 * 3_600_000).toISOString();

export const MOCK_FINTECH_ASSUMPTIONS: string[] = [
  "Payment gateway failure is infrastructure-related (not cyber attack)",
  "Central bank RTGS backup systems remain operational",
  "Cash reserves at bank branches sufficient for 72-hour surge",
  "No concurrent banking sector stress compounding the outage",
  "Payment gateway failover to secondary center achievable within 12 hours",
];

export const MOCK_FINTECH_COUNTRY_EXPOSURES: CountryExposureEntry[] = [
  { code: "UAE", name: "United Arab Emirates", nameAr: "الإمارات العربية المتحدة", exposureUsd: 340_000_000, stressLevel: 0.68, primaryDriver: "Payment gateway hub — stress at 82%", primaryDriverAr: "مركز بوابة الدفع — الضغط عند 82%", transmissionChannel: "Digital payments → merchant revenue → consumer spending", transmissionChannelAr: "المدفوعات الرقمية → إيرادات التجار → الإنفاق الاستهلاكي" },
  { code: "KSA", name: "Saudi Arabia", nameAr: "المملكة العربية السعودية", exposureUsd: 280_000_000, stressLevel: 0.62, primaryDriver: "Mobile wallets (STC Pay) — stress at 75%", primaryDriverAr: "المحافظ المحمولة (STC Pay) — الضغط عند 75%", transmissionChannel: "Mobile payments → SME operations → employment", transmissionChannelAr: "المدفوعات المحمولة → عمليات الشركات الصغيرة → التوظيف" },
  { code: "BHR", name: "Bahrain", nameAr: "البحرين", exposureUsd: 120_000_000, stressLevel: 0.52, primaryDriver: "Fintech hub dependency — stress at 52%", primaryDriverAr: "اعتماد مركز التكنولوجيا المالية — الضغط عند 52%", transmissionChannel: "Payment processing → fintech services → cross-border flows", transmissionChannelAr: "معالجة الدفع → خدمات التكنولوجيا المالية → التدفقات العابرة" },
  { code: "QAT", name: "Qatar", nameAr: "قطر", exposureUsd: 80_000_000, stressLevel: 0.38, primaryDriver: "POS network — stress at 38%", primaryDriverAr: "شبكة نقاط البيع — الضغط عند 38%", transmissionChannel: "Retail payments → consumer spending", transmissionChannelAr: "مدفوعات التجزئة → الإنفاق الاستهلاكي" },
  { code: "KWT", name: "Kuwait", nameAr: "الكويت", exposureUsd: 60_000_000, stressLevel: 0.32, primaryDriver: "E-commerce platforms — stress at 32%", primaryDriverAr: "منصات التجارة الإلكترونية — الضغط عند 32%", transmissionChannel: "Online payments → retail sector", transmissionChannelAr: "المدفوعات الإلكترونية → قطاع التجزئة" },
  { code: "OMN", name: "Oman", nameAr: "عُمان", exposureUsd: 40_000_000, stressLevel: 0.22, primaryDriver: "Digital banking channels — stress at 22%", primaryDriverAr: "القنوات المصرفية الرقمية — الضغط عند 22%", transmissionChannel: "Digital services → banking operations", transmissionChannelAr: "الخدمات الرقمية → العمليات المصرفية" },
];

export const MOCK_FINTECH_OUTCOMES = {
  baseCase: { label: "Base Case (No Intervention)", labelAr: "السيناريو الأساسي (بدون تدخل)", lossLow: 780_000_000, lossHigh: 1_060_000_000, recoveryDays: 14, description: "Full digital payment outage with cash-only fallback. Recovery dependent on gateway infrastructure repair.", descriptionAr: "انقطاع كامل للدفع الرقمي مع تراجع للنقد فقط. التعافي يعتمد على إصلاح البنية التحتية." } as OutcomeScenario,
  mitigatedCase: { label: "Mitigated Case (Rapid Response)", labelAr: "السيناريو المخفف (استجابة سريعة)", lossLow: 260_000_000, lossHigh: 420_000_000, recoveryDays: 5, description: "3 coordinated interventions reducing exposure by 60%. RTGS backup and gateway failover restore critical flows.", descriptionAr: "3 تدخلات منسقة تقلل التعرض بنسبة 60%. استعادة التدفقات الحرجة عبر RTGS الاحتياطي." } as OutcomeScenario,
  valueSaved: { low: 360_000_000, high: 800_000_000, description: "Estimated value preserved through RTGS backup activation, merchant cash distribution, and gateway failover.", descriptionAr: "القيمة المقدرة المحفوظة من خلال تفعيل RTGS الاحتياطي وتوزيع النقد وتحويل البوابة." },
};

export const MOCK_FINTECH_SECTOR_DEPTH: Record<string, { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }> = {
  fintech: { topDriver: "Payment gateway cascade failure — 85% digital transactions blocked", secondOrderRisk: "1 recommended intervention — Gateway failover to secondary center", confidenceLow: 0.64, confidenceHigh: 0.80 },
  banking: { topDriver: "Cash demand surge — ATM withdrawal volumes spike 400%", secondOrderRisk: "1 recommended intervention — Activate RTGS backup channel", confidenceLow: 0.30, confidenceHigh: 0.46 },
  trade: { topDriver: "E-commerce checkout failure — online retail revenue drops 90%", secondOrderRisk: "Monitoring for supply chain order backlog effects", confidenceLow: 0.37, confidenceHigh: 0.53 },
};
