import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Impact Observatory — Light/boardroom palette
        "io-bg": "#F8FAFC",
        "io-surface": "#FFFFFF",
        "io-primary": "#0F172A",
        "io-secondary": "#475569",
        "io-accent": "#1D4ED8",
        "io-success": "#15803D",
        "io-warning": "#B45309",
        "io-danger": "#B91C1C",
        "io-border": "#E2E8F0",
        // Classification colors
        "io-critical": "#B91C1C",
        "io-elevated": "#B45309",
        "io-moderate": "#CA8A04",
        "io-low": "#15803D",
        "io-nominal": "#059669",
        // Legacy gcc-* colors removed — all migrated to io-* palette
      },
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        en: ["DM Sans", "system-ui", "sans-serif"],
        ar: ["IBM Plex Sans Arabic", "Noto Sans Arabic", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
