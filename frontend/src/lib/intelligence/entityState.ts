/**
 * Impact Observatory | مرصد الأثر — Entity Exposure State
 *
 * Entities exist under sectors and countries.
 * Each entity tracks:
 *   - exposure level (0–1 + classified)
 *   - dependency links (what it depends on)
 *   - risk classification
 *   - response status (awaiting / active / executed / overdue)
 *
 * Entity exposure is computed from the intersection of
 * country stress and sector pressure.
 */

import type { GCCCountry } from './countryState';
import type { GCCSector, SectorState } from './sectorState';
import type { CountryMacroState } from './countryState';

/* ── Types ── */

export type ExposureLevel = 'minimal' | 'moderate' | 'elevated' | 'high' | 'critical';
export type RiskClassification = 'monitored' | 'guarded' | 'elevated' | 'severe' | 'critical';
export type ResponseStatus = 'awaiting' | 'active' | 'executed' | 'overdue';

export interface EntityDefinition {
  id: string;
  name: string;
  nameAr: string;
  country: GCCCountry;
  sector: GCCSector;
  /** How exposed this entity is to its sector's stress (0–1) */
  sectorCoupling: number;
  /** How exposed this entity is to its country's macro stress (0–1) */
  countryCoupling: number;
  /** What this entity depends on — named references */
  dependencies: string[];
  /** Which entity owns the decision response */
  responseOwner: string;
}

export interface EntityExposureState {
  entityId: string;
  name: string;
  country: GCCCountry;
  sector: GCCSector;
  /** Computed exposure intensity 0–1 */
  exposure: number;
  /** Classified exposure level */
  level: ExposureLevel;
  /** Computed risk classification */
  riskClassification: RiskClassification;
  /** Current response status */
  responseStatus: ResponseStatus;
  /** Primary driver of exposure */
  driver: string;
  /** Dependencies */
  dependencies: string[];
}

/* ── Entity Registry ──
   Canonical GCC entities across all 6 sectors and 6 countries.
   Expanding this registry adds resolution to the intelligence core.
*/

export const ENTITY_REGISTRY: EntityDefinition[] = [
  // ── Saudi Arabia ──
  { id: 'sama',       name: 'SAMA (Central Bank)',        nameAr: 'مؤسسة النقد العربي السعودي', country: 'SA', sector: 'Banking',    sectorCoupling: 0.90, countryCoupling: 0.85, dependencies: ['Saudi banking system', 'GCC interbank market'], responseOwner: 'SAMA Governor' },
  { id: 'snb',        name: 'Saudi National Bank',        nameAr: 'البنك الأهلي السعودي',       country: 'SA', sector: 'Banking',    sectorCoupling: 0.85, countryCoupling: 0.75, dependencies: ['SAMA liquidity facility', 'Saudi corporate credit'], responseOwner: 'SNB CEO' },
  { id: 'aramco',     name: 'Saudi Aramco',               nameAr: 'أرامكو السعودية',           country: 'SA', sector: 'OilGas',     sectorCoupling: 0.95, countryCoupling: 0.90, dependencies: ['Hormuz transit', 'Global crude demand', 'Pipeline infrastructure'], responseOwner: 'Aramco CEO' },
  { id: 'mof_sa',     name: 'Ministry of Finance (KSA)',   nameAr: 'وزارة المالية',             country: 'SA', sector: 'Government', sectorCoupling: 0.90, countryCoupling: 0.95, dependencies: ['Oil revenue', 'PIF portfolio', 'Vision 2030 budget'], responseOwner: 'Minister of Finance' },
  { id: 'tawuniya',   name: 'Tawuniya Insurance',         nameAr: 'شركة التعاونية للتأمين',     country: 'SA', sector: 'Insurance',  sectorCoupling: 0.75, countryCoupling: 0.65, dependencies: ['Saudi corporate market', 'Reinsurance capacity'], responseOwner: 'Tawuniya CEO' },
  { id: 'stc_pay',    name: 'stc pay',                    nameAr: 'اس تي سي باي',              country: 'SA', sector: 'Fintech',    sectorCoupling: 0.65, countryCoupling: 0.55, dependencies: ['SAMA licensing', 'Saudi payment rails'], responseOwner: 'stc pay CEO' },
  { id: 'roshn',      name: 'ROSHN Group',                nameAr: 'مجموعة روشن',               country: 'SA', sector: 'RealEstate', sectorCoupling: 0.70, countryCoupling: 0.60, dependencies: ['Saudi housing demand', 'Construction financing'], responseOwner: 'ROSHN CEO' },

  // ── UAE ──
  { id: 'cbuae',      name: 'Central Bank of the UAE',    nameAr: 'مصرف الإمارات المركزي',     country: 'AE', sector: 'Banking',    sectorCoupling: 0.90, countryCoupling: 0.85, dependencies: ['UAE banking system', 'AED peg stability'], responseOwner: 'CBUAE Governor' },
  { id: 'enbd',       name: 'Emirates NBD',               nameAr: 'الإمارات دبي الوطني',       country: 'AE', sector: 'Banking',    sectorCoupling: 0.85, countryCoupling: 0.75, dependencies: ['UAE trade finance', 'CBUAE liquidity'], responseOwner: 'ENBD CEO' },
  { id: 'adnoc',      name: 'ADNOC',                     nameAr: 'أدنوك',                     country: 'AE', sector: 'OilGas',     sectorCoupling: 0.90, countryCoupling: 0.85, dependencies: ['Hormuz transit', 'Fujairah pipeline', 'Asian crude demand'], responseOwner: 'ADNOC CEO' },
  { id: 'dpworld',    name: 'DP World',                   nameAr: 'موانئ دبي العالمية',         country: 'AE', sector: 'OilGas',     sectorCoupling: 0.80, countryCoupling: 0.70, dependencies: ['Global shipping lanes', 'Port throughput', 'Container demand'], responseOwner: 'DP World CEO' },
  { id: 'mof_ae',     name: 'Ministry of Finance (UAE)',   nameAr: 'وزارة المالية',             country: 'AE', sector: 'Government', sectorCoupling: 0.85, countryCoupling: 0.90, dependencies: ['Federal budget', 'Emirate-level reserves'], responseOwner: 'Minister of Finance' },
  { id: 'emaar',      name: 'Emaar Properties',           nameAr: 'إعمار العقارية',            country: 'AE', sector: 'RealEstate', sectorCoupling: 0.80, countryCoupling: 0.65, dependencies: ['Dubai property demand', 'Foreign capital inflows'], responseOwner: 'Emaar CEO' },

  // ── Kuwait ──
  { id: 'cbk',        name: 'Central Bank of Kuwait',     nameAr: 'بنك الكويت المركزي',        country: 'KW', sector: 'Banking',    sectorCoupling: 0.90, countryCoupling: 0.85, dependencies: ['Kuwait banking system', 'KD peg stability'], responseOwner: 'CBK Governor' },
  { id: 'kpc',        name: 'Kuwait Petroleum Corp',      nameAr: 'مؤسسة البترول الكويتية',    country: 'KW', sector: 'OilGas',     sectorCoupling: 0.90, countryCoupling: 0.85, dependencies: ['Global crude price', 'OPEC quota', 'Hormuz transit'], responseOwner: 'KPC CEO' },
  { id: 'mof_kw',     name: 'Ministry of Finance (KWT)',   nameAr: 'وزارة المالية',             country: 'KW', sector: 'Government', sectorCoupling: 0.90, countryCoupling: 0.95, dependencies: ['Oil revenue', 'Future Generations Fund', 'Public sector payroll'], responseOwner: 'Minister of Finance' },
  { id: 'gig_kw',     name: 'Gulf Insurance Group',       nameAr: 'مجموعة الخليج للتأمين',     country: 'KW', sector: 'Insurance',  sectorCoupling: 0.75, countryCoupling: 0.65, dependencies: ['GCC reinsurance market', 'Marine cargo lines'], responseOwner: 'GIG CEO' },

  // ── Qatar ──
  { id: 'qcb',        name: 'Qatar Central Bank',         nameAr: 'مصرف قطر المركزي',          country: 'QA', sector: 'Banking',    sectorCoupling: 0.90, countryCoupling: 0.85, dependencies: ['Qatar banking system', 'QAR peg stability'], responseOwner: 'QCB Governor' },
  { id: 'qe',         name: 'QatarEnergy',                nameAr: 'قطر للطاقة',                country: 'QA', sector: 'OilGas',     sectorCoupling: 0.95, countryCoupling: 0.90, dependencies: ['LNG production', 'Asian LNG demand', 'Hormuz transit'], responseOwner: 'QatarEnergy CEO' },
  { id: 'qia',        name: 'Qatar Investment Authority',  nameAr: 'جهاز قطر للاستثمار',        country: 'QA', sector: 'Government', sectorCoupling: 0.80, countryCoupling: 0.90, dependencies: ['Global portfolio allocation', 'LNG revenue inflows'], responseOwner: 'QIA CEO' },

  // ── Bahrain ──
  { id: 'cbb',        name: 'Central Bank of Bahrain',    nameAr: 'مصرف البحرين المركزي',      country: 'BH', sector: 'Banking',    sectorCoupling: 0.90, countryCoupling: 0.90, dependencies: ['Bahrain banking sector', 'Saudi GCC support'], responseOwner: 'CBB Governor' },
  { id: 'mof_bh',     name: 'Ministry of Finance (BHR)',   nameAr: 'وزارة المالية',             country: 'BH', sector: 'Government', sectorCoupling: 0.90, countryCoupling: 0.95, dependencies: ['Oil revenue', 'GCC fiscal support package', 'Debt service'], responseOwner: 'Minister of Finance' },
  { id: 'bapco',      name: 'BAPCO Energies',             nameAr: 'شركة نفط البحرين',          country: 'BH', sector: 'OilGas',     sectorCoupling: 0.85, countryCoupling: 0.80, dependencies: ['Saudi crude supply via pipeline', 'Refining margins'], responseOwner: 'BAPCO CEO' },

  // ── Oman ──
  { id: 'cbo',        name: 'Central Bank of Oman',       nameAr: 'البنك المركزي العماني',     country: 'OM', sector: 'Banking',    sectorCoupling: 0.90, countryCoupling: 0.85, dependencies: ['Oman banking system', 'OMR peg stability'], responseOwner: 'CBO Governor' },
  { id: 'oci',        name: 'OQ (Oman Oil)',              nameAr: 'أوكيو',                     country: 'OM', sector: 'OilGas',     sectorCoupling: 0.90, countryCoupling: 0.85, dependencies: ['Crude production', 'Hormuz transit', 'Duqm refinery'], responseOwner: 'OQ CEO' },
  { id: 'mof_om',     name: 'Ministry of Finance (OMN)',   nameAr: 'وزارة المالية',             country: 'OM', sector: 'Government', sectorCoupling: 0.90, countryCoupling: 0.95, dependencies: ['Oil revenue', 'Oman Vision 2040', 'External debt service'], responseOwner: 'Minister of Finance' },
  { id: 'sohar_port', name: 'Port of Sohar',              nameAr: 'ميناء صحار',                country: 'OM', sector: 'OilGas',     sectorCoupling: 0.70, countryCoupling: 0.65, dependencies: ['Gulf shipping lanes', 'Industrial zone demand'], responseOwner: 'Sohar Port CEO' },
];

/* ── Computation ── */

export function classifyExposure(exposure: number): ExposureLevel {
  if (exposure < 0.15) return 'minimal';
  if (exposure < 0.35) return 'moderate';
  if (exposure < 0.55) return 'elevated';
  if (exposure < 0.75) return 'high';
  return 'critical';
}

export function classifyRisk(exposure: number, sectorStress: number): RiskClassification {
  const composite = exposure * 0.6 + sectorStress * 0.4;
  if (composite < 0.15) return 'monitored';
  if (composite < 0.35) return 'guarded';
  if (composite < 0.55) return 'elevated';
  if (composite < 0.75) return 'severe';
  return 'critical';
}

function deriveResponseStatus(exposure: number, t: number): ResponseStatus {
  if (exposure < 0.2) return 'awaiting';
  if (t < 0.3) return 'awaiting';
  if (t < 0.7) return 'active';
  if (exposure > 0.6 && t > 0.7) return 'overdue';
  return 'executed';
}

/**
 * Compute exposure state for a single entity.
 */
export function computeEntityExposure(
  entity: EntityDefinition,
  countryState: CountryMacroState,
  sectorState: SectorState,
  t: number,
): EntityExposureState {
  // Entity exposure = blend of country macro stress and sector-specific stress
  const countryComponent = countryState.compositeStress * entity.countryCoupling;
  const sectorComponent = sectorState.stress * entity.sectorCoupling;
  const exposure = Math.min(1, countryComponent * 0.45 + sectorComponent * 0.55);

  return {
    entityId: entity.id,
    name: entity.name,
    country: entity.country,
    sector: entity.sector,
    exposure,
    level: classifyExposure(exposure),
    riskClassification: classifyRisk(exposure, sectorState.stress),
    responseStatus: deriveResponseStatus(exposure, t),
    driver: sectorState.transmissionSource,
    dependencies: entity.dependencies,
  };
}

/**
 * Compute all entity exposure states.
 */
export function computeAllEntityExposures(
  countryStates: CountryMacroState[],
  sectorStates: SectorState[],
  t: number,
): EntityExposureState[] {
  const countryMap = new Map(countryStates.map(cs => [cs.countryCode, cs]));
  const sectorMap = new Map(sectorStates.map(ss => [ss.sector, ss]));

  return ENTITY_REGISTRY.map((entity) => {
    const cs = countryMap.get(entity.country);
    const ss = sectorMap.get(entity.sector);
    if (!cs || !ss) {
      return {
        entityId: entity.id, name: entity.name, country: entity.country,
        sector: entity.sector, exposure: 0, level: 'minimal' as ExposureLevel,
        riskClassification: 'monitored' as RiskClassification,
        responseStatus: 'awaiting' as ResponseStatus,
        driver: 'No data', dependencies: entity.dependencies,
      };
    }
    return computeEntityExposure(entity, cs, ss, t);
  });
}
