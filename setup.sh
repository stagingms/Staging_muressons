#!/bin/bash
# ──────────────────────────────────────────────────────────────
#  Muressons Corporation — First-Time Setup (macOS/Linux)
#  Installs all dependencies, then starts the simulation
# ──────────────────────────────────────────────────────────────

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  🏢  Muressons Corporation — Setup"
echo "  ─────────────────────────────────────────"
echo ""

# ── Check Python ────────────────────────────────
echo "[1/4] Checking Python..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "  ❌ Python not found!"
    echo "  Install: https://www.python.org/downloads/"
    echo "  Or: brew install python3  /  sudo apt install python3"
    exit 1
fi
PY=$(command -v python3 || command -v python)
echo "  ✅ $($PY --version)"

# ── Check Node.js ───────────────────────────────
echo "[2/4] Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "  ❌ Node.js not found!"
    echo "  Install: https://nodejs.org/"
    echo "  Or: brew install node  /  sudo apt install nodejs npm"
    exit 1
fi
echo "  ✅ Node.js $(node --version)"

# ── Install Backend Dependencies ────────────────
echo "[3/4] Installing backend dependencies..."
cd "$DIR/backend"
$PY -m pip install -r requirements.txt --quiet 2>/dev/null
echo "  ✅ Backend dependencies installed"

# ── Install Frontend Dependencies ───────────────
echo "[4/4] Installing frontend dependencies..."
cd "$DIR/frontend"
npm install --silent 2>/dev/null
echo "  ✅ Frontend dependencies installed"

echo ""
echo "  ========================================="
echo "  ✅ Setup Complete!"
echo "  ========================================="
echo ""
echo "  Run ./start.sh to launch the simulation."
echo ""
