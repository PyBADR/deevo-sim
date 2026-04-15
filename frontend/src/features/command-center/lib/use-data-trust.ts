/**
 * useDataTrust — hook returning static data trust metadata for the active scenario.
 *
 * Returns safe static fallback metadata from the Data Trust Layer.
 * No live data is connected. No API calls are made.
 *
 * When a live provenance API endpoint becomes available, this hook
 * can be updated to fetch from it — the component interface stays the same.
 */

import { useMemo } from "react";
import type { DataTrustMeta } from "../components/DataTrustPanel";

/**
 * Static confidence baselines per scenario type.
 * These come from the backend Data Trust Layer source_registry
 * (src_scenario_catalog.confidence_weight = 0.85).
 *
 * Scenario-specific adjustments based on data completeness:
 *   - Well-studied scenarios (Hormuz, Saudi Oil): 0.85
 *   - Moderate data scenarios: 0.80
 *   - Less-studied scenarios: 0.75
 */
const SCENARIO_CONFIDENCE: Record<string, number> = {
  hormuz_chokepoint_disruption: 0.85,
  hormuz_full_closure: 0.82,
  saudi_oil_shock: 0.85,
  uae_banking_crisis: 0.83,
  gcc_cyber_attack: 0.80,
  qatar_lng_disruption: 0.83,
  bahrain_sovereign_stress: 0.78,
  kuwait_fiscal_shock: 0.80,
  oman_port_closure: 0.78,
  red_sea_trade_corridor_instability: 0.80,
  energy_market_volatility_shock: 0.82,
  regional_liquidity_stress_event: 0.79,
  critical_port_throughput_disruption: 0.78,
  financial_infrastructure_cyber_disruption: 0.77,
  iran_regional_escalation: 0.75,
};

/** Default confidence when scenario is unknown */
const DEFAULT_CONFIDENCE = 0.75;

/** Total registered sources in the backend Data Trust Layer */
const REGISTERED_SOURCES = 15;

/** Live sources currently connected (always 0 in v1) */
const LIVE_SOURCES_CONNECTED = 0;

/**
 * Returns data trust metadata for the active scenario.
 *
 * All values are static fallback in v1 — no API calls, no live feeds.
 */
export function useDataTrust(scenarioId: string | null): DataTrustMeta {
  return useMemo<DataTrustMeta>(() => {
    const confidence = scenarioId
      ? SCENARIO_CONFIDENCE[scenarioId] ?? DEFAULT_CONFIDENCE
      : DEFAULT_CONFIDENCE;

    return {
      sourceMode: "static_fallback",
      sourceType: "static",
      freshness: "unknown",
      lastUpdated: "Static baseline — 2026-04-10",
      confidenceScore: confidence,
      auditStatus: "Source-aware, live feeds not connected",
      auditStatusAr: "واعٍ بالمصادر، البيانات الحية غير متصلة",
      registeredSources: REGISTERED_SOURCES,
      liveSourcesConnected: LIVE_SOURCES_CONNECTED,
      provenanceTracked: true,
    };
  }, [scenarioId]);
}
