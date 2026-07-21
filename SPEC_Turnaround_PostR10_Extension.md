# Implementation Spec — Post-R10 Turnaround Arc (Optional Extension)

**Feature:** Deliberate, opt-in 4-round crisis-recovery arc offered after Round 10 when the terminal Regenerative Multiple falls below 0.80.
**Status:** Design spec — not yet implemented.
**Author basis:** Reconstructed from `engine.py` (Feature 25), `config.py`, `simulation_config.json`, `router.py`, `round_logic.py`, `terminal_valuation.py`, and `branching_engine.py` (Extended Horizon precedent).

---

## 1. Summary & goals

The turnaround ladder (`crisis → stabilisation → recovery → exit`) already exists in `engine.py` but runs **automatically and invisibly** mid-simulation whenever a team hits treasury ≤ $0 and reputation < 30. This spec repurposes the same phase machinery into a **deliberate, facilitator-gated extension that begins after Round 10**, giving a "Stranded Relic" team a bounded, four-round shot at a comeback.

Design decisions locked in:

- **Fixed 4-round arc** (T1–T4). Exactly four decision rounds, one gate check per round.
- **Offered, not forced.** Eligibility surfaces only when terminal **M_R < 0.80** and the extension is enabled; entry requires an explicit opt-in call.
- **Reuses the existing phase gates and caps verbatim** — only the *entry* changes from reactive to deliberate.
- **Backward compatible.** Default-off; the existing auto-trigger mid-sim behaviour is untouched.

### Non-goals

- No change to the mid-sim auto-trigger arc (it stays as-is).
- No new terminal-valuation formula — we re-run the existing one with the clamp lifted on graduation.
- No new player-facing *panel* (per `CLAUDE.md` V-D slotting rule — see §7).

---

## 2. Stage parameters (reference — unchanged from source)

Pulled from `_TURNAROUND_PHASES` (engine.py) / `turnaround_pathway` in `simulation_config.json`. The extension reuses these exactly.

| Stage | Advance gate (to next stage) | CapEx cap | M_R cap | Cash event |
|---|---|---|---|---|
| **Crisis** | treasury > $0 **and** rep > 20 | 0.0 (frozen) | 0.60 | +$3M emergency credit (on entry) |
| **Stabilisation** | treasury > $10M **and** rep > 45 | 0.50 | 0.80 | dividends suspended |
| **Recovery** | treasury > $20M **and** rep > 55 | 1.0 (full) | 1.20 | credit rating +1 notch |
| **Exit** (graduation) | — | uncapped | +0.10 bonus | investment-grade restored |

To graduate you must clear **3 gates**, so the minimum path is 3 rounds; the 4th round is a buffer. Failing to reach Exit by end of T4 ends the arc with M_R clamped at the last phase's `mr_cap`.

---

## 3. Configuration

### 3.1 New config block (`simulation_config.json`)

Extend the existing `turnaround_pathway` object with an `arc` sub-block (numeric only — matches the `config.py` "numeric parameters only" convention):

```json
"turnaround_pathway": {
  "...existing crisis/stabilisation/recovery/exit blocks...": {},
  "arc": {
    "max_rounds": 4,
    "eligibility_mr_threshold": 0.80,
    "entry_bailout": 3000000
  }
}
```

### 3.2 New constants (`config.py`, LAYER 2 — Turnaround Pathway, ~line 566)

```python
_ta_arc = _ta.get("arc", {})
TURNAROUND_ARC_MAX_ROUNDS: int   = int(_ta_arc.get("max_rounds", 4))
TURNAROUND_ARC_MR_THRESHOLD: float = float(_ta_arc.get("eligibility_mr_threshold", 0.80))
TURNAROUND_ARC_ENTRY_BAILOUT: float = float(_ta_arc.get("entry_bailout", 3_000_000))
```

### 3.3 God-Mode toggle (`admin_god_controls.py`)

- Add `"turnaround_extension_enabled": False` to the `_god_mode_settings` defaults.
- Add the key to the writable tuple in `PUT /god/settings` (currently only `allow_facilitator_cohort_creation`):
  ```python
  for key in ("allow_facilitator_cohort_creation", "turnaround_extension_enabled"):
  ```
- Call `mark_godmode_dirty()` on change (already in that handler).

---

## 4. State model

New keys, all under `global_state` (persisted via `db.update_latest_global_state`):

| Key | Type | Meaning |
|---|---|---|
| `gs["turnaround_enabled"]` | bool | Per-session copy of the God-Mode toggle, set at session start |
| `gs["turnaround_mode"]` | bool | True while the post-R10 arc is active |
| `gs["turnaround_round"]` | int | 1–4 (T1–T4); 0 when inactive |
| `flags["turnaround_phase"]` | str | `crisis` / `stabilisation` / `recovery` / `exit` (reuses existing flag) |
| `flags["turnaround_graduated"]` | bool | True once Exit reached |
| `flags["turnaround_final_mr_cap"]` | float | The clamp applied if the arc ends without graduation |

`flags` = `gs["active_event_flags"]`.

---

## 5. Backend changes

### 5.1 Split entry from progression in `detect_distress` (`engine.py:1292`)

Add a `deliberate_entry` parameter (default `False`, so every existing caller and test is unaffected):

```python
def detect_distress(treasury, group_reputation, round_number,
                    already_in_survival=False, current_phase="none",
                    deliberate_entry=False):
    # Deliberate post-R10 entry: drop straight into Crisis, bypass the
    # ≤$0 / <30 auto-condition and the R2 grace guard.
    if deliberate_entry and current_phase == "none":
        crisis = _TURNAROUND_PHASES["crisis"]
        return {
            "distress_detected": True, "survival_mode": True,
            "turnaround_phase": "crisis", "phase_transition": True,
            "bailout_amount": crisis["bailout"],
            "capex_cap_multiplier": crisis["capex_cap"], "mr_cap": crisis["mr_cap"],
            "archetype_override": "turnaround_manager",
            "message": crisis["narrative_enter"],
        }

    if round_number < 2 and not deliberate_entry:
        return {"distress_detected": False, "survival_mode": already_in_survival,
                "turnaround_phase": current_phase}
    # ... existing crisis→stabilisation→recovery→exit progression UNCHANGED ...
```

The three climb branches are reused with no edits — they already read `current_phase` and the live treasury/rep.

### 5.2 Enforce the caps (the pre-existing gap)

Today `detect_distress` returns `capex_cap_multiplier` and `mr_cap` but round_logic only consumes an `impacts`-sourced `mr_cap` (round_logic.py:2454) and a hard-coded `capex_cap_multiplier` (round_logic.py:960). In the turnaround commit path (§5.4), wire the distress dict through:

```python
if distress.get("capex_cap_multiplier") is not None:
    events["capex_cap_multiplier"] = distress["capex_cap_multiplier"]
if distress.get("mr_cap") is not None:
    extra["mr_cap"] = distress["mr_cap"]          # feeds mr = min(mr, extra["mr_cap"])
```

This makes the phase caps real for the extension (and is safe for the mid-sim arc too, but scope it to `turnaround_mode` if you want to avoid touching live-sim behaviour in this commit).

### 5.3 Eligibility offer on the final report (`router.py`, `get_final_report` @1251)

After the game is finished, attach an offer when eligible:

```python
mr = gs.get("regenerative_multiple", 1.0)
offer = None
if (gs.get("turnaround_enabled") and gs.get("game_over")
        and not gs.get("turnaround_mode") and not flags.get("turnaround_graduated")
        and mr < TURNAROUND_ARC_MR_THRESHOLD):
    offer = {
        "eligible": True,
        "current_mr": round(mr, 3),
        "threshold": TURNAROUND_ARC_MR_THRESHOLD,
        "max_rounds": TURNAROUND_ARC_MAX_ROUNDS,
        "premium_if_graduated": 0.10,
        "reason": f"Terminal M_R {mr:.2f} < {TURNAROUND_ARC_MR_THRESHOLD:.2f} — a comeback is available.",
    }
# add to the returned dict:
"turnaround_offer": offer,
```

### 5.4 New endpoints (mirror `activate_extended_mode` @5688)

**A. Enter the arc** — `POST /{session_id}/turnaround/enter`

```python
@router.post("/{session_id}/turnaround/enter",
             summary="Enter the post-R10 Turnaround Arc (4 rounds)")
async def enter_turnaround(session_id: str):
    latest = await db.fetch_latest_state(session_id)
    if not latest: raise HTTPException(404, "Session not found")
    gs, bus = latest["global_state"], latest["bu_states"]
    flags = gs.setdefault("active_event_flags", {})

    if not gs.get("turnaround_enabled"):
        raise HTTPException(403, "Turnaround extension not enabled for this session")
    if gs.get("regenerative_multiple", 1.0) >= TURNAROUND_ARC_MR_THRESHOLD:
        raise HTTPException(409, "Not eligible — terminal M_R ≥ 0.80")
    if gs.get("turnaround_mode"):
        raise HTTPException(409, "Turnaround already active")

    # Deliberate entry → Crisis
    distress = detect_distress(gs.get("corporate_treasury", 0),
                               gs.get("group_reputation", 0),
                               round_number=99, current_phase="none",
                               deliberate_entry=True)
    gs["turnaround_mode"] = True
    gs["turnaround_round"] = 1
    gs["game_over"] = False
    gs["game_over_reason"] = None
    flags["turnaround_phase"] = "crisis"
    gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0)
                                     + distress["bailout_amount"], 2)
    await db.update_latest_global_state(session_id, gs, bus)
    return {
        "ok": True, "turnaround_round": 1, "phase": "crisis",
        "bailout_applied": distress["bailout_amount"],
        "config": get_turnaround_round_config(1),
        "message": distress["message"],
    }
```

**B. Commit a turnaround round** — `POST /{session_id}/turnaround/commit`

Runs one T-round: apply the player's recovery decision through `process_tick` **with the active phase's caps**, then run `detect_distress` progression, advance `turnaround_round`, and terminate at T4 or on graduation.

```python
@router.post("/{session_id}/turnaround/commit")
async def commit_turnaround(session_id: str, body: TurnaroundCommitRequest):
    latest = await db.fetch_latest_state(session_id)
    gs, bus = latest["global_state"], latest["bu_states"]
    flags = gs["active_event_flags"]
    if not gs.get("turnaround_mode"):
        raise HTTPException(409, "Not in turnaround mode")

    t_round = gs["turnaround_round"]
    phase   = flags["turnaround_phase"]

    # 1. Resolve decision via the normal engine, but pass the phase caps.
    #    (Reuse the existing commit/process_tick path; §5.2 wires caps in.)
    result = run_turnaround_tick(gs, bus, phase, body.choice)  # thin wrapper

    # 2. Progression check against updated treasury/rep.
    distress = detect_distress(gs["corporate_treasury"], gs["group_reputation"],
                               round_number=99, already_in_survival=True,
                               current_phase=phase)
    flags["turnaround_phase"] = distress["turnaround_phase"]

    graduated = distress.get("turnaround_phase") == "exit"
    last_round = t_round >= TURNAROUND_ARC_MAX_ROUNDS

    if graduated:
        flags["turnaround_graduated"] = True
        _finalize_turnaround(gs, bus, graduated=True)     # §5.5
    elif last_round:
        flags["turnaround_final_mr_cap"] = _phase_mr_cap(distress["turnaround_phase"])
        _finalize_turnaround(gs, bus, graduated=False)    # §5.5
    else:
        gs["turnaround_round"] = t_round + 1

    await db.update_latest_global_state(session_id, gs, bus)
    return {
        "ok": True, "turnaround_round": gs["turnaround_round"],
        "phase": flags["turnaround_phase"],
        "graduated": graduated,
        "arc_complete": graduated or last_round,
        "config": None if (graduated or last_round)
                  else get_turnaround_round_config(gs["turnaround_round"]),
        "message": distress.get("message"),
    }
```

`TurnaroundCommitRequest` = `{ "choice": "option_a" | "option_b" | "option_c" }` (add to `models.py`).

### 5.5 Finalisation & re-valuation (`_finalize_turnaround`)

```python
def _finalize_turnaround(gs, bus, graduated):
    from terminal_valuation import compute_terminal_valuation  # existing entry
    flags = gs["active_event_flags"]
    if graduated:
        flags.pop("turnaround_final_mr_cap", None)           # clamp lifted
        gs["_turnaround_mr_bonus"] = TURNAROUND_EXIT_MR_BONUS # +0.10
    # Re-run the existing terminal valuation; it reads mr_cap / bonus from flags.
    val = compute_terminal_valuation(gs, bus)
    gs["terminal_valuation"] = val["terminal_valuation"]
    gs["regenerative_multiple"] = val["regenerative_multiple"]
    gs["archetype"] = val["archetype"]      # graduated & M_R↑ may exit turnaround_manager
    gs["turnaround_mode"] = False
    gs["game_over"] = True
    gs["game_over_reason"] = "turnaround_complete" if graduated else "turnaround_expired"
```

Note: `terminal_valuation.py` (~line 548) currently forces `turnaround_manager` whenever survival mode is set and caps M_R at 0.80. On **graduation**, clear `survival_mode` before re-valuation so the archetype can legitimately climb above Turnaround Manager (that's the reward). On **expiry**, keep the clamp.

### 5.6 Round content (`branching_engine.py` — mirror `EXTENDED_ROUNDS`)

Add a fixed 4-entry config and accessor, parallel to `EXTENDED_ROUNDS` / `get_extended_round_config`:

```python
TURNAROUND_ROUNDS = {
  1: {"title": "T1 — Triage", "phase_hint": "crisis",
      "crisis": "Creditors demand an immediate survival plan. Every dollar counts.",
      "options": {  # A/B/C recovery levers
        "option_a": {"title": "Deep Cost Freeze", ...},
        "option_b": {"title": "Asset-Light Restructure", ...},
        "option_c": {"title": "Bet on a Growth Lever", ...}}},
  2: {"title": "T2 — Stabilise", ...},
  3: {"title": "T3 — Rebuild", ...},
  4: {"title": "T4 — Prove the Comeback", ...},
}
def get_turnaround_round_config(n): return TURNAROUND_ROUNDS.get(n)
```

Option `impacts` should move treasury/reputation so that clearing the phase gates is achievable but not trivial — calibrate against the gate table in §2 (e.g. T1 options must be able to lift treasury above $0 and rep above 20 from the distressed floor).

---

## 6. Arc semantics (fixed 4-round)

```
[R10 terminal valuation]
        │  M_R < 0.80  and  turnaround_enabled
        ▼
  turnaround_offer  ──(player declines)──▶ game stays over (Stranded Relic, M_R as-is)
        │ (opt-in: POST /turnaround/enter)
        ▼
  ┌──────────── Crisis (entry, +$3M, CapEx frozen, M_R≤0.60) ───────────┐
  │  T1 commit → gate? treasury>0 & rep>20  → Stabilisation             │
  │  T2 commit → gate? treasury>$10M & rep>45 → Recovery                │
  │  T3 commit → gate? treasury>$20M & rep>55 → Exit (graduate)         │
  │  T4 commit → last chance to clear the pending gate                  │
  └────────────────────────────────────────────────────────────────────┘
        │ reached Exit                     │ T4 done, not graduated
        ▼                                  ▼
  Re-value, clamp lifted, +0.10     Re-value, M_R clamped at last phase cap
  → archetype may rise              → stays Turnaround Manager / capped
```

Minimum to graduate = 3 clean gate clears (T1–T3). T4 is a buffer for one stalled round.

---

## 7. Frontend surface (CLAUDE.md V-D compliant)

**Do not add a standing panel** (the slotting rule calls that a review defect). Use two existing slots, and name each in the component header comment:

- **KPI belt** — a compact, glanceable phase chip: `Crisis › Stabilisation › Recovery › Exit` with the current stage lit and the next gate shown (`Need: Treasury > $0 · Rep > 20`). Numbers/status only. Rendered only when `gs.turnaround_mode`.
- **OverlayHost** — the entry ("🚨 Turnaround Manager Appointed"), each phase transition, and the final "✅ Comeback / ⏳ Expired" are interrupts. They're already emitted into `custom_black_swans`; route them through OverlayHost.
- The comeback **recap** (before/after M_R, premium earned) renders in the **results stage**, not mid-arc (V-A precedent).

Tokens: use `app/styles/tokens.css` (`--danger`, `--success`, `--caution`) — no raw hex. Note `EngineEventsPanel.js:550` currently hard-codes `rgba(239,68,68,…)`; the new chip must not repeat that.

---

## 8. API contract summary

| Endpoint | Request | Key response fields |
|---|---|---|
| `GET /{id}/final-report` | — | `turnaround_offer: {eligible, current_mr, threshold, max_rounds, premium_if_graduated}` |
| `POST /{id}/turnaround/enter` | — | `turnaround_round:1, phase:"crisis", bailout_applied, config` |
| `POST /{id}/turnaround/commit` | `{choice}` | `turnaround_round, phase, graduated, arc_complete, config` |

---

## 9. Tests

Backend (extend `tests/test_new_features.py` / `test_simulation_integrity_extended.py`):

1. **Gate off** — `turnaround_enabled=False` → `final-report` returns `turnaround_offer=None`; `/enter` → 403.
2. **Eligibility boundary** — M_R = 0.79 eligible; 0.80 not (`409`).
3. **Deliberate entry** — `detect_distress(deliberate_entry=True, current_phase="none")` returns `crisis` regardless of treasury/rep, and applies the $3M bailout.
4. **Happy path graduation** — scripted T1–T3 clears all gates → `graduated=True`, clamp lifted, `+0.10` applied, archetype rises above Turnaround Manager.
5. **Expiry** — 4 rounds without clearing → `arc_complete=True, graduated=False`, M_R clamped at last phase cap, archetype stays Turnaround Manager.
6. **Cap enforcement** — while in Stabilisation, terminal M_R cannot exceed 0.80 (regression on the §5.2 gap).
7. **Backward-compat** — existing `detect_distress` unit tests still pass unchanged (default `deliberate_entry=False`).

---

## 10. Rollout & conventions

- **Commit 1 (backend, headless):** config + constants + God-Mode toggle + `detect_distress` split + cap enforcement + tests 1–3, 7. No UI, low risk.
- **Commit 2 (backend):** endpoints + `TURNAROUND_ROUNDS` content + `_finalize_turnaround` + tests 4–6.
- **Commit 3 (frontend):** KPI-belt chip + OverlayHost routing + results-stage recap, per §7.

Per `CLAUDE.md`: if the God-Mode toggle appears in any sidebar tab, update the tab tooltip in the same commit (tooltip must describe what it renders). No `ROLE_HIERARCHY` / RBAC changes are needed — the endpoints run on live-run management, so gate them on `require_sim_manager`, not `require_facilitator`.

*Sources: engine.py (`_TURNAROUND_PHASES`, `detect_distress`, Feature-25 tick), config.py:566–594, simulation_config.json (`turnaround_pathway`), router.py (`get_final_report`:1251, `activate_extended_mode`:5688, R10 valuation), round_logic.py:960/2454, terminal_valuation.py:541–557, branching_engine.py (`EXTENDED_ROUNDS`), admin_god_controls.py.*
