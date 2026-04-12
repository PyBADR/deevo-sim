"use client";

/**
 * DemoOverlay — Full-screen demo experience
 *
 * Manages:
 * - Step state (current step, direction)
 * - Autoplay timer
 * - Keyboard navigation (ArrowRight/Left, Space, Escape)
 * - Right-side DemoController panel
 */

import React, { useState, useCallback, useEffect, useRef } from "react";
import { DemoController } from "./DemoController";
import { DemoStepRenderer, TOTAL_STEPS, STEP_DURATIONS } from "./DemoStepRenderer";
import { SourceStrip } from "./SourceStrip";

// Steps that get a micro-pause (extra 600ms) before advancing — lets the user absorb
const MICRO_PAUSE_AFTER: Set<number> = new Set([3, 7]); // Transmission, Outcome

interface DemoOverlayProps {
  onExit: () => void;
}

export function DemoOverlay({ onExit }: DemoOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Clear any existing timer
  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Advance to next step
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

  // Go to previous step
  const goBack = useCallback(() => {
    setDirection(-1);
    setCurrentStep((prev) => Math.max(0, prev - 1));
  }, []);

  // Play autoplay
  const play = useCallback(() => {
    setIsPlaying(true);
  }, []);

  // Pause autoplay
  const pause = useCallback(() => {
    setIsPlaying(false);
    clearTimer();
  }, [clearTimer]);

  // Restart from beginning
  const restart = useCallback(() => {
    clearTimer();
    setDirection(1);
    setCurrentStep(0);
    setIsPlaying(true);
  }, [clearTimer]);

  // Scroll reset on every step change
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [currentStep]);

  // Autoplay timer (with micro-pause support)
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

  return (
    <div className="fixed inset-0 z-50 bg-white overflow-hidden">
      {/* Main content area (leaves room for 260px controller) */}
      <div ref={contentRef} className="absolute inset-0 right-[260px] overflow-y-auto overflow-x-hidden scroll-smooth">
        <DemoStepRenderer currentStep={currentStep} direction={direction} onPause={pause} />
      </div>

      {/* Bottom credibility strip (skip on intro and trust steps) */}
      {currentStep > 0 && currentStep < TOTAL_STEPS - 1 && <SourceStrip />}

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
      />
    </div>
  );
}
