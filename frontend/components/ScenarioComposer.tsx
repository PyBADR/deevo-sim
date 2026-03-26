'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Globe, Zap, Users, Radio, AlertTriangle, Shield,
  ChevronDown, ChevronUp, Plus, X, Play
} from 'lucide-react'
import { t, tField, label, domainLabel, regionLabel, triggerLabel, isRTL, dirClass } from '@/lib/i18n'
import type { BilingualText, ScenarioDomain, ScenarioRegion, TriggerType, SignalType } from '@/lib/types'

interface ComposerScenario {
  title: BilingualText
  description: BilingualText
  domain: ScenarioDomain
  region: ScenarioRegion
  trigger: TriggerType
  actors: string[]
  signals: { type: SignalType; source: string; content: string }[]
  constraints: string[]
  strategy: string
}

const DOMAINS: ScenarioDomain[] = ['energy', 'telecom', 'banking', 'insurance', 'policy', 'brand', 'supply-chain', 'security']
const REGIONS: ScenarioRegion[] = ['saudi', 'uae', 'kuwait', 'bahrain', 'qatar', 'oman', 'gcc-wide']
const TRIGGERS: TriggerType[] = ['price-change', 'regulation', 'social-media', 'competitor', 'geopolitical', 'natural-disaster', 'cyber-attack', 'market-shift']
const SIGNAL_TYPES: SignalType[] = ['social', 'news', 'regulatory', 'market', 'internal', 'geopolitical']

const domainIcons: Record<string, React.ReactNode> = {
  energy: <Zap className="w-4 h-4" />,
  telecom: <Radio className="w-4 h-4" />,
  banking: <Globe className="w-4 h-4" />,
  insurance: <Shield className="w-4 h-4" />,
  policy: <AlertTriangle className="w-4 h-4" />,
  brand: <Users className="w-4 h-4" />,
  'supply-chain': <Globe className="w-4 h-4" />,
  security: <Shield className="w-4 h-4" />,
}

interface ScenarioComposerProps {
  onLaunch?: (scenario: ComposerScenario) => void
  collapsed?: boolean
}

export default function ScenarioComposer({ onLaunch, collapsed = false }: ScenarioComposerProps) {
  const [isExpanded, setIsExpanded] = useState(!collapsed)
  const [activeSection, setActiveSection] = useState<'basic' | 'actors' | 'signals' | 'constraints'>('basic')

  const [title, setTitle] = useState<BilingualText>({ en: '', ar: '' })
  const [description, setDescription] = useState<BilingualText>({ en: '', ar: '' })
  const [domain, setDomain] = useState<ScenarioDomain>('energy')
  const [region, setRegion] = useState<ScenarioRegion>('saudi')
  const [trigger, setTrigger] = useState<TriggerType>('price-change')
  const [actors, setActors] = useState<string[]>([])
  const [actorInput, setActorInput] = useState('')
  const [signals, setSignals] = useState<{ type: SignalType; source: string; content: string }[]>([])
  const [constraints, setConstraints] = useState<string[]>([])
  const [constraintInput, setConstraintInput] = useState('')
  const [strategy, setStrategy] = useState('')

  const addActor = () => {
    if (actorInput.trim()) {
      setActors([...actors, actorInput.trim()])
      setActorInput('')
    }
  }

  const removeActor = (index: number) => {
    setActors(actors.filter((_, i) => i !== index))
  }

  const addSignal = () => {
    setSignals([...signals, { type: 'social', source: '', content: '' }])
  }

  const updateSignal = (index: number, field: string, value: string) => {
    const updated = [...signals]
    updated[index] = { ...updated[index], [field]: value }
    setSignals(updated)
  }

  const removeSignal = (index: number) => {
    setSignals(signals.filter((_, i) => i !== index))
  }

  const addConstraint = () => {
    if (constraintInput.trim()) {
      setConstraints([...constraints, constraintInput.trim()])
      setConstraintInput('')
    }
  }

  const removeConstraint = (index: number) => {
    setConstraints(constraints.filter((_, i) => i !== index))
  }

  const handleLaunch = () => {
    const scenario: ComposerScenario = {
      title,
      description,
      domain,
      region,
      trigger,
      actors,
      signals,
      constraints,
      strategy,
    }
    onLaunch?.(scenario)
  }

  const isValid = title.en.trim() !== '' && description.en.trim() !== ''

  const sections = [
    { id: 'basic' as const, label: 'Scenario Definition' },
    { id: 'actors' as const, label: 'Actors & Entities' },
    { id: 'signals' as const, label: 'Signals & Intelligence' },
    { id: 'constraints' as const, label: 'Constraints & Strategy' },
  ]

  return (
    <div className={`border border-zinc-800 rounded-lg bg-zinc-950/80 backdrop-blur overflow-hidden ${dirClass()}`}>
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-zinc-900/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
          <span className="text-xs font-mono uppercase tracking-widest text-zinc-400">
            {label('scenarioInput')}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-zinc-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-zinc-500" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Section Tabs */}
            <div className="flex border-b border-zinc-800">
              {sections.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveSection(s.id)}
                  className={`flex-1 px-3 py-2 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                    activeSection === s.id
                      ? 'text-indigo-400 border-b-2 border-indigo-500 bg-indigo-500/5'
                      : 'text-zinc-600 hover:text-zinc-400'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            <div className="p-4 space-y-4">
              {/* Basic Section */}
              {activeSection === 'basic' && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="space-y-3"
                >
                  {/* Title EN/AR */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] font-mono text-zinc-500 mb-1">TITLE (EN)</label>
                      <input
                        type="text"
                        value={title.en}
                        onChange={(e) => setTitle({ ...title, en: e.target.value })}
                        placeholder="Fuel Price Surge in Saudi Arabia"
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 placeholder-zinc-700 focus:border-indigo-500 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-mono text-zinc-500 mb-1">TITLE (AR)</label>
                      <input
                        type="text"
                        value={title.ar}
                        onChange={(e) => setTitle({ ...title, ar: e.target.value })}
                        placeholder="ارتفاع أسعار الوقود في السعودية"
                        dir="rtl"
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 placeholder-zinc-700 focus:border-indigo-500 focus:outline-none text-right"
                      />
                    </div>
                  </div>

                  {/* Description */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] font-mono text-zinc-500 mb-1">DESCRIPTION (EN)</label>
                      <textarea
                        value={description.en}
                        onChange={(e) => setDescription({ ...description, en: e.target.value })}
                        placeholder="Describe the scenario..."
                        rows={3}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 placeholder-zinc-700 focus:border-indigo-500 focus:outline-none resize-none"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-mono text-zinc-500 mb-1">DESCRIPTION (AR)</label>
                      <textarea
                        value={description.ar}
                        onChange={(e) => setDescription({ ...description, ar: e.target.value })}
                        placeholder="وصف السيناريو..."
                        dir="rtl"
                        rows={3}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 placeholder-zinc-700 focus:border-indigo-500 focus:outline-none resize-none text-right"
                      />
                    </div>
                  </div>

                  {/* Domain / Region / Trigger */}
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-[10px] font-mono text-zinc-500 mb-1">{label('domain').toUpperCase()}</label>
                      <select
                        value={domain}
                        onChange={(e) => setDomain(e.target.value as ScenarioDomain)}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 focus:border-indigo-500 focus:outline-none"
                      >
                        {DOMAINS.map((d) => (
                          <option key={d} value={d}>{domainLabel(d)}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-mono text-zinc-500 mb-1">{label('region').toUpperCase()}</label>
                      <select
                        value={region}
                        onChange={(e) => setRegion(e.target.value as ScenarioRegion)}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 focus:border-indigo-500 focus:outline-none"
                      >
                        {REGIONS.map((r) => (
                          <option key={r} value={r}>{regionLabel(r)}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-mono text-zinc-500 mb-1">{label('trigger').toUpperCase()}</label>
                      <select
                        value={trigger}
                        onChange={(e) => setTrigger(e.target.value as TriggerType)}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 focus:border-indigo-500 focus:outline-none"
                      >
                        {TRIGGERS.map((tr) => (
                          <option key={tr} value={tr}>{triggerLabel(tr)}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Actors Section */}
              {activeSection === 'actors' && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="space-y-3"
                >
                  <label className="block text-[10px] font-mono text-zinc-500 mb-1">{label('actors').toUpperCase()}</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={actorInput}
                      onChange={(e) => setActorInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addActor()}
                      placeholder="Add actor (e.g., Saudi Aramco, SAMA)"
                      className="flex-1 bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 placeholder-zinc-700 focus:border-indigo-500 focus:outline-none"
                    />
                    <button
                      onClick={addActor}
                      className="px-3 py-2 bg-indigo-600/20 border border-indigo-500/30 rounded text-indigo-400 hover:bg-indigo-600/30 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {actors.map((actor, i) => (
                      <span
                        key={i}
                        className="flex items-center gap-1 px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-300"
                      >
                        {actor}
                        <button onClick={() => removeActor(i)} className="text-zinc-600 hover:text-red-400">
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                    {actors.length === 0 && (
                      <p className="text-xs text-zinc-600">No actors added yet</p>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Signals Section */}
              {activeSection === 'signals' && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <label className="text-[10px] font-mono text-zinc-500">{label('signals').toUpperCase()}</label>
                    <button
                      onClick={addSignal}
                      className="flex items-center gap-1 px-2 py-1 text-[10px] bg-indigo-600/20 border border-indigo-500/30 rounded text-indigo-400 hover:bg-indigo-600/30 transition-colors"
                    >
                      <Plus className="w-3 h-3" /> ADD SIGNAL
                    </button>
                  </div>
                  {signals.map((signal, i) => (
                    <div key={i} className="grid grid-cols-[120px_1fr_1fr_auto] gap-2 items-start">
                      <select
                        value={signal.type}
                        onChange={(e) => updateSignal(i, 'type', e.target.value)}
                        className="bg-zinc-900 border border-zinc-800 rounded px-2 py-1.5 text-xs text-zinc-300 focus:border-indigo-500 focus:outline-none"
                      >
                        {SIGNAL_TYPES.map((st) => (
                          <option key={st} value={st}>{st}</option>
                        ))}
                      </select>
                      <input
                        type="text"
                        value={signal.source}
                        onChange={(e) => updateSignal(i, 'source', e.target.value)}
                        placeholder="Source"
                        className="bg-zinc-900 border border-zinc-800 rounded px-2 py-1.5 text-xs text-zinc-300 placeholder-zinc-700 focus:border-indigo-500 focus:outline-none"
                      />
                      <input
                        type="text"
                        value={signal.content}
                        onChange={(e) => updateSignal(i, 'content', e.target.value)}
                        placeholder="Content / description"
                        className="bg-zinc-900 border border-zinc-800 rounded px-2 py-1.5 text-xs text-zinc-300 placeholder-zinc-700 focus:border-indigo-500 focus:outline-none"
                      />
                      <button onClick={() => removeSignal(i)} className="text-zinc-600 hover:text-red-400 pt-1">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  {signals.length === 0 && (
                    <p className="text-xs text-zinc-600">No signals added yet</p>
                  )}
                </motion.div>
              )}

              {/* Constraints Section */}
              {activeSection === 'constraints' && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="space-y-3"
                >
                  <label className="block text-[10px] font-mono text-zinc-500 mb-1">CONSTRAINTS</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={constraintInput}
                      onChange={(e) => setConstraintInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addConstraint()}
                      placeholder="Add constraint (e.g., No official response yet)"
                      className="flex-1 bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 placeholder-zinc-700 focus:border-indigo-500 focus:outline-none"
                    />
                    <button
                      onClick={addConstraint}
                      className="px-3 py-2 bg-indigo-600/20 border border-indigo-500/30 rounded text-indigo-400 hover:bg-indigo-600/30 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {constraints.map((c, i) => (
                      <span
                        key={i}
                        className="flex items-center gap-1 px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-300"
                      >
                        {c}
                        <button onClick={() => removeConstraint(i)} className="text-zinc-600 hover:text-red-400">
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>

                  <div className="pt-2">
                    <label className="block text-[10px] font-mono text-zinc-500 mb-1">ANNOUNCEMENT STRATEGY</label>
                    <select
                      value={strategy}
                      onChange={(e) => setStrategy(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 focus:border-indigo-500 focus:outline-none"
                    >
                      <option value="">Select strategy...</option>
                      <option value="pre-announce">Pre-announce</option>
                      <option value="stealth">Stealth</option>
                      <option value="coordinated-leak">Coordinated Leak</option>
                      <option value="crisis-response">Crisis Response</option>
                      <option value="phased-rollout">Phased Rollout</option>
                    </select>
                  </div>
                </motion.div>
              )}

              {/* Launch Button */}
              <div className="pt-2 border-t border-zinc-800">
                <button
                  onClick={handleLaunch}
                  disabled={!isValid}
                  className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded font-mono text-xs uppercase tracking-wider transition-all ${
                    isValid
                      ? 'bg-indigo-600 hover:bg-indigo-500 text-white'
                      : 'bg-zinc-800 text-zinc-600 cursor-not-allowed'
                  }`}
                >
                  <Play className="w-4 h-4" />
                  {label('runSimulation')}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
  }
