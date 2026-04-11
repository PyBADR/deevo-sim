"use client";

/**
 * Impact Observatory | مرصد الأثر — Banking Stress Detail Panel
 *
 * Shows full banking sector stress breakdown:
 * - Aggregate stress gauge
 * - Institution-level table
 * - Liquidity / Credit / FX / Contagion breakdown
 * - Basel III metrics
 * - Time to liquidity breach countdown
 */

import React from "react";
import type { BankingStress, Classification, Language } from "@/types/observatory";

// ── Helpers ──────────────────────────────────────────────────────────

const classificationColors: Record<Classification, string> = {
  CRITICAL: "bg-red-50 text-red-700",
  ELEVATED: "bg-orange-50 text-orange-700",
  MODERATE: "bg-amber-50 text-amber-700",
  LOW: "bg-yellow-50 text-yellow-700",
  NOMINAL: "bg-green-50 text-green-700",
};

function Badge({ level }: { level: Classification }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${classificationColors[level]}`}>
      {level}
    </span>
  );
}

import { formatUSD, formatHours, safeFixed, safePercent } from "@/lib/format";

function StressBar({ value, label, color }: { value: number; label: string; color: string }) {
  const pct = Math.min((value ?? 0) * 100, 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-slate-600 font-medium">{label}</span>
        <span className="font-semibold text-slate-900">{safeFixed(pct, 1)}%</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── Labels ────────────────────────────────────────────────────────────

const labels: Record<Language, Record<string, string>> = {
  en: {
    title: "Banking Sector Stress",
    aggregate: "Aggregate Stress",
    total_exposure: "Total Exposure",
    ttl_breach: "Time to Liquidity Breach",
    car_impact: "Capital Adequacy Impact",
    liquidity: "Liquidity Stress",
    credit: "Credit Stress",
    fx: "FX Stress",
    contagion: "Interbank Contagion",
    institutions: "Affected Institutions",
    institution: "Institution",
    country: "Country",
    exposure: "Exposure",
    stress: "Stress",
    car: "Proj. CAR",
    stress_decomposition: "Stress Decomposition",
    basel_metrics: "Basel III Indicators",
    min_car: "Minimum CAR (Basel III)",
    min_car_value: "8.0%",
    lcr_label: "LCR Requirement",
    lcr_value: "100%",
  },
  ar: {
    title: "ضغط القطاع البنكي",
    aggregate: "الضغط الكلي",
    total_exposure: "إجمالي التعرض",
    ttl_breach: "الوقت إلى كسر السيولة",
    car_impact: "أثر كفاية رأس المال",
    liquidity: "ضغط السيولة",
    credit: "ضغط الائتمان",
    fx: "ضغط العملة",
    contagion: "عدوى بين البنوك",
    institutions: "المؤسسات المتأثرة",
    institution: "المؤسسة",
    country: "الدولة",
    exposure: "التعرض",
    stress: "الضغط",
    car: "CAR المتوقع",
    stress_decomposition: "تحليل الضغط",
    basel_metrics: "مؤشرات بازل III",
    min_car: "الحد الأدنى CAR (بازل III)",
    min_car_value: "8.0%",
    lcr_label: "متطلب LCR",
    lcr_value: "100%",
  },
};

// ── Main Component ───────────────────────────────────────────────────

export default function BankingDetailPanel({
  data,
  lang = "en",
}: {
  data: BankingStress;
  lang?: Language;
}) {
  const t = labels[lang];
  const isRTL = lang === "ar";

  return (
    <div className={`space-y-6 ${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">{t.title}</h2>
        <Badge level={data.classification as Classification} />
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-600 mb-1">{t.aggregate}</p>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{safePercent(data.aggregate_stress)}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-600 mb-1">{t.total_exposure}</p>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{formatUSD(data.total_exposure_usd)}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-600 mb-1">{t.ttl_breach}</p>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{formatHours(data.time_to_liquidity_breach_hours)}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-600 mb-1">{t.car_impact}</p>
          <p className="text-2xl font-bold tabular-nums text-red-600">-{safeFixed(data.capital_adequacy_impact_pct, 2)}%</p>
        </div>
      </div>

      {/* Stress Decomposition */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">{t.stress_decomposition}</h3>
        <div className="space-y-3">
          <StressBar value={data.liquidity_stress} label={t.liquidity} color="bg-blue-500" />
          <StressBar value={data.credit_stress} label={t.credit} color="bg-amber-500" />
          <StressBar value={data.fx_stress} label={t.fx} color="bg-orange-500" />
          <StressBar value={data.interbank_contagion} label={t.contagion} color="bg-red-500" />
        </div>
      </div>

      {/* Basel III Reference */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">{t.basel_metrics}</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex justify-between text-sm border-b border-slate-200 pb-2">
            <span className="text-slate-600">{t.min_car}</span>
            <span className="font-semibold text-slate-900">{t.min_car_value}</span>
          </div>
          <div className="flex justify-between text-sm border-b border-slate-200 pb-2">
            <span className="text-slate-600">{t.lcr_label}</span>
            <span className="font-semibold text-slate-900">{t.lcr_value}</span>
          </div>
          <div className="flex justify-between text-sm border-b border-slate-200 pb-2">
            <span className="text-slate-600">{t.car_impact}</span>
            <span className={`font-semibold ${data.capital_adequacy_impact_pct > 2 ? "text-red-600" : "text-amber-600"}`}>
              -{safeFixed(data.capital_adequacy_impact_pct, 2)}%
            </span>
          </div>
          <div className="flex justify-between text-sm border-b border-slate-200 pb-2">
            <span className="text-slate-600">{t.contagion}</span>
            <span className={`font-semibold ${data.interbank_contagion > 0.5 ? "text-red-600" : "text-slate-900"}`}>
              {safePercent(data.interbank_contagion)}
            </span>
          </div>
        </div>
      </div>

      {/* Institution Table */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">{t.institutions}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-600 bg-slate-50">
                <th className="text-left py-2 font-medium">{t.institution}</th>
                <th className="text-left py-2 font-medium">{t.country}</th>
                <th className="text-right py-2 font-medium">{t.exposure}</th>
                <th className="text-right py-2 font-medium">{t.stress}</th>
                <th className="text-right py-2 font-medium">{t.car}</th>
              </tr>
            </thead>
            <tbody>
              {(data.affected_institutions ?? []).length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-xs text-slate-600">
                    {lang === "ar"
                      ? "لا توجد بيانات مؤسسية لهذا السيناريو"
                      : "No institution-level data available for this scenario"}
                  </td>
                </tr>
              ) : (
                (data.affected_institutions ?? []).map((inst) => (
                  <tr key={inst.id} className="border-b border-slate-200">
                    <td className="py-2.5 font-medium text-slate-900">
                      {lang === "ar" ? inst.name_ar : inst.name}
                    </td>
                    <td className="py-2.5 text-slate-600">{inst.country}</td>
                    <td className="py-2.5 text-right tabular-nums font-medium">{formatUSD(inst.exposure_usd)}</td>
                    <td className="py-2.5 text-right tabular-nums">
                      <span className={inst.stress > 0.6 ? "text-red-600 font-semibold" : inst.stress > 0.4 ? "text-amber-600" : "text-slate-900"}>
                        {safePercent(inst.stress)}
                      </span>
                    </td>
                    <td className="py-2.5 text-right tabular-nums">
                      <span className={inst.projected_car_pct < 10 ? "text-red-600 font-semibold" : "text-slate-900"}>
                        {safeFixed(inst.projected_car_pct, 1)}%
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
