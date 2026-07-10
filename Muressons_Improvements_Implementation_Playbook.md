# Muressons — Implementation Playbook for the Green/Yellow Improvements

*How to make each improvement without breaking the code, the simulation math, the round flow, or the user experience. Every item is mapped to a real integration point in your tree, with a "why it's safe" note. Nothing here changes engine outputs — most are presentation, content, or additive-config layers that ride on data you already compute.*

**Risk legend:** ⚪ Content/copy only (no code path touched) · 🟢 Additive UI (new element, no state change) · 🟡 Additive state (new field, backward-compatible) · 🔵 Refactor (behaviour-preserving)

---

## A. Credibility & Methodology (defensibility in the room)

### A1 ⚪ Surface the synergy double-count fix in the debrief
**Where:** `frontend/app/components/DebriefReport.js` (and/or `GameOverSummary.js`), fed by the existing `terminal_valuation.py` M_R breakdown.
**How:** You already compute the M_R components server-side. Add a static "Methodology notes" disclosure at the bottom of the debrief that renders a short, fixed string per component — for synergy: *"Synergy contributes +0.15 to M_R (not +0.30): its OPEX savings already raise EBITDA, so a larger multiple would double-count the same benefit."* Store these one-liners in a small `METHODOLOGY_NOTES` dict keyed by M_R component, colocated with the breakdown so they can never drift from the numbers.
**Safety:** Pure copy in a collapsible panel; no math, no flow change. Facilitators get the defence pre-written.

### A2 ⚪ Publish parameter provenance
**Where:** `simulation_config.json` + a new `docs/Parameter_Provenance.md` (and optionally a read-only "Assumptions" tab in God Mode).
**How:** Keep the JSON numeric (don't add prose that could break parsing). Instead add a sibling `simulation_config.provenance.json` (or a `_sources` block your loader ignores) that maps each constant to a citation: shadow carbon $250 → internal-carbon-price literature (e.g., CDP corporate ICP ranges); carbon $50 @ 5% → observed compliance-market trajectories; greenium/brown penalty → green-bond spread studies; exit multiples → sector EV/EBITDA comps. Surface it as a static doc first; wiring it into the UI is optional.
**Safety:** New file, ignored by the engine. Zero runtime impact; buys credibility.

### A3 🟢 Turn the assets you already built into facilitator artifacts
**Where:** `scripts/monte_carlo_stress_test.py`, `backend/test_bu_substitution.py`.
**How:** Add a `scripts/generate_facilitator_evidence.py` wrapper that runs both and writes two PNqG/PDF outputs into `reports/`: (1) the M_R distribution across strategies with the floor/cap lines drawn, annotated *"no strategy is strictly dominant; M_R never breaches [floor, cap]"*; (2) a vertical-swap parity table showing terminal-valuation balance holds when default BUs are substituted. Run it in CI so the artifacts regenerate on every engine change.
**Safety:** Read-only analysis over existing code; produces documents, touches no runtime path. Makes your fairness claims evidence-backed.

### A4 🟢 Make determinism visible
**Where:** the crisis/briefing header (`RoundBriefing.js`) or the stochastic-roll UI (`StochasticDiceRoll.js` already exists).
**How:** When a cohort seed is present (`rng_util._resolve_seed`), render a small, dismissible chip near any random event: *"🎲 Shared dice — every team in this cohort faces the identical roll this round."* Drive it off a boolean the backend already knows (seed present vs. absent) so solo/unseeded sessions simply don't show it.
**Safety:** One conditional badge; no logic change. Kills the "we got unlucky" objection at the source.

---

## B. Pedagogy (the learning loop)

### B1 🟡 Show the consequence hypothesis *before* commit
**Where:** `DecisionTile.js` (tile) using data from `ConsequencePreview.js`, which already runs the What-If projection.
**How:** `ConsequencePreview` already returns ranked projected impacts. Add a pure function `topTradeoff(preview)` that picks the single largest positive and largest negative projected delta and renders one line under the tile: *"Defers NCD (+) · raises R4 severity (−)."* Frame it as a hypothesis with a subtle label ("Projected — you'll see if you were right next round"). Reuse the existing impact icons/formatters so it's visually native.
**Safety:** Reads data you already compute; adds one text line per tile. No new fetch, no state mutation, no change to what "commit" does. If the preview is empty, render nothing (graceful).

### B2 🟡 One required reflection box between rounds
**Where:** the round-transition point in `page.js` (the `roundChanged` / briefing gate) → persisted via `useSimulation.commitTurn` payload → stored on the round row → surfaced in `DebriefReport.js`.
**How:** After commit, before the next briefing, show a single textarea: *"Predicted vs. actual — and why?"* Send it as an optional `reflection` string on the commit payload; store it on the immutable round record (a nullable column/field, so old data is unaffected). At debrief, list the reflections beside each round's actual KPI moves.
**Safety:** New optional field, backward-compatible (null for existing sessions). One screen you already gate on (`roundChanged`), so no new route. Make it skippable-by-facilitator-config to preserve pacing for fast cohorts.

### B3 🟡 Lead the round recap with *attributable* KPI moves
**Where:** `backend/round_recap_engine.py:generate_round_recap` (already ranks events by `treasury_delta`/`reputation_delta` magnitude).
**How:** The engine already emits discrete named events with deltas. Tag each event with a `source` enum — `decision` (caused by this round's choice), `drift` (passive decay/natural drift, burnout drift, macro noise), or `stochastic`. Then have the recap render two groups: **"Because of your decision"** (top 2–3 `decision` deltas) and a collapsed **"Background movements"** (drift/stochastic). You're not changing any number — only labelling and ordering what you already produce.
**Safety:** 🔵 Additive metadata on events + presentation grouping. Totals are identical; attribution just becomes legible. This is the highest-leverage pedagogy change and it's a labelling exercise, not a math change.

### B4 ⚪ Name the misconception ("the deferred-cost trap")
**Where:** `DebriefReport.js`, triggered by the existing `electronics_blindspot` flag.
**How:** When that flag fired (R1 audit skipped → R4 severity doubled), render a titled callout: *"The Deferred-Cost Trap — skipping the R1 audit felt free; it doubled your R4 crisis. Sustainability spend deferred is not sustainability spend avoided."* Gate purely on the flag you already set.
**Safety:** Conditional copy block; no logic. Portable lesson, zero risk.

### B5 🟢 Live "teachable moment" flags for the facilitator
**Where:** Facilitator dashboard (`admin/facilitator/page.js` / `FacilitatorTeleprompter.js`), fed by `terminal_valuation.py:get_flag_dependency_graph` + per-cohort decision tallies you already store.
**How:** Compute, per round, a cross-team tally of chosen flags; when N teams converge on a flag the dependency graph marks as forfeiting a bonus (e.g., `insurance_only` → blocks +0.20 resilience), push a non-blocking teleprompter note: *"3/5 teams chose insurance-only in R5 → all forfeited the +0.20 resilience bonus. Pause and discuss."* This is a read-side aggregation over existing decision data + the existing graph.
**Safety:** 🟢 Read-only aggregation surfaced to the facilitator only; players see nothing change. Uses the WebSocket admin channel you already have.

### B6 🔵 Accessibility pass on the decision flow (WCAG-AA)
**Where:** the commit path components — `DecisionTile.js`, `ExecutiveCockpit.js`, `FocusOverlay.js`, modals.
**How:** Scope the first pass to the *decision flow only* (not all 228 components): (1) add `role`/`aria-pressed` to tiles and `aria-live="polite"` to the KPI region so screen readers announce post-commit deltas; (2) ensure the commit action is reachable and triggerable by keyboard (Enter/Space) with a visible focus ring; (3) verify contrast against your existing `--color-*` tokens; (4) extend the single `prefers-reduced-motion` guard to wrap the cockpit's animations. Do it as a checklist against the existing `design:accessibility-review` skill.
**Safety:** 🔵 Semantic/attribute additions + focus styles; no behaviour change for mouse users. Widens participation without touching logic.

---

## C. Visual System (reads as "finished" on a projector)

### C1 🔵 Consolidate onto the tokens you already have
**Where:** `globals.css` already defines `:root`/`[data-theme]` with `--space-*`, a `--fs-*` `clamp()` scale, and a light block. The drift lives in the ~140 `*.module.css` files.
**How:** This is mostly *done* — the task is enforcement, not creation. Grep the modules for hardcoded hex and px (`#`, `px`) and replace with the existing custom properties. Add a Stylelint rule (`declaration-property-value-disallowed-list`) to block raw hex/px in new CSS so drift can't return. Do it file-by-file; each is independent and low-risk.
**Safety:** 🔵 Behaviour-preserving substitution of equal values by variable. Roll out incrementally; visual output is identical where tokens already equal the hardcoded values, and consistent where they didn't.

### C2 🟢 Colour-blind-safe KPI encoding; reserve red for danger
**Where:** the KPI/gauge components (`CapitalGauges.js`, KPI chips) + `--color-*` tokens.
**How:** Define semantic tokens — `--kpi-good`, `--kpi-warn`, `--kpi-danger`, `--kpi-neutral` — using a colour-blind-safe ramp (e.g., blue/teal for good, amber for warn, red *only* for danger), and pair colour with a shape/icon (▲▼ or arrow) so hue is never the sole signal. Point the gauges at these tokens.
**Safety:** 🟢 Token indirection + an icon; no threshold logic changes. A glance-across-the-room win.

### C3 🔵 Design the light theme (don't just invert)
**Where:** the `[data-theme="light"]` block in `globals.css`.
**How:** Treat light as a first-class palette: set surface/elevation, border, and muted-text tokens explicitly for bright rooms (higher surface contrast, softer accent saturation) rather than inheriting inverted dark values. Validate with the contrast checks from C2.
**Safety:** 🔵 Scoped to the light token block; dark theme untouched. Toggling remains identical.

### C4 ⚪/🟢 Ration the spectacle
**Where:** Three.js usage (`ESGImpactConstellation`, any 3D) vs. Recharts dashboards.
**How:** Policy, not rewrite: keep working dashboards on flat Recharts/CSS; reserve Three.js for debrief/ambient moments (constellation, rewind). If any per-round dashboard currently mounts a 3D scene, lazy-load it or gate it behind an "expand" so the decision screen stays fast.
**Safety:** ⚪ mostly a guideline; where you lazy-load, it's 🟢 and improves perf. No feature removed.

---

## D. UX & Robustness

### D1 🔵 Cognitive load — "one primary decision per round"
**Where:** `page.js` (1,685 lines) + `ExecutiveCockpit.js`; you already have `FocusOverlay.js`.
**How:** Make Focus Mode the *default* landing for a round: the crisis + the decision tiles front-and-centre, with dashboards/minigames/analytics behind tabs or a drawer ("Details", "Analytics", "Stakeholders"). You don't need to delete components — just change default visibility/progressive disclosure. Optionally, mechanically split `page.js` by extracting the WebSocket effect, the mailbox effects, and the broadcast handling into hooks (`useBroadcastSocket`, `useMailboxEvents`) — pure refactor, same behaviour.
**Safety:** 🔵 Re-parents existing components behind disclosure; all features remain reachable. Ship behind a facilitator/God-Mode flag first, compare, then default it.

### D2 🟡 Projector/responsive reality (1024px & 720p)
**Where:** `globals.css` (3 `@media` blocks), `page.module.css` (1), cockpit modules.
**How:** Add breakpoints at 1280×720 (projector) and ~1024px (laptops). Because you already use a `clamp()` type scale and `--space-*` tokens, most reflow is CSS-only: switch KPI rows and decision tiles to `flex-wrap`/`minmax()` grids so gauges reflow instead of clipping. Test with the browser at those sizes.
**Safety:** 🟡 Additive media queries; desktop layout above the breakpoints is unchanged.

### D3 🟡 State-loss UX (memory-DB dies on restart)
**Where:** DB selection in `main.py` (`USE_MEMORY_DB`), `useSimulation.js` (already has try/catch + demo fallback + autosave interval), `layout.js` `ErrorBoundary`.
**How:** Two independent, non-breaking layers. (1) Backend: offer a persistent **SQLite** default for graded sessions alongside the existing memory/Postgres options — a third `database_sqlite` module behind the same interface `main.py` already swaps on; keep memory mode as the explicit demo flag. (2) Frontend: since `useSimulation` already saves on an interval, add a small save-state indicator ("Saved ✓ / Saving…") and, when `database == memory`, a dismissible banner: *"Demo mode — progress is not saved across a server restart."* Drive the banner off the `/health` response you already return (`"database": "memory"`).
**Safety:** 🟡 New optional DB backend implementing the existing contract (no call-site changes); frontend banner reads an existing field. No change to game logic.

### D4 🔵 Centralise number formatting
**Where:** currency is formatted inline in `page.js`, `ConsequencePreview.js`, `DecisionTile` (`fmtCurrency`), mailbox, etc.
**How:** Create `frontend/app/utils/format.js` exporting `fmtCurrency`, `fmtPct`, `fmtNumber` (single source of the `$X.XM / $X.XK` rules). Replace the inline copies. Do it as a mechanical find-and-replace, one component at a time.
**Safety:** 🔵 Behaviour-preserving extraction; if you match the existing rounding rules, output is byte-identical. Prevents future drift between panels.

### D5 🟢 Verify every async panel has an "unavailable" empty-state
**Where:** `AIAdvisor.js`, `BenchmarksPanel.js`, `PeerComparison.js`, and any panel doing its own fetch.
**How:** Standardise a tiny `<PanelEmptyState reason="unavailable" />` and ensure each panel's catch path renders it instead of nothing. `useSimulation` already models this pattern (error + fallback); mirror it per panel. A hung advisor/benchmark call then shows "temporarily unavailable," never a blank region.
**Safety:** 🟢 Additive fallback UI in existing catch branches. No happy-path change.

### D6 ⚪ Sub-3-minute Round 1 (cold executive, no manual)
**Where:** `OnboardingWalkthrough.js` / `OnboardingWizard.js`.
**How:** Run a timed dry-run: a first-timer should reach a committed R1 decision in under 3 minutes. If not, trim the walkthrough to three steps — *what you're deciding, how to commit, where your KPIs are* — and defer everything else to contextual tooltips. This is a content/sequencing edit to the walkthrough steps array, not new machinery.
**Safety:** ⚪ Copy/step-order change in an existing component. No flow impact beyond onboarding.

---

## Suggested sequencing (lowest risk → highest leverage)

1. **Pure content, ship today (⚪):** A1 synergy note, A2 provenance doc, B4 deferred-cost trap, A4 determinism chip, D6 onboarding trim. No code paths touched.
2. **Additive UI (🟢):** A3 evidence artifacts, B1 consequence one-liner, B5 facilitator flags, C2 KPI colours, D5 empty-states.
3. **Additive state, backward-compatible (🟡):** B2 reflection box, B3 attributable recap (highest pedagogy leverage), D2 responsive breakpoints, D3 SQLite default + save indicator.
4. **Behaviour-preserving refactors (🔵):** C1 token consolidation + Stylelint guard, C3 light theme, D1 focus-first disclosure, D4 format util, B6 accessibility pass.

**Global guardrails that keep the simulation intact:** none of the above alters `engine.py`, `round_logic.py`, or `terminal_valuation.py` math — they surface, label, or re-parent data you already compute. Land each behind a facilitator/God-Mode toggle where it changes what players see (B2, D1), run the existing test suite after each 🟡/🔵 change, and keep the Monte-Carlo/parity artifacts (A3) as your regression evidence that balance is unchanged.

---

*Want me to implement any tier? Tier 1 (pure content) is safe to apply now with zero risk to flow; I'd recommend starting there and validating in a dry-run before the 🟡/🔵 items.*
