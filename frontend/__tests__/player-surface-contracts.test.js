/**
 * player-surface-contracts.test.js
 *
 * Two promises Phases 3 and 4 made, pinned so they cannot quietly lapse.
 *
 *   ONE WAY TO SAY A NUMBER (Phase 3). Before format.js there were three
 *   formatting systems and they disagreed. formatCurrency.js hard-coded '$'
 *   and ignored the session currency, kpiFormats.js built on it so it did too,
 *   and only CurrencyContext knew the real symbol — and only from inside React.
 *   A rupee cohort saw '₹16.6M' and '$11.62' on the SAME SCREEN. The same
 *   score rendered '1.4237×' on the archetype reveal and '1.42×' on the
 *   scorecard one screen later. Neither was a styling drift.
 *
 *   THE ACTION BAR (Phase 4). The commit control lived at the foot of the
 *   right rail, below ten other panels, at 12px — the token tokens.css
 *   documents as "labels, chips, meta". It is the button that advances the
 *   simulation. It now sits under the decision it commits.
 *
 * These are source-shape assertions. A browser is still the only place the
 * result can be judged; this is the cheap thing that stops the shape drifting
 * back between browser passes.
 */

const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');

const COCKPIT = 'app/components/ExecutiveCockpit.js';

// ── one way to say a number ─────────────────────────────────────────────────

describe('number formatting', () => {
  test('format.js is the only store of the currency symbol', () => {
    const fmt = read('app/utils/format.js');
    expect(fmt).toMatch(/let _symbol/);
    expect(fmt).toMatch(/export function setCurrencySymbol/);

    // exactly one writer, and it is the provider that owns the currency
    const writers = ['app/contexts/CurrencyContext.js', 'app/utils/format.js', 'app/utils/formatCurrency.js',
      'app/utils/kpiFormats.js', 'app/components/GameOverSummary.js', 'app/components/ArchetypeReveal.js']
      .filter((f) => /setCurrencySymbol\s*\(/.test(read(f)) && !f.endsWith('format.js'));
    expect(writers).toEqual(['app/contexts/CurrencyContext.js']);
  });

  test('formatCurrency delegates rather than hard-coding a glyph', () => {
    // strip comments first: the file's own docblock quotes the bug it fixed,
    // and an assertion that reads prose is an assertion about prose.
    const fc = read('app/utils/formatCurrency.js').replace(/\/\*[\s\S]*?\*\//g, '');
    expect(fc).toMatch(/from '\.\/format'/);
    // the old shape: a literal glyph in a template, whatever the session currency
    expect(fc).not.toMatch(/\$\$\{/);
    expect(fc).not.toMatch(/'\$'/);
  });

  test('the same score cannot render at two precisions', () => {
    // M_R is a multiple; utils/format.ratio fixes it at 2dp for everyone.
    // M_R was rendered at 2dp, 3dp AND 4dp across two adjacent screens; M_SDG
    // at 4dp, including the literal '1.0000× (track not used)'.
    for (const f of ['app/components/ArchetypeReveal.js', 'app/components/GameOverSummary.js']) {
      expect({ [f]: read(f).match(/toFixed\([34]\)/g) || [] }).toEqual({ [f]: [] });
    }
    expect(read('app/utils/format.js')).toMatch(/toFixed\(2\)\}×/);
  });

  test('the minus sign is the one that aligns in a tabular column', () => {
    // U+2212 shares the advance width of a digit; the ASCII hyphen does not,
    // so a column of negatives visibly stutters.
    const fmt = read('app/utils/format.js');
    expect(fmt).toContain("const MINUS = '−'");
    expect(fmt).toContain("const EMPTY = '—'");
  });

  test('the migrated surfaces no longer carry a hard-coded currency glyph', () => {
    // A ratchet, not a rule: FrontPageReveal (23) and the R2 gate still do, and
    // both are named in the plan. Lower these as each is migrated.
    const DEBT = {
      'app/components/ArchetypeReveal.js': 0,
      'app/components/GameOverSummary.js': 0,
      'app/components/FrontPageReveal.js': 8,
    };
    for (const [f, base] of Object.entries(DEBT)) {
      // `$${...}` — a literal dollar immediately before an interpolation — is
      // the shape a hard-coded currency glyph actually takes here.
      const src = read(f).replace(/\/\*[\s\S]*?\*\//g, '');
      const n = (src.match(/\$\$\{/g) || []).length + (src.match(/'\$'|"\$"/g) || []).length;
      expect(`${f}: ${n} <= ${base}`).toBe(`${f}: ${Math.min(n, base)} <= ${base}`);
    }
  });
});

// ── the action bar ──────────────────────────────────────────────────────────

describe('action bar', () => {
  const src = read(COCKPIT);

  test('the commit control renders in the centre column, not the right rail', () => {
    const bar   = src.indexOf('styles.actionBar');
    const commit = src.indexOf('styles.rightCommit');
    const rail  = src.indexOf('styles.rightSidebar');
    expect(bar).toBeGreaterThan(-1);
    expect(commit).toBeGreaterThan(bar);   // inside the bar
    expect(commit).toBeLessThan(rail);     // and before the rail even opens
  });

  test('the bar carries the step indicator too, so progress and action are one object', () => {
    const bar = src.indexOf('styles.actionBar');
    const checklist = src.indexOf('{roundChecklist && (');
    expect(checklist).toBeGreaterThan(bar);
    expect(checklist).toBeLessThan(src.indexOf('styles.rightSidebar'));
  });

  test('the primary action clears the 44px target minimum', () => {
    // Was `height: 34` in a 24% column.
    expect(src).toMatch(/minHeight: 48/);
    expect(src).not.toMatch(/width: '100%', height: 34/);
  });

  test('button labels name the outcome, not the state machine', () => {
    expect(src).toContain('Commit this round');
    for (const dev of ['Complete Steps', 'Over-Allocated', 'Commit Decisions']) {
      expect({ label: dev, present: src.includes(dev) }).toEqual({ label: dev, present: false });
    }
  });

  test('disabled is a surface change, not opacity alone', () => {
    // opacity on a dark surface takes a disabled label under 3:1; the state has
    // to be readable to be a state.
    expect(src).not.toMatch(/opacity: 0\.85, cursor: 'not-allowed'/);
  });

  test('the rollback is one line, like CANVAS_FIRST', () => {
    expect(src).toMatch(/const ACTION_BAR = true;/);
  });
});

// ── the breadcrumb that could read "Step 0 / 2" ─────────────────────────────

describe('focus overlay breadcrumb', () => {
  test('no step counter can render, so none can render as zero', () => {
    // HISTORY: the header read "Step {currentIdx + 1} / {steps.length}".
    // `results` is a reachable focusStep that is never pushed into focusSteps,
    // so indexOf returned -1 and the header said "Step 0 / 2". That was first
    // fixed with a `currentIdx >= 0` guard, and this test pinned the guard.
    //
    // The counter is now GONE, not guarded. Once each stage grew a headline of
    // its own, the header was naming the screen twice within fourteen vertical
    // pixels, and step position was already shown — better — by the round
    // checklist beneath the canvas, which names all five steps rather than
    // three. So the assertion moves up a level: the defect is unreachable
    // because the feature that could express it does not exist.
    const fo = read('app/components/FocusOverlay.js');
    expect(fo).not.toMatch(/Step \{currentIdx \+ 1\}/);
    expect(fo).not.toMatch(/stepBadge/);
    expect(fo).not.toMatch(/styles\.stepLabel/);
  });

  test('the stage still announces itself to a screen reader', () => {
    // Removing the header heading removed a focus target. Losing it silently
    // would mean a keyboard user gets no signal that the stage changed — a
    // worse regression than the one above. Focus moves to the panel region,
    // whose aria-label carries the step name.
    const fo = read('app/components/FocusOverlay.js');
    expect(fo).toMatch(/panelRef\.current\?\.focus\(\)/);
    // both variants — inline canvas and fullscreen takeover — must be targets
    expect((fo.match(/ref=\{panelRef\}/g) || []).length).toBe(2);
    expect((fo.match(/aria-label=\{`Decision (canvas|stage) —/g) || []).length).toBe(2);
  });
});

// ── no component may mint its own currency symbol ───────────────────────────

/**
 * WHY THIS EXISTS
 *   The Phase 3 fix routed formatCurrency.js and kpiFormats.js through
 *   format.js, so every call site THROUGH THEM became currency-aware — and the
 *   test above pinned that. What neither caught is that ~45 components never
 *   called them: each carried a private
 *
 *       const fmtM = (v) => `$${(v / 1_000_000).toFixed(1)}M`
 *
 *   with the glyph baked into a template literal. So a rupee cohort still saw
 *   "Capital deployed ₹5.6M" beside "GROUP EBITDA $12.3M" on one screen, while
 *   the suite stayed green. A single-writer assertion is worthless without a
 *   no-bypass assertion beside it.
 *
 *   The player tree is derived here rather than listed, because a hand-kept
 *   list is exactly what goes stale when someone adds a component.
 */

const walkPlayerTree = () => {
  const seen = new Set();
  const resolve = (from, spec) => {
    if (!spec.startsWith('.')) return null;
    const base = path.normalize(path.join(path.dirname(from), spec));
    for (const c of [base, base + '.js', base + '.jsx', path.join(base, 'index.js')]) {
      if (fs.existsSync(c) && fs.statSync(c).isFile()) return c;
    }
    return null;
  };
  const visit = (f) => {
    if (seen.has(f)) return;
    seen.add(f);
    let src;
    try { src = fs.readFileSync(f, 'utf8'); } catch { return; }
    const re = /(?:from\s+|import\s*\(\s*)["'`]([^"'`]+)["'`]/g;
    let m;
    while ((m = re.exec(src))) {
      const r = resolve(f, m[1]);
      if (r) visit(r);
    }
  };
  ['app/page.js', 'app/layout.js'].forEach((r) => visit(path.join(root, r)));
  return [...seen]
    .filter((f) => /\.jsx?$/.test(f))
    .filter((f) => !/utils[\\/]format\.js$/.test(f))
    .sort();
};

describe('currency symbol has exactly one source', () => {
  const tree = walkPlayerTree();

  test('the player tree is actually being walked', () => {
    // If the resolver silently stops working this whole describe passes
    // vacuously, which is the failure mode a count test cannot see.
    expect(tree.length).toBeGreaterThan(100);
    expect(tree.some((f) => /ExecutiveCockpit\.js$/.test(f))).toBe(true);
    expect(tree.some((f) => /KPIDashboard\.js$/.test(f))).toBe(true);
  });

  test('no JSX text renders a bare glyph before an expression', () => {
    // THE HOLE THE FIRST SWEEP LEFT. The check below finds `$${expr}` inside
    // TEMPLATE literals. In JSX a hard-coded glyph looks different — literal
    // text followed by an expression container:
    //
    //     <div>${(bs.net_assets / 1e6).toFixed(0)}M</div>
    //
    // No backticks, so the template regex never saw it. Four survived the
    // 121-site sweep; three were caught by eye and the fourth was still in the
    // results panel a day later.
    //
    // A line regex cannot tell this from `${x}` inside a multi-line template
    // literal — 78 SVG and HTML string builders match the same shape. So this
    // reads the AST instead: a JSXText node whose text ends in a currency
    // glyph, immediately followed by an expression. That is the defect and
    // nothing else is.
    const parser = require('@babel/parser');
    const offenders = [];
    const GLYPHS = ['$', '£', '€', '¥', '₹'];

    const walk = (node, file, onJsx) => {
      if (!node || typeof node !== 'object') return;
      if (Array.isArray(node)) { node.forEach((n) => walk(n, file, onJsx)); return; }
      if (node.type === 'JSXElement' || node.type === 'JSXFragment') onJsx(node, file);
      for (const k of Object.keys(node)) {
        if (k === 'loc' || k === 'leadingComments' || k === 'trailingComments') continue;
        walk(node[k], file, onJsx);
      }
    };

    for (const f of tree) {
      let ast;
      try {
        ast = parser.parse(fs.readFileSync(f, 'utf8'), { sourceType: 'module', plugins: ['jsx'] });
      } catch {
        continue;   // a parse failure is another test's problem, not this one's
      }
      walk(ast, f, (el) => {
        const kids = el.children || [];
        kids.forEach((child, i) => {
          if (child.type !== 'JSXText') return;
          const next = kids[i + 1];
          if (!next || next.type !== 'JSXExpressionContainer') return;
          const trimmed = child.value.replace(/\s+$/, '');
          if (GLYPHS.includes(trimmed.slice(-1))) {
            offenders.push(`${path.relative(root, f)}:${child.loc.end.line}  ${trimmed.trim().slice(-60)}{…}`);
          }
        });
      });
    }
    expect(offenders).toEqual([]);
  });

  test('no component interpolates a number after a hard-coded glyph', () => {
    const offenders = [];
    for (const f of tree) {
      fs.readFileSync(f, 'utf8').split(/\r?\n/).forEach((line, i) => {
        if (/\$\$\{/.test(line.replace(/^\s*(\/\/|\*|\/\*).*$/, ''))) {
          offenders.push(`${path.relative(root, f)}:${i + 1}  ${line.trim().slice(0, 90)}`);
        }
      });
    }
    // Listed, not counted: a failure should say WHERE without a second run.
    expect(offenders).toEqual([]);
  });

  test('authored dollar amounts in copy are frozen, not forgotten', () => {
    // These are NOT formatter output — they are scenario copy: option cost
    // labels, briefing text, the $40/tonne shadow price, glossary entries.
    // The narrative is denominated in dollars by an author, and converting it
    // would need the underlying scenario numbers converted too. That is a
    // content decision, not a formatting one, so the count is frozen rather
    // than driven to zero: it cannot grow without someone saying so.
    let count = 0;
    for (const f of tree) {
      fs.readFileSync(f, 'utf8').split(/\r?\n/).forEach((line) => {
        const code = line.replace(/^\s*(\/\/|\*|\/\*).*$/, '');
        count += (code.match(/\$(?=[\d,]|\s?[A-Z]?\d)/g) || []).length;
      });
    }
    // Fails in BOTH directions, like the ui-budgets ledger: converting copy to
    // the session currency is welcome, but it must lower this number on purpose.
    expect(count).toBe(116);
  });

  test('format.js carries the fixed-unit formatters the components now share', () => {
    const fmt = read('app/utils/format.js');
    expect(fmt).toMatch(/export function moneyM\(/);
    expect(fmt).toMatch(/export function moneyMScaled\(/);
    // both must read the one symbol, not a literal
    const bodies = fmt.split(/export function /).filter((b) => /^money/.test(b));
    expect(bodies.length).toBeGreaterThanOrEqual(3);
    for (const b of bodies) expect(b).toContain('_symbol');
  });
});

// ── one primary action, and every gate still on it ──────────────────────────

describe('the single CTA', () => {
  const src = read(COCKPIT);

  test('it is a one-line rollback, like the two before it', () => {
    expect(src).toMatch(/const SINGLE_CTA = true;/);
    // the two stage buttons it replaces must be GUARDED, not deleted, or the
    // flag rolls back to a screen with no way forward at all
    expect((src.match(/\{!SINGLE_CTA && \(/g) || []).length).toBe(2);
  });

  test('advancing runs no gates; committing runs all of them', () => {
    // Moving from the decision to the allocation is not the irreversible act,
    // so it must not be gated. The commit still is — and the order matters:
    // observer, then decision, then allocation, then preflight, then modal.
    const onClick = src.slice(src.indexOf('if (commitResults) return;'));
    const iObserver  = onClick.indexOf('showStageWarning(\'Observer view');
    const iAdvance   = onClick.indexOf('if (advanceTo)');
    const iDecision  = onClick.indexOf('Select a Strategic Option');
    const iAlloc     = onClick.indexOf('Allocate capital across');
    const iPreflight = onClick.indexOf('onPreflight()');
    const iModal     = onClick.indexOf('setShowPredictionModal(true)');
    for (const [name, i] of Object.entries({ iObserver, iAdvance, iDecision, iAlloc, iPreflight, iModal })) {
      expect({ [name]: i > -1 }).toEqual({ [name]: true });
    }
    // observer refusal precedes everything, including the advance
    expect(iObserver).toBeLessThan(iAdvance);
    // and the advance returns before any commit gate is consulted
    expect(iAdvance).toBeLessThan(iDecision);
    expect(iDecision).toBeLessThan(iAlloc);
    expect(iAlloc).toBeLessThan(iPreflight);
    expect(iPreflight).toBeLessThan(iModal);
  });

  test('the bar still means COMMIT when there is no canvas to advance through', () => {
    // With the canvas dismissed there is no stage machine on screen. If the
    // button kept trying to advance, a player on the dashboard would press the
    // round's primary action and watch nothing happen.
    expect(src).toMatch(/const advanceTo = \(SINGLE_CTA && isFocusActive && !commitResults\)/);
  });

  test('the label names the next act, never the missing state, while advancing', () => {
    expect(src).toContain("'Continue to capital →'");
    // and the old in-canvas duplicate wording is gone from the live path
    expect(src).toContain("'Lock Decision & Continue →'");   // still present, but behind !SINGLE_CTA
    const guarded = src.slice(src.indexOf('{!SINGLE_CTA && ('));
    expect(guarded).toContain('Lock Decision & Continue →');
  });
});

// ── the waiting stage is a hold, never a trap ───────────────────────────────

describe('committed · waiting', () => {
  const hook = read('app/hooks/useRoundStage.js');

  test('a solo player can never enter it', () => {
    // cohortWaiting is the ONLY gate into 'waiting', and the cockpit computes
    // it from a team count greater than one. Get this wrong and a solo session
    // stops dead after its first commit, forever, with no button to press.
    const src = read(COCKPIT);
    expect(src).toMatch(/const cohortWaiting = !!commitResults\s*\n\s*&& cohortTeamCount > 1/);
    expect(hook).toMatch(/if \(cohortWaiting\) return 'waiting';/);
  });

  test('it releases itself, and does not need a click to do it', () => {
    // The poll that refreshes global_state flips cohortWaiting; the stage must
    // follow it out. Without this effect a team that waited would still be
    // waiting after the last table committed.
    expect(hook).toMatch(/if \(focusStep === 'waiting' && !cohortWaiting\)/);
    expect(hook).toMatch(/setFocusStep\('results'\)/);
  });

  test('the facilitator release and the timeout both dissolve it', () => {
    // cohort_advance_unblocked is set by Force Advance and by the free-mode
    // timeout. One absent team must not be able to hold a room.
    const src = read(COCKPIT);
    expect(src).toMatch(/globalState\?\.cohort_advance_unblocked !== true/);
  });

  test('the barrier is computed once, not copied a third time', () => {
    // Two copies of this predicate already existed — the results advance
    // button and the journey gate. A third would be the one that drifts.
    const src = read(COCKPIT);
    expect((src.match(/const cohortWaiting =/g) || []).length).toBe(1);
  });
});

// ── the results screen summons its deep dives ───────────────────────────────

describe('results deep dives', () => {
  const src = read(COCKPIT);

  test('every panel is behind a link, and every link has a panel', () => {
    // The failure this guards is an affordance that opens nothing: a link
    // offered while its visibility switch is off. Same rule as the Charts tab,
    // which used to open an empty panel when kpi_dashboard was off.
    for (const id of ['chain', 'retrospect', 'ebitda', 'peers']) {
      expect({ [id]: src.includes(`resultsPanel === '${id}'`) }).toEqual({ [id]: true });
    }
    // and each link declares the same gate its panel does
    for (const gate of ['consequence_replay', 'round_retrospect', 'ebitda_waterfall', 'peer_benchmarking']) {
      const uses = (src.match(new RegExp(`isPlayerVisible\\('${gate}'\\)`, 'g')) || []).length;
      expect({ [gate]: uses >= 2 }).toEqual({ [gate]: true });
    }
  });

  test('nothing was deleted to shorten the screen', () => {
    // The point was to summon these, not to drop them. All four components
    // must still be rendered somewhere in this file.
    for (const c of ['ConsequenceReplay', 'EngineEventsPanel', 'EBITDAWaterfall', 'peerLeaderboard']) {
      expect(src).toContain(c);
    }
  });

  test('the disclosure state is announced, not just styled', () => {
    expect(src).toMatch(/aria-expanded=\{resultsPanel === p\.id\}/);
  });

  test('a second click closes it', () => {
    // A disclosure that only opens leaves a player unable to get back to the
    // short screen the change exists to give them.
    expect(src).toMatch(/setResultsPanel\(resultsPanel === p\.id \? null : p\.id\)/);
  });
});

// ── one position indicator per screen ───────────────────────────────────────

describe('where-am-I is stated once', () => {
  const fo = read('app/components/FocusOverlay.js');

  test('the canvas drops the breadcrumb; the takeover keeps it', () => {
    // The action bar's step row names all five steps directly beneath the
    // canvas. Three emoji dots above it were the third statement of position
    // on one screen. But the takeover variant is the CANVAS_FIRST rollback —
    // a fullscreen overlay that COVERS the action bar — so removing the
    // breadcrumb outright would leave that path with no indicator at all.
    expect(fo).toMatch(/\{variant !== 'inline' && \(/);
    expect(fo).toMatch(/styles\.breadcrumb/);
  });

  test('the header still names nothing, and the step row still names everything', () => {
    const rc = read('app/components/RoundChecklist.js');
    expect(fo).not.toMatch(/styles\.stepLabel/);
    for (const step of ['Briefing', 'Decision', 'Capital', 'Commit']) {
      expect(rc).toContain(step);
    }
  });
});

// ── the wait shows the claim, it does not ask for a second one ──────────────

describe('prediction echo', () => {
  const src = read(COCKPIT);

  test('the waiting stage reads the SAME key the commit modal writes', () => {
    // Two different keys would mean the wait quotes nothing while the debrief
    // holds a prediction, and nobody would notice because both are "working".
    const writes = src.match(/`prediction_r\$\{roundNumber\}_\$\{sim\?\.sessionId \|\| 'demo'\}`/g) || [];
    expect(writes.length).toBe(2);   // one setItem at commit, one getItem in the wait
    expect(src).toMatch(/sessionStorage\.setItem\(key, predictionText\)/);
    expect(src).toMatch(/sessionStorage\.getItem\(`prediction_r/);
  });

  test('it never writes a second prediction', () => {
    // A second input here would overwrite the pre-commit one — which is the
    // more interesting of the two, made while the decision could still change.
    const waitBlock = src.slice(src.indexOf('THE PREDICTION THE PLAYER ALREADY MADE'), src.indexOf('ONLY WHAT EXISTS'));
    expect(waitBlock).not.toMatch(/setItem|<textarea|onChange=/);
  });

  test('no prediction recorded falls back to the nudge, not an empty quote', () => {
    expect(src).toMatch(/if \(recorded && recorded\.trim\(\)\)/);
    expect(src).toContain('While you wait');
  });

  test('a storage failure cannot take the stage down with it', () => {
    // Private mode throws on sessionStorage access. The wait screen is between
    // a player and their results; it must not be the thing that breaks.
    const waitBlock = src.slice(src.indexOf('THE PREDICTION THE PLAYER ALREADY MADE'), src.indexOf('ONLY WHAT EXISTS'));
    expect(waitBlock).toMatch(/try \{[\s\S]*?\} catch/);
  });
});

// ── the round clock reads what the endpoint sends ───────────────────────────

describe('countdown timer', () => {
  const t = read('app/components/CountdownTimer.js');
  const backend = fs.readFileSync(path.join(root, '..', 'backend', 'admin_router.py'), 'utf8');

  test('it reads the keys GET /pacing actually returns', () => {
    // It read pacing_mode, deadline_utc and round_duration_seconds — three keys
    // the endpoint has never returned. Every poll fell through to null, so a
    // facilitator could set a per-round time and no player ever saw a clock.
    // Strip comments: the fix's own note names the three dead keys, and an
    // assertion that reads prose is an assertion about prose. Third time this
    // trap has been set in this file.
    const code = t.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
    for (const dead of ['pacing_mode', 'deadline_utc', 'round_duration_seconds']) {
      expect({ [dead]: code.includes(dead) }).toEqual({ [dead]: false });
    }
    expect(t).toMatch(/data\.mode === 'timed'/);
    expect(t).toMatch(/data\.next_unlock_at/);
    expect(t).toMatch(/data\.interval_seconds/);
  });

  test('and the endpoint still returns them — drift here is silent', () => {
    // If the backend renames a key, the clock stops and nothing errors. This is
    // the assertion that turns that into a failing build.
    const handler = backend.slice(backend.indexOf('async def get_pacing'), backend.indexOf('async def get_pacing') + 600);
    for (const key of ['"mode"', '"next_unlock_at"', '"interval_seconds"']) {
      expect({ [key]: handler.includes(key) }).toEqual({ [key]: true });
    }
  });

  test('a bad timestamp cannot start a runaway countdown', () => {
    expect(t).toMatch(/Number\.isNaN\(deadline\)/);
  });

  test('the bar variant exists and carries a screen-reader label', () => {
    // A clock that re-announces itself every second is unusable with a screen
    // reader on, so the visible one is aria-hidden and a static label sits
    // beside it.
    expect(t).toMatch(/variant === 'bar'/);
    expect(t).toMatch(/aria-hidden="true">\{clock\} left/);
    expect(t).toMatch(/minutes \{secs\} seconds left in this round/);
  });
});

// ── the results screen says why, in the engine's words ──────────────────────

describe('results explanation', () => {
  const src = read(COCKPIT);

  test('the sentence comes from the catalog, never from the cockpit', () => {
    // consequenceCatalog.js already maps every engine flag to an explain()
    // written for a student. Authoring a second sentence here would be a
    // causal claim the cockpit is not entitled to make.
    expect(src).toMatch(/lookupConsequence\(k\)/);
    expect(src).toMatch(/typeof x\.entry\.explain === 'function'/);
  });

  test('an unrecognised flag yields no sentence, not a guess', () => {
    expect(src).toMatch(/if \(!pick\) return null;/);
    expect(src).toMatch(/isIgnoredKey\(k\)/);
  });

  test('a throwing explain() cannot take the results screen down', () => {
    // These are arbitrary functions over engine payloads. One bad shape must
    // not be the thing standing between a team and their outcomes.
    const block = src.slice(src.indexOf("WHY IT MOVED"), src.indexOf('THE OUTCOME TILES'));
    expect(block).toMatch(/try \{[\s\S]*?\} catch \{ return null; \}/);
  });

  test('bad news is picked before good', () => {
    // When a round both helped and hurt, the cost is what a team needs at the
    // top; the upside is what they already expected.
    const block = src.slice(src.indexOf("WHY IT MOVED"), src.indexOf('THE OUTCOME TILES'));
    expect(block.indexOf("severity === 'bad'")).toBeLessThan(block.indexOf("severity === 'good'"));
  });
});

// ── phase 8: the floor that did not exist ───────────────────────────────────

describe('accessibility floor', () => {
  const g = read('app/globals.css');
  const layout = read('app/layout.js');
  const src = read(COCKPIT);

  test('there is a skip link, and it targets something real', () => {
    // A cockpit with three columns and a rail of tabs is a lot of stops before
    // a keyboard user reaches the decision.
    expect(layout).toMatch(/className="skip-link"/);
    expect(layout).toMatch(/href="#main-stage"/);
    expect(src).toMatch(/id="main-stage"/);
    // and the target must be focusable, or focus stays where it was
    expect(src).toMatch(/id="main-stage" tabIndex=\{-1\}/);
    expect(g).toMatch(/\.skip-link\s*\{/);
    expect(g).toMatch(/\.skip-link:focus\s*\{/);
  });

  test('one h1 per screen, and it is the round', () => {
    // The only h1 in the tree was inside the crisis overlay, so the outline a
    // screen reader offered went straight to h2. Stage heads stay h2; this is
    // their parent.
    expect(src).toMatch(/<h1 className="sr-only">/);
  });

  test('sr-only exists and hides without collapsing the text', () => {
    expect(g).toMatch(/\.sr-only\s*\{/);
    // clip-path, not the legacy clip; nowrap so a long label is not reflowed
    // into a 1px column before it is read
    expect(g).toMatch(/clip-path: inset\(50%\)/);
    expect(g).toMatch(/white-space: nowrap/);
  });

  test('one focus ring, defined as a token', () => {
    // Two ring colours and dozens of `outline: none` overrides meant "where am
    // I" depended on which component a keyboard user had reached.
    expect(g).toMatch(/--focus-ring:/);
    expect(g).toMatch(/:focus-visible\s*\{[\s\S]*?outline: var\(--focus-ring\)/);
  });
});

// ── phase 5.3: an opt-out that survives a refresh ───────────────────────────

describe('dashboard preference', () => {
  const hook = read('app/hooks/useRoundStage.js');

  test('it is stored, not held in a ref that dies on reload', () => {
    // A ref makes it a suggestion. A facilitator asking a room to reload got
    // the overlay forced back on for the rest of the session.
    expect(hook).toMatch(/localStorage\.setItem\(PREF_KEY/);
    expect(hook).toMatch(/localStorage\.getItem\(PREF_KEY\)/);
  });

  test('keyed by session, so it does not follow a player into the next cohort', () => {
    expect(hook).toMatch(/muressons_prefers_dashboard_\$\{sessionId \|\| 'demo'\}/);
  });

  test('storage being disabled cannot take the round-stage machine down', () => {
    const reads = hook.match(/try \{[^}]*localStorage[\s\S]*?catch/g) || [];
    expect(reads.length).toBeGreaterThanOrEqual(2);
  });
});


/* ── PHASE 8: every modal goes through the one primitive ──────────────────────

   Dialog.js provides role="dialog", aria-modal, an accessible name, a focus
   trap (2.1.2), focus restore (2.4.3), topmost-only Escape via a module-level
   stack, and a refcounted scroll lock. Four components declared the first two
   attributes by hand and honoured none of the rest:

     AnnualReport      Escape only — no trap, no restore
     FrontPageReveal   Escape only — no trap, no restore, full-viewport
     ArchetypeReveal   nothing at all, on a terminal screen
     ShortcutSheet     nothing of its own — a keyboard-shortcut sheet that a
                       keyboard user could Tab straight out of

   The defect this locks is not "a modal lacks a trap". It is that declaring
   aria-modal="true" by hand LOOKS like the fix, passes any grep for it, and
   delivers none of the behaviour the attribute promises to a screen reader.

   So: assert that nothing outside Dialog.js writes those attributes on a
   plain element. A new modal either adopts the primitive or fails here. */
describe('modal accessibility is centralised', () => {
  const parser = require('@babel/parser');

  const walk = (dir, out = []) => {
    for (const e of fs.readdirSync(path.join(root, dir), { withFileTypes: true })) {
      const rel = `${dir}/${e.name}`;
      if (e.isDirectory()) { if (e.name !== 'node_modules') walk(rel, out); continue; }
      if (e.name.endsWith('.js')) out.push(rel);
    }
    return out;
  };

  const handRolled = () => {
    const offenders = [];
    for (const f of walk('app')) {
      if (f === 'app/components/Dialog.js') continue;
      let ast;
      try {
        ast = parser.parse(read(f), { sourceType: 'module', plugins: ['jsx'] });
      } catch { continue; }
      JSON.stringify(ast, (k, v) => {
        if (v && v.type === 'JSXOpeningElement' && v.name?.type === 'JSXIdentifier'
            && v.name.name !== 'Dialog') {
          for (const a of v.attributes) {
            if (a.type !== 'JSXAttribute') continue;
            const isRoleDialog = a.name.name === 'role'
              && a.value?.type === 'StringLiteral' && a.value.value === 'dialog';
            if (isRoleDialog || a.name.name === 'aria-modal') {
              offenders.push(`${f}:${v.loc.start.line}`);
            }
          }
        }
        return v;
      });
    }
    return [...new Set(offenders)];
  };

  test('no component hand-rolls role="dialog" or aria-modal', () => {
    expect(handRolled()).toEqual([]);
  });

  test('the four that used to are now adopters', () => {
    for (const f of ['AnnualReport', 'FrontPageReveal', 'ArchetypeReveal', 'ShortcutSheet']) {
      const s = read(`app/components/${f}.js`);
      expect(`${f} imports Dialog: ${/import Dialog from '\.\/Dialog'/.test(s)}`)
        .toBe(`${f} imports Dialog: true`);
      expect(`${f} renders Dialog: ${/<Dialog\b/.test(s)}`)
        .toBe(`${f} renders Dialog: true`);
    }
  });

  test('none of them keeps a private Escape listener beside the shared one', () => {
    // Two handlers for one key is how a stacked dialog collapses both — which
    // is the exact reason Dialog keeps a module-level stack.
    for (const f of ['AnnualReport', 'FrontPageReveal', 'ArchetypeReveal', 'ShortcutSheet']) {
      const s = read(`app/components/${f}.js`).replace(/\/\*[\s\S]*?\*\//g, '');
      expect(`${f}: ${/addEventListener\('keydown'/.test(s)}`).toBe(`${f}: false`);
    }
  });

  test('the terminal reveal is non-dismissible, not un-trapped', () => {
    // ArchetypeReveal has nowhere to dismiss TO — the run is over. That is a
    // reason for dismissible={false}, not a reason to skip the trap.
    const s = read('app/components/ArchetypeReveal.js');
    expect(s).toMatch(/dismissible=\{false\}/);
    // And its own body-overflow lock is gone: two independent locks racing
    // over one style property is how a page gets stuck unscrollable.
    expect(s).not.toMatch(/document\.body\.style\.overflow = 'hidden'/);
  });
});
