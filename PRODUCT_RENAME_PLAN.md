# Product Rename Plan — Step 2

**Date:** 2026-04-02
**Target Identity:** Impact Observatory | مرصد الأثر
**Scope:** All user-visible branding. Internal package scope `@deevo/` is retained (infrastructure-level, not user-facing).

---

## 1. String Categories

| Category | Old String | New String | Risk Level |
|----------|-----------|------------|------------|
| **A. Visible Product Name** | `Deevo Analytics` | `Impact Observatory` | LOW — cosmetic |
| **B. Visible AR Name** | `ديفو أناليتكس` | `مرصد الأثر` | LOW — cosmetic |
| **C. URL / Domain** | `deevo-sim.vercel.app` | TBD (new Vercel domain) | MEDIUM — breaks CORS + production URLs |
| **D. Database Credentials** | `deevo` / `deevo_secure` | `observatory_admin` / `io_pilot_2026` | HIGH — breaks running containers |
| **E. Internal Package Scope** | `@deevo/gcc-*` | **KEEP AS-IS** | N/A — not user-facing |
| **F. Code Comments** | `DeevoSim.jsx`, `deevo-sim` | `Impact Observatory` | LOW — no runtime effect |
| **G. Copyright** | `Deevo Analytics` | `Impact Observatory` | LOW — legal text |

---

## 2. Files Affected — Exact Rename Targets

### Category A: "Deevo Analytics" → "Impact Observatory"

| # | File | Line | Current | Target |
|---|------|------|---------|--------|
| 1 | `LICENSE` | 1 | `Copyright (c) 2026 Deevo Analytics.` | `Copyright (c) 2026 Impact Observatory.` |
| 2 | `LICENSE` | 6 | `permission of Deevo Analytics.` | `permission of Impact Observatory.` |
| 3 | `packages/@deevo/gcc-knowledge-graph/package.json` | 19 | `"author": "Deevo Analytics"` | `"author": "Impact Observatory"` |

**Total: 3 edits in 2 files**

### Category B: "ديفو أناليتكس" → "مرصد الأثر"

No occurrences found in the main repository tree (only in `.claude/worktrees/serene-mcnulty/` which is a snapshot). **0 edits needed.**

### Category C: URL/Domain References

| # | File | Line | Current | Target |
|---|------|------|---------|--------|
| 1 | `backend/src/core/config.py` | 38 | `https://deevo-sim.vercel.app` | `https://impact-observatory.vercel.app` |
| 2 | `API.md` | 5 | `https://deevo-sim.vercel.app/api` | `https://impact-observatory.vercel.app/api` |
| 3 | `docs/RUNBOOK.md` | 46 | `git clone https://github.com/PyBADR/deevo-sim.git && cd deevo-sim` | `git clone https://github.com/PyBADR/impact-observatory.git && cd impact-observatory` |
| 4 | `frontend/.env.production` | 3 | `https://deevo-cortex-production.up.railway.app` | New Railway URL (requires deployment setup) |

**Total: 4 edits in 4 files**

**NOTE:** `backend/src/core/config.py` is in the `backend/src/` tree (marked for REMOVE in Step 1). If it is removed before this rename, edit #1 becomes unnecessary. If not, rename it to prevent CORS errors during transition.

### Category D: Database Credentials (docker-compose.yml)

| # | File | Line | Current | Target |
|---|------|------|---------|--------|
| 1 | `docker-compose.yml` | 11 | `DATABASE_URL=postgresql://deevo:deevo_secure@postgres:5432/deevo` | `DATABASE_URL=postgresql://observatory_admin:io_pilot_2026@postgres:5432/impact_observatory` |
| 2 | `docker-compose.yml` | 14 | `NEO4J_PASSWORD=deevo_neo4j_2026` | `NEO4J_PASSWORD=io_graph_2026` |
| 3 | `docker-compose.yml` | 32 | `POSTGRES_DB=deevo` | `POSTGRES_DB=impact_observatory` |
| 4 | `docker-compose.yml` | 33 | `POSTGRES_USER=deevo` | `POSTGRES_USER=observatory_admin` |
| 5 | `docker-compose.yml` | 34 | `POSTGRES_PASSWORD=deevo_secure` | `POSTGRES_PASSWORD=io_pilot_2026` |
| 6 | `docker-compose.yml` | 49 | `NEO4J_AUTH=neo4j/deevo_neo4j_2026` | `NEO4J_AUTH=neo4j/io_graph_2026` |

**Total: 6 edits in 1 file**

### Category E: Internal Package Scope — NO CHANGE

The `@deevo/` scope in `packages/@deevo/gcc-constants/` and `packages/@deevo/gcc-knowledge-graph/` is **retained**. Rationale:

1. It is an npm scope, not user-visible branding
2. Renaming the scope requires updating `package.json` name, `package-lock.json` name, all import paths in any consumer, `docker-compose.yml` migration mount path, and the physical directory name
3. The scope is referenced in `docker-compose.yml:39` as a volume mount path: `./packages/@deevo/gcc-knowledge-graph/migrations:/docker-entrypoint-initdb.d`
4. Zero user-facing impact — this is infrastructure plumbing
5. If desired later, scope can be changed to `@io/` in a dedicated refactor

### Category F: Code Comments — "DeevoSim" / "deevo-sim" References

| # | File | Line | Current | Notes |
|---|------|------|---------|-------|
| 1 | `backend/src/services/seed_data.py` | 3 | `This mirrors the DeevoSim.jsx node/edge graph` | Comment only. In `backend/src/` (REMOVE candidate). |

**Total: 1 edit in 1 file** (or 0 if `backend/src/` is removed first)

### Category G: Deployment Entry Points Using `src.main`

These reference the `backend/src/` entrypoint which conflicts with the canonical `backend/app/` entrypoint. These are identity-adjacent because they encode the old architecture.

| # | File | Line | Current | Target |
|---|------|------|---------|--------|
| 1 | `Makefile` | 85 | `uvicorn src.main:app` | `uvicorn app.main:app` |
| 2 | `Procfile` | 1 | `uvicorn src.main:app` | `uvicorn app.main:app` |
| 3 | `Dockerfile.backend` | 24 | `uvicorn src.main:app` | `uvicorn app.main:app` |

**Total: 3 edits in 3 files**

---

## 3. Files NOT Affected (Already Correct)

These files already use "Impact Observatory" / "مرصد الأثر" — verified, no edits needed:

| File | Current Identity |
|------|-----------------|
| `README.md` | "Impact Observatory \| مرصد الأثر" |
| `frontend/src/app/layout.tsx` | `title: "Impact Observatory \| مرصد الأثر"` |
| `frontend/src/app/page.tsx` | IO branded throughout |
| `frontend/src/app/dashboard/page.tsx` | IO branded |
| `frontend/src/app/control-room/page.tsx` | IO branded |
| `frontend/src/app/scenario-lab/page.tsx` | IO branded |
| `frontend/src/app/graph-explorer/page.tsx` | IO branded |
| `frontend/src/app/entity/[id]/page.tsx` | IO branded |
| `frontend/src/i18n/en.json` | `"product_name": "Impact Observatory"` |
| `frontend/src/i18n/ar.json` | Arabic translations |
| `frontend/tailwind.config.ts` | IO design tokens |
| `frontend/src/theme/tokens.ts` | IO design rules |
| `frontend/src/theme/globals.css` | IO CSS variables |
| `frontend/components/ui/Footer.tsx` | "Impact Observatory" / "مرصد الأثر" |
| `frontend/components/ui/Navbar.tsx` | "Impact Observatory" / "مرصد الأثر" |
| `frontend/package.json` | `"name": "impact-observatory"` |
| `frontend/.env.example` | `NEXT_PUBLIC_PRODUCT_NAME=Impact Observatory` |
| `frontend/.env.production` | `NEXT_PUBLIC_PRODUCT_NAME=Impact Observatory` |
| `.env.example` | `POSTGRES_DB=impact_observatory` + `NEXT_PUBLIC_PRODUCT_NAME=Impact Observatory` |
| `Makefile` help text | "Impact Observatory \| مرصد الأثر" |
| `db/init.sql` | "Impact Observatory \| مرصد الأثر" |
| `config/project.yml` | Likely correct (not checked — low risk) |
| All `frontend/src/` component headers | IO branded in file comments |

---

## 4. Risk Assessment — Import/Route Breaking

### HIGH RISK: Database Credential Rename (Category D)

**What breaks:**
- Any running Docker container using `deevo` / `deevo_secure` credentials will lose database connectivity
- PostgreSQL volume data is tied to the database name `deevo` — changing `POSTGRES_DB` to `impact_observatory` means the old volume's database won't match

**Mitigation:**
- Run `docker-compose down -v` to destroy volumes before applying credential rename (destructive but clean)
- OR: Add a migration script that renames the database: `ALTER DATABASE deevo RENAME TO impact_observatory;` and updates the role
- Apply ALL 6 credential edits atomically in a single commit

### MEDIUM RISK: Entrypoint Alignment (Category G)

**What breaks:**
- `Makefile`, `Procfile`, `Dockerfile.backend` all reference `src.main:app`
- Changing to `app.main:app` means `backend/src/` imports no longer resolve for Railway/Heroku/Docker deployments
- If `backend/src/` is NOT removed first, two entrypoints coexist with different import paths

**Mitigation:**
- Remove `backend/src/` BEFORE changing entrypoints (sequence matters — see Section 5)
- OR: Verify `backend/app/main.py` works standalone before changing deployment configs
- Test `uvicorn app.main:app --host 0.0.0.0 --port 8000` locally before committing

### MEDIUM RISK: Vercel/Railway URL Change (Category C)

**What breaks:**
- `frontend/.env.production` hardcodes Railway URL — changing it without updating Railway config breaks the deployed API proxy
- `backend/src/core/config.py` CORS allowlist includes `deevo-sim.vercel.app` — if old domain is still live, removing it blocks requests

**Mitigation:**
- Add new URL to CORS allowlist as an additional origin (don't remove old one yet)
- Update Vercel project settings to use new domain before updating `.env.production`
- Keep old domain as redirect for 30 days

### LOW RISK: LICENSE / Author / Comment Renames (Categories A, F, G)

**What breaks:** Nothing at runtime. These are cosmetic/legal text changes.

**Mitigation:** None needed. Safe to apply at any time.

### NO RISK: @deevo/ Package Scope (Category E — NOT CHANGING)

Retaining `@deevo/` avoids:
- Renaming `packages/@deevo/` directory (breaks git history tracking)
- Updating `docker-compose.yml` volume mount path
- Updating any future import statements
- Updating `package.json` / `package-lock.json` name fields and npm resolution

---

## 5. Safe Rename Execution Order

The order is designed so each step is independently deployable and no step creates a broken state.

### Phase 1: Zero-Risk Cosmetic (can deploy immediately)

| Order | File | Change | Risk |
|-------|------|--------|------|
| 1.1 | `LICENSE` | "Deevo Analytics" → "Impact Observatory" (2 occurrences) | ZERO |
| 1.2 | `packages/@deevo/gcc-knowledge-graph/package.json` | `"author": "Deevo Analytics"` → `"author": "Impact Observatory"` | ZERO |

### Phase 2: Backend `src/` Removal Prerequisite

| Order | File | Change | Risk |
|-------|------|--------|------|
| 2.1 | Verify `uvicorn app.main:app` works locally | Test command | LOW |
| 2.2 | `Makefile:85` | `src.main:app` → `app.main:app` | LOW (after verification) |
| 2.3 | `Procfile:1` | `src.main:app` → `app.main:app` | LOW (Railway redeploy needed) |
| 2.4 | `Dockerfile.backend:24` | `src.main:app` → `app.main:app` | LOW (Docker rebuild needed) |
| 2.5 | Remove `backend/src/` entirely | Delete directory | MEDIUM (only after 2.1-2.4) |

### Phase 3: Database Credential Alignment

| Order | File | Change | Risk |
|-------|------|--------|------|
| 3.1 | `docker-compose.yml` | All 6 credential edits (see Category D) | HIGH |
| 3.2 | Run `docker-compose down -v && docker-compose up -d` | Recreate volumes | HIGH (data loss on dev) |
| 3.3 | Verify `make status` passes all health checks | Validation | — |

### Phase 4: URL/Domain Migration

| Order | File | Change | Risk |
|-------|------|--------|------|
| 4.1 | Create new Vercel project domain OR add alias | Infra setup | MEDIUM |
| 4.2 | `API.md:5` | Update base URL | LOW |
| 4.3 | `docs/RUNBOOK.md:46` | Update git clone URL | LOW |
| 4.4 | `frontend/.env.production:3` | Update Railway URL when ready | MEDIUM |
| 4.5 | `backend/src/core/config.py:38` (if not already removed in Phase 2) | Add new domain to CORS | MEDIUM |

### Phase 5: Cleanup

| Order | File | Change | Risk |
|-------|------|--------|------|
| 5.1 | `backend/src/services/seed_data.py:3` (if not removed in Phase 2) | Update comment | ZERO |
| 5.2 | Remove old Vercel domain alias after 30 days | Infra | LOW |
| 5.3 | (Optional future) Rename GitHub repo `deevo-sim` → `impact-observatory` | Infra | HIGH — breaks all clones |
| 5.4 | (Optional future) Rename `@deevo/` scope → `@io/` | Package scope | HIGH — breaks all imports |

---

## 6. Summary Statistics

| Category | Edits | Files | Risk |
|----------|-------|-------|------|
| A. Visible product name | 3 | 2 | LOW |
| B. Arabic name | 0 | 0 | — |
| C. URL/domain | 4 | 4 | MEDIUM |
| D. DB credentials | 6 | 1 | HIGH |
| E. Package scope | 0 | 0 | N/A (kept) |
| F. Code comments | 1 | 1 | ZERO |
| G. Entrypoint alignment | 3 | 3 | MEDIUM |
| **TOTAL** | **17** | **11** | — |

Plus 23+ files already correct (no action needed).

---

## 7. Decision Gate

Before executing this plan, the following must be true:

1. `uvicorn app.main:app` has been verified to start successfully on local
2. Decision made: destroy Docker volumes (clean rename) OR write migration SQL (preserve data)
3. New Vercel domain decided (e.g., `impact-observatory.vercel.app` or custom domain)
4. New Railway deployment URL confirmed (for `.env.production`)
5. GitHub repo rename decision: now or deferred

Awaiting your command to proceed.
