/**
 * GCC Macro Financial Intelligence — Curated Briefing Data
 *
 * Executive-grade content for decision-makers (CEOs, central banks, regulators).
 * All language is macro-financial — no technical/IT terminology.
 */

import type {
  UnifiedRunResult,
  PropagationStep,
  SectorImpact,
  CausalStep,
  DecisionActionV2,
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  ImpactedEntity,
} from "@/types/observatory";

// ── Scenario Headline ─────────────────────────────────────────────────

export const MOCK_SCENARIO = {
  template_id: "hormuz_chokepoint_disruption",
  label: "Energy & Trade Flow Disruption — Strait of Hormuz",
  label_ar: "اضطراب تدفقات الطاقة والتجارة — مضيق هرمز",
  severity: 0.72,
  horizon_hours: 168,
  domain: "ENERGY_TRADE",
  trigger_time: "2026-04-08T06:14:00Z",
};

export const MOCK_HEADLINE = {
  total_loss_usd: 4_270_000_000,
  total_nodes_impacted: 31,
  propagation_depth: 5,
  peak_day: 3,
  max_recovery_days: 42,
  average_stress: 0.61,
  affected_entities: 31,
  critical_count: 7,
  elevated_count: 12,
};

// ── Graph Nodes (subset for command center) ───────────────────────────

export const MOCK_GRAPH_NODES: KnowledgeGraphNode[] = [
  { id: "hormuz_strait", label: "Strait of Hormuz", label_ar: "مضيق هرمز", layer: "geography", type: "chokepoint", weight: 0.95, lat: 26.56, lng: 56.25, sensitivity: 0.92, stress: 0.88, classification: "CRITICAL" },
  { id: "ras_tanura", label: "Ras Tanura Terminal", label_ar: "محطة رأس تنورة", layer: "infrastructure", type: "port", weight: 0.88, lat: 26.63, lng: 50.16, sensitivity: 0.85, stress: 0.74, classification: "ELEVATED" },
  { id: "jebel_ali", label: "Jebel Ali Port", label_ar: "ميناء جبل علي", layer: "infrastructure", type: "port", weight: 0.91, lat: 25.02, lng: 55.06, sensitivity: 0.80, stress: 0.71, classification: "ELEVATED" },
  { id: "aramco", label: "Saudi Aramco", label_ar: "أرامكو السعودية", layer: "economy", type: "corporation", weight: 0.96, lat: 26.39, lng: 50.10, sensitivity: 0.78, stress: 0.65, classification: "MODERATE" },
  { id: "adnoc", label: "ADNOC", label_ar: "أدنوك", layer: "economy", type: "corporation", weight: 0.85, lat: 24.45, lng: 54.65, sensitivity: 0.75, stress: 0.62, classification: "MODERATE" },
  { id: "sama", label: "SAMA", label_ar: "مؤسسة النقد", layer: "finance", type: "central_bank", weight: 0.90, lat: 24.69, lng: 46.69, sensitivity: 0.70, stress: 0.48, classification: "MODERATE" },
  { id: "cbuae", label: "CBUAE", label_ar: "مصرف الإمارات المركزي", layer: "finance", type: "central_bank", weight: 0.87, lat: 24.49, lng: 54.37, sensitivity: 0.68, stress: 0.45, classification: "LOW" },
  { id: "brent_crude", label: "Brent Crude", label_ar: "خام برنت", layer: "economy", type: "commodity", weight: 0.82, lat: 25.30, lng: 51.52, sensitivity: 0.90, stress: 0.78, classification: "ELEVATED" },
  { id: "gcc_insurance", label: "GCC Insurance Sector", label_ar: "قطاع التأمين الخليجي", layer: "finance", type: "sector", weight: 0.74, lat: 25.20, lng: 55.27, sensitivity: 0.72, stress: 0.58, classification: "MODERATE" },
  { id: "gcc_trade", label: "GCC Trade Volume", label_ar: "حجم التجارة الخليجية", layer: "economy", type: "indicator", weight: 0.79, lat: 24.71, lng: 46.67, sensitivity: 0.82, stress: 0.67, classification: "ELEVATED" },
];

export const MOCK_GRAPH_EDGES: KnowledgeGraphEdge[] = [
  { id: "e1", source: "hormuz_strait", target: "ras_tanura", weight: 0.92, polarity: 1, label: "blocks export flow", label_ar: "يعطل تدفق الصادرات", transmission: 0.88 },
  { id: "e2", source: "hormuz_strait", target: "jebel_ali", weight: 0.87, polarity: 1, label: "disrupts container throughput", label_ar: "يعطل إنتاجية الحاويات", transmission: 0.82 },
  { id: "e3", source: "ras_tanura", target: "aramco", weight: 0.85, polarity: 1, label: "reduces export capacity", label_ar: "يقلل طاقة التصدير", transmission: 0.78 },
  { id: "e4", source: "jebel_ali", target: "gcc_trade", weight: 0.80, polarity: 1, label: "constrains trade volume", label_ar: "يقيد حجم التجارة", transmission: 0.74 },
  { id: "e5", source: "hormuz_strait", target: "brent_crude", weight: 0.90, polarity: 1, label: "spikes crude prices", label_ar: "يرفع أسعار النفط", transmission: 0.86 },
  { id: "e6", source: "brent_crude", target: "gcc_insurance", weight: 0.65, polarity: 1, label: "increases marine P&I claims", label_ar: "يزيد مطالبات التأمين البحري", transmission: 0.58 },
  { id: "e7", source: "aramco", target: "sama", weight: 0.70, polarity: 1, label: "reduces fiscal inflow", label_ar: "يقلل التدفق المالي", transmission: 0.62 },
  { id: "e8", source: "adnoc", target: "cbuae", weight: 0.68, polarity: 1, label: "reduces fiscal inflow", label_ar: "يقلل التدفق المالي", transmission: 0.60 },
  { id: "e9", source: "hormuz_strait", target: "adnoc", weight: 0.84, polarity: 1, label: "disrupts operations", label_ar: "يعطل العمليات", transmission: 0.79 },
  { id: "e10", source: "gcc_trade", target: "sama", weight: 0.55, polarity: 1, label: "strains FX reserves", label_ar: "يضغط على الاحتياطي", transmission: 0.48 },
];

// ── Impacted Entities (map overlay) ───────────────────────────────────

export const MOCK_IMPACTED_ENTITIES: ImpactedEntity[] = MOCK_GRAPH_NODES.map((n) => ({
  node_id: n.id,
  label: n.label,
  label_ar: n.label_ar,
  lat: n.lat,
  lng: n.lng,
  stress: n.stress ?? 0,
  loss_usd: Math.round((n.stress ?? 0) * 600_000_000),
  classification: n.classification ?? "NOMINAL",
  layer: n.layer,
}));

// ── Propagation Chain ─────────────────────────────────────────────────

export const MOCK_PROPAGATION_STEPS: PropagationStep[] = [
  { from: "hormuz_strait", fromLabel: "Strait of Hormuz", to: "ras_tanura", toLabel: "Ras Tanura Terminal", weight: 0.92, polarity: 1, impact: 0.88, label: "Energy export flow disruption", iteration: 1 },
  { from: "hormuz_strait", fromLabel: "Strait of Hormuz", to: "jebel_ali", toLabel: "Jebel Ali Port", weight: 0.87, polarity: 1, impact: 0.82, label: "Trade volume contraction", iteration: 1 },
  { from: "hormuz_strait", fromLabel: "Strait of Hormuz", to: "brent_crude", toLabel: "Brent Crude", weight: 0.90, polarity: 1, impact: 0.86, label: "Commodity price shock", iteration: 1 },
  { from: "ras_tanura", fromLabel: "Ras Tanura Terminal", to: "aramco", toLabel: "Saudi Aramco", weight: 0.85, polarity: 1, impact: 0.65, label: "Export revenue reduction", iteration: 2 },
  { from: "jebel_ali", fromLabel: "Jebel Ali Port", to: "gcc_trade", toLabel: "GCC Trade Volume", weight: 0.80, polarity: 1, impact: 0.67, label: "Cross-border trade constraint", iteration: 2 },
  { from: "brent_crude", fromLabel: "Brent Crude", to: "gcc_insurance", toLabel: "GCC Insurance Sector", weight: 0.65, polarity: 1, impact: 0.58, label: "Marine claims acceleration", iteration: 2 },
  { from: "aramco", fromLabel: "Saudi Aramco", to: "sama", toLabel: "SAMA", weight: 0.70, polarity: 1, impact: 0.48, label: "Fiscal revenue shortfall", iteration: 3 },
  { from: "adnoc", fromLabel: "ADNOC", to: "cbuae", toLabel: "CBUAE", weight: 0.68, polarity: 1, impact: 0.45, label: "Fiscal revenue shortfall", iteration: 3 },
];

export const MOCK_SECTOR_IMPACTS: SectorImpact[] = [
  { sector: "energy", sectorLabel: "Oil & Gas", avgImpact: 0.73, maxImpact: 0.88, nodeCount: 4, topNode: "ras_tanura", color: "#EF4444" },
  { sector: "trade", sectorLabel: "Trade & Commerce", avgImpact: 0.68, maxImpact: 0.78, nodeCount: 5, topNode: "brent_crude", color: "#F59E0B" },
  { sector: "banking", sectorLabel: "Banking & Finance", avgImpact: 0.50, maxImpact: 0.58, nodeCount: 4, topNode: "gcc_insurance", color: "#3B82F6" },
  { sector: "insurance", sectorLabel: "Insurance & Reinsurance", avgImpact: 0.48, maxImpact: 0.58, nodeCount: 3, topNode: "gcc_insurance", color: "#8B5CF6" },
];

// ── Causal Chain (Propagation narrative — executive language) ─────────

export const MOCK_CAUSAL_CHAIN: CausalStep[] = [
  { step: 1, entity_id: "hormuz_strait", entity_label: "Strait of Hormuz", entity_label_ar: "مضيق هرمز", event: "Energy transit corridor partially restricted — vessel movement reduced 60%", event_ar: "تقييد جزئي لممر عبور الطاقة — انخفاض حركة السفن 60%", impact_usd: 0, stress_delta: 0.88, mechanism: "direct_shock" },
  { step: 2, entity_id: "brent_crude", entity_label: "Brent Crude", entity_label_ar: "خام برنت", event: "Commodity prices surge +$18/bbl on supply constraint expectations", event_ar: "ارتفاع أسعار السلع +18$/برميل بسبب توقعات قيود الإمداد", impact_usd: 1_200_000_000, stress_delta: 0.78, mechanism: "price_transmission" },
  { step: 3, entity_id: "ras_tanura", entity_label: "Ras Tanura Terminal", entity_label_ar: "محطة رأس تنورة", event: "Export capacity constrained to 40% — revenue flow materially reduced", event_ar: "تقييد طاقة التصدير إلى 40% — انخفاض جوهري في تدفق الإيرادات", impact_usd: 890_000_000, stress_delta: 0.74, mechanism: "physical_constraint" },
  { step: 4, entity_id: "jebel_ali", entity_label: "Jebel Ali Port", entity_label_ar: "ميناء جبل علي", event: "Trade flow congestion exceeds 72h — cross-border commerce rerouting", event_ar: "ازدحام تدفق التجارة يتجاوز 72 ساعة — إعادة توجيه التجارة العابرة للحدود", impact_usd: 670_000_000, stress_delta: 0.71, mechanism: "capacity_overflow" },
  { step: 5, entity_id: "aramco", entity_label: "Saudi Aramco", entity_label_ar: "أرامكو السعودية", event: "Daily export volumes reduced 3.2M bbl — force majeure declared on contracts", event_ar: "تقليص حجم الصادرات اليومية 3.2 مليون برميل — إعلان القوة القاهرة على العقود", impact_usd: 820_000_000, stress_delta: 0.65, mechanism: "supply_chain" },
  { step: 6, entity_id: "gcc_insurance", entity_label: "GCC Insurance Sector", entity_label_ar: "قطاع التأمين الخليجي", event: "Marine claims accelerate 4.2x — reinsurance capacity under pressure", event_ar: "تسارع المطالبات البحرية 4.2 ضعف — ضغط على طاقة إعادة التأمين", impact_usd: 410_000_000, stress_delta: 0.58, mechanism: "claims_cascade" },
  { step: 7, entity_id: "sama", entity_label: "SAMA", entity_label_ar: "مؤسسة النقد", event: "FX reserves drawdown accelerates — interbank liquidity under pressure", event_ar: "تسارع سحب احتياطي العملات — ضغط على السيولة بين البنوك", impact_usd: 280_000_000, stress_delta: 0.48, mechanism: "monetary_transmission" },
];

// ── Decision Actions ──────────────────────────────────────────────────

export const MOCK_DECISION_ACTIONS: DecisionActionV2[] = [
  {
    id: "da_1", action: "Activate Strategic Petroleum Reserve release (SAMA coordination)", action_ar: "تفعيل إطلاق الاحتياطي البترولي الاستراتيجي (بالتنسيق مع مؤسسة النقد)",
    sector: "energy", owner: "Ministry of Energy", urgency: 92, value: 88,
    regulatory_risk: 0.15, priority: 95, target_node_id: "ras_tanura",
    target_lat: 26.63, target_lng: 50.16, loss_avoided_usd: 1_800_000_000,
    cost_usd: 120_000_000, confidence: 0.87,
    deadline_hours: 6, escalation_trigger: "Crude export throughput below 40% for 12+ hours", escalation_trigger_ar: "إنتاجية تصدير النفط أقل من 40% لأكثر من 12 ساعة",
  },
  {
    id: "da_2", action: "Deploy emergency vessel rerouting through Bab el-Mandeb corridor", action_ar: "نشر خطة إعادة توجيه السفن الطارئة عبر ممر باب المندب",
    sector: "maritime", owner: "Federal Transport Authority", urgency: 88, value: 75,
    regulatory_risk: 0.22, priority: 82, target_node_id: "jebel_ali",
    target_lat: 25.02, target_lng: 55.06, loss_avoided_usd: 920_000_000,
    cost_usd: 85_000_000, confidence: 0.79,
    deadline_hours: 12, escalation_trigger: "Container backlog exceeds 96h at Jebel Ali", escalation_trigger_ar: "تراكم الحاويات يتجاوز 96 ساعة في جبل علي",
  },
  {
    id: "da_3", action: "Trigger IFRS 17 catastrophe reserve allocation for marine P&I", action_ar: "تفعيل تخصيص احتياطي الكوارث وفق المعيار الدولي IFRS 17 للتأمين البحري",
    sector: "insurance", owner: "Insurance Authority", urgency: 78, value: 70,
    regulatory_risk: 0.30, priority: 74, target_node_id: "gcc_insurance",
    target_lat: 25.20, target_lng: 55.27, loss_avoided_usd: 410_000_000,
    cost_usd: 45_000_000, confidence: 0.82,
    deadline_hours: 24, escalation_trigger: "Marine claims exceed 5x baseline within 48h", escalation_trigger_ar: "مطالبات التأمين البحري تتجاوز 5 أضعاف خلال 48 ساعة",
  },
  {
    id: "da_4", action: "Coordinate GCC central bank FX swap lines to stabilize interbank rates", action_ar: "تنسيق خطوط مبادلة العملات بين البنوك المركزية الخليجية لتثبيت أسعار الفائدة",
    sector: "finance", owner: "SAMA + CBUAE", urgency: 72, value: 82,
    regulatory_risk: 0.18, priority: 77, target_node_id: "sama",
    target_lat: 24.69, target_lng: 46.69, loss_avoided_usd: 650_000_000,
    cost_usd: 30_000_000, confidence: 0.85,
    deadline_hours: 18, escalation_trigger: "Interbank rate spread exceeds 200bps for 24h", escalation_trigger_ar: "فارق أسعار ما بين البنوك يتجاوز 200 نقطة أساس لمدة 24 ساعة",
  },
];

// ── Explanation Pack ──────────────────────────────────────────────────

export const MOCK_EXPLANATION = {
  narrative_en:
    "A partial restriction of the Strait of Hormuz — reducing energy transit by approximately 60% — triggers a multi-sector financial cascade across the GCC. The disruption transmits through three primary channels: (1) energy export revenue contraction, with Ras Tanura capacity falling to 40% and Jebel Ali trade flows constrained; (2) commodity price transmission, with Brent crude rising +$18/bbl within 48 hours; and (3) insurance loss acceleration, as marine claims surge 4.2x across regional carriers. Total estimated financial exposure reaches $3.8B–$4.7B over the 7-day horizon, with peak stress on Day 3. Recovery timeline is 42 days assuming diplomatic resolution within 10 days.",
  narrative_ar:
    "يؤدي التقييد الجزئي لمضيق هرمز — مع تقليص عبور الطاقة بنسبة 60% تقريبا — إلى سلسلة تأثيرات مالية متعددة القطاعات عبر دول مجلس التعاون الخليجي. ينتقل الاضطراب عبر ثلاث قنوات رئيسية: انكماش إيرادات تصدير الطاقة، وانتقال صدمة أسعار السلع، وتسارع خسائر التأمين.",
  methodology: "Multi-layer macro-financial analysis covering 43 GCC financial entities across energy, banking, insurance, trade, and sovereign sectors. Confidence intervals derived from 10,000 Monte Carlo simulations across historical precedent scenarios.",
  confidence: 0.84,
  total_steps: 7,
};

// ── Sector Rollups ────────────────────────────────────────────────────

export const MOCK_SECTOR_ROLLUPS = {
  // Primary sectors
  energy: { aggregate_stress: 0.78, total_loss: 2_100_000_000, node_count: 5, classification: "ELEVATED" as const },
  banking: { aggregate_stress: 0.52, total_loss: 890_000_000, node_count: 6, classification: "MODERATE" as const },
  insurance: { aggregate_stress: 0.58, total_loss: 410_000_000, node_count: 4, classification: "MODERATE" as const },
  // Secondary sectors
  fintech: { aggregate_stress: 0.35, total_loss: 120_000_000, node_count: 3, classification: "LOW" as const },
  real_estate: { aggregate_stress: 0.44, total_loss: 340_000_000, node_count: 4, classification: "MODERATE" as const },
  government: { aggregate_stress: 0.38, total_loss: 180_000_000, node_count: 3, classification: "LOW" as const },
  trade: { aggregate_stress: 0.67, total_loss: 750_000_000, node_count: 4, classification: "ELEVATED" as const },
};

// ── V2.1 Curated Data — Decision Clock, Loss Range, Sector Depth ─────

/** Decision deadline: always 14 hours from now (dynamic for demo) */
export const MOCK_DECISION_DEADLINE = new Date(Date.now() + 14 * 3_600_000).toISOString();

/** Loss range (90% confidence interval) */
export const MOCK_LOSS_RANGE = {
  low: 3_810_000_000,
  mid: 4_270_000_000,
  high: 4_730_000_000,
  confidence_pct: 90,
};

/** Per-sector: top driver, second-order risk, confidence band */
export const MOCK_SECTOR_DEPTH: Record<
  string,
  { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }
> = {
  energy: {
    topDriver: "Crude export throughput reduced to 40% at Ras Tanura",
    secondOrderRisk: "Force majeure triggers on LNG forward contracts (Qatar cross-exposure)",
    confidenceLow: 0.78,
    confidenceHigh: 0.91,
  },
  trade: {
    topDriver: "Jebel Ali container backlog exceeding 72h cycle time",
    secondOrderRisk: "Re-export hub disruption cascades to East Africa supply chains",
    confidenceLow: 0.72,
    confidenceHigh: 0.86,
  },
  banking: {
    topDriver: "Interbank liquidity tightening via FX reserve drawdown",
    secondOrderRisk: "Credit rating agency negative watch triggers margin calls",
    confidenceLow: 0.70,
    confidenceHigh: 0.84,
  },
  insurance: {
    topDriver: "Marine P&I claims surge 4.2x baseline — reinsurance triggers activated",
    secondOrderRisk: "Catastrophe reserve depletion constrains underwriting capacity for 2+ quarters",
    confidenceLow: 0.74,
    confidenceHigh: 0.88,
  },
  fintech: {
    topDriver: "Cross-border payment settlement delays exceeding SLA thresholds",
    secondOrderRisk: "Merchant liquidity squeeze triggers working capital facility drawdowns",
    confidenceLow: 0.65,
    confidenceHigh: 0.79,
  },
  real_estate: {
    topDriver: "Developer financing costs spike on interbank rate transmission",
    secondOrderRisk: "Off-plan mortgage market freeze triggers project completion delays across UAE/SA",
    confidenceLow: 0.62,
    confidenceHigh: 0.78,
  },
  government: {
    topDriver: "Fiscal revenue shortfall from reduced hydrocarbon receipts",
    secondOrderRisk: "Sovereign wealth fund drawdown accelerates — stabilization reserves constrained for 2+ quarters",
    confidenceLow: 0.68,
    confidenceHigh: 0.82,
  },
};

/** Assumptions for compact panel */
export const MOCK_ASSUMPTIONS = [
  "Diplomatic resolution within 10 days (baseline scenario)",
  "No military escalation beyond current posture",
  "Central bank FX intervention capacity at full availability",
  "Reinsurance treaties activated at standard contractual thresholds",
  "Commodity price feeds reflect a 5-minute settlement delay",
];

// ── Country Exposure Data ────────────────────────────────────────────

export interface CountryExposureEntry {
  code: string;
  name: string;
  nameAr: string;
  exposureUsd: number;
  stressLevel: number;
  primaryDriver: string;
  primaryDriverAr: string;
  transmissionChannel: string;
  transmissionChannelAr: string;
}

export const MOCK_COUNTRY_EXPOSURES: CountryExposureEntry[] = [
  {
    code: "KSA",
    name: "Saudi Arabia",
    nameAr: "المملكة العربية السعودية",
    exposureUsd: 1_850_000_000,
    stressLevel: 0.74,
    primaryDriver: "Energy export revenue contraction — Aramco force majeure on forward contracts",
    primaryDriverAr: "انكماش إيرادات تصدير الطاقة — القوة القاهرة لأرامكو على العقود الآجلة",
    transmissionChannel: "Oil revenue → fiscal balance → banking sector liquidity",
    transmissionChannelAr: "إيرادات النفط → الميزانية المالية → سيولة القطاع المصرفي",
  },
  {
    code: "UAE",
    name: "United Arab Emirates",
    nameAr: "الإمارات العربية المتحدة",
    exposureUsd: 1_340_000_000,
    stressLevel: 0.68,
    primaryDriver: "Trade flow disruption — Jebel Ali re-export hub congestion",
    primaryDriverAr: "اضطراب تدفق التجارة — ازدحام مركز إعادة التصدير في جبل علي",
    transmissionChannel: "Trade volume → logistics sector → real estate demand",
    transmissionChannelAr: "حجم التجارة → قطاع الخدمات اللوجستية → الطلب العقاري",
  },
  {
    code: "KWT",
    name: "Kuwait",
    nameAr: "الكويت",
    exposureUsd: 520_000_000,
    stressLevel: 0.52,
    primaryDriver: "Crude export capacity constraint — Al-Ahmadi terminal exposure",
    primaryDriverAr: "قيود طاقة تصدير النفط — تعرض محطة الأحمدي",
    transmissionChannel: "Energy revenue → sovereign wealth fund drawdown",
    transmissionChannelAr: "إيرادات الطاقة → سحب صندوق الثروة السيادية",
  },
  {
    code: "QAT",
    name: "Qatar",
    nameAr: "قطر",
    exposureUsd: 380_000_000,
    stressLevel: 0.45,
    primaryDriver: "LNG forward contract exposure — transit route dependency",
    primaryDriverAr: "تعرض عقود الغاز المسال الآجلة — الاعتماد على مسار العبور",
    transmissionChannel: "LNG revenue → fiscal surplus → banking reserves",
    transmissionChannelAr: "إيرادات الغاز المسال → الفائض المالي → احتياطيات البنوك",
  },
];

// ── Outcome Data (Base Case / Mitigated / Value Saved) ───────────────

export interface OutcomeScenario {
  label: string;
  labelAr: string;
  lossLow: number;
  lossHigh: number;
  recoveryDays: number;
  description: string;
  descriptionAr: string;
}

export const MOCK_OUTCOMES = {
  baseCase: {
    label: "Base Case (No Intervention)",
    labelAr: "السيناريو الأساسي (بدون تدخل)",
    lossLow: 4_100_000_000,
    lossHigh: 4_730_000_000,
    recoveryDays: 42,
    description: "Full propagation across energy, trade, and financial sectors. Recovery dependent on diplomatic resolution timeline.",
    descriptionAr: "انتشار كامل عبر قطاعات الطاقة والتجارة والمالية. التعافي يعتمد على الجدول الزمني للحل الدبلوماسي.",
  } as OutcomeScenario,
  mitigatedCase: {
    label: "Mitigated Case (Coordinated Response)",
    labelAr: "السيناريو المخفف (استجابة منسقة)",
    lossLow: 2_200_000_000,
    lossHigh: 2_800_000_000,
    recoveryDays: 21,
    description: "Strategic reserve release + FX swap coordination + insurance reserve activation. Recovery timeline halved.",
    descriptionAr: "إطلاق الاحتياطي الاستراتيجي + تنسيق مبادلات العملات + تفعيل احتياطيات التأمين. تقليص فترة التعافي بالنصف.",
  } as OutcomeScenario,
  valueSaved: {
    low: 1_300_000_000,
    high: 2_530_000_000,
    description: "Estimated value preserved through coordinated intervention across 4 GCC central banks and 3 regulatory authorities.",
    descriptionAr: "القيمة المقدرة المحفوظة من خلال التدخل المنسق عبر 4 بنوك مركزية خليجية و3 هيئات تنظيمية.",
  },
};

// ══════════════════════════════════════════════════════════════════════
// SCENARIO 2: Regional Liquidity Stress Event
// ══════════════════════════════════════════════════════════════════════

export const MOCK_LIQUIDITY_SCENARIO = {
  template_id: "regional_liquidity_stress_event",
  label: "Regional Liquidity Stress — GCC Banking System",
  label_ar: "ضغط سيولة إقليمي — النظام المصرفي الخليجي",
  severity: 0.68,
  horizon_hours: 336,
  domain: "LIQUIDITY",
  trigger_time: "2026-04-10T09:30:00Z",
};

export const MOCK_LIQUIDITY_HEADLINE = {
  total_loss_usd: 2_600_000_000,
  total_nodes_impacted: 24,
  propagation_depth: 4,
  peak_day: 6,
  max_recovery_days: 21,
  average_stress: 0.54,
  affected_entities: 24,
  critical_count: 4,
  elevated_count: 9,
};

export const MOCK_LIQUIDITY_GRAPH_NODES: KnowledgeGraphNode[] = [
  { id: "uae_banking", label: "UAE Banking Sector", label_ar: "القطاع المصرفي الإماراتي", layer: "finance", type: "sector", weight: 0.92, lat: 24.45, lng: 54.65, sensitivity: 0.88, stress: 0.76, classification: "ELEVATED" },
  { id: "saudi_banking", label: "Saudi Banking Sector", label_ar: "القطاع المصرفي السعودي", layer: "finance", type: "sector", weight: 0.94, lat: 24.69, lng: 46.69, sensitivity: 0.85, stress: 0.72, classification: "ELEVATED" },
  { id: "qatar_banking", label: "Qatar Banking Sector", label_ar: "القطاع المصرفي القطري", layer: "finance", type: "sector", weight: 0.86, lat: 25.30, lng: 51.52, sensitivity: 0.78, stress: 0.65, classification: "ELEVATED" },
  { id: "gcc_fsb", label: "GCC Financial Stability Board", label_ar: "مجلس الاستقرار المالي الخليجي", layer: "finance", type: "regulator", weight: 0.90, lat: 24.71, lng: 46.67, sensitivity: 0.72, stress: 0.58, classification: "MODERATE" },
  { id: "sama_liquidity", label: "SAMA Liquidity Window", label_ar: "نافذة السيولة لمؤسسة النقد", layer: "finance", type: "central_bank", weight: 0.93, lat: 24.69, lng: 46.69, sensitivity: 0.82, stress: 0.52, classification: "MODERATE" },
  { id: "cbuae_interbank", label: "CBUAE Interbank Market", label_ar: "سوق ما بين البنوك لمصرف الإمارات", layer: "finance", type: "central_bank", weight: 0.89, lat: 24.49, lng: 54.37, sensitivity: 0.80, stress: 0.68, classification: "ELEVATED" },
  { id: "gcc_insurance_liq", label: "GCC Insurance Reserves", label_ar: "احتياطيات التأمين الخليجية", layer: "finance", type: "sector", weight: 0.74, lat: 25.20, lng: 55.27, sensitivity: 0.65, stress: 0.42, classification: "MODERATE" },
  { id: "gcc_fintech_liq", label: "GCC Fintech Payment Rails", label_ar: "بنية المدفوعات التقنية الخليجية", layer: "infrastructure", type: "sector", weight: 0.72, lat: 25.02, lng: 55.06, sensitivity: 0.70, stress: 0.48, classification: "MODERATE" },
];

export const MOCK_LIQUIDITY_GRAPH_EDGES: KnowledgeGraphEdge[] = [
  { id: "le1", source: "uae_banking", target: "cbuae_interbank", weight: 0.90, polarity: 1, label: "liquidity demand surge", label_ar: "ارتفاع الطلب على السيولة", transmission: 0.85 },
  { id: "le2", source: "saudi_banking", target: "sama_liquidity", weight: 0.88, polarity: 1, label: "reserve drawdown pressure", label_ar: "ضغط سحب الاحتياطي", transmission: 0.82 },
  { id: "le3", source: "uae_banking", target: "gcc_fsb", weight: 0.78, polarity: 1, label: "systemic risk escalation", label_ar: "تصاعد المخاطر النظامية", transmission: 0.72 },
  { id: "le4", source: "qatar_banking", target: "gcc_fsb", weight: 0.75, polarity: 1, label: "cross-border contagion", label_ar: "عدوى عابرة للحدود", transmission: 0.68 },
  { id: "le5", source: "cbuae_interbank", target: "gcc_fintech_liq", weight: 0.65, polarity: 1, label: "payment settlement delays", label_ar: "تأخير تسوية المدفوعات", transmission: 0.58 },
  { id: "le6", source: "sama_liquidity", target: "gcc_insurance_liq", weight: 0.60, polarity: 1, label: "reserve requirement strain", label_ar: "ضغط متطلبات الاحتياطي", transmission: 0.52 },
  { id: "le7", source: "saudi_banking", target: "qatar_banking", weight: 0.72, polarity: 1, label: "interbank lending freeze", label_ar: "تجميد الإقراض بين البنوك", transmission: 0.65 },
];

export const MOCK_LIQUIDITY_CAUSAL_CHAIN: CausalStep[] = [
  { step: 1, entity_id: "uae_banking", entity_label: "UAE Banking Sector", entity_label_ar: "القطاع المصرفي الإماراتي", event: "Interbank lending rates spike 280bps — overnight liquidity dries up across major UAE banks", event_ar: "ارتفاع أسعار الإقراض بين البنوك 280 نقطة أساس — جفاف السيولة الليلية عبر البنوك الإماراتية الكبرى", impact_usd: 0, stress_delta: 0.76, mechanism: "direct_shock" },
  { step: 2, entity_id: "saudi_banking", entity_label: "Saudi Banking Sector", entity_label_ar: "القطاع المصرفي السعودي", event: "Deposit flight accelerates — SAR 18B withdrawn from term deposits within 72 hours", event_ar: "تسارع هروب الودائع — سحب 18 مليار ريال من الودائع لأجل خلال 72 ساعة", impact_usd: 680_000_000, stress_delta: 0.72, mechanism: "contagion" },
  { step: 3, entity_id: "cbuae_interbank", entity_label: "CBUAE Interbank Market", entity_label_ar: "سوق ما بين البنوك لمصرف الإمارات", event: "Central bank emergency facility activated — AED 45B injected to stabilize overnight rates", event_ar: "تفعيل تسهيل الطوارئ للبنك المركزي — ضخ 45 مليار درهم لتثبيت الأسعار الليلية", impact_usd: 520_000_000, stress_delta: 0.68, mechanism: "monetary_transmission" },
  { step: 4, entity_id: "qatar_banking", entity_label: "Qatar Banking Sector", entity_label_ar: "القطاع المصرفي القطري", event: "Cross-border lending facilities frozen — Qatar banks face USD funding squeeze", event_ar: "تجميد تسهيلات الإقراض العابرة للحدود — بنوك قطر تواجه ضغط تمويل بالدولار", impact_usd: 440_000_000, stress_delta: 0.65, mechanism: "cross_border_contagion" },
  { step: 5, entity_id: "gcc_fsb", entity_label: "GCC Financial Stability Board", entity_label_ar: "مجلس الاستقرار المالي الخليجي", event: "Systemic risk indicator breaches threshold — coordinated regulatory response initiated", event_ar: "مؤشر المخاطر النظامية يتجاوز العتبة — بدء استجابة رقابية منسقة", impact_usd: 360_000_000, stress_delta: 0.58, mechanism: "regulatory_cascade" },
  { step: 6, entity_id: "gcc_fintech_liq", entity_label: "GCC Fintech Payment Rails", entity_label_ar: "بنية المدفوعات التقنية الخليجية", event: "Payment settlement SLAs breached — cross-border merchant transactions delayed 8+ hours", event_ar: "تجاوز اتفاقيات مستوى خدمة تسوية المدفوعات — تأخير المعاملات التجارية العابرة للحدود 8+ ساعات", impact_usd: 180_000_000, stress_delta: 0.48, mechanism: "operational_contagion" },
];

export const MOCK_LIQUIDITY_DECISION_ACTIONS: DecisionActionV2[] = [
  {
    id: "lda_1", action: "Activate GCC-wide central bank liquidity injection facility (coordinated $12B)", action_ar: "تفعيل تسهيل ضخ السيولة على مستوى مجلس التعاون (12 مليار دولار منسق)",
    sector: "banking", owner: "SAMA + CBUAE + QCB", urgency: 95, value: 92,
    regulatory_risk: 0.10, priority: 96, target_node_id: "sama_liquidity",
    target_lat: 24.69, target_lng: 46.69, loss_avoided_usd: 1_100_000_000,
    cost_usd: 80_000_000, confidence: 0.91,
    deadline_hours: 4, escalation_trigger: "Overnight interbank rate exceeds 350bps", escalation_trigger_ar: "سعر الإقراض الليلي بين البنوك يتجاوز 350 نقطة أساس",
  },
  {
    id: "lda_2", action: "Establish emergency interbank lending facility with reduced reserve requirements", action_ar: "إنشاء تسهيل إقراض طوارئ بين البنوك مع خفض متطلبات الاحتياطي",
    sector: "banking", owner: "CBUAE", urgency: 90, value: 85,
    regulatory_risk: 0.18, priority: 88, target_node_id: "cbuae_interbank",
    target_lat: 24.49, target_lng: 54.37, loss_avoided_usd: 680_000_000,
    cost_usd: 45_000_000, confidence: 0.86,
    deadline_hours: 8, escalation_trigger: "Deposit withdrawal rate exceeds SAR 5B/day", escalation_trigger_ar: "معدل سحب الودائع يتجاوز 5 مليار ريال يوميا",
  },
  {
    id: "lda_3", action: "Activate payment system contingency protocols — route critical settlements through backup rails", action_ar: "تفعيل بروتوكولات طوارئ نظام المدفوعات — توجيه التسويات الحرجة عبر مسارات احتياطية",
    sector: "fintech", owner: "GCC Payments Authority", urgency: 82, value: 78,
    regulatory_risk: 0.12, priority: 80, target_node_id: "gcc_fintech_liq",
    target_lat: 25.02, target_lng: 55.06, loss_avoided_usd: 320_000_000,
    cost_usd: 25_000_000, confidence: 0.84,
    deadline_hours: 12, escalation_trigger: "Settlement failure rate exceeds 15% of daily volume", escalation_trigger_ar: "معدل فشل التسوية يتجاوز 15% من الحجم اليومي",
  },
  {
    id: "lda_4", action: "Temporary capital controls easing — allow USD repo access at preferential rates", action_ar: "تخفيف مؤقت لضوابط رأس المال — السماح بالوصول لعمليات إعادة الشراء بالدولار بأسعار تفضيلية",
    sector: "finance", owner: "SAMA", urgency: 75, value: 80,
    regulatory_risk: 0.25, priority: 76, target_node_id: "sama_liquidity",
    target_lat: 24.69, target_lng: 46.69, loss_avoided_usd: 450_000_000,
    cost_usd: 35_000_000, confidence: 0.79,
    deadline_hours: 24, escalation_trigger: "USD repo rate premium exceeds 150bps above Fed rate", escalation_trigger_ar: "علاوة سعر إعادة الشراء بالدولار تتجاوز 150 نقطة فوق سعر الفيدرالي",
  },
];

export const MOCK_LIQUIDITY_SECTOR_IMPACTS: SectorImpact[] = [
  { sector: "banking", sectorLabel: "Banking & Finance", avgImpact: 0.72, maxImpact: 0.76, nodeCount: 6, topNode: "uae_banking", color: "#3B82F6" },
  { sector: "fintech", sectorLabel: "Fintech & Payments", avgImpact: 0.48, maxImpact: 0.52, nodeCount: 3, topNode: "gcc_fintech_liq", color: "#8B5CF6" },
  { sector: "insurance", sectorLabel: "Insurance Reserves", avgImpact: 0.42, maxImpact: 0.48, nodeCount: 2, topNode: "gcc_insurance_liq", color: "#F59E0B" },
  { sector: "government", sectorLabel: "Regulatory Response", avgImpact: 0.55, maxImpact: 0.58, nodeCount: 3, topNode: "gcc_fsb", color: "#10B981" },
];

export const MOCK_LIQUIDITY_SECTOR_ROLLUPS = {
  banking: { aggregate_stress: 0.72, total_loss: 1_480_000_000, node_count: 6, classification: "ELEVATED" as const },
  insurance: { aggregate_stress: 0.42, total_loss: 210_000_000, node_count: 3, classification: "MODERATE" as const },
  fintech: { aggregate_stress: 0.48, total_loss: 280_000_000, node_count: 3, classification: "MODERATE" as const },
  government: { aggregate_stress: 0.55, total_loss: 320_000_000, node_count: 3, classification: "MODERATE" as const },
  real_estate: { aggregate_stress: 0.38, total_loss: 180_000_000, node_count: 2, classification: "LOW" as const },
  trade: { aggregate_stress: 0.32, total_loss: 130_000_000, node_count: 3, classification: "LOW" as const },
};

export const MOCK_LIQUIDITY_LOSS_RANGE = {
  low: 2_210_000_000,
  mid: 2_600_000_000,
  high: 3_050_000_000,
  confidence_pct: 90,
};

export const MOCK_LIQUIDITY_DECISION_DEADLINE = new Date(Date.now() + 18 * 3_600_000).toISOString();

export const MOCK_LIQUIDITY_ASSUMPTIONS = [
  "No simultaneous sovereign credit downgrade event",
  "GCC central bank coordination mechanisms fully operational",
  "Cross-border payment settlement infrastructure functional at reduced capacity",
  "USD repo markets accessible through bilateral swap arrangements",
  "Deposit insurance mechanisms prevent full retail bank run",
];

export const MOCK_LIQUIDITY_COUNTRY_EXPOSURES: CountryExposureEntry[] = [
  {
    code: "UAE",
    name: "United Arab Emirates",
    nameAr: "الإمارات العربية المتحدة",
    exposureUsd: 980_000_000,
    stressLevel: 0.72,
    primaryDriver: "Interbank lending rate spike — overnight liquidity crisis across major banks",
    primaryDriverAr: "ارتفاع أسعار الإقراض بين البنوك — أزمة سيولة ليلية عبر البنوك الكبرى",
    transmissionChannel: "Interbank rates → deposit flight → payment system delays",
    transmissionChannelAr: "أسعار ما بين البنوك → هروب الودائع → تأخير نظام المدفوعات",
  },
  {
    code: "KSA",
    name: "Saudi Arabia",
    nameAr: "المملكة العربية السعودية",
    exposureUsd: 850_000_000,
    stressLevel: 0.68,
    primaryDriver: "Term deposit withdrawal acceleration — SAR liquidity squeeze",
    primaryDriverAr: "تسارع سحب الودائع لأجل — ضغط سيولة الريال السعودي",
    transmissionChannel: "Deposit flight → reserve drawdown → credit tightening",
    transmissionChannelAr: "هروب الودائع → سحب الاحتياطي → تشديد الائتمان",
  },
  {
    code: "QAT",
    name: "Qatar",
    nameAr: "قطر",
    exposureUsd: 480_000_000,
    stressLevel: 0.58,
    primaryDriver: "Cross-border USD funding freeze — QAR swap line pressure",
    primaryDriverAr: "تجميد التمويل بالدولار العابر للحدود — ضغط خطوط مبادلة الريال القطري",
    transmissionChannel: "USD funding → banking reserves → sovereign guarantee calls",
    transmissionChannelAr: "تمويل الدولار → احتياطيات البنوك → مطالبات الضمانات السيادية",
  },
  {
    code: "BHR",
    name: "Bahrain",
    nameAr: "البحرين",
    exposureUsd: 290_000_000,
    stressLevel: 0.48,
    primaryDriver: "Offshore banking sector liquidity spillover",
    primaryDriverAr: "تسرب سيولة قطاع الخدمات المصرفية الخارجية",
    transmissionChannel: "Offshore banking → domestic credit → real estate financing",
    transmissionChannelAr: "الخدمات المصرفية الخارجية → الائتمان المحلي → تمويل العقارات",
  },
];

export const MOCK_LIQUIDITY_OUTCOMES = {
  baseCase: {
    label: "Base Case (No Intervention)",
    labelAr: "السيناريو الأساسي (بدون تدخل)",
    lossLow: 2_400_000_000,
    lossHigh: 3_050_000_000,
    recoveryDays: 21,
    description: "Liquidity crisis propagates across GCC banking system. Interbank markets freeze, payment settlements delayed. Recovery requires coordinated central bank response.",
    descriptionAr: "انتشار أزمة السيولة عبر النظام المصرفي الخليجي. تجميد أسواق ما بين البنوك وتأخير تسويات المدفوعات. التعافي يتطلب استجابة منسقة من البنوك المركزية.",
  } as OutcomeScenario,
  mitigatedCase: {
    label: "Mitigated Case (Coordinated Injection)",
    labelAr: "السيناريو المخفف (ضخ منسق)",
    lossLow: 1_100_000_000,
    lossHigh: 1_500_000_000,
    recoveryDays: 10,
    description: "Coordinated liquidity injection + emergency interbank facility + payment rail contingency. Deposit confidence restored within 5 days.",
    descriptionAr: "ضخ سيولة منسق + تسهيل طوارئ بين البنوك + احتياطي مسارات المدفوعات. استعادة ثقة المودعين خلال 5 أيام.",
  } as OutcomeScenario,
  valueSaved: {
    low: 900_000_000,
    high: 1_950_000_000,
    description: "Estimated value preserved through coordinated central bank intervention across 3 GCC monetary authorities.",
    descriptionAr: "القيمة المقدرة المحفوظة من خلال التدخل المنسق للبنوك المركزية عبر 3 سلطات نقدية خليجية.",
  },
};

export const MOCK_LIQUIDITY_SECTOR_DEPTH: Record<
  string,
  { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }
> = {
  banking: {
    topDriver: "Interbank overnight rate spike 280bps — deposit flight accelerating",
    secondOrderRisk: "Credit rating downgrade watch triggers margin calls on sovereign-linked instruments",
    confidenceLow: 0.80,
    confidenceHigh: 0.92,
  },
  insurance: {
    topDriver: "Insurance reserve drawdown pressure from banking sector guarantees",
    secondOrderRisk: "Policyholder surrender rates increase on liquidity anxiety",
    confidenceLow: 0.68,
    confidenceHigh: 0.82,
  },
  fintech: {
    topDriver: "Payment settlement SLA breaches — merchant transaction delays exceed 8 hours",
    secondOrderRisk: "Working capital facility drawdowns trigger cascade across SME sector",
    confidenceLow: 0.72,
    confidenceHigh: 0.85,
  },
  government: {
    topDriver: "Regulatory intervention triggers — coordinated GCC stability response activated",
    secondOrderRisk: "Sovereign guarantee capacity tested — fiscal buffer utilization accelerates",
    confidenceLow: 0.75,
    confidenceHigh: 0.88,
  },
  real_estate: {
    topDriver: "Mortgage lending freeze as banks conserve capital buffers",
    secondOrderRisk: "Off-plan project financing halted — developer cash flow crisis",
    confidenceLow: 0.60,
    confidenceHigh: 0.76,
  },
  trade: {
    topDriver: "Trade finance letter of credit issuance suspended",
    secondOrderRisk: "Import-dependent supply chains face 5-7 day procurement delays",
    confidenceLow: 0.58,
    confidenceHigh: 0.74,
  },
};

export const MOCK_LIQUIDITY_EXPLANATION = {
  narrative_en:
    "A regional liquidity stress event — triggered by a sudden interbank rate spike of 280bps — cascades through the GCC banking system via three primary channels: (1) interbank lending freeze, with UAE and Saudi banks facing acute overnight funding pressure; (2) deposit flight acceleration, with SAR 18B withdrawn from term deposits within 72 hours; and (3) cross-border contagion, as Qatari banks face USD funding squeeze through frozen lending facilities. Total estimated financial exposure reaches $2.2B–$3.1B over the 14-day horizon, with peak stress on Day 6. Recovery timeline is 21 days assuming coordinated central bank intervention within 48 hours.",
  narrative_ar:
    "حدث ضغط سيولة إقليمي — ناتج عن ارتفاع مفاجئ في أسعار ما بين البنوك بمقدار 280 نقطة أساس — ينتشر عبر النظام المصرفي الخليجي من خلال ثلاث قنوات رئيسية: تجميد الإقراض بين البنوك، وتسارع هروب الودائع، والعدوى العابرة للحدود.",
  methodology: "Multi-layer banking stress analysis covering 24 GCC financial entities across banking, fintech, insurance, and regulatory sectors. Liquidity stress index derived from interbank rate spreads, deposit flow analysis, and cross-border funding gap metrics.",
  confidence: 0.82,
  total_steps: 6,
};

export const MOCK_LIQUIDITY_TRUST = {
  trace_id: "trc_20260410_093000_liquidity",
  audit_id: "aud_cc_002",
  audit_hash: "sha256:b5a3d9e02f4c8a17d6e3b2d5c9f8a4e3b2d5c9f8a4e3b2d5c9f8a4e3b2d5c9f8",
  model_version: "io-v4.0.0",
  pipeline_version: "unified-v2.1",
  confidence_score: 0.82,
  data_sources: ["SAMA Interbank Data", "CBUAE Liquidity Reports", "QCB Banking Statistics", "Bloomberg Terminal", "GCC Financial Stability Board"],
  stages_completed: ["macro_assessment", "propagation_analysis", "country_exposure", "banking_transmission", "insurance_absorption", "sector_impact", "decision_framework", "outcome_projection", "trust_verification"],
  warnings: ["Interbank rate data: 15min delayed", "Deposit flow estimates: T+1 reporting lag"],
};

// ── Scenario Registry (for switching) ────────────────────────────────

export type ScenarioKey = "hormuz" | "liquidity";

export interface ScenarioPreset {
  key: ScenarioKey;
  labelEn: string;
  labelAr: string;
  templateId: string;
  domain: string;
}

export const SCENARIO_PRESETS: ScenarioPreset[] = [
  { key: "hormuz", labelEn: "Hormuz Energy Disruption", labelAr: "اضطراب طاقة هرمز", templateId: "hormuz_chokepoint_disruption", domain: "ENERGY_TRADE" },
  { key: "liquidity", labelEn: "Regional Liquidity Stress", labelAr: "ضغط سيولة إقليمي", templateId: "regional_liquidity_stress_event", domain: "LIQUIDITY" },
];

// ── Trust Metadata ────────────────────────────────────────────────────

export const MOCK_TRUST = {
  trace_id: "trc_20260408_061400_hormuz",
  audit_id: "aud_cc_001",
  audit_hash: "sha256:a4f2c8d91e3b7f06e5d2a1c4b8f7e3d2a1c4b8f7e3d2a1c4b8f7e3d2a1c4b8f7",
  model_version: "io-v4.0.0",
  pipeline_version: "unified-v2.1",
  confidence_score: 0.84,
  data_sources: ["ACLED Conflict Data", "Maritime Traffic Intelligence", "Bloomberg Terminal", "SAMA Open Data", "GCC Central Bank Reports"],
  stages_completed: ["macro_assessment", "propagation_analysis", "country_exposure", "banking_transmission", "insurance_absorption", "sector_impact", "decision_framework", "outcome_projection", "trust_verification"],
  warnings: ["Maritime traffic data: 12min settlement delay", "Commodity prices: 5min delayed"],
};
