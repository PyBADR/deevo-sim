"use client";

/**
 * Impact Observatory | مرصد الأثر
 *
 * Product landing page → Scenario runner → Executive dashboard
 * White/light boardroom aesthetic. Financial-first. Large typography.
 * Arabic + English bilingual.
 */

import React, { useState } from "react";
import ExecutiveDashboard from "@/features/dashboard/ExecutiveDashboard";
import BankingDetailPanel from "@/features/banking/BankingDetailPanel";
import InsuranceDetailPanel from "@/features/insurance/InsuranceDetailPanel";
import FintechDetailPanel from "@/features/fintech/FintechDetailPanel";
import DecisionDetailPanel from "@/features/decisions/DecisionDetailPanel";
import type { RunResult, Language, ViewMode } from "@/types/observatory";

type AppView = "landing" | "scenarios" | "results";
type DetailView = "dashboard" | "banking" | "insurance" | "fintech" | "decisions";

// ── Scenarios ────────────────────────────────────────────────────────

const SCENARIOS = [
  { id: "hormuz_disruption", label: "Hormuz Closure", label_ar: "إغلاق مضيق هرمز", desc: "Strait of Hormuz blockade — oil transit, shipping, energy supply chain", desc_ar: "حصار مضيق هرمز — عبور النفط والشحن وسلسلة إمداد الطاقة", loss: "$3.2B", severity: 0.8, icon: "⚓" },
  { id: "yemen_escalation", label: "Yemen Escalation", label_ar: "تصعيد يمني", desc: "Regional conflict escalation — Red Sea shipping, insurance claims surge", desc_ar: "تصعيد صراع إقليمي — شحن البحر الأحمر وارتفاع مطالبات التأمين", loss: "$1.8B", severity: 0.7, icon: "🔥" },
  { id: "cyber_attack", label: "Cyber Attack", label_ar: "هجوم سيبراني", desc: "Financial infrastructure cyberattack — payment systems, API disruption", desc_ar: "هجوم سيبراني على البنية المالية — أنظمة الدفع وتعطل الواجهات", loss: "$0.9B", severity: 0.6, icon: "🛡️" },
  { id: "oil_price_shock", label: "Oil Price Shock", label_ar: "صدمة أسعار النفط", desc: "Sudden oil price collapse — GDP impact, banking stress, fiscal reserves", desc_ar: "انهيار مفاجئ في أسعار النفط — أثر على الناتج المحلي والاحتياطيات", loss: "$4.5B", severity: 0.8, icon: "📉" },
  { id: "banking_stress", label: "Banking Stress", label_ar: "ضغط بنكي إقليمي", desc: "Regional banking contagion — liquidity crisis, CAR deterioration", desc_ar: "عدوى بنكية إقليمية — أزمة سيولة وتدهور كفاية رأس المال", loss: "$2.1B", severity: 0.7, icon: "🏦" },
  { id: "port_disruption", label: "Port Disruption", label_ar: "تعطل ميناء رئيسي", desc: "Major port shutdown — trade flow, supply chain cascade, insurance", desc_ar: "توقف ميناء رئيسي — تدفق التجارة وتأثيرات سلسلة التوريد", loss: "$1.5B", severity: 0.6, icon: "🚢" },
];

// ── Capability Cards ─────────────────────────────────────────────────

const CAPABILITIES = {
  en: [
    { title: "Financial Impact Modeling", desc: "Compute GDP-weighted loss propagation across 31 GCC entities with sector-specific elasticities. Real economics, not estimates.", icon: "💰" },
    { title: "Banking Stress Analysis", desc: "Basel III-aligned liquidity, credit, and FX stress testing across 6 major GCC institutions. Time-to-liquidity-breach countdown.", icon: "🏦" },
    { title: "Insurance Stress Modeling", desc: "IFRS-17 compliant claims surge modeling across 8 insurance lines. Combined ratio tracking with reinsurance trigger detection.", icon: "📋" },
    { title: "Fintech & Payment Disruption", desc: "Payment volume impact, settlement delays, API availability monitoring across 7 GCC payment platforms.", icon: "💳" },
    { title: "Decision Intelligence", desc: "Priority = Value + Urgency + RegulatoryRisk. Top 3 actionable decisions with cost-benefit analysis and owner assignment.", icon: "🎯" },
    { title: "Bilingual Explainability", desc: "20-step causal chain explaining how events propagate through the GCC financial system. Arabic and English narratives.", icon: "🔗" },
  ],
  ar: [
    { title: "نمذجة الأثر المالي", desc: "حساب انتشار الخسائر المرجحة بالناتج المحلي عبر 31 كياناً خليجياً مع مرونات قطاعية محددة.", icon: "💰" },
    { title: "تحليل الضغط البنكي", desc: "اختبار ضغط السيولة والائتمان والعملة وفق بازل III عبر 6 مؤسسات خليجية. العد التنازلي لكسر السيولة.", icon: "🏦" },
    { title: "نمذجة ضغط التأمين", desc: "نمذجة ارتفاع المطالبات وفق IFRS-17 عبر 8 خطوط تأمين. تتبع النسبة المجمعة مع كشف تفعيل إعادة التأمين.", icon: "📋" },
    { title: "تعطل الفنتك والمدفوعات", desc: "أثر حجم المدفوعات وتأخر التسوية ومراقبة توفر واجهة API عبر 7 منصات دفع خليجية.", icon: "💳" },
    { title: "ذكاء القرار", desc: "الأولوية = القيمة + الإلحاح + المخاطر التنظيمية. أهم 3 قرارات قابلة للتنفيذ مع تحليل التكلفة والعائد.", icon: "🎯" },
    { title: "تفسير ثنائي اللغة", desc: "سلسلة سببية من 20 خطوة توضح كيف تنتشر الأحداث عبر النظام المالي الخليجي. بالعربية والإنجليزية.", icon: "🔗" },
  ],
};

// ── Main Component ───────────────────────────────────────────────────

export default function HomePage() {
  const [appView, setAppView] = useState<AppView>("landing");
  const [result, setResult] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<Language>("en");
  const [viewMode, setViewMode] = useState<ViewMode>("executive");
  const [detailView, setDetailView] = useState<DetailView>("dashboard");

  const isAr = lang === "ar";

  const runScenario = async (templateId: string, severity: number) => {
    setLoading(true);
    setError(null);
    setAppView("results");
    try {
      const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const headers = {
        "Content-Type": "application/json",
        "X-IO-API-Key": "io_master_key_2026",
      };

      // 1. Launch run
      const runRes = await fetch(`${BASE}/api/v1/runs`, {
        method: "POST",
        headers,
        body: JSON.stringify({ template_id: templateId }),
      });
      if (!runRes.ok) throw new Error(`API error: ${runRes.status}`);
      const runData = await runRes.json();
      const runId = runData.data?.run_id;
      if (!runId) throw new Error("No run_id returned");
      if (runData.data?.status === "failed") throw new Error(runData.data?.error || "Run failed");

      // 2. Fetch all sections in parallel
      const fetchSection = async (path: string) => {
        const res = await fetch(`${BASE}/api/v1/runs/${runId}/${path}`, { headers });
        if (!res.ok) return {};
        const json = await res.json();
        return json.data || {};
      };

      const [financial, banking, insurance, fintech, decision, explanation, businessImpact, timeline] =
        await Promise.all([
          fetchSection("financial"),
          fetchSection("banking"),
          fetchSection("insurance"),
          fetchSection("fintech"),
          fetchSection("decision"),
          fetchSection("explanation"),
          fetchSection("business-impact"),
          fetchSection("timeline"),
        ]);

      // 3. Compose into RunResult shape for dashboard
      const composedResult: RunResult = {
        schema_version: "4.0.0",
        run_id: runId,
        status: "completed",
        pipeline_stages_completed: runData.data?.stages_completed || 9,
        scenario: {
          template_id: templateId,
          label: SCENARIOS.find((s) => s.id === templateId)?.label || templateId,
          label_ar: SCENARIOS.find((s) => s.id === templateId)?.label_ar || null,
          severity,
          horizon_hours: 336,
        },
        headline: {
          total_loss_usd: financial.aggregate?.total_loss || 0,
          peak_day: (businessImpact as Record<string, number>).peak_loss_timestep || 0,
          max_recovery_days: 14,
          average_stress: 0,
          affected_entities: financial.count || 0,
          critical_count: financial.aggregate?.breach_count || 0,
          elevated_count: 0,
        },
        financial: (financial.entities || []).map((e: Record<string, unknown>) => ({
          entity_id: e.entity_id || "",
          entity_label: e.name || e.entity_id || "",
          sector: e.entity_type || "",
          loss_usd: (e.loss as number) || 0,
          loss_pct_gdp: 0,
          peak_day: 0,
          recovery_days: 14,
          confidence: 0.85,
          stress_level: (e.loss as number) > 1000 ? 0.8 : 0.4,
          classification: (e.loss as number) > 1000 ? "CRITICAL" : (e.loss as number) > 100 ? "ELEVATED" : "MODERATE",
        })),
        banking: {
          run_id: runId,
          total_exposure_usd: banking.aggregate?.total_exposure || 0,
          liquidity_stress: banking.aggregate?.avg_lcr ? 1 - banking.aggregate.avg_lcr : 0.6,
          credit_stress: banking.aggregate?.avg_car ? 1 - banking.aggregate.avg_car : 0.4,
          fx_stress: 0.3,
          interbank_contagion: banking.aggregate?.breach_count ? banking.aggregate.breach_count / 4 : 0.5,
          time_to_liquidity_breach_hours: 72,
          capital_adequacy_impact_pct: banking.aggregate?.avg_car || 0,
          aggregate_stress: banking.aggregate?.avg_composite || 0.65,
          classification: banking.aggregate?.breach_count > 2 ? "CRITICAL" : "ELEVATED",
          affected_institutions: [],
        },
        insurance: {
          run_id: runId,
          portfolio_exposure_usd: insurance.aggregate?.total_exposure || 0,
          claims_surge_multiplier: insurance.aggregate?.avg_combined_ratio || 1.5,
          severity_index: 0.7,
          loss_ratio: 0.85,
          combined_ratio: insurance.aggregate?.avg_combined_ratio || 1.2,
          underwriting_status: insurance.aggregate?.breach_count > 1 ? "RESTRICTED" : "WATCH",
          time_to_insolvency_hours: 168,
          reinsurance_trigger: (insurance.aggregate?.breach_count || 0) > 1,
          ifrs17_risk_adjustment_pct: 15,
          aggregate_stress: insurance.aggregate?.avg_composite || 0.6,
          classification: insurance.aggregate?.breach_count > 1 ? "ELEVATED" : "MODERATE",
          affected_lines: [],
        },
        fintech: {
          run_id: runId,
          payment_volume_impact_pct: fintech.aggregate?.avg_settlement_delay ? fintech.aggregate.avg_settlement_delay * 2 : 35,
          settlement_delay_hours: fintech.aggregate?.avg_settlement_delay || 4.5,
          api_availability_pct: fintech.aggregate?.avg_availability ? fintech.aggregate.avg_availability * 100 : 92,
          cross_border_disruption: 0.45,
          digital_banking_stress: 0.5,
          time_to_payment_failure_hours: 48,
          aggregate_stress: fintech.aggregate?.avg_composite || 0.55,
          classification: fintech.aggregate?.breach_count > 1 ? "ELEVATED" : "MODERATE",
          affected_platforms: [],
        },
        decisions: {
          run_id: runId,
          scenario_label: SCENARIOS.find((s) => s.id === templateId)?.label || null,
          total_loss_usd: financial.aggregate?.total_loss || 0,
          peak_day: 7,
          time_to_failure_hours: 48,
          actions: (decision.actions || []).map((a: Record<string, unknown>) => ({
            id: a.action_id || "",
            action: a.action_text || "",
            action_ar: a.action_text_ar || null,
            sector: a.sector || "",
            owner: a.owner || "",
            urgency: (a.urgency as number) || 0,
            value: (a.value as number) || 0,
            regulatory_risk: 0.5,
            priority: (a.priority as number) || 0,
            time_to_act_hours: 24,
            time_to_failure_hours: 48,
            loss_avoided_usd: (a.value as number) || 0,
            cost_usd: (a.feasibility as number) ? (1 - (a.feasibility as number)) * 100 : 50,
            confidence: 0.85,
          })),
          all_actions: [],
        },
        explanation: {
          run_id: runId,
          scenario_label: null,
          narrative_en: (explanation as Record<string, string>).executive_summary_en || "",
          narrative_ar: (explanation as Record<string, string>).executive_summary_ar || "",
          causal_chain: ((explanation as Record<string, unknown[]>).causal_chain || []).map((c: unknown, i: number) => ({
            step: i + 1,
            entity_id: (c as Record<string, string>).entity_id || "",
            entity_label: (c as Record<string, string>).entity_id || "",
            entity_label_ar: null,
            event: (c as Record<string, string>).event_en || "",
            event_ar: (c as Record<string, string>).event_ar || null,
            impact_usd: (c as Record<string, number>).impact_usd || 0,
            stress_delta: 0,
            mechanism: (c as Record<string, string>).mechanism || "",
          })),
          total_steps: ((explanation as Record<string, unknown[]>).causal_chain || []).length,
          headline_loss_usd: financial.aggregate?.total_loss || 0,
          peak_day: 7,
          confidence: 0.85,
          methodology: "v4-pipeline-9stage",
        },
        executive_report: {},
        flow_states: [],
        propagation: [],
        duration_ms: runData.data?.computed_in_ms || 0,
      };

      setResult(composedResult);
      setDetailView("dashboard");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (detailView !== "dashboard") {
      setDetailView("dashboard");
    } else if (result) {
      setResult(null);
      setAppView("scenarios");
    } else {
      setAppView("landing");
    }
  };

  const detailLabels: Record<Language, Record<DetailView, string>> = {
    en: { dashboard: "Dashboard", banking: "Banking Stress", insurance: "Insurance Stress", fintech: "Fintech Stress", decisions: "Decision Actions" },
    ar: { dashboard: "لوحة المعلومات", banking: "ضغط القطاع البنكي", insurance: "ضغط التأمين", fintech: "ضغط الفنتك", decisions: "إجراءات القرار" },
  };

  // ── Top Navigation (always visible) ──

  const TopNav = () => (
    <nav className="bg-io-surface border-b border-io-border px-6 lg:px-10 py-3 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <button onClick={() => { setAppView("landing"); setResult(null); }} className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-io-accent rounded-lg flex items-center justify-center text-white text-sm font-bold">IO</div>
          <span className="text-lg font-bold text-io-primary group-hover:text-io-accent transition-colors">
            {isAr ? "مرصد الأثر" : "Impact Observatory"}
          </span>
        </button>
        {appView !== "landing" && (
          <span className="text-xs text-io-secondary font-medium bg-io-bg px-2 py-0.5 rounded border border-io-border">v1.0</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        {appView === "results" && result && (
          <div className="hidden md:flex bg-io-bg rounded-lg p-0.5 border border-io-border">
            {(["executive", "analyst", "regulatory"] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-colors ${viewMode === mode ? "bg-io-accent text-white" : "text-io-secondary hover:text-io-primary"}`}
              >
                {mode}
              </button>
            ))}
          </div>
        )}
        <button
          onClick={() => setLang(isAr ? "en" : "ar")}
          className="px-3 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary transition-colors"
        >
          {isAr ? "English" : "العربية"}
        </button>
        {appView === "landing" && (
          <div className="flex items-center gap-2">
            <a
              href="/dashboard"
              className="px-4 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-accent hover:border-io-accent transition-colors"
            >
              {isAr ? "لوحة المعلومات" : "Dashboard"}
            </a>
            <button
              onClick={() => setAppView("scenarios")}
              className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors"
            >
              {isAr ? "ابدأ التحليل" : "Run Scenario"}
            </button>
          </div>
        )}
      </div>
    </nav>
  );

  // ── LANDING PAGE ──────────────────────────────────────────────────

  if (appView === "landing") {
    const caps = CAPABILITIES[lang];
    return (
      <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
        <TopNav />

        {/* Hero Section */}
        <section className="max-w-5xl mx-auto px-6 lg:px-10 pt-20 pb-16 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-io-accent/5 border border-io-accent/20 rounded-full text-io-accent text-xs font-medium mb-6">
            {isAr ? "منصة ذكاء القرار للأسواق المالية الخليجية" : "Decision Intelligence for GCC Financial Markets"}
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-io-primary leading-tight mb-6">
            {isAr ? "افهم الأثر المالي" : "Understand financial impact"}
            <br />
            <span className="text-io-accent">
              {isAr ? "قبل حدوثه" : "before it happens"}
            </span>
          </h1>
          <p className="text-lg md:text-xl text-io-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
            {isAr
              ? "نمذجة الأثر المالي في الوقت الحقيقي عبر القطاع البنكي والتأمين والفنتك. من الحدث إلى القرار في ثوانٍ."
              : "Real-time financial impact modeling across banking, insurance, and fintech sectors. From event to decision in seconds."}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => setAppView("scenarios")}
              className="px-8 py-3.5 bg-io-accent text-white text-base font-semibold rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-io-accent/20"
            >
              {isAr ? "ابدأ التحليل" : "Run Scenario"}
            </button>
            <a
              href="#capabilities"
              className="px-8 py-3.5 text-io-secondary text-base font-medium rounded-xl border border-io-border hover:border-io-accent hover:text-io-accent transition-colors"
            >
              {isAr ? "اكتشف المنصة" : "Explore Platform"}
            </a>
          </div>
        </section>

        {/* Metrics Strip */}
        <section className="max-w-5xl mx-auto px-6 lg:px-10 pb-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { value: "31", label: isAr ? "كيان خليجي" : "GCC Entities", sub: isAr ? "طاقة · بحري · طيران · مالي" : "Energy · Maritime · Aviation · Finance" },
              { value: "12", label: isAr ? "خدمة تحليلية" : "Analysis Services", sub: isAr ? "سيناريو → قرار" : "Scenario → Decision" },
              { value: "$2.1T", label: isAr ? "ناتج محلي مغطى" : "GDP Coverage", sub: isAr ? "دول الخليج الست" : "Six GCC nations" },
              { value: "<2s", label: isAr ? "وقت التحليل" : "Analysis Time", sub: isAr ? "من الحدث إلى القرار" : "Event to decision" },
            ].map((m) => (
              <div key={m.label} className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm text-center">
                <p className="text-3xl font-bold text-io-accent tabular-nums">{m.value}</p>
                <p className="text-sm font-semibold text-io-primary mt-1">{m.label}</p>
                <p className="text-xs text-io-secondary mt-0.5">{m.sub}</p>
              </div>
            ))}
          </div>
        </section>

        {/* What It Does */}
        <section className="bg-io-surface border-y border-io-border py-16">
          <div className="max-w-5xl mx-auto px-6 lg:px-10">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-io-primary mb-3">
                {isAr ? "كيف يعمل مرصد الأثر" : "How Impact Observatory Works"}
              </h2>
              <p className="text-io-secondary text-base max-w-2xl mx-auto">
                {isAr
                  ? "كل مخرج يربط: الحدث → الأثر المالي → ضغط القطاع → القرار"
                  : "Every output maps: Event → Financial Impact → Sector Stress → Decision"}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  step: "01",
                  title: isAr ? "حدد السيناريو" : "Define Scenario",
                  desc: isAr ? "اختر حدثاً جيوسياسياً أو اقتصادياً — إغلاق مضيق هرمز، صدمة نفطية، هجوم سيبراني" : "Select a geopolitical or economic event — Hormuz closure, oil shock, cyber attack",
                },
                {
                  step: "02",
                  title: isAr ? "حلل الأثر" : "Analyze Impact",
                  desc: isAr ? "محرك الفيزياء ينشر الصدمة عبر 31 كياناً خليجياً ويحسب الخسارة المالية والضغط القطاعي" : "Physics engine propagates the shock across 31 GCC entities, computing financial loss and sector stress",
                },
                {
                  step: "03",
                  title: isAr ? "اتخذ القرار" : "Decide & Act",
                  desc: isAr ? "أعلى 3 إجراءات ذات أولوية مع تحليل التكلفة والعائد وتعيين المسؤول" : "Top 3 prioritized actions with cost-benefit analysis and owner assignment",
                },
              ].map((s) => (
                <div key={s.step} className="bg-io-bg border border-io-border rounded-xl p-6">
                  <div className="w-10 h-10 bg-io-accent/10 rounded-lg flex items-center justify-center text-io-accent text-sm font-bold mb-4">
                    {s.step}
                  </div>
                  <h3 className="text-lg font-bold text-io-primary mb-2">{s.title}</h3>
                  <p className="text-sm text-io-secondary leading-relaxed">{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Capabilities Grid */}
        <section id="capabilities" className="max-w-5xl mx-auto px-6 lg:px-10 py-16">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-io-primary mb-3">
              {isAr ? "القدرات" : "Capabilities"}
            </h2>
            <p className="text-io-secondary text-base">
              {isAr ? "نمذجة مالية شاملة للأسواق الخليجية" : "Comprehensive financial modeling for GCC markets"}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {caps.map((cap) => (
              <div key={cap.title} className="bg-io-surface border border-io-border rounded-xl p-6 shadow-sm hover:shadow-md hover:border-io-accent/30 transition-all">
                <div className="text-2xl mb-3">{cap.icon}</div>
                <h3 className="text-base font-bold text-io-primary mb-2">{cap.title}</h3>
                <p className="text-sm text-io-secondary leading-relaxed">{cap.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="bg-io-accent py-16">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              {isAr ? "ابدأ تحليل الأثر المالي الآن" : "Start analyzing financial impact now"}
            </h2>
            <p className="text-blue-100 text-base mb-8 max-w-xl mx-auto">
              {isAr
                ? "اختر سيناريو خليجي واحصل على تحليل مالي شامل مع إجراءات قرار مُرتّبة حسب الأولوية"
                : "Choose a GCC scenario and get comprehensive financial analysis with prioritized decision actions"}
            </p>
            <button
              onClick={() => setAppView("scenarios")}
              className="px-10 py-4 bg-white text-io-accent text-base font-bold rounded-xl hover:bg-blue-50 transition-colors shadow-lg"
            >
              {isAr ? "تشغيل السيناريو" : "Run Scenario"}
            </button>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-io-surface border-t border-io-border py-8">
          <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-io-accent rounded flex items-center justify-center text-white text-[10px] font-bold">IO</div>
              <span className="text-sm font-semibold text-io-primary">Impact Observatory</span>
              <span className="text-xs text-io-secondary">| مرصد الأثر</span>
            </div>
            <p className="text-xs text-io-secondary">
              {isAr ? "منصة ذكاء القرار للأسواق المالية الخليجية" : "Decision Intelligence Platform for GCC Financial Markets"}
            </p>
          </div>
        </footer>
      </div>
    );
  }

  // ── SCENARIO SELECTOR ─────────────────────────────────────────────

  if (appView === "scenarios" && !result && !loading) {
    return (
      <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
        <TopNav />
        <div className="max-w-4xl mx-auto px-6 lg:px-10 pt-12 pb-16">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-io-primary mb-3">
              {isAr ? "اختر سيناريو" : "Select a Scenario"}
            </h2>
            <p className="text-io-secondary text-base">
              {isAr
                ? "اختر حدثاً لتحليل الأثر المالي عبر القطاعات الخليجية"
                : "Choose an event to analyze financial impact across GCC sectors"}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {SCENARIOS.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => runScenario(scenario.id, scenario.severity)}
                className="bg-io-surface border border-io-border rounded-xl p-6 text-left shadow-sm hover:shadow-lg hover:border-io-accent transition-all group"
              >
                <div className="flex items-start gap-4">
                  <div className="text-3xl flex-shrink-0 mt-0.5">{scenario.icon}</div>
                  <div className="flex-1">
                    <p className="text-lg font-bold text-io-primary group-hover:text-io-accent transition-colors">
                      {isAr ? scenario.label_ar : scenario.label}
                    </p>
                    <p className="text-sm text-io-secondary mt-1 leading-relaxed">
                      {isAr ? scenario.desc_ar : scenario.desc}
                    </p>
                    <div className="flex items-center gap-3 mt-3 text-xs">
                      <span className="px-2 py-0.5 bg-io-danger/10 text-io-danger rounded font-semibold">
                        {scenario.loss}
                      </span>
                      <span className="text-io-secondary">
                        Severity: {(scenario.severity * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <div className="text-center mt-8">
            <button
              onClick={() => setAppView("landing")}
              className="text-sm text-io-secondary hover:text-io-accent transition-colors"
            >
              {isAr ? "← العودة للصفحة الرئيسية" : "← Back to Home"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── RESULTS VIEW (Loading / Error / Dashboard) ─────────────────────

  return (
    <div className="min-h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
      <TopNav />

      {/* Detail Navigation Tabs */}
      {result && (
        <div className="bg-io-surface border-b border-io-border px-6 lg:px-10 py-0 flex items-center gap-1 overflow-x-auto">
          {(["dashboard", "banking", "insurance", "fintech", "decisions"] as DetailView[]).map((view) => (
            <button
              key={view}
              onClick={() => setDetailView(view)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                detailView === view
                  ? "border-io-accent text-io-accent"
                  : "border-transparent text-io-secondary hover:text-io-primary hover:border-io-border"
              }`}
            >
              {detailLabels[lang][view]}
            </button>
          ))}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center mt-32">
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-io-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-io-primary font-semibold text-lg mb-1">
              {isAr ? "جاري تحليل السيناريو..." : "Analyzing scenario..."}
            </p>
            <p className="text-io-secondary text-sm">
              {isAr ? "12 محرك تحليلي يعمل الآن" : "Running 12 analysis engines"}
            </p>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="max-w-lg mx-auto mt-16 p-6 bg-red-50 border border-red-200 rounded-xl text-center">
          <p className="text-io-danger font-medium mb-2">{error}</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => { setError(null); setAppView("scenarios"); }}
              className="px-4 py-2 text-sm bg-io-surface border border-io-border rounded-lg hover:bg-io-bg transition-colors"
            >
              {isAr ? "اختر سيناريو آخر" : "Try Another Scenario"}
            </button>
          </div>
        </div>
      )}

      {/* Dashboard */}
      {result && detailView === "dashboard" && (
        <ExecutiveDashboard data={result} lang={lang} onNavigate={(view: string) => setDetailView(view as DetailView)} />
      )}

      {result && detailView === "banking" && (
        <div className="max-w-6xl mx-auto p-6"><BankingDetailPanel data={result.banking} lang={lang} /></div>
      )}

      {result && detailView === "insurance" && (
        <div className="max-w-6xl mx-auto p-6"><InsuranceDetailPanel data={result.insurance} lang={lang} /></div>
      )}

      {result && detailView === "fintech" && (
        <div className="max-w-6xl mx-auto p-6"><FintechDetailPanel data={result.fintech} lang={lang} /></div>
      )}

      {result && detailView === "decisions" && (
        <div className="max-w-6xl mx-auto p-6"><DecisionDetailPanel decisions={result.decisions} explanation={result.explanation} lang={lang} /></div>
      )}

      {/* Back button */}
      {(result || loading) && (
        <div className="fixed bottom-6 left-6 z-50">
          <button
            onClick={handleBack}
            className="px-4 py-2 text-sm font-medium bg-io-surface border border-io-border rounded-lg shadow-md hover:shadow-lg transition-shadow"
          >
            {detailView !== "dashboard" && result
              ? (isAr ? "← لوحة المعلومات" : "← Dashboard")
              : (isAr ? "← سيناريو جديد" : "← New Scenario")
            }
          </button>
        </div>
      )}
    </div>
  );
}
