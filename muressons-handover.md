# Muressons player surface — what changed, and what to watch

Rewritten at commit 47. The previous version was written at commit 22 and
described a world that no longer exists; this replaces it rather than
appending to it.

If you read one section before the next cohort runs, read §6.

---

## 1. Where things stand

Commits 23–47 covered: the Committed·waiting stage, the results explanation,
the round timer, the accessibility floor, the whole of Phase 6 (type, spacing,
palette, the icon primitive), Phase 5's rail work, Phase 7's state work, and
the currency conversion feature.

The debt ledger, which fails a build in **both** directions:

```
sub-12px type          318   (was 357)  — and now ZERO outside the player list
off-scale spacing        0   (was 372)
raw semantic hex        110   (was 419)
perpetual animations     21   (unchanged — untouched this phase)
```

44 suites, 1,084 frontend tests. The backend carries 2,025.

---

## 2. The switches, in the order you would reach for them

`CONTEXT_DRAWER` — `ExecutiveCockpit.js:136`. The right rail becomes a drawer
summoned from the header and the belt. **This is the one that has caused
trouble**; §5 is about it. `false` restores the rail.

`SINGLE_CTA` — the only switch that changes what the primary button *does*.

`ACTION_BAR` — returns the commit control to the right rail.

`CANVAS_FIRST` — returns the decision canvas to the pre-Phase-D takeover.

Plus `cohortWaiting`, the sole route into the waiting stage, and `data-rails`
on `.mainContent`.

---

## 3. Three defects that were live in production, found by reading

**Every priced option announced its cost as a gain.** `round_configs.py`
writes an option's cost as a *negative* treasury impact — 26 impacts in that
file, 22 negative, none positive. `DecisionTile.js` had the sign backwards in
three places: `buildTradeoff()` pushed a spend onto the *good* list as "frees
cash", the screen-reader text said "Frees ₹30M" for a ₹30M expense, and the
cost rendered green. The same inversion had already been found and fixed in
the projected-impact chip and the KPI belt; it survived here because nothing
was looking at this file.

**Four modals declared `aria-modal="true"` and honoured none of it.** No focus
trap, no focus restore, and in two cases no Escape at all — including
`ArchetypeReveal`, whose own closing comment asserts that interaction with the
cockpit beneath is impossible. It was possible with the Tab key. All four now
go through the `Dialog` primitive that nine other modals already used.

**A dropped pacing poll deleted the round clock.** A failed poll and "this
round has no time limit" both left `timeLeft` null and both rendered nothing,
so one dropped request during a timed round removed the clock from every
screen in the room. The deadline is an absolute instant, so the local tick can
now carry it across failures.

---

## 4. Four lessons that each cost real time

**A check that knows one syntax reports a number that looks like the answer.**
This happened four times. The currency pass missed 47 sites because in JSX the
defect takes a different shape. The type pass found 585 CSS declarations and
missed 905 inline `fontSize`. An `!important` blind spot exempted a
declaration from the type floor entirely. And `var(--fs-xs, 0.65rem)` hid 17
sub-12px sizes from a tripwire that was asserting zero — the assertion was
true and the code was not, because the two were looking at different syntax.

**A contrast number applied to the wrong property breaks eleven things to fix
one.** I reported `#dc2626` as failing AA at 11 sites. Ten were gradient stops
and badge *fills*, where the ratio that matters is the glyph against the fill.
Exactly one used it as text.

**A source-text assertion cannot tell a declared modal from an honoured one.**
`front-page-newspaper.test.js` asserted the literal string `aria-modal="true"`
and passed for the entire time that modal had no trap, no restore and a
stack-breaking Escape handler.

**Four tripwires in this suite have been tripped by prose describing the
defect they removed.** Strip comments before asserting. It is now the habit.

---

## 5. The rail, and why it is the thing to watch

`CONTEXT_DRAWER` produced **four** regressions in one session, each found only
by a screenshot:

1. A 56px spine holding one unlabelled icon above 1300px of nothing. I had
   invented the spine — the mock has no right rail at all, and summons the
   drawer from an ✉ in the header and a "Context" button in the belt.
2. The centre did not grow into the released width, leaving 24% of the
   viewport dead black.
3. Fixing that with a centred 92ch column left dead black on *both* sides —
   two holes flanking the content, which reads as two removed panels.
4. Resources went into the drawer, sealed behind an envelope labelled
   "Messages and intelligence". **This was the fourth time this one control
   has been made unreachable while narrowing this rail.** It is a launcher for
   a separate surface, not intelligence about the round; it was only ever in
   that rail because that is where the space was. It now lives in the header,
   and a test finally pins that it is never inside the drawer.

The pattern: the three-column grid has assumptions baked in further than
source-reading reveals. Everything verifiable from source was verified;
everything needing the running app was wrong until a screenshot arrived.

**Still unverified:** whether stakeholder names inside the drawer render in
full rather than as `J…` `C…` `B…`. That truncation at 208px was the entire
argument for 360px, and it is the one claim the drawer rests on.

---

## 6. What still needs your eyes

**Walk `SINGLE_CTA` through a real commit.** Unchanged from the last handover
and still owed. This is the one place a mistake costs a workshop rather than a
screenshot.

**The waiting stage in a live multi-team session.** Solo players never see it —
`cohortTeamCount > 1` — so it has never run for real.

**A non-default currency, one full round**, and now with a rate set. Every
automated assertion runs with the symbol pinned and the rate at 1.

**The drawer**, per §5.

---

## 7. Open work, and what each needs

| item | remaining | blocked on |
|---|---|---|
| 6.3 tints | 41 sites | a screenshot — it changes appearance |
| 6.3 paper set | 19 sites | care: several sit in SVG string builders where `var()` renders as nothing |
| 6.5 icon sweep | 644 glyphs | a look at the set (delivered at commit 47) |
| 44×44 targets | 17 candidates | a pointer on a running screen |
| authored dollars | done | see §11 |
| perpetual animations | 21 | untouched; no pass has been scoped |

Authored dollars are done, and doing them turned up why they could not be done
first: the currency RATE was wired at roughly one site in eight. See §11.

---

## 8. Decisions taken, so they are not relitigated

**The legacy decision surface stays**, as a different affordance for
experienced players, with its defects fixed on their own merits rather than by
deletion. Its sign bug is fixed; the post-selection-only impact preview is
still open and is a design question, not a defect.

**Currency numbers convert**, using a super-admin rate applied once at the
`format.js` boundary — never in the engine, where `config.py`'s constants and
every tuned ratio are expressed in engine units. Authored teaching copy rounds
to **one significant figure**; computed figures keep full precision, because
rounded numbers stop summing and a team that adds the column must find it ties.

**The spacing pass resolved ties upward** — the opposite of the type pass, and
deliberately. The type rule was "nothing gets bigger without a decision";
spacing's problem is density, so a tie resolved downward would have spent the
pass making the cockpit denser.

**Gradient deep stops got a name, not a migration.** A shade of a semantic
colour is not an independent semantic colour, and three ramps were left alone
rather than shifted to make a count smaller.

---

## 9. A defect in the mock itself

`muressons-desk-mock.html` colours every impact cell by **sign** rather than by
whether the movement is good. Option B — "Approve capital without board
committee review. Breaches ESRS 1 §1.51" — renders `Gov. risk +10` in green.
The comparison table repeats it, and does the same to natural capital. Carbon,
inconsistently, is correct.

**The shipped code does not have this bug and must not be changed to match.**
The `METRICS` array carries an explicit direction per metric. Worth fixing the
mock before anyone briefs from it, since a facilitator reading it would
reasonably conclude the product teaches that breaching ESRS 1 is good.

---

## 10. Operational notes for whoever works on this next

Do not run git against the mount from a tool that cannot delete files — it
permits writes and denies unlink, so every invocation that writes the index
(including read-only `git status`) can strand a `.git/index.lock`. Use
`GIT_INDEX_FILE` pointed at `/tmp` plus `--no-optional-locks` if you must.

Commit messages must be pure ASCII (cmd code-page) and delivered via
`git commit -F`. `git add` must be a single line — bash `\` continuations do
not continue lines in cmd, and that silently staged nothing twice.

`/api/health` now reports `build.uptime_seconds`, `build.commit` and
`build.deployment`. Three times in this work, "has my deploy gone out?" had no
answer, because a still-building deploy and a *failed* one look identical from
outside — Railway keeps the previous container serving in both cases. Seconds
of uptime means it just landed.

The Docker build is cold every time: `apt-get`, a NodeSource install, `npm ci`,
then `next build`. Five to twelve minutes. Checking at ninety seconds proves
nothing.

`_to_delete/` holds every tarball and commit message from this work, and can
be deleted whole.

---

## 11. The currency rate did not work, and this is what fixing it took

Written after the authored-dollar pass, which could not be done first.

**The finding.** `money()`, `moneyM()`, `moneyFull()` and the rest all multiply
by `_rate`. **153 sites across 43 files never called them.** They took the
symbol from `format.js` and did the arithmetic themselves:

```js
{currencySymbol()}{(team.treasury / 1_000_000).toFixed(1)}M
const fmtM = (v) => `${currencySymbol()}${((v || 0) / 1e6).toFixed(1)}M`;
```

Glyph localised, quantity not — which `format.js`'s own header calls "a worse
lie than leaving it in dollars." Setting a rate would have converted about one
figure in eight and left the rest, putting figures 83× apart on one screen.

**Why nothing caught it.** Every currency tripwire in the suite asserted on the
SYMBOL. Searching the whole frontend suite for `currencyRate` / `setCurrencyRate`
returned zero hits outside `format.js`. The feature shipped with no test of its
effect. This is the fifth instance of §4's first lesson, and I wrote that lesson.

**Why the authored dollars had to wait.** They share a screen. The scorecard's
option costs (`'−$3M'`) and its EBITDA sit sixteen lines apart in one component.
Converting the copy first would have put ₹200M beside ₹8.60M for an engine value
of 8.6M — the same currency contradicting itself in one panel.

### What was done

`atRate(value)` — the rate for sites that build money by hand. It is a bridge,
not an endorsement: those 153 sites are still private formatters that will
disagree with `money()` the day someone changes the ladder. Converging them is
follow-up work that needs eyes on screens, not another sweep. It was chosen over
a migration because each site carries a precision decision (1dp here, 2dp there,
`k` in one module and `K` in another) and folding them into `money()` would move
~150 figures with no screenshot, in a session that has already shipped four
regressions found only by screenshot.

Multiplication is **linear**, so wrapping the numeric operand converts the
figure and cannot move a decimal place. At rate 1, `atRate` is `Number(v)` — an
exact identity. That is the whole safety argument, and it is asserted.

Where a component rounds first — `const damage = (x / 1e6).toFixed(1)` — the
rate lands on the **raw value at the definition**, not the rounded string, or
`.toFixed()`'s precision is thrown away. Both routes are legitimate; the tripwire
knows about both.

`localiseAuthored(text)` — the rate inside a sentence. `authoredMoney()` takes a
number, which is useless for `'every $1M of green CapEx reduces NCD by 0.5'`.
This scans a string and rewrites the amounts, applied at the **render point** —
one edit per screen rather than one per amount, because ~90 amounts sit inside
prose and wrapping each would mean restructuring the sentences.

Two decisions inside it are worth keeping:

- **Identity at rate 1.** One significant figure would turn an author's `$1.2M`
  into `1M` and `$50.00` into `50`, discarding a chosen figure for nothing.
  Rounding is right only for a number a machine just produced, so it is
  conditional on a rate having been set. At the default this is a pure glyph swap.
- **A `$` with no digits after it is a unit.** That is the guard for the
  glossary's `'per $M revenue, taxed at R10 ($250/tonne)'` — one string carrying
  a unit and an amount. It **cannot** guard a regex replacement string; `$1` in a
  `.replace()` is indistinguishable from one dollar by any text rule. That guard
  is the call site's job, and it is asserted by location.

### 116 was never the number

The old freeze counted 116 authored amounts. It was counting three things:

```
regex capture groups (InlineReviewViewer)     7
comments                                      7
authored amounts                            102
                                            ---
                                            116
```

The stripper removed a line whose FIRST token was a comment marker, so
continuation lines inside `/* */` counted as code. Three of those six comments
were sentences explaining amounts a previous pass had just converted. **That is
the fifth time a tripwire here has been tripped by its own documentation.** It is
now a state machine, not a line prefix.

The inventory now stands at 75 / 7 captures / 68 authored — but the number no
longer means "unconverted." Every remaining literal reaches the screen through a
converter, and a second test names the route per file, so a new file carrying
authored money fails until someone says how it gets converted.

### Line endings — read this before any sweep

**28 files in this repo contain `\r\r\n`**, and the repo is mixed CRLF/LF. This
is pre-existing and predates this work. Two consequences bit, both worth knowing:

1. A line-based rewrite that rejoins with one terminator silently reformats the
   whole file. Split with `/(\r\n|\r|\n)/` and rejoin the captured terminators.
2. **Two tripwires were dark because of it.** `audience-profiles` and
   `option-constraints-drift` both slice source with literal `'\n'`; when their
   target files went CRLF, `indexOf` returned −1 and the assertion passed
   vacuously or threw. Both now normalise on read, and both now pass — they had
   been failing in the tree before this work started.

### Verification

Content was verified by **AST equivalence against a pristine copy**: strip every
`atRate(...)` wrapper from the new tree and the parse must equal the old one.
Parentheses do not exist in an AST, so the check is immune to the normalisation
that defeated a textual diff. **25 files verify as pure mechanical wraps.** The
other 26 are deliberate semantic edits, each small and hand-reviewed.

The new tripwire was proved to fail: reverting one conversion in
`PeerComparison.js` fails it by name and line. A tripwire that has not been shown
to fail is worth nothing — that is now the habit alongside stripping comments.

`next build` passes. 44/44 suites, 1,097 tests.

### Still owed

A cohort on a non-default currency **with a rate set**, one full round. Every
automated assertion still runs the symbol pinned and the rate at 1, and that has
now been the gap twice.

`KPIDashboard`'s "tCO₂e per $1M Revenue" is **excluded on purpose** and is the one
place left. It is a unit, not an amount: carbon intensity is computed against
engine-unit revenue, so converting the denominator without rescaling the metric
would restate it rather than localise it. Fixing it properly is an engine
question, not a formatting one.

Amounts that duplicated a constant were derived rather than converted —
`GREEN_FUND`, `SHADOW_PRICE`, `WAR_CHEST`, `BOND_PRINCIPAL`, `FEE_BEFORE/AFTER`,
`MATERIALITY_BUDGET`, the achievement thresholds, the insetting defaults. Several
were three copies of one number: `GreenFundBidding` carried `cost: 900_000` and
`costLabel: '$900K'` side by side, and its ledger built money by hand, so the
budget, the spend and the remainder would have disagreed the moment a rate was
set. Those labels are gone; the panel now computes from one source.
