/**
 * Impact Observatory | مرصد الأثر — System Loop
 *
 * The complete intelligence cycle:
 *
 *   Signal
 *     → Country State
 *       → Sector Transmission
 *         → Entity Exposure
 *           → Propagation (cascading effects)
 *             → Decision
 *               → Monitoring
 *                 → Evaluation feedback
 *
 * One function call produces the entire intelligence snapshot.
 * Deterministic. Expandable. Sovereign-grade.
 */

import { computeAllCountryStates, type CountryMacroState, type GCCCountry } from './countryState';
import { computeAllSectorStates, type SectorState } from './sectorState';
import { computeAllEntityExposures, type EntityExposureState } from './entityState';
import { processSignals, type SignalEngineOutput } from './signalEngine';
import { runPropagation, type PropagationResult, type ContagionEvent } from './propagationEngine';
import { runDecisionEngine, type DecisionEngineOutput, type DecisionPosture } from './decisionEngine';
import { computeMonitoringState, type MonitoringState } from './monitoringEngine';

/* ── Types ── */

export interface IntelligenceSnapshot {
  /** Scenario this snapshot belongs to */
  scenarioId: string;
  /** Normalised progress 0→1 */
  t: number;
  /** Hours elapsed */
  elapsedHours: number;
  /** Horizon hours */
  horizonHours: number;
  /** Base risk score from existing system (0–1) */
  baseRisk: number;

  /** Signal engine output */
  signals: SignalEngineOutput;
  /** Country-level macro states (post-propagation) */
  countries: CountryMacroState[];
  /** Sector transmission states (post-propagation) */
  sectors: SectorState[];
  /** Entity exposure states (post-propagation) */
  entities: EntityExposureState[];
  /** Contagion events from this tick */
  contagionLog: ContagionEvent[];
  /** Decision engine output */
  decision: DecisionEngineOutput;
  /** Monitoring state */
  monitoring: MonitoringState;

  /** Summary metrics for quick UI consumption */
  summary: IntelligenceSummary;
}

export interface IntelligenceSummary {
  /** Most stressed country */
  mostStressedCountry: string;
  /** Most stressed country composite value */
  mostStressedCountryValue: number;
  /** Most pressured sector */
  mostPressuredSector: string;
  /** Most pressured sector stress value */
  mostPressuredSectorValue: number;
  /** Number of entities at critical/high exposure */
  criticalEntityCount: number;
  /** Number of active signals */
  activeSignalCount: number;
  /** Decision posture label */
  decisionPosture: DecisionPosture;
  /** Total contagion events this tick */
  contagionEventCount: number;
  /** Monitoring phase */
  monitoringPhase: string;
}

/**
 * Idle snapshot returned when no scenario is active.
 */
export const IDLE_INTELLIGENCE: IntelligenceSnapshot = {
  scenarioId: '',
  t: 0,
  elapsedHours: 0,
  horizonHours: 0,
  baseRisk: 0,
  signals: { activeSignals: [], sectorAmplifier: 0, decisionUrgencyMod: 1.0, peakCount: 0, activeCount: 0 },
  countries: [],
  sectors: [],
  entities: [],
  contagionLog: [],
  decision: {
    posture: 'monitoring',
    urgencyMultiplier: 1.0,
    systemSeverity: 'Nominal — system under observation',
    advisory: 'No active scenario. Intelligence system idle.',
    priorityCountries: [],
    criticalSectors: [],
    overdueEntities: [],
    escalationActions: [],
  },
  monitoring: {
    scenarioId: '',
    phase: 'pre_activation',
    assignments: [],
    hoursUntilReview: 0,
    escalationCount: 0,
    statusSummary: 'System idle.',
  },
  summary: {
    mostStressedCountry: '',
    mostStressedCountryValue: 0,
    mostPressuredSector: '',
    mostPressuredSectorValue: 0,
    criticalEntityCount: 0,
    activeSignalCount: 0,
    decisionPosture: 'monitoring',
    contagionEventCount: 0,
    monitoringPhase: 'pre_activation',
  },
};

/* ── Main Loop ── */

/**
 * Execute the full intelligence loop for a given scenario at a given time point.
 *
 * @param scenarioId - active scenario ID
 * @param elapsedHours - hours since activation
 * @param horizonHours - total scenario horizon
 * @param baseRisk - risk score from existing systemState (0–1)
 * @param decisions - decision actions from the scenario manifest
 */
export function runIntelligenceLoop(
  scenarioId: string,
  elapsedHours: number,
  horizonHours: number,
  baseRisk: number,
  decisions: Array<{ action: string; owner: string; deadline: string; sector: string }>,
): IntelligenceSnapshot {
  const t = Math.min(elapsedHours / Math.max(horizonHours, 1), 1);

  // 1. SIGNAL PROCESSING
  const signals = processSignals(scenarioId, t, elapsedHours);

  // 2. COUNTRY STATE (raw, before propagation)
  const rawCountries = computeAllCountryStates(scenarioId, t, baseRisk);

  // 3. SECTOR TRANSMISSION (raw, before propagation)
  const rawSectors = computeAllSectorStates(rawCountries, elapsedHours, signals.sectorAmplifier);

  // 4. ENTITY EXPOSURE (raw, before propagation)
  const rawEntities = computeAllEntityExposures(rawCountries, rawSectors, t);

  // 5. PROPAGATION — cascading effects across all three layers
  const propagation: PropagationResult = runPropagation(rawCountries, rawSectors, rawEntities);

  // 6. DECISION ENGINE — react to post-propagation state
  const decision = runDecisionEngine(
    propagation.countries,
    propagation.sectors,
    propagation.entities,
    signals,
  );

  // 7. MONITORING ENGINE — track decision execution
  const monitoring = computeMonitoringState(
    scenarioId,
    decisions,
    elapsedHours,
    horizonHours,
    decision.posture,
  );

  // 8. SUMMARY — quick consumption metrics
  const sortedCountries = [...propagation.countries].sort((a, b) => b.compositeStress - a.compositeStress);
  const sortedSectors = [...propagation.sectors].sort((a, b) => b.stress - a.stress);
  const criticalEntityCount = propagation.entities.filter(
    e => e.level === 'critical' || e.level === 'high',
  ).length;

  const summary: IntelligenceSummary = {
    mostStressedCountry: sortedCountries[0]?.name ?? '',
    mostStressedCountryValue: sortedCountries[0]?.compositeStress ?? 0,
    mostPressuredSector: sortedSectors[0]?.label ?? '',
    mostPressuredSectorValue: sortedSectors[0]?.stress ?? 0,
    criticalEntityCount,
    activeSignalCount: signals.activeCount,
    decisionPosture: decision.posture,
    contagionEventCount: propagation.contagionLog.length,
    monitoringPhase: monitoring.phase,
  };

  return {
    scenarioId,
    t,
    elapsedHours,
    horizonHours,
    baseRisk,
    signals,
    countries: propagation.countries,
    sectors: propagation.sectors,
    entities: propagation.entities,
    contagionLog: propagation.contagionLog,
    decision,
    monitoring,
    summary,
  };
}
