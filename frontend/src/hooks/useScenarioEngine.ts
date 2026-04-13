/**
 * Impact Observatory | مرصد الأثر — Scenario Engine Hook
 *
 * Manages the simulation lifecycle: activate → auto-tick → resolve.
 *
 * Provides:
 *   run(id, name, horizonHours)  — start scenario
 *   advance()                    — manual single tick
 *   stop()                       — reset to idle
 *
 * Exposes the intelligence snapshot alongside the simulation snapshot,
 * allowing any component to read country, sector, entity, signal,
 * decision, and monitoring state from a single hook.
 *
 * Deterministic — no randomness, no backend dependency.
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useSystemState } from '@/lib/systemState';

const TICK_INTERVAL_MS = 1500;

export function useScenarioEngine() {
  const {
    activeScenarioId,
    activeScenarioName,
    status,
    snapshot,
    intelligence,
    activateScenario,
    tick,
    reset,
  } = useSystemState();

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-tick while running or escalating
  useEffect(() => {
    if (status === 'running' || status === 'escalating') {
      intervalRef.current = setInterval(() => {
        tick();
      }, TICK_INTERVAL_MS);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [status, tick]);

  const run = useCallback(
    (id: string, name: string, horizonHours: number) => {
      activateScenario(id, name, horizonHours);
    },
    [activateScenario],
  );

  const advance = useCallback(() => {
    tick();
  }, [tick]);

  const stop = useCallback(() => {
    reset();
  }, [reset]);

  return {
    // Existing API (unchanged)
    scenarioId: activeScenarioId,
    scenarioName: activeScenarioName,
    status,
    snapshot,
    isActive: status !== 'idle',
    isRunning: status === 'running' || status === 'escalating',
    isResolved: status === 'resolved',
    run,
    advance,
    stop,

    // Intelligence core (new)
    intelligence,
  };
}
