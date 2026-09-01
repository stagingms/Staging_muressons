# PLAN — Engine Excellence Roadmap
**Date:** 2026-08-31 · **Status:** ACTIVE · **Owner:** design owner (Jose) + engine maintainers
**Question this answers:** what remains between the current engine and one that is robust, provably calculates what the simulation claims, and meets world-class simulation practice.

## Where this picks up from

The 2026-08-31 campaign (see AUDIT_R2_RESPONSE, AUDIT_FULLCOURSE_RESPONSE, AUDIT_ENGINES_DEEP and their resolution addenda) repaired the impact-key surface across all ten rounds and both paradigms, gave pillar mode a single impact applier plus an evidence-rated revenue lever, consolidated M_R into one clamped arbiter equal to the player-facing projection, made the EU AI Act threat real, put the four highest-stakes dice rolls on the per-cohort seed, made greenwash claims config-driven, and generated the strike glossary from config. Invariant suites now pin all of it. What follows is ordered by trust bought per unit of work.

---

## Workstream 1 — Make green mean green (robustness foundation)

A suite that is never fully green trains everyone to ignore red, which is how the
next C-1 ships.

1. Fix or explicitly quarantine (with reasons) the 11 permanently failing tests:
   `test_team_seats` ×5, `test_scope_seeding_parity` ×4, `test_ci_delta_roundtrip`,
   `test_player_login_parity`. They fail identically at every branch base touched
   this cycle — pre-existing, owner unknown.
2. Kill the order-dependent flakes with real per-test state isolation (the memory
   DB accumulates sessions across a process; the cross-session market-seeding
   noise occasionally swamps small assertions — observed twice this cycle).
3. CI gate: the full suite (plus the invariant files) must pass before anything
   can reach `production` (DEPLOYMENT_CHECKLIST §4 sketches this; the
   `ci-workflow` branch started it). A red build must be unable to deploy.
4. Run the Postgres parity suite (`PG_PARITY=1`) in CI — conftest.py itself
   documents that memory-only testing is how a string of Postgres-only
   production bugs shipped invisibly.

**Definition of done:** a fresh clone runs one command, everything is green, and
`production` is mechanically unreachable otherwise.

**Status (2026-08-31, branch `chore/green-suite`):** items 1–2 CLOSED — the "11
permanent failures" were an environment gap, not code (async tests unrunnable
without `pytest-asyncio`, which requirements-dev.txt omitted; now declared and
pinned). Full suite: **2200 passed, 0 failed**, three consecutive clean runs.
Items 3–4 largely PRE-EXISTED: `.github/workflows/ci.yml` already runs the full
memory-mode suite, a real-Postgres parity job (the deploy gate), frontend tests/
build, and dependency audits — and was itself red on the same missing
dependency; the requirements fix un-reds it. **Remaining, human-action:** in
Railway, enable "Wait for CI" on the service (the workflow's own comment says
exactly this) and optionally add GitHub branch protection requiring the CI
checks on `production`. Nothing further to code here.

## Workstream 2 — Finish the truth programme (claims = calculations)

1. **DEEP-8, the treasury ledger.** `test_treasury_waterfall.py` documents up to
   $656M/run of unattributed treasury movement and prescribes its own method:
   claim the exact-$2,000,000 SINGLE_BU_PHARMA lead first (one ledger term
   double-counted or never applied), then add the missing terms — carbon fees,
   green-fund transfers, fines, black swans, NPC penalties, board resolutions,
   and now pillar costs/revenue — ratcheting the residual ceiling toward zero.
   A golden trace can never find a leak that was always there; only a
   conservation law can. Alongside: hunt the last entropy source so
   `test_the_deterministic_runner_is_actually_deterministic` flips green and any
   graded run replays bit-for-bit (candidate per its docstring: a `hash()` on a
   string somewhere in the engine path — PYTHONHASHSEED is set nowhere).
2. **DEEP-5/9, the flag triage.** 171 of 271 declared flags are read by nothing,
   backend or frontend — the largest remaining pool of promised-but-unmodelled
   consequences (nearly all sustainability_reporting side-track flags, most
   healthcare consequence flags, `ceo_only_signoff`, the supply-chain track's
   M_R bonuses `sc_track_mr_bonus`/`_penalty`, dead helper
   `check_bu_greenwash_scandal`). This is a design session, not code: per
   cluster rule **wire it / demote it to a documented `narrative_tags` field /
   delete it** — then the existing flag-invariant tests hold the line forever.
   Fold in the two parked rulings: `divest_all` (R10, deliberately inert) and
   `supply_chain_fragile` (two disagreeing writers).

**Definition of done:** the waterfall ratchet reads $0 and asserts equality; the
declared-flag surface has zero unruled entries.

## Workstream 3 — Close the doc-drift class structurally

Student-facing numbers must be GENERATED from config, never hand-written beside
it. The R2 mechanics tables (generator + parity test) and the strike glossary
(config-interpolated, DEEP-7) are the pattern; extend it to SIMULATION_CONTEXT's
per-round tables and the remaining hard-coded figures in the glossary and
teleprompter. **Definition of done:** grep finds no load-bearing number in a
student-facing doc that a config change would not update.

## Workstream 4 — Validate the model, not just the code (world-class layer)

Everything above proves the engine does what the config says. Nothing yet proves
the config teaches what is intended. Three instruments:

1. **Balance report** (committed script, run each release): batch-run the seeded
   strategy archetypes and print score spreads, M_R component attainment rates,
   archetype distribution, and per-round / per-option outcome sensitivity. C-1
   survived thirty cohorts because nobody measured whether each lever moved
   outcomes; sensitivity analysis catches dead levers empirically in one run.
   (Seeds exist; the ad-hoc max/min/pillar trajectory harnesses from this cycle
   are the starting material.)
2. **Model card**: the SPEC_Pillar_Revenue_Impacts v2 discipline — every number
   tied to published evidence — applied to the rest of the economics: the
   $25–60/t internal carbon fee vs real ETS prices, the 12× exit multiple and
   WACC coupling vs sector norms, NCD→cost-of-debt at 1bp/unit, strike and
   cyclone probabilities. Document assumptions, sources, and known limitations
   in one place, as serious simulation models do.
3. **Cohort telemetry loop**: after each cohort, compare intended pedagogy with
   realized experience (share of teams earning each M_R component, discount
   rates, greenwash scandal frequency) and feed the next calibration pass. For
   a graded teaching instrument, this closed loop is the credibility layer.

**Definition of done:** each release ships with a balance-report diff; the model
card exists and is cited by SIMULATION_CONTEXT; per-cohort telemetry is a
one-command report.

## Workstream 5 — Hygiene

`.gitattributes` for line endings; normalise the mixed-encoding comment headers
(real `═` vs mojibake bytes — they defeated patch anchors this cycle); delete
confirmed-dead code once Workstream 2's rulings land; retire fully-merged fix
branches.

## Sequencing

W1 first (a week of unglamorous work; everything else stands on it), then W2's
ledger, then the W2 flag-triage session, then W4's balance report and model
card, with W3 and W5 slotted alongside as small sittings. Ship behavioural
changes only at cohort boundaries, red-acceptance-tests-first, exactly as this
cycle's branches did.
