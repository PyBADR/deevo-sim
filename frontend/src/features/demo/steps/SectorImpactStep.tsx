"use client";

/**
 * Step 6 — Sector Impact (V2.2: Reactive Stress)
 *
 * Reads sector stress from sim snapshot when available.
 * Falls back to static demoScenario.sectors[].currentStress when sim is undefined.
 * Highlights sectors that were affected by the last decision toggle.
 */

import React from "react";
import { motion } from "framer-motion";
import {
  Flame,
  Landmark,
  Shield,
  Smartphone,
  Building2,
  Building,
  Crosshair,
  GitBranch,
  Gauge,
} from "lucide-react";
import { demoScenario } from "../data/demo-scenario";
import type { DemoStepProps } from "../DemoStepRenderer";

const ICON_MAP: Record<string, React.ElementType> = {
  fuel: Flame,
  landmark: Landmark,
  shield: Shield,
  smartphone: Smartphone,
  building: Building2,
  university: Building,
};

const RISK_THEME: Record<string, { accent: string; bg: string; text: string; iconBg: string; barBg: string }> = {
  CRITICAL: { accent: "#EF4444", bg: "#FEF2F2", text: "#991B1B", iconBg: "rgba(239,68,68,0.08)", barBg: "rgba(239,68,68,0.15)" },
  ELEVATED: { accent: "#F59E0B", bg: "#FFFBEB", text: "#92400E", iconBg: "rgba(245,158,11,0.08)", barBg: "rgba(245,158,11,0.15)" },
  MODERATE: { accent: "#EAB308", bg: "#FEFCE8", text: "#854D0E", iconBg: "rgba(234,179,8,0.08)", barBg: "rgba(234,179,8,0.15)" },
  LOW:      { accent: "#22C55E", bg: "#F0FDF4", text: "#166534", iconBg: "rgba(34,197,94,0.08)", barBg: "rgba(34,197,94,0.15)" },
  NOMINAL:  { accent: "#94A3B8", bg: "#F8FAFC", text: "#475569", iconBg: "rgba(148,163,184,0.08)", barBg: "rgba(148,163,184,0.15)" },
};

/** Derive risk level from numeric stress for display when sim overrides static value */
function stressToLevel(stress: number): string {
  if (stress >= 0.75) return "CRITICAL";
  if (stress >= 0.55) return "ELEVATED";
  if (stress >= 0.35) return "MODERATE";
  if (stress >= 0.15) return "LOW";
  return "NOMINAL";
}

export function SectorImpactStep({ sim }: DemoStepProps) {
  const { sectors } = demoScenario;
  const hasSimData = sim && sim.decisionsActivated > 0;

  return (
    <div className="flex flex-col items-center justify-start min-h-screen px-8 py-10">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-4"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100">
          <span className="text-xs font-semibold text-indigo-600 tracking-wide">
            SECTOR INTELLIGENCE
          </span>
        </span>
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="text-h2 md:text-h1 text-center text-slate-900 mb-2"
      >
        Sector Decision Utility
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-400 text-center max-w-md mb-8"
      >
        {hasSimData
          ? "Stress levels updated based on activated decisions"
          : "Stress, drivers, second-order risk, and recommended levers per sector"}
      </motion.p>

      {/* Sector cards — 3x2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 w-full max-w-[920px]">
        {sectors.map((sector, i) => {
          const Icon = ICON_MAP[sector.icon] ?? Flame;

          // Reactive stress: use sim if any decision activated, else static
          const currentStress = hasSimData ? sim.sectorStress[i] : sector.currentStress;
          const baseStress = sector.currentStress;
          const delta = hasSimData ? currentStress - baseStress : 0;
          const wasAffected = hasSimData && sim.lastAffectedSectors.includes(i);

          // Derive visual risk level from current stress (may differ from static)
          const effectiveRiskLevel = hasSimData ? stressToLevel(currentStress) : sector.riskLevel;
          const theme = RISK_THEME[effectiveRiskLevel] ?? RISK_THEME.NOMINAL;

          return (
            <motion.div
              key={sector.name}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 + i * 0.07, duration: 0.4 }}
              className={`bg-white border rounded-xl overflow-hidden shadow-ds transition-all duration-500 ${
                wasAffected ? "border-blue-300 ring-1 ring-blue-200" : "border-slate-200"
              }`}
              style={{ borderTopWidth: "3px", borderTopColor: theme.accent }}
            >
              <div className="p-3.5">
                {/* Header */}
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-7 h-7 rounded-lg flex items-center justify-center"
                      style={{ background: theme.iconBg }}
                    >
                      <Icon size={14} style={{ color: theme.accent }} />
                    </div>
                    <span className="text-[12px] font-bold text-slate-800">{sector.name}</span>
                  </div>
                  <span
                    className="px-1.5 py-[2px] rounded text-[8px] font-bold uppercase tracking-wider"
                    style={{ background: theme.bg, color: theme.text }}
                  >
                    {effectiveRiskLevel}
                  </span>
                </div>

                {/* Stress bar */}
                <div className="mb-2.5">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[8px] font-bold text-slate-300 uppercase tracking-[0.15em]">
                      Current Stress
                    </span>
                    <div className="flex items-center gap-1.5">
                      <motion.span
                        key={currentStress}
                        initial={{ scale: 1.2 }}
                        animate={{ scale: 1 }}
                        className="text-[10px] font-bold tabular-nums"
                        style={{ color: theme.accent }}
                      >
                        {Math.round(currentStress * 100)}%
                      </motion.span>
                      {/* Delta badge */}
                      {delta !== 0 && (
                        <motion.span
                          initial={{ opacity: 0, x: -4 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={`text-[9px] font-bold tabular-nums ${
                            delta < 0 ? "text-emerald-500" : "text-red-500"
                          }`}
                        >
                          {delta < 0 ? "" : "+"}{Math.round(delta * 100)}
                        </motion.span>
                      )}
                    </div>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ background: theme.barBg }}>
                    <motion.div
                      animate={{ width: `${currentStress * 100}%` }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                      className="h-full rounded-full"
                      style={{ background: theme.accent }}
                    />
                  </div>
                </div>

                {/* Signal */}
                <div className="mb-2">
                  <p className="text-[12px] font-semibold text-slate-700 leading-snug">
                    {sector.signal}
                  </p>
                </div>

                {/* Decision utility rows */}
                <div className="space-y-1.5 pt-2 border-t border-slate-100">
                  <div className="flex items-start gap-1.5">
                    <Crosshair size={10} className="text-slate-300 mt-0.5 flex-shrink-0" />
                    <p className="text-[10px] text-slate-500 leading-snug">
                      <span className="font-semibold text-slate-600">Driver:</span> {sector.topDriver}
                    </p>
                  </div>
                  <div className="flex items-start gap-1.5">
                    <GitBranch size={10} className="text-slate-300 mt-0.5 flex-shrink-0" />
                    <p className="text-[10px] text-slate-500 leading-snug">
                      <span className="font-semibold text-slate-600">2nd-order:</span> {sector.secondOrderRisk}
                    </p>
                  </div>
                  <div className="flex items-start gap-1.5">
                    <Gauge size={10} className="text-slate-300 mt-0.5 flex-shrink-0" />
                    <p className="text-[10px] text-slate-500 leading-snug">
                      <span className="font-semibold text-slate-600">Confidence:</span> {sector.confidenceBand}
                    </p>
                  </div>
                </div>

                {/* Recommended lever */}
                <div className="mt-2 px-2.5 py-2 rounded-lg bg-slate-50 border border-slate-100">
                  <p className="text-[9px] font-bold text-slate-300 uppercase tracking-[0.12em] mb-0.5">
                    Recommended Lever
                  </p>
                  <p className="text-[10px] font-semibold text-slate-700 leading-snug">
                    {sector.recommendedLever}
                  </p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
