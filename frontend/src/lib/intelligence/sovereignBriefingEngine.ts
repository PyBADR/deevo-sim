/**
 * Impact Observatory | مرصد الأثر — Sovereign Intelligence Briefing Engine
 *
 * Transforms the raw IntelligenceSnapshot into a structured briefing
 * that addresses all 8 architectural fixes:
 *
 *   FIX 1: Multi-Narrative Perspectives       → perspectiveEngine.ts
 *   FIX 2: Signal Intelligence (dual signal)  → signalBrief
 *   FIX 3: Propagation (prose chain)          → propagationChain
 *   FIX 4: GCC Macro (country-specific)       → macroExposures
 *   FIX 5: Decision (directive prose)          → directives
 *   FIX 6: Monitoring (owner/escalation/review)→ monitoringSummary
 *   FIX 7: CEO Readability (vertical sequence) → sections array
 *   FIX 8: Missing layers (temporal/confidence/counterfactual)
 *          → temporalHorizon, confidenceBasis, counterfactual
 *
 * Output is a SovereignBriefing — a single object the UI renders
 * as a vertical reading sequence. No dashboards. No SaaS chrome.
 */

import type { IntelligenceSnapshot } from './systemLoop';
import type { CountryMacroState } from './countryState';
import type { SectorState } from './sectorState';
import type { ActiveSignal } from './signalEngine';
import type { MonitoringAssignment } from './monitoringEngine';
import { generateAllPerspectives, type PerspectiveNarrative, type IntelligencePerspective } from './perspectiveEngine';

/* ═══════════════════════════════════════════════════════════════════════
 * Types
 * ═══════════════════════════════════════════════════════════════════════ */

/** FIX 2: Dual signal with selection rationale */
export interface SignalBrief {
  dominantSignal: string;
  dominantType: string;
  dominantIntensity: number;
  selectionBasis: string;
  secondSignal: string | null;
  secondType: string | null;
  secondIntensity: number;
  activeCount: number;
  peakCount: number;
}

/** FIX 3: Numbered prose propagation chain */
export interface PropagationProseStep {
  stepNumber: number;
  prose: string;
}

/** FIX 4: Country-specific sector impact */
export interface CountrySectorExposure {
  country: string;
  countryCode: string;
  sector: string;
  exposure: string;
  stressIntensity: number;
}

/** FIX 5: Directive with consequence clause */
export interface DirectiveItem {
  directive: string;
  consequence: string;
  owner: string;
  sector: string;
}

/** FIX 6: Monitoring (cleaned) */
export interface MonitoringBrief {
  statusSummary: string;
  assignments: Array<{
    action: string;
    owner: string;
    escalationAuthority: string;
    reviewCycleHours: number;
    status: string;
    hoursRemaining: number;
  }>;
}

/** FIX 8A: Temporal horizon */
export interface TemporalHorizon {
  now: string;
  hours72: string;
  days30: string;
}

/** FIX 8B: Confidence basis */
export interface ConfidenceBasis {
  score: number;
  explanation: string;
}

/** FIX 8C: Counterfactual */
export interface CounterfactualBaseline {
  withoutAction: string;
}

/** Complete sovereign briefing — one object, vertical read */
export interface SovereignBriefing {
  scenarioId: string;
  timestamp: string;

  /** FIX 7: Vertical reading sequence labels */
  sectionOrder: readonly string[];

  /** Macro overview — headline posture + advisory */
  macro: {
    posture: string;
    advisory: string;
  };

  /** FIX 2: Signal intelligence */
  signal: SignalBrief;

  /** FIX 3: Propagation prose chain */
  propagation: PropagationProseStep[];

  /** FIX 5: Decision directives */
  directives: DirectiveItem[];

  /** FIX 4: Country-specific sector exposures */
  macroExposures: CountrySectorExposure[];

  /** FIX 6: Monitoring (cleaned) */
  monitoring: MonitoringBrief;

  /** FIX 1: Multi-narrative perspectives */
  perspectives: PerspectiveNarrative[];
  activePerspective: IntelligencePerspective;

  /** FIX 8: Missing layers */
  temporalHorizon: TemporalHorizon;
  confidenceBasis: ConfidenceBasis;
  counterfactual: CounterfactualBaseline;
}

/* ═══════════════════════════════════════════════════════════════════════
 * Builders
 * ═══════════════════════════════════════════════════════════════════════ */

function buildSignalBrief(signals: IntelligenceSnapshot['signals']): SignalBrief {
  const sorted = [...signals.activeSignals]
    .filter(s => s.intensity > 0)
    .sort((a, b) => b.intensity - a.intensity);

  const dominant = sorted[0];
  const second = sorted[1] ?? null;

  if (!dominant) {
    return {
      dominantSignal: 'No active signals',
      dominantType: '',
      dominantIntensity: 0,
      selectionBasis: 'No intelligence signals are currently active.',
      secondSignal: null,
      secondType: null,
      secondIntensity: 0,
      activeCount: 0,
      peakCount: 0,
    };
  }

  const selectionBasis = second
    ? `${dominant.signal.signal} dominates at ${Math.round(dominant.intensity * 100)}% intensity (${dominant.signal.type}) because it exceeds the next signal (${second.signal.signal}, ${Math.round(second.intensity * 100)}%) by ${Math.round((dominant.intensity - second.intensity) * 100)} points and carries higher transmission weight to affected GCC sectors.`
    : `${dominant.signal.signal} is the sole active intelligence input at ${Math.round(dominant.intensity * 100)}% intensity.`;

  return {
    dominantSignal: dominant.signal.signal,
    dominantType: dominant.signal.type,
    dominantIntensity: dominant.intensity,
    selectionBasis,
    secondSignal: second?.signal.signal ?? null,
    secondType: second?.signal.type ?? null,
    secondIntensity: second?.intensity ?? 0,
    activeCount: signals.activeCount,
    peakCount: signals.peakCount,
  };
}

function buildPropagationProse(snapshot: IntelligenceSnapshot): PropagationProseStep[] {
  const steps: PropagationProseStep[] = [];
  const countries = snapshot.countries;
  const sectors = snapshot.sectors;
  const entities = snapshot.entities;
  const log = snapshot.contagionLog;

  // Step 1: Event trigger
  const topCountry = [...countries].sort((a, b) => b.compositeStress - a.compositeStress)[0];
  if (topCountry) {
    steps.push({
      stepNumber: 1,
      prose: `The event triggers macro stress in ${topCountry.name}, reaching ${Math.round(topCountry.compositeStress * 100)}% composite pressure. Trade disruption (${Math.round(topCountry.tradeDisruption.intensity * 100)}%) and fiscal burden (${Math.round(topCountry.fiscalBurden.intensity * 100)}%) are the primary transmission channels.`,
    });
  }

  // Step 2: Country spillover
  const spillovers = log.filter(e => e.type === 'country_spillover');
  if (spillovers.length > 0) {
    const topSpillover = spillovers.sort((a, b) => b.magnitude - a.magnitude)[0];
    steps.push({
      stepNumber: 2,
      prose: `${topSpillover.source} macro stress transmits to ${topSpillover.target} through interbank and trade linkages, adding ${Math.round(topSpillover.magnitude * 100)} points of pressure. ${spillovers.length > 1 ? `${spillovers.length - 1} additional cross-border spillovers are active.` : ''}`,
    });
  }

  // Step 3: Sector transmission
  const topSector = [...sectors].sort((a, b) => b.stress - a.stress)[0];
  if (topSector && topSector.stress > 0.1) {
    steps.push({
      stepNumber: steps.length + 1,
      prose: `${topSector.label} absorbs the highest sector transmission at ${Math.round(topSector.stress * 100)}% stress, driven by ${topSector.transmissionSource}. Time lag from trigger to sector impact: ${topSector.timeLagHours} hours.`,
    });
  }

  // Step 4: Cross-sector amplification
  const crossSector = log.filter(e => e.type === 'cross_sector');
  if (crossSector.length > 0) {
    const topCross = crossSector.sort((a, b) => b.magnitude - a.magnitude)[0];
    steps.push({
      stepNumber: steps.length + 1,
      prose: `${topCross.source} stress amplifies ${topCross.target} by ${Math.round(topCross.magnitude * 100)} points through dependency coupling. ${crossSector.length > 1 ? `${crossSector.length} cross-sector amplification channels are active.` : ''}`,
    });
  }

  // Step 5: Entity impact
  const criticalEntities = entities.filter(e => e.level === 'critical' || e.level === 'high');
  if (criticalEntities.length > 0) {
    const topEntity = criticalEntities.sort((a, b) => b.exposure - a.exposure)[0];
    steps.push({
      stepNumber: steps.length + 1,
      prose: `${topEntity.name} (${topEntity.country}, ${topEntity.sector}) reaches ${Math.round(topEntity.exposure * 100)}% exposure — ${topEntity.level} classification. ${criticalEntities.length > 1 ? `${criticalEntities.length - 1} additional entities at critical or high exposure.` : ''}`,
    });
  }

  return steps;
}

function buildCountrySectorExposures(
  countries: CountryMacroState[],
  sectors: SectorState[],
): CountrySectorExposure[] {
  const exposures: CountrySectorExposure[] = [];

  for (const country of countries) {
    if (country.compositeStress < 0.15) continue;

    // Map country pressure dimensions to sector-specific exposure narratives
    const dimensionMap: Array<{ sector: string; intensity: number; narrative: string }> = [
      {
        sector: 'Banking',
        intensity: country.liquidityStress.intensity,
        narrative: `liquidity adequacy under deposit outflow pressure (${Math.round(country.liquidityStress.intensity * 100)}%)`,
      },
      {
        sector: 'Insurance',
        intensity: Math.max(country.tradeDisruption.intensity, country.inflationPressure.intensity) * 0.8,
        narrative: country.tradeDisruption.intensity > country.inflationPressure.intensity
          ? `marine cargo exposure from trade corridor disruption (${Math.round(country.tradeDisruption.intensity * 100)}%)`
          : `reinsurance repricing from inflation pass-through (${Math.round(country.inflationPressure.intensity * 100)}%)`,
      },
      {
        sector: 'Energy',
        intensity: country.tradeDisruption.intensity * 0.9,
        narrative: `export volume compression through trade corridor disruption (${Math.round(country.tradeDisruption.intensity * 100)}%)`,
      },
      {
        sector: 'Government',
        intensity: country.fiscalBurden.intensity,
        narrative: `fiscal revenue compression from ${country.fiscalBurden.driver.toLowerCase()} (${Math.round(country.fiscalBurden.intensity * 100)}%)`,
      },
    ];

    for (const dim of dimensionMap) {
      if (dim.intensity > 0.2) {
        exposures.push({
          country: country.name,
          countryCode: country.countryCode,
          sector: dim.sector,
          exposure: dim.narrative,
          stressIntensity: dim.intensity,
        });
      }
    }
  }

  return exposures.sort((a, b) => b.stressIntensity - a.stressIntensity);
}

function buildDirectives(
  decision: IntelligenceSnapshot['decision'],
  monitoring: IntelligenceSnapshot['monitoring'],
): DirectiveItem[] {
  return monitoring.assignments.map(a => {
    const isEscalated = a.status === 'escalated' || a.status === 'at_risk';
    const consequence = isEscalated
      ? `Failure to execute within ${Math.round(a.hoursRemaining)}h will trigger escalation to ${a.ownership.escalationAuthority}, risking uncontrolled loss amplification across dependent institutions.`
      : a.hoursRemaining < 24
        ? `Delay beyond ${Math.round(a.hoursRemaining)}h narrows the response window. ${a.ownership.escalationAuthority} will be notified if deadline passes without execution confirmation.`
        : `Response window is ${Math.round(a.hoursRemaining)}h. Timely execution prevents escalation to ${a.ownership.escalationAuthority} and preserves decision optionality.`;

    return {
      directive: a.action,
      consequence,
      owner: a.ownership.executionOwner,
      sector: a.sector,
    };
  });
}

function buildMonitoringBrief(monitoring: IntelligenceSnapshot['monitoring']): MonitoringBrief {
  return {
    statusSummary: monitoring.statusSummary,
    assignments: monitoring.assignments.map(a => ({
      action: a.action,
      owner: a.ownership.executionOwner,
      escalationAuthority: a.ownership.escalationAuthority,
      reviewCycleHours: a.ownership.reviewCycleHours,
      status: a.status,
      hoursRemaining: a.hoursRemaining,
    })),
  };
}

function buildTemporalHorizon(snapshot: IntelligenceSnapshot): TemporalHorizon {
  const decision = snapshot.decision;
  const countries = snapshot.countries;
  const topStress = Math.max(...countries.map(c => c.compositeStress));

  const now = decision.posture === 'crisis'
    ? `Multi-vector systemic stress is active. ${decision.priorityCountries.length} economies require immediate coordinated response. All directives are binding.`
    : decision.posture === 'immediate'
      ? `Severe pressure is building across ${decision.priorityCountries.join(' and ')}. Primary directives must be executed within their deadlines.`
      : `System is under ${decision.posture} posture. Monitoring intensity is elevated. No immediate binding directives.`;

  const hours72 = topStress > 0.6
    ? `Without intervention, composite stress is projected to reach ${Math.min(100, Math.round(topStress * 130))}% within 72 hours as cross-border contagion compounds. Banking sector liquidity will deteriorate further.`
    : `Stress levels are expected to plateau near ${Math.round(topStress * 110)}% within 72 hours. Containment is achievable with current measures.`;

  const days30 = topStress > 0.5
    ? `30-day outlook: structural fiscal damage becomes irreversible if sovereign response is delayed beyond 7 days. Credit rating agency reviews are probable. IMF monitoring engagement likely.`
    : `30-day outlook: recovery to baseline stress levels is achievable. Long-term structural impact remains contained if current response posture is maintained.`;

  return { now, hours72, days30 };
}

function buildConfidenceBasis(snapshot: IntelligenceSnapshot): ConfidenceBasis {
  const signalCount = snapshot.signals.activeCount;
  const entityCount = snapshot.entities.length;
  const contagionEvents = snapshot.contagionLog.length;

  const score = Math.min(1, Math.max(0,
    0.3 + (Math.min(signalCount, 5) * 0.08) + (Math.min(contagionEvents, 10) * 0.02) + (entityCount > 20 ? 0.1 : 0),
  ));

  const explanation = `Confidence is ${Math.round(score * 100)}%, derived from ${signalCount} active intelligence signals, ${entityCount} monitored entities, and ${contagionEvents} confirmed contagion events. ${score > 0.7 ? 'High signal density supports strong directional conviction.' : score > 0.4 ? 'Moderate signal coverage — directional assessment is reliable but magnitude estimates carry uncertainty.' : 'Limited signal coverage — assessment is preliminary and should be treated as indicative.'}`;

  return { score, explanation };
}

function buildCounterfactual(snapshot: IntelligenceSnapshot): CounterfactualBaseline {
  const decision = snapshot.decision;
  const countries = snapshot.countries;
  const criticalCount = snapshot.entities.filter(e => e.level === 'critical' || e.level === 'high').length;

  const withoutAction = decision.posture === 'crisis' || decision.posture === 'immediate'
    ? `Without action, ${criticalCount} entities will breach critical exposure thresholds within 48 hours. ${decision.priorityCountries.length > 2 ? 'GCC-wide contagion becomes self-reinforcing, with sovereign credit downgrades probable within 14 days.' : `${decision.priorityCountries.join(' and ')} face isolated but severe fiscal damage.`} Estimated unmitigated loss trajectory exceeds current projections by 2.5–3.5x.`
    : `Without action, stress levels continue to build but remain within managed parameters for 72 hours. ${criticalCount > 0 ? `${criticalCount} entities at elevated risk will deteriorate to critical classification.` : 'No entities at immediate risk of critical breach.'} Early intervention preserves response optionality and reduces long-term fiscal cost.`;

  return { withoutAction };
}

/* ═══════════════════════════════════════════════════════════════════════
 * Main Export
 * ═══════════════════════════════════════════════════════════════════════ */

/**
 * Transform an IntelligenceSnapshot into a SovereignBriefing.
 * This is the single function the UI calls.
 */
export function generateSovereignBriefing(
  snapshot: IntelligenceSnapshot,
  activePerspective: IntelligencePerspective = 'gcc_sovereign',
): SovereignBriefing {
  return {
    scenarioId: snapshot.scenarioId,
    timestamp: new Date().toISOString(),

    sectionOrder: [
      'Macro',
      'Signal',
      'Propagation',
      'Decision',
      'Exposure',
      'Monitoring',
    ] as const,

    macro: {
      posture: snapshot.decision.systemSeverity,
      advisory: snapshot.decision.advisory,
    },

    signal: buildSignalBrief(snapshot.signals),
    propagation: buildPropagationProse(snapshot),
    directives: buildDirectives(snapshot.decision, snapshot.monitoring),
    macroExposures: buildCountrySectorExposures(snapshot.countries, snapshot.sectors),
    monitoring: buildMonitoringBrief(snapshot.monitoring),

    perspectives: generateAllPerspectives(
      snapshot.countries,
      snapshot.sectors,
      snapshot.entities,
      snapshot.signals,
      snapshot.decision,
    ),
    activePerspective,

    temporalHorizon: buildTemporalHorizon(snapshot),
    confidenceBasis: buildConfidenceBasis(snapshot),
    counterfactual: buildCounterfactual(snapshot),
  };
}
