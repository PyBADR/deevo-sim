"use client";

/**
 * Step 6 — Sector Impact (Phase 2 polish)
 *
 * All 6 sectors with:
 *   Signal → Impact → Interpretation
 *
 * Cleaner visual hierarchy. No tables. No dense text.
 * Signal + interpretation only with risk accent.
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
} from "lucide-react";
import { demoScenario } from "../data/demo-scenario";

const ICON_MAP: Record<string, React.ElementType> = {
  fuel: Flame,
  landmark: Landmark,
  shield: Shield,
  smartphone: Smartphone,
  building: Building2,
  university: Building,
};

const RISK_THEME: Record<string, { accent: string; bg: string; text: string; iconBg: string }> = {
  CRITICAL: { accent: "#EF4444", bg: "#FEF2F2", text: "#991B1B", iconBg: "rgba(239,68,68,0.08)" },
  ELEVATED: { accent: "#F59E0B", bg: "#FFFBEB", text: "#92400E", iconBg: "rgba(245,158,11,0.08)" },
  MODERATE: { accent: "#EAB308", bg: "#FEFCE8", text: "#854D0E", iconBg: "rgba(234,179,8,0.08)" },
  LOW:      { accent: "#22C55E", bg: "#F0FDF4", text: "#166534", iconBg: "rgba(34,197,94,0.08)" },
  NOMINAL:  { accent: "#94A3B8", bg: "#F8FAFC", text: "#475569", iconBg: "rgba(148,163,184,0.08)" },
};

export function SectorImpactStep() {
  const { sectors } = demoScenario;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8 py-14">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-5"
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
        Sector-by-sector analysis
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-400 text-center max-w-md mb-10"
      >
        AI-generated signals and impact interpretation per sector
      </motion.p>

      {/* Sector cards — 3x2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 w-full max-w-[900px]">
        {sectors.map((sector, i) => {
          const Icon = ICON_MAP[sector.icon] ?? Flame;
          const theme = RISK_THEME[sector.riskLevel] ?? RISK_THEME.NOMINAL;

          return (
            <motion.div
              key={sector.name}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 + i * 0.07, duration: 0.4 }}
              className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-ds"
              style={{ borderTopWidth: "3px", borderTopColor: theme.accent }}
            >
              <div className="p-4">
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center"
                      style={{ background: theme.iconBg }}
                    >
                      <Icon size={16} style={{ color: theme.accent }} />
                    </div>
                    <span className="text-[13px] font-bold text-slate-800">{sector.name}</span>
                  </div>
                  <span
                    className="px-2 py-[2px] rounded text-[9px] font-bold uppercase tracking-wider"
                    style={{ background: theme.bg, color: theme.text }}
                  >
                    {sector.riskLevel}
                  </span>
                </div>

                {/* Signal */}
                <div className="mb-2.5">
                  <p className="text-[9px] font-bold text-slate-300 uppercase tracking-[0.15em] mb-0.5">
                    Signal
                  </p>
                  <p className="text-[12px] font-semibold text-slate-700 leading-snug">
                    {sector.signal}
                  </p>
                </div>

                {/* Impact */}
                <div className="mb-2.5">
                  <p className="text-[9px] font-bold text-slate-300 uppercase tracking-[0.15em] mb-0.5">
                    Impact
                  </p>
                  <p className="text-[12px] font-semibold leading-snug" style={{ color: theme.text }}>
                    {sector.impact}
                  </p>
                </div>

                {/* Interpretation — short, not a paragraph */}
                <p className="text-[10px] text-slate-400 leading-relaxed">
                  {sector.explanation}
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
