/**
 * Impact Observatory | مرصد الأثر — Unified Adapter
 *
 * Converts UnifiedRunResult (from POST /graph/unified-run)
 * → RunResult (consumed by ExecutiveDashboard and legacy pages).
 *
 * This adapter exists because:
 * 1. The unified pipeline produces a different shape than pipeline_v4
 * 2. The Dashboard is typed to RunResult
 * 3. We need both pipelines to feed the same UI until full migration
 *
 * Zero logic duplication — only structural mapping.
 */

import type {
  RunResult,
  UnifiedRunResult,
  FinancialImpact,
  BankingStress,
  InsuranceStress,
  FintechStress,
  DecisionPlan,
  ExplanationPack,
  RunHeadline,
  Classification,
  BusinessSeverity,
  ExecutiveStatus,
  TimelineStep,
  RegulatoryEvent,
} from "@/types/observatory";

/**
 * Convert UnifiedRunResult → RunResult for Dashboard consumption.
 *
 * Maps unified pipeline output (graph-centric) to the legacy RunResult
 * shape (sector-centric) that ExecutiveDashboard expects.
 */
export function unifiedToRunResult(unified: UnifiedRunResult): RunResult {
  // Defensive: ensure top-level objects exist even if payload is partial
  const uHeadline = unified.headline ?? { total_loss_usd: 0, total_nodes_impacted: 0, propagation_depth: 0 };
  const uScenario = unified.scenario ?? { template_id: "", label: "", severity: 0, horizon_hours: 168 };
  const mapPayload = unified.map_payload ?? { impacted_entities: [], total_estimated_loss_usd: 0 };
  const sectorRollups = unified.sector_rollups ?? { banking: {} as any, insurance: {} as any, fintech: {} as any };
  const decisionInputs = unified.decision_inputs ?? { run_id: "", total_loss_usd: 0, actions: [], all_actions: [] };
  const graphPayload = unified.graph_payload ?? { nodes: [], edges: [], categories: [] };
  const warnings = unified.warnings ?? [];
  const confidence = unified.confidence ?? 0.1;
  const sectors = unified.sectors;
  const math = unified.math;
  const physics = unified.physics;

  // ── Financial Impacts ───────────────────────────────────
  const financial: FinancialImpact[] = (sectors?.financial_impacts ?? []).map(
    (fi) => ({
      entity_id: fi.entity_id,
      entity_label: fi.entity_id.replace(/_/g, " "),
      sector: fi.entity_id.split("_")[0] ?? "finance",
      loss_usd: fi.loss ?? 0,
      loss_pct_gdp: fi.loss ? fi.loss / 2.1e12 : 0,
      peak_day: 1,
      recovery_days: 7,
      confidence: confidence,
      stress_level: fi.loss && fi.exposure ? fi.loss / fi.exposure : 0,
      classification: _classifyStress(
        fi.loss && fi.exposure ? fi.loss / fi.exposure : 0
      ),
    })
  );

  // ── Banking Stress ──────────────────────────────────────
  const bankingAgg = sectors?.banking_aggregate ?? ({} as Record<string, unknown>);
  const banking: BankingStress = {
    run_id: unified.run_id,
    total_exposure_usd: uHeadline.total_loss_usd,
    liquidity_stress:
      1.0 - ((bankingAgg.aggregate_lcr as number) ?? 1.0),
    credit_stress:
      1.0 - ((bankingAgg.aggregate_cet1 as number) ?? 0.045),
    fx_stress: 0.3,
    interbank_contagion: confidence < 0.5 ? 0.7 : 0.3,
    time_to_liquidity_breach_hours: 72,
    capital_adequacy_impact_pct:
      ((bankingAgg.aggregate_car as number) ?? 0.08) * 100,
    aggregate_stress:
      sectorRollups?.banking?.aggregate_stress ?? 0,
    classification: _classifyStress(
      sectorRollups?.banking?.aggregate_stress ?? 0
    ),
    affected_institutions: (sectors?.banking_stresses ?? []).map((bs) => ({
      id: bs.entity_id,
      name: bs.entity_id.replace(/_/g, " "),
      name_ar: "",
      country: "GCC",
      exposure_usd: 0,
      stress: 1.0 - bs.lcr,
      projected_car_pct: bs.capital_adequacy_ratio * 100,
    })),
  };

  // ── Insurance Stress ────────────────────────────────────
  const insAgg = sectors?.insurance_aggregate ?? ({} as Record<string, unknown>);
  const insurance: InsuranceStress = {
    run_id: unified.run_id,
    portfolio_exposure_usd: uHeadline.total_loss_usd * 0.15,
    claims_surge_multiplier:
      (insAgg.claims_spike as number) ?? 1.0,
    severity_index: uScenario.severity,
    loss_ratio: 0.75,
    combined_ratio:
      (insAgg.aggregate_combined_ratio as number) ?? 1.0,
    underwriting_status: "stressed",
    time_to_insolvency_hours: 168,
    reinsurance_trigger: true,
    ifrs17_risk_adjustment_pct: 15,
    aggregate_stress:
      sectorRollups?.insurance?.aggregate_stress ?? 0,
    classification: _classifyStress(
      sectorRollups?.insurance?.aggregate_stress ?? 0
    ),
    affected_lines: (sectors?.insurance_stresses ?? []).map((is_) => ({
      id: is_.entity_id,
      name: is_.entity_id.replace(/_/g, " "),
      name_ar: "",
      exposure_usd: 0,
      claims_surge: 1.0 - is_.solvency_ratio,
      stress: is_.combined_ratio,
    })),
  };

  // ── Fintech Stress ──────────────────────────────────────
  const ftAgg = sectors?.fintech_aggregate ?? ({} as Record<string, unknown>);
  const fintech: FintechStress = {
    run_id: unified.run_id,
    payment_volume_impact_pct:
      (1.0 - ((ftAgg.aggregate_service_availability as number) ?? 1.0)) * 100,
    settlement_delay_hours:
      ((ftAgg.aggregate_settlement_delay_min as number) ?? 0) / 60,
    api_availability_pct:
      ((ftAgg.aggregate_service_availability as number) ?? 1.0) * 100,
    cross_border_disruption: 0.5,
    digital_banking_stress:
      sectorRollups?.fintech?.aggregate_stress ?? 0,
    time_to_payment_failure_hours: 48,
    aggregate_stress:
      sectorRollups?.fintech?.aggregate_stress ?? 0,
    classification: _classifyStress(
      sectorRollups?.fintech?.aggregate_stress ?? 0
    ),
    affected_platforms: (sectors?.fintech_stresses ?? []).map((ft) => ({
      id: ft.entity_id,
      name: ft.entity_id.replace(/_/g, " "),
      name_ar: "",
      country: "GCC",
      volume_impact_pct: (1.0 - ft.service_availability) * 100,
      cross_border_stress: 0.5,
      stress: 1.0 - ft.service_availability,
    })),
  };

  // ── Decision Plan ───────────────────────────────────────
  const dpActions = sectors?.decision_plan?.actions ?? [];
  const decisions: DecisionPlan = {
    run_id: unified.run_id,
    scenario_label: uScenario.label,
    total_loss_usd: uHeadline.total_loss_usd,
    peak_day: 1,
    time_to_failure_hours: 72,
    actions: dpActions.map((a) => ({
      id: a.action_id,
      action: `${a.action_type}: ${a.target_ref}`,
      action_ar: null,
      sector: a.target_ref?.split("_")[0] ?? "finance",
      owner: "Risk Committee",
      urgency: a.urgency,
      value: a.value,
      regulatory_risk: 0.5,
      priority: a.priority_score,
      time_to_act_hours: a.execution_window_hours,
      time_to_failure_hours: 72,
      loss_avoided_usd: a.expected_loss_reduction,
      cost_usd: 0,
      confidence: a.feasibility,
    })),
    all_actions: dpActions.map((a) => ({
      id: a.action_id,
      action: `${a.action_type}: ${a.target_ref}`,
      action_ar: null,
      sector: a.target_ref?.split("_")[0] ?? "finance",
      owner: "Risk Committee",
      urgency: a.urgency,
      value: a.value,
      regulatory_risk: 0.5,
      priority: a.priority_score,
      time_to_act_hours: a.execution_window_hours,
      time_to_failure_hours: 72,
      loss_avoided_usd: a.expected_loss_reduction,
      cost_usd: 0,
      confidence: a.feasibility,
    })),
  };

  // ── Explanation ─────────────────────────────────────────
  const expData = sectors?.explanation;
  const explanation: ExplanationPack = {
    run_id: unified.run_id,
    scenario_label: uScenario.label,
    narrative_en: expData?.summary ?? "",
    narrative_ar: "",
    causal_chain: (expData?.drivers ?? []).map((d, i) => ({
      step: i + 1,
      entity_id: "",
      entity_label: d.driver,
      entity_label_ar: null,
      event: d.driver,
      event_ar: null,
      impact_usd: d.magnitude,
      stress_delta: 0,
      mechanism: d.unit,
    })),
    total_steps: expData?.drivers?.length ?? 0,
    headline_loss_usd: uHeadline.total_loss_usd,
    peak_day: 1,
    confidence: confidence,
    methodology: "Unified pipeline: quality→graph→physics→math→sector→decision",
  };

  // ── Headline ────────────────────────────────────────────
  const impactedEntities = mapPayload.impacted_entities ?? [];
  const headline: RunHeadline = {
    total_loss_usd: uHeadline.total_loss_usd,
    peak_day: 1,
    max_recovery_days: uScenario.horizon_hours / 24,
    average_stress:
      impactedEntities.reduce(
        (s: number, e: any) => s + (e.stress ?? 0),
        0
      ) / Math.max(impactedEntities.length, 1),
    affected_entities: uHeadline.total_nodes_impacted,
    critical_count: impactedEntities.filter(
      (e: any) => e.classification === "CRITICAL"
    ).length,
    elevated_count: impactedEntities.filter(
      (e: any) => e.classification === "ELEVATED"
    ).length,
  };

  // ── Severity / Status ───────────────────────────────────
  const avgStress = headline.average_stress;
  const businessSeverity: BusinessSeverity =
    avgStress >= 0.7
      ? "severe"
      : avgStress >= 0.5
        ? "high"
        : avgStress >= 0.3
          ? "medium"
          : "low";
  const executiveStatus: ExecutiveStatus =
    avgStress >= 0.7
      ? "crisis"
      : avgStress >= 0.5
        ? "escalate"
        : avgStress >= 0.3
          ? "intervene"
          : "monitor";

  // ── Regulatory Events ───────────────────────────────────
  const regState = sectors?.regulatory_state;
  const regulatoryEvents: RegulatoryEvent[] = regState
    ? [
        {
          timestep: 0,
          breach_level: (regState.breach_level as RegulatoryEvent["breach_level"]) ?? "none",
          mandatory_actions: regState.mandatory_actions ?? [],
          sector: "cross_sector",
        },
      ]
    : [];

  return {
    schema_version: "4.0.0",
    run_id: unified.run_id,
    status: unified.status,
    pipeline_stages_completed: (unified.stages_completed ?? []).length,
    scenario: {
      ...uScenario,
      label_ar: null,
    },
    headline,
    financial,
    banking,
    insurance,
    fintech,
    decisions,
    explanation,
    business_severity: businessSeverity,
    executive_status: executiveStatus,
    model_version: "4.0.0",
    global_confidence: confidence,
    assumptions: unified.assumptions ?? [],
    audit_hash: unified.trust?.audit_hash ?? "",
    stages_completed: unified.stages_completed ?? [],
    stage_log: (unified.stage_log ?? {}) as RunResult["stage_log"],
    timeline: [],
    regulatory_events: regulatoryEvents,
    executive_report: {},
    flow_states: [],
    propagation: unified.propagation_steps ?? [],
    duration_ms: unified.duration_ms ?? 0,
  };
}

function _classifyStress(stress: number): Classification {
  if (stress >= 0.8) return "CRITICAL";
  if (stress >= 0.6) return "ELEVATED";
  if (stress >= 0.4) return "MODERATE";
  if (stress >= 0.2) return "LOW";
  return "NOMINAL";
}
