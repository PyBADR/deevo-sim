"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Compass } from "lucide-react";
import { EXPERIENCE_COPY } from "../lib/step-copy";
import type { Locale } from "@/i18n/dictionary";

interface TraceImpactCTAProps {
  variant: "hero" | "inline";
  locale: Locale;
}

export function TraceImpactCTA({ variant, locale }: TraceImpactCTAProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const copy = EXPERIENCE_COPY;
  const isAr = locale === "ar";

  const handleClick = () => {
    const params = new URLSearchParams();
    params.set("mode", "experience");
    const runId = searchParams.get("run");
    if (runId) params.set("run", runId);
    // Intentionally omit ?tab — experience mode hides the tab rail
    router.push(`/command-center?${params.toString()}`);
  };

  if (variant === "hero") {
    return (
      <motion.button
        onClick={handleClick}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        transition={{ duration: 0.18 }}
        className={`w-full rounded-card bg-io-charcoal text-white px-6 py-5 shadow-quiet-lg flex items-center gap-4 text-left hover:bg-io-graphite transition-colors ${isAr ? "flex-row-reverse text-right" : ""}`}
        dir={isAr ? "rtl" : "ltr"}
        aria-label={`${copy.ctaLabel[locale]} — ${copy.ctaSubLabel[locale]}`}
      >
        <div className="flex-shrink-0 p-3 rounded-lg bg-white/10">
          <Compass className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white leading-tight">
            {copy.ctaLabel[locale]}
          </p>
          <p className="text-xs text-white/60 mt-0.5">
            {copy.ctaSubLabel[locale]}
          </p>
        </div>
        <div className="flex-shrink-0">
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-io-accent text-white">
            {isAr ? "جديد" : "New"}
          </span>
        </div>
      </motion.button>
    );
  }

  // inline variant
  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-io-charcoal text-white hover:bg-io-graphite transition-colors ${isAr ? "flex-row-reverse" : ""}`}
      dir={isAr ? "rtl" : "ltr"}
    >
      <Compass className="w-3.5 h-3.5" />
      {copy.ctaLabel[locale]}
    </button>
  );
}
