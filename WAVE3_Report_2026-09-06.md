# Wave 3 — Implementation Report (2026-09-06)

Branch `fix/audit-remediation-wave3-20260906`, HEAD `0ad1246` (off `8d21fc4`, the deployed Wave 2 head).
Plan: `PLAN_Audit_Remediation_2026-09-04.md` § Wave 3 "Debt (no bearing on this deployment) · ≈3 dev-days", plus the two
Wave 2 gate residuals. Fourteen commits, ~70 files, +3,100 / −260.
Nothing was pushed; `main` and `production` are fast-forwarded locally to HEAD (below); production was never contacted.

## Commits (one per finding group, tests in the same commit; each new test shown failing on the previous commit via stash/pop)

| # | Commit | Findings | What changed | New / changed tests |
|---|---|---|---|---|
| 1 | `4a38cc6` | FIN-06 | the consequence waterfall is a **closed bridge from opening treasury to the treasury the round persists**: every in-tick treasury write is an entry (regulatory ratchet fine, CBAM, offsets, L&D levy, adaptation, SDG retribution, black-swan direct hit) with a named residual "Unattributed in-tick movement"; `run_new_engines` marks its 18 sections and `waterfall_bridge` appends one step per post-tick mover (pillar costs, option treasury, post_tick, each engine, resync); the cockpit waterfall renders the bridge, and the teleprompter's "EXACTLY how treasury moved" is true | `test_waterfall_closes_on_stored_treasury.py` (8: 5 paradigms × 10 rounds, `unattributed == 0.0`, `final_treasury == stored`), `treasury-bridge.test.js` (5) |
| 2 | `ace604c` | SEAM-14 | DebriefNarrative, DebriefReport, projector, trading floor, MarketTicker format money through `utils/format` at the cohort's symbol and rate (`loadSessionCurrency` per surface) | `projected-surfaces-currency.test.js` (8) |
| 3 | `91a34b8` | SEAM-15 | carbon intensity on the display surfaces (cockpit, benchmarks, session report, analytics) is the group's revenue-weighted tCO₂e per $M; the benchmark badge names its static FTSE table | `test_seam_display_units.py` (3), `ci-revenue-weighted.test.js` (2) |
| 4 | `2bdf85f` | FLOW-05, FLOW-06 | the draft autosaves 2 s after a change and on `beforeunload`/`pagehide`/hidden (keepalive); the 30 s interval is gone; the results screen survives a reload (`muressons_pending_results_<sid>`, cleared on advance/logout); the Last Round Summary reads the real history row | `draft-and-results-survive-reload.test.js` (9) |
| 5 | `9c091fd` | VAL-11a/c/f/g/h, VAL-10 | HR uplift on the real TV formula (`ebitda × multiple × M_SDG × M_R`); hostile-takeover cap as a breakdown line; BRSR dividend as a value; `/final-report.terminal_valuation` derived from the canonical record; the front page's "hollow" band; the Titan caveat and the instability-discount source on the teleprompter | `test_val11_hygiene.py` (6) |
| 6 | `dbfbf33` | FIN-05, FIN-04 | the **emergency credit line is a real facility**: drawn once into cash at the $5M trigger the cockpit announces (server trigger `treasury × CSF_POOL_TREASURY_FRACTION < FINANCIAL_EMERGENCY_CREDIT_AMOUNT`, was the $25M pool floor), interest on the outstanding balance only, repaid when the treasury clears the trigger or at R10, a current liability on the statement, a ledger term in the conservation law, a waterfall entry; the cockpit banner says which state it is in. `GET /balance-sheet` before the first commit is a **preview on deep copies** and persists nothing (R1 was depreciated twice) | `test_emergency_credit_and_bs_preview.py` (7); `test_treasury_waterfall._residual` and the UME ledger carry the two new terms |
| 7 | `06483ca` | FIN-07, FIN-11, FIN-12, FIN-13 | **RE named as the plug**: the identity is checked, not asserted; `bs.re_bridge` (opening / NI / dividends / expected / closing / residual) on the statement, the history row and the diagnostics; the cockpit statement, history table and modal print "Retained Earnings (closing residual)" and the bridge residual. **Config reaches the loan rate** (solo start, `/start` model default_factory, sweep fallback, both reset fallbacks). **The statement records the dividend actually paid** (`setdefault`). **Insolvency consequences apply**: last round's `capex_cap_multiplier` (insolvency notice, financial tipping, turnaround stabilisation) caps CapEx; `dividend_suspended` (and the turnaround crisis/stabilisation) zeroes the dividend; the verdict flags are written every tick so they clear; **the R10 draw is priced and repaid in the round** (`capex_loan_balance` 0 at R10). Not applied on purpose: the turnaround crisis phase's 0.0 cap — the pool floor is the minimum loan-funded investment path | `test_fin_hygiene_wave3.py` (10), `re-bridge-rows.test.js` (2) |
| 8 | `f1387d5` | IMP-10, IMP-12, IMP-14, IMP-15, IMP-16, IMP-17 | social tipping tests **low** licence (`avg_slo_below`); the Regional ESG Report sums `absolute_emissions` (was a key nobody wrote → 0 tCO₂e GREEN); turnaround injections and the entry bailout are **rescue financing carried as debt** in the re-valuation (graduation gates untouched); the pillar-mode R9 clawback is real and the message says what happened; tipping penalties come from `IRREVERSIBILITY_PENALTIES`, **level shifts once** (gated by `<dim>_penalty_applied` in the persisted state, both locations), ceilings and the FIN-13 flags every round; two documented-but-dead penalties gone; `planet_expendable` defined once; the constant hectares-as-percent pill removed | `test_imp_hygiene_wave3.py` (15); `apply_tipping_penalties()` extracted so the gating is testable |
| 9 | `6397c52` | RNG-2, RNG-5, RNG-6, RNG-8 | **the typed rng_seed reaches the game**: two-location stamp (flags + top level — the store repack prefers the top-level copy) for the cohort and every team; the wizard **omits a blank box** (it sent `''` on every save, which the honoured blank would have read as "un-seed"); the CEO fallback noise is `stable_rng(session, dim)`; board vote, coalition check, sandbox whistleblower, R2 materiality BU pick and supply-chain disruption draw from `event_rng` keyed by round and subject; RNG-6 was closed by WP-23 (pinned) | `test_rng_hygiene_wave3.py` (5), `rng-seed-wizard.test.js` (1); `test_ceo_interview` injects a complete row and cleans up |
| 10 | `173b04a` | RNG-4 | **the replay verifier has a door**: `GET /api/admin/sessions/{id}/replay` (facilitator, read-only) and "🔁 Verify reproducibility" on the Round Debrief; the payload names the stages replay does not run and carries a reading guide; PARTIAL stays the expected verdict for a real run (see "Deliberately not done") | `test_replay.py` +1, `replay-verdict-debrief.test.js` (1) |
| 11 | `e5e6157` | SEAM-12, SEAM-16, SEAM-17 | peer benchmarking and what-if popularity rank against **the cohort's team sessions** (was every session on the server; a solo run's peers are itself; histories fetched for the peers only); the belt labels "Cost of Capital (corporate)" and shows the ESG-adjusted WACC that prices the exit multiple; KPI-belt chips and the BU ticker compute deltas against the **prior round's row** ("vs R{N−1}"), not this round's own snapshot | `test_seam_peer_scope_wave3.py` (1), `belt-deltas-prior-round.test.js` (2); ui-budgets debt 128 → 127 |
| 12 | `88b859f` | FLOW-08, FLOW-10, ACC-5 (FLOW-07, FLOW-11 pinned) | `expected_round` **required at the commit gate by default** (a stale bundle gets 400 "Refresh the page…", its draft safe; `REQUIRE_EXPECTED_ROUND=false` restores warning-only); the server's own auto-commit carries the round (it would have refused itself); a facilitator/god-mode freeze is `{code: "frozen", scope, message}` and the client shows it as a pause instead of retrying as "server busy"; the projector refreshes its JWT every 90 min and on focus | `test_flow_hygiene_wave3.py` (4), `freeze-and-projector-refresh.test.js` (2); `test_coordination_state` isolation fixture no longer deep-copies live asyncio handles |
| 13 | `484a2ad` | Wave 2 residuals | a black-swan modifier flag counts by **truth**, not key membership (FIN-13 now writes False-valued flags every tick); `test_r2_materiality_audit` pins one seed so B-vs-C compares decisions, not luck | `test_black_swan_semantics.py` +1 |
| 14 | `0ad1246` | gate | `test_medium_cohort_controls` follows the VAL-11c `/final-report` contract (its fixture carried a key nothing ever wrote) | 2 tests re-pointed |

Already closed before this wave and only re-verified here: IMP-13 (TCFD arithmetic) and the `tnfd_mr_bonus` relabel (WP-22), FLOW-07 reset copy + password-version bump and FLOW-11 RunBar `target_round` (WP-26), OPS-4 strict health `SELECT 1` (WP-20), RNG-6 message = deducted fine (WP-23 / FIN-09). FIN-15 (CapEx lever proportionality) is the design workshop the plan excludes.

## Verification gate (HEAD `0ad1246`, memory store, `~/audit_scratch/env.sh`, all five paradigms)

| Check | Result |
|---|---|
| Backend `pytest backend/tests` (8 Wave-0 slices + 37 new files) | **2,703 passed, 15 skipped, 0 failed** (Wave 2: 2,637) |
| Frontend `jest` (6 chunks + 17 new suites) | **1,178 passed, 4 skipped, 0 failed** (Wave 2: 1,147) |
| Production build (`next build`, the Dockerfile stage Railway runs, on the committed tree — fonts stubbed for the sandbox) | **passes** at `484a2ad` (11 routes; compiled in 42 s); `0ad1246` changes one backend test file only |
| Five paradigms × 10 rounds through the real commit path (`wave3/full_run_seeded2.py`, advanced tier, $1M CapEx/BU, option A) | 50/50 rounds committed; **waterfall `unattributed` 0.00 and `final_treasury == stored treasury` in all 50** (FIN-06 holds through FIN-05/FIN-13) |
| Seeded HEAD-vs-`8d21fc4` attribution (same `stochastic_seed`, same `shuffle_seed`, worktree of the base commit) | legacy_abc, multi_toggles, advanced_climate, brsr_ngrbc: **identical to the cent in every round** (treasury, reputation, options, fines, swans, flags). healthcare differs only once its treasury goes negative: R9 −5.14M → −5.01M (the old $140K interest on a never-credited line is gone — FIN-05), R10 −25.57M → −29.22M (the R10 term-loan draw of $4M is repaid in the round with a round's interest — FIN-13). No other paradigm draws in R10 at this ladder |
| Golden traces, `test_treasury_waterfall` fingerprints, `BALANCE_REPORT_BASELINE.md` | **unmoved** — no DELTA entry this wave (FIN-13's R10 settlement moves a run only when it borrows in R10; none of the pinned runs does) |
| `acc` — new endpoint | `GET /api/admin/sessions/{id}/replay` anonymous → 401/403, facilitator → 200, state byte-identical before/after (pinned) |
| `flow` | commit without `expected_round` → 400 + round unmoved; freeze → 503 `code: frozen`; stale-round 409 and 429 cooldown unchanged (existing suites) |

### A gate finding about the gate itself
The seeded probe used since Wave 2 (`wave2/full_run_seeded.py`) set `stochastic_seed` on the flags only — exactly RNG-2's
bug — so the store's repack silently kept each session's derived seed and the "seeded" runs were never on the same luck.
`wave3/full_run_seeded2.py` writes both locations; the attribution table above is the first truly like-for-like comparison.
Wave 2's "Why the bots got poorer" attribution used those runs: its seed-independent evidence (the `greenwashing_detected`
signature, the cascade flags, the reputation trajectories) stands; the treasury deltas quoted there were not luck-paired and
should be read as indicative, not as a measurement.

### Test-suite hygiene found by the gate (all fixed in the commits above)
- `generate_player_id` drew letters from the process-global `random`, which `dry_run`/`validation_logic` seed and the test
  harness restores per test — ids repeated across tests, and the uniqueness scan never looked at the credential registry, so a
  later `change-password` found a stale record ("Current password is incorrect"). Both stores mint from `random.SystemRandom`
  and check the registry. Order-dependent; surfaced by adding one test file.
- `test_ceo_interview` injected a store row without `session_id`/`cohort_name`/`facilitator_id`/`start_time` and left it
  behind; any later test scanning the store 500'd. Complete row, teardown.
- `test_coordination_state`'s isolation fixture deep-copied `_round_pacing`, which holds a live asyncio Task after any pacing
  test runs first — six setup ERRORs. Values copied, handles kept by reference.
- Wave 2 intermittents: `test_r2_materiality_audit::test_option_c_reduces_position_never_improves_it` compared two solo
  sessions on their own seeds (luck as well as decisions) — pinned to one seed; `test_timed_autocommit_path::…keeps_the_flags…`
  did not reproduce in nine runs — left as observed.

## Deliberately not done, and why
- **RNG-4 full-pipeline replay.** The finding's fix is the module's own: extract the commit pipeline into one pure function
  that `commit_turn` and `replay` both call. `_commit_turn_impl` is 1,200 lines coupled to cohort settings, pacing, side
  tracks, practice mode, WebSocket pushes and the store; a shadow replay through it would either duplicate the sequencing
  (the "second copy that drifts" the module warns about) or push events to live sockets. Recorded as debt; the door and the
  honest scope statement are in. Reproducibility for the class rests on the cohort seed (now actually settable — RNG-2) plus
  the recorded commit envelopes.
- **Turnaround crisis-phase CapEx freeze (cap 0.0).** FIN-13 applies the stabilisation cap (0.5) and the insolvency /
  financial-tipping cap; the crisis phase's "ALL capital expenditure frozen" stays narrative because the pool floor exists so
  an insolvent team can still make the minimum, loan-funded investment (the engine's own design note). Your call whether the
  narrative or the floor should move.
- **IMP-17 dead instruments that render nothing** — `MidGameCheckpoint` (no `setCheckpointData`), the player `RoundRecap`
  reads (`round_recap_engine` uncalled), `CalibrationReport` (fetches a scored predictions log the server does not keep;
  renders null), `sdg_score_history`/`avg_group_sdg_score` (no writer), `market_dynamics` (no importer), the
  `supply_chain_network` Scope-3 estimator (a function of visibility, unrendered). None shows a false number; wiring any of
  them is a feature build (the checkpoint needs two reads fixed first — `gs["workforce_readiness"]` top-level and
  `calculate_terminal_value` without the R10 args). Listed so nobody mistakes them for working features.
- **FLOW-08's escape hatch.** `REQUIRE_EXPECTED_ROUND` defaults on. If a room reports "Refresh the page to load the current
  client" on R1, that is a tab on an old bundle doing what it should; a hard reload fixes it. Set the variable to `false` on
  Railway only if that message appears for a tab that *is* current.

## Residual observations (for whoever owns them)
- The seeded probe's fix (above) means every prior cross-commit "seeded" comparison in `~/audit_scratch/wave2` was on
  per-session luck; the Wave 2 report's numbers for those runs are real runs, but not paired.
- `database_memory.create_session` / `database.create_session` still default `loan_interest_rate=0.12` in their own
  signatures; every caller passes the config value now (FIN-11), so the defaults are dead — left for a signature-cleanup pass.
- `financial_tipped`'s `dividend_suspended` / `capex_cap_multiplier` flags are re-asserted by `run_new_engines` after the
  engine's every-tick clear, so they persist exactly while tipped — the intended shape, noted because the two writers now
  cooperate rather than one overwriting the other.
- The tipping messages, the consequence catalogue and RoundBriefing R5's pedagogy text ("NCD costs permanently compound")
  now differ: the first two describe the code (one-off level shifts), the last describes the real-world concept. Left.

## Deploy (when you push)
`git push origin main production` from the repo; Railway builds `main`. Then the one read-only `GET /api/health`: expect
`build.branch: main`, `config.migrated` unchanged from `8d21fc4`, `volume_differs_from_image_on: []`. Nothing in this wave
touches the volume config, the schema or the persisted state shapes (new flags/keys are additive; a session in flight at the
deploy self-heals: the FIN-13 verdict flags are rewritten on its next tick, the tipping `penalty_applied` markers start on
the first tipped round after the deploy — a cohort already tipped before the deploy takes its level shift once more, on that
round, and never again).
