# 🏢 Muressons Global Command

A 10-round corporate sustainability simulation. Lead four business units through ESG crises, investment trade-offs, and stakeholder dynamics.

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
| http://localhost:3000 | Player Cockpit |
| http://localhost:3000/admin | God Mode / Facilitator Dashboard |
| http://localhost:8000/docs | API Documentation |

### Multiplayer (Other Devices on Same Network)

The simulation binds to `0.0.0.0`, so any device on the same WiFi/LAN can connect using the host computer's IP:

```
http://<HOST-IP>:3000          # Player cockpit
http://<HOST-IP>:3000/admin    # Facilitator dashboard
```

The host IP is displayed when you run `start.bat`.

## 📦 Distributing to Someone Else

1. **Zip the `muressons-sim` folder** (exclude `frontend/node_modules/` and `__pycache__/`)
2. Send the zip file
3. Recipient runs `setup.bat` (Windows) or `./setup.sh` (Mac/Linux), then `start.bat` / `./start.sh`

## How It Works

1. **Facilitator** creates a cohort in God Mode, registers players, sets decision paradigm
2. **Players** join using their Player ID + password
3. **Each Round** — Review the crisis, select a strategy, allocate investments, review & commit
4. **10 Rounds** — Navigate ESG challenges across Pharma, Electronics, Consumer Goods, and Software
5. **Final Report** — See your 2050 Terminal Valuation and corporate archetype

### Decision Paradigms

| Paradigm | Description |
|----------|-------------|
| **Narrative Crisis** | Classic A/B/C options per round |
| **Strategic Pillars** | 4 independent toggles (Energy, Operations, Supply Chain, Offsetting) |

## Architecture

```
muressons-sim/
├── backend/               # FastAPI + Python
│   ├── main.py            # Entry point (auto-detects DB mode)
│   ├── engine.py          # Mathematical simulation engine
│   ├── round_logic.py     # Round-specific mutations (R1–R10)
│   ├── router.py          # Player API endpoints
│   ├── admin_router.py    # God Mode API endpoints
│   └── materiality_db.py  # Materiality dictionary management
├── frontend/              # Next.js + React
│   └── app/
│       ├── page.js        # Player cockpit (lobby → game → report)
│       ├── admin/page.js  # God Mode dashboard
│       └── components/    # UI components
├── setup.bat / setup.sh   # Dependency installer
├── start.bat / start.sh   # One-click launcher
├── Dockerfile             # Container build
└── docker-compose.yml     # One-command Docker deploy
```

## Database Modes

| Mode | Set via | Requires |
|------|---------|----------|
| **In-Memory** (default) | `USE_MEMORY_DB=true` | Python only |
| **PostgreSQL** | `USE_MEMORY_DB=false` + `DATABASE_URL` | PostgreSQL 14+ |

In-memory mode stores all data in Python dicts. Data resets on server restart. Use for workshops and demos.

## License

MIT
