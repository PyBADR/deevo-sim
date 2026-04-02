"use client";

import AppShell from "@/components/shell/AppShell";
import { useAppStore } from "@/store/app-store";

export default function ScenarioLabPage() {
  const isAr = useAppStore((s) => s.language) === "ar";

  return (
    <AppShell activeRoute="scenario-lab">
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="text-center space-y-4 px-6">
          <div className="w-16 h-16 bg-io-accent/10 rounded-2xl flex items-center justify-center mx-auto text-3xl">
            🧪
          </div>
          <h1 className="text-2xl font-bold text-io-primary">
            {isAr ? "معمل السيناريو" : "Scenario Lab"}
          </h1>
          <p className="text-io-secondary max-w-md">
            {isAr
              ? "بناء سيناريوهات مخصصة — قيد التطوير للإصدار الثاني"
              : "Custom scenario builder — under development for V2"}
          </p>
          <span className="inline-block px-3 py-1 text-xs font-semibold bg-io-accent/10 text-io-accent rounded-full">
            V2 Roadmap
          </span>
        </div>
      </div>
    </AppShell>
  );
}
