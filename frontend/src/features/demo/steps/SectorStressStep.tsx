'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Flame,
  Landmark,
  Shield,
  Smartphone,
  Building2,
  Building,
  TrendingUp,
  AlertCircle,
  Zap,
} from 'lucide-react';
import { DemoStepProps } from '../DemoStepRenderer';
import { getScenario } from '../data/demo-scenario';

const ICON_MAP: Record<string, React.ElementType> = {
  'Oil & Gas': Flame,
  Banking: Landmark,
  Insurance: Shield,
  'Financial Flows': Smartphone,
  'Real Estate': Building2,
  Government: Building,
};

const RISK_THEME: Record<string, { accent: string; bg: string; text: string; iconBg: string; barBg: string }> = {
  CRITICAL: {
    accent: 'from-red-600 to-red-700',
    bg: 'bg-red-50',
    text: 'text-red-900',
    iconBg: 'bg-red-100',
    barBg: 'bg-red-200',
  },
  ELEVATED: {
    accent: 'from-orange-600 to-orange-700',
    bg: 'bg-orange-50',
    text: 'text-orange-900',
    iconBg: 'bg-orange-100',
    barBg: 'bg-orange-200',
  },
  MODERATE: {
    accent: 'from-amber-600 to-amber-700',
    bg: 'bg-amber-50',
    text: 'text-amber-900',
    iconBg: 'bg-amber-100',
    barBg: 'bg-amber-200',
  },
  LOW: {
    accent: 'from-blue-600 to-blue-700',
    bg: 'bg-blue-50',
    text: 'text-blue-900',
    iconBg: 'bg-blue-100',
    barBg: 'bg-blue-200',
  },
  NOMINAL: {
    accent: 'from-slate-600 to-slate-700',
    bg: 'bg-slate-50',
    text: 'text-slate-900',
    iconBg: 'bg-slate-100',
    barBg: 'bg-slate-200',
  },
};

const stressToLevel = (stress: number): string => {
  if (stress >= 0.75) return 'CRITICAL';
  if (stress >= 0.55) return 'ELEVATED';
  if (stress >= 0.35) return 'MODERATE';
  if (stress >= 0.15) return 'LOW';
  return 'NOMINAL';
};

interface SectorCardProps {
  name: string;
  icon: string;
  currentStress: number;
  topDriver: string;
  secondOrderRisk: string;
  confidenceBand: string;
  recommendedLever: string;
  isCompact: boolean;
  simStress?: number;
}

const SectorCard: React.FC<SectorCardProps> = ({
  name,
  icon,
  currentStress,
  topDriver,
  secondOrderRisk,
  confidenceBand,
  recommendedLever,
  isCompact,
  simStress,
}) => {
  const displayStress = simStress !== undefined ? simStress : currentStress;
  const riskLevel = stressToLevel(displayStress);
  const theme = RISK_THEME[riskLevel];
  const IconComponent = ICON_MAP[icon] || Zap;
  const delta = simStress !== undefined ? simStress - currentStress : 0;
  const deltaSign = delta > 0 ? '+' : '';

  if (isCompact) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`${theme.bg} border rounded-xl border-slate-200 p-3`}
      >
        <div className="flex items-center gap-3 mb-2">
          <div className={`${theme.iconBg} rounded-lg p-2`}>
            <IconComponent className={`w-4 h-4 ${theme.text}`} />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-slate-900 truncate">{name}</h4>
            <p className={`text-xs ${theme.text}`}>{riskLevel}</p>
          </div>
        </div>
        <div className={`${theme.barBg} h-2 rounded-full overflow-hidden`}>
          <div
            className={`h-full bg-gradient-to-r ${theme.accent}`}
            style={{ width: `${Math.min(displayStress * 100, 100)}%` }}
          />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`${theme.bg} border rounded-xl border-slate-200 p-4`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className={`${theme.iconBg} rounded-lg p-2.5 flex-shrink-0`}>
            <IconComponent className={`w-5 h-5 ${theme.text}`} />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-slate-900">{name}</h3>
            <p className={`text-xs ${theme.text}`}>{riskLevel}</p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-600">Stress Level</span>
            {delta !== 0 && (
              <span className={delta > 0 ? 'text-red-600' : 'text-emerald-600'} style={{ fontSize: '0.75rem' }}>
                {deltaSign}{(delta * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <div className={`${theme.barBg} h-2.5 rounded-full overflow-hidden`}>
            <div
              className={`h-full bg-gradient-to-r ${theme.accent}`}
              style={{ width: `${Math.min(displayStress * 100, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>{displayStress.toFixed(2)}</span>
            <span>Confidence: {confidenceBand}</span>
          </div>
        </div>

        <div className="border-t border-slate-300 pt-2">
          <p className="text-xs font-medium text-slate-600 mb-1">Primary Driver</p>
          <p className="text-sm text-slate-800">{topDriver}</p>
        </div>

        <div>
          <p className="text-xs font-medium text-slate-600 mb-1">Second-Order Risk</p>
          <p className="text-sm text-slate-800">{secondOrderRisk}</p>
        </div>

        <div className="bg-white rounded-lg p-2 border border-slate-200">
          <div className="flex items-start gap-2">
            <Zap className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-600">Recommended Lever</p>
              <p className="text-sm text-slate-800">{recommendedLever}</p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export const SectorStressStep: React.FC<DemoStepProps> = ({
  onPause,
  activeRole,
  sim,
  scenarioId,
}) => {
  const scenario = getScenario(scenarioId);

  if (!scenario) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        Scenario not found
      </div>
    );
  }

  const primaryIndices = scenario.primarySectors;
  const secondaryIndices = scenario.secondarySectors;

  const primarySectorsData = primaryIndices.map((idx) => ({ sector: scenario.sectors[idx], sectorIdx: idx }));
  const secondarySectorsData = secondaryIndices.map((idx) => ({ sector: scenario.sectors[idx], sectorIdx: idx }));

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-full flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Sector Impact Assessment</h2>
          <p className="text-slate-600 text-sm mt-1">Current stress levels across economic sectors</p>
        </div>
        <button
          onClick={onPause}
          className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition"
        >
          Pause
        </button>
      </div>

      {/* Primary Sectors */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <h3 className="font-semibold text-slate-900">Critical Sectors</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {primarySectorsData.map(({ sector, sectorIdx }, idx) => (
            <SectorCard
              key={`primary-${idx}`}
              name={sector.name}
              icon={sector.icon}
              currentStress={sector.currentStress}
              topDriver={sector.topDriver}
              secondOrderRisk={sector.secondOrderRisk}
              confidenceBand={sector.confidenceBand}
              recommendedLever={sector.recommendedLever}
              isCompact={false}
              simStress={
                sim && sim.decisionsActivated > 0 && sim.sectorStress
                  ? sim.sectorStress[sectorIdx]
                  : undefined
              }
            />
          ))}
        </div>
      </div>

      {/* Secondary Sectors */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-amber-600" />
          <h3 className="font-semibold text-slate-900">Secondary Exposure</h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {secondarySectorsData.map(({ sector, sectorIdx }, idx) => (
            <SectorCard
              key={`secondary-${idx}`}
              name={sector.name}
              icon={sector.icon}
              currentStress={sector.currentStress}
              topDriver={sector.topDriver}
              secondOrderRisk={sector.secondOrderRisk}
              confidenceBand={sector.confidenceBand}
              recommendedLever={sector.recommendedLever}
              isCompact={true}
              simStress={
                sim && sim.decisionsActivated > 0 && sim.sectorStress
                  ? sim.sectorStress[sectorIdx]
                  : undefined
              }
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};
