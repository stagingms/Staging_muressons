# Player Dashboard v2 — Simplification Review & Plan

*Grounded in the current tree (2026-07-11, branch `ux/v3-phases`), the attached
screenshot (R2, Double Materiality Gate, BU drill-down open), and the v1
redesign review. Review and plan only — no code changed. Constraints unchanged:
simulation logic, round flow, gating, scoring, and data flow stay functionally
identical; presentation layer only.*

**Severity key:** 🔴 hurts decision quality / learning · 🟠 cognitive load / noise · ⚪ polish

---

## 0. Ground truth — read the code before the screenshot

The v1 redesign (`REVIEW_Muressons_PlayerDashboard_Redesign.md`) **was fully
implemented**: Phases A–E all shipped (`useRoundStage.js` extracted; tokens.css;
Phase C rail collapse; Phase D inversion at `af4f0ef` with `CANVAS_FIRST = true`
live; Phase E responsive at `632c481`). The stage-driven Decision Canvas IS the
primary surface today.

**So why does the screenshot still look maximal?** Two reasons, both visible in
the history:

1. **The screenshot is the disclosure layer, working as designed but overgrown.**
   The player dismissed the canvas ("Re-enter Focus Mode" is showing), opened a
   BU drill-down, and the rail is expanded. The dense dashboard was deliberately
   preserved in Phase D as the browse/deep-dive layer — but it never got a
   density budget of its own.
2. **Six feature waves landed AFTER the redesign, without a slotting rule.**
   Measured against `ExecutiveCockpit.js` alone: W-A ticker/atmosphere/commit
   ceremony (+151 lines), W-B Nordhaven rival intel (+18), W-C Annual Report
   (+35), WOW-1/7/11 ConsequenceReplay/LivingPlanet/PressureTimer (+20),
   Improvements Playbook B2/B3 reflection + recap (+51) — plus
   `EngineEventsPanel`'s "What Happened This Round" and "Road Not Taken"
   accordions in the rail. Each arrived as a new always-visible surface.
   Inline styles: 373 (v1 counted 402; B-phase tokens exist but the new code
   didn't use them).

**Diagnosis in one sentence:** v1 fixed the architecture; the problem now is
**accretion governance** — the disclosure layer has quietly become a second
cockpit, and every new feature since the redesign bought screen space instead
of renting a slot.

---

## 1. Design-thinking frame

**Empathize — who is on this screen, when?** A student, mid-round, under a
countdown, who pressed "back to dashboard" for ONE of exactly four reasons:
check a KPI/chart, read mail, inspect a BU, or reconsider the options. Never
all four. The facilitator's projector is a fifth persona (W-A's atmosphere
exists for it) with opposite needs: ambient richness, zero interaction.

**Define.** The player needs *one* answer per glance: "what changed, and what
do I do next?" The screenshot answers everything simultaneously: four renders
of the same round directive (top bar chip, FOUNDATION card, mailbox item #1,
feed item #1), two competitor readouts (rail header bar + FTSE panel), last
round's retrospective ("Road Not Taken — you chose Option C") ABOVE the
current round's work, full Option A/B/C prose while the prerequisite banner
admits they can't be acted on yet, and three different ways back into the flow
(Re-enter Focus Mode, left-rail FOCUS MODE, the stepper).

**Ideate → the governing concept:** *the disclosure layer is a reading room,
not a second cockpit.* One primary per column; retrospect never outranks
prospect; locked content renders locked; every feature — existing and future —
occupies exactly one slot from a fixed menu.

---

## 2. Findings (anchored to the screenshot, verified in code)

### V-1 🔴 The disclosure layer shows all four "reasons to be here" at once
Charts panel + investment matrix + BU drill-down + strategic options + fully
expanded rail render simultaneously. The player who came to check one thing
must visually suppress the other three. Fix is structural (see §3): the center
column shows matrix **or** BU detail **or** options — the drill-down replaces,
never stacks; the left panel shows one tab; the rail opens one section.

### V-2 🔴 Locked options masquerade as live ones
Full Option A/B/C cards with complete prose, checkmarks, and costs render while
the prerequisite banner says the CSRD assessment is incomplete. Under time
pressure, reading 400 words of option text that cannot be selected is pure
sunk cost — and some players will believe they've "chosen" by reading.
**Fix:** pre-gate, options render as locked summary chips (title + one line +
🔒 "unlocks after CSRD assessment"); the full prose belongs to the strategy
stage in the canvas (where it already exists).
**Rejected quick fix:** greying the cards out. Grey full-prose cards still
cost the read; the content, not the opacity, is the load.

### V-3 🔴 Retrospect outranks prospect
"Road Not Taken — you chose Option C, here's what the alternatives would have
yielded" (last round's counterfactual) and "What Happened This Round" sit at
eye level in the rail, above the READY bar and next-step CTA. The
counterfactual is one of the best learning artifacts in the sim — in the
**results/recap stage**, where causality is fresh. Mid-decision it is
regret-bait competing with the current choice.
**Fix:** both accordions move into the results stage of the canvas (recap
already renders there — B3) and into the Archive; the rail keeps at most a
one-line "R1 recap ▸" link.

### V-4 🟠 Same fact, four renders
The round directive appears in the top bar, the FOUNDATION card, mailbox item
1, and feed item 1; competitor standing appears as the rail's TRAILING bar and
the left FTSE panel; three flow re-entry affordances. Each duplicate is a sync
risk (v1's F-P4 — the class returned with the new features).
**Fix:** single homes — directive: FOUNDATION card (top-bar keeps the short
chip); competitor: ONE intel row in the rail (FTSE benchmarks fold into the
Analytics drawer); flow re-entry: the stepper (the two buttons become one).

### V-5 🟠 The new features ignored the token system
Nordhaven purple/red bar, cyan RESOURCES button, orange Focus pill, gold
CAROIC, green ECO — the accreted surfaces reintroduced the accent competition
Phase B retired, because they shipped with raw inline colors (373 blocks).
**Fix:** apply the existing `tokens.css` to the six accreted surfaces only
(bounded, ~a day), and add the one-line rule to CLAUDE.md/review checklist:
*new player-facing UI must use tokens and claim a slot (§3) in the same
commit.* That rule is the actual fix; the restyle is cleanup.

### V-6 🟠 The stepper floats over content
In the screenshot the stepper overlaps the Option A card text (and its ✕
suggests dismissability — a flow indicator should not be dismissible). Dock it
to the bottom edge below the scroll area, always visible, never overlapping;
remove the ✕.

### V-7 ⚪ Ambient theatrics vs. concentration (residual)
Phase B dims the ticker during allocation stages; the dimming doesn't cover
the disclosure layer's browse state with the drill-down open, and the
stock-chart's -76.9% red header animates at full intensity beside the work.
Extend the existing `data-concentration` mechanism to drill-down state.

---

## 3. The slotting matrix (the governance fix)

Every player-facing surface gets exactly one home. Applied to today's
inventory:

| Slot | Rule | Goes here |
|---|---|---|
| **Canvas stage** | Needed to complete the current stage | Gate cards, strategy options (full prose), allocation matrix + BU cards, commit ceremony, results + **Road Not Taken** + **What Happened** + reflection box (B2) |
| **KPI belt** | Always-glanceable state | 5 KPIs + delta arrows; CAROIC grade chip |
| **Expand drawer** (center, on demand) | Deep-dive detail | BU drill-down, charts, FTSE benchmarks, TCFD/engine widgets, Annual Report (year-end) |
| **Rail tab** (one open at a time) | Asynchronous context | Mailbox ● / Market feed / ONE competitor-intel row / Decisions log |
| **⋯ More menu** | Occasional utilities | Podcast, Leaderboard, Badges, Glossary, Sound, Archive, Log Out |
| **Projector/atmosphere layer** | Facilitator theatre | Ticker (single row), LivingPlanet, atmosphere FX — auto-dim under `data-concentration`, OFF on <1280px |
| **OverlayHost** | Interrupts | Crisis, Shockwave, broadcast, tour (unchanged) |

The screenshot's center column then has exactly one occupant per moment:
matrix (allocation stage) → or BU detail (drawer, replacing it) → or locked
option chips (pre-gate). The rail is an accordion, one section open.

---

## 4. Phased plan (same protocol as every phase so far: one commit per phase,
player HAR byte-identical, `test_api_flow.py` smoke, screenshot diffs,
`git revert` rollback)

### Phase V-A — Retrospect to the recap (V-3) · lowest risk, highest calm
Move What-Happened + Road-Not-Taken accordions from the rail into the results
stage (components exist; this is a render-location move) + one-line recap link
in the rail. **Test:** results stage shows both after commit; rail shows link
only; mid-round rail no longer renders either; commit payload/HAR unchanged.

### Phase V-B — Locked-state truth (V-2) + single homes (V-4)
Locked option chips pre-gate (full cards remain the canvas strategy stage,
untouched); de-duplicate directive/competitor/flow-re-entry to the single
homes above. **Test:** pre-gate, no option prose in the disclosure layer;
post-gate behavior identical; all four directive renders reduced to two
(chip + card); one Focus re-entry; stepper unchanged.

### Phase V-C — One primary per column (V-1) + stepper dock (V-6)
Center column becomes exclusive (matrix ⇄ drill-down ⇄ locked chips — the
drill-down already has "← OVERVIEW", it becomes a true swap); rail becomes a
single-open accordion (Phase C's collapse logic extended, not rewritten);
stepper docks, loses ✕. **Test:** all four "reasons to visit" reachable in ≤2
clicks with the others hidden; Esc/1–4 BU switching unchanged; walk all 5
stages with rail closed (nothing required lives there — re-verify Phase C's
invariant).

### Phase V-D — Token pass on the accreted surfaces (V-5) + concentration
extension (V-7)
Bounded restyle of the six post-redesign surfaces with existing tokens; extend
`data-concentration` to drill-down; add the slotting rule to the repo's
review checklist. **Test:** visual diff on the six surfaces only; WCAG AA on
decision path; reduced-motion honored.

**Explicitly rejected easy workarounds:** hiding the disclosure layer behind
Focus Mode permanently (kills the legitimate browse persona and the R3+ D1
preference); a global "compact mode" toggle (doubles the test matrix — density
should be the default, not an option); restyling without re-slotting (v1's
lesson: prettier duplication is still duplication).

---

## 5. What this buys, in the player's terms

Mid-round glance answers "what changed / what's next" in one fixation path:
KPI belt → canvas stage → stepper. The reading room (mail, intel, charts, BU
detail) is one click away and shows one thing at a time. The counterfactual
lands at the moment of maximum learning instead of maximum distraction. And the
next feature wave has a rulebook, so this review doesn't need a v3.
