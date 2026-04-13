"use client";

import React from "react";
import type { OperatingScenario } from "../types/scenario-operating";

interface ScenarioOperatingStripProps {
  scenarios: OperatingScenario[];
  activeScenarioId: string | null;
  onSelect: (id: string) => void;
}

function severityLabel(severity: number) {
  return `${Math.round(severity * 100)}%`;
}

export function ScenarioOperatingStrip({
  scenarios,
  activeScenarioId,
  onSelect,
}: ScenarioOperatingStripProps) {
  return (
    <div className="max-w-6xl mx-auto px-6 sm:px-8 pt-5 pb-1 overflow-x-auto">
      <div className="flex gap-3 min-w-max">
        {scenarios.map((scenario) => {
          const active = scenario.id === activeScenarioId;
          return (
            <button
              key={scenario.id}
              onClick={() => onSelect(scenario.id)}
              className={`text-left rounded-2xl border px-4 py-3 min-w-[250px] transition-all ${
                active
                  ? "bg-white border-[#0071e3] shadow-sm"
                  : "bg-[#fbfbfd] border-[#e5e5e7] hover:border-[#c7c7cc]"
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="text-[1.125rem]">{scenario.icon}</div>
                <span className={`text-[0.6875rem] font-semibold ${active ? "text-[#0071e3]" : "text-[#6e6e73]"}`}>
                  {severityLabel(scenario.severity)}
                </span>
              </div>
              <p className="text-[0.875rem] font-semibold text-[#1d1d1f] leading-snug mb-1">
                {scenario.title}
              </p>
              <p className="text-[0.75rem] text-[#6e6e73] leading-relaxed line-clamp-2">
                {scenario.description}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
