"use client";

/**
 * Step 4 — Transmission (HEART of the demo)
 *
 * Simulation-grade animated cascade:
 *   Oil → Shipping → Banking → Insurance → Government
 *
 * Each node activates sequentially with:
 *   - Animated connector beam between nodes
 *   - Causal label on the edge ("Price spike", "Liquidity stress")
 *   - Ripple effect on activation
 *   - Running narrative below the chain
 *
 * Must feel like a LIVE SIMULATION — not a static flowchart.
 */

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Flame,
  Ship,
  Landmark,
  Shield,
  Building,
} from "lucide-react";
import { demoScenario } from "../data/demo-scenario";

const NODE_ICONS = [Flame, Ship, Landmark, Shield, Building];

const NODE_THEME = [
  { bg: "#FEF2F2", border: "#FECACA", text: "#B91C1C", icon: "#EF4444", glow: "rgba(239,68,68,0.15)", beam: "#EF4444" },
  { bg: "#EFF6FF", border: "#BFDBFE", text: "#1D4ED8", icon: "#3B82F6", glow: "rgba(59,130,246,0.15)", beam: "#3B82F6" },
  { bg: "#EEF2FF", border: "#C7D2FE", text: "#4338CA", icon: "#6366F1", glow: "rgba(99,102,241,0.15)", beam: "#6366F1" },
  { bg: "#FFFBEB", border: "#FDE68A", text: "#B45309", icon: "#F59E0B", glow: "rgba(245,158,11,0.15)", beam: "#F59E0B" },
  { bg: "#F8FAFC", border: "#CBD5E1", text: "#334155", icon: "#64748B", glow: "rgba(100,116,139,0.12)", beam: "#64748B" },
];

export function TransmissionStep() {
  const { transmission } = demoScenario;
  const [activeNode, setActiveNode] = useState(-1);
  const [activeEdge, setActiveEdge] = useState(-1);
  // Orchestrate: node0 → edge0 → node1 → edge1 → …
  useEffect(() => {
    setActiveNode(-1);
    setActiveEdge(-1);
    const timers: ReturnType<typeof setTimeout>[] = [];
    const BASE = 500;
    const NODE_DELAY = 700;
    const EDGE_DELAY = 400;

    transmission.nodes.forEach((_, i) => {
      const nodeTime = BASE + i * (NODE_DELAY + EDGE_DELAY);
      const edgeTime = nodeTime + EDGE_DELAY;

      timers.push(setTimeout(() => setActiveNode(i), nodeTime));
      if (i < transmission.nodes.length - 1) {
        timers.push(setTimeout(() => setActiveEdge(i), edgeTime));
      }
    });
    return () => timers.forEach(clearTimeout);
  }, [transmission.nodes]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-5"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
          </span>
          <span className="text-xs font-semibold text-indigo-600 tracking-wide">
            SIMULATING TRANSMISSION
          </span>
        </span>
      </motion.div>

      {/* Title */}
      <motion.h2
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="text-h2 md:text-h1 text-center text-slate-900 mb-2"
      >
        How the shock propagates
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-400 text-center max-w-md mb-12"
      >
        Watch stress cascade across 5 critical sectors in real time
      </motion.p>

      {/* ════════ TRANSMISSION CHAIN ════════ */}
      <div className="w-full max-w-5xl">
        {/* Nodes + Edges row */}
        <div className="flex items-center justify-center gap-0">
          {transmission.nodes.map((node, i) => {
            const Icon = NODE_ICONS[i];
            const theme = NODE_THEME[i];
            const isActive = i <= activeNode;
            const isCurrent = i === activeNode;
            const edgeLit = i <= activeEdge;

            return (
              <React.Fragment key={node.id}>
                {/* ── NODE ── */}
                <motion.div
                  initial={{ opacity: 0.15, scale: 0.88 }}
                  animate={
                    isActive
                      ? { opacity: 1, scale: 1 }
                      : { opacity: 0.15, scale: 0.88 }
                  }
                  transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                  className="relative flex flex-col items-center"
                  style={{ zIndex: isCurrent ? 10 : 1 }}
                >
                  {/* Ripple ring on active */}
                  {isCurrent && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.6 }}
                      animate={{ opacity: [0, 0.5, 0], scale: [0.6, 1.5, 1.8] }}
                      transition={{ duration: 1.2, ease: "easeOut" }}
                      className="absolute inset-0 flex items-start justify-center pointer-events-none"
                      style={{ top: "12px" }}
                    >
                      <div
                        className="w-20 h-20 rounded-2xl"
                        style={{ boxShadow: `0 0 0 3px ${theme.glow}`, background: "transparent" }}
                      />
                    </motion.div>
                  )}

                  {/* Card */}
                  <div
                    className="w-[108px] md:w-[120px] rounded-xl p-4 text-center border-2 transition-shadow duration-500"
                    style={{
                      background: isActive ? theme.bg : "#F8FAFC",
                      borderColor: isActive ? theme.border : "#E2E8F0",
                      boxShadow: isCurrent
                        ? `0 8px 24px ${theme.glow}, 0 0 0 1px ${theme.border}`
                        : "0 1px 3px rgba(0,0,0,0.04)",
                    }}
                  >
                    <div className="flex justify-center mb-2">
                      <div
                        className="w-9 h-9 rounded-lg flex items-center justify-center transition-colors duration-300"
                        style={{
                          background: isActive ? `${theme.glow}` : "rgba(0,0,0,0.03)",
                        }}
                      >
                        <Icon
                          size={20}
                          style={{ color: isActive ? theme.icon : "#94A3B8" }}
                        />
                      </div>
                    </div>
                    <p
                      className="text-[11px] font-bold mb-0.5 leading-tight"
                      style={{ color: isActive ? theme.text : "#94A3B8" }}
                    >
                      {node.label}
                    </p>
                    <p className="text-[9px] text-slate-400 leading-tight">
                      {node.description}
                    </p>
                  </div>
                </motion.div>

                {/* ── EDGE CONNECTOR ── */}
                {i < transmission.nodes.length - 1 && (
                  <div className="flex flex-col items-center mx-1 md:mx-2 flex-shrink-0 w-[60px] md:w-[72px]">
                    {/* Edge label */}
                    <AnimatePresence>
                      {edgeLit && (
                        <motion.p
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.3 }}
                          className="text-[9px] font-semibold text-slate-500 mb-1.5 text-center whitespace-nowrap"
                        >
                          {transmission.edges[i]?.label}
                        </motion.p>
                      )}
                    </AnimatePresence>

                    {/* Beam line */}
                    <div className="relative w-full h-[3px] rounded-full bg-slate-100 overflow-hidden">
                      <motion.div
                        initial={{ width: "0%" }}
                        animate={{ width: edgeLit ? "100%" : "0%" }}
                        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                        className="absolute inset-y-0 left-0 rounded-full"
                        style={{
                          background: `linear-gradient(90deg, ${NODE_THEME[i].beam}, ${NODE_THEME[i + 1].beam})`,
                        }}
                      />
                      {/* Traveling pulse */}
                      {edgeLit && (
                        <motion.div
                          initial={{ left: "-8px" }}
                          animate={{ left: "calc(100% + 8px)" }}
                          transition={{ duration: 0.6, ease: "easeInOut", repeat: 0 }}
                          className="absolute top-[-2px] w-2 h-[7px] rounded-full"
                          style={{
                            background: NODE_THEME[i + 1].beam,
                            boxShadow: `0 0 6px ${NODE_THEME[i + 1].beam}`,
                          }}
                        />
                      )}
                    </div>

                    {/* Arrow tip */}
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: edgeLit ? 1 : 0.15 }}
                      transition={{ duration: 0.3 }}
                      className="mt-1"
                    >
                      <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
                        <path d="M4 6L0 0H8L4 6Z" fill={edgeLit ? NODE_THEME[i + 1].beam : "#CBD5E1"} />
                      </svg>
                    </motion.div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* ════════ RUNNING NARRATIVE ════════ */}
        <div className="mt-10 flex justify-center">
          <AnimatePresence mode="wait">
            {activeNode >= 0 && (
              <motion.div
                key={activeNode}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.35 }}
                className="flex items-start gap-3 px-5 py-3.5 rounded-xl max-w-lg"
                style={{
                  background: NODE_THEME[activeNode].bg,
                  border: `1px solid ${NODE_THEME[activeNode].border}`,
                }}
              >
                <div
                  className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 animate-pulse"
                  style={{ background: NODE_THEME[activeNode].beam }}
                />
                <div>
                  <p
                    className="text-[10px] font-bold uppercase tracking-[0.12em] mb-0.5"
                    style={{ color: NODE_THEME[activeNode].text }}
                  >
                    Stage {activeNode + 1}: {transmission.nodes[activeNode].label}
                  </p>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {transmission.cascadeLabels[activeNode]}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ════════ STAGE PROGRESS ════════ */}
        <div className="mt-8 flex justify-center">
          <div className="flex items-center gap-1.5">
            {transmission.nodes.map((_, i) => (
              <motion.div
                key={i}
                animate={{
                  width: i === activeNode ? 28 : i <= activeNode ? 16 : 8,
                  backgroundColor:
                    i === activeNode
                      ? NODE_THEME[i].beam
                      : i < activeNode
                      ? NODE_THEME[i].beam
                      : "#E2E8F0",
                  opacity: i <= activeNode ? 1 : 0.4,
                }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="h-[3px] rounded-full"
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
