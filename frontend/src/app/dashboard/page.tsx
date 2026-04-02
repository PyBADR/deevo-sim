"use client";

/**
 * Impact Observatory | مرصد الأثر — Dashboard Shell
 * Executive overview with scenario quick-launch and recent runs.
 * Connects to /api/v1/ endpoints when backend is running.
 */

import React, { useState } from "react";
import AppShell from "@/components/shell/AppShell";
import { useAppStore } from "@/store/app-store";

const QUICK_SCENARIOS = [
  { id: "hormuz_disruption", en: "Hormuz Closure", ar: "إغلاق مضيق هرمز", icon: "⚓", severity: "Severe" },
  { id: "oil_price_shock", en: "Oil Price Shock", ar: "صدمة أسعار النفط", icon: "📉", severity: "Severe" },
  { id: "cyber_attack", en: "Cyber Attack", ar: "هجوم سيبراني", icon: "🛡️", severity: "High" },
  { id: "banking_stress", en: "Banking Stress", ar: "ضغط بنكي إقليمي", icon: "🏦", severity: "High" },
];

const SECTOR_CARDS = [
  { en: "Banking", ar: "القطاع البنكي", metric: "CAR", value: "14.2%", threshold: ">8%", status: "nominal" },
  { en: "Insurance", ar: "التأمين", metric: "Combined Ratio", value: "0.96", threshold: "<1.0", status: "nominal" },
  { en: "Fintech", ar: "الفنتك", metric: "Availability", value: "99.5%", threshold: ">95%", status: "nominal" },
  { en: "Energy", ar: "الطاقة", metric: "Supply Flow", value: "98.1%", threshold: ">90%", status: "nominal" },
];

export default function DashboardPage() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const [healthStatus, setHealthStatus] = useState<"idle" | "ok" | "error">("idle");

  const checkHealth = async () => {
    try {
      const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${BASE}/health`);
      setHealthStatus(res.ok ? "ok" : "error");
    } catch {
      setHealthStatus("error");
    }
  };

  return (
    <AppShell activeRoute="dashboard">
      <div className="max-w-6xl mx-auto px-6 lg:px-10 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-io-primary">
              {isAr ? "لوحة المعلومات التنفيذية" : "Executive Dashboard"}
            </h1>
            <p className="text-sm text-io-secondary mt-1">
              {isAr
                ? "نظرة عامة على الوضع المالي الخليجي في الوقت الحقيقي"
                : "Real-time GCC financial posture overview"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={checkHealth}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                healthStatus === "ok"
                  ? "border-io-success/30 bg-io-success/5 text-io-success"
                  : healthStatus === "error"
                  ? "border-io-danger/30 bg-io-danger/5 text-io-danger"
                  : "border-io-border text-io-secondary hover:text-io-primary"
              }`}
            >
              {healthStatus === "ok" ? "API Connected" : healthStatus === "error" ? "API Offline" : "Check API"}
            </button>
          </div>
        </div>

        {/* Sector Overview */}
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-io-secondary uppercase tracking-wider mb-4">
            {isAr ? "نظرة القطاعات" : "Sector Overview"}
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {SECTOR_CARDS.map((card) => (
              <div
                key={card.en}
                className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm"
              >
                <p className="text-sm font-semibold text-io-primary">{isAr ? card.ar : card.en}</p>
                <p className="text-2xl font-bold text-io-accent tabular-nums mt-2">{card.value}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-io-secondary">{card.metric}</span>
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase bg-io-success/10 text-io-success">
                    {card.status}
                  </span>
                </div>
                <p className="text-[10px] text-io-secondary mt-1">
                  {isAr ? "الحد:" : "Threshold:"} {card.threshold}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Quick Scenarios */}
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-io-secondary uppercase tracking-wider mb-4">
            {isAr ? "تشغيل سريع" : "Quick Launch"}
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {QUICK_SCENARIOS.map((s) => (
              <a
                key={s.id}
                href={`/?scenario=${s.id}`}
                className="bg-io-surface border border-io-border rounded-xl p-4 shadow-sm hover:shadow-md hover:border-io-accent/30 transition-all group"
              >
                <div className="text-2xl mb-2">{s.icon}</div>
                <p className="text-sm font-bold text-io-primary group-hover:text-io-accent transition-colors">
                  {isAr ? s.ar : s.en}
                </p>
                <span className="inline-block mt-2 text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-io-danger/10 text-io-danger">
                  {s.severity}
                </span>
              </a>
            ))}
          </div>
        </section>

        {/* Pipeline Info */}
        <section className="bg-io-surface border border-io-border rounded-xl p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-io-secondary uppercase tracking-wider mb-4">
            {isAr ? "محرك التحليل" : "Analysis Engine"}
          </h2>
          <div className="grid grid-cols-3 lg:grid-cols-6 gap-4 text-center">
            {[
              { label: isAr ? "مراحل" : "Stages", value: "9" },
              { label: isAr ? "قطاعات" : "Sectors", value: "5" },
              { label: isAr ? "كيانات" : "Entities", value: "31" },
              { label: isAr ? "إجراءات" : "Actions", value: "Top 3" },
              { label: isAr ? "لغات" : "Languages", value: "EN/AR" },
              { label: isAr ? "الإصدار" : "Version", value: "v4.0" },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-xl font-bold text-io-accent tabular-nums">{item.value}</p>
                <p className="text-xs text-io-secondary mt-0.5">{item.label}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
