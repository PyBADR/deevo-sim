/**
 * Impact Observatory | مرصد الأثر — Country-Level Macro State
 *
 * Structured model for each GCC country's macroeconomic condition.
 * Six pressure dimensions tracked per country, each with severity
 * classification and numeric intensity (0–1).
 *
 * Updated deterministically when a scenario runs.
 * No backend dependency. Pure state + computation.
 */

/* ── Types ── */

export type GCCCountry = 'SA' | 'AE' | 'KW' | 'QA' | 'BH' | 'OM';

export type PressureLevel = 'low' | 'moderate' | 'high' | 'severe';

export interface PressureDimension {
  /** Numeric intensity 0–1 */
  intensity: number;
  /** Classified level derived from intensity */
  level: PressureLevel;
  /** What is driving this pressure */
  driver: string;
}

export interface CountryMacroState {
  countryCode: GCCCountry;
  name: string;
  nameAr: string;
  /** GDP growth pressure — contraction risk */
  gdpPressure: PressureDimension;
  /** Inflation transmission — CPI pass-through */
  inflationPressure: PressureDimension;
  /** Banking system liquidity adequacy */
  liquidityStress: PressureDimension;
  /** Government fiscal burden / deficit exposure */
  fiscalBurden: PressureDimension;
  /** Trade corridor disruption impact */
  tradeDisruption: PressureDimension;
  /** Composite sovereign risk posture */
  sovereignRisk: PressureDimension;
  /** Overall composite stress 0–1 */
  compositeStress: number;
}

/* ── Constants ── */

export const GCC_COUNTRIES: Record<GCCCountry, { name: string; nameAr: string }> = {
  SA: { name: 'Saudi Arabia',       nameAr: 'المملكة العربية السعودية' },
  AE: { name: 'United Arab Emirates', nameAr: 'الإمارات العربية المتحدة' },
  KW: { name: 'Kuwait',             nameAr: 'الكويت' },
  QA: { name: 'Qatar',              nameAr: 'قطر' },
  BH: { name: 'Bahrain',            nameAr: 'البحرين' },
  OM: { name: 'Oman',               nameAr: 'عمان' },
};

export const ALL_COUNTRY_CODES: GCCCountry[] = ['SA', 'AE', 'KW', 'QA', 'BH', 'OM'];

/* ── Sensitivity Profiles ──
   Each country has a baseline sensitivity to each pressure dimension.
   These are structural — they reflect economic composition, not scenario state.
   Values 0–1 representing how sensitive this country is to this dimension.
*/

export interface CountrySensitivity {
  gdp: number;
  inflation: number;
  liquidity: number;
  fiscal: number;
  trade: number;
  sovereign: number;
}

export const COUNTRY_SENSITIVITY: Record<GCCCountry, CountrySensitivity> = {
  SA: { gdp: 0.70, inflation: 0.50, liquidity: 0.40, fiscal: 0.75, trade: 0.65, sovereign: 0.35 },
  AE: { gdp: 0.55, inflation: 0.45, liquidity: 0.60, fiscal: 0.40, trade: 0.80, sovereign: 0.30 },
  KW: { gdp: 0.65, inflation: 0.40, liquidity: 0.35, fiscal: 0.80, trade: 0.50, sovereign: 0.45 },
  QA: { gdp: 0.50, inflation: 0.35, liquidity: 0.30, fiscal: 0.55, trade: 0.70, sovereign: 0.25 },
  BH: { gdp: 0.60, inflation: 0.55, liquidity: 0.70, fiscal: 0.85, trade: 0.55, sovereign: 0.75 },
  OM: { gdp: 0.65, inflation: 0.50, liquidity: 0.65, fiscal: 0.80, trade: 0.60, sovereign: 0.65 },
};

/* ── Scenario → Country Impact Profiles ──
   Maps each scenario to the raw shock magnitude per dimension per country.
   Values 0–1 representing the scenario's direct pressure on each dimension.
   These are multiplied by country sensitivity to produce actual state.
*/

export interface ScenarioCountryShock {
  gdp: number;
  inflation: number;
  liquidity: number;
  fiscal: number;
  trade: number;
  sovereign: number;
}

/** Default shock: minimal impact */
const ZERO_SHOCK: ScenarioCountryShock = { gdp: 0, inflation: 0, liquidity: 0, fiscal: 0, trade: 0, sovereign: 0 };

/**
 * Scenario impact matrix.
 * For each scenario ID, defines per-country shock magnitudes.
 * Missing countries default to a reduced regional spillover.
 */
export const SCENARIO_COUNTRY_IMPACTS: Record<string, Partial<Record<GCCCountry, ScenarioCountryShock>>> = {
  hormuz_chokepoint_disruption: {
    SA: { gdp: 0.65, inflation: 0.70, liquidity: 0.50, fiscal: 0.75, trade: 0.90, sovereign: 0.40 },
    AE: { gdp: 0.60, inflation: 0.65, liquidity: 0.55, fiscal: 0.50, trade: 0.95, sovereign: 0.35 },
    KW: { gdp: 0.55, inflation: 0.60, liquidity: 0.40, fiscal: 0.70, trade: 0.85, sovereign: 0.35 },
    QA: { gdp: 0.50, inflation: 0.50, liquidity: 0.35, fiscal: 0.55, trade: 0.80, sovereign: 0.25 },
    BH: { gdp: 0.55, inflation: 0.55, liquidity: 0.50, fiscal: 0.65, trade: 0.75, sovereign: 0.45 },
    OM: { gdp: 0.60, inflation: 0.60, liquidity: 0.55, fiscal: 0.70, trade: 0.85, sovereign: 0.50 },
  },
  hormuz_full_closure: {
    SA: { gdp: 0.85, inflation: 0.80, liquidity: 0.70, fiscal: 0.90, trade: 0.95, sovereign: 0.60 },
    AE: { gdp: 0.80, inflation: 0.75, liquidity: 0.75, fiscal: 0.70, trade: 0.95, sovereign: 0.55 },
    KW: { gdp: 0.75, inflation: 0.70, liquidity: 0.60, fiscal: 0.85, trade: 0.90, sovereign: 0.55 },
    QA: { gdp: 0.70, inflation: 0.65, liquidity: 0.55, fiscal: 0.75, trade: 0.90, sovereign: 0.45 },
    BH: { gdp: 0.75, inflation: 0.70, liquidity: 0.70, fiscal: 0.85, trade: 0.85, sovereign: 0.65 },
    OM: { gdp: 0.80, inflation: 0.75, liquidity: 0.70, fiscal: 0.85, trade: 0.90, sovereign: 0.70 },
  },
  iran_regional_escalation: {
    SA: { gdp: 0.60, inflation: 0.55, liquidity: 0.50, fiscal: 0.55, trade: 0.60, sovereign: 0.65 },
    AE: { gdp: 0.55, inflation: 0.50, liquidity: 0.55, fiscal: 0.45, trade: 0.55, sovereign: 0.55 },
    KW: { gdp: 0.55, inflation: 0.50, liquidity: 0.45, fiscal: 0.55, trade: 0.50, sovereign: 0.60 },
    QA: { gdp: 0.50, inflation: 0.45, liquidity: 0.40, fiscal: 0.50, trade: 0.55, sovereign: 0.50 },
    BH: { gdp: 0.65, inflation: 0.55, liquidity: 0.60, fiscal: 0.65, trade: 0.50, sovereign: 0.70 },
    OM: { gdp: 0.55, inflation: 0.50, liquidity: 0.50, fiscal: 0.60, trade: 0.55, sovereign: 0.55 },
  },
  saudi_oil_shock: {
    SA: { gdp: 0.85, inflation: 0.60, liquidity: 0.55, fiscal: 0.90, trade: 0.70, sovereign: 0.50 },
    AE: { gdp: 0.35, inflation: 0.30, liquidity: 0.25, fiscal: 0.25, trade: 0.30, sovereign: 0.15 },
    KW: { gdp: 0.40, inflation: 0.35, liquidity: 0.30, fiscal: 0.45, trade: 0.35, sovereign: 0.20 },
    QA: { gdp: 0.30, inflation: 0.25, liquidity: 0.20, fiscal: 0.30, trade: 0.25, sovereign: 0.10 },
    BH: { gdp: 0.50, inflation: 0.40, liquidity: 0.45, fiscal: 0.55, trade: 0.35, sovereign: 0.40 },
    OM: { gdp: 0.45, inflation: 0.35, liquidity: 0.40, fiscal: 0.50, trade: 0.30, sovereign: 0.35 },
  },
  uae_banking_crisis: {
    SA: { gdp: 0.30, inflation: 0.15, liquidity: 0.40, fiscal: 0.20, trade: 0.25, sovereign: 0.15 },
    AE: { gdp: 0.75, inflation: 0.40, liquidity: 0.90, fiscal: 0.55, trade: 0.60, sovereign: 0.50 },
    KW: { gdp: 0.25, inflation: 0.15, liquidity: 0.35, fiscal: 0.20, trade: 0.20, sovereign: 0.15 },
    QA: { gdp: 0.20, inflation: 0.10, liquidity: 0.30, fiscal: 0.15, trade: 0.15, sovereign: 0.10 },
    BH: { gdp: 0.45, inflation: 0.25, liquidity: 0.55, fiscal: 0.40, trade: 0.30, sovereign: 0.35 },
    OM: { gdp: 0.35, inflation: 0.20, liquidity: 0.45, fiscal: 0.30, trade: 0.25, sovereign: 0.25 },
  },
  qatar_lng_disruption: {
    SA: { gdp: 0.20, inflation: 0.25, liquidity: 0.15, fiscal: 0.15, trade: 0.30, sovereign: 0.10 },
    AE: { gdp: 0.25, inflation: 0.30, liquidity: 0.20, fiscal: 0.15, trade: 0.35, sovereign: 0.10 },
    KW: { gdp: 0.20, inflation: 0.25, liquidity: 0.15, fiscal: 0.20, trade: 0.25, sovereign: 0.10 },
    QA: { gdp: 0.80, inflation: 0.55, liquidity: 0.50, fiscal: 0.85, trade: 0.90, sovereign: 0.45 },
    BH: { gdp: 0.30, inflation: 0.30, liquidity: 0.25, fiscal: 0.30, trade: 0.30, sovereign: 0.20 },
    OM: { gdp: 0.25, inflation: 0.30, liquidity: 0.20, fiscal: 0.25, trade: 0.30, sovereign: 0.15 },
  },
  bahrain_sovereign_stress: {
    SA: { gdp: 0.15, inflation: 0.10, liquidity: 0.15, fiscal: 0.10, trade: 0.10, sovereign: 0.10 },
    AE: { gdp: 0.15, inflation: 0.10, liquidity: 0.20, fiscal: 0.10, trade: 0.10, sovereign: 0.10 },
    KW: { gdp: 0.15, inflation: 0.10, liquidity: 0.15, fiscal: 0.15, trade: 0.10, sovereign: 0.10 },
    QA: { gdp: 0.10, inflation: 0.10, liquidity: 0.10, fiscal: 0.10, trade: 0.10, sovereign: 0.05 },
    BH: { gdp: 0.80, inflation: 0.65, liquidity: 0.85, fiscal: 0.90, trade: 0.50, sovereign: 0.90 },
    OM: { gdp: 0.20, inflation: 0.15, liquidity: 0.20, fiscal: 0.20, trade: 0.15, sovereign: 0.20 },
  },
  kuwait_fiscal_shock: {
    SA: { gdp: 0.15, inflation: 0.10, liquidity: 0.15, fiscal: 0.10, trade: 0.10, sovereign: 0.10 },
    AE: { gdp: 0.15, inflation: 0.10, liquidity: 0.15, fiscal: 0.10, trade: 0.10, sovereign: 0.05 },
    KW: { gdp: 0.80, inflation: 0.55, liquidity: 0.60, fiscal: 0.90, trade: 0.50, sovereign: 0.65 },
    QA: { gdp: 0.10, inflation: 0.10, liquidity: 0.10, fiscal: 0.10, trade: 0.10, sovereign: 0.05 },
    BH: { gdp: 0.25, inflation: 0.15, liquidity: 0.25, fiscal: 0.25, trade: 0.15, sovereign: 0.20 },
    OM: { gdp: 0.20, inflation: 0.15, liquidity: 0.20, fiscal: 0.20, trade: 0.15, sovereign: 0.15 },
  },
  oman_port_closure: {
    SA: { gdp: 0.15, inflation: 0.15, liquidity: 0.10, fiscal: 0.10, trade: 0.30, sovereign: 0.05 },
    AE: { gdp: 0.25, inflation: 0.20, liquidity: 0.15, fiscal: 0.10, trade: 0.45, sovereign: 0.10 },
    KW: { gdp: 0.10, inflation: 0.10, liquidity: 0.10, fiscal: 0.10, trade: 0.20, sovereign: 0.05 },
    QA: { gdp: 0.10, inflation: 0.10, liquidity: 0.10, fiscal: 0.10, trade: 0.20, sovereign: 0.05 },
    BH: { gdp: 0.15, inflation: 0.15, liquidity: 0.15, fiscal: 0.15, trade: 0.25, sovereign: 0.10 },
    OM: { gdp: 0.75, inflation: 0.55, liquidity: 0.55, fiscal: 0.70, trade: 0.90, sovereign: 0.55 },
  },
  red_sea_trade_corridor_instability: {
    SA: { gdp: 0.50, inflation: 0.55, liquidity: 0.30, fiscal: 0.40, trade: 0.80, sovereign: 0.25 },
    AE: { gdp: 0.55, inflation: 0.50, liquidity: 0.35, fiscal: 0.30, trade: 0.85, sovereign: 0.20 },
    KW: { gdp: 0.30, inflation: 0.35, liquidity: 0.20, fiscal: 0.30, trade: 0.50, sovereign: 0.15 },
    QA: { gdp: 0.25, inflation: 0.30, liquidity: 0.15, fiscal: 0.25, trade: 0.45, sovereign: 0.10 },
    BH: { gdp: 0.40, inflation: 0.40, liquidity: 0.30, fiscal: 0.40, trade: 0.55, sovereign: 0.25 },
    OM: { gdp: 0.45, inflation: 0.45, liquidity: 0.30, fiscal: 0.40, trade: 0.70, sovereign: 0.30 },
  },
  energy_market_volatility_shock: {
    SA: { gdp: 0.55, inflation: 0.65, liquidity: 0.35, fiscal: 0.60, trade: 0.50, sovereign: 0.30 },
    AE: { gdp: 0.40, inflation: 0.55, liquidity: 0.30, fiscal: 0.35, trade: 0.40, sovereign: 0.20 },
    KW: { gdp: 0.55, inflation: 0.60, liquidity: 0.35, fiscal: 0.65, trade: 0.45, sovereign: 0.30 },
    QA: { gdp: 0.45, inflation: 0.50, liquidity: 0.25, fiscal: 0.50, trade: 0.40, sovereign: 0.20 },
    BH: { gdp: 0.50, inflation: 0.55, liquidity: 0.40, fiscal: 0.55, trade: 0.40, sovereign: 0.35 },
    OM: { gdp: 0.55, inflation: 0.55, liquidity: 0.40, fiscal: 0.60, trade: 0.45, sovereign: 0.35 },
  },
  gcc_cyber_attack: {
    SA: { gdp: 0.40, inflation: 0.20, liquidity: 0.55, fiscal: 0.25, trade: 0.45, sovereign: 0.30 },
    AE: { gdp: 0.45, inflation: 0.20, liquidity: 0.60, fiscal: 0.25, trade: 0.50, sovereign: 0.30 },
    KW: { gdp: 0.35, inflation: 0.15, liquidity: 0.50, fiscal: 0.20, trade: 0.35, sovereign: 0.25 },
    QA: { gdp: 0.30, inflation: 0.15, liquidity: 0.45, fiscal: 0.20, trade: 0.35, sovereign: 0.20 },
    BH: { gdp: 0.40, inflation: 0.20, liquidity: 0.55, fiscal: 0.30, trade: 0.40, sovereign: 0.35 },
    OM: { gdp: 0.35, inflation: 0.15, liquidity: 0.50, fiscal: 0.25, trade: 0.35, sovereign: 0.30 },
  },
  regional_liquidity_stress_event: {
    SA: { gdp: 0.40, inflation: 0.25, liquidity: 0.70, fiscal: 0.35, trade: 0.30, sovereign: 0.25 },
    AE: { gdp: 0.45, inflation: 0.25, liquidity: 0.75, fiscal: 0.35, trade: 0.35, sovereign: 0.30 },
    KW: { gdp: 0.35, inflation: 0.20, liquidity: 0.65, fiscal: 0.35, trade: 0.25, sovereign: 0.25 },
    QA: { gdp: 0.30, inflation: 0.20, liquidity: 0.55, fiscal: 0.30, trade: 0.25, sovereign: 0.20 },
    BH: { gdp: 0.50, inflation: 0.30, liquidity: 0.80, fiscal: 0.50, trade: 0.30, sovereign: 0.50 },
    OM: { gdp: 0.45, inflation: 0.25, liquidity: 0.70, fiscal: 0.45, trade: 0.30, sovereign: 0.40 },
  },
  critical_port_throughput_disruption: {
    SA: { gdp: 0.40, inflation: 0.45, liquidity: 0.25, fiscal: 0.30, trade: 0.75, sovereign: 0.20 },
    AE: { gdp: 0.55, inflation: 0.50, liquidity: 0.35, fiscal: 0.30, trade: 0.90, sovereign: 0.25 },
    KW: { gdp: 0.25, inflation: 0.30, liquidity: 0.15, fiscal: 0.20, trade: 0.50, sovereign: 0.10 },
    QA: { gdp: 0.20, inflation: 0.25, liquidity: 0.15, fiscal: 0.15, trade: 0.45, sovereign: 0.10 },
    BH: { gdp: 0.35, inflation: 0.35, liquidity: 0.25, fiscal: 0.30, trade: 0.55, sovereign: 0.20 },
    OM: { gdp: 0.40, inflation: 0.40, liquidity: 0.25, fiscal: 0.35, trade: 0.70, sovereign: 0.25 },
  },
  financial_infrastructure_cyber_disruption: {
    SA: { gdp: 0.35, inflation: 0.15, liquidity: 0.65, fiscal: 0.25, trade: 0.40, sovereign: 0.25 },
    AE: { gdp: 0.40, inflation: 0.15, liquidity: 0.70, fiscal: 0.25, trade: 0.45, sovereign: 0.30 },
    KW: { gdp: 0.30, inflation: 0.10, liquidity: 0.55, fiscal: 0.20, trade: 0.30, sovereign: 0.20 },
    QA: { gdp: 0.25, inflation: 0.10, liquidity: 0.50, fiscal: 0.15, trade: 0.30, sovereign: 0.15 },
    BH: { gdp: 0.40, inflation: 0.15, liquidity: 0.65, fiscal: 0.30, trade: 0.35, sovereign: 0.35 },
    OM: { gdp: 0.35, inflation: 0.15, liquidity: 0.55, fiscal: 0.25, trade: 0.30, sovereign: 0.25 },
  },
};

/* ── Computation ── */

/** Classify numeric intensity into pressure level */
export function classifyPressure(intensity: number): PressureLevel {
  if (intensity < 0.25) return 'low';
  if (intensity < 0.50) return 'moderate';
  if (intensity < 0.75) return 'high';
  return 'severe';
}

/**
 * Compute country macro state for a given scenario at a given progress point.
 *
 * @param countryCode - GCC country
 * @param scenarioId - active scenario
 * @param t - normalised progress 0→1 (elapsed / horizon)
 * @param baseRisk - scenario's global risk score 0→1
 */
export function computeCountryState(
  countryCode: GCCCountry,
  scenarioId: string,
  t: number,
  baseRisk: number,
): CountryMacroState {
  const info = GCC_COUNTRIES[countryCode];
  const sensitivity = COUNTRY_SENSITIVITY[countryCode];
  const shockProfile = SCENARIO_COUNTRY_IMPACTS[scenarioId]?.[countryCode] ?? ZERO_SHOCK;

  // Time-modulated shock: pressure builds logistically, then stabilises
  const timeModulator = 1 / (1 + Math.exp(-10 * (t - 0.3)));

  function computeDimension(
    shockMag: number,
    sensitivityVal: number,
    driver: string,
  ): PressureDimension {
    const raw = shockMag * sensitivityVal * timeModulator * (0.6 + baseRisk * 0.4);
    const intensity = Math.min(1, Math.max(0, raw));
    return { intensity, level: classifyPressure(intensity), driver };
  }

  const gdpPressure = computeDimension(shockProfile.gdp, sensitivity.gdp, 'GDP contraction risk from supply/demand disruption');
  const inflationPressure = computeDimension(shockProfile.inflation, sensitivity.inflation, 'CPI pass-through from energy and import cost escalation');
  const liquidityStress = computeDimension(shockProfile.liquidity, sensitivity.liquidity, 'Banking system liquidity adequacy under deposit outflow');
  const fiscalBurden = computeDimension(shockProfile.fiscal, sensitivity.fiscal, 'Government fiscal burden from revenue compression');
  const tradeDisruption = computeDimension(shockProfile.trade, sensitivity.trade, 'Trade corridor disruption affecting import/export volume');
  const sovereignRisk = computeDimension(shockProfile.sovereign, sensitivity.sovereign, 'Sovereign risk repricing from composite macro stress');

  const compositeStress = (
    gdpPressure.intensity * 0.20 +
    inflationPressure.intensity * 0.15 +
    liquidityStress.intensity * 0.20 +
    fiscalBurden.intensity * 0.20 +
    tradeDisruption.intensity * 0.15 +
    sovereignRisk.intensity * 0.10
  );

  return {
    countryCode,
    name: info.name,
    nameAr: info.nameAr,
    gdpPressure,
    inflationPressure,
    liquidityStress,
    fiscalBurden,
    tradeDisruption,
    sovereignRisk,
    compositeStress: Math.min(1, compositeStress),
  };
}

/**
 * Compute all 6 GCC country states for a given scenario.
 */
export function computeAllCountryStates(
  scenarioId: string,
  t: number,
  baseRisk: number,
): CountryMacroState[] {
  return ALL_COUNTRY_CODES.map((code) =>
    computeCountryState(code, scenarioId, t, baseRisk),
  );
}

/**
 * Idle state for a country (no active scenario).
 */
export function idleCountryState(countryCode: GCCCountry): CountryMacroState {
  const info = GCC_COUNTRIES[countryCode];
  const idle: PressureDimension = { intensity: 0, level: 'low', driver: 'No active scenario' };
  return {
    countryCode, name: info.name, nameAr: info.nameAr,
    gdpPressure: idle, inflationPressure: idle, liquidityStress: idle,
    fiscalBurden: idle, tradeDisruption: idle, sovereignRisk: idle,
    compositeStress: 0,
  };
}
