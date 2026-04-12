"use client";

/**
 * Step 8 — Outcome (V2.2: Reactive Simulation)
 *
 * Three hero numbers with count-up animation:
 *   WITHOUT ACTION: $4.9B (red)  — always baseline
 *   WITH ACTION:    $X.XB (emerald) — computed from sim when decisions activated
 *   SAVED:          $XXXM (blue gradient) — computed delta
 *
 * Count-up targets are reactive: when sim provides computed values,
 * the hook re-animates to the new target smoothly.
 */

import React, { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  TrendingDown,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  ArrowDown,
  Sparkles,
  Zap,
} from "lucide-react";
import { demoScenario } from "../data/demo-scenario";
import type { DemoStepProps } from "../DemoStepRenderer";

/* ─── Count-up hook (reactive to target changes) ─── */
function useCountUp(
  target: number,
  duration: number = 1400,
  delay: number = 0,
  decimals: number = 1,
) {
  const [value, setValue] = useState(0);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    let start: number | null = null;
    let delayTimer: ReturnType<typeof setTimeout> | null = null;
    const from = value; // animate from current displayed value

    const animate = (ts: number) => {
      if (start === null) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(from + (target - from) * eased);
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      }
    };

    delayTimer = setTimeout(() => {
      frameRef.current = requestAnimationFrame(animate);
    }, delay);

    return () => {
      if (delayTimer) clearTimeout(delayTimer);
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, duration, delay]);

  if (decimals === 0) return Math.round(value).toString();
  return value.toFixed(decimals);
}

export function OutcomeStep({ sim }: DemoStepProps) {
  const { outcome, financialRanges } = demoScenario;
  const hasSimData = sim && sim.decisionsActivated > 0;

  // Reactive targets: use sim-computed values when decisions activated, else defaults
  const withActionTarget = hasSimData ? sim.withActionLossB : 4.3;
  const savedTarget = hasSimData ? sim.savedM : 600;

  // Count-up values — re-animate when targets change
  const withoutVal = useCountUp(4.9, 1400, 400, 1);
  const withVal = useCountUp(withActionTarget, 1400, hasSimData ? 0 : 550, 1);
  const savedVal = useCountUp(savedTarget, 1600, hasSimData ? 0 : 750, 0);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-6"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-50 border border-slate-200">
          <span className="text-xs font-semibold text-slate-600 tracking-wide">
            OUTCOME PROJECTION
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
        Action vs. Inaction
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-500 text-center max-w-lg mb-4"
      >
        {hasSimData
          ? "Outcomes updated based on your activated decisions"
          : "Projected outcomes comparing coordinated response against no intervention"}
      </motion.p>

      {/* V2.2: Sim-aware status */}
      {hasSimData && sim && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-4xl mb-6"
        >
          <div className="flex items-center justify-center gap-3 px-4 py-2.5 bg-blue-50 border border-blue-200 rounded-xl">
            <Zap size={13} className="text-blue-600" />
            <span className="text-[11px] font-semibold text-blue-800">
              {sim.decisionsActivated} decision{sim.decisionsActivated !== 1 ? "s" : ""} activated — outcomes recalculated
            </span>
          </div>
        </motion.div>
      )}

      {/* ═══════ THREE HERO NUMBERS ═══════ */}
      <div className="flex flex-col md:flex-row items-stretch gap-5 w-full max-w-4xl mb-8">
        {/* WITHOUT ACTION */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="flex-1 bg-white border-2 border-red-200 rounded-2xl overflow-hidden shadow-ds"
        >
          <div className="bg-red-50 px-5 py-3 border-b border-red-100 flex items-center gap-2">
            <AlertTriangle size={16} className="text-red-500" />
            <span className="text-xs font-bold text-red-800 uppercase tracking-wider">
              Without Action
            </span>
          </div>
          <div className="p-6 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400 mb-2">
              Projected Total Loss
            </p>
            <p className="text-5xl md:text-6xl font-bold text-red-700 tabular-nums tracking-tight">
              ${withoutVal}B
            </p>
            <div className="flex items-center justify-center gap-1.5 mt-3">
              <TrendingUp size={14} className="text-red-400" />
              <span className="text-xs text-red-500 font-medium">
                Risk escalation {outcome.withoutAction.riskEscalation}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Recovery: {outcome.withoutAction.recoveryTimeline}
            </p>
            {/* V2.1: Range band */}
            <div className="mt-3 pt-3 border-t border-red-100">
              <p className="text-[9px] font-bold text-red-300 uppercase tracking-[0.12em] mb-1">Range</p>
              <p className="text-[11px] text-red-600 font-semibold tabular-nums">
                {financialRanges.withoutAction.low} – {financialRanges.withoutAction.high}
              </p>
              <p className="text-[9px] text-red-400/70 mt-0.5">{financialRanges.withoutAction.sensitivity}</p>
            </div>
          </div>
        </motion.div>

        {/* WITH ACTION */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45, duration: 0.5 }}
          className="flex-1 bg-white border-2 border-emerald-200 rounded-2xl overflow-hidden shadow-ds"
        >
          <div className="bg-emerald-50 px-5 py-3 border-b border-emerald-100 flex items-center gap-2">
            <ShieldCheck size={16} className="text-emerald-500" />
            <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
              With Action
            </span>
          </div>
          <div className="p-6 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400 mb-2">
              Reduced Total Loss
            </p>
            <p className="text-5xl md:text-6xl font-bold text-emerald-700 tabular-nums tracking-tight">
              ${withVal}B
            </p>
            <div className="flex items-center justify-center gap-1.5 mt-3">
              <TrendingDown size={14} className="text-emerald-400" />
              <span className="text-xs text-emerald-500 font-medium">
                Risk reduction {outcome.withAction.riskReduction}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Recovery: {outcome.withAction.recoveryTimeline}
            </p>
            {/* V2.1: Range band */}
            <div className="mt-3 pt-3 border-t border-emerald-100">
              <p className="text-[9px] font-bold text-emerald-300 uppercase tracking-[0.12em] mb-1">Range</p>
              <p className="text-[11px] text-emerald-600 font-semibold tabular-nums">
                {financialRanges.withAction.low} – {financialRanges.withAction.high}
              </p>
              <p className="text-[9px] text-emerald-400/70 mt-0.5">{financialRanges.withAction.sensitivity}</p>
            </div>
          </div>
        </motion.div>

        {/* SAVED — The hero with emphasis */}
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.65, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="flex-1 relative"
        >
          {/* Glow ring */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: [0, 0.5, 0.3], scale: [0.9, 1.04, 1.02] }}
            transition={{ delay: 1.3, duration: 1.2, ease: "easeOut" }}
            className="absolute -inset-1 rounded-[20px] bg-blue-400/20 blur-md pointer-events-none"
          />

          <div className="relative bg-gradient-to-b from-blue-600 to-blue-700 rounded-2xl overflow-hidden shadow-lg shadow-blue-200">
            <div className="px-5 py-3 border-b border-blue-500/30 flex items-center gap-2">
              <Sparkles size={16} className="text-blue-200" />
              <span className="text-xs font-bold text-blue-100 uppercase tracking-wider">
                Value Saved
              </span>
            </div>
            <div className="p-6 text-center">
              <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-blue-200 mb-2">
                Net Decision Value
              </p>

              {/* The number — with scale pulse */}
              <motion.p
                initial={{ scale: 1 }}
                animate={{ scale: [1, 1.06, 1] }}
                transition={{ delay: 1.8, duration: 0.6, ease: "easeInOut" }}
                className="text-5xl md:text-6xl font-bold text-white tabular-nums tracking-tight"
              >
                ${savedVal}M
              </motion.p>

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.5, duration: 0.4 }}
                className="flex items-center justify-center gap-1.5 mt-3"
              >
                <ArrowDown size={14} className="text-blue-200" />
                <span className="text-xs text-blue-200 font-medium">
                  Within 24–72h window
                </span>
              </motion.div>
              {/* V2.1: Range band */}
              <div className="mt-3 pt-3 border-t border-blue-500/20">
                <p className="text-[9px] font-bold text-blue-300/60 uppercase tracking-[0.12em] mb-1">Range</p>
                <p className="text-[11px] text-blue-100 font-semibold tabular-nums">
                  {financialRanges.saved.low} – {financialRanges.saved.high}
                </p>
                <p className="text-[9px] text-blue-200/60 mt-0.5">{financialRanges.saved.sensitivity}</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* ═══════ WHY EXPLANATIONS ═══════ */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.1, duration: 0.5 }}
        className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        {/* Without action — why */}
        <div className="px-5 py-4 rounded-xl bg-red-50/50 border border-red-100/60">
          <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-red-400 mb-1.5">
            Why ${withoutVal}B without action?
          </p>
          <p className="text-xs text-red-800/80 leading-relaxed">
            {outcome.withoutAction.why}
          </p>
        </div>

        {/* With action — why */}
        <div className="px-5 py-4 rounded-xl bg-emerald-50/50 border border-emerald-100/60">
          <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-400 mb-1.5">
            Why ${withVal}B with action?
          </p>
          <p className="text-xs text-emerald-800/80 leading-relaxed">
            {outcome.withAction.why}
          </p>
        </div>
      </motion.div>

      {/* Saved explanation */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.25, duration: 0.4 }}
        className="w-full max-w-4xl mt-4"
      >
        <div className="px-5 py-3 rounded-xl bg-blue-50/60 border border-blue-100/50">
          <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-blue-400 mb-1">
            How is ${savedVal}M derived?
          </p>
          <p className="text-xs text-blue-700/80 leading-relaxed">
            {outcome.saved.explanation}
          </p>
        </div>
      </motion.div>
    </div>
  );
}
