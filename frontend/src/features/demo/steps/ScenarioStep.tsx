"use client";

/**
 * Step 2 — Scenario
 *
 * "Something serious just happened"
 * Shows: Severity, Estimated loss, Confidence, Nodes impacted.
 * Each metric includes a WHY explanation.
 */

import React from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Activity, Network, Target } from "lucide-react";
import { demoScenario } from "../data/demo-scenario";

export function ScenarioStep() {
  const s = demoScenario;

  const metrics = [
    {
      icon: AlertTriangle,
      label: "Severity",
      value: `${Math.round(s.severity * 100)}%`,
      sublabel: s.severityLabel,
      why: "Derived from transit volume reduction (60%), strategic chokepoint classification, and historical disruption precedents.",
      color: "text-amber-600",
      bg: "bg-amber-50",
      border: "border-amber-100",
    },
    {
      icon: Activity,
      label: "Estimated Loss",
      value: `$${(s.lossWithoutAction / 1e9).toFixed(1)}B`,
      sublabel: "Without intervention",
      why: "Aggregated from oil repricing, trade finance exposure, insurance claims, and fiscal revenue shortfall across all 6 GCC economies.",
      color: "text-red-600",
      bg: "bg-red-50",
      border: "border-red-100",
    },
    {
      icon: Target,
      label: "Confidence",
      value: `${Math.round(s.confidence * 100)}%`,
      sublabel: "Model certainty",
      why: "Based on 5 validated data sources, calibrated against 3 historical Hormuz disruption events (2019, 2021, 2024).",
      color: "text-blue-600",
      bg: "bg-blue-50",
      border: "border-blue-100",
    },
    {
      icon: Network,
      label: "Nodes Impacted",
      value: String(s.nodesImpacted),
      sublabel: `of 43 total`,
      why: "Propagation engine traces shock across energy, shipping, banking, insurance, and government nodes with > 5% exposure.",
      color: "text-slate-700",
      bg: "bg-slate-50",
      border: "border-slate-200",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8">
      {/* Scenario badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-6"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-50 border border-amber-200">
          <AlertTriangle size={14} className="text-amber-600" />
          <span className="text-xs font-semibold text-amber-700 tracking-wide">
            SCENARIO DETECTED
          </span>
        </span>
      </motion.div>

      {/* Title */}
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="text-h1 md:text-display-sm text-center text-slate-900 max-w-3xl"
      >
        {s.name}
      </motion.h2>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        className="text-body-lg text-slate-500 text-center mt-4 max-w-lg"
      >
        Simulated disruption of one of the world&apos;s most critical maritime chokepoints,
        affecting 21% of global petroleum flow
      </motion.p>

      {/* Metric cards with WHY */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-14 w-full max-w-4xl"
      >
        {metrics.map(({ icon: Icon, label, value, sublabel, why, color, bg, border }, i) => (
          <motion.div
            key={label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 + i * 0.1, duration: 0.4 }}
            className={`${bg} border ${border} rounded-xl p-5`}
          >
            <div className="flex items-center gap-2 mb-3">
              <Icon size={18} className={color} />
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400">
                {label}
              </p>
            </div>

            <p className={`text-2xl font-bold tabular-nums ${color} mb-1`}>
              {value}
            </p>
            <p className="text-[11px] text-slate-400 mb-3">{sublabel}</p>

            {/* WHY — explainability */}
            <div className="pt-3 border-t border-slate-200/60">
              <p className="text-[10px] text-slate-400 leading-relaxed">
                <span className="font-semibold text-slate-500">Why: </span>
                {why}
              </p>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Time horizon */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.1, duration: 0.4 }}
        className="mt-10"
      >
        <p className="text-xs text-slate-400 text-center">
          Time horizon: <span className="font-semibold text-slate-600">{s.timeHorizon}</span>
        </p>
      </motion.div>
    </div>
  );
}
