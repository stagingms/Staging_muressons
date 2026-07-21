# Detailed Implementation Plan — Turnaround Module (Post-Completion Optional Extension)

**Module:** A superadmin-gated, facilitator-orchestrated, 4-round crisis-recovery arc that a facilitator may run **after a session has completed its 10 rounds**, offered to teams whose terminal Regenerative Multiple (M_R) fell below 0.80.

**Companion docs:** `SPEC_Turnaround_PostR10_Extension.md` (mechanics), `PATHWAY_MAP_Muressons.md` (context).

---

## 1. Guiding principles (non-negotiable framing)

1. **The normal game ends at Round 10.** A standard run is *completed* the moment R10's terminal valuation is written. The turnaround module never changes that. It is a separate, additive overlay.
2. **Non-destructive.** The canonical R10 result (M_R, terminal value, archetype) is snapshotted immutably before the arc begins. The arc can only ever *append* an amended result; it can never silently overwrite the original.
3. **Off by default, two-key access.** Superadmin (god_mode / super_admin) must enable the capability globally **and** grant it to a specific facilitator. Only then can that facilitator orchestrate the arc for a completed session they manage. This mirrors the existing side-track permission model exactly.
4. **Facilitator orchestrates, player plays.** The facilitator opens the arc and paces the four rounds; the team makes the T1–T4 decisions. Neither can start it without the superadmin grant.
5. **Reuse, don't reinvent.** The phase gates, caps, bailout and terminal-valuation math already exist (`engine.py` Feature 25, `terminal_valuation.py`). This module adds a *front door, a permission layer, orchestration controls, and a UI* — not new economics.

---

## 2. Permission & orchestration model (three tiers)

Mirrors the side-track pattern (`_god_mode_settings["side_tracks_available"]` + `side_tracks_facilitator_permissions`, and `assign_cohort_side_tracks`). Uses the existing RBAC guards.

| Tier | Who | Action | Guard | Storage |
|---|---|---|---|---|
| **1. Global enable** | god_mode / super_admin | Turn the module on platform-wide | `require_super_admin` (+ audit reason) | `_god_mode_settings["turnaround_module_enabled"]` |
| **2. Per-facilitator grant** | god_mode / super_admin | Allow a named facilitator to orchestrate | `require_super_admin` | `_god_mode_settings["turnaround_facilitator_permissions"][fac_id]` |
| **3. Orchestrate a session** | facilitator (sim manager) | Open + pace the arc on a completed session they manage | `require_sim_manager` | per-session `gs["turnaround_*"]` |
| **(play)** | player (team) | Submit T1–T4 decisions when the facilitator opens each round | `X-Player-Id` + session ownership (SEC-3) | per-session decision log |

Rules enforced (copying `set_facilitator_side_track_permissions` semantics):

- A facilitator grant is rejected unless the module is globally enabled first (`400 "enable globally first"`).
- Base `facilitator` may orchestrate only if present in `turnaround_facilitator_permissions`; `lead_facilitator` and above bypass the per-facilitator list but the bypass is **audited** (`_audit("turnaround_permission_bypassed", …)`), exactly as side-tracks do.
- `project_admin` is **excluded** — orchestrating a live/finished run is run-management, so all orchestration endpoints use `require_sim_manager`, never `require_facilitator`. (Per `CLAUDE.md` RBAC rule 2.)
- `god_mode` passes every guard by level, so no string checks — use `is_admin_role` / the level-gated guards.

### Endpoints (permission surface)

| Method / path | Guard | Purpose |
|---|---|---|
| `PUT /api/admin/turnaround/global` | `require_super_admin` (+reason) | Set `turnaround_module_enabled` |
| `GET /api/admin/turnaround/permissions` | `require_super_admin` | Read global flag + per-facilitator grants |
| `PUT /api/admin/turnaround/permissions/{fac_id}` | `require_super_admin` | Grant/revoke a facilitator |
| `GET /api/admin/turnaround/eligibility/{session_id}` | `require_sim_manager` | Is this completed session eligible + is caller permitted? |
| `POST /api/simulations/{session_id}/turnaround/open` | `require_sim_manager` | Facilitator opens the arc (enters Crisis) |
| `POST /api/simulations/{session_id}/turnaround/round/{n}/open` | `require_sim_manager` | Facilitator releases T-round n to players |
| `POST /api/simulations/{session_id}/turnaround/commit` | player (SEC-3) | Team submits the round's decision |
| `POST /api/simulations/{session_id}/turnaround/round/{n}/advance` | `require_sim_manager` | Facilitator closes the round → gate check → next phase |
| `POST /api/simulations/{session_id}/turnaround/abort` | `require_sim_manager` | Cancel the arc, restore canonical R10 result |

---

## 3. Completion invariant — how "completed after 10 rounds" is protected

The word "completed" must keep meaning R10 for normal runs, so:

1. When R10 valuation is written, **also** persist an immutable snapshot: `gs["final_report_canonical"] = {terminal_valuation, regenerative_multiple, archetype, computed_at, source:"r10"}`. This is written once and never mutated by the arc.
2. `game_over` stays `True` and `round_number` stays `10` for the base session. The arc does **not** reuse `round_number`; it uses a separate `turnaround_round` (1–4). No collision with Extended Horizon (which advances `round_number` to 11+).
3. The dashboard, `get_final_report`, and the leaderboard read `final_report_canonical` as the authoritative "completed" result **unless** the arc graduated, in which case they show the canonical result *plus* an explicitly-labelled `turnaround_amended` result. The original is always retrievable.
4. Aborting or expiring the arc leaves the session exactly as it was at R10 completion.

This means a normal run is never in a half-finished state, and analytics that count "completed sessions" are unaffected.

---

## 4. Lifecycle state machine

```
COMPLETED (R10, game_over=True, final_report_canonical written)
   │
   │  superadmin: module_enabled AND facilitator granted
   │  AND canonical M_R < 0.80
   ▼
ELIGIBLE ──(facilitator: /turnaround/open)──▶ ARC_OPEN (phase=crisis, +$3M, T-round=1)
   │                                              │
   │ facilitator never opens → stays COMPLETED    │ per round n = 1..4:
   │                                              │   facilitator opens round n
   │                                              │   players commit decision
   │                                              │   facilitator advances → gate check
   │                                              ▼
   │                        ┌─ gate cleared → phase++ (crisis→stab→recovery→exit)
   │                        └─ not cleared  → same phase, round++
   │
   ├── reached EXIT (≤ T4) ──▶ GRADUATED → re-value (clamp lifted, +0.10) → turnaround_amended
   ├── T4 done, no EXIT   ──▶ EXPIRED   → M_R clamped at last phase cap → canonical unchanged
   └── /turnaround/abort  ──▶ ABORTED   → canonical restored, arc state cleared
```

Terminal states: `GRADUATED`, `EXPIRED`, `ABORTED`. All three set `turnaround_mode=False` and leave `game_over=True`.

---

## 5. Data model

### 5.1 God-Mode settings (`admin_god_controls.py` / `_god_mode_settings`)

```python
"turnaround_module_enabled": False,                 # tier-1 global switch
"turnaround_facilitator_permissions": {},           # {fac_id: True} tier-2 grants
```

### 5.2 Per-session state (`global_state`)

| Key | Type | Notes |
|---|---|---|
| `final_report_canonical` | dict | Immutable R10 snapshot (written at completion) |
| `turnaround_mode` | bool | Arc active |
| `turnaround_round` | int | 1–4; 0 when inactive |
| `turnaround_round_open` | bool | Facilitator has released the current round to players |
| `flags["turnaround_phase"]` | str | crisis / stabilisation / recovery / exit |
| `flags["turnaround_status"]` | str | eligible / open / graduated / expired / aborted |
| `flags["turnaround_graduated"]` | bool | |
| `turnaround_amended_report` | dict\|null | Only written on graduation |
| `turnaround_audit` | list | Per-round log (who opened, choices, gate result) |

---

## 6. Backend workstreams

### WS-A — Config & constants
- `simulation_config.json`: add `turnaround_pathway.arc { max_rounds:4, eligibility_mr_threshold:0.80, entry_bailout:3000000 }`.
- `config.py` (~line 566): `TURNAROUND_ARC_MAX_ROUNDS`, `TURNAROUND_ARC_MR_THRESHOLD`, `TURNAROUND_ARC_ENTRY_BAILOUT`.

### WS-B — Permission plumbing (mirror side-tracks)
- `admin_god_controls.py`: add the two settings keys; add them to the writable set in `PUT /god/settings`; `mark_godmode_dirty()` on change.
- New admin endpoints (`PUT /turnaround/global`, `GET|PUT /turnaround/permissions[/{fac_id}]`) modeled line-for-line on `update_global_side_tracks` / `set_facilitator_side_track_permissions`, including the "enable globally first" guard and audit entries.
- Helper `can_orchestrate_turnaround(role, fac_id) -> bool`: `is_admin_role(role)` or (`lead_facilitator+`) or `fac_id in permissions`. Bypass by privileged roles is audited.

### WS-C — Completion snapshot
- In the R10 valuation write path (round_logic.py, `_post_r10_grand_finale` region / commit_turn_impl ~1950), after M_R/archetype are set, write `gs["final_report_canonical"]` **once** (guard: only if absent).
- `get_final_report` (router.py:1251): return `final_report_canonical` as authoritative; include `turnaround_amended_report` when present; compute and attach `turnaround_offer` (eligible when module enabled + caller permitted + canonical M_R < threshold + not already run).

### WS-D — Engine: deliberate entry + cap enforcement
- `detect_distress` (engine.py:1292): add `deliberate_entry=False` param that returns the Crisis-entry dict when `current_phase=="none"`, bypassing the ≤$0/<30 condition and the R2 grace. **Default False keeps all existing callers/tests identical.**
- Cap enforcement (the current gap): in the turnaround commit path, feed `distress["capex_cap_multiplier"]` → `events["capex_cap_multiplier"]` (round_logic.py:960 path) and `distress["mr_cap"]` → `extra["mr_cap"]` (round_logic.py:2454 clamp). Scope to `turnaround_mode` so mid-sim behaviour is untouched in this change.

### WS-E — Round content
- `branching_engine.py`: `TURNAROUND_ROUNDS = {1..4}` + `get_turnaround_round_config(n)`, mirroring `EXTENDED_ROUNDS`. Each round = one A/B/C recovery lever. **Calibrate impacts so the §2 gates are reachable from the distressed floor** (T1 must be able to lift treasury > $0 and rep > 20). This is the one content-design task, not mechanical wiring.

### WS-F — Orchestration endpoints
- `open`, `round/{n}/open`, `commit` (player), `round/{n}/advance`, `abort` per §2. All orchestration guards = `require_sim_manager`; `commit` = player SEC-3 ownership.
- `advance` runs `detect_distress(...current_phase=phase)` progression, updates `turnaround_phase`, advances `turnaround_round`, and terminates at graduation or after T4.
- On graduation: clear `survival_mode`, re-run `compute_terminal_valuation` with clamp lifted + `TURNAROUND_EXIT_MR_BONUS`, write `turnaround_amended_report`, set status `graduated`.
- On expiry: write clamp = last phase `mr_cap`, status `expired`, leave canonical untouched.
- `abort`: clear all `turnaround_*` state, status `aborted`.

### WS-G — WebSocket / pacing
- Emit arc state changes over the existing admin/player WS fan-out (`ws_fanout.py` / `admin_ws.py`) so the facilitator console and player belt update live when a round opens/closes.

---

## 7. Frontend workstreams (CLAUDE.md V-D compliant)

Three distinct surfaces, each owned by its role. **No new always-visible player panel.**

### FE-1 — Superadmin settings (God-Mode console)
- A toggle for `turnaround_module_enabled` and a per-facilitator grant list, placed in the existing God-Mode settings area alongside the side-track global/permission controls (reuse those components' shape).
- If it lands in a sidebar tab, update that tab's tooltip in the same commit (tooltip must describe what it renders — `CLAUDE.md` sidebar rule).

### FE-2 — Facilitator orchestration console
- On a **completed** session the facilitator manages, show a "Turnaround Available" affordance (only if permitted + eligible). Controls: Open Arc → per-round Open/Advance → live phase + gate status + which teams have committed. Lives in the admin/facilitator surface, not the player app.

### FE-3 — Player surfaces (two existing slots only)
- **KPI belt** — a glanceable phase chip `Crisis › Stabilisation › Recovery › Exit`, current stage lit, next gate shown (`Need: Treasury > $0 · Rep > 20`). Rendered only while `turnaround_mode`. Header comment names the slot: *KPI belt*.
- **OverlayHost** — entry / phase-transition / graduation-or-expiry are interrupts (already emitted as `custom_black_swans`); route through OverlayHost.
- **Results stage** — the comeback recap (before/after M_R, premium) renders here, not mid-arc (V-A precedent).
- Tokens only (`--danger` / `--success` / `--caution`), no raw hex (contrast with the existing hard-coded `rgba(...)` in `EngineEventsPanel.js:550`).

---

## 8. Scoring, leaderboard & analytics

- Leaderboard's authoritative entry stays the **canonical R10 result**. A graduated arc adds a separate, clearly-labelled `turnaround_amended` figure — never silently replacing the R10 score. Facilitators/superadmin choose whether to display amended results in a cohort view.
- M_R normalization (pathway difficulty coefficients) is unaffected; the amended M_R is post-normalization annotated as "turnaround-adjusted."
- Analytics counting "completed sessions" continue to key off R10 completion; the arc adds an orthogonal `turnaround_status` dimension.

---

## 9. Test plan

Backend (extend `tests/test_new_features.py`, `test_simulation_integrity_extended.py`, `backend/tests/`):

1. **Default-off** — module disabled → `eligibility` returns not-eligible; `open` → 403.
2. **Two-key gate** — globally enabled but facilitator not granted → base facilitator 403; granted → 200; `lead_facilitator` bypass succeeds and writes an audit row.
3. **project_admin excluded** — orchestration endpoints reject project_admin (require_sim_manager).
4. **Eligibility threshold** — canonical M_R 0.79 eligible, 0.80 not.
5. **Completion invariant** — after `open` + rounds, `final_report_canonical` is byte-identical to the R10 snapshot; `game_over` never flips to False for the base report.
6. **Deliberate entry** — `detect_distress(deliberate_entry=True, current_phase="none")` → crisis, +$3M, regardless of treasury/rep.
7. **Graduation** — scripted T1–T3 clears gates → amended report written, clamp lifted, +0.10, archetype rises above Turnaround Manager.
8. **Expiry** — 4 rounds, gate never cleared → status expired, canonical untouched, M_R clamped at last phase cap.
9. **Cap enforcement** — while in Stabilisation, amended M_R ≤ 0.80 (regression on the pre-existing gap).
10. **Abort** — restores canonical state, clears `turnaround_*`.
11. **Backward-compat** — all existing `detect_distress` tests pass unchanged; role-hierarchy sync tripwire (`test_role_hierarchy_sync.py`) still green.

---

## 10. Rollout phases & acceptance criteria

| Phase | Scope | Acceptance |
|---|---|---|
| **P1 — Permission spine** | WS-A, WS-B, God-Mode settings + admin endpoints, tests 1–3 | Superadmin can enable globally + grant a facilitator; base facilitator without grant is blocked; bypass audited. No player-visible change. |
| **P2 — Completion snapshot + eligibility** | WS-C, tests 4–5 | Canonical R10 snapshot written once and immutable; `get_final_report` exposes `turnaround_offer` only when the two keys + threshold hold. |
| **P3 — Engine + orchestration** | WS-D, WS-E, WS-F, tests 6–10 | Facilitator can open + pace T1–T4 headlessly (via API); graduation/expiry/abort all behave per §4; caps enforced. |
| **P4 — Realtime + UI** | WS-G, FE-1/2/3 | Superadmin toggle, facilitator console, and player belt chip work end-to-end; slotting-rule compliant; tooltips + tokens correct. |
| **P5 — Analytics/leaderboard** | §8 | Amended results labelled and separable; "completed" counts unchanged. |

Each phase is independently shippable; P1–P3 are backend-only and fully testable without UI.

---

## 11. Risks, conventions & tripwires

- **Slotting rule (V-D):** no new standing player panel — belt chip + OverlayHost + results stage only. Name each slot in the component header. A reviewer will treat a new ambient panel as a defect.
- **RBAC rule (CLAUDE.md §2):** orchestration = live-run management → `require_sim_manager` (excludes project_admin), not `require_facilitator`. Role assignment untouched, so no `ROLE_HIERARCHY` drift — but run `test_role_hierarchy_sync.py` anyway.
- **Sidebar tooltip rule:** if the superadmin toggle appears in a sidebar tab, change the tooltip in the same commit.
- **Tokens (Phase-B note):** hue/semantic-color choices use `tokens.css` on a real screen, not raw hex.
- **Gate calibration risk (WS-E):** the only judgment-heavy task — mis-tuned option impacts make graduation impossible or trivial. Calibrate against §2 and add a Monte-Carlo sanity check (see `test_qa_monte_carlo.py`) that a "reasonable play" graduates with plausible probability.
- **Idempotency:** `open`, `round/{n}/open`, and `advance` must be safe to retry (facilitator double-clicks); key off `turnaround_round` + `turnaround_round_open`.

*Sources: admin_router.py (side-track global/permission/assign endpoints 9173–9310, `require_sim_manager`:168), admin_god_controls.py, admin_shared.py (`is_admin_role`, `assignable_roles_for`, `require_sim_manager`), engine.py (Feature 25), config.py:566–594, simulation_config.json, router.py (`get_final_report`:1251, `activate_extended_mode`:5688), round_logic.py:960/2454/1950, terminal_valuation.py:541–557, branching_engine.py (`EXTENDED_ROUNDS`), CLAUDE.md conventions.*
