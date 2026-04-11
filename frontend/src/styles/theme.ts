/**
 * theme.ts — Executive dark theme design tokens for Impact Observatory.
 *
 * Single source of truth for all visual tokens used across the Decision
 * Command Center.  Replaces scattered Tailwind color literals with a
 * cohesive, enterprise-grade dark palette.
 *
 * Usage:
 *   import { theme, themeClass } from "@/styles/theme";
 *   <div className={themeClass("card", "border border-card-border")}>
 *
 * All tokens are intentionally CSS-friendly hex strings so they can be
 * used in both className-based Tailwind and inline style overrides.
 */

// ── Core palette ─────────────────────────────────────────────────────

export const theme = {
  /* Backgrounds */
  bg_primary:   "#0B1220",   // page / shell
  bg_secondary: "#0F172A",   // section / zone divider
  bg_card:      "#111827",   // card surface
  bg_hover:     "#1E293B",   // interactive hover

  /* Text */
  text_primary:   "#E5E7EB", // headings, primary copy
  text_secondary: "#9CA3AF", // supporting, muted copy
  text_tertiary:  "#64748B", // timestamps, footnotes
  text_inverse:   "#0F172A", // text on accent backgrounds

  /* Borders */
  border_default: "#1E293B",
  border_subtle:  "#1A2332",
  border_focus:   "#3B82F6",

  /* Accent — semantic */
  accent_green:  "#10B981",  // healthy / positive
  accent_amber:  "#F59E0B",  // warning / elevated
  accent_red:    "#EF4444",  // critical / severe
  accent_blue:   "#3B82F6",  // info / interactive
  accent_purple: "#8B5CF6",  // simulated / AI-derived

  /* Severity scale (risk levels) */
  severity: {
    nominal:  { bg: "#064E3B", text: "#6EE7B7", badge: "#10B981" },
    low:      { bg: "#064E3B", text: "#6EE7B7", badge: "#10B981" },
    guarded:  { bg: "#78350F", text: "#FDE68A", badge: "#F59E0B" },
    elevated: { bg: "#78350F", text: "#FDE68A", badge: "#F59E0B" },
    high:     { bg: "#7F1D1D", text: "#FCA5A5", badge: "#EF4444" },
    severe:   { bg: "#7F1D1D", text: "#FCA5A5", badge: "#EF4444" },
  },

  /* Stress heat (for gauges, progress bars, map dots) */
  stress: {
    critical: "#EF4444",
    high:     "#F97316",
    elevated: "#EAB308",
    moderate: "#22C55E",
    low:      "#64748B",
  },

  /* Surface overlays */
  overlay_light: "rgba(255,255,255,0.03)",
  overlay_dark:  "rgba(0,0,0,0.40)",

  /* Shadows */
  shadow_card:  "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)",
  shadow_modal: "0 20px 60px rgba(0,0,0,0.6)",

  /* Radii */
  radius_sm: "6px",
  radius_md: "8px",
  radius_lg: "12px",

  /* Typography scale (px) */
  font: {
    xs:  "10px",
    sm:  "12px",
    base: "14px",
    lg:  "16px",
    xl:  "20px",
    h1:  "28px",
  },

  /* Transitions */
  transition_fast:   "150ms cubic-bezier(0.4, 0, 0.2, 1)",
  transition_normal: "250ms cubic-bezier(0.4, 0, 0.2, 1)",
  transition_slow:   "400ms cubic-bezier(0.4, 0, 0.2, 1)",
} as const;

// ── Tailwind-class shorthand map ─────────────────────────────────────
// Maps semantic names to Tailwind utility strings for consistent styling

export const tw = {
  /* Surfaces */
  page:    "bg-[#0B1220] text-[#E5E7EB]",
  section: "bg-[#0F172A]",
  card:    "bg-[#111827] border border-[#1E293B] rounded-lg",
  card_hover: "hover:bg-[#1E293B] transition-colors",

  /* Text */
  heading:   "text-[#E5E7EB] font-semibold",
  body:      "text-[#9CA3AF]",
  muted:     "text-[#64748B]",
  label:     "text-[10px] font-semibold text-[#64748B] uppercase tracking-wider",

  /* Interactive */
  btn_primary:   "px-4 py-2 text-xs font-semibold rounded-lg bg-[#3B82F6] text-white hover:bg-[#2563EB] transition-colors",
  btn_secondary: "px-4 py-2 text-xs font-semibold rounded-lg bg-[#1E293B] text-[#9CA3AF] hover:bg-[#334155] hover:text-[#E5E7EB] transition-colors",
  btn_ghost:     "px-3 py-1.5 text-[10px] font-semibold rounded-md bg-transparent text-[#64748B] hover:bg-[#1E293B] hover:text-[#9CA3AF] transition-colors",

  /* Badges */
  badge_green:  "px-2 py-0.5 rounded text-[10px] font-bold bg-[#064E3B] text-[#6EE7B7]",
  badge_amber:  "px-2 py-0.5 rounded text-[10px] font-bold bg-[#78350F] text-[#FDE68A]",
  badge_red:    "px-2 py-0.5 rounded text-[10px] font-bold bg-[#7F1D1D] text-[#FCA5A5]",
  badge_blue:   "px-2 py-0.5 rounded text-[10px] font-bold bg-[#1E3A5F] text-[#93C5FD]",
  badge_purple: "px-2 py-0.5 rounded text-[10px] font-bold bg-purple-900/40 text-purple-300",

  /* Dividers */
  divider: "border-t border-[#1E293B]",
} as const;

// ── Helper: merge theme class with overrides ─────────────────────────

export function themeClass(base: keyof typeof tw, extra?: string): string {
  return extra ? `${tw[base]} ${extra}` : tw[base];
}

export default theme;
