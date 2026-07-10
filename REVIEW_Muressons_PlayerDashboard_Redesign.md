# Player Dashboard Redesign — Review & Implementation Plan

*Expert simulation-design + UI/UX review of the player cockpit. Grounded in the actual code, not the screenshot alone. Review and plan only — no code changed. Constraint honoured throughout: simulation logic, round flow, gating, scoring, and data flow stay functionally identical; this is a presentation-layer inversion, not a mechanics change.*

**Severity key:** 🔴 hurts decision quality / learning · 🟠 adds cognitive load or visual noise · ⚪ polish

---

## 0. What the code actually says

| Fact | Evidence |
|---|---|
| `ExecutiveCockpit.js` is a 4,260-line monolith with **44 imports** | file head |
| **402 inline `style={{}}` blocks** in the cockpit alone; its CSS module is 2,874 lines with only **2 `@media` queries** | grep counts |
| The round flow is implemented **twice**: once as the dense 3-column cockpit (center column, lines ~1760–2480) and again as the Focus-Mode stepped overlay (`gate → strategy → allocation → commit → results`, lines ~2937–3530) | section markers |
| A real **stage machine already exists**: `getFirstIncompleteStep()` derives the current stage purely from game state (`roundPrerequisiteMet`, `hasDecision`, `allocations`, `commitResults`) with auto-advance effects | lines 771–860 |
| Focus Mode **auto-opens every round** and players dismiss it to reach the dashboard; from R3+ the dismissal is remembered (D1 pref, `prefersDashboardRef`) | lines 803–850 |
| `page.js` (1,720 lines) stacks additional full-screen layers: username, briefing, crisis, CFO override, Shockwave takeover, broadcast banner, climate module overlays (z=21000), onboarding tour | page.js structure |

**The architectural diagnosis in one sentence:** the product maintains *two complete UIs for one flow* — the calm, stepped experience players actually need exists, but it is bolted **on top of** the dense cockpit as an overlay, so every round the player is shown the simple path, dismisses it, and lands in the maximal one. The redesign is an **inversion**, not an invention: make the stage-driven canvas the primary surface and demote the dense cockpit to progressive disclosure around it.

---

## 1. Findings

### F-P1 🔴 Two parallel flow implementations compete for the player's attention
The bottom stepper (Read Briefing → Stakeholder Map → Strategic Decision → Capital Allocation → Commit Turn), the center column's gate/tiles/deployment sections, and the Focus-Mode overlay all express the same five stages. Players see the flow, a copy of the flow, and a summary of the flow simultaneously. Beyond confusion, this is a maintenance trap: every round-mechanic change must be mirrored in two render paths (and demonstrably has drifted — the overlay and center column style the same decisions differently).

### F-P2 🔴 Everything is on screen at once; nothing is the obvious next action
The screenshot state is Round 1 *orientation* — the player's only real job is "read briefing, do the stakeholder map." Yet the viewport simultaneously shows: 5 KPI cards, a 3-tab left panel, 10 launcher buttons, competitor intel, a 4-tab right rail, mailbox items, market feed, readiness gauge, capital-allocation CTA, strategic options A/B/C, 4 BU cards, a stepper, and a double-height market ticker. Sweller's cognitive-load citation is *rendered on the screen* while the screen violates it. The learning lives in the decision; the UI buries the decision.

### F-P3 🟠 Chrome overload: ten global launchers, permanently visible
Podcast, Leaderboard, Badges, Advisor, Analytics, SDG Radar, Glossary, Sound, Log Out, plus Narrative Crises and Focus Mode — eleven always-visible entry points in the left rail for functions used a few times per session (or never mid-decision). Each is a decorated pill with its own icon and color.

### F-P4 🟠 Duplicated information surfaces
KPIs appear in the left panel, the focus-mode KPI strip, and (partially) the header. Competitor intel appears in the right rail header *and* the left panel. Market events appear in the Market Reality Feed *and* the bottom ticker. Round narrative appears in the left rail *and* the center header *and* the mailbox. Every duplication is a synchronization risk and a visual tax.

### F-P5 🟠 No visual grammar: 402 inline styles, ~7 competing accent colors, two media queries
Cyan (LIVE/resources), purple (competitor), orange (focus/allocate), green (success/eco), red (crises), indigo (round chips), amber (gold accents) all fight at equal intensity, so *semantic* color (danger, success) has no privileged meaning. Type sizes are ad-hoc (0.6rem–1.5rem continuum). With 2 media queries in 2,874 CSS lines, the layout effectively has one breakpoint: "big projector" — yet sessions run on mixed laptops (prior review's projector finding, still unaddressed on the player side).

### F-P6 🟠 Overlay stack is a z-index battlefield
Crisis interstitial, Shockwave takeover, broadcast banner, climate modules (z=21000), focus overlay, onboarding tour, prediction modal, results overlay, message modal — mounted across two files with hand-tuned z-indices and explicit "suppressed while tour is active" workarounds. Each new layer multiplies interaction bugs.

### F-P7 ⚪ Ambient theatrics compete with work surfaces
The double-row ticker, heartbeat animations, and gradient chips are excellent *between* decisions and on the projector, but they run at full intensity during allocation — the moment requiring the most concentration.

---

## 2. Redesign concept — "one flow, one surface"

### Principles
1. **The stage is the screen.** At any moment the center canvas renders exactly one thing: the current stage from the existing stage machine. Everything else is context, and context is collapsed until summoned.
2. **Invert, don't invent.** The five Focus-Mode step components become the *canonical* stage components rendered inline (no overlay). The dense cockpit content doesn't disappear — it becomes the disclosure layer around the canvas.
3. **Same state, same calls.** The stage machine, gating, commit payloads, WS handling, and every pedagogical trigger (prediction gate, tribunal, recap, crisis interstitials) are untouched. Only *where things render* changes.

### Target layout (desktop)

```
┌────────────────────────────────────────────────────────────────────┐
│ HEADER  logo · cohort/round/date · LIVE state · timer · ⋯ More menu │
├────────────────────────────────────────────────────────────────────┤
│ KPI BELT  Treasury ▲ · EBITDA · Reputation · Carbon · Green Fund    │  ← single KPI source
├──────────────────────────────────────────────────────┬─────────────┤
│                                                      │ CONTEXT RAIL│
│   DECISION CANVAS (stage-driven, one stage at a time)│ (collapsed  │
│   R1: Orientation → Gate → Strategy → Allocation →   │  by default;│
│       Commit → Results                               │  Mailbox ●3 │
│   Narrative header + the stage's single work surface │  Intel      │
│                                                      │  Engines    │
│   [∨ Expand: BU details · charts · advanced metrics] │  Feed)      │
├──────────────────────────────────────────────────────┴─────────────┤
│ STEPPER  ✓ Briefing → ✓ Map → ● Decision → Allocation → Commit     │  ← the only flow indicator
├────────────────────────────────────────────────────────────────────┤
│ ticker (single row, dims to 40% opacity while allocation is open)   │
└────────────────────────────────────────────────────────────────────┘
```

- **KPI belt** replaces the left panel's KPI tab as the single always-visible KPI source: 5 tiles, big numerals, delta-since-last-round arrows, colour-blind-safe glyphs (reusing the C2 work). Charts/advanced metrics move into the canvas's "Expand" drawer — same components, summoned not ambient.
- **Decision canvas** = the existing focus-step components rendered inline. The narrative/crisis text heads the canvas (single home for the round story). BU cards render *inside* the allocation stage where they're acted on, not as a permanent gallery.
- **Context rail**: the current right rail, kept, but collapsed to icon+badge tabs by default (`Mailbox ●3`); opens as a 380px slide-over. Nothing in it is required to complete a turn — that's what makes collapsing safe.
- **⋯ More menu** absorbs the ten launchers (Podcast, Leaderboard, Badges, Advisor, Analytics, SDG Radar, Glossary, Sound, Log Out). Advisor and Narrative Crises keep escalation rights: they may surface a badge/toast, never a permanent panel.
- **Dashboard mode survives** as "📊 Pinned dashboard" for the R3+ players who prefer it — the D1 preference already exists and simply flips the shell between *canvas-first* and *dense* arrangements. R1/R2 mandatory gates behave identically in both (they already do).

### Visual grammar (the "pleasing" half)
- **Tokens**: build on the existing `--kpi-*` / theme-var work — one spacing scale (8px grid), one radius (10px cards / 6px chips), one elevation pair, 4-step type scale (12/14/17/22px equivalent), `JetBrains Mono` reserved for numerals only.
- **Colour discipline**: one brand accent (the indigo already dominant), green/amber/red strictly semantic, everything else neutral slate. Cyan/purple/gold decorations retire. This alone restores meaning to red.
- **Card system**: one card component (header slot, body, footer) replacing the ~6 ad-hoc card styles; panels stop competing via borders-plus-glows-plus-gradients.
- **Motion discipline**: framer-motion stays for stage transitions and results reveals; ambient pulsing limited to LIVE dot and crisis states; ticker single-row and dimmed during allocation (F-P7).

---

## 3. Architectural changes required

1. **Extract the stage machine** into `hooks/useRoundStage.js`: verbatim move of `getFirstIncompleteStep`, the auto-advance effects, and the D1 preference. Same inputs, same outputs, one home. (This is the load-bearing refactor — everything else composes on it.)
2. **Decompose `ExecutiveCockpit.js`** (4,260 lines) into a layout shell + region components: `CockpitHeader`, `KpiBelt`, `DecisionCanvas` (hosting the five stage components extracted from the focus-overlay blocks), `ContextRail`, `UtilityMenu`, `FlowStepper`, plus the existing overlay components. Pure file moves first, behaviour-preserving; the shell then arranges regions per mode (canvas-first vs pinned dashboard).
3. **Delete the duplicate flow render** (the center-column re-implementation) once the canvas hosts the canonical stage components — the single biggest simplification and the single biggest risk, hence isolated in its own phase behind the mode switch.
4. **Design tokens file** (`app/styles/tokens.css` or extension of `globals.css` vars) + migrate inline styles *per touched region only* (a mass rewrite of 402 inline styles in one pass is the kind of "easy workaround" that produces regressions; the token system makes each subsequent touch cheaper instead).
5. **Overlay coordinator**: one `<OverlayHost>` mounting crisis/shockwave/broadcast/climate/tour/modals from a small priority list, replacing hand-tuned z-indices and the "suppress while tour active" special cases. Overlay *content* unchanged.
6. **Rollout switch**: keep both shell arrangements compiled and choose via one boolean. Recommended: flip by commit on a branch (house rollback style — `git revert` restores the old shell wholesale). If you want runtime control instead, a `player_ui_v2` key in god-mode global settings works, but requires one Pydantic field in `GlobalSettingsPatch` — a backend touch; flag it consciously rather than sneaking it in.

---

## 4. Phased implementation plan

Same protocol as the admin phases: one commit per phase, per-phase testing checklist, `git revert` rollback, endpoint-contract diff (this time the *player* HAR: `/dashboard`, `/pillar-config`, `/commit-turn`, WS — none may change), and the repo's `test_api_flow.py` smoke after every phase.

### Phase A — Foundation (zero visual change)
Extract `useRoundStage`; split cockpit into region files by verbatim move; introduce tokens file (defined, not yet applied); add `OverlayHost` wrapping the existing overlays in current z-order.
**Test:** pixel-diff screenshots per stage (R1 gate, strategy, allocation, commit, results) — must be identical; commit-turn HAR byte-identical; focus auto-open/dismiss/D1 behaviour unchanged; full player smoke.
**Rollback:** revert; no state or CSS semantics changed.

### Phase B — Visual grammar on the existing layout
Apply tokens/type/colour/card system to the current arrangement (no layout moves): KPI cards, tiles, rail panels, chips. Retire non-semantic accents. Single-row ticker + allocation dimming.
**Test:** contrast audit (WCAG AA on decision path); screenshot review on 1280×720 projector + 1366×768 laptop; no DOM-structure diffs beyond class/style attributes.
**Rollback:** revert restores old styles; token file is additive.

### Phase C — Chrome simplification
⋯ More menu absorbs the launchers; context rail collapses to badge tabs with slide-over; de-duplicate KPIs/intel/feed to single sources (left-panel KPI tab content merges into belt + expand drawer).
**Test:** every absorbed function reachable in ≤2 clicks and keyboard-accessible; mailbox badge counts match; nothing required for a turn lives only in a collapsed surface (walk all 5 stages with the rail closed).
**Rollback:** revert; launchers return.

### Phase D — The inversion (highest risk, isolated)
Stage components render inline in the Decision Canvas as the default; the center-column duplicate flow is removed; Focus-Mode overlay retires (its components live on as the canvas); D1 pref becomes the canvas/dashboard shell switch; "pinned dashboard" arrangement retained for R3+ opt-outs.
**Test:** the critical suite — R1→R3 full-round walkthrough in both shell modes; mandatory R1/R2 gates block identically; prediction gate/confidence/recap/tribunal/R6/R7 scaffolds fire at the same stage boundaries (toggle each in god-mode and verify); commit payloads and `/dashboard` responses byte-identical to Phase 0 capture; crisis interstitial and Shockwave still take over above the canvas; results overlay → next round transition timing unchanged (auto-advance effects untouched in the hook).
**Rollback:** flip the shell boolean (old arrangement still compiled) or revert the commit.

### Phase E — Responsive + polish
Breakpoints at 1280 / 1024 / 768 (rail becomes bottom sheet, belt scrolls, canvas full-width); reduced-motion pass; focus-order/keyboard audit of the five stages; delete dead focus-overlay CSS.
**Test:** 720p projector and 13″ laptop walkthroughs; `prefers-reduced-motion` honoured; axe/Lighthouse a11y pass on each stage.

**Sequencing rationale:** A and B are invisible-risk enablers; C is reversible chrome; D is the only phase that touches *which component renders the flow* and sits behind a one-line switch; E hardens. At every phase the backend, `useSimulation.js`'s WS/session logic, and all engine/pedagogy code remain untouched — the stage machine is *moved*, never modified.

### Explicitly rejected easy workarounds
- **"Just make Focus Mode default and hide the dashboard"** — hides the duplication instead of removing it; two flow implementations keep drifting, and R3+ veterans lose their dense view.
- **"CSS-only cleanup"** — restyling both duplicate surfaces makes them prettier and still doubles cognitive load; F-P1/F-P2 are structural.
- **"Feature-flag everything at runtime from day one"** — a settings-driven dual-UI matrix doubles the test surface permanently; one boolean at Phase D with compiled fallback is the honest version.

---

*Verification assets to reuse: `test_api_flow.py` (player smoke), the admin phases' HAR-contract method, and `pytest` (961 green) as the backend-untouched tripwire. Happy to start Phase A — it's pure extraction and pixel-identical by definition.*
