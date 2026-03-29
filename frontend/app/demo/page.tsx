'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  RotateCcw,
  Settings,
  Zap,
  Globe,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  Circle,
  Clock,
  Activity,
  Radio,
  Shield,
} from 'lucide-react'

import GraphPanel from '@/components/graph/GraphPanel'
import TimelinePanel from '@/components/simulation/TimelinePanel'
import ReportPanel from '@/components/report/ReportPanel'
import ChatPanel from '@/components/chat/ChatPanel'
import {
  mockScenarios,
  mockGraphNodes,
  mockGraphEdges,
  mockSimulationSteps,
  mockReport,
  mockChatMessages,
} from '@/lib/mock-data'
import {
  checkBackendHealth,
  runScenario,
  fetchTrustStatus,
  type ScenarioResult,
  type TrustStatus,
} from '@/lib/api/demo'

/* ──────────────────────────────────────────────
   Processing pipeline steps
   ────────────────────────────────────────────── */
const processingSteps = [
  { label: 'Parsing scenario input' },
  { label: 'Extracting entities' },
  { label: 'Building relationship graph' },
  { label: 'Generating agent personas' },
  { label: 'Running simulation engine' },
  { label: 'Compiling intelligence brief' },
]

export default function DemoPage() {
  // ── State ──
  const [selectedScenario, setSelectedScenario] = useState(mockScenarios[0])
  const [scenarioTitle, setScenarioTitle] = useState(mockScenarios[0].title)
  const [scenarioText, setScenarioText] = useState(mockScenarios[0].scenario)
  const [country, setCountry] = useState(mockScenarios[0].country)
  const [category, setCategory] = useState(mockScenarios[0].category)
  const [isRunning, setIsRunning] = useState(false)
  const [hasResults, setHasResults] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [processingStep, setProcessingStep] = useState(0)
  const [isMobile, setIsMobile] = useState(false)
  const [runId, setRunId] = useState('—')
  const [runTimestamp, setRunTimestamp] = useState('—')

  // ── Live backend state ──
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const [liveResult, setLiveResult] = useState<ScenarioResult | null>(null)
  const [trustStatus, setTrustStatus] = useState<TrustStatus | null>(null)
  const [dataSource, setDataSource] = useState<'live' | 'mock'>('mock')

  // ── Backend connection: only attempt if NEXT_PUBLIC_API_URL is configured ──
  const apiConfigured = typeof window !== 'undefined'
    && !!process.env.NEXT_PUBLIC_API_URL
    && !process.env.NEXT_PUBLIC_API_URL.includes('localhost')

  useEffect(() => {
    if (!apiConfigured) {
      setBackendOnline(false)
      return
    }
    checkBackendHealth().then(online => {
      setBackendOnline(online)
      if (online) {
        fetchTrustStatus().then(setTrustStatus).catch(() => {})
      }
    })
  }, [apiConfigured])

  // ── Mobile detection ──
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // ── Simulation processing ──
  useEffect(() => {
    if (!isRunning) return
    const interval = setInterval(() => {
      setProcessingStep(prev => {
        if (prev < processingSteps.length - 1) return prev + 1
        return prev
      })
    }, 700)
    return () => clearInterval(interval)
  }, [isRunning])

  useEffect(() => {
    if (processingStep === processingSteps.length - 1 && isRunning) {
      const timeout = setTimeout(() => {
        setIsRunning(false)
        setHasResults(true)
        setCurrentStep(0)
      }, 600)
      return () => clearTimeout(timeout)
    }
  }, [processingStep, isRunning])

  // ── Handlers ──
  const handleScenarioSelect = (scenario: typeof mockScenarios[0]) => {
    setSelectedScenario(scenario)
    setScenarioTitle(scenario.title)
    setScenarioText(scenario.scenario)
    setCountry(scenario.country)
    setCategory(scenario.category)
    setHasResults(false)
    setCurrentStep(0)
  }

  const handleReset = () => {
    setHasResults(false)
    setCurrentStep(0)
    setProcessingStep(0)
    setIsRunning(false)
    setRunId('—')
    setRunTimestamp('—')
  }

  const handleRunSimulation = async () => {
    setIsRunning(true)
    setProcessingStep(0)
    setHasResults(false)
    setLiveResult(null)
    setRunId(`SIM-${Math.random().toString(36).substring(2, 8).toUpperCase()}`)
    setRunTimestamp(new Date().toLocaleTimeString('en-US', { hour12: false }))

    // Try live backend if available
    if (backendOnline) {
      try {
        const scenarioMap: Record<string, string> = {
          economy: 'hormuz_closure',
          'public sentiment': 'banking_shock',
          'business reaction': 'port_disruption',
          technology: 'airport_disruption',
          policy: 'sanctions_escalation',
        }
        const scenarioType = scenarioMap[category] ?? 'hormuz_closure'
        const result = await runScenario(scenarioType, 'sovereign_treasury', 0.8, 72)
        setLiveResult(result)
        setDataSource('live')
        // Also refresh trust status
        fetchTrustStatus().then(setTrustStatus).catch(() => {})
      } catch {
        setDataSource('mock')
      }
    } else {
      setDataSource('mock')
    }
  }

  // ── System status ──
  const systemStatus = useMemo(() => {
    if (isRunning) return { label: 'PROCESSING', color: 'bg-ds-accent', pulse: true }
    if (hasResults) return { label: 'COMPLETE', color: 'bg-ds-success', pulse: false }
    return { label: 'READY', color: 'bg-ds-text-dim', pulse: false }
  }, [isRunning, hasResults])

  // ── Mobile fallback ──
  if (isMobile) {
    return (
      <div className="h-screen w-full bg-ds-bg flex items-center justify-center p-6">
        <div className="ds-card p-10 text-center max-w-md">
          <div className="w-14 h-14 rounded-full bg-ds-surface-raised border border-ds-border flex items-center justify-center mx-auto mb-5">
            <Globe className="w-6 h-6 text-ds-text-muted" />
          </div>
          <h2 className="text-h3 mb-3">Desktop Required</h2>
          <p className="text-caption text-ds-text-muted mb-8 leading-relaxed">
            The Control Room requires a desktop viewport for the full intelligence experience.
          </p>
          <Link href="/" className="ds-btn-primary">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  /* ══════════════════════════════════════════════
     MAIN SYSTEM INTERFACE
     ══════════════════════════════════════════════ */
  return (
    <div className="h-screen w-full bg-ds-bg flex flex-col overflow-hidden">

      {/* ── TOP BAR — System status bar ── */}
      <div className="h-11 border-b border-ds-border bg-ds-surface/80 backdrop-blur-xl flex-shrink-0 flex items-center justify-between px-5">
        {/* Left: Nav + breadcrumb */}
        <div className="flex items-center gap-3 min-w-0">
          <Link
            href="/"
            className="flex items-center gap-2 text-ds-text-muted hover:text-ds-text transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
          </Link>
          <div className="w-px h-5 bg-ds-border" />
          <span className="text-micro font-semibold text-ds-text tracking-tight">DEEVO SIM</span>
          <span className="text-micro text-ds-text-dim font-mono">/</span>
          <span className="text-micro text-ds-text-muted font-mono">Control Room</span>
        </div>

        {/* Center: System status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${systemStatus.color} ${systemStatus.pulse ? 'animate-pulse' : ''}`} />
            <span className="text-nano font-mono uppercase tracking-[0.15em] text-ds-text-secondary">
              {systemStatus.label}
            </span>
          </div>
          {runId !== '—' && (
            <>
              <span className="text-nano text-ds-text-dim">·</span>
              <span className="text-nano font-mono text-ds-text-dim">
                <Clock size={10} className="inline mr-1 -mt-0.5" />
                {runTimestamp}
              </span>
              <span className="text-nano font-mono text-ds-text-dim">{runId}</span>
            </>
          )}
        </div>

        {/* Right: Mode indicator + Scenario meta */}
        <div className="flex items-center gap-3 min-w-0">
          {backendOnline ? (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span className="text-nano font-mono text-emerald-400 tracking-wider">LIVE</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-ds-accent/10 border border-ds-accent/20">
              <div className="w-1.5 h-1.5 rounded-full bg-ds-accent" />
              <span className="text-nano font-mono text-ds-accent tracking-wider">DEMO</span>
            </div>
          )}
          <span className="text-micro text-ds-text-muted truncate max-w-[200px] font-mono">
            {scenarioTitle}
          </span>
          <button className="p-1.5 hover:bg-ds-card rounded-md transition-colors text-ds-text-dim hover:text-ds-text">
            <Settings className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ── MAIN 3-COLUMN LAYOUT ── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ═══ LEFT SIDEBAR — Controls ═══ */}
        <div className="w-[280px] bg-ds-surface border-r border-ds-border overflow-y-auto flex flex-col">
          <div className="p-5 space-y-5 flex flex-col">

            {/* Scenario Input */}
            <div>
              <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-3 flex items-center gap-2">
                <Radio size={10} />
                Scenario Input
              </h3>
              <div className="space-y-3">
                <input
                  type="text"
                  value={scenarioTitle}
                  onChange={(e) => setScenarioTitle(e.target.value)}
                  placeholder="Scenario title"
                  className="ds-input text-micro"
                />
                <textarea
                  value={scenarioText}
                  onChange={(e) => setScenarioText(e.target.value)}
                  placeholder="Describe the scenario..."
                  dir="auto"
                  className="ds-input min-h-[100px] resize-none text-micro"
                />
                <select
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="ds-select text-micro"
                >
                  <option value="Saudi Arabia">Saudi Arabia</option>
                  <option value="Kuwait">Kuwait</option>
                  <option value="UAE">UAE</option>
                  <option value="Bahrain">Bahrain</option>
                  <option value="Oman">Oman</option>
                  <option value="Qatar">Qatar</option>
                  <option value="GCC">GCC</option>
                </select>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="ds-select text-micro"
                >
                  <option value="economy">Economy</option>
                  <option value="public sentiment">Public Sentiment</option>
                  <option value="business reaction">Business Reaction</option>
                  <option value="technology">Technology</option>
                  <option value="policy">Policy</option>
                </select>
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunSimulation}
              disabled={isRunning}
              className="w-full ds-btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  Run Simulation
                </>
              )}
            </button>

            {/* Processing Pipeline */}
            <AnimatePresence>
              {isRunning && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="pt-4 border-t border-ds-border space-y-3">
                    <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold flex items-center gap-2">
                      <Activity size={10} className="text-ds-accent" />
                      Pipeline
                    </h3>
                    <div className="space-y-2.5">
                      {processingSteps.map((step, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -8 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="flex items-center gap-2.5"
                        >
                          {idx < processingStep ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-ds-success flex-shrink-0" />
                          ) : idx === processingStep ? (
                            <Loader2 className="w-3.5 h-3.5 text-ds-accent animate-spin flex-shrink-0" />
                          ) : (
                            <Circle className="w-3.5 h-3.5 text-ds-text-dim flex-shrink-0" />
                          )}
                          <span className={`text-[11px] font-mono ${
                            idx < processingStep
                              ? 'text-ds-text-muted line-through'
                              : idx === processingStep
                                ? 'text-ds-accent'
                                : 'text-ds-text-dim'
                          }`}>
                            {step.label}
                          </span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Divider */}
            <div className="ds-divider" />

            {/* Preset Scenarios */}
            <div>
              <h3 className="text-nano uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-3 flex items-center gap-2">
                <Shield size={10} />
                Presets
              </h3>
              <div className="space-y-2">
                {mockScenarios.slice(0, 3).map((scenario) => (
                  <button
                    key={scenario.id}
                    onClick={() => handleScenarioSelect(scenario)}
                    className={`w-full text-left px-3.5 py-3 rounded-ds-lg border transition-all duration-200 ${
                      selectedScenario.id === scenario.id
                        ? 'bg-ds-accent/8 border-ds-accent/25'
                        : 'bg-ds-bg-alt border-ds-border hover:border-ds-border-hover hover:bg-ds-card/40'
                    }`}
                  >
                    <div className="text-micro font-medium text-ds-text truncate">
                      {scenario.title}
                    </div>
                    <div className="flex items-center gap-1.5 mt-1.5 text-[10px] text-ds-text-dim font-mono">
                      <Globe className="w-3 h-3" />
                      {scenario.country}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ═══ CENTER — Graph + Timeline (primary focus) ═══ */}
        <div className="flex-1 bg-ds-bg overflow-y-auto flex flex-col p-4 gap-4">
          {/* Graph Panel — dominant visual weight */}
          <div className="flex-1 min-h-[420px]">
            {!hasResults && !isRunning && (
              <div className="h-full ds-card rounded-ds-xl flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 ds-grid-bg opacity-20" />
                <div className="relative text-center">
                  <div className="w-12 h-12 rounded-full bg-ds-surface-raised border border-ds-border flex items-center justify-center mx-auto mb-3">
                    <Circle className="w-5 h-5 text-ds-text-dim" />
                  </div>
                  <p className="text-caption text-ds-text-dim">
                    Run a simulation to generate the entity graph
                  </p>
                  <p className="text-nano text-ds-text-dim mt-1 font-mono">AWAITING INPUT</p>
                </div>
              </div>
            )}
            {isRunning && (
              <div className="h-full ds-card rounded-ds-xl flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 ds-grid-bg opacity-20" />
                <div className="relative text-center">
                  <Loader2 className="w-10 h-10 mx-auto mb-3 text-ds-accent animate-spin" />
                  <p className="text-caption text-ds-text-muted">
                    Generating entity graph...
                  </p>
                  <p className="text-nano text-ds-accent font-mono mt-1">SIGNAL PROPAGATION ACTIVE</p>
                </div>
              </div>
            )}
            {hasResults && (
              <GraphPanel initialNodes={mockGraphNodes} initialEdges={mockGraphEdges} />
            )}
          </div>

          {/* Timeline Panel */}
          <div className="flex-shrink-0">
            {!hasResults && !isRunning && (
              <div className="ds-card rounded-ds-xl p-5 text-center">
                <p className="text-caption text-ds-text-dim font-mono">TIMELINE · AWAITING SIMULATION</p>
              </div>
            )}
            {isRunning && (
              <div className="ds-card rounded-ds-xl p-5 flex items-center justify-center gap-3">
                <Loader2 className="w-4 h-4 text-ds-accent animate-spin" />
                <span className="text-caption text-ds-text-muted font-mono">Building temporal model...</span>
              </div>
            )}
            {hasResults && (
              <TimelinePanel
                steps={mockSimulationSteps}
                activeStep={currentStep}
                onStepChange={setCurrentStep}
              />
            )}
          </div>
        </div>

        {/* ═══ RIGHT SIDEBAR — Intelligence Brief + Analyst ═══ */}
        <div className="w-[360px] bg-ds-surface border-l border-ds-border overflow-y-auto flex flex-col">
          <div className="p-4 space-y-4 flex flex-col h-full">

            {/* Action buttons */}
            {hasResults && (
              <div className="flex gap-2 flex-shrink-0">
                <button
                  onClick={handleRunSimulation}
                  className="flex-1 ds-btn-primary text-micro"
                >
                  <Play className="w-3.5 h-3.5" />
                  Rerun
                </button>
                <button
                  onClick={handleReset}
                  className="flex-1 ds-btn-secondary text-micro"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Reset
                </button>
              </div>
            )}

            {/* Live Engine Metrics (when backend data available) */}
            {hasResults && liveResult && (
              <div className="flex-shrink-0 ds-card rounded-ds-lg p-3 space-y-2 border border-ds-accent/20">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span className="text-nano font-mono uppercase tracking-widest text-ds-accent">Live Engine Output</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div>
                    <span className="text-ds-text-dim">Total Loss</span>
                    <div className="text-ds-text font-semibold">${(liveResult.totalLoss / 1e9).toFixed(2)}B</div>
                  </div>
                  <div>
                    <span className="text-ds-text-dim">Credibility</span>
                    <div className="text-emerald-400 font-semibold">{liveResult.costCredibility}</div>
                  </div>
                  <div>
                    <span className="text-ds-text-dim">Calibration</span>
                    <div className="text-ds-text font-semibold">{liveResult.calibrationScore}</div>
                  </div>
                  <div>
                    <span className="text-ds-text-dim">Trust Level</span>
                    <div className="text-ds-accent font-semibold">{liveResult.overallTrustLevel}</div>
                  </div>
                  <div className="col-span-2">
                    <span className="text-ds-text-dim">Deployment</span>
                    <div className="text-ds-text font-semibold">{liveResult.deploymentSuitability}</div>
                  </div>
                </div>
                {liveResult.drivers.length > 0 && (
                  <div className="pt-2 border-t border-ds-border">
                    <span className="text-[10px] text-ds-text-dim font-mono">DRIVERS</span>
                    <div className="text-[11px] text-ds-text-muted mt-1">{liveResult.drivers.join(' · ')}</div>
                  </div>
                )}
              </div>
            )}

            {/* Trust Status (when backend available) */}
            {trustStatus && (
              <div className="flex-shrink-0 ds-card rounded-ds-lg p-3 space-y-1 text-[11px] font-mono">
                <span className="text-nano text-ds-text-dim uppercase tracking-widest">System Trust</span>
                <div className="flex justify-between"><span className="text-ds-text-dim">Cost Credibility</span><span className="text-emerald-400">{trustStatus.costCredibility}</span></div>
                <div className="flex justify-between"><span className="text-ds-text-dim">Calibration</span><span className="text-ds-text">{trustStatus.calibrationScore}</span></div>
                <div className="flex justify-between"><span className="text-ds-text-dim">References</span><span className="text-ds-text">{trustStatus.fileReferences}/{trustStatus.totalReferences}</span></div>
                <div className="flex justify-between"><span className="text-ds-text-dim">Fields</span><span className="text-ds-text">{trustStatus.supportedFields}S/{trustStatus.weakFields}W/{trustStatus.unsupportedFields}U</span></div>
              </div>
            )}

            {/* Report / Intelligence Brief */}
            <div className="flex-shrink-0">
              {!hasResults && (
                <ReportPanel report={null} />
              )}
              {hasResults && (
                <ReportPanel report={mockReport} />
              )}
            </div>

            {/* Analyst / Chat */}
            <div className="flex-1 min-h-0 flex flex-col">
              <ChatPanel
                initialMessages={
                  hasResults
                    ? mockChatMessages
                    : [
                        {
                          id: '1',
                          role: 'assistant' as const,
                          content: 'Run a simulation to activate the analyst interface.',
                        },
                      ]
                }
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
