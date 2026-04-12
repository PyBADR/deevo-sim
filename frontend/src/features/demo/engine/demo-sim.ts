/**
 * Demo Simulation Engine — Lightweight, deterministic, no backend.
 *
 * Architecture:
 *   1. DECISION_EFFECTS maps each decision index → sector stress deltas
 *   2. useReducer holds { activatedDecisions, sectorStress, computed losses }
 *   3. When a decision is toggled, sector stresses update → losses recompute
 *
 * All math is additive (deltas on 0-1 stress scale). Losses are weighted sums.
 * This is a presentation-grade simulation, not a production risk engine.
 */

import { useReducer, useCallback, useMemo } from "react";
import { demoScenario } from "../data/demo-scenario";

/* ═══════════════════════════════════════════════════════════════════
 * SECTOR KEYS — stable indices matching demoScenario.sectors order
 * 0: Oil & Gas
 * 1: Banking & Finance
 * 2: Insurance
 * 3: Fintech & Payments
 * 4: Real Estate
 * 5: Government & Fiscal
 * ═══════════════════════════════════════════════════════════════════ */

/** Stress delta per sector when a decision is activated. Negative = stress reduced. */
export interface DecisionEffect {
  /** Map of sector index → stress delta (e.g. -0.15 = reduce 15 points) */
  sectorDeltas: Record<number, number>;
  /** Flat $B reduction to the "with action" loss estimate */
  lossReductionB: number;
}

/**
 * DECISION_EFFECTS[i] = effect of activating decision i.
 * Indices match demoScenario.decisions order.
 */
export const DECISION_EFFECTS: DecisionEffect[] = [
  // 0: Activate strategic petroleum reserves
  {
    sectorDeltas: { 0: -0.15, 1: -0.04, 5: -0.06 },
    lossReductionB: 0.18,
  },
  // 1: Inject emergency liquidity into interbank market
  {
    sectorDeltas: { 1: -0.14, 2: -0.06, 3: -0.08, 5: -0.05 },
    lossReductionB: 0.15,
  },
  // 2: Reroute maritime traffic via alternative corridors
  {
    sectorDeltas: { 0: -0.08, 2: -0.10, 4: -0.04 },
    lossReductionB: 0.10,
  },
  // 3: Adjust credit exposure limits on energy sector
  {
    sectorDeltas: { 1: -0.08, 3: -0.05, 5: -0.04 },
    lossReductionB: 0.08,
  },
  // 4: Stabilize digital payment rails and settlement systems
  {
    sectorDeltas: { 3: -0.12, 1: -0.03 },
    lossReductionB: 0.05,
  },
];

/* ═══════════════════════════════════════════════════════════════════
 * STATE
 * ═══════════════════════════════════════════════════════════════════ */

export interface SimSnapshot {
  /** Current stress per sector (0–1), reflecting all activated decisions */
  sectorStress: number[];
  /** Set of decision indices currently activated */
  activatedDecisions: Set<number>;
  /** Computed "with action" loss in $B — decreases as decisions are activated */
  withActionLossB: number;
  /** Computed "without action" loss in $B — always the baseline */
  withoutActionLossB: number;
  /** Computed delta saved in $M */
  savedM: number;
  /** Number of decisions activated */
  decisionsActivated: number;
  /** Which sector indices changed in the LAST action (for animation) */
  lastAffectedSectors: number[];
}

/* ── Internal reducer state (Set is not directly reducible, use array) ── */

interface SimState {
  activatedDecisions: number[]; // sorted indices
  sectorStress: number[];       // current values
  lastAffectedSectors: number[];
}

type SimAction =
  | { type: "TOGGLE_DECISION"; index: number }
  | { type: "RESET" };

const BASE_STRESS: number[] = demoScenario.sectors.map((s) => s.currentStress);
const BASE_WITHOUT_ACTION_B = 4.9;

/** Weighted sector → loss contribution (sums to ~1.0) */
const SECTOR_LOSS_WEIGHTS: number[] = [
  0.28, // Oil & Gas — dominant
  0.22, // Banking & Finance
  0.18, // Insurance
  0.10, // Fintech & Payments
  0.07, // Real Estate
  0.15, // Government & Fiscal
];

function computeWithActionLoss(stressValues: number[], activatedDecisions: number[]): number {
  // Base with-action loss is 4.3B. Each activated decision reduces it by its lossReductionB.
  // Additionally, stress reduction affects the weighted sum.
  let totalReduction = 0;
  for (const idx of activatedDecisions) {
    const effect = DECISION_EFFECTS[idx];
    if (effect) totalReduction += effect.lossReductionB;
  }

  // Stress-weighted component: average stress ratio vs baseline affects remaining loss
  let stressRatio = 0;
  for (let i = 0; i < stressValues.length; i++) {
    const baseStress = BASE_STRESS[i];
    const ratio = baseStress > 0 ? stressValues[i] / baseStress : 1;
    stressRatio += ratio * SECTOR_LOSS_WEIGHTS[i];
  }

  // With-action loss = base * stressRatio - directReduction
  // Floor at a minimum loss (can't go below $2.8B in this scenario)
  const raw = 4.3 * stressRatio - totalReduction * 0.3; // partial attribution to avoid double-counting
  return Math.max(2.8, Math.min(4.3, parseFloat(raw.toFixed(2))));
}

function simReducer(state: SimState, action: SimAction): SimState {
  switch (action.type) {
    case "TOGGLE_DECISION": {
      const idx = action.index;
      const isActive = state.activatedDecisions.includes(idx);
      const nextDecisions = isActive
        ? state.activatedDecisions.filter((d) => d !== idx)
        : [...state.activatedDecisions, idx].sort((a, b) => a - b);

      // Recompute stress from scratch (BASE + all active deltas)
      const nextStress = [...BASE_STRESS];
      for (const dIdx of nextDecisions) {
        const effect = DECISION_EFFECTS[dIdx];
        if (!effect) continue;
        for (const [sectorIdx, delta] of Object.entries(effect.sectorDeltas)) {
          const si = Number(sectorIdx);
          nextStress[si] = Math.max(0, Math.min(1, nextStress[si] + delta));
        }
      }

      // Track which sectors changed
      const affected: number[] = [];
      const effect = DECISION_EFFECTS[idx];
      if (effect) {
        for (const sectorIdx of Object.keys(effect.sectorDeltas)) {
          affected.push(Number(sectorIdx));
        }
      }

      return {
        activatedDecisions: nextDecisions,
        sectorStress: nextStress,
        lastAffectedSectors: affected,
      };
    }

    case "RESET":
      return {
        activatedDecisions: [],
        sectorStress: [...BASE_STRESS],
        lastAffectedSectors: [],
      };

    default:
      return state;
  }
}

/* ═══════════════════════════════════════════════════════════════════
 * HOOK
 * ═══════════════════════════════════════════════════════════════════ */

export function useDemoSim() {
  const [state, dispatch] = useReducer(simReducer, {
    activatedDecisions: [],
    sectorStress: [...BASE_STRESS],
    lastAffectedSectors: [],
  });

  const toggleDecision = useCallback((index: number) => {
    dispatch({ type: "TOGGLE_DECISION", index });
  }, []);

  const resetSim = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  const snapshot: SimSnapshot = useMemo(() => {
    const withActionLossB = computeWithActionLoss(
      state.sectorStress,
      state.activatedDecisions,
    );
    const withoutActionLossB = BASE_WITHOUT_ACTION_B;
    const savedM = Math.round((withoutActionLossB - withActionLossB) * 1000);

    return {
      sectorStress: state.sectorStress,
      activatedDecisions: new Set(state.activatedDecisions),
      withActionLossB,
      withoutActionLossB,
      savedM,
      decisionsActivated: state.activatedDecisions.length,
      lastAffectedSectors: state.lastAffectedSectors,
    };
  }, [state]);

  return { snapshot, toggleDecision, resetSim };
}
