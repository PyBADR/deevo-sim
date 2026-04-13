/**
 * Impact Observatory — Design token constants for runtime use.
 * These mirror the CSS custom properties and Tailwind tokens
 * for cases where JS-level access is needed (charts, dynamic styles).
 */

export const colors = {
  bg: {
    main: "#F5F5F2",
    surface: "#FFFFFF",
    muted: "#ECECE8",
  },
  text: {
    primary: "#111111",
    secondary: "#5F5F58",
    tertiary: "#8A8A83",
  },
  border: {
    soft: "#D9D9D2",
    muted: "#E6E6E0",
  },
  charcoal: "#1B1B19",
  graphite: "#252522",
  status: {
    amber: "#A06A34",
    red: "#8E4338",
    olive: "#5E6759",
  },
} as const;

export const radii = {
  sm: "6px",
  md: "10px",
  lg: "14px",
  xl: "18px",
} as const;

export const shadows = {
  soft: "0 1px 4px rgba(0, 0, 0, 0.03)",
  card: "0 2px 8px rgba(0, 0, 0, 0.04)",
  cardHover: "0 4px 16px rgba(0, 0, 0, 0.06)",
} as const;

export const layout = {
  maxContent: "1120px",
  maxNarrow: "720px",
  sectionGap: "5rem",
  blockGap: "2.5rem",
} as const;

/** Stress classification thresholds (URS-based) */
export const stressLevels = {
  NOMINAL: { max: 0.2, color: colors.text.tertiary, label: "Nominal" },
  LOW: { max: 0.35, color: colors.status.olive, label: "Low" },
  GUARDED: { max: 0.5, color: colors.status.olive, label: "Guarded" },
  ELEVATED: { max: 0.65, color: colors.status.amber, label: "Elevated" },
  HIGH: { max: 0.8, color: colors.status.red, label: "High" },
  SEVERE: { max: 1.0, color: colors.status.red, label: "Severe" },
} as const;

export function classifyStress(urs: number): keyof typeof stressLevels {
  if (urs < 0.2) return "NOMINAL";
  if (urs < 0.35) return "LOW";
  if (urs < 0.5) return "GUARDED";
  if (urs < 0.65) return "ELEVATED";
  if (urs < 0.8) return "HIGH";
  return "SEVERE";
}
