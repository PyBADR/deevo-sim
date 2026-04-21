"use client";

import { motion } from "framer-motion";
import { Shield, TrendingDown, TrendingUp } from "lucide-react";
import type { Scenario } from "@/features/demo/data/demo-scenario";
import type { Locale } from "@/i18n/dictionary";

interface BeforeAfterDecisionPanelProps {
  scenario: Scenario;
  locale: Locale;
}

/**
 * DECISION SPLIT — dominant center-focused delta
 * ─────────────────────────────────────
 * Primary:   SAVED delta ($) + % reduction (center, huge)
 * Secondary: WITHOUT ACTION · WITH ACTION (flanking)
 */
export function BeforeAfterDecisionPanel({
  scenario,
  locale,
}: BeforeAfterDecisionPanelProps) {
  const isAr = locale === "ar";
  const { outcome, lossWithoutAction, lossWithAction, lossSaved } = scenario;

  // Derived: loss reduction percentage
  const lossReductionPct = Math.round(
    ((lossWithoutAction - lossWithAction) / lossWithoutAction) * 100
  );

  const savedDisplay =
    lossSaved >= 1e9
      ? `$${(lossSaved / 1e9).toFixed(1)}B`
      : `$${(lossSaved / 1e6).toFixed(0)}M`;

  return (
    <div className="flex flex-col gap-5" dir={isAr ? "rtl" : "ltr"}>
      {/* PRIMARY — Central dominant SAVED delta */}
      <motion.div
        initial={{ opacity: 0, scale: 0.94 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="rounded-card bg-io-charcoal text-white p-8 text-center shadow-quiet-lg relative overflow-hidden"
      >
        {/* subtle radial glow */}
        <div
          aria-hidden
          className="absolute inset-0 opacity-30 pointer-events-none"
          style={{
            background:
              "radial-gradient(circle at 50% 40%, rgba(12,107,88,0.35) 0%, transparent 60%)",
          }}
        />

        <div className="relative">
          <div
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 mb-4 ${isAr ? "flex-row-reverse" : ""}`}
          >
            <Shield className="w-3.5 h-3.5 text-white/80" />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/70">
              {isAr ? "قيمة القرار" : "Decision Value"}
            </span>
          </div>

          <p
            className="font-bold text-white leading-none tabular-nums mb-2"
            style={{ fontSize: "clamp(3.5rem, 9vw, 6rem)" }}
          >
            {savedDisplay}
          </p>
          <p className="text-sm font-semibold uppercase tracking-wider text-white/60">
            {isAr ? "خسائر متجنبة" : "Avoided Losses"}
          </p>

          {/* Two reduction stats */}
          <div
            className={`mt-6 flex items-center justify-center gap-8 ${isAr ? "flex-row-reverse" : ""}`}
          >
            <div>
              <p className="text-3xl font-bold text-white tabular-nums">
                −{lossReductionPct}%
              </p>
              <p className="text-[10px] uppercase tracking-wider text-white/50 mt-0.5">
                {isAr ? "الخسارة" : "Loss"}
              </p>
            </div>
            <div className="w-px h-10 bg-white/15" />
            <div>
              <p className="text-3xl font-bold text-white tabular-nums">
                −{outcome.withAction.riskReduction}
              </p>
              <p className="text-[10px] uppercase tracking-wider text-white/50 mt-0.5">
                {isAr ? "المخاطر" : "Risk"}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* SECONDARY — Without vs With (flanking comparison) */}
      <div className="grid grid-cols-2 gap-3">
        {/* Without */}
        <motion.div
          initial={{ opacity: 0, x: isAr ? 12 : -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.35, delay: 0.2 }}
          className="rounded-card border-2 border-io-status-severe/30 bg-io-status-severe/5 p-4"
        >
          <div className={`flex items-center gap-1.5 mb-2 ${isAr ? "flex-row-reverse" : ""}`}>
            <TrendingDown className="w-3.5 h-3.5 text-io-status-severe" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-io-status-severe">
              {isAr ? "بدون تدخل" : "Without Action"}
            </span>
          </div>
          <p className="text-2xl font-bold text-io-status-severe tabular-nums leading-none mb-1">
            {outcome.withoutAction.totalLoss}
          </p>
          <p className="text-[11px] text-io-secondary">
            {isAr ? "التعافي:" : "Recovery:"}{" "}
            <span className="font-semibold text-io-primary">
              {outcome.withoutAction.recoveryTimeline}
            </span>
          </p>
        </motion.div>

        {/* With */}
        <motion.div
          initial={{ opacity: 0, x: isAr ? -12 : 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.35, delay: 0.3 }}
          className="rounded-card border-2 border-io-status-low/30 bg-io-status-low/5 p-4"
        >
          <div className={`flex items-center gap-1.5 mb-2 ${isAr ? "flex-row-reverse" : ""}`}>
            <TrendingUp className="w-3.5 h-3.5 text-io-status-low" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-io-status-low">
              {isAr ? "مع التدخل" : "With Action"}
            </span>
          </div>
          <p className="text-2xl font-bold text-io-status-low tabular-nums leading-none mb-1">
            {outcome.withAction.totalLoss}
          </p>
          <p className="text-[11px] text-io-secondary">
            {isAr ? "التعافي:" : "Recovery:"}{" "}
            <span className="font-semibold text-io-primary">
              {outcome.withAction.recoveryTimeline}
            </span>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
