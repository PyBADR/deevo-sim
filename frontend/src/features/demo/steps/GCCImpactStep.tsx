"use client";

/**
 * Step 5 — GCC Impact (Phase 2 polish)
 *
 * Cleaner, more visual country cards.
 * Hero loss number, tighter layout, subtle stress gradient.
 */

import React from "react";
import { motion } from "framer-motion";
import { MapPin } from "lucide-react";
import { demoScenario } from "../data/demo-scenario";

const LEVEL_COLORS: Record<string, { bar: string; badge: string; badgeText: string }> = {
  CRITICAL: { bar: "#EF4444", badge: "#FEF2F2", badgeText: "#B91C1C" },
  ELEVATED: { bar: "#F59E0B", badge: "#FFFBEB", badgeText: "#B45309" },
  MODERATE: { bar: "#EAB308", badge: "#FEFCE8", badgeText: "#A16207" },
  LOW:      { bar: "#22C55E", badge: "#F0FDF4", badgeText: "#15803D" },
  NOMINAL:  { bar: "#94A3B8", badge: "#F8FAFC", badgeText: "#64748B" },
};

export function GCCImpactStep() {
  const { countries } = demoScenario;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-5"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-50 border border-slate-200">
          <MapPin size={13} className="text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 tracking-wide">
            GCC IMPACT ASSESSMENT
          </span>
        </span>
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="text-h2 md:text-h1 text-center text-slate-900 mb-2"
      >
        Impact across the GCC
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-400 text-center max-w-md mb-10"
      >
        Estimated economic exposure within the critical window
      </motion.p>

      {/* Country cards — 3x2 grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3.5 w-full max-w-[820px]">
        {countries.map((c, i) => {
          const colors = LEVEL_COLORS[c.impactLevel] ?? LEVEL_COLORS.NOMINAL;

          return (
            <motion.div
              key={c.country}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.08, duration: 0.4 }}
              className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-ds hover:shadow-ds-md transition-shadow"
            >
              {/* Top bar — country + badge */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <span className="text-base leading-none">{flagEmoji(c.flag)}</span>
                  <span className="text-[13px] font-bold text-slate-800">{c.country}</span>
                </div>
                <span
                  className="px-2 py-[2px] rounded text-[9px] font-bold uppercase tracking-wider"
                  style={{ background: colors.badge, color: colors.badgeText }}
                >
                  {c.impactLevel}
                </span>
              </div>

              <div className="px-4 py-3">
                {/* Hero loss number */}
                <p className="text-2xl font-bold text-slate-900 tabular-nums leading-none mb-1">
                  {c.estimatedLoss}
                </p>
                <p className="text-[10px] text-slate-400 font-medium mb-3">
                  {c.topSector}
                </p>

                {/* Stress bar */}
                <div className="flex items-center gap-2 mb-3">
                  <div className="flex-1 h-[5px] bg-slate-100 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${c.sectorStress * 100}%` }}
                      transition={{ delay: 0.5 + i * 0.08, duration: 0.6, ease: "easeOut" }}
                      className="h-full rounded-full"
                      style={{ background: colors.bar }}
                    />
                  </div>
                  <span className="text-[10px] font-bold text-slate-500 tabular-nums w-7 text-right">
                    {Math.round(c.sectorStress * 100)}
                  </span>
                </div>

                {/* Driver */}
                <p className="text-[10px] text-slate-400 leading-snug">
                  {c.driver}
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function flagEmoji(code: string): string {
  return code
    .toUpperCase()
    .split("")
    .map((c) => String.fromCodePoint(0x1f1e6 + c.charCodeAt(0) - 65))
    .join("");
}
