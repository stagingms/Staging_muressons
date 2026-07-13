@echo off
REM ============================================================================
REM  commit_stakeholder.cmd  -  clear the stale git lock and commit the COMPLETE
REM  stakeholder-realism implementation (all files, incl. the 2 new untracked
REM  ones) in one shot. Double-click it, or run it from Command Prompt.
REM
REM  It commits ONLY the stakeholder files -- your other work in progress
REM  (main.py, page.js, auth_jwt.py, etc.) is left untouched.
REM ============================================================================
setlocal
cd /d "%~dp0"

echo.
echo == Step 0: is a git process still running? ==
tasklist /fi "imagename eq git.exe" 2>nul | find /i "git.exe" >nul
if not errorlevel 1 (
  echo   [!] git.exe is RUNNING in the background -- almost certainly the
  echo       Antigravity IDE watching this folder. CLOSE THE IDE COMPLETELY,
  echo       then re-run this script. ^(A live git process re-creates the locks
  echo       faster than we can clear them.^)
  echo.
  choice /c YN /m "Try anyway (Y) or stop so you can close the IDE (N)"
  if errorlevel 2 ( pause & exit /b 1 )
)

echo.
echo == Step 1: clear ALL stale git locks ==
del /f /q ".git\index.lock"  2>nul
del /f /q ".git\HEAD.lock"   2>nul
del /f /q ".git\config.lock" 2>nul
del /f /q /s ".git\refs\*.lock" 2>nul
if exist ".git\index.lock" goto :locked
if exist ".git\HEAD.lock"  goto :locked
echo   [OK] locks cleared
goto :staged
:locked
echo   [!] A lock could not be deleted -- a git process still holds it.
echo       Close the Antigravity IDE (and any open Git window), then re-run.
pause
exit /b 1
:staged

echo.
echo == Step 2: stage the complete stakeholder set ==
git add ^
  backend/config.py ^
  backend/npc_stakeholders.py ^
  backend/round_logic.py ^
  backend/engine.py ^
  backend/systemic_risk_engine.py ^
  backend/autonomous_agents.py ^
  backend/pedagogical_engine.py ^
  backend/models.py ^
  backend/admin_router.py ^
  backend/router.py ^
  backend/stakeholder_engagement.py ^
  backend/tests/test_stakeholder_golden_trace.py ^
  backend/tests/golden/stakeholder_slo_trace.json ^
  frontend/app/components/CreateCohortModal.js ^
  frontend/app/components/StakeholderIntelRail.jsx
if errorlevel 1 (
  echo   [!] git add failed -- see the message above.
  pause
  exit /b 1
)
echo   [OK] staged. Files going into this commit:
git diff --cached --name-only

echo.
echo == Step 3: commit (only the staged stakeholder files) ==
git commit -m "feat(stakeholder): F1-F6 realism waves on NPC + 5-agent engines, golden oracle, per-cohort toggles (all waves default-off)" -- ^
  backend/config.py ^
  backend/npc_stakeholders.py ^
  backend/round_logic.py ^
  backend/engine.py ^
  backend/systemic_risk_engine.py ^
  backend/autonomous_agents.py ^
  backend/pedagogical_engine.py ^
  backend/models.py ^
  backend/admin_router.py ^
  backend/router.py ^
  backend/stakeholder_engagement.py ^
  backend/tests/test_stakeholder_golden_trace.py ^
  backend/tests/golden/stakeholder_slo_trace.json ^
  frontend/app/components/CreateCohortModal.js ^
  frontend/app/components/StakeholderIntelRail.jsx
if errorlevel 1 (
  echo   [!] commit failed -- see the message above.
  pause
  exit /b 1
)

echo.
echo == Done. Latest commit: ==
git log --oneline -1
echo.
echo (Docs like the SPEC, checklist and .docx manuals are NOT in this commit --
echo  add them separately if you want them versioned.)
echo.
pause
