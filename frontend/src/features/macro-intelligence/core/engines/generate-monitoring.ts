import type { MonitoringStatus } from "../types/intelligence";
import { generateDecisionDirectives } from "./generate-decisions";

export function generateMonitoringStatuses(): MonitoringStatus[] {
  const now = Date.now();
  return generateDecisionDirectives().map((directive, i) => ({
    directiveId: directive.id,
    owner: directive.owner,
    currentStatus: i === 0 ? "overdue" : i === 1 ? "in_progress" : "pending",
    nextReviewIso: new Date(now + directive.reviewCadenceHours * 60 * 60 * 1000).toISOString(),
    escalationAuthority: directive.escalationAuthority,
    confirmationCriteria: [
      "Action owner formally activated",
      "First review cycle completed",
      "Transmission pressure no longer increasing",
    ],
  }));
}
