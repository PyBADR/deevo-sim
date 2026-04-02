"use client";

/**
 * Impact Observatory | مرصد الأثر — AppShell
 * Top navigation + page wrapper. Used by dashboard and all V2 routes.
 */

import React from "react";
import Link from "next/link";
import { useAppStore } from "@/store/app-store";

interface AppShellProps {
  children: React.ReactNode;
  /** Active route for nav highlighting */
  activeRoute?: "home" | "dashboard" | "control-room" | "graph" | "scenario-lab";
}

const NAV_ITEMS = [
  { key: "home", href: "/", en: "Home", ar: "الرئيسية" },
  { key: "dashboard", href: "/dashboard", en: "Dashboard", ar: "لوحة المعلومات" },
  { key: "control-room", href: "/control-room", en: "Control Room", ar: "غرفة التحكم" },
  { key: "graph", href: "/graph-explorer", en: "Graph", ar: "الرسم البياني" },
  { key: "scenario-lab", href: "/scenario-lab", en: "Scenario Lab", ar: "معمل السيناريو" },
] as const;

export default function AppShell({ children, activeRoute }: AppShellProps) {
  const language = useAppStore((s) => s.language);
  const setLanguage = useAppStore((s) => s.setLanguage);
  const isAr = language === "ar";

  return (
    <div className="min-h-screen bg-io-bg">
      {/* Top Nav */}
      <nav className="bg-io-surface border-b border-io-border px-6 lg:px-10 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-io-accent rounded-lg flex items-center justify-center text-white text-sm font-bold">
              IO
            </div>
            <span className="text-lg font-bold text-io-primary group-hover:text-io-accent transition-colors">
              {isAr ? "مرصد الأثر" : "Impact Observatory"}
            </span>
          </Link>
          <span className="text-xs text-io-secondary font-medium bg-io-bg px-2 py-0.5 rounded border border-io-border">
            v4.0
          </span>
        </div>

        {/* Nav Links (desktop) */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.key}
              href={item.href}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                activeRoute === item.key
                  ? "bg-io-accent/10 text-io-accent"
                  : "text-io-secondary hover:text-io-primary hover:bg-io-bg"
              }`}
            >
              {isAr ? item.ar : item.en}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setLanguage(isAr ? "en" : "ar")}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary transition-colors"
          >
            {isAr ? "English" : "العربية"}
          </button>
        </div>
      </nav>

      {/* Page content */}
      {children}
    </div>
  );
}
