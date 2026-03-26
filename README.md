# Deevo Sim

**Simulation Intelligence Engine for GCC Scenarios**

Deevo Sim transforms real-world events into interactive, agent-based simulations. Input a scenario — a policy change, price hike, or social trigger — and watch it propagate through a network of GCC-specific personas, producing predictive intelligence on how public reaction might unfold.

This is not a chatbot. This is not a dashboard. This is a **system experience**.

---

## Architecture

```
deevo-sim/
├── frontend/     Next.js 14 · TypeScript · Tailwind CSS · React Flow · Framer Motion
├── backend/      FastAPI · Python 3.11+ · Pydantic v2 · Async Services
└── seeds/        JSON seed data (scenarios, agents, graphs, simulations)
```

**Pipeline:** Scenario Input → Entity Extraction → Graph Build → Agent Generation → Simulation → Intelligence Brief → Analyst Query

---

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## Deploy to Vercel

1. Import the `deevo-sim` repository
2. Set **Root Directory** to `frontend`
3. Framework auto-detects as **Next.js**
4. Deploy

---

## License

Proprietary — Deevo Analytics. All rights reserved.
