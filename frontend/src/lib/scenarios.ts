/**
 * Impact Observatory — Scenario Briefing Data
 *
 * Observatory-grade briefings for GCC decision-makers.
 * Each scenario is a self-contained narrative with five sections:
 *   Context → Transmission → Impact → Decision → Outcome
 *
 * Every field uses business language written for central bank governors,
 * sovereign wealth fund CIOs, and ministry officials. No template prose.
 * No placeholder text. Each line reads like a macro-financial analyst wrote it.
 */

// ── Types ───────────────────────────────────────────────────────────

export interface TransmissionStep {
  origin: string;
  destination: string;
  delay: string;
  mechanism: string;
}

export interface ExposureEntry {
  entity: string;
  sector: string;
  exposure: string;
  severity: "Critical" | "Elevated" | "Moderate" | "Low";
}

export interface DecisionEntry {
  action: string;
  owner: string;
  deadline: string;
  sector: string;
}

export interface ScenarioBriefing {
  slug: string;
  // ── Context ──
  severity: number;
  domain: string;
  horizon: string;
  sectors: number;
  title: string;
  summary: string;
  significance: string;
  // ── Transmission ──
  transmissionFraming: string;
  transmissionChain: TransmissionStep[];
  // ── Impact ──
  impactFraming: string;
  exposureRegister: ExposureEntry[];
  // ── Decision ──
  decisionFraming: string;
  actions: DecisionEntry[];
  // ── Outcome ──
  outcomeNarrative: string;
  monitoringCriteria: string[];
}

// ── Scenario Registry ───────────────────────────────────────────────

export const scenarios: Record<string, ScenarioBriefing> = {
  // ═══════════════════════════════════════════════════════════════════
  // HORMUZ CHOKEPOINT DISRUPTION
  // ═══════════════════════════════════════════════════════════════════
  hormuz_chokepoint_disruption: {
    slug: "hormuz_chokepoint_disruption",

    // ── Context ──
    severity: 0.72,
    domain: "Energy & Trade",
    horizon: "7 days",
    sectors: 6,
    title: "Strait of Hormuz Disruption",
    summary:
      "A partial naval blockade restricts vessel transit through the Strait of Hormuz, reducing energy throughput by approximately 60%. The disruption immediately affects 17\u201320 million barrels per day of crude oil and condensate transit, along with 25% of global LNG trade volume. Within hours, Brent crude spot prices surge $25\u201340 per barrel. Export terminals at Ras Tanura and Fujairah face operational standstill. Container throughput at Jebel Ali drops below 40% of baseline within 48 hours as rerouting through the Bab el-Mandeb corridor adds 7\u201310 days to shipping schedules.",
    significance:
      "For GCC decision-makers, this scenario represents the single highest-concentration risk in the regional economic architecture. Saudi Arabia and the UAE together depend on Hormuz for over 80% of their hydrocarbon export revenue. A 7-day disruption at this severity level translates to $3.8B\u2013$4.7B in direct financial exposure across energy, trade, banking, and insurance sectors \u2014 before accounting for second-order effects on sovereign credit positioning and foreign reserve drawdown. The window for coordinated central bank and ministry-level intervention is 48\u201372 hours before market contagion mechanisms become self-reinforcing.",

    // ── Transmission ──
    transmissionFraming:
      "The disruption propagates through three primary transmission channels: physical infrastructure constraints, commodity price pass-through, and financial market contagion. Each channel amplifies the next within 24\u201348 hours.",
    transmissionChain: [
      {
        origin: "Strait of Hormuz",
        destination: "Ras Tanura Terminal",
        delay: "Immediate",
        mechanism:
          "Physical blockade halts tanker transit at the chokepoint, creating an immediate queue of 80\u2013120 loaded vessels. Ras Tanura export capacity falls to approximately 40% as terminal storage reaches operational limits and outbound scheduling collapses.",
      },
      {
        origin: "Strait of Hormuz",
        destination: "Brent Crude (Global)",
        delay: "0\u20134 hours",
        mechanism:
          "Supply constraint of 17\u201320M barrels/day drives Brent crude spot price escalation of $25\u201340/barrel within hours. Futures curve enters steep backwardation. Energy-importing GCC neighbors face immediate fiscal pressure from refined product cost increases.",
      },
      {
        origin: "Ras Tanura Terminal",
        destination: "Saudi Aramco",
        delay: "6\u201312 hours",
        mechanism:
          "Export revenue contraction begins as force majeure clauses activate on term contracts. Daily revenue loss reaches $380\u2013420M. Aramco triggers contingency drawdown of strategic storage at Ras Tanura and Yanbu, but Yanbu pipeline capacity covers only 25\u201330% of eastern terminal throughput.",
      },
      {
        origin: "Strait of Hormuz",
        destination: "Jebel Ali Port",
        delay: "12\u201324 hours",
        mechanism:
          "Container rerouting through Bab el-Mandeb adds 7\u201310 days to transit times. Jebel Ali throughput drops below 40% of baseline. The port\u2019s role as a re-export hub for 14 regional markets means the disruption cascades into East African and South Asian supply chains within 72 hours.",
      },
      {
        origin: "Brent Crude",
        destination: "GCC Insurance Sector",
        delay: "24\u201348 hours",
        mechanism:
          "Marine Protection & Indemnity claims surge 4.2x baseline as war-risk premiums reprice across the Gulf. Lloyd\u2019s syndicates and regional reinsurers face aggregate exposure thresholds. IFRS 17 catastrophe reserve calculations trigger mandatory disclosure requirements.",
      },
      {
        origin: "Saudi Aramco",
        destination: "SAMA (Central Bank)",
        delay: "48\u201372 hours",
        mechanism:
          "Reduced hydrocarbon receipts compress fiscal revenue by $1.8\u20132.2B over the 7-day window. SAMA faces simultaneous pressure on foreign exchange reserves as the central bank intervenes to defend the riyal peg. Interbank liquidity tightens as banks pull precautionary buffers.",
      },
      {
        origin: "Jebel Ali Port",
        destination: "GCC Trade Volume",
        delay: "48\u201396 hours",
        mechanism:
          "Cross-border trade contraction reaches 35\u201340% of baseline across non-energy goods. Letters of credit face delayed settlement. SME supply chains in UAE, Bahrain, and Oman experience working capital stress as receivables extend beyond 90-day terms.",
      },
    ],

    // ── Impact ──
    impactFraming:
      "Institutional exposure concentrates in energy infrastructure and sovereign fiscal channels. The six sectors below absorb the initial shock in order of severity. Loss estimates reflect the 7-day horizon at 90% confidence.",
    exposureRegister: [
      {
        entity: "Saudi Aramco",
        sector: "Energy",
        exposure: "$2.1B in export revenue at risk over the 7-day horizon, with daily revenue loss of $380\u2013420M from Ras Tanura and Fujairah terminal disruption",
        severity: "Critical",
      },
      {
        entity: "Brent Crude Markets",
        sector: "Commodities",
        exposure: "$25\u201340/barrel spot price premium creates $1.2B in mark-to-market losses across GCC energy derivative positions",
        severity: "Critical",
      },
      {
        entity: "Jebel Ali Port Authority",
        sector: "Trade",
        exposure: "$750M in trade flow disruption as throughput drops below 40% and rerouting adds 7\u201310 days to 14 regional supply chains",
        severity: "Elevated",
      },
      {
        entity: "GCC Banking Sector",
        sector: "Banking",
        exposure: "$890M in interbank liquidity pressure as precautionary reserve drawdowns tighten overnight lending by 120\u2013180bps",
        severity: "Elevated",
      },
      {
        entity: "Regional Insurance Carriers",
        sector: "Insurance",
        exposure: "$410M in marine P&I claims acceleration at 4.2x baseline, with IFRS 17 catastrophe reserves approaching depletion thresholds",
        severity: "Moderate",
      },
      {
        entity: "UAE Real Estate Finance",
        sector: "Real Estate",
        exposure: "$340M in developer financing pressure as interbank rate transmission adds 80\u2013120bps to mortgage pipeline costs",
        severity: "Moderate",
      },
      {
        entity: "GCC Sovereign Fiscal Position",
        sector: "Government",
        exposure: "$180M in fiscal revenue shortfall as hydrocarbon receipts compress and sovereign wealth fund stabilization reserves face drawdown pressure",
        severity: "Low",
      },
    ],

    // ── Decision ──
    decisionFraming:
      "Four coordinated interventions are required within the first 72 hours. Delays beyond the stated deadlines allow market contagion to become self-reinforcing, significantly increasing total financial exposure.",
    actions: [
      {
        action: "Release strategic petroleum reserves through coordinated SAMA and Ministry of Energy activation, targeting 2.4M barrels/day of supplementary supply to offset eastern terminal losses.",
        owner: "Ministry of Energy",
        deadline: "6 hours",
        sector: "Energy",
      },
      {
        action: "Deploy emergency vessel rerouting protocols through the Bab el-Mandeb corridor, prioritizing energy cargoes and perishable container freight for Jebel Ali-bound traffic.",
        owner: "Federal Transport Authority",
        deadline: "12 hours",
        sector: "Maritime",
      },
      {
        action: "Coordinate bilateral FX swap lines between SAMA and CBUAE to inject $4\u20136B in interbank liquidity, stabilizing overnight lending rates below the 200bps escalation threshold.",
        owner: "SAMA + CBUAE",
        deadline: "18 hours",
        sector: "Finance",
      },
      {
        action: "Trigger IFRS 17 catastrophe reserve allocation for marine Protection & Indemnity lines, activating excess-of-loss reinsurance treaties at standard contractual thresholds.",
        owner: "Insurance Authority",
        deadline: "24 hours",
        sector: "Insurance",
      },
    ],

    // ── Outcome ──
    outcomeNarrative:
      "If all four interventions execute within their deadlines, total financial exposure reduces from $4.3B to approximately $1.5B \u2014 preserving $2.8B in economic value across the GCC. Strategic petroleum reserve activation covers 60\u201370% of the eastern terminal shortfall within 48 hours. Vessel rerouting restores Jebel Ali throughput to 65% of baseline by Day 5. Interbank rate stabilization prevents the credit contagion channel from activating. Insurance reserve allocation contains marine claims within existing treaty limits. Full recovery to pre-disruption baseline requires 42 days, assuming diplomatic resolution within 10 days of the initial event.",
    monitoringCriteria: [
      "Ras Tanura throughput recovers above 60% within 72 hours of SPR activation \u2014 if not, escalate to full Yanbu pipeline diversion",
      "Brent\u2013WTI spread narrows below $15/barrel within 5 days \u2014 persistent premium above $20 indicates structural supply dislocation beyond this scenario\u2019s assumptions",
      "Interbank overnight rate remains below 200bps spread after SAMA/CBUAE intervention \u2014 breach above 250bps for 12+ hours triggers secondary banking stress protocols",
      "Marine P&I claims trajectory stays within 5x baseline \u2014 breach above 6x indicates reinsurance treaty capacity will be exhausted before the 14-day treaty period",
    ],
  },

  // ═══════════════════════════════════════════════════════════════════
  // REGIONAL LIQUIDITY STRESS EVENT
  // ═══════════════════════════════════════════════════════════════════
  regional_liquidity_stress_event: {
    slug: "regional_liquidity_stress_event",

    // ── Context ──
    severity: 0.68,
    domain: "Banking & Finance",
    horizon: "14 days",
    sectors: 5,
    title: "Regional Liquidity Stress",
    summary:
      "A sudden interbank rate dislocation of 280 basis points freezes overnight lending across GCC money markets. The trigger is a combination of large-scale deposit withdrawal from three systemically important UAE banks and simultaneous tightening of cross-border funding lines from international correspondent banks. Within 48 hours, deposit outflows reach 3.2% of total system deposits. The interbank market fragments along national lines, with UAE, Saudi, and Bahraini institutions losing access to each other\u2019s liquidity pools.",
    significance:
      "GCC banking systems are more interconnected than their regulatory frameworks acknowledge. Cross-border interbank exposures total approximately $180B, concentrated among 12 systemically important institutions. A liquidity freeze of this severity last occurred in modified form during the 2020 oil price collapse, when SAMA and CBUAE jointly injected $13B to prevent cascading failures. The current scenario is more severe because it combines deposit flight with correspondent banking withdrawal \u2014 attacking both sides of bank funding simultaneously. Decision-makers have a 48-hour window before the credit channel transmission converts a liquidity event into a solvency discussion.",

    // ── Transmission ──
    transmissionFraming:
      "Liquidity stress transmits through four channels in sequence: interbank market freeze, deposit flight, credit tightening, and sovereign spread widening. Each channel activates within 24\u201348 hours of the previous one.",
    transmissionChain: [
      {
        origin: "GCC Interbank Market",
        destination: "UAE Banking Sector",
        delay: "0\u201312 hours",
        mechanism:
          "Overnight lending rate spikes 280bps as counterparty risk repricing freezes bilateral credit lines. Three systemically important banks lose access to interbank funding. Repo market haircuts widen 15\u201325% on GCC sovereign collateral as risk committees impose precautionary limits.",
      },
      {
        origin: "UAE Banking Sector",
        destination: "Saudi Banking Sector",
        delay: "12\u201336 hours",
        mechanism:
          "Cross-border funding lines between UAE and Saudi banks contract by approximately $8B as Saudi institutions pull precautionary liquidity buffers. Correspondent banking relationships enter review. The interbank market fragments along national borders for the first time since the 2009 Dubai World crisis.",
      },
      {
        origin: "Saudi Banking Sector",
        destination: "Real Estate Finance",
        delay: "36\u201372 hours",
        mechanism:
          "Credit tightening transmits to the real estate sector as banks freeze new mortgage commitments and developer financing drawdowns. Off-plan purchase financing pipelines in Dubai and Riyadh face 90-day extensions. Developer financing costs surge 180bps, pushing several mid-tier developers past debt service coverage ratios.",
      },
      {
        origin: "Real Estate Finance",
        destination: "GCC Sovereign Bonds",
        delay: "72\u2013120 hours",
        mechanism:
          "Sovereign credit default swap spreads widen 45bps as international investors reassess GCC banking sector contingent liabilities. Five-year sovereign bond yields rise 30\u201340bps across UAE, Saudi, and Bahrain issuances. Fiscal financing costs for planned infrastructure spending increase by approximately $350M annually.",
      },
      {
        origin: "GCC Sovereign Bonds",
        destination: "Payment Infrastructure",
        delay: "96\u2013168 hours",
        mechanism:
          "Fintech payment processors and digital banks face liquidity buffer breaches as settlement cycles extend from T+0 to T+2. Cross-border payment volumes through regional payment gateways drop 35%. Small and medium enterprise receivables financing grinds to a halt as factoring facilities withdraw.",
      },
    ],

    // ── Impact ──
    impactFraming:
      "Exposure concentrates in the banking and real estate sectors, with secondary pressure on sovereign fiscal positioning and fintech infrastructure. Entities below are ranked by severity of institutional stress over the 14-day horizon.",
    exposureRegister: [
      {
        entity: "UAE Systemically Important Banks",
        sector: "Banking",
        exposure: "$680M in funding gap as deposit outflows reach 3.2% and interbank access freezes for 48+ hours, with CET1 ratios approaching the 12% regulatory floor",
        severity: "Critical",
      },
      {
        entity: "Saudi Commercial Banks",
        sector: "Banking",
        exposure: "$520M in cross-border exposure contraction as correspondent lines tighten and precautionary liquidity buffers are pulled from UAE counterparties",
        severity: "Elevated",
      },
      {
        entity: "UAE/Saudi Real Estate Developers",
        sector: "Real Estate",
        exposure: "$480M in financing pipeline disruption as mortgage commitments freeze and developer debt service coverage ratios breach covenant thresholds",
        severity: "Moderate",
      },
      {
        entity: "GCC Sovereign Issuers",
        sector: "Government",
        exposure: "$350M in increased fiscal financing costs as CDS spreads widen 45bps and five-year sovereign yields rise 30\u201340bps across three issuances",
        severity: "Moderate",
      },
      {
        entity: "Regional Insurance Carriers",
        sector: "Insurance",
        exposure: "$220M in credit default swap exposure on banking counterparties, with investment portfolio mark-to-market losses on sovereign bond holdings",
        severity: "Moderate",
      },
      {
        entity: "Fintech Payment Processors",
        sector: "Fintech",
        exposure: "$180M in settlement disruption as cross-border payment volumes drop 35% and liquidity buffers breach minimum regulatory thresholds",
        severity: "Moderate",
      },
      {
        entity: "GCC Trade Finance",
        sector: "Trade",
        exposure: "$130M in letter-of-credit delays as issuing banks impose temporary drawdown restrictions on uncommitted trade finance facilities",
        severity: "Low",
      },
    ],

    // ── Decision ──
    decisionFraming:
      "Three interventions are required, with the first two critical within 12 hours. The liquidity injection and regulatory forbearance must occur simultaneously \u2014 one without the other is insufficient to arrest the contagion sequence.",
    actions: [
      {
        action: "Activate emergency liquidity facility through coordinated SAMA and CBUAE injection of $8\u201312B into the interbank market, targeting overnight rate stabilization below the 200bps spread threshold.",
        owner: "SAMA + CBUAE",
        deadline: "4 hours",
        sector: "Banking",
      },
      {
        action: "Suspend mark-to-market requirements for banking book positions for a 72-hour window, preventing forced asset sales from converting liquidity stress into realized losses on sovereign bond portfolios.",
        owner: "Banking Regulators (SAMA, CBUAE, CBB)",
        deadline: "8 hours",
        sector: "Banking",
      },
      {
        action: "Extend developer financing payment deadlines by 90 days across all regulated real estate lending, preventing covenant breaches from triggering a wave of project completion defaults.",
        owner: "Real Estate Regulatory Agency",
        deadline: "48 hours",
        sector: "Real Estate",
      },
    ],

    // ── Outcome ──
    outcomeNarrative:
      "If all three interventions execute within their deadlines, total financial exposure reduces from $2.7B to approximately $1.1B \u2014 preserving $1.5B in economic value. The coordinated liquidity injection arrests the interbank freeze within 24\u201336 hours and prevents the credit channel from transmitting to the real estate sector. Regulatory forbearance on mark-to-market avoids forced selling of sovereign bonds, which would otherwise widen spreads by an additional 25\u201335bps. The 90-day payment extension contains developer defaults to under 2% of the pipeline, versus an estimated 8\u201312% without intervention. Full normalization of interbank conditions requires 60 days, with cross-border correspondent relationships taking 90\u2013120 days to fully restore.",
    monitoringCriteria: [
      "Interbank overnight rate returns below 150bps spread within 48 hours of SAMA/CBUAE injection \u2014 persistent elevation above 200bps indicates the injection volume was insufficient and a second tranche is required",
      "Deposit outflow velocity decelerates to under 0.5%/day within 72 hours \u2014 sustained outflows above 1%/day indicate loss of depositor confidence that requires public communication intervention",
      "No G-SIB\u2019s CET1 ratio falls below 12% during the 14-day window \u2014 a breach at any single institution triggers mandatory recapitalization discussion with sovereign wealth fund backstop",
    ],
  },

  // ═══════════════════════════════════════════════════════════════════
  // SAUDI OIL PRODUCTION SHOCK
  // ═══════════════════════════════════════════════════════════════════
  saudi_oil_shock: {
    slug: "saudi_oil_shock",

    // ── Context ──
    severity: 0.75,
    domain: "Energy",
    horizon: "10 days",
    sectors: 5,
    title: "Saudi Oil Production Shock",
    summary:
      "A major disruption to Saudi Aramco\u2019s eastern province production infrastructure reduces output by 5.7M barrels per day \u2014 approximately 50% of the Kingdom\u2019s total production capacity. The disruption affects the Abqaiq processing facility and the Khurais oil field, which together represent the largest concentration of global hydrocarbon processing capacity. Within hours, crude oil futures enter limit-up trading. The Kingdom\u2019s strategic petroleum reserves at Ras Tanura and Ju\u2019aymah are activated but cover only 25\u201330 days at reduced output levels.",
    significance:
      "Saudi Arabia supplies approximately 12% of global crude oil. A 50% production cut is the most severe supply disruption scenario in the GCC risk register, exceeding the 2019 Abqaiq attack in both scale and duration. For GCC decision-makers, the scenario presents simultaneous fiscal, monetary, and geopolitical pressure: Saudi fiscal revenue contracts by $600M+ per day, while commodity price spikes create inflationary pressure across all six GCC economies. The UAE and Kuwait face secondary exposure through OPEC+ coordination obligations and shared infrastructure dependencies.",

    // ── Transmission ──
    transmissionFraming:
      "The shock transmits through two parallel channels \u2014 physical supply disruption and financial market repricing \u2014 which converge on the fiscal and sovereign credit channels within 72\u201396 hours.",
    transmissionChain: [
      {
        origin: "Abqaiq / Khurais",
        destination: "Saudi Aramco",
        delay: "Immediate",
        mechanism:
          "Processing capacity at Abqaiq falls from 7M to 2M barrels/day. Khurais field output drops to zero. Combined production loss of 5.7M bbl/day triggers force majeure on all term contracts with Asian and European refinery customers. Strategic reserve activation begins but covers only partial shortfall.",
      },
      {
        origin: "Saudi Aramco",
        destination: "Global Crude Markets",
        delay: "0\u20136 hours",
        mechanism:
          "Brent crude surges $30\u201345/barrel in the first trading session. Futures curve enters extreme backwardation. NYMEX and ICE invoke volatility circuit breakers. Asian spot premiums for Arab Light widen to $8\u201312/barrel over benchmark, the widest since the 2022 Russian embargo.",
      },
      {
        origin: "Global Crude Markets",
        destination: "GCC Fiscal Revenue",
        delay: "24\u201372 hours",
        mechanism:
          "Paradox: crude prices rise but Saudi revenue collapses because volume loss exceeds price gain at this severity level. Saudi fiscal revenue drops $600M+/day. UAE and Kuwait benefit from higher prices on their unaffected production but face OPEC+ coordination pressure to increase output as spare capacity buffer.",
      },
      {
        origin: "GCC Fiscal Revenue",
        destination: "Sovereign Credit Markets",
        delay: "48\u201396 hours",
        mechanism:
          "Saudi sovereign CDS spreads widen 60\u201380bps. International investors reassess Kingdom\u2019s fiscal breakeven oil price. Sovereign bond yields rise 40\u201355bps on five-year issuances. Rating agency review initiated with negative watch placement.",
      },
      {
        origin: "Sovereign Credit Markets",
        destination: "GCC Banking Sector",
        delay: "72\u2013120 hours",
        mechanism:
          "Saudi banks face mark-to-market losses on sovereign bond portfolios. Interbank lending tightens as banks reassess counterparty exposure to government-related entities. Foreign bank branches in DIFC and ADGM reduce GCC exposure limits.",
      },
    ],

    // ── Impact ──
    impactFraming:
      "Exposure is dominated by the energy sector but transmits rapidly to sovereign fiscal and banking channels. The 10-day horizon captures the initial shock and first-order financial transmission, but recovery extends to 90+ days.",
    exposureRegister: [
      {
        entity: "Saudi Aramco",
        sector: "Energy",
        exposure: "$3.2B in direct revenue loss from 5.7M bbl/day production cut, plus $900M in infrastructure repair and force majeure contract penalties",
        severity: "Critical",
      },
      {
        entity: "Saudi Fiscal Authority",
        sector: "Government",
        exposure: "$1.8B in fiscal revenue shortfall over 10 days, with sovereign wealth fund drawdown of $2.4B to maintain spending commitments",
        severity: "Critical",
      },
      {
        entity: "GCC Banking Sector",
        sector: "Banking",
        exposure: "$720M in sovereign bond portfolio mark-to-market losses and interbank liquidity tightening as counterparty risk reprices",
        severity: "Elevated",
      },
      {
        entity: "Regional Insurance Market",
        sector: "Insurance",
        exposure: "$580M in property damage and business interruption claims from Abqaiq/Khurais facilities, testing catastrophe reserve adequacy",
        severity: "Elevated",
      },
      {
        entity: "GCC Trade Partners",
        sector: "Trade",
        exposure: "$430M in supply chain disruption for petrochemical downstream industries across UAE, Bahrain, and Oman",
        severity: "Moderate",
      },
    ],

    // ── Decision ──
    decisionFraming:
      "Five coordinated actions across energy, fiscal, and financial sectors. The first two are immediate \u2014 SPR activation and OPEC+ coordination must begin within hours. Fiscal and banking measures follow within 48 hours.",
    actions: [
      {
        action: "Activate Saudi strategic petroleum reserves and redirect Yanbu pipeline capacity to maximum throughput, targeting 2.8M bbl/day of substitute supply within 72 hours.",
        owner: "Ministry of Energy",
        deadline: "4 hours",
        sector: "Energy",
      },
      {
        action: "Initiate emergency OPEC+ coordination to authorize temporary production increases from UAE (0.8M bbl/day) and Kuwait (0.5M bbl/day) spare capacity.",
        owner: "OPEC+ Secretariat",
        deadline: "12 hours",
        sector: "Energy",
      },
      {
        action: "Deploy sovereign wealth fund liquidity buffer of $5\u20138B to maintain government spending commitments and prevent fiscal contraction from amplifying the economic shock.",
        owner: "Public Investment Fund",
        deadline: "48 hours",
        sector: "Government",
      },
      {
        action: "Coordinate SAMA intervention to stabilize interbank rates and provide emergency repo facilities against sovereign bond collateral at pre-disruption haircuts.",
        owner: "SAMA",
        deadline: "24 hours",
        sector: "Banking",
      },
      {
        action: "Activate regional catastrophe reinsurance treaties and coordinate with Lloyd\u2019s of London on claims processing capacity for Abqaiq/Khurais property damage.",
        owner: "Insurance Authority",
        deadline: "72 hours",
        sector: "Insurance",
      },
    ],

    // ── Outcome ──
    outcomeNarrative:
      "If all five interventions execute within their deadlines, total financial exposure reduces from $5.2B to approximately $2.1B \u2014 preserving $3.1B in economic value. Strategic reserves and OPEC+ coordination restore 70\u201380% of global supply shortfall within 5 days, collapsing the crude premium to under $15/barrel. Sovereign wealth fund deployment prevents fiscal contraction and maintains the Kingdom\u2019s credit rating at current levels. SAMA intervention contains interbank spread widening to under 100bps. Full production recovery at Abqaiq/Khurais requires 60\u201390 days based on 2019 precedent, with staged restoration beginning at Day 14.",
    monitoringCriteria: [
      "Abqaiq processing capacity recovers above 4M bbl/day within 14 days \u2014 if restoration falls behind this trajectory, the scenario extends beyond the modeled 10-day horizon and fiscal projections require revision",
      "Brent\u2013Arab Light spread narrows below $5/barrel within 7 days \u2014 persistent premium above $8 indicates Asian refinery customers are seeking permanent supply diversification",
      "Saudi sovereign CDS spread returns below 80bps within 21 days \u2014 sustained elevation above 100bps triggers rating agency downgrade review with systemic implications for GCC sovereign benchmarks",
    ],
  },

  // ═══════════════════════════════════════════════════════════════════
  // RED SEA TRADE CORRIDOR INSTABILITY
  // ═══════════════════════════════════════════════════════════════════
  red_sea_trade_corridor_instability: {
    slug: "red_sea_trade_corridor_instability",

    // ── Context ──
    severity: 0.60,
    domain: "Trade & Logistics",
    horizon: "21 days",
    sectors: 4,
    title: "Red Sea Trade Corridor Disruption",
    summary:
      "Sustained attacks on commercial shipping in the southern Red Sea and Bab el-Mandeb strait force major container lines to reroute around the Cape of Good Hope, adding 10\u201314 days to Asia\u2013Europe transit times. GCC ports on the western Arabian coast \u2014 Jeddah Islamic Port, King Abdullah Port, and Yanbu Commercial Port \u2014 experience 40\u201355% throughput decline as shipping lines bypass the corridor entirely. War-risk insurance premiums for Red Sea transit increase 10x, effectively pricing out non-essential cargo.",
    significance:
      "The Red Sea corridor handles approximately 12\u201315% of global trade by volume. For Saudi Arabia, western coast ports handle 60% of non-oil imports including food, construction materials, and consumer goods. A sustained disruption directly impacts the Kingdom\u2019s Vision 2030 megaproject supply chains \u2014 NEOM, The Red Sea Project, and AMAALA all depend on Jeddah and King Abdullah Port for material deliveries. The 21-day horizon is conservative; similar disruptions in 2024 persisted for 6+ months.",

    // ── Transmission ──
    transmissionFraming:
      "The disruption transmits through logistics cost inflation, supply chain elongation, and food security pressure. Unlike energy shocks, trade corridor disruptions compound over weeks rather than days.",
    transmissionChain: [
      {
        origin: "Bab el-Mandeb Strait",
        destination: "Jeddah Islamic Port",
        delay: "0\u201348 hours",
        mechanism:
          "Major container lines (Maersk, MSC, CMA CGM) announce Red Sea transit suspension. Jeddah port throughput drops 45% within 72 hours as vessels divert to Cape of Good Hope routing. Import container availability falls below 60% of baseline.",
      },
      {
        origin: "Jeddah Islamic Port",
        destination: "Saudi Import Supply Chains",
        delay: "3\u20137 days",
        mechanism:
          "Food import delivery schedules extend by 10\u201314 days. Construction material pipelines for Vision 2030 megaprojects face 3\u20134 week delays. Domestic inventory buffers for perishable goods drop below 15-day coverage in western province retail channels.",
      },
      {
        origin: "Saudi Import Supply Chains",
        destination: "Logistics Cost Structure",
        delay: "7\u201314 days",
        mechanism:
          "Container shipping rates on Asia\u2013GCC routes increase 200\u2013350%. War-risk insurance adds $50,000\u2013100,000 per transit for vessels that attempt Red Sea passage. Total landed cost for imported goods rises 8\u201315% across categories, with construction materials seeing the highest increase.",
      },
      {
        origin: "Logistics Cost Structure",
        destination: "Consumer Price Index",
        delay: "14\u201321 days",
        mechanism:
          "Import cost inflation transmits to consumer prices with a 2\u20133 week lag. Food price inflation accelerates 3\u20135 percentage points in western province cities. Central bank faces tension between inflation mandate and need to maintain accommodative monetary conditions during supply disruption.",
      },
    ],

    // ── Impact ──
    impactFraming:
      "Impact is distributed across trade, logistics, food security, and construction sectors. Unlike energy shocks, losses accumulate gradually over the 21-day horizon rather than concentrating in the first 72 hours.",
    exposureRegister: [
      {
        entity: "Saudi Western Coast Ports",
        sector: "Trade",
        exposure: "$580M in throughput revenue loss and container handling disruption as major shipping lines bypass the Red Sea corridor entirely",
        severity: "Elevated",
      },
      {
        entity: "Vision 2030 Megaprojects",
        sector: "Construction",
        exposure: "$420M in construction delay costs as material delivery schedules extend 3\u20134 weeks for NEOM, Red Sea Project, and AMAALA",
        severity: "Elevated",
      },
      {
        entity: "GCC Food Import Network",
        sector: "Food Security",
        exposure: "$310M in food supply chain disruption with perishable goods inventory dropping below 15-day coverage in western province",
        severity: "Moderate",
      },
      {
        entity: "Regional Logistics Providers",
        sector: "Logistics",
        exposure: "$190M in operational cost increases from rerouting, extended transit times, and war-risk insurance premium escalation",
        severity: "Moderate",
      },
    ],

    // ── Decision ──
    decisionFraming:
      "Three interventions spanning maritime security, supply chain contingency, and strategic reserves. The food security action is time-critical \u2014 inventory depletion becomes irreversible after Day 10.",
    actions: [
      {
        action: "Activate strategic food reserves and redirect eastern coast port capacity (Dammam, Jubail) for priority food imports via alternative Indian Ocean routing.",
        owner: "Ministry of Commerce",
        deadline: "72 hours",
        sector: "Food Security",
      },
      {
        action: "Negotiate emergency container allocation agreements with Maersk and MSC for dedicated GCC-bound capacity on Cape of Good Hope routes at pre-disruption rates.",
        owner: "Saudi Ports Authority",
        deadline: "7 days",
        sector: "Trade",
      },
      {
        action: "Establish temporary construction material procurement corridors through Oman (Salalah/Sohar) and UAE (Khalifa Port) for Vision 2030 megaproject critical path items.",
        owner: "Royal Commission for NEOM",
        deadline: "14 days",
        sector: "Construction",
      },
    ],

    // ── Outcome ──
    outcomeNarrative:
      "If all three interventions execute within their deadlines, total financial exposure reduces from $1.5B to approximately $650M \u2014 preserving $850M in economic value. Strategic food reserve activation maintains 30-day coverage for essential goods in western province. Container reallocation agreements restore 70% of import capacity within 14 days via alternative routing. Construction material corridors through Oman and UAE limit megaproject delays to 2 weeks instead of 6\u20138 weeks. Full trade corridor restoration depends on the geopolitical resolution timeline, which is outside the model\u2019s scope.",
    monitoringCriteria: [
      "Western province food inventory remains above 20-day coverage throughout the 21-day window \u2014 drop below 15 days requires emergency airlift authorization",
      "Container availability at Jeddah recovers above 50% of baseline within 14 days through alternative routing \u2014 failure to reach this threshold indicates rerouting capacity is insufficient and eastern port overflow is required",
      "Vision 2030 critical path delays remain under 3 weeks \u2014 extensions beyond 4 weeks trigger contractual penalty clauses and require Royal Commission escalation",
    ],
  },

  // ═══════════════════════════════════════════════════════════════════
  // GCC CYBER INFRASTRUCTURE ATTACK
  // ═══════════════════════════════════════════════════════════════════
  gcc_cyber_attack: {
    slug: "gcc_cyber_attack",

    // ── Context ──
    severity: 0.70,
    domain: "Financial Infrastructure",
    horizon: "5 days",
    sectors: 5,
    title: "GCC Cyber Infrastructure Attack",
    summary:
      "A coordinated cyberattack targets regional financial infrastructure \u2014 payment processing networks, SWIFT gateway nodes, and central bank real-time gross settlement (RTGS) systems across three GCC countries simultaneously. The attack vector combines ransomware deployment on bank core systems with distributed denial-of-service attacks on public-facing payment gateways. Within 6 hours, domestic payment processing in UAE and Saudi Arabia degrades to 30% of normal throughput. Cross-border settlement between GCC central banks halts completely.",
    significance:
      "GCC financial infrastructure processes approximately $4.8B in daily payment flows. A 5-day disruption at this severity level exposes structural dependencies that no individual central bank can resolve unilaterally. The attack surface is particularly concerning because GCC payment modernization initiatives (Saudi Arabia\u2019s Sarie, UAE\u2019s UAEPGS) have increased digital throughput while creating single points of failure. For decision-makers, this scenario tests the regional financial system\u2019s crisis coordination capacity \u2014 specifically whether SAMA, CBUAE, and CBB can execute a synchronized response within the 12-hour window before settlement failures trigger cascading bank-level liquidity stress.",

    // ── Transmission ──
    transmissionFraming:
      "The disruption transmits through payment infrastructure paralysis, settlement failure cascades, and confidence-driven deposit behavior. The 5-day horizon is compressed \u2014 each channel activates within hours, not days.",
    transmissionChain: [
      {
        origin: "RTGS Systems",
        destination: "Domestic Payment Networks",
        delay: "0\u20136 hours",
        mechanism:
          "Central bank settlement systems enter degraded mode. Domestic payment processing throughput drops to 30%. High-value interbank transfers queue indefinitely. ATM networks begin experiencing intermittent failures as back-end authorization systems timeout.",
      },
      {
        origin: "Domestic Payment Networks",
        destination: "SWIFT Gateway Nodes",
        delay: "6\u201312 hours",
        mechanism:
          "Cross-border payment messaging halts as SWIFT gateway nodes are isolated for containment. International correspondent banks place GCC payment instructions on manual review. Trade finance settlement \u2014 including energy commodity payments \u2014 faces 24\u201348 hour delays.",
      },
      {
        origin: "SWIFT Gateway Nodes",
        destination: "Commercial Banking Operations",
        delay: "12\u201336 hours",
        mechanism:
          "Banks switch to business continuity processing modes with severely reduced capacity. Corporate treasury operations face cash management paralysis. Payroll processing for the current cycle is at risk for employers with cross-bank payment dependencies.",
      },
      {
        origin: "Commercial Banking Operations",
        destination: "Public Confidence",
        delay: "24\u201348 hours",
        mechanism:
          "ATM failures and digital banking outages become publicly visible. Social media amplification drives precautionary cash withdrawal behavior. Retail deposit queues form at major branches. Central banks face pressure to issue public statements on deposit safety.",
      },
    ],

    // ── Impact ──
    impactFraming:
      "Impact is concentrated in financial infrastructure and banking operations, with rapid transmission to the real economy through payment disruption. The 5-day window is short but the intensity is extreme.",
    exposureRegister: [
      {
        entity: "GCC Payment Infrastructure",
        sector: "Financial Infrastructure",
        exposure: "$1.2B in payment flow disruption as daily processing capacity drops to 30% across domestic and cross-border channels",
        severity: "Critical",
      },
      {
        entity: "Commercial Banks (UAE/Saudi)",
        sector: "Banking",
        exposure: "$890M in operational losses from business continuity processing, settlement failures, and precautionary deposit withdrawals",
        severity: "Critical",
      },
      {
        entity: "Corporate Treasury Operations",
        sector: "Corporate",
        exposure: "$420M in working capital disruption as cash management, payroll, and supplier payment systems operate at degraded capacity",
        severity: "Elevated",
      },
      {
        entity: "Digital Banking Platforms",
        sector: "Fintech",
        exposure: "$280M in transaction processing losses and customer acquisition damage as digital-only banks face extended service outages",
        severity: "Elevated",
      },
      {
        entity: "Energy Commodity Settlement",
        sector: "Energy",
        exposure: "$180M in delayed settlement on crude oil and LNG term contract payments, triggering counterparty disputes",
        severity: "Moderate",
      },
    ],

    // ── Decision ──
    decisionFraming:
      "Four interventions must execute within the first 24 hours. The payment system restoration and public communication actions are interdependent \u2014 restoring infrastructure without public assurance risks continued deposit flight behavior.",
    actions: [
      {
        action: "Activate GCC Financial Sector Emergency Protocol and deploy joint SAMA/CBUAE/CBB cyber incident response team to isolate compromised systems and begin forensic recovery of RTGS platforms.",
        owner: "GCC Central Bank Coordination Committee",
        deadline: "2 hours",
        sector: "Financial Infrastructure",
      },
      {
        action: "Switch domestic payment processing to backup settlement infrastructure and authorize offline clearing of high-value transactions through manual verification protocols.",
        owner: "SAMA + CBUAE",
        deadline: "6 hours",
        sector: "Banking",
      },
      {
        action: "Issue coordinated public statement from all three central banks confirming deposit safety, insurance coverage, and estimated timeline for payment system restoration.",
        owner: "Central Bank Governors",
        deadline: "12 hours",
        sector: "Public Confidence",
      },
      {
        action: "Establish emergency SWIFT bypass channel through bilateral central bank settlement for critical energy commodity and trade finance payments exceeding $10M.",
        owner: "SAMA + CBUAE + SWIFT",
        deadline: "24 hours",
        sector: "Trade",
      },
    ],

    // ── Outcome ──
    outcomeNarrative:
      "If all four interventions execute within their deadlines, total financial exposure reduces from $2.8B to approximately $950M \u2014 preserving $1.9B in economic value. Backup settlement infrastructure restores 70% of domestic payment capacity within 48 hours. Coordinated public communication arrests deposit flight behavior before it reaches systemic levels. Emergency SWIFT bypass maintains critical commodity settlement flows. Full RTGS restoration requires 5\u20137 days with staged recovery, beginning with high-value interbank settlement and extending to retail payment channels by Day 5.",
    monitoringCriteria: [
      "Domestic payment processing recovers above 60% of normal throughput within 48 hours of backup activation \u2014 if below 40% at the 48-hour mark, manual clearing backlogs will overwhelm bank operations branches",
      "Retail deposit withdrawal rate decelerates below 0.3%/day within 24 hours of public statement \u2014 sustained withdrawals above 0.5%/day indicate the communication was insufficient and governor-level media appearances are required",
      "Cross-border SWIFT settlement resumes on primary channels within 5 days \u2014 extended outage beyond 7 days risks permanent correspondent banking relationship damage with European and Asian counterparties",
    ],
  },

  // ═══════════════════════════════════════════════════════════════════
  // IRAN REGIONAL ESCALATION
  // ═══════════════════════════════════════════════════════════════════
  iran_regional_escalation: {
    slug: "iran_regional_escalation",

    // ── Context ──
    severity: 0.78,
    domain: "Geopolitical",
    horizon: "14 days",
    sectors: 7,
    title: "Iran Regional Escalation",
    summary:
      "A significant escalation in regional tensions involving Iran triggers a multi-domain crisis across the GCC. The scenario begins with a military confrontation in the Persian Gulf that damages commercial maritime infrastructure and temporarily closes Hormuz to commercial traffic for 72 hours. Concurrent cyber operations target GCC financial and energy infrastructure. Commodity markets enter panic pricing as geopolitical risk premiums reprice across all GCC-linked asset classes. Capital flight from regional equity and bond markets reaches $12\u201315B within the first week.",
    significance:
      "This is the highest-severity scenario in the observatory\u2019s register. It combines elements of energy disruption, financial infrastructure attack, and sovereign credit repricing into a single correlated shock. No individual scenario model captures the full exposure \u2014 this scenario represents the convergence case. For GCC decision-makers, the critical question is whether the region\u2019s crisis response mechanisms can operate simultaneously across energy, financial, military, and diplomatic channels. Historical precedent (2019 Abqaiq, 2024 Red Sea) suggests these channels have never been tested concurrently at this severity level.",

    // ── Transmission ──
    transmissionFraming:
      "The escalation transmits through five parallel channels simultaneously, creating compounding pressure that exceeds the sum of individual channel stresses. The 14-day horizon captures the initial shock and second-order contagion effects.",
    transmissionChain: [
      {
        origin: "Persian Gulf Military Zone",
        destination: "Hormuz Commercial Traffic",
        delay: "Immediate",
        mechanism:
          "Commercial maritime traffic halts for 72 hours as naval operations create exclusion zones. 80\u2013120 laden tankers and 40\u201360 container vessels queue at the strait approaches. Energy transit drops to zero for the closure period, then recovers to 30\u201340% as vessels navigate under escort protocols.",
      },
      {
        origin: "Hormuz Commercial Traffic",
        destination: "Global Energy Markets",
        delay: "0\u20134 hours",
        mechanism:
          "Brent crude surges $40\u201360/barrel in the first trading session \u2014 the largest single-day move since the 1990 Kuwait invasion. LNG spot prices in Asia triple. Energy-importing economies in South and East Asia face immediate fiscal pressure. OPEC+ emergency session convened within 24 hours.",
      },
      {
        origin: "Global Energy Markets",
        destination: "GCC Sovereign Credit",
        delay: "24\u201372 hours",
        mechanism:
          "Saudi and UAE sovereign CDS spreads widen 100\u2013150bps as international investors price in geopolitical tail risk. Five-year bond yields surge 70\u201390bps. Sovereign wealth funds face margin calls on derivative positions and leveraged international portfolio holdings.",
      },
      {
        origin: "GCC Sovereign Credit",
        destination: "Regional Equity Markets",
        delay: "48\u201396 hours",
        mechanism:
          "Tadawul and ADX indices fall 15\u201325% over 5 trading sessions. Circuit breakers activate multiple times. Foreign institutional investors execute $8\u201312B in net outflows. Market-making capacity evaporates as broker-dealers reduce inventory limits.",
      },
      {
        origin: "Regional Equity Markets",
        destination: "Banking & Insurance Sectors",
        delay: "72\u2013168 hours",
        mechanism:
          "Banks face simultaneous pressure on three fronts: sovereign bond portfolio losses, equity market collateral haircuts, and retail deposit flight. Insurance carriers face war-risk and political violence claims that exceed single-event treaty limits. Reinsurance capacity for the Gulf region enters review.",
      },
    ],

    // ── Impact ──
    impactFraming:
      "This is the broadest impact scenario in the registry, touching all seven sectors. Exposure estimates carry wider confidence intervals than single-channel scenarios due to compounding interaction effects.",
    exposureRegister: [
      {
        entity: "GCC Energy Export Complex",
        sector: "Energy",
        exposure: "$2.8B in direct revenue loss from 72-hour Hormuz closure plus reduced throughput at 30\u201340% capacity for the remaining 11 days",
        severity: "Critical",
      },
      {
        entity: "Regional Equity Markets",
        sector: "Capital Markets",
        exposure: "$2.1B in market capitalization destruction as Tadawul/ADX indices fall 15\u201325% with $8\u201312B in foreign institutional outflows",
        severity: "Critical",
      },
      {
        entity: "GCC Sovereign Credit",
        sector: "Government",
        exposure: "$1.4B in fiscal impact from sovereign spread widening, bond portfolio losses, and emergency response expenditure",
        severity: "Critical",
      },
      {
        entity: "GCC Banking Sector",
        sector: "Banking",
        exposure: "$1.1B in combined exposure from sovereign bond losses, equity collateral haircuts, and interbank liquidity stress",
        severity: "Elevated",
      },
      {
        entity: "Regional Insurance Market",
        sector: "Insurance",
        exposure: "$680M in war-risk and political violence claims that exceed single-event treaty limits across marine, property, and liability lines",
        severity: "Elevated",
      },
      {
        entity: "GCC Trade Infrastructure",
        sector: "Trade",
        exposure: "$520M in trade flow disruption from combined Hormuz closure and Red Sea risk repricing on commercial shipping",
        severity: "Elevated",
      },
      {
        entity: "Real Estate & Construction",
        sector: "Real Estate",
        exposure: "$380M in project financing disruption as investor confidence in regional stability drives construction lending freeze",
        severity: "Moderate",
      },
    ],

    // ── Decision ──
    decisionFraming:
      "Six coordinated actions spanning energy, financial, diplomatic, and military channels. The first three must execute within 24 hours. This is the only scenario where all GCC heads of state require simultaneous briefing.",
    actions: [
      {
        action: "Activate joint GCC strategic petroleum reserves and coordinate emergency OPEC+ supply response, targeting 4M bbl/day of supplementary global supply within 72 hours.",
        owner: "GCC Energy Ministers Council",
        deadline: "6 hours",
        sector: "Energy",
      },
      {
        action: "Implement coordinated circuit breaker protocols across Tadawul, ADX, DFM, and Boursa Kuwait with synchronized trading halt triggers at 10% and 15% daily decline thresholds.",
        owner: "Capital Market Authorities",
        deadline: "4 hours",
        sector: "Capital Markets",
      },
      {
        action: "Deploy $15\u201320B in joint central bank liquidity injection through emergency repo facilities, swap lines, and standing lending facilities at pre-crisis rates.",
        owner: "GCC Central Bank Governors",
        deadline: "12 hours",
        sector: "Banking",
      },
      {
        action: "Activate GCC mutual defense coordination and establish commercial maritime escort protocols for energy cargoes transiting Hormuz under international naval cooperation framework.",
        owner: "GCC Joint Defense Council",
        deadline: "24 hours",
        sector: "Maritime Security",
      },
      {
        action: "Issue joint GCC sovereign statement on regional stability, coordinated with diplomatic engagement through UN Security Council and Gulf Cooperation Council frameworks.",
        owner: "GCC Secretary General",
        deadline: "12 hours",
        sector: "Diplomatic",
      },
      {
        action: "Activate catastrophe reinsurance treaties across all GCC insurance markets and coordinate with Lloyd\u2019s on war-risk capacity allocation for Gulf maritime and property risks.",
        owner: "GCC Insurance Federation",
        deadline: "48 hours",
        sector: "Insurance",
      },
    ],

    // ── Outcome ──
    outcomeNarrative:
      "If all six interventions execute within their deadlines, total financial exposure reduces from $7.0B to approximately $2.8B \u2014 preserving $4.2B in economic value. Strategic reserve activation and OPEC+ coordination collapse the crude premium to under $20/barrel within 7 days. Coordinated circuit breakers and liquidity injection arrest the equity market selloff at \u221215% rather than \u221225%. Maritime escort protocols restore Hormuz throughput to 60\u201370% within 5 days. Joint sovereign statement stabilizes CDS spreads within 100bps of pre-crisis levels by Day 10. Full normalization requires 90\u2013120 days and depends on geopolitical resolution, which is outside the model\u2019s scope.",
    monitoringCriteria: [
      "Hormuz commercial traffic recovers above 50% of baseline within 7 days under escort protocols \u2014 failure indicates military escalation has exceeded the scenario\u2019s containment assumptions",
      "GCC equity market foreign outflows decelerate below $500M/day by Day 7 \u2014 sustained outflows above $1B/day indicate permanent capital reallocation away from the region",
      "No GCC sovereign rating downgrade within the 14-day window \u2014 a downgrade triggers index exclusion reviews that would cause an additional $3\u20135B in forced institutional selling",
      "Central bank FX reserves remain above 80% of pre-crisis levels throughout \u2014 drawdown below 75% triggers peg defense discussions that could fundamentally alter the GCC monetary framework",
    ],
  },
};

// ── Helpers ──────────────────────────────────────────────────────────

export function getScenario(slug: string): ScenarioBriefing | undefined {
  return scenarios[slug];
}

export function getAllSlugs(): string[] {
  return Object.keys(scenarios);
}

export function severityWord(s: number): string {
  if (s >= 0.7) return "High";
  if (s >= 0.5) return "Elevated";
  return "Moderate";
}

export function severityVariant(s: number): "red" | "amber" | "olive" {
  if (s >= 0.7) return "red";
  if (s >= 0.5) return "amber";
  return "olive";
}
