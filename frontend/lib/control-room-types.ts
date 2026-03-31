/**
 * Control Room UI Types
 * Specialized types for the Control Room spatial & visualization interface
 */

export interface ScenarioTemplate {
  id: string
  name: string
  nameAr: string
  description: string
  descriptionAr: string
  category: 'geopolitical' | 'economic' | 'infrastructure' | 'security'
  severity: number
}

export interface ScenarioResult {
  scenarioId: string
  runId: string
  timestamp: string
  severity: number
  totalImpact: number
  affectedEntities: string[]
  riskDelta: number
  cascadeChain: string[]
  insuranceImpact: number
  summary: string
  summaryAr: string
  recommendations: string[]
  recommendationsAr: string[]
}

export interface RiskScore {
  overall: number
  disruption: number
  probability: number
  velocity: number
  scale: number
}

export interface MapEntity {
  id: string
  type: 'event' | 'airport' | 'port' | 'corridor' | 'flight' | 'vessel' | 'conflict_zone'
  name: string
  nameAr: string
  lat: number
  lon: number
  riskScore: RiskScore
  disruptionScore: number
  severity?: number
  status?: 'active' | 'monitored' | 'resolved'
  description?: string
  descriptionAr?: string
  relatedEntities?: string[]
  recentEvents?: Event[]
}

export interface Event {
  id: string
  type: string
  timestamp: Date
  description: string
  impact: number
  affectedEntities: string[]
}

export interface ExplanationOutput {
  whatHappened: string
  whatHappenedAr: string
  whatImpacted: string
  whatImpactedAr: string
  riskQuantified: string
  riskQuantifiedAr: string
  recommendations: string
  recommendationsAr: string
  cascadeVisualization: CascadeNode[]
}

export interface CascadeNode {
  id: string
  label: string
  impact: number
  layer: 'geography' | 'infrastructure' | 'economy' | 'finance' | 'society'
  children?: CascadeNode[]
}

export interface LayerVisibility {
  events: boolean
  airports: boolean
  ports: boolean
  corridors: boolean
  flights: boolean
  vessels: boolean
  heatmap: boolean
  riskZones: boolean
  flowLines: boolean
}

export interface PanelState {
  leftOpen: boolean
  rightOpen: boolean
  bottomOpen: boolean
  selectedEntity: string | null
  selectedScenario: string | null
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical'
  riskLevel: number
  activeSources: number
  lastRefresh: Date
  scenarioRunning: boolean
  activeScearioName?: string
}

export interface DeckglLayer {
  id: string
  type: 'heatmap' | 'arc' | 'path' | 'scatterplot' | 'icon' | 'screengrid'
  visible: boolean
  opacity: number
  data: any[]
}
