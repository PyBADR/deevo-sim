# Screenshot Checklist — Observatory V2

Capture at 1440×900 (desktop) and 390×844 (mobile). Light mode only. Use Hormuz Chokepoint Disruption as the primary scenario for all pages.

## 1. Landing Page — Scenario Register

- [ ] Full page at `/` showing "Active Intelligence" heading and scenario register
- [ ] Focus: first 4–5 scenarios visible, severity colors (red for Severe, amber for Elevated)
- [ ] Hover state on one scenario row (subtle muted background)
- [ ] Mobile: stacked metadata above title

## 2. Scenario Briefing — Context Section

- [ ] Full header at `/scenario/hormuz_chokepoint_disruption`
- [ ] Focus: metadata line (Severe · Maritime & Energy · 72h horizon · sectors), title, context paragraph, significance
- [ ] TopNav visible with "Overview · Decisions · Evaluation"

## 3. Scenario Briefing — Transmission Section

- [ ] "How Pressure Transmits" section
- [ ] Focus: numbered prose paragraphs with Source → Target (+Xh) — mechanism pattern
- [ ] No dot-and-connector rail visible

## 4. Scenario Briefing — Impact Section

- [ ] "Institutional Exposure" section
- [ ] Focus: stacked disclosure blocks — entity + severity, sector, exposure narrative
- [ ] No column grid, no table headers

## 5. Scenario Briefing — Decision Section

- [ ] "Required Response" section
- [ ] Focus: numbered prose with embedded owner/deadline/sector
- [ ] "View decision brief →" link visible at bottom

## 6. Scenario Briefing — Outcome Section

- [ ] "Expected Outcome" paragraph
- [ ] "Monitoring Criteria" numbered list below with clear whitespace separation
- [ ] Quiet footer visible at bottom

## 7. Decision Directive — Primary Directive

- [ ] Full header at `/decision/hormuz_chokepoint_disruption`
- [ ] Focus: "Directive · Severe" label, imperative title at dominant scale
- [ ] Primary Directive section: action at 1.25rem, rationale, "If Not Executed"
- [ ] "View scenario analysis →" link visible

## 8. Decision Directive — Supporting Actions + Footer

- [ ] Supporting Actions as numbered prose
- [ ] Expected Effect + Monitoring Criteria
- [ ] Briefing footer: Reference · Issued · Origin · Distribution in quiet text-xs

## 9. Evaluation Register

- [ ] Full page at `/evaluation`
- [ ] Focus: "Accountability" heading, verdict colors (olive Confirmed, amber Partially Confirmed, grey Inconclusive)
- [ ] Correctness percentages visible
- [ ] Summary text beneath each scenario title

## 10. Evaluation Review — Outcome Assessment

- [ ] Full header at `/evaluation/hormuz_chokepoint_disruption`
- [ ] Focus: "Evaluation · Confirmed · 87%" header
- [ ] Outcome Assessment section: "Expected" and "Actual" as stacked prose blocks

## 11. Evaluation Review — Correctness + Analyst + Rules

- [ ] Correctness section: "Confirmed at 87%" verdict line
- [ ] Analyst Commentary section
- [ ] Rule Performance numbered list
- [ ] Briefing footer visible

## 12. Navigation Flow

- [ ] Screenshot sequence showing the full navigation chain:
  Landing → Scenario → Decision → Evaluation
- [ ] Cross-links visible at each transition point

## 13. Mobile Responsive

- [ ] Landing page at 390px width
- [ ] Scenario briefing Context section at 390px
- [ ] Decision directive Primary Directive at 390px
- [ ] Evaluation register at 390px

## Notes

- All screenshots should show the #F5F5F2 warm background, not white
- DM Sans font must be loaded (check that headings render in DM Sans, not system font)
- Severity colors: Severe/High = red (#8E4338), Elevated = amber (#A06A34), Guarded = tertiary grey
- Verdict colors: Confirmed = olive (#5E6759), Partially Confirmed = amber, Inconclusive = grey
