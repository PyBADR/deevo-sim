'use client'
import { useState, useCallback, Component, type ReactNode } from 'react'
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  useReactFlow,
  type Node,
  type Edge,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Eye, EyeOff } from 'lucide-react'
import { getNodeColor } from '@/lib/utils'

/* ──────────────────────────────────────────────
   Error Boundary — catches React Flow crashes
   ────────────────────────────────────────────── */
interface EBProps { children: ReactNode; fallbackNodes: Node[]; fallbackEdges: Edge[] }
interface EBState { hasError: boolean }

class GraphErrorBoundary extends Component<EBProps, EBState> {
  state: EBState = { hasError: false }
  static getDerivedStateFromError(): EBState { return { hasError: true } }
  render() {
    if (this.state.hasError) {
      return <StaticGraphFallback nodes={this.props.fallbackNodes} edges={this.props.fallbackEdges} />
    }
    return this.props.children
  }
}

/* ──────────────────────────────────────────────
   Static SVG Fallback — renders if React Flow dies
   ────────────────────────────────────────────── */
function StaticGraphFallback({ nodes, edges }: { nodes: Node[]; edges: Edge[] }) {
  const nodeMap = new Map(nodes.map(n => [n.id, n]))
  return (
    <div className="w-full h-full bg-ds-surface rounded-ds-xl border border-ds-border overflow-hidden relative">
      <div className="ds-panel-header">
        <div className="ds-panel-header-title">
          <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
          <span className="text-caption font-semibold text-ds-text tracking-tight">Entity Graph</span>
          <span className="text-nano text-amber-400 font-mono ml-1">STATIC</span>
        </div>
        <span className="ds-panel-header-meta">{nodes.length} nodes · {edges.length} edges</span>
      </div>
      <svg viewBox="0 0 800 520" className="w-full h-[calc(100%-52px)]">
        <defs>
          <filter id="glow"><feGaussianBlur stdDeviation="3" result="g" /><feMerge><feMergeNode in="g" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        {edges.map(e => {
          const s = nodeMap.get(e.source)
          const t = nodeMap.get(e.target)
          if (!s || !t) return null
          return <line key={e.id} x1={s.position.x + 40} y1={s.position.y + 40} x2={t.position.x + 40} y2={t.position.y + 40} stroke="#1C1C2A" strokeWidth={1.2} />
        })}
        {nodes.map(n => {
          const color = getNodeColor(n.data?.type as string || 'Topic')
          const w = (n.data?.weight as number) || 0.5
          const r = 16 + w * 14
          return (
            <g key={n.id} filter="url(#glow)">
              <circle cx={n.position.x + 40} cy={n.position.y + 40} r={r} fill={`${color}20`} stroke={`${color}55`} strokeWidth={1} />
              <circle cx={n.position.x + 40} cy={n.position.y + 40} r={3} fill={color} />
              <text x={n.position.x + 40} y={n.position.y + 40 + r + 12} textAnchor="middle" fill="#A0A0B0" fontSize={9} fontFamily="sans-serif">{n.data?.label as string}</text>
            </g>
          )
        })}
      </svg>
    </div>
  )
  }

/* ──────────────────────────────────────────────
   Custom Node — cinematic, glowing, alive
   ────────────────────────────────────────────── */
function CustomNode({ data }: { data: { label: string; type: string; weight: number } }) {
  const color = getNodeColor(data.type)
  const weight = data.weight || 0.5
  const size = 44 + weight * 36
  const glowIntensity = Math.round(weight * 40)
  const pulseClass = weight > 0.7 ? 'animate-pulse-glow' : ''

  return (
    <div className="relative group">
      <Handle type="target" position={Position.Top} className="!bg-transparent !border-0 !w-3 !h-3" />

      {/* Outer glow ring */}
      <div
        className={`absolute inset-0 rounded-full ${pulseClass}`}
        style={{
          background: `radial-gradient(circle, ${color}${Math.round(weight * 20).toString(16).padStart(2, '0')} 0%, transparent 70%)`,
          transform: 'scale(1.8)',
          filter: `blur(${8 + weight * 12}px)`,
          pointerEvents: 'none',
        }}
      />

      {/* Node body */}
      <div
        className="relative flex flex-col items-center justify-center rounded-full border transition-all duration-300 group-hover:scale-110"
        style={{
          width: size,
          height: size,
          borderColor: `${color}55`,
          backgroundColor: `${color}12`,
          boxShadow: `
            0 0 ${glowIntensity}px ${color}20,
            inset 0 0 ${glowIntensity / 2}px ${color}08,
            0 0 ${glowIntensity * 2}px ${color}08
          `,
        }}
      >
        {/* Inner dot */}
        <div
          className="w-2 h-2 rounded-full mb-1"
          style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}60` }}
        />
        <span
          className="text-[9px] font-semibold text-ds-text text-center leading-tight px-1"
          style={{ maxWidth: size + 16 }}
        >
          {data.label}
        </span>
      </div>

      {/* Hover tooltip */}
      <div
        className="absolute -bottom-7 left-1/2 -translate-x-1/2 text-[9px] font-mono text-ds-text-muted whitespace-nowrap opacity-0 group-hover:opacity-100 transition-all duration-300 bg-ds-bg/90 backdrop-blur-sm px-2 py-0.5 rounded border border-ds-border/50"
      >
        {data.type} · {Math.round(weight * 100)}%
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-0 !w-3 !h-3" />
    </div>
  )
}

const nodeTypes = { custom: CustomNode }

/* ──────────────────────────────────────────────
   Flow Inner — must be inside ReactFlowProvider
   ────────────────────────────────────────────── */
interface FlowInnerProps {
  initialNodes: Node[]
  initialEdges: Edge[]
}

function FlowInner({ initialNodes, initialEdges }: FlowInnerProps) {
  const { fitView } = useReactFlow()

  // Ensure every node has type: 'custom' and valid position
  // Do NOT add width/height — let the custom node component control its own size
  const safeNodes = initialNodes.map(n => ({
    ...n,
    type: 'custom',
    position: n.position ?? { x: 0, y: 0 },
  }))

  const [nodes, , onNodesChange] = useNodesState(safeNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)
  const [focusMode, setFocusMode] = useState(false)

  const styledEdges = edges.map(e => ({
    ...e,
    style: {
      stroke: focusMode ? '#2A2A3D' : '#1C1C2A',
      strokeWidth: 1.2,
      strokeDasharray: e.animated ? '6 4' : undefined,
    },
    animated: true,
    labelStyle: { fill: '#5A5A70', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' },
    labelBgStyle: { fill: '#0E0E14', fillOpacity: 0.95 },
    labelBgPadding: [6, 3] as [number, number],
    labelBgBorderRadius: 6,
  }))

  const onInit = useCallback(() => {
    // Delay fitView so React Flow has time to measure custom nodes
    setTimeout(() => {
      try { fitView({ padding: 0.35 }) } catch { /* swallow */ }
    }, 200)
  }, [fitView])

  return (
    <div className="w-full h-full bg-ds-surface rounded-ds-xl border border-ds-border overflow-hidden relative">
      {/* Panel header */}
      <div className="ds-panel-header">
        <div className="ds-panel-header-title">
          <div className="w-2 h-2 rounded-full bg-ds-success animate-pulse" />
          <span className="text-caption font-semibold text-ds-text tracking-tight">Entity Graph</span>
          <span className="text-nano text-ds-text-dim font-mono ml-1">LIVE</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="ds-panel-header-meta">{nodes.length} nodes · {edges.length} edges</span>
          <button
            onClick={() => setFocusMode(!focusMode)}
            className="p-1.5 rounded-md hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text"
            title={focusMode ? 'Exit Focus Mode' : 'Focus Mode'}
          >
            {focusMode ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
      </div>

      {/* Graph */}
      <div className="h-[calc(100%-52px)]">
        <ReactFlow
          nodes={nodes}
          edges={styledEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          onInit={onInit}
          defaultViewport={{ x: 0, y: 0, zoom: 0.85 }}
          proOptions={{ hideAttribution: true }}
          className="!bg-ds-surface"
          minZoom={0.3}
          maxZoom={2}
        >
          <Background color="#1A1A28" gap={36} size={1} />
          <Controls
            className="!bg-ds-card !border-ds-border !rounded-ds-lg !shadow-ds [&>button]:!bg-ds-card [&>button]:!border-ds-border [&>button]:!text-ds-text-muted [&>button:hover]:!bg-ds-card-hover [&>button:hover]:!text-ds-text"
          />
        </ReactFlow>
      </div>

      {/* Focus mode overlay indicator */}
      {focusMode && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 bg-ds-accent/10 border border-ds-accent/20 backdrop-blur-sm rounded-full px-3 py-1 text-nano font-mono text-ds-accent flex items-center gap-1.5">
          <Eye size={10} />
          FOCUS MODE
        </div>
      )}
    </div>
  )
}

/* ──────────────────────────────────────────────
   Graph Panel — exported wrapper with safety layers
   ────────────────────────────────────────────── */
interface GraphPanelProps {
  initialNodes: Node[]
  initialEdges: Edge[]
}

export default function GraphPanel({ initialNodes, initialEdges }: GraphPanelProps) {
  return (
    <GraphErrorBoundary fallbackNodes={initialNodes} fallbackEdges={initialEdges}>
      <ReactFlowProvider>
        <FlowInner initialNodes={initialNodes} initialEdges={initialEdges} />
      </ReactFlowProvider>
    </GraphErrorBoundary>
  )
}
