# Implementation — fourth pass, 2 Aug 2026

Closes every remaining item on the "Still open" list from pass 3, except the one
that needs a human with a screen reader (and that one now has its scaffolding).

## Verification

- **`npx next build` PASSES** — `✓ Compiled successfully in 44s`, 11/11 static
  pages. Fonts stubbed for the offline sandbox, `layout.js` restored and
  `diff`-verified byte-identical.
- **Backend: 1814 passed**, 6 skipped (was 1802 — 12 new).
- **Frontend jest: 33 suites, 841 passed**, 4 documented skips (was 835).

---

## Token migration (#20) — the ratchet moved

10 semantic-hex occurrences replaced with tokens, all of them `color:` on text —
the contrast-relevant case. `rawHex` baseline **1250 → 1240**. Seven files came
off the legacy lists; `LEGACY_Z_FILES` is now **empty** — all 12 z-index
offenders migrated into the documented scale.

Two judgement calls worth reviewing, both made because a straight token swap
would have been wrong:

1. **Three panels are hardcoded-light in both themes** (`DebriefReport.panel`,
   `RoundPacingControl.panel`, `ResourceSidebar.sidebar` set `background: #fff`
   unconditionally). Dropping `var(--kpi-good)` there fixes light mode and
   **breaks dark** — the token resolves to `#10b981` on white, 2.2:1, worse than
   what it replaced. Added theme-invariant bridge tokens
   `--kpi-good-on-light` / `--kpi-warn-on-light`. The real fix is making those
   three panels theme-aware; the bridge is documented as temporary.
2. **`.bronze` is a rank medal, not a warning.** `--kpi-warn` and
   `--accent-gold` are the same value, and `.gold` already uses `--accent-gold`
   — mapping bronze onto the warn token would have made 1st and 3rd place
   identical. Added `--medal-bronze`.

**11 gradient-stop occurrences were left alone** — each is
`linear-gradient(135deg, var(--token), #rawhex)` where the raw hex is the second
stop of a depth gradient. Replacing it flattens the button, which is restyling,
not a contrast fix. Flagged rather than silently changed.

The z-index scale had **no tier above a full-screen takeover**, which is exactly
why twelve files invented 9500–21500. An ordered band (9100–9700) was added to
`globals.css` rather than exceeding the ceiling, and relative order was preserved
exactly — including FacilitatorManager's deliberate 19000/19001 adjacency, now
9500/9501.

> **Needs a human eyeball.** Dark-mode hues shift on every swap
> (`#059669` → `#10b981`). The full checklist is in the pass-4 notes below and
> the agent's report: delta badges, the leaderboard's 1st-vs-3rd distinction in
> light mode, the three always-light panels in dark, and a stacking-order walk
> (join gate → balance sheet → prediction modal; drawer → delete confirm; BRSR
> portal with a side-track toast). Two stacking behaviours **deliberately
> change**: FacilitatorManager's delete-confirm now paints above its own drawer
> (it was behind it — a latent bug), and the DoubleMateriality dragged chip now
> paints above the onboarding overlay.

---

## WCAG (#18 follow-through) — automated floor + five real defects fixed

New `__tests__/a11y-axe.test.js` (jest-axe over Dialog, ConfirmModal,
JoinCohortModal, DecisionTile, RunBar, DebriefNarrative in 14 render states),
`docs/ACCESSIBILITY_MANUAL_TESTS.md` (a 45-minute NVDA/keyboard/zoom script with
SC references), and `docs/VPAT_DRAFT.md` (6 of 50 criteria pre-filled, 44 "Not
Evaluated", header stating plainly that an overclaimed VPAT is a legal
liability).

**axe found zero violations — and that is the finding.** The config was
sanity-checked against a deliberately broken tree and correctly caught
`image-alt`, `label`, `button-name`, `link-name`. So the tooling works, and a
hand review of the same markup still found **five genuine Level A defects axe
structurally cannot see**. All five are now **fixed**:

| ID | Component | SC | What was wrong |
|---|---|---|---|
| **F1** | JoinCohortModal | 1.3.1, 3.3.2 | Labels visually present but **not associated** — no `htmlFor`, no `id`. axe passed only because the placeholder supplied a name, which disappears on first keystroke. First screen every participant sees. |
| **F4** | DecisionTile | 1.3.1, 4.1.2 | `role="button"` is children-presentational, so the description, trade-off, cost and impact preview were **stripped from the a11y tree**. A blind participant made the product's central decision hearing only "Option A: Retrofit the Lyon plant". Fixed with `aria-describedby` (not suppressed by children-presentational). |
| **F5** | DebriefNarrative | 4.1.2, 2.4.3 | Declared `aria-modal` with **no focus trap** and rendered `{children}` twice (every table row announced twice). Now uses the `Dialog` primitive and renders children once. |
| **F2** | ConfirmModal | 1.3.1, 3.3.2 | Typed-phrase input's only name was its placeholder; the instruction was an unassociated sibling. Highest-consequence control in the admin surface. |
| **F3** | ConfirmModal | 4.1.2, 3.3.1 | Locked confirm button used `disabled` — removed from the tab order with no explanation, unlock never announced. Now `aria-disabled` + a polite live region. |

One assertion was **corrected rather than satisfied**: F5's original test required
zero focusable elements outside the dialog, which only `inert` on every sibling
or a portal delivers. WCAG 2.1.2 requires that focus cannot *leave* — a
Tab-cycling property. The test now asserts the real thing, with the reasoning
inline.

**What this does not prove:** conformance. The strongest evidence is in the
deliverable itself — axe returned clean while five Level A defects sat in the
same code. `ExecutiveCockpit`, the dnd-kit capital allocation (**the largest
Level A risk in the product**), the projector view, and all charts remain
unevaluated; 12 axe rules including `color-contrast` did not run in jsdom and are
carried as manual obligations.

---

## Per-BU consequence families (#21 follow-through)

Engines stamp the entity onto the *key*
(`talent_penalty_applied_pharma`, `npc_cascade_treasury_activist_fund`), and the
set is unbounded because verticals and NPC ids are configurable. These fell
through to the generic humaniser and read like variable names.

New `PER_ENTITY_FAMILIES` + `matchPerEntity()`: **18 families**, each verified
against a real `ctx.events[f"..._{bu_id}"]` write site in `engine.py`. The family
supplies the sentence, the suffix supplies the subject — so
`talent_penalty_applied_consumer_goods` now reads *"Consumer Goods carried a
talent penalty of 1.40× on its operating costs — people left faster than they
were replaced."* Longest-prefix matching means `technical_debt_streak_x` never
resolves against `technical_debt_penalty`. 6 new tests.

---

## `team_consensus` becomes honest (#7 follow-through, TEAM-3)

The field defaulted to `'majority'` in the model *and* was hardcoded by the
client, so the decision audit log asserted a majority decision for **every round
ever played** — including solo play and every server auto-commit. The debrief
question "how did your team decide?" was answered from fiction.

- `consensus_level` enum gains **`not_recorded`**; the column becomes
  `NULL DEFAULT NULL` in both `db/init.sql` and the auto-schema DDL.
- **Forward-only, idempotent migration** in `database.py` startup, matching the
  existing `metadata` column pattern: `ADD VALUE IF NOT EXISTS 'not_recorded'`,
  `DROP NOT NULL`, `DROP DEFAULT`. Existing rows are **not** rewritten —
  backfilling would be a guess about history, and those rows sit behind an
  immutability trigger.
- `BUDecision.team_consensus` is `Optional` with no default; neither store
  coerces a missing value.
- **Bug found and fixed:** the auto-commit paths wrote `"auto_default"`, which is
  **not a member of the Postgres enum** — that write would have violated the type
  on a real database. Both paths now write `not_recorded`, which is exactly what
  a server commit means.
- Client no longer pre-selects an answer; the selector starts unset.

New `tests/test_team_consensus_nullable.py` (12 tests), including a tripwire
asserting `engine.py`, `round_logic.py` and `terminal_valuation.py` never
reference the field — that is the whole safety argument for changing it against
a validated engine.

---

## Files touched

**Backend:** `models.py`, `database.py`, `database_memory.py`, `router.py`,
`admin_router.py`, `tests/test_team_consensus_nullable.py` (new).
**Schema:** `db/init.sql`.
**Frontend:** `globals.css`, 19 `*.module.css`, `ConfirmModal.js`,
`JoinCohortModal.js`, `DecisionTile.js`, `DebriefNarrative.js`,
`consequenceCatalog.js`, `page.js`, `__tests__/a11y-axe.test.js` (new),
`__tests__/consequence-catalog.test.js`, `__tests__/design-token-drift.test.js`,
`docs/ACCESSIBILITY_MANUAL_TESTS.md` (new), `docs/VPAT_DRAFT.md` (new).
`jest-axe` added to devDependencies.

## Still open

1. **The manual WCAG pass.** Everything automatable is automated; the rest needs
   a person, NVDA and 45 minutes. `docs/ACCESSIBILITY_MANUAL_TESTS.md` is the
   script. **Do not send the VPAT to anyone until that is done.**
2. **The visual check on the token migration** (list above). Nothing is known
   broken; hues shifted and no one has looked.
3. **CreateCohortModal wizard** — `PLAN_CreateCohort_Wizard.md`, awaiting your
   answers to its four questions.
4. **Three always-light panels** should become theme-aware, retiring the
   `--kpi-*-on-light` bridge tokens.
5. **11 gradient buttons** still run corrected-token → uncorrected-raw in light
   mode, so a white label sits on ~3:1 at the raw end. A real AA question, but
   the answer is a design decision about the gradient, not a find-and-replace.
