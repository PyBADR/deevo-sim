"use client";

/**
 * Step 7 — Decision Layer (V2.2: Reactive Simulation)
 *
 * Clicking a decision now:
 *  1. Toggles it in the global sim state (via onToggleDecision)
 *  2. Pauses autoplay on first interaction
 *  3. Shows per-action simulated effect
 *  4. Shows aggregate "decisions activated" count + total stress reduction
 *
 * Decision pressure layer (V2.1) preserved: clock, escalation, consequence.
 */

import React, { useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lightbulb,
  Clock,
  ArrowUpRight,
  CheckCircle2,
  TrendingDown,
  AlertTriangle,
  Timer,
  Zap,
} from "lucide-react";
import { demoScenario } from "../data/demo-scenario";
import { DECISION_EFFECTS } from "../engine/demo-sim";
import type { DemoStepProps } from "../DemoStepRenderer";

const URGENCY_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  IMMEDIATE: { bg: "bg-red-50", text: "text-red-700", label: "Immediate" },
  "24H":     { bg: "bg-amber-50", text: "text-amber-700", label: "Within 24h" },
  "72H":     { bg: "bg-blue-50", text: "text-blue-700", label: "Within 72h" },
};

const SIMULATED_EFFECTS: string[] = [
  "Crude supply stabilized → market stress reduced 18%",
  "Interbank liquidity restored → credit freeze averted",
  "Route diversification active → transit delay reduced to 8 days",
  "Credit exposure capped → portfolio default risk contained",
  "Settlement SLA restored → cross-border payments normalized",
];

export function DecisionStep({ onPause, sim, onToggleDecision }: DemoStepProps) {
  const { decisions, decisionPressure } = demoScenario;
  const activatedSet = sim?.activatedDecisions ?? new Set<number>();
  const hasAnyActivation = activatedSet.size > 0;

  const handleSelect = useCallback(
    (i: number) => {
      // Pause autoplay on first interaction
      if (!hasAnyActivation && onPause) onPause();
      if (onToggleDecision) onToggleDecision(i);
    },
    [hasAnyActivation, onPause, onToggleDecision],
  );

  // Summary: how many sectors affected across all activated decisions
  const affectedSectorSet = new Set<number>();
  for (const dIdx of activatedSet) {
    const effect = DECISION_EFFECTS[dIdx];
    if (effect) {
      for (const sKey of Object.keys(effect.sectorDeltas)) {
        affectedSectorSet.add(Number(sKey));
      }
    }
  }

  return (
    <div className="flex flex-col items-center justify-start min-h-screen px-8 py-10">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-4"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-50 border border-emerald-100">
          <Lightbulb size={14} className="text-emerald-600" />
          <span className="text-xs font-semibold text-emerald-700 tracking-wide">
            DECISION INTELLIGENCE
          </span>
        </span>
      </motion.div>

      {/* Title */}
      <motion.h2
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="text-h2 md:text-h1 text-center text-slate-900 mb-2"
      >
        Recommended Actions
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.5 }}
        className="text-sm text-slate-500 text-center max-w-lg mb-5"
      >
        AI-generated response plan within the 24–72 hour critical window
      </motion.p>

      {/* ═══ DECISION PRESSURE BAR ═══ */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="w-full max-w-3xl mb-4"
      >
        <div className="flex items-stretch gap-3">
          {/* Decision clock */}
          <div className="flex items-center gap-3 px-4 py-3 bg-slate-900 rounded-xl flex-shrink-0">
            <Timer size={16} className="text-amber-400" />
            <div>
              <p className="text-[9px] font-bold text-slate-400 uppercase tracking-[0.15em]">
                {decisionPressure.clockLabel}
              </p>
              <p className="text-sm font-bold text-white tabular-nums">
                {decisionPressure.clockValue}
              </p>
            </div>
          </div>

          {/* Escalation banner */}
          <div className="flex-1 flex items-center gap-2.5 px-4 py-3 bg-red-50 border border-red-200 rounded-xl">
            <AlertTriangle size={15} className="text-red-500 flex-shrink-0" />
            <p className="text-[11px] text-red-800 leading-snug font-medium">
              {decisionPressure.escalationBanner}
            </p>
          </div>
        </div>

        <p className="text-[10px] text-slate-400 text-center mt-2.5 italic">
          {decisionPressure.consequenceStatement}
        </p>
      </motion.div>

      {/* ═══ LIVE SIM STATUS BAR — shows when any decision is activated ═══ */}
      <AnimatePresence>
        {hasAnyActivation && sim && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-3xl mb-4 overflow-hidden"
          >
            <div className="flex items-center justify-between px-4 py-2.5 bg-blue-50 border border-blue-200 rounded-xl">
              <div className="flex items-center gap-2">
                <Zap size={13} className="text-blue-600" />
                <span className="text-[11px] font-semibold text-blue-800">
                  {activatedSet.size} of {decisions.length} actions activated
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-[10px] text-blue-600">
                  <span className="font-bold">{affectedSectorSet.size}</span> sectors affected
                </span>
                <span className="text-[10px] font-bold text-emerald-600 tabular-nums">
                  ${sim.savedM}M projected savings
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Interaction hint */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.5 }}
        className="text-[10px] text-slate-400 text-center mb-4 tracking-wide uppercase"
      >
        Click actions to simulate their effect on sector stress
      </motion.p>

      {/* Decision cards */}
      <div className="space-y-3 w-full max-w-3xl">
        {decisions.map((action, i) => {
          const urgency = URGENCY_STYLES[action.urgency] ?? URGENCY_STYLES["72H"];
          const isSelected = activatedSet.has(i);

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.08, duration: 0.4 }}
            >
              <button
                type="button"
                onClick={() => handleSelect(i)}
                className={`w-full text-left bg-white border-2 rounded-xl shadow-ds overflow-hidden transition-all duration-300 ${
                  isSelected
                    ? "border-emerald-400 shadow-md shadow-emerald-100 ring-1 ring-emerald-200"
                    : "border-slate-200 hover:border-slate-300 hover:shadow-md"
                }`}
              >
                <div className="flex items-stretch">
                  {/* Rank */}
                  <div
                    className={`flex items-center justify-center w-12 border-r flex-shrink-0 transition-colors duration-300 ${
                      isSelected
                        ? "bg-emerald-50 border-emerald-100"
                        : "bg-slate-50 border-slate-100"
                    }`}
                  >
                    {isSelected ? (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 400, damping: 20 }}
                      >
                        <CheckCircle2 size={16} className="text-emerald-500" />
                      </motion.div>
                    ) : (
                      <span className="text-base font-bold text-slate-300 tabular-nums">
                        {i + 1}
                      </span>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 px-4 py-3.5">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <h3 className="text-[13px] font-semibold text-slate-900 leading-snug">
                        {action.title}
                      </h3>
                      <span
                        className={`flex-shrink-0 px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide ${urgency.bg} ${urgency.text}`}
                      >
                        {urgency.label}
                      </span>
                    </div>

                    {/* Owner */}
                    <div className="flex items-center gap-4 mb-2">
                      <div className="flex items-center gap-1.5">
                        <BuildingIcon size={11} className="text-slate-400" />
                        <span className="text-[11px] font-medium text-slate-600">{action.owner}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock size={11} className="text-slate-400" />
                        <span className="text-[11px] text-slate-500">{action.urgency}</span>
                      </div>
                    </div>

                    {/* Expected effect */}
                    <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-emerald-50/60 border border-emerald-100/60 mb-2">
                      <ArrowUpRight size={13} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                      <p className="text-[11px] text-emerald-800 leading-relaxed">
                        {action.expectedEffect}
                      </p>
                    </div>

                    {/* Consequence if delayed */}
                    <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-red-50/40 border border-red-100/40">
                      <AlertTriangle size={11} className="text-red-400 mt-0.5 flex-shrink-0" />
                      <p className="text-[10px] text-red-600/80 leading-relaxed">
                        <span className="font-semibold">If delayed:</span> {action.consequence}
                      </p>
                    </div>

                    {/* Simulated effect — appears on activation */}
                    <AnimatePresence>
                      {isSelected && (
                        <motion.div
                          initial={{ opacity: 0, height: 0, marginTop: 0 }}
                          animate={{ opacity: 1, height: "auto", marginTop: 8 }}
                          exit={{ opacity: 0, height: 0, marginTop: 0 }}
                          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                          className="overflow-hidden"
                        >
                          <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-blue-50 border border-blue-100">
                            <TrendingDown size={13} className="text-blue-600 flex-shrink-0" />
                            <p className="text-[11px] font-medium text-blue-800">
                              {SIMULATED_EFFECTS[i] ?? "Stress level reduced"}
                            </p>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </button>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function BuildingIcon({ size, className }: { size: number; className: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
      <path d="M9 22v-4h6v4" />
      <path d="M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01" />
    </svg>
  );
}
