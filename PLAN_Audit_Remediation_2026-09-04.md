# PLAN — Remediation of AUDIT_Engines_Flow_Classroom50_2026-09-04

**Status:** plan only. No code is touched until the owner says go. Implementation will then land on a new branch `fix/audit-remediation-20260904` off `fix/launch-readiness-20260903` (`d3bbf09`), uncommitted, one work package per logical change, with the full backend suite (1,851 tests / 163 files) and the jest suite run and reported.

**Scope:** every finding in the audit, organised into four waves by deadline. Wave 0 is what turns NO-GO into GO-WITH-CONDITIONS; Waves 1–3 are ordered by classroom impact. The owner decides the cut.

**Verification standard for every wave:** the five shipped paradigms — `legacy_abc`, **`multi_toggles`** (pillar mode: `pillar_flags`, `hr_invested_r*`, proxy-option translation), `advanced_climate`, `healthcare`, `brsr_ngrbc` — each played end to end through the real router (`~/audit_scratch/rng/harness.py` pattern), at `advanced` and `expert` tiers, plus the golden traces, the invariant suites and the audit probes named per work package. A work package is done only when its "Done when" line is true on all five paradigms (or explicitly scoped otherwise, e.g. CBAM is `advanced_climate`-only).

**Conventions carried from CLAUDE.md and the repo:** tests in the same commit as the change; golden rebaselines via `MURESSONS_REBASELINE_GOLDEN=1` in the same commit with the delta stated in the message; any player-facing UI change names its slot and uses `tokens.css`; shockwave catalog / role hierarchy tripwires untouched; docs that describe a changed mechanic updated in the same commit (three prior audits found stale tooltips).

Effort figures are developer hours for one person who knows the codebase; "verify" hours include running probes on five paradigms.

---

## 0. Branch, tooling and gates (do first, ½ day)

| Step | What | Done when |
|---|---|---|
| 0.1 | `git checkout -b fix/audit-remediation-20260904 d3bbf09`. Never commit to `main`/`production`. | branch exists |
| 0.2 | Copy the audit probe archive (`Claude outputs/audit_2026-09-04_probes_and_cluster_reports.tar.gz`) to a scratch dir outside the tree; `env.sh` points `MURESSONS_DATA_DIR` at scratch. Two probes write into the repo (`cfg/probe_hot_reload.py`, `acc/probe_admin_reach.py`) — run them only on a throwaway clone. | probes run green against HEAD before any change (baseline) |
| 0.3 | Add `backend/tests/test_five_paradigm_smoke.py`: parametrised over `config.VALID_DECISION_PARADIGMS` × `{advanced, expert}`, plays 10 rounds through the router with the dry_run "balanced" scorer, asserts no `engine_failures`, `game_over`, `final_report_canonical` present, treasury/reputation/M_R finite. This is the regression gate every wave runs. (~2 h) Bug it would have caught today: VAL-06 (`brsr_ngrbc` never reaches its finale — assert `terminal_ebitda` present for brsr). | 10 parametrised cases pass on HEAD except the brsr case, which is `xfail(strict=True)` until WP-28 |
| 0.4 | Add `scripts/verify_wave.sh`: runs pytest (full), jest (full), the smoke above, the golden traces, `audit_financial/run_trace.py`, and the per-WP probes listed below; prints a one-screen pass/fail table. | script exists; used at the end of every wave |

---

## Wave 0 — Blocking before class (turns NO-GO into GO-WITH-CONDITIONS) · ≈ 1.5 developer-days

### WP-01 · Render the forced change-password screen in the cockpit — F-01 · P0 · 2 h + 1 h verify
- **Files.** `frontend/app/page.js` (early returns at ~1371/1395; join overlay :1535), `frontend/app/hooks/useSimulation.js` (:414-437 login; :553-559 commit 403 handler), `frontend/app/components/StakeholderMapModal.js:274`, `DoubleMaterialityMatrix.js:1071` (renders `data.detail` — an object for this 403), `components/ChangePasswordModal.js` (props `isOpen, isForced, prefillPlayerId, onClose, onSuccess` as used in `JoinCohortModal.js:240-252`).
- **Change.** In `page.js`, before the username/briefing early returns: `if (sim.sessionId && sim.mustChangePassword) return <ChangePasswordModal isOpen isForced prefillPlayerId={localStorage.getItem('muressons_playerId') || ''} onClose={() => {}} onSuccess={() => sim.setMustChangePassword(false)} />` (or expose `playerId` from the hook — it is stored at `useSimulation.js:420` but not returned). Make every 403 handler surface `detail.message` when `detail.code === 'password_change_required'` and re-open the modal: commit (:553-559 already sets the flag — now the page reacts), stakeholder map (:274), matrix (page.js:1942 → pass a string, not the object), save-decisions. Slot: OverlayHost (interrupt), per CLAUDE.md.
- **Tests.** Extend `~/audit_scratch/flow/jest/pwmodal.test.js` into `frontend/__tests__/forced-password.test.js`: rendering `page.js` with `sessionId` set and `mustChangePassword: true` must render `#change-password-title`; after `onSuccess` the briefing renders. Backend: `backend/tests/test_launch_audit_2026_09_01.py` already pins the 403; add one case that `change-password` with the default password then `save-decisions` → 200 (the recovery path).
- **Verify.** `flow/probe_pwchange.py` unchanged (server side) + jest. Manual: fresh player on all five paradigms → sign in → modal → set password → R1 map submits.
- **Done when.** A fresh `MUR-XXXX@123` login lands on the change-password screen and cannot bypass it; after changing, R1 writes succeed; the `CHANGES_launch_blockers_2026-09-02.md:147-149` sentence becomes true.
- **Risk.** Low. Rollback: revert the page.js block. **Dependency:** none. The facilitator "Forgot your password?" recipe stays in the runbook as the fallback.

### WP-02 · Forward the cohort seed before post-tick engines — F-04 · P0 · 1 h + 2 h verify
- **Files.** `backend/router.py` (before `post_events = post_tick(` at ~2901); reference `dry_run.py:191`.
- **Change.** `_seed_fwd = (current_global.get("active_event_flags") or {}).get("stochastic_seed"); if _seed_fwd: new_global.setdefault("active_event_flags", {}).setdefault("stochastic_seed", _seed_fwd)`. Also copy `decision_paradigm`, `difficulty_tier`, `ending_pathway`, `loan_interest_rate` the same way (they are read by post-tick engines from `gs` today and currently only survive via the later merge) — one helper `_forward_persistent_flags(current_global, new_global)`.
- **Tests.** New `backend/tests/test_seed_reaches_post_tick.py`: two players, identical decisions, force the regulator to "enforcement" at R2 via state, assert identical `regulatory_fine` and treasury (the bug: `npc_stakeholders.py:693` falls to `random.uniform`). Extend `tests/test_seeded_stochastics.py` with a router-path case (today every seeded test is engine-level).
- **Verify.** `rng/probe_diverge.py` → three identical teams identical; `rng/probe_fix_verify.py` → fine `17,078,216.61` × 3 (memory store); `rng/probe_full_identical.py` without the stub → 0 diffs; run on all five paradigms.
- **Done when.** Identical decisions → identical state on every paradigm, no stub. **Side effect to record in the commit:** NPC/agent threshold offsets become per-cohort (RNG-7 closes).

### WP-03 · Production volume config + ratchet clamp — F-07 · P0 (conditional) · 1 h dev + 0.5 h ops
- **Ops first (owner, Railway CLI):** the F-07 inspect one-liner; patch if stale; Restart; re-inspect; deploy log has no `[CONFIG] WARNING`. If `/data/simulation_config.json` is absent, nothing to do.
- **Code.** `backend/config.py` after :493: clamp `REG_RATCHET_BASELINE <= 10.0` → 20.0 with the `[CONFIG] WARNING` pattern of :481. Add the four `slo_ramp` keys and `greenwash_abs_capex_floor` to `scripts/patch_volume_config.py` `PATCH` (SOC-9) and move the script to `backend/patch_volume_config.py` so it ships in the image (Dockerfile copies `backend/`).
- **Tests.** `tests/test_launch_audit_2026_09_01.py`: add `TestF10RatchetBound` mirroring `TestF07ImitationDecayBound` (stale volume → clamped + warning; in-range honoured).
- **Verify.** `cfg/probe_e2e_cbam_tax.py` on the stale scratch volume → R1 ratchet inactive, WARNING printed.
- **Done when.** A volume with `baseline 10.0` cannot fine R1; the patcher runs from inside the image.

### WP-04 · Debrief cards read the right round's decision — F-02 · P0 · 1 h + 1 h verify
- **Files.** `backend/admin_router.py:8555` → `decisions_by_round.get(decision_round, [])`; `backend/router.py:2159` → `out[tag] = ch` and fix the docstring :2145-2151.
- **Tests.** New `tests/test_debrief_decision_attribution.py`: play 3 rounds with known distinct options, GET `/api/admin/{sid}/debrief`, assert card N shows the option committed in round N; assert `dashboard.history[N].choice_selected` likewise.
- **Verify.** `seam/compare.py` decision rows match the commit log (all five paradigms; in `multi_toggles` assert the pillar summary, not a legacy letter).
- **Done when.** 10/10 cards correct; the latest played round shows its decision, not `''`.

### WP-05 · Reputation 0 is 0 everywhere — F-03 · P0 · 1.5 h + 1 h verify
- **Files.** `backend/admin_debrief_narrative.py:46` (`or 50` → `None`-check); 18 frontend sites: `ExecutiveCockpit.js:482, 590, 597, 615, 632, 2621, 4944-4947`, `AnnualReport.js:41`, `StudentReportExport.js:18`, `TerminalValuationCalc.js:51`, `WhatIfSandbox.js:45`, `MarketTicker.js:53`, `AIAdvisor.js:43`, `ESGImpactConstellation.js:60-61`, `stockValuationEngine.js:208`, `DecisionHistory.js:51`; plus `negotiation.py:319` (SEAM-18).
- **Change.** `x ?? 50` (JS) / `50 if x is None else x` (Python). Add an eslint rule or a jest "idiom tripwire" that greps `group_reputation || 50` (pattern of `__tests__/shockwave-catalog.test.js`).
- **Tests.** Narrative: session with persisted reputation 0.0 → `final.reputation == 0.0`, no "up" turning point. Jest: `ExecutiveCockpit` with `group_reputation: 0` renders `0/100`.
- **Verify.** `seam/compare.py` on player beta (reputation 0) → all surfaces 0.0.

### WP-06 · Counterfactuals compare like with like — F-06 · P0 · 2 h + 1 h verify
- **Files.** `backend/router.py:3319-3337`.
- **Change.** Baseline = `tick_result["global_state"]` (the actual `process_tick` output at :2811), not `new_global` after post-tick engines. State that the counterfactual is "engine-only" in the payload (`"scope": "process_tick"`) and in `EngineEventsPanel.js:702` / `FrontPageReveal.js:1044` copy. (Running the shadow through the full pipeline is the better model but doubles commit cost — defer to Wave 2 as an option.)
- **Tests.** New `tests/test_regret_analysis.py`: after a commit, `regret[alt].treasury_delta` for the chosen option's own letter is 0 and the two alternatives differ from each other whenever their option costs differ.
- **Verify.** `seam/compare.py` gap table → per-alternative deltas no longer equal the post-tick gap; R10 panel names the option actually applied (`r10_choice`).

### WP-07 · One closing number — F-08 · P0/P1 · 3 h + 2 h verify
- **Files.** `backend/router.py` (after `run_new_engines` :2919 and before `merged_flags` :3005), `backend/round_logic.py` (`_post_r10_grand_finale` :2593, :2766-2779, :2933, :3000; `run_new_engines` balance-sheet block :709-766 vs agents :1006-1035), `frontend/app/hooks/useSimulation.js:613-615`.
- **Change.** (a) Add `_restamp_finale(new_global, new_bus)` in router after `run_new_engines` when `round == SIM_ROUNDS`: recompute `final_treasury`, `group_reputation`, net debt → equity → `price_per_share`, `carbon_tonnage_group`, `final_report_canonical`, and the DMAV gate from the post-engine state (factor the bridge out of `_post_r10_grand_finale` into a function both call). (b) Move the balance-sheet tick to the end of `run_new_engines` (after agents) or add the re-sync block from FIN-02. (c) `useSimulation.js:613`: `setGlobalState(data.global_state); setBusinessUnits(data.business_units);` before `setGameOver(true)`.
- **Tests.** New `tests/test_finale_consistency.py`: after R10, `flags.final_treasury == gs.corporate_treasury == balance_sheet.cash (max 0)`; equity recomputed from persisted treasury equals `flags.equity_value`. Extend `test_financial_golden_trace.py` money surface with `final_treasury` (rebaseline expected: the golden's R10 values move by the R10 agent hits — state the delta in the commit).
- **Verify.** `seam/compare.py` final tables → treasury/reputation/equity/emissions agree across dashboard, final-report, front-page, balance-sheet; `fin/recon_full.py` cash articulation 0 of 200 statements stale.
- **Done when.** One closing treasury on every surface, live and after reload, all five paradigms.

### WP-08 · Desalination pays what it promises — F-05 · P0 · 0.5 h + 0.5 h verify
- **Files.** `backend/round_configs.py:588-592, 603`; `backend/admin_teleprompter.py:570`; `frontend/app/components/FacilitatorTeleprompter.js:1320`.
- **Change.** `payback_rounds: 2`; text "a single $5M payment credited at the Round 10 tick"; teleprompter strings to match ($5M once). Alternative (more faithful): make `_process_pending_projects` support `per_round` payouts — Wave 2 (WP-24).
- **Tests.** `flag/probe_deferred.py` → convert to `tests/test_pending_projects_mature.py`: R8-C → `revenue_generation` matures at the R10 tick (+$5M); NCD −30 still matures.
- **Done when.** The R8-C text, the teleprompter and the engine agree.

### WP-09 · Wizard pacing is enforced — F-18(i) · P1 (blocking because it strands the facilitator's controls) · 2 h + 1 h verify
- **Files.** `backend/admin_router.py` `save_cohort_pacing` (~10944-11000, :10985), `set_pacing` clamp pattern (:3810-3814), `frontend/app/components/CreateCohortModal.js:727-733`, `RoundPacingControl.js:9-24, 115`, `RunBar.js:104, 123-125`.
- **Change.** Server: map wizard vocabulary → gate vocabulary (`free_play→free`, `manual→manual` + `unlocked_round = max_unlocked_round` clamped ≥ current round, `scheduled→timed` + `schedule` from `round_schedules`); write through the same code as `set_pacing`. RunBar: send `target_round = unlocked_round + 1` (idempotent, FLOW-11). Wizard copy: "Free Play" explains the barrier.
- **Tests.** New `tests/test_wizard_pacing_enforced.py`: create with `manual/max_unlocked_round=1` → R2 commit 403 "locked"; `scheduled` → schedule persisted; `free_play` → mode `free`. Extend `probe_wizard_pacing.py` cases.
- **Done when.** The wizard's choice and Round Pacing agree and a player cannot run ahead in Manual.

### WP-10 · Close the answer-key leaks and the forgeable guard — F-10, F-11 · P1 (blocking for graded validity) · 2 h + 1 h verify
- **Files.** `backend/admin_teleprompter.py:960, 1011, 1187, 1221`; `backend/admin_router.py:1559, 8897, 10633, 10857, 12413, 12797`; `backend/router.py:4839` (`stakeholder-map/master`); `backend/admin_router.py:7176` (`materiality-config`); `backend/admin_analytics.py:621-624`.
- **Change.** `_g: None = Depends(require_facilitator)` on the ten reference handlers. `materiality-config`: return a player projection (strip `financial_impact`, `societal_impact`, `correct_quadrant`, `panel_recommendations`) unless `get_facilitator_from_request(request)` — the `esg_profile_weights` pattern at `admin_router.py:500-540`; confirm `DoubleMaterialityMatrix.js:411` and `InvestmentMatrix.js:126` render without the stripped fields. `admin_analytics.py`: replace the header compare with `await _assert_player_owns_session(request, session_id, allow_observer=True)` and `_assert_session_visible` for facilitators.
- **Tests.** Extend `tests/test_admin_route_guards.py`: the ten routes → 401 without a cookie; `materiality-config` no-creds body has no `financial_impact`; `analytics/player` with forged header → 403, with other-cohort facilitator → 403. Lower `_MAX_UNTENANTED` accordingly.
- **Verify.** `acc/sweep_noauth.py` → the 57 no-cred 200s drop to the intended-public set (list in ACC §B); `acc/probe_analytics_player.py` → 403/403.
- **Done when.** Logged-out `GET /api/admin/teleprompter` → 401 on production after deploy (runbook pre-flight 3).

### WP-D0 · Deployment for Wave 0 (owner, 1 h)
1. `scripts/verify_wave.sh` green on the branch. 2. Push; Railway → Settings → Source watches the pushed branch; `GET /api/health` `.build` shows the new commit. 3. WP-03 ops steps. 4. Volume mounted at `/data` (OPS-3 check). 5. Runbook pre-flight items 3–6. 6. Keep `production` and `main` untouched until the cohort has run; merge after.

**Wave 0 acceptance gate.** Smoke on five paradigms × two tiers green; `probe_pwchange`, `probe_diverge`, `probe_deferred`, `seam/compare.py`, `probe_wizard_pacing`, `sweep_noauth` all show the new behaviour; goldens rebaselined with stated deltas only where WP-07 moved R10 figures.

---

## Wave 1 — Before class if time allows (P1 code fixes) · ≈ 3 developer-days

### WP-11 · CapEx term loan on the statement — F-12 · 2 h + 1 h verify
- **Files.** `backend/round_logic.py:731-741` (`bs_events`), `backend/balance_sheet.py:736-740, 783` (readers exist), `frontend/app/components/SustainabilityBalancedScorecard.js:1181-1185`, `BalanceSheetModal.js:232-243`.
- **Change.** Add `capex_loan_balance` (from `events`, falling back to `active_event_flags`) and `loan_interest_payment` to `bs_events`; add a "CapEx Term Loan" row to both statements (Total Non-Current already sums the key).
- **Tests.** Fix the harness gap: `tests/test_launch_audit_2026_09_01.py:1052-1059` currently passes the engine dict directly — add a router-path case: commit with CapEx > 20% of treasury → `GET /balance-sheet` shows `capex_term_loan > 0` and `interest_expense` includes the loan interest.
- **Verify.** `fin/bs_loan_probe.py` both shapes equal; `fin/full_run_probe.py` → `bsLoanMax > 0` wherever `capex_loan_balance > 0`; `audit_financial/recon.py` D/E moves. Goldens: the financial trace carries no loan (5–10% rungs), so no rebaseline expected — assert that.

### WP-12 · One price for a negative treasury; floor enforced where treasury is written — F-13, FIN-10 · 3 h + 2 h verify
- **Files.** `backend/balance_sheet.py:509-514, 573` (`charge_interest`), :795 (`/2` convention); `backend/engine.py:3357-3359` (debt service, no `/2`); floor :4124 vs post-tick writers (`npc_stakeholders.py:694`, `autonomous_agents.py:704/711`, `impact_engine.py:133`, `biodiversity_engine.py:465-468`).
- **Change.** Decide the one price (recommend: keep the engine's debt service, at `cost_of_capital / 2` per 6-month round, waterfalled; `_sweep_negative_cash(..., charge_interest=False)`); apply `FINANCIAL_TREASURY_FLOOR` once at the end of `run_new_engines` with an event, so no writer can breach it; cap brain-drain `penalty = min(penalty, 1.30)` (`engine.py:736-756`) — a calibration call, state it.
- **Tests.** `tests/test_treasury_waterfall.py`: add a negative-treasury case asserting exactly one interest line per round and closure; new `tests/test_floor_after_engines.py`: force a fine that would breach the floor → persisted treasury == floor.
- **Verify.** `fin/full_run_probe.py` healthcare/pure-A no longer ends below the floor; `fin/line_trace.py` shows one interest write per round. Rebaseline the financial golden if its trace ever goes negative (it does not at 5–10% rungs — assert).

### WP-13 · Projector, leaderboard and CSV use the awarded terminal value — F-14, SEAM-13 · 1.5 h + 1 h verify
- **Files.** `backend/admin_router.py:6113-6118` (+ row fields), `:6133-6145` sparkline, `frontend/app/admin/trading-floor/page.js:227-251`, `components/LeaderboardMatrix.js:239`, `ReportsExport.js:193`.
- **Change.** `terminal_value = flags.terminal_value if present else proxy` and label the proxy `"terminal_value_source": "projection"`; add `price_per_share`, `equity_value`, `regenerative_multiple`, `archetype` to the row; CSV exports the awarded value with a `source` column.
- **Tests.** `tests/test_leaderboard_awarded_tv.py`: completed game → leaderboard `terminal_value == flags.terminal_value`; mid-game → `source == "projection"`.
- **Verify.** `val/probe_leaderboard.py` served == awarded; `seam/compare.py` TV row agrees on 7 surfaces.

### WP-14 · Mid-game M_R projections and the ladder/mirror use the finale's flag semantics — F-15 · 3 h + 2 h verify
- **Files.** `backend/engine.py:4762-4770` (preview; `hr_investment_rounds` has no writer), `backend/consequence_dna_api.py:321`, `backend/admin_router.py:12445-12459` (what-if: pass `use_dynamic_multiple=True`, `wacc`), `backend/round_logic.py:3292-3325` (`_collect_all_flags` — make it importable without a cycle, e.g. move to `flag_utils.py`), `frontend/app/utils/mrJourney.js:36`, `components/MirrorDebrief.js:116`, `MRLadderReveal`/`RewindRibbon` (read `flags.mr_breakdown`).
- **Change.** One helper `mr_input_from_state(gs)` returning `({f: True for f in _collect_all_flags(flags)}, hr_rounds counted as round_logic.py:2620-2623)`; all four callers use it. Frontend reads `mr_breakdown` for earned components and derives "missed" from the arbiter's component list, not its own table.
- **Tests.** Extend `tests/test_mr_single_arbiter.py`: the finale/preview equality test must use a state with list-held flags (`r7_flags: ["synergy_unlock"]`) — today it uses `{}` and cannot see the bug. Jest: MirrorDebrief with `mr_breakdown.resilience_bonus: 0.2` does not list resilience as missed.
- **Verify.** `val/probe_preview_vs_finale.py` → 0/384 divergent; `val/probe_fullgame.py` preview at R9 == finale-style; multi_toggles: `hr_invested_r*` counted in preview.

### WP-15 · Reveal scale and units — F-20 · 1 h + 0.5 h verify
- **Files.** `simulation_config.json` `terminal_valuation.shares_outstanding` (+ volume patch list), `frontend/app/utils/stockValuationEngine.js:17`, `components/ArchetypeReveal.js:641`, `backend/round_logic.py:2798-2801` (DMAV NCD term).
- **Change.** `shares_outstanding` 6,500,000 (EV $19.2M×17 ÷ $50 baseline) so a $280M EV prices at ~$43 and $891M at ~$137; NCD formatter → "N NCD pts"; drop or scale the NCD term in `_dmav` (document the choice in MODEL_CARD).
- **Tests.** `tests/test_share_price_floor.py` — add a "typical EV prices above the amber threshold" case; jest snapshot for the NCD formatter.
- **Verify.** `val/probe_mr_bounds.py` share prices; seven full games → no solvent team red.

### WP-16 · Patience clock arms only from the first hostile-ish tier — F-16 · 1 h + 2 h verify
- **Files.** `backend/npc_stakeholders.py:552` (`tier_idx >= 1` → `>= 2`), `tests/test_stakeholder_golden_trace.py:668-690` (fixture pinning tier-1 forcing).
- **Change.** As stated; re-fixture the patience test at tier 2. Consider making `PATIENCE_LIMIT` per-NPC or raising to 4 — calibration call, state it.
- **Tests.** Re-fixture; add "an even-investment team with F4 ON receives no forced action in 10 rounds" (`soc/p10` as a test).
- **Verify.** `soc/p10_patience_cost.py` F4 ON ≈ F4 OFF for the even team; stakeholder golden unchanged (waves pinned OFF there).

### WP-17 · Timed-pacing auto-commit goes through the real commit path — OPS-1 · 2 h + 1 h verify
- **Files.** `backend/admin_router.py:3399-3530` (`_auto_commit_player`), `:3557-3566` caller; `backend/router.py` `_auto_commit_laggards`, `_run_commit_locked` (:487-612).
- **Change.** Delete `_auto_commit_player`; `_scheduled_unlock_task` calls `router._auto_commit_laggards(session_id, current_unlocked + 1)` once (locked, merging flags, R10-aware, draft-aware).
- **Tests.** `ops/probe_timed_autocommit.py` → `tests/test_timed_autocommit_path.py`: flags count equal to a normal commit; `stochastic_seed` present; R10 sets `game_over`, no R11 row.

### WP-18 · Server-side free-mode barrier and correct pacing chip — F-18(ii, iii) · 3 h + 1 h verify
- **Files.** `backend/router.py` commit gate (~2549-2571), `admin_shared.py:1527-1534`, `frontend/app/components/DecisionPressureTimer.js:49, 96-101`, `CountdownTimer.js:45-56` (reference), `page.js:1798` (banner wording).
- **Change.** In free mode with `free_advance_timeout_seconds == 0`, refuse commit of round N+1 while `cohort_advance_unblocked` is false and fewer than all teams have committed N (403 with the existing "waiting" copy); the reload path re-enters "waiting" from `team_commits_this_round`. Timer resolves `parent_cohort_id` (or reads `globalState.cohort_pacing_mode/cohort_next_unlock_at`, already on the dashboard `router.py:2249-2255`). Banner: "submitted for you from your draft" vs "with defaults".
- **Tests.** `tests/test_free_mode_barrier.py`: two teams, A commits R1 then R2 → 403 until B commits R1 or Force Advance. Jest: timer under a timed cohort shows the countdown on the briefing screen.
- **Verify.** `flow/probe_flow.py` A3 → 403; `flow/probe_pacing_scope.py` chip == cohort pacing.

### WP-19 · History and analytics integrity — SEAM-08/09/10/11 · 3 h + 1 h verify
- **Files.** `backend/router.py:3149-3155` (R10 overwrite), `:3290-3295` (board pressure after persistence), `:3524` (DNA state without `round_number`); `backend/admin_analytics.py:690-693`; `backend/admin_debrief_narrative.py:82-92`; `backend/consequence_dna_api.py:222`.
- **Change.** Persist a `final_state` (or row 11 flagged `is_final`) instead of overwriting row 10; apply board pressure before `insert_next_round`; pass `round_number` into the DNA state; pair prediction r with outcome r. Update every history consumer that assumed "row N = state entering N" (list in SEAM §B).
- **Tests.** `tests/test_history_semantics.py`: after R10, history has 10 entering-states + a final state; analytics R9/R10 deltas equal commit-time deltas; prediction r pairs with round r's delta; live DNA at R6 has the R6 node count.
- **Verify.** `seam/compare.py` mid-game and final tables; `seam/pred_probe.py`.

### WP-20 · Config observability and runbook — CFG-02, CFG-03, OPS-3, OPS-4 · 3 h + 1 h verify
- **Files.** `backend/config.py` (clamp ledger list appended at each `WARNING` site), `backend/config_introspect.py:136-137, 167-170`, `backend/main.py` lifespan (~295) and `health_check` (:594-696), `backend/runtime_paths.py:140`, `DEPLOYMENT_CHECKLIST.md` §5, `PREDEPLOY_CHECKLIST.md` Layer 4, `SETUP_STEPS.md` (remove the plaintext secrets block, CFG-07), `frontend/app/components/ConfigLiveStatus.js:13-15, 89`, `SimulationSwitchboard.js:994-996`.
- **Change.** `/config/live`: report clamps as high-severity `clamped_value`, add `image_vs_volume` key diff, demote `inert_tunable` to advisories so `healthy` means what it says; boot log prints `[config] volume differs from image on N keys: …`; `/health?strict=1` runs `SELECT 1` with a 2-s timeout and reports `mounted` from `/proc/mounts`; runbook gains the volume-refresh step and the "no `[CONFIG] WARNING`" check; fix the three "lives in the image" sentences.
- **Tests.** `tests/test_config_introspect.py`: stale scratch volume → `clamped_value` problems present, `healthy: false`; pristine → `healthy: true`.
- **Verify.** `cfg/probe_config_live.py` cases a/b.

**Wave 1 acceptance gate.** Wave 0 gate + `fin/recon_full.py` (loan on BS, cash articulation), `val/probe_preview_vs_finale.py` 0 divergent, `seam/compare.py` all rows agree, `soc/p10`, `ops/probe_timed_autocommit.py`, `flow/probe_flow.py`, on all five paradigms. Goldens: rebaseline only if WP-12 changes a traced round (assert not).

---

## Wave 2 — Before the next cohort (P2 model and content fixes) · ≈ 5–6 developer-days

### WP-21 · Natural decay per BU, recalibrated on the right quantity — F-17 · 4 h + 4 h verify
- **Files.** `backend/engine.py:3089-3096, 4632-4634, 4702`; `config.py:558-640` (tiers, comments :585-603 rewritten); `tests/golden/*.json`; `tests/test_stakeholder_golden_trace.py:143-144`; `DELTA_*` docs; `EVAL_Stakeholder_SLO_2026-09-01.md:43`.
- **Change.** `_inv_ratio = float(dec.get("investment_ratio", 0) or 0)`, falling back to the pre-austerity average only when `cfo_austerity_active`. Then re-measure tier populations **per BU per tick** on the stored real decisions (the 241-decision set is not in the repo — the owner must supply the export) before touching the bands; only then decide 0.15/0.20/0.30 vs alternatives.
- **Tests.** New `tests/test_natural_decay_per_bu.py`: a $0 BU decays while a $3M BU in the same team grows; austerity fallback pinned. Rebaseline both goldens (`MURESSONS_REBASELINE_GOLDEN=1`) with the per-BU delta stated (electronics/software will fall to the decay tier in the stakeholder trace).
- **Verify.** `soc/p1`, `p2`, `p3` grids; five-paradigm smoke; `scripts/balance_report.py` regenerated and BALANCE_REPORT_BASELINE.md updated with the reason.

### WP-22 · Display engines: fix or retire — F-19 (IMP-01/02/03/08), IMP-04, IMP-06, IMP-07 · 8 h + 3 h verify
- **Biodiversity.** `round_logic.py:692` sums `natural_capital_debt_applied_r*`; `biodiversity_engine.py:81, 94` zero the constant drivers or give them a writer; `tnfd_mr_bonus` gets a reader in `calculate_mr` or is removed (IMP-17). Test: greenest vs extractive bot → EHI differs and moves with NCD.
- **TCFD.** `tcfd_scenarios.py:164-165, 145, 154, 184`: emissions = Σ CI × revenue/1e6; price index by decade; guards. Test: annual carbon cost ≈ 1–3% of revenue at $250/t.
- **Meadows.** `consequence_dna_api.py:537` signature; `router.py:7048` builds history via the DNA extractor; `meadows_leverage.py:541` picks the highest non-LP12 point with count > 0. Test: a diverse decision history is not LP12.
- **SDG.** `router.py:3598-3620` reuses `sdg_result["bu_scores"]`; `sdg_linkage_engine.py:133, 198, 205, 208` read the real keys/ranges. Test: NCD 0 vs 5000 moves SDG-12; EHI 0 vs 100 moves SDG-15.
- **Journey panels (IMP-04).** Either apply the R7 allocation in post-tick and route the R6/R8 responses through a player endpoint, or reword `PedagogicalScaffolding.js:797, 835-838` and default the three toggles OFF.
- **Systemic-risk toggles (IMP-06)** get readers stamped onto `active_event_flags` at commit; **materiality shock (IMP-07)** gated on the team's own R2 flag and applying `forced_reallocation_pct` as a one-round flow, or demoted from a blocking modal.
- **Verify.** `imp/probe_bio.py`, `probe_tcfd.py`, `probe_meadows.py`, `probe_sdg.py`, `probe_toggles_dead.py`, full-game harness on five paradigms.

### WP-23 · Black-swan semantics and difficulty vocabulary — IMP-05, FIN-08, FIN-09, FLAG-8, IMP-11 · 4 h + 2 h verify
- `black_swan_registry.py:821-828` record the base changes as transients via `ctx.record_transient` and re-apply for `events_continuing`; headline "treasury hit" includes the flow erosion; `DIFFICULTY_TIERS` keyed `foundation/advanced/expert`; wire or delete `treasury_floor/bailout_amount/npc_max_fine/natural_decay_rate`; cap the regulator fine `min(fine, npc_max_fine)` and scale by trailing revenue; read `supply_chain_transparency`; evaluate `ethical_ai_overhaul` via `_collect_all_flags`. Tests: a sovereign-debt swan at R4 leaves revenue_base restored at R4+duration; `foundation` ≠ `advanced` impact multiplier. Goldens: unaffected (no swans in the traces — assert).

### WP-24 · Flags and promises — FLAG-2/3/4/5/9/10, VAL-05/07/08/09, SOC-3/4/7 · 8 h + 3 h verify
- FLAG-2: `round_logic._apply_option_flags` returns early when `events.get("pillar_cost_applied") is not None` (multi_toggles no longer inherits the proxy option's flags). Test on multi_toggles: omitted R5 area → no `insurance_only`.
- FLAG-3: `engine.py:4424-4427` feeds `ctx.events["pillar_flags"]` and the legacy option's `flags_set` to the sentiment engine. Test: `renewable_ppa_signed` produces its narrative.
- FLAG-4: flatten with `_collect_all_flags` before the status test (`terminal_valuation.py:690`).
- FLAG-5: consume `adj_severity` in R6+ crises or remove the "adaptive severity" copy (`consequenceCatalog.js:1604`) and the branch modifiers.
- FLAG-9: write `greenwashing_detected` (or rename the five readers to `greenwashing_scandal`); add `greenwashing_scandal` to `_BETRAYAL_FLAGS` (SOC-4) and the Fortress-Premium exclusion set.
- FLAG-10: reconcile the seven text/number contradictions (strike 75%→50%; +0.35→0.30; "over 3 rounds" ×2 → per-round pending projects via `_process_pending_projects` `per_round` support; NCD forgiveness term or text; R5 "Round 7/8"; teleprompter $).
- VAL-05: add `workforce_readiness`, `pillar_effectiveness_modifier` to `ENGINE_STATE_KEYS` (`engine.py:4483`); finale reads it. VAL-07: Divest → `synergy_multiplier = 0.0` or snapshot pre-wipe for `calculate_mr`. VAL-08: pass `baseline_ci` at `round_logic.py:2631`. VAL-09: `_solvent = _dmav > 0 and equity_value >= 0`.
- SOC-3: capture `rep_at_tick_start` before `reconcile_reputation_stock` (`engine.py:4705-4709`); fix `TestF08` to a state with a positive reconciliation. SOC-7: build greenwash messages from `_claim_level`/threshold/`avg_capex` (`engine.py:3992-4012`).
- Tests: `flag/flag_sweep.py` becomes `tests/test_flag_sweep.py` with a ratchet on inert-core-flags (31 → 0 unruled) — replaces the blind `test_flag_taxonomy.py` (fix BOM handling and the `frontend/src` path).
- Verify: `flag/probe_*`, `soc/p5`, `p9`, `p12`, `val/probe_readiness.py`, `probe_synergy_wipe.py`, `probe_solvency_axes.py`; goldens may move (VAL-05 changes readiness → SLO paths in multi_toggles) — rebaseline with delta.

### WP-25 · Config importer and hot reload — CFG-04/05/06/08 · 4 h + 1 h verify
- `config_excel.py`: range validation (negatives only on an allow-list; `*_rate|*_ratio|*_fraction` in [0,1]); merge instead of wholesale replace (or export the sheet with every key); regenerate `simulation_config.xlsx` via `config_excel.py export` and add `tests/test_config_excel_sync.py` (round-trip value-identical). Hot reload: `router.py:2756, 5962`, `dry_run.py:186` read `config.DEFAULT_IMITATION_DECAY_RATE` at call time; `admin_shared.py:316-317` seed overrun tunables from config. Provenance sidecar: fix the five non-existent keys or delete the file.

### WP-26 · Tenancy and persistence of admin edits — ACC-4, ACC-6, OPS-2, OPS-5, OPS-6 · 4 h + 1 h verify
- `reset_player_password` asserts cohort ownership; pillar-overrides write via `runtime_paths.data_file()` with a one-time seed from `backend/db/` and `require_super_admin`; cohort-wide undo skips the shell and the UI derives `currentRound` from the children; stakeholder-map resubmission returns the stored result; player token carries `pw_version`.

### WP-27 · BRSR routing — VAL-06 · 2 h + 2 h verify
- `router.py:2907` passes `decision_paradigm=paradigm` to `post_tick`; `/round-config/{n}` gets a brsr branch (`router.py:4015-4022`); `tests/test_brsr_paradigm.py:14-16` creates with `brsr_ngrbc`, not `legacy_abc`; the five-paradigm smoke's brsr `xfail` is removed. Until then: do not create brsr cohorts.

### WP-28 · Documentation drift — SOC-8, CFG-09, OPS-7, FIN-14, VAL-11d/e, teleprompter strings · 3 h
- `engine.py:794-795`, `config.py:636, 589-592, 489-492`, `config_excel.py:200-203`, `REPORT_launch_readiness_2026-09-03.md` addendum, `MODEL_CARD.md:152-153` (fatigue), `SIMULATION_CONTEXT.md:783-784, 850, 886, 891, 898`, `TechnicalGlossary.js:75, 194-197, 240-242`, `admin_analytics.py:865, 867`, `admin_teleprompter.py:459, 1616-1626`, `sidebarConfig.js:163`, `PlayerRegistry.js:264`, `init.sql:129-165` trigger, the facilitator manual's health-endpoint sentence, `SETUP_STEPS.md:82` branch, DEPLOYMENT_CHECKLIST.md multi-worker note (`MURESSONS_MULTIWORKER_VERIFIED`), `_PARADIGM_NORMALIZATION.max_mr`, `terminal_valuation.py:288` `max_achievable_mr` per paradigm.

**Wave 2 acceptance gate.** Both goldens rebaselined once, with a `DELTA_` note listing every moved number and its cause; `scripts/balance_report.py` regenerated; five-paradigm smoke including brsr; the full probe set green; flag sweep ratchet at 0 unruled core flags.

---

## Wave 3 — Debt (no bearing on this deployment) · ≈ 3 developer-days
FIN-04 (no persisting tick on GET), FIN-05 (emergency credit: credit the $1M with a term or delete the interest; align the $5M/$25M thresholds), FIN-06 (extend `run_deterministic_simulation` to the full pipeline; move `engine.py:4163-4169` after :4750; add `brsr_ngrbc`, drop `un_sdg` from `test_treasury_waterfall._PARADIGMS`; render the waterfall or fix the teleprompter), FIN-07 (RE bridge residual diagnostic; drop the unconditional `balanced: True`), FIN-11/12/13 (loan-rate seeding from config; dividends `setdefault`; R10 loan draw interest/repayment; insolvency consequences consumed), FIN-15 (calibration: CapEx lever proportionality — a design workshop, not a patch), IMP-10 (social tipping `_below` keys), IMP-12 (regional report reads `absolute_emissions`), IMP-13/14/15/16/17, RNG-2 (two-location seed write; wizard omits blank `rng_seed`), RNG-4 (replay through the full pipeline), RNG-5 (seed the CEO fallback), RNG-6/8, SEAM-12 (peer benchmarking filtered by cohort), SEAM-14 (currency rate on projected surfaces), SEAM-15/16/17, OPS-4 (strict health checks DB), FLOW-05 (debounced autosave + `beforeunload`), FLOW-06 (Last Round Summary fields; results screen after reload), FLOW-07/08/10/11, ACC-5 (projector JWT refresh), VAL-10/11 hygiene bundle.

---

## Cross-cutting

**Golden-trace protocol.** Rebaseline only in WP-07 (R10 figures), WP-21 (per-BU decay) and WP-24 (readiness) — one rebaseline per wave, never mid-wave, each with a `DELTA_<wave>_<date>.md` that lists every moved number, the WP that moved it and why. `git diff --stat` on `tests/golden/*.json` must be empty in every other commit.

**Test-harness debts to pay in the same wave as the code they guard.** `test_universal_math_engine.run_deterministic_simulation` → full pipeline (Wave 3 / FIN-06); `test_treasury_waterfall._PARADIGMS` → `config.VALID_DECISION_PARADIGMS` (Wave 0, trivial); `test_mr_single_arbiter` list-flag case (WP-14); `test_flag_taxonomy` → `test_flag_sweep` (WP-24); `test_admin_route_guards._MAX_UNTENANTED` ratchet (WP-10); `test_launch_audit` F-05 router-path case (WP-11); `test_config_introspect` clamp case (WP-20); `test_brsr_paradigm` real paradigm (WP-27); `test_five_paradigm_smoke` (step 0.3).

**Verification matrix (run by `scripts/verify_wave.sh` at the end of every wave).**

| Check | legacy_abc | multi_toggles | advanced_climate | healthcare | brsr_ngrbc |
|---|---|---|---|---|---|
| 10-round smoke, advanced + expert, no engine failures | ✓ | ✓ | ✓ | ✓ | xfail until WP-27 |
| Identical teams → identical state (WP-02) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Conservation inside `process_tick` (`fin/law_all_paradigms.py`) | ✓ | ✓ | ✓ (CBAM R3/R7) | ✓ | ✓ |
| Seam compare, final + mid-game (`seam/compare.py`) | ✓ | ✓ (pillar summary, not letters) | ✓ | ✓ | ✓ |
| Preview == finale M_R (`val/probe_preview_vs_finale.py`) | ✓ | ✓ (+ `hr_invested_r*`) | ✓ | ✓ | ✓ |
| Flag promises (`flag/probe_deferred.py`, `probe_phantom_proxy.py`) | ✓ | ✓ (FLAG-2 case) | — | — | — |
| Golden traces | ✓ | (stakeholder trace is legacy) | — | — | — |
| Access sweep (`acc/sweep_noauth.py`, `probe_isolation.py`) | paradigm-independent, run once | | | | |

**Deployment and rollback.** Each wave deploys as one push after the gate; Railway keeps the previous deployment for one-click Redeploy (schema is additive, so an older image tolerates new columns — untested, keep a DB snapshot before Wave 2). Wave 0 deploys before class; Waves 1+ never mid-cohort (a push restarts the container: in-flight commits fail with a readable 503, pacing survives, tokens survive — verified in OPS §B).

**Facilitator track (in parallel, no code).** Slide 1 password recipe (until WP-01 ships); Round Pacing → Manual after creating each cohort (until WP-09); projection rules from the runbook (until WP-04–07/13 ship); cohort toggles OFF for biodiversity/TCFD/mirror/ladder/ribbon/journey panels (until WP-22); no `brsr_ngrbc` cohorts (until WP-27); rehearsal with three test players after every deploy.

**Effort summary.** Setup ½ day · Wave 0 ≈ 1.5 days · Wave 1 ≈ 3 days · Wave 2 ≈ 5–6 days · Wave 3 ≈ 3 days. Verification is ~40% of each wave and is not optional: three of the seven prior "fixed" claims in the ledger were not.

**Open decisions for the owner before implementation starts.** (1) WP-12: which single price for a negative treasury (engine debt service at CoC/2 per round is recommended). (2) WP-06: engine-only counterfactuals now vs full-pipeline shadow (2× commit cost) later. (3) WP-15: rescale shares (6.5M) vs re-price IPO ($3.3). (4) WP-21: supply the stored decision export so the tiers can be re-measured per BU; otherwise keep 0.15/0.20/0.30 and say so. (5) WP-22: fix the four display engines or retire them for this cohort. (6) WP-10: is the R2 matrix rubric meant to be transparent to players?
