# Wave 2 — Implementation Report (2026-09-05)

Branch `fix/audit-remediation-wave2-20260905`, HEAD `8d21fc4` (Wave 1 ended at `936a8ff`); `f86c3ca` deployed 2026-09-06 00:33 UTC, `87b92d6` at 00:59 UTC.
Plan: `PLAN_Audit_Remediation_2026-09-04.md`, WP-21 … WP-28, plus the two owner calibration rulings (C-1, C-2) decided on 2026-09-05. Sixteen commits, 82 files, +5,099 / −975.
Nothing was pushed; `main` and `production` are untouched; production was never contacted.

## Commits (one per WP, tests in the same commit; each new test shown failing on the previous commit via stash/pop)

| # | Commit | WP | Findings | New / changed tests |
|---|---|---|---|---|
| 1 | `af3cc77` | WP-27 a brsr_ngrbc session plays the BRSR track to its own finale | VAL-06 (+ the paradigm label the router stamped as `legacy_abc` for every non-pillar paradigm, which had advanced_climate paying the legacy mid-game carbon OPEX on top of its own fee) | `test_brsr_paradigm.py` rewritten (5); BRSR finale stamps the same bridge / NCD liability / archetype / canonical record as the main finale via one helper `_equity_and_solvency`; 4 of 5 fail on `936a8ff` |
| 2 | `d767ff2` | WP-25 config importer merges and validates; template in sync; hot reload reaches the commit path | CFG-04/05/06/08/09 | `test_config_excel_sync.py` (17), `engine-tunables-inert.test.js` (2); importer overlays the volume file (omitted keys keep their value, unknown keys refused, 422 with the row list); template regenerated (208 rows, value-identical); new super-admin `GET /api/admin/config/excel`; router / dry_run read the config module at call time; 16 of 17 fail on `af3cc77` |
| 3 | `3d70002` | WP-26 admin edits tenanted and persisted | ACC-4, ACC-6, OPS-2, OPS-5, OPS-6 | `test_admin_edit_tenancy.py` (6), `undo-round-cohort.test.js` (2); pillar overrides live on the data dir (super-admin writes); cohort-wide undo treats the shell as coordinator; stakeholder-map resubmission replaces; a facilitator reset revokes the old device (`pwv`); all 6 fail on `d767ff2` |
| 4 | `a0188c1` | WP-23 black swans are flows for their duration; tier table in the session's vocabulary; regulator's fine capped | IMP-05, FIN-08, FIN-09, FLAG-8, IMP-11 (+ targeted swan percentages were never applied) | `test_black_swan_semantics.py` (9); **financial golden rebaselined** (DELTA § WP-23), 8 of 15 runner fingerprints re-pinned; all 9 fail on `3d70002` |
| 5 | `1583b06` | WP-22 display engines fixed or retired; the systemic-risk switches and cohort toggles have readers | F-19 (IMP-01/02/03/08), IMP-04, IMP-06, IMP-06b, IMP-07 | `test_display_engines.py` (14), `journey-reflection.test.js` (2); `_systemic_toggles` bag stamped by `commit_turn`, read by `systemic_toggle_on`; materiality shock is a posture-scaled one-round OPEX flow tied to the team's own matrix; R6/R7/R8 journey panels labelled reflection-only; **both goldens rebaselined** (DELTA § WP-22) |
| 6 | `4b2f2db` | WP-24 flags and promises — the model keeps what the options say | FLAG-2/3/4/5/9/10/11, VAL-05/07/08/09, SOC-3/4/7 | `test_flags_and_promises.py` (16), `test_flag_sweep.py` (5, replaces `test_flag_taxonomy.py`; ratchet `_CORE_INERT − FLAG_TAXONOMY = ∅`); four suites re-pinned to the new numbers (Divest wipes synergy, R3-B spreads NCD 5+5+5, F-08 stages reputation); **financial golden rebaselined** (DELTA § WP-24, one cause: SOC-3) |
| 7 | `2077b6a` | WP-21 natural decay evaluated on each BU's own investment ratio | F-17 | `test_natural_decay_per_bu.py` (2); **both goldens rebaselined** (DELTA § WP-21); `BALANCE_REPORT_BASELINE.md` regenerated with a history note |
| 8 | `8af1258` | WP-28 the in-repo text says what the code does | SOC-8, CFG-09, OPS-7, FIN-14, VAL-11d/e | `test_doc_drift.py` (5); `MR_PUBLISHED_CEILINGS` per paradigm (`max_achievable_mr_for` used by `calculate_mr`, the DNA API and the leaderboard normalisation — the 2.33 is gone); glossary / teleprompter / checklist / model card / context doc corrected; `simulation_config.xlsx` regenerated (values identical) |
| 9 | `56e57ad` | gate hygiene — GATE-1 | new (see below) | `test_flags_and_promises.py` +2 (18); `EconomicEngineTunables.js` colour fallback the ui-budgets lint refuses |
| 10 | `b13a72d` | DELTA ledger table | — | one row per baseline movement; the gate row moves nothing |
| 11 | `0a50652` | **C-1** a green claim is backed by the team's share of the CSF pool, not the BU average | owner ruling (see below) | `test_flags_and_promises.py` +2 (20), `green-claim-advice.test.js` (7); 8 of 15 runner fingerprints re-pinned (DELTA § C-1); goldens unmoved; `/round-config` serves `greenwash_bars`; cockpit shows the claim's backing before the commit |
| 12 | `1e907a0` | **C-2** balance report reference strategies at 50 % of the pool | owner ruling (see below) | `BALANCE_REPORT_BASELINE.md` regenerated (DELTA § C-2) |
| 13 | `af80d37` | pre-deploy check — build break | — | C-1 left an unescaped apostrophe in two glossary strings; jest never imports the glossary, `next build` (the Dockerfile stage Railway runs) failed to parse it; caught by building the committed tree before the deploy |
| 14 | `f86c3ca` | tripwire | — | `syntax-sweep.test.js` parses every file under `frontend/app` (2) |
| 15 | `87b92d6` | **CFG-10** a volume seeded by an intermediate build is migrated at boot | found live after the deploy (see below) | `config_migrations.py` (one table shared with the patcher); `config.CONFIG_MIGRATIONS` → `/api/health` `config.migrated` + boot-log lines; `test_config_introspect.py` +2, clamp tests re-pinned on unknown values with migrated twins; both new tests fail on `f86c3ca` |
| 16 | `8d21fc4` | **CFG-10** second shape — a key the image carries and the volume lacks is seeded at boot | found on the first boot of `87b92d6` | `test_config_introspect.py` +1; fails on `87b92d6` |

## Verification gate (HEAD, memory store, `~/audit_scratch/env.sh`, all five paradigms)

| Check | Result |
|---|---|
| Backend `pytest backend/tests` (8 Wave-0 slices + 28 new files) | **2,637 passed, 15 skipped, 0 failed** after C-1 (Wave 1: 2,558); `test_timed_autocommit_path::…keeps_the_flags…` was red once in the slice and green alone and on the re-run — intermittent, noted below |
| Frontend `jest` (6 chunks + new suites) | **1,147 passed, 4 skipped, 0 failed** after C-1 and the syntax sweep (Wave 1: 1,134) |
| Production build (`npm ci` + `next build`, the Dockerfile stage Railway runs, on the committed tree) | **passes** at `af80d37` (11 routes); failed at `1e907a0` on the glossary apostrophe — fixed before the deploy |
| Five-paradigm × two-tier smoke (`test_five_paradigm_smoke.py`) | 10/10 |
| Golden traces | financial golden moved in WP-23, WP-22, WP-24, WP-21; stakeholder golden in WP-22 and WP-21 — every movement attributed to its cause in `DELTA_Wave2_2026-09-05.md` (old → new per round, verified by regenerating with the old code / the single mechanism reverted); unmoved by WP-27/25/26/28 and by the gate commit; `test_mr_single_arbiter` tripwire green |
| Flag sweep ratchet (`test_flag_sweep.py`) | **0 unruled core flags**; 29 pillar choice-markers, 21 `es_*` narrative flags and `pr_containment` / `spinoff` ruled in `flag_taxonomy.py` |
| `scripts/balance_report.py` | regenerated in WP-21 (header carries the SOC-4 + FLAG-9 bisection); byte-identical after GATE-1; **regenerated again under C-2** at the realistic ratio (see the rulings below) |
| `fin/full_run_probe.py` + `fin/recon_full.py` (advanced tier, $1M CapEx/BU, 5 paradigms) | `A−L−E` 0.00; `cash_bad` 0; commit response == stored state (gap 0.00); no engine failures on any paradigm |
| `val/probe_preview_vs_finale_after.py` (384-state grid) | **0 divergent** |
| Seeded HEAD-vs-`1583b06` attribution (`wave2/full_run_seeded.py`: fixed `stochastic_seed` and `shuffle_seed`, so both commits roll the same swans and play the same canonical options) | see "Why the bots got poorer" below |
| `seam/` replay on a fresh cohort (alpha balanced 0.4, beta profit 0.15, gamma green 0.6 → `pull.py` → `compare.py`) | mid-game: analytics `decision_impact` R5 and the admin debrief R5 row equal the commit deltas (−19,897,338.63 / +43.65, `option_b`); final: dashboard, final-report, `flags.final_treasury`, peer leaderboard, admin leaderboard, analytics and debrief narrative agree on the closing treasury and reputation for alpha (2,383,204.28 / 0.0) and beta (−26,672,251.91 / 0.0); M_R and TV agree on every surface; rows still apart are the deferred ones (waterfall FIN-06, revenue-weighted CI SEAM-15, `terminal_valuation` null / `sdg_impact_score` 0 VAL-11) plus two script artefacts (the "cockpit belt `||50`" row simulates the pre-Wave-0 expression — the frontend has 0 `|| 50` sites; "NCD admin avg" is an average against a sum) |
| `soc/p10_patience_cost.py` (12 seeds, even production-chain team, no betrayal) | hostile actions F4 ON **0.2** (audit 3.5, Wave 1 0.3); R10 reputation 72.4 vs 73.0 with F4 off |
| `ops/probe_timed_autocommit.py` | flag keys missing after auto-commit **0**; saved allocations retained; R10 auto-commit ends the game (history 10, profile stamped, later commit → 409, final report 200) |
| `flow/probe_flow.py` | A3 → 403 `waiting_for_teams`; double submit 429 → 409 `stale_round`; manual / timed / free transitions as in Wave 1 |
| `cfg/probe_config_live.py` | `file_vs_process: in_sync`, `stale_bindings: 0`; the only problem is the probe volume's own `image_vs_volume` (its `shares_outstanding`), as designed |
| `acc/sweep_noauth.py` (369 routes, 363 probed) | no-credential 200s 46 → 46, nothing newly open; new `GET /api/admin/config/excel` → 401; new `POST …/materiality/commission-panel` → 422 on an empty body, owner-checked inside |
| `imp/` probes (biodiversity, TCFD, Meadows, SDG, dead toggles, live toggles), `flag/` (phantom proxy flags, sentiment reads the option flags on the first call of the round and not on the two shadow ticks, endpoint flag-dependency graph), `soc/` (p2, p5 fatigue 180/360, p9, p12), `val/` (synergy wipe Divest 0.97 vs Spin-off 1.25, solvency axes, readiness `no_lever`, full-game pillar readiness → 100) | as recorded in the WP commits |

## Why the bots got poorer — attribution of the gate's biggest movement

Every unseeded probe run this wave (fin full run, seam replay, balance ladder) shows the
all-A / balanced bots ending far below their pre-Wave-2 numbers. Two of the causes are the
audit's own remediations acting on bots that greenwash; one was a latent defect the
remediations made reachable, fixed in `56e57ad`.

1. **The bots are serial greenwashers by construction.** `investment_ratio` is recomputed
   server-side as `capex_BU / CSF pool`; a bot that spreads 40 % of the pool over four BUs
   (`seam` alpha) or spends $1M per BU (`fin`) sits at ≈10 % — under the 15 % bar for a
   full green claim, under the 10.05 % bar for a moderate one (alpha misses it by 0.05 pp),
   and under the $3M/BU absolute floor. Before Wave 2 the scandal cost an SLO penalty and
   nothing else; SOC-4 makes it a betrayal for NPC and agent trust memory, so from R3 the
   community leader files an injunction, the regulator fines, the activist launches a
   proxy fight, and the agents escalate. FLAG-9 makes `greenwashing_detected` real, which
   adds +15 pp to the whistleblower roll and +12 pp to the SEC-rule roll (12 % cap).
2. **Seeded, apples-to-apples** (same swans, same canonical options, $1M/BU bot):
   multi_toggles R10 treasury 50.45M → 38.14M, legacy_abc 17.06M → −30.13M (three swans
   at R7–R8 at HEAD, one of them the whistleblower). The same seeded runs with a **clean**
   bot ($3M/BU, ≥ the absolute floor): reputation trajectories identical through R8 on
   both commits, treasury within swan-draw noise (legacy 47.2M → 25.6M on one extra
   embargo, multi_toggles 46.7M → 27.9M), R9 reputation 9.8 → 4.8 from SOC-3 fatigue.
   The remediation punishes the claim it was meant to punish and nothing else.
3. **GATE-1 (new finding, fixed).** `run_new_engines` handed `evaluate_npc_cascades` the
   active-cascade list from *this tick's* events, which never carry it — the previous
   round's list lives in `active_event_flags` — so the "already active → skip" guard never
   held and every open gate re-fired each round: the seam alpha bot took divestment + proxy
   fight + enforcement + injunction every round from R6 and ended at −90.6M. With the
   persisted list read and filtered to its persistence window, the same bot on a fresh
   cohort ends at +2.4M. Goldens and the balance report are unchanged (no cascade runs in
   them); the balance ladder's bankrupt rows stand — they are item 1.

Owner's calibration levers, unchanged here (SOC-1/2 territory): `GREENWASH_INVESTMENT_THRESHOLD`
0.15 is compared with the *average of per-BU ratios*, so a four-BU team needs 60 % of the CSF
pool behind a full claim (or $3M per BU); real teams (241 stored decisions, median ratio 0.50)
mostly clear it, the bot ladder never does. `crisis_count_lifetime` increments every scripted
round, so fatigue efficiency reaches 0.25 by R10 (DELTA § WP-24 note).

## The two calibration rulings (decided 2026-09-05, after the gate)

**C-1 — what backs a green claim.** The check averaged the per-BU investment ratios (each
BU's CapEx over the same pool), so the same 15 % bar meant 60 % of the pool for a four-BU
group and 15 % for a single-BU company, and the archetypal real team — one BU at ~50 % of
the pool, $1 in the other three (169 of the 241 stored BU rows are $1) — averaged 12.5 % and
was a greenwasher on every full claim. Once SOC-4 gave the scandal teeth, that made the
median real team a serial betrayer in the stakeholders' memory. Ruling: a green claim is a
group decision, backed by the group's spend — the team's share of the CSF pool (Σ CapEx /
pool) against the same 15 % / ≈10 % bars, total CapEx against the same $3M floor. Per-BU
neglect keeps its own consequence (the natural-decay tier on each BU's own ratio, F-17); the
other readers of the average ratio are untouched. Goldens unmoved; 8 of 15 runner
fingerprints re-pinned (+2.3M … +2.9M treasury by R10 — the SLO penalty's brand/talent
terms; legacy_abc / healthcare now fingerprint identically to brsr_ngrbc, which was never
greenwash-checked there, so that penalty was the whole difference). The seeded $1M/BU bot
(40 % of the pool) no longer greenwashes in any round: legacy_abc R10 treasury 17.1M
(1583b06) → 73.5M, multi_toggles 50.5M → 84.1M. Players now see the rule before they commit:
the cockpit shows, under the allocation, whether the selected option's claim is backed
(green) or would read as greenwashing (caution), with the bars served from the engine's own
constants.

**C-2 — the reference ladder.** The balance report's reference strategies deployed 10 % of
the pool — under both bars — so every reference row was bankrupt by R6 and the report could
not tell a regression from its own greenwashing. They now deploy 50 % (the median
substantive real allocation); the 5 % / 10 % rungs stay to show the cliff. pure_B $124.0M /
−$86.9M bankrupt R6 → $636.2M / $133.9M solvent; `balanced` −$122.2M R6 → $832.3M / $51.1M
SAFE_HAVEN; ladder 20 % $579.7M, 35 % $575.6M, 60 % $604.7M. Two observations left for you,
not changed: the R1 → A lever (skip the deep audit; the R4 contagion doubles) costs −$231.8M
treasury on the solvent baseline, and pure_C (every ambitious option) is bankrupt at R7 even
at 50 % of the pool.

## After the deploy — what `/api/health` said, and the fix

`f86c3ca` went live at 00:33 UTC (deployment `3450b0ed`); one read-only GET at 00:36 read
green on every checklist line but one: `database: postgresql`, volume `mounted` / `durable`
at `/data` with 48.9 GB free, `clamped_values: []`, engine and persistence failures 0, one
worker as required. The amber: `config.volume_differs_from_image_on` named the four
`slo_ramp` natural-decay keys and `terminal_valuation.shares_outstanding`. What the volume held became clear
across two boots: the share count was the pre-WP-15 100,000,000 (a share price 15× below
the model's scale through the Wave 1 and Wave 2 deploys), and the four natural-decay keys
were not stale values but *absent* — the volume was seeded by the 2 September build, a day
before the `slo_ramp` block entered the JSON, so `config.py` ran its code defaults (equal to
the shipped 0.15 / 0.20 / 0.30 / $100k, the engine was right on those) while `/health` named
the four keys after every boot. My first reading — that the reverted 0.10 / 0.25 / 0.50 tiers
were in play — was wrong; the `/health` list shows key names, not values, and the history had
two candidates. The runbook's remedy (§5b, the patcher in a Railway shell) had not been run
after Wave 1.

The remote paths were not open from this session (the linked shell's egress blocks the
production host; the in-app browser action on the admin UI was refused by the session's
policy), so the fix is in code: **CFG-10** (`87b92d6`) migrates known superseded values on
the volume at boot — the table in `config_migrations.py` lists every value the shipped JSON
once carried and the current one; a key holding exactly a superseded value is rewritten
before `config.py` reads it, announced in the boot log and listed in `/api/health` under
`config.migrated`; a value that is neither superseded nor current is a deliberate tuning and
is left alone. The patcher reads the same table. `87b92d6` booted at 00:59 UTC and migrated the share
count; the four absent keys needed the second shape (`8d21fc4`): a leaf the image carries
and the volume lacks is seeded with the image's value and announced as `[config] SEEDED …`.
On the boot of `8d21fc4` the log should show the four SEEDED lines and `/api/health` an
empty `volume_differs_from_image_on` — no shell step, no restart.

Also on that health read: `build.branch` is `main` (Railway's `RAILWAY_GIT_BRANCH`), so the
service appears sourced from `main` while SETUP_STEPS §5 says `production` — harmless while
both point at the same commit; confirm in the service settings and correct the sentence.

## Deviations from the plan (stated in the commits)

1. **Golden protocol.** The plan asked for one rebaseline per wave; four commits move the
   financial golden and two the stakeholder golden. Rather than hold the goldens red across
   commits, each moving commit rebaselined and wrote its own DELTA section with per-round
   old → new and the cause verified by reverting the single mechanism; the gate re-read the
   whole ledger and indexed it (`b13a72d`).
2. **WP-27** also fixed the paradigm label: the router stamped `legacy_abc` for every
   non-pillar paradigm, so advanced_climate paid the legacy mid-game carbon OPEX on top of
   its own fee and its finale carbon-tax sync never fired. advanced_climate numbers move;
   legacy_abc / multi_toggles do not.
3. **WP-23** also activated targeted swan percentages (`revenue_pct_reduction_targeted` /
   `opex_pct_increase_targeted` were never applied) — the embargo now costs what it says.
4. **WP-22 IMP-06b** (new): `commit_turn` hydrates `pedagogical_overrides` from the cohort
   for the tick and pops it before persistence — settings are not state. The pedagogical
   PUT still filters to `DEFAULT_PEDAGOGICAL_TOGGLES` (drops the four systemic keys by
   design); the per-key cohort route is `PATCH /api/admin/sessions/{id}/cohort-settings`.
5. **WP-24 VAL-05** carries a `no_lever` guard: readiness crosses the tick, but the legacy
   paradigms have no HR lever, so the stock holds there (without it readiness fell to 0 by
   R5 on every legacy team and the Gen-Z agent walked out at R6).
6. **FLAG-9 semantics pinned at the gate:** `greenwashing_scandal` is this round's verdict
   (written every tick, cleared by the merge); `greenwashing_detected` is the run's record
   (written only when a scandal fires, so it persists) and every reader is record-shaped.
7. `docs/` and `SETUP_STEPS.md` are gitignored: the facilitator-manual health sentence and
   the deploy-from-production snippet are local-file edits only. No secret value appears in
   any commit, log, or this report.

## Residual observations (for the wave that owns them)

- Deferred and still visible in the probes: `consequence_waterfall.final_treasury` and the
  RE-bridge bands (FIN-06/07), revenue-weighted carbon intensity (SEAM-15),
  `/final-report.terminal_valuation` null and `sdg_impact_score` 0 (VAL-11), the instability
  discount (VAL-10), 16 inert engine tunables (reported as advisories, CFG-08).
- `black_swan_registry` tests a modifier flag by **key membership** (`mod["flag"] in flags`),
  not truth — a False-valued key would count; every flag it names today is written only
  when True, so nothing misfires, but a future per-round flag would.
- The NPC profiles' `triggers` dicts (`"greenwashing_detected": "enforcement_action"`) are
  not evaluated by any code — narrative config only.
- Balance ladder: pure_A/B/C, extractive and balanced bankrupt R5–R6 at the ladder's
  ratios (item 1 above); a ladder at realistic ratios is the owner's call.
- Intermittent, each red once and green on re-run: `test_timed_autocommit_path::…keeps_the_flags…` (timer body run with delay 0) and `test_r2_materiality_audit::test_option_c_reduces_position_never_improves_it` (solo sessions roll swans from a per-session seed).
- Carried: `consequence_dna_snapshot.flag_nodes` stringified into the R10 flag namespace;
  `_apply_pacing` `next_unlock_at` may be a past entry; cohort creation idempotent by name;
  `test_durable_storage::test_off_railway_repo_dir_is_durable` needs delete permission on
  this mount (green here).

## Before class (owner)

1. Push `main` + `production` (`8d21fc4`); `GET /api/health` `.build.commit` shows `8d21fc4`,
   `config.migrated` lists the four seeded keys, `volume_differs_from_image_on` is empty. Boot log as in the Wave 1 checklist (no `[CONFIG] WARNING`, no
   `[config] CLAMPED`, `[config] volume config matches the image copy`).
2. Pillar overrides now live on the data volume (`ACC-6`): the first boot seeds them from
   the image; edits are super-admin only.
3. A cohort's systemic-risk switches are cohort settings (`PATCH …/cohort-settings`); the
   god-mode defaults apply where a cohort has none. `GodModeStatus` shows R6/R7/R8 journey
   panels as reflection exercises with no engine impact.
4. Runbook pre-flight as in the Wave 1 report, plus: a brsr_ngrbc test cohort through R10
   shows the BRSR finale (bridge, archetype, canonical record) and the BRSR round config in
   the cockpit; upload the regenerated `simulation_config.xlsx` once on the volume and
   confirm `/config/live` reports `in_sync` and every key kept its value.
5. Tell the room the greenwashing rule as the engine states it (C-1, and the cockpit's
   pre-commit line): a green option needs the team to put ≥ 15 % (full) / ≈ 10 % (moderate)
   of the round's CSF pool behind it, or ≥ $3M total CapEx; a scandal is a betrayal the
   stakeholders remember.
