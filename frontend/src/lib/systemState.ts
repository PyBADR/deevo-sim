/**
 * Impact Observatory | مرصد الأثر — Global System State
 *
 * Zustand store for scenario activation and simulation state.
 * Single source of truth for whether the system is idle or active.
 *
 * State model:
 *   idle → running → escalating → resolved
 *
 * Integrates the intelligence core: on every tick, the full
 * intelligence loop runs (Signal → Country → Sector → Entity →
 * Propagation → Decision → Monitoring) and its output is stored
 * as `intelligence` alongside the existing `snapshot`.
 *
 * No backend dependency. All simulation is deterministic client-side.
 */

import { create } from 'zustand';
import {
  runIntelligenceLoop,
  IDLE_INTELLIGENCE,
  type IntelligenceSnapshot,
} from './intelligence/systemLoop';
import { getScenario } from './scenarios';

/* ── Types ── */

export type SystemStatus = 'idle' | 'running' | 'escalating' | 'resolved';
export type ImpactState = 'Contained' | 'Expanding' | 'Cascading' | 'Stabilising' | 'Resolved';

export interface SimulationSnapshot {
  elapsedHours: number;
  horizonHours: number;
  confidence: number;
  riskScore: number;
  impactState: ImpactState;
  stressLevel: string;
  urgencyMultiplier: number;
  activeSectors: string[];
  evaluationDataPoints: number;
}

export interface SystemState {
  activeScenarioId: string | null;
  activeScenarioName: string;
  status: SystemStatus;
  snapshot: SimulationSnapshot;
  /** Intelligence core output — full macro state */
  intelligence: IntelligenceSnapshot;

  activateScenario: (id: string, name: string, horizonHours: number) => void;
  tick: () => void;
  reset: () => void;
}

/* ── Default snapshot (idle) ── */

const IDLE_SNAPSHOT: SimulationSnapshot = {
  elapsedHours: 0,
  horizonHours: 0,
  confidence: 0,
  riskScore: 0,
  impactState: 'Contained',
  stressLevel: 'Nominal',
  urgencyMultiplier: 1.0,
  activeSectors: [],
  evaluationDataPoints: 0,
};

/* ── Deterministic simulation math (existing logic preserved) ── */

function computeSnapshot(
  elapsed: number,
  horizon: number,
): SimulationSnapshot {
  const t = Math.min(elapsed / Math.max(horizon, 1), 1);

  const riskScore = Math.min(
    1,
    1 / (1 + Math.exp(-12 * (t - 0.35))) * 0.85 + t * 0.1,
  );

  const confidence = Math.min(0.95, 0.25 + 0.7 * (1 - Math.exp(-3 * t)));

  let impactState: ImpactState;
  let stressLevel: string;
  if (t < 0.15) {
    impactState = 'Contained';
    stressLevel = 'Nominal';
  } else if (t < 0.35) {
    impactState = 'Expanding';
    stressLevel = 'Elevated';
  } else if (t < 0.6) {
    impactState = 'Cascading';
    stressLevel = 'High';
  } else if (t < 0.85) {
    impactState = 'Stabilising';
    stressLevel = 'Guarded';
  } else {
    impactState = 'Resolved';
    stressLevel = 'Nominal';
  }

  const urgencyMultiplier = t < 0.6
    ? 1.0 + riskScore * 1.5
    : Math.max(1.0, 2.5 - (t - 0.6) * 4);

  const allSectors = ['Energy', 'Banking', 'Logistics', 'Insurance', 'Sovereign'];
  const activeSectorCount = Math.min(
    allSectors.length,
    Math.floor(1 + t * allSectors.length),
  );
  const activeSectors = allSectors.slice(0, activeSectorCount);

  const evaluationDataPoints = t < 0.3
    ? 0
    : Math.floor((t - 0.3) / 0.7 * 6);

  return {
    elapsedHours: elapsed,
    horizonHours: horizon,
    confidence,
    riskScore,
    impactState,
    stressLevel,
    urgencyMultiplier,
    activeSectors,
    evaluationDataPoints,
  };
}

/* ── Intelligence integration helper ── */

function computeIntelligence(
  scenarioId: string,
  snapshot: SimulationSnapshot,
): IntelligenceSnapshot {
  // Get scenario decisions from manifest
  const scenario = getScenario(scenarioId);
  const decisions = scenario?.decisions ?? [];

  return runIntelligenceLoop(
    scenarioId,
    snapshot.elapsedHours,
    snapshot.horizonHours,
    snapshot.riskScore,
    decisions,
  );
}

/* ── Tick increment ── */

function tickHours(horizon: number): number {
  if (horizon <= 24) return 1;
  if (horizon <= 72) return 2;
  if (horizon <= 168) return 4;
  return 6;
}

/* ── Store ── */

export const useSystemState = create<SystemState>((set, get) => ({
  activeScenarioId: null,
  activeScenarioName: '',
  status: 'idle',
  snapshot: { ...IDLE_SNAPSHOT },
  intelligence: IDLE_INTELLIGENCE,

  activateScenario: (id, name, horizonHours) => {
    const snapshot = computeSnapshot(0, horizonHours);
    const intelligence = computeIntelligence(id, snapshot);

    set({
      activeScenarioId: id,
      activeScenarioName: name,
      status: 'running',
      snapshot,
      intelligence,
    });
  },

  tick: () => {
    const state = get();
    if (state.status === 'idle' || state.status === 'resolved') return;
    if (!state.activeScenarioId) return;

    const { elapsedHours, horizonHours } = state.snapshot;
    const increment = tickHours(horizonHours);
    const newElapsed = Math.min(elapsedHours + increment, horizonHours);
    const newSnapshot = computeSnapshot(newElapsed, horizonHours);

    // Run intelligence core
    const intelligence = computeIntelligence(state.activeScenarioId, newSnapshot);

    // Status transitions (existing logic preserved)
    let newStatus: SystemStatus = 'running';
    if (newSnapshot.impactState === 'Cascading') newStatus = 'escalating';
    if (newElapsed >= horizonHours) newStatus = 'resolved';

    // Override urgency multiplier with intelligence-derived value
    newSnapshot.urgencyMultiplier = intelligence.decision.urgencyMultiplier;

    set({
      status: newStatus,
      snapshot: newSnapshot,
      intelligence,
    });
  },

  reset: () => {
    set({
      activeScenarioId: null,
      activeScenarioName: '',
      status: 'idle',
      snapshot: { ...IDLE_SNAPSHOT },
      intelligence: IDLE_INTELLIGENCE,
    });
  },
}));
