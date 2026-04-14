/**
 * Impact Observatory | مرصد الأثر — Design Tokens
 *
 * Boardroom aesthetic. Clean spacing. Premium cards.
 * No neon. No black default. Graph is secondary.
 */

export const theme = {
  mode: "light" as const,

  palette: {
    background: "#F8FAFC",
    surface: "#FFFFFF",
    primary: "#0F172A",
    secondary: "#475569",
    accent: "#0C6B58",
    success: "#2D6A4F",
    warning: "#8B6914",
    danger: "#8C2318",
    border: "#E2E8F0",
  },

  classification: {
    severe: "#8C2318",
    high: "#A0522D",
    elevated: "#8B6914",
    guarded: "#5E6759",
    low: "#2D6A4F",
    nominal: "#3A7D6C",
    /** Alias: enterprise components use "critical" for severe-tier */
    critical: "#8C2318",
    /** Alias: enterprise components use "moderate" for guarded-tier */
    moderate: "#5E6759",
  },

  typography: {
    fontFamily: "Inter, 'Noto Sans Arabic', system-ui, sans-serif",
    fontFamilyAr: "'Noto Sans Arabic', 'Cairo', system-ui, sans-serif",
    headlineLarge: { fontSize: "2rem", fontWeight: 700, lineHeight: 1.2 },
    headlineMedium: { fontSize: "1.5rem", fontWeight: 600, lineHeight: 1.3 },
    headlineSmall: { fontSize: "1.25rem", fontWeight: 600, lineHeight: 1.4 },
    bodyLarge: { fontSize: "1rem", fontWeight: 400, lineHeight: 1.6 },
    bodySmall: { fontSize: "0.875rem", fontWeight: 400, lineHeight: 1.5 },
    label: { fontSize: "0.75rem", fontWeight: 500, lineHeight: 1.4, letterSpacing: "0.04em", textTransform: "uppercase" as const },
    metric: { fontSize: "2.5rem", fontWeight: 700, lineHeight: 1.1, fontVariantNumeric: "tabular-nums" },
  },

  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
    xxl: "3rem",
  },

  borderRadius: {
    sm: "6px",
    md: "8px",
    lg: "12px",
    xl: "16px",
  },

  shadow: {
    sm: "0 1px 2px rgba(0,0,0,0.04)",
    md: "0 1px 3px rgba(0,0,0,0.08)",
    lg: "0 4px 12px rgba(0,0,0,0.08)",
    xl: "0 8px 24px rgba(0,0,0,0.12)",
  },

  designRules: [
    "clean_spacing",
    "premium_cards",
    "no_neon",
    "no_black_default",
    "boardroom_aesthetic",
    "graph_is_secondary",
  ],
} as const;

export type Theme = typeof theme;
export type Classification = keyof typeof theme.classification;
