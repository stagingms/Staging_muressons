"""Round 2 (Double Materiality) audit regression suite.

Seven defects were found by executing the engine against its own shipped
configuration (audit of 2026-08); these tests pin the repairs so none of them
can recur silently:

  F-1  r2_governance_choice written by _post_r2_materiality (the round's
       post-tick handler — the only point where matrix + choice both exist).
  F-2  Exactly one code path writes the materiality tier flags; no flag may
       exist in dual form (boolean key + rN_flags list entry).
  F-3  The released materiality budget is a ring-fenced fund with a real
       consumer (CapEx offset), not a pure treasury debit; the Option C
       clawback REDUCES the team's position (the old code refunded it).
  F-4  (doc drift — pinned in SIMULATION_CONTEXT.md, no engine change)
  F-5  Assurance signals are all reachable and loseable.
  F-6  One quadrant classifier; Q2/Q3 reachable; string labels govern until a
       dictionary carries all four dual-axis fields.
  F-7  No option's revenue_delta explodes ×n_business_units into a
       group-scale hit (the per-unit sanity sweep).

Also pinned: the §4.1 premium tiering across all nine accuracy × option
combinations, and the M_R ceilings (~1.93 / ~2.02 with JT scaling) that the
teaching material depends on.
"""

import glob
import json
import os
import re

import pytest
from fastapi.testclient import TestClient

import database_memory as dbm
import materiality_db as mdb
from main import app
from round2_csrd import CSRD_ISSUES, correct_quadrant_v2, _DUAL_AXIS_FIELDS
from round_logic import _collect_all_flags, _find_dual_form_flags
from router import _commit_timestamps

client = TestClient(app)

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DEFAULT_CONFIG ground truth under the (single) string-label rule
Q1_IDS = ["data_privacy_impact", "api_leakage_impact", "drug_safety_financial_risk",
          "e_waste_impact", "plastic_waste_impact"]
Q2_IDS = ["supply_chain_labor_risk", "biodiversity_financial_risk"]
Q3_IDS = ["energy_financial_risk"]

TOTAL_BUDGET = 15_000_000


# ── helpers ──────────────────────────────────────────────────────────────────

def _start():
    r = client.post("/api/simulations/solo-start",
                    json={"player_name": "AUD", "decision_paradigm": "legacy_abc"})
    assert r.status_code in (200, 201), r.text[:300]
    sid = r.json()["session_id"]
    bus = client.get(f"/api/simulations/{sid}/dashboard").json()["business_units"]
    return sid, bus


def _display_key(sid, rnd, canonical_choice):
    """Anti-gaming shuffle: commit-turn deshuffles the submitted key through the
    session's shuffle_seed, so tests must send the DISPLAY key that maps back
    to the canonical option they mean."""
    seed = (dbm._sessions.get(sid) or {}).get("shuffle_seed")
    if seed is None:
        return canonical_choice
    from option_shuffle import get_shuffle_mapping
    return get_shuffle_mapping(seed, rnd)["canonical_to_display"].get(
        canonical_choice, canonical_choice)


def _commit(sid, bus, rnd, choice, capex=500_000):
    _commit_timestamps.pop(sid, None)
    display = _display_key(sid, rnd, choice)
    payload = {
        "decisions": [
            {"bu_id": b["bu_id"], "investment_ratio": 0.4,
             "capex_allocated": capex, "choice_selected": display}
            for b in bus
        ],
        "force_override_cfo": True,
        "expected_round": rnd,
    }
    r = client.post(f"/api/simulations/{sid}/commit-turn", json=payload)
    assert r.status_code == 201, f"R{rnd} commit failed: {r.status_code} {r.text[:400]}"
    return r.json()


def _submit(sid, q1, q2=(), q3=(), q4=(), force=False):
    payload = {
        "matrix_submission": {
            "quadrant_1_top_right": list(q1),
            "quadrant_2_top_left": list(q2),
            "quadrant_3_bottom_right": list(q3),
            "quadrant_4_bottom_left": list(q4),
        },
        "force_override_cfo": force,
    }
    return client.post(f"/api/simulations/{sid}/materiality", json=payload)


def _state(sid):
    """Latest persisted global state, with packed flags merged to top level."""
    g = dbm._global_states[sid][-1]
    flags = dict(g.get("active_event_flags") or {})
    merged = dict(flags)
    merged.update({k: v for k, v in g.items() if k != "active_event_flags"})
    return merged, flags


def _bus_latest(sid):
    rounds = dbm._bu_states.get(sid) or {}
    return rounds[max(rounds)] if rounds else []


def _string_quad(issue):
    hf = issue.get("financial_impact") == "high"
    hi = issue.get("societal_impact") == "high"
    return "q1" if (hf and hi) else "q2" if hi else "q3" if hf else "q4"


def _play_r2(choice, q1, q2=(), q3=(), force=False, capex=500_000, submit=True):
    """R1 commit → matrix submit → R2 commit. Returns (sid, merged_state, flags)."""
    sid, bus = _start()
    _commit(sid, bus, 1, "option_b")
    if submit:
        r = _submit(sid, q1, q2=q2, q3=q3, force=force)
        assert r.status_code == 200, r.text[:400]
    _commit(sid, bus, 2, choice, capex=capex)
    merged, flags = _state(sid)
    return sid, merged, flags


def _shipped_label_dictionaries():
    """Every shipped dictionary that carries the string axis labels."""
    out = {"materiality_db.DEFAULT_CONFIG": mdb.DEFAULT_CONFIG["issues"]}
    for bu_id, cfg in getattr(mdb, "BU_DEFAULT_CONFIGS", {}).items():
        issues = (cfg or {}).get("issues", [])
        if issues:
            out[f"materiality_db.BU_DEFAULT_CONFIGS[{bu_id}]"] = issues
    for path in sorted(glob.glob(os.path.join(_BACKEND_DIR, "db", "materiality_config_*.json"))):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        issues = data.get("issues", data) if isinstance(data, dict) else data
        if issues:
            out[os.path.basename(path)] = issues
    return out


# ── 1. Budget behaviour (F-3) ────────────────────────────────────────────────

@pytest.mark.parametrize("recall_n", [0, 1, 3, 5])
def test_fund_scales_with_recall_and_never_debits_treasury(recall_n):
    sid, bus = _start()
    _commit(sid, bus, 1, "option_b")
    treasury_before = dbm._global_states[sid][-1]["corporate_treasury"]

    q1 = Q1_IDS[:recall_n]
    r = _submit(sid, q1)
    assert r.status_code == 200, r.text[:300]
    body = r.json()

    expected_release = int(TOTAL_BUDGET * (recall_n / len(Q1_IDS)))
    assert body["allocated_budget"] == expected_release

    merged, _ = _state(sid)
    # Sign and magnitude: the release is a restricted fund, not a debit.
    assert merged["corporate_treasury"] == treasury_before
    assert merged.get("materiality_fund_released") == expected_release
    assert merged.get("materiality_restricted_fund", 0) >= expected_release


def test_fund_is_consumed_as_capex_offset():
    """The fund has a real consumer: it pays this round's ESG CapEx before the
    loan machinery. Full recall → $15M fund → 5 × $2M capex fully covered."""
    sid, bus = _start()
    _commit(sid, bus, 1, "option_b")
    assert _submit(sid, Q1_IDS).status_code == 200
    body = _commit(sid, bus, 2, "option_a", capex=2_000_000)
    ev = body.get("events") or {}
    merged, flags = _state(sid)
    used = ev.get("materiality_fund_used") or flags.get("materiality_fund_used")
    expected = 2_000_000 * len(bus)   # every BU's ESG capex drawn from the fund
    assert used == expected
    assert merged.get("materiality_restricted_fund") == TOTAL_BUDGET - expected


def test_q2_disclosure_budget_unlockable_and_credited_to_fund():
    sid, bus = _start()
    _commit(sid, bus, 1, "option_b")
    r = _submit(sid, Q1_IDS, q2=Q2_IDS, q3=Q3_IDS)
    assert r.status_code == 200
    merged, _ = _state(sid)
    unlocked = merged.get("q2_disclosure_budget_unlocked", 0)
    assert unlocked == 1_000_000, "both disclosure-carrying Q2 issues correct → full unlock"
    # Consumer: it is part of the spendable restricted fund.
    assert merged.get("materiality_restricted_fund") == TOTAL_BUDGET + unlocked


# ── 2. Precision gate ────────────────────────────────────────────────────────

def test_precision_gate_rejects_then_penalises_on_override():
    sid, bus = _start()
    _commit(sid, bus, 1, "option_b")
    rep_before = dbm._global_states[sid][-1]["group_reputation"]

    r = _submit(sid, Q1_IDS + Q3_IDS)  # a non-Q1 issue in Q1, no override
    assert r.status_code == 400
    assert "CFO Override" in r.json()["detail"]

    r = _submit(sid, Q1_IDS + Q3_IDS, force=True)
    assert r.status_code == 200
    merged, _ = _state(sid)
    assert merged["group_reputation"] == rep_before - 10


# ── 3. Option C actually penalises (F-3 direction) ───────────────────────────

def test_option_c_reduces_position_never_improves_it():
    """Direction asserted explicitly: same perfect matrix, same capex — the
    Option C team must end R2 strictly worse off (treasury + restricted fund)
    than the Option B team. F-3 existed because nobody ever asserted this."""
    _, m_b, _ = _play_r2("option_b", Q1_IDS, capex=4_000_000)
    _, m_c, _ = _play_r2("option_c", Q1_IDS, capex=4_000_000)

    def position(m):
        return m["corporate_treasury"] + float(m.get("materiality_restricted_fund", 0) or 0)

    assert m_c.get("r2_budget_clawback") == int(0.40 * TOTAL_BUDGET)
    # Option C's own impacts are treasury-neutral-or-positive (rev +400K/BU),
    # so a strictly lower position can only come from the clawback penalty.
    assert position(m_c) < position(m_b)


# ── 4. Per-unit impact sanity (F-7) ─────────────────────────────────────────

# Options allowed to exceed the 10%-of-group band, each with a reason.
REVENUE_DELTA_ALLOWLIST = {
    # R10 option_c is "Divest" — removing ~$10M of group revenue is plausibly
    # the point of a divestment. Pending design-owner confirmation (§5.3 of the
    # audit); remove from this list if the owner rules it a units error.
    (10, "option_c"),
}


def test_no_per_unit_revenue_delta_explodes_at_group_scale():
    from round_configs import get_round_options
    import bu_profiles as bp
    core = ["pharma", "electronics", "consumer_goods", "software", "oil_gas"]
    group = sum(bp.BU_PROFILES[k]["revenue_base"] for k in core)
    n_bus = len(core)
    offenders = []
    for rnd in range(1, 11):
        for key, opt in (get_round_options(rnd) or {}).items():
            if not isinstance(opt, dict):
                continue
            rd = (opt.get("impacts") or {}).get("revenue_delta", 0)
            if rd and abs(rd) * n_bus > 0.10 * group and (rnd, key) not in REVENUE_DELTA_ALLOWLIST:
                offenders.append((rnd, key, rd, rd * n_bus))
    assert not offenders, (
        f"revenue_delta is applied PER business unit; these options hit >10% of "
        f"group revenue base once multiplied out (the F-7 failure mode): {offenders}"
    )


def test_r2_option_a_group_revenue_effect_is_zero():
    """Acceptance: Option A applies NO revenue_delta. _apply_common_impacts
    stamps revenue_delta_applied_r2 whenever it mutates revenue_base — that
    marker must not exist for an Option A commit. (Session-to-session revenue
    comparison is useless here: market dynamics are seeded per session.)"""
    sid, bus = _start()
    _commit(sid, bus, 1, "option_b")
    assert _submit(sid, Q1_IDS).status_code == 200
    body = _commit(sid, bus, 2, "option_a")
    ev = body.get("events") or {}
    _, flags = _state(sid)
    assert "revenue_delta_applied_r2" not in ev
    assert "revenue_delta_applied_r2" not in flags


def test_r2_option_a_costs_what_it_says():
    from round_configs import get_round_options
    impacts = get_round_options(2)["option_a"]["impacts"]
    assert impacts["treasury"] == -2_500_000   # the documented compliance cost
    assert impacts["revenue_delta"] == 0       # was -2.5M PER BU = -$12.5M group


# ── 5. Flag tiering — all nine combinations (§4.1) ───────────────────────────

def _matrix_for(accuracy_band):
    """Placements yielding <80 / =80 / >80 full-quadrant accuracy."""
    if accuracy_band == "lt80":     # 2 correct of 5 placed = 40%
        return dict(q1=Q1_IDS[:2] + Q3_IDS + Q2_IDS, force=True)
    if accuracy_band == "eq80":     # 4 correct of 5 placed = 80%
        return dict(q1=Q1_IDS[:4] + Q3_IDS, force=True)
    return dict(q1=Q1_IDS, q2=Q2_IDS, q3=Q3_IDS, force=False)  # 100%


TIER_EXPECTATIONS = [
    ("option_a", "lt80", "materiality_ignored"),
    ("option_a", "eq80", "materiality_aligned"),
    ("option_a", "gt80", "materiality_aligned"),
    ("option_b", "lt80", "materiality_ignored"),
    ("option_b", "eq80", "materiality_partial"),
    ("option_b", "gt80", "materiality_partial"),
    ("option_c", "lt80", "materiality_ignored"),
    ("option_c", "eq80", "materiality_ignored"),
    ("option_c", "gt80", "materiality_ignored"),
]


@pytest.mark.parametrize("choice,band,expected", TIER_EXPECTATIONS)
def test_flag_tiering_matrix(choice, band, expected):
    spec = _matrix_for(band)
    sid, merged, flags = _play_r2(
        choice, spec["q1"], q2=spec.get("q2", ()), q3=spec.get("q3", ()),
        force=spec["force"],
    )
    # Asserted on what the valuation actually sees — the union collector —
    # not on what any single writer wrote.
    seen = _collect_all_flags(flags)
    tiers_seen = seen & {"materiality_aligned", "materiality_partial", "materiality_ignored"}
    assert tiers_seen == {expected}, (
        f"{choice}/{band}: expected {{{expected}}}, valuation sees {tiers_seen} "
        f"(accuracy={merged.get('materiality_full_accuracy')})"
    )
    assert merged.get("r2_governance_choice") == choice  # F-1: the key is written


def test_option_a_below_threshold_holds_no_premium_flag_at_any_point():
    sid, bus = _start()
    _commit(sid, bus, 1, "option_b")
    # 3 correct of 4 placed = 75% < 80
    r = _submit(sid, Q1_IDS[:3] + Q3_IDS, force=True)
    assert r.status_code == 200
    _, flags_mid = _state(sid)
    assert "materiality_aligned" not in _collect_all_flags(flags_mid)  # not at submit
    _commit(sid, bus, 2, "option_a")
    _, flags_end = _state(sid)
    seen = _collect_all_flags(flags_end)
    assert "materiality_aligned" not in seen and "materiality_partial" not in seen
    assert "materiality_ignored" in seen


def test_unsubmitted_matrix_scores_as_ignored():
    _, merged, flags = _play_r2("option_a", [], submit=False)
    seen = _collect_all_flags(flags)
    assert "materiality_ignored" in seen
    assert "materiality_aligned" not in seen


# ── 6. No dual-form flags (F-2 guard) ───────────────────────────────────────

@pytest.mark.parametrize("choice", ["option_a", "option_b", "option_c"])
def test_no_flag_exists_in_dual_form_after_r2(choice):
    sid, merged, flags = _play_r2(choice, Q1_IDS)
    assert _find_dual_form_flags(flags) == set()
    assert "dual_form_flags_detected" not in flags


def test_idempotency_record_never_leaks_flags():
    """Beyond the audit list: _collect_all_flags recursed into nested dicts,
    so the _materiality_idempotency replay bundle (whose debrief snapshot
    holds booleans like governance_board / q1_recall) leaked those names into
    the flag namespace. Underscore-prefixed state bags are storage, not flags."""
    bag = {"_materiality_idempotency": {"materiality_submitted_r2": {"debrief": {
        "assurance_signals": {"q1_recall": True, "governance_board": True,
                              "q2_disclosed": True, "ambiguous_handled": True}}}}}
    assert _collect_all_flags(bag) == set()


# ── 7 & 8. One classifier / quadrant coverage (F-6) ─────────────────────────

def test_one_classifier_for_every_shipped_dictionary():
    for name, issues in _shipped_label_dictionaries().items():
        for issue in issues:
            assert correct_quadrant_v2(issue) == _string_quad(issue), (
                f"{name}:{issue.get('id')} — numeric branch overrode the string "
                f"labels (F-6: legacy severity×likelihood must not classify)"
            )


def test_classifier_reaches_all_four_quadrants():
    mk = lambda f, s: {"financial_impact": f, "societal_impact": s}
    assert correct_quadrant_v2(mk("high", "high")) == "q1"
    assert correct_quadrant_v2(mk("low", "high")) == "q2"
    assert correct_quadrant_v2(mk("high", "low")) == "q3"
    assert correct_quadrant_v2(mk("low", "low")) == "q4"


def test_no_shipped_dictionary_collapses_to_the_diagonal():
    """The F-6 signature was every issue landing on Q1/Q4. Every shipped
    dictionary must place at least one issue in Q2 or Q3."""
    for name, issues in _shipped_label_dictionaries().items():
        quads = {correct_quadrant_v2(i) for i in issues}
        assert quads & {"q2", "q3"}, f"{name} collapsed to the Q1/Q4 diagonal: {quads}"


def test_default_config_covers_q1_q2_q3():
    quads = {correct_quadrant_v2(i) for i in mdb.DEFAULT_CONFIG["issues"]}
    assert {"q1", "q2", "q3"} <= quads


def test_csrd_library_covers_all_four_quadrants():
    quads = {i["correct_quadrant"] for i in CSRD_ISSUES.values()}
    assert quads == {1, 2, 3, 4}


# ── 9. Partial numeric scores rejected ──────────────────────────────────────

def test_no_shipped_issue_carries_partial_dual_axis_fields():
    for name, issues in _shipped_label_dictionaries().items():
        for issue in issues:
            present = [f for f in _DUAL_AXIS_FIELDS if issue.get(f) is not None]
            assert len(present) in (0, len(_DUAL_AXIS_FIELDS)), (
                f"{name}:{issue.get('id')} carries a PARTIAL dual-axis field set "
                f"{present} — all four or none"
            )


def test_legacy_severity_pairs_do_not_alter_classification():
    # Labels say q2; the legacy pair (5×5=25 ≥ 12) would say q1 — labels must win.
    issue = {"financial_impact": "medium", "societal_impact": "high",
             "severity_score": 5, "likelihood_score": 5}
    assert correct_quadrant_v2(issue) == "q2"
    # And all four dual-axis fields DO engage the numeric branch.
    dual = {"financial_impact": "medium", "societal_impact": "high",
            "impact_severity_score": 2, "impact_likelihood_score": 2,
            "financial_magnitude_score": 4, "financial_likelihood_score": 4}
    assert correct_quadrant_v2(dual) == "q3"  # fin 16≥12, imp 4<12 — labels overridden


# ── 10. Assurance signals — each reachable AND loseable (F-5, F-1) ──────────

def _signals(merged):
    return (merged.get("r2_esrs_debrief") or {}).get("assurance_signals") or {}


def test_assurance_all_four_signals_earnable_and_four_stars():
    # biodiversity (ambiguous, correct q2) placed adjacent in q1 → half credit
    # keeps accuracy ≥80% while exercising the adjacency path.
    sid, merged, _ = _play_r2(
        "option_a",
        Q1_IDS + ["biodiversity_financial_risk"],  # 5 full + 0.5 adjacent
        q2=["supply_chain_labor_risk"], q3=Q3_IDS, force=True,
    )
    sig = _signals(merged)
    assert sig == {"q1_recall": True, "governance_board": True,
                   "q2_disclosed": True, "ambiguous_handled": True}
    assert (merged.get("r2_esrs_debrief") or {}).get("assurance_stars") == 4


def test_assurance_each_signal_loseable():
    # q1_recall + ambiguous + q2 lost: 2-of-5 recall, ambiguous non-adjacent (q3),
    # no correct q2. governance_board lost via Option C.
    sid, merged, _ = _play_r2(
        "option_c", Q1_IDS[:2],
        q3=["biodiversity_financial_risk"],  # ambiguous, correct=q2, q3 NOT adjacent
        force=True,
    )
    sig = _signals(merged)
    assert sig["q1_recall"] is False
    assert sig["governance_board"] is False        # F-1: finally loseable
    assert sig["q2_disclosed"] is False
    assert sig["ambiguous_handled"] is False
    assert (merged.get("r2_esrs_debrief") or {}).get("assurance_stars") == 0


# ── 11. Documented cost matches applied cost ────────────────────────────────

_MONEY = re.compile(r"[-−+]?\$(\d+(?:\.\d+)?)\s*([MK])", re.IGNORECASE)


def _stated_amounts(text):
    out = set()
    for num, unit in _MONEY.findall(text or ""):
        out.add(float(num) * (1_000_000 if unit.upper() == "M" else 1_000))
    return out


def test_documented_cost_matches_applied_cost():
    """Every dollar figure an option's description states must be reconcilable
    with something the option actually applies (treasury, revenue_delta at
    per-unit OR group scale, or an explicitly configured amount). F-7 shipped
    because R2A's documentation said "$2.5M" while the engine applied $15M,
    and nothing ever compared the two."""
    from round_configs import get_round_options
    n_bus = 5
    failures = []
    for rnd in range(1, 11):
        for key, opt in (get_round_options(rnd) or {}).items():
            if not isinstance(opt, dict):
                continue
            stated = _stated_amounts(opt.get("description", ""))
            if not stated:
                continue
            impacts = opt.get("impacts") or {}
            applied = set()
            for k, v in {**opt, **impacts}.items():
                if isinstance(v, (int, float)) and abs(v) >= 1000:
                    applied.add(abs(v))
                    if k == "revenue_delta":
                        applied.add(abs(v) * n_bus)  # the group-scale effect
            unmatched = {s for s in stated if not any(abs(s - a) < 1 for a in applied)}
            if unmatched and applied:
                failures.append((rnd, key, sorted(unmatched), sorted(applied)))
    assert not failures, (
        "option descriptions state dollar figures their impacts do not apply: "
        f"{failures}"
    )


# ── 11b. The doc's R2 mechanics tables are generated, not hand-maintained ──

def test_simulation_context_r2_tables_match_generator():
    """SIMULATION_CONTEXT.md's Round 2 tables are spliced from
    scripts/generate_r2_mechanics_table.py, which builds them from
    round_configs and this file's TIER_EXPECTATIONS. If this fails, run:
        python3 scripts/generate_r2_mechanics_table.py --write"""
    import importlib.util
    root = os.path.dirname(_BACKEND_DIR)
    gen_path = os.path.join(root, "scripts", "generate_r2_mechanics_table.py")
    spec = importlib.util.spec_from_file_location("_gen_r2", gen_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    block = mod.build_block()
    with open(os.path.join(root, "SIMULATION_CONTEXT.md"), encoding="utf-8") as f:
        doc = f.read()
    assert block in doc, (
        "SIMULATION_CONTEXT.md Round 2 block is stale — regenerate with "
        "scripts/generate_r2_mechanics_table.py --write"
    )


def test_config_declares_the_real_accuracy_numbers():
    """F-4 guard: the special_rules keys must describe what the engine does."""
    from round_configs import get_round_config
    rules = (get_round_config(2) or {}).get("special_rules", {})
    assert rules.get("accuracy_threshold_pct") == 80
    assert rules.get("accuracy_bonus_points") == 1000
    assert "accuracy_bonus_amount" not in rules        # the phantom $2M
    assert "materiality_accuracy_treasury_bonus" not in rules


# ── 12. M_R ceilings unchanged ──────────────────────────────────────────────

def test_mr_ceilings_unchanged():
    from terminal_valuation import calculate_mr
    best = {"materiality_aligned": True, "synergy_unlock": True,
            "ethical_ai_overhaul": True, "community_fund": True}
    top = calculate_mr(best, avg_slo=90, avg_burnout=10, workforce_readiness=80,
                       synergy_multiplier=1.0, hr_investment_rounds=0)["mr"]
    assert top == pytest.approx(1.93, abs=1e-6)
    top_jt = calculate_mr(best, avg_slo=90, avg_burnout=10, workforce_readiness=80,
                          synergy_multiplier=1.0, hr_investment_rounds=5)["mr"]
    assert top_jt == pytest.approx(2.02, abs=1e-6)
    # The partial tier can never beat the full tier (ceiling intact).
    partial = calculate_mr({**best, "materiality_aligned": False, "materiality_partial": True},
                           avg_slo=90, avg_burnout=10, workforce_readiness=80,
                           synergy_multiplier=1.0, hr_investment_rounds=0)["mr"]
    assert partial == pytest.approx(1.88, abs=1e-6)
