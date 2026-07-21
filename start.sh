#!/bin/bash
# ──────────────────────────────────────────────────────────────
#  Muressons Global Command — Quick Start (macOS/Linux)
#  Launches backend (in-memory) + frontend together
# ──────────────────────────────────────────────────────────────

echo ""
echo "  🏢  Muressons Global Command — Starting..."
echo "  ─────────────────────────────────────────"
echo ""

DIR="$(cd "$(dirname "$0")" && pwd)"

# Force in-memory mode (no PostgreSQL required)
export USE_MEMORY_DB=true

# ── Backend ──────────────────────────────────
echo "[1/2] Starting backend (port 8000)..."
cd "$DIR/backend"
pip install -q fastapi uvicorn python-dotenv pydantic 2>/dev/null
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# ── Frontend ─────────────────────────────────
echo "[2/2] Starting frontend (port 3000)..."
cd "$DIR/frontend"
npm install --silent 2>/dev/null
npx next dev --port 3000 &
FRONTEND_PID=$!

echo ""
echo "  ✅  Both servers running!"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  Admin:     http://localhost:3000/admin"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop both servers..."

# Stop both on Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
