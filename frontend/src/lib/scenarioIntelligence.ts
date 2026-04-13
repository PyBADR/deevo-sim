/**
 * Impact Observatory | مرصد الأثر — Scenario Intelligence Manifest
 *
 * Enterprise-grade intelligence layers for all 15 GCC scenarios.
 * Each scenario carries four intelligence structures:
 *
 *   1. Narratives   — US Financial, EU Regulatory, Asia Industrial perspectives
 *   2. Signals      — Structured intelligence inputs (economic, geopolitical, market)
 *   3. Propagation  — Causal chain from trigger to systemic outcome
 *   4. Reasoning    — WHY / HOW / WHAT decision logic tied to signals
 *
 * Static for SSG. In production, enriched from backend intelligence pipeline.
 */

/* ── Types ── */

export interface RegionalNarrative {
  region: 'US Financial' | 'EU Regulatory' | 'Asia Industrial';
  perspective: string;
}

export type SignalType = 'Economic' | 'Geopolitical' | 'Market' | 'Operational' | 'Regulatory';

export interface IntelligenceSignal {
  signal: string;
  type: SignalType;
  source: string;
  impact: string;
}

export interface PropagationStep {
  node: string;
  effect: string;
  direction: '↑' | '↓' | '→' | '⚠';
}

export interface DecisionReasoning {
  why: string;
  how: string;
  what: string;
  signalBasis: string[];
  propagationLink: string;
}

export interface ScenarioIntelligence {
  scenarioId: string;
  narratives: RegionalNarrative[];
  signals: IntelligenceSignal[];
  propagation: PropagationStep[];
  reasoning: DecisionReasoning;
}

/* ── Manifest ── */

const manifest: ScenarioIntelligence[] = [
  {
    scenarioId: 'hormuz_chokepoint_disruption',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Hormuz disruption triggers immediate repricing of energy futures on NYMEX. Treasury markets face safe-haven inflows as institutional investors rotate out of GCC sovereign bonds. The Fed monitors second-order inflation pass-through from elevated crude prices, with oil-weighted CPI components forecasted to spike 180bps within two weeks.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'ESMA activates enhanced surveillance on energy derivative markets. ECB stress-tests cross-exposure of European banks to GCC counterparties reliant on Hormuz transit. EIOPA issues advisory on reinsurance reserve adequacy for marine cargo policies transiting the Persian Gulf corridor.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Japanese refiners invoke strategic reserve drawdown protocols. South Korean petrochemical producers face immediate feedstock shortfall as naphtha shipments are rerouted via the Cape of Good Hope, adding 12–15 days to supply chains. Chinese state-owned importers accelerate overland pipeline procurement from Central Asia.',
      },
    ],
    signals: [
      { signal: 'Brent crude futures breach $130/bbl', type: 'Market', source: 'ICE Futures Europe', impact: 'Cascading repricing of energy-linked sovereign revenues across GCC states' },
      { signal: 'US 5th Fleet repositioning to Arabian Sea', type: 'Geopolitical', source: 'OSINT / AIS vessel tracking', impact: 'Signals military escalation risk; insurance premiums for Gulf transit spike 400%' },
      { signal: 'VLCC day-rates surge to $85,000', type: 'Economic', source: 'Baltic Exchange', impact: 'Shipping cost pass-through to downstream consumer goods within 30 days' },
      { signal: 'LNG spot prices in Asia exceed $25/MMBtu', type: 'Market', source: 'JKM benchmark', impact: 'Qatar export revenue windfall offset by contractual repricing disputes' },
      { signal: 'Marine cargo insurance War Risk premium triples', type: 'Operational', source: 'Lloyd\'s Joint War Committee', impact: 'Commercial vessels begin voluntary Hormuz avoidance within 48 hours' },
    ],
    propagation: [
      { node: 'Oil transit volume', effect: 'Daily throughput drops from 21M bbl/d to ~8M bbl/d', direction: '↓' },
      { node: 'Global crude price', effect: 'Brent spikes $35–50/bbl above baseline', direction: '↑' },
      { node: 'Shipping costs', effect: 'Rerouting via Cape of Good Hope adds $2.1M per VLCC voyage', direction: '↑' },
      { node: 'GCC export revenue', effect: 'Short-term windfall from price spike; medium-term volume collapse', direction: '⚠' },
      { node: 'Asian refinery throughput', effect: 'Japanese and Korean refiners cut runs 15–20%', direction: '↓' },
      { node: 'Global inflation', effect: 'Energy-weighted CPI rises 120–180bps in importing economies', direction: '↑' },
      { node: 'Banking sector liquidity', effect: 'Trade finance volumes contract; LC confirmation costs rise', direction: '↓' },
    ],
    reasoning: {
      why: 'The Hormuz chokepoint carries 21% of global oil and 25% of global LNG. Partial blockage creates a supply asymmetry that reprices the entire global energy complex within hours. GCC economies face the paradox of higher unit revenue against collapsed volume — net negative within 72 hours.',
      how: 'Strategic petroleum reserve release signals supply continuity to global markets, capping the speculative premium. Parallel activation of East-West pipeline capacity (IPSA/Habshan-Fujairah) provides physical bypass. Diplomatic channels target 48-hour de-escalation window before insurance markets fully reprice.',
      what: 'Release 2M bbl/d from strategic reserves immediately. Activate Habshan-Fujairah pipeline to full 1.5M bbl/d capacity. Coordinate with IEA member states on synchronised reserve drawdown. Issue sovereign guarantee on trade finance LCs to prevent banking liquidity freeze.',
      signalBasis: ['Brent crude futures breach $130/bbl', 'Marine cargo insurance War Risk premium triples', 'US 5th Fleet repositioning to Arabian Sea'],
      propagationLink: 'Oil transit volume ↓ → Global crude price ↑ → Banking sector liquidity ↓',
    },
  },
  {
    scenarioId: 'hormuz_full_closure',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Full Hormuz closure represents the most severe energy supply shock since 1973. US equity markets enter correction territory as energy stocks decouple from broad indices. Federal Reserve faces impossible trinity: rising inflation, demand destruction, and financial stability risk simultaneously.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'European Commission invokes emergency energy solidarity measures. ECB activates Transmission Protection Instrument to prevent sovereign spread widening in energy-dependent periphery states. EU Council convenes emergency session on strategic reserve coordination.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'China activates 90-day strategic petroleum reserve drawdown. Japanese industrial output contracts as power generation shifts to emergency coal and nuclear restart. Indian refinery complex faces total feedstock disruption on Gulf-sourced crude grades.',
      },
    ],
    signals: [
      { signal: 'Brent crude breaches $180/bbl intraday', type: 'Market', source: 'ICE Futures Europe', impact: 'Global recession risk repriced from 15% to 65% probability' },
      { signal: 'IRGC naval exercises in Strait confirmed', type: 'Geopolitical', source: 'US CENTCOM / satellite imagery', impact: 'Complete commercial shipping halt within 12 hours' },
      { signal: 'GCC sovereign CDS spreads widen 200bps', type: 'Economic', source: 'IHS Markit', impact: 'Cost of sovereign borrowing rises sharply; bond issuance window closes' },
      { signal: 'Asian LNG spot exceeds $45/MMBtu', type: 'Market', source: 'S&P Global Platts', impact: 'Power generation switching triggers industrial rationing in Japan/Korea' },
    ],
    propagation: [
      { node: 'Strait transit', effect: 'Complete closure — zero commercial vessel passage', direction: '↓' },
      { node: 'Global oil supply', effect: '17–21M bbl/d removed from seaborne market', direction: '↓' },
      { node: 'Energy prices', effect: 'Oil $180+, LNG $45+, coal parity repricing globally', direction: '↑' },
      { node: 'GCC fiscal position', effect: 'Revenue collapses despite price spike — no volume to sell', direction: '↓' },
      { node: 'Global GDP', effect: 'Estimated 2–3% contraction in energy-importing economies', direction: '↓' },
      { node: 'Financial markets', effect: 'Broad equity selloff; flight to USD and gold', direction: '↓' },
    ],
    reasoning: {
      why: 'Full closure eliminates the physical throughput capacity that partial disruption merely constrains. No pipeline bypass can replace 21M bbl/d. The scenario converts from a supply-cost shock to a supply-existence crisis, requiring wartime economic coordination.',
      how: 'Immediate IEA coordinated emergency release of 4M+ bbl/d from member strategic reserves. GCC states activate all non-Hormuz export infrastructure simultaneously. Central banks pre-announce unlimited swap lines to prevent dollar liquidity crisis in Gulf banking.',
      what: 'Execute maximum SPR release across all IEA member states. Deploy full East-West pipeline and Red Sea terminal capacity. Central bank swap lines activated with Fed, ECB, BOJ. Sovereign guarantee on all GCC trade finance for 90-day window.',
      signalBasis: ['Brent crude breaches $180/bbl intraday', 'IRGC naval exercises in Strait confirmed', 'GCC sovereign CDS spreads widen 200bps'],
      propagationLink: 'Strait transit ↓ → Global oil supply ↓ → GCC fiscal position ↓',
    },
  },
  {
    scenarioId: 'iran_regional_escalation',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Regional escalation triggers risk-off rotation across emerging market portfolios. GCC-weighted ETFs see 15–20% outflows as institutional allocators invoke geopolitical risk overlays. US defense sector equities rally on procurement acceleration expectations.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'EU activates crisis management protocols for financial market stability. Sanctions compliance framework expanded as new entities designated. ESMA monitors CCP margin calls on GCC sovereign bond positions held by European banks.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Chinese Belt and Road infrastructure investments in the Gulf face force majeure review. Indian pharmaceutical exports to GCC states face logistics disruption via Red Sea corridor. Southeast Asian sovereign wealth funds pause new GCC real estate allocations.',
      },
    ],
    signals: [
      { signal: 'Iranian missile capability deployment confirmed', type: 'Geopolitical', source: 'IISS / satellite intelligence', impact: 'Gulf state infrastructure enters direct threat envelope' },
      { signal: 'GCC defense spending approvals accelerate', type: 'Economic', source: 'Sovereign budget releases', impact: 'Fiscal reallocation from development to security within 30 days' },
      { signal: 'Insurance underwriters invoke force majeure reviews', type: 'Operational', source: 'Lloyd\'s market intelligence', impact: 'Project finance for Gulf infrastructure delayed 6–12 months' },
      { signal: 'Capital flight indicators in Gulf banking', type: 'Market', source: 'Central bank flow data', impact: 'Deposit base contraction pressures banking system liquidity' },
    ],
    propagation: [
      { node: 'Regional security', effect: 'Conventional threat level elevates to direct infrastructure risk', direction: '⚠' },
      { node: 'FDI flows', effect: 'Foreign direct investment pipeline freezes; project starts postponed', direction: '↓' },
      { node: 'Insurance markets', effect: 'Political risk insurance premiums repriced 300–500%', direction: '↑' },
      { node: 'Sovereign credit', effect: 'Rating agency negative watches initiated', direction: '↓' },
      { node: 'Domestic confidence', effect: 'Consumer and business sentiment indices decline sharply', direction: '↓' },
    ],
    reasoning: {
      why: 'Regional escalation converts latent geopolitical risk into priced-in threat premium across all GCC asset classes. Unlike energy disruption, escalation risk cannot be hedged through commodity positions — it reprices the entire investment thesis for Gulf economies.',
      how: 'Immediate diplomatic de-escalation combined with visible GCC collective security activation. Financial markets require sovereign communication clarity within 6 hours of threat materialisation. Central bank forward guidance must pre-empt capital flight.',
      what: 'Activate GCC Joint Defence Council. Issue coordinated sovereign statements within 6 hours. Central banks publish unlimited deposit guarantee framework. Suspend non-essential capital account outflows temporarily.',
      signalBasis: ['Iranian missile capability deployment confirmed', 'Capital flight indicators in Gulf banking'],
      propagationLink: 'Regional security ⚠ → FDI flows ↓ → Domestic confidence ↓',
    },
  },
  {
    scenarioId: 'critical_port_throughput_disruption',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'US importers face 2–3 week delays on Gulf-origin petrochemical feedstocks. Logistics-heavy S&P 500 components revise quarterly guidance downward. Container shipping equities rally as spot rates surge on capacity reallocation.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'EU supply chain due diligence directive stress-tested against Gulf port dependency. ECB monitors import price inflation transmission. European aluminium smelters face feedstock shortages as Jebel Ali throughput collapses.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Chinese manufacturers dependent on Gulf-origin polymers activate alternative sourcing from Southeast Asia at 20% premium. Japanese automotive supply chains face 3-week disruption on Gulf-shipped aluminium. Indian ports see transshipment volume surge as cargo diverts.',
      },
    ],
    signals: [
      { signal: 'Jebel Ali container throughput drops 60%', type: 'Operational', source: 'DP World operational data', impact: 'Regional hub function disrupted; transshipment cargo diverts to Oman/Bahrain' },
      { signal: 'Container spot rates Asia-Gulf triple', type: 'Market', source: 'Freightos Baltic Index', impact: 'Trade costs for Gulf imports spike; consumer price pass-through within 45 days' },
      { signal: 'Customs clearance backlog exceeds 14 days', type: 'Operational', source: 'UAE Federal Customs Authority', impact: 'Perishable cargo losses mount; pharmaceutical supply chain at risk' },
    ],
    propagation: [
      { node: 'Port throughput', effect: 'Multi-port capacity drops 40–60% across GCC', direction: '↓' },
      { node: 'Shipping rates', effect: 'Spot rates surge 200–300% on Gulf lanes', direction: '↑' },
      { node: 'Trade finance', effect: 'LC amendment volumes spike as delivery terms fail', direction: '⚠' },
      { node: 'Consumer prices', effect: 'Import-dependent goods inflate 8–15% within 60 days', direction: '↑' },
      { node: 'Re-export economy', effect: 'UAE re-export hub function severely impaired', direction: '↓' },
    ],
    reasoning: {
      why: 'GCC economies are structurally dependent on port throughput for both export revenue and import-dependent consumption. Port disruption simultaneously constrains outbound energy shipments and inbound consumer/industrial goods — a dual channel that no financial instrument can hedge.',
      how: 'Emergency port operations protocols activate secondary terminals. Fast-track customs clearance on essential goods. Coordinate with regional port operators (Oman, Bahrain) to absorb diverted volumes.',
      what: 'Invoke emergency port operations at Sohar, Khalifa, and Hamad ports. Deploy military logistics for critical supply chains. Issue temporary tariff waivers on diverted cargo. Activate sovereign food security reserves.',
      signalBasis: ['Jebel Ali container throughput drops 60%', 'Container spot rates Asia-Gulf triple'],
      propagationLink: 'Port throughput ↓ → Consumer prices ↑ → Re-export economy ↓',
    },
  },
  {
    scenarioId: 'saudi_oil_shock',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Aramco production shock reprices the entire OPEC+ supply discipline thesis. US shale producers face pressure to accelerate output despite capital discipline commitments. Energy sector M&A activity surges as majors seek diversified supply portfolios.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'EU energy security directorate escalates Gulf supply dependency review. European refinery margins compress as Saudi-grade crude becomes scarce and substitutes trade at premium. Carbon border adjustment calculations disrupted by volatile energy input costs.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Chinese state refiners lose access to preferred Saudi Arab Light grade, forcing emergency spot procurement at $15–20/bbl premium. Indian refining complex — the world\'s third largest — faces 30% feedstock shortfall on Saudi-origin crude.',
      },
    ],
    signals: [
      { signal: 'Aramco production drops 4M bbl/d below target', type: 'Economic', source: 'OPEC Monthly Oil Market Report', impact: 'Global spare capacity effectively zero; any additional disruption triggers crisis' },
      { signal: 'Saudi fiscal break-even price recalculated to $95/bbl', type: 'Economic', source: 'IMF Article IV consultation', impact: 'Vision 2030 capital expenditure timeline at risk of 18-month delay' },
      { signal: 'Asian term contract nominations decline 25%', type: 'Market', source: 'Aramco OSP notifications', impact: 'Long-term buyer relationships strained; contract renegotiation cycle begins' },
    ],
    propagation: [
      { node: 'Saudi production', effect: 'Output drops 4M bbl/d — largest single-source disruption since 2019', direction: '↓' },
      { node: 'OPEC+ compliance', effect: 'Cartel discipline collapses as members compete for price windfall', direction: '⚠' },
      { node: 'Global spare capacity', effect: 'Effective spare capacity falls below 1M bbl/d', direction: '↓' },
      { node: 'Saudi sovereign revenue', effect: 'Price spike offset by volume loss — net revenue negative at 72h', direction: '↓' },
      { node: 'Vision 2030 funding', effect: 'PIF capital deployment slowed; giga-project timelines slip', direction: '↓' },
    ],
    reasoning: {
      why: 'Saudi Arabia is the world\'s swing producer and sole holder of meaningful spare capacity. A production shock removes the global energy market\'s primary stabilisation mechanism, creating systemic fragility that compounds every other risk in the GCC.',
      how: 'Emergency OPEC+ coordination to redistribute quotas. Activate Saudi strategic reserves for domestic consumption. Accelerate Jafurah gas field development to displace oil-for-power use domestically.',
      what: 'Convene emergency OPEC+ ministerial within 24 hours. Deploy strategic reserves for domestic energy needs. Issue sovereign communication to Aramco long-term contract holders. Accelerate non-oil revenue programmes.',
      signalBasis: ['Aramco production drops 4M bbl/d below target', 'Saudi fiscal break-even price recalculated to $95/bbl'],
      propagationLink: 'Saudi production ↓ → Global spare capacity ↓ → Vision 2030 funding ↓',
    },
  },
  {
    scenarioId: 'uae_banking_crisis',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'UAE banking stress raises contagion concerns for global banks with Gulf exposure. Moody\'s places 6 UAE banks on negative watch. US money market funds with GCC sovereign paper reduce allocation, tightening dollar liquidity in Gulf interbank markets.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'ECB conducts targeted review of EU bank subsidiaries in UAE. European correspondent banking relationships face enhanced due diligence requirements. AML/CFT compliance frameworks stress-tested against potential UAE banking system instability.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Indian IT services companies with major UAE banking clients face payment delays. Chinese construction firms with Dubai projects encounter LC confirmation difficulties. Singaporean wealth management platforms report client anxiety over UAE-domiciled assets.',
      },
    ],
    signals: [
      { signal: 'UAE interbank rate EIBOR spikes 150bps', type: 'Market', source: 'UAE Central Bank', impact: 'Borrowing costs for SMEs and real estate sector become prohibitive' },
      { signal: 'Real estate developer defaults on $2B bond', type: 'Economic', source: 'Dubai Financial Market', impact: 'Property sector repricing triggers margin calls on construction finance' },
      { signal: 'Deposit outflows exceed AED 40B in 72 hours', type: 'Market', source: 'Banking system aggregate data', impact: 'Liquidity crunch forces central bank emergency window activation' },
      { signal: 'Rating downgrades on 3 major UAE banks', type: 'Regulatory', source: 'S&P / Moody\'s', impact: 'International counterparty limits reduced; trade finance capacity contracts' },
    ],
    propagation: [
      { node: 'Banking liquidity', effect: 'Interbank lending seizes; overnight rates spike', direction: '↓' },
      { node: 'Real estate sector', effect: 'Property valuations drop 15–25% on forced sales', direction: '↓' },
      { node: 'SME sector', effect: 'Working capital access collapses; business failures accelerate', direction: '↓' },
      { node: 'Trade finance', effect: 'LC confirmation costs rise 500%; import financing disrupted', direction: '↑' },
      { node: 'Sovereign guarantee', effect: 'Government forced to backstop banking system — fiscal cost $20–30B', direction: '⚠' },
    ],
    reasoning: {
      why: 'UAE banking is the financial plumbing of the entire GCC trade ecosystem. A banking crisis doesn\'t just affect UAE — it severs trade finance, correspondent banking, and payment clearing for the entire Gulf region.',
      how: 'UAE Central Bank activates emergency liquidity assistance. Government announces blanket deposit guarantee. Coordinated GCC central bank swap lines to prevent cross-border contagion.',
      what: 'Central bank provides unlimited overnight liquidity at penal rate. Sovereign guarantee on all deposits up to AED 5M. Temporary suspension of real estate margin calls. Announce recapitalisation facility for systemically important banks.',
      signalBasis: ['UAE interbank rate EIBOR spikes 150bps', 'Deposit outflows exceed AED 40B in 72 hours', 'Rating downgrades on 3 major UAE banks'],
      propagationLink: 'Banking liquidity ↓ → Trade finance ↑ → Sovereign guarantee ⚠',
    },
  },
  {
    scenarioId: 'qatar_lng_disruption',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'US LNG exporters see immediate arbitrage opportunity as Asian spot premiums surge. Cheniere Energy and other Gulf Coast terminals maximise cargo diversion to Asia. US natural gas equities rally 20–30% on repricing of long-term contract value.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'EU energy security framework stress-tested as Qatar supplies 15% of European LNG. Emergency coordination with Norway and Algeria for supplementary volumes. REPowerEU targets re-evaluated against reduced Qatari supply availability.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Japan and South Korea face immediate power generation shortfall. Industrial gas rationing protocols activated in both countries. Chinese LNG importers pivot to pipeline gas from Russia and Central Asia, accelerating strategic energy diversification.',
      },
    ],
    signals: [
      { signal: 'QatarEnergy force majeure declaration', type: 'Operational', source: 'QatarEnergy corporate communications', impact: 'Long-term contract deliveries suspended; buyers invoke destination flexibility clauses' },
      { signal: 'JKM LNG spot price exceeds $35/MMBtu', type: 'Market', source: 'S&P Global Platts', impact: 'Power generation costs in Asia spike; industrial demand destruction begins' },
      { signal: 'Ras Laffan facility throughput halted', type: 'Operational', source: 'Port authority / AIS data', impact: 'World\'s largest LNG export complex offline — 77 MTPA capacity removed' },
    ],
    propagation: [
      { node: 'LNG export capacity', effect: 'Qatar\'s 77 MTPA — 22% of global LNG — goes offline', direction: '↓' },
      { node: 'Asian gas prices', effect: 'JKM spot surges to $35–50/MMBtu', direction: '↑' },
      { node: 'European gas security', effect: 'Storage drawdown accelerates; winter adequacy at risk', direction: '↓' },
      { node: 'Qatar fiscal revenue', effect: 'LNG revenue stream collapses — $60B+ annual impact', direction: '↓' },
      { node: 'Global fertiliser production', effect: 'Natural gas feedstock shortage impacts food security chain', direction: '↓' },
    ],
    reasoning: {
      why: 'Qatar is the world\'s largest LNG exporter. Disruption removes 22% of global LNG supply from a market with no short-term substitution capacity. Unlike oil, LNG cannot be released from strategic reserves — the physical infrastructure IS the supply.',
      how: 'Emergency coordination with alternative LNG suppliers (US, Australia, Malaysia). Demand-side management in importing countries. Fast-track repair or bypass of affected infrastructure.',
      what: 'Activate mutual aid agreements with GCC states for domestic gas needs. Coordinate with IEA on emergency LNG allocation framework. Issue sovereign guarantee on existing long-term contract obligations. Deploy technical response for infrastructure recovery.',
      signalBasis: ['QatarEnergy force majeure declaration', 'Ras Laffan facility throughput halted'],
      propagationLink: 'LNG export capacity ↓ → Asian gas prices ↑ → Qatar fiscal revenue ↓',
    },
  },
  {
    scenarioId: 'regional_liquidity_stress_event',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Dollar liquidity squeeze in Gulf interbank markets reverberates through US correspondent banking networks. Fed monitors repo market stress as GCC central banks draw on USD reserves. Gulf sovereign wealth fund asset sales create selling pressure in US equity and treasury markets.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'ECB activates bilateral swap line with GCC central banks. European banks with Gulf subsidiary operations face consolidated capital adequacy pressure. Basel III liquidity coverage ratio compliance questioned for banks with concentrated GCC exposure.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Asian exporters to GCC face payment delays as trade finance dries up. Indian remittance flows from Gulf states — $40B+ annually — face settlement disruption. Chinese sovereign wealth fund pauses new Gulf-region allocations pending stability assessment.',
      },
    ],
    signals: [
      { signal: 'Cross-border interbank lending freezes', type: 'Market', source: 'GCC central bank aggregate data', impact: 'Dollar liquidity evaporates; overnight rates exceed 8%' },
      { signal: 'Sovereign wealth fund redemption queues forming', type: 'Economic', source: 'Fund administrator reports', impact: 'Forced asset sales in global markets create secondary contagion' },
      { signal: 'Trade finance LC rejections spike 400%', type: 'Operational', source: 'ICC Trade Register', impact: 'Physical goods trade between GCC states functionally halts' },
    ],
    propagation: [
      { node: 'Interbank liquidity', effect: 'Cross-border lending between GCC banks ceases', direction: '↓' },
      { node: 'Dollar availability', effect: 'USD/local currency spreads widen to crisis levels', direction: '↓' },
      { node: 'Trade finance', effect: 'Import/export LC confirmation collapses', direction: '↓' },
      { node: 'Sovereign reserves', effect: 'Central banks draw down FX reserves to defend liquidity', direction: '↓' },
      { node: 'Economic activity', effect: 'GDP contraction across GCC as financial plumbing fails', direction: '↓' },
    ],
    reasoning: {
      why: 'GCC banking systems are interconnected through trade finance, correspondent banking, and sovereign wealth fund cross-holdings. A liquidity shock in one jurisdiction propagates within hours through these channels — faster than regulators can respond individually.',
      how: 'Coordinated GCC central bank liquidity injection. Fed swap line activation. Temporary capital controls to prevent accelerating outflows. Sovereign guarantee on interbank positions.',
      what: 'GCC central bank governors convene emergency session. Activate Fed/ECB bilateral swap lines. Inject $50B+ combined liquidity into interbank markets. Announce temporary depositor guarantee across all GCC jurisdictions.',
      signalBasis: ['Cross-border interbank lending freezes', 'Trade finance LC rejections spike 400%'],
      propagationLink: 'Interbank liquidity ↓ → Trade finance ↓ → Economic activity ↓',
    },
  },
  {
    scenarioId: 'financial_infrastructure_cyber_disruption',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'SWIFT connectivity disruption to GCC entities triggers US correspondent banking isolation protocols. SEC monitors for anomalous trading patterns suggesting adversary foreknowledge. US CISA issues emergency directive to financial institutions with Gulf payment system exposure.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'ECB activates cyber crisis management framework. TARGET2 system monitors for secondary propagation from GCC-linked payment chains. EU Network and Information Security Directive stress-tested against cross-border financial cyber contagion scenarios.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Asian banks halt automated payment processing to GCC entities pending security verification. Commodity trading houses in Singapore face settlement failures on Gulf-origin energy trades. Indian IT outsourcing firms providing GCC bank infrastructure support mobilise incident response.',
      },
    ],
    signals: [
      { signal: 'Payment system latency exceeds 6 hours', type: 'Operational', source: 'GCC RTGS monitoring', impact: 'Real-time gross settlement failure; queued transactions approach $15B' },
      { signal: 'Multiple GCC bank core systems compromised', type: 'Operational', source: 'CERT-GCC advisory', impact: 'Transaction integrity questioned; manual verification required on all large transfers' },
      { signal: 'SWIFT message authentication failures detected', type: 'Regulatory', source: 'SWIFT ISAC alert', impact: 'International correspondent banking freezes GCC message processing' },
    ],
    propagation: [
      { node: 'Payment systems', effect: 'RTGS and ACH processing halt across GCC', direction: '↓' },
      { node: 'Transaction integrity', effect: 'All pending transactions require manual verification', direction: '⚠' },
      { node: 'International payments', effect: 'Cross-border wire transfers to/from GCC suspended', direction: '↓' },
      { node: 'Economic activity', effect: 'Commerce halts as payment rails become unavailable', direction: '↓' },
      { node: 'Confidence', effect: 'Depositor panic risk as account access disrupted', direction: '↓' },
    ],
    reasoning: {
      why: 'Financial infrastructure is the nervous system of the economy. A cyber attack that disrupts payment rails doesn\'t just delay transactions — it creates existential uncertainty about the integrity of every balance and record in the system.',
      how: 'Immediate network isolation to prevent lateral movement. Activate backup payment processing via central bank manual systems. International communication to maintain correspondent banking relationships during recovery.',
      what: 'Invoke national cyber emergency protocols. Central banks activate backup RTGS systems. Issue joint GCC statement confirming deposit safety and system integrity. Deploy international incident response teams.',
      signalBasis: ['Payment system latency exceeds 6 hours', 'SWIFT message authentication failures detected'],
      propagationLink: 'Payment systems ↓ → International payments ↓ → Confidence ↓',
    },
  },
  {
    scenarioId: 'red_sea_trade_corridor_instability',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Red Sea disruption forces rerouting via Cape of Good Hope, adding 10–14 days to Asia-Europe trade. US consumers face delayed delivery of goods transshipped through Suez. Container shipping equities surge as effective fleet capacity drops 15%.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'EU trade commissioner invokes emergency consultations on supply chain resilience. European automotive sector faces component shortages as just-in-time inventory buffers erode. ECB revises inflation forecast upward on transport cost pass-through.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Chinese export manufacturers face 2-week delay on European-bound shipments. Indian exporters lose competitive advantage as transit costs to European markets equalise with distant competitors. South Korean semiconductor shipments to European fabs delayed.',
      },
    ],
    signals: [
      { signal: 'Suez Canal transit volumes drop 45%', type: 'Operational', source: 'Suez Canal Authority', impact: 'Global trade artery operating below half capacity' },
      { signal: 'Container freight rates surge 250%', type: 'Market', source: 'Drewry World Container Index', impact: 'Trade costs spike for all goods transiting Red Sea corridor' },
      { signal: 'Naval advisory issued for Bab el-Mandeb strait', type: 'Geopolitical', source: 'UKMTO / MSCHOA', impact: 'Insurance premiums for Red Sea transit become commercially prohibitive' },
    ],
    propagation: [
      { node: 'Red Sea transit', effect: 'Commercial shipping diverts; Suez volumes collapse', direction: '↓' },
      { node: 'Shipping costs', effect: 'Global container and tanker rates surge 200–300%', direction: '↑' },
      { node: 'Trade volumes', effect: 'Effective trade capacity reduced by rerouting inefficiency', direction: '↓' },
      { node: 'GCC re-export function', effect: 'Oman and Saudi Red Sea ports lose feeder volume', direction: '↓' },
      { node: 'Consumer inflation', effect: 'Import price pass-through reaches consumers within 60 days', direction: '↑' },
    ],
    reasoning: {
      why: 'The Red Sea corridor carries 12% of global trade. Disruption doesn\'t just affect transit — it reconfigures the entire cost structure of global logistics, with GCC states caught in the middle as both transit points and trade-dependent economies.',
      how: 'Naval protection frameworks for commercial shipping. Alternative routing coordination with port operators. Diplomatic engagement to address root cause of instability.',
      what: 'Activate GCC naval escort programme for commercial vessels. Accelerate Oman rail-to-port corridor for overland bypass. Coordinate with Egyptian authorities on Suez security enhancement. Issue temporary freight subsidy for essential goods imports.',
      signalBasis: ['Suez Canal transit volumes drop 45%', 'Container freight rates surge 250%'],
      propagationLink: 'Red Sea transit ↓ → Shipping costs ↑ → Consumer inflation ↑',
    },
  },
  {
    scenarioId: 'gcc_cyber_attack',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'GCC infrastructure cyber attack echoes the 2012 Aramco Shamoon incident at massive scale. US cybersecurity equities rally as defence procurement expectations rise. Federal government issues emergency advisory to US entities with GCC operational technology exposure.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'EU ENISA raises cyber threat level for entities with GCC operations. DORA (Digital Operational Resilience Act) compliance tested against scenario of third-country infrastructure compromise. European energy companies with Gulf JV operations review IT/OT segmentation.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Asian energy companies with GCC SCADA system integration contracts face liability review. Japanese industrial automation firms deploy emergency patches for Gulf-deployed systems. Chinese state enterprises with Gulf infrastructure projects activate cyber incident response.',
      },
    ],
    signals: [
      { signal: 'Multi-vector attack on GCC critical infrastructure', type: 'Operational', source: 'GCC-CERT', impact: 'Power, water, and telecommunications systems simultaneously affected' },
      { signal: 'Industrial control systems compromised across energy sector', type: 'Operational', source: 'ICS-CERT advisory', impact: 'Oil and gas production facilities enter manual override — output drops 30%' },
      { signal: 'Telecommunications backbone degraded', type: 'Operational', source: 'National telecom operators', impact: 'Financial transaction processing speed drops; e-commerce halts' },
    ],
    propagation: [
      { node: 'Critical infrastructure', effect: 'Power, water, telecom systems enter degraded mode', direction: '↓' },
      { node: 'Energy production', effect: 'Oil/gas output drops as SCADA systems go offline', direction: '↓' },
      { node: 'Financial systems', effect: 'Payment processing slows to manual backup levels', direction: '↓' },
      { node: 'Economic output', effect: 'GDP impact estimated at 2–4% annualised during disruption', direction: '↓' },
      { node: 'Sovereign reputation', effect: 'Investment attractiveness damaged for 12–18 months', direction: '↓' },
    ],
    reasoning: {
      why: 'GCC economies have undergone rapid digitalisation. The attack surface is vast and interconnected — a cyber attack on one system cascades through digitally-dependent infrastructure. Unlike physical disruption, cyber attacks can persist invisibly for weeks.',
      how: 'Network isolation of compromised systems. Activation of manual backup operations. International coordination with Five Eyes cyber commands for attribution and response.',
      what: 'Activate national cyber emergency protocols. Isolate compromised networks. Switch critical infrastructure to manual operation. Deploy international incident response teams. Issue sovereign communication on continuity of essential services.',
      signalBasis: ['Multi-vector attack on GCC critical infrastructure', 'Industrial control systems compromised across energy sector'],
      propagationLink: 'Critical infrastructure ↓ → Energy production ↓ → Economic output ↓',
    },
  },
  {
    scenarioId: 'energy_market_volatility_shock',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Energy price volatility exceeds 2020 levels. Options market implied volatility on crude reaches 80%. Commodity trading houses face margin call cascades — at least two major traders request emergency credit lines from prime brokers.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'ESMA considers temporary position limits on energy derivatives. EU energy price cap mechanism stress-tested against extreme volatility. ECB models second-round inflation effects of persistent energy price instability on Eurozone economy.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Asian state-owned oil companies accelerate long-term supply agreements to hedge volatility. Chinese strategic reserve purchases surge, removing spot volume from an already tight market. Indian fuel subsidy programme faces fiscal blowout on volatile input costs.',
      },
    ],
    signals: [
      { signal: 'Crude oil 30-day volatility exceeds 60%', type: 'Market', source: 'CBOE OVX Index', impact: 'Risk management models across energy industry break down' },
      { signal: 'GCC fiscal planning assumptions invalidated', type: 'Economic', source: 'Ministry of Finance forecasts', impact: 'Budget execution becomes impossible with unpredictable revenue' },
      { signal: 'Commodity trader margin calls exceed $10B', type: 'Market', source: 'LME / ICE clearing data', impact: 'Systemic risk in commodity trading ecosystem; potential clearing house stress' },
    ],
    propagation: [
      { node: 'Energy prices', effect: 'Daily swings of 10–15% — beyond hedging capacity', direction: '⚠' },
      { node: 'GCC fiscal planning', effect: 'Revenue forecasting becomes unreliable; budget execution freezes', direction: '↓' },
      { node: 'Investment decisions', effect: 'Capital allocation halts as NPV calculations become meaningless', direction: '↓' },
      { node: 'Commodity trading', effect: 'Counterparty risk repriced; clearing house adequacy questioned', direction: '⚠' },
      { node: 'Consumer confidence', effect: 'Fuel price instability erodes household budget predictability', direction: '↓' },
    ],
    reasoning: {
      why: 'Volatility destroys the ability to plan. GCC sovereign budgets, corporate capital allocation, and household spending all depend on predictable energy prices. When volatility exceeds hedging capacity, the entire economic planning framework fails.',
      how: 'Coordinated OPEC+ production adjustment to narrow price bands. Sovereign communication to signal fiscal resilience. Emergency hedging programme for exposed state-owned enterprises.',
      what: 'OPEC+ emergency session to agree production adjustment corridor. GCC central banks publish FX reserve adequacy data to demonstrate fiscal buffers. State-owned enterprises execute emergency hedging programme. Announce consumer price stabilisation fund.',
      signalBasis: ['Crude oil 30-day volatility exceeds 60%', 'GCC fiscal planning assumptions invalidated'],
      propagationLink: 'Energy prices ⚠ → GCC fiscal planning ↓ → Investment decisions ↓',
    },
  },
  {
    scenarioId: 'oman_port_closure',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Oman port closure disrupts US military logistics in the Arabian Sea. LNG shipments from Qalhat terminal suspended, affecting US East Coast re-gasification imports. Oman sovereign bond spreads widen as fiscal vulnerability exposed.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'EU monitors disruption to Oman-origin petrochemical exports feeding European industrial supply chains. Salalah free zone operations halt impacts European retailers with Oman-hub distribution. Maritime safety advisories updated for Indian Ocean approaches.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Indian western coast ports see overflow from Oman transshipment diversion. Chinese-built Duqm industrial zone operations disrupted, affecting Belt and Road milestone delivery. South Korean shipbuilders face delay on vessels under construction at Oman drydock facilities.',
      },
    ],
    signals: [
      { signal: 'Salalah and Sohar ports simultaneously offline', type: 'Operational', source: 'Oman Ports Authority', impact: 'Oman loses both primary commercial port terminals' },
      { signal: 'Oman LNG loadings suspended at Qalhat', type: 'Market', source: 'AIS vessel tracking', impact: '10+ MTPA LNG capacity removed from seaborne market' },
      { signal: 'Oman GDP forecast revised down 3%', type: 'Economic', source: 'Central Bank of Oman', impact: 'Sovereign fiscal buffers tested; rating outlook shifts negative' },
    ],
    propagation: [
      { node: 'Port operations', effect: 'Oman\'s two major ports go offline simultaneously', direction: '↓' },
      { node: 'LNG exports', effect: 'Qalhat terminal ceases loading — 10 MTPA removed', direction: '↓' },
      { node: 'Re-export trade', effect: 'Salalah free zone transshipment function collapses', direction: '↓' },
      { node: 'Oman GDP', effect: 'Port-dependent GDP contracts 3–5%', direction: '↓' },
      { node: 'GCC logistics chain', effect: 'Regional logistics network loses redundancy node', direction: '↓' },
    ],
    reasoning: {
      why: 'Oman\'s ports are the GCC\'s eastern redundancy — when Hormuz or UAE ports face stress, Oman absorbs overflow. Losing Oman ports simultaneously removes the backup system, leaving the entire region with no maritime fallback.',
      how: 'Emergency cargo diversion to UAE and Saudi Red Sea ports. Military logistics support for essential supplies. Accelerate repair timelines with international maritime engineering support.',
      what: 'Redirect Oman-bound cargo to Jebel Ali and King Abdullah Port. Deploy Omani military for port security and logistics. Request GCC mutual aid for essential goods supply. Activate Oman sovereign fund drawdown for emergency fiscal support.',
      signalBasis: ['Salalah and Sohar ports simultaneously offline', 'Oman LNG loadings suspended at Qalhat'],
      propagationLink: 'Port operations ↓ → Re-export trade ↓ → GCC logistics chain ↓',
    },
  },
  {
    scenarioId: 'bahrain_sovereign_stress',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Bahrain sovereign stress raises contagion fears for GCC dollar bond market. US investment banks pull back from Bahraini debt placement. GCC sovereign guarantee framework — informally assumed since 2018 — faces its first real test.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'European banks with Bahrain subsidiaries face regulatory scrutiny on exposure concentration. EBA conducts targeted assessment of EU banking system exposure to GCC sovereign risk. European asset managers with Bahraini bond holdings mark positions to distressed levels.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Asian banks with Bahrain-hub operations review booking centre viability. Indian IT outsourcing contracts with Bahrain financial institutions face payment delays. Bahrain\'s aluminium smelter — a major Asian export — faces operational uncertainty.',
      },
    ],
    signals: [
      { signal: 'Bahrain 10Y bond yield exceeds 8%', type: 'Market', source: 'Bloomberg', impact: 'Sovereign borrowing costs become unsustainable for budget financing' },
      { signal: 'Foreign reserve cover drops below 2 months imports', type: 'Economic', source: 'Central Bank of Bahrain', impact: 'Currency peg sustainability questioned; capital controls discussed' },
      { signal: 'GCC financial support package negotiations stall', type: 'Geopolitical', source: 'Diplomatic sources', impact: 'Market confidence in implicit GCC sovereign guarantee erodes' },
    ],
    propagation: [
      { node: 'Sovereign borrowing', effect: 'Bond yields spike to 8%+ — market access effectively closed', direction: '↑' },
      { node: 'Currency peg', effect: 'BHD/USD peg pressure mounts; central bank intervention depletes reserves', direction: '⚠' },
      { node: 'Banking sector', effect: 'Banks face sovereign exposure concentration; NPL ratios rise', direction: '↓' },
      { node: 'GCC contagion', effect: 'Other GCC sovereigns repriced on precedent of potential default', direction: '↓' },
      { node: 'Financial centre status', effect: 'Bahrain\'s role as GCC financial hub permanently damaged', direction: '↓' },
    ],
    reasoning: {
      why: 'Bahrain is the smallest GCC economy but hosts a disproportionate share of regional financial infrastructure. A sovereign stress event doesn\'t just affect Bahrain — it reprices the implicit mutual support assumption that underpins GCC sovereign credit ratings.',
      how: 'GCC financial support package activation. IMF technical assistance engagement. Fiscal consolidation programme announcement. Central bank reserve management optimisation.',
      what: 'Activate GCC Development Fund emergency tranche ($5B+). IMF Article IV accelerated consultation. Announce 3-year fiscal consolidation roadmap. Central bank deploys reserve management optimisation to extend peg defence capacity.',
      signalBasis: ['Bahrain 10Y bond yield exceeds 8%', 'Foreign reserve cover drops below 2 months imports'],
      propagationLink: 'Sovereign borrowing ↑ → Currency peg ⚠ → GCC contagion ↓',
    },
  },
  {
    scenarioId: 'kuwait_fiscal_shock',
    narratives: [
      {
        region: 'US Financial',
        perspective: 'Kuwait fiscal shock highlights structural vulnerability of oil-dependent sovereigns. KIA — one of the world\'s oldest SWFs — faces unprecedented drawdown pressure. US asset managers with Kuwait Investment Office mandates face redemption notices.',
      },
      {
        region: 'EU Regulatory',
        perspective: 'European real estate markets — particularly London — face selling pressure from Kuwaiti sovereign divestment. EU monitors capital flow implications of GCC fiscal retrenchment. ECB assesses second-order effects on European bank Gulf exposure.',
      },
      {
        region: 'Asia Industrial',
        perspective: 'Kuwaiti infrastructure project deferrals affect Asian contractors with $20B+ in active Gulf projects. Chinese construction equipment exports to Kuwait decline sharply. Japanese trading houses with Kuwait petroleum agreements face renegotiation pressure.',
      },
    ],
    signals: [
      { signal: 'Kuwait budget deficit exceeds 20% of GDP', type: 'Economic', source: 'Kuwait Ministry of Finance', impact: 'Structural fiscal imbalance exposed; legislative gridlock prevents reform' },
      { signal: 'KIA forced to liquidate $15B in global assets', type: 'Market', source: 'SWF transaction data', impact: 'Forced selling creates downward pressure in global markets' },
      { signal: 'Public sector salary payments at risk', type: 'Economic', source: 'Parliamentary budget committee', impact: 'Social stability risks as government employment is 80%+ of Kuwaiti workforce' },
    ],
    propagation: [
      { node: 'Fiscal balance', effect: 'Deficit exceeds 20% of GDP — unsustainable trajectory', direction: '↓' },
      { node: 'Sovereign wealth', effect: 'KIA drawdown accelerates; intergenerational wealth transfers reversed', direction: '↓' },
      { node: 'Public spending', effect: 'Capital expenditure halted; current expenditure at risk', direction: '↓' },
      { node: 'Economic growth', effect: 'Non-oil GDP contracts as government spending engine stalls', direction: '↓' },
      { node: 'GCC fiscal credibility', effect: 'Market questions fiscal resilience of all oil-dependent GCC states', direction: '↓' },
    ],
    reasoning: {
      why: 'Kuwait\'s fiscal shock exposes the structural vulnerability of the GCC rentier state model. With 80%+ of Kuwaiti nationals employed by government, fiscal stress translates directly to social stress — a risk no other shock channel creates.',
      how: 'Emergency fiscal package combining expenditure rationalisation with KIA strategic drawdown programme. GCC solidarity mechanisms to prevent contagion. Legislative engagement to unlock structural reform.',
      what: 'Emergency Amiri decree enabling KIA drawdown for fiscal stabilisation. Immediate capital expenditure review — prioritise by economic multiplier. Engage Parliament on revenue diversification legislation. Coordinate with GCC partners on joint fiscal messaging.',
      signalBasis: ['Kuwait budget deficit exceeds 20% of GDP', 'Public sector salary payments at risk'],
      propagationLink: 'Fiscal balance ↓ → Public spending ↓ → GCC fiscal credibility ↓',
    },
  },
];

/* ── Accessors ── */

const manifestMap = new Map(manifest.map((s) => [s.scenarioId, s]));

export function getIntelligence(scenarioId: string): ScenarioIntelligence | undefined {
  return manifestMap.get(scenarioId);
}

export function getAllIntelligence(): ScenarioIntelligence[] {
  return manifest;
}
