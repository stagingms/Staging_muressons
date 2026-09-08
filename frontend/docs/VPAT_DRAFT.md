# Accessibility Conformance Report — **DRAFT / INCOMPLETE**

### VPAT® Version 2.5 Rev — WCAG Edition

---

> # ⚠ THIS IS NOT A CONFORMANCE CLAIM. DO NOT SEND IT TO A CLIENT.
>
> **Status: DRAFT SCAFFOLD. The overwhelming majority of criteria below are
> marked `Not Evaluated`, which is a statement of ignorance, not of failure.**
>
> A VPAT is a **legal representation**. In the United States it is relied on for
> Section 508 procurement decisions; in the EU it feeds EN 301 549 and the
> European Accessibility Act. Under this client's contract it is a
> representation about a contractual deliverable.
>
> **An overclaimed VPAT is a liability, not a marketing asset.** Marking a
> criterion "Supports" when you have not tested it is a misrepresentation that
> survives in procurement records for years, transfers risk from the buyer to
> the vendor, and is discoverable. The FTC has treated inaccurate accessibility
> conformance statements as deceptive-practice exposure, and every published
> Section 508 procurement dispute turns on the accuracy of exactly this
> document. **The correct entry for an untested criterion is `Not Evaluated`.
> There is no penalty for honesty here and there is real exposure in the
> alternative.**
>
> **Nothing in this document may be changed from `Not Evaluated` without a
> named evidence source recorded in the Remarks column.**

---

## 1. Product and report information

| Field | Value |
|---|---|
| **Product name** | Muressons Global — simulation platform (web frontend) |
| **Product version** | *(fill in at publication — do not leave blank)* |
| **Report date** | 2026-08-02 — **DRAFT** |
| **Report version** | 0.1 (scaffold) |
| **Contact** | *(accessibility owner — to be assigned)* |
| **Evaluation methods used** | **Partial and automated only.** (a) axe-core 4.12 via `jest-axe` 11 over six components rendered in isolation in jsdom — `frontend/__tests__/a11y-axe.test.js`; (b) source review of those same components. **No** assistive-technology testing, **no** browser-rendered testing, **no** testing with disabled users, and **no** evaluation of the majority of the product's surfaces has been performed. |
| **Notes** | See §3 "Scope and limits of the evidence" before reading any row. |

## 2. Applicable standards

| Standard | Included in this report |
|---|---|
| WCAG 2.1 Level A | Yes — **scaffolded, almost entirely Not Evaluated** |
| WCAG 2.1 Level AA | Yes — **scaffolded, almost entirely Not Evaluated** |
| WCAG 2.1 Level AAA | No |
| Revised Section 508 (36 CFR 1194) | Not addressed in this draft |
| EN 301 549 | Not addressed in this draft |

### Conformance-level terms (VPAT 2.5 definitions)

| Term | Meaning |
|---|---|
| **Supports** | The functionality meets the criterion **without** known defects. |
| **Partially Supports** | Some functionality meets the criterion; **known defects exist**. |
| **Does Not Support** | The majority of the functionality does not meet the criterion. |
| **Not Applicable** | The criterion is not relevant to the product. |
| **Not Evaluated** | **The criterion has not been tested.** No claim of any kind is made. |

---

## 3. Scope and limits of the evidence

**What was actually done on 2026-08-02:**

- An automated axe-core scan of **six components**, rendered in isolation:
  `Dialog`, `ConfirmModal`, `JoinCohortModal`, `DecisionTile` (+ `PillarTile`),
  `RunBar`, `DebriefNarrative`.
- A source review of those same six components.

**What that evidence cannot support:**

1. **Automated tooling detects roughly a third of WCAG failures.** On these six
   components axe reported **zero violations**, and a hand review of the same
   six found **five real AA-relevant defects** (§5). A clean automated run is
   not evidence of conformance; it is evidence that one class of defect is
   absent.
2. **jsdom has no layout or cascade engine.** Contrast, reflow, resize and
   target-size rules were therefore **disabled** in the automated suite — they
   did not run and did not pass. Any claim about 1.4.3, 1.4.4, 1.4.10, 1.4.11
   rests on source review and hand measurement only.
3. **No assistive technology was used.** Nothing here has been heard through
   NVDA, JAWS, VoiceOver, Narrator, Dragon or a switch device.
4. **Component-level ≠ page-level.** Components audited in isolation cannot
   evidence landmark structure, heading order, reading order, bypass blocks,
   page titles, or language of page. Those rows stay `Not Evaluated`.
5. **Most of the product was not looked at.** `ExecutiveCockpit`, the capital
   allocation surface (`@dnd-kit`), `/admin/projector`, `/admin/god-mode`,
   `/admin/war-map`, `/admin/shockwave`, `/admin/trading-floor`, the results and
   scorecard surfaces, and every chart (`recharts`) and 3-D view
   (`@react-three/fiber`) are entirely unevaluated.

**Criteria pre-filled below (6 of 50):** 1.4.3, 2.1.1, 2.4.3, 2.4.7, 4.1.2, and
2.5.8 (see the note on 2.5.8 in §6). **Every one is `Partially Supports`** —
none is claimed as `Supports`, because in each case the evidence covers only
part of the product and a known defect exists.

Several further criteria (notably 1.4.1, 2.1.2, 3.3.2, 4.1.3) have *partial*
code evidence from this work but are deliberately left `Not Evaluated`, because
the evidence covers too little of the product to support even a partial claim.
That is the conservative direction and it is the correct one.

**To move any row off `Not Evaluated`,** execute
`docs/ACCESSIBILITY_MANUAL_TESTS.md`, record the result, and cite it in Remarks.
Automated results alone are never sufficient for a `Supports` rating.

---

## 4. WCAG 2.1 Level A

| Criterion | Conformance Level | Remarks and Explanations |
|---|---|---|
| **1.1.1** Non-text Content | Not Evaluated | Requires human judgement of whether alt text and `aria-label`s are *meaningful*; no tool can assess this. Icon-only and emoji-glyph controls across the cockpit are unreviewed. |
| **1.2.1** Audio-only and Video-only (Prerecorded) | Not Evaluated | Determine first whether the product contains prerecorded media; if not, this becomes Not Applicable. |
| **1.2.2** Captions (Prerecorded) | Not Evaluated | As 1.2.1. |
| **1.2.3** Audio Description or Media Alternative (Prerecorded) | Not Evaluated | As 1.2.1. |
| **1.3.1** Info and Relationships | Not Evaluated | **Two known defects already identified** (`A11Y-F1`, `A11Y-F4`, §5), so this criterion will not reach "Supports". Left Not Evaluated rather than "Partially Supports" because no page-level structural review has been done. |
| **1.3.2** Meaningful Sequence | Not Evaluated | Requires reading-order review in a real browser. MANUAL TEST 2.1. |
| **1.3.3** Sensory Characteristics | Not Evaluated | Requires copy review for instructions that rely on shape/position/colour alone. |
| **1.4.1** Use of Color | Not Evaluated | Partial evidence exists: `RunBar` deliberately pairs every colour cue with text and the commit tally is textual. Not claimed — the greyscale sweep across the cockpit and dashboard (MANUAL TEST 5.2) has not been run. |
| **1.4.2** Audio Control | Not Evaluated | `CockpitSounds` plays audio on commit and on warnings. Determine whether any sound plays automatically for >3s and whether a pause/stop/volume control exists. **Likely risk area.** |
| **2.1.1** Keyboard | **Partially Supports** | **Evidence:** `DecisionTile.js` exposes `role="button"`, `tabIndex={0}`, `aria-pressed` and Enter/Space handlers; the two inline legacy A/B/C tile renders in `ExecutiveCockpit.js` were brought to the same contract (UX audit #8 / `A11Y-2`, 2026-08-02). `Dialog.js` moves focus into every adopting modal and cycles Tab within it. Automated pins in `__tests__/a11y-axe.test.js` ("DecisionTile is keyboard operable"). **Known limits:** the capital-allocation surface is built on `@dnd-kit` and **its keyboard alternative is unverified** — the automated suite skips it explicitly because jsdom has no layout boxes for drag sensors to resolve. If any allocation is drag-only this criterion drops to *Does Not Support*. MANUAL TEST 1.4 is the deciding check. Charts (`recharts`) and 3-D views (`@react-three/fiber`) are also unevaluated. |
| **2.1.2** No Keyboard Trap | Not Evaluated | Partial evidence: `Dialog.js` implements Tab/Shift+Tab cycling and Escape (topmost-dialog only, via a module-level stack). Not claimed — `DebriefNarrative`'s projected overlay does **not** use `Dialog` and does not trap focus (`A11Y-F5`, §5), and no browser-level verification of the other overlays has been done. MANUAL TEST 3. |
| **2.1.4** Character Key Shortcuts | Not Evaluated | Audit for single-character shortcuts; if none exist this becomes Not Applicable. |
| **2.2.1** Timing Adjustable | Not Evaluated | **Likely risk area.** Round pacing has timed unlocks and the projector view runs a countdown. Determine whether any time limit affects the *user's* ability to complete a task and whether it can be extended. |
| **2.2.2** Pause, Stop, Hide | Not Evaluated | **Likely risk area.** The market ticker, the projector's rotating trap footer, `framer-motion` animation and the R5 dice-roll animation are all auto-updating/moving content. `prefers-reduced-motion` is honoured in `globals.css`, which is relevant but is **not** the same as an author-provided pause mechanism. |
| **2.3.1** Three Flashes or Below Threshold | Not Evaluated | Review the dice-roll animation, shockwave effects and any alert flashing. |
| **2.4.1** Bypass Blocks | Not Evaluated | Page-level; no skip-link was observed but this was not tested. |
| **2.4.2** Page Titled | Not Evaluated | Page-level; requires route-by-route review of Next.js metadata. |
| **2.4.3** Focus Order | **Partially Supports** | **Evidence:** `Dialog.js` (added 2026-08-02, UX audit #18 / `A11Y-3`) captures `document.activeElement` on open, moves focus into the dialog — to `initialFocusRef`, else the first focusable node, else the dialog itself — and restores focus to the invoking element on close, guarded by `document.contains()`. Pinned by automated tests: focus-lands-inside, initialFocusRef honoured, empty-dialog fallback, and Escape-restores-focus. Adopted by `ConfirmModal` and `JoinCohortModal`. **Known limits:** *focus order* also requires that the tab sequence be *logical*, which no automated test can assess — unverified across every screen. `DebriefNarrative`'s projected overlay restores focus correctly but does not trap it (`A11Y-F5`). Modals that have not adopted `Dialog` are unaudited. MANUAL TESTS 1 and 3. |
| **2.4.4** Link Purpose (In Context) | Not Evaluated | Requires review of link text across all surfaces. |
| **2.5.1** Pointer Gestures | Not Evaluated | **Likely risk area** — the allocation surface uses drag. Determine whether any path-based or multipoint gesture lacks a single-pointer alternative. |
| **2.5.2** Pointer Cancellation | Not Evaluated | Audit for actions fired on `pointerdown` rather than `pointerup`/`click`. |
| **2.5.3** Label in Name | Not Evaluated | Requires checking that every `aria-label` contains its visible text. Note `DecisionTile`'s `aria-label` is `"OPTION A: <title>"` while the visible text is the icon + `"OPTION A"` + title — plausibly compliant, but unverified. |
| **2.5.4** Motion Actuation | Not Evaluated | Likely Not Applicable; confirm no device-motion input exists. |
| **3.1.1** Language of Page | Not Evaluated | Page-level; check `<html lang>` in `app/layout.js`. The automated suite disables `html-has-lang` because components are not rendered in a document. |
| **3.2.1** On Focus | Not Evaluated | Requires browser testing for context changes on focus. |
| **3.2.2** On Input | Not Evaluated | Requires browser testing for context changes on input. |
| **3.3.1** Error Identification | Not Evaluated | Partial evidence: `JoinCohortModal` renders an error box and `DebriefNarrative` uses `role="alert"`. Not claimed — errors are not systematically associated with their fields, and `ConfirmModal`'s locked confirm button gives no identification of what is wrong (`A11Y-F3`, §5). |
| **3.3.2** Labels or Instructions | Not Evaluated | **Two known defects already identified** (`A11Y-F1`, `A11Y-F2`, §5). Will not reach "Supports". |
| **4.1.1** Parsing | Not Evaluated | Removed from WCAG 2.2 and deprecated in practice; retained here because VPAT 2.5 Rev WCAG for a **2.1** claim still lists it. Note as such rather than deleting the row. |
| **4.1.2** Name, Role, Value | **Partially Supports** | **Evidence:** `Dialog.js` guarantees `role="dialog"` + `aria-modal="true"` + an accessible name via `aria-labelledby` (when a heading id is supplied) or `aria-label`, and never both. `DecisionTile` exposes `role="button"` + `aria-pressed`. `RunBar` exposes `role="region"` with `aria-label="Live run status"` and marks its decorative dot glyphs `aria-hidden`. `DebriefNarrative` uses `scope="col"` table headers, `role="alert"` on error and named `⛶ Project` buttons. axe-core reports **zero** name/role/value violations across all six audited components. **Known limits and defects:** `A11Y-F4` — `role="button"` makes `DecisionTile`'s descendants presentational, so the cost, trade-off and impact figures are **not exposed to assistive technology at all**; `A11Y-F5` — `DebriefNarrative`'s projection asserts `aria-modal="true"` while five controls remain outside it in the tab order, i.e. the role's value is a false statement to AT; `A11Y-F2`/`A11Y-F3` — unnamed phrase input and a `disabled` (rather than `aria-disabled`) confirm button. Charts, 3-D views and all unaudited surfaces are unknown. |
| **4.1.3** Status Messages | Not Evaluated | *(Level AA — listed here for adjacency; the canonical row is in §5's AA table.)* See below. |

---

## 5. WCAG 2.1 Level AA

| Criterion | Conformance Level | Remarks and Explanations |
|---|---|---|
| **1.2.4** Captions (Live) | Not Evaluated | Determine whether live media exists; likely Not Applicable. |
| **1.2.5** Audio Description (Prerecorded) | Not Evaluated | As 1.2.4. |
| **1.3.4** Orientation | Not Evaluated | Check for any orientation lock. Likely Supports, but untested. |
| **1.3.5** Identify Input Purpose | Not Evaluated | **Likely risk area.** `JoinCohortModal`'s identifier field sets `autoComplete="off"`; the password field's autocomplete purpose is unset. Requires review against the WCAG input-purpose token list. |
| **1.4.3** Contrast (Minimum) | **Partially Supports** | **Evidence:** dark-theme text tiers were raised and the ratios recorded inline in `app/globals.css` — `--text-secondary: #b0bec5` (5.8:1), `--text-muted: #8899a6` (4.6:1). Light-theme tokens were corrected on 2026-08-02 (UX audit #11 / `A11Y-1`) with measured ratios recorded per token against the `#f1f5f9` light surface: `--accent-cyan #0e7490` 3.36:1→**4.89:1**, `--accent-gold #b45309` 2.91:1→**4.58:1**, `--gauge-green #047857` 3.44:1→**5.01:1**, `--gauge-yellow #b45309` **4.58:1**, `--gauge-red #b91c1c` 4.41:1→**5.91:1**. A high-contrast mode also exists (`.mur-high-contrast`). **Known limits — this is the weakest evidence in the report.** The automated suite **disables** axe's `color-contrast` rule entirely, because jsdom has no layout or cascade engine and cannot resolve an effective background colour; the rule did not run and did not pass. The measured ratios above are token-level and were computed against *nominal* surfaces — they do **not** account for the many translucent/tinted backgrounds (`RunBar`'s chips, gradient overlays, `backdrop-filter` panels), where the effective background differs from the token's assumed one. Several hundred inline colour literals remain unmigrated. Rendered-page measurement in both themes (MANUAL TEST 5) has **not** been performed. |
| **1.4.4** Resize Text | Not Evaluated | No 200% zoom test performed; jsdom cannot evaluate it. MANUAL TEST 4.1. |
| **1.4.5** Images of Text | Not Evaluated | Requires review for text baked into images. |
| **1.4.10** Reflow | Not Evaluated | No 320px reflow test performed. A `min-height: 44px` wrapping header rule exists at the mobile breakpoint, which is suggestive but not evidence. MANUAL TEST 4.2. |
| **1.4.11** Non-text Contrast | Not Evaluated | The focus ring (`2px solid var(--accent-cyan)`, `outline-offset: 2px`) and control boundaries have **not** been measured against their surfaces. Same jsdom limitation as 1.4.3. MANUAL TEST 5.1 items 5–6. |
| **1.4.12** Text Spacing | Not Evaluated | Requires applying the WCAG text-spacing bookmarklet and checking for clipping. |
| **1.4.13** Content on Hover or Focus | Not Evaluated | **Likely risk area.** `GlobalTooltip`, `PillarSelectDropdown`'s portalled hover card, and the many native `title` attributes must be dismissable, hoverable and persistent. `DecisionTile` uses `onMouseEnter`/`onMouseLeave` with **no focus equivalent**, so hover content is plausibly unavailable to keyboard users — verify. |
| **2.4.5** Multiple Ways | Not Evaluated | Determine applicability for an application-style product. |
| **2.4.6** Headings and Labels | Not Evaluated | Partial evidence: `Dialog` requires an accessible name and `ConfirmModal`/`JoinCohortModal` supply one. Not claimed — heading descriptiveness across the product is unreviewed, and 2.4.6 also covers form labels, where `A11Y-F1`/`A11Y-F2` are open. |
| **2.4.7** Focus Visible | **Partially Supports** | **Evidence:** a global focus-ring system exists in `app/globals.css`, explicitly authored against this SC — `:focus-visible { outline: 2px solid var(--accent-blue); outline-offset: 2px }`, with a stronger ring for interactive elements (`button, a, input, select, textarea`): `2px solid var(--accent-cyan)` plus a `0 0 0 4px rgba(6,182,212,0.15)` halo. `:focus:not(:focus-visible)` suppresses the ring on mouse click only. `.decisionTile:focus-visible` carries a component-level rule. **Known limits:** the ring's **contrast against its surrounding surface has not been measured** in either theme (that is 1.4.11, still Not Evaluated), and no rendered test confirms the ring is not clipped by `overflow: hidden` ancestors — a common real-world failure given the cockpit's scroll containers, and one this codebase has already hit once (the `PillarSelectDropdown` clipping bug). Custom-styled controls that set their own `outline: none` are unaudited. |
| **3.1.2** Language of Parts | Not Evaluated | |
| **3.2.3** Consistent Navigation | Not Evaluated | |
| **3.2.4** Consistent Identification | Not Evaluated | |
| **3.3.3** Error Suggestion | Not Evaluated | Requires review of whether error messages suggest a correction. |
| **3.3.4** Error Prevention (Legal, Financial, Data) | Not Evaluated | Partial evidence: `ConfirmModal`'s three tiers (plain / blast-radius impact / typed-phrase) are a deliberate reversal-and-confirmation mechanism for destructive admin actions, and round commit is gated behind a review/prediction step. Not claimed — coverage across all destructive actions is unverified, and `A11Y-F2`/`A11Y-F3` mean the confirmation gate is itself partly inaccessible. |
| **4.1.3** Status Messages | Not Evaluated | Partial evidence: `RunBar` uses `role="status"` for its flash notices, `DebriefNarrative` uses `role="alert"` for load failures, and its loading card sets `aria-busy`. Not claimed — no AT verification, and several state changes are silent (notably `ConfirmModal`'s lock→unlock transition, `A11Y-F3`). MANUAL TEST 2.6. |

---

## 6. Note on Target Size (2.5.8) — **out of scope for a WCAG 2.1 report**

**2.5.8 Target Size (Minimum) is a WCAG 2.2 Level AA criterion. It does not
exist in WCAG 2.1** and therefore has no legitimate row in a VPAT 2.5 Rev WCAG
report scoped to 2.1 A/AA. The nearest 2.1 criterion is **2.5.5 Target Size
(Enhanced), Level AAA**, which is outside this report's scope.

Evidence gathered on 2026-08-02 is recorded here so it is not lost, and so that
if the contract is later read as requiring WCAG 2.2, this row has a starting
point. **It is not a claim against WCAG 2.1.**

| Criterion | Conformance Level | Remarks and Explanations |
|---|---|---|
| **2.5.8** Target Size (Minimum) — *WCAG 2.2 AA, informational only* | **Partially Supports** *(unscoped)* | **Evidence:** a 44×44px floor is applied at specific sites — `DebriefNarrative`'s projection close button (`minWidth: 44, minHeight: 44`) and its retry button (`minHeight: 44`); the projector footer (`minHeight: 44`); the cockpit header at the mobile breakpoint (`min-height: 44px`); `ResourceSidebar` and `AnalyticsControlPanel` controls (44×44px); `admin/page.module.css` (`min-height: 44px`). Note 2.5.8's actual threshold is **24×24 CSS px** with spacing exceptions; 44px is the stricter 2.5.5/mobile-guideline figure, so where it is applied it comfortably clears 2.5.8. **Known limits:** application is **ad hoc, not systematic**. Many controls set only padding and font-size — e.g. `RunBar`'s Advance/Pacing/Projector controls (`padding: 0.3rem 0.7rem`, `font-size: 0.72rem`), `ConfirmModal`'s buttons (`padding: 0.5rem 1.1rem`) and `DebriefNarrative`'s `⛶ Project` button (`minHeight: 32`) — whose rendered height is **below 44px and possibly below 24px**. None of this has been measured in a browser: jsdom has no layout, so the automated suite cannot evaluate target size at all and explicitly skips it. |

---

## 7. Known defects carried into this report

All five were found by **source review**, not by the scanner. axe-core reported
**zero violations** on the very same components. They are pinned as
`test.failing` cases in `frontend/__tests__/a11y-axe.test.js`, which pass while
the defect exists and fail the moment it is fixed.

| ID | Component | Criterion | Severity | Defect |
|---|---|---|---|---|
| `A11Y-F1` | `JoinCohortModal` | 1.3.1 (A), 3.3.2 (A) | **Serious** | Both credential fields have a visible `<label>` with no `htmlFor` and no wrapping, and the inputs have no `id`/`aria-label`/`aria-labelledby`. axe's `label` rule passes **only** because of a non-empty `placeholder` — an axe-documented but explicitly weak pass condition. A screen reader announces the placeholder as the name, and the placeholder vanishes on typing. This is the first screen every participant sees. |
| `A11Y-F4` | `DecisionTile` | 1.3.1 (A), 4.1.2 (A) | **Serious** | `role="button"` is *children-presentational* per WAI-ARIA, so the description, projected trade-off, cost figure, `$0 CapEx` deferred-risk warning and the entire treasury/reputation/carbon impact preview are stripped from the accessibility tree. A blind participant is asked to make the product's central decision with none of the data a sighted participant sees. |
| `A11Y-F5` | `DebriefNarrative` | 4.1.2 (A), 2.4.3 (A) | Moderate | The projected fullscreen overlay declares `aria-modal="true"` but does not trap focus — five `⛶ Project` buttons remain outside it in the tab order — and renders `{children}` twice, so AT announces the section content twice. Background scroll is not locked. It is the one dialog in scope that did not adopt the shared `Dialog` primitive; Escape and focus restore *do* work. |
| `A11Y-F2` | `ConfirmModal` | 1.3.1 (A), 3.3.2 (A) | Moderate | The typed-phrase input's only accessible name is `placeholder={requirePhrase}` (the phrase itself), and the instruction "Type RESET to unlock:" is an unassociated sibling `<div>`. On the highest-consequence control in the admin surface, AT users get no instruction. |
| `A11Y-F3` | `ConfirmModal` | 4.1.2 (A), 3.3.1 (A) | Moderate | The locked confirm button uses the `disabled` attribute, removing it from the tab order with no explanation of what would unlock it; the lock→unlock transition is never announced. Remedy: `aria-disabled="true"` + keep it focusable + `aria-describedby` + a polite live region. |

---

## 8. Required work before any row moves off `Not Evaluated`

1. Execute `docs/ACCESSIBILITY_MANUAL_TESTS.md` in full and record results.
2. Fix `A11Y-F1`–`A11Y-F5` (all are small, local changes) and delete the
   corresponding `test.failing` markers.
3. Extend automated coverage beyond the six components — in particular the
   capital-allocation surface, which is unevaluated for **2.1.1 (Level A)** and
   is the single largest conformance risk in the product.
4. Test with real assistive technology: NVDA + Chrome/Edge on Windows at
   minimum; JAWS and VoiceOver if the audience warrants.
5. Engage a qualified accessibility auditor for the criteria that require
   professional judgement (1.1.1, 1.3.2, 1.3.3, 2.4.4, 3.3.3, and the media and
   timing criteria).
6. Test with disabled users. Nothing above substitutes for this.
7. Only then publish, with a named accessibility owner and a real product
   version — and only with the conformance levels the recorded evidence
   actually supports.

---

*VPAT® is a registered trademark of the Information Technology Industry Council
(ITI). This draft follows the VPAT 2.5 Rev WCAG structure. It has not been
reviewed by a qualified accessibility auditor and must not be published,
distributed to a client, or cited in a procurement response in its current
state.*
