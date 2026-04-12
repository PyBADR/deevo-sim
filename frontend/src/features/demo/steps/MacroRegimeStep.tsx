"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingDown, TrendingUp } from "lucide-react";
import { getScenario } from "../data/demo-scenario";
import type { DemoStepProps } from "../DemoStepRenderer";

const SEVERITY_COLORS: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  NOMINAL:  { bg: "#F8FAFC", border: "#E2E8F0", text: "#334155", badge: "#64748B" },
  LOW:      { bg: "#F0FDF4", border: "#DCFCE7", text: "#166534", badge: "#22C55E" },
  GUARDED:  { bg: "#FFFBEB", border: "#FEF3C7", text: "#B45309", badge: "#F59E0B" },
  ELEVATED: { bg: "#FEF2F2", border: "#FECACA", text: "#991B1B", badge: "#EF4444" },
  HIGH:     { bg: "#FEF2F2", border: "#FECACA", text: "#7F1D1D", badge: "#DC2626" },
  SEVERE:   { bg: "#7F1D1D", border: "#450A0A", text: "#FEF2F2", badge: "#991B1B" },
};

export function MacroRegimeStep({ scenarioId }: DemoStepProps) {
  const scenario = getScenario(scenarioId);
  const { macroRegime } = scenario;
  const [visibleSignals, setVisibleSignals] = useState(-1);

  useEffect(() => {
    setVisibleSignals(-1);
    const timers: ReturnType<typeof setTimeout>[] = [];
    macroRegime.signals.forEach((_, i) => {
      timers.push(setTimeout(() => setVisibleSignals(i), 800 + i * 150));
    });
    return () => timers.forEach(clearTimeout);
  }, [macroRegime.signals]);

  const colors = SEVERITY_COLORS[macroRegime.severityTier] || SEVERITY_COLORS.NOMINAL;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8 py-12">
      {/* Severity badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-6"
      >
        <div
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border"
          style={{ background: colors.bg, borderColor: colors.border }}
        >
          <span className="text-xs font-bold tracking-wide" style={{ color: colors.text }}>
            MACRO STATE
          </span>
          <span
            className="text-xs font-bold px-2.5 py-1 rounded-md"
            style={{ background: colors.badge, color: "#FFF" }}
          >
            {macroRegime.severityTier}
          </span>
        </div>
      </motion.div>

      {/* System state headline */}
      <motion.h2
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="text-3xl md:text-4xl font-bold text-center text-slate-900 mb-2 max-w-3xl"
      >
        {macroRegime.systemState}
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-400 text-center max-w-xl mb-10"
      >
        {macroRegime.scenarioType}
      </motion.p>

      {/* Metrics grid — 2x2 */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        className="w-full max-w-3xl mb-12"
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Exposure Points", value: `${macroRegime.regimeMetrics.exposurePoints}/${macroRegime.regimeMetrics.totalPoints}` },
            { label: "Time Horizon", value: macroRegime.regimeMetrics.timeHorizon },
            { label: "Confidence", value: `${Math.round(macroRegime.regimeMetrics.confidence * 100)}%` },
            { label: "Est. Exposure", value: macroRegime.regimeMetrics.estimatedExposure },
          ].map((metric, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 + i * 0.08, duration: 0.4 }}
              className="p-4 rounded-lg border bg-white border-slate-200"
            >
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-[0.08em] mb-1.5">
                {metric.label}
              </p>
              <p className="text-base font-bold text-slate-900">{metric.value}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Signals table */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7, duration: 0.4 }}
        className="w-full max-w-3xl"
      >
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.08em] mb-4">
          Macro Signals
        </p>
        <div className="rounded-lg border border-slate-200 overflow-hidden bg-white">
          {macroRegime.signals.map((signal, i) => (
            <AnimatePresence key={i}>
              {visibleSignals >= i && (
                <motion.div
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.3 }}
                  className={`flex items-center justify-between px-5 py-3.5 border-b border-slate-100 ${
                    i === visibleSignals ? "bg-slate-50" : ""
                  }`}
                >
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-slate-900">
                      {signal.indicator}
                    </p>
                  </div>
                  <div className="flex items-center gap-4 ml-4">
                    <div className="text-right">
                      <p className="text-base font-bold text-slate-900 tabular-nums">
                        {signal.value}
                      </p>
                    </div>
                    <div
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-md"
                      style={{
                        background: signal.direction === "up" ? "#FEE2E2" : "#F0FDF4",
                      }}
                    >
                      {signal.direction === "up" ? (
                        <TrendingUp size={14} className="text-red-600" />
                      ) : (
                        <TrendingDown size={14} className="text-emerald-600" />
                      )}
                      <span
                        className="text-xs font-semibold"
                        style={{
                          color: signal.direction === "up" ? "#DC2626" : "#16A34A",
                        }}
                      >
                        {signal.change}
                      </span>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
