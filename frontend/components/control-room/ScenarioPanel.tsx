"use client";

import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Play, AlertTriangle } from "lucide-react";
import type { ScenarioTemplate, ScenarioResult } from "@/lib/control-room-types";

interface ScenarioPanelProps {
  scenarios: ScenarioTemplate[];
  onRunScenario: (scenarioId: string, severity: number) => void;
  loading: boolean;
  result: ScenarioResult | null;
  language: "en" | "ar";
}

export default function ScenarioPanel({
  scenarios,
  onRunScenario,
  loading,
  result,
  language,
}: ScenarioPanelProps) {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [severity, setSeverity] = useState(5);

  const selected = useMemo(
    () => scenarios.find((s) => s.id === selectedScenario),
    [selectedScenario, scenarios]
  );

  const handleRunScenario = () => {
    if (selectedScenario) {
      onRunScenario(selectedScenario, severity);
    }
  };

  return (
    <div className="w-full h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b ds-border">
        <h2 className="text-sm font-semibold uppercase tracking-wider ds-text-secondary">
          {language === "en" ? "Scenario Execution" : "تنفيذ السيناريو"}
        </h2>
      </div>

      {/* Scenario Selection */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Scenario Dropdown */}
        <div>
          <label className="text-xs uppercase tracking-wider ds-text-secondary block mb-2">
            {language === "en" ? "Select Scenario" : "اختر السيناريو"}
          </label>
          <select
            value={selectedScenario || ""}
            onChange={(e) => setSelectedScenario(e.target.value)}
            disabled={loading}
            className="w-full p-2 rounded text-sm ds-bg-panel ds-border border ds-input transition-colors disabled:opacity-50"
          >
            <option value="">
              {language === "en"
                ? "Choose a scenario..."
                : "اختر سيناريو..."}
            </option>
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {language === "en" ? scenario.name : scenario.nameAr}
              </option>
            ))}
          </select>
        </div>

        {/* Scenario Details */}
        {selected && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-3 rounded ds-bg-accent/10 border ds-border-accent/30"
          >
            <h3 className="font-semibold text-sm mb-2">
              {language === "en" ? selected.name : selected.nameAr}
            </h3>
            <p className="text-xs ds-text-secondary mb-3">
              {language === "en"
                ? selected.description
                : selected.descriptionAr}
            </p>
            <div className="flex items-center gap-2 text-xs">
              <AlertTriangle size={14} className="ds-text-accent" />
              <span>
                {language === "en" ? "Severity:" : "الشدة:"}{" "}
                <span className="font-semibold">{selected.severity}</span>
              </span>
            </div>
          </motion.div>
        )}

        {/* Severity Slider */}
        {selected && (
          <div>
            <label className="text-xs uppercase tracking-wider ds-text-secondary block mb-2">
              {language === "en" ? "Impact Severity" : "شدة التأثير"}
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min="1"
                max="10"
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                disabled={loading}
                className="w-full accent-ds-accent disabled:opacity-50"
              />
              <div className="flex justify-between text-xs ds-text-secondary">
                <span>{language === "en" ? "Low" : "منخفضة"}</span>
                <span className="ds-text-accent font-semibold">{severity}/10</span>
                <span>{language === "en" ? "High" : "عالية"}</span>
              </div>
            </div>
          </div>
        )}

        {/* Run Button */}
        {selected && (
          <motion.button
            onClick={handleRunScenario}
            disabled={loading || !selectedScenario}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full p-3 rounded font-semibold text-sm bg-ds-accent text-black hover:bg-opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-4 h-4 border-2 border-black border-t-transparent rounded-full"
                />
                {language === "en" ? "Running..." : "جاري التنفيذ..."}
              </>
            ) : (
              <>
                <Play size={16} />
                {language === "en" ? "Execute Scenario" : "تنفيذ السيناريو"}
              </>
            )}
          </motion.button>
        )}

        {/* Results Display */}
        {result && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3 p-3 rounded ds-bg-panel border ds-border"
          >
            <div>
              <h4 className="text-xs uppercase tracking-wider ds-text-secondary mb-2">
                {language === "en" ? "Execution Results" : "نتائج التنفيذ"}
              </h4>
            </div>

            {/* Severity Badge */}
            <div className="flex items-center justify-between">
              <span className="text-xs ds-text-secondary">
                {language === "en" ? "Final Severity" : "الشدة النهائية"}
              </span>
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className={`px-2 py-1 rounded text-xs font-semibold ${
                  result.severity === "critical"
                    ? "bg-red-500/20 text-red-400"
                    : result.severity === "high"
                      ? "bg-orange-500/20 text-orange-400"
                      : result.severity === "medium"
                        ? "bg-yellow-500/20 text-yellow-400"
                        : "bg-green-500/20 text-green-400"
                }`}
              >
                {result.severity?.toUpperCase()}
              </motion.span>
            </div>

            {/* Total Impact */}
            <div className="flex items-center justify-between">
              <span className="text-xs ds-text-secondary">
                {language === "en" ? "Total Impact" : "التأثير الكلي"}
              </span>
              <motion.span
                initial={{ x: 20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                className="font-semibold ds-text-accent"
              >
                {(result.totalImpact * 100).toFixed(1)}%
              </motion.span>
            </div>

            {/* Affected Entities */}
            <div>
              <span className="text-xs ds-text-secondary block mb-1">
                {language === "en"
                  ? "Affected Entities"
                  : "الكيانات المتأثرة"}
              </span>
              <div className="text-sm font-semibold">
                {result.affectedEntities?.length || 0}
              </div>
            </div>

            {/* Risk Delta */}
            {result.riskDelta !== undefined && (
              <div className="flex items-center justify-between pt-2 border-t ds-border">
                <span className="text-xs ds-text-secondary">
                  {language === "en" ? "Risk Change" : "تغيير المخاطر"}
                </span>
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className={`text-sm font-semibold ${
                    result.riskDelta > 0
                      ? "text-red-400"
                      : result.riskDelta < 0
                        ? "text-green-400"
                        : "ds-text-secondary"
                  }`}
                >
                  {result.riskDelta > 0 ? "+" : ""}
                  {(result.riskDelta * 100).toFixed(1)}%
                </motion.span>
              </div>
            )}

            {/* Summary */}
            {result.summary && (
              <div className="pt-3 border-t ds-border">
                <p className="text-xs ds-text-secondary leading-relaxed">
                  {language === "en"
                    ? result.summary
                    : result.summaryAr || result.summary}
                </p>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}
