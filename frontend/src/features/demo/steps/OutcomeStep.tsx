"use client";

/**
 * Step 8 — Outcome (THE MONEY SHOT)
 *
 * Three hero numbers with count-up animation:
 *   WITHOUT ACTION: $4.9B (red)
 *   WITH ACTION:    $4.3B (emerald)
 *   SAVED:          $600M (blue gradient, emphasized)
 *
 * Count-up runs on mount, $600M gets extra glow + scale pulse.
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
} from "lucide-react";
import { demoScenario } from "../data/demo-scenario";

/* ─── Count-up hook ─── */
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

    const animate = (ts: number) => {
      if (start === null) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(eased * target);
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
  }, [target, duration, delay]);

  if (decimals === 0) return Math.round(value).toString();
  return value.toFixed(decimals);
}

export function OutcomeStep() {
  const { outcome } = demoScenario;

  // Count-up values (display-only)
  const withoutVal = useCountUp(4.9, 1400, 400, 1);
  const withVal = useCountUp(4.3, 1400, 550, 1);
  const savedVal = useCountUp(600, 1600, 750, 0);

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
        className="text-sm text-slate-500 text-center max-w-lg mb-10"
      >
        Projected outcomes comparing coordinated response against no intervention
      </motion.p>

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
            Why $4.9B without action?
          </p>
          <p className="text-xs text-red-800/80 leading-relaxed">
            {outcome.withoutAction.why}
          </p>
        </div>

        {/* With action — why */}
        <div className="px-5 py-4 rounded-xl bg-emerald-50/50 border border-emerald-100/60">
          <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-400 mb-1.5">
            Why $4.3B with action?
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
            How is $600M derived?
          </p>
          <p className="text-xs text-blue-700/80 leading-relaxed">
            {outcome.saved.explanation}
          </p>
        </div>
      </motion.div>
    </div>
  );
}
