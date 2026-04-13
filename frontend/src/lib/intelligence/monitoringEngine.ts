/**
 * Impact Observatory | مرصد الأثر — Monitoring Engine
 *
 * Every decision must have:
 *   - owner (institution responsible for execution)
 *   - monitoring owner (institution responsible for oversight)
 *   - escalation authority (who gets involved if deadline missed)
 *   - review cycle (how often status is re-evaluated)
 *
 * Monitoring state evolves as the scenario progresses:
 *   - Pre-activation: ownership assigned, awaiting trigger
 *   - Active monitoring: tracking execution against deadline
 *   - Escalation: deadline missed or severity increased
 *   - Review: periodic re-assessment of decision effectiveness
 *   - Closed: scenario resolved, final evaluation pending
 */

import type { DecisionPosture } from './decisionEngine';
import type { EntityExposureState } from './entityState';

/* ── Types ── */

export type MonitoringPhase = 'pre_activation' | 'active_monitoring' | 'escalation' | 'review' | 'closed';

export interface MonitoringOwnership {
  /** Institution responsible for executing the decision */
  executionOwner: string;
  /** Institution responsible for monitoring execution */
  monitoringOwner: string;
  /** Authority escalated to if execution fails or deadline passes */
  escalationAuthority: string;
  /** Hours between status reviews */
  reviewCycleHours: number;
}

export interface MonitoringState {
  /** Scenario being monitored */
  scenarioId: string;
  /** Current monitoring phase */
  phase: MonitoringPhase;
  /** All ownership assignments */
  assignments: MonitoringAssignment[];
  /** Hours until next review */
  hoursUntilReview: number;
  /** Number of escalations triggered */
  escalationCount: number;
  /** Summary of monitoring status */
  statusSummary: string;
}

export interface MonitoringAssignment {
  /** Decision action being monitored */
  action: string;
  /** Sector context */
  sector: string;
  /** Ownership chain */
  ownership: MonitoringOwnership;
  /** Current status */
  status: 'pending' | 'active' | 'on_track' | 'at_risk' | 'escalated' | 'completed';
  /** Deadline (from decision data) */
  deadline: string;
  /** Hours remaining (computed) */
  hoursRemaining: number;
}

/* ── Default Ownership Mapping ──
   Maps sector → default institutional chain.
   Scenario-specific overrides come from decision data.
*/

const SECTOR_OWNERSHIP: Record<string, MonitoringOwnership> = {
  Energy: {
    executionOwner: 'Ministry of Energy / National Oil Company',
    monitoringOwner: 'Supreme Council Economic Affairs Committee',
    escalationAuthority: 'GCC Supreme Council',
    reviewCycleHours: 4,
  },
  Banking: {
    executionOwner: 'Central Bank',
    monitoringOwner: 'Financial Stability Committee',
    escalationAuthority: 'Ministry of Finance',
    reviewCycleHours: 6,
  },
  Insurance: {
    executionOwner: 'Insurance Authority / Regulator',
    monitoringOwner: 'Central Bank Supervisory Division',
    escalationAuthority: 'Ministry of Finance',
    reviewCycleHours: 12,
  },
  Shipping: {
    executionOwner: 'Port Authority / Maritime Administration',
    monitoringOwner: 'Ministry of Commerce',
    escalationAuthority: 'Cabinet / Economic Council',
    reviewCycleHours: 8,
  },
  Government: {
    executionOwner: 'Ministry of Finance',
    monitoringOwner: 'Supreme Council Economic Affairs Committee',
    escalationAuthority: 'Head of State / Crown Prince Office',
    reviewCycleHours: 4,
  },
  OilGas: {
    executionOwner: 'National Oil Company',
    monitoringOwner: 'Ministry of Energy',
    escalationAuthority: 'Supreme Council / OPEC Coordination',
    reviewCycleHours: 4,
  },
  Fintech: {
    executionOwner: 'Central Bank Digital Payments Division',
    monitoringOwner: 'Financial Regulatory Authority',
    escalationAuthority: 'Central Bank Governor',
    reviewCycleHours: 8,
  },
  RealEstate: {
    executionOwner: 'Real Estate Regulatory Authority',
    monitoringOwner: 'Ministry of Housing / Municipal Affairs',
    escalationAuthority: 'Ministry of Finance',
    reviewCycleHours: 24,
  },
};

/* ── Computation ── */

function parseDeadlineHours(deadline: string): number {
  const match = deadline.match(/(\d+)\s*(hour|h)/i);
  if (match) return parseInt(match[1], 10);
  const dayMatch = deadline.match(/(\d+)\s*(day|d)/i);
  if (dayMatch) return parseInt(dayMatch[1], 10) * 24;
  return 48; // default 48h if unparseable
}

function deriveAssignmentStatus(
  hoursRemaining: number,
  elapsedHours: number,
  deadlineHours: number,
  posture: DecisionPosture,
): MonitoringAssignment['status'] {
  if (hoursRemaining <= 0) return 'escalated';
  if (posture === 'crisis' && hoursRemaining < deadlineHours * 0.25) return 'at_risk';
  if (elapsedHours < 1) return 'pending';
  const progress = 1 - (hoursRemaining / deadlineHours);
  if (progress > 0.8) return 'at_risk';
  if (progress > 0.3) return 'on_track';
  return 'active';
}

function derivePhase(
  t: number,
  posture: DecisionPosture,
  escalationCount: number,
): MonitoringPhase {
  if (t >= 0.95) return 'closed';
  if (escalationCount > 0 || posture === 'crisis') return 'escalation';
  if (t > 0.7) return 'review';
  if (t > 0.05) return 'active_monitoring';
  return 'pre_activation';
}

/**
 * Generate monitoring assignments from scenario decisions.
 */
export function computeMonitoringState(
  scenarioId: string,
  decisions: Array<{ action: string; owner: string; deadline: string; sector: string }>,
  elapsedHours: number,
  horizonHours: number,
  posture: DecisionPosture,
): MonitoringState {
  const t = Math.min(elapsedHours / Math.max(horizonHours, 1), 1);

  const assignments: MonitoringAssignment[] = decisions.map(d => {
    const deadlineHours = parseDeadlineHours(d.deadline);
    const hoursRemaining = Math.max(0, deadlineHours - elapsedHours);
    const ownership = SECTOR_OWNERSHIP[d.sector] ?? SECTOR_OWNERSHIP.Government;

    // Override execution owner with decision-specified owner
    const customOwnership: MonitoringOwnership = {
      ...ownership,
      executionOwner: d.owner,
    };

    return {
      action: d.action,
      sector: d.sector,
      ownership: customOwnership,
      status: deriveAssignmentStatus(hoursRemaining, elapsedHours, deadlineHours, posture),
      deadline: d.deadline,
      hoursRemaining,
    };
  });

  const escalationCount = assignments.filter(a => a.status === 'escalated').length;
  const atRiskCount = assignments.filter(a => a.status === 'at_risk').length;
  const phase = derivePhase(t, posture, escalationCount);

  // Review cycle: shortest among all assignments
  const minReviewCycle = Math.min(
    ...assignments.map(a => a.ownership.reviewCycleHours),
    24,
  );
  const hoursUntilReview = minReviewCycle - (elapsedHours % minReviewCycle);

  // Status summary
  let statusSummary: string;
  if (phase === 'closed') {
    statusSummary = 'Scenario monitoring closed. Final evaluation pending.';
  } else if (escalationCount > 0) {
    statusSummary = `${escalationCount} decision${escalationCount > 1 ? 's' : ''} past deadline — escalation authority engaged. ${atRiskCount > 0 ? `${atRiskCount} additional at risk.` : ''}`;
  } else if (atRiskCount > 0) {
    statusSummary = `${atRiskCount} decision${atRiskCount > 1 ? 's' : ''} at risk of missing deadline. Monitoring intensity increased.`;
  } else if (phase === 'review') {
    statusSummary = 'Periodic review cycle. Assessing decision effectiveness against monitoring criteria.';
  } else if (phase === 'active_monitoring') {
    statusSummary = `Active monitoring in progress. ${assignments.filter(a => a.status === 'on_track').length} decisions on track. Next review in ${Math.round(hoursUntilReview)}h.`;
  } else {
    statusSummary = 'Pre-activation. Decision ownership assigned, awaiting scenario trigger.';
  }

  return {
    scenarioId,
    phase,
    assignments,
    hoursUntilReview,
    escalationCount,
    statusSummary,
  };
}
