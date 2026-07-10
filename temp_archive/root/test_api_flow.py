"""End-to-end API integration test — TCFD, ConsequencePreview, commit flow."""
import requests, json

API = "http://127.0.0.1:8000/api/simulations"

print("=" * 60)
print("  MURESSONS FULL INTEGRATION TEST")
print("=" * 60)

# 1. Create solo session
r = requests.post(f"{API}/solo-start", json={"username": "FullTest"})
data = r.json()
sid = data["session_id"]
print(f"\n[1] Session: {sid}")

# 2. Dashboard
dash = requests.get(f"{API}/{sid}/dashboard").json()
gs = dash["global_state"]
bus = dash["business_units"]
paradigm = dash.get("decision_paradigm", "multi_toggles")
print(f"[2] BUs: {len(bus)}, Treasury: ${gs['corporate_treasury']:,.0f}, Paradigm: {paradigm}")

# 3. TCFD
tcfd = requests.get(f"{API}/{sid}/tcfd-scenarios").json()
assert "summary" in tcfd, "TCFD missing summary"
print(f"[3] TCFD: {len(tcfd['scenarios'])} scenarios, risk={tcfd['summary']['overall_risk']}")

# 4. Pillar Config
pc = requests.get(f"{API}/pillar-config/1").json()
areas = pc.get("areas", {})
print(f"[4] Pillars: {list(areas.keys())}")

# 5. Commit with proper schema
pillar_sels = {}
for ak, area in areas.items():
    opts = area.get("options", {})
    if opts:
        pillar_sels[ak] = list(opts.keys())[0]

bu_decisions = []
for bu in bus:
    bu_decisions.append({
        "bu_id": bu["bu_id"],
        "investment_ratio": 0.25,
        "capex_allocated": gs["corporate_treasury"] * 0.05,
        "choice_selected": "option_a",
        "pillar_decisions": pillar_sels,
    })

commit_body = {
    "decisions": bu_decisions,
    "dividends_paid": 0,
    "crisis_severity": 0,
}

r = requests.post(f"{API}/{sid}/commit-turn", json=commit_body)
print(f"[5] Commit: {r.status_code}")
if r.status_code in (200, 201):
    cr = r.json()
    new_gs = cr["global_state"]
    events = cr.get("events", {})
    print(f"    New round: {cr['new_round_number']}")
    print(f"    Treasury: ${new_gs['corporate_treasury']:,.0f}")
    print(f"    Reputation: {new_gs['group_reputation']}")
    print(f"    Carbon: {new_gs.get('tco2e_emissions', 0):.0f}t")
    print(f"    Events: {list(events.keys())[:8]}")
    
    tipping = events.get("systemic_tipping", {})
    if tipping:
        ts = tipping.get("tipping_state", {})
        print(f"    Tipping: {json.dumps(ts)[:200]}")
    
    # 6. Verify ConsequencePreview data
    print(f"\n[6] ConsequencePreview Data Verification")
    merged = {}
    labels = []
    for ak, ok in pillar_sels.items():
        opt = areas.get(ak, {}).get("options", {}).get(ok, {})
        if opt:
            labels.append(opt.get("title", ok))
            for k, v in opt.get("impacts", {}).items():
                if isinstance(v, (int, float)):
                    merged[k] = merged.get(k, 0) + v
            if opt.get("cost") and "treasury" not in opt.get("impacts", {}):
                merged["treasury"] = merged.get("treasury", 0) + opt["cost"]
    
    print(f"    Labels: {' + '.join(labels)}")
    print(f"    Merged impacts ({len(merged)} keys): {merged}")
    
    non_zero = {k: v for k, v in merged.items() if v != 0 and "factor" not in k and "risk" not in k and "flag" not in k}
    print(f"    Display bars ({len(non_zero)} after filter): {non_zero}")
    
    if non_zero:
        print(f"    PASS: ConsequencePreview will show {len(non_zero)} impact bars")
    else:
        print(f"    WARN: No impact bars to display")
    
    # 7. Test TCFD post-commit
    tcfd2 = requests.get(f"{API}/{sid}/tcfd-scenarios").json()
    if "summary" in tcfd2:
        print(f"\n[7] TCFD post-commit: risk={tcfd2['summary']['overall_risk']}")
    
    # 8. Test other engine endpoints
    for endpoint, name in [
        ("biodiversity", "Biodiversity"),
        ("balance-sheet", "Balance Sheet"),
        ("board-governance", "Board Governance"),
        ("supply-chain", "Supply Chain"),
    ]:
        er = requests.get(f"{API}/{sid}/{endpoint}")
        status = "OK" if er.status_code == 200 else f"ERR {er.status_code}"
        print(f"[8] {name}: {status}")
    
    # 9. R2 commit
    print(f"\n[9] Round 2 Commit")
    pc2 = requests.get(f"{API}/pillar-config/2").json()
    areas2 = pc2.get("areas", {})
    sels2 = {}
    for ak, area in areas2.items():
        opts = area.get("options", {})
        if opts:
            sels2[ak] = list(opts.keys())[0]
    
    dash2 = requests.get(f"{API}/{sid}/dashboard").json()
    bus2 = dash2["business_units"]
    gs2 = dash2["global_state"]
    
    bu_dec2 = []
    for bu in bus2:
        bu_dec2.append({
            "bu_id": bu["bu_id"],
            "investment_ratio": 0.2,
            "capex_allocated": gs2["corporate_treasury"] * 0.04,
            "choice_selected": "option_a",
            "pillar_decisions": sels2,
        })
    
    r2 = requests.post(f"{API}/{sid}/commit-turn", json={"decisions": bu_dec2})
    print(f"    Status: {r2.status_code}")
    if r2.status_code in (200, 201):
        cr2 = r2.json()
        print(f"    New round: {cr2['new_round_number']}")
        print(f"    Treasury: ${cr2['global_state']['corporate_treasury']:,.0f}")
else:
    print(f"    ERROR: {r.text[:400]}")

print(f"\n{'=' * 60}")
print(f"  ALL TESTS COMPLETE")
print(f"{'=' * 60}")
