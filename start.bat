@echo off
REM ──────────────────────────────────────────────────────────
REM  Muressons Corporation — One-Click Start Script
REM  Starts both backend (port 8000) and frontend (port 3000)
REM ──────────────────────────────────────────────────────────

echo.
echo  ========================================
echo   Muressons Corporation Simulation
echo  ========================================
echo.

REM Get the local IP address for display
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
)
set LOCAL_IP=%LOCAL_IP: =%

echo  Starting Backend (port 8000)...
cd /d "%~dp0backend"
set USE_MEMORY_DB=true
start "Muressons Backend" cmd /k "python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo  Starting Frontend (port 3000)...
cd /d "%~dp0frontend"
start "Muressons Frontend" cmd /k "npm run dev -- -H 0.0.0.0"

timeout /t 5 /nobreak > nul

echo.
echo  ========================================
echo   READY! Open in browser:
echo  ========================================
echo.
echo   Player:  http://localhost:3000
echo   Admin:   http://localhost:3000/admin
echo.
echo   From other machines on your network:
echo   Player:  http://%LOCAL_IP%:3000
echo   Admin:   http://%LOCAL_IP%:3000/admin
echo.
echo   Swagger: http://localhost:8000/docs
echo  ========================================
echo.
pause
