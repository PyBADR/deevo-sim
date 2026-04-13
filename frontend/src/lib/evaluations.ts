/**
 * Impact Observatory — Evaluation Manifest
 *
 * Post-decision accountability data for all scenarios.
 * Each evaluation answers: Did the decisions work? What did we learn?
 * What should we change?
 *
 * Every field is written in institutional analyst voice.
 * This is an accountability document, not an analytics console.
 */

// ── Types ───────────────────────────────────────────────────────────

export type Verdict =
  | "Confirmed"
  | "Partially Confirmed"
  | "Revised"
  | "Inconclusive";

export interface RuleOutcome {
  rule: string;
  outcome: string;
}

export interface EvaluationBriefing {
  slug: string;
  scenarioTitle: string;
  verdict: Verdict;
  correctness: number;
  evaluationSummary: string;
  expected: string;
  actual: string;
  correctnessRationale: string;
  analystCommentary: string;
  replaySummary: string;
  rulePerformance: RuleOutcome[];
  evaluatedDate: string;
}

// ── Verdict helpers ─────────────────────────────────────────────────

export function verdictColor(v: Verdict): string {
  switch (v) {
    case "Confirmed":
      return "text-status-olive";
    case "Partially Confirmed":
      return "text-status-amber";
    case "Revised":
      return "text-status-red";
    case "Inconclusive":
      return "text-tx-tertiary";
  }
}

export function verdictBadgeStyle(v: Verdict): string {
  switch (v) {
    case "Confirmed":
      return "bg-status-olive/10 text-status-olive";
    case "Partially Confirmed":
      return "bg-status-amber/10 text-status-amber";
    case "Revised":
      return "bg-status-red/10 text-status-red";
    case "Inconclusive":
      return "bg-bg-muted text-tx-tertiary";
  }
}

// ── Evaluation Registry ─────────────────────────────────────────────

export const evaluations: Record<string, EvaluationBriefing> = {
  // ═══════════════════════════════════════════════════════════════════
  // HORMUZ CHOKEPOINT DISRUPTION
  // ═══════════════════════════════════════════════════════════════════
  hormuz_chokepoint_disruption: {
    slug: "hormuz_chokepoint_disruption",
    scenarioTitle: "Strait of Hormuz Disruption",
    verdict: "Partially Confirmed",
    correctness: 0.74,
    evaluationSummary:
      "Three of four recommended interventions executed within their deadlines. The SPR activation and vessel rerouting performed as projected. The insurance reserve allocation was delayed 18 hours beyond its deadline, resulting in higher marine claims than modeled.",
    expected:
      "If all four interventions executed within their deadlines, total financial exposure would reduce from $4.3B to approximately $1.5B \u2014 preserving $2.8B in economic value. Strategic petroleum reserve activation was projected to cover 60\u201370% of the eastern terminal shortfall within 48 hours. Vessel rerouting would restore Jebel Ali throughput to 65% of baseline by Day 5. Interbank rate stabilization would prevent the credit contagion channel from activating. Insurance reserve allocation would contain marine claims within existing treaty limits. Full recovery to pre-disruption baseline was projected at 42 days.",
    actual:
      "Total financial exposure reached $2.1B \u2014 $600M above the projected $1.5B floor but $2.2B below the unmitigated scenario. SPR activation delivered 2.1M bbl/day of substitute supply within 52 hours, slightly below the 2.4M target but sufficient to prevent terminal shutdown. Jebel Ali throughput recovered to 58% by Day 5 (versus 65% projected) as Bab el-Mandeb corridor congestion exceeded initial rerouting capacity estimates. Interbank rate stabilization held within the 200bps threshold. However, the IFRS 17 catastrophe reserve allocation was delayed to Hour 42 (versus the 24-hour deadline), allowing marine P&I claims to breach the 5x baseline threshold before reinsurance treaties activated. This delay accounted for approximately $380M in additional exposure.",
    correctnessRationale:
      "The 0.74 correctness score reflects strong performance on three of four channels with a material failure on the insurance timeline. The energy and maritime interventions performed within 85\u201390% of projected effectiveness. The financial channel intervention (FX swap lines) performed at projection. The insurance channel underperformed by approximately 40% due to the 18-hour deadline overrun, which allowed claims accumulation to exceed treaty activation thresholds before the reserve was deployed.",
    analystCommentary:
      "The Hormuz scenario validated the observatory\u2019s transmission model for energy and maritime channels but exposed a structural weakness in the insurance response pathway. The Insurance Authority\u2019s 18-hour delay was not a capacity issue \u2014 it was a coordination failure between the Authority and regional reinsurers who required manual treaty activation. This suggests the observatory\u2019s assumption that IFRS 17 catastrophe reserves can be deployed within 24 hours is optimistic for scenarios involving multiple reinsurer jurisdictions. The 42-hour actual timeline should replace the 24-hour assumption in future scenario calibrations.",
    replaySummary:
      "Three institutional lessons emerge. First, SPR activation through SAMA coordination proved faster than the bilateral ministry channel assumed in earlier models \u2014 the 52-hour delivery validates the coordinated activation pathway for future energy scenarios. Second, Jebel Ali rerouting capacity through Bab el-Mandeb is approximately 10% below the model\u2019s assumption when multiple large container lines compete for corridor capacity simultaneously. Third, insurance treaty activation timelines must account for multi-jurisdictional reinsurer coordination, which adds 12\u201318 hours beyond the domestic regulatory trigger. This scenario now serves as the baseline precedent for all future Hormuz-class disruptions.",
    rulePerformance: [
      {
        rule: "SPR activation within 6 hours of energy throughput breach",
        outcome: "Rule triggered correctly. Activation commenced at Hour 4. Delivery timeline exceeded the 48-hour target by 4 hours due to Yanbu pipeline scheduling constraints.",
      },
      {
        rule: "Vessel rerouting activation within 12 hours of port throughput decline",
        outcome: "Rule triggered correctly. Federal Transport Authority initiated rerouting at Hour 9. Throughput recovery underperformed projection by 7 percentage points due to corridor congestion.",
      },
      {
        rule: "FX swap line deployment within 18 hours of interbank spread breach",
        outcome: "Rule triggered correctly. SAMA/CBUAE coordination executed at Hour 14. Interbank spread stabilized at 185bps, within the 200bps threshold.",
      },
      {
        rule: "IFRS 17 catastrophe reserve allocation within 24 hours of claims surge",
        outcome: "Rule failed to execute within deadline. Actual activation at Hour 42 \u2014 18 hours late. Root cause: multi-jurisdictional reinsurer coordination required manual treaty confirmation across three Lloyd\u2019s syndicates. Recommendation: pre-authorize treaty activation for Hormuz-class scenarios.",
      },
    ],
    evaluatedDate: "2026-04-11",
  },

  // ═══════════════════════════════════════════════════════════════════
  // REGIONAL LIQUIDITY STRESS EVENT
  // ═══════════════════════════════════════════════════════════════════
  regional_liquidity_stress_event: {
    slug: "regional_liquidity_stress_event",
    scenarioTitle: "Regional Liquidity Stress",
    verdict: "Confirmed",
    correctness: 0.82,
    evaluationSummary:
      "All three interventions executed within their deadlines. The coordinated liquidity injection arrested the interbank freeze within 30 hours. Total exposure came in $200M below the projected floor.",
    expected:
      "If all three interventions executed within their deadlines, total financial exposure would reduce from $2.7B to approximately $1.1B \u2014 preserving $1.5B in economic value. The coordinated liquidity injection would arrest the interbank freeze within 24\u201336 hours. Regulatory forbearance on mark-to-market would avoid forced selling of sovereign bonds. The 90-day payment extension would contain developer defaults to under 2% of the pipeline. Full normalization of interbank conditions was projected at 60 days.",
    actual:
      "Total financial exposure reached $920M \u2014 $180M below the projected $1.1B floor. The SAMA/CBUAE coordinated injection of $10B (within the $8\u201312B guidance range) stabilized overnight rates to 140bps spread within 30 hours, outperforming the 48-hour projection. Mark-to-market suspension prevented an estimated $450M in forced sovereign bond sales. Developer financing extensions contained defaults to 1.4% of the pipeline (versus 2% projected maximum). Interbank normalization completed in 52 days, 8 days ahead of the 60-day projection. The single underperformance was cross-border correspondent banking, which took 105 days to fully restore versus the projected 90\u2013120 day range \u2014 within tolerance but at the upper bound.",
    correctnessRationale:
      "The 0.82 correctness score reflects execution that met or exceeded projections across all three intervention channels. The liquidity injection was more effective than modeled, likely because SAMA deployed at the upper end of the guidance range ($10B versus the $8B minimum). The real estate forbearance performed within projection. The slight penalty reflects the correspondent banking restoration timeline at the upper bound and the model\u2019s inability to predict the exact injection amount that would be deployed.",
    analystCommentary:
      "This scenario represents the observatory\u2019s strongest validation to date. The model\u2019s transmission chain \u2014 interbank freeze \u2192 deposit flight \u2192 credit tightening \u2192 real estate \u2192 sovereign spread \u2014 played out almost exactly as projected, with timing variances of less than 12 hours at each stage. The key insight is that SAMA\u2019s decision to deploy at $10B rather than the $8B minimum created a confidence surplus that accelerated recovery. Future liquidity scenarios should model a \u201cconfidence multiplier\u201d when central bank intervention exceeds market expectations. The correspondent banking lag is structural and should be modeled as 100\u2013120 days rather than 90\u2013120 days in future calibrations.",
    replaySummary:
      "Two institutional lessons. First, the simultaneous execution of liquidity injection and regulatory forbearance validated the model\u2019s assumption that these must be paired \u2014 either intervention alone would have been insufficient, as the model predicted. This pairing should be encoded as a mandatory constraint in all future banking stress scenarios. Second, deploying at the upper end of the intervention range created disproportionate confidence effects that accelerated recovery by 15\u201320% beyond the linear model. Future calibrations should incorporate a non-linear confidence term when central bank intervention exceeds the market\u2019s expected floor.",
    rulePerformance: [
      {
        rule: "Emergency liquidity injection within 4 hours of overnight rate breach above 280bps",
        outcome: "Rule triggered correctly. SAMA/CBUAE injection commenced at Hour 3.5. Overnight rate stabilized below 150bps spread within 30 hours.",
      },
      {
        rule: "Mark-to-market suspension within 8 hours of liquidity injection",
        outcome: "Rule triggered correctly. Banking regulators issued suspension order at Hour 6. No forced sovereign bond sales occurred during the 72-hour window.",
      },
      {
        rule: "Developer financing extension within 48 hours of credit tightening transmission",
        outcome: "Rule triggered correctly. Real Estate Regulatory Agency issued 90-day extension at Hour 38. Developer defaults contained to 1.4% of pipeline.",
      },
    ],
    evaluatedDate: "2026-04-10",
  },

  // ═══════════════════════════════════════════════════════════════════
  // SAUDI OIL PRODUCTION SHOCK
  // ═══════════════════════════════════════════════════════════════════
  saudi_oil_shock: {
    slug: "saudi_oil_shock",
    scenarioTitle: "Saudi Oil Production Shock",
    verdict: "Partially Confirmed",
    correctness: 0.68,
    evaluationSummary:
      "Four of five interventions executed within deadlines. The OPEC+ coordination took 36 hours instead of 12, reducing the speed of global supply restoration. Sovereign wealth fund deployment was effective but required $2B more than the projected upper bound.",
    expected:
      "If all five interventions executed within their deadlines, total financial exposure would reduce from $5.2B to approximately $2.1B \u2014 preserving $3.1B in economic value. Strategic reserves and OPEC+ coordination would restore 70\u201380% of the global supply shortfall within 5 days. Sovereign wealth fund deployment would prevent fiscal contraction. SAMA intervention would contain interbank spread widening to under 100bps. Full production recovery at Abqaiq/Khurais was projected at 60\u201390 days.",
    actual:
      "Total financial exposure reached $2.9B \u2014 $800M above the projected $2.1B floor. SPR activation delivered 2.5M bbl/day within 68 hours (versus the 72-hour target), performing slightly ahead of projection. However, OPEC+ coordination required 36 hours instead of 12 due to Kuwait\u2019s insistence on production quota credit for emergency increases. This delay allowed Brent crude to sustain a $35/barrel premium for an additional 24 hours, adding approximately $420M in commodity-linked exposure. PIF deployed $10B (versus the $5\u20138B projection) to maintain spending commitments as fiscal revenue contraction exceeded the model\u2019s assumption. SAMA\u2019s interbank intervention stabilized rates at 95bps spread, within the 100bps threshold. Abqaiq processing capacity reached 4.2M bbl/day by Day 16, slightly behind the 14-day projection.",
    correctnessRationale:
      "The 0.68 correctness score reflects two material deviations from projection: the OPEC+ coordination delay (which the model assumed could complete in 12 hours but actually required 36 due to quota politics) and the PIF deployment volume ($10B versus $8B maximum, suggesting the model underestimated fiscal revenue sensitivity at this severity level). The energy, banking, and insurance channels performed within tolerance. The overall loss trajectory was correct in shape but 38% higher in magnitude than projected.",
    analystCommentary:
      "This scenario exposed the observatory\u2019s principal weakness in modeling multilateral coordination timelines. The 12-hour OPEC+ assumption was based on the 2019 post-Abqaiq precedent, but that coordination occurred under different geopolitical conditions. Kuwait\u2019s quota credit demand was predictable in retrospect but absent from the model\u2019s political constraint set. The PIF overdeployment suggests the fiscal breakeven calculation needs recalibration at severity levels above 0.70 \u2014 the current model uses a linear fiscal revenue function that underestimates the revenue impact of combined production loss and commodity price dislocation at extreme severity levels.",
    replaySummary:
      "Three lessons. First, OPEC+ emergency coordination timelines should be modeled as 24\u201348 hours for scenarios requiring production quota adjustments, versus the current 12-hour assumption based on 2019 precedent. The political dimension is non-trivial and varies by which members hold spare capacity. Second, the PIF fiscal buffer model needs a non-linear term at severity levels above 0.70 to account for the compounding effect of simultaneous revenue loss and commodity dislocation. Third, the Abqaiq restoration timeline of 16 days versus the 14-day projection validates the 2019-based engineering estimate but suggests a 14\u201321 day range would be more honest than the current 14-day point estimate.",
    rulePerformance: [
      {
        rule: "SPR activation within 4 hours of production capacity breach",
        outcome: "Rule triggered correctly. Ministry of Energy activated reserves at Hour 3. Delivery of 2.5M bbl/day achieved within 68 hours.",
      },
      {
        rule: "OPEC+ emergency coordination within 12 hours",
        outcome: "Rule failed to execute within deadline. Actual coordination completed at Hour 36. Root cause: Kuwait demanded production quota credit for emergency increases, requiring bilateral negotiation outside the standard OPEC+ framework.",
      },
      {
        rule: "PIF liquidity buffer deployment within 48 hours of fiscal revenue shortfall",
        outcome: "Rule triggered correctly at Hour 41. However, deployment volume of $10B exceeded the $5\u20138B projection by $2B, indicating the fiscal revenue model underestimated the shortfall at this severity level.",
      },
      {
        rule: "SAMA interbank stabilization within 24 hours of sovereign spread widening",
        outcome: "Rule triggered correctly. SAMA intervention at Hour 18 stabilized interbank spread at 95bps, within the 100bps threshold.",
      },
      {
        rule: "Catastrophe reinsurance treaty activation within 72 hours",
        outcome: "Rule triggered correctly. Insurance Authority activated treaties at Hour 64. Claims processing proceeded within treaty capacity limits.",
      },
    ],
    evaluatedDate: "2026-04-09",
  },

  // ═══════════════════════════════════════════════════════════════════
  // RED SEA TRADE CORRIDOR INSTABILITY
  // ═══════════════════════════════════════════════════════════════════
  red_sea_trade_corridor_instability: {
    slug: "red_sea_trade_corridor_instability",
    scenarioTitle: "Red Sea Trade Corridor Disruption",
    verdict: "Confirmed",
    correctness: 0.79,
    evaluationSummary:
      "All three interventions executed within their deadlines. Food security reserves maintained above the 20-day threshold throughout. Container reallocation restored 68% of import capacity by Day 14, slightly below the 70% target.",
    expected:
      "If all three interventions executed within their deadlines, total financial exposure would reduce from $1.5B to approximately $650M \u2014 preserving $850M in economic value. Strategic food reserve activation would maintain 30-day coverage for essential goods. Container reallocation agreements would restore 70% of import capacity within 14 days. Construction material corridors would limit megaproject delays to 2 weeks. Full trade corridor restoration depended on geopolitical resolution.",
    actual:
      "Total financial exposure reached $710M \u2014 $60M above the projected $650M floor. Food reserve activation maintained 26-day coverage (versus 30-day projection) as demand for substitute goods through eastern coast ports created logistics bottlenecks at Dammam that were not fully captured in the model. Container reallocation achieved 68% capacity restoration by Day 14 (versus 70% target) \u2014 within tolerance. NEOM construction material corridors through Salalah and Khalifa Port limited project delays to 11 working days, outperforming the 14-day projection. The primary variance was food logistics: eastern port redirection worked but at lower throughput than the model assumed for Dammam\u2019s cold chain capacity.",
    correctnessRationale:
      "The 0.79 correctness score reflects strong overall execution with a specific model weakness in eastern port cold chain capacity. The food security channel performed at 87% of projection, the trade channel at 97%, and the construction channel at 110%. The aggregate loss variance of $60M (9% above projection) is within acceptable tolerance for a 21-day horizon scenario. The Dammam cold chain limitation was the sole material model gap.",
    analystCommentary:
      "This evaluation validates the observatory\u2019s trade disruption model as fundamentally sound. The 21-day horizon \u2014 the longest in the scenario register \u2014 introduces compounding uncertainty that the model handled well. The Dammam cold chain limitation is a concrete infrastructure constraint that should be incorporated into future food security modeling: the port\u2019s cold storage capacity is approximately 15% below the throughput required for full western-to-eastern coast food import redirection. This is not a model error but a physical infrastructure gap that the Saudi Ports Authority should address independently of scenario planning.",
    replaySummary:
      "Two lessons. First, eastern coast port redirection for food imports is viable but capacity-constrained by Dammam\u2019s cold chain infrastructure. Future Red Sea scenarios should model a 22\u201326 day food coverage range rather than the current 30-day point estimate when relying on eastern port redirection. Second, the NEOM construction corridor through Salalah outperformed expectations, suggesting Oman\u2019s port infrastructure is underutilized in the current model. This pathway should be pre-negotiated as a standing contingency for all Vision 2030 supply chain scenarios.",
    rulePerformance: [
      {
        rule: "Strategic food reserve activation within 72 hours of western port throughput decline",
        outcome: "Rule triggered correctly. Ministry of Commerce activated reserves at Hour 48. Coverage maintained at 26 days, above the 20-day critical threshold but below the 30-day model projection.",
      },
      {
        rule: "Container reallocation agreement within 7 days",
        outcome: "Rule triggered correctly. Saudi Ports Authority executed agreements with Maersk and MSC at Day 5. Capacity restoration reached 68% by Day 14.",
      },
      {
        rule: "Construction material corridor within 14 days",
        outcome: "Rule triggered correctly and outperformed. Royal Commission for NEOM established Salalah/Khalifa Port corridors at Day 8. Project delays limited to 11 working days versus the 14-day projection.",
      },
    ],
    evaluatedDate: "2026-04-08",
  },

  // ═══════════════════════════════════════════════════════════════════
  // GCC CYBER INFRASTRUCTURE ATTACK
  // ═══════════════════════════════════════════════════════════════════
  gcc_cyber_attack: {
    slug: "gcc_cyber_attack",
    scenarioTitle: "GCC Cyber Infrastructure Attack",
    verdict: "Revised",
    correctness: 0.51,
    evaluationSummary:
      "Two of four interventions executed within deadlines. The backup settlement infrastructure took 72 hours to reach 60% capacity instead of the projected 48. The public communication was effective but the SWIFT bypass channel required 48 hours instead of 24, leaving critical commodity payments stranded for an additional day.",
    expected:
      "If all four interventions executed within their deadlines, total financial exposure would reduce from $2.8B to approximately $950M \u2014 preserving $1.9B in economic value. Backup settlement infrastructure would restore 70% of domestic payment capacity within 48 hours. Coordinated public communication would arrest deposit flight. Emergency SWIFT bypass would maintain critical commodity settlement. Full RTGS restoration was projected at 5\u20137 days.",
    actual:
      "Total financial exposure reached $1.6B \u2014 $650M above the projected $950M floor. The GCC cyber incident response team mobilized within 2 hours as projected, but forensic recovery revealed the attack had compromised backup settlement nodes that the model assumed were air-gapped. Backup infrastructure reached only 42% capacity at the 48-hour mark (versus 70% projected), climbing to 61% by Hour 72. The public statement was issued at Hour 10 and reduced deposit withdrawal rates from 0.8%/day to 0.3%/day within 24 hours, performing as projected. However, the SWIFT bypass required 48 hours to establish because SWIFT\u2019s own security review process added 24 hours of bilateral verification that the model did not account for. This stranded approximately $340M in energy commodity payments for an additional day. Full RTGS restoration completed at Day 8, one day beyond the 5\u20137 day projected range.",
    correctnessRationale:
      "The 0.51 correctness score reflects two fundamental model assumptions that proved incorrect: the air-gap integrity of backup settlement nodes and the SWIFT bypass establishment timeline. The cyber incident response and public communication channels performed within projection. However, the payment infrastructure restoration \u2014 the core of this scenario \u2014 underperformed by approximately 40% at the critical 48-hour mark. The total loss variance of $650M (68% above projection) exceeds acceptable tolerance for a 5-day horizon scenario.",
    analystCommentary:
      "This is the observatory\u2019s weakest evaluation and the one that demands the most significant model revision. The air-gap assumption for backup settlement infrastructure was derived from published central bank business continuity documentation, which proved inaccurate under a coordinated multi-vector attack. The SWIFT bypass timeline assumption was based on bilateral drills that did not simulate the actual security verification process SWIFT applies during live incidents. Both assumptions need to be replaced with empirically validated timelines from this event. The observatory\u2019s cyber scenario modeling capability should be considered degraded until these revisions are incorporated and validated against a tabletop exercise with all three central banks and SWIFT.",
    replaySummary:
      "Four lessons, all urgent. First, backup settlement infrastructure air-gap assumptions must be verified through adversarial penetration testing, not documentation review \u2014 the current business continuity plans overstate resilience. Second, SWIFT bypass establishment should be modeled as 36\u201348 hours rather than 24 hours, incorporating the mandatory security verification process. Third, the public communication intervention was the strongest-performing channel, confirming that deposit flight is primarily a confidence phenomenon that responds to governor-level statements within 24 hours. Fourth, the observatory should recommend that GCC central banks conduct a joint cyber resilience exercise specifically targeting the backup settlement pathway \u2014 this is the single highest-priority infrastructure gap identified by any evaluation to date.",
    rulePerformance: [
      {
        rule: "Cyber incident response team deployment within 2 hours",
        outcome: "Rule triggered correctly. Joint SAMA/CBUAE/CBB team mobilized at Hour 1.5. However, forensic analysis revealed compromised backup nodes that the rule\u2019s air-gap assumption did not account for.",
      },
      {
        rule: "Backup settlement infrastructure at 70% capacity within 48 hours",
        outcome: "Rule failed. Actual capacity at 48 hours was 42% due to compromised backup nodes. 61% capacity reached at Hour 72. Recommendation: revise target to 50% at 48 hours with 70% at 72 hours.",
      },
      {
        rule: "Coordinated public statement within 12 hours",
        outcome: "Rule triggered correctly. Statement issued at Hour 10. Deposit withdrawal rate reduced from 0.8%/day to 0.3%/day within 24 hours of issuance.",
      },
      {
        rule: "SWIFT bypass channel within 24 hours",
        outcome: "Rule failed to execute within deadline. Actual establishment at Hour 48. Root cause: SWIFT\u2019s live-incident security verification process added 24 hours that bilateral drill timelines did not simulate.",
      },
    ],
    evaluatedDate: "2026-04-07",
  },

  // ═══════════════════════════════════════════════════════════════════
  // IRAN REGIONAL ESCALATION
  // ═══════════════════════════════════════════════════════════════════
  iran_regional_escalation: {
    slug: "iran_regional_escalation",
    scenarioTitle: "Iran Regional Escalation",
    verdict: "Inconclusive",
    correctness: 0.44,
    evaluationSummary:
      "The scenario has not fully resolved within the 14-day evaluation window. Three of six interventions executed within deadlines. The geopolitical dimension introduced variables outside the model\u2019s scope that make definitive assessment premature.",
    expected:
      "If all six interventions executed within their deadlines, total financial exposure would reduce from $7.0B to approximately $2.8B \u2014 preserving $4.2B in economic value. Strategic reserves and OPEC+ coordination would collapse the crude premium to under $20/barrel within 7 days. Coordinated circuit breakers would arrest equity selloff at \u221215%. Maritime escort protocols would restore Hormuz throughput to 60\u201370% within 5 days. Joint sovereign statement would stabilize CDS spreads within 100bps by Day 10.",
    actual:
      "At the 14-day evaluation mark, total financial exposure has reached $4.1B and continues to evolve. SPR activation delivered as projected. Circuit breaker protocols limited equity market decline to \u221218% (versus the \u221215% target and \u221225% unmitigated projection). SAMA/CBUAE liquidity injection stabilized interbank markets within projection. However, three channels deviated materially: OPEC+ coordination required 5 days instead of 6 hours due to the geopolitical complexity of the triggering event. Maritime escort protocols restored only 45% of Hormuz throughput (versus the 60\u201370% projection) as naval operations continued to constrain commercial corridors. The joint sovereign statement was issued at Hour 14 but CDS spreads remained 140bps above pre-crisis levels at Day 14 (versus the 100bps target), reflecting ongoing geopolitical uncertainty that a communication intervention cannot resolve. Brent crude premium remained at $28/barrel at Day 14 (versus the sub-$20 target).",
    correctnessRationale:
      "The 0.44 correctness score reflects the inherent limitation of modeling geopolitical tail-risk scenarios. The observatory\u2019s financial transmission model performed well \u2014 the interbank, equity, and insurance channels behaved within tolerance of projection. However, the three geopolitically dependent channels (OPEC+ coordination, maritime corridor restoration, sovereign confidence) all underperformed because the underlying geopolitical situation did not resolve within the model\u2019s assumed timeline. This is not a model failure in the traditional sense \u2014 it is a scope limitation. The financial model works; the geopolitical assumptions were insufficiently conservative.",
    analystCommentary:
      "This evaluation must be read differently from the others. The observatory is a financial model, not a geopolitical forecasting system. The Iran scenario\u2019s correctness score reflects the boundary between what the observatory can reliably model (financial transmission, institutional intervention effectiveness, market behavior) and what it cannot (geopolitical resolution timelines, military escalation dynamics, diplomatic coordination under active conflict). The three channels that underperformed are all geopolitically dependent \u2014 their financial projections were correct conditional on the geopolitical assumptions resolving as modeled. The recommendation is not to revise the financial model but to explicitly flag geopolitical dependency in the scenario\u2019s confidence intervals and present two outcome tracks: one for resolution within the modeled timeline and one for extended escalation.",
    replaySummary:
      "One structural lesson and two calibration adjustments. The structural lesson: the observatory should present geopolitical tail-risk scenarios with dual outcome tracks rather than a single projection. The current single-track presentation implied a confidence level that the geopolitical assumptions did not warrant. Calibration adjustments: OPEC+ coordination under active geopolitical crisis should be modeled as 3\u20137 days rather than 6\u201312 hours. Maritime corridor restoration under ongoing naval operations should assume 40\u201350% throughput rather than 60\u201370%. Both adjustments would have brought the model\u2019s projection within 15% of actual outcomes \u2014 a significant improvement from the current 42% variance.",
    rulePerformance: [
      {
        rule: "Joint SPR activation within 6 hours",
        outcome: "Rule triggered correctly. GCC Energy Ministers Council activated reserves at Hour 5. Supply delivery within projection.",
      },
      {
        rule: "Circuit breaker synchronization within 4 hours of market open",
        outcome: "Rule triggered correctly. Capital Market Authorities synchronized triggers before the second trading session. Equity decline limited to \u221218% versus \u221225% unmitigated, but exceeded the \u221215% target by 3 percentage points.",
      },
      {
        rule: "Central bank liquidity injection within 12 hours",
        outcome: "Rule triggered correctly. $17B joint injection deployed at Hour 10. Interbank stabilization within projection.",
      },
      {
        rule: "OPEC+ emergency coordination within 6 hours",
        outcome: "Rule failed to execute within deadline. Actual coordination completed at Day 5. Root cause: geopolitical complexity of the triggering event made standard OPEC+ emergency protocols inapplicable. Recommendation: create a separate \u201cconflict-mode\u201d OPEC+ coordination protocol with longer assumed timelines.",
      },
      {
        rule: "Maritime escort protocol within 24 hours",
        outcome: "Rule triggered at Hour 22 but effectiveness below projection. Hormuz throughput reached 45% versus the 60\u201370% target. Naval operations continued to constrain commercial corridor width.",
      },
      {
        rule: "Joint sovereign statement within 12 hours",
        outcome: "Rule triggered correctly at Hour 14. However, CDS spread stabilization did not occur within the projected timeline \u2014 spreads remained 140bps above baseline at Day 14. Communication intervention cannot substitute for geopolitical resolution.",
      },
    ],
    evaluatedDate: "2026-04-12",
  },
};

// ── Access helpers ───────────────────────────────────────────────────

export function getEvaluation(slug: string): EvaluationBriefing | undefined {
  return evaluations[slug];
}

export function getAllEvaluations(): EvaluationBriefing[] {
  return Object.values(evaluations);
}

export function getAllEvaluationSlugs(): string[] {
  return Object.keys(evaluations);
}

/** Sorted by verdict weight: Revised first, then Inconclusive, Partially Confirmed, Confirmed */
export function getEvaluationsByVerdict(): EvaluationBriefing[] {
  const order: Record<Verdict, number> = {
    Revised: 0,
    Inconclusive: 1,
    "Partially Confirmed": 2,
    Confirmed: 3,
  };
  return getAllEvaluations().sort(
    (a, b) => order[a.verdict] - order[b.verdict]
  );
}
