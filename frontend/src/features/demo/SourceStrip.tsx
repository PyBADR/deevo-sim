"use client";

/**
 * SourceStrip — Compact credibility ribbon
 *
 * Fixed at the bottom of the demo content area.
 * Shows: source count, data freshness, confidence, model version.
 * Subtle, premium, never distracting.
 */

import React from "react";
import { motion } from "framer-motion";
import { demoScenario } from "./data/demo-scenario";

export function SourceStrip() {
  const { trust, confidence } = demoScenario;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.8, duration: 0.4 }}
      className="fixed bottom-0 left-0 right-[260px] z-[55] pointer-events-none"
    >
      <div className="flex items-center justify-center gap-6 px-6 py-2.5 bg-gradient-to-t from-white via-white/95 to-white/0">
        <Chip label="Sources" value={`${trust.dataSources.length} feeds`} />
        <Divider />
        <Chip label="Freshness" value={trust.dataFreshness} />
        <Divider />
        <Chip label="Confidence" value={`${Math.round(confidence * 100)}%`} accent />
        <Divider />
        <Chip label="Model" value={trust.modelVersion} />
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
          accent ? "text-blue-500" : "text-slate-500"
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
