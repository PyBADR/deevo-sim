"use client";

/**
 * Step 7 — Decision Layer (Interactive)
 *
 * "Recommended Actions (24-72 hours)"
 * Each action: Owner, Urgency, Expected effect.
 *
 * INTERACTION MODE: Clicking an action pauses autoplay,
 * highlights it, and shows a simulated stress-reduction effect.
 */

import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lightbulb, Clock, ArrowUpRight, CheckCircle2, TrendingDown } from "lucide-react";
import { demoScenario } from "../data/demo-scenario";
import type { DemoStepProps } from "../DemoStepRenderer";

const URGENCY_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  IMMEDIATE: { bg: "bg-red-50", text: "text-red-700", label: "Immediate" },
  "24H": { bg: "bg-amber-50", text: "text-amber-700", label: "Within 24h" },
  "72H": { bg: "bg-blue-50", text: "text-blue-700", label: "Within 72h" },
};

/** Simulated stress-reduction per action (visual-only, no backend) */
const SIMULATED_EFFECTS: string[] = [
  "Crude supply stabilized → market stress reduced 18%",
  "Interbank liquidity restored → credit freeze averted",
  "Route diversification active → transit delay reduced to 8 days",
  "Credit exposure capped → portfolio default risk contained",
  "Settlement SLA restored → cross-border payments normalized",
];

export function DecisionStep({ onPause }: DemoStepProps) {
  const { decisions } = demoScenario;
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  const handleSelect = useCallback(
    (i: number) => {
      // Pause autoplay on first interaction — let user explore
      if (selectedIndex === null && onPause) {
        onPause();
      }
      setSelectedIndex((prev) => (prev === i ? null : i));
    },
    [selectedIndex, onPause],
  );

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8 py-16">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-6"
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
        className="text-h2 md:text-h1 text-center text-slate-900 mb-3"
      >
        Recommended Actions
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-500 text-center max-w-lg mb-4"
      >
        AI-generated response plan within the 24&ndash;72 hour critical window
      </motion.p>

      {/* Interaction hint */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.5 }}
        className="text-[10px] text-slate-400 text-center mb-8 tracking-wide uppercase"
      >
        Click any action to see simulated effect
      </motion.p>

      {/* Decision cards */}
      <div className="space-y-4 w-full max-w-3xl">
        {decisions.map((action, i) => {
          const urgency = URGENCY_STYLES[action.urgency] ?? URGENCY_STYLES["72H"];
          const isSelected = selectedIndex === i;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.35 + i * 0.1, duration: 0.45 }}
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
                    className={`flex items-center justify-center w-14 border-r flex-shrink-0 transition-colors duration-300 ${
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
                        <CheckCircle2 size={18} className="text-emerald-500" />
                      </motion.div>
                    ) : (
                      <span className="text-lg font-bold text-slate-300 tabular-nums">
                        {i + 1}
                      </span>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 p-5">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                        {action.title}
                      </h3>
                      <span
                        className={`flex-shrink-0 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${urgency.bg} ${urgency.text}`}
                      >
                        {urgency.label}
                      </span>
                    </div>

                    {/* Owner */}
                    <div className="flex items-center gap-4 mb-3">
                      <div className="flex items-center gap-1.5">
                        <BuildingIcon size={12} className="text-slate-400" />
                        <span className="text-xs text-slate-500">{action.owner}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock size={12} className="text-slate-400" />
                        <span className="text-xs text-slate-500">{action.urgency}</span>
                      </div>
                    </div>

                    {/* Expected effect */}
                    <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-emerald-50/60 border border-emerald-100/60">
                      <ArrowUpRight size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-emerald-800 leading-relaxed">
                        {action.expectedEffect}
                      </p>
                    </div>

                    {/* Simulated effect — appears on click */}
                    <AnimatePresence>
                      {isSelected && (
                        <motion.div
                          initial={{ opacity: 0, height: 0, marginTop: 0 }}
                          animate={{ opacity: 1, height: "auto", marginTop: 12 }}
                          exit={{ opacity: 0, height: 0, marginTop: 0 }}
                          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                          className="overflow-hidden"
                        >
                          <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-blue-50 border border-blue-100">
                            <TrendingDown size={14} className="text-blue-600 flex-shrink-0" />
                            <p className="text-xs font-medium text-blue-800">
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

/** Inline Building SVG to avoid lucide naming conflicts */
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
