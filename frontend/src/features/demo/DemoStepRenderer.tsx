"use client";

/**
 * DemoStepRenderer — Routes current step index to the correct screen component.
 * Wraps each step in AnimatePresence for smooth transitions.
 */

import React from "react";
import { AnimatePresence, motion } from "framer-motion";

import { IntroStep } from "./steps/IntroStep";
import { ScenarioStep } from "./steps/ScenarioStep";
import { ShockStep } from "./steps/ShockStep";
import { TransmissionStep } from "./steps/TransmissionStep";
import { GCCImpactStep } from "./steps/GCCImpactStep";
import { SectorImpactStep } from "./steps/SectorImpactStep";
import { DecisionStep } from "./steps/DecisionStep";
import { OutcomeStep } from "./steps/OutcomeStep";
import { TrustStep } from "./steps/TrustStep";

export interface DemoStepProps {
  onPause?: () => void;
}

const STEPS: React.ComponentType<DemoStepProps>[] = [
  IntroStep,
  ScenarioStep,
  ShockStep,
  TransmissionStep,
  GCCImpactStep,
  SectorImpactStep,
  DecisionStep,
  OutcomeStep,
  TrustStep,
];

export const TOTAL_STEPS = STEPS.length;

// Duration each step stays visible during autoplay (ms)
// Tuned for ~52s total — executive-grade pacing, no step feels rushed
export const STEP_DURATIONS = [
  3200,  // 0 Intro — brief, sets context
  4500,  // 1 Scenario — absorb 4 metrics + WHY
  4000,  // 2 Shock — 3 KPIs, fast read
  8000,  // 3 Transmission — 5-node cascade + micro-pause after
  5500,  // 4 GCC Impact — 6 country cards, scan + absorb
  7000,  // 5 Sector Impact — 6 sectors, needs reading time
  5500,  // 6 Decision — 5 actions (may pause on interaction)
  5800,  // 7 Outcome — the money shot + count-up + micro-pause after
  4000,  // 8 Trust — closing authority, footer
];

interface DemoStepRendererProps {
  currentStep: number;
  direction: number; // 1 = forward, -1 = backward
  onPause?: () => void;
}

export function DemoStepRenderer({ currentStep, direction, onPause }: DemoStepRendererProps) {
  const StepComponent = STEPS[currentStep];
  if (!StepComponent) return null;

  return (
    <AnimatePresence mode="wait" custom={direction}>
      <motion.div
        key={currentStep}
        custom={direction}
        initial={{ opacity: 0, x: direction > 0 ? 60 : -60 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: direction > 0 ? -60 : 60 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        className="w-full h-full will-change-transform"
      >
        <StepComponent onPause={onPause} />
      </motion.div>
    </AnimatePresence>
  );
}
