"use client";

import React from "react";
import { motion } from "framer-motion";
import { getScenario, type ScenarioId } from "./data/demo-scenario";

interface SourceStripProps {
  scenarioId: ScenarioId;
}

export function SourceStrip({ scenarioId }: SourceStripProps) {
  const scenario = getScenario(scenarioId);
  const { trust, confidence } = scenario;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.8, duration: 0.4 }}
      className="fixed bottom-0 left-0 right-[260px] z-[55] pointer-events-none"
    >
      <div className="flex items-center justify-center gap-6 px-6 py-2.5 bg-gradient-to-t from-[#FAFAFA] via-[#FAFAFA]/95 to-transparent">
        <Chip label="Sources" value={`${trust.dataSources.length} feeds`} />
        <Divider />
        <Chip label="Freshness" value={trust.dataFreshness} />
        <Divider />
        <Chip label="Confidence" value={`${Math.round(confidence * 100)}%`} accent />
        <Divider />
        <Chip label="Version" value={trust.assessmentVersion} />
      </div>
    </motion.div>
  );
}

function Chip({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[9px] font-semibold uppercase tracking-[0.1em] text-slate-300">
        {label}
      </span>
      <span
        className={`text-[10px] font-bold tabular-nums ${
          accent ? "text-slate-700" : "text-slate-500"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function Divider() {
  return <div className="w-px h-3 bg-slate-200" />;
}
