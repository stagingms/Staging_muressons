"""
Muressons UN SDG — Comprehensive API Audit Script
Tests all roles, session lifecycles, and SDG-specific mechanics
Credentials loaded from TEST_FAC_ID / TEST_FAC_PW env vars (is_admin=True).
"""
import os
import urllib.request
import urllib.error
import json
import sys
import random

API = "http://localhost:8000"
# MED-001: Credentials come from env vars — no hardcoded secrets in source.
# Set TEST_FAC_ID and TEST_FAC_PW before running:
#   export TEST_FAC_ID=Jose
#   export TEST_FAC_PW=<hashed-or-plain-password>
_TEST_FAC_ID: str = os.getenv("TEST_FAC_ID", "")
_TEST_FAC_PW: str = os.getenv("TEST_FAC_PW", "")
issues = []
warnings = []
passed = []

# ─── helpers ──────────────────────────────────────────────────────────────────

def req(method, path, body=None, label=None):
    url = API + path
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=8) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode())
        except Exception:
            detail = {"raw": str(e)}
        return e.code, detail
    except Exception as ex:
        return 0, {"error": str(ex)}

def ok(msg):
    passed.append(msg)
    print(f"  [PASS] {msg}")

def fail(msg, critical=True):
    tag = "CRITICAL" if critical else "WARNING"
    (issues if critical else warnings).append(f"{tag}: {msg}")
    print(f"  [{'FAIL' if critical else 'WARN'}] {msg}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ─── Phase 1: Health & Admin ───────────────────────────────────────────────────

section("PHASE 1 — HEALTH & ADMIN")

s, d = req("GET", "/health")
if s == 200:
    ok(f"Health OK — db={d.get('database')} ver={d.get('version')}")
else:
    fail(f"Health endpoint failed ({s}): {d}")

# Admin facilitators list
s, d = req("GET", "/api/admin/facilitators")
if s == 200:
    facs = d if isinstance(d, list) else d.get("facilitators", [])
    ok(f"Facilitator list loaded — {len(facs)} facilitators")
    jose_exists = any(f.get("facilitator_id") == _TEST_FAC_ID and not f.get("deleted_at") for f in facs)
    if not jose_exists:
        fail(f"No active '{_TEST_FAC_ID}' facilitator found — login will fail", critical=False)
    else:
        ok(f"'{_TEST_FAC_ID}' facilitator account exists and active")
else:
    fail(f"Facilitator list failed ({s}): {d}")

# Admin login - God Mode
s, d = req("POST", "/api/admin/facilitators/login",
           {"facilitator_id": _TEST_FAC_ID, "password": _TEST_FAC_PW})
if s == 200:
    is_admin = d.get("is_admin", False)
    ok(f"God Mode login OK ({_TEST_FAC_ID}) — is_admin={is_admin}")
    if not is_admin:
        fail("Login succeeded but is_admin=False — God Mode will deny entry")
else:
    fail(f"God Mode login failed ({s}): {d}")

# Admin global settings
s, d = req("GET", "/api/admin/global-settings")
if s == 200:
    ok("Global settings loaded")
else:
    fail(f"Global settings failed ({s}): {d}", critical=False)

# ─── Phase 2: Session Creation — All 5 Paradigms ──────────────────────────────

section("PHASE 2 — SESSION CREATION (ALL 5 PARADIGMS)")

PARADIGMS = ["legacy_abc", "multi_toggles", "advanced_climate", "healthcare"]
sessions = {}

for paradigm in PARADIGMS:
    s, d = req("POST", "/api/simulations/start", {
        "team_name": f"AuditTeam_{paradigm}",
        "cohort_name": f"Audit_{paradigm}_2025",
        "facilitator_id": _TEST_FAC_ID,
        "decision_paradigm": paradigm
    })
    sid = d.get("session_id", "")
    if s == 200 and sid:
        sessions[paradigm] = sid
        ok(f"Session created: {paradigm} → {sid[:8]}...")
    else:
        fail(f"Session creation failed for paradigm '{paradigm}' ({s}): {d}")

# ─── Phase 3: State Validation — UN SDG ───────────────────────────────────────

section("PHASE 3 — STATE VALIDATION (UN SDG)")

sid_sdg = sessions.get("un_sdg")
if sid_sdg:
    s, d = req("GET", f"/api/simulations/{sid_sdg}/state")
    if s != 200:
        fail(f"Cannot read SDG state ({s}): {d}")
    else:
        gs = d.get("global_state", {})
        bus = d.get("business_units", [])
        bu_ids = [b.get("bu_id") for b in bus]

        # Paradigm stored correctly
        p = gs.get("decision_paradigm")
        if p == "un_sdg":
            ok("decision_paradigm persisted as 'un_sdg'")
        else:
            fail(f"decision_paradigm stored as '{p}' instead of 'un_sdg'")

        # Required SDG global state fields
        for field in ["political_capital", "community_trust_score", "global_emissions_intensity"]:
            if field in gs:
                ok(f"Global state has '{field}'")
            else:
                fail(f"Global state missing field: '{field}'")

        # 4 Regions
        EXPECTED_BUS = {"sub_saharan_corridor", "south_asia_subcontinent",
                        "southeast_asia_hub", "northern_transition_zone"}
        present = set(bu_ids)
        if EXPECTED_BUS == present:
            ok(f"All 4 SDG regional BUs present: {sorted(present)}")
        else:
            missing = EXPECTED_BUS - present
            extra = present - EXPECTED_BUS
            if missing:
                fail(f"Missing SDG regions: {missing}")
            if extra:
                fail(f"Unexpected BUs detected: {extra}", critical=False)

        # SDG cluster fields on BUs
        SDG_CLUSTERS = ["basic_needs", "human_capital", "sustainable_growth",
                        "planet", "governance", "partnerships"]
        for bu in bus:
            bid = bu.get("bu_id", "?")
            metrics = bu.get("sdg_metrics", bu)
            for cluster in SDG_CLUSTERS:
                if cluster not in metrics and cluster not in bu:
                    fail(f"BU '{bid}' missing SDG cluster '{cluster}'", critical=False)
            # governance below 40 check
            gov = bu.get("governance", metrics.get("governance", 999))
            if gov < 40:
                ok(f"  BU '{bid}' gov={gov} (<40) — Institutional Leakage will activate")

        # Treasury start
        treasury = gs.get("treasury", 0)
        if treasury == 500_000_000:
            ok(f"Treasury initialized correctly: ${treasury:,.0f}")
        elif treasury > 0:
            fail(f"Treasury wrong: ${treasury:,.0f} (expected $500,000,000)", critical=False)
        else:
            fail(f"Treasury is ZERO or missing: {treasury}")

else:
    fail("SDG session ID missing — cannot validate state")

# ─── Phase 4: Round 1-10 Simulation — UN SDG ─────────────────────────────────

section("PHASE 4 — FULL 10-ROUND UN SDG SIMULATION")

if sid_sdg:
    # Gate 1: Stakeholder map
    s, d = req("POST", f"/api/simulations/{sid_sdg}/stakeholder-map", {"mapping": {}})
    if s in (200, 201):
        ok("Stakeholder Map gate passed")
    elif s == 404:
        fail("Stakeholder Map endpoint not found (404)", critical=False)
    else:
        fail(f"Stakeholder Map gate failed ({s}): {d}", critical=False)

    # Gate 2: Materiality matrix
    s, d = req("POST", f"/api/simulations/{sid_sdg}/materiality-matrix", {"matrix": {}})
    if s in (200, 201):
        ok("Materiality Matrix gate passed")
    elif s == 404:
        fail("Materiality Matrix endpoint not found (404)", critical=False)
    else:
        fail(f"Materiality Matrix gate failed ({s}): {d}", critical=False)

    OPTIONS = ["option_a", "option_b", "option_c"]
    prev_treasury = None

    for rnd in range(1, 11):
        choice = OPTIONS[rnd % 3]
        s, d = req("POST", f"/api/simulations/{sid_sdg}/decide", {
            "round_number": rnd,
            "decision": choice
        })

        if s != 200:
            fail(f"Round {rnd} decision failed ({s}): {d}")
            continue

        gs = d.get("global_state", {})
        events = d.get("events", [])
        treasury = gs.get("treasury", 0)
        rnd_now = gs.get("current_round", "?")

        print(f"\n  R{rnd} ({choice}): treasury=${treasury:,.0f} round={rnd_now}")
        print(f"    events={events[:5]}")

        # Check treasury is numeric
        if not isinstance(treasury, (int, float)):
            fail(f"Round {rnd}: treasury is non-numeric type: {type(treasury)}")

        # For UN SDG — check HDI fields appear in R10
        if rnd == 10:
            term = gs.get("terminal_value") or d.get("terminal_value")
            hdi = gs.get("global_hdi") or d.get("global_hdi")
            profile = gs.get("profile") or d.get("profile")
            print(f"    [R10] terminal_value={term} global_hdi={hdi} profile={profile}")
            if hdi:
                ok(f"R10 HDI computed: {hdi}")
            else:
                fail("R10 terminal HDI is missing — Grand Finale not firing for SDG")
            if profile:
                ok(f"R10 profile assigned: {profile}")
            else:
                fail("R10 profile archetype is missing")

        # Education lag maturation check
        if rnd == 6:
            lag_matured = any("education_lag" in str(e) for e in events)
            if lag_matured:
                ok("R6: Education lag matured (compulsory_schooling R3→R6)")
            else:
                pass  # only fires if option_a was chosen in R3

        ok(f"Round {rnd} completed successfully")
        prev_treasury = treasury

# ─── Phase 5: Facilitator APIs ────────────────────────────────────────────────

section("PHASE 5 — FACILITATOR ROLE APIS")

s, d = req("GET", "/api/admin/sessions")
if s == 200:
    sess_list = d if isinstance(d, list) else d.get("sessions", [])
    ok(f"Session list loaded — {len(sess_list)} active sessions")
else:
    fail(f"Admin sessions list failed ({s}): {d}")

s, d = req("GET", "/api/admin/leaderboard?facilitator_id=admin")
if s == 200:
    ok("Leaderboard loaded OK")
else:
    fail(f"Leaderboard failed ({s}): {d}", critical=False)

# ─── Phase 6: Edge Cases ──────────────────────────────────────────────────────

section("PHASE 6 — EDGE CASES & VULNERABILITIES")

# Test invalid paradigm
s, d = req("POST", "/api/simulations/start", {
    "team_name": "Hacker", "cohort_name": "HackTest_9999",
    "facilitator_id": _TEST_FAC_ID, "decision_paradigm": "INVALID_PARADIGM"
})
if s in (400, 422):
    ok(f"Invalid paradigm correctly rejected ({s})")
else:
    fail(f"Invalid paradigm NOT rejected — returned {s}: {d}")

# Test replaying a round
if sid_sdg:
    s, d = req("POST", f"/api/simulations/{sid_sdg}/decide", {
        "round_number": 1, "decision": "option_a"
    })
    if s in (400, 409, 422):
        ok(f"Round replay correctly blocked ({s})")
    elif s == 200:
        fail("Round 1 can be replayed on a completed 10-round session — no guard!")
    else:
        fail(f"Round replay attempt returned unexpected {s}: {d}", critical=False)

# Test nonexistent session
s, d = req("GET", "/api/simulations/nonexistent-session-id/state")
if s == 404:
    ok("Nonexistent session returns 404")
else:
    fail(f"Nonexistent session returned {s} instead of 404: {d}")

# Test negative budget (over-spend)
s, d = req("POST", "/api/simulations/start", {
    "team_name": "BudgetTest", "cohort_name": "Test",
    "facilitator_id": "admin", "decision_paradigm": "un_sdg"
})
sid_budget = d.get("session_id")
if sid_budget:
    # Try to force a very expensive round
    s, d = req("POST", f"/api/simulations/{sid_budget}/decide", {
        "round_number": 1, "decision": "option_c"
    })
    if s == 200:
        treas = d.get("global_state", {}).get("treasury", 0)
        if treas < 0:
            fail(f"Treasury went NEGATIVE after R1: ${treas:,.0f}")
        else:
            ok(f"Treasury stayed non-negative after R1: ${treas:,.0f}")

# ─── Final Summary ─────────────────────────────────────────────────────────────

section("AUDIT SUMMARY")
print(f"\n  PASSED:   {len(passed)}")
print(f"  ISSUES:   {len(issues)}")
print(f"  WARNINGS: {len(warnings)}")

if issues:
    print("\n  === CRITICAL ISSUES ===")
    for i in issues:
        print(f"    !! {i}")

if warnings:
    print("\n  === WARNINGS ===")
    for w in warnings:
        print(f"    ~~ {w}")

print("\n  Done.")
