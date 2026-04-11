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

import React, { Suspense, useState, useCallback, useMemo } from "react";
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

// ── Loading Skeleton ──

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin" />
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
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
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
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
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

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>
      {/* ── Intelligence Brief ── */}
      {scenario && headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {isAr ? "موجز الاستخبارات" : "Intelligence Brief"}
          </h2>

          {/* Headline Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <MetricCard
              label={isAr ? "الخسارة الرئيسية" : "Headline Loss"}
              value={`$${(headline.totalLossUsd / 1e9).toFixed(1)}B`}
              color="text-red-600"
            />
            <MetricCard
              label={isAr ? "متوسط الضغط" : "Avg Stress"}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-amber-600"
            />
            <MetricCard
              label={isAr ? "عمق الانتشار" : "Propagation Depth"}
              value={`${headline.propagationDepth}`}
              color="text-blue-700"
            />
            <MetricCard
              label={isAr ? "يوم الذروة" : "Peak Day"}
              value={`Day ${headline.peakDay}`}
              color="text-purple-600"
            />
          </div>

          {/* Narrative */}
          {(narrativeEn || narrativeAr) && (
            <div className="bg-slate-50 border border-slate-100 rounded-lg p-4 mb-4">
              <p className="text-sm text-slate-700 leading-relaxed">
                {isAr ? (narrativeAr || narrativeEn) : (narrativeEn || narrativeAr)}
              </p>
            </div>
          )}

          {/* System Risk + Confidence */}
          <div className="flex items-center gap-4 text-xs">
            {macroContext?.system_risk_index != null && (
              <span className="px-2 py-1 rounded bg-red-50 text-red-700 font-semibold">
                {isAr ? "مخاطر النظام" : "System Risk"}: {(macroContext.system_risk_index * 100).toFixed(0)}%
              </span>
            )}
            {confidence != null && (
              <span className="px-2 py-1 rounded bg-blue-50 text-blue-700 font-semibold">
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
  { label, value, color }: { label: string; value: string; color: string }
) {
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-lg font-bold ${color}`}>{value}</p>
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
            <span className="inline-block w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mr-2">
              1
            </span>
            {sectionLabel("Macro Shock", "الصدمة الكلية")}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label={sectionLabel("Headline Loss", "الخسارة الرئيسية")}
              value={`$${(headline.totalLossUsd / 1e9).toFixed(1)}B`}
              color="text-red-600"
            />
            <MetricCard
              label={sectionLabel("Avg Stress", "متوسط الضغط")}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-amber-600"
            />
            <MetricCard
              label={sectionLabel("Propagation Depth", "عمق الانتشار")}
              value={`${headline.propagationDepth}`}
              color="text-blue-700"
            />
            <MetricCard
              label={sectionLabel("Peak Day", "يوم الذروة")}
              value={`Day ${headline.peakDay}`}
              color="text-purple-600"
            />
          </div>
        </div>
      )}

      {/* 2. Transmission Channels */}
      {causalChain && causalChain.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mr-2">
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
            <span className="inline-block w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mr-2">
              3
            </span>
            {sectionLabel("Sector Impact", "تأثير القطاع")}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(sectorRollups).map(([sector, data]: any) => (
              <div key={sector} className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                  {sector}
                </p>
                <p className="text-sm font-bold text-slate-900">
                  {((data?.stress || 0) * 100).toFixed(0)}% stress
                </p>
                <p className="text-xs text-slate-600">
                  Loss: ${((data?.loss_usd || 0) / 1e9).toFixed(1)}B
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Entity Exposure */}
      {scenario && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4">
            <span className="inline-block w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mr-2">
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
            <span className="inline-block w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mr-2">
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
            <span className="inline-block w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mr-2">
              6
            </span>
            {sectionLabel("Value / ROI", "القيمة / العائد")}
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-sm text-slate-700">
              {sectionLabel("System Risk Index: ", "مؤشر مخاطر النظام: ")}
              <span className="font-semibold text-red-600">
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
          <span className="inline-block w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center mr-2">
            7
          </span>
          {sectionLabel("Trust / Confidence / Audit", "الثقة / الموثوقية / التدقيق")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {sectionLabel("Confidence", "الثقة")}
            </p>
            <p className="text-lg font-bold text-blue-700">
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
