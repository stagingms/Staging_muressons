# Capital Allocation (Investment Matrix) — Redesign Plan

*Design-thinking + simulation-pedagogy review of the player Capital Allocation
stage (`frontend/app/components/InvestmentMatrix.js`, 509 lines). Grounded in
the code, not the screenshot alone. Review and plan only — no code changed.
Hard constraint honoured throughout: the allocation logic, data flow, round
fluency, and scoring stay functionally identical. Every recommendation is a
presentation-layer change to how the same numbers and the same slider are shown.*

---

## 0. What the code actually does (so nothing here breaks it)

Each of the four BU tiles is a `<input type="range">` from `0` to
`csfPool × 1.20`, step ₹100k, writing to `allocations[bu_id]` via
`onAllocationsChange`. The header ring is `allocated / pool`. Per tile the code
already computes:

- **BU health** — `getBuHealth(bu)`: `good | warning | danger` from margin
  (<25 warn / <15 danger), social licence (<55 / <40), governance risk
  (>15 / >25). Rendered today only as a tiny coloured dot.
- **Four metric mini-bars** — Margin, Social Lic., Gov Risk, Nat. Debt, each
  with warn/danger thresholds, an `invert` flag (gov/ncd are "lower is better"),
  and a year-over-year `prev` delta.
- **Slider fill colour** — `getSliderColor(pct)`: calm accent → amber (>80%) →
  red (>100%), already encoding over-allocation.
- `% of pool`, revenue, allocation amount; a SORT bar (default/revenue/margin/
  risk), already hidden in the single-BU edition.

All of that is decision-support data the redesign must *keep* — the issue is
how it's presented, not what it is.

---

## 1. Design-thinking frame

**Empathise — who is here, when?** A student mid-round, under a countdown, whose
single job at this stage is: *split a scarce ₹9.9M pool across four business
units.* They are not reading operational KPIs for their own sake; they are
deciding **where money does the most good and how much is left.**

**Define — the one question the screen must answer per glance:** "Should I fund
this BU, and by how much?" The current tiles instead present four equal-weight
faint mini-bars per BU — four near-identical dark mini-dashboards the eye has to
parse separately, when the actual task is a *comparison* across four units under
one budget.

**Observe — what the screenshot shows going wrong:**
1. **Very low contrast.** The panel is near-black; the metric bars and the
   `₹0.0M` values are barely legible — exactly the numbers the decision rests on.
2. **Four metrics as decoration, not decision support.** Margin / Social Lic. /
   Gov Risk / Nat. Debt render at equal weight, disconnected from the slider,
   so nothing says *"fund here because…"*. The health verdict the engine already
   computes (`good/warning/danger`) is buried in one 8px dot.
3. **Zero-noise.** Nat. Debt is ₹0.0M for all four BUs this round — a whole
   bar per tile spent on a uniformly-zero signal.
4. **Budget tension under-sold.** REMAINING (₹5.7M) is the constraint the whole
   stage is about, shown at the same weight as POOL and ALLOCATED.
5. **Comparison is hard.** A 2×2 of independent tiles fights the "compare four,
   split one pool" task; the eye can't scan a column of health or allocation.

**The governing idea:** *allocate against health, and feel the tension.* Make
each tile answer "fund here, how much?" with one clear health verdict and the
slider as the hero; make the shrinking pool the emotional centre; move the four
detailed metrics into an on-demand expand (summoned, not ambient) — the same
"one surface per slot" discipline from the player-v2 pass.

---

## 2. Redesign concept

### 2.1 Elevate the budget tension (the stage's whole point)
Make **REMAINING** the hero number: large, and colour-shifting as it approaches
zero and turns red past the pool (the data for this already exists —
`remaining`, and `getSliderColor` already knows the over-allocation colours).
Pair the existing ring with a single full-width "pool spent" bar so the tension
reads in one glance: filled = allocated, with a clear over-allocation state.
Nothing about how the pool is computed changes.

### 2.2 One health verdict per BU, with a one-line thesis — not four faint bars
Promote `getBuHealth()` from an 8px dot to the tile's primary signal: a coloured
status chip ("Healthy" / "Watch" / "At risk") **plus a one-line reason derived
from the metric that triggered it** — "Strong 36% margin," "Low social licence
(48/100)," "Elevated governance risk (20%)." This reframes the operational
numbers as an *investment thesis* at the moment of decision, which is the
triple-bottom-line lesson the sim is teaching (you fund against financial AND
social/governance health, not margin alone). The four detailed metric bars move
into a **tap-to-expand** panel on the tile — same component, same data, same
thresholds and YoY arrows, summoned not ambient.

### 2.3 Make the slider the centre of gravity, with live consequence
The slider is the action; give it the tile's centre and strengthen the existing
calm→amber→red fill. Put the allocation amount and `% of pool` at the thumb (the
tooltip scaffold already exists), and show "remaining after this" so each drag
has an immediate, legible consequence. **Suppress metrics that are uniformly
zero this round** (Nat. Debt at R1) — show them only inside the expand, so a
zero signal never costs a permanent bar.

### 2.4 Comparison-first alignment
Keep the tiles, but align them as a comparison: identity + health verdict on the
left, the big allocation number + slider on the right, on a consistent baseline
so the eye can scan the *column* of health and the *column* of money. (On the
single-BU edition this collapses to one full-width row — the SORT bar is already
correctly hidden there.)

### 2.5 Visual grammar
Apply `app/styles/tokens.css` semantic colours — `positive/caution/danger` for
the health verdict and the budget tension, one card style, and raised
text contrast on the numbers — the same token discipline as the V-D pass. This
alone fixes most of the "too dark / can't read it" problem without touching a
single value.

---

## 3. What must NOT change (verified against the code)

- The `<input type=range>` bounds (`0…csfPool×1.20`), `step 100_000`, the
  `onAllocationsChange` write path, and the native-input listener map
  (`sliderRefs`, NEW-05) — untouched; this is what keeps allocation deterministic
  and the commit payload identical.
- `getBuHealth` thresholds, the four metric definitions, `invert` flags, and YoY
  `prev` deltas — kept verbatim; only *where/how prominently* they render moves.
- `getSliderColor` over-allocation semantics, the pool/allocated/remaining math,
  the SORT behaviour, and the "Confirm Allocation & Continue" gate — unchanged.
- No invented numbers. There is **no** projected-return value at this stage (the
  engine computes effects at commit), so the redesign will not fabricate a
  "predicted ROI" — the realism comes from reframing the *existing* health
  metrics as a thesis, not from new data. (An honest, backend-sourced
  "projected effect" preview would be a separate, later, backend-touching item —
  explicitly out of scope here.)

---

## 4. Phased plan (same protocol as the V-series)

One commit per phase · jest + player smoke green · endpoint-contract unchanged
(this stage sends no new requests) · screenshot diff per stage · `git revert`
rollback. All within `InvestmentMatrix.js` + its CSS module.

**Phase CA-A — Legibility & tokens (lowest risk, highest immediate payoff).**
Token-migrate the panel (contrast, one card style, semantic health colours),
raise numeral contrast, strengthen the slider fill. No layout or data change —
pure grammar. *Test:* WCAG AA on the allocation path; screenshot diff shows same
structure, readable numbers.

**Phase CA-B — Budget tension.** REMAINING becomes the hero with the shrinking
"pool spent" bar and over-allocation state. *Test:* drag to 0 and past the pool
→ colour/state changes match `getSliderColor`; pool math identical to before.

**Phase CA-C — Health verdict + expand.** Promote `getBuHealth` to a chip + one
-line thesis; move the four metric bars into a tap-to-expand; suppress
uniformly-zero metrics from the ambient view. *Test:* every metric still
reachable (in the expand); thresholds/YoY unchanged; keyboard-operable expand.

**Phase CA-D — Comparison alignment + motion polish.** Consistent baseline so
the four tiles read as a comparison; reduced-motion pass; single-BU full-width
check. *Test:* 1280/1024 widths; single-BU edition; commit flow unchanged.

**Sequencing rationale:** CA-A is invisible-risk and fixes the loudest problem
(legibility) first; CA-B and CA-C are additive re-slotting of existing data;
CA-D is polish. At no point does the slider’s value, bounds, or write path
change — so the allocation the player commits is byte-identical to today’s.

---

## 5. Explicitly rejected easy workarounds
- *"Just brighten the colours."* Fixes contrast but leaves four equal-weight
  metrics fighting the decision — the structural problem (no clear "fund here,
  how much") remains.
- *"Add a predicted-ROI number to each tile."* Tempting for realism, but that
  value doesn’t exist pre-commit; inventing one would mislead learners and
  couple the UI to a number the engine doesn’t produce here. Reframe existing
  health metrics instead; a real projected-effect preview is a separate
  backend-sourced feature, flagged not smuggled.
- *"Drop the metrics to declutter."* They’re the pedagogy (you allocate against
  triple-bottom-line health). Re-slot them into the expand; don’t delete the
  lesson.

---

*Recommendation: CA-A + CA-B make a tight first phase — they remove the "dark and
unreadable" problem and sell the budget tension, with zero risk to the
allocation logic. Ready to implement on your go, in the V-series style.*
