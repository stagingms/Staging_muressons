# Manual Accessibility Test Script — Muressons

**WCAG 2.1 Level AA · UX audit #18 follow-through**
Version 1.0 · 2026-08-02

---

## READ THIS FIRST

**This script is not a conformance certificate, and neither is the automated
suite it accompanies.**

The automated half of this work (`frontend/__tests__/a11y-axe.test.js`, axe-core
4.12) detects roughly **a third** of WCAG failures. On the six components it
covers it currently reports **zero violations** — and a hand review of those same
six components found **five real AA-relevant defects it could not see** (logged
as `A11Y-F1`–`A11Y-F5` in that test file). That gap is the entire reason this
document exists.

Nothing here proves conformance either. A pass on every item below means
"a non-specialist, using the checks listed, found no failure in the flows
listed." It does **not** cover:

- users of magnification, switch access, voice control, or braille displays
- cognitive-accessibility criteria (3.1.x, 3.2.x beyond the mechanical checks)
- any flow not listed here
- testing by actual disabled users, which is the only thing that closes the loop

**If the contract requires a conformance statement, this document plus the
axe suite is the input to that work, not the output of it.** A qualified
accessibility auditor and a session with real AT users are still required.

---

## Before you start

| | |
|---|---|
| **Time budget** | ~45 minutes for the full pass |
| **Browser** | Chrome or Edge, latest. Windows (matches the client's environment). |
| **Screen reader** | NVDA (free, Windows) — https://www.nvaccess.org/download/ |
| **Contrast tool** | TPGi Colour Contrast Analyser, or Chrome DevTools' contrast readout in the colour picker |
| **Environment** | A cohort with **at least 3 players**, at least **2 committed rounds**, and **manual pacing mode** — several checks have nothing to inspect on an empty cohort |
| **Accounts** | One participant login (`MUR-xxx` + cipher) and one facilitator/admin login |

**Recording failures.** For every failure, capture *all* of:

1. Test ID and step number (e.g. `T1.4`)
2. The WCAG SC number printed next to the step
3. URL and browser zoom level
4. Exactly what you did (keys pressed, in order)
5. What you expected vs. what happened
6. A screenshot, and for screen-reader items a note of **what NVDA actually said**, verbatim
7. Theme (light/dark) and viewport width

Log to the accessibility issue tracker with the label `a11y` and the SC number.
Anything at **Level A** is a contractual blocker; Level AA is a blocker under
this contract too, but triage A first.

---

## TEST 1 — Keyboard-only path through the full player decision flow

**~12 minutes. Level A. This is the single most important test in this document.**

> **Physically move the mouse out of reach before you begin.** Not "don't click" —
> move it. Every check in this section is invalidated by one unconscious click.
> If you get stuck and must use the mouse to continue, that is itself a **FAIL**:
> record where you were stuck and what you had to click.

Keys you will use: `Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`, arrow keys.

### T1.1 — Sign in (SC 2.1.1 Keyboard, SC 3.3.2 Labels or Instructions)

1. Load the participant URL. Press `Tab` once.
2. **PASS:** focus lands on a control *inside* the sign-in panel (the Executive
   Identifier field or the first control in it), with a **clearly visible focus
   ring**. It does not land on browser chrome or on something behind the panel.
3. Type the player ID, `Tab` to the cipher field, type it, `Tab` to
   **ESTABLISH LINK**, press `Enter`.
4. **PASS:** you are signed in without touching the mouse.
5. **FAIL and record if:** focus starts outside the panel; any field cannot be
   reached; the visible label text ("EXECUTIVE IDENTIFIER") disappears from view
   once you type; you cannot tell which field is focused.

> **Known open defect — expect this one to fail its screen-reader counterpart
> (T2.2), not this step.** `A11Y-F1`: the two credential fields have no
> programmatic label; their accessible name comes from the placeholder only.
> Confirm it is still present rather than re-discovering it.

### T1.2 — Briefing / gate step (SC 2.1.1, SC 2.4.3 Focus Order)

1. `Tab` through the round briefing.
2. **PASS:** focus moves through the briefing content and its acknowledge /
   continue control in the same order the content reads visually, top to bottom.
   The gate's continue button is reachable and activates with `Enter` or `Space`.
3. **FAIL and record if:** focus jumps backwards up the page, skips the continue
   control, or lands on something invisible (watch for the ring vanishing while
   `Tab` still counts up — that is a hidden focusable element).

### T1.3 — Strategy step: the decision tiles (SC 2.1.1, SC 4.1.2 Name/Role/Value)

1. `Tab` to the first decision tile (Option A / B / C, or the pillar tiles in
   multi-pillar rounds).
2. Press `Enter`. Then `Tab` to another tile and press `Space`.
3. **PASS:** both keys select the tile; the selected tile changes appearance in
   a way that is **not colour alone** (border weight, a checkmark, a filled
   state — look for something a greyscale screenshot would still show); and you
   can move between all tiles with `Tab`/`Shift+Tab`.
4. Take a greyscale screenshot (Windows: Settings → Accessibility → Colour
   filters → Greyscale) and confirm you can still tell which tile is selected.
5. **FAIL and record if:** `Space` scrolls the page instead of selecting; a tile
   can be focused but not activated; selection is signalled by colour only.

### T1.4 — Allocation step (SC 2.1.1, SC 2.5.7 Dragging Movements)

This is the highest-risk step: the allocation surface is built on drag-and-drop
(`@dnd-kit`), and **drag-and-drop has no automated coverage at all** — the
automated suite explicitly skips it (jsdom has no layout, so drag sensors never
fire).

1. `Tab` into the allocation matrix.
2. Attempt to set an allocation for **every** business unit using only the
   keyboard. Try, in order: `Enter`/`Space` to pick up, arrow keys to move,
   `Enter` to drop, `Escape` to cancel; and separately, typing a number directly
   into any numeric field.
3. **PASS:** every allocation reachable by dragging is *also* achievable by
   keyboard, and the over-allocation warning is reachable/readable by keyboard.
4. **FAIL and record if:** any allocation can only be set by dragging. Record
   **exactly which BU** and what you tried. This is an SC 2.1.1 Level A failure
   and a contractual blocker — flag it immediately, do not batch it.

### T1.5 — Review / prediction modal (SC 2.1.2 No Keyboard Trap, SC 2.4.3)

1. `Tab` to the commit control and press `Enter` to open the pre-commit
   prediction / review modal.
2. **PASS (focus entry):** focus is already *inside* the modal — your next `Tab`
   moves within it, not to the page behind.
3. Press `Tab` repeatedly, at least one full cycle plus five more presses.
   **PASS (trap):** focus cycles within the modal and never reaches anything
   behind it. Watch the page behind for a stray focus ring.
4. Press `Shift+Tab` from the first control. **PASS:** focus wraps to the *last*
   control in the modal.
5. Press `Escape`. **PASS:** the modal closes **and focus returns to the commit
   control that opened it** — press `Enter` again and the same modal should
   reopen. This is the check people skip; do not skip it.
6. Reopen and commit with `Enter`.
7. **FAIL and record if:** `Tab` escapes to the page behind; `Escape` does
   nothing; `Escape` closes the modal but focus is dumped to `<body>` (you press
   `Tab` and land back at the top of the page).

### T1.6 — Every other modal in the player flow (SC 2.1.2, SC 2.4.3)

Repeat steps T1.5.2–T1.5.5 for each of: **Change Password**, **Focus Mode**
overlay, **Deep Dive** overlay, **Commit Results** overlay, and any confirmation
dialog you meet.

**PASS:** all four behaviours (focus in / trap / wrap / Escape-restores-focus)
hold for every one.

> Context: the shared `Dialog` primitive was introduced on 2026-08-02 precisely
> to guarantee these four. Any modal that fails is a modal that has not adopted
> it — name the modal in your report so the fix is a two-line change.

---

## TEST 2 — Screen-reader pass with NVDA

**~15 minutes. Level A. Windows only, matching the client's environment.**

### Setup

1. Start NVDA (`Ctrl+Alt+N`). The `NVDA` key is `Insert` (or `CapsLock` in
   laptop layout).
2. **Turn on speech viewer:** `NVDA menu → Tools → Speech Viewer`. This gives
   you a written transcript, which is what you paste into failure reports.
   Do not try to transcribe by ear.
3. Useful keys:
   | Key | Does |
   |---|---|
   | `NVDA+↓` | Read continuously from here |
   | `H` / `Shift+H` | Next / previous heading |
   | `D` | Next landmark |
   | `F` | Next form field |
   | `B` | Next button |
   | `T` | Next table |
   | `NVDA+F7` | Elements list (headings / links / form fields) |
   | `Ctrl` | Stop speech |

### T2.1 — Cockpit structure (SC 1.3.1 Info and Relationships, SC 2.4.6 Headings and Labels)

1. On the player cockpit, press `NVDA+F7` → Headings.
2. **PASS:** the list is a sensible outline of the page — round title, then the
   decision area, resources, market feed. Headings describe their section.
3. Press `D` repeatedly to walk landmarks.
   **PASS:** the main decision surface, the sidebar and the header are
   distinguishable regions with names.
4. **FAIL and record if:** the headings list is empty, contains only styling
   text, or the outline order does not match the visual order.

### T2.2 — Sign-in fields (SC 3.3.2 Labels or Instructions, SC 1.3.1)

1. Sign out, reload, press `F` to jump to the first form field.
2. **PASS:** NVDA announces the field's **visible label** — "Executive
   Identifier, edit" — not the placeholder.
3. Type two characters, then `Shift+Tab` and `Tab` back to the field.
   **PASS:** NVDA still announces a name for the field.
4. **KNOWN FAIL — `A11Y-F1`.** As of 2026-08-02 NVDA announces "MUR-001, edit"
   (the placeholder), and once you type, the field has no usable name at all.
   Confirm and record the exact speech-viewer text; do not re-file as new.

### T2.3 — Decision tiles (SC 1.3.1, SC 4.1.2)

1. Press `B` to reach a decision tile.
2. **PASS:** NVDA announces the option label, the option title, the button role,
   **and the cost / trade-off / impact figures a sighted player uses to decide.**
3. **KNOWN FAIL — `A11Y-F4`.** `role="button"` makes all descendant content
   presentational, so NVDA announces only "Option A: <title>, toggle button".
   The cost, the projected trade-off ("frees cash, lifts reputation"), the
   `$0 CapEx — deferred risk` warning and the whole treasury/reputation/carbon
   impact preview are **silent**. A blind participant is asked to make the
   product's central decision without the data. Confirm it is still present;
   record the speech-viewer text.

### T2.4 — Modals under NVDA (SC 4.1.2)

For the prediction/review modal and one confirmation modal:

1. Open it. **PASS:** NVDA announces the dialog **name** and the word "dialog"
   on open, then reads the first control.
2. Press `NVDA+↓`. **PASS:** NVDA reads only the modal's content and stops at
   its end — it does not read the page behind.
3. **FAIL and record if:** NVDA reads page content behind an `aria-modal`
   dialog (the dialog is lying about being modal), or the dialog is announced
   with no name ("dialog" alone).

### T2.5 — Confirmation dialog with a typed phrase (SC 3.3.2, SC 4.1.2)

1. As facilitator, trigger a destructive action that requires typing a phrase
   (e.g. a reset-all).
2. Press `F` to reach the input. **PASS:** NVDA states what to type.
3. Type the phrase. **PASS:** NVDA announces that the confirm button became
   available.
4. **KNOWN FAILS — `A11Y-F2` / `A11Y-F3`.** The input's only name is the
   placeholder (the phrase itself); the instruction "Type RESET to unlock" is
   not associated with it; and the confirm button uses `disabled`, so it is
   absent from the tab order with no explanation and no announcement when it
   unlocks. Confirm and record.

### T2.6 — Facilitator dashboard (SC 1.3.1, SC 4.1.2, SC 4.1.3 Status Messages)

1. On the facilitator dashboard with a cohort selected, press `D` to reach the
   run bar. **PASS:** announced as a region named "Live run status".
2. Read the run bar with `NVDA+↓`. **PASS:** the commit tally is spoken as
   **text** ("4 of 6 committed"), the decorative dot glyphs are silent, and the
   pacing mode and backend health are spoken as words, not implied by colour.
3. Trigger an Advance. **PASS:** the resulting status message ("Round N
   unlocked…") is **announced without moving focus** — NVDA speaks it while you
   stay put.
4. Open the **debrief narrative** tab. Press `T` to reach the ranking table,
   then read across a row with `Ctrl+Alt+→`.
   **PASS:** column headers ("Rank", "Player", "Final treasury", "Reputation")
   are announced with each cell.
5. Activate a **⛶ Project** button. **PASS:** the fullscreen projection is
   announced as a named dialog; NVDA reads its content **once**; `Tab` stays
   inside it; `Escape` closes it and returns focus to the ⛶ Project button.
6. **KNOWN FAIL — `A11Y-F5`.** The projection announces `aria-modal="true"` but
   five ⛶ Project buttons remain in the tab order outside it, and the section
   content is rendered twice, so NVDA reads the table twice. Escape and focus
   restore *do* work. Confirm and record.

---

## TEST 3 — Focus management sweep

**~5 minutes. Level A. Do this even though Tests 1 and 2 touched it — this is
the systematic pass across every modal in the product.**

For **each** modal below, run the same four checks and mark each PASS/FAIL:

| # | Check | PASS looks like | SC |
|---|---|---|---|
| a | **Focus enters** | Immediately after opening, pressing `Tab` moves within the modal — focus is already inside | 2.4.3 |
| b | **Focus is trapped** | 2 full `Tab` cycles never reach anything behind the modal; `Shift+Tab` from the first control wraps to the last | 2.1.2 |
| c | **Escape closes** | `Escape` dismisses it (except deliberately blocking modals — see below) | 2.1.2 |
| d | **Focus restores** | After closing, the control that opened it is focused again — pressing `Enter` reopens the same modal | 2.4.3 |

Modals to cover:

- Sign-in panel *(deliberately non-dismissible — **c is expected to fail by
  design**; signing in is the only exit. Verify a, b, d and that there is a
  visible way forward. Record only if there is no way out at all.)*
- Change Password *(also non-dismissible when the change is forced — same
  exemption)*
- Pre-commit prediction / review
- Commit results overlay
- Focus Mode overlay
- Deep Dive overlay
- Every admin confirmation (plain / impact / typed-phrase tiers)
- Debrief **⛶ Project** fullscreen *(known: **b fails** — `A11Y-F5`)*

**Record on failure:** modal name, which of a–d failed, and — for (b) — the
first element behind the modal that `Tab` reached.

---

## TEST 4 — Zoom to 200% and reflow at 320px

**~5 minutes. Level AA.**

### T4.1 — 200% zoom (SC 1.4.4 Resize Text)

1. On the player cockpit, press `Ctrl` + `+` until the browser reads **200%**.
2. **PASS:** all text and controls are still readable and operable; nothing is
   clipped, overlapped or cut off at a container edge; no content is lost.
   Horizontal scrolling of the *page* is acceptable at this step.
3. Repeat at 200% on: the facilitator dashboard, the prediction modal (open it
   while zoomed), and one admin confirmation modal.
4. **FAIL and record if:** text is truncated with no way to see it; two elements
   overlap so one is unreadable; a button moves off-screen with no scroll to it;
   a modal's action buttons are pushed below the fold with no scroll.

### T4.2 — Reflow at 320px (SC 1.4.10 Reflow)

1. Reset zoom to 100%. Open DevTools (`F12`) → device toolbar (`Ctrl+Shift+M`)
   → set width to **320px**, height 640px.
   *(Equivalent to 400% zoom on a 1280px display — the SC's actual definition.)*
2. **PASS:** **no horizontal scrollbar**; content reflows to one column; every
   control remains reachable and operable; the decision tiles, the allocation
   matrix and the commit button are all usable.
3. Check the facilitator run bar at 320px. **PASS:** chips wrap rather than
   overflowing; every button and the projector link remain reachable.
4. **FAIL and record if:** you must scroll horizontally to read a line of text
   or reach a control; content is clipped; a modal is wider than the viewport.

> Two-dimensional horizontal scrolling is permitted by 1.4.10 only for content
> that genuinely requires it — data tables, and arguably the allocation matrix.
> If you find horizontal scroll, record **what** scrolls; the exemption is
> narrow and a reviewer must judge it.

---

## TEST 5 — Contrast spot-checks, both themes

**~6 minutes. Level AA. Do this manually — it is the largest hole in the
automated suite.**

> **Why this cannot be automated here:** the jest suite runs in jsdom, which has
> **no CSS layout or cascade engine**. axe cannot resolve an element's effective
> background colour, so the `color-contrast` rule is *disabled* in
> `a11y-axe.test.js` — it is **not passing, it is not running**. Every contrast
> claim in this product rests on this test.

The theme toggle sets `data-theme` on `<html>` and persists to `localStorage`.
**Run every check below twice — once in dark, once in light.** The light theme
is the newer of the two and several of its tokens were only corrected on
2026-08-02 (audit item #11 / `A11Y-1` in `globals.css`).

### Thresholds (SC 1.4.3 Contrast (Minimum), SC 1.4.11 Non-text Contrast)

| What | Minimum |
|---|---|
| Body text (< 18.66px, or < 24px if bold) | **4.5:1** |
| Large text (≥ 24px, or ≥ 18.66px bold) | **3:1** |
| UI component boundaries, icons, chart series, focus rings | **3:1** |
| Disabled controls | exempt — but note them, "disabled" must not be the only cue |

### T5.1 — Spot-check list

Sample the following with the Colour Contrast Analyser (eyedropper the
foreground, then the background *actually behind it* — beware translucent
overlays, which is where this most often fails):

1. **Muted/secondary text** — the `--text-muted` / `--text-secondary` tiers.
   Sample the *dimmest* text you can find: card sub-labels, the debrief
   narrative's grey lead-in line, chip meta text, the sign-in footnote.
2. **KPI and gauge colours** — good/warn/danger numerals in the resource
   sidebar, on their actual card backgrounds.
3. **Decision tile** — title, description, the green ✓ / amber ✗ trade-off line,
   the cost figure in both its green and red states.
4. **Run bar chips** — every chip: round, commit tally, split-field warning,
   pacing, backend health. These are pale text on translucent tinted
   backgrounds, the highest-risk pattern in the app.
5. **Focus ring** — `Tab` to a button and sample the ring against the surface
   behind it. Needs **3:1** (1.4.11).
6. **Chart and gauge fills** against their plot backgrounds (1.4.11).
7. **Text over gradients or translucent overlays** — sample at the *worst* point
   of the gradient, not the middle.

**PASS:** every sample meets its threshold in **both** themes.

**FAIL and record:** the element, the two hex values, the measured ratio, the
required ratio, and the theme. Screenshot with the analyser readout visible.

### T5.2 — Colour is not the only cue (SC 1.4.1 Use of Colour)

1. Switch Windows to greyscale (Settings → Accessibility → Colour filters →
   Greyscale).
2. Walk the cockpit and the facilitator dashboard.
3. **PASS:** selected vs unselected tiles, committed vs uncommitted players,
   good vs bad KPI movement, healthy vs failing backend, and validation errors
   are all still distinguishable via text, icon, shape or position.
4. **FAIL and record if:** any status is conveyed by hue alone.

---

## TEST 6 — Projector view at distance

**~3 minutes. This is a fitness-for-purpose check, not a WCAG SC — the
projector is a room display, not a user agent surface. Related: SC 1.4.4,
SC 1.4.3, SC 1.4.1.**

1. Open `/admin/projector?cohort=<cohortId>` on the largest screen available,
   full-screen (`F11`).
2. **Stand ~10 metres back** (or, if the room is smaller, at the back wall —
   record the actual distance you used).
3. **PASS, all of:**
   - the **round number** and the **commit tally** are legible without squinting
   - the **per-player commit dots** are individually countable
   - the **top-5 team table** — names and treasury figures — is readable
   - the **pacing countdown / "facilitator advances"** text is readable
   - the **LIVE / STALE** corner stamp is distinguishable **by its text**, not
     only by its colour (check this in greyscale too — a room projector's colour
     rendition is unreliable, which is exactly why 1.4.1 matters here)
   - the rotating footer of active traps completes a full cycle and every entry
     is readable before it rotates
4. Kill the backend (or block the request in DevTools) and confirm the board
   flips to **STALE** and keeps the last good data rather than blanking or
   showing zeros.
5. **FAIL and record:** which element was illegible, the distance, the screen
   size and resolution, and a photo taken from that distance.

---

## Reporting template

```
TEST ID:        T_._
WCAG SC:        _._._ (Level A / AA) — <name>
SEVERITY:       Blocker (Level A) / Blocker (Level AA) / Advisory
URL:            
THEME:          dark / light
VIEWPORT+ZOOM:  ____ x ____ @ ____%
BROWSER / AT:   Chrome ___ / NVDA ___

STEPS:
  1.
  2.

EXPECTED:
ACTUAL:
NVDA SAID (verbatim, from speech viewer):
MEASURED RATIO (contrast items):  __:__  (required __:__)
SCREENSHOT:
```

---

## What a completed run of this document does and does not mean

**It means:** on the flows listed, in the browsers and AT listed, a
non-specialist found no failure beyond the known open findings.

**It does not mean:** the product conforms to WCAG 2.1 AA. It does not mean
every page was tested — only the player decision flow, the facilitator
dashboard and the projector were. It does not mean the product works for
disabled users; only disabled users can tell you that.

**Do not describe a clean run of this checklist as a conformance claim in any
document that reaches the client.** See `VPAT_DRAFT.md` for what is and is not
currently evidenced, and why an overclaimed VPAT is a legal liability rather
than a marketing asset.
