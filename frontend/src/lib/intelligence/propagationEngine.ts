/**
 * Impact Observatory | مرصد الأثر — Propagation Engine
 *
 * Upgrades propagation from static text to live computational logic.
 *
 * Traverses: Country → Sector → Entity
 * Simulates cascading effects over time.
 * Updates stress values as pressure transmits through the system.
 *
 * This engine takes the raw country/sector/entity states and
 * applies cross-cutting propagation effects:
 *   - Inter-country contagion (GCC spillover)
 *   - Cross-sector amplification (banking stress → real estate)
 *   - Entity-level dependency cascades
 */

import type { CountryMacroState, GCCCountry } from './countryState';
import type { SectorState, GCCSector } from './sectorState';
import type { EntityExposureState } from './entityState';

/* ── Types ── */

export interface PropagationResult {
  /** Country states after contagion */
  countries: CountryMacroState[];
  /** Sector states after cross-sector amplification */
  sectors: SectorState[];
  /** Entity states after dependency cascades */
  entities: EntityExposureState[];
  /** Contagion events that occurred this tick */
  contagionLog: ContagionEvent[];
}

export interface ContagionEvent {
  /** Type of propagation */
  type: 'country_spillover' | 'cross_sector' | 'entity_cascade';
  /** Source of the contagion */
  source: string;
  /** Target affected */
  target: string;
  /** Magnitude of the effect (0–1) */
  magnitude: number;
  /** Description */
  description: string;
}

/* ── Inter-Country Contagion Matrix ──
   How much stress in one country spills into another.
   Asymmetric: Saudi stress affects Bahrain more than Bahrain affects Saudi.
*/

const COUNTRY_CONTAGION: Record<GCCCountry, Partial<Record<GCCCountry, number>>> = {
  SA: { AE: 0.25, KW: 0.20, QA: 0.15, BH: 0.35, OM: 0.20 },
  AE: { SA: 0.20, KW: 0.15, QA: 0.15, BH: 0.25, OM: 0.20 },
  KW: { SA: 0.15, AE: 0.10, QA: 0.10, BH: 0.15, OM: 0.10 },
  QA: { SA: 0.10, AE: 0.15, KW: 0.10, BH: 0.10, OM: 0.10 },
  BH: { SA: 0.10, AE: 0.10, KW: 0.05, QA: 0.05, OM: 0.05 },
  OM: { SA: 0.10, AE: 0.15, KW: 0.05, QA: 0.05, BH: 0.10 },
};

/* ── Cross-Sector Amplification ──
   How stress in one sector amplifies another.
   Banking stress amplifies real estate; oil & gas amplifies government.
*/

const CROSS_SECTOR_AMP: Partial<Record<GCCSector, Partial<Record<GCCSector, number>>>> = {
  Banking:    { RealEstate: 0.30, Fintech: 0.25, Insurance: 0.20 },
  OilGas:     { Government: 0.35, Banking: 0.20 },
  Government: { Banking: 0.15, Insurance: 0.10 },
  Insurance:  { Banking: 0.10 },
  RealEstate: { Banking: 0.15 },
};

/* ── Computation ── */

/**
 * Apply inter-country contagion: high-stress countries
 * push additional pressure onto their neighbors.
 */
function applyCountryContagion(
  countries: CountryMacroState[],
  log: ContagionEvent[],
): CountryMacroState[] {
  const countryMap = new Map(countries.map(c => [c.countryCode, c]));
  const adjustments: Map<GCCCountry, number> = new Map();

  for (const source of countries) {
    // Only propagate if source is under meaningful stress
    if (source.compositeStress < 0.25) continue;

    const spillovers = COUNTRY_CONTAGION[source.countryCode] ?? {};
    for (const [targetCode, coefficient] of Object.entries(spillovers)) {
      const spillover = source.compositeStress * (coefficient as number) * 0.3;
      if (spillover < 0.02) continue;

      const current = adjustments.get(targetCode as GCCCountry) ?? 0;
      adjustments.set(targetCode as GCCCountry, current + spillover);

      log.push({
        type: 'country_spillover',
        source: source.name,
        target: countryMap.get(targetCode as GCCCountry)?.name ?? targetCode,
        magnitude: spillover,
        description: `${source.name} macro stress (${(source.compositeStress * 100).toFixed(0)}%) transmitting to ${countryMap.get(targetCode as GCCCountry)?.name ?? targetCode}`,
      });
    }
  }

  // Apply adjustments
  return countries.map(c => {
    const adj = adjustments.get(c.countryCode) ?? 0;
    if (adj === 0) return c;
    return {
      ...c,
      compositeStress: Math.min(1, c.compositeStress + adj),
    };
  });
}

/**
 * Apply cross-sector amplification: high-stress sectors
 * push additional pressure onto dependent sectors.
 */
function applySectorAmplification(
  sectors: SectorState[],
  log: ContagionEvent[],
): SectorState[] {
  const sectorMap = new Map(sectors.map(s => [s.sector, s]));
  const adjustments: Map<GCCSector, number> = new Map();

  for (const source of sectors) {
    if (source.stress < 0.25) continue;

    const amps = CROSS_SECTOR_AMP[source.sector] ?? {};
    for (const [targetSector, coefficient] of Object.entries(amps)) {
      const amplification = source.stress * (coefficient as number) * 0.25;
      if (amplification < 0.02) continue;

      const current = adjustments.get(targetSector as GCCSector) ?? 0;
      adjustments.set(targetSector as GCCSector, current + amplification);

      log.push({
        type: 'cross_sector',
        source: source.label,
        target: sectorMap.get(targetSector as GCCSector)?.label ?? targetSector,
        magnitude: amplification,
        description: `${source.label} stress amplifying ${sectorMap.get(targetSector as GCCSector)?.label ?? targetSector} pressure`,
      });
    }
  }

  return sectors.map(s => {
    const adj = adjustments.get(s.sector) ?? 0;
    if (adj === 0) return s;
    const newStress = Math.min(1, s.stress + adj);
    return {
      ...s,
      stress: newStress,
      level: newStress < 0.15 ? 'nominal'
        : newStress < 0.35 ? 'elevated'
          : newStress < 0.55 ? 'high'
            : newStress < 0.75 ? 'severe'
              : 'critical',
    };
  });
}

/**
 * Apply entity-level dependency cascades:
 * if an entity's dependency is under high exposure,
 * the entity's own exposure increases.
 */
function applyEntityCascades(
  entities: EntityExposureState[],
  log: ContagionEvent[],
): EntityExposureState[] {
  const entityMap = new Map(entities.map(e => [e.entityId, e]));
  const nameMap = new Map(entities.map(e => [e.name, e]));

  return entities.map(entity => {
    let cascadeBoost = 0;

    for (const dep of entity.dependencies) {
      // Try to find the dependency in our entity registry
      const depEntity = nameMap.get(dep) ??
        entities.find(e => dep.toLowerCase().includes(e.name.toLowerCase()));

      if (depEntity && depEntity.exposure > 0.4) {
        const boost = depEntity.exposure * 0.15;
        cascadeBoost += boost;

        if (boost > 0.03) {
          log.push({
            type: 'entity_cascade',
            source: depEntity.name,
            target: entity.name,
            magnitude: boost,
            description: `${entity.name} exposure rising due to dependency on ${depEntity.name}`,
          });
        }
      }
    }

    if (cascadeBoost === 0) return entity;

    const newExposure = Math.min(1, entity.exposure + cascadeBoost);
    return {
      ...entity,
      exposure: newExposure,
      level: newExposure < 0.15 ? 'minimal'
        : newExposure < 0.35 ? 'moderate'
          : newExposure < 0.55 ? 'elevated'
            : newExposure < 0.75 ? 'high'
              : 'critical',
    };
  });
}

/**
 * Run the full propagation engine.
 * Takes raw computed states and applies all cascading effects.
 */
export function runPropagation(
  countries: CountryMacroState[],
  sectors: SectorState[],
  entities: EntityExposureState[],
): PropagationResult {
  const contagionLog: ContagionEvent[] = [];

  const propagatedCountries = applyCountryContagion(countries, contagionLog);
  const propagatedSectors = applySectorAmplification(sectors, contagionLog);
  const propagatedEntities = applyEntityCascades(entities, contagionLog);

  return {
    countries: propagatedCountries,
    sectors: propagatedSectors,
    entities: propagatedEntities,
    contagionLog,
  };
}
