/**
 * Impact Observatory — Landing Page V3
 *
 * Institutional. Sovereign. Executive.
 * Entry point to a macro-financial decision intelligence system
 * for GCC decision-makers: central bank governors,
 * sovereign wealth fund CIOs, ministry officials.
 *
 * Left: positioning + entry
 * Right: institutional flow visual (Signal → Transmission → Decision → Outcome)
 * Background: subtle intelligence grid with faint gradient
 */

import Link from "next/link";

// ── Institutional Flow Visual ──
// Clean 4-node pipeline: Signal → Transmission → Decision → Outcome
// Thin lines, small nodes, muted labels. No SaaS graphics.

function IntelligenceFlowVisual() {
  const nodes = [
    { label: "Signal", sublabel: "Macro event detected", y: 40 },
    { label: "Transmission", sublabel: "Cross-sector propagation", y: 140 },
    { label: "Decision", sublabel: "Institutional response", y: 240 },
    { label: "Outcome", sublabel: "Impact confirmation", y: 340 },
  ];

  return (
    <svg
      viewBox="0 0 240 400"
      className="w-full max-w-[240px] h-auto"
      aria-hidden="true"
    >
      {/* Vertical connector line */}
      <line
        x1="120" y1="56" x2="120" y2="324"
        stroke="currentColor"
        strokeWidth="1"
        className="text-charcoal/10"
        strokeDasharray="4 4"
      />

      {/* Nodes */}
      {nodes.map((node, idx) => (
        <g key={node.label}>
          {/* Node circle */}
          <circle
            cx="120"
            cy={node.y}
            r={idx === 0 ? 6 : 5}
            className={idx === 0 ? "fill-amber-500/70" : "fill-charcoal/15"}
            stroke="none"
          />

          {/* Outer ring for signal node */}
          {idx === 0 && (
            <circle
              cx="120"
              cy={node.y}
              r="10"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-amber-400/40"
            />
          )}

          {/* Label */}
          <text
            x="144"
            y={node.y - 4}
            className="fill-charcoal/70"
            fontSize="11"
            fontWeight="600"
            letterSpacing="0.03em"
          >
            {node.label}
          </text>

          {/* Sublabel */}
          <text
            x="144"
            y={node.y + 10}
            className="fill-charcoal/30"
            fontSize="9"
            letterSpacing="0.01em"
          >
            {node.sublabel}
          </text>

          {/* Step connector dots between nodes */}
          {idx < nodes.length - 1 && (
            <>
              <circle cx="120" cy={node.y + 33} r="1.5" className="fill-charcoal/8" />
              <circle cx="120" cy={node.y + 50} r="1.5" className="fill-charcoal/8" />
              <circle cx="120" cy={node.y + 67} r="1.5" className="fill-charcoal/8" />
            </>
          )}
        </g>
      ))}

      {/* Faint horizontal cross-links (network feel) */}
      <line x1="60" y1="140" x2="108" y2="140" stroke="currentColor" strokeWidth="0.5" className="text-charcoal/6" />
      <line x1="132" y1="240" x2="190" y2="240" stroke="currentColor" strokeWidth="0.5" className="text-charcoal/6" />
      <circle cx="60" cy="140" r="2" className="fill-charcoal/6" />
      <circle cx="190" cy="240" r="2" className="fill-charcoal/6" />
    </svg>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* ── Intelligence background ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `
            linear-gradient(180deg, #F7F7F5 0%, #F0F0EC 40%, #EAEAE5 100%),
            repeating-linear-gradient(0deg, transparent, transparent 59px, rgba(0,0,0,0.018) 59px, rgba(0,0,0,0.018) 60px),
            repeating-linear-gradient(90deg, transparent, transparent 59px, rgba(0,0,0,0.018) 59px, rgba(0,0,0,0.018) 60px)
          `,
        }}
      />
      {/* Faint radial glow in top-right */}
      <div
        className="absolute -top-20 -right-20 w-[500px] h-[500px] rounded-full pointer-events-none opacity-30"
        style={{
          background: "radial-gradient(circle, rgba(180,170,155,0.15) 0%, transparent 70%)",
        }}
      />

      {/* ── Wordmark ── */}
      <header className="relative z-10 px-8 sm:px-12 pt-8">
        <span className="text-[0.8125rem] font-medium tracking-[0.04em] text-tx-tertiary">
          Impact Observatory
        </span>
      </header>

      {/* ── Hero: Left copy + Right flow visual ── */}
      <main className="relative z-10 flex-1 flex items-center">
        <div className="w-full max-w-[1100px] mx-auto px-8 sm:px-12 py-16 sm:py-0 flex items-center gap-12 lg:gap-20">

          {/* Left: positioning */}
          <div className="flex-1 min-w-0">
            <h1
              className="
                text-[clamp(2.25rem,5.5vw,4rem)] font-semibold
                leading-[1.08] tracking-[-0.035em]
                text-charcoal text-balance
              "
            >
              GCC Decision
              <br />
              Intelligence Platform
            </h1>

            <p
              className="
                mt-5 text-[1.0625rem] sm:text-[1.1875rem]
                leading-[1.6] text-tx-secondary
                max-w-[460px]
              "
            >
              For macroeconomic, financial, and strategic decision systems.
            </p>

            <p
              className="
                mt-2.5 text-[0.9375rem] sm:text-[1.0625rem]
                leading-[1.7] text-tx-tertiary
                max-w-[460px]
              "
              dir="rtl"
            >
              من الإشارة الاقتصادية إلى قرار مؤسسي قابل للتنفيذ.
            </p>

            {/* ── Value line ── */}
            <p className="mt-7 text-[0.875rem] sm:text-[0.9375rem] font-medium text-charcoal/75 tracking-[-0.005em] max-w-[460px]">
              Understand Impact. Control Transmission. Execute Decisions.
            </p>

            {/* ── Trust strip ── */}
            <div className="mt-8 flex items-center gap-3 flex-wrap text-[0.6875rem] font-medium text-tx-tertiary uppercase tracking-[0.06em]">
              <span>Institutional Reference Dataset</span>
              <span className="w-1 h-1 rounded-full bg-tx-tertiary/30" />
              <span>17-Stage Simulation Engine</span>
              <span className="w-1 h-1 rounded-full bg-tx-tertiary/30" />
              <span>GCC Coverage</span>
            </div>

            {/* ── Entry ── */}
            <div className="mt-8">
              <Link
                href="/command-center?demo=true"
                className="
                  inline-flex items-center gap-3
                  text-[0.9375rem] font-medium text-charcoal
                  border-b border-charcoal/30 pb-1
                  transition-all duration-200
                  hover:border-charcoal hover:gap-4
                "
              >
                Enter Decision Briefing
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M3 8h10M9 4l4 4-4 4"
                    stroke="currentColor"
                    strokeWidth="1.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </Link>
            </div>
          </div>

          {/* Right: institutional flow visual (hidden on small screens) */}
          <div className="hidden lg:flex items-center justify-center flex-shrink-0 w-[260px]">
            <IntelligenceFlowVisual />
          </div>
        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="relative z-10 px-8 sm:px-12 pb-8 flex items-end justify-between">
        <span className="text-[0.6875rem] text-tx-tertiary tracking-[0.02em]">
          GCC Decision Intelligence Platform
        </span>
        <span className="text-[0.6875rem] text-tx-tertiary tabular-nums">
          2026
        </span>
      </footer>
    </div>
  );
}
