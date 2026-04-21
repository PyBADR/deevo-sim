"use client";

import { AnimatePresence, motion } from "framer-motion";
import { STEP_COPY } from "../lib/step-copy";
import { TOTAL_STEPS } from "../store/trace-impact-store";
import type { Locale } from "@/i18n/dictionary";

interface NarrativeStripProps {
  stepIndex: number;
  locale: Locale;
}

export function NarrativeStrip({ stepIndex, locale }: NarrativeStripProps) {
  const copy = STEP_COPY[stepIndex];
  const isAr = locale === "ar";

  return (
    <div
      className={`bg-io-charcoal text-white px-6 py-4 ${isAr ? "text-right" : "text-left"}`}
      dir={isAr ? "rtl" : "ltr"}
    >
      <div className="max-w-4xl mx-auto">
        {/* Step label + counter */}
        <AnimatePresence mode="wait">
          <motion.div
            key={`label-${stepIndex}`}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className={`flex items-center gap-2 mb-1 ${isAr ? "flex-row-reverse justify-end" : ""}`}
          >
            <span className="text-xs font-semibold tracking-widest uppercase text-white/50">
              {copy.label[locale]}
            </span>
            <span className="text-xs text-white/30">
              {stepIndex + 1} / {TOTAL_STEPS}
            </span>
          </motion.div>
        </AnimatePresence>

        {/* Title */}
        <AnimatePresence mode="wait">
          <motion.h2
            key={`title-${stepIndex}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.28, ease: "easeOut", delay: 0.04 }}
            className="text-lg font-semibold text-white leading-snug"
          >
            {copy.title[locale]}
          </motion.h2>
        </AnimatePresence>

        {/* Subtitle */}
        <AnimatePresence mode="wait">
          <motion.p
            key={`subtitle-${stepIndex}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25, delay: 0.1 }}
            className="text-sm text-white/60 mt-1 leading-relaxed"
          >
            {copy.subtitle[locale]}
          </motion.p>
        </AnimatePresence>
      </div>
    </div>
  );
}
