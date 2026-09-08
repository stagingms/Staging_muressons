# Wave 1 — Implementation Report (2026-09-05)

Branch `fix/audit-remediation-20260904`, HEAD `936a8ff` (Wave 0 ended at `3fc618d`).
Plan: `PLAN_Audit_Remediation_2026-09-04.md`, WP-11 … WP-20. Eleven commits, 67 files, +3,581 / −583.
Nothing was pushed; `main` and `production` are untouched; production was never contacted.

## Commits (one per WP, tests in the same commit; each new test file shown failing on the previous commit via stash/pop)

| # | Commit | WP | Findings | New / changed tests |
|---|---|---|---|---|
| 1 | `850c0bb` | WP-11 CapEx term loan on the statement | F-12 | `test_capex_loan_on_statement.py` (5) — loan and interest on the balance sheet and P&L through the router; two scorecard rows + BalanceSheetModal row |
| 2 | `81b44bd` | WP-12 negative-treasury price, floor where treasury is written | F-13, FIN-10 | `test_floor_after_engines.py` (7); `test_balance_sheet_after_engines.py` tightened; `test_treasury_waterfall.py` gains `brsr_ngrbc`. Brain-drain penalty capped (`BRAINDRAIN_PENALTY_CAP` 1.30); post-tick floor clamp + covenant surcharge floored. **Financial golden rebaselined**: R9 218,627,880.89 → 219,924,487.24, R10 247,756,157.19 → 249,052,763.54 (+1,296,606.35 = one R9 talent premium above the cap; verified by re-running with the cap disabled == old golden) |
| 3 | `e7cc491` | WP-13 awarded terminal value on projector / God-Mode leaderboard / grading CSV | F-14, SEAM-13 | `test_leaderboard_awarded_tv.py` (3); rows carry `terminal_value_source`, `price_per_share`, `equity_value`, `regenerative_multiple`, `archetype` |
| 4 | `0ab8b92` | WP-14 M_R projections read the flags the finale reads | F-15 | `backend/flag_utils.py` (one flag reader for preview, DNA, What-If, finale); `test_mr_projection_reads_list_flags.py` (8); `test_mr_single_arbiter` gains the engine==arbiter case; `mr-journey-arbiter.test.js` (7) |
| 5 | `c2e1059` | WP-15 reveal scale and units | F-20 | `shares_outstanding` 100,000,000 → 6,500,000 (JSON, config default, patcher, two frontend engines); NCD line is a priced liability (`ncd_liability_usd` = points × $/pt × exit multiple) deducted from DMAV; `test_reveal_scale_and_units.py` (4), `reveal-scale-units.test.js` (3), `test_share_price_floor.py` reworked, MODEL_CARD rows |
| 6 | `b4798b2` | WP-16 patience clock arms from the first hostile-ish tier | F-16 | `PATIENCE_ARMS_FROM_TIER = 2`; `test_patience_clock_arms_from_hostile.py` (4); stakeholder golden re-fixtured. **Financial golden rebaselined**: the golden game was itself being forced by the clock — treasury R6 +828,275 … R10 +5,767,793 (249,052,763.54 → 254,820,556.69); terminal snapshot unchanged; verified by regenerating with tier 1 == previous golden bit for bit |
| 7 | `ad7be88` | WP-17 timed auto-commit through the real commit path | OPS-1 | `_auto_commit_player` deleted; `_scheduled_unlock_task` → `router._auto_commit_laggards` (clears the commit cooldown); `test_timed_autocommit_path.py` (3) |
| 8 | `2479f84` | WP-18 free-mode barrier server-side; pacing chip polls the cohort; auto-commit banner | F-18(ii, iii) | 403 `waiting_for_teams` for a team ahead of the slowest sibling in free mode (fails open); `roundLockReason` in `useSimulation`; `DecisionPressureTimer` resolves the parent cohort's pacing; `test_free_mode_barrier.py` (3), `free-mode-barrier.test.js` (4) |
| 9 | `66ec477` | WP-19 history and analytics integrity | SEAM-08/09/10/11 | `backend/history_semantics.py`; the R10 commit stashes the entering-R10 row, both stores splice it back (row K = state entering K, uniformly) and append the closing state as round 11 `is_final` on request; every consumer updated (see below); board pressure before persistence; live DNA at the session round; prediction r ↔ round r; `test_history_semantics.py` (10); `front-page-newspaper.test.js` rewritten to the convention (29) |
| 10 | `cc6421f` | WP-20 config observability + runbook | CFG-02/03, OPS-3/4 | `CONFIG_CLAMPS` ledger; `/config/live` reports `clamped_value` (high) and `image_vs_volume` (medium), demotes inert tunables to `advisories`; boot log `[config] …` lines; `/health` carries a `config` block and `storage.mounted`; `?strict=1` runs `SELECT 1` (2 s) → 503; DEPLOYMENT_CHECKLIST §2/§5/§5b, PREDEPLOY Layer 4; `test_config_introspect.py` (+5), `test_durable_storage.py` (+3), `test_health_strict_db.py` (5), `config-live-status.test.js` (+2) |
| 11 | `936a8ff` | gate hygiene | — | three suites that pinned pre-Wave-1 behaviour re-pinned (brain-drain cap, DMAV with NCD liability, free-mode barrier in the pacing tests, single auto-commit builder) |

## Verification gate (HEAD `936a8ff`, memory store, `~/audit_scratch/env.sh`, all five paradigms)

| Check | Result |
|---|---|
| Backend `pytest backend/tests` (8 Wave-0 slices + 20 new files, `-n 2`) | **2,558 passed, 15 skipped, 0 failed** (Wave 0: 2,497) |
| Frontend `jest` (51 suites, 6 chunks + 3 new) | **1,134 passed, 4 skipped, 0 failed** (Wave 0: 1,115) |
| Five-paradigm × two-tier smoke (`test_five_paradigm_smoke.py`) | 10/10 |
| Golden traces | financial rebaselined twice with stated deltas (WP-12, WP-16 — each verified causal by regenerating with the old value); stakeholder golden unchanged in WP-12, re-fixtured in WP-16; `test_mr_single_arbiter` AST tripwire green |
| `fin/full_run_probe.py` + `fin/recon_full.py` (advanced tier, 5 paradigms) | `A−L−E` max 0.00; `cash_bad = 0` (cash == max(0, treasury) on all 50 statements); CapEx loan on the balance sheet on all five (`bsLoanMax` 2.95M–4.0M, == `flags.capex_loan_balance` where outstanding at R10); commit response == stored state (gap 0.00); no engine failures. Waterfall / RE-bridge residuals remain (FIN-06 / FIN-07, deferred by the plan) at the pre-Wave band |
| `val/probe_preview_vs_finale.py` (384-state grid) | **0 divergent** (audit: 370) |
| `seam/` replay on a fresh cohort (alpha balanced 0.4, beta profit 0.15, gamma green 0.6 → `pull.py` → `compare.py`) | mid-game: analytics `decision_impact` R5 and the admin debrief R5 row equal the commit deltas (−24,407,286.42 / +43.97, `option_b`); final: dashboard, final-report, `flags.final_treasury`, balance-sheet cash, peer leaderboard, admin leaderboard, analytics and debrief narrative agree on the closing treasury and reputation for alpha (62,656,262.53 / 55.27) and beta (−142,328,194.32 / 0.0); `dna current_round` live == snapshot == dashboard (10/10/10, was 1/10/10); `seam/pred_probe.py`: the R5 prediction pairs with R5's actual (−23,539,230.91 / +43.97). Rows still apart are all deferred findings: `consequence_waterfall.final_treasury` (FIN-06), revenue-weighted CI (SEAM-15), `final-report.terminal_valuation` null (VAL-11) |
| `soc/p10_patience_cost.py` (12 seeds, even production-chain team) | hostile actions F4 ON 0.3 (audit 3.5), R10 reputation within 1.0 of F4 OFF |
| `ops/probe_timed_autocommit.py` | flag keys missing after auto-commit **0** (audit 26); saved allocations retained; R10 auto-commit ends the game (history 10 rows, profile stamped, later commit → 409 completed, final report 200) |
| `flow/probe_flow.py` | A3 (R2 commit while a sibling is on R1, free mode) → **403 `waiting_for_teams`** (audit 201); manual/timed/free transitions as before |
| `cfg/probe_config_live.py` | stale volume: 2 × high `clamped_value` (ratchet baseline 10 → 20, imitation 0.1 → 0.05) + medium `image_vs_volume`, `healthy: false`; patched volume: `healthy: true`, 16 advisories; boot log prints `[config] volume differs from image on N keys` / `[config] CLAMPED …` |
| `acc/sweep_noauth.py` (361 routes) | no-credential 200s 46 → 46; nothing newly open, nothing newly closed |
| `/health` | `storage.mounted` / `mount_point` present; `?strict=1` on the memory store `database_reachable: true`; fake unreachable Postgres → 503 with `database_error` while the plain endpoint stays 200 |

## Deviations from the plan (stated in the commits)

1. **WP-19** went further than the four SEAM rows because the new convention exposed every "latest = hist[-1]" reader: peer leaderboard, cohort pulse, situation-room bulletin, session report, complexity-event feeds, export-my-data, cohort analytics all now read with `include_final=True` (a finished team ranks on what it ended on; `display_round` reports it as round 10 / finished, never "11"; event feeds are labelled by the round whose commit produced the row). The frontend `keyInsights` ledger (game-over "three key insights", newspaper decision ledger) was reading row K as the CLOSE of K — every delta was the previous round's outcome under this round's call, round 1 printed "no change" and round 10's result never appeared; it now attributes row K+1 − row K to round K and takes the closing state from the game-over `globalState` / the report's `final_treasury`.
2. **WP-20** `image_vs_volume` is a *medium* problem (the audit's minimal fix) rather than an advisory: a deliberately tuned volume will read as a problem naming its keys — the message says so — because the same signal on a stale volume is the one the class needs. It already earned its keep: the audit's "clean" scratch volume, seeded before WP-15, differed from the image on `terminal_valuation.shares_outstanding` (100,000,000 vs 6,500,000) — a 15× share-price error no clamp guards.
3. **WP-20** OPS-3: `durable` on Railway now also requires the data dir to be on a mount of its own; when `/proc/mounts` is unreadable `mounted` is `null` and the old reading stands (an unknown is not a verdict). `test_durable_storage` re-pinned accordingly.
4. **CFG-09** (deferred) got one line in passing: the `slo_ramp.min_abs_capex` clamp message said "using 500,000" while the code set 100,000.
5. `SETUP_STEPS.md` is gitignored, so the CFG-07 secrets removal is a local-file change only (not in any commit); no secret value appears in any commit, log, or this report.

## Residual observations (for the wave that owns them)

- Seam rows still apart, all on the plan's deferred list: `events.consequence_waterfall.final_treasury` (FIN-06, waterfall frozen before the last entries), carbon-intensity BU mean vs revenue-weighted (SEAM-15), `/final-report.terminal_valuation` always null (VAL-11), `sdg_impact_score` 0 alongside `group_sdg_score` (VAL-11 bundle).
- `fin/recon_full.py`: waterfall residual and RE-bridge residual are unchanged in kind (FIN-06 / FIN-07); the balance sheet balances by construction (`balance_sheet_balanced` hard-coded — FIN-07).
- `/config/live` `god_mode_shadowing` and the 16 inert tunables (CFG-08) are unchanged — now reported as advisories.
- `cohort-pulse` heat-map cells R1..R10 are the states ENTERING each round (as they always were for R1..R9); the closing state is in the `current` columns and `finished: true`.
- Volume patcher: `backend/patch_volume_config.py` covers 12 keys incl. `shares_outstanding`; the runbook's inspect one-liner prints `shares`.
- Carried from Wave 0: `consequence_dna_snapshot.flag_nodes` stringified into the R10 flag namespace (WP-24 territory); `_apply_pacing` `next_unlock_at` may be a past entry; cohort creation idempotent by name; `test_durable_storage::test_off_railway_repo_dir_is_durable` intermittently red on this mount (green in this run).

## Before class (owner)

1. Push the branch; point Railway's Source at it; `GET /api/health` `.build.commit` shows `936a8ff`.
2. Boot log (DEPLOYMENT_CHECKLIST §5): `[storage] … mounted=True … durable=True`; **no `[CONFIG] WARNING`, no `[config] CLAMPED`**, `[config] volume config matches the image copy`. If not: §5b — inspect, `python3 /app/backend/patch_volume_config.py`, restart, re-check; then `GET /api/admin/config/live` as super-admin must read `"healthy": true`.
3. Point the uptime monitor at `/health?strict=1` (now also a database check).
4. Runbook pre-flight as in the Wave 0 report, plus: on a two-team free-mode cohort, team A commits R1, team A's R2 shows "Waiting for other teams" (server-enforced), team B commits R1, both proceed; end a game and confirm the leaderboard, the newspaper ledger (ten rows, round 10 with its own change) and the debrief R9/R10 deltas agree with the last two commits.
