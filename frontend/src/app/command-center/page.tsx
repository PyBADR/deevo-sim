"use client";

/**
 * Impact Observatory | مرصد الأثر — Command Center (White Enterprise Theme)
 *
 * RESTORED ARCHITECTURE:
 * ┌─────────────────────────────────────────────────────────────┐
 * │  OBSERVATORY SHELL (identity, language, scenario bar, tabs) │
 * ├─────────────────────────────────────────────────────────────┤
 * │  TAB: Dashboard     → Scenario Library + Intelligence Brief │
 * │  TAB: Scenarios     → Full ScenarioLibrary page             │
 * │  TAB: Macro         → MacroIntelligenceView (top-down flow) │
 * │  TAB: Propagation   → Causal chain flow diagram             │
 * │  TAB: Map           → GCC 6-country impact map              │
 * │  TAB: Sectors       → Banking / Insurance / Fintech stress  │\n * │  TAB: Decisions     → DecisionRoomV2 (full decision engine) │\n * │  TAB: Audit         → Audit trail + regulatory breaches     │\n * └─────────────────────────────────────────────────────────────┘\n *\n * Scenario context is preserved across all tabs via URL params.\n * Data flow: useCommandCenter(runId) feeds all views.\n */

import React, { Suspense, useState, useCallback, useMemo, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAppStore } from "@/store/app-store";
import { useCommandCenter } from "@/features/command-center/lib/use-command-center";

// ── Shell & Navigation ──
import { ObservatoryShell } from "@/components/shell/ObservatoryShell";

// ── Tab: Dashboard (Scenario Library + Brief) ──
import { ScenarioLibrary } from "@/components/scenario/ScenarioLibrary";
import { ScenarioSelector } from "@/components/scenario/ScenarioSelector";

// ── Tab: Decision Room ──
import { DecisionRoomV2 } from "@/components/provenance/DecisionRoomV2";

// ── Tab: Impact Map ──
import { GCCImpactMap } from "@/components/map/GCCImpactMap";

// ── Tab: Propagation ──
import { PropagationView } from "@/components/panels/PropagationView";

// ── Tab: Sector Intelligence ──
import { SectorIntelligenceView } from "@/components/panels/SectorIntelligenceView";

// ── Tab: Regulatory / Audit ──
import { RegulatoryAuditView } from "@/components/panels/RegulatoryAuditView";

// ── Operational Deep-Dive (existing) ──
import { StatusBar } from "@/features/command-center/components/StatusBar";

// ── PDF Export ──

const IO_API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

function exportErrorMessage(status: number): string {
  if (status === 404) return "Report not found. Please re-run the scenario and try again.";
  if (status === 425) return "Report is still generating. Please wait a moment and try again.";
  if (status === 403) return "Report export requires elevated permissions.";
  if (status >= 500) return "Export service temporarily unavailable.";
  return "Report export could not be completed.";
}

async function downloadRunPDF(runId: string, lang: string): Promise<void> {
  const res = await fetch(`/api/v1/runs/${runId}/export?lang=${lang}`, {
    headers: { "X-IO-API-Key": IO_API_KEY },
  });
  if (!res.ok) throw new Error(exportErrorMessage(res.status));
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `impact-observatory-${runId.slice(0, 8)}-${lang}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Loading Skeleton ──

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-io-bg flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-io-accent/30 border-t-io-accent rounded-full animate-spin" />
        <p className="text-sm text-slate-500">Loading intelligence pipeline...</p>
      </div>
    </div>
  );
}

// ── Error State ──

function ErrorState(
  {
    error,
    onRetry,
    onFallbackMock,
  }: {
    error: string;
    onRetry?: () => void;
    onFallbackMock?: () => void;
  }
) {
  return (
    <div className="min-h-screen bg-io-bg flex items-center justify-center">
      <div className="max-w-md text-center px-6">
        <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center mx-auto mb-4">
          <span className="text-red-600 text-lg">!</span>
        </div>
        <h2 className="text-sm font-semibold text-slate-900 mb-2">Pipeline Error</h2>
        <p className="text-xs text-slate-600 mb-4">{error}</p>
        <div className="flex items-center justify-center gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-io-accent text-white hover:bg-io-accent-hover transition-colors"
            >
              Retry
            </button>
          )}
          {onFallbackMock && (
            <button
              onClick={onFallbackMock}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              Load Demo Data
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// DASHBOARD TAB — Scenario Library + Intelligence Brief
// ══════════════════════════════════════════════════════════════

function DashboardView(
  {
    runId,
    scenario,
    headline,
    narrativeEn,
    narrativeAr,
    macroContext,
    confidence,
    causalChain,
    sectorRollups,
    decisionActions,
    locale,
    onSelectScenario,
    isRunningScenario,
  }: {
    runId?: string | null;
    scenario: ReturnType<typeof useCommandCenter>["scenario"];
    headline: ReturnType<typeof useCommandCenter>["headline"];
    narrativeEn?: string;
    narrativeAr?: string;
    macroContext?: ReturnType<typeof useCommandCenter>["macroContext"];
    confidence?: number;
    causalChain: ReturnType<typeof useCommandCenter>["causalChain"];
    sectorRollups: ReturnType<typeof useCommandCenter>["sectorRollups"];
    decisionActions: ReturnType<typeof useCommandCenter>["decisionActions"];
    locale: "en" | "ar";
    onSelectScenario: (id: string) => void;
    isRunningScenario: boolean;
  }
) {
  const isAr = locale === "ar";
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExportPDF = useCallback(async () => {
    if (!runId) return;
    setIsExporting(true);
    setExportError(null);
    try {
      await downloadRunPDF(runId, locale);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setIsExporting(false);
    }
  }, [runId, locale]);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Executive Intelligence Brief ── */}
      {scenario && headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-slate-900">
              {isAr ? "الإحاطة التنفيذية" : "Executive Briefing"}
            </h2>
            <div className="flex items-center gap-3">
              <span className="text-xs text-io-secondary">
                {isAr ? scenario.labelAr || scenario.label : scenario.label}
              </span>
              {runId && (
                <button
                  onClick={handleExportPDF}
                  disabled={isExporting}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg border border-io-border bg-white text-io-primary hover:bg-slate-50 transition-colors disabled:opacity-50"
                >
                  {isExporting ? (
                    <>
                      <span className="w-3 h-3 border border-io-secondary/40 border-t-io-secondary rounded-full animate-spin" />
                      {isAr ? "جارٍ التصدير..." : "Exporting..."}
                    </>
                  ) : (
                    <>
                      <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 10v3a1 1 0 01-1 1H3a1 1 0 01-1-1v-3M8 2v8M5 7l3 3 3-3" />
                      </svg>
                      {isAr ? "تصدير التقرير" : "Export Report"}
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
          {exportError && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
              {exportError}
            </div>
          )}

          {/* Executive Summary Line */}
          <div className="bg-io-accent/5 border border-io-accent/15 rounded-lg p-4 mb-5">
            <p className="text-sm text-slate-800 leading-relaxed">
              {isAr
                ? (narrativeAr || narrativeEn || `خسائر متوقعة بقيمة $${(headline.totalLossUsd / 1e9).toFixed(1)} مليار عبر ${headline.propagationDepth} قنوات انتقال — ذروة الضغط في اليوم ${headline.peakDay}`)
                : (narrativeEn || narrativeAr || `$${(headline.totalLossUsd / 1e9).toFixed(1)}B projected loss across ${headline.propagationDepth} transmission channels — stress peaks Day ${headline.peakDay}`)}
            </p>
          </div>

          {/* Headline Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
            <MetricCard
              label={isAr ? "الخسارة الرئيسية" : "Headline Loss"}
              value={`$${(headline.totalLossUsd / 1e9).toFixed(1)}B`}
              color="text-io-status-severe"
              source="17-stage simulation engine"
              formula="Σ(node_loss) across 42-node GCC graph"
              assumption="Severity-calibrated; Monte Carlo confidence band ±8-12%"
            />
            <MetricCard
              label={isAr ? "متوسط الضغط" : "Avg Stress"}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-io-status-elevated"
              source="Graph propagation engine"
              formula="mean(node.stress) for all impacted nodes"
              assumption="Stress range 0-100%; ≥80% = Severe, ≥65% = High"
            />
            <MetricCard
              label={isAr ? "عمق الانتشار" : "Propagation Depth"}
              value={`${headline.propagationDepth}`}
              color="text-io-accent"
              source="Causal chain trace"
              formula="Max hop count in transmission path"
              assumption="Deeper propagation = wider systemic exposure"
            />
            <MetricCard
              label={isAr ? "يوم الذروة" : "Peak Day"}
              value={`${isAr ? "اليوم" : "Day"} ${headline.peakDay}`}
              color="text-io-status-high"
              source="Scenario peak_day_offset"
              formula="min(scenario.peak_day_offset, horizon_days)"
              assumption="Assumes no secondary shock after initial event"
            />
          </div>

          {/* Propagation Summary — elevated per Sarah's directive */}
          {causalChain && causalChain.length > 0 && (
            <div className="border border-slate-200 rounded-lg p-4 mb-5">
              <h3 className="text-xs font-semibold text-io-secondary uppercase tracking-wider mb-3">
                {isAr ? "مسار الانتقال الرئيسي" : "Primary Transmission Path"}
              </h3>
              <div className="flex items-center gap-2 overflow-x-auto pb-1">
                {causalChain.slice(0, 5).map((step, idx) => (
                  <React.Fragment key={idx}>
                    <div className="flex-shrink-0 bg-slate-50 rounded-lg px-3 py-2 text-center min-w-[100px]">
                      <p className="text-xs font-semibold text-slate-900 truncate">{step.entity_label}</p>
                      <p className="text-[10px] text-io-status-elevated tabular-nums mt-0.5">
                        {step.stress_delta > 0 ? "+" : ""}{(step.stress_delta * 100).toFixed(0)}%
                      </p>
                    </div>
                    {idx < Math.min(causalChain.length, 5) - 1 && (
                      <span className="text-io-accent text-xs flex-shrink-0">→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* Top Decision — owner/timing per Sarah */}
          {decisionActions && decisionActions.length > 0 && (() => {
            const top = [...decisionActions].sort((a: any, b: any) => a.priority - b.priority)[0] as any;
            return (
              <div className="border border-io-accent/20 bg-io-accent/5 rounded-lg p-4 mb-5">
                <h3 className="text-xs font-semibold text-io-secondary uppercase tracking-wider mb-2">
                  {isAr ? "القرار الأول — مطلوب الآن" : "Priority Decision — Required Now"}
                </h3>
                <p className="text-sm font-semibold text-slate-900 mb-2">
                  {isAr && top.action_ar ? top.action_ar : top.action}
                </p>
                <div className="flex flex-wrap gap-3 text-xs text-io-secondary">
                  {top.owner && (
                    <span><span className="font-medium text-slate-700">{isAr ? "المسؤول:" : "Owner:"}</span> {top.owner}</span>
                  )}
                  {top.time_to_act_hours != null && (
                    <span><span className="font-medium text-slate-700">{isAr ? "الوقت المتاح:" : "Window:"}</span> {top.time_to_act_hours}h</span>
                  )}
                  {top.loss_avoided_usd > 0 && (
                    <span><span className="font-medium text-slate-700">{isAr ? "خسائر متجنبة:" : "Loss avoided:"}</span> ${(top.loss_avoided_usd / 1e9).toFixed(1)}B</span>
                  )}
                  {top.cost_usd > 0 && (
                    <span><span className="font-medium text-slate-700">{isAr ? "التكلفة:" : "Cost:"}</span> ${(top.cost_usd / 1e6).toFixed(0)}M</span>
                  )}
                </div>
              </div>
            );
          })()}

          {/* System Risk + Confidence */}
          <div className="flex items-center gap-4 text-xs">
            {macroContext?.system_risk_index != null && (
              <span className="px-2 py-1 rounded bg-io-status-severe/10 text-io-status-severe font-semibold">
                {isAr ? "مخاطر النظام" : "System Risk"}: {(macroContext.system_risk_index * 100).toFixed(0)}%
              </span>
            )}
            {confidence != null && (
              <span className="px-2 py-1 rounded bg-io-accent/10 text-io-accent font-semibold">
                {isAr ? "الثقة" : "Confidence"}: {(confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── Scenario Library ── */}
      <div>
        <h2 className="text-base font-bold text-slate-900 mb-4">
          {isAr ? "مكتبة السيناريوهات" : "Scenario Library"}
        </h2>
        <ScenarioLibrary
          onSelectScenario={onSelectScenario}
          isLoading={isRunningScenario}
          locale={locale}
        />
      </div>
    </div>
  );
}

function MetricCard(
  { label, value, color, source, formula, assumption }: {
    label: string;
    value: string;
    color: string;
    source?: string;
    formula?: string;
    assumption?: string;
  }
) {
  const [showDetail, setShowDetail] = useState(false);
  const hasProvenance = source || formula || assumption;

  return (
    <div
      className="bg-slate-50 rounded-lg p-3 relative group"
      onMouseEnter={() => hasProvenance && setShowDetail(true)}
      onMouseLeave={() => setShowDetail(false)}
    >
      <div className="flex items-start justify-between">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{label}</p>
        {hasProvenance && (
          <span className="text-[8px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
            ⓘ
          </span>
        )}
      </div>
      <p className={`text-lg font-bold ${color}`}>{value}</p>
      {showDetail && hasProvenance && (
        <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-[10px] text-slate-600 space-y-1">
          {source && <p><span className="font-semibold text-slate-700">Source:</span> {source}</p>}
          {formula && <p><span className="font-semibold text-slate-700">Formula:</span> {formula}</p>}
          {assumption && <p><span className="font-semibold text-slate-700">Assumption:</span> {assumption}</p>}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// MACRO INTELLIGENCE VIEW — Top-down flow with enterprise cards
// ══════════════════════════════════════════════════════════════

function MacroIntelligenceView(
  {
    scenario,
    headline,
    narrativeEn,
    narrativeAr,
    macroContext,
    confidence,
    causalChain,
    sectorRollups,
    decisionActions,
    trust,
    locale,
  }: {
    scenario: ReturnType<typeof useCommandCenter>["scenario"];
    headline: ReturnType<typeof useCommandCenter>["headline"];
    narrativeEn?: string;
    narrativeAr?: string;
    macroContext?: ReturnType<typeof useCommandCenter>["macroContext"];
    confidence?: number;
    causalChain: ReturnType<typeof useCommandCenter>["causalChain"];
    sectorRollups: ReturnType<typeof useCommandCenter>["sectorRollups"];
    decisionActions: ReturnType<typeof useCommandCenter>["decisionActions"];
    trust?: ReturnType<typeof useCommandCenter>["trust"];
    locale: "en" | "ar";
  }
) {
  const isAr = locale === "ar";

  const sectionLabel = (en: string, ar: string) => (isAr ? ar : en);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>
      {/* 1. Macro Shock */}
      {headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              1
            </span>
            {sectionLabel("Macro Shock", "الصدمة الكلية")}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label={sectionLabel("Headline Loss", "الخسارة الرئيسية")}
              value={`$${(headline.totalLossUsd / 1e9).toFixed(1)}B`}
              color="text-io-status-severe"
            />
            <MetricCard
              label={sectionLabel("Avg Stress", "متوسط الضغط")}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-io-status-elevated"
            />
            <MetricCard
              label={sectionLabel("Propagation Depth", "عمق الانتشار")}
              value={`${headline.propagationDepth}`}
              color="text-io-accent"
            />
            <MetricCard
              label={sectionLabel("Peak Day", "يوم الذروة")}
              value={`Day ${headline.peakDay}`}
              color="text-io-status-high"
            />
          </div>
        </div>
      )}

      {/* 1b. Macro Indicators — enriched institutional panel */}
      {macroContext && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              &#9670;
            </span>
            {sectionLabel("Macro-Financial Indicators", "المؤشرات الاقتصادية والمالية الكلية")}
          </h3>
          {/* Real macro signals from the pipeline — shown when available */}
          {macroContext.macro_signals && macroContext.macro_signals.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {macroContext.macro_signals.slice(0, 8).map((sig: any) => (
                <div key={sig.id || sig.name_en} className="bg-slate-50 rounded-lg p-2.5 group relative">
                  <p className="text-[9px] text-slate-500 uppercase tracking-wider mb-0.5">
                    {isAr ? sig.name_ar : sig.name_en}
                  </p>
                  <p className={`text-sm font-bold tabular-nums ${
                    sig.impact === "high" ? "text-io-status-severe"
                    : sig.impact === "medium" ? "text-io-status-elevated"
                    : "text-io-status-guarded"
                  }`}>
                    {sig.value}
                  </p>
                  <p className="text-[8px] text-slate-400 mt-0.5">
                    {isAr ? "من محرك المحاكاة" : "From simulation engine"}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            /* Derived indicators when no macro signals available */
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <MetricCard
                label={sectionLabel("System Risk Index", "مؤشر المخاطر")}
                value={`${(macroContext.system_risk_index * 100).toFixed(0)}%`}
                color="text-io-status-high"
                source="Unified Risk Score (URS)"
                formula="Weighted avg of sector stress indices"
              />
              <MetricCard
                label={sectionLabel("Contagion Risk", "مخاطر العدوى")}
                value={`${(macroContext.system_risk_index * 100).toFixed(0)}%`}
                color="text-io-status-elevated"
                source="Graph propagation depth"
                formula="Correlated with system_risk_index"
              />
            </div>
          )}
        </div>
      )}

      {/* 2. Transmission Channels */}
      {causalChain && causalChain.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              2
            </span>
            {sectionLabel("Transmission Channels", "قنوات الانتقال")}
          </h3>
          <div className="space-y-2">
            {causalChain.slice(0, 5).map((link, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-slate-50 p-3 rounded-lg">
                <div className="text-xs font-semibold text-slate-500 mt-0.5">→</div>
                <div className="flex-1">
                  <p className="text-sm text-slate-700">{link.entity_label}: {link.event}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Sector Impact */}
      {sectorRollups && Object.keys(sectorRollups).length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              3
            </span>
            {sectionLabel("Sector Impact", "تأثير القطاع")}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(sectorRollups).map(([sector, data]: any) => {
              const stress = data?.aggregate_stress ?? data?.stress ?? 0;
              const loss = data?.total_loss ?? data?.loss_usd ?? 0;
              const sectorLabel = sector.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase());
              return (
                <div key={sector} className="bg-slate-50 rounded-lg p-3 group relative">
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                    {sectorLabel}
                  </p>
                  <p className="text-sm font-bold text-slate-900">
                    {(stress * 100).toFixed(0)}% stress
                  </p>
                  <p className="text-xs text-slate-600">
                    {loss > 0 ? `Loss: $${(loss / 1e9).toFixed(1)}B` : ""}
                  </p>
                  <p className="text-[8px] text-slate-400 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {isAr ? "التخصيص × الإجهاد × الانتشار" : "allocation × stress × propagation weight"}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 4. Entity Exposure */}
      {scenario && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              4
            </span>
            {sectionLabel("Entity Exposure", "تعريض الكيانات")}
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-sm text-slate-700">
              {isAr
                ? `السيناريو: ${scenario.labelAr || scenario.label}`
                : `Scenario: ${scenario.label}`}
            </p>
            <p className="text-xs text-slate-600 mt-2">
              {isAr ? "الحساسية: " : "Sensitivity: "}
              <span className="font-semibold text-slate-700">
                {scenario.severity != null ? `${(scenario.severity * 100).toFixed(0)}%` : "N/A"}
              </span>
            </p>
          </div>
        </div>
      )}

      {/* 5. Decision Actions */}
      {decisionActions && decisionActions.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              5
            </span>
            {sectionLabel("Decision Actions", "إجراءات القرار")}
          </h3>
          <div className="space-y-2">
            {decisionActions.slice(0, 5).map((action: any, idx: number) => (
              <div key={idx} className="bg-slate-50 p-3 rounded-lg">
                <p className="text-sm font-semibold text-slate-900">
                  {action.title || action.label || `Action ${idx + 1}`}
                </p>
                {action.rationale && (
                  <p className="text-xs text-slate-600 mt-1">{action.rationale}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Value / ROI */}
      {macroContext && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
              6
            </span>
            {sectionLabel("Value / ROI", "القيمة / العائد")}
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-sm text-slate-700">
              {sectionLabel("System Risk Index: ", "مؤشر مخاطر النظام: ")}
              <span className="font-semibold text-io-status-severe">
                {(macroContext?.system_risk_index || 0) * 100 || "N/A"}%
              </span>
            </p>
            {macroContext?.macro_signals && (
              <p className="text-xs text-slate-600 mt-2">
                {isAr ? "الإشارات: " : "Signals: "}
                {Array.isArray(macroContext.macro_signals)
                  ? macroContext.macro_signals.join(", ")
                  : String(macroContext.macro_signals)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* 7. Trust / Confidence / Audit */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-4">
          <span className="inline-block w-6 h-6 rounded-full bg-io-accent/15 text-io-accent text-xs font-bold flex items-center justify-center mr-2">
            7
          </span>
          {sectionLabel("Trust / Confidence / Audit", "الثقة / الموثوقية / التدقيق")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Confidence", "الثقة")}
            </p>
            <p className="text-lg font-bold text-io-accent">
              {confidence != null ? `${(confidence * 100).toFixed(0)}%` : "N/A"}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Methodology", "المنهجية")}
            </p>
            <p className="text-xs text-slate-600">
              {(trust as any)?.methodology_confidence
                ? `${((trust as any).methodology_confidence * 100).toFixed(0)}% confidence`
                : "Standard pipeline"}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Data Quality", "جودة البيانات")}
            </p>
            <p className="text-xs text-slate-600">
              {(trust as any)?.data_quality_score
                ? `${((trust as any).data_quality_score * 100).toFixed(0)}% quality`
                : "Enterprise grade"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// INNER PAGE — reads searchParams, orchestrates tabs
// ══════════════════════════════════════════════════════════════

function CommandCenterInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const language = useAppStore((s) => s.language);
  const locale = language as "en" | "ar";

  const runId = searchParams.get("run");
  const activeTab = searchParams.get("tab") || "dashboard";
  const [isRunningScenario, setIsRunningScenario] = useState(false);

  const {
    status,
    error,
    dataSource,
    scenario,
    headline,
    causalChain,
    sectorRollups,
    decisionActions,
    graphNodes,
    sectorImpacts,
    impacts,
    narrativeEn,
    confidence,
    trust,

    // Deep-dive data
    decisionTrust,
    decisionIntegration,
    decisionValue,
    governance,
    pilot,

    // Decision Trust Layer
    metricExplanations,
    decisionTransparencyResult,

    // Decision Reliability Layer
    reliabilityPayload,

    // Explainability Layer
    narrativeAr,
    macroContext,

    // Actions
    executeAction,
    switchToMock,
    switchToLive,
  } = useCommandCenter(runId);

  // ── Scenario selection: POST /api/v1/runs → navigate to new run ──
  const handleScenarioSelect = useCallback(
    async (templateId: string) => {
      setIsRunningScenario(true);
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
        const res = await fetch(`${API_BASE}/api/v1/runs`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ template_id: templateId, severity: 0.75 }),
        });
        const json = await res.json();
        const newRunId = json?.data?.run_id ?? json?.run_id;
        if (newRunId) {
          router.push(`/command-center?run=${newRunId}`);
        }
      } catch {
        switchToMock();
      } finally {
        setIsRunningScenario(false);
      }
    },
    [router, switchToMock],
  );

  const handleSubmitForReview = useCallback(
    (actionId: string) => {
      executeAction(actionId);
    },
    [executeAction],
  );

  // ── State gates ──
  if (status === "loading") return <LoadingSkeleton />;
  if (status === "error" && !scenario) {
    return (
      <ErrorState
        error={error ?? "Unknown error"}
        onRetry={runId ? () => switchToLive(runId) : undefined}
        onFallbackMock={switchToMock}
      />
    );
  }

  // ── Derive country exposures from impacts for the map ──
  const countryExposures = useMemo(() => {
    if (!impacts?.length) return undefined;
    const exposures: Record<
      string,
      { stressLevel: number; lossUsd: number; dominantSector: string; entities: string[] }
    > = {};

    // Map sector-level impacts to countries
    const sectorToCountry: Record<string, string[]> = {
      banking: ["SA", "AE", "BH"],
      insurance: ["SA", "AE", "QA"],
      fintech: ["AE", "SA", "BH"],
      energy: ["SA", "QA", "KW"],
      logistics: ["OM", "AE", "QA"],
    };

    for (const impact of impacts) {
      const countries = sectorToCountry[impact.sector] || ["SA"];
      for (const cc of countries) {
        if (!exposures[cc]) {
          exposures[cc] = {
            stressLevel: 0,
            lossUsd: 0,
            dominantSector: impact.sector,
            entities: [],
          };
        }
        exposures[cc].stressLevel = Math.max(exposures[cc].stressLevel, impact.stressLevel);
        exposures[cc].lossUsd += (impact.lossUsd || 0) / countries.length;
      }
    }
    return Object.keys(exposures).length > 0 ? exposures : undefined;
  }, [impacts]);

  // ── Render active tab content ──
  const renderTabContent = () => {
    switch (activeTab) {
      case "scenarios":
        return (
          <div className="p-6 max-w-7xl mx-auto">
            <ScenarioLibrary
              onSelectScenario={handleScenarioSelect}
              isLoading={isRunningScenario}
              locale={locale}
            />
          </div>
        );

      case "macro":
        if (!scenario || !headline) {
          return (
            <div className="flex items-center justify-center h-96 text-slate-500 text-sm">
              {locale === "ar"
                ? "لا توجد بيانات سيناريو — اختر سيناريو من لوحة المعلومات"
                : "No scenario data — select a scenario from the Dashboard"}
            </div>
          );
        }
        return (
          <MacroIntelligenceView
            scenario={scenario}
            headline={headline}
            narrativeEn={narrativeEn}
            narrativeAr={narrativeAr}
            macroContext={macroContext}
            confidence={confidence}
            causalChain={causalChain}
            sectorRollups={sectorRollups}
            decisionActions={decisionActions}
            trust={trust}
            locale={locale}
          />
        );

      case "propagation":
        return (
          <PropagationView
            locale={locale}
            scenarioLabel={scenario?.label}
            scenarioLabelAr={scenario?.labelAr ?? undefined}
            severity={scenario?.severity}
            totalLossUsd={headline?.totalLossUsd}
            causalChain={causalChain}
          />
        );

      case "map":
        return (
          <div className="p-6 max-w-7xl mx-auto">
            <GCCImpactMap
              countryExposures={countryExposures}
              sectorRollups={
                sectorRollups as unknown as
                  | Record<string, { stress: number; loss_usd: number }>
                  | undefined
              }
              scenarioLabel={scenario?.label}
              locale={locale}
            />
          </div>
        );

      case "sectors":
        return (
          <SectorIntelligenceView
            locale={locale}
            scenarioLabel={scenario?.label}
            scenarioLabelAr={scenario?.labelAr ?? undefined}
            severity={scenario?.severity}
            narrativeEn={narrativeEn}
            narrativeAr={narrativeAr ?? undefined}
            systemRiskIndex={macroContext?.system_risk_index}
            macroSignals={macroContext?.macro_signals}
            causalChain={causalChain}
            decisionActions={decisionActions as any}
          />
        );

      case "decisions":
        if (!scenario || !headline) {
          return (
            <div className="flex items-center justify-center h-96 text-slate-500 text-sm">
              {locale === "ar"
                ? "لا توجد بيانات سيناريو — اختر سيناريو من لوحة المعلومات"
                : "No scenario data — select a scenario from the Dashboard"}
            </div>
          );
        }
        return (
          <div className="p-6">
            <DecisionRoomV2
              runId={runId ?? undefined}
              scenarioLabel={scenario.label}
              scenarioLabelAr={scenario.labelAr ?? ""}
              severity={String(scenario.severity)}
              totalLossUsd={headline.totalLossUsd}
              averageStress={headline.averageStress}
              propagationDepth={headline.propagationDepth}
              peakDay={headline.peakDay}
              causalChain={causalChain}
              decisionActions={decisionActions}
              sectorRollups={sectorRollups}
              locale={locale}
              metricExplanations={metricExplanations}
              decisionTransparency={decisionTransparencyResult ?? undefined}
              reliability={reliabilityPayload ?? undefined}
              confidenceScore={confidence}
              narrativeEn={narrativeEn}
              narrativeAr={narrativeAr ?? ""}
              macroContext={macroContext ?? undefined}
              trustInfo={trust ?? undefined}
              onSubmitForReview={handleSubmitForReview}
            />
          </div>
        );

      case "audit":
        return (
          <RegulatoryAuditView
            locale={locale}
            runId={runId ?? undefined}
            scenarioLabel={scenario?.label}
            scenarioLabelAr={scenario?.labelAr ?? undefined}
            severity={scenario?.severity}
            horizonHours={scenario?.horizonHours}
            trustInfo={trust ?? undefined}
            decisionActions={decisionActions}
          />
        );

      // Dashboard (default)
      default:
        return (
          <DashboardView
            runId={runId}
            scenario={scenario}
            headline={headline}
            narrativeEn={narrativeEn}
            narrativeAr={narrativeAr ?? undefined}
            macroContext={macroContext}
            confidence={confidence}
            causalChain={causalChain}
            sectorRollups={sectorRollups}
            decisionActions={decisionActions}
            locale={locale}
            onSelectScenario={handleScenarioSelect}
            isRunningScenario={isRunningScenario}
          />
        );
    }
  };

  return (
    <ObservatoryShell
      scenarioLabel={scenario?.label}
      scenarioLabelAr={scenario?.labelAr ?? undefined}
      dataSource={dataSource}
      activeTab={activeTab}
    >
      {/* Fallback banner (API failed, showing mock) */}
      {error && scenario && (
        <div className="flex items-center justify-between px-4 py-1.5 bg-amber-50 border-b border-amber-200 flex-shrink-0">
          <p className="text-[11px] text-amber-700 truncate">{error}</p>
          {runId && (
            <button
              onClick={() => switchToLive(runId)}
              className="ml-3 flex-shrink-0 px-3 py-1 text-[10px] font-semibold rounded bg-amber-100 text-amber-800 hover:bg-amber-200 transition-colors"
            >
              Retry Live
            </button>
          )}
        </div>
      )}

      {/* Scenario quick-switcher (compact pill bar) */}
      {scenario && activeTab !== "dashboard" && (
        <div className="px-6 pt-3">
          <ScenarioSelector
            activeScenarioId={scenario.templateId}
            onSelect={handleScenarioSelect}
            isLoading={isRunningScenario}
            locale={locale}
          />
        </div>
      )}

      {/* Active tab content */}
      {renderTabContent()}

      {/* Status Bar */}
      <StatusBar dataSource={dataSource} trust={trust} confidence={confidence} />
    </ObservatoryShell>
  );
}

// ── Page Export ──

export default function CommandCenterPage() {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <CommandCenterInner />
    </Suspense>
  );
}
