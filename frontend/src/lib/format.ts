/**
 * Impact Observatory | مرصد الأثر — Null-Safe Formatting Utilities
 *
 * Boundary guards for numeric and array formatting. These do NOT replace
 * root-cause fixes — they exist to prevent .toFixed() / .map() crashes
 * if any future schema drift occurs.
 *
 * Every feature component should import from this module instead of
 * calling .toFixed() directly.
 */

const FALLBACK = "—";

/**
 * Null-safe .toFixed() replacement.
 * Returns formatted string or fallback for undefined/null/NaN.
 */
export function safeFixed(
  value: unknown,
  digits = 1,
  fallback = FALLBACK
): string {
  if (value === null || value === undefined) return fallback;
  const n = Number(value);
  if (!isFinite(n)) return fallback;
  return n.toFixed(digits);
}

/**
 * Null-safe percentage formatter.
 * Multiplies by 100 and appends "%". Returns fallback for non-numeric input.
 */
export function safePercent(
  value: unknown,
  digits = 1,
  fallback = FALLBACK
): string {
  if (value === null || value === undefined) return fallback;
  const n = Number(value);
  if (!isFinite(n)) return fallback;
  return `${(n * 100).toFixed(digits)}%`;
}

/**
 * Format USD amounts with B/M/K suffixes.
 * Returns fallback for non-numeric input.
 */
export function formatUSD(value: unknown, fallback = FALLBACK): string {
  if (value === null || value === undefined) return fallback;
  const n = Number(value);
  if (!isFinite(n)) return fallback;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${Math.round(n).toLocaleString()}`;
}

/**
 * Format hours into human-readable duration (h / d / mo).
 * Returns "N/A" for null/undefined (meaning: data not available).
 */
export function formatHours(value: unknown, fallback = "N/A"): string {
  if (value === null || value === undefined) return fallback;
  const h = Number(value);
  if (!isFinite(h)) return fallback;
  if (h >= 720) return `${Math.round(h / 720)}mo`;
  if (h >= 24) return `${Math.round(h / 24)}d`;
  return `${Math.round(h)}h`;
}

/**
 * Ensure value is an array. Returns empty array for non-array input.
 * Use at system boundaries to prevent .map() on undefined/null/object.
 */
export function safeArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  return [];
}

/**
 * Convert snake_case mechanism labels to human-readable text.
 * "direct_shock" → "Direct Shock", "price_transmission" → "Price Transmission"
 */
const MECHANISM_LABELS: Record<string, { en: string; ar: string }> = {
  direct_shock:          { en: "Direct Shock",          ar: "صدمة مباشرة" },
  price_transmission:    { en: "Price Transmission",    ar: "انتقال الأسعار" },
  physical_constraint:   { en: "Physical Constraint",   ar: "قيد مادي" },
  capacity_overflow:     { en: "Capacity Overflow",     ar: "تجاوز الطاقة" },
  supply_chain:          { en: "Supply Chain",          ar: "سلسلة التوريد" },
  claims_cascade:        { en: "Claims Cascade",        ar: "سلسلة المطالبات" },
  monetary_transmission: { en: "Monetary Transmission", ar: "انتقال نقدي" },
  secondary_contagion:   { en: "Secondary Contagion",   ar: "عدوى ثانوية" },
  liquidity_stress:      { en: "Liquidity Stress",      ar: "ضغط السيولة" },
  credit_channel:        { en: "Credit Channel",        ar: "قناة الائتمان" },
  trade_disruption:      { en: "Trade Disruption",      ar: "اضطراب تجاري" },
  sovereign_exposure:    { en: "Sovereign Exposure",    ar: "تعرض سيادي" },
  reinsurance_trigger:   { en: "Reinsurance Trigger",   ar: "تفعيل إعادة التأمين" },
  fx_pressure:           { en: "FX Pressure",           ar: "ضغط العملات" },
  fiscal_transmission:   { en: "Fiscal Transmission",   ar: "انتقال مالي" },
  operational_risk:      { en: "Operational Risk",      ar: "مخاطر تشغيلية" },
};

export function humanizeMechanism(mechanism: string | undefined | null, locale: "en" | "ar" = "en"): string {
  if (!mechanism) return FALLBACK;
  const known = MECHANISM_LABELS[mechanism];
  if (known) return locale === "ar" ? known.ar : known.en;
  // Fallback: capitalize and replace underscores
  return mechanism.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Count true values in a breach flags object.
 * Backend returns breach_flags as {lcr_breach: bool, nsfr_breach: bool, ...}.
 * This converts to an integer count.
 */
export function countBreaches(flags: object | null | undefined): number {
  if (!flags || typeof flags !== "object") return 0;
  return Object.values(flags).filter((v) => v === true).length;
}

/**
 * Classify severity based on breach count.
 */
export function classifyByBreaches(
  breachCount: number,
  thresholds: { critical: number; elevated: number } = { critical: 3, elevated: 1 }
): "CRITICAL" | "ELEVATED" | "MODERATE" {
  if (breachCount >= thresholds.critical) return "CRITICAL";
  if (breachCount >= thresholds.elevated) return "ELEVATED";
  return "MODERATE";
}
