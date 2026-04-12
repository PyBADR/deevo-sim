"use client";

/**
 * DemoStepRenderer — V4.0 (Macro Financial Intelligence)
 *
 * Routes step index to the correct layer component.
 * 9 layers: Signal → Transmission → Exposure → Banking → Insurance →
 *           Sector Stress → Decision Engine → Outcome → Trust
 */

import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { DemoRole, ScenarioId } from "./data/demo-scenario";
import type { SimSnapshot } from "./engine/demo-sim";

import { MacroRegimeStep } from "./steps/MacroRegimeStep";
import { PropagationStep } from "./steps/PropagationStep";
import { GCCExposureStep } from "./steps/GCCExposureStep";
import { BankingLayerStep } from "./steps/BankingLayerStep";
import { InsuranceLayerStep } from "./steps/InsuranceLayerStep";
import { SectorStressStep } from "./steps/SectorStressStep";
import { DecisionEngineStep } from "./steps/DecisionEngineStep";
import { OutcomeStepV3 } from "./steps/OutcomeStepV3";
import { TrustStepV3 } from "./steps/TrustStepV3";

export interface DemoStepProps {
  onPause?: () => void;
  activeRole?: DemoRole;
  sim?: SimSnapshot;
  onToggleDecision?: (index: number) => void;
  scenarioId: ScenarioId;
}

const STEPS: React.ComponentType<DemoStepProps>[] = [
  MacroRegimeStep,    // 0 — Macro State
  PropagationStep,    // 1 — Transmission (stress path)
  GCCExposureStep,    // 2 — Country Exposure
  BankingLayerStep,   // 3 — Banking Layer
  InsuranceLayerStep, // 4 — Insurance Layer
  SectorStressStep,   // 5 — Sector Impact
  DecisionEngineStep, // 6 — Decision Room
  OutcomeStepV3,      // 7 — Outcome
  TrustStepV3,        // 8 — Trust
];

export const TOTAL_STEPS = STEPS.length;

/** Duration each layer stays visible during autoplay (ms) */
export const STEP_DURATIONS = [
  4000,  // 0 Macro State
  8000,  // 1 Propagation (primary — needs time for cascade)
  5500,  // 2 Country Exposure
  5000,  // 3 Banking Layer
  5000,  // 4 Insurance Layer
  6000,  // 5 Sector Impact
  7500,  // 6 Decision Room (interactive — longer)
  5800,  // 7 Outcome
  4000,  // 8 Trust
];

interface DemoStepRendererProps {
  currentStep: number;
  direction: number;
  onPause?: () => void;
  activeRole?: DemoRole;
  sim?: SimSnapshot;
  onToggleDecision?: (index: number) => void;
  scenarioId: ScenarioId;
}

export function DemoStepRenderer({
  currentStep,
  direction,
  onPause,
  activeRole,
  sim,
  onToggleDecision,
  scenarioId,
}: DemoStepRendererProps) {
  const StepComponent = STEPS[currentStep];
  if (!StepComponent) return null;

  return (
    <AnimatePresence mode="wait" custom={direction}>
      <motion.div
        key={`${scenarioId}-${currentStep}`}
        custom={direction}
        initial={{ opacity: 0, x: direction > 0 ? 60 : -60 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: direction > 0 ? -60 : 60 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        className="w-full h-full will-change-transform"
      >
        <StepComponent
          onPause={onPause}
          activeRole={activeRole}
          sim={sim}
          onToggleDecision={onToggleDecision}
          scenarioId={scenarioId}
        />
      </motion.div>
    </AnimatePresence>
  );
}
