# Terminal Archetype Realism — Diagnosis & Proposal

*Why a company with **negative enterprise value** was crowned "De-risked Safe
Haven," and how to make the Round-10 archetype reflect true performance.
Grounded in the code (`backend/round_logic.py`, `backend/branching_engine.py`,
`backend/ending_pathways.py`, `frontend/app/components/ArchetypeReveal.js`).
Review and proposal only — no code changed. The fix touches **only the label
mapping**; M_R, the valuation math, scoring, flags and round flow stay
byte-identical.*

---

## 1. What the screenshot shows (the symptom)

At Round 10 the player is classified **"De-Risked Safe Haven — Cautious.
Resilient. Structurally sound."** — while the same screen reports:

| Line | Value |
|---|---|
| Final Treasury Balance | **−$464.55M** (negative cash) |
| Regenerative Multiple (M_R) | 1.0000× |
| Double-Materiality Adjusted Value | **−$464.55M** (negative enterprise value) |
| System's own verdict | *"Enterprise value is negative. This is what asset stranding looks like from the inside."* |

The title says *resilient, structurally sound*; the numbers say *insolvent*. The
label and the outcome are describing two different companies.

---

## 2. Root cause (confirmed in code)

**The terminal archetype is classified on M_R alone.** In
`round_logic.py` (the R10 resolver) the entire decision is:

```
if   mr >= thresholds["regenerative_titan"] (1.8): "The Regenerative Titan"
elif mr >= thresholds["derisked_safe_haven"] (1.2): "The De-risked Safe-Haven"
elif mr >= thresholds["fragile_giant"]       (0.8): "The Fragile Giant"
else:                                                "The Stranded Relic"
```

`terminal_value`, `equity_value`, `final_treasury`, and the Natural-Capital-Debt
are all computed a few lines above — and **none of them enter the decision.**

Why that mislabels: **M_R is a *multiplier*, not an *outcome*.** The glossary
defines it as a *"risk-adjusted valuation modifier, range 0.60–2.08, base 1.0"* —
it scores the *quality of the ESG/regenerative strategy* (synergy, resilience,
truth, community bonuses), i.e. how much the market *re-rates* you. But a
multiplier applied to a negative or negligible base is still failure: `1.0 ×
(−$464M) = −$464M`. Classifying on the modifier while ignoring the base is like
grading a company "AAA" because its P/E multiple is healthy, while it's filing
for Chapter 11.

**Two corroborating facts from the codebase:**

- The reveal screen already computes the honest signal it needs —
  `adjustedFinalValue = final_treasury × M_R − NCD` and
  `isValueDestroyed = adjustedFinalValue <= 0` (`ArchetypeReveal.js`). The UI
  *knows* value was destroyed (it renders the asset-stranding warning) — the
  classifier simply never consulted it.
- The **R5 formative checkpoint** classifier (`branching_engine.classify_player_archetype`)
  is already multi-axis — it reads reputation, social licence, carbon intensity,
  burnout and trend. The R10 *terminal* classifier is the one that regressed to a
  single axis. So multi-dimensional classification is an established pattern here;
  we're restoring it at the finale, not inventing it.

*(Secondary inconsistency to verify: the player shows M_R = 1.0000 yet received
"De-risked Safe-Haven," whose gate is M_R ≥ 1.2. Under the ladder, M_R = 1.0
should yield "Fragile Giant." Either a pathway/custom threshold or a
classify-vs-display mismatch is in play — worth a quick trace, but it's a
symptom; the single-axis design is the disease.)*

---

## 3. Design principle

**A terminal archetype must describe the *outcome* first and the *strategy* second.**
Two independent things happened over ten rounds and the label should encode both:

- **Realized value / solvency** — did the company actually create or preserve
  enterprise value and stay solvent? *(the outcome — currently ignored)*
- **Regenerative quality (M_R)** — was the strategy ESG-sound and resilient?
  *(the strategy — currently the only axis)*

A single axis can't separate *"regenerative and valuable"* from *"regenerative
but bankrupt."* Reality can, and so should the label.

---

## 4. Proposal — a two-axis classification with a solvency gate

### 4.1 A hard solvency/value gate comes first
Before any flattering label, check the outcome the screen already computes:

```
value_destroyed = (final_treasury × M_R − NCD) <= 0     # DMAV ≤ 0
insolvent       = final_treasury < 0  (or equity_value ≤ 0)
```

If the company is value-destroyed or insolvent, it **cannot** receive
*Titan* / *Safe-Haven* / *Fragile Giant* — regardless of M_R. It lands in an
outcome-honest band (§4.3). This single gate would have caught the screenshot:
negative DMAV ⇒ never "Safe Haven."

### 4.2 Then place survivors on the two-axis matrix
For companies that ended solvent, classify on **both** axes — M_R (strategy) and
a realized-value tier (outcome, e.g. DMAV or equity-value percentile):

| | **Low M_R** (weak ESG) | **High M_R** (strong ESG) |
|---|---|---|
| **High realized value** | **Fragile Giant** — big and profitable, but ESG-brittle; value now, risk later | **Regenerative Titan** — regenerative *and* valuable (the only path to the top badge) |
| **Modest value** | **Pragmatic Operator** — kept the lights on, unremarkable | **De-risked Safe-Haven** — resilient, disciplined, genuinely lower-risk (its true meaning) |

"De-risked Safe-Haven" becomes *earned*: solvent **and** resilient. "Regenerative
Titan" now requires actually creating value, not just a high multiplier.

### 4.3 Outcome-honest names for the failure band
The value-destroyed / insolvent companies get names that tell the truth and carry
the pedagogy — including the sharp lesson that *good ESG optics don't save an
insolvent balance sheet*:

- **The Stranded Relic** — low M_R **and** value-destroyed (the deserved floor).
- **The Hollow Idealist** *(new)* — decent M_R (good ESG story) but negative
  enterprise value. "You told a regenerative story the balance sheet couldn't
  fund." This is precisely the screenshot's company.
- **The Turnaround Manager** — insolvent but on a clearly improving trajectory
  (reuse the existing R5 "trend" signal), i.e. rescued-from-the-brink.

### 4.4 Keep it configurable — extend the Archetype Editor
Today the God-Mode editor exposes one knob per archetype: an **M_R threshold**.
Add a **second axis** — a value/solvency band (e.g. "min DMAV," or a
"requires-solvent" flag) — so facilitators define the 2-D ladder and the editor
stays in sync with the engine (the same one-source discipline the role/shockwave
tables follow). Default ladder ships with the matrix above; customs still
override by key.

---

## 5. Why this changes **no** simulation logic (the hard constraint)

- **M_R is untouched** — same bonuses, same penalties, same 0.60–2.08 range,
  same terminal-value formula. We *read* it; we don't change it.
- **The valuation math is untouched** — treasury, terminal value, equity bridge,
  NCD, DMAV all compute exactly as today. The gate reuses `adjustedFinalValue` /
  `isValueDestroyed`, which the reveal screen already derives.
- **Scoring, flags, round flow, the leaderboard M_R normalisation — untouched.**
- Only the **label mapping** at `round_logic.py`'s archetype block changes, from
  a 1-D `if mr >= …` ladder to a 2-D `gate → matrix` lookup, using variables
  already in scope. No new engine inputs, no new endpoints.

The player's *numbers* stay identical; only the *word* attached to them becomes
honest.

---

## 6. Phased plan (same protocol as the S/V/CA/SA series)

One commit per phase · pytest green · endpoint-contract unchanged · screenshot
diff on the reveal · `git revert` rollback.

**AR-A — Solvency gate (highest value, lowest risk).** Add the value-destroyed /
insolvent gate: negative DMAV or negative equity can never map to
Titan/Safe-Haven/Fragile-Giant; route to Stranded Relic / new Hollow Idealist.
*Test:* replay the screenshot's end-state → no longer "Safe Haven"; solvent runs
unchanged. Add a unit test pinning "negative DMAV ⇒ non-flattering archetype."

**AR-B — Two-axis matrix for survivors.** Introduce the realized-value tier and
the M_R × value lookup; retune the four survivor names to the matrix. *Test:*
golden cases at each quadrant; the terminal-value/M_R numbers are byte-identical.

**AR-C — Editor second axis.** Extend `DEFAULT_ARCHETYPES` + the Archetype Editor
with a value/solvency band; keep the M_R-only customs backward-compatible
(missing band ⇒ "any"). *Test:* editor round-trip; custom archetype still wins by
key.

**AR-D — Copy + reveal polish.** Align the archetype subtitle and the DMAV
callout so the headline word and the headline number agree; verify the
asset-stranding wording (it currently blames NCD even when the driver is a
negative treasury). *Test:* screenshot diff; a11y.

---

## 7. Explicitly rejected easy workarounds

- *"Just raise the M_R thresholds."* Doesn't help — a high-M_R company can still
  be insolvent; the axis itself is wrong, not its cut-points.
- *"Append 'INSOLVENT' to the title and move on."* A band-aid; it leaves a
  self-contradicting label ("Safe-Haven — Insolvent") and skips the pedagogy of a
  distinct, honest archetype.
- *"Classify on treasury alone."* Over-corrects — it would punish a regenerative
  firm that invested heavily (low cash, high enterprise value). Use realized
  value / DMAV (which already nets treasury × M_R − NCD), not raw cash.
- *"Change M_R so it captures solvency."* That would alter scoring and every
  downstream number — out of bounds. Keep M_R as the strategy axis; add value as
  a second axis.

---

*Recommendation: ship **AR-A alone** first — the solvency gate is a few lines, is
covered by one unit test, and immediately stops the "insolvent Safe-Haven"
class of mislabel with zero risk to any number on the screen. AR-B–D turn the
gate into a genuinely two-dimensional, configurable, honest terminal profile.*
