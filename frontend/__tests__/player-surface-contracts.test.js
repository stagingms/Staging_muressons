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

