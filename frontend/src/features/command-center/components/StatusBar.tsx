"use client";

/**
 * StatusBar — Minimal bottom bar for data provenance
 *
 * Clean, light-themed. Shows: data source, confidence, model version, audit hash.
 * No technical pipeline stages or dark theme.
 */

import React from "react";
import {
  CheckCircle2,
  Fingerprint,
  Wifi,
  WifiOff,
} from "lucide-react";
import type { DataSource, CommandCenterTrust } from "../lib/command-store";
import { safeNum, safeStr, safeArr, safeFixed, safePercent } from "../lib/format";

// ── Types ─────────────────────────────────────────────────────────────

interface StatusBarProps {
  dataSource: DataSource;
  trust: CommandCenterTrust | null;
  confidence: number;
  durationMs?: number;
}

// ── Main Component ────────────────────────────────────────────────────

export function StatusBar({
  dataSource,
  trust,
  confidence,
  durationMs,
}: StatusBarProps) {
  const _confidence = safeNum(confidence);
  const _modelVersion = trust ? safeStr(trust.modelVersion, "—") : "—";
  const _auditHash = trust ? safeStr(trust.auditHash, "—") : "—";

  return (
    <footer className="w-full bg-white border-t border-slate-200 px-4 py-1.5">
      <div className="flex items-center gap-4 text-[10px]">
        {/* Data source */}
        <div className="flex items-center gap-1">
          {dataSource === "live" ? (
            <Wifi size={10} className="text-emerald-600" />
          ) : (
            <WifiOff size={10} className="text-amber-500" />
          )}
          <span
            className={
              dataSource === "live" ? "text-emerald-700 font-medium" : "text-amber-600 font-medium"
            }
          >
            {dataSource === "live" ? "Live Data" : "Demo Mode"}
          </span>
        </div>

        {/* Separator */}
        <span className="text-slate-300">|</span>

        {/* Confidence */}
        <div className="flex items-center gap-1">
          <CheckCircle2 size={10} className="text-slate-400" />
          <span className="text-slate-500">
            Confidence:{" "}
            <span
              className={
                _confidence >= 0.8
                  ? "text-emerald-700 font-semibold"
                  : _confidence >= 0.6
                  ? "text-amber-700 font-semibold"
                  : "text-red-700 font-semibold"
              }
            >
              {safePercent(_confidence, 0)}%
            </span>
          </span>
        </div>

        <span className="text-slate-300">|</span>

        {/* Model version */}
        {trust && (
          <span className="text-slate-400">v{_modelVersion}</span>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Audit hash (truncated) */}
        {trust && (
          <div className="flex items-center gap-1">
            <Fingerprint size={10} className="text-slate-400" />
            <span className="font-mono text-slate-400 truncate max-w-[180px]">
              {_auditHash}
            </span>
          </div>
        )}
      </div>
    </footer>
  );
}
