#!/bin/bash
# Docker entrypoint — starts both backend and frontend
# Railway-compatible: uses $PORT for the public-facing frontend

echo "🏢 Muressons Corporation — Docker Start"

# Railway provides $PORT for the public-facing service
FRONTEND_PORT="${PORT:-3000}"

# Start backend (bound to localhost — not exposed externally)
cd /app/backend
export USE_MEMORY_DB="${USE_MEMORY_DB:-true}"
export BACKEND_URL="http://127.0.0.1:8000"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "  ⏳ Waiting for backend..."
for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "  ✅ Backend ready!"
    break
  fi
  sleep 1
done

# Start frontend on Railway's PORT
cd /app/frontend
export BACKEND_URL="http://127.0.0.1:8000"
npx next start --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

echo ""
echo "  ✅ Both servers running!"
echo "  Frontend:  port $FRONTEND_PORT (public)"
echo "  Backend:   port 8000 (internal)"
echo "  Admin:     /admin"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
