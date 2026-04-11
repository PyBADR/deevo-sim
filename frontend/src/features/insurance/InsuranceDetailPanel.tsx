"use client";

/**
 * Impact Observatory | مرصد الأثر — Insurance Stress Detail Panel
 *
 * Shows full insurance sector stress breakdown:
 * - Aggregate stress + classification
 * - Claims surge multiplier
 * - Combined ratio & loss ratio
 * - IFRS-17 risk adjustment
 * - Reinsurance trigger status
 * - Affected insurance lines table
 * - Time to insolvency countdown
 */

import React from "react";
import type { InsuranceStress, Classification, Language } from "@/types/observatory";

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

function RatioGauge({ value, label, threshold, thresholdLabel }: { value: number; label: string; threshold: number; thresholdLabel: string }) {
  const pct = Math.min((value ?? 0) * 100, 150);
  const thresholdPct = Math.min((threshold ?? 0) * 100, 150);
  const isBreached = (value ?? 0) >= (threshold ?? 0);

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-slate-600 font-medium">{label}</span>
        <span className={`font-semibold ${isBreached ? "text-red-600" : "text-slate-900"}`}>
          {safePercent(value)}
        </span>
      </div>
      <div className="relative h-3 bg-slate-100 rounded-full overflow-visible">
        <div
          className={`h-full rounded-full transition-all duration-500 ${isBreached ? "bg-red-500" : "bg-blue-500"}`}
          style={{ width: `${Math.min((pct / 150) * 100, 100)}%` }}
        />
        {/* Threshold marker */}
        <div
          className="absolute top-0 h-full w-0.5 bg-slate-400"
          style={{ left: `${(thresholdPct / 150) * 100}%` }}
          title={thresholdLabel}
        />
      </div>
      <p className="text-xs text-slate-600">{thresholdLabel}: {safePercent(threshold, 0)}</p>
    </div>
  );
}

// ── Labels ────────────────────────────────────────────────────────────

const labels: Record<Language, Record<string, string>> = {
  en: {
    title: "Insurance Sector Stress",
    aggregate: "Aggregate Stress",
    portfolio: "Portfolio Exposure",
    claims_surge: "Claims Surge",
    time_insolvency: "Time to Insolvency",
    combined_ratio: "Combined Ratio",
    loss_ratio: "Loss Ratio",
    uw_status: "Underwriting Status",
    reinsurance: "Reinsurance Trigger",
    ifrs17: "IFRS-17 Risk Adjustment",
    affected_lines: "Affected Insurance Lines",
    line: "Line of Business",
    exposure: "Exposure",
    surge: "Claims Surge",
    stress: "Stress",
    key_ratios: "Key Ratios",
    regulatory: "Regulatory Indicators",
    triggered: "TRIGGERED",
    normal: "Normal",
    threshold_combined: "Threshold",
    threshold_loss: "Threshold",
  },
  ar: {
    title: "ضغط قطاع التأمين",
    aggregate: "الضغط الكلي",
    portfolio: "تعرض المحفظة",
    claims_surge: "ارتفاع المطالبات",
    time_insolvency: "الوقت إلى فشل التأمين",
    combined_ratio: "النسبة المجمعة",
    loss_ratio: "نسبة الخسارة",
    uw_status: "حالة الاكتتاب",
    reinsurance: "تفعيل إعادة التأمين",
    ifrs17: "تعديل المخاطر IFRS-17",
    affected_lines: "خطوط التأمين المتأثرة",
    line: "خط الأعمال",
    exposure: "التعرض",
    surge: "ارتفاع المطالبات",
    stress: "الضغط",
    key_ratios: "النسب الرئيسية",
    regulatory: "المؤشرات التنظيمية",
    triggered: "مُفعّل",
    normal: "طبيعي",
    threshold_combined: "الحد",
    threshold_loss: "الحد",
  },
};

// ── Main Component ───────────────────────────────────────────────────

export default function InsuranceDetailPanel({
  data,
  lang = "en",
}: {
  data: InsuranceStress;
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

      {/* Top Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-600 mb-1">{t.aggregate}</p>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{safePercent(data.aggregate_stress)}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-600 mb-1">{t.claims_surge}</p>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{safeFixed(data.claims_surge_multiplier, 2)}x</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-600 mb-1">{t.portfolio}</p>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{formatUSD(data.portfolio_exposure_usd)}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-600 mb-1">{t.time_insolvency}</p>
          <p className="text-2xl font-bold tabular-nums text-slate-900">{formatHours(data.time_to_insolvency_hours)}</p>
        </div>
      </div>

      {/* Key Ratios with Gauges */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">{t.key_ratios}</h3>
        <div className="space-y-4">
          <RatioGauge value={data.combined_ratio} label={t.combined_ratio} threshold={1.0} thresholdLabel={t.threshold_combined} />
          <RatioGauge value={data.loss_ratio} label={t.loss_ratio} threshold={0.75} thresholdLabel={t.threshold_loss} />
        </div>
      </div>

      {/* Regulatory Indicators */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">{t.regulatory}</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex justify-between items-center text-sm border-b border-slate-200 pb-2">
            <span className="text-slate-600">{t.uw_status}</span>
            <span className={`font-semibold ${data.underwriting_status === "SUSPENDED" ? "text-red-600" : data.underwriting_status === "RESTRICTED" ? "text-amber-600" : "text-slate-900"}`}>
              {data.underwriting_status}
            </span>
          </div>
          <div className="flex justify-between items-center text-sm border-b border-slate-200 pb-2">
            <span className="text-slate-600">{t.reinsurance}</span>
            <span className={`font-semibold ${data.reinsurance_trigger ? "text-red-600" : "text-green-600"}`}>
              {data.reinsurance_trigger ? t.triggered : t.normal}
            </span>
          </div>
          <div className="flex justify-between items-center text-sm border-b border-slate-200 pb-2">
            <span className="text-slate-600">{t.ifrs17}</span>
            <span className="font-semibold text-slate-900">{safeFixed(data.ifrs17_risk_adjustment_pct, 2)}%</span>
          </div>
          <div className="flex justify-between items-center text-sm border-b border-slate-200 pb-2">
            <span className="text-slate-600">{t.claims_surge}</span>
            <span className={`font-semibold ${data.claims_surge_multiplier > 2 ? "text-red-600" : data.claims_surge_multiplier > 1.5 ? "text-amber-600" : "text-slate-900"}`}>
              {safeFixed(data.claims_surge_multiplier, 2)}x
            </span>
          </div>
        </div>
      </div>

      {/* Affected Lines Table */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">{t.affected_lines}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-600 bg-slate-50">
                <th className="text-left py-2 font-medium">{t.line}</th>
                <th className="text-right py-2 font-medium">{t.exposure}</th>
                <th className="text-right py-2 font-medium">{t.surge}</th>
                <th className="text-right py-2 font-medium">{t.stress}</th>
              </tr>
            </thead>
            <tbody>
              {(data.affected_lines ?? []).length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-xs text-slate-600">
                    {lang === "ar"
                      ? "لا توجد بيانات خطوط التأمين لهذا السيناريو"
                      : "No insurance line data available for this scenario"}
                  </td>
                </tr>
              ) : (
                (data.affected_lines ?? []).map((line) => (
                  <tr key={line.id} className="border-b border-slate-200">
                    <td className="py-2.5 font-medium text-slate-900">
                      {lang === "ar" ? line.name_ar : line.name}
                    </td>
                    <td className="py-2.5 text-right tabular-nums font-medium">{formatUSD(line.exposure_usd)}</td>
                    <td className="py-2.5 text-right tabular-nums">
                      <span className={line.claims_surge > 2 ? "text-red-600 font-semibold" : line.claims_surge > 1.5 ? "text-amber-600" : "text-slate-900"}>
                        {safeFixed(line.claims_surge, 2)}x
                      </span>
                    </td>
                    <td className="py-2.5 text-right tabular-nums">
                      <span className={line.stress > 0.6 ? "text-red-600 font-semibold" : line.stress > 0.4 ? "text-amber-600" : "text-slate-900"}>
                        {safePercent(line.stress)}
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
