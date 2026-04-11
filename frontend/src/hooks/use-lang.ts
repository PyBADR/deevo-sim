"use client";

/**
 * useLang — Centralized language state hook for Impact Observatory.
 *
 * Provides locale state + the `t()` translator as a single import.
 * State is held in React context so the entire component tree re-renders
 * on language change.
 *
 * Usage (provider, typically in layout or page):
 *   import { LangProvider } from "@/hooks/use-lang";
 *   <LangProvider><App /></LangProvider>
 *
 * Usage (consumer):
 *   const { locale, setLocale, t, isAr, dir } = useLang();
 */

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  type ReactNode,
} from "react";
import { t as translate, type Locale } from "@/i18n/dictionary";

// ── Context shape ────────────────────────────────────────────────────

interface LangContextValue {
  /** Current locale */
  locale: Locale;
  /** Set locale directly */
  setLocale: (l: Locale) => void;
  /** Toggle between en ↔ ar */
  toggleLocale: () => void;
  /** Translation shorthand — uses current locale */
  t: (key: string) => string;
  /** Convenience: locale === "ar" */
  isAr: boolean;
  /** HTML dir attribute value */
  dir: "ltr" | "rtl";
}

const LangContext = createContext<LangContextValue | null>(null);

// ── Provider ─────────────────────────────────────────────────────────

interface LangProviderProps {
  children: ReactNode;
  /** Initial locale (defaults to "en") */
  defaultLocale?: Locale;
}

export function LangProvider({ children, defaultLocale = "en" }: LangProviderProps) {
  const [locale, setLocale] = useState<Locale>(defaultLocale);

  const toggleLocale = useCallback(() => {
    setLocale((prev) => (prev === "en" ? "ar" : "en"));
  }, []);

  const tFn = useCallback(
    (key: string) => translate(key, locale),
    [locale],
  );

  const value = useMemo<LangContextValue>(
    () => ({
      locale,
      setLocale,
      toggleLocale,
      t: tFn,
      isAr: locale === "ar",
      dir: locale === "ar" ? "rtl" : "ltr",
    }),
    [locale, toggleLocale, tFn],
  );

  return React.createElement(LangContext.Provider, { value }, children);
}

// ── Hook ─────────────────────────────────────────────────────────────

export function useLang(): LangContextValue {
  const ctx = useContext(LangContext);
  if (!ctx) {
    // Fallback for components rendered outside provider — safe default
    return {
      locale: "en",
      setLocale: () => {},
      toggleLocale: () => {},
      t: (key: string) => translate(key, "en"),
      isAr: false,
      dir: "ltr",
    };
  }
  return ctx;
}

export default useLang;
