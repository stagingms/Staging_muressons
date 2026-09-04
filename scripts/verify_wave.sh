#!/usr/bin/env bash
# verify_wave.sh — the end-of-wave gate for the audit remediation branch
# (PLAN_Audit_Remediation_2026-09-04.md, step 0.4 / "Wave N acceptance gate").
#
# Runs, in order, and prints one pass/fail table at the end:
#   1. backend/tests — the full pytest suite (pytest-xdist when installed)
#   2. the five-paradigm × two-tier smoke game (tests/test_five_paradigm_smoke.py)
#   3. the two golden traces (financial + stakeholder)
#   4. frontend — the full jest suite
#   5. optionally, the audit probes in $MURESSONS_AUDIT_SCRATCH (default
#      ~/audit_scratch) when that directory exists — the scratch harness is
#      not part of the repo, so this section is skipped, not failed, without it.
#
# Environment: the backend steps run in memory mode with a throwaway data
# directory unless you export your own (USE_MEMORY_DB, MURESSONS_DATA_DIR,
# MASTER_PASSWORD, PROJECT_ADMIN_PASSWORD, JWT_SECRET are all honoured).
#
# Usage:  scripts/verify_wave.sh            # everything
#         scripts/verify_wave.sh --no-jest  # backend only (jest takes ~10 min)
#         scripts/verify_wave.sh --no-probes
# Exit status is non-zero if any required step fails.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_JEST=1; RUN_PROBES=1
for a in "$@"; do
  case "$a" in
    --no-jest) RUN_JEST=0 ;;
    --no-probes) RUN_PROBES=0 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

export USE_MEMORY_DB="${USE_MEMORY_DB:-true}"
export DEBUG="${DEBUG:-true}"
export MURESSONS_DATA_DIR="${MURESSONS_DATA_DIR:-$(mktemp -d -t muressons-verify-XXXXXX)}"
export MASTER_PASSWORD="${MASTER_PASSWORD:-verify-master-pw}"
export PROJECT_ADMIN_PASSWORD="${PROJECT_ADMIN_PASSWORD:-verify-project-pw}"
export JWT_SECRET="${JWT_SECRET:-verify-jwt-secret-not-for-production}"
export BCRYPT_ROUNDS="${BCRYPT_ROUNDS:-4}"
export MURESSONS_SNAPSHOT_DEBOUNCE_MS="${MURESSONS_SNAPSHOT_DEBOUNCE_MS:-0}"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"

declare -a NAMES STATUSES NOTES
record() { NAMES+=("$1"); STATUSES+=("$2"); NOTES+=("$3"); }

XDIST=""
if python3 -c "import xdist" 2>/dev/null; then XDIST="-n auto"; fi
PYTEST="python3 -m pytest -p no:cacheprovider -q -W ignore"

step_pytest() {
  local name="$1"; shift
  local log; log="$(mktemp)"
  ( cd "$ROOT/backend" && $PYTEST "$@" ) >"$log" 2>&1
  local rc=$?
  local summary; summary="$(grep -E '^(=+ )?[0-9]+ (passed|failed)|[0-9]+ passed|[0-9]+ failed' "$log" | tail -1)"
  if [ $rc -eq 0 ]; then record "$name" PASS "$summary"; else record "$name" FAIL "$summary (log: $log)"; fi
  return $rc
}

echo "== 1/5 backend: full pytest suite"
step_pytest "pytest (backend/tests)" $XDIST tests
echo "== 2/5 backend: five-paradigm smoke (advanced + expert)"
step_pytest "five-paradigm smoke" tests/test_five_paradigm_smoke.py
echo "== 3/5 backend: golden traces"
step_pytest "golden traces" tests/test_financial_golden_trace.py tests/test_stakeholder_golden_trace.py

if [ $RUN_JEST -eq 1 ]; then
  echo "== 4/5 frontend: full jest suite"
  log="$(mktemp)"
  ( cd "$ROOT/frontend" && npx jest --silent ) >"$log" 2>&1
  rc=$?
  summary="$(grep -E '^Tests:' "$log" | tail -1)"
  if [ $rc -eq 0 ]; then record "jest (frontend)" PASS "$summary"; else record "jest (frontend)" FAIL "$summary (log: $log)"; fi
else
  record "jest (frontend)" SKIP "--no-jest"
fi

SCRATCH="${MURESSONS_AUDIT_SCRATCH:-$HOME/audit_scratch}"
if [ $RUN_PROBES -eq 1 ] && [ -d "$SCRATCH" ]; then
  echo "== 5/5 audit probes in $SCRATCH (informational: each must exit 0)"
  for probe in flow/probe_pwchange.py rng/probe_diverge.py flag/probe_deferred.py seam/compare.py \
               flow/probe_wizard_pacing.py acc/sweep_noauth.py acc/probe_analytics_player.py; do
    if [ -f "$SCRATCH/$probe" ]; then
      log="$(mktemp)"
      ( cd "$ROOT/backend" && timeout 600 python3 "$SCRATCH/$probe" ) >"$log" 2>&1
      rc=$?
      if [ $rc -eq 0 ]; then record "probe $probe" PASS "$(tail -1 "$log" | cut -c1-90)"; else record "probe $probe" FAIL "exit $rc (log: $log)"; fi
    else
      record "probe $probe" SKIP "not present"
    fi
  done
else
  record "audit probes" SKIP "$([ $RUN_PROBES -eq 1 ] && echo "no $SCRATCH" || echo --no-probes)"
fi

echo
echo "=================== verify_wave: $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null) ==================="
printf '%-44s %-5s %s\n' "check" "state" "detail"
fail=0
for i in "${!NAMES[@]}"; do
  printf '%-44s %-5s %s\n' "${NAMES[$i]}" "${STATUSES[$i]}" "${NOTES[$i]}"
  [ "${STATUSES[$i]}" = FAIL ] && fail=1
done
echo "======================================================================"
exit $fail
