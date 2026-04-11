/**
 * dictionary.ts — Centralized bilingual dictionary for Impact Observatory.
 *
 * Single source of truth for ALL UI strings across the Decision Command
 * Center.  Replaces scattered inline `isAr ? "..." : "..."` patterns
 * with a structured, type-safe dictionary.
 *
 * Usage:
 *   import { t } from "@/i18n/dictionary";
 *   <span>{t("decision_room.title", locale)}</span>
 *
 * Nested keys use dot notation: "section.key"
 */

export type Locale = "en" | "ar";

// ── Flat dictionary (dot-notation keys) ──────────────────────────────

const dict: Record<string, { en: string; ar: string }> = {
  // ── App chrome ──
  "app.product_name":       { en: "Impact Observatory",     ar: "مرصد الأثر" },
  "app.data_live":          { en: "Live Intelligence",      ar: "بيانات مباشرة" },
  "app.data_demo":          { en: "Demo Mode",              ar: "وضع العرض" },
  "app.present":            { en: "Present",                ar: "عرض" },
  "app.retry":              { en: "Retry",                  ar: "إعادة المحاولة" },
  "app.loading":            { en: "Loading intelligence pipeline…", ar: "جاري تحميل محرك الذكاء…" },

  // ── Decision Room ──
  "dr.title":               { en: "Decision Room",          ar: "غرفة القرار" },
  "dr.top_decisions":       { en: "Top Decisions",          ar: "أهم القرارات" },
  "dr.cascade_view":        { en: "Cascade View",           ar: "مسار الانتشار" },
  "dr.map_view":            { en: "Map View",               ar: "خريطة الأثر" },

  // ── Depth Toggle ──
  "depth.level_1":          { en: "Executive",              ar: "تنفيذي" },
  "depth.level_2":          { en: "Analyst",                ar: "تحليلي" },
  "depth.level_3":          { en: "Full Detail",            ar: "تفصيل كامل" },

  // ── Mode system ──
  "mode.executive":         { en: "Executive",              ar: "تنفيذي" },
  "mode.analyst":           { en: "Analyst",                ar: "محلل" },
  "mode.decision":          { en: "Decision",               ar: "قرار" },

  // ── Executive Brief ──
  "brief.headline_loss":    { en: "Headline Loss",          ar: "الخسارة الرئيسية" },
  "brief.avg_stress":       { en: "Avg Stress",             ar: "متوسط الضغط" },
  "brief.prop_depth":       { en: "Propagation Depth",      ar: "عمق الانتشار" },
  "brief.peak_day":         { en: "Peak Day",               ar: "يوم الذروة" },
  "brief.severity":         { en: "Severity",               ar: "الشدة" },
  "brief.scenario":         { en: "Scenario",               ar: "السيناريو" },

  // ── Macro Panel ──
  "macro.title":            { en: "Macro Context",          ar: "السياق الاقتصادي الكلي" },
  "macro.sri":              { en: "System Risk",            ar: "مخاطر النظام" },
  "macro.triggered":        { en: "Triggered by",           ar: "ناتج عن" },
  "macro.simulated":        { en: "Simulated",              ar: "محاكاة" },
  "macro.no_signals":       { en: "No macro signals derived", ar: "لم يتم استخلاص إشارات" },

  // ── SRI levels ──
  "sri.severe":             { en: "SEVERE",                 ar: "حرج" },
  "sri.high":               { en: "HIGH",                   ar: "عالي" },
  "sri.elevated":           { en: "ELEVATED",               ar: "مرتفع" },
  "sri.guarded":            { en: "GUARDED",                ar: "متحفظ" },
  "sri.low":                { en: "LOW",                    ar: "منخفض" },
  "sri.nominal":            { en: "NOMINAL",                ar: "طبيعي" },

  // ── Map ──
  "map.title":              { en: "GCC Impact Map",         ar: "خريطة الأثر الخليجية" },
  "map.shock":              { en: "Shock Origin",           ar: "نقطة الصدمة" },
  "map.legend":             { en: "Stress",                 ar: "الضغط" },
  "map.high":               { en: "High",                   ar: "عالي" },
  "map.low":                { en: "Low",                    ar: "منخفض" },
  "map.click_detail":       { en: "Click node for detail",  ar: "انقر على العقدة للتفاصيل" },

  // ── Explainability ──
  "explain.title":          { en: "Explainability",         ar: "التفسير" },
  "explain.confidence":     { en: "Confidence",             ar: "الثقة" },
  "explain.loss_range":     { en: "Loss Range",             ar: "نطاق الخسارة" },
  "explain.top_driver":     { en: "Top Driver",             ar: "المحرك الأول" },
  "explain.narrative":      { en: "Narrative",              ar: "السرد" },
  "explain.show_detail":    { en: "Show Details",           ar: "عرض التفاصيل" },
  "explain.hide_detail":    { en: "Hide Details",           ar: "إخفاء التفاصيل" },
  "explain.drivers":        { en: "Key Drivers",            ar: "المحركات الرئيسية" },
  "explain.range":          { en: "Range Analysis",         ar: "تحليل النطاق" },

  // ── Sector Stress ──
  "sector.banking":         { en: "Banking",                ar: "المصرفية" },
  "sector.insurance":       { en: "Insurance",              ar: "التأمين" },
  "sector.fintech":         { en: "Fintech",                ar: "التقنية المالية" },
  "sector.title":           { en: "Sector Stress Analysis", ar: "تحليل ضغط القطاعات" },

  // ── Decision Cards ──
  "decision.cost":          { en: "Est. Cost",              ar: "التكلفة المقدرة" },
  "decision.loss_avoided":  { en: "Loss Avoided",           ar: "الخسارة المتجنبة" },
  "decision.confidence":    { en: "Confidence",             ar: "الثقة" },
  "decision.submit_review": { en: "Submit for Review",      ar: "إرسال للمراجعة" },
  "decision.pending":       { en: "Pending Review",         ar: "قيد المراجعة" },
  "decision.why":           { en: "Why This Decision",      ar: "لماذا هذا القرار" },
  "decision.why_now":       { en: "Why Now",                ar: "لماذا الآن" },
  "decision.why_rank":      { en: "Why This Rank",          ar: "لماذا هذا الترتيب" },
  "decision.tradeoff":      { en: "If Not Executed",        ar: "في حال عدم التنفيذ" },

  // ── Trust / Transparency ──
  "trust.loss_inducing":    { en: "Loss-Inducing Warning",  ar: "تحذير من خسائر محتملة" },
  "trust.transparency":     { en: "Decision Transparency",  ar: "شفافية القرار" },
  "trust.audit_hash":       { en: "Audit Hash",             ar: "بصمة المراجعة" },

  // ── Operational Intelligence ──
  "ops.title":              { en: "Operational Intelligence", ar: "الاستخبارات التشغيلية" },
  "ops.subtitle":           { en: "Trust · Workflows · Value · Governance · Pilot", ar: "الثقة · سير العمل · القيمة · الحوكمة · التجريب" },

  // ── Propagation ──
  "prop.title":             { en: "Propagation Chain",      ar: "سلسلة الانتشار" },
  "prop.step":              { en: "Step",                   ar: "خطوة" },
  "prop.entity":            { en: "Entity",                 ar: "الكيان" },
  "prop.impact":            { en: "Impact",                 ar: "الأثر" },

  // ── General ──
  "general.expand":         { en: "Expand",                 ar: "توسيع" },
  "general.collapse":       { en: "طي",                     ar: "طي" },
  "general.close":          { en: "Close",                  ar: "إغلاق" },
  "general.lang_toggle":    { en: "عربي",                   ar: "EN" },
};

// ── Translation function ─────────────────────────────────────────────

export function t(key: string, locale: Locale): string {
  const entry = dict[key];
  if (!entry) {
    if (process.env.NODE_ENV === "development") {
      console.warn(`[i18n] Missing key: "${key}"`);
    }
    return key;
  }
  return entry[locale];
}

// ── Re-export type ───────────────────────────────────────────────────

export type DictKey = keyof typeof dict;

export default t;
