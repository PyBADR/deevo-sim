"use client";

/**
 * Impact Observatory | مرصد الأثر — Shared Navigation Bar
 *
 * Consistent navigation across all pages. Bilingual.
 * Highlights the current active page.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppStore } from "@/store/app-store";

const NAV_ITEMS = [
  { href: "/dashboard", en: "Dashboard", ar: "لوحة المعلومات" },
  { href: "/map", en: "Impact Map", ar: "خريطة الأثر" },
  { href: "/graph-explorer", en: "Propagation", ar: "الانتشار" },
  { href: "/scenario-lab", en: "Scenario Lab", ar: "المعمل" },
  { href: "/timeline", en: "Timeline", ar: "الجدول الزمني" },
  { href: "/regulatory", en: "Regulatory", ar: "التنظيمي" },
];

export default function NavBar() {
  const pathname = usePathname();
  const { language, setLanguage } = useAppStore();
  const isAr = language === "ar";

  return (
    <nav className="bg-io-surface border-b border-io-border px-4 py-2 flex items-center justify-between shrink-0 sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="w-7 h-7 flex items-center justify-center bg-io-accent text-white text-xs font-bold rounded">
            IO
          </span>
          <span className="text-base font-bold text-io-primary group-hover:text-io-accent transition-colors">
            {isAr ? "مرصد الأثر" : "Impact Observatory"}
          </span>
        </Link>
        <span className="text-[10px] text-io-secondary bg-io-bg px-1.5 py-0.5 rounded border border-io-border">
          v4.0
        </span>
      </div>

      <div className="flex items-center gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                isActive
                  ? "bg-io-accent text-white"
                  : "text-io-secondary hover:text-io-primary hover:bg-io-bg"
              }`}
            >
              {isAr ? item.ar : item.en}
            </Link>
          );
        })}

        <span className="mx-1 text-io-border">|</span>

        <button
          onClick={() => setLanguage(isAr ? "en" : "ar")}
          className="px-3 py-1.5 text-xs font-medium rounded border border-io-border text-io-secondary hover:text-io-primary transition-colors"
        >
          {isAr ? "EN" : "AR"}
        </button>
      </div>
    </nav>
  );
}
