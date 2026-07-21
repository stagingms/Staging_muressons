# Autonomous Stakeholders — Caricature Redesign Plan

*Design-thinking + animation + simulation-pedagogy review of the player
"Autonomous Stakeholders" panel (`frontend/app/components/StakeholderAgentPanel.js`,
373 lines; agent identities in `backend/autonomous_agents.py`). Grounded in the
code, not the screenshot alone. **Review and plan only — no code changed.**
Hard constraint honoured throughout: the agent state machine, tolerance math,
escalation thresholds, cascade logic, data flow, and scoring stay functionally
identical. Every recommendation is a presentation-layer change to how the same
numbers and the same five stages are drawn.*

---

## 0. What the code actually does (so nothing here breaks it)

Each of the five rows is one `AgentCard`. Today it renders, per agent:

- **A header** — `avatar_emoji` + `icon` + `name` + `title`.
- **A stage badge** — from `STAGE_META[stage]`: a 5-state machine
  `dormant → watching → agitated → hostile → triggered`, each with a **color**
  and emoji (`😊 #10b981` → `👀 #f59e0b` → `😠 #f97316` → `🔥 #ef4444` →
  `💥 #dc2626`) and an `order` used to sort most-critical-first.
- **A `ToleranceBar`** — a flat horizontal track whose fill **width =
  `tolerance / max_tolerance`** and whose **color = the stage color**, plus
  `zoneMarker` ticks at each escalation threshold and a numeric tolerance label.
- **An expand drawer** — dialogue/`message`, red-line `violations`, a stats row
  (Patience, Tolerance Δ, Trend), and any `triggered_event`.

Data arrives already-computed from the backend as `agentSummary` (baseline) +
`agentActions` (this round's action, overrides summary on merge). The five
agents are stable, keyed by `agent_id`:

| `agent_id` | Persona | Archetype | Brand color | Escalation thresholds (tol) |
|---|---|---|---|---|
| `the_regulator` | Commissioner Eleanor Carson | Regulator / Auditor | Indigo `#6366f1` | 65 / 45 / 25 / 10 |
| `the_gen_z_employee` | Greta Berg | Labour / Workforce | Pink `#ec4899` | (per-profile) |
| `the_institutional_investor` | Marcus Chen-Hoffmann | Shareholder / Capital | Amber `#f59e0b` | (per-profile) |
| `the_community_activist` | Megha Patrike | Community / Environment | Emerald `#10b981` | (per-profile) |
| `the_journalist` | Jay Buffet | Media / Press | Violet `#8b5cf6` | (per-profile) |

**Two independent signals live in every row today, and the redesign must keep
both:** *who* the stakeholder is (identity — shape + name + brand color) and
*how agitated* they are (state — the stage color + tolerance level). The flat
bar currently carries the state signal; the tiny emoji carries identity. The
bar is legible but inert — a green rectangle that turns red. That is the whole
opportunity.

---

## 1. Design-thinking frame

**Empathise — who is here, when?** A player mid-round scanning a rail tab to
answer one question per stakeholder: *"Is this group calm, or am I about to
provoke them?"* The panel is *asynchronous context* (a rail tab in the slotting
rule), glanced at between decisions — not a surface anyone reads slowly.

**Define — the one thing each row must telegraph at a glance:** the **emotional
state** of a specific, recognisable stakeholder. A bar communicates a magnitude
but not a *mood*; yet the pedagogy here is explicitly about **autonomous agents
with feelings, patience, and red lines** (Mitchell Stakeholder Salience). A face
communicates mood in one fixation; a bar makes you read a number and translate.

**Observe — what the current row under-sells:**
1. **Mood is abstract.** "DORMANT / 75" asks the eye to decode a badge + a
   number. Five near-identical green bars read as a spreadsheet, not as five
   living stakeholders with distinct temperaments.
2. **Identity is a 16px emoji.** The regulator, the worker, the investor, the
   community leader, and the journalist — five vivid archetypes — are reduced
   to interchangeable rows.
3. **Escalation has no drama.** The single most important teaching moment is a
   stakeholder *escalating*; today that is a bar changing width and hue, easy
   to miss in a rail tab.

**The governing idea:** *make each stakeholder a face whose expression and
colour are their state.* Replace the inert bar with a **simple caricature per
archetype** that (a) is instantly recognisable as *that* stakeholder, (b)
**recolours across the five stages** (calm green → furious dark-red), and (c)
**changes expression and micro-animation** with the stage — while still carrying
the exact tolerance number and threshold zones the bar carried. Identity via
*shape*, state via *colour + expression*: two orthogonal signals, no information
lost.

---

## 2. Design concept

### 2.1 One caricature per archetype (identity = shape, not colour)
Five original, geometric, **line-art** caricatures built on a shared "face rig"
(head, two eyes, brows, mouth) plus an archetype-defining prop/silhouette so each
is unmistakable **without relying on colour**:

- **Regulator (Carson)** — official/judicial: a subtle wig or peaked cap +
  balance-scales motif; square spectacles; composed.
- **Labour (Berg)** — a raised-fist silhouette beside the head; bandana/beanie;
  youthful, expressive brows.
- **Shareholder (Chen-Hoffmann)** — suit collar + tie; a small candlestick-chart
  glint; sharp, appraising eyes.
- **Community (Patrike)** — a leaf/hill motif + headscarf; warm, rounded features.
- **Media (Buffet)** — a "PRESS" hat-band + notebook/pen or mic; one raised
  eyebrow, perpetually curious.

Because identity is carried by silhouette, the **fill colour is freed to encode
state**. The agent's **brand colour is retained as a thin accent** (a prop tint
or a 1px identity ring) so the persona stays anchored even at the reddest stage.

### 2.2 Colour + expression = the five stages (the core ask)
The caricature's face **fills with the stage colour** and its **expression
morphs** across the exact same five states the engine already emits, from the
single source of truth `STAGE_META`:

| Stage | Colour (today) | Face / expression |
|---|---|---|
| `dormant` | green `#10b981` | soft closed-mouth smile, relaxed brows, slow blink |
| `watching` | amber `#f59e0b` | neutral mouth, one raised brow, eyes tracking |
| `agitated` | orange `#f97316` | slight frown, tightened brows |
| `hostile` | red `#ef4444` | hard frown, furrowed brows, a heat/sweat accent |
| `triggered` | dark-red `#dc2626` | mouth open (shout), a one-shot burst/flash |

No new states, no new colours — the caricature is a *richer renderer of the
state the engine already computes.*

### 2.3 Tolerance is preserved — as a ring, not dropped
The bar's quantitative payload (tolerance 0–100 + the four threshold zones) is
**not lost** — it is re-encoded as a **radial gauge ring** around the caricature:
the ring's sweep = `tolerance / max_tolerance` (identical math), with **tick
marks at the four escalation thresholds** (watching/agitated/hostile/triggered)
and the **numeric tolerance retained** at the ring's base. So one figure now
carries all three signals the row used to spread across an emoji + a badge + a
bar: *who* (silhouette), *how agitated* (colour + face), *how close to snapping*
(ring + number). This is the anti-workaround: richer, not lossier.

### 2.4 Animation as state (the "make it feel alive" layer)
Each stage gets a **signature micro-animation**, so the panel reads as five
living agents rather than five gauges — all built on `framer-motion` (already a
dependency) and all **`prefers-reduced-motion` aware**:

- `dormant` — slow "breathing" scale (1 ↔ 1.02, ~4 s), occasional slow blink.
- `watching` — eyes drift side-to-side; a single deliberate brow-raise.
- `agitated` — a faint 1–2 px shiver every few seconds; a finger-tap tempo.
- `hostile` — a continuous low tension tremor; a rising heat/steam accent.
- `triggered` — a sharp shake + one-shot flash/burst, then a "spent" settle;
  reuses the existing `agentTriggered` / `agentStageChanged` pulse classes.

**Reduced-motion:** every animation collapses to a *static* per-stage
expression + colour (frown depth, eye shape, ring level) — no shake, tremor, or
flash — matching the reduced-motion discipline from the CA-D / V-D passes.

### 2.5 Visual grammar
Migrate the stage colours to `app/styles/tokens.css` semantic tokens
(`--positive` / `--caution` / `--danger`) where they map, so the caricature,
badge, and ring share **one** stage-colour source (hue decisions happen on the
real screen, never a blind regex — per the tokens.css Phase-B note). One card
style, raised numeral contrast, consistent baseline across the five rows so the
column of faces scans top-to-bottom like a mood board.

---

## 3. Architecture (fits the existing structure — no logic touched)

- **New pure-presentational component** `StakeholderCaricature.jsx` (single
  file), props only:
  `{ archetypeKey, stage, tolerancePct, thresholds, brandColor, reducedMotion, size }`.
  Renders one inline `<svg>`: a shared face rig + an archetype prop layer, filled
  by a CSS var `--stage-color`, expression chosen by `stage`, wrapped in the SVG
  ring gauge. No fetches, no state beyond animation.
- **`agent_id → archetypeKey` map** with a **generic-stakeholder fallback**, so
  the panel is robust if a cohort's config adds/renames agents (no hard
  dependency on exactly these five). `agent_id` is already in the payload.
- **`AgentCard` change is one swap:** the `<ToleranceBar>` (and the redundant
  header emoji) are replaced by `<StakeholderCaricature>`; header text, stage
  badge, trend, expand drawer, stats, violations, cascade log — **untouched**.
- **Slotting rule compliance:** this panel is a *Rail tab* (asynchronous
  context) — the change stays inside one existing slot; no new always-visible
  surface is created. `STAGE_META` remains the single stage→colour source.
- **Zero backend / contract change:** no new fields, no new requests; the
  caricature is a different renderer of `agentSummary` + `agentActions`.

---

## 4. What must NOT change (verified against the code)

- `agentSummary` / `agentActions` / `cascadesFired` / `interferenceActive` data
  shapes and the merge (`action` overrides `agent`).
- `STAGE_META` stages, `order`, and the sort-by-severity; the escalation
  `thresholds`; the `tolerance / max_tolerance` math and numeric readout.
- The expand drawer: dialogue, red-line `violations`, Patience / Tolerance Δ /
  Trend, `triggered_event`; the interference + cascade sections.
- `backend/autonomous_agents.py` — profiles, decay/recovery, cascades: untouched.
- Only the **visual encoding** of (identity, stage, tolerance) inside `AgentCard`
  changes: an inert bar becomes an expressive figure carrying the same data.

---

## 5. Phased plan (same protocol as the V- / CA- series)

One commit per phase · jest + player smoke green · endpoint-contract unchanged
(this panel sends no requests) · screenshot diff per stage · `git revert`
rollback. All within `StakeholderAgentPanel.js` + the new component + CSS.

**Phase SA-A — Caricature scaffold (non-destructive).** Build
`StakeholderCaricature` with the five archetype SVGs + the generic fallback,
*static*, stage-coloured via CSS var; render it **alongside** the existing bar to
validate the `agent_id → archetype` mapping and recolour across all five stages.
*Test:* all five + fallback render; recolour correct at each stage; zero data
change.

**Phase SA-B — Fold in the tolerance ring, retire the bar.** Add the radial
gauge (sweep = `tolerance/max_tolerance`) + threshold ticks + numeric tolerance
into the caricature; remove the flat `ToleranceBar`. *Test:* ring sweep and ticks
match the old bar exactly; number identical; no zone information lost.

**Phase SA-C — State animation.** Add the five signature micro-animations via
`framer-motion` variants keyed on `stage`; `prefers-reduced-motion` fallback to
static expressions; reuse the existing triggered/stage-changed pulses. *Test:*
each stage animates distinctly; reduced-motion is fully static; no layout shift;
triggered flashes once then settles.

**Phase SA-D — Polish, tokens, a11y.** Migrate stage colours to `tokens.css`
semantic tokens (single source); add `role="img"` + an `aria-label`
("Commissioner Carson — Watching; tolerance 62 of 100; worsening"); check
1280 / 1024 widths and the collapsed-panel state; verify WCAG AA contrast on all
five stage colours. *Test:* contrast + screen-reader pass; jest; player smoke;
screenshot diff shows five expressive rows, same data.

**Sequencing rationale:** SA-A is invisible-risk (additive) and proves the
hardest bit (identity mapping + recolour) first; SA-B is a like-for-like data
re-encode; SA-C and SA-D are additive polish. At no point do the stages,
thresholds, or tolerance math change — the state a player reads is byte-identical
to today's, only more legible and alive.

---

## 6. Explicitly rejected easy workarounds
- *"Just swap the emoji per stage (😊→😠→🔥)."* Not a caricature, no identity,
  no tolerance encoding, no animation range — it's the current badge with extra
  steps.
- *"Make the bar taller / add a gradient."* Fixes nothing: the row still reads as
  a gauge, not a stakeholder with a mood.
- *"Drop the tolerance number and threshold zones to simplify."* That number is
  the pedagogy (how close to triggering); re-encode it in the ring, never delete
  it.
- *"Use PNG/portrait images."* Can't recolour per stage cleanly, no crisp
  animation, heavier, and risks depicting real likenesses. Inline SVG line-art
  only.
- *"Hardcode exactly five agents."* Brittle to cohort config; drive off
  `agent_id → archetype` with a generic fallback.
- *"Colour the caricature by the agent's brand hue."* That would break the core
  requirement ("colour changes with state"); brand hue is relegated to a thin
  identity accent so *shape* carries identity and *colour* carries state.
- *"Copy a recognisable caricature style or a real person."* Original geometric
  line-art for fictional personas only — non-photoreal, non-defamatory.

---

*Recommendation: SA-A + SA-B make a tight, low-risk first cut — they deliver the
five recognisable, state-coloured faces and preserve every number, with zero risk
to the agent state machine. SA-C + SA-D bring the animation and polish. Ready to
implement on your go, in the V-/CA-series style.*
