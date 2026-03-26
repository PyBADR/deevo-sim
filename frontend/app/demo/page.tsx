'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft, Settings, Zap, Globe, ChevronDown,
  Play, Pause, SkipForward
} from 'lucide-react'
import Link from 'next/link'
import GraphPanel from '@/components/graph/GraphPanel'
import ReportPanel from '@/components/report/ReportPanel'
import DecisionPanel from '@/components/decision/DecisionPanel'
import ChatPanel from '@/components/chat/ChatPanel'
import TimelinePanel from '@/components/simulation/TimelinePanel'
import {
  mockScenarios, mockEntities, mockGraphNodes, mockGraphEdges,
  mockSimulationSteps, mockReport, mockDecisionOutput,
  mockChatMessages, mockChatResponses, mockAgents,
} from '@/lib/mock-data'

type ViewTab = 'brief' | 'decision'

export default function DemoPage() {
  const [selectedScenario, setSelectedScenario] = useState(mockScenarios[0])
  const [isSimulating, setIsSimulating] = useState(false)
  const [simulationComplete, setSimulationComplete] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [rightTab, setRightTab] = useState<ViewTab>('decision')

  const handleRunSimulation = () => {
    if (isSimulating) return
    setIsSimulating(true)
    setSimulationComplete(false)
    setCurrentStep(0)

    // Simulate steps over time
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev >= mockSimulationSteps.length - 1) {
          clearInterval(stepInterval)
          setIsSimulating(false)
          setSimulationComplete(true)
          return prev
        }
        return prev + 1
      })
    }, 1500)
  }

  const selectScenario = (scenario: typeof mockScenarios[0]) => {
    setSelectedScenario(scenario)
    setSimulationComplete(false)
    setIsSimulating(false)
    setCurrentStep(0)
  }

  return (
    <div className="min-h-screen bg-ds-bg text-ds-text flex flex-col">
      {/* Top Bar */}
      <header className="h-12 border-b border-zinc-800/60 flex items-center justify-between px-4 bg-zinc-950/80 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <span className="text-xs font-mono font-bold tracking-wider text-indigo-400">DEEVO SIM</span>
          <span className="text-zinc-600">/</span>
          <span className="text-xs text-zinc-400">Control Room</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${simulationComplete ? 'bg-emerald-400' : isSimulating ? 'bg-amber-400 animate-pulse' : 'bg-zinc-600'}`} />
            <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              {simulationComplete ? 'COMPLETE' : isSimulating ? 'SIMULATING' : 'READY'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500 truncate max-w-[200px]">
            {selectedScenario.title}
          </span>
          <Settings className="w-3.5 h-3.5 text-zinc-600" />
        </div>
      </header>

      {/* Main 3-Column Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANEL — Scenario Input */}
        <aside className="w-72 border-r border-zinc-800/60 flex flex-col bg-zinc-950/40 shrink-0">
          <div className="p-4 space-y-4 flex-1 overflow-y-auto custom-scrollbar">
            {/* Scenario Header */}
            <div className="flex items-center gap-2 text-zinc-500">
              <Globe className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-[10px] uppercase tracking-widest font-semibold">Scenario Input</span>
            </div>

            {/* Selected Scenario */}
            <div className="space-y-3">
              <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
                <p className="text-sm font-medium text-zinc-200">{selectedScenario.title}</p>
              </div>
              <div className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3">
                <p className="text-sm text-zinc-300 leading-relaxed text-right" dir="rtl">
                  {selectedScenario.scenario}
                </p>
              </div>
              <div className="flex gap-2">
                <span className="text-xs px-2.5 py-1 rounded bg-zinc-800 text-zinc-400">
                  {selectedScenario.country}
                </span>
                <span className="text-xs px-2.5 py-1 rounded bg-zinc-800 text-zinc-400">
                  {selectedScenario.category}
                </span>
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunSimulation}
              disabled={isSimulating}
              className={`w-full py-3 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all ${
                isSimulating
                  ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20'
              }`}
            >
              {isSimulating ? (
                <><span className="w-4 h-4 border-2 border-zinc-500 border-t-transparent rounded-full animate-spin" /> Simulating...</>
              ) : (
                <><Zap className="w-4 h-4" /> Run Simulation</>
              )}
            </button>

            {/* Presets */}
            <div className="pt-2">
              <div className="flex items-center gap-2 text-zinc-500 mb-3">
                <ChevronDown className="w-3 h-3" />
                <span className="text-[10px] uppercase tracking-widest">Presets</span>
              </div>
              <div className="space-y-2">
                {mockScenarios.map(sc => (
                  <button
                    key={sc.id}
                    onClick={() => selectScenario(sc)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedScenario.id === sc.id
                        ? 'bg-indigo-500/10 border-indigo-500/30 text-zinc-200'
                        : 'bg-zinc-900/40 border-zinc-800 text-zinc-400 hover:border-zinc-700'
                    }`}
                  >
                    <p className="text-xs font-medium">{sc.title}</p>
                    <p className="text-[10px] text-zinc-500 mt-0.5 flex items-center gap-1">
                      <Globe className="w-2.5 h-2.5" /> {sc.country}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* CENTER — Graph + Timeline */}
        <main className="flex-1 flex flex-col min-w-0">
          {/* Graph Area */}
          <div className="flex-1 relative">
            <GraphPanel
              nodes={mockGraphNodes}
              edges={mockGraphEdges}
              isActive={isSimulating || simulationComplete}
            />
            {!isSimulating && !simulationComplete && (
              <div className="absolute inset-0 flex items-center justify-center bg-zinc-950/60">
                <div className="text-center">
                  <div className="w-12 h-12 rounded-full border border-zinc-700 flex items-center justify-center mx-auto mb-3">
                    <Play className="w-5 h-5 text-zinc-500" />
                  </div>
                  <p className="text-sm text-zinc-500">Run a simulation to generate the entity graph</p>
                  <p className="text-[10px] uppercase tracking-widest text-zinc-600 mt-1">AWAITING INPUT</p>
                </div>
              </div>
            )}
          </div>

          {/* Timeline Bar */}
          <div className="h-24 border-t border-zinc-800/60 bg-zinc-950/60 shrink-0">
            <TimelinePanel
              steps={mockSimulationSteps}
              currentStep={currentStep}
              isActive={isSimulating || simulationComplete}
            />
          </div>
        </main>

        {/* RIGHT PANEL — Intelligence Brief / Decision Output / Analyst */}
        <aside className="w-96 border-l border-zinc-800/60 flex flex-col bg-zinc-950/40 shrink-0">
          {/* Tab Switcher */}
          <div className="flex border-b border-zinc-800/60 shrink-0">
            <button
              onClick={() => setRightTab('decision')}
              className={`flex-1 py-2.5 text-[10px] uppercase tracking-widest font-semibold transition-colors ${
                rightTab === 'decision'
                  ? 'text-indigo-400 border-b-2 border-indigo-400 bg-indigo-500/5'
                  : 'text-zinc-500 hover:text-zinc-400'
              }`}
            >
              Decision Output
            </button>
            <button
              onClick={() => setRightTab('brief')}
              className={`flex-1 py-2.5 text-[10px] uppercase tracking-widest font-semibold transition-colors ${
                rightTab === 'brief'
                  ? 'text-indigo-400 border-b-2 border-indigo-400 bg-indigo-500/5'
                  : 'text-zinc-500 hover:text-zinc-400'
              }`}
            >
              Intelligence Brief
            </button>
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-hidden p-3">
            <AnimatePresence mode="wait">
              {rightTab === 'decision' ? (
                <motion.div key="decision" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <DecisionPanel
                    decision={mockDecisionOutput}
                    isActive={simulationComplete}
                  />
                </motion.div>
              ) : (
                <motion.div key="brief" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                  <ReportPanel
                    report={mockReport}
                    isActive={simulationComplete}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Analyst Chat */}
          <div className="h-52 border-t border-zinc-800/60 shrink-0">
            <ChatPanel
              messages={mockChatMessages}
              responses={mockChatResponses}
              isActive={simulationComplete}
            />
          </div>
        </aside>
      </div>
    </div>
  )
}
