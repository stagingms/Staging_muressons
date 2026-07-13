<#
.SYNOPSIS
  Automate Steps 0-2 of the stakeholder module ship (Windows / PowerShell).
    0. config integrity check   (are the wave constants present?)
    1. clear stale bytecode + run the golden oracle twice (write, then enforce)
    2. run the tripwires (+ optional full backend suite with -Full)

.EXAMPLE
  .\ship_stakeholder.ps1
  .\ship_stakeholder.ps1 -Full
  .\ship_stakeholder.ps1 -Rebaseline

.NOTES
  Run from the repo root (or anywhere inside it) in a normal PowerShell window.
  Requires Python + pytest on PATH (python -m pytest --version must work).
  Exits non-zero if any must-pass step fails, so it's CI-friendly.
#>
[CmdletBinding()]
param(
  [switch]$Full,        # also run the entire backend suite (slower)
  [switch]$Rebaseline   # regenerate the golden baseline on purpose
)

$ErrorActionPreference = 'Continue'

function Say-Ok   ($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function Say-Warn ($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Say-Fail ($m){ Write-Host "[FAIL] $m" -ForegroundColor Red }
function Say-Head ($m){ Write-Host ""; Write-Host "== $m ==" -ForegroundColor Cyan }

$StepFail = 0

# ── locate repo / backend dir ──
$root = (& git rev-parse --show-toplevel 2>$null)
if (-not $root) { $root = (Get-Location).Path }
if     (Test-Path (Join-Path $root 'backend\config.py')) { $be = Join-Path $root 'backend' }
elseif ((Test-Path (Join-Path $root 'config.py')) -and (Test-Path (Join-Path $root 'tests'))) { $be = $root }
else { Say-Fail "cannot find the backend directory (need backend\config.py). Run from the repo."; exit 2 }
Say-Ok "backend dir: $be"

# ── python + pytest ──
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python3 -ErrorAction SilentlyContinue).Source }
if (-not $py) { Say-Fail "python not found on PATH"; exit 2 }
& $py -m pytest --version *> $null
if ($LASTEXITCODE -ne 0) {
  Say-Fail "pytest not available for $py. Install: pip install -r `"$be\requirements.txt`" pytest"; exit 2
}

# ── STEP 0: config integrity ──
Say-Head "Step 0 - config integrity"
$cfg = Join-Path $be 'config.py'
$needed = @('TRUST_GAIN_RATE','STAKEHOLDER_SLO_COUPLING','ENGAGE_TOWNHALL_COST','COALITION_STRIKE_GAIN',
            'THRESHOLD_JITTER','NPC_SENTIMENT_BRIDGE_WEIGHT','PROMISE_KEPT_TRUST_BONUS','PATIENCE_LIMIT')
$missing = @()
foreach ($k in $needed) {
  if (-not (Select-String -Path $cfg -Pattern "^$k[: ]" -Quiet)) { $missing += $k }
}
if ($missing.Count -eq 0) {
  Say-Ok "all $($needed.Count) stakeholder wave constants present in config.py"
} else {
  Say-Fail "config.py is MISSING $($missing.Count) constant(s): $($missing -join ', ')"
  Say-Warn "the waves will silently no-op until these are restored (see STAKEHOLDER_SHIP_CHECKLIST.md)"
  $StepFail = 1
}

# ── STEP 1: clear bytecode + golden oracle ──
Say-Head "Step 1 - clear bytecode + golden oracle"
Get-ChildItem -Path $be -Recurse -Include *.pyc -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $be -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Say-Ok "cleared stale .pyc / __pycache__"

$golden = Join-Path $be 'tests\golden\stakeholder_slo_trace.json'
Push-Location $be
try {
  if ($Rebaseline) {
    Say-Warn "rebaseline requested - regenerating the golden baseline"
    $env:MURESSONS_REBASELINE_GOLDEN = '1'
    & $py -m pytest tests\test_stakeholder_golden_trace.py -q
    Remove-Item Env:\MURESSONS_REBASELINE_GOLDEN -ErrorAction SilentlyContinue
  }

  if (-not (Test-Path $golden)) {
    Write-Host "  no baseline yet -> first run will write it"
    & $py -m pytest tests\test_stakeholder_golden_trace.py -q
    if (Test-Path $golden) { Say-Ok "golden baseline written: tests\golden\stakeholder_slo_trace.json (review + commit it)" }
    else { Say-Fail "golden baseline was not written - check the run above"; $StepFail = 1 }
  } else {
    Say-Ok "existing golden baseline found"
  }

  Write-Host "  enforcing run (must pass, no skips):"
  & $py -m pytest tests\test_stakeholder_golden_trace.py -q
  if ($LASTEXITCODE -eq 0) { Say-Ok "stakeholder suite green (golden enforced + all wave unit tests pass)" }
  else { Say-Fail "stakeholder suite FAILED - inspect the assertion messages above"; $StepFail = 1 }

  # ── STEP 2: tripwires (+ optional full suite) ──
  Say-Head "Step 2 - tripwires"
  $trip = @('tests\test_role_hierarchy_sync.py','tests\test_qa_monte_carlo.py',
            'tests\test_universal_math_engine.py','tests\test_shockwave_catalog_endpoint.py')
  $existing = @($trip | Where-Object { Test-Path $_ })
  if ($existing.Count -gt 0) {
    & $py -m pytest @existing -q
    if ($LASTEXITCODE -eq 0) { Say-Ok "tripwires green" } else { Say-Fail "a tripwire FAILED"; $StepFail = 1 }
  } else { Say-Warn "no tripwire test files found (skipping)" }

  if ($Full) {
    Say-Head "Step 2b - full backend suite (-Full)"
    & $py -m pytest tests\ -q
    if ($LASTEXITCODE -eq 0) { Say-Ok "full backend suite green" }
    else { Say-Fail "full suite has failures (review; some may be pre-existing/infra)"; $StepFail = 1 }
  }
}
finally { Pop-Location }

# ── summary ──
Say-Head "Summary"
if ($StepFail -eq 0) {
  Say-Ok "ALL CHECKS PASSED"
  Write-Host "  Next: git add `"$golden`" then git commit the reviewed baseline,"
  Write-Host "  then enable the per-cohort toggles (Memory -> SLO feedback -> Promises first) and playtest."
  exit 0
} else {
  Say-Fail "ONE OR MORE STEPS FAILED - see above (start with Step 0 if config constants were missing)"
  exit 1
}
