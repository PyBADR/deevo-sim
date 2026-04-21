"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Compass, LayoutDashboard } from "lucide-react";
import { EXPERIENCE_COPY } from "../lib/step-copy";
import type { Locale } from "@/i18n/dictionary";

interface ExperienceModeToggleProps {
  locale: Locale;
}

export function ExperienceModeToggle({ locale }: ExperienceModeToggleProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const copy = EXPERIENCE_COPY;
  const isAr = locale === "ar";

  const currentMode = searchParams.get("mode");
  const isExperience = currentMode === "experience";
  const runId = searchParams.get("run");

  const handleToggle = () => {
    if (isExperience) {
      // Exit experience → standard view (restore default tab)
      const params = new URLSearchParams();
      if (runId) params.set("run", runId);
      const qs = params.toString();
      router.push(`/command-center${qs ? `?${qs}` : ""}`);
    } else {
      // Enter experience
      const params = new URLSearchParams();
      params.set("mode", "experience");
      if (runId) params.set("run", runId);
      router.push(`/command-center?${params.toString()}`);
    }
  };

  if (isExperience) {
    return (
      <button
        onClick={handleToggle}
        className={`inline-flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg bg-io-charcoal text-white hover:bg-io-graphite transition-colors ${isAr ? "flex-row-reverse" : ""}`}
        aria-label={copy.exitLabel[locale]}
      >
        <LayoutDashboard className="w-3.5 h-3.5" />
        {copy.exitLabel[locale]}
      </button>
    );
  }

  return (
    <button
      onClick={handleToggle}
      className={`inline-flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg border border-io-border text-io-secondary hover:text-io-primary hover:bg-io-muted transition-colors ${isAr ? "flex-row-reverse" : ""}`}
      aria-label={copy.toggleLabel[locale]}
    >
      <Compass className="w-3.5 h-3.5" />
      {copy.toggleLabel[locale]}
    </button>
  );
}
