#!/usr/bin/env bash
# ============================================================================
# Impact Observatory | مرصد الأثر — PHASE 2: Git Preparation + GitHub Push
# ============================================================================
# This script must be run from the project root: deevo-sim/
#
# What it does:
#   1. Removes stale git lock (if present)
#   2. Deletes broken root vercel.json
#   3. Creates 6 logical commits
#   4. Pushes to origin/main
#   5. Verifies push
#
# SAFE: Each step checks for errors and halts on failure.
# ============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ── Guard: must be in project root ──
if [ ! -f "backend/src/main.py" ]; then
  fail "Run this script from the deevo-sim/ project root."
fi

# ── Guard: must be on main branch ──
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
  fail "Current branch is '$BRANCH', expected 'main'. Aborting."
fi

# ── Step 0: Clear stale index lock ──
if [ -f ".git/index.lock" ]; then
  rm -f .git/index.lock
  log "Removed stale .git/index.lock"
else
  log "No stale git lock found"
fi

# ── Step 1: Pre-flight — delete broken vercel.json ──
if [ -f "vercel.json" ]; then
  git rm vercel.json
  git commit -m "$(cat <<'EOF'
fix: remove broken root vercel.json

Root vercel.json used ${VARIABLE} placeholders that Vercel does not
expand in JSON config, causing all API rewrites to route to literal
strings. Rewrites are correctly handled by frontend/next.config.mjs.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
  log "Commit 0: removed broken vercel.json"
else
  log "vercel.json already absent — skipping"
fi

# ── Commit 1: Design System Foundation ──
git add \
  frontend/src/app/globals.css \
  frontend/theme/globals.css \
  frontend/tailwind.config.ts \
  frontend/src/app/layout.tsx \
  frontend/src/lib/theme.ts \
  frontend/src/lib/copy.ts \
  frontend/src/components/layout/

git commit -m "$(cat <<'EOF'
refactor: Observatory V2 design system — tokens, typography, layout shell

Institutional design token layer (--io-* CSS custom properties), Tailwind
io.* extensions, PageShell + Container composition, TopNav, and full
copy/theme manifests for the sovereign-grade briefing system.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
log "Commit 1: design system foundation"

# ── Commit 2: Scenario Observatory V2 ──
git add \
  frontend/src/lib/scenarios.ts \
  frontend/src/app/scenario/

git commit -m "$(cat <<'EOF'
feat: scenario observatory V2 — institutional macro-financial briefing pages

15-scenario manifest with transmission chains, exposure lines, and decision
summaries. Detail page renders 5-section institutional briefing with
generateStaticParams() for Vercel SSG (15 static routes).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
log "Commit 2: scenario observatory V2"

# ── Commit 3: Decision Directive V2 ──
git add \
  frontend/src/lib/decisions.ts \
  frontend/src/app/decision/

git commit -m "$(cat <<'EOF'
feat: decision directive V2 — sovereign-grade decision briefings with register

15-scenario decision manifest with primary directives, supporting actions,
monitoring criteria. Register page sorted by classification severity.
Detail page renders dominant directive at 1.25rem with rationale and
consequence-of-inaction. SSG via generateStaticParams() (15 routes).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
log "Commit 3: decision directive V2"

# ── Commit 4: Evaluation Observatory V2 ──
git add \
  frontend/src/lib/evaluations.ts \
  frontend/src/app/evaluation/

git commit -m "$(cat <<'EOF'
feat: evaluation observatory V2 — accountability layer with verdict register

15-scenario evaluation manifest with verdicts (Confirmed/Partially
Confirmed/Revised/Inconclusive), correctness scores, analyst commentary,
replay summaries, and rule performance audits. Register sorted by verdict.
Detail page renders 6-section accountability document. SSG (15 routes).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
log "Commit 4: evaluation observatory V2"

# ── Commit 5: Landing + Backend Routes + Adapters ──
git add \
  frontend/src/app/page.tsx \
  frontend/src/features/demo/adapters/ \
  backend/src/main.py \
  backend/app/

git commit -m "$(cat <<'EOF'
feat: institutional landing page + backend phase routes + demo adapters

Landing page rewritten as scenario register (severity-sorted, institutional
tone). Backend main.py adds phase 1-3 route imports (simulation,
counterfactuals, entity graph, decisions). Demo adapters bridge frontend
components to backend API contracts.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
log "Commit 5: landing + backend + adapters"

# ── Commit 6: Deployment + Documentation ──
git add \
  README.md \
  RELEASE.md \
  DEPLOYMENT.md \
  BACKEND_DEPLOYMENT.md

git commit -m "$(cat <<'EOF'
docs: deployment guides, release notes, README institutional positioning

README repositioned for sovereign-grade briefing system (15 scenarios,
5-layer narrative). Vercel frontend deployment guide (47 static pages).
Railway backend deployment guide (7-stage startup, 20 smoke tests).
Release notes covering full Observatory V2 transformation.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
log "Commit 6: deployment + documentation"

# ── Verification ──
echo ""
echo "============================================"
echo "  COMMIT LOG (newest first)"
echo "============================================"
git log --oneline -7
echo ""

echo "============================================"
echo "  REMAINING UNTRACKED (intentionally excluded)"
echo "============================================"
git status --short
echo ""

# ── Push ──
echo "============================================"
echo "  PUSHING TO origin/main"
echo "============================================"
git push origin main

if [ $? -eq 0 ]; then
  echo ""
  log "PHASE 2 COMPLETE — all commits pushed to origin/main"
  echo ""
  echo "  Repo: https://github.com/PyBADR/impact-observatory"
  echo ""
  echo "  Next: PHASE 3 (Vercel) + PHASE 4 (Railway)"
else
  fail "Push failed. Check authentication and try: git push origin main"
fi
