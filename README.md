# DecisionCore Intelligence — GCC Decision Intelligence Platform

**Phase 12: Hardening Layer**

A mathematically grounded, graph-native decision intelligence system for Global Connectivity and Criticality (GCC) scenario analysis. DecisionCore Intelligence ingests multi-source geopolitical and infrastructure data, normalizes it to a canonical schema, constructs a 76-node GCC entity graph, runs propagation simulations, scores risk holistically, and produces explainable decision recommendations with mitigation strategies.

**Status**: Pilot (Live: https://deevo-sim.vercel.app/demo)

---

## Quick Start

```bash
# 1. Clone and navigate
git clone <repo>
cd deevo-sim

# 2. Install dependencies
make install

# 3. Start services
make dev

# 4. Access the platform
# API:       http://localhost:8000 (docs at /api/docs)
# Frontend:  http://localhost:3000
# Neo4j:     http://localhost:7474 (browse graph)
```

---

## Tech Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Backend** | FastAPI | 0.115+ | REST API + WebSocket server |
| **Database** | PostgreSQL + PostGIS | 16 | Relational data + geospatial queries |
| **Graph DB** | Neo4j | 5.x | Entity relationships + propagation paths |
| **Cache** | Redis | 7.x | Session cache + task queue |
| **Frontend** | Next.js 14 | 14.2+ | React-based control room UI |
| **Python** | 3.11+ | - | Async backend + simulation engine |
| **Node** | LTS | 20+ | Frontend build & runtime |
| **Docker** | 20.10+ | - | Containerization |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (CesiumJS Globe)                 │
│              Real-time scenario visualization                │
└────────────────────────┬────────────────────────────────────┘
                         │ REST / WebSocket
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │ Health/Auth  │ Scenarios    │ Graph Intelligence       │ │
│  ├──────────────┼──────────────┼──────────────────────────┤ │
│  │ Data Ingest  │ Entity CRUD  │ Propagation Simulation   │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└────────┬─────────────────┬─────────────────────┬────────────┘
         │                 │                     │
    ┌────↓─────┐    ┌─────↓──────┐     ┌───────↓───────┐
    │PostgreSQL │    │   Neo4j    │     │    Redis      │
    │ (Schema)  │    │  (Graph)   │     │  (Cache/Q)    │
    └───────────┘    └────────────┘     └───────────────┘
```

**Data Flow:**
1. **Ingest** — ACLED API, aviation feeds, maritime AIS, manual uploads
2. **Normalize** — Map to 41 canonical schema models (9 Pydantic modules)
3. **Graph** — Entity extraction, relationship creation in Neo4j (76 nodes, 190+ edges)
4. **Risk Score** — Multi-factor risk assessment (threat field, exposure, confidence)
5. **Propagation** — Discrete dynamic simulation across corridor network
6. **Decision** — Urgency + recommendation engine with mitigation effectiveness
7. **Output** — REST API + 3D globe visualization with explainability

---

## Key Features

### 1. Canonical Schema
- **9 Pydantic modules**, **41 models**: Event, Airport, Port, Flight, Vessel, Corridor, Region, Route, RiskScore
- **Language-aware**: English + Arabic fields for GCC region
- **Validated**: Type hints, constraints, enum validation

### 2. GCC Entity Graph
- **76 nodes**: 12 regions, 30 airports, 20 ports, 14 risk categories
- **190+ edges**: Flight routes, shipping corridors, region adjacency, propagation paths
- **Neo4j APOC**: Shortest path, centrality, community detection

### 3. Risk & Physics
- **Risk Score Model**: Threat field + exposure + confidence (0-1 scale)
- **Physics Modules**: Threat field diffusion, flow field simulation, pressure distribution, shockwave propagation
- **Insurance Risk**: Sector-specific loss functions for aviation, maritime, trade

### 4. Scenario Templates
- **15 preconfigured GCC scenarios**: Hormuz closure, Suez canal disruption, cyber attacks, pandemics, etc.
- **Customizable parameters**: Severity, duration, impact radius
- **Deterministic simulation**: Same input = same output (for debugging)

### 5. Decision Engine
- **5-question model**: What happened? Where? How bad? What breaks? What do we do?
- **Explainability**: All scores include component breakdown
- **Mitigation Effectiveness**: Confidence-weighted action recommendations

### 6. API
- **RESTful** `/api/v1/` with OpenAPI docs
- **Async**: Leverages Python asyncio for concurrency
- **Health checks**: Liveness probes for all backends

---

## Directory Structure

```
deevo-sim/
├── Makefile                          # Project task runner
├── README.md                         # This file
├── docker-compose.yml                # Multi-service orchestration
├── LICENSE
│
├── backend/                          # FastAPI Python backend
│   ├── requirements.txt              # Python dependencies
│   ├── pyproject.toml               # Project metadata + tool config
│   ├── .env.example                 # Environment template
│   │
│   ├── app/
│   │   ├── main.py                  # FastAPI app + lifespan
│   │   ├── config/
│   │   │   └── settings.py          # Pydantic settings loader
│   │   │
│   │   ├── schema/                  # 9 Pydantic v2 modules
│   │   │   ├── core.py              # Base models
│   │   │   ├── event.py             # Event + EventType
│   │   │   ├── geography.py         # Airport, Port, Region, Corridor
│   │   │   ├── aviation.py          # Flight, FlightStatus
│   │   │   ├── maritime.py          # Vessel, VesselType
│   │   │   ├── routing.py           # Route, RouteType
│   │   │   ├── risk.py              # RiskScore, RiskLevel
│   │   │   ├── simulation.py        # Simulation models
│   │   │   └── decision.py          # Decision output models
│   │   │
│   │   ├── db/                      # SQLAlchemy ORM models
│   │   │   ├── base.py              # Base declarative model\n│   │   ├── models.py            # All table models\n│   │   └── session.py              # Async session factory\n│   │\n│   │   ├── api/                     # FastAPI routers\n│   │   │   ├── health.py            # /health, /version\n│   │   │   ├── scenarios.py         # /scenarios (list + details)\n│   │   │   ├── entities.py          # /entities (CRUD)\n│   │   │   ├── graph.py             # /graph (intelligence)\n│   │   │   ├── ingest.py            # /ingest (data upload)\n│   │   │   ├── pipeline.py          # /pipeline (status)\n│   │   │   └── auth.py              # /auth (if needed)\n│   │   │\n│   │   ├── services/                # Business logic layer\n│   │   │   ├── orchestrator.py      # Lifecycle orchestrator\n│   │   │   ├── normalization.py     # Schema normalization\n│   │   │   ├── graph_ingestion.py   # Neo4j writing\n│   │   │   ├── graph_query.py       # Neo4j querying\n│   │   │   ├── scoring_service.py   # Risk score computation\n│   │   │   ├── physics_service.py   # Physics simulation\n│   │   │   ├── insurance_service.py # Insurance risk\n│   │   │   ├── enrichment.py        # Data enrichment\n│   │   │   └── pipeline_status.py   # Pipeline tracking (Redis)\n│   │   │\n│   │   ├── models/                  # Mathematical modules\n│   │   │   ├── risk/                # Risk score model\n│   │   │   ├── spatial/             # Spatial analysis\n│   │   │   ├── temporal/            # Time-based decay\n│   │   │   ├── propagation/         # Discrete propagation sim\n│   │   │   ├── exposure/            # Exposure calculation\n│   │   │   ├── confidence/          # Confidence scoring\n│   │   │   ├── physics/             # Physics modules\n│   │   │   │   ├── threat_field.py\n│   │   │   │   ├── flow_field.py\n│   │   │   │   ├── pressure.py\n│   │   │   │   ├── shockwave.py\n│   │   │   │   ├── diffusion.py\n│   │   │   │   ├── routing.py\n│   │   │   │   └── system_stress.py\n│   │   │   └── insurance/           # Insurance models\n│   │   │       ├── aviation.py\n│   │   │       ├── maritime.py\n│   │   │       └── trade.py\n│   │   │\n│   │   ├── intelligence/            # Intelligence layer\n│   │   │   ├── scenario_engine.py   # Run scenario\n│   │   │   ├── decision_engine.py   # 5-question model\n│   │   │   └── recommendation.py    # Action suggestions\n│   │   │\n│   │   ├── scenarios/               # Scenario definitions\n│   │   │   ├── templates.py         # 15 scenario templates\n│   │   │   ├── hormuz_closure.py\n│   │   │   ├── suez_disruption.py\n│   │   │   ├── cyber_attack.py\n│   │   │   └── ... (12 more)\n│   │   │\n│   │   ├── connectors/              # External data connectors\n│   │   │   ├── acled.py             # ACLED API\n│   │   │   ├── aviation.py          # Aviation feeds\n│   │   │   ├── maritime.py          # AIS data\n│   │   │   └── manual.py            # Manual import\n│   │   │\n│   │   ├── graph/                   # Neo4j integration\n│   │   │   ├── client.py            # Async Neo4j driver\n│   │   │   └── schema.py            # Graph schema definition\n│   │   │\n│   │   └── simulation/              # Simulation engine\n│   │       ├── propagation.py       # Propagation algorithm\n│   │       └── discrete_time.py     # Discrete time stepping\n│   │\n│   ├── tests/                       # Pytest test suite\n│   │   ├── conftest.py              # Shared fixtures\n│   │   ├── test_integration.py      # Integration tests\n│   │   ├── test_schema_validation.py # Schema validation\n│   │   ├── api/                     # API endpoint tests\n│   │   ├── schema/                  # Schema tests\n│   │   ├── scenarios/               # Scenario tests\n│   │   └── ... (more test modules)\n│   │\n│   ├── seeds/                       # Seed data\n│   │   ├── events.json              # 175 canonical events\n│   │   ├── airports.json            # 30 GCC airports\n│   │   ├── ports.json               # 20 GCC ports\n│   │   ├── corridors.json           # 15 major corridors\n│   │   ├── flights.json             # Sample flight data\n│   │   ├── vessels.json             # Sample vessel data\n│   │   └── actors.json              # Threat actors\n│   │\n│   └── migrations/                  # Alembic DB migrations\n│       └── versions/\n│\n├── frontend/                        # Next.js React frontend\n│   ├── package.json\n│   ├── tsconfig.json\n│   ├── tailwind.config.js\n│   ├── .env.example\n│   │\n│   ├── app/\n│   │   ├── layout.tsx              # Root layout\n│   │   ├── page.tsx                # Home page\n│   │   ├── demo/\n│   │   │   └── page.tsx            # Command center (CesiumJS globe)\n│   │   ├── api/                    # API routes (if running serverless)\n│   │   │   ├── health/\n│   │   │   ├── scenarios/\n│   │   │   ├── run-scenario/\n│   │   │   └── ...\n│   │   └── ...\n│   │\n│   ├── components/                 # React components\n│   │   ├── GlobeViewer.tsx         # CesiumJS globe widget\n│   │   ├── ScenarioPanel.tsx       # Scenario selector\n│   │   ├── DetailPanel.tsx         # Entity details\n│   │   ├── DecisionOutput.tsx      # Decision recommendations\n│   │   └── ...\n│   │\n│   ├── lib/                        # Utilities & helpers\n│   │   ├── gcc-graph.ts            # 76-node GCC graph\n│   │   ├── propagation-engine.ts   # Client-side propagation\n│   │   ├── scenario-engines.ts     # 15 scenario formulas\n│   │   ├── decision-engine.ts      # 5-question model\n│   │   ├── server/\n│   │   │   ├── auth.ts             # API key validation\n│   │   │   ├── execution.ts        # Pipeline executor\n│   │   │   ├── audit.ts            # Audit logging\n│   │   │   └── store.ts            # Result persistence\n│   │   └── ...\n│   │\n│   └── public/                     # Static assets\n│       ├── fonts/\n│       └── images/\n│\n├── docs/                           # Documentation\n│   ├── ROADMAP.md                  # Phase breakdown\n│   ├── RUNBOOK.md                  # Operator runbook\n│   ├── SCHEMA.md                   # Schema reference\n│   ├── API.md                      # API documentation\n│   └── DEPLOYMENT.md               # Deployment guide\n│\n└── .github/                        # GitHub config\n    ├── workflows/\n    │   └── ci.yml                  # CI/CD pipeline\n    └── ...\n```

---

## Development Setup

### Prerequisites
- **Python** 3.11+
- **Node.js** 18+ (LTS)
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Make** (for running tasks)

### Environment Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Backend env vars (DC7_ prefix)
DC7_ENVIRONMENT=development
DC7_POSTGRES_HOST=postgres
DC7_NEO4J_URI=bolt://neo4j:7687
DC7_REDIS_URL=redis://redis:6379/0
DC7_ALLOWED_ORIGINS=http://localhost:3000

# Optional: ACLED API
DC7_ACLED_API_KEY=your_key
DC7_ACLED_API_EMAIL=your_email
```

### First Run

```bash
# Install all dependencies
make install

# Start all services (Docker + databases)
make dev

# In another terminal, seed the databases
make seed              # PostgreSQL
make seed-graph        # Neo4j

# Visit the dashboard
# API docs: http://localhost:8000/api/docs
# Frontend: http://localhost:3000
```

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (no prefix needed) |
| GET | `/scenarios` | List all 15 scenario templates |
| GET | `/scenarios/{id}` | Get scenario details |
| POST | `/scenarios/run` | Execute scenario simulation |
| POST | `/scenarios/decision` | Get decision recommendations |
| GET | `/entities` | List all entities (airports, ports, etc.) |
| GET | `/entities/{id}` | Get entity details |
| GET | `/graph/nodes` | List all graph nodes |
| GET | `/graph/edges` | List all graph edges |
| POST | `/graph/query` | Execute Cypher query |
| POST | `/ingest/events` | Upload event data |
| POST | `/ingest/flights` | Upload flight data |
| GET | `/pipeline/status` | Get pipeline status |

### Example: Run Hormuz Closure Scenario

```bash
curl -X POST http://localhost:8000/api/v1/scenarios/run \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "hormuz_closure",
    "severity": 0.8,
    "duration_days": 30
  }'
```

**Response:**
```json
{
  "run_id": "run_20260331_001",
  "scenario_id": "hormuz_closure",
  "status": "completed",
  "duration_seconds": 2.34,
  "node_impacts": {
    "oil_supply": 0.95,
    "shipping_lanes": 0.88,
    "global_trade": 0.72
  },
  "sector_impacts": {
    "aviation": 0.65,
    "maritime": 0.92,
    "trade": 0.78
  },
  "decisions": {
    "what_happened": "Strait of Hormuz blockade simulated",
    "where": "Persian Gulf region, impact zones: [UAE, Saudi, Iran]",
    "how_bad": "Critical (score: 0.85)",
    "what_breaks": ["Oil exports", "Container shipping", "Aviation fuel supply"],
    "what_do_we_do": [
      {
        "action": "Activate emergency reserves",
        "urgency": "immediate",
        "effectiveness": 0.72
      },
      {
        "action": "Reroute shipping via Suez/Red Sea",
        "urgency": "high",
        "effectiveness": 0.58
      }
    ]
  }
}
```

---

## Running Tests

### All Tests
```bash
make test
```

### Backend Only
```bash
make test-backend
```

### Integration Tests
```bash
make test-integration
```

### Test Coverage
```bash
cd backend && PYTHONPATH=. pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Seed Data

The platform includes 175+ canonical seed records:

### Load Seed Data

```bash
# PostgreSQL (relational schema)
make seed

# Neo4j (entity graph)
make seed-graph
```

### Seed Components
- **Events**: 175 historical GCC events with bilingual descriptions
- **Airports**: 30 IATA-coded major GCC airports
- **Ports**: 20 major GCC maritime ports with coordinates
- **Corridors**: 15 critical supply chain corridors (air + sea + land)
- **Flights**: 25 sample flights across the network
- **Vessels**: 20 sample vessels with AIS data
- **Actors**: 15 threat actors with profiles

---

## Scenario Templates (15 Total)

| Scenario ID | Description | Severity | Region |
|-------------|-------------|----------|--------|
| `hormuz_closure` | Strait of Hormuz blockade | 0.9 | Persian Gulf |
| `suez_disruption` | Suez Canal incident | 0.85 | Red Sea |
| `cyber_attack` | Critical infrastructure cyber attack | 0.8 | Multi-region |
| `pandemics_variant` | New pandemic variant outbreak | 0.7 | Global |
| `saudi_instability` | Saudi Arabia political instability | 0.75 | Arabian Peninsula |
| `iran_escalation` | Iran-Israel escalation | 0.8 | Levant |
| `uae_isolation` | UAE diplomatic isolation | 0.6 | Gulf |
| `yemen_cholera` | Yemen cholera outbreak | 0.65 | Yemen |
| `iraq_unrest` | Iraq civil unrest | 0.7 | Mesopotamia |
| `syria_crisis` | Syria humanitarian crisis | 0.75 | Levant |
| `turkey_earthquake` | Turkey major earthquake | 0.8 | Anatolia |
| `mediterranean_storm` | Mediterranean supply chain disruption | 0.65 | Mediterranean |
| `gulf_piracy` | Piracy surge in Arabian Sea | 0.7 | Arabian Sea |
| `aviation_fuel_shortage` | Global aviation fuel shortage | 0.72 | Global |
| `trade_war` | Regional trade war escalation | 0.68 | GCC-wide |

---

## Configuration Reference

### Backend (Python) Configuration

```ini
# app/config/settings.py

# Application
APP_NAME = "DecisionCore Intelligence"
ENVIRONMENT = "development" # development | pilot | production
DEBUG = False
LOG_LEVEL = "INFO"

# Database
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "decision_core"
POSTGRES_USER = "dc7"
POSTGRES_PASSWORD = "dc7_pilot_2026"

# Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "dc7_graph_2026"

# Redis
REDIS_URL = "redis://localhost:6379/0"

# API
API_PREFIX = "/api/v1"
ALLOWED_ORIGINS = "http://localhost:3000"
API_TIMEOUT = 30  # seconds
```

### Frontend (Node.js) Configuration

```bash
# .env.local (Next.js)

REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

---

## Project Structure: Detailed Explanation

### Backend Organization

**Schema Layer** (`app/schema/`)
- 9 Pydantic v2 modules with 41 canonical models
- Bilingual support (English + Arabic)
- Type validation, constraints, enum enforcement
- Example: `schema.event.Event` with 15+ attributes

**Services Layer** (`app/services/`)
- **Normalization**: Map external data to canonical models
- **Graph Ingestion**: Write normalized data to Neo4j
- **Graph Query**: Read from Neo4j for intelligence
- **Scoring**: Risk score computation (0-1 scale)
- **Physics**: Threat field, flow field, pressure, shockwave
- **Insurance**: Sector-specific loss functions
- **Enrichment**: Add context (weather, time of day, etc.)

**Models Layer** (`app/models/`)
- Mathematical modules for risk, spatial, temporal, propagation
- Physics simulation (threat field diffusion, etc.)
- Insurance loss estimation by sector

**Intelligence Layer** (`app/intelligence/`)
- **Scenario Engine**: Run parameterized scenarios
- **Decision Engine**: 5-question model (what/where/how bad/what breaks/what do)
- **Recommendation Engine**: Mitigation effectiveness scoring

**API Layer** (`app/api/`)
- RESTful endpoints (OpenAPI-documented)
- WebSocket for real-time updates
- Async request handling

### Frontend Organization

**Components** (`components/`)
- GlobeViewer: CesiumJS 3D globe
- ScenarioPanel: Scenario selector + parameter tuning
- DetailPanel: Entity information (airports, ports, etc.)
- DecisionOutput: Recommendations + urgency + effectiveness

**Libraries** (`lib/`)
- `gcc-graph.ts`: 76-node GCC entity graph (in-memory)
- `propagation-engine.ts`: Discrete dynamic simulation (client-side)
- `scenario-engines.ts`: 15 scenario formula engines
- `decision-engine.ts`: 5-question decision model
- Server-side utilities: auth, audit, execution, store

---

## Contributing

### Code Quality

```bash
# Lint and format all code
make format
make lint

# Run full CI pipeline
make check
```

### Git Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `make test`
3. Commit with clear message: `git commit -m "feat: describe change"`
4. Push and create pull request

### Testing Requirements

- Unit tests for all new functions
- Integration tests for cross-module interactions
- API tests for new endpoints
- Coverage target: 80%+

---

## Troubleshooting

### Services Won't Start

```bash
# Check service status
make status

# View logs
make logs

# Restart all services
make down && make dev
```

### Database Issues

```bash
# Reset databases (WARNING: destructive)
make clean
make dev
make seed
```

### Port Conflicts

If ports are already in use, update `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change 8001 to your desired port
```

### Tests Failing

```bash
# Run specific test with verbose output
cd backend && PYTHONPATH=. pytest tests/test_integration.py -v --tb=long
```

---

## Production Deployment

### Environment: Pilot

```bash
DC7_ENVIRONMENT=pilot
DC7_DEBUG=false
DC7_LOG_LEVEL=INFO
DC7_POSTGRES_HOST=pilot-db.example.com
DC7_NEO4J_URI=bolt://pilot-graph.example.com:7687
```

### Environment: Production

```bash
DC7_ENVIRONMENT=production
DC7_DEBUG=false
DC7_LOG_LEVEL=WARNING
# Use managed database services (AWS RDS, Azure CosmosDB, etc.)
```

### Deployment to Vercel

1. Push code to GitHub
2. Import repository in Vercel dashboard
3. Set **Root Directory** to `frontend`
4. Configure environment variables
5. Deploy

---

## License

Proprietary — Deevo Analytics. All rights reserved.

---

## Support

For issues, questions, or contributions, contact the DecisionCore Intelligence team.

**Last Updated**: 2026-03-31 (Phase 12 Hardening)
