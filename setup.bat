@echo off
REM ──────────────────────────────────────────────────────────
REM  Muressons Corporation — First-Time Setup (Windows)
REM  Installs all dependencies, then starts the simulation
REM ──────────────────────────────────────────────────────────

echo.
echo  ========================================
echo   Muressons Corporation - Setup
echo  ========================================
echo.

REM ── Check Python ────────────────────────────
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found!
    echo   Download from: https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   Found Python %%v

REM ── Check Node.js ───────────────────────────
echo [2/4] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Node.js not found!
    echo   Download from: https://nodejs.org/
    pause
    exit /b 1
)
for /f %%v in ('node --version') do echo   Found Node.js %%v

REM ── Install Backend Dependencies ────────────
echo [3/4] Installing backend dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo   ERROR: Backend dependency install failed!
    pause
    exit /b 1
)
echo   Backend dependencies installed.

REM ── Install Frontend Dependencies ───────────
echo [4/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm install --silent
if errorlevel 1 (
    echo   ERROR: Frontend dependency install failed!
    pause
    exit /b 1
)
echo   Frontend dependencies installed.

echo.
echo  ========================================
echo   Setup Complete!
echo  ========================================
echo.
echo   Run start.bat to launch the simulation.
echo.
pause
