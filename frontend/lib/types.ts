/* =================================================
    Deevo Sim — Core Type Definitions
    Decision Intelligence Platform
   ================================================= */

// Base type unions
export type EntityType = 'person' | 'organization' | 'topic' | 'region' | 'platform' | 'media'
export type SpreadLevel = 'low' | 'medium' | 'high' | 'critical'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type SentimentDirection = 'positive' | 'negative' | 'mixed' | 'neutral'
export type AgentArchetype = 'reactive' | 'analytical' | 'neutral'
export type AgentPlatform = 'twitter' | 'whatsapp' | 'news'
export type ActionPriority = 'immediate' | 'short-term' | 'monitoring'
export type FactorDirection = 'amplifying' | 'dampening' | 'neutral'

/** Scenario seed input */
export interface Scenario {
  id: string
  title: string
  titleAr?: string
  scenario: string
  raw_text: string
  language: 'ar' | 'en'
  country: string
  category: string
}

/** Extracted entity from scenario parsing */
export interface Entity {
  id: string
  name: string
  nameAr?: string
  type: EntityType
  weight: number
  description?: string
}

/** Graph node for visualization */
export interface GraphNode {
  id: string
  label: string
  type: EntityType
  weight: number
  x?: number
  y?: number
}

/** Graph edge representing relationship */
export interface GraphEdge {
  id: string
  source: string
  target: string
  label?: string
  weight: number
}

/** Single simulation timestep */
export interface SimulationStep {
  id: number
  title: string
  titleAr?: string
  description: string
  descriptionAr?: string
  timestamp: string
  sentiment: number
  visibility: number
  events: string[]
   }

/* =================================================
   DECISION LAYER TYPES
   ================================================= */

/** Recommended executive action */
export interface RecommendedAction {
  id: string
  priority: ActionPriority
  action: string
  actionAr?: string
  rationale: string
  rationaleAr?: string
  timeframe: string
  impact: 'high' | 'medium' | 'low'
}

/** Explainability factor for predictions */
export interface ExplainabilityItem {
  factor: string
  factorAr?: string
  direction: FactorDirection
  weight: number
  description: string
  descriptionAr?: string
}

/** Scenario narrative framing */
export interface ScenarioNarrative {
  title: string
  titleAr?: string
  subtitle: string
  subtitleAr?: string
  summary: string
  summaryAr?: string
  riskDescription: string
  riskDescriptionAr?: string
}

/** Full decision output from simulation engine */
export interface DecisionOutput {
  riskLevel: RiskLevel
  expectedSpread: number
  sentiment: SentimentDirection
  primaryDriver: string
  primaryDriverAr?: string
  criticalTimeWindow: string
  criticalTimeWindowAr?: string
  recommendedActions: RecommendedAction[]
  explanation: ExplainabilityItem[]
  narrative: ScenarioNarrative
}

/** Complete simulation report with decision layer */
export interface SimulationReport {
  prediction: string
  predictionAr?: string
  mainDriver: string
  mainDriverAr?: string
  spreadLevel: SpreadLevel
  confidence: number
  topInfluencers: string[]
  keyObservations: string[]
  keyObservationsAr?: string[]
  decision: DecisionOutput
}

/** Chat message in analyst panel */
export interface ChatMessage {
  id: string
  role: 'user' | 'analyst'
  content: string
  timestamp: string
}

/** GCC agent persona */
export interface Agent {
  id: string
  name: string
  nameAr?: string
  archetype: AgentArchetype
  platform: AgentPlatform
  influence: number
  region: string
  description?: string
  descriptionAr?: string
}

/** Simulation engine input contract */
export interface SimulationInput {
  scenarioId: string
  scenarioTitle: string
  entities: Entity[]
  agents: Agent[]
  hasGovernmentResponse: boolean
  hasInfluencerAmplification: boolean
  hasMediaPickup: boolean
  baseSentiment: SentimentDirection
}

/** Structured JSON output (Phase 6 compliance) */
export interface SimulationJSON {
  scenario_title: string
  risk_level: RiskLevel
  expected_spread: string
  sentiment: SentimentDirection
  primary_driver: string
  time_window: string
  explanation: string[]
  recommended_actions: string[]
  confidence: string
  key_entities: string[]
}
