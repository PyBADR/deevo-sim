"use client";

/**
 * StatusBar — Bottom-of-screen pipeline status and audit metadata
 *
 * Shows: data source indicator, pipeline stages, audit hash,
 * model version, confidence, latency. Minimal footprint.
 */

import React from "react";
import {
  CheckCircle2,
  Database,
  Fingerprint,
  Clock,
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
  const _durationMs = safeNum(durationMs, -1);
  const _stagesCompleted = trust ? safeArr<string>(trust.stagesCompleted) : [];
  const _modelVersion = trust ? safeStr(trust.modelVersion, "—") : "—";
  const _auditHash = trust ? safeStr(trust.auditHash, "—") : "—";

  return (
    <footer className="w-full bg-io-surface border-t border-io-border-muted px-4 py-1.5">
      <div className="flex items-center gap-4 text-[10px]">
        {/* Data source */}
        <div className="flex items-center gap-1">
          {dataSource === "live" ? (
            <Wifi size={10} className="text-io-status-low" />
          ) : (
            <WifiOff size={10} className="text-io-status-elevated" />
          )}
          <span
            className={
              dataSource === "live" ? "text-io-status-low" : "text-io-status-elevated"
            }
          >
            {dataSource === "live" ? "LIVE" : "SIMULATION"}
          </span>
        </div>

        {/* Separator */}
        <span className="text-io-border-soft">|</span>

        {/* Pipeline stages */}
        {trust && (
          <div className="flex items-center gap-1">
            <CheckCircle2 size={10} className="text-io-status-low" />
            <span className="text-io-tertiary">
              {_stagesCompleted.length}/9 layers
            </span>
          </div>
        )}

        <span className="text-io-border-soft">|</span>

        {/* Confidence */}
        <div className="flex items-center gap-1">
          <Database size={10} className="text-io-tertiary" />
          <span className="text-io-tertiary">
            Confidence:{" "}
            <span
              className={
                _confidence >= 0.8
                  ? "text-io-status-low"
                  : _confidence >= 0.6
                  ? "text-io-status-elevated"
                  : "text-io-status-severe"
              }
            >
              {safePercent(_confidence, 0)}%
            </span>
          </span>
        </div>

        <span className="text-io-border-soft">|</span>

        {/* Model version */}
        {trust && (
          <div className="flex items-center gap-1">
            <span className="text-io-tertiary">v{_modelVersion}</span>
          </div>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Audit hash (truncated) */}
        {trust && (
          <div className="flex items-center gap-1">
            <Fingerprint size={10} className="text-io-tertiary" />
            <span className="font-mono text-io-tertiary truncate max-w-[180px]">
              {_auditHash}
            </span>
          </div>
        )}

        {/* Duration */}
        {_durationMs >= 0 && (
          <div className="flex items-center gap-1">
            <Clock size={10} className="text-io-tertiary" />
            <span className="text-io-tertiary tabular-nums">
              {_durationMs >= 1000
                ? `${safeFixed(_durationMs / 1000, 1)}s`
                : `${_durationMs}ms`}
            </span>
          </div>
        )}
      </div>
    </footer>
  );
}
