"use client";

import React, { useMemo } from "react";

interface CountryExposureData {
  stressLevel: number;
  lossUsd: number;
  dominantSector: string;
  entities: string[];
}

interface GCCImpactMapProps {
  countryExposures?: Record<string, CountryExposureData>;
  sectorRollups?: Record<string, { stress: number; loss_usd: number }>;
  scenarioLabel?: string;
  locale?: "en" | "ar";
  onCountryClick?: (countryCode: string) => void;
}

// ── GCC Country Registry ──

const DEFAULT_COUNTRIES: Record<string, { en: string; ar: string; sector: string; entities: string[] }> = {
  SA: { en: "Saudi Arabia", ar: "السعودية", sector: "Energy", entities: ["Saudi Aramco", "SAMA", "Tadawul"] },
  AE: { en: "UAE", ar: "الإمارات", sector: "Banking", entities: ["CBUAE", "DP World", "ADNOC"] },
  QA: { en: "Qatar", ar: "قطر", sector: "Energy", entities: ["QatarEnergy", "QCB", "Hamad Port"] },
  KW: { en: "Kuwait", ar: "الكويت", sector: "Energy", entities: ["KPC", "CBK", "KIA"] },
  BH: { en: "Bahrain", ar: "البحرين", sector: "Banking", entities: ["CBB", "Bahrain Bourse", "BAPCO"] },
  OM: { en: "Oman", ar: "عُمان", sector: "Logistics", entities: ["Port of Salalah", "CBO", "PDO"] },
};

// Repositioned for readability — wider viewBox, no overlaps
const COUNTRY_POSITIONS: Record<string, { x: number; y: number; w: number; h: number }> = {
  KW: { x: 16,  y: 16,  w: 120, h: 80 },
  SA: { x: 16,  y: 112, w: 160, h: 120 },
  BH: { x: 152, y: 16,  w: 120, h: 80 },
  QA: { x: 288, y: 16,  w: 120, h: 80 },
  AE: { x: 424, y: 16,  w: 136, h: 120 },
  OM: { x: 288, y: 112, w: 160, h: 120 },
};

// ── Classification colors (from tokens.ts) ──

const STRESS_COLORS = {
  nominal:  { bg: "#3A7D6C", text: "#1a4a3f" },
  low:      { bg: "#2D6A4F", text: "#1a4030" },
  guarded:  { bg: "#5E6759", text: "#3a3f36" },
  elevated: { bg: "#8B6914", text: "#5a440d" },
  high:     { bg: "#A0522D", text: "#66341d" },
  severe:   { bg: "#8C2318", text: "#5a170f" },
} as const;

function getStressLevel(stress: number): keyof typeof STRESS_COLORS {
  if (stress >= 0.80) return "severe";
  if (stress >= 0.65) return "high";
  if (stress >= 0.50) return "elevated";
  if (stress >= 0.35) return "guarded";
  if (stress >= 0.20) return "low";
  return "nominal";
}

function getStressLabel(level: keyof typeof STRESS_COLORS, isAr: boolean): string {
  const labels: Record<keyof typeof STRESS_COLORS, { en: string; ar: string }> = {
    nominal:  { en: "Nominal",  ar: "طبيعي" },
    low:      { en: "Low",      ar: "منخفض" },
    guarded:  { en: "Guarded",  ar: "مراقب" },
    elevated: { en: "Elevated", ar: "مرتفع" },
    high:     { en: "High",     ar: "عالي" },
    severe:   { en: "Severe",   ar: "حرج" },
  };
  return isAr ? labels[level].ar : labels[level].en;
}

function formatUsd(amount: number): string {
  if (amount >= 1e9) return `$${(amount / 1e9).toFixed(1)}B`;
  if (amount >= 1e6) return `$${(amount / 1e6).toFixed(0)}M`;
  if (amount >= 1e3) return `$${(amount / 1e3).toFixed(0)}K`;
  return `$${amount.toLocaleString()}`;
}

export function GCCImpactMap({
  countryExposures = {},
  sectorRollups = {},
  scenarioLabel,
  locale = "en",
  onCountryClick,
}: GCCImpactMapProps): React.ReactElement {
  const isAr = locale === "ar";

  const countryData = useMemo(() => {
    return Object.entries(DEFAULT_COUNTRIES).map(([code, defaults]) => {
      const exposure = countryExposures[code];
      const hasData = !!exposure && exposure.stressLevel > 0;

      return {
        code,
        name: isAr ? defaults.ar : defaults.en,
        stress: hasData ? exposure.stressLevel : 0,
        loss: hasData ? exposure.lossUsd : 0,
        sector: exposure?.dominantSector || defaults.sector,
        entities: exposure?.entities || defaults.entities,
        hasData,
      };
    });
  }, [countryExposures, isAr]);

  const hasAnyData = countryData.some((c) => c.hasData);

  return (
    <div className="w-full bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 pt-5 pb-3 border-b border-slate-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">
              {isAr ? "خريطة التعرض الخليجية" : "GCC Exposure Map"}
            </h2>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {isAr ? "٦ دول — الإجهاد المالي النسبي" : "6 nations — relative financial stress"}
            </p>
          </div>
          {scenarioLabel && (
            <span className="text-[11px] text-io-accent font-medium px-2.5 py-1 rounded-md bg-io-accent/8 border border-io-accent/15">
              {scenarioLabel}
            </span>
          )}
        </div>
      </div>

      {/* Map */}
      <div className="px-6 py-5">
        <svg viewBox="0 0 576 248" className="w-full h-auto" xmlns="http://www.w3.org/2000/svg">
          {/* Background */}
          <rect width="576" height="248" rx="8" fill="#FAFBFC" />

          {/* Country cards */}
          {countryData.map((country) => {
            const pos = COUNTRY_POSITIONS[country.code];
            if (!pos) return null;

            const level = getStressLevel(country.stress);
            const colors = STRESS_COLORS[level];
            const stressText = country.hasData ? `${(country.stress * 100).toFixed(0)}%` : "—";
            const levelLabel = country.hasData ? getStressLabel(level, isAr) : (isAr ? "لا بيانات" : "No data");

            return (
              <g
                key={country.code}
                className="cursor-pointer"
                onClick={() => onCountryClick?.(country.code)}
              >
                {/* Card background */}
                <rect
                  x={pos.x} y={pos.y}
                  width={pos.w} height={pos.h}
                  rx="6"
                  fill={country.hasData ? colors.bg : "#94A3B8"}
                  opacity="0.08"
                  stroke={country.hasData ? colors.bg : "#94A3B8"}
                  strokeWidth="1.5"
                />

                {/* Hover overlay */}
                <rect
                  x={pos.x} y={pos.y}
                  width={pos.w} height={pos.h}
                  rx="6"
                  fill="transparent"
                  className="hover:fill-black/[0.03] transition-colors"
                />

                {/* Country name — primary text */}
                <text
                  x={pos.x + 12} y={pos.y + 22}
                  fontSize="12" fontWeight="700"
                  fill="#1E293B"
                  className="pointer-events-none"
                >
                  {country.name}
                </text>

                {/* Dominant sector */}
                <text
                  x={pos.x + 12} y={pos.y + 36}
                  fontSize="9" fontWeight="500"
                  fill="#64748B"
                  className="pointer-events-none"
                >
                  {country.sector}
                </text>

                {/* Stress percentage — large, right-aligned */}
                <text
                  x={pos.x + pos.w - 12} y={pos.y + 26}
                  textAnchor="end"
                  fontSize="16" fontWeight="800"
                  fill={country.hasData ? colors.bg : "#94A3B8"}
                  className="pointer-events-none tabular-nums"
                >
                  {stressText}
                </text>

                {/* Classification label */}
                <text
                  x={pos.x + 12} y={pos.y + pos.h - 28}
                  fontSize="9" fontWeight="600"
                  fill={country.hasData ? colors.bg : "#94A3B8"}
                  className="pointer-events-none uppercase"
                  letterSpacing="0.5"
                >
                  {levelLabel}
                </text>

                {/* Loss amount */}
                {country.loss > 0 && (
                  <text
                    x={pos.x + 12} y={pos.y + pos.h - 14}
                    fontSize="11" fontWeight="700"
                    fill={colors.text}
                    className="pointer-events-none tabular-nums"
                  >
                    {formatUsd(country.loss)}
                  </text>
                )}

                {/* Top entity names (small, bottom-right) */}
                {country.entities.slice(0, 2).map((entity, i) => (
                  <text
                    key={i}
                    x={pos.x + pos.w - 12}
                    y={pos.y + pos.h - 28 + i * 13}
                    textAnchor="end"
                    fontSize="8" fontWeight="400"
                    fill="#94A3B8"
                    className="pointer-events-none"
                  >
                    {entity}
                  </text>
                ))}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="px-6 pb-5">
        <div className="bg-slate-50 rounded-lg border border-slate-100 px-4 py-3">
          <div className="flex items-center justify-between flex-wrap gap-y-2">
            <div className="flex items-center gap-4 flex-wrap">
              {(["nominal", "low", "guarded", "elevated", "high", "severe"] as const).map((level) => (
                <div key={level} className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: STRESS_COLORS[level].bg }} />
                  <span className="text-[10px] text-slate-600 font-medium">
                    {getStressLabel(level, isAr)}
                  </span>
                </div>
              ))}
            </div>
            {!hasAnyData && (
              <span className="text-[10px] text-slate-400 italic">
                {isAr ? "اختر سيناريو لعرض بيانات التعرض" : "Select a scenario to view exposure data"}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export type { GCCImpactMapProps };
