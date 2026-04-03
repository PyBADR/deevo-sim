/**
 * Impact Observatory | مرصد الأثر
 * Safe number formatters — never throw on null/undefined/NaN/Infinity/non-numeric.
 * Use these instead of raw .toFixed() calls throughout the codebase.
 */

/**
 * Format a number to fixed decimal places.
 * Returns `fallback` for null / undefined / NaN / Infinity values.
 */
export function fmt(
  value: unknown,
  decimals = 2,
  fallback = "—"
): string {
  if (value === null || value === undefined) return fallback;
  const n = typeof value === "number" ? value : Number(value);
  if (!isFinite(n) || isNaN(n)) return fallback;
  return n.toFixed(decimals);
}

/**
 * Format a plain number as a percentage string (value is already 0–100 range).
 * e.g. 73.4 → "73.4%"
 */
export function fmtPct(
  value: unknown,
  decimals = 1,
  fallback = "0%"
): string {
  if (value === null || value === undefined) return fallback;
  const n = typeof value === "number" ? value : Number(value);
  if (!isFinite(n) || isNaN(n)) return fallback;
  return `${n.toFixed(decimals)}%`;
}

/**
 * Format a 0-1 fraction multiplied by 100 as a percentage string.
 * e.g. 0.734 → "73.4%"
 */
export function fmtFracPct(
  value: unknown,
  decimals = 1,
  fallback = "0%"
): string {
  if (value === null || value === undefined) return fallback;
  const n = typeof value === "number" ? value : Number(value);
  if (!isFinite(n) || isNaN(n)) return fallback;
  return `${(n * 100).toFixed(decimals)}%`;
}

/**
 * Format a USD amount with B/M/K suffix.
 * Handles null/undefined/NaN safely.
 */
export function fmtUSD(
  value: unknown,
  fallback = "$0"
): string {
  if (value === null || value === undefined) return fallback;
  const n = typeof value === "number" ? value : Number(value);
  if (!isFinite(n) || isNaN(n)) return fallback;
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${Math.round(n)}`;
}

/**
 * Safe toFixed — replaces raw `x.toFixed(n)` calls.
 * Handles: undefined, null, NaN, Infinity, -Infinity, non-numeric strings, objects.
 * Never throws.
 */
export function safeFixed(
  value: unknown,
  decimals = 2,
  fallback?: string
): string {
  const fb = fallback !== undefined ? fallback : Number(0).toFixed(decimals);
  if (value === null || value === undefined) return fb;
  const n = typeof value === "number" ? value : Number(value);
  if (!isFinite(n) || isNaN(n)) return fb;
  return n.toFixed(decimals);
}

/**
 * Safe percentage formatter for 0-1 fractions.
 * e.g. safeFixed(0.734, 1) → "73.4", safePct(0.734, 1) → "73.4%"
 */
export function safePct(value: unknown, decimals = 1): string {
  if (value === null || value === undefined) return `${"0".padEnd(decimals > 0 ? 2 + decimals : 1, "0")}%`;
  const n = typeof value === "number" ? value : Number(value);
  if (!isFinite(n) || isNaN(n)) return `0.${"0".repeat(decimals)}%`;
  return `${(n * 100).toFixed(decimals)}%`;
}

/**
 * Safe USD formatter. Alias for fmtUSD with same API as safeFixed family.
 */
export function safeUSD(value: unknown): string {
  return fmtUSD(value, "$0");
}

/**
 * Coerce a potentially undefined/null/NaN value to a safe number.
 */
export function safeNum(value: unknown, fallback = 0): number {
  if (value === null || value === undefined) return fallback;
  const n = typeof value === "number" ? value : Number(value);
  if (!isFinite(n) || isNaN(n)) return fallback;
  return n;
}
