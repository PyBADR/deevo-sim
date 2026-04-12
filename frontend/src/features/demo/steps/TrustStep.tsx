"use client";

/**
 * Step 9 — Trust & Explainability (Phase 2 polish)
 *
 * Closing authority layer. Calm, confident, institutional.
 *
 * Confidence: 84%  |  Data freshness: <10m  |  Sources: multi-signal
 *
 * Footer:
 * "This is not a dashboard.
 *  This is an AI Simulation System.
 *  Signal → Transmission → Decision → Outcome → Audit"
 */

import React from "react";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  Database,
  FileText,
  Cpu,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { demoScenario } from "../data/demo-scenario";

export function TrustStep() {
  const { trust, confidence } = demoScenario;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8 py-12">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-5"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-50 border border-slate-200">
          <ShieldCheck size={13} className="text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 tracking-wide">
            TRUST &amp; EXPLAINABILITY
          </span>
        </span>
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="text-h2 md:text-h1 text-center text-slate-900 mb-2"
      >
        Confidence &amp; Transparency
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-400 text-center max-w-md mb-10"
      >
        Every simulation is auditable. Every number is explainable.
      </motion.p>

      <div className="w-full max-w-3xl space-y-4">
        {/* ─── 3 TRUST KPIs ─── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.45 }}
          className="grid grid-cols-3 gap-3"
        >
          <TrustKPI
            icon={<Cpu size={17} className="text-blue-500" />}
            iconBg="bg-blue-50"
            label="Confidence"
            value={`${Math.round(confidence * 100)}%`}
            valueColor="text-blue-600"
            detail={trust.modelVersion}
          />
          <TrustKPI
            icon={<Clock size={17} className="text-emerald-500" />}
            iconBg="bg-emerald-50"
            label="Data Freshness"
            value={trust.dataFreshness}
            valueColor="text-emerald-600"
            detail="Signal latency"
          />
          <TrustKPI
            icon={<CheckCircle2 size={17} className="text-amber-500" />}
            iconBg="bg-amber-50"
            label="Validation"
            value={trust.validationMethod}
            valueColor="text-amber-600"
            detail={`${trust.dataSources.length} feeds`}
            smallValue
          />
        </motion.div>

        {/* ─── DATA SOURCES + ASSUMPTIONS ─── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45, duration: 0.4 }}
            className="bg-white border border-slate-200 rounded-xl p-4 shadow-ds"
          >
            <div className="flex items-center gap-2 mb-3">
              <Database size={12} className="text-slate-300" />
              <p className="text-[10px] font-bold text-slate-300 uppercase tracking-[0.15em]">
                Data Sources
              </p>
            </div>
            <div className="space-y-1.5">
              {trust.dataSources.map((source, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-1 h-1 rounded-full bg-blue-400 flex-shrink-0" />
                  <p className="text-[11px] text-slate-500">{source}</p>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.52, duration: 0.4 }}
            className="bg-white border border-slate-200 rounded-xl p-4 shadow-ds"
          >
            <div className="flex items-center gap-2 mb-3">
              <FileText size={12} className="text-slate-300" />
              <p className="text-[10px] font-bold text-slate-300 uppercase tracking-[0.15em]">
                Key Assumptions
              </p>
            </div>
            <div className="space-y-1.5">
              {trust.assumptions.map((a, i) => (
                <div key={i} className="flex items-start gap-2">
                  <div className="w-1 h-1 rounded-full bg-amber-400 flex-shrink-0 mt-1.5" />
                  <p className="text-[11px] text-slate-500 leading-relaxed">{a}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* ─── CLOSING AUTHORITY FOOTER ─── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65, duration: 0.45 }}
          className="rounded-2xl overflow-hidden"
          style={{
            background: "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)",
          }}
        >
          <div className="px-8 py-6 text-center">
            <p className="text-[13px] font-medium text-slate-400 mb-1">
              This is not a dashboard.
            </p>
            <p className="text-lg font-bold text-white mb-5">
              This is an AI Simulation System.
            </p>

            {/* Pipeline */}
            <div className="flex items-center justify-center gap-1.5 flex-wrap">
              {trust.footerPipeline.split(" \u2192 ").map((stage, i, arr) => (
                <React.Fragment key={stage}>
                  <span className="px-3 py-1.5 rounded-lg text-[11px] font-semibold text-white/85 bg-white/[0.07] border border-white/[0.06]">
                    {stage}
                  </span>
                  {i < arr.length - 1 && (
                    <svg width="12" height="8" viewBox="0 0 12 8" fill="none" className="text-white/20 flex-shrink-0">
                      <path d="M1 4H11M11 4L8 1M11 4L8 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </React.Fragment>
              ))}
            </div>

            <p className="text-[10px] text-slate-500 mt-5">
              Calibration: {trust.lastCalibration} &middot; {trust.modelVersion} &middot; SHA-256 audit trail
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

/* ── Trust KPI sub-component ── */
function TrustKPI({
  icon,
  iconBg,
  label,
  value,
  valueColor,
  detail,
  smallValue = false,
}: {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  value: string;
  valueColor: string;
  detail: string;
  smallValue?: boolean;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-ds text-center">
      <div className="flex justify-center mb-2.5">
        <div className={`w-8 h-8 rounded-lg ${iconBg} border border-slate-100/50 flex items-center justify-center`}>
          {icon}
        </div>
      </div>
      <p className="text-[9px] font-bold uppercase tracking-[0.15em] text-slate-300 mb-1">
        {label}
      </p>
      <p className={`${smallValue ? "text-[15px]" : "text-2xl"} font-bold tabular-nums ${valueColor}`}>
        {value}
      </p>
      <p className="text-[9px] text-slate-400 mt-0.5">{detail}</p>
    </div>
  );
}
