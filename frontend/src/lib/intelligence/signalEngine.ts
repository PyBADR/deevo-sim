/**
 * Impact Observatory | مرصد الأثر — Signal Engine
 *
 * Implements the Signal-to-Decision cascade:
 *   Signal → Country Impact → Sector Transmission → Entity Exposure → Decision Shift
 *
 * Signals from scenarioIntelligence.ts are processed to produce:
 *   - Per-signal activation state (active / dormant / resolved)
 *   - Aggregate signal amplifier for sector stress
 *   - Country-specific signal pressure
 *   - Decision urgency modification
 */

import type { IntelligenceSignal, SignalType } from '../scenarioIntelligence';
import { getIntelligence } from '../scenarioIntelligence';
import type { GCCCountry } from './countryState';

/* ── Types ── */

export type SignalActivationState = 'dormant' | 'emerging' | 'active' | 'peak' | 'declining' | 'resolved';

export interface ActiveSignal {
  /** Original signal definition */
  signal: IntelligenceSignal;
  /** Current activation state */
  state: SignalActivationState;
  /** Activation intensity 0–1 */
  intensity: number;
  /** Hours since this signal first activated */
  activeHours: number;
  /** Country-level pressure contribution */
  countryPressure: Partial<Record<GCCCountry, number>>;
}

export interface SignalEngineOutput {
  /** All signals with their activation states */
  activeSignals: ActiveSignal[];
  /** Aggregate amplifier for sector stress computation (0–1) */
  sectorAmplifier: number;
  /** Decision urgency modifier (multiplier, 1.0 = no change) */
  decisionUrgencyMod: number;
  /** Count of signals at peak intensity */
  peakCount: number;
  /** Count of signals currently active (emerging + active + peak) */
  activeCount: number;
}

/* ── Signal Type → Country Impact Weights ──
   How much each signal type pressures each GCC country.
   Geopolitical signals hit all countries; Market signals
   primarily hit trade-dependent economies.
*/

const SIGNAL_TYPE_COUNTRY_WEIGHTS: Record<SignalType, Record<GCCCountry, number>> = {
  Economic: {
    SA: 0.75, AE: 0.70, KW: 0.65, QA: 0.55, BH: 0.60, OM: 0.60,
  },
  Geopolitical: {
    SA: 0.80, AE: 0.70, KW: 0.65, QA: 0.60, BH: 0.75, OM: 0.65,
  },
  Market: {
    SA: 0.70, AE: 0.80, KW: 0.60, QA: 0.65, BH: 0.55, OM: 0.55,
  },
  Operational: {
    SA: 0.60, AE: 0.75, KW: 0.50, QA: 0.55, BH: 0.50, OM: 0.60,
  },
  Regulatory: {
    SA: 0.55, AE: 0.65, KW: 0.50, QA: 0.50, BH: 0.60, OM: 0.50,
  },
};

/* ── Signal Type → Urgency Weight ── */

const SIGNAL_TYPE_URGENCY: Record<SignalType, number> = {
  Geopolitical: 1.4,
  Market:       1.3,
  Economic:     1.2,
  Operational:  1.1,
  Regulatory:   1.0,
};

/* ── Computation ── */

/**
 * Compute signal activation state based on scenario progress.
 * Each signal has a lifecycle: dormant → emerging → active → peak → declining → resolved
 */
function computeSignalState(
  signalIndex: number,
  totalSignals: number,
  t: number,
): { state: SignalActivationState; intensity: number } {
  // Each signal activates at a staggered time
  const activationPoint = 0.05 + (signalIndex / Math.max(totalSignals, 1)) * 0.35;
  const peakPoint = activationPoint + 0.15;
  const declinePoint = peakPoint + 0.25;

  if (t < activationPoint) {
    return { state: 'dormant', intensity: 0 };
  }
  if (t < activationPoint + 0.05) {
    const progress = (t - activationPoint) / 0.05;
    return { state: 'emerging', intensity: progress * 0.5 };
  }
  if (t < peakPoint) {
    const progress = (t - (activationPoint + 0.05)) / (peakPoint - activationPoint - 0.05);
    return { state: 'active', intensity: 0.5 + progress * 0.5 };
  }
  if (t < declinePoint) {
    return { state: 'peak', intensity: 1.0 };
  }
  if (t < 0.9) {
    const progress = (t - declinePoint) / (0.9 - declinePoint);
    return { state: 'declining', intensity: Math.max(0.2, 1.0 - progress * 0.6) };
  }
  return { state: 'resolved', intensity: 0.15 };
}

/**
 * Process all signals for a scenario at a given progress point.
 */
export function processSignals(
  scenarioId: string,
  t: number,
  elapsedHours: number,
): SignalEngineOutput {
  const intel = getIntelligence(scenarioId);
  if (!intel) {
    return {
      activeSignals: [],
      sectorAmplifier: 0,
      decisionUrgencyMod: 1.0,
      peakCount: 0,
      activeCount: 0,
    };
  }

  const activeSignals: ActiveSignal[] = intel.signals.map((signal, i) => {
    const { state, intensity } = computeSignalState(i, intel.signals.length, t);

    // Compute per-country pressure from this signal
    const weights = SIGNAL_TYPE_COUNTRY_WEIGHTS[signal.type];
    const countryPressure: Partial<Record<GCCCountry, number>> = {};
    for (const [code, weight] of Object.entries(weights)) {
      countryPressure[code as GCCCountry] = intensity * weight;
    }

    return {
      signal,
      state,
      intensity,
      activeHours: state === 'dormant' ? 0 : elapsedHours * (intensity > 0 ? 1 : 0),
      countryPressure,
    };
  });

  // Aggregate sector amplifier: average intensity of all active signals
  const activeIntensities = activeSignals
    .filter(s => s.intensity > 0)
    .map(s => s.intensity);
  const sectorAmplifier = activeIntensities.length > 0
    ? activeIntensities.reduce((sum, v) => sum + v, 0) / activeIntensities.length
    : 0;

  // Decision urgency modifier: weighted by signal type urgency
  const urgencyWeights = activeSignals
    .filter(s => s.intensity > 0.3)
    .map(s => s.intensity * SIGNAL_TYPE_URGENCY[s.signal.type]);
  const decisionUrgencyMod = urgencyWeights.length > 0
    ? Math.min(2.5, 1.0 + urgencyWeights.reduce((sum, v) => sum + v, 0) / urgencyWeights.length * 0.5)
    : 1.0;

  const peakCount = activeSignals.filter(s => s.state === 'peak').length;
  const activeCount = activeSignals.filter(s =>
    s.state === 'emerging' || s.state === 'active' || s.state === 'peak',
  ).length;

  return {
    activeSignals,
    sectorAmplifier,
    decisionUrgencyMod,
    peakCount,
    activeCount,
  };
}
