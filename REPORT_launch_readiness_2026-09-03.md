# Launch Readiness Work Order — Report

**Branch:** `fix/launch-readiness-20260903` (off `main` @ `a81b753`, 5 commits ahead of `production` @ `81c23f9`)
**Commits:** `d5d36f9` (item 1), `0392094` (item 2), plus this report.
Nothing pushed to `production`. Nothing committed to `main`.

**Mid-course cohort check (constraint 2.2):** none running. No server process; the
in-memory snapshot (`db/memory_snapshot.json`) was last written 2026-08-04 and every
player session in it has already recorded round 10. Both repairs were safe to apply.

---

## ITEM 1 — REPAIR · Bound the imitation-decay rate ✅

**File and symbol:** `backend/config.py` — `DEFAULT_IMITATION_DECAY_RATE`, with new module
constants `_IMITATION_DECAY_DEFAULT` (0.05) and `_IMITATION_DECAY_SANITY_MAX` (0.08).
The clamp copies the CBAM pattern at `config.py` ~471–479 exactly: named default, named
ceiling, clamp above the ceiling, `[CONFIG] WARNING` naming the observed value, the
ceiling, the value used, and the instruction to update the volume copy.

**Observed value before and after — read back from a running process** (`python -c "import
config; print(config.DEFAULT_IMITATION_DECAY_RATE)"` from `backend/`, with the stale volume
copy in place):

| | before the clamp | after the clamp |
|---|---|---|
| `config.DEFAULT_IMITATION_DECAY_RATE` | `0.1` | `0.05` |
| `[CONFIG] WARNING` emitted | no | yes |

```
[CONFIG] WARNING: engine_parameters.imitation_decay.default_rate=0.1 exceeds the 0.08
sanity ceiling (stale pre-F-07 value); using 0.05. Update simulation_config.json on the
data volume.
```

**The ceiling, and why 0.08.** Stated in the commit message as asked.
* The default is 0.05, the known-bad stale value is 0.10 — exactly double. The ceiling has
  to separate them.
* The key is facilitator-editable through the Excel importer (`config_excel.py:212`,
  `("engine_parameters","imitation_decay","default_rate")` → "%/round"), so a bound at the
  default would forbid every legitimate tuning. 0.08 leaves a band 60% above the default.
* It is **not** set to 0.10. Constraint 2.4: a ceiling raised to admit the value it exists
  to catch certifies that value. If a facilitator should legitimately be able to run 0.10,
  the right instrument is a validated range with an explicit allow-list — a design ruling
  this work order did not ask for and this commit does not make.

**The decay figures, executed rather than hand-computed** (rule 3.3 — `engine.calc_vrio_decay`,
nine applications across a ten-round game, advantage 0.80):

| rate | terminal advantage |
|---|---|
| 0.05 | **0.5042** |
| 0.08 (the ceiling) | 0.3778 |
| 0.10 | **0.3100** |

The work order's 0.5042 / 0.3100 are correct.

**Tests that pin it, by name.**
`backend/tests/test_launch_audit_2026_09_01.py::TestF07ImitationDecayBound` — 5 tests,
**all passing**. The convention followed is CBAM's: the launch-audit file, one class per
finding. Both clamp branches are exercised the way production exercises them
(`MURESSONS_DATA_DIR` + `importlib.reload`, the mechanism behind
`config.reload_simulation_config`), through a fixture that restores the environment and
reloads on teardown so it cannot leak a poisoned config into the rest of the session.

* `test_the_live_rate_is_the_documented_one`
* `test_the_ceiling_sits_below_the_known_bad_value`
* `test_repo_config_matches_the_default`
* `test_a_stale_volume_value_is_clamped_and_says_so` — branch 1 (0.10 → 0.05 + warning)
* `test_a_configured_value_within_the_bound_is_honoured` — branch 2 (0.07 and 0.08 used, silently)

`test_financial_golden_trace.py` and `test_treasury_waterfall.py`: **31 passed, unchanged**
(the suite's `conftest.py` points `MURESSONS_DATA_DIR` at a temp dir seeded from the
repository copy, which already says 0.05, so the clamp is a no-op on every tested path —
exactly as the acceptance criterion expects).

**1b — and this is the first place the work order is wrong.**
`imitation_decay.default_rate` 0.05 was **already** on the deployment refresh list in
`CHANGES_launch_blockers_2026-09-02.md` §"Config keys the deployed volume must pick up",
and so was every other stale key. It was not the only key missing; nothing was missing.

The list's actual defect is different and worse. It named
`ncd_parameters.hostile_threshold` and `ncd_parameters.warning_threshold`. **Neither key
exists** — not in `config.py`, not in either `simulation_config.json`, not anywhere in the
tree. `config.py` reads `hard_cap` and `warn_threshold` (~line 218). Anyone refreshing a
volume from that list would have added two keys nothing reads and left the two that
matter at their dollar-scale legacy values, while believing the job was done. This is
method 3.5 — the right fact checked with the wrong key — sitting inside the very document
that would have been used to fix the volume. Corrected in commit `d5d36f9`, along with the
sentence claiming `config.py` clamps "two" poison values (three, now).

**Anything found that was not in the work order.**
`imitation_decay_rate_start` is a god-mode setting that is echoed at
`admin_router.py:580` with a default of **0.05** and read at `admin_router.py:1579` with a
default of **0.10**, where it renders the facilitator-facing formula card
`Synergy_new = Synergy × (1 − 0.10)`. It reaches no engine — `process_tick` always takes
`config.DEFAULT_IMITATION_DECAY_RATE`. So the reference page a facilitator reads before
class states a decay rate that (a) disagrees with itself between two endpoints and
(b) disagrees with what the engine runs. Not fixed: it is a display change on an admin
surface and outside item 1's scope.

---

## ITEM 2 — REPAIR · Refresh the data-volume configuration ✅

**File:** `db/simulation_config.json` — the durable data dir on this working tree
(`MURESSONS_DATA_DIR` unset → `runtime_paths.data_dir()` → `<repo>/db`). It is gitignored,
so the record git carries is the note added to `CHANGES_launch_blockers_2026-09-02.md` in
commit `0392094`. Previous copy preserved as `db/simulation_config.json.pre-refresh-20260903.bak`.

Reconciled **key by key**, after diffing, not wholesale.

| Key | Volume before | Volume after |
|---|---|---|
| `engine_parameters.cbam.surcharge_rate` | 100000 | 100 |
| `engine_parameters.imitation_decay.default_rate` | 0.1 | 0.05 |
| `engine_parameters.regulatory_ratchet.baseline` | 10.0 | 20.0 |
| `engine_parameters.synergy.max_reduction_per_round` | absent | 0.06 |
| `ncd_parameters.hard_cap` | 1000000 | 5000 |
| `ncd_parameters.warn_threshold` | 500000 | 1000 |
| `ncd_parameters.opex_penalty_per_unit` | absent | 1000 |

The repo/volume diff is now empty in both directions except for one key.
`ncd_parameters.opex_scaling_factor: 50000` is the only key on the volume and not in the
repository, and it was **preserved**, per the work order. Nothing reads it — its sole
mention in the tree is the legacy-key warning in `config.py:226` — and that warning is now
silent because `opex_penalty_per_unit` is present. Deleting a key a facilitator's volume
carries is a separate decision from refreshing values, so it was left alone; say the word
and it goes.

**The seven observed values, read back out of the running process** (not out of the file
just written), `python -c "import config; ..."` from `backend/`:

```
CONFIG_PATH                     = <repo>/db/simulation_config.json
DEFAULT_IMITATION_DECAY_RATE    = 0.05
CBAM_SURCHARGE_RATE             = 100.0
NCD_OPEX_PENALTY_PER_UNIT       = 1000.0
REG_RATCHET_BASELINE            = 20.0
SYNERGY_MAX_REDUCTION_PER_ROUND = 0.06
NCD_HARD_CAP                    = 5000.0
NCD_WARN_THRESHOLD              = 1000.0
```

**No `[CONFIG] WARNING` lines at import.** (Before the refresh there were four.)

**The decay rate the textbook is waiting on is `0.05`** — a running server now reports a
single number, so the three chapters and the facilitator pre-flight that currently state a
range can be reduced to 5% per round.

**Scope caveat, stated plainly.** This is the **dev** data dir. The Railway production
volume is not reachable from a working tree and is **not** refreshed by this work. It still
needs the same seven keys. Until it gets them, and once `main` deploys, the clamps
neutralise three of the five stale values there — but `regulatory_ratchet.baseline` (10.0)
is **not clamped** and would govern, and `synergy.max_reduction_per_round` would fall back
to the code default. On the *current* production build the clamps do not exist at all and
CBAM is live at $100,000/tonne, as the work order says.

**And this is the second place the work order is wrong.**
The acceptance criterion "`/api/admin/config/live` no longer reports 'running on hardcoded
defaults' at high severity" describes something the endpoint never did.
`config_introspect.check_file_ahead_of_process` emits that message only when the config
file is **missing** or **unparseable**. Loaded against the pre-refresh copy (verified by
pointing `MURESSONS_DATA_DIR` at the `.bak`), it returned `file_vs_process: "in_sync"`,
`stale_bindings: []`, and **zero** high-severity problems. After the refresh: identical.
The 16 problems that remain are all `severity: "low"`, `kind: "inert_tunable"`, and
pre-date this work.

Worse, and worth its own line: the endpoint reported `in_sync` **while `config.py` was
actively clamping four of that file's values away**. It compares the file's JSON against
`SIMULATION_CONFIG` — the same JSON — and never against the typed constants the engine
reads. The endpoint whose docstring asks "what configuration is this process ACTUALLY
running?" cannot currently see a clamp. Reported, not fixed: that is a behaviour change to
an admin surface nobody asked for.

---

## ITEM 3 — INVESTIGATE · The carbon-price noise draw

**Confirmation: I changed no behaviour.** No file was edited for this item.

### What the code actually does

`engine.calc_macro_noise` (lines 1331–1364, owner resolved by AST, not by line number)
returns four fields. Three of them are consumed twelve hundred lines later in
`_run_stochastic_layer` (2506–2687, also by AST):

* `inflation_noise` → `inflation_index` at line 2648
* `micro_strike_triggered` / `micro_strike_bu_idx` → the OPEX spike at 2651–2669
* `carbon_price_noise_pct` → stored into `ctx.events["macro_noise"]` at 2649 and **read by
  nothing**

**The sweep, and what it could not have found (method 3.6).** Grep across `backend/` for
`carbon_price_noise`, `carbon_price_pct` and `MACRO_NOISE_CARBON_BAND` returns: the writer,
its own docstring, the display-list entry at `pedagogical_engine.py:115`, the config
binding, and four test assertions. Nothing in `frontend/`. That sweep could not have found
a consumer that reaches the value through a dynamically-built key or a `**events` splat,
which is why the experiment below matters more.

### The decisive test — and why the work order's version of it is not decisive

The work order says: *"Run two full games with identical decisions and different seeds, and
compare the carbon cost. If it does not differ, the draw is not reaching a price."*

**I ran that test. The carbon cost DOES differ** — `carbon_cost`, `carbon_tonnage_group`
and all nine `midgame_carbon_cost_r*` figures diverge between seed 424242 and seed 999331,
and terminal value moves from $231.8M to $322.7M. Followed literally, that test says the
draw *is* reaching a price. It is wrong. Changing the seed changes every rng stream in the
game — crises, FX, micro-strikes, black swans, inflation — so a difference in carbon cost
carries no information about the carbon draw specifically. **A two-seed comparison cannot
isolate a one-field question.**

So I ran the isolating version: **same seed, same decisions, same everything, with
`calc_macro_noise` wrapped so that only `carbon_price_noise_pct` differs** — forced to
`+0.07` in one run and `−0.07` in the other, every other returned field held identical.
That is a ±14% swing on the widest possible band, applied in all ten rounds.

| strategy | numeric event fields compared over 10 rounds | fields that differ | terminal value |
|---|---|---|---|
| pure_B @ 10% | ~800 | **0** (excluding the stored draw itself) | $231,765,212.88 → $231,765,212.88 |
| aggressive_green | 812 | **0** | $891,417,065.08 → $891,417,065.08 |
| extractive | 801 | **0** | $35,249,373.71 → $35,249,373.71 |
| balanced | 802 | **0** | $415,264,975.87 → $415,264,975.87 |

Final treasury and M_R are bit-identical too. Every carbon mechanic that fires in these
runs — `carbon_cost`, `carbon_tax_per_ton`, `carbon_tonnage_group`, the ten
`carbon_intensity_applied_r*` and the nine `midgame_carbon_rate_r*` / `midgame_carbon_cost_r*`
— is untouched. **Bound on the negative result:** these bot runs do not trigger the CBAM
levy (gated on CI > 40 in R3/R7) or the player-set internal carbon fee, so neither was
exercised empirically; both were read instead (`engine.py:3594-3598` and `3653-3665`), and
both take their price from `active_event_flags["global_carbon_fee"]` /
`ECONOMIC_CARBON_PRICE_BASE` and the shadow price from
`active_event_flags["shadow_carbon_price"]` / `FINANCIAL_SHADOW_CARBON_PRICE`. None of them
touches `events["macro_noise"]`.

### Which of the three states — and it is not quite any of them

Not (3): there is no consumer.

Not (1) either, strictly. "Display-only by design" requires it to be displayed, and it is
not. The frontend's own catalogue entry for `macro_noise`
(`frontend/app/components/consequenceCatalog.js:1054`) reads *"perturbs inflation and can
trigger localised disruption"* — carbon is not claimed — and its `explain()` ignores the
value entirely, so the `noise_message` string that says "carbon +6.9%" never reaches a
player. The draw is not a price and not a display. It is **orphaned**.

**It is (2): a consumer was intended and never built.** Four independent signs:

1. It is the only one of `calc_macro_noise`'s four returned fields with no consumer. The
   other three are all wired.
2. `pedagogical_engine.STOCHASTIC_ENGINES` lists `"carbon_price_noise"` as an *engine id* —
   a label for events a consumer would emit. No such event exists. (Nothing in the backend
   emits an `engine_id` at all; that whole labelling layer is consumer-only. Separate
   finding, below.)
3. The band is a first-class facilitator tunable — `config_excel.py:180`,
   `("engine_parameters","macro_noise","carbon_price_band")` → "Carbon price noise band per
   round (symmetric)". A knob that changes only a string nobody reads.
4. The function's docstring says `carbon_price_noise: ±5% of baseline`. The band is 0.07,
   i.e. ±7%. Someone wrote a spec and someone else set a different number, and no consumer
   ever forced them to agree.

### Recommendation — **build the consumer, after launch. Implemented neither.**

Not before the 30-cohort launch: wiring it changes carbon cost on every run, moves the
golden traces and the balance report, and invalidates the pinned figures. It must be a
deliberately-versioned behavioural change with the delta written down first (constraint 2.3).

Build rather than remove, when it is time, because removing loses two things that already
exist and are correct: a documented facilitator tunable, and a stated design intent
("prevents players from reverse-engineering the deterministic math engine") that inflation
noise alone only half delivers. The natural consumer is `carbon_fee_per_ton` at
`engine.py:3656` — the one price whose name and scale match a ±7% annual band. Note it
would be a real difficulty change: ±7% on the compounding internal fee is a meaningful
swing by R10.

If instead the ruling is to remove it, then remove the config key and the
`STOCHASTIC_ENGINES` entry with it, and fix the docstring — otherwise the next audit
re-reports exactly this.

**Either way, do these two now, they are free and not behavioural:** correct the docstring's
±5% to ±7%, and add the allow-list entry / comment that stops the next sweep re-finding it.
I have not made even these changes, because item 3 says implement nothing.

---

## ITEM 4 — INVESTIGATE · The non-monotonic investment sweep

**Confirmation: I changed no behaviour, and no constant.** No file was edited for this item.

### First: the table is not what the work order calls it

The work order calls it *"terminal value by **ESG investment ratio**"*. The report's own
heading is *"CapEx intensity ladder (pure_B choices, varying **capex share of CSF pool**)"*,
and that is what it is. In `dry_run._decisions`:

```
per_bu           = frac * csf_pool / len(bus)
investment_ratio = capex / csf_pool          # == frac / len(bus)
```

With the DEFAULT_4_BU composition, **`investment_ratio = capex_frac / 4`**. So the ladder's
five rungs are investment ratios of **0.0125, 0.025, 0.05, 0.0875 and 0.15** — the whole
sweep sits at or below the *lowest* social-licence band. That single fact dissolves the
work order's point 3, and it is confirmed by execution in the table below.

(Also: *"The report's own summary says 'no dead levers'"* — that sentence belongs to §3,
Lever sensitivity, a different table about switching one round's option. It is not a claim
about §1b.)

### 1. Full decomposition — 5% and 10%, seed 424242

Reproduced the baseline exactly (412.5 / 166.4 / 248.2 / 222.8 / 592.6). One trap worth
recording: `dry_run._run_one` seeds the event streams from
`f"dryrun-{strategy_id}-{seed}"`, so the **strategy name string is part of the seed** — the
same ladder under different strategy names gives entirely different numbers. Registering
them as `ladder_B_5` … `ladder_B_60`, exactly as `scripts/balance_report.py` does, is what
reproduces the published table.

| capex share | investment ratio | TV $M | raw terminal EBITDA $M | exit multiple | WACC | M_R | M_SDG | net debt $M | **CapEx loan closing $M** | **total loan drawn $M** | treasury $M | mean SLO R10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **5%** | 0.0125 | **412.5** | 25.02 | 17.00 | 0.0800 | 0.970 | 1.0 | −60.0 | **0.00** | **0.00** | 110.0 | 5.0 |
| **10%** | 0.0250 | **166.4** | 13.67 | 12.75 | 0.1000 | 0.955 | 1.0 | −43.1 | **0.00** | **0.00** | 93.0 | 0.0 |
| 20% | 0.0500 | 248.2 | 20.49 | 12.75 | 0.1000 | 0.950 | 1.0 | −61.3 | 0.00 | 0.00 | 111.3 | 0.0 |
| 35% | 0.0875 | 222.8 | 18.20 | 12.75 | 0.1000 | 0.960 | 1.0 | −7.3 | 0.00 | 0.00 | 57.3 | 5.0 |
| 60% | 0.1500 | 592.6 | 34.56 | 17.68 | 0.0777 | 0.970 | 1.0 | −78.2 | 0.00 | 0.00 | 128.2 | 52.5 |

M_R breakdowns for the two runs in question:

```
 5%: base 1.0, resilience_bonus +0.20, just_transition_bonus +0.12,
     wellbeing_bonus +0.050, instability_discount −0.40   → 0.970
10%: base 1.0, resilience_bonus +0.20, just_transition_bonus +0.12,
     wellbeing_bonus +0.035, instability_discount −0.40   → 0.955
```

**The financing explanation does not hold.** The work order's hypothesis was that the 5% run
retains treasury which funds CapEx that would otherwise draw a 12% term loan. In fact
**neither run ever draws a term loan** — `capex_loan_drawn` is 0.00 in all ten rounds of
both, and both end in *net cash* (−$60.0M and −$43.1M net debt). Per-BU CapEx at these rungs
is far below the free-CSF threshold (`FINANCIAL_FREE_CSF_PCT` 0.20 × starting treasury =
$10M), so the loan path is never reached. The 5% run is not winning on financing; there is
no financing to win on.

**Where the difference actually is.** `TV = max(EBITDA_FLOOR, EBITDA) × multiple × M_R × M_SDG`,
and the arithmetic closes exactly:

* 5%: 25.02 × 17.00 × 0.970 × 1.0 = **412.5**
* 10%: 13.67 × 12.75 × 0.955 × 1.0 = **166.4**

The 2.48× gap decomposes as **EBITDA 1.83× × exit multiple 1.33× × M_R 1.016×**. The
multiple gap is entirely the dynamic Gordon-growth multiple responding to WACC (0.0800 vs
0.1000). So it is operations and cost of capital compounding, not financing — and, as §2
shows, mostly luck.

### 2. Does the sweep run one seed or many? **One.**

`scripts/balance_report.py:44` — `_SEED = 424242  # one fixed seed: the report is a
baseline, not a distribution`. Five points on a single stochastic path, exactly as the work
order suspected.

Re-run across eight seeds (baseline strategy names preserved), terminal value $M:

| seed | 5% | 10% | 20% | 35% | 60% | 5% beats 10/20/35? |
|---|---|---|---|---|---|---|
| **424242** (published) | 412.5 | 166.4 | 248.2 | 222.8 | 592.6 | **YES** |
| 7 | 311.2 | 354.4 | 253.2 | 254.6 | 474.4 | no |
| 991 | 314.2 | 233.3 | 248.8 | 358.8 | 518.3 | no |
| 20260903 | 103.3 | 317.5 | 218.1 | 190.1 | 607.7 | no |
| 555001 | 212.3 | 154.3 | 248.7 | 291.0 | 614.1 | no |
| 13337 | 226.5 | 315.1 | 236.4 | 269.0 | 635.0 | no |
| 2718281 | 150.3 | 221.3 | 240.3 | 320.5 | 635.9 | no |
| 161803 | 223.7 | 140.2 | 82.2 | 232.0 | 483.4 | no |

**Median across the eight seeds: 5% = $225.1M, 10% = $227.3M, 20% = $244.2M,
35% = $261.8M, 60% = $600.2M — monotonic non-decreasing, and 5% ranks last of five.**

The ordering is not stable. The published seed is the one seed in eight where the 5% run
beats 10%, 20% and 35%.

### 3. Are the social-licence natural-decay tiers engaging? No — and not for the stated reason

Two separate reasons, both verified by executing `engine.apply_natural_decay`.

**(a) The ladder never reaches the bands.** The bands are `>= 0.15` (no decay),
`>= NATURAL_DECAY_MID_RATIO` = 0.20 (mild growth), `>= 0.30` (growth) — the work order's
15/20/30 is right. The ladder spans investment ratios 0.0125 → 0.15. Only the top rung even
touches the first band.

**(b) More importantly, the full-decay branch is unreachable for anyone who spends a
dollar.** At the call site, `engine.py:2998`:

```python
invested = _inv_ratio >= 0.15 or dec.get("capex_allocated", 0) > 0
```

and inside `apply_natural_decay` the third branch is `elif investment_ratio >= 0.15 or
invested:` → treading water. Executed, holding the ratio fixed at 0.0125 and varying only
`capex_allocated`:

```
capex_allocated = 0.00  ->  (rep 48.0, slo 48.0)   # the 4%/round decay
capex_allocated = 1.00  ->  (rep 50.0, slo 50.0)   # no decay at all
```

**One dollar of CapEx buys complete immunity from natural decay.** `dry_run` floors per-BU
CapEx at `max(1.0, …)`, so every bot run — 5% included — is immune. The `>= 0.15` band is
dead for every player who allocates anything at all; the only band that does real work is
the *absolute* escape (`capex_abs >= NATURAL_DECAY_GROWTH_ABS_CAPEX` = $3M → forced into the
growth tier), which is what lifts the 60% rung's mean SLO to 52.5 while every other rung
ends at 0–5.

So the answer to "a 5% run should be losing licence continuously — is it?" is: **no, and
neither would a 0.001% run.** SLO does fall across the trace (47.5 → 5.0) but from crises
and stakeholder pressure, not from natural decay, which never fires.

### Verdict — defect, calibration choice, or emergent property?

**The non-monotonicity is neither a defect nor an emergent property. It is single-seed
noise in a table presented as a sweep.** The underlying relationship is monotonic in the
median across eight seeds and the 5% rung is the *worst* of the five, not the best; the
published inversion survives on exactly one seed. There is nothing here to teach and
nothing to tune — and specifically, no constant should move, because the constants are not
what produced the table.

The **real** finding underneath it is (b): a $1 CapEx allocation disables the social-licence
decay tier that the whole ESG-investment lever is supposed to hang on. That is a defect,
it is in scope for a future work order rather than this one, and it is what I would fix
first. Fixing it would move behaviour and the balance report, so it needs its own ruling
and its own written delta.

Two smaller things to fix in the reporting layer, neither behavioural:
`BALANCE_REPORT_BASELINE.md` §1b should say what its axis is (CapEx share of the CSF pool,
and the resulting investment ratio), and `scripts/balance_report.py` should either run the
ladder over several seeds or state on the page that a single seed cannot support an
ordering claim.

---

## ITEM 5 — INVESTIGATE · The BRSR finale's separate M_R computation

**Confirmation: I changed no behaviour. Nothing was refactored, and no test was added** —
the invariant below is a proposal, as instructed, because its exception list depends on the
ruling.

### Verified myself, not accepted from the table

**Component sets.** `terminal_valuation.calculate_mr` (106–289) writes **eleven** named
components plus arbitrary `pathway_bonuses`: `materiality_governance`, `synergy_bonus`,
`resilience_bonus`, `truth_premium`, `community_champion_bonus`, `just_transition_bonus`,
`workforce_bonus`, `wellbeing_bonus`, `planet_expendable_penalty`,
`brsr_esg_alpha_dividend`, `instability_discount`. (The work order's prose says "twelve";
its own table lists eleven. Eleven is right.)

`round_logic._post_brsr_grand_finale` (308–468) writes: `brsr_truth_premium_blocked`,
`brsr_esg_alpha_dividend`, one of `brsr_pioneer_bonus` / `brsr_steward_bonus` /
`brsr_laggard_penalty`, `workforce_bonus`, `wellbeing_bonus`, `instability_discount`.

Shared: **four**, not three — `brsr_esg_alpha_dividend` is shared too. Absent from the BRSR
path: **seven**, not six (`materiality_governance`, `synergy_bonus`, `resilience_bonus`,
`truth_premium`, `community_champion_bonus`, `just_transition_bonus`,
`planet_expendable_penalty`).

**Shapes — executed, not read.** `calculate_mr` ramps; BRSR steps.

| workforce readiness | `calculate_mr` | BRSR inline |
|---|---|---|
| 74.0 | +0.040 | 0.00 |
| 74.9 | +0.049 | 0.00 |
| **75.0** | **+0.050** | **+0.100** |
| 76.0 | +0.060 | +0.100 |
| 80.0+ | +0.100 | +0.100 |

| avg burnout | `calculate_mr` | BRSR inline |
|---|---|---|
| 19.0 | +0.030 | +0.050 |
| 19.9 | +0.0255 | +0.050 |
| **20.0** | **+0.025** | **0.00** |
| 21.0 | +0.020 | 0.00 |

| avg social licence | `calculate_mr` | BRSR inline |
|---|---|---|
| ≤ 70 | −0.400 | −0.400 |
| 74.0 | −0.240 | −0.400 |
| 74.9 | −0.204 | −0.400 |
| **75.0** | **−0.200** | **0.000** |
| 76.0 | −0.160 | 0.000 |
| ≥ 80 | 0.000 | 0.000 |

**Third place the work order is wrong.** Its table says *"Instability Discount at average
licence 75: `calculate_mr` −0.20, BRSR inline −0.40"*. At **exactly 75** the BRSR path gives
**0.00** — `if avg_sl < 75` is false — so at the stated value the BRSR path is *more
generous*, not harsher. The −0.40 / −0.20 comparison holds just *below* 75 (at 74.9:
−0.400 vs −0.204). The claim "the same named component returns twice the value" is true, but
only inside the lower half of the ramp band; in the upper half BRSR returns nothing where
the canon returns half. The real shape of the divergence is a ±5-point window around each
threshold in which the two disagree, **with the sign of the disagreement flipping at the
threshold** — which is precisely the knife-edge GAME-2 was written to remove, still live on
this path.

Two further divergences the work order does not mention:
* BRSR applies `max(0.0, mr)` — the floor — but **not `MR_CEILING` (2.05)**. Its reachable
  maximum is 1.0 + 0.05 dividend + 0.65 pioneer + 0.10 + 0.05 = **1.85**, so the missing
  ceiling does not bite today. It is still an omission, not a choice.
* BRSR hard-codes `exit_multiple = 12.0` and duplicates the archetype thresholds
  (1.8 / 1.2 / 0.8) inline instead of calling `determine_archetype`, emitting `profile`
  rather than `archetype`.

### Design or drift? — **Drift, on the shared components. Design, on the BRSR-specific ones.**

The seven absent components are defensible: a BRSR/NGRBC ending legitimately scores BRSR
things, and `brsr_pioneer/steward/laggard` and the truth-premium forfeiture belong nowhere
else. The four shared components are not defensible. Nobody designs a component called
`workforce_bonus` to return 0.05 on one ending and 0.10 on the other for the same input.

The evidence that it is drift rather than an unwritten design decision:

1. `calculate_mr` already takes a `pathway_bonuses` parameter, documented as *"additional
   M_R adjustments from the ending pathway (STRAT-004)"* — the exact mechanism this finale
   would use, present and unused.
2. GAME-2's own note says the ramps exist so *"a fraction of a point is never worth a large
   discrete jump"*. Keeping the 0.40 cliff on one path is the defect GAME-2 was written to
   remove, not a variant of it.
3. Flooring but not capping is an omission, not a design.
4. Duplicated archetype thresholds and a hard-coded exit multiple are the classic drift
   signature.
5. `backend/tests/test_mr_single_arbiter.py` states the ruling in its own docstring:
   *"terminal_valuation.calculate_mr's semantics are canonical … The R10 engine must award
   exactly what calculate_mr computes."* A second implementation contradicting a recorded
   ruling, with no written exception, is drift by definition.
6. **No test anywhere touches `_post_brsr_grand_finale`.** Nothing pins it, which is how it
   diverged unnoticed.

### The reachability finding, which changes the priority

`_post_brsr_grand_finale` is reached only from `round_logic.post_tick` line 487,
`if decision_paradigm == "brsr_ngrbc"`. `brsr_ngrbc` is in the Pydantic enum
(`models.py:17`) but **not** in `config.VALID_DECISION_PARADIGMS`, which
`router.py:1553` and `router.py:1728` validate cohort and solo creation against. Executed
against a live TestClient:

```
POST /api/simulations/start  decision_paradigm='brsr_ngrbc'  -> 422
  {"detail":"Invalid decision_paradigm 'brsr_ngrbc'. Valid values:
   ['advanced_climate','healthcare','legacy_abc','multi_toggles']"}
POST /api/simulations/start  decision_paradigm='legacy_abc'  -> 201
```

**No supported route can create a cohort that reaches this finale.** The divergence is
latent, not live: no stored cohort game has been scored by it. That means (a) it is not a
30-cohort-launch blocker, and (b) whenever it *is* fixed, no published number and no stored
game moves — which makes the fix unusually safe, and is an argument for doing it properly
rather than minimally.

Related, and the same shape as the `un_sdg` incident `config.py:20-23` already records: a
facilitator record can carry `brsr_ngrbc` as its default paradigm
(`admin_router.py:2082`, `2476`) while cohort creation rejects it with 422. The set is
authoritative in one place and not enforced in the other.

### Recommendation

**Take the work order's "if drift" path, but not before launch, and with the delta written
down first.** `_post_brsr_grand_finale` should call `calculate_mr` and pass its BRSR
bonuses through `pathway_bonuses`, which is what that parameter is for. Also route the exit
multiple and the archetype through `terminal_valuation`, since they have drifted for the
same reason.

**One consequence must be stated before anyone does it**, because it is not obvious:
`calculate_mr` awards `resilience_bonus` **+0.20 by default** — `if not
flags.get("insurance_only") and not …water_priority`. Routing BRSR through it hands every
BRSR team +0.20 they do not get today, plus whatever `materiality_governance`,
`synergy_bonus` and `truth_premium` they have legitimately earned. That is a large M_R
change, and it is exactly the "different ending scoring on different things" question the
work order says is not mine to settle. If the ruling is that a BRSR ending should *not*
earn resilience or synergy, then the route is `calculate_mr` with those flags suppressed
through `pathway_bonuses`, and that suppression needs to be written down as design, not
left implicit in a second implementation.

### The proposed invariant — written, not added

Home: `backend/tests/test_mr_single_arbiter.py`, whose docstring already states the ruling
this would enforce.

> **Every finale path computes M_R through `terminal_valuation.calculate_mr`, or appears on
> `_MR_ARBITER_EXCEPTIONS` with a written reason and a companion test asserting its intended
> divergence.**

Shape, matching the `_MAX_UNGUARDED` / shockwave-catalog tripwires this codebase already
uses — a universal statement with a named exception list, so adding an exception is a
reviewable diff rather than a silent drift:

```python
# Every function that produces a terminal `regenerative_multiple`. A new finale
# must either call calculate_mr or be added here WITH a reason and a companion
# test pinning what it does instead. Adding a name here is a design decision and
# must be visible in review.
_MR_ARBITER_EXCEPTIONS: dict[str, str] = {
    # "round_logic._post_brsr_grand_finale": "reason, ruling date, companion test name",
}

def test_every_finale_path_routes_through_calculate_mr():
    """AST, not grep: find every function that writes `regenerative_multiple`
    and assert it also calls calculate_mr, unless it is a declared exception."""
    # for each backend/*.py: parse, walk FunctionDefs;
    #   writes_mr  = assigns/subscript-sets "regenerative_multiple"
    #   calls_mr   = any Call whose func resolves to calculate_mr
    #   assert not (writes_mr and not calls_mr) or qualname in _MR_ARBITER_EXCEPTIONS

def test_every_exception_has_a_companion_test():
    """An exception without a test asserting its divergence is drift with paperwork."""
```

**The exception list is left empty and the test is not added**, because whether
`_post_brsr_grand_finale` belongs on it is the ruling. If the ruling is *drift*, the list
stays empty and the finale is fixed. If the ruling is *design*, the finale goes on the list
with its reason, its shared components are still routed through `_ramp_fraction`, and the
companion test pins exactly which components a BRSR ending may and may not earn.

---

## 6. Regression contract — observed results

| Check | Required | Observed |
|---|---|---|
| `pytest tests/ -q` (full memory suite) | passes | **2328 passed, 15 skipped** |
| `test_financial_golden_trace.py` + `test_stakeholder_golden_trace.py` | unchanged, passing | **20 passed** — not rebaselined, unchanged |
| `test_treasury_waterfall.py` + `test_engine_invariants.py` | 6 fingerprints unchanged, conservation closes to 0.00 | **84 passed, 1 skipped** — neither file touched (`git diff main` empty) |
| `test_admin_route_guards.py` | ratchets unmoved | **11 passed**; `_MAX_UNGUARDED` still 58, `_MAX_UNTENANTED` still 1, file unmodified |
| `python3 scripts/balance_report.py` (no `--write`) | matches `BALANCE_REPORT_BASELINE.md` | **byte-identical** once the stdout log lines are stripped |

**Accounting for the test-count difference.** The work order states a baseline of 2,320. I
measured `main` directly rather than trusting the number: a clean worktree at `main`
(`a81b753`) runs **2323 passed, 15 skipped**. The branch runs 2328. The delta is **+5,
exactly the five tests added in `TestF07ImitationDecayBound`** — confirmed independently by
AST count of the changed file (60 test functions at `main`, 65 at HEAD; it is the only test
file the branch touches). **The work order's 2,320 is stale by three**; `main` already
carried 2323 before this work.

No test was deleted, skipped, `xfail`ed or loosened. No golden trace, fingerprint or
balance report was regenerated. No bound, threshold or tolerance was widened. No exception
was swallowed. The frontend was not touched.

---

## 7. What in this work order turned out to be wrong

You asked me to assume something here was stale, and to name it. There were four.

1. **Item 1b — "It is the only stale key missing from that list."** It was not missing.
   `imitation_decay.default_rate` 0.05 was already on the deployment refresh list, and so
   was every other stale key from item 2's table. The list's real defect was two key names
   that do not exist anywhere in the codebase — `ncd_parameters.hostile_threshold` and
   `ncd_parameters.warning_threshold`, where `config.py` reads `hard_cap` and
   `warn_threshold`. Following that list would have left the two NCD values stale forever
   while looking like a completed refresh. Corrected in `d5d36f9`.

2. **Item 2 acceptance — "`/api/admin/config/live` no longer reports 'running on hardcoded
   defaults' at high severity."** It never did, for this condition. That message fires only
   on a missing or unparseable file. Loaded against the stale copy the endpoint reported
   `in_sync` with zero high-severity problems — and reported `in_sync` while `config.py`
   was clamping four of that file's values away, because it compares the file against the
   raw loaded JSON and never against the typed constants. Verified both before and after.

3. **Item 3's decisive test is not decisive.** Two seeds with identical decisions *do*
   produce different carbon costs — I ran it and terminal value moved by $91M — because a
   seed change moves every rng stream at once. Read literally, the stated test returns the
   wrong verdict. The isolating experiment (force only `carbon_price_noise_pct`, hold all
   else identical) is what settles it, and it returns zero differences across ~800 numeric
   event fields per strategy over four strategies.

4. **Item 4 calls the table an "ESG investment ratio" sweep and item 5's table misreads its
   own threshold.** The ladder varies the CapEx share of the CSF pool; the resulting
   investment ratio is a quarter of it (0.0125–0.15), which is why the 15/20/30 licence
   bands never engage — the premise of item 4's third question. And at average licence
   exactly 75 the BRSR inline discount is **0.00**, not the −0.40 the item 5 table states;
   the 2× divergence lives just below 75, and above 75 the divergence runs the other way.

Smaller: item 5 says "six of the twelve documented components" — it is **seven of eleven**,
and there are **four** shared components with differing behaviour, not three
(`brsr_esg_alpha_dividend` is shared and carries a BRSR-only forfeiture gate).

### And three things found that were in no item

* **`imitation_decay_rate_start`** is a god-mode setting defaulted to 0.05 in one endpoint
  and 0.10 in another, rendered to facilitators as the live VRIO decay formula, and read by
  no engine.
* **Nothing in the backend ever emits an `engine_id`**, so the whole
  `pedagogical_engine` / `round_recap_engine` event-labelling layer — `STOCHASTIC_ENGINES`,
  `CAUSAL_TEMPLATES`, `filter_engine_events` — is consumer-only and currently inert.
* **`dry_run._run_one` seeds its event streams from the strategy NAME**
  (`f"dryrun-{strategy_id}-{seed}"`), so renaming a strategy silently changes every number
  it produces. Worth a comment in `scripts/balance_report.py`; it cost me one confused
  round trip and would cost the next reader the same.
