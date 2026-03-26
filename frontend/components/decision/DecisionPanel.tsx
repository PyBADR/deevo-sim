'use client'

import { motion } from 'framer-motion'
import {
  AlertTriangle, TrendingUp, Clock, Shield,
  ChevronRight, Zap, Eye, MessageSquare
} from 'lucide-react'
import type { DecisionOutput } from '@/lib/types'

interface DecisionPanelProps {
  decision: DecisionOutput
  isActive: boolean
}

const riskColors: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  LOW: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30', glow: 'shadow-emerald-500/20' },
  MEDIUM: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30', glow: 'shadow-amber-500/20' },
  HIGH: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30', glow: 'shadow-orange-500/20' },
  CRITICAL: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30', glow: 'shadow-red-500/20' },
}

const sentimentIcons: Record<string, string> = {
  positive: '↑',
  negative: '↓',
  mixed: '↔',
  neutral: '•',
}

const priorityColors: Record<string, string> = {
  immediate: 'text-red-400 bg-red-500/10 border-red-500/20',
  'short-term': 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  monitoring: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
}

export default function DecisionPanel({ decision, isActive }: DecisionPanelProps) {
  if (!isActive) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-600">
        <div className="text-center">
          <Shield className="w-8 h-8 mx-auto mb-3 opacity-40" />
          <p className="text-sm">Run a simulation to generate</p>
          <p className="text-sm">decision intelligence output</p>
        </div>
      </div>
    )
  }

  const risk = riskColors[decision.riskLevel] || riskColors.MEDIUM

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-full overflow-y-auto space-y-4 pr-1 custom-scrollbar"
    >
      {/* Scenario Narrative Header */}
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <p className="text-[10px] uppercase tracking-widest text-indigo-400 mb-1">
          {decision.narrative.subtitle}
        </p>
        <h3 className="text-sm font-semibold text-zinc-100 mb-2">
          {decision.narrative.title}
        </h3>
        <p className="text-xs text-zinc-400 leading-relaxed">
          {decision.narrative.summary}
        </p>
      </div>

      {/* Risk + Spread + Sentiment Row */}
      <div className="grid grid-cols-3 gap-2">
        <div className={`border rounded-lg p-3 text-center ${risk.bg} ${risk.border}`}>
          <AlertTriangle className={`w-4 h-4 mx-auto mb-1 ${risk.text}`} />
          <p className="text-[10px] uppercase tracking-wider text-zinc-500">Risk</p>
          <p className={`text-lg font-bold ${risk.text}`}>{decision.riskLevel}</p>
        </div>
        <div className="border border-zinc-800 rounded-lg p-3 text-center bg-zinc-900/50">
          <TrendingUp className="w-4 h-4 mx-auto mb-1 text-indigo-400" />
          <p className="text-[10px] uppercase tracking-wider text-zinc-500">Spread</p>
          <p className="text-lg font-bold text-indigo-400">{decision.expectedSpread}%</p>
        </div>
        <div className="border border-zinc-800 rounded-lg p-3 text-center bg-zinc-900/50">
          <Eye className="w-4 h-4 mx-auto mb-1 text-zinc-400" />
          <p className="text-[10px] uppercase tracking-wider text-zinc-500">Sentiment</p>
          <p className="text-lg font-bold text-zinc-200">
            {sentimentIcons[decision.sentiment]} {decision.sentiment}
          </p>
        </div>
      </div>

      {/* Primary Driver */}
      <div className="border border-zinc-800 rounded-lg p-3 bg-zinc-900/50">
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-[10px] uppercase tracking-wider text-zinc-500">Primary Driver</span>
        </div>
        <p className="text-sm text-zinc-200">{decision.primaryDriver}</p>
      </div>

      {/* Critical Time Window */}
      <div className={`border rounded-lg p-3 ${risk.bg} ${risk.border}`}>
        <div className="flex items-center gap-2 mb-1">
          <Clock className={`w-3.5 h-3.5 ${risk.text}`} />
          <span className="text-[10px] uppercase tracking-wider text-zinc-500">Critical Window</span>
        </div>
        <p className={`text-sm font-medium ${risk.text}`}>{decision.criticalTimeWindow}</p>
      </div>

      {/* WHY — Explainability Section */}
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center gap-2 mb-3">
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Why This Outcome
          </h4>
        </div>
        <div className="space-y-2.5">
          {decision.explanation.map((item, i) => (
            <div key={i} className="flex items-start gap-2">
              <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${
                item.direction === 'amplifying' ? 'bg-red-400' :
                item.direction === 'dampening' ? 'bg-emerald-400' : 'bg-zinc-500'
              }`} />
              <div>
                <p className="text-xs font-medium text-zinc-200">{item.factor}</p>
                <p className="text-[11px] text-zinc-500 leading-relaxed">{item.description}</p>
                <div className="mt-1 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      item.direction === 'amplifying' ? 'bg-red-500/60' : 'bg-emerald-500/60'
                    }`}
                    style={{ width: (item.weight * 100) + '%' }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Actions */}
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Recommended Actions
          </h4>
        </div>
        <div className="space-y-2">
          {decision.recommendedActions.map((action) => (
            <div
              key={action.id}
              className="flex items-start gap-2 p-2 rounded-md bg-zinc-800/40"
            >
              <span className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded border shrink-0 mt-0.5 ${priorityColors[action.priority]}`}>
                {action.priority === 'short-term' ? 'SHORT' : action.priority}
              </span>
              <div>
                <p className="text-xs text-zinc-200">{action.action}</p>
                <p className="text-[10px] text-zinc-500 mt-0.5">
                  {action.rationale}
                </p>
                <span className="text-[10px] text-zinc-600">{action.timeframe}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
  }
