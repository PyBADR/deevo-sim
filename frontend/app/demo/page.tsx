'use client'

import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play, RotateCcw, Globe as GlobeIcon, ArrowLeft, Loader2, CheckCircle2, Circle,
  Activity, Radio, Shield, Zap, BarChart3, List, FileText, ChevronDown, Languages,
} from 'lucide-react'
import GraphPanel from '@/components/graph/GraphPanel'
import { gccNodes, gccEdges, gccScenarios, type GCCNode, type GCCEdge, type GCCScenario } from '@/lib/gcc-graph'
import { runPropagation, formatPropagationChain, type PropagationResult } from '@/lib/propagation-engine'
import { nodeCoordinates, shippingRoutes, aviationRoutes } from '@/lib/gcc-coordinates'
import {
  labels, label, setLanguage, getLanguage, isRTL, type Language,
} from '@/lib/i18n'

/* ?? Layer visual config ?? */
const LAYER_COLORS: Record<string, string> = {
  geography: '#22d3ee',
  infrastructure: '#f59e0b',
  economy: '#3b82f6',
  finance: '#a78bfa',
  society: '#ef4444',
}
const LAYER_LABELS_AR: Record<string, string> = {
  geography: '?????????',
  infrastructure: '?????? ???????',
  economy: '????????',
  finance: '???????',
  society: '???????',
}
const LAYER_LABELS_EN: Record<string, string> = {
  geography: 'Geography',
  infrastructure: 'Infrastructure',
  economy: 'Economy',
  finance: 'Finance',
  society: 'Society',
}

/* ?? Additional bilingual labels ?? */
const UI: Record<string, { en: string; ar: string }> = {
  title: { en: 'Deevo Sim', ar: '???? ???' },
  controlRoom: { en: 'Control Room', ar: '???? ??????' },
  subtitle: { en: 'GCC Intelligence Simulation', ar: '?????? ??????????? ????????' },
  selectScenario: { en: 'Select Scenario', ar: '???? ???????' },
  runSim: { en: 'Run Simulation', ar: '????? ????????' },
  processing: { en: 'Processing...', ar: '???? ????????...' },
  graphView: { en: 'Graph View', ar: '??? ????? ???????' },
  globeView: { en: 'Globe View', ar: '??? ????? ???????' },
  impactChain: { en: 'Impact Chain', ar: '????? ???????' },
  topDrivers: { en: 'Top Drivers', ar: '??? ????????' },
  sectorImpact: { en: 'Sector Impact', ar: '??????? ???????' },
  explanation: { en: 'Explanation', ar: '???????' },
  severity: { en: 'Severity', ar: '?????' },
  confidence: { en: 'Confidence', ar: '?????' },
  systemEnergy: { en: 'System Energy', ar: '???? ??????' },
  nodesAffected: { en: 'Nodes Affected', ar: '????? ????????' },
  totalLoss: { en: 'Est. Exposure', ar: '?????? ??????' },
  awaitingInput: { en: 'AWAITING INPUT', ar: '?? ?????? ???????' },
  running: { en: 'PROCESSING', ar: '???????? ?????' },
  complete: { en: 'COMPLETE', ar: '?????' },
  ready: { en: 'READY', ar: '????' },
  runToSee: { en: 'Run a simulation to see results', ar: '?? ?????? ?????? ???? ???????' },
  shockNodes: { en: 'Shock Nodes', ar: '??? ??????' },
  presets: { en: 'Scenario Presets', ar: '?????????? ?????' },
  pipeline: { en: 'Pipeline', ar: '?? ????????' },
  spread: { en: 'Spread Level', ar: '????? ????????' },
  desktop: { en: 'Desktop Required', ar: '????? ??? ??????' },
  desktopMsg: { en: 'Control Room requires desktop viewport.', ar: '???? ?????? ????? ???? ??? ??????.' },
}

function ui(key: string): string {
  const lang = getLanguage()
  const entry = UI[key]
  return entry ? (lang === 'ar' ? entry.ar : entry.en) : key
}

function layerLabel(layer: string): string {
  const lang = getLanguage()
  return lang === 'ar' ? (LAYER_LABELS_AR[layer] || layer) : (LAYER_LABELS_EN[layer] || layer)
}

/* ?? Processing pipeline steps ?? */
const PIPELINE = [
  { en: 'Parsing scenario input', ar: '????? ?????? ?????????' },
  { en: 'Extracting entities', ar: '??????? ????????' },
  { en: 'Building relationship graph', ar: '???? ??? ????????' },
  { en: 'Running propagation engine', ar: '????? ???? ????????' },
  { en: 'Computing sector impacts', ar: '???? ????????? ????????' },
  { en: 'Generating intelligence brief', ar: '????? ?????? ????????????' },
]

/* ?? Globe Component (dynamic import to avoid SSR) ?? */
import dynamic from 'next/dynamic'
const GlobeGL = dynamic(() => import('react-globe.gl'), { ssr: false })

/* ??????????????????????????????????????????????????????????
   GLOBE VIEW COMPONENT
   ?????????????????????????????????????????????????????????? */
function GlobeView({
  propagation,
  selectedNode,
  onSelectNode,
}: {
  propagation: PropagationResult | null
  selectedNode: string | null
  onSelectNode: (id: string | null) => void
}) {
  const globeRef = useRef<any>(null)

  const pointsData = useMemo(() => {
    return gccNodes.map(node => {
      const coords = nodeCoordinates[node.id]
      if (!coords) return null
      const impact = propagation ? (propagation.nodeImpacts.get(node.id) || 0) : 0
      return {
        id: node.id,
        lat: coords.lat,
        lng: coords.lng,
        label: node.label,
        layer: node.layer,
        impact: Math.abs(impact),
        color: LAYER_COLORS[node.layer] || '#64748b',
        size: 0.3 + Math.abs(impact) * 1.5,
        isSelected: selectedNode === node.id,
      }
    }).filter(Boolean)
  }, [propagation, selectedNode])

  const arcsData = useMemo(() => {
    if (!propagation) return []
    const arcs: any[] = []
    for (const step of propagation.propagationChain) {
      const fromCoords = nodeCoordinates[step.from]
      const toCoords = nodeCoordinates[step.to]
      if (!fromCoords || !toCoords) continue
      const fromNode = gccNodes.find(n => n.id === step.from)
      arcs.push({
        startLat: fromCoords.lat, startLng: fromCoords.lng,
        endLat: toCoords.lat, endLng: toCoords.lng,
        color: LAYER_COLORS[fromNode?.layer || 'geography'] || '#22d3ee',
        stroke: Math.abs(step.impact) * 3,
      })
    }
    return arcs
  }, [propagation])

  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.pointOfView({ lat: 25, lng: 51, altitude: 2.5 }, 1000)
    }
  }, [])

  return (
    <div className="w-full h-full bg-[#06060a] rounded-xl overflow-hidden">
      <GlobeGL
        ref={globeRef}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-dark.jpg"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        pointsData={pointsData}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointAltitude={(d: any) => d.impact * 0.05}
        pointRadius={(d: any) => d.size}
        pointLabel={(d: any) => `<div style="color:${d.color};font-family:system-ui;font-size:12px;font-weight:600">${d.label}<br/><span style="color:#94a3b8">${(d.impact * 100).toFixed(0)}% impact</span></div>`}
        onPointClick={(point: any) => onSelectNode(point.id)}
        arcsData={arcsData}
        arcStartLat="startLat"
        arcStartLng="startLng"
        arcEndLat="endLat"
        arcEndLng="endLng"
        arcColor="color"
        arcStroke="stroke"
        arcDashLength={0.5}
        arcDashGap={0.3}
        arcDashAnimateTime={2000}
        atmosphereColor="#22d3ee"
        atmosphereAltitude={0.15}
        width={800}
        height={600}
        animateIn={true}
      />
    </div>
  )
}

/* ??????????????????????????????????????????????????????????
   SECTOR IMPACT BAR
   ?????????????????????????????????????????????????????????? */
function SectorBar({ sector, avgImpact, color }: { sector: string; avgImpact: number; color: string }) {
  const pct = Math.min(100, avgImpact * 100)
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className="text-[11px] w-20 text-ds-text-muted truncate">{layerLabel(sector)}</span>
      <div className="flex-1 h-3 bg-ds-bg-alt rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6 }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
      <span className="text-[11px] font-mono w-10 text-end" style={{ color }}>{pct.toFixed(0)}%</span>
    </div>
  )
}

/* ??????????????????????????????????????????????
   MAIN DEMO PAGE
   ?????????????????????????????????????????????? */
export default function DemoPage() {
  const [lang, setLang] = useState<Language>('ar')
  const [scenarioId, setScenarioId] = useState<string>('')
  const [isRunning, setIsRunning] = useState(false)
  const [processingStep, setProcessingStep] = useState(0)
  const [propagation, setPropagation] = useState<PropagationResult | null>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'graph' | 'globe'>('graph')
  const [severityMod, setSeverityMod] = useState(1.0)
  const [isMobile, setIsMobile] = useState(false)

  // Apply language
  useEffect(() => {
    setLanguage(lang)
    if (typeof document !== 'undefined') {
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
      document.documentElement.lang = lang
    }
  }, [lang])

  // Mobile detection
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 1024)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  const scenario = useMemo(() => gccScenarios.find(s => s.id === scenarioId), [scenarioId])

  // Processing animation
  useEffect(() => {
    if (!isRunning) return
    const interval = setInterval(() => {
      setProcessingStep(prev => (prev < PIPELINE.length - 1 ? prev + 1 : prev))
    }, 500)
    return () => clearInterval(interval)
  }, [isRunning])

  useEffect(() => {
    if (processingStep === PIPELINE.length - 1 && isRunning) {
      const timeout = setTimeout(() => {
        if (scenario) {
          const modShocks = scenario.shocks.map(s => ({
            ...s, impact: Math.min(1, s.impact * severityMod),
          }))
          const result = runPropagation(gccNodes, gccEdges, modShocks, 6)
          setPropagation(result)
        }
        setIsRunning(false)
      }, 400)
      return () => clearTimeout(timeout)
    }
  }, [processingStep, isRunning, scenario, severityMod])

  const handleRun = useCallback(() => {
    if (!scenario) return
    setIsRunning(true)
    setProcessingStep(0)
    setPropagation(null)
    setSelectedNode(null)
  }, [scenario])

  const handleReset = useCallback(() => {
    setPropagation(null)
    setIsRunning(false)
    setProcessingStep(0)
    setSelectedNode(null)
  }, [])

  // Build graph panel nodes/edges from propagation results
  const graphNodes = useMemo(() => {
    return gccNodes.map(n => {
      const impact = propagation ? Math.abs(propagation.nodeImpacts.get(n.id) || 0) : 0
      const coords = nodeCoordinates[n.id]
      return {
        id: n.id,
        type: 'default',
        position: { x: (coords?.lng || 50) * 30 - 1200, y: (coords?.lat || 25) * -30 + 900 },
        data: {
          label: lang === 'ar' ? (gccScenarios.find(s => s.id === scenarioId)?.titleAr || n.label) : n.label,
          layer: n.layer,
          impact,
        },
        style: {
          background: impact > 0.05 ? LAYER_COLORS[n.layer] : '#1e293b',
          color: '#e2e8f0',
          border: `2px solid ${selectedNode === n.id ? '#fff' : (impact > 0.05 ? LAYER_COLORS[n.layer] : '#334155')}`,
          borderRadius: '8px',
          padding: '6px 10px',
          fontSize: '11px',
          fontWeight: impact > 0.1 ? '700' : '400',
          opacity: impact > 0.01 ? 1 : 0.5,
          boxShadow: impact > 0.2 ? `0 0 ${impact * 20}px ${LAYER_COLORS[n.layer]}40` : 'none',
        },
      }
    })
  }, [propagation, selectedNode, lang, scenarioId])

  const graphEdges = useMemo(() => {
    return gccEdges.map(e => {
      const sourceImpact = propagation ? Math.abs(propagation.nodeImpacts.get(e.source) || 0) : 0
      const strength = e.weight * sourceImpact
      return {
        id: e.id,
        source: e.source,
        target: e.target,
        animated: strength > 0.1,
        style: {
          stroke: strength > 0.05 ? '#22d3ee' : '#1e293b',
          strokeWidth: 1 + strength * 4,
          opacity: 0.2 + strength * 0.8,
        },
      }
    })
  }, [propagation])

  // Status
  const simStatus = isRunning ? 'running' : propagation ? 'complete' : scenario ? 'ready' : 'awaiting'
  const statusColor = { awaiting: '#f59e0b', running: '#3b82f6', complete: '#10b981', ready: '#64748b' }[simStatus]
  const statusText = ui(simStatus === 'awaiting' ? 'awaitingInput' : simStatus)

  // Formatted propagation chains
  const chains = useMemo(() => {
    if (!propagation) return []
    return formatPropagationChain(propagation.propagationChain)
  }, [propagation])

  // Mobile fallback
  if (isMobile) {
    return (
      <div className="h-screen w-full bg-ds-bg flex items-center justify-center p-6" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
        <div className="ds-card p-10 text-center max-w-md">
          <GlobeIcon className="w-10 h-10 text-ds-text-muted mx-auto mb-4" />
          <h2 className="text-lg font-bold mb-2">{ui('desktop')}</h2>
          <p className="text-sm text-ds-text-muted mb-6">{ui('desktopMsg')}</p>
          <Link href="/" className="ds-btn-primary"><ArrowLeft className="w-4 h-4" /> {lang === 'ar' ? '??????' : 'Back'}</Link>
        </div>
      </div>
    )
  }

  /* ??????????????????????????????????????????????
     MAIN RENDER
     ?????????????????????????????????????????????? */
  return (
    <div className="h-screen w-full bg-ds-bg flex flex-col overflow-hidden" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
      {/* ?? TOP BAR ?? */}
      <div className="h-11 border-b border-ds-border bg-ds-surface/80 backdrop-blur-xl flex-shrink-0 flex items-center justify-between px-5">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-ds-text-muted hover:text-ds-text transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
          </Link>
          <div className="w-px h-5 bg-ds-border" />
          <span className="text-[11px] font-semibold text-ds-text tracking-tight">{ui('title')}</span>
          <span className="text-[11px] text-ds-text-dim font-mono">/</span>
          <span className="text-[11px] text-ds-text-muted font-mono">{ui('controlRoom')}</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full`} style={{ backgroundColor: statusColor }} />
            <span className="text-[10px] font-mono uppercase tracking-[0.15em]" style={{ color: statusColor }}>{statusText}</span>
          </div>
          {propagation && (
            <>
              <span className="text-[10px] text-ds-text-dim">|</span>
              <span className="text-[10px] font-mono text-ds-text-dim">{ui('confidence')}: <span className="text-emerald-400">{(propagation.confidence * 100).toFixed(0)}%</span></span>
              <span className="text-[10px] text-ds-text-dim">|</span>
              <span className="text-[10px] font-mono text-ds-text-dim">{ui('spread')}: <span className="text-cyan-400 uppercase">{propagation.spreadLevel}</span></span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-ds-card border border-ds-border hover:border-ds-border-hover transition-colors text-[11px] font-semibold text-ds-text"
          >
            <Languages className="w-3 h-3" />
            {lang === 'ar' ? 'EN' : '????'}
          </button>
        </div>
      </div>

      {/* ?? MAIN 3-COLUMN LAYOUT ?? */}
      <div className="flex-1 flex overflow-hidden">
        {/* ??? LEFT Ñ Controls ??? */}
        <div className="w-[270px] bg-ds-surface border-e border-ds-border overflow-y-auto flex-shrink-0">
          <div className="p-4 space-y-4">
            {/* Scenario Selector */}
            <div>
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-2 flex items-center gap-2">
                <Radio size={10} /> {ui('selectScenario')}
              </h3>
              <select
                value={scenarioId}
                onChange={(e) => { setScenarioId(e.target.value); handleReset() }}
                className="ds-select text-[12px] w-full"
                dir={lang === 'ar' ? 'rtl' : 'ltr'}
              >
                <option value="">{ui('selectScenario')}</option>
                {gccScenarios.map(s => (
                  <option key={s.id} value={s.id}>{lang === 'ar' ? s.titleAr : s.title}</option>
                ))}
              </select>
            </div>

            {/* Scenario Details */}
            {scenario && (
              <div className="space-y-3">
                <p className="text-[12px] text-ds-text-muted leading-relaxed">
                  {lang === 'ar' ? scenario.descriptionAr : scenario.description}
                </p>

                <div>
                  <span className="text-[10px] text-ds-text-dim font-semibold uppercase tracking-wider">{ui('shockNodes')}</span>
                  {scenario.shocks.map(s => {
                    const node = gccNodes.find(n => n.id === s.nodeId)
                    return (
                      <div key={s.nodeId} className="flex items-center justify-between mt-1 px-2 py-1.5 bg-ds-bg-alt rounded-md text-[11px]">
                        <span style={{ color: LAYER_COLORS[node?.layer || 'geography'] }}>{node?.label}</span>
                        <span className="text-red-400 font-mono font-semibold">{(s.impact * severityMod * 100).toFixed(0)}%</span>
                      </div>
                    )
                  })}
                </div>

                {/* Severity Slider */}
                <div>
                  <div className="flex justify-between text-[10px] text-ds-text-dim mb-1">
                    <span>{ui('severity')}</span>
                    <span className="font-mono">{(severityMod * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range" min="0.1" max="1.5" step="0.05"
                    value={severityMod}
                    onChange={(e) => setSeverityMod(parseFloat(e.target.value))}
                    className="w-full accent-cyan-500"
                  />
                </div>

                {/* Run Button */}
                <button
                  onClick={handleRun}
                  disabled={isRunning}
                  className="w-full ds-btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" /> {ui('processing')}</> : <><Zap className="w-4 h-4" /> {ui('runSim')}</>}
                </button>
              </div>
            )}

            {/* Processing Pipeline */}
            <AnimatePresence>
              {isRunning && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                  <div className="pt-3 border-t border-ds-border space-y-2">
                    <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-semibold flex items-center gap-2">
                      <Activity size={10} className="text-cyan-400" /> {ui('pipeline')}
                    </h3>
                    {PIPELINE.map((step, idx) => (
                      <motion.div key={idx} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.05 }} className="flex items-center gap-2">
                        {idx < processingStep ? <CheckCircle2 className="w-3 h-3 text-emerald-500 flex-shrink-0" /> :
                         idx === processingStep ? <Loader2 className="w-3 h-3 text-cyan-400 animate-spin flex-shrink-0" /> :
                         <Circle className="w-3 h-3 text-ds-text-dim flex-shrink-0" />}
                        <span className={`text-[11px] font-mono ${idx < processingStep ? 'text-ds-text-muted line-through' : idx === processingStep ? 'text-cyan-400' : 'text-ds-text-dim'}`}>
                          {lang === 'ar' ? step.ar : step.en}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="border-t border-ds-border" />

            {/* Presets */}
            <div>
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-ds-text-dim font-semibold mb-2 flex items-center gap-2">
                <Shield size={10} /> {ui('presets')}
              </h3>
              <div className="space-y-1.5">
                {gccScenarios.map(s => (
                  <button
                    key={s.id}
                    onClick={() => { setScenarioId(s.id); handleReset() }}
                    className={`w-full text-start px-3 py-2.5 rounded-lg border transition-all text-[12px] ${
                      scenarioId === s.id ? 'bg-cyan-500/10 border-cyan-500/25' : 'bg-ds-bg-alt border-ds-border hover:border-ds-border-hover'
                    }`}
                  >
                    <div className="font-medium text-ds-text">{lang === 'ar' ? s.titleAr : s.title}</div>
                    <div className="text-[10px] text-ds-text-dim mt-0.5 font-mono">{s.country} á {s.category}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ??? CENTER Ñ Visualization ??? */}
        <div className="flex-1 bg-ds-bg flex flex-col overflow-hidden">
          {/* View Toggle */}
          <div className="flex items-center gap-0 px-4 py-2 border-b border-ds-border bg-ds-surface/50">
            <button
              onClick={() => setViewMode('graph')}
              className={`px-4 py-1.5 text-[12px] font-semibold rounded-s-md border border-ds-border transition-colors ${
                viewMode === 'graph' ? 'bg-cyan-500 text-ds-bg border-cyan-500' : 'bg-ds-card text-ds-text-muted'
              }`}
            >
              {ui('graphView')}
            </button>
            <button
              onClick={() => setViewMode('globe')}
              className={`px-4 py-1.5 text-[12px] font-semibold rounded-e-md border border-ds-border transition-colors ${
                viewMode === 'globe' ? 'bg-cyan-500 text-ds-bg border-cyan-500' : 'bg-ds-card text-ds-text-muted'
              }`}
            >
              <GlobeIcon className="w-3 h-3 inline me-1" />{ui('globeView')}
            </button>
            {propagation && (
              <div className="ms-auto flex items-center gap-3 text-[10px] font-mono text-ds-text-dim">
                <span>{ui('totalLoss')}: <span className="text-red-400 font-semibold">${propagation.totalLoss.toFixed(1)}B</span></span>
                <span>{ui('nodesAffected')}: <span className="text-cyan-400">{propagation.propagationChain.length}</span></span>
              </div>
            )}
          </div>

          {/* Visualization */}
          <div className="flex-1 relative">
            {!propagation && !isRunning && (
              <div className="h-full ds-card m-4 rounded-xl flex items-center justify-center">
                <div className="text-center">
                  <Circle className="w-10 h-10 text-ds-text-dim mx-auto mb-3" />
                  <p className="text-sm text-ds-text-dim">{ui('runToSee')}</p>
                  <p className="text-[10px] text-ds-text-dim font-mono mt-1">{ui('awaitingInput')}</p>
                </div>
              </div>
            )}
            {isRunning && (
              <div className="h-full ds-card m-4 rounded-xl flex items-center justify-center">
                <div className="text-center">
                  <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mx-auto mb-3" />
                  <p className="text-sm text-ds-text-muted">{lang === 'ar' ? '???? ???? ????? ???????...' : 'Building entity graph...'}</p>
                </div>
              </div>
            )}
            {propagation && !isRunning && viewMode === 'graph' && (
              <div className="h-full p-2">
                <GraphPanel initialNodes={graphNodes} initialEdges={graphEdges} />
              </div>
            )}
            {propagation && !isRunning && viewMode === 'globe' && (
              <div className="h-full p-2">
                <GlobeView propagation={propagation} selectedNode={selectedNode} onSelectNode={setSelectedNode} />
              </div>
            )}
          </div>
        </div>

        {/* ??? RIGHT Ñ Intelligence Panels ??? */}
        <div className="w-[320px] bg-ds-surface border-s border-ds-border overflow-y-auto flex-shrink-0">
          <div className="p-4 space-y-4">
            {propagation && (
              <div className="flex gap-2">
                <button onClick={handleRun} className="flex-1 ds-btn-primary text-[12px]"><Play className="w-3 h-3" /> {lang === 'ar' ? '?????' : 'Rerun'}</button>
                <button onClick={handleReset} className="flex-1 ds-btn-secondary text-[12px]"><RotateCcw className="w-3 h-3" /> {lang === 'ar' ? '????? ?????' : 'Reset'}</button>
              </div>
            )}

            {/* Impact Chain */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-cyan-400 font-bold mb-2 flex items-center gap-2">
                <List size={12} /> {ui('impactChain')}
              </h3>
              {propagation && chains.length > 0 ? (
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {chains.slice(0, 8).map((chain, i) => (
                    <div key={i} className="text-[11px] font-mono text-ds-text-muted px-2 py-1 bg-ds-bg-alt rounded">
                      {chain}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee')}</p>
              )}
            </div>

            {/* Top Drivers */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-amber-400 font-bold mb-2 flex items-center gap-2">
                <BarChart3 size={12} /> {ui('topDrivers')}
              </h3>
              {propagation ? (
                <div className="space-y-2">
                  {propagation.topDrivers.slice(0, 8).map((driver, i) => (
                    <div key={driver.nodeId} className="flex items-center gap-2 cursor-pointer hover:bg-ds-bg-alt rounded px-1 py-0.5 transition-colors" onClick={() => setSelectedNode(driver.nodeId)}>
                      <span className="text-[10px] text-ds-text-dim w-4 text-center">{i + 1}</span>
                      <div className="flex-1">
                        <div className="text-[11px] text-ds-text font-medium">{driver.label}</div>
                        <div className="h-2 bg-ds-bg-alt rounded-full mt-0.5">
                          <div className="h-2 rounded-full transition-all" style={{
                            width: `${driver.impact * 100}%`,
                            backgroundColor: LAYER_COLORS[driver.layer],
                          }} />
                        </div>
                      </div>
                      <span className="text-[10px] font-mono font-semibold" style={{ color: LAYER_COLORS[driver.layer] }}>
                        {(driver.impact * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee')}</p>
              )}
            </div>

            {/* Sector Impact */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-emerald-400 font-bold mb-2 flex items-center gap-2">
                <Activity size={12} /> {ui('sectorImpact')}
              </h3>
              {propagation ? (
                <div>
                  {propagation.affectedSectors.map(s => (
                    <SectorBar key={s.sector} sector={s.sector} avgImpact={s.avgImpact} color={s.color} />
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee')}</p>
              )}
            </div>

            {/* Explanation */}
            <div className="ds-card rounded-xl p-3">
              <h3 className="text-[10px] uppercase tracking-[0.15em] text-purple-400 font-bold mb-2 flex items-center gap-2">
                <FileText size={12} /> {ui('explanation')}
              </h3>
              {propagation ? (
                <p className="text-[12px] text-ds-text-muted leading-relaxed">{propagation.explanation}</p>
              ) : (
                <p className="text-[11px] text-ds-text-dim">{ui('runToSee')}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ?? STATUS BAR ?? */}
      <div className="h-8 border-t border-ds-border bg-ds-surface/80 backdrop-blur-xl flex items-center justify-between px-5 text-[10px] font-mono flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor }} />
            <span style={{ color: statusColor }} className="uppercase tracking-wider">{statusText}</span>
          </div>
          {propagation && (
            <>
              <span className="text-ds-text-dim">|</span>
              <span className="text-ds-text-dim">{ui('systemEnergy')}: <span className="text-cyan-400">{(Array.from(propagation.nodeImpacts.values()).reduce((a, b) => a + Math.abs(b), 0)).toFixed(2)}</span></span>
            </>
          )}
        </div>
        <span className="text-ds-text-dim">Deevo Sim v2.0 | deevo-sim.vercel.app</span>
      </div>
    </div>
  )
}