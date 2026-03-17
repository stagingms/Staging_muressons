#!/bin/bash
# Docker entrypoint — starts both backend and frontend

echo "🏢 Muressons Corporation — Docker Start"

# Start backend
cd /app/backend
export USE_MEMORY_DB=true
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd /app/frontend
npx next start --port 3000 &
FRONTEND_PID=$!

echo ""
echo "  ✅ Both servers running!"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  Admin:     http://localhost:3000/admin"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
