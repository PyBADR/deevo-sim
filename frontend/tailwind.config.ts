import type { Config } from "tailwindcss";

/**
 * Impact Observatory | مرصد الأثر — Tailwind Design Tokens
 *
 * Calm, institutional, Apple-inspired.
 * Neutral light palette. No neon. No blue-led. No admin-panel aesthetics.
 */
const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        io: {
          // Surfaces — institutional warm white
          bg:          '#F7F7F5',
          surface:     '#FFFFFF',
          muted:       '#EDEDEB',
          // Text — sovereign charcoal hierarchy
          primary:     '#1A1A1A',
          secondary:   '#555550',
          tertiary:    '#8A8A83',
          // Borders — quiet institutional
          'border-soft':  '#D9D9D2',
          'border-muted': '#E6E6E0',
          // Emphasis — dark sovereign
          charcoal:    '#1B1B19',
          graphite:    '#252522',
          // Accent — sovereign teal (replaces blue)
          accent:      '#0C6B58',
          'accent-hover': '#0A5A4A',
          'accent-dim':   '#E8F5F0',
          // Status — institutional, desaturated
          'status-severe':   '#8C2318',
          'status-high':     '#A0522D',
          'status-elevated': '#8B6914',
          'status-guarded':  '#5E6759',
          'status-low':      '#2D6A4F',
          'status-nominal':  '#3A7D6C',
        },
        // Legacy ds-* tokens preserved for backward compatibility
        ds: {
          bg: '#F8FAFC', 'bg-alt': '#F1F5F9', surface: '#FFFFFF', 'surface-raised': '#FFFFFF',
          card: '#FFFFFF', 'card-hover': '#F8FAFC', 'card-active': '#F1F5F9',
          border: '#E2E8F0', 'border-subtle': '#F1F5F9', 'border-accent': '#CBD5E1', 'border-hover': '#94A3B8',
          text: '#0F172A', 'text-secondary': '#475569', 'text-muted': '#94A3B8', 'text-dim': '#CBD5E1',
          accent: '#0C6B58', 'accent-hover': '#0A5A4A', 'accent-dim': '#3A7D6C',
          'accent-muted': 'rgba(12, 107, 88, 0.06)', 'accent-glow': 'rgba(12, 107, 88, 0.04)',
          gold: '#8B6914', 'gold-light': '#A07D2E', 'gold-muted': 'rgba(139, 105, 20, 0.08)',
          success: '#2D6A4F', 'success-dim': 'rgba(45, 106, 79, 0.06)',
          warning: '#8B6914', 'warning-dim': 'rgba(139, 105, 20, 0.06)',
          danger: '#8C2318', 'danger-dim': 'rgba(140, 35, 24, 0.06)',
          critical: '#6B1A12', 'critical-dim': 'rgba(107, 26, 18, 0.05)',
        },
      },
      fontFamily: {
        sans: ['DM Sans', 'system-ui', '-apple-system', 'sans-serif'],
        ar:   ['IBM Plex Sans Arabic', 'Noto Sans Arabic', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        'hero':       ['4rem',     { lineHeight: '1.06', letterSpacing: '-0.03em', fontWeight: '700' }],
        'hero-sm':    ['3rem',     { lineHeight: '1.08', letterSpacing: '-0.025em', fontWeight: '700' }],
        'heading-1':  ['2.5rem',   { lineHeight: '1.1',  letterSpacing: '-0.025em', fontWeight: '700' }],
        'heading-2':  ['1.75rem',  { lineHeight: '1.2',  letterSpacing: '-0.02em',  fontWeight: '600' }],
        'heading-3':  ['1.25rem',  { lineHeight: '1.35', letterSpacing: '-0.01em',  fontWeight: '600' }],
        'body-lg':    ['1.0625rem',{ lineHeight: '1.7' }],
        'body':       ['0.9375rem',{ lineHeight: '1.65' }],
        'caption':    ['0.875rem', { lineHeight: '1.5' }],
        'label':      ['0.75rem',  { lineHeight: '1.4',  letterSpacing: '0.04em',  fontWeight: '600' }],
        'micro':      ['0.6875rem',{ lineHeight: '1.45' }],
      },
      borderRadius: {
        'card': '12px',
        'badge': '6px',
      },
      boxShadow: {
        'quiet':       '0 1px 3px rgba(0,0,0,0.03)',
        'quiet-md':    '0 2px 8px rgba(0,0,0,0.04)',
        'quiet-lg':    '0 4px 16px rgba(0,0,0,0.05)',
        // Legacy shadows preserved
        'ds':          '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06)',
        'ds-md':       '0 4px 6px rgba(0,0,0,0.04), 0 2px 4px rgba(0,0,0,0.06)',
        'ds-lg':       '0 10px 15px rgba(0,0,0,0.04), 0 4px 6px rgba(0,0,0,0.05)',
        'ds-card-hover':'0 8px 25px rgba(0,0,0,0.05), 0 0 0 1px rgba(29, 78, 216, 0.04)',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '26': '6.5rem',
        '30': '7.5rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
