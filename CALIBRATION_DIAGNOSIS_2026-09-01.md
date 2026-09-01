# Calibration Diagnosis — Why Every Team Goes Bankrupt by R6

**Date:** 2026-09-01 · **Instruments:** cohort telemetry (real alpha sessions),
balance report (scripted strategies), controlled what-if runs through the
production pipeline (dry_run, fixed seeds). No behaviour was changed in this
diagnosis; options below await a design ruling.

## 1. The pattern

Every real finisher in the stored alpha data AND every scripted strategy shows
the same trajectory: margin flips negative around R4, insolvency R5–R7, pinned
to the insolvency floor by R9–R10, STRANDED_RELIC at terminal. One real team,
round by round (team 2da103dc, legacy):

| | R1 | R3 | R5 | R7 | R9 | R10 |
|---|---|---|---|---|---|---|
| Revenue | $53.5M | $44.7M | $37.7M | $41.3M | $35.6M | $21.3M |
| OPEX | $34.3M | $42.4M | $53.5M | $67.2M | $105.5M | $171.1M |
| Treasury | $49.5M | $54.3M | $27.9M | −$61.0M | −$309.2M | −$496.1M |

Revenue **falls ~60%** over the game; OPEX **grows ~5×** — while the applied
inflation was only ~2.4–3.0%/round. The gap is the finding.

## 2. Mechanism: a ratchet-down economy (flow adjustments written into stock)

Several per-round *flow* penalties are written back into the **base state**, so
they compound forever instead of applying once:

1. **Governance cash-conversion drag → `revenue_base`** (engine.py:2473).
   `calc_cash_conversion`'s own docstring says it returns "realized_revenue
   (the cash that actually arrives)" — a timing/flow concept — but the caller
   assigns the result to `bu["revenue_base"]`. At gov-risk 30 that is −6% of
   revenue **per round, permanently** (0.94¹⁰ ≈ −46%), for every team, from R1.
   The single largest cash driver in the what-ifs below.
2. **Talent braindrain → `opex_base`** (engine.py:2847): the rep<65 penalty
   multiplies the base, so it compounds each round reputation stays low.
3. **NCD opex penalty → `opex_base`** (engine.py:3217), micro-strike penalty →
   `opex_base` (engine.py:2501): same write-into-base pattern.
4. **Nominal asymmetry:** OPEX inflates every round (default 5%/round; the
   session observed used ~2.5–3%), but there is **no revenue growth mechanism
   at all** — no price inflation, no volume growth; option `revenue_delta`s
   are small one-offs. Costs live in a nominal economy, revenue in a real one.
5. **Cost of capital 20%/round** (regulatory floor) turns any negative
   treasury into a terminal debt spiral — but the what-ifs show it only
   matters *after* items 1–4 have caused insolvency.

The "spiralling neglect cascade" is documented, intended design — for
*neglect*. The defect is that the spirals engage from the **baseline state**
(starting gov ≈ 8–20 rising to 30, rep 47) for every team, including ones
investing consistently: the all-B strategy at 10% capex goes bankrupt at R5.

## 3. Causal attribution (seeded what-ifs, pure_B baseline, DEFAULT_4_BU/legacy)

| Variant | Bankrupt | R5 treasury | Terminal value |
|---|---|---|---|
| baseline | R5 | −$10.4M | −$333.5M |
| inflation 0 | R6 | +$27.4M | −$105.1M |
| inflation 2.5% | R6 | +$8.5M | −$179.7M |
| cost of capital 8% (+floor) | R5 | −$10.4M | −$333.5M |
| reputation start 80 | R7 | +$38.2M | −$126.0M |
| governance risk 5 | R7 | +$58.7M | −$26.5M |
| SLO start 70 | R5 | −$10.4M | −$333.5M |
| healthy start (rep 65 / gov 12 / SLO 60) | R7 | +$44.4M | −$108.1M |
| **all softened jointly** | **—** | **+$109.7M** | **+$119.3M** |

No single knob rescues the game; the spiral is the *joint product* of the
governance revenue drag × reputation penalties × inflation, with the 20% cost
of capital finishing the job. Softening everything at once produces a solvent,
positive-TV game — proving the engine can express a winnable economy without
touching M_R or the option design.

## 4. Options for the design ruling (all behavioural → cohort boundary)

- **A. Flow, not stock — cash conversion** (engine.py:2473): apply the
  governance drag to the round's realized cash (a CSF/waterfall line item, as
  its docstring already describes) instead of mutating `revenue_base`.
  Structural fix for the biggest driver; gov risk still hurts every round, but
  stops eroding the base permanently. New waterfall term → conservation-law
  test extends naturally.
- **B. Nominal symmetry**: inflate `revenue_base` alongside OPEX (full or a
  configurable fraction, e.g. 80% "pricing power"), so inflation becomes a
  margin-pressure mechanic instead of a guaranteed death tax. Economically
  principled; MODEL_CARD already flags the round-compression context.
- **C. Threshold + flow the penalty writers**: braindrain, NCD-opex and
  micro-strike penalties charge the round (flow) rather than multiply the
  base, and/or engage only above risk thresholds so healthy teams aren't
  taxed by default.
- **D. Retune scalars**: inflation default 5%→2.5%/round; cost-of-capital
  floor 20%→10–12%. Cheap config-level relief, treats symptoms not structure.
- **E. Intended-brutality**: keep as-is; reframe the pedagogy (survival IS the
  win), and say so in the teleprompter, glossary and model card.

Recommended package: **A + B (at ~80% pass-through) + C**, then remeasure with
`scripts/balance_report.py` — the target picture is pure_C/extractive still
failing hard, pure_B marginal, and disciplined ESG strategies solvent — and
verify the M_R ceilings (1.93/2.02) and golden trace, which none of A–C should
touch (they change cash, not M_R components).

## 5. Resolution (same day, branch `fix/ratchet-economy`, ruling: A+B+C)

Implemented as red-acceptance-tests-first (tests/test_ratchet_economy.py):
transient flow adjustments — the penalty is REAL for the round it occurs
(CSF, waterfall and all intra-round readers see the adjusted figures) and is
reversed from the persisted base at end of tick. Sites converted: governance
cash-conversion drag (revenue_base), talent braindrain, NCD opex penalty,
micro-strike (opex_base) — and three more base-eroding flow sites found during
implementation: revenue cannibalization, FX swings (a random walk was being
compounded into the base!), and the healthcare patient-outcomes multiplier
(converted symmetrically). Ruling B: `INFLATION_REVENUE_PASSTHROUGH = 0.80`
(config-overridable; 0 restores old behaviour).

After (balance report, DEFAULT_4_BU/legacy, seeded): aggressive_green
**solvent, TV +$349M, SAFE_HAVEN, M_R 1.42**; balanced +$127M; pure_B marginal
+$29M; pure_A and pure_C bankrupt R7; extractive bankrupt R5 at −$2.3B. CapEx
ladder: 5% fails, 10%+ solvent with diminishing returns — the intended
teaching gradient. Deliberate rebaselines: financial + stakeholder golden
traces, six treasury fingerprints; INV-8 now accounts for the end-of-tick
reversals via the engine's own reversal event; the SLO-steerability fixture
scales capex to the (now larger) CSF pool so it keeps measuring SLO, not
greenwash. Conservation law and M_R ceilings (1.93/2.02) untouched and green.
Ships at the cohort boundary with everything else. Watch item for next
cohort's telemetry: greenwash scandal frequency (relative-ratio threshold vs
healthier treasuries).
