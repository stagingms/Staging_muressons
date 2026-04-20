"""
Muressons Global Command — COMPREHENSIVE SIMULATION TEST
=========================================================
Tests EVERY strategic option (A, B, C) for EVERY round (1-10)
across ALL paradigms: legacy_abc, multi_toggles, advanced_climate, healthcare.

For each (paradigm, round, option) combination:
  1. Creates a fresh session
  2. Completes any required gates (stakeholder map, materiality)
  3. Commits up to (round - 1) with a neutral option_b
  4. Commits round N with the specific option under test
  5. Validates the commit result and KPI invariants

Run:  python test_comprehensive.py
"""

import sys
import time
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ─── Helpers ────────────────────────────────────────────────────────────────

STANDARD_BUS = ["pharma", "electronics", "consumer_goods", "software"]
HEALTHCARE_BUS = ["hospitals", "primary_care_clinics", "telehealth"]

PARADIGMS = ["legacy_abc", "multi_toggles", "advanced_climate", "healthcare"]

ALL_OPTIONS = ["option_a", "option_b", "option_c"]

RESULTS: list[dict] = []  # collects pass/fail rows


def api(method, path, data=None, silent=False):
    if method == "GET":
        r = client.get(path)
    elif method == "POST":
        r = client.post(path, json=data)
    elif method == "PUT":
        r = client.put(path, json=data)
    elif method == "DELETE":
        r = client.delete(path)
    else:
        raise ValueError(f"Unknown method {method}")
    if not silent and r.status_code >= 400:
        print(f"    [WARN] {method} {path} => {r.status_code}: {r.text[:200]}")
    return r


def create_session(paradigm: str, label: str) -> str | None:
    r = api("POST", "/api/simulations/start", {
        "cohort_name": label,
        "decision_paradigm": paradigm,
    })
    if r.status_code != 201:
        return None
    return r.json()["session_id"]


def get_dashboard(sid: str) -> dict:
    r = api("GET", f"/api/simulations/{sid}/dashboard")
    if r.status_code != 200:
        return {}
    return r.json()


def submit_stakeholder_map(sid: str) -> bool:
    r = api("GET", "/api/simulations/stakeholder-map/stakeholders", silent=True)
    if r.status_code != 200:
        return False
    stakeholders = r.json().get("stakeholders", [])
    quadrants = [
        "high_power_high_interest", "high_power_low_interest",
        "low_power_high_interest", "low_power_low_interest"
    ]
    mapping = {}
    for i, s in enumerate(stakeholders):
        sid_s = s.get("id", s.get("stakeholder_id", f"s{i}"))
        mapping[sid_s] = quadrants[i % 4]
    r2 = api("POST", f"/api/simulations/{sid}/stakeholder-map", {"mapping": mapping}, silent=True)
    return r2.status_code == 200


def submit_materiality(sid: str, paradigm: str) -> bool:
    if paradigm == "multi_toggles":
        r = api("GET", f"/api/admin/{sid}/r2-bu-selection", silent=True)
        bu_id = r.json().get("selected_bu") if r.status_code == 200 else None
        r = api("GET", f"/api/admin/materiality-config/bu/{bu_id}" if bu_id else "/api/admin/materiality-config", silent=True)
    else:
        r = api("GET", "/api/admin/materiality-config", silent=True)

    if r.status_code != 200:
        return False
    issues = r.json().get("issues", [])
    q1, q2, q3, q4 = [], [], [], []
    for issue in issues:
        fi = issue.get("financial_impact", "low")
        si = issue.get("societal_impact", "low")
        if fi == "high" and si == "high":
            q1.append(issue["id"])
        elif fi == "high":
            q2.append(issue["id"])
        elif si == "high":
            q3.append(issue["id"])
        else:
            q4.append(issue["id"])
    payload = {
        "consultant_used": False,
        "matrix_submission": {
            "quadrant_1_top_right": q1,
            "quadrant_2_top_left": q2,
            "quadrant_3_bottom_right": q3,
            "quadrant_4_bottom_left": q4,
        },
        "force_override_cfo": False,
    }
    r2 = api("POST", f"/api/simulations/{sid}/materiality", payload, silent=True)
    return r2.status_code == 200


def build_decisions(sid: str, paradigm: str, choice: str) -> list[dict]:
    """Build a decisions payload for the current round."""
    dash = get_dashboard(sid)
    active_bus = [bu["bu_id"] for bu in dash.get("business_units", [])]
    if not active_bus:
        active_bus = HEALTHCARE_BUS if paradigm == "healthcare" else STANDARD_BUS

    decisions = []
    for bu in active_bus:
        d = {
            "bu_id": bu,
            "investment_ratio": 0.25,
            "capex_allocated": 500_000,
            "choice_selected": choice if paradigm in ("legacy_abc", "healthcare") else "",
        }
        if paradigm in ("multi_toggles", "advanced_climate"):
            pillar_opts = ["moderate", "aggressive", "conservative"]
            idx = ALL_OPTIONS.index(choice)
            d["pillar_decisions"] = {
                "energy": pillar_opts[idx % 3],
                "operations": pillar_opts[(idx + 1) % 3],
                "supply_chain": pillar_opts[(idx + 2) % 3],
                "offsetting": pillar_opts[idx % 3],
            }
        decisions.append(d)
    return decisions


def commit_one_round(sid: str, paradigm: str, choice: str) -> dict | None:
    """Commit the current round with the given option. Returns result dict or None."""
    decisions = build_decisions(sid, paradigm, choice)
    payload = {
        "decisions": decisions,
        "dividends_paid": 0,
        "crisis_severity": 0,
        "force_override_cfo": True,
    }
    r = api("POST", f"/api/simulations/{sid}/commit-turn", payload, silent=True)
    if r.status_code in (200, 201):
        return r.json()
    return None


def advance_to_round(sid: str, paradigm: str, target_round: int) -> bool:
    """Fast-forward the session to (target_round) using neutral option_b commits."""
    for _ in range(target_round - 1):
        dash = get_dashboard(sid)
        current = dash.get("current_round", 1)
        if current >= target_round:
            break

        # Handle gates
        if current == 1:
            submit_stakeholder_map(sid)
        elif current == 2:
            submit_materiality(sid, paradigm)

        result = commit_one_round(sid, paradigm, "option_b")
        if result is None:
            return False
    return True


def validate_kpis(gs: dict, bus: list[dict], paradigm: str, round_num: int, option: str) -> list[str]:
    """Return a list of invariant violations detected in the global state and business units."""
    violations = []
    treasury = gs.get("corporate_treasury", None)
    reputation = gs.get("group_reputation", None)
    ebitda = gs.get("historical_ebitda", None)
    co2 = gs.get("tco2e_emissions", None)

    if treasury is None:
        violations.append("missing:corporate_treasury")
    if reputation is None:
        violations.append("missing:group_reputation")
    elif not (0 <= reputation <= 100):
        violations.append(f"reputation_out_of_range:{reputation:.1f}")
    if ebitda is None:
        violations.append("missing:historical_ebitda")
    if co2 is None:
        violations.append("missing:tco2e_emissions")
    elif co2 < 0:
        violations.append(f"negative_co2:{co2}")

    # Healthcare-specific KPIs
    if paradigm == "healthcare":
        for bu in bus:
            burnout = bu.get("staff_burnout_index", None)
            bed_util = bu.get("bed_capacity_utilization", None)
            if burnout is None:
                violations.append(f"missing:staff_burnout_index_in_{bu.get('bu_id')}")
            if bed_util is None:
                violations.append(f"missing:bed_capacity_utilization_in_{bu.get('bu_id')}")

    return violations


# ─── Single Option Test ──────────────────────────────────────────────────────

def _test_option(paradigm: str, round_num: int, option: str) -> dict:
    """
    Run a single test: create session, advance to round_num, commit with option.
    Returns a result dict.
    """
    label = f"test_{paradigm}_r{round_num}_{option}_{int(time.time())}"
    result = {
        "paradigm": paradigm,
        "round": round_num,
        "option": option,
        "status": "FAIL",
        "error": None,
        "treasury": None,
        "reputation": None,
        "ebitda": None,
        "co2": None,
        "new_round": None,
        "violations": [],
    }

    # 1. Create session
    sid = create_session(paradigm, label)
    if not sid:
        result["error"] = "session_create_failed"
        return result

    # 2. Advance to target round (skip if round 1)
    if round_num > 1:
        ok = advance_to_round(sid, paradigm, round_num)
        if not ok:
            result["error"] = "advance_failed"
            return result

    # 3. Gates for this round
    dash = get_dashboard(sid)
    current = dash.get("current_round", 1)
    if current == 1:
        submit_stakeholder_map(sid)
    elif current == 2:
        submit_materiality(sid, paradigm)

    # 4. Commit the round with the target option
    commit_result = commit_one_round(sid, paradigm, option)
    if commit_result is None:
        result["error"] = "commit_failed"
        return result

    # 5. Extract and validate
    gs = commit_result.get("global_state", {})
    bus = commit_result.get("business_units", [])
    violations = validate_kpis(gs, bus, paradigm, round_num, option)

    result["treasury"] = gs.get("corporate_treasury")
    result["reputation"] = gs.get("group_reputation")
    result["ebitda"] = gs.get("historical_ebitda")
    result["co2"] = gs.get("tco2e_emissions")
    result["new_round"] = commit_result.get("new_round_number")
    result["violations"] = violations
    result["status"] = "PASS" if not violations else "WARN"

    return result


# ─── Main Test Runner ────────────────────────────────────────────────────────

def run_all_tests():
    print("=" * 70)
    print("  MURESSONS - COMPREHENSIVE DECISION TEST (All Paradigms x R1-10 x A/B/C)")
    print("=" * 70)

    total = 0
    passed = 0
    warned = 0
    failed = 0

    for paradigm in PARADIGMS:
        print(f"\n{'-'*70}")
        print(f"  PARADIGM: {paradigm.upper()}")
        print(f"{'-'*70}")

        for round_num in range(1, 11):
            for option in ALL_OPTIONS:
                total += 1
                sys.stdout.write(f"  R{round_num:02d} {option} [{paradigm:<18}] ... ")
                sys.stdout.flush()

                r = _test_option(paradigm, round_num, option)
                RESULTS.append(r)

                status = r["status"]
                if status == "PASS":
                    passed += 1
                    treasury_str = f"${r['treasury']:>12,.0f}" if r['treasury'] is not None else "        N/A"
                    rep_str = f"{r['reputation']:5.1f}" if r['reputation'] is not None else "  N/A"
                    print(f"PASS  treasury={treasury_str}  rep={rep_str}  -> R{r['new_round']}")
                elif status == "WARN":
                    warned += 1
                    print(f"WARN  violations={r['violations']}")
                else:
                    failed += 1
                    print(f"FAIL  error={r['error']}")

    # ─── Summary ────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  SUMMARY: {total} tests  |  {passed} PASS  |  {warned} WARN  |  {failed} FAIL")
    print(f"{'='*70}")

    # Print failures / warnings
    failures = [r for r in RESULTS if r["status"] != "PASS"]
    if failures:
        print(f"\n  -- ISSUES DETECTED --")
        for r in failures:
            tag = f"R{r['round']} {r['option']} [{r['paradigm']}]"
            if r["status"] == "WARN":
                print(f"  WARN  {tag}  violations={r['violations']}")
            else:
                print(f"  FAIL  {tag}  error={r['error']}")

    # Per-paradigm summary
    print(f"\n  -- PER-PARADIGM BREAKDOWN --")
    for paradigm in PARADIGMS:
        prows = [r for r in RESULTS if r["paradigm"] == paradigm]
        p = sum(1 for r in prows if r["status"] == "PASS")
        w = sum(1 for r in prows if r["status"] == "WARN")
        f = sum(1 for r in prows if r["status"] == "FAIL")
        emoji = "[OK]" if f == 0 and w == 0 else ("[WARN]" if f == 0 else "[FAIL]")
        print(f"  {emoji}  {paradigm:<20}  {p:2d} PASS  {w:2d} WARN  {f:2d} FAIL")

    # Per-round summary (across paradigms)
    print(f"\n  -- PER-ROUND BREAKDOWN --")
    for round_num in range(1, 11):
        rrows = [r for r in RESULTS if r["round"] == round_num]
        p = sum(1 for r in rrows if r["status"] == "PASS")
        w = sum(1 for r in rrows if r["status"] == "WARN")
        f = sum(1 for r in rrows if r["status"] == "FAIL")
        emoji = "[OK]" if f == 0 and w == 0 else ("[WARN]" if f == 0 else "[FAIL]")
        print(f"  {emoji}  Round {round_num:2d}   {p:2d} PASS  {w:2d} WARN  {f:2d} FAIL")

    # Save JSON report
    report_path = "test_comprehensive_results.json"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(RESULTS, f, indent=2, default=str)
        print(f"\n  Full report saved to: {report_path}")
    except Exception as e:
        print(f"\n  [WARN] Could not save report: {e}")

    print(f"{'='*70}")
    return failed == 0


if __name__ == "__main__":
    ok = run_all_tests()
    sys.exit(0 if ok else 1)
