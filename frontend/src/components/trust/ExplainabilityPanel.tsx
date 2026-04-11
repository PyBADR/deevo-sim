"use client";

/**
 * ExplainabilityPanel — Aggregated Trust + Explainability Summary.
 *
 * Surfaces existing backend data (metric_explanations, reliability.ranges,
 * confidence_score, explainability narrative) in a compact, collapsible panel.
 *
 * Shows at a glance:
 *   1. Overall Confidence (%)
 *   2. Range bands for headline metrics (loss, URS)
 *   3. Top Drivers across all metrics (ranked)
 *   4. Bilingual narrative explanation
 *
 * Compact by default (Level 1). Expand for per-metric detail via MetricWhyCard.
 *
 * Data contract: Reuses existing types — MetricExplanation, RangeEstimate,
 * ReliabilityPayload, ConfidenceAdjustment. No new backend engines required.
 */

import { useState, useMemo } from "react";
import type {
  MetricExplanation,
  RangeEstimate,
  ReliabilityPayload,
  ExplanationDriver,
} from "@/types/observatory";
import { MetricWhyCard } from "./MetricWhyCard";

// ── Bilingual labels ──────────────────────────────────────────────────────

const LABELS = {
  title:       { en: "Decision Explainability",   ar: "شرح القرار" },
  confidence:  { en: "Confidence",                ar: "مستوى الثقة" },
  range:       { en: "Expected Range",            ar: "النطاق المتوقع" },
  drivers:     { en: "Top Drivers",               ar: "العوامل الرئيسية" },
  narrative:   { en: "Narrative",                  ar: "الرواية التحليلية" },
  expand:      { en: "Show details",              ar: "عرض التفاصيل" },
  collapse:    { en: "Hide details",              ar: "إخفاء التفاصيل" },
  low:         { en: "Low",                       ar: "أدنى" },
  base:        { en: "Base",                      ar: "أساس" },
  high:        { en: "High",                      ar: "أعلى" },
  method:      { en: "Method",                    ar: "المنهجية" },
  confLabel:   { en: "confidence",                ar: "ثقة" },
  provisional: { en: "Provisional",               ar: "مؤقت" },
} as const;

type LKey = keyof typeof LABELS;
function t(key: LKey, locale: "en" | "ar"): string {
  return LABELS[key][locale];
}

// ── Props ─────────────────────────────────────────────────────────────────

interface ExplainabilityPanelProps {
  /** Per-metric explanation objects from backend (stages 41a) */
  metricExplanations?: MetricExplanation[];
  /** Reliability payload including ranges, sensitivities, adjustments (stages 41c–41g) */
  reliability?: ReliabilityPayload;
  /** Global confidence score from simulation engine (0–1) */
  confidenceScore?: number;
  /** Bilingual narrative from explainability block */
  narrativeEn?: string;
  narrativeAr?: string;
  /** UI locale */
  locale: "en" | "ar";
  /** Start expanded (default: false — compact mode) */
  defaultExpanded?: boolean;
}

// ── Helpers ───────────────────────────────────────────────────────────────

function formatUsd(v: number): string {
  if (v >= 1e12) return `$${(v / 1e12).toFixed(1)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${Math.round(v)}`;
}

function formatMetricValue(v: number, metricId: string): string {
  if (metricId.includes("loss") || metricId.includes("projected")) {
    return formatUsd(v);
  }
  if (v <= 1.0 && v >= 0) return (v * 100).toFixed(1) + "%";
  return v.toFixed(2);
}

function confColor(pct: number): string {
  if (pct >= 75) return "text-emerald-600";
  if (pct >= 50) return "text-amber-600";
  return "text-red-600";
}

function confBarColor(pct: number): string {
  if (pct >= 75) return "bg-emerald-500";
  if (pct >= 50) return "bg-amber-500";
  return "bg-red-500";
}

// ── Component ─────────────────────────────────────────────────────────────

export function ExplainabilityPanel({
  metricExplanations,
  reliability,
  confidenceScore,
  narrativeEn,
  narrativeAr,
  locale,
  defaultExpanded = false,
}: ExplainabilityPanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const isAr = locale === "ar";
  const narrative = isAr ? narrativeAr : narrativeEn;

  // ── Derived: aggregate top drivers across all metric explanations ──
  const topDrivers = useMemo(() => {
    if (!metricExplanations || metricExplanations.length === 0) return [];
    const all: (ExplanationDriver & { source: string })[] = [];
    for (const me of metricExplanations) {
      for (const d of me.drivers) {
        all.push({ ...d, source: me.label });
      }
    }
    // Deduplicate by label, keep highest contribution
    const byLabel = new Map<string, (typeof all)[0]>();
    for (const d of all) {
      const existing = byLabel.get(d.label);
      if (!existing || d.contribution_pct > existing.contribution_pct) {
        byLabel.set(d.label, d);
      }
    }
    return [...byLabel.values()]
      .sort((a, b) => b.contribution_pct - a.contribution_pct)
      .slice(0, 5);
  }, [metricExplanations]);

  // ── Derived: match ranges to explanations by metric_id ──
  const rangeMap = useMemo(() => {
    const m = new Map<string, RangeEstimate>();
    if (reliability?.ranges) {
      for (const r of reliability.ranges) {
        m.set(r.metric_id, r);
      }
    }
    return m;
  }, [reliability?.ranges]);

  // ── Derived: headline metrics (loss + URS) ──
  const headlineMetrics = useMemo(() => {
    if (!metricExplanations) return [];
    return metricExplanations.filter(
      (me) => me.metric_id === "projected_loss" || me.metric_id === "unified_risk_score",
    );
  }, [metricExplanations]);

  // ── Confidence as percentage ──
  const confPct = confidenceScore !== undefined
    ? Math.round(confidenceScore <= 1 ? confidenceScore * 100 : confidenceScore)
    : null;

  // ── Guard: nothing to show ──
  if (!metricExplanations?.length && confPct === null && !narrative) {
    return null;
  }

  return (
    <div
      className="border border-blue-200 bg-blue-50/40 rounded-lg overflow-hidden"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* ── Compact header (always visible) ── */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-blue-50/70 transition-colors"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3">
          {/* Chevron */}
          <svg
            className={`w-3.5 h-3.5 text-blue-500 transition-transform ${expanded ? "rotate-90" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>

          <span className="text-[11px] font-semibold text-blue-700 uppercase tracking-wider">
            {t("title", locale)}
          </span>
        </div>

        {/* Compact summary chips */}
        <div className="flex items-center gap-3">
          {/* Confidence chip */}
          {confPct !== null && (
            <span className={`text-[11px] font-bold tabular-nums ${confColor(confPct)}`}>
              {t("confidence", locale)}: {confPct}%
            </span>
          )}

          {/* Risk range chip for projected_loss */}
          {(() => {
            const lossRange = rangeMap.get("projected_loss");
            if (!lossRange) return null;
            return (
              <span className="text-[10px] text-slate-500 tabular-nums">
                {formatUsd(lossRange.low)} – {formatUsd(lossRange.high)}
              </span>
            );
          })()}

          {/* Top driver chip */}
          {topDrivers.length > 0 && (
            <span className="text-[10px] text-slate-500 truncate max-w-[160px]">
              {topDrivers[0].label} ({topDrivers[0].contribution_pct.toFixed(0)}%)
            </span>
          )}
        </div>
      </button>

      {/* ── Expanded detail ── */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-blue-200">

          {/* ── Section 1: Overall Confidence ── */}
          {confPct !== null && (
            <div className="pt-3">
              <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {t("confidence", locale)}
              </h4>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${confBarColor(confPct)}`}
                    style={{ width: `${confPct}%` }}
                  />
                </div>
                <span className={`text-sm font-bold tabular-nums ${confColor(confPct)}`}>
                  {confPct}%
                </span>
              </div>
            </div>
          )}

          {/* ── Section 2: Headline Range Bands ── */}
          {headlineMetrics.length > 0 && (
            <div>
              <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                {t("range", locale)}
              </h4>
              <div className="space-y-3">
                {headlineMetrics.map((me) => {
                  const range = rangeMap.get(me.metric_id);
                  if (!range) return null;
                  const spread = range.high - range.low || 1;
                  const basePos = ((range.base - range.low) / spread) * 100;

                  return (
                    <div key={me.metric_id}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-medium text-slate-600">{me.label}</span>
                        <span className="text-[9px] px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded font-medium">
                          {range.method} · {range.confidence}% {t("confLabel", locale)}
                        </span>
                      </div>
                      <div className="relative h-3 bg-slate-200 rounded-full overflow-visible">
                        <div className="absolute inset-y-0 bg-blue-200 rounded-full" style={{ left: "0%", right: "0%" }} />
                        <div
                          className="absolute top-0 bottom-0 w-1.5 bg-blue-600 rounded-full"
                          style={{ left: `${Math.max(0, Math.min(100, basePos))}%` }}
                        />
                      </div>
                      <div className="flex justify-between mt-0.5 text-[9px] text-slate-500 tabular-nums">
                        <span>{t("low", locale)}: {formatMetricValue(range.low, me.metric_id)}</span>
                        <span className="font-bold text-blue-700">{t("base", locale)}: {formatMetricValue(range.base, me.metric_id)}</span>
                        <span>{t("high", locale)}: {formatMetricValue(range.high, me.metric_id)}</span>
                      </div>
                      {range.notes && range.notes.length > 0 && (
                        <ul className="mt-1 space-y-0.5">
                          {range.notes.map((n, i) => (
                            <li key={i} className="text-[9px] text-slate-400 pl-2 border-l border-slate-200">{n}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Section 3: Top Drivers ── */}
          {topDrivers.length > 0 && (
            <div>
              <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                {t("drivers", locale)}
              </h4>
              <div className="space-y-2">
                {topDrivers.map((d, i) => {
                  const maxPct = topDrivers[0].contribution_pct || 1;
                  return (
                    <div key={i}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-[11px] font-medium text-slate-700">{d.label}</span>
                        <span className="text-[10px] text-slate-500 tabular-nums">{d.contribution_pct.toFixed(1)}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${(d.contribution_pct / maxPct) * 100}%` }}
                        />
                      </div>
                      <p className="text-[9px] text-slate-400 mt-0.5">{d.rationale}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ── Section 4: Narrative ── */}
          {narrative && (
            <div>
              <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                {t("narrative", locale)}
              </h4>
              <p className="text-[11px] text-slate-600 leading-relaxed">{narrative}</p>
            </div>
          )}

          {/* ── Section 5: Per-Metric Detail (MetricWhyCard instances) ── */}
          {metricExplanations && metricExplanations.length > 0 && (
            <div className="space-y-1 pt-2 border-t border-blue-100">
              {metricExplanations.map((me) => {
                const range = rangeMap.get(me.metric_id);
                const sensitivity = reliability?.sensitivities?.find(
                  (s) => s.variable_tested === me.metric_id || s.variable_tested === "severity",
                );
                const confAdj = reliability?.confidence_adjustments?.find(
                  (c) => c.metric_id === me.metric_id,
                );
                return (
                  <MetricWhyCard
                    key={me.metric_id}
                    explanation={me}
                    locale={locale}
                    range={range}
                    sensitivity={sensitivity}
                    confidenceAdjustment={confAdj}
                  />
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ExplainabilityPanel;
