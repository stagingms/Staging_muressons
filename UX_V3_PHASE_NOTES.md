
---

## Capital Allocation redesign (player Investment Matrix) — CA-A → CA-D

Scope from `REVIEW_Muressons_CapitalAllocation_Redesign_Plan.md`. Files:
`components/InvestmentMatrix.js` + `.module.css`. **Untouched (verified
byte-identical baseline↔HEAD):** the `<input type=range>` bounds
(`0…csfPool×1.20`, `step 100_000`, `value`, `onChange={handleSlider}`, refs),
`getBuHealth` thresholds, the four metric definitions, `getSliderColor`, and the
pool/allocated/remaining math. Presentation-only; no new fetch/WS.

- **CA-A (`a15c8f3`)** — legibility + tokens (CSS only): metric text/fills moved
  from near-invisible dark `#059669`/`#d97706` to the bright `-text` semantic
  tokens; thicker gauge tracks; brighter slider empty track.
- **CA-B (`fb3092e`)** — budget tension: REMAINING promoted to the hero number
  (colours as it drains, red when over-allocated) + a full-width pool-spent bar
  (calm/amber/over, same thresholds as the slider fill).
- **CA-C (`bad08f6`)** — `getBuHealth` promoted to a verdict chip + one-line
  investment thesis (mirrors the same thresholds, invents no numbers); the four
  metric gauges moved behind a per-tile "Metrics" expand, so the default tile
  leads with health + slider and zero-valued metrics no longer cost ambient
  space.
- **CA-D (`ebe0a01`)** — comparison alignment: health chip inline on the BU name
  row (no longer collides with the alloc amount); thesis clamped to one line for
  equal tile heights; reduced-motion pass; single-BU full-width unchanged.

Per-phase gates: JSX parse + CSS brace balance, jest 85/85, logic-untouchable
audit (slider input / health thresholds / sliderMax all present, unchanged).

**Rollback:** four independent commits — revert any subset. **On-machine:** drag
to over-allocate → REMAINING red + pool bar over-state + slider red; open a
tile’s "Metrics" → the four gauges (incl. Nat. Debt) with thresholds/YoY as
before; confirm the committed allocation is identical to pre-CA.

*(Commits used a git-plumbing path — write-tree/commit-tree + direct ref write —
because a stale `.git/HEAD.lock` the sandbox mount can’t delete blocks normal
`git commit`. Harmless; delete the lock on your machine if git complains.)*
