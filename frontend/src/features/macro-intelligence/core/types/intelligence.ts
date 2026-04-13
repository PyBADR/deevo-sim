export type NarrativeLens = "us_financial" | "eu_regulatory" | "asia_industrial";

export type SignalSourceType =
  | "news"
  | "market_data"
  | "macro_data"
  | "official_statement"
  | "social_realtime"
  | "internal_model";

export type SignalCategory =
  | "energy"
  | "rates"
  | "inflation"
  | "regulation"
  | "logistics"
  | "banking"
  | "insurance"
  | "fintech"
  | "real_estate"
  | "government"
  | "geopolitical";

export type GCCCountry =
  | "saudi_arabia"
  | "uae"
  | "kuwait"
  | "qatar"
  | "bahrain"
  | "oman";

export type SectorType =
  | "banking"
  | "insurance"
  | "fintech"
  | "real_estate"
  | "government"
  | "oil_and_gas"
  | "logistics"
  | "energy";

export type EntityType =
  | "country"
  | "central_bank"
  | "commercial_bank"
  | "insurer"
  | "fintech"
  | "port"
  | "airport"
  | "energy_asset"
  | "government_body"
  | "commodity"
  | "market";

export type StressLevel = "guarded" | "elevated" | "high" | "severe" | "critical";

export interface IntelligenceSignal {
  id: string;
  title: string;
  summary: string;
  sourceType: SignalSourceType;
  sourceName: string;
  category: SignalCategory;
  timestampIso: string;
  regions: string[];
  affectedCountries: GCCCountry[];
  confidence: number;
  intensity: number;
  contradictsBaseCase?: boolean;
  supportsNarrativeLenses: NarrativeLens[];
}

export interface LensReading {
  lens: NarrativeLens;
  headline: string;
  interpretation: string;
  whyItMatters: string;
}

export interface GraphNodeRef {
  id: string;
  label: string;
  type: EntityType;
  country?: GCCCountry;
  sector?: SectorType;
}

export interface GraphEdgeRef {
  from: string;
  to: string;
  relation:
    | "depends_on"
    | "funds"
    | "insures"
    | "regulates"
    | "routes_through"
    | "prices"
    | "settles_with"
    | "exposed_to";
  weight: number;
  rationale: string;
}

export interface PropagationStep {
  step: number;
  triggerNode: GraphNodeRef;
  targetNode: GraphNodeRef;
  mechanism: string;
  effectSummary: string;
  timeLagHours: number;
  stressDelta: number;
  lossDeltaUsd?: number;
}

export interface CountryMacroState {
  country: GCCCountry;
  stressLevel: StressLevel;
  compositeStress: number;
  primaryDriver: string;
  fiscalPressure: number;
  liquidityPressure: number;
  externalExposure: number;
  narrativeSummary: string;
}

export interface SectorTransmissionState {
  sector: SectorType;
  stressLevel: StressLevel;
  compositeStress: number;
  transmissionChannel: string;
  primaryCountry: GCCCountry;
  impactSummary: string;
}

export interface EntityExposureState {
  entity: GraphNodeRef;
  exposureScore: number;
  stressLevel: StressLevel;
  reason: string;
  estimatedLossUsd?: number;
}

export interface DecisionDirective {
  id: string;
  action: string;
  owner: string;
  sector: SectorType | "cross_sector";
  urgency: number;
  rationale: string;
  consequenceOfDelay: string;
  escalationAuthority: string;
  reviewCadenceHours: number;
}

export interface MonitoringStatus {
  directiveId: string;
  owner: string;
  currentStatus: "pending" | "in_progress" | "executed" | "overdue" | "escalated";
  nextReviewIso: string;
  escalationAuthority: string;
  confirmationCriteria: string[];
}

export interface IntelligenceSnapshot {
  scenarioId: string;
  scenarioLabel: string;
  generatedAtIso: string;
  topLineStatus: StressLevel;
  summary: string;
  lensReadings: LensReading[];
  signals: IntelligenceSignal[];
  graphNodes: GraphNodeRef[];
  graphEdges: GraphEdgeRef[];
  countryStates: CountryMacroState[];
  sectorStates: SectorTransmissionState[];
  propagation: PropagationStep[];
  entityExposure: EntityExposureState[];
  decisions: DecisionDirective[];
  monitoring: MonitoringStatus[];
}
