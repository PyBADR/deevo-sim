'use client';

import { motion } from 'framer-motion';
import { Landmark, TrendingDown, CheckCircle, AlertCircle } from 'lucide-react';
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

export function BankingLayerStep({ scenarioId, onPause, sim, onToggleDecision }: DemoStepProps) {
  const scenario = getScenario(scenarioId as ScenarioId);
  const banking = scenario.bankingLayer;

  const displayStress =
    sim && sim.decisionsActivated > 0 ? sim.sectorStress[banking.sectorIndex] : banking.stressIndex;

  const severity = stressToLevel(displayStress);
  const theme = RISK_THEME[severity];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.1 },
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
              BANKING SECTOR
            </div>
            <h2 className="text-2xl font-semibold text-slate-900">{banking.headline}</h2>
            <p className="text-sm text-slate-600 mt-2">
              Regional financial system under stress from shock transmission
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

      {/* Main Stress Card */}
      <motion.div
        variants={itemVariants}
        className="rounded-lg border-2 border-slate-200 bg-[#FAFAFA] p-6"
        style={{
          borderLeftWidth: '6px',
          borderLeftColor: {
            CRITICAL: '#b91c1c',
            ELEVATED: '#ea580c',
            MODERATE: '#b45309',
            LOW: '#2563eb',
            NOMINAL: '#64748b',
          }[severity],
        }}
      >
        {/* Stress Indicator */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-lg ${theme.bg}`}>
              <Landmark className={`h-6 w-6 ${theme.accent}`} />
            </div>
            <div>
              <p className="text-xs text-slate-600 font-medium">Banking Sector Stress</p>
              <h3 className="text-xl font-bold text-slate-900">
                {(displayStress * 100).toFixed(1)}%
              </h3>
            </div>
          </div>
          <div className={`px-4 py-2 rounded-lg text-sm font-semibold ${theme.bg} ${theme.accent}`}>
            {severity}
          </div>
        </div>

        {/* Stress Bar */}
        <div className="mb-6">
          <div className="h-3 rounded-full bg-slate-200 overflow-hidden">
            <div
              className="h-full transition-all duration-500"
              style={{
                width: `${displayStress * 100}%`,
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
      </motion.div>

      {/* Metrics Grid */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        {banking.metrics.map((metric, idx) => {
          const metricSeverity = metric.severity;
          const metricTheme = RISK_THEME[metricSeverity] || RISK_THEME.NOMINAL;

          return (
            <div
              key={idx}
              className="rounded-lg border border-slate-200 bg-[#FAFAFA] p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-sm font-medium text-slate-600">{metric.label}</span>
                <span className={`text-xs font-semibold ${metricTheme.accent}`}>
                  {metricSeverity}
                </span>
              </div>
              <p className="text-lg font-bold text-slate-900 mb-2">{metric.value}</p>
              <p className="text-xs text-slate-600">{metric.detail}</p>
            </div>
          );
        })}
      </motion.div>

      {/* Transmission Path */}
      <motion.div
        variants={itemVariants}
        className="rounded-lg border border-slate-200 bg-[#FAFAFA] p-5"
      >
        <div className="mb-4">
          <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-3">
            Transmission Path
          </p>
          <div className="space-y-3">
            {banking.transmissionPath.map((step, idx) => (
              <div key={idx} className="flex items-start gap-3">
                <div className="flex items-center justify-center h-6 w-6 rounded-full bg-slate-200 flex-shrink-0 mt-0.5">
                  <span className="text-xs font-semibold text-slate-600">{idx + 1}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700">{step}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-slate-200 my-4" />

        {/* Risk Assessment */}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-start gap-2">
            <TrendingDown className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
            <div className="text-xs">
              <p className="text-slate-600 font-medium">Liquidity Risk</p>
              <p className="text-slate-700 mt-1">Elevated due to capital outflows and funding constraints</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="text-xs">
              <p className="text-slate-600 font-medium">Solvency Pressure</p>
              <p className="text-slate-700 mt-1">Deteriorating asset quality and earnings compression</p>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
