# Combined delta — everything held for rebaseline sign-off

**Status: NOTHING IS REBASELINED. Two golden traces and fifteen treasury fingerprints are
failing on this branch on purpose, and stay failing until this is signed off.** Nothing was
skipped, `xfail`ed or loosened to hide them.

This supersedes `DELTA_natural_decay_recalibration_2026-09-03.md` as the single sign-off
document: that one covers item 4 alone, this one covers everything that moves a baseline.

| Change | Moves golden traces | Moves treasury fingerprints | Moves balance report |
|---|---|---|---|
| Item 4 — natural-decay recalibration | **yes**, both | no | yes |
| B-2 — transient OPEX leak | no | **yes**, all 15 | yes |
| B-3 — `planet_expendable` double charge | no | no | no |
| B-4 — JT scaling reachable | no | no | no |
| B-5 — conservation law coverage | no | no (6 unchanged, 9 added) | no |

Item 4 and B-2 are the only two behavioural changes with baseline consequences, and they
are **cleanly separable** — verified, not assumed.

---

## 1. What moves each baseline, attributed

### 1.1 Golden traces — item 4 only

**Financial trace:** one R1 effect of **−$346,441.84** on treasury, carried forward as a
*constant* offset through R10. Nothing compounds. The only other movement is cost of
capital (0.0500 → 0.0519 at R6–R8, 0.0582 → 0.0585 at R9). EBITDA, emissions, synergy,
M_R, terminal value and every BU field are unchanged.

Measured after B-2 landed, the financial trace delta is **still exactly that constant** —
B-2 adds nothing to it, because that scenario runs at `investment_ratio` 0.3, above
`IMPLEMENTATION_LAG_INV_THRESHOLD`, which is precisely the gap B-2's defect hid in.

**Stakeholder trace:** large and compounding, and the single biggest judgement call here.
The scenario sits at ratio ≈ 0.312, so it cleared the old 0.30 growth bar and now falls to
the mild tier: SLO +1.00/round instead of +3.12/round.

| round | SLO before | after | delta |
|---|---|---|---|
| R1 | 58.12 | 56.00 | −2.12 |
| R5 | 70.62 | 60.00 | −10.62 |
| R10 | 64.25 | 43.00 | **−21.25** |

`community_leader` escalates **`watchful` → `protest` from R7 onward**. That is a visible
in-class stakeholder consequence, not a number on a report.

### 1.2 Treasury fingerprints — B-2 only

All 15 move. They **all passed at the commit immediately before B-2**, which is what
attributes them to it rather than to item 4. Isolated by neutralising
`rescale_bu_transients` at runtime, so this is B-2's effect alone:

| composition / paradigm | pre-B-2 | post-B-2 | delta | % |
|---|---|---|---|---|
| DEFAULT_4_BU / legacy_abc | 155,204,990.48 | 152,374,189.88 | −2,830,800.60 | −1.82% |
| DEFAULT_4_BU / multi_toggles | 71,908,539.72 | 68,794,659.10 | −3,113,880.62 | −4.33% |
| VERTICAL_OIL_AND_GAS_SUB / multi_toggles | 67,076,963.62 | 63,467,076.09 | −3,609,887.53 | −5.38% |
| SINGLE_BU_PHARMA / * | ~111.9M | ~111.9M | ≈ −5,700 | −0.01% |

**Every delta is negative, without exception** — the leak was creating money and no longer
does. Mean −$2,080,201.70 over ten rounds. (One row reads −50.77%: that is
`VERTICAL_OIL_AND_GAS_SUB/advanced_climate`, whose base is near zero and negative. Its
absolute effect, −$3,281,715.92, is identical to its siblings.)

The six pre-existing fingerprints were **unchanged by B-5**, which is the evidence that
B-5's four new ledger terms are 0.00 on the previously covered paradigms — the fingerprint
payload includes `_residual()`, so a non-zero new term would have moved them.

### 1.3 Balance report — item 4 and B-2 together

| strategy | TV before | TV after | bankruptcy before | after |
|---|---|---|---|---|
| pure_A | $0.0M | $0.0M | R7 | R7 |
| **pure_B** | $148.1M | $146.0M | — (solvent) | **R10** |
| pure_C | $0.0M | $0.0M | R7 | R7 |
| aggressive_green | $891.4M | $891.4M | — | — |
| **extractive** | $35.2M | $21.0M | R7 | **R6** |
| **balanced** | $415.3M | $402.3M | — (solvent) | **R9** |

CapEx ladder: 5% $412.5M → **$183.2M** (final treasury $110.0M → **−$1.1M**, now bankrupt
at R10); 10% $166.4M → $66.0M. `wellbeing_bonus` attainment 82% → 73%. Every
lever-sensitivity row moves. "No dead levers" still holds.

---

## 2. The judgement call

Three of six reference strategies stop being survivable, and a stakeholder escalates to
protest in the golden scenario. For a launch of thirty simultaneous cohorts that is a live
pedagogical change: teams that would have finished solvent now go bankrupt, and any
facilitator material quoting survivability or SLO trajectories becomes wrong.

**How much of that is a correction versus a difficulty choice, honestly split:**

* **B-2 is a straight correction.** The engine was creating money — understating cost by
  0.9848% of every transient OPEX surcharge, permanently, every round. Its share of the
  balance-report tightening (roughly 1–2%) is the game finally charging what it always
  said it charged. There is no design question here; the only question is timing.
* **Item 4 is a difficulty choice, and it is the larger share.** Nothing was broken about
  the old bands other than being degenerate; moving the growth bar 0.30 → 0.50 is a
  deliberate hardening. This is where the bankruptcies and the −21 SLO come from.

**If item 4 overshoots, two one-value alternatives, neither needing a code change** — that
is what putting the literals in config bought:

* `slo_ramp.growth_ratio` **0.50 → 0.40**, so ratios in the low 0.30s keep full growth. This
  alone would restore most of the stakeholder trace.
* `slo_ramp.min_abs_capex` **500,000 → 1,000,000** — still inside the empty interval in the
  real data, so it still reclassifies exactly the token $1 allocations.

---

## 3. What sign-off means mechanically

```bash
cd backend
MURESSONS_REBASELINE_GOLDEN=1 python3 -m pytest tests/test_financial_golden_trace.py \
                                              tests/test_stakeholder_golden_trace.py -q
# then update the 15 entries in test_treasury_waterfall._EXPECTED_RUNNER_FINGERPRINTS
python3 ../scripts/balance_report.py --write
```

committing the JSON, the fingerprints and the markdown diff **in one commit alongside this
document**, per constraint 2.3.

**My recommendation:** rebaseline B-2 and keep it — it is a correction, and leaving money
creation in the engine through thirty cohorts is worse than the 1–2% it costs. Take one
more look at item 4's `growth_ratio` before rebaselining that half, because the −21.25 SLO
and the R7 protest escalation are the parts a facilitator will feel in the room, and 0.40
buys most of it back for one config value.

---

## 4. Regression contract as it stands

| Check | Observed |
|---|---|
| `pytest tests/ -q` | **2403 passed, 15 skipped, 17 failed** |
| The 17 | 2 golden traces (item 4) + 15 treasury fingerprints (B-2) — all deliberate, all held |
| Unexpected failures | **none** |
| Conservation law | passes on **all 15** cases (was 6; `advanced_climate` was breaking it by $1,813,896) |
| Route-guard ratchets | `_MAX_UNGUARDED` 58, `_MAX_UNTENANTED` 1, file unmodified |
| Test-count accounting | 2435 collected vs 2352 at the bug-hunt commit: +37 (B-3) +36 (B-5's 9 new paradigm cases x 4 parametrized tests) +1 (B-2) +2 (B-4) +7 (B-1/B-6) |
