/**
 * Impact Observatory | مرصد الأثر — Multi-Narrative Perspective Engine
 *
 * FIX 1: Multi-Narrative Perspectives
 *
 * Four sovereign intelligence perspectives:
 *   1. GCC Sovereign      — state-level economic defence posture
 *   2. Regional Banking    — central bank / financial stability view
 *   3. Insurance / Risk    — reinsurance, IFRS-17, loss ratio framing
 *   4. International Counterparty — foreign institutional exposure view
 *
 * Each perspective produces:
 *   - transmissionFraming: how the event transmits through this lens
 *   - exposureNarrative: what is at stake
 *   - decisionRationale: what action this stakeholder should take
 */

import type { CountryMacroState } from './countryState';
import type { SectorState } from './sectorState';
import type { EntityExposureState } from './entityState';
import type { SignalEngineOutput, ActiveSignal } from './signalEngine';
import type { DecisionEngineOutput } from './decisionEngine';

/* ── Types ── */

export type IntelligencePerspective =
  | 'gcc_sovereign'
  | 'regional_banking'
  | 'insurance_risk'
  | 'international_counterparty';

export const ALL_PERSPECTIVES: IntelligencePerspective[] = [
  'gcc_sovereign',
  'regional_banking',
  'insurance_risk',
  'international_counterparty',
];

export const PERSPECTIVE_LABELS: Record<IntelligencePerspective, { en: string; ar: string }> = {
  gcc_sovereign: { en: 'GCC Sovereign', ar: 'السيادة الخليجية' },
  regional_banking: { en: 'Regional Banking', ar: 'القطاع المصرفي الإقليمي' },
  insurance_risk: { en: 'Insurance / Risk', ar: 'التأمين والمخاطر' },
  international_counterparty: { en: 'International Counterparty', ar: 'الطرف الدولي المقابل' },
};

export interface PerspectiveNarrative {
  perspective: IntelligencePerspective;
  label: string;
  transmissionFraming: string;
  exposureNarrative: string;
  decisionRationale: string;
}

/* ── Generator Functions ── */

function generateSovereignPerspective(
  countries: CountryMacroState[],
  sectors: SectorState[],
  decision: DecisionEngineOutput,
  signals: SignalEngineOutput,
): PerspectiveNarrative {
  const topCountry = [...countries].sort((a, b) => b.compositeStress - a.compositeStress)[0];
  const topSector = [...sectors].sort((a, b) => b.stress - a.stress)[0];
  const peakSignals = signals.activeSignals.filter(s => s.state === 'peak');

  const transmissionFraming = topCountry
    ? `Sovereign transmission concentrates through ${topCountry.name}'s fiscal-trade corridor. ${topCountry.tradeDisruption.level === 'severe' || topCountry.tradeDisruption.level === 'high' ? `Trade corridor pressure at ${Math.round(topCountry.tradeDisruption.intensity * 100)}% is compressing export revenue capacity.` : `Macro stress at ${Math.round(topCountry.compositeStress * 100)}% is within managed parameters but trending adversely.`} ${countries.filter(c => c.compositeStress > 0.5).length} GCC states are above 50% composite stress.`
    : 'No active sovereign transmission detected.';

  const exposureNarrative = `GCC sovereign exposure is ${decision.posture === 'crisis' ? 'at crisis level' : decision.posture === 'immediate' ? 'severe' : 'elevated'}. ${decision.priorityCountries.length > 0 ? `Priority states: ${decision.priorityCountries.join(', ')}.` : ''} ${topSector ? `${topSector.label} is the primary transmission sector at ${Math.round(topSector.stress * 100)}% stress.` : ''} Fiscal reserves are the primary buffer against revenue compression.`;

  const decisionRationale = decision.posture === 'crisis' || decision.posture === 'immediate'
    ? `Activate coordinated GCC fiscal response. ${decision.escalationActions[0] ?? 'Deploy sovereign stabilisation instruments across affected states.'} Diplomatic de-escalation window is narrowing.`
    : `Maintain elevated monitoring posture. Pre-position fiscal response capacity across ${decision.priorityCountries.length > 0 ? decision.priorityCountries.join(' and ') : 'all GCC states'}. No immediate sovereign intervention required.`;

  return {
    perspective: 'gcc_sovereign',
    label: 'GCC Sovereign',
    transmissionFraming,
    exposureNarrative,
    decisionRationale,
  };
}

function generateBankingPerspective(
  countries: CountryMacroState[],
  sectors: SectorState[],
  entities: EntityExposureState[],
  decision: DecisionEngineOutput,
): PerspectiveNarrative {
  const bankingSector = sectors.find(s => s.sector === 'Banking');
  const bankingEntities = entities.filter(e => e.sector === 'Banking');
  const criticalBanks = bankingEntities.filter(e => e.level === 'critical' || e.level === 'high');
  const maxLiquidityStress = Math.max(...countries.map(c => c.liquidityStress.intensity));

  const transmissionFraming = bankingSector
    ? `Banking sector transmission at ${Math.round(bankingSector.stress * 100)}% aggregate stress, driven by ${bankingSector.transmissionSource}. Interbank contagion is ${bankingSector.stress > 0.5 ? 'active and accelerating' : 'contained but building'}. ${criticalBanks.length > 0 ? `${criticalBanks.length} institutions at critical exposure.` : 'No institutions at critical exposure.'}`
    : 'Banking transmission dormant.';

  const exposureNarrative = `Regional liquidity stress peaks at ${Math.round(maxLiquidityStress * 100)}%. ${criticalBanks.length > 0 ? `Central banks in ${[...new Set(criticalBanks.map(e => e.country))].join(', ')} face immediate supervisory decisions.` : 'Liquidity buffers are adequate at current stress levels.'} Cross-border interbank exposure remains the primary contagion channel.`;

  const decisionRationale = bankingSector && bankingSector.stress > 0.5
    ? `Central banks should activate emergency liquidity facilities. Interbank lending limits require immediate review. Capital adequacy waivers may be necessary for systemically important institutions.`
    : `Maintain enhanced surveillance on interbank exposures. Pre-clear emergency liquidity mechanism activation procedures. No immediate intervention warranted.`;

  return {
    perspective: 'regional_banking',
    label: 'Regional Banking',
    transmissionFraming,
    exposureNarrative,
    decisionRationale,
  };
}

function generateInsurancePerspective(
  countries: CountryMacroState[],
  sectors: SectorState[],
  entities: EntityExposureState[],
  signals: SignalEngineOutput,
): PerspectiveNarrative {
  const insuranceSector = sectors.find(s => s.sector === 'Insurance');
  const insuranceEntities = entities.filter(e => e.sector === 'Insurance');
  const operationalSignals = signals.activeSignals.filter(s => s.signal.type === 'Operational' && s.intensity > 0.3);

  const transmissionFraming = insuranceSector
    ? `Insurance transmission at ${Math.round(insuranceSector.stress * 100)}% sector stress. ${operationalSignals.length > 0 ? `${operationalSignals.length} operational risk signals are driving claims frequency escalation.` : 'Claims frequency is within baseline parameters.'} Loss ratio deterioration is ${insuranceSector.stress > 0.4 ? 'accelerating beyond IFRS-17 risk adjustment thresholds' : 'contained within current reserve adequacy'}.`
    : 'Insurance sector transmission dormant.';

  const exposureNarrative = `${insuranceEntities.filter(e => e.exposure > 0.5).length > 0 ? `${insuranceEntities.filter(e => e.exposure > 0.5).map(e => `${e.name} (${e.country})`).join(', ')} face elevated claims exposure.` : 'No insurers at critical exposure.'} Reinsurance treaty trigger points should be reviewed against current loss trajectory. Marine cargo and energy lines carry disproportionate concentration risk.`;

  const decisionRationale = insuranceSector && insuranceSector.stress > 0.4
    ? `Invoke reinsurance treaty notification protocols. Accelerate IFRS-17 risk adjustment recalibration. Halt new policy issuance in affected marine cargo and energy lines until loss ratio stabilises.`
    : `Monitor loss ratio trends against IFRS-17 thresholds. No reinsurance triggers breached. Maintain underwriting discipline in exposed lines.`;

  return {
    perspective: 'insurance_risk',
    label: 'Insurance / Risk',
    transmissionFraming,
    exposureNarrative,
    decisionRationale,
  };
}

function generateCounterpartyPerspective(
  countries: CountryMacroState[],
  sectors: SectorState[],
  decision: DecisionEngineOutput,
  signals: SignalEngineOutput,
): PerspectiveNarrative {
  const geopoliticalSignals = signals.activeSignals.filter(s => s.signal.type === 'Geopolitical' && s.intensity > 0.3);
  const marketSignals = signals.activeSignals.filter(s => s.signal.type === 'Market' && s.intensity > 0.3);
  const avgStress = countries.reduce((sum, c) => sum + c.compositeStress, 0) / Math.max(countries.length, 1);

  const transmissionFraming = `International counterparty exposure to GCC markets is ${avgStress > 0.5 ? 'severely elevated' : avgStress > 0.3 ? 'materially increased' : 'within normal parameters'}. ${geopoliticalSignals.length > 0 ? `${geopoliticalSignals.length} geopolitical risk signals are active, driving sovereign bond repricing.` : ''} ${marketSignals.length > 0 ? `Commodity market signals indicate ${marketSignals.length} active disruption vectors.` : ''}`;

  const exposureNarrative = `Foreign institutional holders of GCC sovereign debt, energy futures, and trade finance instruments face ${decision.posture === 'crisis' ? 'immediate mark-to-market losses' : decision.posture === 'immediate' ? 'significant repricing risk' : 'moderate hedging requirements'}. Counterparty credit risk on GCC bank exposures should be reassessed. ${sectors.filter(s => s.stress > 0.5).length > 0 ? `${sectors.filter(s => s.stress > 0.5).map(s => s.label).join(', ')} sectors are above 50% stress, affecting linked derivative contracts.` : ''}`;

  const decisionRationale = avgStress > 0.5
    ? `Reduce GCC sovereign bond duration exposure. Activate commodity hedging overlays. Review counterparty credit limits on GCC financial institutions. Consider partial portfolio de-risking pending stabilisation signals.`
    : `Maintain current GCC allocation with enhanced monitoring. No immediate de-risking required. Review hedging costs against probability-weighted loss scenarios.`;

  return {
    perspective: 'international_counterparty',
    label: 'International Counterparty',
    transmissionFraming,
    exposureNarrative,
    decisionRationale,
  };
}

/**
 * Generate all four perspective narratives for the current intelligence state.
 */
export function generateAllPerspectives(
  countries: CountryMacroState[],
  sectors: SectorState[],
  entities: EntityExposureState[],
  signals: SignalEngineOutput,
  decision: DecisionEngineOutput,
): PerspectiveNarrative[] {
  return [
    generateSovereignPerspective(countries, sectors, decision, signals),
    generateBankingPerspective(countries, sectors, entities, decision),
    generateInsurancePerspective(countries, sectors, entities, signals),
    generateCounterpartyPerspective(countries, sectors, decision, signals),
  ];
}
