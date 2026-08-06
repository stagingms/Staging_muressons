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
| authored dollars | 116 amounts | content — routing them through `authoredMoney()` |
| perpetual animations | 21 | untouched; no pass has been scoped |

The 116 authored amounts are frozen by a tripwire, which is what makes them a
safe follow-up rather than a silent one.

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
