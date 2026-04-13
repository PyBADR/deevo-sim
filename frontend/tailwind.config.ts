import type { Config } from "tailwindcss";

/**
 * Impact Observatory — Design System Tokens
 * Neutral premium palette. No blue-led identity.
 * Apple-inspired calmness, decision-first structure.
 */
const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          main: "#F5F5F2",
          surface: "#FFFFFF",
          muted: "#ECECE8",
        },
        tx: {
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
        // Legacy io-* tokens kept for backward compat with command-center
        io: {
          bg: "#F8FAFC",
          surface: "#FFFFFF",
          primary: "#0F172A",
          secondary: "#475569",
          accent: "#1D4ED8",
          success: "#15803D",
          warning: "#B45309",
          danger: "#B91C1C",
          border: "#E2E8F0",
          critical: "#991B1B",
          elevated: "#B45309",
          moderate: "#A16207",
          guarded: "#15803D",
          stable: "#475569",
        },
      },
      fontFamily: {
        sans: ["DM Sans", "system-ui", "-apple-system", "sans-serif"],
        ar: ["IBM Plex Sans Arabic", "Noto Sans Arabic", "sans-serif"],
        mono: ["JetBrains Mono", "SF Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        hero: ["4.5rem", { lineHeight: "1.04", letterSpacing: "-0.035em", fontWeight: "600" }],
        "hero-sub": ["1.375rem", { lineHeight: "1.5", letterSpacing: "-0.01em", fontWeight: "400" }],
        "section-title": ["2rem", { lineHeight: "1.15", letterSpacing: "-0.025em", fontWeight: "600" }],
        "section-sub": ["1.0625rem", { lineHeight: "1.65", letterSpacing: "0", fontWeight: "400" }],
        "card-title": ["1.125rem", { lineHeight: "1.35", letterSpacing: "-0.01em", fontWeight: "600" }],
        "card-body": ["0.9375rem", { lineHeight: "1.6", fontWeight: "400" }],
        label: ["0.8125rem", { lineHeight: "1.5", letterSpacing: "0.01em", fontWeight: "500" }],
        caption: ["0.75rem", { lineHeight: "1.5", letterSpacing: "0.01em", fontWeight: "400" }],
        micro: ["0.6875rem", { lineHeight: "1.45", letterSpacing: "0.02em", fontWeight: "500" }],
        // Legacy sizes for command-center compat
        display: ["4rem", { lineHeight: "1.06", letterSpacing: "-0.03em", fontWeight: "700" }],
        "display-sm": ["3rem", { lineHeight: "1.08", letterSpacing: "-0.025em", fontWeight: "700" }],
        h1: ["2.25rem", { lineHeight: "1.12", letterSpacing: "-0.02em", fontWeight: "700" }],
        h2: ["1.75rem", { lineHeight: "1.18", letterSpacing: "-0.015em", fontWeight: "600" }],
        h3: ["1.25rem", { lineHeight: "1.3", letterSpacing: "-0.01em", fontWeight: "600" }],
        h4: ["1.0625rem", { lineHeight: "1.4", letterSpacing: "-0.005em", fontWeight: "600" }],
        "body-lg": ["1.0625rem", { lineHeight: "1.7" }],
        body: ["0.9375rem", { lineHeight: "1.65" }],
        nano: ["0.6875rem", { lineHeight: "1.45" }],
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "14px",
        xl: "18px",
        // Legacy
        ds: "8px",
        "ds-lg": "12px",
        "ds-xl": "16px",
        "ds-2xl": "20px",
      },
      boxShadow: {
        soft: "0 1px 4px rgba(0, 0, 0, 0.03)",
        card: "0 2px 8px rgba(0, 0, 0, 0.04)",
        "card-hover": "0 4px 16px rgba(0, 0, 0, 0.06)",
        // Legacy
        ds: "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)",
        "ds-md": "0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.06)",
        "ds-lg": "0 10px 15px rgba(0,0,0,0.04), 0 4px 6px rgba(0,0,0,0.05)",
        "ds-glow": "0 0 0 1px rgba(29, 78, 216, 0.06)",
        "ds-glow-md": "0 0 0 1px rgba(29, 78, 216, 0.10)",
        "ds-glow-accent": "0 0 0 3px rgba(29, 78, 216, 0.06)",
        "ds-inner": "inset 0 1px 0 rgba(255,255,255,0.6)",
        "ds-card-hover": "0 8px 25px rgba(0,0,0,0.05), 0 0 0 1px rgba(29, 78, 216, 0.04)",
      },
      spacing: {
        18: "4.5rem",
        22: "5.5rem",
        26: "6.5rem",
        30: "7.5rem",
        34: "8.5rem",
        38: "9.5rem",
      },
      maxWidth: {
        content: "1120px",
        narrow: "720px",
      },
      animation: {
        "fade-in": "fadeIn 0.6s ease-out forwards",
        "slide-up": "slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
