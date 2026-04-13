/**
 * ScenarioGallery — curated grid of macro scenarios.
 *
 * Visual rules:
 *   - section title + subtitle
 *   - 3-column grid on desktop, 2 on tablet, 1 on mobile
 *   - max 6 cards (no more than 4 per row)
 *   - each card carries loss estimate, sector count, and time horizon
 *   - muted background section
 */

import { Container } from "@/components/layout/Container";
import { SectionTitle } from "@/components/primitives/SectionTitle";
import { ScenarioCard } from "./ScenarioCard";
import type { ScenarioCardData } from "./ScenarioCard";
import { scenarioGallery } from "@/lib/copy";

const FEATURED_SCENARIOS: ScenarioCardData[] = [
  {
    title: "Strait of Hormuz Disruption",
    domain: "Energy & Trade",
    severity: 0.72,
    description:
      "Partial closure reduces energy transit by 60%, triggering cascading financial exposure across energy, trade, and banking sectors.",
    slug: "hormuz_chokepoint_disruption",
    estimatedLoss: "$3.8B\u2013$4.7B",
    sectorsAffected: 6,
    horizonDays: 7,
  },
  {
    title: "Regional Liquidity Stress",
    domain: "Banking & Finance",
    severity: 0.68,
    description:
      "Interbank rate spike of 280bps cascades through GCC banking systems, causing deposit flight and cross-border contagion.",
    slug: "regional_liquidity_stress_event",
    estimatedLoss: "$2.2B\u2013$3.1B",
    sectorsAffected: 5,
    horizonDays: 14,
  },
  {
    title: "Saudi Oil Production Shock",
    domain: "Energy",
    severity: 0.75,
    description:
      "Major disruption to Saudi Aramco production capacity triggers commodity price shock and downstream fiscal revenue contraction.",
    slug: "saudi_oil_shock",
    estimatedLoss: "$4.1B\u2013$5.2B",
    sectorsAffected: 5,
    horizonDays: 10,
  },
  {
    title: "Red Sea Trade Corridor",
    domain: "Trade & Logistics",
    severity: 0.6,
    description:
      "Red Sea shipping disruption forces rerouting of commercial traffic, impacting GCC trade volumes and logistics costs.",
    slug: "red_sea_trade_corridor_instability",
    estimatedLoss: "$1.4B\u2013$2.1B",
    sectorsAffected: 4,
    horizonDays: 21,
  },
  {
    title: "GCC Cyber Infrastructure Attack",
    domain: "Financial Infrastructure",
    severity: 0.7,
    description:
      "Coordinated attack on regional financial infrastructure disrupts payment systems, settlement, and interbank operations.",
    slug: "gcc_cyber_attack",
    estimatedLoss: "$2.8B\u2013$3.6B",
    sectorsAffected: 5,
    horizonDays: 5,
  },
  {
    title: "Iran Regional Escalation",
    domain: "Geopolitical",
    severity: 0.78,
    description:
      "Regional geopolitical escalation drives commodity volatility, capital flight, and sovereign risk repricing across the GCC.",
    slug: "iran_regional_escalation",
    estimatedLoss: "$5.2B\u2013$7.0B",
    sectorsAffected: 7,
    horizonDays: 14,
  },
];

export function ScenarioGallery() {
  return (
    <Container>
      <SectionTitle
        heading={scenarioGallery.heading}
        subtitle={scenarioGallery.subtitle}
      />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {FEATURED_SCENARIOS.map((scenario) => (
          <ScenarioCard key={scenario.slug} {...scenario} />
        ))}
      </div>
    </Container>
  );
}
