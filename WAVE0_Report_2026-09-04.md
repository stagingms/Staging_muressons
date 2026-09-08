# Wave 0 — implementation and verification report

**Branch** `fix/audit-remediation-20260904` (off `d3bbf09`; 13 commits; `main` / `production` untouched; nothing pushed).
**Plan** `PLAN_Audit_Remediation_2026-09-04.md` · **Audit** `AUDIT_Engines_Flow_Classroom50_2026-09-04.md`.
**Diff** 58 files, +2923 / −175.

## Commits (one per work package; tests in the same commit)

| # | Commit | Work package | Audit finding | New/changed tests |
|---|---|---|---|---|
| 1 | `c07b367` | 0.3 five-paradigm smoke | — | `test_five_paradigm_smoke.py` (10: 5 paradigms × advanced/expert, incl. `multi_toggles` with pillar decisions) |
| 2 | `08cbc6b` | WP-02 seed forward | F-04 / RNG-1 | `test_seed_reaches_post_tick.py` (4) |
| 3 | `8b55bd8` | WP-03 ratchet clamp + patcher in image | F-07 / CFG-01 | `test_launch_audit_2026_09_01.py::TestRatchetBaselineBound` (5) |
| 4 | `bbbeff0` | WP-04 debrief attribution | F-02 / SEAM-01 | `test_debrief_decision_attribution.py` (2) |
| 5 | `cf08b24` | WP-06 counterfactual baseline | F-06 / SEAM-04 | `test_regret_analysis.py` (2) |
| 6 | `601f8aa` | WP-08 desalination payback | F-05 / FLAG-1 | `test_pending_projects_mature.py` (2) |
| 7 | `a74a485` | WP-05 reputation 0 ≠ 50 | F-03 / SEAM-02/03 | `test_reputation_zero_is_a_value.py` (4), jest `reputation-zero-idiom` tripwire |
| 8 | `42131f1` | WP-07a finale re-stamp + reveal state | F-08 / SEAM-05/06 | `test_finale_consistency.py` (3) |
| 9 | `20eb5f9` | WP-07b balance sheet after engines | F-08(b) / FIN-02 | `test_balance_sheet_after_engines.py` (2) |
| 10 | `3fbcde6` | WP-09 wizard pacing enforced | F-18(i) / FLOW-02/11 | `test_wizard_pacing_enforced.py` (9), jest `wizard-pacing` (5), `test_pacing_midrun` pin moved |
| 11 | `32495bd` | WP-10 answer-key leaks + analytics guard | F-10 / F-11 | `test_answer_key_leaks.py` (31), route-guard ratchet 58 → 45, jest `materiality-panel-commission` (4) |
| 12 | `a3dc761` | WP-01 forced change-password screen | F-01 (P0) | jest `forced-password` (5), `test_first_login_password_gate.py` (1), ui-budgets 37 → 38 |
| 13 | `3fc618d` | 0.4 `scripts/verify_wave.sh` | — | — |

Every new test file was shown to fail on the commit before its fix (stash / pop), then pass after.

## Verification gate (HEAD `3fc618d`, memory store, `~/audit_scratch/env.sh`)

| Check | Result |
|---|---|
| Backend `pytest backend/tests` (8 slices + 10 new files, `-n 2`) | **2497 passed, 15 skipped, 0 failed** |
| Five-paradigm × two-tier smoke (`legacy_abc`, `multi_toggles`, `advanced_climate`, `healthcare`, `brsr_ngrbc`) | 10/10 pass — no `engine_failures`, finale keys present, M_R in [0, 2.05], `current_round == 10` |
| Golden traces (financial + stakeholder) | unchanged, pass — **no rebaseline needed** (the traces pin the engine pipeline; the R10 re-stamp moves only the persisted router state) |
| `test_mr_single_arbiter` AST tripwire | pass |
| Frontend `jest` (48 suites, 6 chunks) | **1115 passed, 4 skipped, 0 failed** |
| `flow/probe_pwchange.py` | 403 `password_change_required` on map / save-decisions / commit / materiality with the issued password; change-password 200; save-decisions 200 after; re-login `must_change_password=false` |
| `rng/probe_diverge.py` (3 identical teams, R1–R4) | only `cohort_team_count` / `team_commits_this_round` differ — identical state |
| `flag/probe_deferred.py` (R1b…R8c…R10a) | R10 `capex_project_completed` carries "Desalination Plant Revenue Generation" 5,000,000; `revenue_generation_completed` 7.83M (≥ 5M) |
| `seam/` replay (alpha balanced 0.4, beta profit 0.15, gamma green 0.6 → `pull.py` → `compare.py`) | final treasury/reputation agree across dashboard, final-report, `flags.final_treasury`, balance-sheet cash, peer/admin leaderboards, analytics, debrief narrative (95,691,195.58 / 53.62 for alpha; R10 commit response = persisted); admin debrief R5 row now `option_b · Nature-Based Solutions` with capex (was blank) |
| `flow/probe_wizard_pacing.py` | manual up to R1 → R1 201, R2/R3 403; scheduled → R2 403, schedule + timers persisted; free_play → R1–R3 201 |
| `acc/sweep_noauth.py` (361 routes) | no-credential 200s **57 → 46**; the eleven reference/answer-key routes now 401; nothing newly open; `materiality-config` 5413 → 4318 bytes with no `financial_impact`; `r6-revelation` 1763 → 1342 with no `impacts` |
| `acc/probe_analytics_player.py` | forged header 401; other player's token 403; other-cohort facilitator 403; owner 200; project_admin 200 |

## Deviations from the plan (stated in the commits)

1. **WP-06** — the counterfactual shadow runs `post_tick` as well as `process_tick` (decision 2 of the plan): option effects live in post_tick, so an engine-only shadow read 0/0.
2. **WP-10** — `panel_recommendations` are not simply dropped from the player projection: they are the paid hint mechanic (`experts` is always correct). They moved to `POST /api/simulations/{sid}/materiality/commission-panel` (owner-bound, one group per call, recorded on the session so the fee is charged at submission even if the client lists nothing). `GET /journey/r6-revelation` is projected rather than gated because the player cockpit renders it at R6 (the audit's pass (c) missed that consumer). `/teleprompter/{round}/{paradigm}` was gated too (same content class, not on the audit's list).
3. **WP-09** — `POST /cohort/{id}/apply-setup`'s pacing section goes through the same enforcement helper; the wizard now sends UTC ISO times (datetime-local values were naive and treated as UTC).
4. **WP-01** — the modal is an architectural early return (same pattern as the username/briefing screens), not an OverlayHost slot; ui-budgets baseline raised 37 → 38 with the reason recorded.

## Residual observations (not Wave 0; for the wave that owns them)

- `active_event_flags["consequence_dna_snapshot"]` (R10) contains `flag_nodes` dicts that `_collect_all_flags` stringifies into the flag namespace after game over — cosmetic at R10, but it is namespace pollution (WP-24 flag sweep territory).
- `_apply_pacing` publishes `next_unlock_at` as the first non-empty schedule entry even when it is in the past (pre-existing; the countdown shows a past time until the first future unlock fires).
- The cohort-creation endpoint is idempotent by `cohort_name`; scratch probes that reuse names pick up restored cohorts from the snapshot (the wizard-pacing probe was given unique names for this reason).
- Baseline env artefact still applies: `test_durable_storage.py::test_off_railway_repo_dir_is_durable` is intermittently red on this mount (passed in this run).

## Before class (owner, from the plan's WP-D0)

1. `scripts/verify_wave.sh` on the branch (≈15 min with jest). 2. Push the branch; point Railway's Source at it; `GET /api/health` `.build` shows `3fc618d`. 3. WP-03 ops: `railway ssh -- python3 /app/backend/patch_volume_config.py --dry-run` then without `--dry-run`. 4. Volume mounted at `/data`. 5. Runbook pre-flight 3–6, including: logged-out `GET /api/admin/teleprompter` → 401; three test players sign-in → forced password screen → R1 map → R1 commit → R2 matrix (commission one panel, see its badges) on a **Manual, up to R1** wizard cohort and confirm R2 stays locked until Unlock.
