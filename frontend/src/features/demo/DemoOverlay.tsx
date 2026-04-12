"use client";

/**
 * DemoOverlay — V4.0 (Macro Financial Intelligence)
 *
 * Full-screen demo experience. Manages:
 * - Scenario selection (Hormuz / Financial Flow)
 * - Step state, direction, autoplay timer with micro-pause
 * - Keyboard navigation
 * - Right-side DemoController
 * - Role switcher bar (visible on layers 1-7)
 * - Simulation state via useDemoSim
 */

import React, { useState, useCallback, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { DemoController } from "./DemoController";
import { DemoStepRenderer, TOTAL_STEPS, STEP_DURATIONS } from "./DemoStepRenderer";
import { SourceStrip } from "./SourceStrip";
import { DEMO_ROLES, DEFAULT_SCENARIO_ID, type DemoRole, type ScenarioId } from "./data/demo-scenario";
import { useDemoSim } from "./engine/demo-sim";

const MICRO_PAUSE_AFTER: Set<number> = new Set([1, 7]);

interface DemoOverlayProps {
  onExit: () => void;
}

export function DemoOverlay({ onExit }: DemoOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true);
  const [activeRole, setActiveRole] = useState<DemoRole>("ceo");
  const [scenarioId, setScenarioId] = useState<ScenarioId>(DEFAULT_SCENARIO_ID);
  const { snapshot: sim, toggleDecision, resetSim } = useDemoSim();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const goNext = useCallback(() => {
    setDirection(1);
    setCurrentStep((prev) => {
      if (prev >= TOTAL_STEPS - 1) {
        setIsPlaying(false);
        return prev;
      }
      return prev + 1;
    });
  }, []);

  const goBack = useCallback(() => {
    setDirection(-1);
    setCurrentStep((prev) => Math.max(0, prev - 1));
  }, []);

  const play = useCallback(() => {
    setIsPlaying(true);
  }, []);

  const pause = useCallback(() => {
    setIsPlaying(false);
    clearTimer();
  }, [clearTimer]);

  const restart = useCallback(() => {
    clearTimer();
    setDirection(1);
    setCurrentStep(0);
    setIsPlaying(true);
    resetSim();
  }, [clearTimer, resetSim]);

  const switchScenario = useCallback((id: ScenarioId) => {
    clearTimer();
    setScenarioId(id);
    setDirection(1);
    setCurrentStep(0);
    setIsPlaying(true);
    resetSim();
  }, [clearTimer, resetSim]);

  // Scroll reset on step change
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [currentStep]);

  // Autoplay timer
  useEffect(() => {
    clearTimer();
    if (isPlaying && currentStep < TOTAL_STEPS - 1) {
      const baseDuration = STEP_DURATIONS[currentStep] ?? 5000;
      const microPause = MICRO_PAUSE_AFTER.has(currentStep) ? 600 : 0;
      timerRef.current = setTimeout(goNext, baseDuration + microPause);
    } else if (currentStep >= TOTAL_STEPS - 1) {
      setIsPlaying(false);
    }
    return clearTimer;
  }, [isPlaying, currentStep, goNext, clearTimer]);

  // Keyboard navigation
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      switch (e.key) {
        case "ArrowRight":
        case "ArrowDown":
          e.preventDefault();
          pause();
          goNext();
          break;
        case "ArrowLeft":
        case "ArrowUp":
          e.preventDefault();
          pause();
          goBack();
          break;
        case " ":
          e.preventDefault();
          if (isPlaying) pause();
          else play();
          break;
        case "Escape":
          e.preventDefault();
          onExit();
          break;
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isPlaying, pause, play, goNext, goBack, onExit]);

  const showRoleBar = currentStep > 0 && currentStep < TOTAL_STEPS - 1;

  return (
    <div className="fixed inset-0 z-50 bg-[#FAFAFA] overflow-hidden">
      {/* Role Switcher Bar */}
      {showRoleBar && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="absolute top-0 left-0 right-[260px] z-[56] bg-white/90 backdrop-blur-sm border-b border-slate-100"
        >
          <div className="flex items-center justify-center gap-1 px-4 py-2">
            <span className="text-[9px] font-semibold text-slate-300 uppercase tracking-[0.15em] mr-3">
              Viewing as
            </span>
            {DEMO_ROLES.map((role) => (
              <button
                key={role.id}
                onClick={() => setActiveRole(role.id)}
                className={`px-3 py-1.5 rounded-lg text-[10px] font-semibold transition-all duration-200 ${
                  activeRole === role.id
                    ? "bg-slate-900 text-white"
                    : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                }`}
              >
                {role.label}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Main content */}
      <div
        ref={contentRef}
        className="absolute inset-0 right-[260px] overflow-y-auto overflow-x-hidden scroll-smooth"
        style={{ paddingTop: showRoleBar ? 44 : 0 }}
      >
        <DemoStepRenderer
          currentStep={currentStep}
          direction={direction}
          onPause={pause}
          activeRole={activeRole}
          sim={sim}
          onToggleDecision={toggleDecision}
          scenarioId={scenarioId}
        />
      </div>

      {/* Bottom credibility strip */}
      {currentStep > 0 && currentStep < TOTAL_STEPS - 1 && (
        <SourceStrip scenarioId={scenarioId} />
      )}

      {/* Right-side controller */}
      <DemoController
        currentStep={currentStep}
        totalSteps={TOTAL_STEPS}
        isPlaying={isPlaying}
        onPlay={play}
        onPause={pause}
        onNext={goNext}
        onBack={goBack}
        onExit={onExit}
        onRestart={restart}
        scenarioId={scenarioId}
        onSwitchScenario={switchScenario}
      />
    </div>
  );
}
