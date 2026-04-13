# PR: Observatory V2 — Institutional UI System Reset

## Commit Plan

Two commits. Run these from the repo root:

### Commit 1 — Observatory V2: Design system, data manifests, and page architecture

```bash
git add \
  README.md \
  frontend/src/app/globals.css \
  frontend/src/app/layout.tsx \
  frontend/src/app/page.tsx \
  frontend/tailwind.config.ts \
  frontend/src/lib/copy.ts \
  frontend/src/lib/theme.ts \
  frontend/src/lib/scenarios.ts \
  frontend/src/lib/decisions.ts \
  frontend/src/lib/evaluations.ts \
  frontend/src/components/layout/ \
  frontend/src/app/scenario/ \
  frontend/src/app/decision/ \
  frontend/src/app/evaluation/

git commit -m "$(cat <<'EOF'
feat: Observatory V2 — institutional UI system reset

Replace dashboard/SaaS frontend with a calm, sovereign-grade
briefing system for GCC executive decision-makers.

New pages: Scenario Briefing (5-section vertical analysis),
Decision Directive (dominant primary directive with rationale),
Evaluation Register and Review (accountability layer with
expected vs actual, analyst commentary, rule performance).

15-scenario data manifests with observatory-grade institutional
prose. Design system with CSS custom properties, DM Sans +
IBM Plex Sans Arabic, warm institutional palette.

No KPI grids, no dashboard cards, no progress bars.
Every page reads top to bottom like a sovereign intelligence memo.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### Commit 2 (optional) — Release documentation

```bash
git add RELEASE.md SCREENSHOT_CHECKLIST.md PR_SUMMARY.md

git commit -m "$(cat <<'EOF'
docs: Observatory V2 release notes, screenshot checklist, PR summary

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### Excluded from Observatory commits

These files are unrelated to the Observatory V2 work and should be committed separately if desired:

- `backend/src/main.py` — Phase 1–3 router imports (backend app routes)
- `backend/app/` — Full backend app module (separate feature branch)
- `frontend/theme/globals.css` — Legacy theme file (replaced by src/app/globals.css)
- `frontend/src/components/landing/` — Earlier batch components (not imported by current pages)
- `frontend/src/components/primitives/` — Earlier batch components (not imported by current pages)
- `frontend/src/features/demo/adapters/` — Demo adapter files (separate feature)

---

## PR Body

```
## Summary

- Full UI system reset from dashboard/SaaS to institutional macro-financial briefing
- 4 new page types: Scenario Briefing, Decision Directive, Evaluation Register, Evaluation Review
- 15-scenario data manifests with observatory-grade GCC institutional prose
- Design system: CSS custom properties, warm palette (#F5F5F2), DM Sans + IBM Plex Sans Arabic
- Cross-linked navigation: Overview → Scenario → Decision → Evaluation
- README rewritten to reflect Observatory positioning

## Design Principles

Every page reads top to bottom like a sovereign intelligence memo. No KPI grids, no dashboard cards, no progress bars. Owner/deadline/sector embedded in prose sentences, not metadata rows. Visual hierarchy through typography scale, not chrome.

## Test plan

- [ ] `npx tsc --noEmit` passes (only pre-existing vitest test errors)
- [ ] Landing page renders scenario register with severity colors
- [ ] Scenario page renders all 5 sections for each of 15 scenarios
- [ ] Decision page renders primary directive at dominant scale
- [ ] Evaluation register renders all 15 evaluations sorted by verdict
- [ ] Evaluation page renders all 6 sections with verdict colors
- [ ] Cross-links navigate correctly between all page types
- [ ] Mobile responsive at 390px width
- [ ] TopNav shows Overview · Decisions · Evaluation

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```
