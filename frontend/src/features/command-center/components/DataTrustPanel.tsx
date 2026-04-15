"use client";

/**
 * DataTrustPanel — Read-only provenance & freshness display
 *
 * Shows data trust metadata for the active scenario:
 *   - Source Mode (static fallback)
 *   - Freshness (not live)
 *   - Last Updated (static baseline)
 *   - Confidence score
 *   - Audit Status
 *
 * This panel is informational only. It does NOT change scenario
 * calculations, connect live feeds, or modify any output.
 *
 * Wording rules enforced:
 *   - Never says "real-time" or "live intelligence"
 *   - Uses: "static fallback", "source-ready", "provenance tracked"
 */

import React, { useState } from "react";
import {
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Database,
  Clock,
  Activity,
  FileCheck,
} from "lucide-react";
import type { FreshnessStatus, DataSourceType } from "@/types/data-trust";

// ── Types ─────────────────────────────────────────────────────────────

export interface DataTrustMeta {
  /** Current data source mode */
  sourceMode: "static_fallback" | "source_ready";
  /** Source type classification */
  sourceType: DataSourceType;
  /** Freshness status */
  freshness: FreshnessStatus;
  /** When the static baseline was last updated */
  lastUpdated: string;
  /** Confidence score 0–1 from the trust layer */
  confidenceScore: number;
  /** Human-readable audit status */
  auditStatus: string;
  /** Human-readable audit status in Arabic */
  auditStatusAr: string;
  /** Number of data sources registered */
  registeredSources: number;
  /** Number of live sources connected (currently 0) */
  liveSourcesConnected: number;
  /** Whether provenance tracking is active */
  provenanceTracked: boolean;
}

interface DataTrustPanelProps {
  meta: DataTrustMeta;
  locale?: "en" | "ar";
}

// ── Helpers ───────────────────────────────────────────────────────────

function freshnessLabel(status: FreshnessStatus, locale: "en" | "ar"): string {
  switch (status) {
    case "fresh":
      return locale === "ar" ? "محدّث" : "Fresh";
    case "stale":
      return locale === "ar" ? "قديم" : "Stale";
    case "unknown":
    default:
      return locale === "ar" ? "غير متصل — بيانات ثابتة" : "Not live — static baseline";
  }
}

function sourceModeLabel(
  mode: "static_fallback" | "source_ready",
  locale: "en" | "ar",
): string {
  if (mode === "static_fallback") {
    return locale === "ar" ? "بيانات ثابتة احتياطية" : "Static fallback";
  }
  return locale === "ar" ? "جاهز للمصادر" : "Source-ready";
}

function confidenceColor(score: number): string {
  if (score >= 0.80) return "text-emerald-600";
  if (score >= 0.60) return "text-amber-600";
  return "text-red-600";
}

// ── Component ─────────────────────────────────────────────────────────

export function DataTrustPanel({ meta, locale = "en" }: DataTrustPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const isAr = locale === "ar";

  return (
    <div
      className="mx-6 mb-3"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Collapsed header — always visible */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors group"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-2">
          <ShieldCheck size={14} className="text-slate-500" />
          <span className="text-[11px] font-semibold text-slate-700 tracking-wide uppercase">
            {isAr ? "طبقة ثقة البيانات" : "Data Trust Layer"}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-600 font-medium">
            {sourceModeLabel(meta.sourceMode, locale)}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-slate-500">
            {isAr ? "المصادر:" : "Sources:"}{" "}
            <span className="font-semibold tabular-nums">
              {meta.liveSourcesConnected}/{meta.registeredSources}
            </span>
            {" "}
            {isAr ? "متصلة" : "connected"}
          </span>
          {expanded ? (
            <ChevronUp size={12} className="text-slate-400" />
          ) : (
            <ChevronDown size={12} className="text-slate-400" />
          )}
        </div>
      </button>

      {/* Expanded detail grid */}
      {expanded && (
        <div className="mt-1 px-4 py-3 bg-white border border-slate-200 border-t-0 rounded-b-lg">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {/* Source Mode */}
            <div className="space-y-0.5">
              <div className="flex items-center gap-1">
                <Database size={11} className="text-slate-400" />
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                  {isAr ? "وضع المصدر" : "Source Mode"}
                </p>
              </div>
              <p className="text-xs font-semibold text-slate-800">
                {sourceModeLabel(meta.sourceMode, locale)}
              </p>
            </div>

            {/* Freshness */}
            <div className="space-y-0.5">
              <div className="flex items-center gap-1">
                <Activity size={11} className="text-slate-400" />
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                  {isAr ? "الحداثة" : "Freshness"}
                </p>
              </div>
              <p className="text-xs font-semibold text-slate-800">
                {freshnessLabel(meta.freshness, locale)}
              </p>
            </div>

            {/* Last Updated */}
            <div className="space-y-0.5">
              <div className="flex items-center gap-1">
                <Clock size={11} className="text-slate-400" />
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                  {isAr ? "آخر تحديث" : "Last Updated"}
                </p>
              </div>
              <p className="text-xs font-semibold text-slate-800">
                {meta.lastUpdated}
              </p>
            </div>

            {/* Confidence */}
            <div className="space-y-0.5">
              <div className="flex items-center gap-1">
                <ShieldCheck size={11} className="text-slate-400" />
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                  {isAr ? "الثقة" : "Confidence"}
                </p>
              </div>
              <p className={`text-xs font-bold tabular-nums ${confidenceColor(meta.confidenceScore)}`}>
                {(meta.confidenceScore * 100).toFixed(0)}%
              </p>
            </div>

            {/* Audit Status */}
            <div className="space-y-0.5">
              <div className="flex items-center gap-1">
                <FileCheck size={11} className="text-slate-400" />
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                  {isAr ? "حالة التدقيق" : "Audit Status"}
                </p>
              </div>
              <p className="text-xs font-semibold text-slate-800">
                {isAr ? meta.auditStatusAr : meta.auditStatus}
              </p>
            </div>
          </div>

          {/* Footer note */}
          <div className="mt-3 pt-2 border-t border-slate-100">
            <p className="text-[10px] text-slate-400">
              {isAr
                ? "تتبع المصدر نشط — البيانات الحالية من مجموعة بيانات مرجعية ثابتة. مصادر البيانات الحية غير متصلة بعد."
                : "Provenance tracked — current data from static reference dataset. Live data feeds not connected."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
