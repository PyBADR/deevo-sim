# Impact Observatory | مرصد الأثر

**Decision Intelligence Platform for GCC Financial Markets**

منصة ذكاء القرار للأسواق المالية الخليجية

---

## Mission

Transform: **Event → Financial Impact → Sector Stress → Decision**

Every output maps a geopolitical or economic event through a 12-stage intelligence pipeline to produce calibrated financial losses, sector stress indicators, and ranked decision actions.

## Architecture

```
Scenario → Entity Graph → Physics → Propagation → Financial →
Banking → Insurance → Fintech → Decision → Explainability →
Reporting → Audit
```

### Backend (FastAPI + Python)
- **12 specialized services** orchestrated by `run_orchestrator.py`
- **8 scenario templates**: Hormuz Closure, Yemen Escalation, Cyber Attack, Oil Price Shock, Banking Stress, Port Disruption, Iran Sanctions, Gulf Airspace
- **VersionedModel** base class: `schema_version: "v1"` on all outputs
- **Structured audit trail** with per-stage timing

### Frontend (Next.js + React + TypeScript)
- **White boardroom UI** — executive presentation grade
- **Bilingual**: English + Arabic with full RTL support
- **Components**: KPICard, StressGauge, DecisionActionCard, FinancialImpactPanel
- **Typography**: DM Sans + IBM Plex Sans Arabic

## Sectors

| Sector | Analysis |
|--------|----------|
| **Banking** | Liquidity stress, credit risk, FX exposure, interbank contagion |
| **Insurance** | Claims surge, combined ratio, IFRS-17 risk adjustment |
| **Fintech** | Payment volume impact, settlement delays, API availability |
| **Energy** | Oil supply disruption, flow states |
| **Maritime** | Shipping reroute, port disruption |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/runs` | Execute full 12-stage pipeline |
| `GET` | `/api/v1/runs/{id}` | Retrieve run result |
| `GET` | `/api/v1/runs/{id}/financial` | Financial impacts |
| `GET` | `/api/v1/runs/{id}/banking` | Banking stress |
| `GET` | `/api/v1/runs/{id}/insurance` | Insurance stress |
| `GET` | `/api/v1/runs/{id}/fintech` | Fintech stress |
| `GET` | `/api/v1/runs/{id}/decision` | Decision actions (Top 3) |
| `POST` | `/api/v1/runs/{id}/actions/{aid}/approve` | Human approval |
| `GET` | `/api/v1/scenarios` | List scenario templates |

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Decision Model

```
Priority = 0.25×Urgency + 0.30×Value + 0.20×RegulatoryRisk + 0.15×Feasibility + 0.10×TimeEffect
```

Only **Top 3 actions** are returned. No action executes without **human approval**.

## License

Copyright (c) 2026 Deevo Analytics. All rights reserved.
