/* =================================================
   Deevo Sim v2 — Internationalization System
   Bilingual Arabic + English Support
   ================================================= */

import type { BilingualText } from './types'

export type Language = 'en' | 'ar'

// ── Language State ──────────────────────────────

let currentLanguage: Language = 'en'

export function setLanguage(lang: Language) {
  currentLanguage = lang
  if (typeof document !== 'undefined') {
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
    document.documentElement.lang = lang
  }
}

export function getLanguage(): Language {
  return currentLanguage
}

// ── Text Resolution ─────────────────────────────

export function t(text: BilingualText | undefined, fallback = ''): string {
  if (!text) return fallback
  return currentLanguage === 'ar' ? text.ar : text.en
}

export function tField(en: string | undefined, ar: string | undefined): string {
  if (currentLanguage === 'ar' && ar) return ar
  return en || ''
}

// ── Direction Utilities ─────────────────────────

export function isRTL(): boolean {
  return currentLanguage === 'ar'
}

export function dirClass(): string {
  return currentLanguage === 'ar' ? 'rtl' : 'ltr'
}

export function textAlignClass(): string {
  return currentLanguage === 'ar' ? 'text-right' : 'text-left'
}

// ── Static Labels ───────────────────────────────

export const labels: Record<string, BilingualText> = {
  controlRoom: { en: 'Control Room', ar: '\u063A\u0631\u0641\u0629 \u0627\u0644\u0642\u064A\u0627\u062F\u0629' },
  scenarioInput: { en: 'Scenario Input', ar: '\u0625\u062F\u062E\u0627\u0644 \u0627\u0644\u0633\u064A\u0646\u0627\u0631\u064A\u0648' },
  runSimulation: { en: 'Run Simulation', ar: '\u062A\u0634\u063A\u064A\u0644 \u0627\u0644\u0645\u062D\u0627\u0643\u0627\u0629' },
  decisionOutput: { en: 'Decision Output', ar: '\u0645\u062E\u0631\u062C\u0627\u062A \u0627\u0644\u0642\u0631\u0627\u0631' },
  intelligenceBrief: { en: 'Intelligence Brief', ar: '\u0645\u0644\u062E\u0635 \u0627\u0633\u062A\u062E\u0628\u0627\u0631\u0627\u062A\u064A' },
  scenarioLibrary: { en: 'Scenario Library', ar: '\u0645\u0643\u062A\u0628\u0629 \u0627\u0644\u0633\u064A\u0646\u0627\u0631\u064A\u0648\u0647\u0627\u062A' },
  analyst: { en: 'Analyst', ar: '\u0627\u0644\u0645\u062D\u0644\u0644' },
  risk: { en: 'Risk', ar: '\u0627\u0644\u0645\u062E\u0627\u0637\u0631' },
  spread: { en: 'Spread', ar: '\u0627\u0644\u0627\u0646\u062A\u0634\u0627\u0631' },
  sentiment: { en: 'Sentiment', ar: '\u0627\u0644\u0645\u0634\u0627\u0639\u0631' },
  presets: { en: 'Presets', ar: '\u0642\u0648\u0627\u0644\u0628 \u062C\u0627\u0647\u0632\u0629' },
  ready: { en: 'READY', ar: '\u062C\u0627\u0647\u0632' },
  simulating: { en: 'SIMULATING', ar: '\u062C\u0627\u0631\u064A \u0627\u0644\u0645\u062D\u0627\u0643\u0627\u0629' },
  complete: { en: 'COMPLETE', ar: '\u0645\u0643\u062A\u0645\u0644' },
  region: { en: 'Region', ar: '\u0627\u0644\u0645\u0646\u0637\u0642\u0629' },
  domain: { en: 'Domain', ar: '\u0627\u0644\u0645\u062C\u0627\u0644' },
  trigger: { en: 'Trigger', ar: '\u0627\u0644\u0645\u062D\u0641\u0632' },
  actors: { en: 'Actors', ar: '\u0627\u0644\u0623\u0637\u0631\u0627\u0641' },
  signals: { en: 'Signals', ar: '\u0627\u0644\u0625\u0634\u0627\u0631\u0627\u062A' },
  businessImpact: { en: 'Business Impact', ar: '\u0627\u0644\u062A\u0623\u062B\u064A\u0631 \u0627\u0644\u062A\u062C\u0627\u0631\u064A' },
  financialImpact: { en: 'Financial Impact', ar: '\u0627\u0644\u062A\u0623\u062B\u064A\u0631 \u0627\u0644\u0645\u0627\u0644\u064A' },
  customerImpact: { en: 'Customer Impact', ar: '\u062A\u0623\u062B\u064A\u0631 \u0627\u0644\u0639\u0645\u0644\u0627\u0621' },
  regulatoryRisk: { en: 'Regulatory Risk', ar: '\u0627\u0644\u0645\u062E\u0627\u0637\u0631 \u0627\u0644\u062A\u0646\u0638\u064A\u0645\u064A\u0629' },
  reputationDamage: { en: 'Reputation', ar: '\u0627\u0644\u0633\u0645\u0639\u0629' },
}

// ── Domain Labels ───────────────────────────────

export const domainLabels: Record<string, BilingualText> = {
  energy: { en: 'Energy', ar: '\u0627\u0644\u0637\u0627\u0642\u0629' },
  telecom: { en: 'Telecom', ar: '\u0627\u0644\u0627\u062A\u0635\u0627\u0644\u0627\u062A' },
  banking: { en: 'Banking', ar: '\u0627\u0644\u0628\u0646\u0648\u0643' },
  insurance: { en: 'Insurance', ar: '\u0627\u0644\u062A\u0623\u0645\u064A\u0646' },
  policy: { en: 'Policy', ar: '\u0627\u0644\u0633\u064A\u0627\u0633\u0627\u062A' },
  brand: { en: 'Brand / Media', ar: '\u0627\u0644\u0639\u0644\u0627\u0645\u0629 \u0627\u0644\u062A\u062C\u0627\u0631\u064A\u0629' },
  'supply-chain': { en: 'Supply Chain', ar: '\u0633\u0644\u0633\u0644\u0629 \u0627\u0644\u0625\u0645\u062F\u0627\u062F' },
  security: { en: 'Cyber Security', ar: '\u0627\u0644\u0623\u0645\u0646 \u0627\u0644\u0633\u064A\u0628\u0631\u0627\u0646\u064A' },
}

export const regionLabels: Record<string, BilingualText> = {
  gcc: { en: 'GCC', ar: '\u062F\u0648\u0644 \u0627\u0644\u062E\u0644\u064A\u062C' },
  saudi: { en: 'Saudi Arabia', ar: '\u0627\u0644\u0633\u0639\u0648\u062F\u064A\u0629' },
  kuwait: { en: 'Kuwait', ar: '\u0627\u0644\u0643\u0648\u064A\u062A' },
  uae: { en: 'UAE', ar: '\u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062A' },
  qatar: { en: 'Qatar', ar: '\u0642\u0637\u0631' },
  bahrain: { en: 'Bahrain', ar: '\u0627\u0644\u0628\u062D\u0631\u064A\u0646' },
  oman: { en: 'Oman', ar: '\u0639\u0645\u0627\u0646' },
}

export const triggerLabels: Record<string, BilingualText> = {
  'price-change': { en: 'Price Change', ar: '\u062A\u063A\u064A\u064A\u0631 \u0623\u0633\u0639\u0627\u0631' },
  leak: { en: 'Leak', ar: '\u062A\u0633\u0631\u064A\u0628' },
  announcement: { en: 'Announcement', ar: '\u0625\u0639\u0644\u0627\u0646' },
  rumor: { en: 'Rumor', ar: '\u0625\u0634\u0627\u0639\u0629' },
  incident: { en: 'Incident', ar: '\u062D\u0627\u062F\u062B\u0629' },
  regulatory: { en: 'Regulatory Action', ar: '\u0625\u062C\u0631\u0627\u0621 \u062A\u0646\u0638\u064A\u0645\u064A' },
  cyberattack: { en: 'Cyber Attack', ar: '\u0647\u062C\u0648\u0645 \u0633\u064A\u0628\u0631\u0627\u0646\u064A' },
  fraud: { en: 'Fraud Detection', ar: '\u0643\u0634\u0641 \u0627\u062D\u062A\u064A\u0627\u0644' },
      }
