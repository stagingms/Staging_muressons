"""
Muressons Global Corporation — Global State Traversal & Validation Harness
============================================================================

Executes a systematic traversal of the SimulationOrchestrator (process_tick)
across all decision paradigms, every ending pathway, and both BU-mode configs
(4BU and Single-BU per each of the 4 BUs).

Coverage matrix
───────────────
  Paradigms (up to 10 rounds each, brsr_ngrbc capped at 5):
    legacy_abc · multi_toggles · advanced_climate · healthcare
    un_sdg · brsr_ngrbc

  Ending pathways (all 5):
    activist_ultimatum · climate_black_swan · stakeholder_revolt
    hostile_takeover · regulatory_shutdown

  BU modes:
    4BU mode (all four BUs active)
    Single-BU mode × 4 (one BU per run)

Injections & validation
───────────────────────
  • Randomised 'Noise' injected into the sustainability feed each round
    (stakeholder volatility — reputation ±5–15, SLO ±3–10).
  • 20% of agents forced into Non-Collaborative mode each round
    (branching path analysis — lower investment_ratio, conservative pillars).
  • Terminal value deviation flagged when delta from round-mean > ±5%.
  • Collaboration Gap delta and CPU latency logged per round.

Execution constraints
─────────────────────
  • /commit-turn enforces a 5-second per-session rate limiter → sleep 5.2s.
  • /materiality deducts from treasury → called once per R2 visit.
  • Memory-DB mode enforced via USE_MEMORY_DB=true.
"""

import os
os.environ["USE_MEMORY_DB"] = "true"

import sys
import time
import random
import json
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from fastapi.testclient import TestClient
from main import app

# ─── Constants ────────────────────────────────────────────────────────────────

client = TestClient(app)

ALL_BU_IDS = ["pharma", "electronics", "consumer_goods", "software"]

ALL_PARADIGMS = [
    "legacy_abc",
    "multi_toggles",
    "advanced_climate",
    "healthcare",
    "un_sdg",      # BUG-SDG-001 fixed: sdg_configs.py adapter created
    "brsr_ngrbc",  # BUG-BRSR-001 fixed: brsr_controller.py .update() -> .to_seed_dict()
]

PARADIGM_MAX_ROUNDS = {
    "legacy_abc":       10,
    "multi_toggles":    10,
    "advanced_climate": 10,
    "healthcare":       10,
    "un_sdg":           10,
    "brsr_ngrbc":        5,  # Hard cap — paradigm completes at R5
}

# BU modes supported per paradigm.
# 'healthcare' uses a custom seed (seed_healthcare.json) with BU IDs
# [hospitals, clinics, specialised_care, telehealth] that don't match the
# generic ALL_BU_IDS. Single-BU mode for healthcare is not implemented
# — it always runs as a 4-BU healthcare conglomerate.
# 'un_sdg' and 'brsr_ngrbc' support single-BU via the assigned_bu patch.
PARADIGM_SUPPORTED_BU_MODES: dict[str, list[str]] = {
    "legacy_abc":       ["4bu"] + ["pharma", "electronics", "consumer_goods", "software"],
    "multi_toggles":    ["4bu"] + ["pharma", "electronics", "consumer_goods", "software"],
    "advanced_climate": ["4bu"] + ["pharma", "electronics", "consumer_goods", "software"],
    "healthcare":       ["4bu"],   # healthcare BUs: hospitals/clinics/specialised_care/telehealth
    "un_sdg":           ["4bu"] + ["pharma", "electronics", "consumer_goods", "software"],
    "brsr_ngrbc":       ["4bu"] + ["pharma", "electronics", "consumer_goods", "software"],
}

ALL_PATHWAY_IDS = [
    "activist_ultimatum",
    "climate_black_swan",
    "stakeholder_revolt",
    "hostile_takeover",
    "regulatory_shutdown",
]

# Noise band for stakeholder volatility injection
NOISE_REPUTATION_RANGE = (5, 15)
NOISE_SLO_RANGE = (3, 10)
NON_COLLABORATIVE_FRACTION = 0.20   # 20% of BU agents go non-collaborative
TERMINAL_VALUE_DEVIATION_THRESHOLD = 0.05   # ±5%

# ─── Trace & Metric Structures ────────────────────────────────────────────────

@dataclass
class RoundTrace:
    round_num: int
    paradigm: str
    pathway: str
    bu_mode: str
    treasury: float = 0.0
    ebitda: float = 0.0
    reputation: float = 0.0
    co2: float = 0.0
    collaboration_gap: Optional[float] = None
    gap_label: str = ""
    terminal_value: Optional[float] = None
    tv_deviation_pct: Optional[float] = None
    tv_flagged: bool = False
    noise_injected: dict = field(default_factory=dict)
    non_collab_bus: list = field(default_factory=list)
    latency_ms: float = 0.0
    events: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    call_trace: list = field(default_factory=list)   # function call sequence leading to deviation


@dataclass
class RunSummary:
    paradigm: str
    pathway: str
    bu_mode: str
    session_id: str
    final_round: int
    passed: bool
    errors: list = field(default_factory=list)
    gap_history: list = field(default_factory=list)
    terminal_values: list = field(default_factory=list)
    flagged_rounds: list = field(default_factory=list)
    peak_gap: Optional[float] = None
    avg_latency_ms: float = 0.0
    total_rounds_run: int = 0
    # Per-round call traces for TV deviation flags (round_num → trace lines)
    call_traces: dict = field(default_factory=dict)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def api(method: str, path: str, data=None, expect=None):
    """Thin wrapper around TestClient calls. Returns response object."""
    if method == "GET":
        r = client.get(path)
    elif method == "POST":
        r = client.post(path, json=data)
    elif method == "PUT":
        r = client.put(path, json=data)
    elif method == "DELETE":
        r = client.delete(path)
    else:
        raise ValueError(f"Unknown method: {method}")
    if expect and r.status_code != expect:
        print(f"    !! {method} {path} => {r.status_code}: {r.text[:300]}")
    return r


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_noise() -> dict:
    """Generate randomised noise payload for a round."""
    direction = random.choice([1, -1])
    return {
        "reputation_delta": direction * random.randint(*NOISE_REPUTATION_RANGE),
        "slo_delta": direction * random.randint(*NOISE_SLO_RANGE),
        "label": f"noise_{random.choice(['activist', 'media', 'regulator', 'ngo', 'investor'])}",
    }


def pick_non_collaborative_bus(active_bus: list) -> list:
    """Randomly mark ~20% of BU agents as non-collaborative."""
    k = max(1, round(len(active_bus) * NON_COLLABORATIVE_FRACTION))
    return random.sample(active_bus, k=min(k, len(active_bus)))


def inject_noise_via_override(sid: str, noise: dict) -> bool:
    """
    Inject stakeholder volatility noise into the session via god-mode override.
    Uses /api/admin/{sid}/override with type 'reputation_delta'.
    Falls back gracefully if endpoint not available.
    """
    if noise["reputation_delta"] == 0:
        return True
    payload = {
        "override_type": "reputation_delta",
        "parameters": {
            "reputation_delta": noise["reputation_delta"],
            "slo_delta": noise["slo_delta"],
            "source": noise["label"],
        },
    }
    r = api("POST", f"/api/admin/{sid}/override", payload)
    return r.status_code in (200, 201, 204)


def calc_terminal_value_from_dashboard(dash: dict) -> Optional[float]:
    """
    Derive a terminal-value proxy from dashboard global_state.
    TV = corporate_treasury + (EBITDA × synergy_multiplier × 12)
    """
    gs = dash.get("global_state", {})
    treasury = gs.get("corporate_treasury", 0)
    ebitda = gs.get("historical_ebitda", 0)
    synergy = gs.get("group_synergy_multiplier", gs.get("synergy_multiplier", 1.0))
    return round(treasury + ebitda * synergy * 12, 2)


def get_gap_from_response(resp_json: dict) -> tuple[Optional[float], str]:
    """
    Extract collaboration_gap float from a commit-turn response.
    Searches analytics, extra_events, and events dict.
    """
    # Try analytics sub-key
    for key in ("analytics", "round_analytics", "extra_events"):
        sub = resp_json.get(key)
        if isinstance(sub, dict):
            gap_val = sub.get("collaboration_gap")
            if isinstance(gap_val, (int, float)):
                return float(gap_val), sub.get("gap_label", "")
    # Try events dict
    events = resp_json.get("events", {})
    if isinstance(events, dict):
        gap_val = events.get("collaboration_gap")
        if isinstance(gap_val, (int, float)):
            return float(gap_val), events.get("gap_label", "")
    return None, ""


# ─── Session Management ───────────────────────────────────────────────────────

# Paradigms routed through /solo-start instead of /start.
# un_sdg: /start excludes it from _VALID_PARADIGMS (line 679 router.py).
# brsr_ngrbc: uses /start — it is in _VALID_PARADIGMS at line 679.
_SOLO_ONLY_PARADIGMS: set = {"un_sdg"}


def create_session(paradigm: str, pathway: str, label: str, bu_mode: str = "4bu") -> Optional[str]:
    """
    Create a new simulation session. Returns session_id or None.

    Routes un_sdg paradigm through /solo-start (the only endpoint that accepts it).
    For single-BU mode, writes assigned_bu directly into database_memory._sessions
    post-creation so that commit_turn's _commit_assigned_bu resolution (router.py:1275)
    correctly narrows VULN-009 to the one active BU.

    Direct-write rationale
    ─────────────────────
    /solo-start's SoloStartRequest schema declares no simulation_mode field, so
    the router cannot forward assigned_bu into db.create_session for un_sdg.
    /start does propagate assigned_bu for healthcare/brsr_ngrbc, but the direct
    write is idempotent (same value) and guarantees both code paths are consistent.
    We access _sessions directly rather than going through an HTTP endpoint to
    avoid introducing a new admin API surface for internal harness use only.
    """
    is_single_bu = bu_mode != "4bu"

    if paradigm in _SOLO_ONLY_PARADIGMS:
        payload = {
            "player_name": label,
            "decision_paradigm": paradigm,
        }
        r = api("POST", "/api/simulations/solo-start", payload, expect=201)
        if r.status_code != 201:
            return None
        sid = r.json().get("session_id")
        if sid and pathway:
            _apply_pathway_override(sid, pathway)
    else:
        payload = {
            "cohort_name": label,
            "decision_paradigm": paradigm,
            "ending_pathway": pathway,
        }
        if is_single_bu:
            payload["simulation_mode"] = "single_bu"
            payload["industry_vertical"] = bu_mode
        r = api("POST", "/api/simulations/start", payload, expect=201)
        if r.status_code != 201:
            return None
        sid = r.json().get("session_id")

    if not sid:
        return None

    # ── Single-BU post-creation patch ─────────────────────────────────────
    # Write assigned_bu, simulation_mode, and industry_vertical into the raw
    # session store for ALL paradigms.  commit_turn reads _sessions[sid] directly
    # via db.get_session_info(), so this is the authoritative single fix-point.
    if is_single_bu:
        try:
            import database_memory as _dm  # tripwire-allow: offline QA harness, memory-mode only
            sess = _dm._sessions.get(sid)
            if sess is not None:
                sess["assigned_bu"]      = bu_mode  # e.g. 'pharma'
                sess["simulation_mode"]  = "single_bu"
                sess["industry_vertical"] = bu_mode
        except Exception as _e:
            print(f"    [WARN] single-BU session patch failed for {sid}: {_e}")

    return sid



def _apply_pathway_override(sid: str, pathway: str) -> None:
    """Apply an ending pathway to an already-created session via god-mode override."""
    r = api("POST", f"/api/admin/{sid}/override", {
        "override_type": "ending_pathway",
        "parameters": {"pathway_id": pathway},
    })
    if r.status_code not in (200, 201, 204):
        # Fallback: write directly to active_event_flags via state override
        api("POST", f"/api/admin/{sid}/override", {
            "override_type": "set_flag",
            "parameters": {"flag": "ending_pathway", "value": pathway},
        })


def get_dashboard(sid: str) -> dict:
    r = api("GET", f"/api/simulations/{sid}/dashboard")
    if r.status_code == 200:
        return r.json()
    return {}


def get_active_bus(sid: str, bu_mode: str) -> list:
    """
    Return active BU list for this run.
    bu_mode is either '4bu' or one of the BU IDs (single mode).
    """
    if bu_mode == "4bu":
        dash = get_dashboard(sid)
        bus = [bu["bu_id"] for bu in dash.get("business_units", [])]
        return bus if bus else ALL_BU_IDS
    else:
        return [bu_mode]  # single-BU mode


def submit_stakeholder_map(sid: str) -> bool:
    r = api("GET", "/api/simulations/stakeholder-map/stakeholders")
    if r.status_code != 200:
        return False
    stakeholders = r.json().get("stakeholders", [])
    quadrants = [
        "high_power_high_interest", "high_power_low_interest",
        "low_power_high_interest", "low_power_low_interest",
    ]
    mapping = {
        s.get("id", s.get("stakeholder_id", f"s{i}")): quadrants[i % 4]
        for i, s in enumerate(stakeholders)
    }
    r2 = api("POST", f"/api/simulations/{sid}/stakeholder-map", {"mapping": mapping})
    return r2.status_code == 200


def submit_materiality(sid: str, paradigm: str, bu_id: Optional[str] = None) -> bool:
    """Submit materiality matrix for R2 gate. Handles multi_toggles BU selection."""
    if paradigm == "multi_toggles" and bu_id is None:
        r = api("GET", f"/api/admin/{sid}/r2-bu-selection")
        if r.status_code == 200:
            bu_id = r.json().get("selected_bu")

    endpoint = f"/api/admin/materiality-config/bu/{bu_id}" if bu_id else "/api/admin/materiality-config"
    r = api("GET", endpoint)
    if r.status_code != 200:
        return False
    config = r.json()
    issues = config.get("issues", [])

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
    if bu_id:
        payload["bu_id"] = bu_id
    r2 = api("POST", f"/api/simulations/{sid}/materiality", payload)
    return r2.status_code == 200


# ─── Commit Turn ──────────────────────────────────────────────────────────────

def build_decisions(
    active_bus: list,
    round_num: int,
    paradigm: str,
    non_collab_bus: list,
) -> list:
    """
    Build decision payload for all BUs.
    BUs in non_collab_bus receive conservative/low-engagement settings.
    """
    options = ["option_a", "option_b", "option_c"]
    pillar_opts = ["aggressive", "moderate", "conservative"]

    decisions = []
    for bu in active_bus:
        is_non_collab = bu in non_collab_bus
        inv_ratio = 0.1 if is_non_collab else 0.3
        capex = 100_000 if is_non_collab else 500_000
        choice = options[(round_num - 1) % 3] if paradigm in ("legacy_abc", "healthcare") else ""

        d = {
            "bu_id": bu,
            "investment_ratio": inv_ratio,
            "capex_allocated": capex,
            "choice_selected": choice,
        }

        # Pillar decisions for toggle-based paradigms
        if paradigm in ("multi_toggles", "advanced_climate", "un_sdg", "brsr_ngrbc"):
            if is_non_collab:
                # Non-collaborative: all pillars conservative
                d["pillar_decisions"] = {
                    "energy": "conservative",
                    "operations": "conservative",
                    "supply_chain": "conservative",
                    "offsetting": "conservative",
                }
            else:
                # Rotate to cover diverse decision paths
                d["pillar_decisions"] = {
                    "energy":        pillar_opts[round_num % 3],
                    "operations":    pillar_opts[(round_num + 1) % 3],
                    "supply_chain":  pillar_opts[(round_num + 2) % 3],
                    "offsetting":    pillar_opts[round_num % 3],
                }

        decisions.append(d)
    return decisions


def commit_turn(
    sid: str,
    round_num: int,
    paradigm: str,
    active_bus: list,
    non_collab_bus: list,
) -> tuple[Optional[dict], float]:
    """
    POST /commit-turn. Returns (response_json, latency_ms).
    """
    decisions = build_decisions(active_bus, round_num, paradigm, non_collab_bus)
    payload = {
        "decisions": decisions,
        "dividends_paid": 0,
        "crisis_severity": 0,
        "force_override_cfo": True,
    }
    t0 = time.perf_counter()
    r = api("POST", f"/api/simulations/{sid}/commit-turn", payload)
    latency_ms = (time.perf_counter() - t0) * 1000

    if r.status_code in (200, 201):
        return r.json(), latency_ms
    return None, latency_ms


# ─── Deviation Detection ──────────────────────────────────────────────────────

def check_terminal_value_deviation(
    tv_history: list,
    current_tv: float,
    round_num: int,
    call_trace: list,
) -> tuple[Optional[float], bool, list]:
    """
    Compare current TV to running mean. Flag if deviation > ±5%.
    Returns (deviation_pct, flagged, enriched_call_trace).
    """
    if len(tv_history) < 2:
        return None, False, call_trace

    mean_tv = sum(tv_history[:-1]) / len(tv_history[:-1])
    if mean_tv == 0:
        return None, False, call_trace

    deviation_pct = (current_tv - mean_tv) / abs(mean_tv)
    flagged = abs(deviation_pct) > TERMINAL_VALUE_DEVIATION_THRESHOLD

    if flagged:
        enriched = call_trace + [
            f"DEVIATION FLAG @ R{round_num}",
            f"  current_tv  = ${current_tv:,.0f}",
            f"  rolling_mean = ${mean_tv:,.0f}",
            f"  deviation   = {deviation_pct*100:+.2f}%  (threshold ±{TERMINAL_VALUE_DEVIATION_THRESHOLD*100:.0f}%)",
            f"  trigger     = calc_terminal_value_from_dashboard → commit-turn → process_tick",
        ]
        return round(deviation_pct, 4), True, enriched

    return round(deviation_pct, 4), False, call_trace


# ─── Single Run ───────────────────────────────────────────────────────────────

def run_single(
    paradigm: str,
    pathway: str,
    bu_mode: str,
    seed: Optional[int] = None,
) -> RunSummary:
    """
    Execute one complete simulation run (up to max rounds for paradigm).
    """
    if seed is not None:
        random.seed(seed)

    max_rounds = PARADIGM_MAX_ROUNDS.get(paradigm, 10)
    label = f"traversal_{paradigm}_{pathway}_{bu_mode}_{int(time.time())}"

    print(f"\n  +-- paradigm={paradigm}  pathway={pathway}  bu_mode={bu_mode}")

    sid = create_session(paradigm, pathway, label, bu_mode=bu_mode)
    if not sid:
        print(f"  +-- FAILED: could not create session")
        return RunSummary(
            paradigm=paradigm, pathway=pathway, bu_mode=bu_mode,
            session_id="", final_round=0, passed=False,
            errors=["session_creation_failed"],
        )

    summary = RunSummary(
        paradigm=paradigm, pathway=pathway, bu_mode=bu_mode,
        session_id=sid, final_round=0, passed=False,
    )

    materiality_done = False
    last_round_seen = None
    tv_history: list[float] = []
    latencies: list[float] = []
    round_traces: list[RoundTrace] = []

    for attempt in range(1, max_rounds + 1):
        dash = get_dashboard(sid)
        current_round = dash.get("current_round", attempt)
        gs = dash.get("global_state", {})

        if current_round != last_round_seen:
            materiality_done = False
        last_round_seen = current_round

        # R1 gate: stakeholder map
        if current_round == 1:
            ok = submit_stakeholder_map(sid)
            if not ok:
                summary.errors.append(f"R1: stakeholder_map_failed")

        # R2 gate: materiality (once per R2)
        if current_round == 2 and not materiality_done:
            ok = submit_materiality(sid, paradigm)
            if not ok:
                summary.errors.append(f"R2: materiality_failed")
            materiality_done = True

        # ── Noise Injection ──────────────────────────────────────
        noise = generate_noise()
        noise_ok = inject_noise_via_override(sid, noise)
        noise_label = noise["label"] if noise_ok else f"{noise['label']}(skipped)"

        # ── Non-Collaborative Branching ──────────────────────────
        active_bus = get_active_bus(sid, bu_mode)
        non_collab = pick_non_collaborative_bus(active_bus)

        # ── Commit Turn ──────────────────────────────────────────
        call_trace = [
            f"create_session(paradigm={paradigm}, pathway={pathway})",
            f"inject_noise({noise_label})",
            f"pick_non_collaborative_bus({non_collab})",
            f"build_decisions(round={current_round}, paradigm={paradigm})",
            f"commit_turn → POST /api/simulations/{sid}/commit-turn",
            f"  → process_tick(round={current_round})",
        ]

        resp, latency_ms = commit_turn(sid, current_round, paradigm, active_bus, non_collab)
        latencies.append(latency_ms)

        trace = RoundTrace(
            round_num=current_round,
            paradigm=paradigm,
            pathway=pathway,
            bu_mode=bu_mode,
            noise_injected=noise,
            non_collab_bus=non_collab,
            latency_ms=round(latency_ms, 2),
        )

        if resp is None:
            trace.errors.append(f"commit_turn_failed at R{current_round}")
            summary.errors.append(f"R{current_round}: commit_failed")
            round_traces.append(trace)
            print(f"  |  R{current_round}: FAIL commit failed -- aborting run")
            break

        # ── Extract metrics ──────────────────────────────────────
        rgs = resp.get("global_state", {})
        trace.treasury   = rgs.get("corporate_treasury", 0)
        trace.ebitda     = rgs.get("historical_ebitda", 0)
        trace.reputation = rgs.get("group_reputation", 0)
        trace.co2        = rgs.get("tco2e_emissions", 0)

        gap, gap_label = get_gap_from_response(resp)
        trace.collaboration_gap = gap
        trace.gap_label = gap_label
        if gap is not None:
            summary.gap_history.append({"round": current_round, "gap": gap, "label": gap_label})

        # Terminal value
        post_dash = get_dashboard(sid)
        tv = calc_terminal_value_from_dashboard(post_dash)
        trace.terminal_value = tv
        tv_history.append(tv if tv is not None else 0)
        summary.terminal_values.append(tv)

        # Deviation check
        dev_pct, flagged, enriched_trace = check_terminal_value_deviation(
            tv_history, tv or 0, current_round, call_trace
        )
        trace.tv_deviation_pct = dev_pct
        trace.tv_flagged = flagged
        if flagged:
            trace.call_trace = enriched_trace
            summary.flagged_rounds.append(current_round)
            # Store trace in summary for report export
            summary.call_traces[current_round] = enriched_trace
            print(f"  |  R{current_round}: WARN TV deviation {dev_pct*100:+.2f}%")

        # Events
        events = resp.get("events", {})
        trace.events = [k for k in events.keys() if k != "decision_paradigm"]

        round_traces.append(trace)
        summary.total_rounds_run += 1
        summary.final_round = current_round

        new_rnd = resp.get("new_round_number", "?")
        gap_str = f"  gap={gap:+.1f}" if gap is not None else ""
        print(
            f"  |  R{current_round}->R{new_rnd}: "
            f"treasury=${trace.treasury/1e6:.2f}M  "
            f"rep={trace.reputation:.1f}  "
            f"co2={trace.co2:,.0f}t"
            f"{gap_str}  "
            f"[{latency_ms:.0f}ms]"
            + (f"  [{', '.join(trace.events[:3])}]" if trace.events else "")
        )

        # Stop if we have reached max rounds
        if current_round >= max_rounds:
            break

        # Rate limiter — must wait 5s between commits
        time.sleep(5.2)

    # ── Final pass / summary ─────────────────────────────────────
    if summary.gap_history:
        gaps = [g["gap"] for g in summary.gap_history]
        summary.peak_gap = max(gaps, key=abs)

    summary.avg_latency_ms = (
        round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    )
    summary.passed = (
        len(summary.errors) == 0
        and summary.total_rounds_run >= min(3, max_rounds)
    )

    status = "PASS" if summary.passed else "FAIL"
    print(
        f"  +-- {status} | rounds={summary.total_rounds_run}/{max_rounds} | "
        f"flags={len(summary.flagged_rounds)} | "
        f"avg_lat={summary.avg_latency_ms:.0f}ms | "
        f"errors={summary.errors or 'none'}"
    )

    return summary


# ─── Traversal Runner ─────────────────────────────────────────────────────────

def build_run_matrix() -> list[tuple[str, str, str]]:
    """
    Build the full (paradigm, pathway, bu_mode) matrix.
    BU modes are per-paradigm via PARADIGM_SUPPORTED_BU_MODES.
    """
    matrix = []
    for paradigm in ALL_PARADIGMS:
        supported = PARADIGM_SUPPORTED_BU_MODES.get(paradigm, ["4bu"] + ALL_BU_IDS)
        for pathway in ALL_PATHWAY_IDS:
            for bu_mode in supported:
                matrix.append((paradigm, pathway, bu_mode))
    return matrix


def run_traversal(
    paradigms: Optional[list] = None,
    pathways: Optional[list] = None,
    bu_modes: Optional[list] = None,
    seed: int = 42,
) -> list[RunSummary]:
    """
    Execute the Global State Traversal.

    Parameters
    ----------
    paradigms : subset of ALL_PARADIGMS (or None for all)
    pathways  : subset of ALL_PATHWAY_IDS (or None for all)
    bu_modes  : subset of ['4bu','pharma','electronics','consumer_goods','software']
    seed      : global random seed for reproducibility
    """
    random.seed(seed)

    target_paradigms = paradigms or ALL_PARADIGMS
    target_pathways  = pathways  or ALL_PATHWAY_IDS
    # If bu_modes is explicitly specified, use it for all paradigms.
    # If None, apply per-paradigm BU mode filtering from PARADIGM_SUPPORTED_BU_MODES.
    _explicit_bu_modes = bu_modes  # could be None

    # Compute total runs respecting per-paradigm BU mode constraints
    total_runs = 0
    for paradigm in target_paradigms:
        _bu_for_paradigm = _explicit_bu_modes or PARADIGM_SUPPORTED_BU_MODES.get(paradigm, ["4bu"] + ALL_BU_IDS)
        total_runs += len(target_pathways) * len(_bu_for_paradigm)

    print("\n" + "=" * 70)
    print("  MURESSONS -- GLOBAL STATE TRAVERSAL")
    print(f"  {now_utc()}")
    print("=" * 70)
    print(f"  Paradigms  : {target_paradigms}")
    print(f"  Pathways   : {target_pathways}")
    print(f"  BU modes   : per-paradigm (healthcare=4bu only; others=4bu+4 singles)")
    print(f"  Total runs : {total_runs}")
    print(f"  Noise      : +/-{NOISE_REPUTATION_RANGE} rep / +/-{NOISE_SLO_RANGE} SLO per round")
    print(f"  Non-collab : {int(NON_COLLABORATIVE_FRACTION*100)}% of BU agents per round")
    print(f"  TV trigger : +/-{int(TERMINAL_VALUE_DEVIATION_THRESHOLD*100)}% deviation threshold")
    print("=" * 70)

    all_summaries: list[RunSummary] = []
    run_index = 0

    for paradigm in target_paradigms:
        _bu_modes_for_paradigm = (
            _explicit_bu_modes
            or PARADIGM_SUPPORTED_BU_MODES.get(paradigm, ["4bu"] + ALL_BU_IDS)
        )
        for pathway in target_pathways:
            for bu_mode in _bu_modes_for_paradigm:
                run_index += 1
                run_seed = seed + run_index
                print(f"\n[{run_index}/{total_runs}]", end="")
                try:
                    summary = run_single(paradigm, pathway, bu_mode, seed=run_seed)
                except Exception as exc:
                    tb = traceback.format_exc()
                    print(f"  EXCEPTION in run {run_index}: {exc}\n{tb}")
                    summary = RunSummary(
                        paradigm=paradigm, pathway=pathway, bu_mode=bu_mode,
                        session_id="", final_round=0, passed=False,
                        errors=[f"exception: {exc}"],
                    )
                all_summaries.append(summary)

    return all_summaries


# ─── Report Generation ────────────────────────────────────────────────────────

def generate_trace_report(summaries: list[RunSummary]) -> str:
    """
    Generate a structured trace report of the traversal.
    Highlights all flagged rounds, collaboration gap trends, and failures.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("  MURESSONS GLOBAL STATE TRAVERSAL -- TRACE REPORT")
    lines.append(f"  Generated: {now_utc()}")
    lines.append("=" * 70)

    total = len(summaries)
    passed = sum(1 for s in summaries if s.passed)
    failed = total - passed
    total_flags = sum(len(s.flagged_rounds) for s in summaries)
    all_gaps = []
    for s in summaries:
        for g in s.gap_history:
            all_gaps.append(g["gap"])
    avg_gap = round(sum(all_gaps) / len(all_gaps), 2) if all_gaps else 0.0
    avg_lat = round(
        sum(s.avg_latency_ms for s in summaries if s.avg_latency_ms > 0)
        / max(1, sum(1 for s in summaries if s.avg_latency_ms > 0)),
        2,
    )

    lines.append(f"\n  SUMMARY")
    lines.append(f"  -------------------------------------")
    lines.append(f"  Total runs       : {total}")
    lines.append(f"  Passed           : {passed}  ({100*passed//max(total,1)}%)")
    lines.append(f"  Failed           : {failed}")
    lines.append(f"  TV flags (+/-5%) : {total_flags}")
    lines.append(f"  Avg collab gap   : {avg_gap:+.2f}")
    lines.append(f"  Avg latency (ms) : {avg_lat:.1f}")

    # ── Per-paradigm breakdown ────────────────────────────────
    lines.append(f"\n  PARADIGM BREAKDOWN")
    lines.append(f"  -------------------------------------")
    for paradigm in ALL_PARADIGMS:
        p_runs = [s for s in summaries if s.paradigm == paradigm]
        if not p_runs:
            continue
        p_pass = sum(1 for s in p_runs if s.passed)
        p_flags = sum(len(s.flagged_rounds) for s in p_runs)
        p_gaps = [g["gap"] for s in p_runs for g in s.gap_history]
        p_avg_gap = round(sum(p_gaps) / len(p_gaps), 2) if p_gaps else 0.0
        lines.append(
            f"  {paradigm:<20} pass={p_pass}/{len(p_runs)}  "
            f"flags={p_flags}  avg_gap={p_avg_gap:+.2f}"
        )

    # ── Per-pathway breakdown ─────────────────────────────────
    lines.append(f"\n  PATHWAY BREAKDOWN")
    lines.append(f"  -------------------------------------")
    for pathway in ALL_PATHWAY_IDS:
        p_runs = [s for s in summaries if s.pathway == pathway]
        if not p_runs:
            continue
        p_pass = sum(1 for s in p_runs if s.passed)
        p_flags = sum(len(s.flagged_rounds) for s in p_runs)
        lines.append(
            f"  {pathway:<25} pass={p_pass}/{len(p_runs)}  flags={p_flags}"
        )

    # ── BU mode breakdown ─────────────────────────────────────
    lines.append(f"\n  BU MODE BREAKDOWN")
    lines.append(f"  -------------------------------------")
    for bu_mode in ["4bu"] + ALL_BU_IDS:
        b_runs = [s for s in summaries if s.bu_mode == bu_mode]
        if not b_runs:
            continue
        b_pass = sum(1 for s in b_runs if s.passed)
        b_flags = sum(len(s.flagged_rounds) for s in b_runs)
        lines.append(
            f"  {bu_mode:<15} pass={b_pass}/{len(b_runs)}  flags={b_flags}"
        )

    # ── Flagged rounds detail with call traces ────────────────
    flagged_summaries = [s for s in summaries if s.flagged_rounds]
    if flagged_summaries:
        lines.append(f"\n  TERMINAL VALUE DEVIATION FLAGS  (threshold +/-{int(TERMINAL_VALUE_DEVIATION_THRESHOLD*100)}%)")
        lines.append(f"  -------------------------------------")
        for s in flagged_summaries:
            lines.append(
                f"  [{s.paradigm} / {s.pathway} / {s.bu_mode}]  "
                f"session={s.session_id[:12]}...  "
                f"flagged_rounds={s.flagged_rounds}"
            )
            # Emit per-round call trace for each flagged round
            for rn in s.flagged_rounds:
                trace_lines = s.call_traces.get(rn, [])
                if trace_lines:
                    lines.append(f"    +-- R{rn} call trace:")
                    for tl in trace_lines:
                        lines.append(f"        {tl}")

    # ── Failures ──────────────────────────────────────────────
    failed_runs = [s for s in summaries if not s.passed]
    if failed_runs:
        lines.append(f"\n  FAILURES")
        lines.append(f"  -------------------------------------")
        for s in failed_runs:
            lines.append(
                f"  [{s.paradigm} / {s.pathway} / {s.bu_mode}]  "
                f"rounds={s.total_rounds_run}  errors={s.errors}"
            )

    # ── Collaboration Gap extremes ────────────────────────────
    if all_gaps:
        sorted_sums = sorted(summaries, key=lambda s: s.peak_gap or 0, reverse=True)
        top_n = sorted_sums[:5]
        lines.append(f"\n  TOP 5 WIDEST COLLABORATION GAPS (peak |gap|)")
        lines.append(f"  -------------------------------------")
        for s in top_n:
            if s.peak_gap is not None:
                lines.append(
                    f"  {s.paradigm:<20} {s.pathway:<25} {s.bu_mode:<15}  "
                    f"peak_gap={s.peak_gap:+.2f}"
                )

    lines.append(f"\n{'='*70}")
    return "\n".join(lines)


def save_report(report: str, summaries: list[RunSummary], output_dir: str = ".") -> None:
    """Save the trace report and JSON summary to disk."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    report_path = os.path.join(output_dir, f"traversal_report_{ts}.txt")
    json_path   = os.path.join(output_dir, f"traversal_summaries_{ts}.json")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n  Report saved -> {report_path}")

    # Serialise summaries to JSON (dataclass -> dict)
    data = [asdict(s) for s in summaries]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  JSON data  -> {json_path}")


# ─── Entrypoint ───────────────────────────────────────────────────────────────

def main():
    """
    Default entrypoint: full Global State Traversal across all paradigms,
    pathways, and BU modes.

    To run a focused subset, call run_traversal() directly with filters:
        run_traversal(paradigms=["legacy_abc"], pathways=["activist_ultimatum"])
    """
    # Reconfigure stdout/stderr to UTF-8 so call-trace box characters render
    # correctly on Windows consoles that default to cp1252.
    import io
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    import argparse

    parser = argparse.ArgumentParser(
        description="Muressons Global State Traversal & Validation Harness"
    )
    parser.add_argument(
        "--paradigms", nargs="*", default=None,
        help=f"Paradigm(s) to test. Choices: {ALL_PARADIGMS}"
    )
    parser.add_argument(
        "--pathways", nargs="*", default=None,
        help=f"Ending pathway(s) to test. Choices: {ALL_PATHWAY_IDS}"
    )
    parser.add_argument(
        "--bu-modes", nargs="*", default=None,
        help="BU modes: '4bu' or BU IDs (pharma electronics consumer_goods software)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output-dir", default=".",
        help="Directory for report output files (default: current dir)"
    )
    args = parser.parse_args()

    summaries = run_traversal(
        paradigms=args.paradigms,
        pathways=args.pathways,
        bu_modes=args.bu_modes,
        seed=args.seed,
    )

    report = generate_trace_report(summaries)
    print("\n" + report)
    save_report(report, summaries, output_dir=args.output_dir)

    # Exit code: 0 if all passed, 1 otherwise
    all_passed = all(s.passed for s in summaries)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
