'use client'
import { motion } from 'framer-motion'
import { FileText, AlertTriangle, Users, BarChart3, Target, Shield, ChevronRight } from 'lucide-react'
import { formatConfidence, getSpreadBg } from '@/lib/utils'

interface Report {
  prediction: string
  main_driver: string
  top_influencers: string[]
  spread_level: string
  confidence: number
  timeline_summary: string[]
  graph_observations: string[]
}

interface ReportPanelProps {
  report: Report | null
}

export default function ReportPanel({ report }: ReportPanelProps) {
  if (!report) {
    return (
      <div className="bg-ds-surface rounded-ds-xl border border-ds-border p-6">
        <div className="ds-panel-header-title mb-4">
          <FileText size={14} className="text-ds-text-dim" />
          <span className="text-caption font-semibold text-ds-text-dim">Intelligence Brief</span>
        </div>
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <div className="w-10 h-10 rounded-full bg-ds-surface-raised border border-ds-border flex items-center justify-center mb-3">
            <Shield size={16} className="text-ds-text-dim" />
          </div>
          <p className="text-caption text-ds-text-dim">Run a simulation to generate intelligence brief</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }} className="bg-ds-surface rounded-ds-xl border border-ds-border overflow-hidden">
      <div className="ds-panel-header">
        <div className="ds-panel-header-title">
          <FileText size={14} className="text-ds-accent" />
          <span className="text-caption font-semibold text-ds-text tracking-tight">Intelligence Brief</span>
        </div>
        <span className="text-nano font-mono text-ds-text-dim uppercase tracking-wider">Classified</span>
      </div>
      <div className="p-5 space-y-5">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-ds-card rounded-ds-lg p-4 border border-ds-border">
          <div className="flex items-center gap-2 mb-2.5">
            <Target size={12} className="text-ds-accent" />
            <span className="text-nano font-semibold text-ds-accent uppercase tracking-[0.12em]">Prediction</span>
          </div>
          <p className="text-caption text-ds-text leading-relaxed">{report.prediction}</p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={11} className="text-ds-warning" />
            <span className="text-nano font-semibold text-ds-text-secondary uppercase tracking-[0.12em]">Key Driver</span>
          </div>
          <p className="text-caption text-ds-text-secondary leading-relaxed">{report.main_driver}</p>
        </motion.div>

        <div className="ds-divider" />

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="grid grid-cols-2 gap-3">
          <div className="bg-ds-card rounded-ds-lg p-4 border border-ds-border">
            <span className="text-nano text-ds-text-dim block mb-2 uppercase tracking-wider font-medium">Spread Level</span>
            <span className={`px-2 py-0.5 rounded text-micro font-bold uppercase ${getSpreadBg(report.spread_level)}`}>{report.spread_level}</span>
          </div>
          <div className="bg-ds-card rounded-ds-lg p-4 border border-ds-border">
            <span className="text-nano text-ds-text-dim block mb-2 uppercase tracking-wider font-medium">Confidence</span>
            <span className="text-h4 font-bold text-ds-accent font-mono">{formatConfidence(report.confidence)}</span>
            <div className="mt-2 h-1 bg-ds-border rounded-full overflow-hidden">
              <div className="h-full bg-ds-accent rounded-full transition-all duration-700" style={{ width: `${report.confidence * 100}%` }} />
            </div>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
          <div className="flex items-center gap-2 mb-3">
            <Users size={11} className="text-ds-accent" />
            <span className="text-nano font-semibold text-ds-text-secondary uppercase tracking-[0.12em]">Top Influencers</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {report.top_influencers.map((inf, i) => (
              <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 text-micro bg-ds-card border border-ds-border rounded-full text-ds-text-secondary font-mono hover:border-ds-border-hover hover:text-ds-text transition-all cursor-default">
                <span className="w-1.5 h-1.5 rounded-full bg-ds-accent/40" />
                {inf}
              </span>
            ))}
          </div>
        </motion.div>

        <div className="ds-divider" />

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 size={11} className="text-ds-accent" />
            <span className="text-nano font-semibold text-ds-text-secondary uppercase tracking-[0.12em]">Key Observations</span>
          </div>
          <div className="space-y-2">
            {report.graph_observations.map((obs, i) => (
              <div key={i} className="flex items-start gap-2.5 text-caption text-ds-text-muted">
                <ChevronRight size={12} className="text-ds-accent/50 mt-0.5 flex-shrink-0" />
                <span className="leading-relaxed">{obs}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
            }
