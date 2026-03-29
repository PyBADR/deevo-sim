'use client'
import { useState, useCallback, Component, type ReactNode } from 'react'
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type ReactFlowInstance,
  Handle,
  Position,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Eye, EyeOff, AlertTriangle } from 'lucide-react'
import { getNodeColor } from '@/lib/utils'

/* ──────────────────────────────────────────────
   Error Boundary — catches React Flow crashes
   ────────────────────────────────────────────── */
interface EBProps { children: ReactNode; fallback: ReactNode }
interface EBState { hasError: boolean }

class GraphErrorBoundary extends Component<EBProps, EBState> {
  constructor(props: EBProps) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    if (this.state.hasError) return this.props.fallback
    return this.props.children
  }
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
   Static fallback when React Flow crashes
   ────────────────────────────────────────────── */
function StaticGraphFallback({ nodes }: { nodes: Node[] }) {
  return (
    <div className="w-full h-full bg-ds-surface rounded-ds-xl border border-ds-border overflow-hidden relative">
      <div className="ds-panel-header">
        <div className="ds-panel-header-title">
          <div className="w-2 h-2 rounded-full bg-ds-warning" />
          <span className="text-caption font-semibold text-ds-text tracking-tight">Entity Graph</span>
          <span className="text-nano text-ds-text-dim font-mono ml-1">STATIC</span>
        </div>
      </div>
      <div className="h-[calc(100%-52px)] relative">
        <svg viewBox="0 0 800 500" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          <defs>
            <radialGradient id="nodeGlow">
              <stop offset="0%" stopColor="#6C63FF" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#6C63FF" stopOpacity="0" />
            </radialGradient>
          </defs>
          {nodes.map((node, i) => {
            const x = node.position?.x ?? 100 + (i % 4) * 180
            const y = node.position?.y ?? 80 + Math.floor(i / 4) * 160
            const color = getNodeColor(node.data?.type as string || 'Topic')
            const r = 20 + (node.data?.weight as number || 0.5) * 15
            return (
              <g key={node.id}>
                <circle cx={x} cy={y} r={r * 2} fill="url(#nodeGlow)" opacity="0.4" />
                <circle cx={x} cy={y} r={r} fill={`${color}20`} stroke={`${color}55`} strokeWidth="1.5" />
                <circle cx={x} cy={y} r={3} fill={color} />
                <text x={x} y={y + r + 14} textAnchor="middle" fill="#8A8AA0" fontSize="9" fontFamily="monospace">
                  {node.data?.label as string}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}

/* ──────────────────────────────────────────────
   Inner Flow — separated so hooks run inside Provider
   ────────────────────────────────────────────── */
interface FlowInnerProps {
  initialNodes: Node[]
  initialEdges: Edge[]
}

function FlowInner({ initialNodes, initialEdges }: FlowInnerProps) {
  const safeNodes = initialNodes.map(n => ({
    ...n,
    position: n.position ?? { x: 0, y: 0 },
    width: 80,
    height: 80,
  }))

  const [nodes, , onNodesChange] = useNodesState(safeNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)
  const [focusMode, setFocusMode] = useState(false)

  const onInit = useCallback((instance: ReactFlowInstance) => {
    setTimeout(() => {
      try { instance.fitView({ padding: 0.35 }) } catch {}
    }, 100)
  }, [])

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

      {/* Graph — no MiniMap to avoid premature bounds computation */}
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
   Graph Panel — wrapped with Provider + ErrorBoundary
   ────────────────────────────────────────────── */
interface GraphPanelProps {
  initialNodes: Node[]
  initialEdges: Edge[]
}

export default function GraphPanel({ initialNodes, initialEdges }: GraphPanelProps) {
  return (
    <GraphErrorBoundary fallback={<StaticGraphFallback nodes={initialNodes} />}>
      <ReactFlowProvider>
        <FlowInner initialNodes={initialNodes} initialEdges={initialEdges} />
      </ReactFlowProvider>
    </GraphErrorBoundary>
  )
}
