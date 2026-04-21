"use client";

import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { TOTAL_STEPS } from "../store/trace-impact-store";
import { EXPERIENCE_COPY } from "../lib/step-copy";
import type { Locale } from "@/i18n/dictionary";

interface StepChromeProps {
  stepIndex: number;
  locale: Locale;
  onPrev: () => void;
  onNext: () => void;
  onFinish: () => void;
}

export function StepChrome({
  stepIndex,
  locale,
  onPrev,
  onNext,
  onFinish,
}: StepChromeProps) {
  const isAr = locale === "ar";
  const isFirst = stepIndex === 0;
  const isLast = stepIndex === TOTAL_STEPS - 1;
  const copy = EXPERIENCE_COPY;

  const PrevIcon = isAr ? ChevronRight : ChevronLeft;
  const NextIcon = isAr ? ChevronLeft : ChevronRight;

  return (
    <div
      className="flex items-center justify-between px-6 py-4 bg-io-surface border-t border-io-border"
      role="navigation"
      aria-label={isAr ? "التنقل بين الخطوات" : "Step navigation"}
    >
      {/* Prev Button */}
      <button
        onClick={onPrev}
        disabled={isFirst}
        className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary hover:bg-io-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        aria-label={copy.prev[locale]}
      >
        <PrevIcon className="w-4 h-4" />
        {copy.prev[locale]}
      </button>

      {/* Progress Dots */}
      <div className="flex items-center gap-2" role="tablist" aria-label={isAr ? "الخطوات" : "Steps"}>
        {Array.from({ length: TOTAL_STEPS }).map((_, i) => {
          const isActive = i === stepIndex;
          const isCompleted = i < stepIndex;
          return (
            <motion.button
              key={i}
              role="tab"
              aria-selected={isActive}
              aria-label={isAr ? `الخطوة ${i + 1}` : `Step ${i + 1}`}
              animate={{
                width: isActive ? 24 : 8,
                backgroundColor:
                  isActive || isCompleted ? "#0C6B58" : "#D9D9D2",
              }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
              className="h-2 rounded-full cursor-pointer"
              onClick={() => {
                // Handled by parent via direct index — no-op here,
                // parent uses onPrev/onNext. Dots are visual only.
              }}
              style={{ minWidth: isActive ? 24 : 8 }}
            />
          );
        })}
      </div>

      {/* Next / Finish Button */}
      {isLast ? (
        <button
          onClick={onFinish}
          className="flex items-center gap-2 px-5 py-2 text-sm font-semibold rounded-lg bg-io-accent text-white hover:bg-io-accent-hover transition-colors shadow-quiet-md"
        >
          {copy.finish[locale]}
          <NextIcon className="w-4 h-4" />
        </button>
      ) : (
        <button
          onClick={onNext}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary hover:bg-io-muted transition-colors"
          aria-label={copy.next[locale]}
        >
          {copy.next[locale]}
          <NextIcon className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
