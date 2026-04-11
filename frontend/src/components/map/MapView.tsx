"use client";

/**
 * MapView — Interactive inline SVG map of the GCC region.
 *
 * Shows shock origin, propagation arcs, and exposure intensity
 * as colored dots on a minimal GCC outline. Features hover tooltips,
 * click-to-highlight, and country exposure overlays.
 *
 * Data source: causalChain (from simulation), GCC node coordinates
 * (from /api/v1/nodes or passed as props).
 *
 * Geographic bounds: lat 15–31°N, lng 43–60°E (GCC + buffer)
 */

import { useMemo, useState, useCallback } from "react";
import type { CausalStep } from "@/types/observatory";
import { theme } from "@/styles/theme";

// ── Geographic projection (simple Mercator within GCC bounds) ─────────

const LAT_MIN = 15;
const LAT_MAX = 31;
const LNG_MIN = 43;
const LNG_MAX = 60;

const VIEW_W = 480;
const VIEW_H = 320;

function project(lat: number, lng: number): { x: number; y: number } {
  const x = ((lng - LNG_MIN) / (LNG_MAX - LNG_MIN)) * VIEW_W;
  const y = ((LAT_MAX - lat) / (LAT_MAX - LAT_MIN)) * VIEW_H;
  return { x, y };
}

// ── GCC country outlines (simplified polygons for context) ────────────

const GCC_COUNTRIES: {
  id: string;
  label: string;
  label_ar: string;
  points: string;
  centroid?: { x: number; y: number };
}[] = [
  {
    id: "sa", label: "Saudi Arabia", label_ar: "السعودية",
    points: "196,40 270,30 310,45 320,95 310,180 280,220 210,250 170,220 140,170 150,110 180,60",
  },
  {
    id: "uae", label: "UAE", label_ar: "الإمارات",
    points: "320,95 370,85 380,110 360,130 320,120",
  },
  {
    id: "qa", label: "Qatar", label_ar: "قطر",
    points: "250,85 262,78 265,95 255,100 248,92",
  },
  {
    id: "kw", label: "Kuwait", label_ar: "الكويت",
    points: "196,40 210,35 218,50 208,58 196,50",
  },
  {
    id: "bh", label: "Bahrain", label_ar: "البحرين",
    points: "238,80 244,78 246,85 240,87",
  },
  {
    id: "om", label: "Oman", label_ar: "عُمان",
    points: "360,130 400,100 440,130 430,200 380,260 320,220 310,180 320,120",
  },
];

// ── Stress → color mapping ────────────────────────────────────────────

function stressColor(stress: number): string {
  if (stress >= 0.65) return theme.stress.critical;
  if (stress >= 0.50) return theme.stress.high;
  if (stress >= 0.35) return theme.stress.elevated;
  if (stress >= 0.20) return theme.stress.moderate;
  return theme.stress.low;
}

function stressRadius(stress: number): number {
  return 4 + stress * 8; // 4–12px
}

function stressLabel(stress: number, locale: "en" | "ar"): string {
  if (stress >= 0.65) return locale === "ar" ? "حرج" : "Critical";
  if (stress >= 0.50) return locale === "ar" ? "عالي" : "High";
  if (stress >= 0.35) return locale === "ar" ? "مرتفع" : "Elevated";
  if (stress >= 0.20) return locale === "ar" ? "متوسط" : "Moderate";
  return locale === "ar" ? "منخفض" : "Low";
}

// ── Bilingual labels ──────────────────────────────────────────────────

const L = {
  title:     { en: "GCC Impact Map", ar: "خريطة الأثر الخليجية" },
  shock:     { en: "Shock Origin",   ar: "نقطة الصدمة" },
  legend:    { en: "Stress",         ar: "الضغط" },
  high:      { en: "High",           ar: "عالي" },
  low:       { en: "Low",            ar: "منخفض" },
  click:     { en: "Click node for detail", ar: "انقر على العقدة للتفاصيل" },
  stress:    { en: "Stress",         ar: "الضغط" },
  sector:    { en: "Sector",         ar: "القطاع" },
  noData:    { en: "No impact data", ar: "لا توجد بيانات أثر" },
} as const;

function t(key: keyof typeof L, locale: "en" | "ar"): string {
  return L[key][locale];
}

// ── Node coordinate lookup ───────────────────────────────────────────

interface NodeCoord {
  id: string;
  label: string;
  label_ar: string;
  lat: number;
  lng: number;
  sector: string;
}

// ── Map node (projected) ─────────────────────────────────────────────

interface MapNode {
  id: string;
  label: string;
  label_ar: string;
  x: number;
  y: number;
  stress: number;
  isShock: boolean;
  sector: string;
}

// ── Tooltip state ────────────────────────────────────────────────────

interface TooltipState {
  node: MapNode;
  screenX: number;
  screenY: number;
}

// ── Props ─────────────────────────────────────────────────────────────

interface MapViewProps {
  causalChain: CausalStep[];
  nodes?: NodeCoord[];
  locale: "en" | "ar";
}

// ── Component ─────────────────────────────────────────────────────────

export function MapView({ causalChain, nodes, locale }: MapViewProps) {
  const isAr = locale === "ar";
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  // Build node map from causal chain
  const mapNodes = useMemo(() => {
    if (!causalChain || causalChain.length === 0) return [];

    const coordLookup = new Map<string, NodeCoord>();
    if (nodes) {
      for (const n of nodes) {
        coordLookup.set(n.id, n);
      }
    }

    const seen = new Set<string>();
    const result: MapNode[] = [];

    for (const step of causalChain) {
      const baseId = step.entity_id.replace(/_sub\d+$/, "");
      if (seen.has(baseId)) continue;
      seen.add(baseId);

      const coord = coordLookup.get(baseId);
      if (coord) {
        const { x, y } = project(coord.lat, coord.lng);
        result.push({
          id: baseId,
          label: coord.label,
          label_ar: coord.label_ar,
          x, y,
          stress: step.stress_delta,
          isShock: step.step === 0,
          sector: coord.sector || "infrastructure",
        });
      }
    }
    return result;
  }, [causalChain, nodes]);

  // Build propagation arcs
  const arcs = useMemo(() => {
    if (mapNodes.length < 2) return [];
    const shockNodes = mapNodes.filter((n) => n.isShock);
    const targets = mapNodes.filter((n) => !n.isShock).slice(0, 8);

    const result: { x1: number; y1: number; x2: number; y2: number; stress: number }[] = [];
    for (const src of shockNodes) {
      for (const tgt of targets) {
        result.push({
          x1: src.x, y1: src.y,
          x2: tgt.x, y2: tgt.y,
          stress: tgt.stress,
        });
      }
    }
    return result;
  }, [mapNodes]);

  // ── Interaction handlers ──────────────────────────────────────────

  const handleNodeHover = useCallback(
    (node: MapNode, event: React.MouseEvent) => {
      const rect = (event.currentTarget as SVGElement).closest("svg")?.getBoundingClientRect();
      if (rect) {
        setTooltip({
          node,
          screenX: event.clientX - rect.left,
          screenY: event.clientY - rect.top,
        });
      }
    },
    [],
  );

  const handleNodeLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  const handleNodeClick = useCallback(
    (node: MapNode) => {
      setSelectedId((prev) => (prev === node.id ? null : node.id));
    },
    [],
  );

  return (
    <div
      className="border border-[#1E293B] bg-[#111827] rounded-lg overflow-hidden transition-all duration-250"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#1E293B]">
        <span className="text-[10px] font-semibold text-[#64748B] uppercase tracking-wider">
          {t("title", locale)}
        </span>
        {/* Legend */}
        <div className="flex items-center gap-3">
          <span className="text-[9px] text-[#64748B]">{t("legend", locale)}:</span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: theme.stress.critical }} />
            <span className="text-[9px] text-[#9CA3AF]">{t("high", locale)}</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: theme.stress.moderate }} />
            <span className="text-[9px] text-[#9CA3AF]">{t("low", locale)}</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm border-2 border-red-500 bg-transparent" />
            <span className="text-[9px] text-[#9CA3AF]">{t("shock", locale)}</span>
          </span>
        </div>
      </div>

      {/* SVG Map */}
      <div className="relative">
        <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} className="w-full h-auto" style={{ maxHeight: 300 }}>
          {/* Water background */}
          <rect width={VIEW_W} height={VIEW_H} fill="#0C1929" rx={0} />

          {/* Country outlines */}
          {GCC_COUNTRIES.map((c) => {
            const isHovered = hoveredCountry === c.id;
            return (
              <polygon
                key={c.id}
                points={c.points}
                fill={isHovered ? "#1E293B" : "#151F2E"}
                stroke={isHovered ? "#3B82F6" : "#1E293B"}
                strokeWidth={isHovered ? 1.2 : 0.8}
                className="transition-all duration-200 cursor-pointer"
                onMouseEnter={() => setHoveredCountry(c.id)}
                onMouseLeave={() => setHoveredCountry(null)}
              />
            );
          })}

          {/* Country labels */}
          {GCC_COUNTRIES.map((c) => {
            const pts = c.points.split(" ").map((p) => {
              const [x, y] = p.split(",").map(Number);
              return { x, y };
            });
            const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
            const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
            return (
              <text
                key={`label-${c.id}`}
                x={cx} y={cy}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#64748B"
                style={{ fontSize: 8, pointerEvents: "none", fontWeight: 500 }}
              >
                {isAr ? c.label_ar : c.label}
              </text>
            );
          })}

          {/* Propagation arcs (animated dash) */}
          {arcs.map((arc, i) => (
            <line
              key={`arc-${i}`}
              x1={arc.x1} y1={arc.y1}
              x2={arc.x2} y2={arc.y2}
              stroke={stressColor(arc.stress)}
              strokeWidth={1}
              strokeDasharray="4,3"
              opacity={0.4}
            >
              <animate
                attributeName="stroke-dashoffset"
                from="0"
                to="-14"
                dur="2s"
                repeatCount="indefinite"
              />
            </line>
          ))}

          {/* Nodes */}
          {mapNodes.map((node) => {
            const isSelected = selectedId === node.id;
            const r = stressRadius(node.stress);

            return (
              <g
                key={node.id}
                className="cursor-pointer"
                onMouseEnter={(e) => handleNodeHover(node, e)}
                onMouseLeave={handleNodeLeave}
                onClick={() => handleNodeClick(node)}
              >
                {node.isShock ? (
                  <>
                    {/* Shock origin: pulsing ring + square */}
                    {isSelected && (
                      <rect
                        x={node.x - 10} y={node.y - 10}
                        width={20} height={20}
                        rx={3}
                        fill="none"
                        stroke="#ef4444"
                        strokeWidth={1}
                        opacity={0.3}
                      >
                        <animate
                          attributeName="opacity"
                          values="0.3;0.1;0.3"
                          dur="2s"
                          repeatCount="indefinite"
                        />
                      </rect>
                    )}
                    <rect
                      x={node.x - 6} y={node.y - 6}
                      width={12} height={12}
                      rx={2}
                      fill="none"
                      stroke="#ef4444"
                      strokeWidth={2}
                    />
                    <rect
                      x={node.x - 3} y={node.y - 3}
                      width={6} height={6}
                      rx={1}
                      fill="#ef4444"
                    >
                      <animate
                        attributeName="opacity"
                        values="1;0.5;1"
                        dur="1.5s"
                        repeatCount="indefinite"
                      />
                    </rect>
                  </>
                ) : (
                  <>
                    {/* Selection ring */}
                    {isSelected && (
                      <circle
                        cx={node.x} cy={node.y}
                        r={r + 4}
                        fill="none"
                        stroke={stressColor(node.stress)}
                        strokeWidth={1.5}
                        opacity={0.4}
                      />
                    )}
                    {/* Glow ring on hover */}
                    <circle
                      cx={node.x} cy={node.y}
                      r={r + 2}
                      fill="none"
                      stroke={stressColor(node.stress)}
                      strokeWidth={0}
                      className="transition-all duration-200"
                      opacity={0}
                    />
                    {/* Main dot */}
                    <circle
                      cx={node.x} cy={node.y}
                      r={r}
                      fill={stressColor(node.stress)}
                      opacity={0.8}
                      stroke="#0B1220"
                      strokeWidth={1}
                      className="transition-all duration-200 hover:opacity-100"
                    />
                  </>
                )}
                {/* Label */}
                <text
                  x={node.x}
                  y={node.y + (node.isShock ? 16 : r + 10)}
                  textAnchor="middle"
                  fill="#9CA3AF"
                  style={{ fontSize: 7, pointerEvents: "none", fontWeight: 500 }}
                >
                  {isAr ? node.label_ar : node.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip overlay */}
        {tooltip && (
          <div
            className="absolute pointer-events-none z-10"
            style={{
              left: tooltip.screenX + 12,
              top: tooltip.screenY - 8,
              transform: "translateY(-100%)",
            }}
          >
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-md px-3 py-2 shadow-lg min-w-[140px]">
              <div className="text-[11px] font-semibold text-[#E5E7EB]">
                {isAr ? tooltip.node.label_ar : tooltip.node.label}
              </div>
              <div className="mt-1 space-y-0.5">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-[9px] text-[#64748B]">{t("stress", locale)}</span>
                  <span
                    className="text-[10px] font-bold"
                    style={{ color: stressColor(tooltip.node.stress) }}
                  >
                    {(tooltip.node.stress * 100).toFixed(0)}%
                    <span className="ml-1 font-normal text-[9px]">
                      {stressLabel(tooltip.node.stress, locale)}
                    </span>
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span className="text-[9px] text-[#64748B]">{t("sector", locale)}</span>
                  <span className="text-[10px] text-[#9CA3AF] capitalize">{tooltip.node.sector}</span>
                </div>
                {tooltip.node.isShock && (
                  <div className="mt-1 text-[9px] text-red-400 font-medium">
                    {t("shock", locale)}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer hint */}
      <div className="px-3 py-1.5 border-t border-[#1E293B]">
        <span className="text-[9px] text-[#64748B]">{t("click", locale)}</span>
      </div>
    </div>
  );
}

export default MapView;
