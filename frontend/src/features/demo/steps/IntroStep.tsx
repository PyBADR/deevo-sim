"use client";

/**
 * Step 1 — Introduction
 *
 * Title screen: "Macro Financial Intelligence for GCC"
 * Clean, cinematic, Apple-keynote feel.
 */

import React from "react";
import { motion } from "framer-motion";
import {
  Globe,
  Shield,
  TrendingUp,
  Building2,
  Landmark,
  Cpu,
} from "lucide-react";

const SECTORS = [
  { icon: Globe, label: "Energy" },
  { icon: Landmark, label: "Banking" },
  { icon: Shield, label: "Insurance" },
  { icon: Cpu, label: "Fintech" },
  { icon: Building2, label: "Real Estate" },
  { icon: TrendingUp, label: "Government" },
];

export function IntroStep() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8">
      {/* Badge */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.6 }}
        className="mb-8"
      >
        <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 border border-blue-100">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-xs font-semibold text-blue-700 tracking-wide">
            AI SIMULATION ENGINE
          </span>
        </span>
      </motion.div>

      {/* Title */}
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className="text-display-sm md:text-display text-center text-slate-900 max-w-4xl leading-tight"
      >
        Macro Financial
        <br />
        <span className="text-blue-600">Intelligence</span> for GCC
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45, duration: 0.6 }}
        className="text-body-lg text-slate-500 text-center mt-6 max-w-xl"
      >
        AI-powered simulation of financial and systemic shocks
        across the Gulf Cooperation Council
      </motion.p>

      {/* GCC Coverage + Sectors */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7, duration: 0.6 }}
        className="mt-16"
      >
        <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-400 text-center mb-5">
          6 Countries &middot; 43 Nodes &middot; 15 Scenarios
        </p>
        <div className="flex items-center gap-6">
          {SECTORS.map(({ icon: Icon, label }, i) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.85 + i * 0.08, duration: 0.4 }}
              className="flex flex-col items-center gap-2"
            >
              <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center">
                <Icon size={20} className="text-slate-500" />
              </div>
              <span className="text-[10px] font-medium text-slate-400">
                {label}
              </span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Bottom attribution */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4, duration: 0.5 }}
        className="absolute bottom-10 left-0 right-0 flex justify-center"
      >
        <p className="text-[11px] text-slate-300 tracking-wide">
          Impact Observatory &middot; Deevo Analytics
        </p>
      </motion.div>
    </div>
  );
}
