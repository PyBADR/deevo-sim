"use client";

/**
 * V2.1 Demo Upgrades — Presentation-grade executive enhancements
 *
 * Components:
 *   - DecisionClock        — countdown to decision deadline
 *   - EscalationBanner     — SEVERE/HIGH stress alert ribbon
 *   - RoleSwitcher         — CEO / Risk / Regulator / Energy perspective toggle
 *   - RangeLossCard        — loss as range ($3.8B–$4.7B)
 *   - CompactAssumptions   — collapsible methodology panel
 *   - EnhancedSectorCard   — top driver + second-order risk + confidence band
 *   - ActionOwnerCard      — decision action with prominent owner emphasis
 *
 * All curated data — no backend dependency.
 */

import React, { useState, useEffect, useMemo } from "react";

// ═══════════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════════

export type ExecutiveRole = "ceo" | "risk" | "regulator" | "energy";

export interface RoleSwitcherProps {
  activeRole: ExecutiveRole;
  onSwitch: (role: ExecutiveRole) => void;
  locale: "en" | "ar";
}

export interface DecisionClockProps {
  deadlineIso: string;
  locale: "en" | "ar";
}

export interface EscalationBannerProps {
  averageStress: number;
  peakSector: string;
  peakStress: number;
  locale: "en" | "ar";
}

export interface RangeLossCardProps {
  lossLow: number;
  lossMid: number;
  lossHigh: number;
  confidencePct: number;
  locale: "en" | "ar";
}

export interface CompactAssumptionsProps {
  methodology: string;
  assumptions: string[];
  dataSources: string[];
  locale: "en" | "ar";
}

export interface EnhancedSectorCardProps {
  sector: string;
  sectorLabel: string;
  stress: number;
  lossUsd: number;
  topDriver: string;
  secondOrderRisk: string;
  confidenceLow: number;
  confidenceHigh: number;
  locale: "en" | "ar";
}

export interface ActionOwnerCardProps {
  id: string;
  action: string;
  actionAr?: string;
  owner: string;
  sector: string;
  urgency: number;
  lossAvoided: number;
  costUsd: number;
  confidence: number;
  deadlineHours?: number;
  escalationTrigger?: string;
  escalationTriggerAr?: string;
  locale: "en" | "ar";
}

// ═══════════════════════════════════════════════════════════════════════════════
// Role Switcher
// ═══════════════════════════════════════════════════════════════════════════════

const ROLE_META: Record<ExecutiveRole, { labelEn: string; labelAr: string; icon: string }> = {
  ceo:       { labelEn: "CEO",       labelAr: "الرئيس التنفيذي", icon: "C" },
  risk:      { labelEn: "Risk",      labelAr: "المخاطر",         icon: "R" },
  regulator: { labelEn: "Regulator", labelAr: "الرقابي",         icon: "G" },
  energy:    { labelEn: "Energy",    labelAr: "الطاقة",          icon: "E" },
};

export function RoleSwitcher({ activeRole, onSwitch, locale }: RoleSwitcherProps) {
  const isAr = locale === "ar";
  return (
    <div className="flex items-center gap-1 bg-slate-50 rounded-lg p-0.5 border border-slate-200">
      {(Object.keys(ROLE_META) as ExecutiveRole[]).map((role) => {
        const meta = ROLE_META[role];
        const active = role === activeRole;
        return (
          <button
            key={role}
            onClick={() => onSwitch(role)}
            className={`
              px-3 py-1.5 text-xs font-semibold rounded-md transition-all duration-150
              ${active
                ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                : "text-slate-500 hover:text-slate-700 hover:bg-white/60"
              }
            `}
            title={isAr ? meta.labelAr : meta.labelEn}
          >
            {isAr ? meta.labelAr : meta.labelEn}
          </button>
        );
      })}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Decision Clock
// ═══════════════════════════════════════════════════════════════════════════════

export function DecisionClock({ deadlineIso, locale }: DecisionClockProps) {
  const isAr = locale === "ar";
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const deadline = new Date(deadlineIso).getTime();
  const diffMs = Math.max(0, deadline - now);
  const hours = Math.floor(diffMs / 3_600_000);
  const mins = Math.floor((diffMs % 3_600_000) / 60_000);
  const secs = Math.floor((diffMs % 60_000) / 1_000);

  const isUrgent = hours < 6;
  const isCritical = hours < 2;

  return (
    <div
      className={`
        inline-flex items-center gap-2.5 px-4 py-2 rounded-lg border
        ${isCritical
          ? "bg-red-50 border-red-200"
          : isUrgent
            ? "bg-amber-50 border-amber-200"
            : "bg-slate-50 border-slate-200"
        }
      `}
    >
      <div className="flex flex-col">
        <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
          {isAr ? "الموعد النهائي للقرار" : "Decision Deadline"}
        </span>
        <div className="flex items-baseline gap-1 mt-0.5">
          <span
            className={`text-xl font-bold tabular-nums tracking-tight ${
              isCritical ? "text-red-700" : isUrgent ? "text-amber-700" : "text-slate-900"
            }`}
          >
            {String(hours).padStart(2, "0")}:{String(mins).padStart(2, "0")}:{String(secs).padStart(2, "0")}
          </span>
          <span className="text-[10px] text-slate-400 font-medium">
            {isAr ? "متبقي" : "remaining"}
          </span>
        </div>
      </div>
      {isCritical && (
        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Escalation Banner
// ═══════════════════════════════════════════════════════════════════════════════

export function EscalationBanner({ averageStress, peakSector, peakStress, locale }: EscalationBannerProps) {
  const isAr = locale === "ar";

  // Only show for ELEVATED+ (>= 0.50)
  if (averageStress < 0.50) return null;

  const isSevere = averageStress >= 0.80;
  const isHigh = averageStress >= 0.65;

  const level = isSevere ? "SEVERE" : isHigh ? "HIGH" : "ELEVATED";
  const levelAr = isSevere ? "حرج" : isHigh ? "مرتفع" : "مرتفع نسبيا";
  const bgColor = isSevere
    ? "bg-red-600"
    : isHigh
      ? "bg-red-500"
      : "bg-amber-500";

  return (
    <div className={`${bgColor} text-white px-6 py-2.5 flex items-center justify-between`}>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
          <span className="text-xs font-bold uppercase tracking-wider">
            {isAr ? `تنبيه ${levelAr}` : `${level} ALERT`}
          </span>
        </div>
        <span className="text-xs text-white/90">
          {isAr
            ? `متوسط الضغط ${(averageStress * 100).toFixed(0)}% — القطاع الأكثر تأثرا: ${peakSector} عند ${(peakStress * 100).toFixed(0)}%`
            : `Avg stress ${(averageStress * 100).toFixed(0)}% — Peak: ${peakSector} at ${(peakStress * 100).toFixed(0)}%`
          }
        </span>
      </div>
      <span className="text-[10px] font-semibold text-white/70 uppercase tracking-wider">
        {isAr ? "يتطلب تصعيد فوري" : "Immediate Escalation Required"}
      </span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Range-based Loss Card
// ═══════════════════════════════════════════════════════════════════════════════

function fmtB(n: number): string {
  return `$${(n / 1e9).toFixed(1)}B`;
}

export function RangeLossCard({ lossLow, lossMid, lossHigh, confidencePct, locale }: RangeLossCardProps) {
  const isAr = locale === "ar";
  const pctLow = ((lossMid - lossLow) / lossMid) * 100;
  const pctHigh = ((lossHigh - lossMid) / lossMid) * 100;

  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
        {isAr ? "نطاق الخسارة المقدرة" : "Estimated Loss Range"}
      </p>
      <div className="flex items-baseline gap-1">
        <span className="text-lg font-bold text-red-600">{fmtB(lossMid)}</span>
      </div>
      <div className="flex items-center gap-2 mt-1.5">
        <div className="flex-1 h-1.5 bg-slate-200 rounded-full relative overflow-hidden">
          <div
            className="absolute h-full bg-red-200 rounded-full"
            style={{ left: "10%", width: "80%" }}
          />
          <div
            className="absolute h-full bg-red-500 rounded-full"
            style={{
              left: `${Math.max(10, 50 - pctLow)}%`,
              width: `${Math.min(80, pctLow + pctHigh)}%`,
            }}
          />
        </div>
      </div>
      <div className="flex items-center justify-between mt-1">
        <span className="text-[10px] text-slate-400 tabular-nums">{fmtB(lossLow)}</span>
        <span className="text-[10px] text-slate-400">
          {confidencePct}% CI
        </span>
        <span className="text-[10px] text-slate-400 tabular-nums">{fmtB(lossHigh)}</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Compact Assumptions Panel
// ═══════════════════════════════════════════════════════════════════════════════

export function CompactAssumptions({ methodology, assumptions, dataSources, locale }: CompactAssumptionsProps) {
  const [open, setOpen] = useState(false);
  const isAr = locale === "ar";

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-slate-50 transition-colors"
      >
        <span className="text-xs font-semibold text-slate-900 uppercase tracking-wider">
          {isAr ? "المنهجية والافتراضات" : "Methodology & Assumptions"}
        </span>
        <svg
          className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="px-5 pb-4 space-y-3 border-t border-slate-100">
          {/* Methodology */}
          <div className="pt-3">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
              {isAr ? "المنهجية" : "Methodology"}
            </p>
            <p className="text-xs text-slate-700 leading-relaxed">{methodology}</p>
          </div>

          {/* Assumptions */}
          {assumptions.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                {isAr ? "الافتراضات" : "Key Assumptions"}
              </p>
              <ul className="space-y-1">
                {assumptions.map((a, i) => (
                  <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                    <span className="text-slate-300 mt-0.5">-</span>
                    <span>{a}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Data Sources */}
          {dataSources.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                {isAr ? "مصادر البيانات" : "Data Sources"}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {dataSources.map((src) => (
                  <span
                    key={src}
                    className="px-2 py-0.5 text-[10px] font-medium bg-slate-100 text-slate-600 rounded"
                  >
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Enhanced Sector Card
// ═══════════════════════════════════════════════════════════════════════════════

export function EnhancedSectorCard({
  sector,
  sectorLabel,
  stress,
  lossUsd,
  topDriver,
  secondOrderRisk,
  confidenceLow,
  confidenceHigh,
  locale,
}: EnhancedSectorCardProps) {
  const isAr = locale === "ar";

  const stressPct = (stress * 100).toFixed(0);
  const stressColor =
    stress >= 0.80 ? "text-red-700" :
    stress >= 0.65 ? "text-red-600" :
    stress >= 0.50 ? "text-amber-600" :
    stress >= 0.35 ? "text-amber-500" :
    "text-slate-600";

  const barColor =
    stress >= 0.65 ? "bg-red-500" :
    stress >= 0.50 ? "bg-amber-500" :
    stress >= 0.35 ? "bg-amber-400" :
    "bg-slate-400";

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-bold text-slate-900">{sectorLabel}</h4>
        <span className={`text-lg font-bold tabular-nums ${stressColor}`}>
          {stressPct}%
        </span>
      </div>

      {/* Stress bar */}
      <div className="h-1.5 bg-slate-100 rounded-full mb-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${Math.min(stress * 100, 100)}%` }}
        />
      </div>

      {/* Loss */}
      <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-100">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">
          {isAr ? "الخسارة" : "Loss"}
        </span>
        <span className="text-sm font-semibold text-slate-900 tabular-nums">
          {fmtB(lossUsd)}
        </span>
      </div>

      {/* Top Driver */}
      <div className="mb-2">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">
          {isAr ? "المحرك الأساسي" : "Top Driver"}
        </p>
        <p className="text-xs text-slate-800 font-medium">{topDriver}</p>
      </div>

      {/* Second-order Risk */}
      <div className="mb-2">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">
          {isAr ? "المخاطر الثانوية" : "Second-order Risk"}
        </p>
        <p className="text-xs text-slate-600">{secondOrderRisk}</p>
      </div>

      {/* Confidence Band */}
      <div className="pt-2 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">
            {isAr ? "نطاق الثقة" : "Confidence Band"}
          </span>
          <span className="text-[10px] text-slate-500 tabular-nums">
            {(confidenceLow * 100).toFixed(0)}%–{(confidenceHigh * 100).toFixed(0)}%
          </span>
        </div>
        <div className="h-1 bg-slate-100 rounded-full mt-1 relative overflow-hidden">
          <div
            className="absolute h-full bg-blue-400 rounded-full"
            style={{
              left: `${confidenceLow * 100}%`,
              width: `${(confidenceHigh - confidenceLow) * 100}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Action Owner Card (prominent owner emphasis)
// ═══════════════════════════════════════════════════════════════════════════════

export function ActionOwnerCard({
  id,
  action,
  actionAr,
  owner,
  sector,
  urgency,
  lossAvoided,
  costUsd,
  confidence,
  deadlineHours,
  escalationTrigger,
  escalationTriggerAr,
  locale,
}: ActionOwnerCardProps) {
  const isAr = locale === "ar";

  const urgencyLabel =
    urgency >= 90 ? (isAr ? "حرج" : "Critical") :
    urgency >= 75 ? (isAr ? "عالي" : "High") :
    urgency >= 50 ? (isAr ? "متوسط" : "Medium") :
    (isAr ? "منخفض" : "Low");

  const urgencyColor =
    urgency >= 90 ? "bg-red-600" :
    urgency >= 75 ? "bg-red-500" :
    urgency >= 50 ? "bg-amber-500" :
    "bg-slate-400";

  const roi = costUsd > 0 ? ((lossAvoided / costUsd)).toFixed(1) : "—";

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      {/* Owner emphasis stripe */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <p className="text-sm font-semibold text-slate-900 leading-snug">
            {isAr && actionAr ? actionAr : action}
          </p>
        </div>
        <span className={`${urgencyColor} text-white text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full whitespace-nowrap`}>
          {urgencyLabel}
        </span>
      </div>

      {/* Owner — prominent */}
      <div className="flex items-center gap-2 mb-4 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
        <div className="w-6 h-6 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">
          {owner.charAt(0)}
        </div>
        <div>
          <p className="text-[10px] text-blue-500 uppercase tracking-wider font-medium">
            {isAr ? "المسؤول" : "Action Owner"}
          </p>
          <p className="text-xs font-bold text-blue-900">{owner}</p>
        </div>
      </div>

      {/* Deadline & Escalation */}
      {(deadlineHours != null || escalationTrigger) && (
        <div className="flex items-stretch gap-3 mb-4">
          {deadlineHours != null && (
            <div className={`flex-1 rounded-lg px-3 py-2 border ${deadlineHours <= 8 ? "bg-red-50 border-red-100" : deadlineHours <= 16 ? "bg-amber-50 border-amber-100" : "bg-slate-50 border-slate-200"}`}>
              <p className="text-[10px] uppercase tracking-wider font-medium mb-0.5"
                 style={{ color: deadlineHours <= 8 ? "#b91c1c" : deadlineHours <= 16 ? "#b45309" : "#64748b" }}>
                {isAr ? "الموعد النهائي" : "Action Deadline"}
              </p>
              <p className={`text-sm font-bold tabular-nums ${deadlineHours <= 8 ? "text-red-700" : deadlineHours <= 16 ? "text-amber-700" : "text-slate-900"}`}>
                {deadlineHours}h
              </p>
            </div>
          )}
          {escalationTrigger && (
            <div className="flex-[2] bg-orange-50 border border-orange-100 rounded-lg px-3 py-2">
              <p className="text-[10px] text-orange-600 uppercase tracking-wider font-medium mb-0.5">
                {isAr ? "محفز التصعيد" : "Escalation Trigger"}
              </p>
              <p className="text-xs text-orange-800 font-medium leading-snug">
                {isAr && escalationTriggerAr ? escalationTriggerAr : escalationTrigger}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Metrics row */}
      <div className="grid grid-cols-4 gap-3">
        <div>
          <p className="text-[10px] text-slate-500 mb-0.5">{isAr ? "القطاع" : "Sector"}</p>
          <p className="text-xs font-semibold text-slate-900 capitalize">{sector}</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500 mb-0.5">{isAr ? "خسائر متجنبة" : "Loss Avoided"}</p>
          <p className="text-xs font-semibold text-emerald-700 tabular-nums">{fmtB(lossAvoided)}</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500 mb-0.5">{isAr ? "التكلفة" : "Cost"}</p>
          <p className="text-xs font-semibold text-slate-900 tabular-nums">{fmtB(costUsd)}</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500 mb-0.5">ROI</p>
          <p className="text-xs font-semibold text-slate-900 tabular-nums">{roi}x</p>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="mt-3 pt-3 border-t border-slate-100">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-slate-500">{isAr ? "الثقة" : "Confidence"}</span>
          <span className="text-[10px] text-slate-600 font-semibold tabular-nums">{(confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full"
            style={{ width: `${confidence * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Role-specific data filtering
// ═══════════════════════════════════════════════════════════════════════════════

/** Which sectors each role cares about most (Primary → Secondary) */
export const ROLE_SECTOR_FOCUS: Record<ExecutiveRole, string[]> = {
  ceo:       ["energy", "banking", "insurance", "fintech", "real_estate", "government", "trade"],
  risk:      ["banking", "insurance", "energy", "fintech", "real_estate", "government", "trade"],
  regulator: ["banking", "insurance", "fintech", "real_estate", "government"],
  energy:    ["energy", "trade", "banking", "government"],
};

/** Role-specific headline emphasis */
export const ROLE_HEADLINE: Record<ExecutiveRole, { labelEn: string; labelAr: string }> = {
  ceo:       { labelEn: "Executive Summary",          labelAr: "الملخص التنفيذي" },
  risk:      { labelEn: "Risk Intelligence Briefing",  labelAr: "موجز استخبارات المخاطر" },
  regulator: { labelEn: "Regulatory Impact Assessment", labelAr: "تقييم الأثر الرقابي" },
  energy:    { labelEn: "Energy Sector Briefing",      labelAr: "موجز قطاع الطاقة" },
};
