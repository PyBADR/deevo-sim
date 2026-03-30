/* ═══════════════════════════════════════════════════════════════
   Monte Carlo Simulation Layer
   ═══════════════════════════════════════════════════════════════
   Runs N stochastic perturbations of the propagation engine to
   produce distributional statistics on economic loss, sector
   impacts, and driver uncertainty.

   Design goals:
   - Pure client-side, no server required
   - 500 runs x 35 nodes in < 2 s (typically ~200 ms)
   - Preserves edge polarity — only magnitude is perturbed
   ═══════════════════════════════════════════════════════════════ */

import { runPropagation } from './propagation-engine'
import type { GCCNode, GCCEdge } from './gcc-graph'

/* ── Result types ── */

export interface MonteCarloResult {
  runs: number
  meanLoss: number
  medianLoss: number
  varianceLoss: number
  p10Loss: number
  p50Loss: number
  p90Loss: number
  bestCase: number
  worstCase: number
  confidenceScore: number
  sectorDistributions: Map<string, { mean: number; p10: number; p90: number }>
  driverUncertainty: { nodeId: string; label: string; meanImpact: number; variance: number }[]
}

/* ── Options ── */

export interface MonteCarloOptions {
  runs?: number
  weightNoise?: number
  severityRange?: [number, number]
  lang?: 'ar' | 'en'
}

/* ════════════════════════════════════════════════
   MAIN MONTE CARLO FUNCTION
   ════════════════════════════════════════════════ */

export function runMonteCarlo(
  nodes: GCCNode[],
  edges: GCCEdge[],
  shocks: { nodeId: string; impact: number }[],
  options: MonteCarloOptions = {},
): MonteCarloResult {
  const {
    runs = 500,
    weightNoise = 0.1,
    severityRange = [0.7, 1.3],
    lang = 'ar',
  } = options

  const [sevMin, sevMax] = severityRange

  // Pre-allocate collection arrays
  const lossResults: number[] = new Array(runs)

  // Sector impact accumulators: sectorName -> array of avgImpact per run
  const sectorRuns = new Map<string, number[]>()

  // Per-node impact accumulators: nodeId -> array of abs(impact) per run
  const nodeRuns = new Map<string, number[]>()
  for (const node of nodes) {
    nodeRuns.set(node.id, new Array(runs))
  }

  // ── Run simulations ──
  for (let r = 0; r < runs; r++) {
    // (a) Perturb edge weights — preserve polarity, only change magnitude
    const perturbedEdges: GCCEdge[] = edges.map(e => {
      const noise = gaussianRandom() * weightNoise
      let newWeight = e.weight * (1 + noise)
      // Clamp magnitude to [0, 1] — polarity lives in e.polarity, not weight
      newWeight = Math.max(0, Math.min(1, newWeight))
      return { ...e, weight: newWeight }
    })

    // (b) Perturb shock severity uniformly within severityRange
    const perturbedShocks = shocks.map(s => ({
      nodeId: s.nodeId,
      impact: Math.max(-1, Math.min(1, s.impact * (sevMin + Math.random() * (sevMax - sevMin)))),
    }))

    // (c) Run propagation
    const result = runPropagation(perturbedEdges.length > 0 ? nodes : nodes, perturbedEdges, perturbedShocks, 6, lang)

    // (d) Collect totalLoss
    lossResults[r] = result.totalLoss

    // Collect sector impacts
    for (const sector of result.affectedSectors) {
      if (!sectorRuns.has(sector.sectorLabel)) {
        sectorRuns.set(sector.sectorLabel, new Array(runs).fill(0))
      }
      sectorRuns.get(sector.sectorLabel)![r] = sector.avgImpact
    }

    // Collect per-node impacts
    for (const node of nodes) {
      const impact = result.nodeImpacts.get(node.id) ?? 0
      nodeRuns.get(node.id)![r] = Math.abs(impact)
    }
  }

  // ── Compute loss statistics ──
  const sortedLoss = lossResults.slice().sort((a, b) => a - b)

  const meanLoss = lossResults.reduce((a, b) => a + b, 0) / runs
  const medianLoss = percentile(sortedLoss, 0.5)
  const varianceLoss = lossResults.reduce((sum, v) => sum + (v - meanLoss) ** 2, 0) / runs
  const p10Loss = percentile(sortedLoss, 0.1)
  const p50Loss = medianLoss
  const p90Loss = percentile(sortedLoss, 0.9)
  const bestCase = sortedLoss[0]
  const worstCase = sortedLoss[sortedLoss.length - 1]

  // Confidence: tighter distribution = higher confidence
  const cv = meanLoss !== 0 ? Math.sqrt(varianceLoss) / Math.abs(meanLoss) : 1
  const confidenceScore = Math.max(0, Math.min(1, 1 - cv))

  // ── Sector distributions ──
  const sectorDistributions = new Map<string, { mean: number; p10: number; p90: number }>()
  for (const [sectorLabel, impacts] of sectorRuns) {
    const sorted = impacts.slice().sort((a, b) => a - b)
    const mean = impacts.reduce((a, b) => a + b, 0) / runs
    sectorDistributions.set(sectorLabel, {
      mean,
      p10: percentile(sorted, 0.1),
      p90: percentile(sorted, 0.9),
    })
  }

  // ── Driver uncertainty ──
  const driverUncertainty: MonteCarloResult['driverUncertainty'] = []
  for (const node of nodes) {
    const impacts = nodeRuns.get(node.id)!
    const mean = impacts.reduce((a, b) => a + b, 0) / runs
    if (mean < 0.005) continue // skip negligible nodes
    const variance = impacts.reduce((sum, v) => sum + (v - mean) ** 2, 0) / runs
    driverUncertainty.push({
      nodeId: node.id,
      label: lang === 'ar' ? (node.labelAr || node.label) : node.label,
      meanImpact: mean,
      variance,
    })
  }
  driverUncertainty.sort((a, b) => b.variance - a.variance)

  return {
    runs,
    meanLoss,
    medianLoss,
    varianceLoss,
    p10Loss,
    p50Loss,
    p90Loss,
    bestCase,
    worstCase,
    confidenceScore,
    sectorDistributions,
    driverUncertainty,
  }
}

/* ════════════════════════════════════════════════
   HELPERS
   ════════════════════════════════════════════════ */

/**
 * Box-Muller transform: returns a normally distributed random number
 * with mean 0 and standard deviation 1.
 */
function gaussianRandom(): number {
  let u = 0
  let v = 0
  // Avoid log(0)
  while (u === 0) u = Math.random()
  while (v === 0) v = Math.random()
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v)
}

/**
 * Returns the value at a given percentile from a pre-sorted array.
 * Uses linear interpolation between adjacent elements.
 */
function percentile(sortedArray: number[], p: number): number {
  if (sortedArray.length === 0) return 0
  if (sortedArray.length === 1) return sortedArray[0]

  const index = p * (sortedArray.length - 1)
  const lower = Math.floor(index)
  const upper = Math.ceil(index)

  if (lower === upper) return sortedArray[lower]

  const frac = index - lower
  return sortedArray[lower] * (1 - frac) + sortedArray[upper] * frac
}
