'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  FileText, Search, GitBranch, Users, Zap, MessageSquare,
  ChevronRight, Layers, BarChart3, Bot, Database, Code2, Terminal,
} from 'lucide-react';
import Navbar from '@/components/ui/Navbar';
import Footer from '@/components/ui/Footer';
import SectionHeading from '@/components/ui/SectionHeading';

export default function ArchitecturePage() {
  const pipelineNodes = [
    { label: 'Input', icon: FileText },
    { label: 'Parse', icon: Search },
    { label: 'Extract', icon: Database },
    { label: 'Graph', icon: GitBranch },
    { label: 'Simulate', icon: Zap },
    { label: 'Report', icon: BarChart3 },
    { label: 'Analyst', icon: Bot },
  ];

  const architectureBlocks = [
    { step: '01', icon: FileText, title: 'Scenario Input', description: 'The entry point of the pipeline. Users provide real-world scenarios in Arabic or English \u2014 news events, policy changes, market shifts \u2014 forming the seed for the entire simulation.', features: ['Multi-language (AR/EN)', 'Preset library', 'Custom metadata', 'Auto-detection'], tech: ['Next.js', 'FastAPI', 'Pydantic'] },
    { step: '02', icon: Search, title: 'Entity Extraction', description: 'Raw text is parsed to identify key entities \u2014 people, organizations, topics, regions, platforms, and events. Each entity is weighted by relevance and classified.', features: ['8+ entity types', 'Relevance scoring', 'Arabic NLP-ready', 'Relationship hints'], tech: ['Python', 'NLP Pipeline', 'Pydantic'] },
    { step: '03', icon: GitBranch, title: 'Relationship Graph', description: 'Entities are connected through relationships \u2014 influence, amplification, reaction, regulation \u2014 forming a directed graph modeling real-world dynamics.', features: ['Directed mapping', 'Interactive visualization', 'Weighted edges', '6 relation types'], tech: ['React Flow', 'In-memory Graph', 'D3-ready'] },
    { step: '04', icon: Users, title: 'Agent Generation', description: 'GCC-specific personas populate the simulation \u2014 Saudi citizens, Kuwaiti citizens, influencers, media accounts, government voices, and youth users.', features: ['6 GCC archetypes', 'Influence scoring', 'Behavioral profiling', 'Platform-specific'], tech: ['FastAPI', 'Agent Models', 'JSON Seeds'] },
    { step: '05', icon: Zap, title: 'Simulation Engine', description: 'Agents interact over 4 time steps. Negative events spread faster, high-influence agents amplify reach, official responses reduce intensity.', features: ['4-step temporal model', 'Rule-based engine', 'Sentiment drift', 'Visibility scoring'], tech: ['Python', 'Rule Engine', 'Async Pipeline'] },
    { step: '06', icon: MessageSquare, title: 'Intelligence Brief', description: 'Structured prediction report with confidence scoring, spread analysis, key drivers. Users can query the simulation results through the analyst interface.', features: ['JSON reports', 'Confidence scoring', 'Analyst queries', 'Explainable AI'], tech: ['FastAPI', 'Next.js', 'React'] },
  ];

  const dataFlowItems = [
    { input: 'Raw Text', icon: FileText, output: 'Normalized Scenario' },
    { input: 'Scenario', icon: Search, output: 'Entity List' },
    { input: 'Entities', icon: GitBranch, output: 'Graph Structure' },
    { input: 'Graph', icon: Users, output: 'Agent Profiles' },
    { input: 'Agents + Graph', icon: Zap, output: 'Simulation Steps' },
    { input: 'Steps', icon: BarChart3, output: 'Intelligence Brief' },
    { input: 'Brief + Context', icon: Bot, output: 'Analyst Response' },
  ];

  const frontendTechs = ['Next.js 14', 'TypeScript', 'Tailwind CSS', 'Framer Motion', 'React Flow', 'Lucide'];
  const backendTechs = ['FastAPI', 'Python 3.11+', 'Pydantic v2', 'Async Services', 'JSON Seeds'];

  return (
    <div className="bg-ds-bg min-h-screen flex flex-col">
      <Navbar />

      <motion.section className="pt-34 pb-22 bg-ds-bg relative overflow-hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
        <div className="absolute inset-0 ds-grid-bg opacity-30" />
        <div className="ds-container text-center relative z-10">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, duration: 0.5 }}>
            <span className="ds-badge-accent inline-flex items-center gap-1.5 mb-6"><Layers className="w-3.5 h-3.5" />Architecture</span>
          </motion.div>
          <motion.h1 initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.5 }} className="text-display-sm lg:text-display text-ds-text font-bold">System Architecture</motion.h1>
          <motion.p initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.5 }} className="text-body-lg text-ds-text-secondary max-w-3xl mx-auto mt-6">A 7-layer intelligence pipeline from raw scenario input to predictive simulation and interactive analysis.</motion.p>
        </div>
      </motion.section>

      <motion.section className="ds-section-tight bg-ds-bg" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <h2 className="text-h3 text-center mb-12 text-ds-text">Pipeline Overview</h2>
          <div className="hidden lg:flex items-center justify-center gap-0">
            {pipelineNodes.map((node, idx) => {
              const Icon = node.icon;
              return (
                <div key={idx} className="flex items-center">
                  <motion.div className="w-28 flex flex-col items-center" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.08 }} viewport={{ once: true }}>
                    <div className={`w-14 h-14 rounded-full flex items-center justify-center border transition-all duration-300 ${idx === 0 ? 'bg-ds-accent-muted border-ds-accent/25 shadow-ds-glow' : 'bg-ds-card border-ds-border'}`}>
                      <Icon className="w-5 h-5 text-ds-accent" />
                    </div>
                    <p className="text-micro text-ds-text-secondary mt-3 text-center font-medium">{node.label}</p>
                  </motion.div>
                  {idx < pipelineNodes.length - 1 && (<ChevronRight className="w-4 h-4 text-ds-text-dim mx-1" />)}
                </div>
              );
            })}
          </div>
          <div className="lg:hidden flex flex-col items-center gap-4">
            {pipelineNodes.map((node, idx) => {
              const Icon = node.icon;
              return (
                <div key={idx} className="flex flex-col items-center">
                  <motion.div className="flex flex-col items-center" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.08 }} viewport={{ once: true }}>
                    <div className={`w-14 h-14 rounded-full flex items-center justify-center border ${idx === 0 ? 'bg-ds-accent-muted border-ds-accent/25' : 'bg-ds-card border-ds-border'}`}>
                      <Icon className="w-5 h-5 text-ds-accent" />
                    </div>
                    <p className="text-micro text-ds-text-secondary mt-2">{node.label}</p>
                  </motion.div>
                </div>
              );
            })}
          </div>
        </div>
      </motion.section>

      <motion.section className="ds-section bg-ds-bg-alt" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <SectionHeading tag="Deep Dive" title="Pipeline Architecture" subtitle="Each stage processes, transforms, and enriches the scenario data as it flows through the system." />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {architectureBlocks.map((block, idx) => {
              const Icon = block.icon;
              return (
                <motion.div key={idx} className="ds-card p-8" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.08, duration: 0.5 }} viewport={{ once: true }}>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-nano font-mono text-ds-accent-dim">{block.step}</span>
                    <div className="w-10 h-10 rounded-ds bg-ds-accent-muted flex items-center justify-center"><Icon className="w-[18px] h-[18px] text-ds-accent" /></div>
                    <h3 className="text-h4 text-ds-text">{block.title}</h3>
                  </div>
                  <p className="text-caption text-ds-text-secondary leading-relaxed">{block.description}</p>
                  <div className="mt-5 grid grid-cols-2 gap-2.5">
                    {block.features.map((feature, fidx) => (<div key={fidx} className="flex items-center gap-2 text-micro text-ds-text-muted"><div className="w-1 h-1 rounded-full bg-ds-accent-dim flex-shrink-0" />{feature}</div>))}
                  </div>
                  <div className="mt-5 flex flex-wrap gap-1.5">
                    {block.tech.map((tech, tidx) => (<span key={tidx} className="text-nano font-mono px-2.5 py-1 bg-ds-bg-alt border border-ds-border-subtle rounded-md text-ds-text-dim">{tech}</span>))}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </motion.section>

      <motion.section className="ds-section bg-ds-bg" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <SectionHeading tag="Data Flow" title="Source \u2192 Transform \u2192 Sink" />
          <div className="flex flex-col items-center gap-0 mt-12">
            {dataFlowItems.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div key={idx} className="w-full">
                  <motion.div className="flex items-center justify-center gap-8" initial={{ opacity: 0, x: -16 }} whileInView={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.08, duration: 0.5 }} viewport={{ once: true }}>
                    <span className="text-micro font-mono text-ds-text-dim w-24 sm:w-36 text-right truncate">{item.input}</span>
                    <div className="w-11 h-11 rounded-full bg-ds-card border border-ds-border flex items-center justify-center flex-shrink-0"><Icon className="w-4 h-4 text-ds-accent" /></div>
                    <span className="text-micro font-mono text-ds-text-muted w-28 sm:w-48">{item.output}</span>
                  </motion.div>
                  {idx < dataFlowItems.length - 1 && (<div className="flex justify-center py-2"><div className="w-px h-8 bg-ds-border" /></div>)}
                </div>
              );
            })}
          </div>
        </div>
      </motion.section>

      <motion.section className="ds-section-tight bg-ds-bg-alt" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container">
          <SectionHeading tag="Stack" title="Technology" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <motion.div className="ds-card p-8" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, duration: 0.5 }} viewport={{ once: true }}>
              <div className="flex items-center gap-2.5 mb-6"><Code2 className="w-5 h-5 text-ds-accent" /><h3 className="text-h4 text-ds-text">Frontend</h3></div>
              <div className="flex flex-wrap gap-2.5">{frontendTechs.map((tech, idx) => (<span key={idx} className="text-micro px-3 py-1.5 bg-ds-surface-raised border border-ds-border rounded-ds text-ds-text-secondary">{tech}</span>))}</div>
            </motion.div>
            <motion.div className="ds-card p-8" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.15, duration: 0.5 }} viewport={{ once: true }}>
              <div className="flex items-center gap-2.5 mb-6"><Terminal className="w-5 h-5 text-ds-accent" /><h3 className="text-h4 text-ds-text">Backend</h3></div>
              <div className="flex flex-wrap gap-2.5">{backendTechs.map((tech, idx) => (<span key={idx} className="text-micro px-3 py-1.5 bg-ds-surface-raised border border-ds-border rounded-ds text-ds-text-secondary">{tech}</span>))}</div>
            </motion.div>
          </div>
        </div>
      </motion.section>

      <motion.section className="ds-section-tight bg-ds-bg" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
        <div className="ds-container text-center">
          <motion.h2 className="text-h2 text-ds-text" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, duration: 0.5 }} viewport={{ once: true }}>See It in Action</motion.h2>
          <motion.p className="text-body-lg text-ds-text-secondary mt-4 max-w-xl mx-auto" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.5 }} viewport={{ once: true }}>Experience the full pipeline from scenario input to predictive intelligence.</motion.p>
          <motion.div className="flex items-center justify-center gap-4 mt-10" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.5 }} viewport={{ once: true }}>
            <Link href="/demo" className="ds-btn-primary text-[15px] px-8 py-4">Launch System</Link>
            <Link href="/" className="ds-btn-secondary text-[15px] px-8 py-4">Back to Home</Link>
          </motion.div>
        </div>
      </motion.section>

      <Footer />
    </div>
  );
}
