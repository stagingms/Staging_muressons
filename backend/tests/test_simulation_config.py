import pytest
import database_memory
import database
import engine
import balance_sheet
import round_logic
import admin_router

pytestmark = pytest.mark.anyio

# Helper to construct a standard BU dict for tests
def make_test_bu(bu_id="software", revenue_base=10000000.0, opex_base=5000000.0, carbon_intensity=10.0, natural_capital_debt=0.0):
    return {
        "bu_id": bu_id,
        "revenue_base": revenue_base,
        "opex_base": opex_base,
        "natural_capital_debt": natural_capital_debt,
        "social_license_score": 55.0,
        "reputation_score": 52.0,
        "governance_risk_score": 15.0,
        "water_dependency": 82.0,
        "carbon_intensity": carbon_intensity,
        "risk_factors": {},
    }

async def test_sim_initial_budget(monkeypatch):
    monkeypatch.setattr(database_memory, "SIM_INITIAL_BUDGET", 80000000.0)
    
    # Create a session and check starting corporate treasury
    sess = await database_memory.create_session(cohort_name="TestBudgetCohort")
    session_id = sess["session_id"]
    
    # Fetch global state
    from database_memory import _global_states
    gs_list = _global_states.get(session_id)
    assert gs_list is not None
    assert len(gs_list) > 0
    # The starting treasury should be 80M (the mocked SIM_INITIAL_BUDGET)
    assert gs_list[0]["corporate_treasury"] == 80000000.0

async def test_sim_rounds(monkeypatch):
    monkeypatch.setattr(database_memory, "SIM_ROUNDS", 7)
    monkeypatch.setattr(admin_router, "SIM_ROUNDS", 7)
    
    # Create a session and check max_unlocked_round
    sess = await database_memory.create_session(cohort_name="TestRoundsCohort")
    session_id = sess["session_id"]
    
    # Check max_unlocked_round from database_memory fetch_all_sessions
    sessions = await database_memory.fetch_all_sessions()
    target = next((s for s in sessions if s["session_id"] == session_id), None)
    assert target is not None
    assert target["max_unlocked_round"] == 7

def test_economic_carbon_price(monkeypatch):
    monkeypatch.setattr(engine, "ECONOMIC_CARBON_PRICE_BASE", 60.0)
    monkeypatch.setattr(engine, "ECONOMIC_CARBON_PRICE_GROWTH", 0.05)
    
    # Set up inputs for process_tick
    global_state = {
        "round_number": 2,
        "corporate_treasury": 10000000.0,
        "group_reputation": 50.0,
        "synergy_multiplier": 1.0,
        "cost_of_capital": 0.05,
        "inflation_index": 0.05,
        "competitor_ebitda": 10000000.0,
        "active_event_flags": {},
    }
    bu_states = [make_test_bu(carbon_intensity=10.0, revenue_base=10000000.0, opex_base=5000000.0)]
    decisions = [
        {
            "bu_id": "software",
            "investment_ratio": 0.0,
            "capex_allocated": 0,
        }
    ]
    
    # Verify fee per ton scales correctly
    # base_fee = 60
    # fee_per_ton = round(60 * (1 + 0.05) ** (2 - 1), 2) = 63.0
    # total emissions will be computed by engine, and round_carbon_fee_total = tco2e_emissions * fee_per_ton
    res = engine.process_tick(global_state, bu_states, decisions, decision_paradigm="advanced_climate")
    carbon_fee_applied = res["events"].get("internal_carbon_fee_deducted", 0)
    
    tco2e_emissions = res["global_state"].get("tco2e_emissions", 0.0)
    expected_fee = round(tco2e_emissions * 63.0, 2)
    assert carbon_fee_applied == expected_fee

def test_constraint_max_carbon_emissions(monkeypatch):
    global_state = {
        "round_number": 1,
        "corporate_treasury": 10000000.0,
        "group_reputation": 50.0,
        "synergy_multiplier": 1.0,
        "cost_of_capital": 0.05,
        "inflation_index": 0.05,
        "competitor_ebitda": 10000000.0,
        "active_event_flags": {},
    }
    # Emissions: carbon_intensity (100) * revenue (1M) = 100 tCO2e
    bu_states = [make_test_bu(carbon_intensity=100.0, revenue_base=1000000.0)]
    decisions = [
        {
            "bu_id": "software",
            "investment_ratio": 0.0,
            "capex_allocated": 0,
        }
    ]
    
    # Run with large limit (no breach)
    monkeypatch.setattr(engine, "CONSTRAINT_MAX_CARBON_EMISSIONS", 5000.0)
    res_no_breach = engine.process_tick(dict(global_state), [dict(b) for b in bu_states], decisions)
    rep_no_breach = res_no_breach["global_state"]["group_reputation"]
    
    # Run with small limit (breach)
    monkeypatch.setattr(engine, "CONSTRAINT_MAX_CARBON_EMISSIONS", 50.0)
    res_breach = engine.process_tick(dict(global_state), [dict(b) for b in bu_states], decisions)
    rep_breach = res_breach["global_state"]["group_reputation"]
    
    # Emissions are 100 tCO2e which exceeds 50.0 max carbon emissions constraint.
    # Group reputation should be reduced by 5.0, and custom black swan warning should be triggered.
    assert res_breach["events"].get("emissions_limit_breached") is True
    assert round(rep_no_breach - rep_breach, 2) == 5.0
    custom_swans = res_breach["events"].get("custom_black_swans", [])
    assert len(custom_swans) > 0
    assert any("⚠️ CARBON EMISSIONS LIMIT BREACHED" in s["title"] for s in custom_swans)

def test_constraint_min_liquidity_ratio(monkeypatch):
    monkeypatch.setattr(balance_sheet, "CONSTRAINT_MIN_LIQUIDITY_RATIO", 0.50)
    
    # Generate a valid initial balance sheet structure
    bus = [make_test_bu()]
    bs = balance_sheet.create_initial_balance_sheet(bus)
    
    # Manually tweak assets/cash to guarantee a low liquidity ratio (< 0.50)
    # total assets will be recalculated, but let's make sure cash is low relative to others
    bs["current_assets"]["cash_and_equivalents"] = 100000.0
    
    # Mock global state with low corporate treasury so it matches cash
    gs = {"corporate_treasury": 100000.0}
    events = {}
    
    # Running balance sheet tick should downgrade covenant_status to 'amber' and create warning
    new_bs, new_diag = balance_sheet.process_balance_sheet_tick(bs, gs, bus, events, round_number=1)
    assert new_bs["covenant_status"] == "amber"
    assert "liquidity_ratio_warning" in new_diag
    assert "minimum of 50.0%" in new_diag["liquidity_ratio_warning"]

def test_circular_economy_bonus(monkeypatch):
    monkeypatch.setattr(round_logic, "ECONOMIC_CIRCULAR_ECONOMY_BONUS", 0.25)
    
    gs = {
        "group_synergy_multiplier": 1.0,
        "green_transition_fund": 0.0,
        "corporate_treasury": 10000000.0,
        "group_reputation": 50.0,
        "synergy_multiplier": 1.0
    }
    bus = [make_test_bu(opex_base=1000000.0)]
    decs = [{"choice_selected": "option_a"}]
    events = {}
    extra = {}
    
    # Run _post_r7_circularity
    round_logic._post_r7_circularity(gs, bus, decs, events, extra, {})
    
    # OPEX base should be reduced by 25% to 750k
    assert bus[0]["opex_base"] == 750000.0
    assert extra.get("circular_efficiency_bonus_applied") == 0.25
