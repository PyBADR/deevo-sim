"use client";

/**
 * Step 3 — Shock
 *
 * "Maritime disruption reduces oil transit by 60%"
 * Three KPI blocks showing the initial shock parameters.
 */

import React from "react";
import { motion } from "framer-motion";
import { Zap, Ship, Clock } from "lucide-react";
import { demoScenario } from "../data/demo-scenario";

const ICONS = [Zap, Ship, Clock];

export function ShockStep() {
  const { shock } = demoScenario;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-6"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-50 border border-red-100">
          <Zap size={14} className="text-red-500" />
          <span className="text-xs font-semibold text-red-600 tracking-wide">
            INITIAL SHOCK
          </span>
        </span>
      </motion.div>

      {/* Headline */}
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="text-h1 md:text-display-sm text-center text-slate-900 max-w-3xl"
      >
        {shock.headline}
      </motion.h2>

      {/* Detail cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-14 w-full max-w-3xl">
        {shock.details.map((detail, i) => {
          const Icon = ICONS[i];
          return (
            <motion.div
              key={detail.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.15, duration: 0.5 }}
              className="bg-white border border-slate-200 rounded-xl p-6 shadow-ds"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center">
                  <Icon size={18} className="text-slate-500" />
                </div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400">
                  {detail.label}
                </p>
              </div>

              <p className="text-3xl font-bold text-slate-900 tabular-nums mb-2">
                {detail.value}
              </p>

              <p className="text-sm text-slate-500 leading-relaxed">
                {detail.description}
              </p>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
