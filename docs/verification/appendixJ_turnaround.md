# Appendix J — Turnaround and extended play (mechanical extraction)

Repo: muressons-sim. git HEAD confirmed: **0ad1246**
Primary file: `backend/turnaround_engine.py` — **366 lines**.
Rule applied: only facts read directly from code. Gaps marked NOT FOUND / UNCERTAIN.

There are TWO distinct systems that share vocabulary. They must not be conflated:

* **System A — mid-sim distress / turnaround pathway.** `engine.detect_distress`
  (`backend/engine.py:1499`), called once per tick from the main pipeline at
  `backend/engine.py:4311`. Reachable by a normal player cohort.
* **System B — post-completion Turnaround ARC module.** `backend/turnaround_engine.py`,
  a fixed 4-round arc offered AFTER R10. Superadmin feature-flagged, facilitator-driven,
  no player commit endpoint.

Both call the same phase table `_TURNAROUND_PHASES` (`backend/engine.py:1455-1497`),
whose numbers come from `backend/config.py:868-886`.

---

## 1. THE DISTRESS STATE — triggers and thresholds

### 1a. Automatic (mid-sim) entry — System A
Entry test, `backend/engine.py:1602-1605`:

```
crisis = _TURNAROUND_PHASES["crisis"]
is_distressed = treasury <= crisis["entry_treasury"] and \
                group_reputation < crisis["entry_reputation"]
```

Both conditions must hold (AND), and `already_in_survival` must be False
(`backend/engine.py:1607`).

| Parameter | Value | Constant | Definition | Live JSON |
|---|---|---|---|---|
| entry_treasury | `0` | `TURNAROUND_CRISIS_ENTRY_TREASURY` | `backend/config.py:868` | `turnaround_pathway.crisis.entry_treasury = 0` |
| entry_reputation | `30` | `TURNAROUND_CRISIS_ENTRY_REP` | `backend/config.py:869` | `= 30` |

So: **treasury ≤ $0 AND group_reputation < 30**. Note the asymmetry — treasury is
`<=`, reputation is `<`.

Grace guard: `backend/engine.py:1533-1535` — `if round_number < 2 and not
deliberate_entry: return {"distress_detected": False, ...}`. Distress cannot fire in
round 1.

Wiring into the tick: `backend/engine.py:4309-4315` reads the previous tick's
`active_event_flags.survival_mode` and `.turnaround_phase`, calls `detect_distress`
with `ctx.new_treasury`, `ctx.group_reputation`, `current_global["round_number"]`, and
writes `ctx.events["distress_detection"]` and `ctx.events["turnaround_phase"]`.

On detection (`backend/engine.py:4317-4330`): treasury += bailout
`TURNAROUND_CRISIS_BAILOUT = 3_000_000` (`backend/config.py:870`), sets
`ctx.events["survival_mode"] = True`, `ctx.events["bailout_applied"]`, records a
waterfall line "Emergency Bailout", and appends a `custom_black_swans` entry titled
"🚨 CRISIS — Turnaround Manager Appointed" at severity `critical`.

### 1b. Deliberate entry — System B
`detect_distress(..., deliberate_entry=True, current_phase="none")` short-circuits at
`backend/engine.py:1522-1532`: it returns the crisis dict unconditionally, "bypassing
the auto-trigger condition and the R2 grace guard". Called only from
`turnaround_engine.enter_arc` (`backend/turnaround_engine.py:123-127`), which passes
`round_number=99`.

### 1c. Triggers that DO NOT exist
* **Covenant breach** — `check_covenants` exists at `backend/balance_sheet.py:398`, but
  it is never referenced by `detect_distress` and does not set distress. NOT a trigger.
* **Liquidity ratio** — `CONSTRAINT_MIN_LIQUIDITY_RATIO = 0.2`
  (`backend/config.py:189`) is consumed only at `backend/balance_sheet.py:924-929` as a
  warning string. NOT a distress trigger.
* **Reputation-only / social-licence floor** — no social-licence term appears anywhere
  in `detect_distress` (`backend/engine.py:1499-1620`). NOT FOUND.
* No other caller of `detect_distress` exists outside `engine.py:4311`,
  `turnaround_engine.py:123` and `:178`, and tests.

### 1d. What distress actually costs (real, player-path consumers)
* **CapEx cap** — `backend/engine.py:3064-3072`: if the previous tick's flags carry
  `survival_mode` and `distress_detection.capex_cap_multiplier`, `_cap_mult` is
  `min()`-ed with it. Crisis multiplier `0.0` (`config.py:871`), stabilisation `0.50`
  (`config.py:876`), recovery `1.0` (`config.py:881`).
* **Dividend suspension** — `backend/engine.py:2961-2967`: dividends forced to 0.0 when
  the previous flags carry `survival_mode` AND `turnaround_phase in ("crisis",
  "stabilisation")`.
* **Goodwill impairment** — `backend/balance_sheet.py:706-708`: `survival` is one of the
  three IAS-36 impairment triggers, tested every 2 rounds.
* Flags persist because `backend/router.py:3324` does `merged_flags.update(events)`.

### 1e. What distress does NOT cost — the mid-sim `mr_cap` is inert
`detect_distress` returns `mr_cap` in every branch (`engine.py:1528, 1546, 1554, 1566,
1574, 1594, 1615`). No non-test code reads it. The only `mr_cap` consumed in scoring is
`extra["mr_cap"]` at `backend/round_logic.py:3100-3106`, and that key is set at exactly
one place — `backend/round_logic.py:2887-2888`, inside the `ending_pathway ==
"hostile_takeover"` branch (Option C, "Accept bid"). The distress `mr_cap` never
reaches it. **The mid-sim distress state does not cap M_R.**

---

## 2. THE RECOVERY ARC — VERDICT: the note is CONFIRMED, with a naming caveat

There are **four named phases**, and separately a **four-round arc**. Both are 4; they
are different fours.

Phase table `_TURNAROUND_PHASES`, `backend/engine.py:1455-1497`.

| # | Phase key | Advance requires (AND) | Grants | Defined |
|---|---|---|---|---|
| 1 | `crisis` | entry: treasury ≤ 0 AND rep < 30 | +$3,000,000 bailout; capex_cap 0.0 (frozen); mr_cap 0.60; `archetype_override: "turnaround_manager"` | `engine.py:1456-1466`; thresholds `config.py:868-872` |
| 2 | `stabilisation` | treasury > `0` AND rep > `20` | capex_cap 0.50; mr_cap 0.80; no bailout | `engine.py:1467-1476`; gate `engine.py:1540-1549`; thresholds `config.py:874-877` |
| 3 | `recovery` | treasury > `10,000,000` AND rep > `45` | capex_cap 1.0 (full); mr_cap 1.20 | `engine.py:1477-1486`; gate `engine.py:1559-1568`; thresholds `config.py:879-882` |
| 4 | `exit` | treasury > `20,000,000` AND rep > `55` | `survival_mode: False`, `recovered: True`, `mr_bonus: 0.10`; all caps lifted | `engine.py:1487-1496`; gate `engine.py:1579-1588`; thresholds `config.py:884-886` |

Progression is strictly one step per call: crisis→stabilisation (`engine.py:1538`),
stabilisation→recovery (`engine.py:1558`), recovery→exit (`engine.py:1578`),
exit is terminal (`engine.py:1597-1599`). No skipping, no regression — there is **no
demotion branch**: once a phase is reached, failing its gate returns the same phase with
a holding message (`engine.py:1549-1557`, `1568-1576`, `1588-1596`).

The module docstring calls it a "3-Act Turnaround Arc" (`backend/engine.py:1506`) while
implementing four phases. The docstring at `engine.py:1512-1517` restates all four.

### 2b. The arc's four ROUNDS (System B content)
`TURNAROUND_ROUNDS`, `backend/turnaround_engine.py:46-95`. Each round offers three
levers (A disciplined / B balanced / C aggressive), all of which INCREASE treasury:

| Round | Title | phase_hint | A (treasury/rep) | B | C | Lines |
|---|---|---|---|---|---|---|
| 1 | T1 — Triage | crisis | +6,000,000 / +10 | +9,000,000 / +6 | +14,000,000 / −4 | `:47-58` |
| 2 | T2 — Stabilise | stabilisation | +8,000,000 / +20 | +11,000,000 / +16 | +16,000,000 / +8 | `:59-70` |
| 3 | T3 — Rebuild | recovery | +10,000,000 / +14 | +14,000,000 / +11 | +20,000,000 / +7 | `:71-82` |
| 4 | T4 — Prove the Comeback | recovery | +10,000,000 / +14 | +14,000,000 / +11 | +20,000,000 / +7 | `:83-94` |

Rounds 3 and 4 are numerically identical. The source flags its own deltas as
"PLACEHOLDER calibration" (`backend/turnaround_engine.py:41-43`).

Arc length: `TURNAROUND_ARC_MAX_ROUNDS = 4` (`backend/config.py:892`; live JSON
`turnaround_pathway.arc.max_rounds = 4`).

`apply_commit` (`:148-211`): applies the lever's treasury delta (`:164-165`), accrues
positive injections into `gs["turnaround_rescue_financing"]` (`:172-174`), clamps
reputation to `[0.0, 100.0]` (`:175-176`), then calls `detect_distress(...,
round_number=99, already_in_survival=True, current_phase=phase)` (`:178-181`).
Graduation = `new_phase == "exit"` (`:184`). Running out = `t_round >=
TURNAROUND_ARC_MAX_ROUNDS` (`:185`).

---

## 3. THE M_R 0.80 CAP — VERDICT: the note is REFUTED as stated; a 0.80 cap does exist, but not where the note places it

The note says "a Regenerative Multiple cap of 0.80 applies in the distress/turnaround
state". What the code contains is **three separate 0.80s**. Only one is a cap, and it is
unreachable from the player path.

### 3a. The real 0.80 cap — `backend/terminal_valuation.py:610-618`
```python
def determine_archetype(mr, thresholds=None, custom_archetypes=None, survival_mode=False):
    t = thresholds or _THRESHOLDS
    a = custom_archetypes or _ARCHETYPES
    # Survival mode: M_R capped at 0.80, always maps to turnaround_manager
    if survival_mode:
        mr = min(mr, 0.80)
        return {"key": "turnaround_manager", **a.get("turnaround_manager", _ARCHETYPES["turnaround_manager"]),
                "mr_capped": True, "original_mr": mr}
    if mr >= t.get("regenerative_titan", 1.8): key = "regenerative_titan"
    elif mr >= t.get("derisked_safe_haven", 1.2): key = "derisked_safe_haven"
    elif mr >= t.get("fragile_giant", 0.8): key = "fragile_giant"
    else: key = "stranded_relic"
    return {"key": key, **a.get(key, _ARCHETYPES["stranded_relic"])}
```
* It is a **CAP** (`min`), value **0.80**, **hardcoded** — not config-routed, not in
  `simulation_config.json`.
* Condition: the caller passes `survival_mode=True`.
* Callers passing `survival_mode=True` (whole repo): `backend/turnaround_engine.py:276`
  and `backend/tests/test_new_features.py:156`. **That is all.**
* The player-path terminal scorer calls it WITHOUT the kwarg —
  `backend/round_logic.py:518-519`: `from terminal_valuation import determine_archetype
  as _determine_archetype` / `_arch = _determine_archetype(mr)`. So `survival_mode`
  defaults to False and the 0.80 cap never fires for a normal run, even one that spent
  rounds in crisis.
* Scope: the cap mutates a **local** `mr` only. The function returns
  `{"key", "title", "icon", "gradient", "mr_capped": True, "original_mr": <capped mr>}`.
  It returns no `mr` field, so it cannot lower the caller's M_R. In
  `turnaround_engine._finalize` the M_R actually used for re-valuation is `mr_final`,
  computed at `:238-252` *before* the call at `:276`, so the 0.80 has no effect on
  `terminal_value`, `equity_value` or `price_per_share` there either. Its only effect is
  forcing `key = "turnaround_manager"`. Note also that `"original_mr"` is assigned the
  already-capped value, so the pre-cap M_R is not reported.
* Can it be lifted? Only by passing `survival_mode=False`. `turnaround_engine._finalize`
  does exactly that on graduation: `survival = False` (`:241`) vs `survival = True`
  (`:249`).

### 3b. The arc's own M_R clamp — NOT 0.80 by default
`_PHASE_MR_CAP` (`backend/turnaround_engine.py:98-103`) maps crisis→
`TURNAROUND_CRISIS_MR_CAP` (**0.60**), stabilisation→`TURNAROUND_STAB_MR_CAP`
(**0.80**), recovery→`TURNAROUND_RECOVERY_MR_CAP` (**1.20**), exit→`None`.

Applied in `_finalize`, `backend/turnaround_engine.py:238-252`:
* graduated: `mr_final = round(base_mr + TURNAROUND_EXIT_MR_BONUS, 3)` — **+0.10**
  (`config.py:886`), `survival = False`, `status = "graduated"`. Clamp lifted.
* expired: `cap = flags.get("turnaround_final_mr_cap")`; `cap =
  TURNAROUND_CRISIS_MR_CAP if cap is None else float(cap)`; `mr_final = round(min(base_mr,
  cap), 3)`, `survival = True`, `status = "expired"`. Default fallback is **0.60**, not
  0.80. 0.80 applies only if the team ended the arc sitting in `stabilisation`
  (`turnaround_engine.py:204`).

### 3c. `fragile_giant` 0.8 — a DIFFERENT mechanic, same number
`backend/round_configs.py:712-716`, round 10 `special_rules.profile_thresholds`:
`{"regenerative_titan": 1.8, "derisked_safe_haven": 1.2, "fragile_giant": 0.8}`.
Consumed at `backend/round_logic.py:3245-3252` as a `>=` **lower bound** for a label —
"M_R ≥ 0.8 is called a Fragile Giant". It changes no number. The same triple is the
in-code default `_THRESHOLDS` at `backend/terminal_valuation.py:586`.

**These are two different mechanics.** 3a is `min(mr, 0.80)` — a ceiling on a value.
3c is `mr >= 0.8` — a floor on a naming bucket. They coincide numerically and both live
inside `determine_archetype`, but neither derives from the other, and 3c is not routed
through `simulation_config.json` at all.

### 3d. Fourth 0.80 — the arc ELIGIBILITY threshold
`TURNAROUND_ARC_MR_THRESHOLD = 0.80` (`backend/config.py:893`; live JSON
`turnaround_pathway.arc.eligibility_mr_threshold = 0.8`). Used by
`engine.turnaround_score_eligible` (`backend/engine.py:1628-1634`): `return float(mr) <
TURNAROUND_ARC_MR_THRESHOLD`. This is an **entry gate**, not a cap: a completed run
qualifies for the arc only if its canonical M_R is strictly below 0.80. Note the
consequence — it is the same boundary as `fragile_giant`, so exactly the runs that
scored `stranded_relic` are the ones offered the arc.

---

## 4. EXTENDED PLAY — a mode past round 10 existed and was REMOVED

`backend/branching_engine.py:279-286`:
```
#  EXTENDED HORIZON MODE (SI-3)
# Extended Horizon (rounds 11-20) content lived here until F-32 (launch audit
# 2026-09-01) retired the feature: it could never be played (commit cap, DB
# CHECK constraint, cockpit game-over logic). The recovery-round content in
# turnaround_engine.py is the surviving sibling.
```
Corroborated at `backend/router.py:2586-2588`: "(Extended Horizon, which used to clear
game_over here, was removed — F-32.)"

`EXTENDED_ROUNDS` has no remaining definition anywhere in the backend; the only
occurrence is the comment reference at `backend/turnaround_engine.py:38`.

Hard stops on rounds > 10, all present at HEAD:
* `backend/router.py:2567-2573` — `current_round = current["round_number"]`; `if
  current_round > 10: raise 409 "Simulation has already completed all 10 rounds."`
* `backend/database.py:149` and `backend/database.py:183` — `round_number SMALLINT NOT
  NULL CHECK (round_number BETWEEN 1 AND 10)` on two tables.
* `backend/router.py:2589-2597` — `if global_state.game_over: raise 409`.

### 4a. Can `SIM_ROUNDS` change at runtime?
`backend/config.py:180`: `SIM_ROUNDS: int = int(_sim_settings.get("rounds", 10))`,
read from `SIMULATION_CONFIG["simulation_settings"]["rounds"]`. Live value in both
`simulation_config.json` and `db/simulation_config.json` is `10`.

**Yes, partially — one superadmin route rebinds it.** `upload_simulation_config`
(`backend/admin_router.py:9058`, guarded `Depends(require_super_admin)`,
`admin_router.py:9059-9060`) writes a new `simulation_config.json`
(`admin_router.py:9123`) and then runs a hot-reload chain,
`backend/admin_router.py:9226-9239`: `importlib.reload` of `config`, `engine`,
`balance_sheet`, `terminal_valuation`, `black_swan_registry`.

Consequences read from code, not inferred beyond them:
* `config.SIM_ROUNDS` rebinds. Modules reloaded in the chain re-import it.
* Modules that did `from config import SIM_ROUNDS` and are NOT in the chain keep the old
  int: `backend/router.py` (via `round_logic`), `backend/round_logic.py:20`,
  `backend/database.py:18`, `backend/database_memory.py:17`, `backend/admin_router.py:340`.
  `backend/config_introspect.py:22-29` names this exact failure mode
  ("stale_binding … this process running a MIXTURE of old and new values").
* `config.reload_simulation_config()` (`backend/config.py:901-914`) exists but has **no
  non-test caller** anywhere in the backend.
* Even a raised `SIM_ROUNDS` cannot produce round 11: `router.py:2569` hardcodes `> 10`
  and the DB CHECK hardcodes `BETWEEN 1 AND 10`. Neither reads `SIM_ROUNDS`.

### 4b. "free_play" is not extended play
`pacing_mode` values are `free_play | manual | scheduled`
(`backend/admin_router.py:11009-11013`), and the "free-play sentinel 999"
(`admin_router.py:3636-3644`) is a `max_unlocked_round` value. These control which of
rounds 1–10 are unlocked, not how many rounds exist. `admin_router.py:11048` clamps:
`_ceiling = max(1, min(_ceiling, SIM_ROUNDS))`.

**The only thing that runs past R10 at HEAD is the post-completion arc — and it does not
advance `round_number` at all.** `enter_arc` sets `gs["turnaround_round"] = 1`
(`turnaround_engine.py:133`) and never touches `round_number`.

---

## 5. WRITE-BACKS AND CONSUMERS

### 5a. What System B writes into `global_state`
`enter_arc` (`backend/turnaround_engine.py:119-146`):
| Key | Line |
|---|---|
| `turnaround_entry_treasury` | `:128` |
| `turnaround_rescue_financing` | `:130` |
| `turnaround_mode = True` | `:131` |
| `turnaround_round = 1` | `:132` |
| `game_over = False` | `:133` |
| `game_over_reason = None` | `:134` |
| `active_event_flags.turnaround_phase = "crisis"` | `:135` |
| `active_event_flags.turnaround_status = "open"` | `:136` |
| `corporate_treasury += bailout` | `:137-138` |

`apply_commit` (`:148-211`): `corporate_treasury` (`:164`), `turnaround_rescue_financing`
(`:174`), `group_reputation` (`:175`), `flags.turnaround_phase` (`:182`),
`flags.turnaround_graduated` (`:202`), `flags.turnaround_final_mr_cap` (`:204`),
`turnaround_round` (`:208`).

`_finalize` (`:215-307`): `gs["turnaround_amended_report"] = report` (`:302`),
`flags["turnaround_status"] = status` (`:303`), `turnaround_mode = False` (`:304`),
`game_over = True` (`:305`), `game_over_reason = "turnaround_complete" | "turnaround_expired"` (`:306`).

`abort_arc` (`:310-325`) reverses all of it and sets `flags["turnaround_status"] = "aborted"`.

What it deliberately does NOT write: `final_report_canonical` is read at `:229` and never
mutated (stated `:224-226`, `:5-8`). `regenerative_multiple` in `gs` is not overwritten.

Re-valuation detail (`:254-274`): `net_debt_new = r10_net_debt - cash_recovered +
rescue_financing` (`:262`), so lever cash is carried as debt (IMP-14, `:166-171`); the
call is `calculate_terminal_value(bus, mr_final, ...)` at `:269-272`, wrapped in a bare
`except Exception: reval = None` (`:273-274`). If `bus` is falsy the whole re-valuation
is skipped and `report["revalued"]` is False (`:268`, `:291`).

### 5b. Consumers — applying the test (display payload / admin route / reverse-map = NOT a consumer)

Every non-test reference to the module, whole repo:

| Site | Kind | Verdict |
|---|---|---|
| `backend/admin_router.py:6192` `leaderboard_annotation(gs)` | admin leaderboard payload | display payload — NOT a consumer |
| `backend/admin_router.py:6559` `leaderboard_annotation(gs)` | admin payload | display payload — NOT a consumer |
| `backend/admin_router.py:12334` `te.enter_arc` | admin route `POST /turnaround/{id}/open` | admin only |
| `backend/admin_router.py:12371` `te.apply_commit` | admin route `POST /turnaround/{id}/commit` | admin only |
| `backend/admin_router.py:12401` `te.abort_arc` | admin route `POST /turnaround/{id}/abort` | admin only |
| `backend/admin_router.py:12419` `te.arc_state` | admin route `GET /turnaround/{id}/state` | admin only |
| `backend/router.py:2164` `gs.get("turnaround_amended_report")` | field in the player final-report response | display payload — NOT a consumer |
| `backend/router.py:2165` `turnaround_offer` from `engine.turnaround_offer_for` | field in the same response | display payload — NOT a consumer |
| `backend/branching_engine.py:286` | comment | not a call site |
| `backend/admin_shared.py:1800` | comment | not a call site |
| tests: `test_imp_hygiene_wave3.py:69`, `test_turnaround_calibration.py:18`, `test_turnaround_p3.py:18`, `test_turnaround_p5.py:9`, `test_turnaround_revaluation.py:11` | tests | tests only |

The engine's own output is explicitly non-authoritative:
`leaderboard_annotation` (`backend/turnaround_engine.py:344-366`) stamps
`"authoritative": False` on every payload it returns (`:359`, `:366`) and its docstring
says "The canonical R10 M_R stays the authoritative leaderboard figure — this is purely
additive" (`:346-350`).

**There is no non-admin, non-test call site of `enter_arc`, `apply_commit`, `abort_arc`
or `arc_state` anywhere in the repo.**

### 5c. System A's write-backs (these DO have real consumers)
`ctx.events` → `active_event_flags` via `backend/router.py:3323-3324`
(`merged_flags.update(events)`). Consumed for real at `backend/engine.py:2961-2967`
(dividends zeroed), `backend/engine.py:3064-3072` (CapEx cap), and
`backend/balance_sheet.py:706-708` (goodwill impairment). `mr_cap` is the exception —
see §1e, it is written and never read.

### 5d. Side-effect worth flagging
`enter_arc` sets `gs["game_over"] = False` (`backend/turnaround_engine.py:133`), and the
player commit endpoint's only two completion gates are `current_round > 10`
(`backend/router.py:2569`) and `game_over` (`backend/router.py:2589`). During an open
arc `round_number` is still 10 and `game_over` is False, so neither gate trips; the
`expected_round` guard (`backend/router.py:2621`) also passes at 10. Marked UNCERTAIN —
downstream guards beyond `router.py:2640` were not exhaustively traced.

---

## 6. REACHABILITY

### System A — mid-sim distress: PLAYER-REACHABLE
Single call site `backend/engine.py:4311`, inside the normal per-tick pipeline invoked
by the player commit path (`backend/router.py` commit handler → `process_tick`). No
feature flag, no permission, no admin action. A cohort that runs treasury to ≤ $0 with
reputation < 30 in round ≥ 2 enters crisis automatically and pays the CapEx freeze, the
dividend suspension and the goodwill impairment. It does **not** pay an M_R cap (§1e,
§3a).

### System B — the post-completion arc: NOT player-reachable
Four locks, all read from code:

1. **Feature flag, default OFF.** `admin_shared.py:328` — `"turnaround_module_enabled":
   False` in the `_god_mode_settings` defaults. Flipped only at
   `backend/admin_router.py:12225`.
2. **Two-key permission.** `can_orchestrate_turnaround`
   (`backend/admin_shared.py:177-197`): returns False if the module is off (`:190-191`);
   `lead_facilitator` and above bypass the grant list (`:192-193`); anything below
   `facilitator` — "project_admin / players never orchestrate" (`:194-195`); a base
   facilitator needs an explicit per-id grant (`:196-197`).
3. **Route guards.** Every arc endpoint carries `Depends(get_fac_role)` +
   `Depends(require_sim_manager)` (`admin_router.py:12329-12331`, `12367-12369`,
   `12397-12399`, `12415-12417`), plus `_assert_session_ownership`
   (`:12333`, `:12374`, `:12403`, `:12420`) and, on `/open`, re-checks of the module flag
   (`:12338`) and `can_orchestrate_turnaround` (`:12340`).
4. **No player endpoint.** `backend/router.py` contains no arc mutation route. Its only
   turnaround references are the two read-only response fields at `:2164-2165`.

Eligibility gates on `/open` (`backend/admin_router.py:12347-12359`): not already active
(409), not already run (409), `round_number >= 10 or game_over` (409), and
`turnaround_score_eligible(canonical M_R)` i.e. M_R < 0.80 (409).

Players CAN see the offer: `backend/router.py:2123-2124` attaches
`turnaround_offer_for(gs, _gms.get("turnaround_module_enabled", False))`
(`backend/engine.py:1652-1677`), returning `{eligible, current_mr, threshold: 0.80,
max_rounds: 4, premium_if_graduated: 0.10}` — or `None` when the module is off
(`engine.py:1657-1658`). It is a display field with no player action behind it.

