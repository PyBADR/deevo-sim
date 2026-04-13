/**
 * Impact Observatory | مرصد الأثر — Sector Transmission State
 *
 * Six canonical GCC sectors, each tracking:
 *   - stress level (0–1 + classified)
 *   - transmission source (what caused the pressure)
 *   - time lag (how many hours after trigger)
 *   - signal sensitivity (how reactive to intelligence signals)
 *
 * Supports propagation: country stress flows into sectors
 * based on sector-country coupling coefficients.
 */

import type { GCCCountry, CountryMacroState } from './countryState';

/* ── Types ── */

export type GCCSector = 'Banking' | 'Insurance' | 'Fintech' | 'RealEstate' | 'Government' | 'OilGas';

export type StressLevel = 'nominal' | 'elevated' | 'high' | 'severe' | 'critical';

export interface SectorState {
  sector: GCCSector;
  label: string;
  /** Aggregate stress 0–1 */
  stress: number;
  /** Classified stress level */
  level: StressLevel;
  /** Primary source of current pressure */
  transmissionSource: string;
  /** Hours after scenario trigger that this sector first feels pressure */
  timeLagHours: number;
  /** How sensitive this sector is to signal-type inputs (0–1) */
  signalSensitivity: number;
  /** Per-country stress contribution */
  countryContributions: Partial<Record<GCCCountry, number>>;
}

/* ── Constants ── */

export const ALL_SECTORS: GCCSector[] = ['Banking', 'Insurance', 'Fintech', 'RealEstate', 'Government', 'OilGas'];

export const SECTOR_LABELS: Record<GCCSector, string> = {
  Banking:    'Banking',
  Insurance:  'Insurance',
  Fintech:    'Fintech',
  RealEstate: 'Real Estate',
  Government: 'Government',
  OilGas:     'Oil & Gas',
};

/**
 * Sector sensitivity to each country macro dimension.
 * Values represent how much of each macro pressure dimension
 * flows into this sector's stress level.
 */
export interface SectorMacroCoupling {
  gdp: number;
  inflation: number;
  liquidity: number;
  fiscal: number;
  trade: number;
  sovereign: number;
}

export const SECTOR_MACRO_COUPLING: Record<GCCSector, SectorMacroCoupling> = {
  Banking:    { gdp: 0.60, inflation: 0.30, liquidity: 0.90, fiscal: 0.50, trade: 0.40, sovereign: 0.70 },
  Insurance:  { gdp: 0.40, inflation: 0.50, liquidity: 0.60, fiscal: 0.30, trade: 0.55, sovereign: 0.45 },
  Fintech:    { gdp: 0.50, inflation: 0.25, liquidity: 0.70, fiscal: 0.20, trade: 0.30, sovereign: 0.35 },
  RealEstate: { gdp: 0.80, inflation: 0.60, liquidity: 0.75, fiscal: 0.40, trade: 0.20, sovereign: 0.50 },
  Government: { gdp: 0.50, inflation: 0.35, liquidity: 0.30, fiscal: 0.90, trade: 0.40, sovereign: 0.85 },
  OilGas:     { gdp: 0.70, inflation: 0.45, liquidity: 0.25, fiscal: 0.75, trade: 0.85, sovereign: 0.40 },
};

/**
 * Base time lag: how many hours after trigger this sector begins absorbing pressure.
 * Varies by scenario; this is the structural default.
 */
export const SECTOR_TIME_LAG: Record<GCCSector, number> = {
  OilGas:     2,
  Banking:    6,
  Insurance:  12,
  Government: 4,
  Fintech:    8,
  RealEstate: 24,
};

/** Signal sensitivity: how much intelligence signals amplify sector stress */
export const SECTOR_SIGNAL_SENSITIVITY: Record<GCCSector, number> = {
  OilGas:     0.85,
  Banking:    0.80,
  Insurance:  0.70,
  Government: 0.65,
  Fintech:    0.60,
  RealEstate: 0.50,
};

/* ── Computation ── */

/** Classify stress into named level */
export function classifyStress(stress: number): StressLevel {
  if (stress < 0.15) return 'nominal';
  if (stress < 0.35) return 'elevated';
  if (stress < 0.55) return 'high';
  if (stress < 0.75) return 'severe';
  return 'critical';
}

/**
 * Compute a single sector's state based on all 6 GCC country states.
 *
 * @param sector - the sector to compute
 * @param countryStates - all 6 country states
 * @param elapsedHours - hours elapsed since scenario trigger
 * @param signalAmplifier - additional amplification from active signals (0–1)
 */
export function computeSectorState(
  sector: GCCSector,
  countryStates: CountryMacroState[],
  elapsedHours: number,
  signalAmplifier: number = 0,
): SectorState {
  const coupling = SECTOR_MACRO_COUPLING[sector];
  const timeLag = SECTOR_TIME_LAG[sector];
  const signalSens = SECTOR_SIGNAL_SENSITIVITY[sector];

  // Time gate: sector doesn't absorb pressure until time lag has passed
  const timeGate = elapsedHours >= timeLag
    ? Math.min(1, (elapsedHours - timeLag) / Math.max(timeLag, 1))
    : 0;

  const countryContributions: Partial<Record<GCCCountry, number>> = {};
  let totalStress = 0;
  let primarySource = 'No active pressure';
  let maxContribution = 0;

  for (const cs of countryStates) {
    // Weighted sum of country dimensions via sector coupling
    const contribution = (
      cs.gdpPressure.intensity * coupling.gdp +
      cs.inflationPressure.intensity * coupling.inflation +
      cs.liquidityStress.intensity * coupling.liquidity +
      cs.fiscalBurden.intensity * coupling.fiscal +
      cs.tradeDisruption.intensity * coupling.trade +
      cs.sovereignRisk.intensity * coupling.sovereign
    ) / 6; // normalise by dimension count

    const gatedContribution = contribution * timeGate;
    countryContributions[cs.countryCode] = gatedContribution;
    totalStress += gatedContribution;

    if (gatedContribution > maxContribution) {
      maxContribution = gatedContribution;
      // Identify which dimension is primary driver
      const dims = [
        { name: 'GDP pressure', val: cs.gdpPressure.intensity * coupling.gdp },
        { name: 'inflation', val: cs.inflationPressure.intensity * coupling.inflation },
        { name: 'liquidity stress', val: cs.liquidityStress.intensity * coupling.liquidity },
        { name: 'fiscal burden', val: cs.fiscalBurden.intensity * coupling.fiscal },
        { name: 'trade disruption', val: cs.tradeDisruption.intensity * coupling.trade },
        { name: 'sovereign risk', val: cs.sovereignRisk.intensity * coupling.sovereign },
      ].sort((a, b) => b.val - a.val);
      primarySource = `${cs.name} ${dims[0].name}`;
    }
  }

  // Average across 6 countries + signal amplification
  const baseStress = totalStress / countryStates.length;
  const amplifiedStress = Math.min(1, baseStress + signalAmplifier * signalSens * 0.15);

  return {
    sector,
    label: SECTOR_LABELS[sector],
    stress: amplifiedStress,
    level: classifyStress(amplifiedStress),
    transmissionSource: primarySource,
    timeLagHours: timeLag,
    signalSensitivity: signalSens,
    countryContributions,
  };
}

/**
 * Compute all 6 sector states.
 */
export function computeAllSectorStates(
  countryStates: CountryMacroState[],
  elapsedHours: number,
  signalAmplifier?: number,
): SectorState[] {
  return ALL_SECTORS.map((s) =>
    computeSectorState(s, countryStates, elapsedHours, signalAmplifier),
  );
}

/**
 * Idle sector state.
 */
export function idleSectorState(sector: GCCSector): SectorState {
  return {
    sector,
    label: SECTOR_LABELS[sector],
    stress: 0,
    level: 'nominal',
    transmissionSource: 'No active scenario',
    timeLagHours: SECTOR_TIME_LAG[sector],
    signalSensitivity: SECTOR_SIGNAL_SENSITIVITY[sector],
    countryContributions: {},
  };
}
