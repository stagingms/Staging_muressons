# 🏢 Muressons Global Corporation

A 10-round corporate sustainability simulation spanning **5 years** (each round = 6-month semester). Lead four business units through ESG crises, investment trade-offs, and stakeholder dynamics — designed for executive education and MBA classrooms.

## 🚀 Running on a New Computer

### Prerequisites
- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/) *(check "Add to PATH")*
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)

### Option A: Setup Script + Start (Recommended)

**Windows:**
```
1. Double-click  setup.bat     ← installs all dependencies (one-time)
2. Double-click  start.bat     ← starts the simulation
```

**macOS / Linux:**
```bash
chmod +x setup.sh start.sh
./setup.sh                     # installs all dependencies (one-time)
./start.sh                     # starts the simulation
```

### Option B: Docker (Zero Setup)

If you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed:

```bash
docker compose up --build
```

That's it — both servers launch in one container. Open `http://localhost:3000`.

### Option C: Manual Start

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
USE_MEMORY_DB=true python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd frontend
npm install
npx next dev --port 3000
```

## 🌐 Access

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Player Executive Cockpit |
| http://localhost:3000/admin | God Mode (Super Admin) |
| http://localhost:3000/admin/facilitator | Facilitator Dashboard |
| http://localhost:8000/docs | API Documentation (Swagger) |

### Multiplayer (Other Devices on Same Network)

The simulation binds to `0.0.0.0`, so any device on the same WiFi/LAN can connect using the host computer's IP:

```
http://<HOST-IP>:3000          # Player cockpit
http://<HOST-IP>:3000/admin    # Admin dashboard
```

The host IP is displayed when you run `start.bat`.

## 📦 Distributing to Someone Else

1. **Zip the `muressons-sim` folder** (exclude `frontend/node_modules/` and `__pycache__/`)
2. Send the zip file
3. Recipient runs `setup.bat` (Windows) or `./setup.sh` (Mac/Linux), then `start.bat` / `./start.sh`

## How It Works

1. **Facilitator** creates a cohort in God Mode, registers players, sets decision paradigm & difficulty
2. **Players** join using their Player ID + password → land in the Executive Cockpit
3. **Each Round** — Review the crisis briefing, select a strategy, allocate investments, commit
4. **10 Rounds** — Navigate ESG challenges across Pharma, Electronics, Consumer Goods, and Software
5. **Minigames** — Unlock specialised modules each round (Green Fund, VCM Portfolio, Policy War Room, etc.)
6. **CEO Interview** — Post-game competency assessment (6 dimensions, 50/50 data/LLM scoring)
7. **Final Report** — See your Year 5 Terminal Valuation, M_R score, and corporate archetype

### Decision Paradigms

| Paradigm | Description |
|----------|-------------|
| **Narrative Crisis** (`legacy_abc`) | Classic A/B/C strategic options per round |
| **Strategic Pillars** (`multi_toggles`) | 4 independent toggles (Energy, Operations, Supply Chain, Offsetting) |
| **Advanced Climate** (`advanced_climate`) | High-risk carbon tipping point scenario — conservative pillars trigger CO₂ spirals |
| **Healthcare Edition** (`healthcare`) | NHS/private hospital setting with burnout, bed capacity, and clinical governance KPIs |

### Difficulty Tiers

| Tier | Description |
|------|-------------|
| **Standard** | Core simulation with crisis events |
| **Advanced** | + New backend engines (biodiversity, board governance, supply chain network) |
| **Expert** | + Regulatory Sandbox (SE-7) for policy design exercises |

## 🎛️ Feature Set

### Core Simulation
- 10-round narrative with 4 business units (Pharma, Electronics, Consumer Goods, Software)
- Investment Matrix (CSF pool with 120% cap + emergency credit)
- KPI Dashboard: Treasury, Reputation, CO₂, Social License, Natural Capital Debt, Synergy
- Crisis alerts, market ticker, stakeholder map, peer comparison leaderboard

### Pedagogical Minigames (auto-unlocked by round)
| Module | Round | Concept |
|--------|-------|---------|
| 🌿 Green Fund Bidding | 3 | MAC curves, green premium |
| 📊 VCM Portfolio Builder | 5 | Carbon credit integrity tiers |
| 🏛️ Policy War Room | 8 | Game-theoretic regulatory lobbying |
| 💰 ESG Refinancing Simulator | 9 | Green bond greenium / brown penalty |
| ♻️ Circular Strategy Dashboard | 10 | ReSOLVE framework, product-as-a-service |
| 🗺️ Double Materiality Matrix | 2 | CSRD impact + financial materiality |
| 🎙️ Boardroom Showdown | Final | Activist scenario negotiation |
| 🎧 AI Podcast | Every round | Dr. Priya Sharma + Prof. James Walker briefing |

### Advanced Backend Engines (12 modules)
- 🌿 Biodiversity Engine (TNFD LEAP, EHI tracking)
- 🏛️ Board Governance (shareholder resolutions, director voting)
- 🔗 Supply Chain Network (3-tier Scope 3, audit depths)
- 🌍 TCFD Scenario Analysis (orderly/disorderly/physical)
- 📈 Market Dynamics (competition response, ESG premium pricing)
- 🏦 Balance Sheet (natural capital debt, intangible valuation)
- 🏛️ Org Politics (C-suite coalition modelling)
- 🌐 NPC Stakeholders (autonomous activist/investor/media)
- 🎭 Dynamic Cases (contextual real-world case study injection)
- 🌿 Meadows Leverage Points (post-game systems analysis)
- 🔀 Branching Narrative Engine (decision-dependent storylines)
- 📡 Complexity Event Feed (emergent event generation)

### Administrative Interfaces
- **God Mode** — 20-tab super-admin dashboard: session health, audit log, archetype editor, economic tunables, crisis overrides, Boardroom Showdown config, sandbox control, facilitator registry
- **Facilitator Dashboard** — 29-tab teaching cockpit: teleprompter, cohort pulse heatmap, decision replay, annotation layer, reports & export, regulatory sandbox injection, peer evaluation, bonus awards
- **Reports & Export** — Full session analytics: terminal value, CO₂, SLO, NCD, CEO interview scores, sandbox burden, side-track grades, CSV + JSON download, per-session deep-dive panels

### Side Tracks (specialist learning paths)
- 🧭 Stakeholder Management
- 🔗 Supply Chain Due Diligence
- 📊 Sustainability Reporting (CSRD/GRI)
- ⚖️ Ethics & Sustainability

## Architecture

```
muressons-sim/
├── backend/                    # FastAPI + Python (71 modules)
│   ├── main.py                 # Entry point (auto-detects DB mode)
│   ├── engine.py               # Core math engine (CSF, M_R, Contagion)
│   ├── round_logic.py          # Round-specific mutations (R1–R10)
│   ├── router.py               # Player API endpoints (~3500 lines)
│   ├── admin_router.py         # God Mode API endpoints (~5500 lines)
│   ├── admin_teleprompter.py   # Facilitator teleprompter scripts
│   ├── admin_analytics.py      # Analytics visibility controls
│   ├── admin_resources.py      # Resource/glossary management
│   ├── regulatory_sandbox.py   # SE-7 policy design module (decay logic)
│   ├── biodiversity_engine.py  # TNFD LEAP, EHI tracking
│   ├── board_governance.py     # Shareholder resolution voting
│   ├── supply_chain_network.py # 3-tier Scope 3 audit
│   ├── tcfd_scenarios.py       # Climate scenario analysis
│   ├── meadows_leverage.py     # Systems thinking debrief
│   ├── side_tracks/            # Specialist learning path modules
│   └── tests/                  # 491 automated tests across 12 files
├── frontend/                   # Next.js 16 + React (113 components)
│   └── app/
│       ├── page.js             # Player cockpit (lobby → game → report)
│       ├── admin/              # God Mode dashboard
│       ├── admin/facilitator/  # Facilitator dashboard (29 tabs)
│       └── components/         # UI components (all wired, none dormant)
├── db/                         # Seed data (standard + healthcare)
├── setup.bat / setup.sh        # Dependency installer
├── start.bat / start.sh        # One-click launcher
├── Dockerfile                  # Container build
└── docker-compose.yml          # One-command Docker deploy
```

## Database Modes

> ⚠️ **For Classroom Sessions**: Use PostgreSQL mode (`USE_MEMORY_DB=false`) to prevent
> data loss if the server crashes. In-memory mode (`USE_MEMORY_DB=true`) is for local
> development and demos only. All session data is lost on server restart in memory mode.

| Mode | Set via | Requires |
|------|---------|----------|
| **In-Memory** (default) | `USE_MEMORY_DB=true` | Python only |
| **PostgreSQL** | `USE_MEMORY_DB=false` + `DATABASE_URL` | PostgreSQL 14+ |

In-memory mode stores all data in Python dicts. Data resets on server restart. Use for workshops and demos.

## Test Suite

```bash
# Fast (< 2 seconds)
python -m pytest backend/tests/ -q               # 425 core tests
python -m pytest backend/test_new_engines_integration.py backend/test_paradigm_parity.py -q  # 66 engine tests

# Integration (< 5 minutes)
python backend/verify_improvements.py            # 21-point engine integration check
python backend/test_full_simulation.py           # E2E: 4 paradigms × 10 rounds

# Extended (run offline — rate-limiter pacing required)
python backend/test_multiplayer.py               # 3-player × 4-paradigm multiplayer
python backend/test_hc_targeted.py               # 36-case option matrix (R1/R2/R3 × all)
```

## License

MIT
