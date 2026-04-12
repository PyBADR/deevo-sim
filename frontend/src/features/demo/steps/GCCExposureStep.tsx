'use client';

import { motion } from 'framer-motion';
import { TrendingUp, AlertTriangle, DollarSign, Zap } from 'lucide-react';
import { getScenario, ScenarioId } from '../data/demo-scenario';
import { DemoStepProps } from '../DemoStepRenderer';

const RISK_THEME = {
  CRITICAL: { accent: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200' },
  ELEVATED: { accent: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-200' },
  MODERATE: { accent: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' },
  LOW: { accent: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
  NOMINAL: { accent: 'text-slate-600', bg: 'bg-slate-50', border: 'border-slate-200' },
};

function stressToLevel(stress: number): keyof typeof RISK_THEME {
  if (stress >= 0.75) return 'CRITICAL';
  if (stress >= 0.55) return 'ELEVATED';
  if (stress >= 0.35) return 'MODERATE';
  if (stress >= 0.15) return 'LOW';
  return 'NOMINAL';
}

function getCountryFlag(code: string): string {
  const codePoints: Record<string, string> = {
    SA: '🇸🇦',
    AE: '🇦🇪',
    KW: '🇰🇼',
    QA: '🇶🇦',
    BH: '🇧🇭',
    OM: '🇴🇲',
  };
  return codePoints[code] || '🏳️';
}

export function GCCExposureStep({ scenarioId, onPause, sim, onToggleDecision }: DemoStepProps) {
  const scenario = getScenario(scenarioId as ScenarioId);
  const filteredCountries = scenario.countries.filter((c) =>
    scenario.exposureFilter.includes(c.flag)
  );

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.12, delayChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 8 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <motion.div
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="border-b border-slate-200 pb-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="inline-block rounded bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 mb-2">
              COUNTRY EXPOSURE
            </div>
            <h2 className="text-2xl font-semibold text-slate-900">
              GCC Financial Impact by Country
            </h2>
            <p className="text-sm text-slate-600 mt-2">
              Cross-border stress transmission and estimated economic loss
            </p>
          </div>
          {onPause && (
            <button
              onClick={onPause}
              className="text-xs font-medium text-slate-500 hover:text-slate-700 transition"
            >
              Pause
            </button>
          )}
        </div>
      </motion.div>

      {/* 2x2 Grid of Countries */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredCountries.map((country, idx) => {
          const severity = stressToLevel(country.sectorStress);
          const theme = RISK_THEME[severity];

          return (
            <div
              key={country.flag}
              className={`rounded-lg border-2 border-slate-200 p-5 bg-[#FAFAFA] transition ${
                idx % 2 === 0 ? 'md:border-r md:border-slate-300' : ''
              }`}
              style={{
                borderLeftWidth: '4px',
                borderLeftColor: {
                  CRITICAL: '#b91c1c',
                  ELEVATED: '#ea580c',
                  MODERATE: '#b45309',
                  LOW: '#2563eb',
                  NOMINAL: '#64748b',
                }[severity],
              }}
            >
              {/* Country Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getCountryFlag(country.flag)}</span>
                  <div>
                    <h3 className="font-semibold text-slate-900">{country.country}</h3>
                    <p className="text-xs text-slate-500">{country.topSector}</p>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium ${theme.bg} ${theme.accent}`}>
                  {severity}
                </div>
              </div>

              {/* Sector Stress Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-slate-600">Sector Stress</span>
                  <span className="text-xs font-semibold text-slate-900">
                    {(country.sectorStress * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
                  <div
                    className="h-full transition-all duration-500"
                    style={{
                      width: `${country.sectorStress * 100}%`,
                      backgroundColor: {
                        CRITICAL: '#b91c1c',
                        ELEVATED: '#ea580c',
                        MODERATE: '#b45309',
                        LOW: '#2563eb',
                        NOMINAL: '#cbd5e1',
                      }[severity],
                    }}
                  />
                </div>
              </div>

              {/* Loss Impact */}
              <div className="mb-4 p-3 rounded bg-white border border-slate-200">
                <div className="flex items-start gap-2">
                  <DollarSign className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-600">Estimated Loss</p>
                    <p className="text-sm font-semibold text-slate-900 truncate">
                      {country.estimatedLoss}
                    </p>
                  </div>
                </div>
              </div>

              {/* Driver & Channel */}
              <div className="space-y-2 text-xs">
                <div>
                  <p className="text-slate-500 font-medium">Primary Driver</p>
                  <p className="text-slate-700">{country.driver}</p>
                </div>
                <div>
                  <p className="text-slate-500 font-medium">Transmission Channel</p>
                  <p className="text-slate-700">{country.channel}</p>
                </div>
              </div>
            </div>
          );
        })}
      </motion.div>

      {/* Summary Footer */}
      <motion.div
        variants={itemVariants}
        className="rounded-lg border border-slate-200 bg-[#FAFAFA] p-4"
      >
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-slate-700">
            <p className="font-medium text-slate-900 mb-1">Cross-Border Risk</p>
            <p>
              Stress transmission flows through commodity exports, financial settlements, and regional supply networks.
              All four countries show elevated exposure to the initial shock.
            </p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
