#!/bin/bash
# Docker entrypoint — starts both backend and frontend
# Railway-compatible: uses $PORT for the public-facing frontend

echo "🏢 Muressons Corporation — Docker Start"

# Railway provides $PORT for the public-facing service
FRONTEND_PORT="${PORT:-3000}"

# Start backend (bound to localhost — not exposed externally)
cd /app/backend
# SEC-2: default to the durable PostgreSQL store. Set USE_MEMORY_DB=true
# explicitly (with DEBUG=true or ALLOW_MEMORY_DB_IN_PROD=true) for a
# local/offline non-durable run. main.py enforces this at startup.
export USE_MEMORY_DB="${USE_MEMORY_DB:-false}"
export BACKEND_URL="http://127.0.0.1:8000"

# audit #7: decide how many web workers are SAFE to run. scale_preflight clamps
# to 1 unless the shared Postgres backend is active (memory/offline/DEBUG mode
# cannot be split across workers — see #5). Set WEB_CONCURRENCY to scale out.
WORKERS="$(python -m scale_preflight)"
if ! [ "$WORKERS" -ge 1 ] 2>/dev/null; then
  echo "  ⚠️ scale_preflight returned '$WORKERS' — defaulting to 1 worker"
  WORKERS=1
fi
echo "  ⚙️  Backend workers: $WORKERS"

# Start backend with restart loop — if the gunicorn master crashes, restart it.
# gunicorn (uvicorn worker class) manages the individual async workers itself;
# each worker runs the FastAPI lifespan, so each rehydrates + refreshes the
# shared coordination store (#5).
(
  while true; do
    echo "  🔄 Starting backend ($WORKERS worker(s))..."
    if [ "$WORKERS" -gt 1 ]; then
      gunicorn main:app \
        -k uvicorn.workers.UvicornWorker \
        -w "$WORKERS" \
        --bind 127.0.0.1:8000 \
        --timeout 120 --graceful-timeout 30 --keep-alive 5 2>&1
    else
      # Single worker: keep the lighter uvicorn path (unchanged behaviour).
      python -m uvicorn main:app --host 127.0.0.1 --port 8000 2>&1
    fi
    EXIT_CODE=$?
    echo "  ❌ Backend exited with code $EXIT_CODE — restarting in 3s..."
    sleep 3
  done
) &
BACKEND_PID=$!

# Wait for backend to be ready
echo "  ⏳ Waiting for backend..."
for i in $(seq 1 60); do
  if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "  ✅ Backend ready!"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "  ⚠️ Backend not ready after 60s — starting frontend anyway"
  fi
  sleep 1
done

# Start frontend on Railway's PORT — with restart loop (parity with backend)
cd /app/frontend
export BACKEND_URL="http://127.0.0.1:8000"
(
  while true; do
    echo "  🔄 Starting frontend on port $FRONTEND_PORT..."
    npx next start --port "$FRONTEND_PORT" 2>&1
    EXIT_CODE=$?
    echo "  ❌ Frontend exited with code $EXIT_CODE — restarting in 3s..."
    sleep 3
  done
) &
FRONTEND_PID=$!

echo ""
echo "  ✅ Both servers running!"
echo "  Frontend:  port $FRONTEND_PORT (public)"
echo "  Backend:   port 8000 (internal)"
echo "  Admin:     /admin"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
