# Plan — Staged wizard for CreateCohortModal

**Audit item #19 (part two).** Pass 3 removed the *failure mode* (the 10-call
browser chain became one `apply-setup` call with a `dry_run` preview). This plan
covers the part deliberately left out: the form itself.

Status: **proposal, not started.** Nothing here has been implemented.

---

## 1. What is actually wrong

Evidence from `frontend/app/components/CreateCohortModal.js` (~3,300 lines):

| | |
|---|---|
| `useState` hooks | **84** |
| Accordion sections | 7 (numbered 1–7, plus a 2b) — any order, all openable at once |
| Hard validations | **3**, all fired at submit: `regionId` (`:958`), `industryVertical` in single-BU (`:962`), per-BU regions in multi-region (`:970`) |
| Submit disabled when | `!cohortName.trim()` — nothing else |
| Draft persistence | none — closing the modal loses everything |

So a first-time instructor faces dozens of settable options, no guidance about
which matter, no feedback until the end, and a button reading **"Permanently
Lock & Create Cohort"**.

### The finding that changes the design

That button, and the ⚠️ banner above it (`:3258`), are **wrong**.

`admin_router.patch_session_metadata` (`:3817`) has an `EDITABLE` set (`:3842`)
containing exactly the fields the banner calls permanent — `decision_paradigm`,
`ending_pathway`, `currency_symbol`, `scenario_preset`, `experience_level`,
`difficulty_tier`, `simulation_mode`, `industry_vertical`, `region_id`,
`stakeholder_pack_id`, `materiality_pack_id` — editable while **round == 1 and
no players are inducted**.

The real rule is not *"permanent on create"*. It is:

> **Everything stays editable until the first player is inducted — for a lead
> facilitator or above. For a base facilitator it is genuinely permanent,
> because the endpoint is `require_lead_facilitator`.**

That is a far less frightening truth, and it is the wrong-by-omission framing
that generates the anxiety the audit measured. Any wizard built on the old story
would inherit the anxiety it is meant to remove.

**Consequence for this plan:** the honest axis is not permanent-vs-not, it is
**"locked once players join"** vs **"changeable any time"** — and the copy must
be role-aware.

---

## 2. The reframe

Two moves, in order of value:

**(a) Ask less.** The biggest win is not rearranging 84 fields into five steps
— it is asking for ~10 and letting the rest take defaults, reachable later in
Cohort Settings. Creating a cohort should be a 90-second job.

**(b) Stage by consequence, not by subject.** The current sections group by
topic (engine, modules, pedagogy), which scatters the consequential choices
across sections 1, 2 and 2b. Group by *what happens if you get it wrong*.

---

## 3. Proposed flow

An entry choice, then a linear path with a skip.

```
┌ START ─────────────────────────────────────────────┐
│  ○ From a template   ○ Clone a cohort   ○ Blank    │
└────────────────────────────────────────────────────┘
        │
   1. Identity ──► 2. Shape ──►┬──► 5. Review & create   (EXPRESS)
                               └──► 3. Teaching ──► 4. Run ──► 5.  (FULL)
```

**Templates become the entry point, not a buried field.** They already exist
(`applyTemplateId` / `saveTemplateName`, `:192-193`, endpoints at `:787-799`)
and sit inside Advanced Controls where nobody looks. Applying a template should
be the *first* question, because it answers most of the others.

### Step 1 — Identity *(always)*
Cohort name · owning facilitator · created-by · start/end dates.
Freely editable forever. ~4 fields.

### Step 2 — Shape *(always — the consequential screen)*
Decision paradigm · scenario preset & difficulty · business shape
(conglomerate vs single business + vertical) · region · currency · ending
pathway · stakeholder/materiality packs.

One screen, because these are the choices that lock together and lock at the
same moment. Role-aware banner:

- Lead facilitator+: *"You can change these until the first player joins."*
- Base facilitator: *"These are fixed once the cohort is created — ask a lead
  facilitator if you need them changed."*

Each choice carries a one-line consequence ("Pillars gives four independent
levers per round instead of an A/B/C choice"), not just a label.

### Step 3 — Teaching *(skippable)*
Pedagogy toggles · analytics visibility matrix · quiz · CEO interview · side
tracks · engine modules. All reversible; header states so plainly.

### Step 4 — Run *(skippable)*
Pacing mode & schedule · roster size and team seats · join method · timezone ·
round timer · interventions (overrides/swipe files) · briefing video base.

> Default pacing should be **Manual**, not `free` — you never run Free Play, and
> the current component default (`RoundPacingControl.js:60`) silently puts an
> untouched cohort in the one mode you don't use.

### Step 5 — Review & create
Calls `POST /api/admin/cohort/{id}/apply-setup` with `dry_run: true` and renders
the **server's** resolved answer — not the client's guess at it. Two blocks:

1. **Locks when players join** — the Step 2 choices, spelled out.
2. **Changeable any time** — everything else, with where to change it.

Button copy: **"Create cohort"**, not "Permanently Lock & Create Cohort".

**Express path = steps 1, 2, 5.** Roughly 10 fields.

---

## 4. State architecture

84 `useState` hooks is the root cause of most of the rest. Applying a template
today means calling ~25 setters by hand; edit-mode hydration does the same at
`:317-340`.

Replace with **one reducer** over a single config object:

```js
const [config, dispatch] = useReducer(cohortConfigReducer, initialConfig(editSession));
// dispatch({ type: 'set', path: 'shape.decisionParadigm', value: 'multi_toggles' })
// dispatch({ type: 'applyTemplate', template })
// dispatch({ type: 'hydrate', session })
```

Shape it to mirror the steps: `{ identity, shape, teaching, run, meta }`.

This makes five currently-awkward things fall out for free: template
application, edit-mode hydration, per-step validation, draft persistence, and
building the `apply-setup` payload (which today is a hand-written literal at
`:826-869`).

**Do this first and separately.** It is a pure refactor with no visual change,
so it can ship and bake before any UI moves.

---

## 5. Validation

Declarative, per step, evaluated on every change:

```js
const STEP_RULES = {
  shape: [
    { field: 'regionId', when: () => true, msg: 'Choose a geographic region.' },
    { field: 'industryVertical', when: c => c.shape.mode === 'single_bu',
      msg: 'Single-business cohorts need an industry vertical.' },
    { field: 'buRegions', when: c => c.shape.multiRegion && c.shape.mode !== 'single_bu',
      msg: 'Multi-region: every business unit needs a region.' },
  ],
  // …
};
```

- **Next is disabled** until the current step is valid, with the reason shown
  next to the button (never a bare disabled control).
- Errors appear **at the field**, on blur — not as a banner after submit.
- The three existing checks move here unchanged; nothing new is enforced in
  phase one, so no cohort that creates successfully today can start failing.

---

## 6. Migration — strangler, not rewrite

A 3,300-line component in a live product does not get replaced in one commit.

1. Extract the reducer; the **existing accordion** drives it. No visual change.
2. Build the wizard shell as a **new component** over the same reducer, behind
   `?wizard=1` and a facilitator-level flag.
3. Dogfood the wizard on a real cohort creation. Accordion remains the default.
4. Flip the default; accordion stays reachable as "Advanced (all settings)".
5. Delete the accordion once a term has run through the wizard without falling
   back.

At every point both paths write the **same config object** through the **same**
create + `apply-setup` calls, so the backend never sees a difference and either
path can be abandoned without stranding anyone.

---

## 7. Phases and effort

| Phase | Work | Effort | Risk |
|---|---|---|---|
| **0** | Establish ground truth: which fields are *actually* immutable, per role. Fix the lying banner and button copy **now** — this is a 1-hour change that removes most of the anxiety without any wizard. | 0.5 day | none |
| **1** | Reducer refactor. 84 `useState` → one config object. Accordion unchanged. | 3 days | low — pure refactor, visual diff should be empty |
| **2** | Wizard shell: stepper, per-step validation, Next/Back, express path (steps 1, 2, 5) behind a flag. | 4 days | low — additive, flagged |
| **3** | Full path: steps 3 and 4, skip affordances, role gating preserved. | 3 days | medium — role gating is the thing most likely to regress |
| **4** | Template/clone entry choice · draft persistence · `dry_run` review screen. | 3 days | low |
| **5** | Flip the default, run a term, delete the accordion. | 2 days + a term | low |

**~3 engineer-weeks of build**, then a term of soak before deletion.

Phase 0 is worth doing on its own even if nothing else proceeds.

---

## 8. Risks and containment

| Risk | Containment |
|---|---|
| **Role gating regresses.** Base facilitators must not see engine/verticals/modules/interventions (`:1590, :1832, :1942, :2200`); System Engine Modules stays super-admin (`:1945`). | Add a jest test pinning visible-steps-per-role **before** phase 3. It should fail loudly if a section becomes visible to a lower tier. |
| **Edit mode breaks.** `editSession` hydrates ~25 setters (`:317-340`). | Phase 1 turns that into one `hydrate` action; keep the existing edit-mode e2e path green throughout. |
| **`apply-setup` fallback lost.** The legacy chain is the compatibility path for a backend without the new route. | Keep `runSubConfigChain` until phase 5 and test with the route disabled. |
| **A field is silently dropped in the reducer move.** 84 → one object is exactly where something goes missing. | Snapshot test: build the create payload + `apply-setup` payload from the old and new state for a fixed set of inputs; assert deep equality. This is the single most valuable test in the plan. |
| **Wizard makes power users slower.** Someone who knows all 84 fields may prefer the dense form. | That is what "Advanced (all settings)" is for. Do not delete it until phase 5, and only if nobody used it. |

---

## 9. Explicitly not doing

- **Not** changing what any field means, or adding new configuration.
- **Not** touching the create or `apply-setup` endpoints — the wizard is a new
  way to fill the same payload.
- **Not** a design-system refactor along the way. Token work is item #20 and has
  its own ratchet; mixing them makes both unreviewable.
- **Not** moving fields to Cohort Settings in phase 1. The express path *hides*
  them behind a skip first; relocating them is a later, separate decision once
  you can see which ones nobody sets.

---

## 10. Decisions I need from you

1. **Express path field list.** My proposed ~10 is a guess. Which fields do you
   *actually* set every time, and which have you never once changed from the
   default? That single answer determines whether this is a good wizard or just
   a differently-shaped form.
2. **Who creates cohorts in practice** — you as lead/super admin, or base
   facilitators? It changes the Step 2 copy from "editable until players join"
   to "permanent", and it decides whether phase 0's banner fix is reassuring or
   simply accurate.
3. **Should the wizard offer "clone this cohort"** (roster shape and settings
   from an existing run), or are saved templates enough? Cloning is more useful
   for a term where you re-run the same design, and it is a small addition on
   top of the template path.
4. **Is anyone besides you creating cohorts this term?** If not, phases 2–4 can
   be dogfooded aggressively with no flag; if yes, the flag matters.
