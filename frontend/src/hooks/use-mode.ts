"use client";

/**
 * useMode — Executive / Analyst / Decision mode system.
 *
 * Controls progressive disclosure across the Decision Command Center.
 * Each mode defines what is visible, how deep the detail goes, and which
 * interactions are available.
 *
 * Mode definitions:
 *   Executive  — 5-second comprehension. KPIs + headline + single action.
 *   Analyst    — Full detail.  All cards, sector tabs, propagation chain.
 *   Decision   — Action-focused.  Decision cards + transparency overlay
 *                in focus, everything else muted.
 *
 * Usage:
 *   const { mode, setMode, visibility } = useMode();
 *   {visibility.showSectorStress && <SectorStressV2 ... />}
 */

import React, {
  createContext,
  useContext,
  useState,
  useMemo,
  type ReactNode,
} from "react";

// ── Types ────────────────────────────────────────────────────────────

export type AppMode = "executive" | "analyst" | "decision";

export interface ModeVisibility {
  /** Executive Brief / KPI row — always visible */
  showBrief: boolean;
  /** Macro context panel */
  showMacro: boolean;
  /** Explainability panel */
  showExplainability: boolean;
  /** Decision cards (top 3) */
  showDecisionCards: boolean;
  /** Sector stress tabs */
  showSectorStress: boolean;
  /** Propagation chain / map view */
  showPropagation: boolean;
  /** Transparency overlays on decision cards */
  showTransparency: boolean;
  /** Loss-inducing warning banner */
  showLossWarning: boolean;
  /** Default depth level for DepthToggle */
  defaultDepth: 1 | 2 | 3;
  /** Decision cards visually emphasized */
  decisionFocus: boolean;
}

// ── Mode → Visibility map ────────────────────────────────────────────

const VISIBILITY: Record<AppMode, ModeVisibility> = {
  executive: {
    showBrief:          true,
    showMacro:          true,
    showExplainability: false,
    showDecisionCards:  true,
    showSectorStress:   false,
    showPropagation:    false,
    showTransparency:   false,
    showLossWarning:    true,
    defaultDepth:       1,
    decisionFocus:      false,
  },
  analyst: {
    showBrief:          true,
    showMacro:          true,
    showExplainability: true,
    showDecisionCards:  true,
    showSectorStress:   true,
    showPropagation:    true,
    showTransparency:   true,
    showLossWarning:    true,
    defaultDepth:       3,
    decisionFocus:      false,
  },
  decision: {
    showBrief:          true,
    showMacro:          false,
    showExplainability: true,
    showDecisionCards:  true,
    showSectorStress:   false,
    showPropagation:    false,
    showTransparency:   true,
    showLossWarning:    true,
    defaultDepth:       2,
    decisionFocus:      true,
  },
};

// ── Context ──────────────────────────────────────────────────────────

interface ModeContextValue {
  mode: AppMode;
  setMode: (m: AppMode) => void;
  visibility: ModeVisibility;
}

const ModeContext = createContext<ModeContextValue | null>(null);

// ── Provider ─────────────────────────────────────────────────────────

interface ModeProviderProps {
  children: ReactNode;
  defaultMode?: AppMode;
}

export function ModeProvider({ children, defaultMode = "analyst" }: ModeProviderProps) {
  const [mode, setMode] = useState<AppMode>(defaultMode);

  const value = useMemo<ModeContextValue>(
    () => ({
      mode,
      setMode,
      visibility: VISIBILITY[mode],
    }),
    [mode],
  );

  return React.createElement(ModeContext.Provider, { value }, children);
}

// ── Hook ─────────────────────────────────────────────────────────────

export function useMode(): ModeContextValue {
  const ctx = useContext(ModeContext);
  if (!ctx) {
    // Fallback: analyst mode if used outside provider
    return {
      mode: "analyst",
      setMode: () => {},
      visibility: VISIBILITY.analyst,
    };
  }
  return ctx;
}

export default useMode;
