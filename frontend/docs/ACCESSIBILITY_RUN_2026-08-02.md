# Accessibility run — 2 Aug 2026

## What was and was not run

I **could not run NVDA.** TEST 2 (screen reader) and TEST 6 (projector legibility
at 10 m) in `ACCESSIBILITY_MANUAL_TESTS.md` require a human at a Windows machine
and remain **outstanding**.

What I did instead: stood the app up for real (FastAPI on :8000, Next.js on
:3000) and ran the mechanical half of the script in **Chromium with real
layout**. That matters because the previous jest-axe floor ran in jsdom, which
has no cascade and no geometry — it forced twelve axe rules off, `color-contrast`
among them, and could not touch the cockpit at all.

| Manual test | Status |
|---|---|
| TEST 1 — keyboard-only path | **Automated** (`e2e/a11y-real-browser.spec.js`) |
| TEST 2 — NVDA screen reader | **Still yours.** Proxy only: accessible-name extraction + dnd live-region capture |
| TEST 3 — focus management | **Automated** |
| TEST 4 — 200% zoom, 320px reflow | **Automated — both pass** |
| TEST 5 — contrast, both themes | **Automated — real cascade. Findings below** |
| TEST 6 — projector at 10 m | **Still yours** (axe on the page is clean) |

Result: **10 passed, 2 failed.** Both failures are the player cockpit's
light-mode contrast, detailed below.

A second, session-based pass signed a real player in and walked the full flow to
the Round 1 gate — that is what produced the dnd-kit correction and findings F10
and F11.

**Incidental finding:** `next.config.mjs`'s `/api/*` rewrite does **not** apply
under Turbopack dev — every `/api/*` call 404s on :3000 while :8000 answers
normally. Production is unaffected (your Railway deploy works), so this is a
local-dev annoyance rather than a product bug, but it will waste someone's
afternoon. The Playwright suite routes around it with request interception.

---

## Defects found and FIXED

Three of these were invisible to jsdom by construction.

| ID | SC | Severity | Defect | Fix |
|---|---|---|---|---|
| **F6** | 4.1.2 | **CRITICAL** | The BU filter `<select>` in the cockpit header had **no accessible name at all**. A screen reader announced an unnamed combo box — the control that switches the whole cockpit between business units was unusable without sight. | `aria-label="Filter cockpit by business unit"` |
| **F7** | 2.1.1 | Serious | The left KPI sidebar is a scroll container with no focusable content, so a keyboard user **could not scroll it**. jsdom has no scroll geometry, so this could not be detected there. | `tabIndex={0}` + `role="group"` + label |
| **F8** | 1.4.3 | Serious | "← Back to Admin Portal" measured **4.34:1**. The token was fine; `opacity: 0.7` composited it below AA. Opacity on text is invisible to a token audit *and* to jsdom. | `--text-secondary`, opacity removed |
| **F10** | 1.3.1, 3.3.2 | Serious | `UsernamePromptModal` — same unassociated-label defect as sign-in, on the screen every new player hits second. | `htmlFor` + `id` |
| **F11** | 2.1.1 | Serious | Stakeholder **intel dossier** was hover-only, so a keyboard user could see intel existed and never read it. | `aria-describedby` (see correction below — the obvious `onFocus` fix broke the drag) |
| **F9** | 1.4.3 | Serious | **Seven light-mode nodes rendered effectively invisible text** — `#f1f5f9` on `#f7f9fc` is **1.03:1**; `#cbd5e1` is 1.40:1; `#94a3b8` is 2.27:1. Dark-theme neutrals serialized into inline styles and rendered on light surfaces. | Restored the neutral rules in the light-mode shim |

On F9: `globals.css` carries a migration note dated 2026-05 claiming the neutral
text colours were replaced everywhere and their shim rules removed. **Chromium
says that migration was incomplete.** The note now records what was actually
measured.

---

## The dnd-kit gates — CORRECTION to an earlier claim

The jest-axe report called the dnd-kit capital allocation "the largest Level A
risk in the product". **Two things in that were wrong, and I repeated them.**

**Wrong component.** Capital allocation does not use dnd-kit. The only two
dnd-kit surfaces are `StakeholderMapModal` (the **Round 1 mandatory gate**) and
`DoubleMaterialityMatrix` (the **Round 2 mandatory gate**) — which is arguably a
worse place for a keyboard failure, because a player literally cannot commit
those rounds without completing them.

**Wrong conclusion.** I signed a real player in (`MUR-FFQ`), drove the browser
through login → username → briefing → tour → cockpit → the R1 gate, and executed
the keyboard drag. **It works.**

```
chips: 10, each role="button" tabindex="0" aria-roledescription="draggable"
Space   → "Draggable item activist_fund was moved over droppable area bank."
Arrows  → "Draggable item activist_fund was moved over droppable area keep_satisfied."
Space   → "Draggable item activist_fund was dropped over droppable area keep_satisfied"
```

`KeyboardSensor` is registered in both gate components
(`StakeholderMapModal.js:160`, `DoubleMaterialityMatrix.js:470`) and dnd-kit's
live region announces every step. The largest claimed Level A risk **is not a
defect**. It could not be checked in jsdom because drag sensors resolve against
bounding boxes and every box there is 0×0 — so the gap was real, but the
conclusion drawn from it was not.

### One real defect found there, and a regression I caused fixing it

**F11 (2.1.1)** — the stakeholder **intel dossier** was `onMouseEnter`-only. The
📋 marker was visible to everyone; the intel behind it — the reasoning material
for placing that stakeholder — was reachable only by hovering.

My first fix opened it on `onFocus`. **That broke the keyboard drag**: this chip
is dnd-kit's drag handle, and mounting a panel inside it on focus silenced the
live region entirely. I only caught it because I re-ran the drag afterwards.

Reworked to expose the dossier through `aria-describedby` — always present,
never visible, no state, so it cannot perturb the drag. Verified:

```
aria-describedby = "DndDescribedBy-0 dossier-activist_fund"
dossier text     = "Intel: 📰 FT: 'FutureFirst acquires 5.2% Muressons stake…"
…and all three drag announcements still fire.
```

**F10 (1.3.1, 3.3.2)** — `UsernamePromptModal` had the same unassociated-label
defect as the sign-in screen. Found by walking the flow, not by scanning a
component in isolation. Fixed.

---

## Still failing — needs a decision on a real screen

**Player cockpit, light mode: 14 nodes between 2.92:1 and 3.43:1.** No longer
invisible, still below the 4.5:1 floor.

| Colour on | Ratio | Where |
|---|---|---|
| `#0d9488` on `#f1f5f9` | 3.41 | BU ticker names (×4) |
| `#059669` on `#f1f5f9` | 3.43 | BU ticker percentages (×4) |
| `#16a34a` on `#ffffff` | 3.29 | Resource card value |
| `#3b82f6` on `#eff5fe` | 3.35 | Mailbox button |
| `#334155` on `#0e1222` | 1.79 | Two rail buttons — a **light**-theme colour on a **dark** surface, i.e. the leak running the other way |
| `#0f766e` on `#142330` | 2.92 | Rail button |

**Player cockpit, dark mode: 3 nodes** — `#8899a6` on `#3d414e` (3.46), `#64748b`
on `#1c2234` (3.32), and the same mailbox button (3.35, wrong in both themes —
its background does not follow the theme).

I stopped here deliberately. Each of these is a hue decision, and this repo's
own `CLAUDE.md` says hue decisions happen on a real screen, never in a blind
regex — the light-mode shim in `globals.css` exists because a previous sweep
ignored that. I fixed the cases that were unarguable (invisible text, a missing
accessible name, a keyboard trap); the rest need someone looking.

The mailbox button is the cheapest win: it fails in **both** themes because its
background is hardcoded light while its text follows the theme.

---

## Passed cleanly

- **1.4.10 Reflow at 320 px** — player and facilitator, zero horizontal scroll.
- **1.4.4 Resize text at 200%** — no horizontal scroll.
- **2.1.1 / 2.4.7** — both credential fields reachable by Tab, visible focus
  indicators, no focus stop on a zero-size element across 40 tab presses.
- **3.3.2** — sign-in fields keep their accessible name after typing (the F1 fix
  from earlier today, confirmed in a real browser).
- **4.1.2** — no unnamed interactive controls on the player sign-in.
- **Facilitator dashboard** — clean in both themes after F8.
- **Projector board** — clean.
- **2.5.8 target size** — measured from real geometry, reported not gated
  (WCAG 2.2, outside the 2.1 obligation).

---

## How to re-run

```
# terminal 1
cd backend && USE_MEMORY_DB=true DEBUG=true JWT_SECRET=<secret> \
  python -m uvicorn main:app --host 127.0.0.1 --port 8000
# terminal 2
cd frontend && BACKEND_URL=http://127.0.0.1:8000 npx next dev --port 3000
# terminal 3
cd frontend && npx playwright test --config=playwright.a11y.config.js
```

`jest.config.js` now excludes `e2e/` — the two suites are complementary, not
alternatives, and jest cannot run Playwright specs.

---

## What this run does and does not mean

It means the **machine-detectable** defects on four surfaces, in both themes,
with real layout, are now either fixed or listed above with exact ratios.

It does **not** mean conformance, and the evidence for that is in this document:
the earlier jsdom pass reported zero violations on components that a real
browser then showed had a critical unnamed control and seven pieces of
invisible text.

Unevaluated: everything NVDA would tell you — an announcement can be technically
correct and still incomprehensible, and no automation detects that; the R2
materiality gate's keyboard drag (R1's is verified, and they share sensor
configuration, so R2 is likely fine but is not *tested*); god-mode, war-map,
shockwave and trading-floor; all charts and the 3-D layer; and projector
legibility at distance.

One process note worth keeping: the F11 regression — an accessibility fix that
silently broke a keyboard path on a mandatory gate — was caught only because the
drag was re-run afterwards. Re-test the interaction you touched, not just the
thing you were fixing.

**Do not send `VPAT_DRAFT.md` to anyone.** It is still 44 of 50 criteria "Not
Evaluated", and today's findings are the argument for why that caution is right.

---
---

# Second real-browser pass — same day, signed-in cockpit

The first pass measured the sign-in screen, the facilitator dashboard and the
projector. This one signed a player in (`MUR-FFQ`), reached the **Executive
Cockpit**, and measured it in **both themes** — the surface a participant looks
at for ten rounds, and the one surface neither previous floor had ever seen.

It found **nine defects, eight of them fixed**, and it retired two conclusions
this document previously recorded. Both retractions matter more than the fixes.

## What the earlier numbers got wrong

The "Still failing" table above lists 14 light-mode nodes between 2.92:1 and
3.43:1 and calls each one a hue decision. Measured properly on the signed-in
cockpit, the real figure was **76 failing nodes across 17 distinct rules in
light mode**, and the worst of them were not hue decisions at all — they were
**1:1**. Invisible text, not dim text.

The gap came from the tool, not the theme. A contrast sweep that composites a
gradient backdrop as if it were flat manufactures phantoms *and* hides real
failures: the round-1 gate's launch button measures 1:1 that way and is
perfectly legible, while the commit button measures 1:1 and genuinely is not.
The probe used here separates the two — anything with a `background-image`
anywhere in its stack is reported **indeterminate**, exactly as axe does, and
judged on a screenshot instead.

| Cockpit | Before | After |
|---|---|---|
| light — real failures | 17 rules / 76 nodes | **4 rules / 5 nodes** |
| dark — real failures | 8 rules / 25 nodes | **3 rules / 6 nodes** |

## The single defect underneath most of it

Eight of the nine findings are one shape: **a surface and the text on it are
decided by two different mechanisms that disagree about the theme.**

The light-mode shim in `globals.css` is the clearest instance. Its colour rules
rewrite a foreground assuming the surface is light. Its background rules
rewrite a surface and say nothing about the text. Neither half knows what the
other did, so it fails in both directions at once:

- **Surface rewritten, text not** — the commit button's inline
  `background: rgb(30,41,59)` became `#fff`, while its class kept `color: #fff`.
  **White on white, 1:1, on the primary action of every round.**
- **Text rewritten, surface not** — the market ticker's `#e2e8f0` prices were
  darkened, but its `#000000` strip is not one of the darks the shim lists.
  **Black on black across every number on the bar.**

That block's own header calls itself a temporary shim and names the durable fix
("replace every remaining inline `color:` with the matching CSS variable").
This pass acted on that instruction where it mattered and left the rest.

## Defects found and FIXED

| ID | SC | Severity | Defect | Fix |
|---|---|---|---|---|
| **F12** | 1.4.3 | **CRITICAL** | The cockpit's `--ck-*` light values in `globals.css` **had never once applied**. They are declared on `<html>`; the dark values are declared on `.cockpit` itself, and an element's own declaration always beats an inherited one. A comment in the module CSS asserted the opposite ("`:root` variables can only be overridden at the `:root` level") and that belief kept the whole left rail dark in light mode while `--ck-text-*`, written as `var(--text-*)` *references*, did follow the theme — slate text on navy, **1.80:1**. | Declare the same overrides on `.cockpit` in `ExecutiveCockpit.module.css`, where they win. The wrong comment is replaced by the measurement. |
| **F13** | 1.4.3 | Serious | The left rail's guides panel hard-codes `#0a0e1a` — not one of the darks the shim rewrites — so the panel stayed navy while the shim darkened its text. "⋯ More" **1.21:1**, the paradigm label **2.66:1**. | `var(--ck-surface-0)`. Identical in dark, follows the theme in light. |
| **F14** | 1.4.3 | **CRITICAL** | Every commit-button state overrides the background inline but left `color` to the class, which is `var(--ck-surface-0)` — near-black, chosen for a teal gradient those overrides replace. **Illegible in both themes**: dark **1.31:1**, light **1:1**. | Each state now carries the foreground that belongs with its background; the shim's white-surface rules now assert a foreground too. |
| **F15** | 1.4.3 | **CRITICAL** | The market ticker is `#000000` in both themes *by design*, but drew its text from theme tokens and shim-visible inline hexes. In light mode: symbols **2.03:1**, prices **1:1**, deltas **3.70:1** — 16 nodes, every number on the bar. | A theme-invariant palette as classes in the component's own `<style>`. A surface that never changes needs a palette that never changes. |
| **F16** | 1.4.3 | Serious | Focus Mode's label used `opacity: 0.7` for de-emphasis — the same trap as F8. | Opacity removed; amber-400/500 added to the shim at `#b45309`. |
| **F17** | 1.4.3 | Serious | The rail's tab strip painted `var(--bg-sidebar, #ffffff)`. **`--bg-sidebar` is defined nowhere in the codebase**, so it was a hard-coded white wearing a token's clothes — white in dark mode, which is why the mailbox tab measured the same failing 3.35:1 in *both* themes. | `var(--ck-surface-1)`, plus a per-theme label colour for each tab. |
| **F18** | 1.4.3, 2.2.2 | Serious | The unread-count badge was `#fff` on red-400 — **2.68:1** at rest — and the shared `pulse` keyframe drops opacity to 0.3, so twice a second it fell to roughly **1.4:1**. | red-600 (4.83:1) and a new `badgePulse` that animates a ring, not the glyph, and yields to `prefers-reduced-motion`. |
| **F19** | 1.4.3 | Moderate | The round checklist's `2/5` counter — the one thing on that strip stated nowhere else — sat at **2.56:1** on its deliberately-white card. | `#475569`, 7.4:1. Its arrows are marked `aria-hidden`: pure decoration, exempt, and darkening them would turn hairlines into a second row of chevrons. |

## F20 — the keyboard drag works, and that was never the question

The correction earlier in this document says the dnd-kit gates are "not a
defect" because the keyboard drag completes. That is true and it was the wrong
thing to check.

Both gates registered `useSensor(KeyboardSensor)` with no coordinate getter, so
they inherited dnd-kit's default: **translate the item 25 px per arrow press.**
Counted in Chromium at 1600×1000, from the bank:

```
lift              -> over droppable "bank"
6  x ArrowRight   -> over "keep_satisfied"
23 x ArrowRight   -> over "manage_closely"      (…and the bottom row needs the ArrowDowns)
```

Ten stakeholders is on the order of **two hundred key presses** to clear a gate
a mouse user clears in ten drags — while the modal offers a five-minute timer.
SC 2.1.1 was satisfied and the gate was still unusable, which is precisely what
a pass/fail check cannot see. The previous pass pressed one arrow, saw the live
region announce a move, and stopped.

`app/lib/dndDroppableKeyboardCoordinates.js` supplies a coordinate getter that
snaps to the next droppable in the pressed direction. Both gates now use it.
Verified in a real browser — **one press, one zone:**

```
R1 StakeholderMapModal      1 x ArrowRight -> keep_satisfied
                            2 x ArrowRight -> manage_closely
   all 10 stakeholders placed by keyboard, gate submitted and scored

R2 DoubleMaterialityMatrix  lift -> bank
                            ArrowRight -> q2   ArrowDown -> q4   ArrowRight -> q3
                            Space      -> dropped over q3
```

**The round-2 gate is now directly tested**, not inferred from shared sensor
configuration. Reaching it meant committing round 1 for real (`new_round_number:
2`), so the commit path is exercised too. Pointer dragging is untouched — a
coordinate getter is consulted only by `KeyboardSensor`.

## Still failing — and why these stop here

**Light mode, 4 rules / 5 nodes. Dark mode, 3 rules / 6 nodes.**

| Ratio | Colour on | Where | Why not fixed |
|---|---|---|---|
| 3.29 | `#16a34a` on `#ffffff` | Green Fund value | Semantic green one shade too light. `#047857` — the value already chosen for `--kpi-good-on-light` — measures 5.5:1. A token decision, not a local one. |
| 3.41 | `#0d9488` on `#f1f5f9` | Resources pill arrow | Same, teal. `#0f766e` (already `--brand-text` in light) measures 4.6:1. |
| 3.43 | `#059669` on `#f1f5f9` | BU ticker percentages | Same, emerald. |
| 4.19 | `#64748b` on `#edf1f5` | Small caps label | Marginal; `#475569` clears it. |
| 1.84 / 2.36 | `#334155` on `#0f1012` *and* `#94a3b8` on `#f4f6f8` | Market Reality Feed `INFO` chip | **Inverted between themes** — a fourth always-light panel, found today. Its badges are also 6.7–7.7 px, which is a type-size decision before it is a colour one. |
| 2.13 | `#22c55e` on `#edfaf2` | `• new` chip | Same panel. |
| 2.26 | `#475569` on `#151b2b` | `/100`, `t` unit suffixes | `--neutral-faint`, deliberately "one step lighter" per `tokens.css`. Changing it is a token decision. |

Every one is a **one-shade-darker move on a shared token**, or a decision about
a panel's type size. Each would be a two-character edit and a codebase-wide
blast radius, and this repo's `CLAUDE.md` says hue decisions happen on a real
screen. They are listed with the exact token, the exact replacement and the
measured ratio so they can be approved as **one decision** rather than seven.

## On the "three always-light panels" — reversing a pass-4 recommendation

Pass 4 called `--kpi-good-on-light` / `--kpi-warn-on-light` a temporary bridge
and said the real fix was to make `DebriefReport.panel`,
`RoundPacingControl.panel` and `ResourceSidebar.sidebar` theme-aware.

**Having now looked at these surfaces in a browser, that recommendation was
wrong.** Some surfaces are *deliberately* theme-invariant and should stay so:
the market ticker is a black trading ribbon in both themes, the round checklist
is a floating white card in both. Flipping those to follow the theme would be a
restyle of the cockpit, not a contrast fix — and F15 shows the actual failure
mode is the opposite one, a fixed surface fed theme-dependent colours.

So the bridge tokens are not a hack awaiting removal; they are **the correct
mechanism for a surface that does not follow the theme**, and the work is to
name that pattern and apply it consistently. The Market Reality Feed is the
fourth member of the family and is where to start.

## What is pinned, and what is not

`__tests__/theme-leak-tripwires.test.js` (18 tests) pins the *source shape* of
every fix above — the losing cascade, the undefined token, the hard-coded
darks, the missing foregrounds, the opacity-animated glyph, the absent
coordinate getters. It is not a contrast assertion: only a browser can measure
a ratio. It is the cheap thing that stops this class of regression landing
between browser passes, and it exists because neither existing floor could see
any of these — jsdom has no cascade, and the token-drift ratchet counts raw hex
so it cannot tell that a token resolves to the wrong value, or that a
declaration never wins at all.

**Verification:** `npx next build` passes (11/11 static pages, fonts stubbed for
the offline sandbox, `layout.js` restored and `diff`-verified byte-identical).
jest **34 suites, 859 passed**, 4 documented skips. Playwright **10 passed, 2
failed** — the same two as the first pass, now down to the four token families
listed above. Backend **1840 passed, 6 skipped**; the 7 `test_deploy_image_hygiene`
failures are this sandbox missing `.dockerignore` (a dotfile that did not survive
the copy), not a code change.

**Still outstanding and still yours:** NVDA (TEST 2) and projector legibility at
10 m (TEST 6). **Do not send `VPAT_DRAFT.md` until those are done.** Today is
the argument for that caution, not against it: a surface that two automated
floors called clean turned out to have its primary action rendered white on
white.

---
---

# Third pass — the mailbox rail

Requested directly. The rail is where the game **talks to the player**: board
briefings, crisis messages, rival press, the ESG rating letter. Measured on a
signed-in cockpit with the MAILBOX tab open, in both themes.

**Dark mode had 18 failing nodes, and they were not chrome.**

```
subject line   #0f172a on #151929 = 1.02:1     "Board Briefing"
preview body   #334155 on #151929 = 1.68:1
subject line   #0f172a on #151929 = 1.02:1     "🔴 ACTIVIST THREAT — Investor Revolt Imminent"
rival headline #0f172a on #131828 = 1.01:1
rating agency  #7c3aed on #14142c = 3.16:1     (and the CCC grade with it)
"MARKET NEWS"  #64748b on #64748b = 1:1        — in BOTH themes
```

Every board briefing and crisis message in the game rendered invisible in the
theme the product ships as its default. A screenshot confirms it: the message
rows show a sender, a blank line where the subject belongs, and a preview you
have to tilt the screen to read.

## Why the earlier passes could not see it

This is **the mirror image of F9**. The `globals.css` shim rewrites *dark*
values found on *light* surfaces — the direction someone hit once and patched.
Nothing rewrites *light* values found on *dark* surfaces, and this entire
subtree was authored in light-theme near-blacks: `#0f172a` subjects, `#334155`
previews, `#334155`/`#475569` archive text, a `#f7f8fc` accordion.

A shim only ever covers the direction someone thought of. That is the argument
for the migration its own header prescribes, and this pass carried it out for
the rail.

| Mailbox rail | Before | After |
|---|---|---|
| light | 9 failing / 34 nodes | **0** |
| dark | 18 failing / 34 nodes | **0** |

## Fixed

| ID | SC | What was wrong | Fix |
|---|---|---|---|
| **M1** | 1.4.3 | Message **subject 1.02:1** and **preview 1.68:1** in dark. Sender names 3.67:1 (dark) *and* 4.16:1 (light) — a 500-weight persona hue used as text on both cards. | Subject/preview move to `--text-primary` / `--text-secondary`. Personas gain `textColor` in the semantic text tier, which flips per theme; `color` is **kept unchanged** because `ShadowBoardAudit.js` builds a border from `${persona.color}40` and a `var()` cannot take an alpha suffix. |
| **M2** | 1.4.3 | The whole Market Intelligence block in light-theme near-blacks: rival headline 1.01:1, body 1.71:1, agency and grade 3.16:1, the disclaimer 1.65:1. And **`MARKET NEWS` was `#64748b` text on `rgba(100,116,139,0.12)` — its own hue as its own background, 1:1 in both themes.** Not a theme bug; an authoring one. | Text tier throughout; `textColor` on `RIVAL`, `AGENCY` and the four rating directions; the chip gets a foreground that is not its backdrop. |
| **M3** | 1.4.3 | `.mailboxBadge` used `background: var(--danger-text)` — the **text** tier, `#f87171` in dark, a pastel meant to be read *on* a dark surface rather than to be one. White on it: **2.77:1**. Same defect as F18, in the second badge. | `#dc2626`, 4.83:1 in both themes. |
| **M4** | 1.4.3 | `ArchiveAccordion` was hard-coded light throughout — a **white slab inside a dark rail**, holding the archive of the very messages listed above it in theme-aware colours. Its own header label measured 4.13:1 on its own light background, so it failed in light mode too. | Token tiers throughout, so the archive matches the list it archives. |
| **M5** | 1.4.3 | "Read" was signalled by `opacity: 0.6`, which composites text toward its surface — the F8 / F16 trap. The preview body of a read message measured **3.8:1** in dark, and *read is the state every message holds for the rest of the game*. | `0.85`. Affordance kept, body holds 5.7:1. |

## A correction to the measuring tool, again

The first cut of this scan reported `MARKET NEWS` at 1:1 and `◆ INITIATED` at
1.01:1 **after** they were fixed. Both were false: the probe's alpha
compositing hard-coded `a: 1`, so a single translucent layer was treated as
opaque and the walk stopped there — a 12 %-alpha slate chip read as solid
`#64748b`.

That is the second time in this audit a measurement error nearly produced a
"fix" for something that was not broken (the first was gradient backdrops, in
the pass above). Worth stating plainly: **a contrast sweep is a program, and a
wrong one manufactures work and hides real defects at the same time.** Both
corrections are now in the probe and both are recorded here.

## Not fixed — and deliberately so

**Nine nodes in the rail are between 9 px and 9.6 px.** The worst chips were
lifted from 0.55 rem (8.8 px) to 0.6 rem (9.6 px) while their colours were
being fixed, because that cost nothing. Going further reflows the rail, and
WCAG 2.1 AA sets no minimum type size — but 9 px is small for a room where a
facilitator may be reading over a shoulder, and it is worth a look next to the
projector test that is still outstanding.

**Verification:** jest **34 suites, 868 passed** (9 new mailbox tripwires,
M1–M5), `npx next build` passes 11/11, Playwright unchanged at 10 passed / 2
failed (the four token families listed in the pass above), backend untouched.

---
---

# Fourth pass — closing the four token families, and what was under them

The pass above handed back four "one-shade-darker" families and said they were
one decision, not seven. Taking that decision turned out to expose something
larger, and the end state is better than the ask: **the signed-in cockpit and
mailbox now measure zero failing text nodes in both themes, and the committed
real-browser suite is 12 passed / 0 failed** — green for the first time.

## F21 — the shim's own answers did not clear AA

The light-mode shim in `globals.css` exists for one job: make a dark-theme
pastel readable when it lands on white. **Ten of its sixteen replacement
values did not themselves reach 4.5:1 on the surfaces it exists to fix.**

```
                current                        replaced with
green-400     #16a34a  3.30 / 3.15 / 3.01      #15803d  5.02 / 4.79 / 4.58
emerald-3/4   #059669  3.77 / 3.60 / 3.44      #047857  5.48 / 5.24 / 5.01
sky-400       #0284c7  4.10 / 3.91 / 3.74      #0369a1  5.93 / 5.67 / 5.42
amber-300     #d97706  3.19 / 3.04 / 2.91      #b45309  5.02 / 4.80 / 4.58
orange        #ea580c  3.56 / 3.40 / 3.25      #c2410c  5.18 / 4.95 / 4.73
cyan          #0891b2  3.68 / 3.52 / 3.36      #0e7490  5.36 / 5.12 / 4.89
red-3/4       #dc2626  4.83 / 4.62 / 4.41      #b91c1c  6.47 / 6.18 / 5.91
indigo-300    #6366f1  4.47 / 4.27 / 4.08      #4f46e5  6.29 / 6.01 / 5.74
                            (against #ffffff / #f8fafc / #f1f5f9)
```

**And this file already knew.** An earlier pass — the `A11Y-1 (UX audit #11)`
comments in the light *token* block, forty lines above — measured the identical
hues and corrected them there:

```
--accent-cyan   #0891b2 -> #0e7490    "3.36:1 on f1f5f9 -> 4.89:1"
--gauge-green   #059669 -> #047857
--gauge-red     #dc2626 -> #b91c1c
--accent-gold   #d97706 -> #b45309
```

The tokens were fixed and the shim was not. One palette, two copies, one of
them stale — so the same colour was right in one half of the file and wrong in
the other. That is the entire finding, and it is why all four "families" the
previous pass handed back were a single edit.

`#dc2626` and `#6366f1` cleared white and missed only on `#f1f5f9`. They were
moved anyway: **a rule that passes on one light surface and fails on another is
exactly how this survived three audits.**

### F21b — the 500 weights were never covered at all

The block handled the 300s and 400s, because those are what a dark theme uses
for *text*. It never handled the **500s** — the weight a component reaches for
when it wants a colour to read as the colour itself: a status dot, a stage
badge, a negative number. Eight families added (emerald, green, red, orange,
teal, violet, sky, rose). That alone cleared the stakeholder panel's `DORMANT`
badge (2.23:1) and an option's cost (3.76:1).

### F21c/d — what the shim structurally cannot reach

A shim keyed on inline styles cannot see a **class**. Three panel badges kept
their dark-theme pastels in light mode — `.badgeWatch` at **1.30:1**,
`.badgeCritical` and `.badgeHostile` at **1.68:1**. These count the
stakeholders about to escalate: the number a player reads to decide whether to
act this round.

And it only runs in *light* mode, so a **light**-theme neutral used in dark is
invisible to it in both senses. That is how every KPI unit suffix (`/100`,
`t`, `%`) sat at **2.35:1** on the dark card through three audits — a carbon
figure whose "t" cannot be read is a number with no unit. 24 literals migrated
to the token tier across the cockpit, benchmarks and stakeholder panel.

Also fixed here: chrome tokens used as text. `--brand` is the `#0d9488` chrome
teal; `--brand-text` is the same identity in the tier `tokens.css` explicitly
reserves for text ("brighter hues reserved for text so contrast survives the
hue discipline"). Three sites were reaching for the wrong one.

## F22 — the fourth opacity-animated glyph

`ci-pulse` (competitor badge) and `criticalPulse` (stakeholder badge) both
dipped **opacity** on an element carrying text — joining the shared `pulse`
keyframe and the rail badge from F18. Four instances of the same mistake in one
codebase is a pattern, not an accident, so the tripwire now asserts the
property directly: **a keyframe on something with a glyph animates
`box-shadow`, never `opacity`**, and yields to `prefers-reduced-motion`.

## Where it lands

| Surface | Before this pass | After |
|---|---|---|
| cockpit + mailbox, light | 9 rules / 19 nodes | **0** |
| cockpit + mailbox, dark | 4 rules / 9 nodes | **0** |
| committed Playwright suite | 10 passed / 2 failed | **12 passed / 0 failed** |

Two nodes remain *indeterminate* — white text on the CSRD gate's red gradient
and on the logo mark's blue one. Both were judged on a screenshot in both
themes and are legible; a gradient backdrop cannot be resolved from computed
style, which is the correction recorded in the pass above.

**Verification:** jest **34 suites, 874 passed** (F21/F22 tripwires added,
including one that recomputes every shim replacement value arithmetically and
fails if any lands below 4.5:1 on any of the three light surfaces — so this
cannot silently rot again). `npx next build` passes 11/11, `layout.js`
`diff`-verified byte-identical. CRLF preserved in the two module stylesheets
that use it.

**Still outstanding and still yours:** NVDA (TEST 2) and projector legibility
at 10 m (TEST 6). Zero machine-detectable contrast failures is not conformance
— it is the floor that had to exist before the human tests are worth running.
