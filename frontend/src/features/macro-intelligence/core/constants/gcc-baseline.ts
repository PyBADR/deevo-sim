import type {
  GCCCountry,
  SectorType,
  GraphNodeRef,
  GraphEdgeRef,
  CountryMacroState,
  SectorTransmissionState,
} from "../types/intelligence";

export const GCC_COUNTRIES: GCCCountry[] = [
  "saudi_arabia",
  "uae",
  "kuwait",
  "qatar",
  "bahrain",
  "oman",
];

export const GCC_SECTORS: SectorType[] = [
  "banking",
  "insurance",
  "fintech",
  "real_estate",
  "government",
  "oil_and_gas",
  "logistics",
  "energy",
];

export const GCC_BASELINE_NODES: GraphNodeRef[] = [
  { id: "sa", label: "Saudi Arabia", type: "country", country: "saudi_arabia" },
  { id: "uae", label: "United Arab Emirates", type: "country", country: "uae" },
  { id: "kw", label: "Kuwait", type: "country", country: "kuwait" },
  { id: "qa", label: "Qatar", type: "country", country: "qatar" },
  { id: "bh", label: "Bahrain", type: "country", country: "bahrain" },
  { id: "om", label: "Oman", type: "country", country: "oman" },

  { id: "sama", label: "Saudi Central Bank", type: "central_bank", country: "saudi_arabia", sector: "banking" },
  { id: "cbuae", label: "Central Bank of the UAE", type: "central_bank", country: "uae", sector: "banking" },
  { id: "cbk", label: "Central Bank of Kuwait", type: "central_bank", country: "kuwait", sector: "banking" },
  { id: "qcb", label: "Qatar Central Bank", type: "central_bank", country: "qatar", sector: "banking" },
  { id: "cbb", label: "Central Bank of Bahrain", type: "central_bank", country: "bahrain", sector: "banking" },
  { id: "cbo", label: "Central Bank of Oman", type: "central_bank", country: "oman", sector: "banking" },

  { id: "aramco", label: "Saudi Aramco", type: "energy_asset", country: "saudi_arabia", sector: "oil_and_gas" },
  { id: "ras_tanura", label: "Ras Tanura Terminal", type: "port", country: "saudi_arabia", sector: "logistics" },
  { id: "jebel_ali", label: "Jebel Ali Port", type: "port", country: "uae", sector: "logistics" },
  { id: "brent", label: "Brent Crude", type: "commodity", sector: "energy" },
];

export const GCC_BASELINE_EDGES: GraphEdgeRef[] = [
  { from: "brent", to: "aramco", relation: "prices", weight: 0.88, rationale: "Oil benchmark repricing affects export revenue expectations." },
  { from: "aramco", to: "ras_tanura", relation: "routes_through", weight: 0.91, rationale: "Export throughput depends on terminal continuity." },
  { from: "ras_tanura", to: "jebel_ali", relation: "routes_through", weight: 0.73, rationale: "Regional shipping congestion spills into UAE logistics." },
  { from: "sa", to: "bh", relation: "depends_on", weight: 0.62, rationale: "Macro-financial spillovers transmit across GCC banking and trade linkages." },
  { from: "sama", to: "cbuae", relation: "settles_with", weight: 0.55, rationale: "Regional liquidity coordination affects UAE market confidence." },
  { from: "sama", to: "cbk", relation: "settles_with", weight: 0.49, rationale: "Saudi liquidity posture transmits into Kuwait cross-border risk perception." },
  { from: "sama", to: "qcb", relation: "settles_with", weight: 0.46, rationale: "Central bank response signaling affects Qatar funding confidence." },
  { from: "sama", to: "cbb", relation: "settles_with", weight: 0.58, rationale: "Bahrain is highly exposed to regional financial signaling." },
  { from: "sama", to: "cbo", relation: "settles_with", weight: 0.42, rationale: "Oman is exposed through liquidity and trade transmission." },
];

export const GCC_BASELINE_COUNTRY_STATES: CountryMacroState[] = [
  {
    country: "saudi_arabia",
    stressLevel: "high",
    compositeStress: 0.72,
    primaryDriver: "energy_export_disruption",
    fiscalPressure: 0.61,
    liquidityPressure: 0.44,
    externalExposure: 0.58,
    narrativeSummary: "Saudi Arabia is the primary transmission anchor through energy, export revenue, and regional signaling.",
  },
  {
    country: "uae",
    stressLevel: "elevated",
    compositeStress: 0.55,
    primaryDriver: "logistics_congestion",
    fiscalPressure: 0.31,
    liquidityPressure: 0.38,
    externalExposure: 0.57,
    narrativeSummary: "UAE stress builds through trade rerouting, ports, and financial confidence effects.",
  },
  {
    country: "kuwait",
    stressLevel: "elevated",
    compositeStress: 0.47,
    primaryDriver: "regional_liquidity_repricing",
    fiscalPressure: 0.28,
    liquidityPressure: 0.41,
    externalExposure: 0.43,
    narrativeSummary: "Kuwait is exposed through sovereign and banking confidence spillovers.",
  },
  {
    country: "qatar",
    stressLevel: "elevated",
    compositeStress: 0.43,
    primaryDriver: "energy_market_repricing",
    fiscalPressure: 0.24,
    liquidityPressure: 0.33,
    externalExposure: 0.39,
    narrativeSummary: "Qatar is pressured through LNG/oil market repricing and regional institutional posture.",
  },
  {
    country: "bahrain",
    stressLevel: "high",
    compositeStress: 0.60,
    primaryDriver: "financial_transmission",
    fiscalPressure: 0.48,
    liquidityPressure: 0.51,
    externalExposure: 0.52,
    narrativeSummary: "Bahrain absorbs high macro-financial stress due to regional dependency coupling.",
  },
  {
    country: "oman",
    stressLevel: "elevated",
    compositeStress: 0.40,
    primaryDriver: "trade_and_energy_spillover",
    fiscalPressure: 0.29,
    liquidityPressure: 0.30,
    externalExposure: 0.36,
    narrativeSummary: "Oman is affected secondarily through trade and energy spillovers.",
  },
];

export const GCC_BASELINE_SECTOR_STATES: SectorTransmissionState[] = [
  {
    sector: "oil_and_gas",
    stressLevel: "high",
    compositeStress: 0.73,
    transmissionChannel: "export_throughput_and_price_repricing",
    primaryCountry: "saudi_arabia",
    impactSummary: "Oil & gas is the primary transmission sector through export compression and benchmark repricing.",
  },
  {
    sector: "logistics",
    stressLevel: "high",
    compositeStress: 0.68,
    transmissionChannel: "port_congestion_and_rerouting",
    primaryCountry: "uae",
    impactSummary: "Logistics stress rises through terminal bottlenecks and delayed regional rerouting.",
  },
  {
    sector: "banking",
    stressLevel: "elevated",
    compositeStress: 0.56,
    transmissionChannel: "confidence_and_liquidity_signaling",
    primaryCountry: "bahrain",
    impactSummary: "Banking stress builds via liquidity posture, interbank confidence, and reserve signaling.",
  },
  {
    sector: "insurance",
    stressLevel: "elevated",
    compositeStress: 0.49,
    transmissionChannel: "marine_risk_and_claims_pressure",
    primaryCountry: "qatar",
    impactSummary: "Insurance is stressed through marine risk repricing and catastrophe reserve pressure.",
  },
];
