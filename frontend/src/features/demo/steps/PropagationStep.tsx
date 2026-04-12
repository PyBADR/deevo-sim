"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Flame, Ship, Landmark, Shield, Building } from "lucide-react";
import { getScenario } from "../data/demo-scenario";
import type { DemoStepProps } from "../DemoStepRenderer";

const POINT_ICONS = [Flame, Ship, Landmark, Shield, Building];

export function PropagationStep({ scenarioId }: DemoStepProps) {
  const scenario = getScenario(scenarioId);
  const { shock, transmission } = scenario;
  const [activePoint, setActivePoint] = useState(-1);
  const [activeLink, setActiveLink] = useState(-1);

  useEffect(() => {
    setActivePoint(-1);
    setActiveLink(-1);
    const timers: ReturnType<typeof setTimeout>[] = [];
    const BASE = 1200;
    const NODE_DELAY = 700;
    const EDGE_DELAY = 400;

    transmission.points.forEach((_, i) => {
      const nodeTime = BASE + i * (NODE_DELAY + EDGE_DELAY);
      const edgeTime = nodeTime + EDGE_DELAY;
      timers.push(setTimeout(() => setActivePoint(i), nodeTime));
      if (i < transmission.points.length - 1) {
        timers.push(setTimeout(() => setActiveLink(i), edgeTime));
      }
    });
    return () => timers.forEach(clearTimeout);
  }, [transmission.points]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8 py-12">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="mb-5"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-900">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-50" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
          </span>
          <span className="text-xs font-semibold text-white tracking-wide">
            STRESS TRANSMISSION
          </span>
        </span>
      </motion.div>

      {/* PRIMARY HEADLINE — above all numbers */}
      <motion.h2
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="text-2xl md:text-3xl font-bold text-center text-slate-900 mb-2 max-w-2xl"
      >
        {shock.transmissionHeadline}
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-sm text-slate-400 text-center max-w-md mb-10"
      >
        {shock.headline}
      </motion.p>

      {/* 3 shock KPI cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl mb-12">
        {shock.details.map((detail, i) => (
          <motion.div
            key={detail.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.1, duration: 0.4 }}
            className="bg-white border border-slate-200 rounded-xl p-5"
          >
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400 mb-3">
              {detail.label}
            </p>
            <p className="text-2xl font-bold text-slate-900 tabular-nums mb-1">
              {detail.value}
            </p>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {detail.description}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Transmission chain label */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7, duration: 0.3 }}
        className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.15em] mb-6"
      >
        Stress Transmission Path
      </motion.p>

      {/* Exposure points + linkages */}
      <div className="flex items-center justify-center gap-0 w-full max-w-5xl">
        {transmission.points.map((point, i) => {
          const Icon = POINT_ICONS[i] || Flame;
          const isActive = i <= activePoint;
          const isCurrent = i === activePoint;
          const linkLit = i <= activeLink;

          return (
            <React.Fragment key={point.id}>
              <motion.div
                initial={{ opacity: 0.15, scale: 0.88 }}
                animate={isActive ? { opacity: 1, scale: 1 } : { opacity: 0.15, scale: 0.88 }}
                transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                className="relative flex flex-col items-center"
                style={{ zIndex: isCurrent ? 10 : 1 }}
              >
                <div
                  className="w-[108px] md:w-[120px] rounded-xl p-4 text-center border transition-all duration-500"
                  style={{
                    background: isActive ? "#0F172A" : "#FFFFFF",
                    borderColor: isActive ? "#334155" : "#E2E8F0",
                  }}
                >
                  <div className="flex justify-center mb-2">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center"
                      style={{ background: isActive ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.03)" }}
                    >
                      <Icon size={20} style={{ color: isActive ? "#FFF" : "#94A3B8" }} />
                    </div>
                  </div>
                  <p
                    className="text-[11px] font-bold mb-0.5 leading-tight"
                    style={{ color: isActive ? "#FFF" : "#94A3B8" }}
                  >
                    {point.label}
                  </p>
                  <p
                    className="text-[9px] leading-tight"
                    style={{ color: isActive ? "#94A3B8" : "#CBD5E1" }}
                  >
                    {point.description}
                  </p>
                </div>
              </motion.div>

              {/* Edge connector */}
              {i < transmission.points.length - 1 && (
                <div className="flex flex-col items-center mx-1 md:mx-2 flex-shrink-0 w-[60px] md:w-[72px]">
                  <AnimatePresence>
                    {linkLit && (
                      <motion.p
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="text-[9px] font-semibold text-slate-500 mb-1.5 text-center whitespace-nowrap"
                      >
                        {transmission.links[i]?.label}
                      </motion.p>
                    )}
                  </AnimatePresence>
                  <div className="relative w-full h-[3px] rounded-full bg-slate-100 overflow-hidden">
                    <motion.div
                      initial={{ width: "0%" }}
                      animate={{ width: linkLit ? "100%" : "0%" }}
                      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                      className="absolute inset-y-0 left-0 rounded-full bg-slate-700"
                    />
                  </div>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Running cascade label */}
      <div className="mt-10 flex justify-center">
        <AnimatePresence mode="wait">
          {activePoint >= 0 && (
            <motion.div
              key={activePoint}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35 }}
              className="flex items-start gap-3 px-5 py-3.5 rounded-xl max-w-lg bg-white border border-slate-200"
            >
              <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 bg-slate-700" />
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-700 mb-0.5">
                  Step {activePoint + 1}: {transmission.points[activePoint].label}
                </p>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {transmission.cascadeLabels[activePoint]}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Stage progress dots */}
      <div className="mt-8 flex justify-center">
        <div className="flex items-center gap-1.5">
          {transmission.points.map((_, i) => (
            <motion.div
              key={i}
              animate={{
                width: i === activePoint ? 28 : i <= activePoint ? 16 : 8,
                backgroundColor: i <= activePoint ? "#334155" : "#E2E8F0",
                opacity: i <= activePoint ? 1 : 0.4,
              }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="h-[3px] rounded-full"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
