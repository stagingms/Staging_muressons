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
  test('a stage outside the step list does not render Step 0', () => {
    // `results` is a reachable focusStep but is never pushed into focusSteps,
    // so indexOf returned -1 and the breadcrumb read "Step 0 / 2".
    const fo = read('app/components/FocusOverlay.js');
    expect(fo).not.toMatch(/Step \{currentIdx \+ 1\} \/ \{steps\.length\}/);
    expect(fo).toMatch(/currentIdx >= 0/);
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
<<<<<<< HEAD
    expect(count).toBe(116);
=======
    expect(count).toBe(117);
>>>>>>> ui/player-surface-phases-0-4
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

