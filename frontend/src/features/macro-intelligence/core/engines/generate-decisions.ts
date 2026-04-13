import type { DecisionDirective } from "../types/intelligence";

export function generateDecisionDirectives(): DecisionDirective[] {
  return [
    {
      id: "dir_1",
      action: "Activate Strategic Petroleum Reserve release",
      owner: "Ministry of Energy",
      sector: "oil_and_gas",
      urgency: 92,
      rationale: "Immediate supply stabilization reduces macro stress amplification across energy and logistics.",
      consequenceOfDelay: "Losses accelerate across interconnected sectors and reduce policy optionality.",
      escalationAuthority: "Head of State / Crown Prince Office",
      reviewCadenceHours: 4,
    },
    {
      id: "dir_2",
      action: "Deploy emergency vessel rerouting protocol",
      owner: "Federal Transport Authority",
      sector: "logistics",
      urgency: 88,
      rationale: "Regional shipping rerouting reduces terminal backlog and protects supply continuity.",
      consequenceOfDelay: "Port congestion compounds and time-to-recovery expands across GCC logistics.",
      escalationAuthority: "GCC Transport Coordination Authority",
      reviewCadenceHours: 4,
    },
    {
      id: "dir_3",
      action: "Trigger marine catastrophe reserve allocation",
      owner: "Insurance Authority",
      sector: "insurance",
      urgency: 78,
      rationale: "Reserve posture reduces claims stress and stabilizes insurance response capacity.",
      consequenceOfDelay: "Marine claims pressure widens into solvency and treaty repricing risk.",
      escalationAuthority: "Ministry of Finance",
      reviewCadenceHours: 6,
    },
  ];
}
