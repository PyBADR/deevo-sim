/**
 * Impact Observatory | مرصد الأثر — Decision Engine
 *
 * Reacts to real state changes across the intelligence core.
 * Decision urgency, posture, and language adapt dynamically
 * based on:
 *   - country stress levels
 *   - sector pressure
 *   - entity exposure
 *   - signal activation
 *
 * Deterministic. No randomness. Pure function of system state.
 */

import type { CountryMacroState } from './countryState';
import type { SectorState } from './sectorState';
import type { EntityExposureState } from './entityState';
import type { SignalEngineOutput } from './signalEngine';

/* ── Types ── */

export type DecisionPosture = 'monitoring' | 'advisory' | 'active' | 'immediate' | 'crisis';

export interface DecisionEngineOutput {
  /** Current decision posture */
  posture: DecisionPosture;
  /** Urgency multiplier for all active directives */
  urgencyMultiplier: number;
  /** Aggregate system severity label */
  systemSeverity: string;
  /** Prose advisory reflecting current system state */
  advisory: string;
  /** Which countries require immediate attention */
  priorityCountries: string[];
  /** Which sectors are under critical pressure */
  criticalSectors: string[];
  /** Which entities have overdue responses */
  overdueEntities: string[];
  /** Recommended escalation actions */
  escalationActions: string[];
}

/* ── Computation ── */

/**
 * Derive decision posture from composite system state.
 */
function derivePosture(
  maxCountryStress: number,
  maxSectorStress: number,
  criticalEntityCount: number,
  signalOutput: SignalEngineOutput,
): DecisionPosture {
  const compositeUrgency = (
    maxCountryStress * 0.30 +
    maxSectorStress * 0.25 +
    Math.min(1, criticalEntityCount * 0.15) * 0.25 +
    signalOutput.sectorAmplifier * 0.20
  );

  if (compositeUrgency >= 0.70) return 'crisis';
  if (compositeUrgency >= 0.55) return 'immediate';
  if (compositeUrgency >= 0.40) return 'active';
  if (compositeUrgency >= 0.25) return 'advisory';
  return 'monitoring';
}

/**
 * Generate human-readable system severity label.
 */
function severityLabel(posture: DecisionPosture): string {
  switch (posture) {
    case 'crisis':    return 'Critical — multi-vector systemic stress';
    case 'immediate': return 'Severe — immediate institutional response required';
    case 'active':    return 'Elevated — active decision execution in progress';
    case 'advisory':  return 'Guarded — heightened monitoring with advisory posture';
    case 'monitoring': return 'Nominal — system under observation';
  }
}

/**
 * Generate contextual advisory prose based on live system state.
 */
function generateAdvisory(
  posture: DecisionPosture,
  priorityCountries: string[],
  criticalSectors: string[],
  overdueEntities: string[],
  peakSignals: number,
): string {
  if (posture === 'crisis') {
    return `System under crisis-level stress. ${priorityCountries.length} GCC economies require coordinated response. ${criticalSectors.length} sectors at critical pressure. ${overdueEntities.length > 0 ? `${overdueEntities.length} entities with overdue response actions.` : ''} All directives should be treated as immediate-execution priority. ${peakSignals} intelligence signals at peak intensity.`;
  }
  if (posture === 'immediate') {
    return `Severe pressure detected across ${priorityCountries.join(', ')}. ${criticalSectors.join(' and ')} sectors are under sustained stress. Primary directives are binding and deadline compliance is critical. Signal intelligence indicates ${peakSignals > 0 ? `${peakSignals} signals at peak` : 'intensifying conditions'}.`;
  }
  if (posture === 'active') {
    return `Active scenario execution in progress. Country-level stress is elevated in ${priorityCountries.join(', ')}. ${criticalSectors.length > 0 ? `${criticalSectors.join(', ')} showing heightened transmission.` : 'Sector transmission is building.'} Directive deadlines are operative.`;
  }
  if (posture === 'advisory') {
    return `System in advisory posture. Early pressure signals detected. Monitoring country macro indicators and sector transmission paths. No immediate action required but readiness posture should be elevated.`;
  }
  return 'System nominal. Intelligence signals under routine observation. No macro stress detected above baseline thresholds.';
}

/**
 * Generate escalation actions based on system state.
 */
function generateEscalationActions(
  posture: DecisionPosture,
  priorityCountries: string[],
  criticalSectors: string[],
  overdueEntities: string[],
): string[] {
  const actions: string[] = [];

  if (posture === 'crisis' || posture === 'immediate') {
    if (priorityCountries.length > 2) {
      actions.push('Activate GCC-wide coordination protocol across all affected sovereign entities');
    }
    if (criticalSectors.includes('Banking')) {
      actions.push('Invoke emergency liquidity backstop via coordinated central bank action');
    }
    if (criticalSectors.includes('Oil & Gas')) {
      actions.push('Activate strategic petroleum reserve release protocol');
    }
    if (overdueEntities.length > 0) {
      actions.push(`Escalate ${overdueEntities.length} overdue entity response actions to ministerial level`);
    }
  }

  if (posture === 'active') {
    actions.push('Ensure all primary directive owners have confirmed receipt and execution timeline');
    if (criticalSectors.length > 0) {
      actions.push(`Monitor ${criticalSectors.join(', ')} sector transmission for escalation triggers`);
    }
  }

  if (posture === 'advisory') {
    actions.push('Increase monitoring frequency on priority country macro indicators');
    actions.push('Pre-position decision authority chain for potential activation');
  }

  return actions;
}

/**
 * Run the decision engine against current system state.
 */
export function runDecisionEngine(
  countries: CountryMacroState[],
  sectors: SectorState[],
  entities: EntityExposureState[],
  signalOutput: SignalEngineOutput,
): DecisionEngineOutput {
  // Find maximums
  const maxCountryStress = Math.max(...countries.map(c => c.compositeStress), 0);
  const maxSectorStress = Math.max(...sectors.map(s => s.stress), 0);

  // Identify critical entities
  const criticalEntities = entities.filter(e => e.level === 'critical' || e.level === 'high');
  const overdueEntities = entities.filter(e => e.responseStatus === 'overdue').map(e => e.name);

  // Priority countries: those above 50% composite stress
  const priorityCountries = countries
    .filter(c => c.compositeStress > 0.40)
    .sort((a, b) => b.compositeStress - a.compositeStress)
    .map(c => c.name);

  // Critical sectors: those at severe or critical
  const criticalSectors = sectors
    .filter(s => s.level === 'severe' || s.level === 'critical')
    .map(s => s.label);

  // Derive posture
  const posture = derivePosture(maxCountryStress, maxSectorStress, criticalEntities.length, signalOutput);

  // Urgency multiplier: blend of signal urgency and state-derived urgency
  const stateUrgency = posture === 'crisis' ? 2.5
    : posture === 'immediate' ? 2.0
      : posture === 'active' ? 1.5
        : posture === 'advisory' ? 1.2
          : 1.0;
  const urgencyMultiplier = Math.min(3.0, stateUrgency * signalOutput.decisionUrgencyMod * 0.7 + stateUrgency * 0.3);

  return {
    posture,
    urgencyMultiplier,
    systemSeverity: severityLabel(posture),
    advisory: generateAdvisory(posture, priorityCountries, criticalSectors, overdueEntities, signalOutput.peakCount),
    priorityCountries,
    criticalSectors,
    overdueEntities,
    escalationActions: generateEscalationActions(posture, priorityCountries, criticalSectors, overdueEntities),
  };
}
