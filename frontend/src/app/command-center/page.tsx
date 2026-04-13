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

// ── Tab: Intelligence Reading Surface ──
import { IntelligenceSurface } from "@/components/intelligence";

// ── Operational Deep-Dive (existing) ──
import { StatusBar } from "@/features/command-center/components/StatusBar";

// ── V2.1 Upgrades ──
import {
  RoleSwitcher,
  DecisionClock,
  EscalationBanner,
  RangeLossCard,
  CompactAssumptions,
  EnhancedSectorCard,
  ActionOwnerCard,
  ROLE_SECTOR_FOCUS,
  ROLE_HEADLINE,
  type ExecutiveRole,
} from "@/features/command-center/components/V21Upgrades";
import type { CountryExposureEntry, OutcomeScenario, ScenarioKey, ScenarioPreset } from "@/features/command-center/lib/mock-data";
import type { DerivedLossRange, DerivedOutcomes } from "@/features/command-center/lib/derive-briefing";

// ── Sector label helper ──

const SECTOR_LABELS: Record<string, string> = {
  energy: "Oil & Gas",
  banking: "Banking",
  insurance: "Insurance",
  fintech: "Fintech",
  real_estate: "Real Estate",
  government: "Government",
  trade: "Trade",
};
function sectorLabel(key: string): string {
  return SECTOR_LABELS[key] ?? key.charAt(0).toUpperCase() + key.slice(1);
}

// ── Loading Skeleton ──

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-8 h-8 border-2 border-blue-600/30 border-t-blue-600 rounded-full animate-spin" />
        <p className="text-sm text-slate-500">Loading intelligence briefing...</p>
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
        <h2 className="text-sm font-semibold text-slate-900 mb-2">Connection Error</h2>
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
// DASHBOARD TAB — 9-Layer Executive Briefing
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
    role,
    trust,
    lossRange,
    deadline,
    assumptions,
    sectorDepth,
    countryExposures,
    outcomes,
    methodology,
    graphNodes,
    scenarioPresets,
    onSwitchScenario,
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
    role: ExecutiveRole;
    trust?: ReturnType<typeof useCommandCenter>["trust"];
    lossRange: DerivedLossRange;
    deadline: string;
    assumptions: string[];
    sectorDepth: Record<string, { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }>;
    countryExposures: CountryExposureEntry[];
    outcomes: DerivedOutcomes;
    methodology: string;
    graphNodes?: ReturnType<typeof useCommandCenter>["graphNodes"];
    scenarioPresets: ScenarioPreset[];
    onSwitchScenario: (key: ScenarioKey) => void;
  }
) {
  const isAr = locale === "ar";
  const roleLabel = ROLE_HEADLINE[role];
  const focusSectors = ROLE_SECTOR_FOCUS[role];
  const L = (en: string, ar: string) => (isAr ? ar : en);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>

      {/* ═══ SCENARIO SWITCHER ═══ */}
      <div className="flex items-center justify-between">
        <ScenarioSwitcherPills
          presets={scenarioPresets}
          activeTemplateId={scenario?.templateId}
          onSwitch={onSwitchScenario}
          onRunLive={onSelectScenario}
          isRunning={isRunningScenario}
          locale={locale}
        />
      </div>

      {/* ═══ LAYER 1: Macro State ═══ */}
      {scenario && headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-start justify-between mb-5">
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                {L("Layer 1", "الطبقة 1")}
              </p>
              <h2 className="text-base font-bold text-slate-900">
                {isAr ? roleLabel.labelAr : roleLabel.labelEn}
              </h2>
            </div>
            <DecisionClock deadlineIso={deadline} locale={locale} />
          </div>

          {/* Pathway headline — above financial loss */}
          <PathwayHeadline causalChain={causalChain} scenario={scenario} locale={locale} />

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <RangeLossCard
              lossLow={lossRange.low}
              lossMid={lossRange.mid}
              lossHigh={lossRange.high}
              confidencePct={lossRange.confidence_pct}
              locale={locale}
            />
            <MetricCard
              label={L("Average Stress Level", "متوسط مستوى الضغط")}
              value={`${(headline.averageStress * 100).toFixed(0)}%`}
              color="text-amber-600"
            />
            <MetricCard
              label={L("Transmission Depth", "عمق الانتقال")}
              value={`${headline.propagationDepth} ${L("layers", "طبقات")}`}
              color="text-blue-700"
            />
            <MetricCard
              label={L("Peak Stress Day", "يوم ذروة الضغط")}
              value={`${L("Day", "اليوم")} ${headline.peakDay}`}
              color="text-purple-600"
            />
          </div>

          {/* Executive narrative */}
          {(narrativeEn || narrativeAr) && (
            <div className="bg-slate-50 border border-slate-100 rounded-lg p-4 mb-4">
              <p className="text-sm text-slate-700 leading-relaxed">
                {isAr ? (narrativeAr || narrativeEn) : (narrativeEn || narrativeAr)}
              </p>
            </div>
          )}

          {confidence != null && (
            <div className="flex items-center gap-4 text-xs">
              <span className="px-2 py-1 rounded bg-blue-50 text-blue-700 font-semibold">
                {L("Confidence", "الثقة")}: {(confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* ═══ LAYER 2: Propagation — How the Shock Transmits ═══ */}
      {causalChain && causalChain.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
            {L("Layer 2 — Primary Headline", "الطبقة 2 — العنوان الرئيسي")}
          </p>
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {L("How the Disruption Transmits", "كيف ينتقل الاضطراب")}
          </h2>
          <div className="space-y-2">
            {causalChain.slice(0, 5).map((link, idx) => {
              const gNode = graphNodes?.find((n: any) => n.id === link.entity_id);
              return (
                <div key={idx} className="flex items-start gap-3 bg-slate-50 p-3 rounded-lg">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-200 text-slate-600 text-xs font-bold flex items-center justify-center mt-0.5">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-slate-800">{isAr ? link.entity_label_ar : link.entity_label}</p>
                    <p className="text-sm text-slate-600 mt-0.5">{isAr ? link.event_ar : link.event}</p>
                    {link.impact_usd > 0 && (
                      <p className="text-xs text-red-600 font-semibold mt-1">
                        ${(link.impact_usd / 1e9).toFixed(2)}B {L("exposure", "تعرض")}
                      </p>
                    )}
                    {/* Entity graph backing */}
                    {gNode && (
                      <div className="flex items-center gap-3 mt-2 pt-2 border-t border-slate-200">
                        <EntityGraphBadge label={L("Layer", "الطبقة")} value={gNode.layer} />
                        <EntityGraphBadge label={L("Type", "النوع")} value={gNode.type.replace(/_/g, " ")} />
                        <EntityGraphBadge
                          label={L("Stress", "الضغط")}
                          value={`${((gNode.stress ?? 0) * 100).toFixed(0)}%`}
                          color={
                            (gNode.stress ?? 0) >= 0.65 ? "text-red-600" :
                            (gNode.stress ?? 0) >= 0.50 ? "text-amber-600" :
                            "text-slate-600"
                          }
                        />
                        <EntityGraphBadge
                          label={L("Classification", "التصنيف")}
                          value={gNode.classification ?? "—"}
                          color={
                            gNode.classification === "CRITICAL" ? "text-red-700" :
                            gNode.classification === "ELEVATED" ? "text-amber-600" :
                            "text-slate-600"
                          }
                        />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ═══ LAYER 3: Country Exposure ═══ */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
          {L("Layer 3", "الطبقة 3")}
        </p>
        <h2 className="text-base font-bold text-slate-900 mb-4">
          {L("Country Exposure", "التعرض القطري")}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {countryExposures.map((c) => (
            <CountryExposureCard key={c.code} country={c} locale={locale} />
          ))}
        </div>
      </div>

      {/* ═══ LAYER 4: Banking Transmission ═══ */}
      {sectorRollups && (sectorRollups as any).banking && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
            {L("Layer 4", "الطبقة 4")}
          </p>
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {L("Banking Sector — Transmission Layer", "القطاع المصرفي — طبقة الانتقال")}
          </h2>
          <EnhancedSectorCard
            sector="banking"
            sectorLabel={sectorLabel("banking")}
            stress={(sectorRollups as any).banking.aggregate_stress}
            lossUsd={(sectorRollups as any).banking.total_loss}
            topDriver={sectorDepth.banking?.topDriver ?? "—"}
            secondOrderRisk={sectorDepth.banking?.secondOrderRisk ?? "—"}
            confidenceLow={sectorDepth.banking?.confidenceLow ?? 0.7}
            confidenceHigh={sectorDepth.banking?.confidenceHigh ?? 0.84}
            locale={locale}
          />
        </div>
      )}

      {/* ═══ LAYER 5: Insurance Absorption ═══ */}
      {sectorRollups && (sectorRollups as any).insurance && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
            {L("Layer 5", "الطبقة 5")}
          </p>
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {L("Insurance Sector — Loss Absorption Layer", "قطاع التأمين — طبقة استيعاب الخسائر")}
          </h2>
          <EnhancedSectorCard
            sector="insurance"
            sectorLabel={sectorLabel("insurance")}
            stress={(sectorRollups as any).insurance.aggregate_stress}
            lossUsd={(sectorRollups as any).insurance.total_loss}
            topDriver={sectorDepth.insurance?.topDriver ?? "—"}
            secondOrderRisk={sectorDepth.insurance?.secondOrderRisk ?? "—"}
            confidenceLow={sectorDepth.insurance?.confidenceLow ?? 0.74}
            confidenceHigh={sectorDepth.insurance?.confidenceHigh ?? 0.88}
            locale={locale}
          />
        </div>
      )}

      {/* ═══ LAYER 5b: Government Fiscal Transmission ═══ */}
      {sectorRollups && (sectorRollups as any).government && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
            {L("Layer 5b", "الطبقة 5ب")}
          </p>
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {L("Government — Fiscal Transmission Layer", "الحكومة — طبقة الانتقال المالي")}
          </h2>
          <EnhancedSectorCard
            sector="government"
            sectorLabel={sectorLabel("government")}
            stress={(sectorRollups as any).government.aggregate_stress}
            lossUsd={(sectorRollups as any).government.total_loss}
            topDriver={sectorDepth.government?.topDriver ?? "—"}
            secondOrderRisk={sectorDepth.government?.secondOrderRisk ?? "—"}
            confidenceLow={sectorDepth.government?.confidenceLow ?? 0.68}
            confidenceHigh={sectorDepth.government?.confidenceHigh ?? 0.82}
            locale={locale}
          />
        </div>
      )}

      {/* ═══ LAYER 5c: Real Estate Market Layer ═══ */}
      {sectorRollups && (sectorRollups as any).real_estate && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
            {L("Layer 5c", "الطبقة 5ج")}
          </p>
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {L("Real Estate — Market Transmission Layer", "العقارات — طبقة انتقال السوق")}
          </h2>
          <EnhancedSectorCard
            sector="real_estate"
            sectorLabel={sectorLabel("real_estate")}
            stress={(sectorRollups as any).real_estate.aggregate_stress}
            lossUsd={(sectorRollups as any).real_estate.total_loss}
            topDriver={sectorDepth.real_estate?.topDriver ?? "—"}
            secondOrderRisk={sectorDepth.real_estate?.secondOrderRisk ?? "—"}
            confidenceLow={sectorDepth.real_estate?.confidenceLow ?? 0.62}
            confidenceHigh={sectorDepth.real_estate?.confidenceHigh ?? 0.78}
            locale={locale}
          />
        </div>
      )}

      {/* ═══ LAYER 6: Sector Impact (remaining sectors, role-filtered) ═══ */}
      {sectorRollups && Object.keys(sectorRollups).length > 0 && (() => {
        const promoted = ["banking", "insurance", "government", "real_estate"];
        const remaining = focusSectors.filter((s) => !promoted.includes(s) && (sectorRollups as any)[s]);
        if (remaining.length === 0) return null;
        return (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
              {L("Layer 6", "الطبقة 6")}
            </p>
            <h2 className="text-base font-bold text-slate-900 mb-4">
              {L("Sector Impact Analysis", "تحليل تأثير القطاعات")}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {remaining.map((sector) => {
                const data = (sectorRollups as any)[sector];
                const depth = sectorDepth[sector];
                return (
                  <EnhancedSectorCard
                    key={sector}
                    sector={sector}
                    sectorLabel={sectorLabel(sector)}
                    stress={data?.aggregate_stress ?? data?.stress ?? 0}
                    lossUsd={data?.total_loss ?? data?.loss_usd ?? 0}
                    topDriver={depth?.topDriver ?? "—"}
                    secondOrderRisk={depth?.secondOrderRisk ?? "—"}
                    confidenceLow={depth?.confidenceLow ?? 0.6}
                    confidenceHigh={depth?.confidenceHigh ?? 0.9}
                    locale={locale}
                  />
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* ═══ LAYER 7: Decision Room ═══ */}
      {decisionActions && decisionActions.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
            {L("Layer 7", "الطبقة 7")}
          </p>
          <h2 className="text-base font-bold text-slate-900 mb-4">
            {L("Decision Room — Recommended Actions", "غرفة القرار — الإجراءات الموصى بها")}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {decisionActions
              .filter((a: any) =>
                role === "ceo" ? true :
                role === "energy" ? ["energy", "maritime"].includes(a.sector) :
                role === "regulator" ? ["banking", "insurance", "fintech"].includes(a.sector) :
                true
              )
              .slice(0, 4)
              .map((a: any) => (
                <ActionOwnerCard
                  key={a.id}
                  id={a.id}
                  action={a.action}
                  actionAr={a.action_ar}
                  owner={a.owner}
                  sector={a.sector}
                  urgency={a.urgency ?? a.priority ?? 50}
                  lossAvoided={a.loss_avoided_usd ?? 0}
                  costUsd={a.cost_usd ?? 0}
                  confidence={a.confidence ?? 0.8}
                  deadlineHours={a.deadline_hours}
                  escalationTrigger={a.escalation_trigger}
                  escalationTriggerAr={a.escalation_trigger_ar}
                  locale={locale}
                />
              ))}
          </div>

          {/* Counterfactual: No Action vs Selected Action vs Delta */}
          <CounterfactualBlock outcomes={outcomes} decisionActions={decisionActions} locale={locale} />
        </div>
      )}

      {/* ═══ LAYER 8: Outcome — Base Case vs. Mitigated ═══ */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
          {L("Layer 8", "الطبقة 8")}
        </p>
        <h2 className="text-base font-bold text-slate-900 mb-4">
          {L("Projected Outcome", "النتائج المتوقعة")}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Base Case */}
          <div className="bg-red-50 border border-red-100 rounded-lg p-4">
            <p className="text-[10px] text-red-500 uppercase tracking-wider font-semibold mb-2">
              {isAr ? outcomes.baseCase.labelAr : outcomes.baseCase.label}
            </p>
            <p className="text-lg font-bold text-red-700 mb-1">
              ${(outcomes.baseCase.lossLow / 1e9).toFixed(1)}B–${(outcomes.baseCase.lossHigh / 1e9).toFixed(1)}B
            </p>
            <p className="text-xs text-red-600 mb-2">
              {L("Recovery:", "التعافي:")} {outcomes.baseCase.recoveryDays} {L("days", "يوم")}
            </p>
            <p className="text-xs text-slate-600 leading-relaxed">
              {isAr ? outcomes.baseCase.descriptionAr : outcomes.baseCase.description}
            </p>
          </div>

          {/* Mitigated Case */}
          <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-4">
            <p className="text-[10px] text-emerald-600 uppercase tracking-wider font-semibold mb-2">
              {isAr ? outcomes.mitigatedCase.labelAr : outcomes.mitigatedCase.label}
            </p>
            <p className="text-lg font-bold text-emerald-700 mb-1">
              ${(outcomes.mitigatedCase.lossLow / 1e9).toFixed(1)}B–${(outcomes.mitigatedCase.lossHigh / 1e9).toFixed(1)}B
            </p>
            <p className="text-xs text-emerald-600 mb-2">
              {L("Recovery:", "التعافي:")} {outcomes.mitigatedCase.recoveryDays} {L("days", "يوم")}
            </p>
            <p className="text-xs text-slate-600 leading-relaxed">
              {isAr ? outcomes.mitigatedCase.descriptionAr : outcomes.mitigatedCase.description}
            </p>
          </div>

          {/* Value Saved */}
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
            <p className="text-[10px] text-blue-600 uppercase tracking-wider font-semibold mb-2">
              {L("Value Preserved Through Action", "القيمة المحفوظة من خلال التدخل")}
            </p>
            <p className="text-lg font-bold text-blue-700 mb-1">
              ${(outcomes.valueSaved.low / 1e9).toFixed(1)}B–${(outcomes.valueSaved.high / 1e9).toFixed(1)}B
            </p>
            <p className="text-xs text-slate-600 leading-relaxed mt-2">
              {isAr ? outcomes.valueSaved.descriptionAr : outcomes.valueSaved.description}
            </p>
          </div>
        </div>
      </div>

      {/* ═══ LAYER 9: Trust & Provenance ═══ */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
          {L("Layer 9", "الطبقة 9")}
        </p>
        <h2 className="text-base font-bold text-slate-900 mb-4">
          {L("Trust & Provenance", "الثقة والمصدر")}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {L("Confidence Level", "مستوى الثقة")}
            </p>
            <p className="text-lg font-bold text-blue-700">
              {confidence != null ? `${(confidence * 100).toFixed(0)}%` : "N/A"}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {L("Data Sources", "مصادر البيانات")}
            </p>
            <p className="text-xs text-slate-600">
              {trust?.dataSources?.length ?? 0} {L("verified sources", "مصادر موثقة")}
            </p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              {L("Audit Trail", "سجل التدقيق")}
            </p>
            <p className="text-xs text-slate-600 font-mono truncate">
              {trust?.auditHash ? trust.auditHash.slice(0, 24) + "..." : "—"}
            </p>
          </div>
        </div>
      </div>

      {/* ── Methodology & Assumptions (collapsible) ── */}
      <CompactAssumptions
        methodology={methodology}
        assumptions={assumptions}
        dataSources={trust?.dataSources ?? DEFAULT_TRUST_SOURCES}
        locale={locale}
      />

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

// ── Default trust data sources (used when trust.dataSources is not available) ──
const DEFAULT_TRUST_SOURCES = ["ACLED Conflict Data", "Maritime Traffic Intelligence", "Bloomberg Terminal", "SAMA Open Data", "GCC Central Bank Reports"];

// ── Country Exposure Card ──

function CountryExposureCard({ country, locale }: { country: CountryExposureEntry; locale: "en" | "ar" }) {
  const isAr = locale === "ar";
  const stressColor =
    country.stressLevel >= 0.65 ? "text-red-600" :
    country.stressLevel >= 0.50 ? "text-amber-600" :
    "text-slate-600";
  const barColor =
    country.stressLevel >= 0.65 ? "bg-red-500" :
    country.stressLevel >= 0.50 ? "bg-amber-500" :
    "bg-slate-400";

  return (
    <div className="bg-slate-50 border border-slate-100 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{country.code}</span>
          <h4 className="text-sm font-bold text-slate-900">{isAr ? country.nameAr : country.name}</h4>
        </div>
        <span className={`text-lg font-bold tabular-nums ${stressColor}`}>
          {(country.stressLevel * 100).toFixed(0)}%
        </span>
      </div>
      <div className="h-1.5 bg-slate-200 rounded-full mb-3 overflow-hidden">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${country.stressLevel * 100}%` }} />
      </div>
      <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-200">
        <span className="text-[10px] text-slate-500 uppercase">{isAr ? "التعرض" : "Exposure"}</span>
        <span className="text-sm font-semibold text-red-600 tabular-nums">${(country.exposureUsd / 1e9).toFixed(1)}B</span>
      </div>
      <div className="mb-2">
        <p className="text-[10px] text-slate-500 uppercase mb-0.5">{isAr ? "المحرك الأساسي" : "Primary Driver"}</p>
        <p className="text-xs text-slate-800 font-medium">{isAr ? country.primaryDriverAr : country.primaryDriver}</p>
      </div>
      <div>
        <p className="text-[10px] text-slate-500 uppercase mb-0.5">{isAr ? "قناة الانتقال" : "Transmission Channel"}</p>
        <p className="text-xs text-slate-600">{isAr ? country.transmissionChannelAr : country.transmissionChannel}</p>
      </div>
    </div>
  );
}

function EntityGraphBadge({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[9px] text-slate-400 uppercase tracking-wider">{label}</span>
      <span className={`text-[11px] font-semibold capitalize ${color ?? "text-slate-700"}`}>{value}</span>
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

// ── Scenario Switcher Pills ──

function ScenarioSwitcherPills({
  presets,
  activeTemplateId,
  onSwitch,
  onRunLive,
  isRunning,
  locale,
}: {
  presets: ScenarioPreset[];
  activeTemplateId?: string;
  onSwitch: (key: ScenarioKey) => void;
  onRunLive: (templateId: string) => void;
  isRunning: boolean;
  locale: "en" | "ar";
}) {
  const isAr = locale === "ar";
  if (!presets?.length) return null;
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {presets.map((p) => {
        const active = activeTemplateId === p.templateId;
        return (
          <button
            key={p.key}
            onClick={() => onSwitch(p.key)}
            disabled={isRunning}
            className={`
              px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all duration-150
              ${active
                ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                : "bg-white text-slate-600 border-slate-200 hover:border-blue-300 hover:text-blue-700"
              }
              ${isRunning ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            {isAr ? p.labelAr : p.labelEn}
          </button>
        );
      })}
    </div>
  );
}

// ── Pathway Headline ──

function PathwayHeadline({
  causalChain,
  scenario,
  locale,
}: {
  causalChain: ReturnType<typeof useCommandCenter>["causalChain"];
  scenario: ReturnType<typeof useCommandCenter>["scenario"];
  locale: "en" | "ar";
}) {
  const isAr = locale === "ar";
  if (!causalChain || causalChain.length < 2) return null;

  const origin = isAr ? causalChain[0].entity_label_ar : causalChain[0].entity_label;
  const terminus = isAr
    ? causalChain[causalChain.length - 1].entity_label_ar
    : causalChain[causalChain.length - 1].entity_label;
  const depth = causalChain.length;

  return (
    <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-lg px-5 py-3 mb-4">
      <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">
        {isAr ? "مسار الانتقال الرئيسي" : "Primary Transmission Pathway"}
      </p>
      <p className="text-sm font-semibold">
        {origin}
        <span className="text-slate-400 mx-2">→</span>
        <span className="text-blue-300">{depth} {isAr ? "طبقات" : "layers"}</span>
        <span className="text-slate-400 mx-2">→</span>
        {terminus}
      </p>
    </div>
  );
}

// ── Counterfactual Comparison Block ──

function CounterfactualBlock({
  outcomes,
  decisionActions,
  locale,
}: {
  outcomes: DerivedOutcomes;
  decisionActions: ReturnType<typeof useCommandCenter>["decisionActions"];
  locale: "en" | "ar";
}) {
  const isAr = locale === "ar";
  const L = (en: string, ar: string) => (isAr ? ar : en);

  const noActionLoss = (outcomes.baseCase.lossLow + outcomes.baseCase.lossHigh) / 2;
  const withActionLoss = (outcomes.mitigatedCase.lossLow + outcomes.mitigatedCase.lossHigh) / 2;
  const lossDelta = noActionLoss - withActionLoss;
  const pctReduction = noActionLoss > 0 ? (lossDelta / noActionLoss) * 100 : 0;

  const topAction = decisionActions?.[0];

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 mt-4">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-3">
        {L("Counterfactual Comparison", "المقارنة المضادة للوقائع")}
      </p>
      <div className="grid grid-cols-3 gap-4">
        {/* No action */}
        <div className="bg-red-50 border border-red-100 rounded-lg p-4">
          <p className="text-[10px] text-red-500 uppercase tracking-wider font-semibold mb-2">
            {L("No Action", "بدون تدخل")}
          </p>
          <p className="text-xl font-bold text-red-700 tabular-nums">
            ${(noActionLoss / 1e9).toFixed(1)}B
          </p>
          <p className="text-xs text-red-600 mt-1">
            {L("Recovery:", "التعافي:")} {outcomes.baseCase.recoveryDays} {L("days", "يوم")}
          </p>
        </div>

        {/* Selected action */}
        <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-4">
          <p className="text-[10px] text-emerald-600 uppercase tracking-wider font-semibold mb-2">
            {L("With Action", "مع التدخل")}
          </p>
          <p className="text-xl font-bold text-emerald-700 tabular-nums">
            ${(withActionLoss / 1e9).toFixed(1)}B
          </p>
          <p className="text-xs text-emerald-600 mt-1">
            {L("Recovery:", "التعافي:")} {outcomes.mitigatedCase.recoveryDays} {L("days", "يوم")}
          </p>
          {topAction && (
            <p className="text-[10px] text-slate-500 mt-2 truncate" title={isAr && topAction.action_ar ? topAction.action_ar : topAction.action}>
              {isAr && topAction.action_ar ? topAction.action_ar : topAction.action}
            </p>
          )}
        </div>

        {/* Loss delta */}
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
          <p className="text-[10px] text-blue-600 uppercase tracking-wider font-semibold mb-2">
            {L("Projected Savings", "الوفورات المتوقعة")}
          </p>
          <p className="text-xl font-bold text-blue-700 tabular-nums">
            ${(lossDelta / 1e9).toFixed(1)}B
          </p>
          <p className="text-xs text-blue-600 mt-1">
            {pctReduction.toFixed(0)}% {L("loss reduction", "تقليص الخسائر")}
          </p>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// MACRO INTELLIGENCE VIEW — Detailed 9-layer analysis
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
    role,
    lossRange,
    deadline,
    assumptions,
    sectorDepth,
    countryExposures,
    outcomes,
    methodology,
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
    role: ExecutiveRole;
    lossRange: DerivedLossRange;
    deadline: string;
    assumptions: string[];
    sectorDepth: Record<string, { topDriver: string; secondOrderRisk: string; confidenceLow: number; confidenceHigh: number }>;
    countryExposures: CountryExposureEntry[];
    outcomes: DerivedOutcomes;
    methodology: string;
  }
) {
  const isAr = locale === "ar";
  const L = (en: string, ar: string) => (isAr ? ar : en);
  const focusSectors = ROLE_SECTOR_FOCUS[role];

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto" dir={isAr ? "rtl" : "ltr"}>
      {/* 1. Macro State — Financial exposure overview */}
      {headline && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span className="inline-flex w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold items-center justify-center">1</span>
              {L("Macro Financial State", "الحالة المالية الكلية")}
            </h3>
            <DecisionClock deadlineIso={deadline} locale={locale} />
          </div>

          {/* Pathway headline — above financial loss */}
          <PathwayHeadline causalChain={causalChain} scenario={scenario} locale={locale} />

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <RangeLossCard lossLow={lossRange.low} lossMid={lossRange.mid} lossHigh={lossRange.high} confidencePct={lossRange.confidence_pct} locale={locale} />
            <MetricCard label={L("Average Stress", "متوسط الضغط")} value={`${(headline.averageStress * 100).toFixed(0)}%`} color="text-amber-600" />
            <MetricCard label={L("Transmission Depth", "عمق الانتقال")} value={`${headline.propagationDepth} ${L("layers", "طبقات")}`} color="text-blue-700" />
            <MetricCard label={L("Peak Stress Day", "يوم ذروة الضغط")} value={`${L("Day", "اليوم")} ${headline.peakDay}`} color="text-purple-600" />
          </div>
          {(narrativeEn || narrativeAr) && (
            <div className="bg-slate-50 border border-slate-100 rounded-lg p-4">
              <p className="text-sm text-slate-700 leading-relaxed">
                {isAr ? (narrativeAr || narrativeEn) : (narrativeEn || narrativeAr)}
              </p>
            </div>
          )}
        </div>
      )}

      {/* 2. Propagation — How the disruption transmits */}
      {causalChain && causalChain.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span className="inline-flex w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold items-center justify-center">2</span>
            {L("Transmission Channels", "قنوات انتقال الاضطراب")}
          </h3>
          <div className="space-y-2">
            {causalChain.map((link, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-slate-50 p-3 rounded-lg">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-200 text-slate-600 text-xs font-bold flex items-center justify-center mt-0.5">{idx + 1}</div>
                <div className="flex-1">
                  <p className="text-xs font-semibold text-slate-800">{isAr ? link.entity_label_ar : link.entity_label}</p>
                  <p className="text-sm text-slate-600 mt-0.5">{isAr ? link.event_ar : link.event}</p>
                  {link.impact_usd > 0 && (
                    <p className="text-xs text-red-600 font-semibold mt-1">${(link.impact_usd / 1e9).toFixed(2)}B</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Country Exposure */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
          <span className="inline-flex w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold items-center justify-center">3</span>
          {L("Country Exposure", "التعرض القطري")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {countryExposures.map((c) => (
            <CountryExposureCard key={c.code} country={c} locale={locale} />
          ))}
        </div>
      </div>

      {/* 4–6. Sector layers */}
      {sectorRollups && Object.keys(sectorRollups).length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span className="inline-flex w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold items-center justify-center">4</span>
            {L("Sector Impact Analysis", "تحليل تأثير القطاعات")}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {focusSectors
              .filter((s) => (sectorRollups as any)[s])
              .map((sector) => {
                const data = (sectorRollups as any)[sector];
                const depth = sectorDepth[sector];
                return (
                  <EnhancedSectorCard
                    key={sector}
                    sector={sector}
                    sectorLabel={sectorLabel(sector)}
                    stress={data?.aggregate_stress ?? data?.stress ?? 0}
                    lossUsd={data?.total_loss ?? data?.loss_usd ?? 0}
                    topDriver={depth?.topDriver ?? "—"}
                    secondOrderRisk={depth?.secondOrderRisk ?? "—"}
                    confidenceLow={depth?.confidenceLow ?? 0.6}
                    confidenceHigh={depth?.confidenceHigh ?? 0.9}
                    locale={locale}
                  />
                );
              })}
          </div>
        </div>
      )}

      {/* 5. Decision Room */}
      {decisionActions && decisionActions.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
            <span className="inline-flex w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold items-center justify-center">5</span>
            {L("Recommended Actions", "الإجراءات الموصى بها")}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {decisionActions.slice(0, 4).map((action: any, idx: number) => (
              <ActionOwnerCard
                key={action.id || idx}
                id={action.id || `action-${idx}`}
                action={action.action || action.title || action.label || `Action ${idx + 1}`}
                actionAr={action.action_ar}
                owner={action.owner || "—"}
                sector={action.sector || "general"}
                urgency={action.urgency ?? action.priority ?? 50}
                lossAvoided={action.loss_avoided_usd ?? 0}
                costUsd={action.cost_usd ?? 0}
                confidence={action.confidence ?? 0.8}
                locale={locale}
              />
            ))}
          </div>

          {/* Counterfactual: No Action vs Selected Action vs Delta */}
          <CounterfactualBlock outcomes={outcomes} decisionActions={decisionActions} locale={locale} />
        </div>
      )}

      {/* 6. Projected Outcome */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
          <span className="inline-flex w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold items-center justify-center">6</span>
          {L("Projected Outcome", "النتائج المتوقعة")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-red-50 border border-red-100 rounded-lg p-4">
            <p className="text-[10px] text-red-500 uppercase tracking-wider font-semibold mb-2">
              {isAr ? outcomes.baseCase.labelAr : outcomes.baseCase.label}
            </p>
            <p className="text-lg font-bold text-red-700">${(outcomes.baseCase.lossLow / 1e9).toFixed(1)}B–${(outcomes.baseCase.lossHigh / 1e9).toFixed(1)}B</p>
            <p className="text-xs text-red-600 mt-1">{L("Recovery:", "التعافي:")} {outcomes.baseCase.recoveryDays} {L("days", "يوم")}</p>
          </div>
          <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-4">
            <p className="text-[10px] text-emerald-600 uppercase tracking-wider font-semibold mb-2">
              {isAr ? outcomes.mitigatedCase.labelAr : outcomes.mitigatedCase.label}
            </p>
            <p className="text-lg font-bold text-emerald-700">${(outcomes.mitigatedCase.lossLow / 1e9).toFixed(1)}B–${(outcomes.mitigatedCase.lossHigh / 1e9).toFixed(1)}B</p>
            <p className="text-xs text-emerald-600 mt-1">{L("Recovery:", "التعافي:")} {outcomes.mitigatedCase.recoveryDays} {L("days", "يوم")}</p>
          </div>
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
            <p className="text-[10px] text-blue-600 uppercase tracking-wider font-semibold mb-2">
              {L("Value Preserved", "القيمة المحفوظة")}
            </p>
            <p className="text-lg font-bold text-blue-700">${(outcomes.valueSaved.low / 1e9).toFixed(1)}B–${(outcomes.valueSaved.high / 1e9).toFixed(1)}B</p>
          </div>
        </div>
      </div>

      {/* 7. Trust & Provenance */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
          <span className="inline-flex w-6 h-6 rounded-full bg-slate-100 text-slate-700 text-xs font-bold items-center justify-center">7</span>
          {L("Trust & Provenance", "الثقة والمصدر")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{L("Confidence", "الثقة")}</p>
            <p className="text-lg font-bold text-blue-700">{confidence != null ? `${(confidence * 100).toFixed(0)}%` : "N/A"}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{L("Data Sources", "مصادر البيانات")}</p>
            <p className="text-xs text-slate-600">{trust?.dataSources?.length ?? 0} {L("verified sources", "مصادر موثقة")}</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{L("Audit Trail", "سجل التدقيق")}</p>
            <p className="text-xs text-slate-600 font-mono truncate">{trust?.auditHash ? trust.auditHash.slice(0, 24) + "..." : "—"}</p>
          </div>
        </div>
      </div>

      {/* Methodology */}
      <CompactAssumptions
        methodology={methodology}
        assumptions={assumptions}
        dataSources={trust?.dataSources ?? DEFAULT_TRUST_SOURCES}
        locale={locale}
      />
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
  const [activeRole, setActiveRole] = useState<ExecutiveRole>("ceo");

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

    // Derived briefing data (live API → derived, mock fallback)
    briefingLossRange,
    briefingDeadline,
    briefingAssumptions,
    briefingSectorDepth,
    briefingCountryExposures,
    briefingOutcomes,
    briefingMethodology,

    // Actions
    executeAction,
    switchToMock,
    switchToLive,

    // Scenario switching
    switchScenario,
    scenarioPresets,
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

  // ── Derive peak sector for escalation banner ──
  const peakSectorInfo = useMemo(() => {
    if (!sectorRollups || typeof sectorRollups !== "object") return { sector: "—", stress: 0 };
    let peak = { sector: "—", stress: 0 };
    for (const [sector, data] of Object.entries(sectorRollups)) {
      const s = (data as any)?.aggregate_stress ?? (data as any)?.stress ?? 0;
      if (s > peak.stress) peak = { sector, stress: s };
    }
    return peak;
  }, [sectorRollups]);

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
      real_estate: ["AE", "SA", "BH"],
      government: ["SA", "AE", "KW", "QA"],
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

      case "intelligence":
        return (
          <div className="max-w-7xl mx-auto px-6">
            <IntelligenceSurface />
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
            role={activeRole}
            lossRange={briefingLossRange}
            deadline={briefingDeadline}
            assumptions={briefingAssumptions}
            sectorDepth={briefingSectorDepth}
            countryExposures={briefingCountryExposures}
            outcomes={briefingOutcomes}
            methodology={briefingMethodology}
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
            role={activeRole}
            trust={trust}
            lossRange={briefingLossRange}
            deadline={briefingDeadline}
            assumptions={briefingAssumptions}
            sectorDepth={briefingSectorDepth}
            countryExposures={briefingCountryExposures}
            outcomes={briefingOutcomes}
            methodology={briefingMethodology}
            graphNodes={graphNodes}
            scenarioPresets={scenarioPresets}
            onSwitchScenario={switchScenario}
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
      headerSlot={
        <RoleSwitcher activeRole={activeRole} onSwitch={setActiveRole} locale={locale} />
      }
    >
      {/* Escalation banner */}
      {headline && (
        <EscalationBanner
          averageStress={headline.averageStress}
          peakSector={sectorLabel(peakSectorInfo.sector)}
          peakStress={peakSectorInfo.stress}
          locale={locale}
        />
      )}

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
