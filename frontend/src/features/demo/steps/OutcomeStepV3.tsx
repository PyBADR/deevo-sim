"use client";

import React, { useState, useRef, useEffect } from "react";
import type { DemoStepProps } from "../DemoStepRenderer";
import { demoScenario } from "../data/demo-scenario";
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  ArrowDown,
  Sparkles,
} from "lucide-react";

function useCountUp(
  target: number,
  duration = 1400,
  delay = 0,
  decimals = 1
): string {
  const [value, setValue] = useState(0);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    let start: number | null = null;
    let delayTimer: ReturnType<typeof setTimeout> | null = null;
    const from = value;

    const animate = (ts: number) => {
      if (start === null) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(from + (target - from) * eased);
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
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

export function OutcomeStepV3({ sim }: DemoStepProps) {
  const withoutActionLoss = sim?.withoutActionLossB ?? 4.9;
  const withActionLoss =
    sim && sim.decisionsActivated > 0 ? sim.withActionLossB : 4.3;
  const saved = withoutActionLoss - withActionLoss;

  const countWithoutAction = useCountUp(withoutActionLoss, 1400, 0, 1);
  const countWithAction = useCountUp(withActionLoss, 1400, 200, 1);
  const countSaved = useCountUp(saved, 1400, 400, 1);

  const financialRange = demoScenario.financialRanges;
  const outcomeData = demoScenario.outcome;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-flex items-center px-2 py-1 rounded-md bg-slate-100 border border-slate-200">
            <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-slate-600">
              OUTCOME
            </span>
          </span>
        </div>
        <h2 className="text-3xl font-bold text-slate-900 mb-1">
          Base vs. Mitigated
        </h2>
        <p className="text-sm text-slate-500">
          {sim && sim.decisionsActivated > 0
            ? "Projections reflect activated interventions"
            : "Estimated loss comparison with and without coordinated response"}
        </p>
      </div>

      {/* Status Bar */}
      {sim && sim.decisionsActivated > 0 && (
        <div className="bg-slate-100 border border-slate-200 rounded-lg px-3.5 py-2.5">
          <p className="text-xs font-medium text-slate-800">
            <span className="font-bold">{sim.decisionsActivated}</span>{" "}
            decision{sim.decisionsActivated !== 1 ? "s" : ""} activated —
            projections updated
          </p>
        </div>
      )}

      {/* Hero Cards */}
      <div className="grid grid-cols-3 gap-4">
        {/* WITHOUT ACTION */}
        <div className="border-2 border-red-600 rounded-xl overflow-hidden bg-white shadow-sm">
          <div className="bg-red-50 px-4 py-3 border-b border-red-100">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-red-700">
                Without Action
              </p>
            </div>
          </div>
          <div className="px-4 py-5 space-y-4">
            <div>
              <p className="text-[9px] font-bold uppercase tracking-[0.1em] text-slate-400 mb-1">
                Estimated Loss
              </p>
              <p className="text-3xl font-bold tabular-nums text-red-700">
                ${countWithoutAction}B
              </p>
            </div>

            <div className="pt-3 border-t border-slate-100 space-y-2.5">
              <div>
                <p className="text-[9px] font-medium text-slate-500 mb-1">
                  Recovery Timeline
                </p>
                <p className="text-xs font-semibold text-slate-700">18-24 months</p>
              </div>
              <div>
                <p className="text-[9px] font-medium text-slate-500 mb-1">
                  Risk Escalation
                </p>
                <p className="text-xs font-semibold text-red-600">Critical</p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100">
              <p className="text-[9px] font-medium text-slate-500 mb-1.5">
                Range Band
              </p>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-[9px] text-slate-400">Low</span>
                  <span className="text-[9px] font-medium text-slate-600">
                    ${financialRange.withoutAction.low}B
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[9px] text-slate-400">High</span>
                  <span className="text-[9px] font-medium text-slate-600">
                    ${financialRange.withoutAction.high}B
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100">
              <p className="text-[9px] font-medium text-slate-500 mb-1">Why</p>
              <p className="text-xs text-slate-600 leading-relaxed">
                {outcomeData.withoutAction.why}
              </p>
            </div>
          </div>
        </div>

        {/* WITH ACTION */}
        <div className="border-2 border-emerald-600 rounded-xl overflow-hidden bg-white shadow-sm">
          <div className="bg-emerald-50 px-4 py-3 border-b border-emerald-100">
            <div className="flex items-center gap-2 mb-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-emerald-700">
                With Coordinated Response
              </p>
            </div>
          </div>
          <div className="px-4 py-5 space-y-4">
            <div>
              <p className="text-[9px] font-bold uppercase tracking-[0.1em] text-slate-400 mb-1">
                Mitigated Loss
              </p>
              <p className="text-3xl font-bold tabular-nums text-emerald-700">
                ${countWithAction}B
              </p>
            </div>

            <div className="pt-3 border-t border-slate-100 space-y-2.5">
              <div>
                <p className="text-[9px] font-medium text-slate-500 mb-1">
                  Recovery Timeline
                </p>
                <p className="text-xs font-semibold text-slate-700">9-12 months</p>
              </div>
              <div>
                <p className="text-[9px] font-medium text-slate-500 mb-1">
                  Risk Reduction
                </p>
                <p className="text-xs font-semibold text-emerald-600">
                  {Math.round(((withoutActionLoss - withActionLoss) / withoutActionLoss) * 100)}%
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100">
              <p className="text-[9px] font-medium text-slate-500 mb-1.5">
                Range Band
              </p>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-[9px] text-slate-400">Low</span>
                  <span className="text-[9px] font-medium text-slate-600">
                    ${financialRange.withAction.low}B
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[9px] text-slate-400">High</span>
                  <span className="text-[9px] font-medium text-slate-600">
                    ${financialRange.withAction.high}B
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100">
              <p className="text-[9px] font-medium text-slate-500 mb-1">Why</p>
              <p className="text-xs text-slate-600 leading-relaxed">
                {outcomeData.withAction.why}
              </p>
            </div>
          </div>
        </div>

        {/* VALUE SAVED */}
        <div className="rounded-xl overflow-hidden bg-gradient-to-b from-emerald-700 to-emerald-800 shadow-sm">
          <div className="px-4 py-5 space-y-4 h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-emerald-200" />
                <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-emerald-200">
                  Value Saved
                </p>
              </div>
              <div className="text-4xl font-bold tabular-nums text-white">
                ${countSaved}B
              </div>
            </div>

            <div className="space-y-3 pt-3 border-t border-emerald-600/40">
              <div>
                <p className="text-[9px] font-medium text-emerald-200 mb-1">
                  Range Band
                </p>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-[9px] text-emerald-300">Low</span>
                    <span className="text-[9px] font-medium text-emerald-100">
                      ${financialRange.saved.low}B
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[9px] text-emerald-300">High</span>
                    <span className="text-[9px] font-medium text-emerald-100">
                      ${financialRange.saved.high}B
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-emerald-600/40">
                <p className="text-[9px] font-medium text-emerald-200 mb-1">
                  Why
                </p>
                <p className="text-xs text-emerald-100 leading-relaxed">
                  {outcomeData.saved.explanation}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
