@echo off
REM ============================================================================
REM  finish_stakeholder_docs.cmd
REM   1) clears any stale git lock
REM   2) deletes the _docgen temp folder (render junk)
REM   3) commits ONLY the stakeholder documentation (spec, checklist, reference,
REM      the updated manuals + SDD) -- nothing else is touched.
REM  Close the Antigravity IDE first (it holds git locks). Double-click to run.
REM ============================================================================
setlocal
cd /d "%~dp0"

echo.
echo == Step 1: clear stale git locks ==
del /f /q ".git\index.lock"  2>nul
del /f /q ".git\HEAD.lock"   2>nul
del /f /q ".git\config.lock" 2>nul
del /f /q /s ".git\refs\*.lock" 2>nul
if exist ".git\index.lock" goto :locked
if exist ".git\HEAD.lock"  goto :locked
echo   [OK] locks cleared
goto :cleanup
:locked
echo   [!] A git process still holds a lock -- close the Antigravity IDE and re-run.
pause
exit /b 1

:cleanup
echo.
echo == Step 2: delete _docgen temp folder ==
if exist "_docgen" (
  rmdir /s /q "_docgen"
  if exist "_docgen" ( echo   [!] could not delete _docgen ^(a file may be open^) ) else ( echo   [OK] _docgen removed )
) else (
  echo   [OK] no _docgen folder
)

echo.
echo == Step 3: stage the stakeholder docs ==
REM  git add silently skips any path that doesn't exist / isn't changed.
git add ^
  SPEC_Muressons_Stakeholder_SLO_Realism_v1.md ^
  STAKEHOLDER_SHIP_CHECKLIST.md ^
  Muressons_Stakeholder_Module_Reference_v1.1.docx ^
  Muressons_Simulation_Design_Document_v1.1_updated.docx ^
  "docs/Muressons_Facilitator_Manual_v10.docx" ^
  "docs/Muressons_Facilitator_Operations_Manual.docx" ^
  "docs/Muressons_Student_Manual_v10.docx"  2>nul
echo   Files staged for this commit:
git diff --cached --name-only

echo.
echo == Step 4: commit ==
git commit -m "docs(stakeholder): spec, ship checklist, module reference, updated facilitator/student manuals + SDD" -- ^
  SPEC_Muressons_Stakeholder_SLO_Realism_v1.md ^
  STAKEHOLDER_SHIP_CHECKLIST.md ^
  Muressons_Stakeholder_Module_Reference_v1.1.docx ^
  Muressons_Simulation_Design_Document_v1.1_updated.docx ^
  "docs/Muressons_Facilitator_Manual_v10.docx" ^
  "docs/Muressons_Facilitator_Operations_Manual.docx" ^
  "docs/Muressons_Student_Manual_v10.docx"  2>nul
if errorlevel 1 (
  echo   [i] Nothing to commit, or commit skipped ^(docs may already be committed^).
) else (
  echo   [OK] docs committed.
)

echo.
echo == Latest commits ==
git log --oneline -3
echo.
pause
