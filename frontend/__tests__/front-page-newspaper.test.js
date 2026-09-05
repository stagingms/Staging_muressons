/**
 * The Year-5 newspaper and the "3 Key Insights" block must report the run that
 * was actually played.
 *
 * THE REPORTED DEFECT
 * -------------------
 * The scorecard printed:
 *     🏆 Best Decision        Round 9 … "OPTION C" generated +$0.0M
 *     💸 Most Costly Mistake  Round 9 … "OPTION C" cost      $0.0M
 * The same round, twice, for zero dollars — in a run where the treasury had in
 * fact swung by hundreds of millions.
 *
 * Two independent causes, both pinned below:
 *   1. WRONG FIELD. The block read `h.treasury ?? h.corporate_treasury` off a
 *      history row. A row is { round_number, choice_selected, business_units,
 *      global_state } and the balance lives at
 *      `global_state.corporate_treasury`. Both reads were undefined, `?? 0`
 *      turned them into zeros, and every delta was 0 − 0.
 *   2. NO DEGENERACY GUARD. With all deltas equal, the two reduces both walk to
 *      the last row, so best === worst. Nothing refused to print.
 *
 * Fixing (1) alone is not enough: a genuinely flat run would still print two
 * confident, contradictory claims. So the suppression rule is pinned too.
 */
const fs = require('fs');
const path = require('path');
const React = require('react');
const { render, screen, fireEvent, act } = require('@testing-library/react');

// These assertions are about the NUMBERS — that best and worst are different
// rounds carrying real figures — not about which currency the cohort runs in.
// They were written when every formatter hard-coded '$'; format.js now defaults
// to the app's real default (₹, per CurrencyContext.DEFAULT_CURRENCY). Pinning
// the symbol here says out loud which currency the expectations below assume,
// instead of inheriting a module default that can move underneath them.
require('../app/utils/format').setCurrencySymbol('$');

const APP = path.join(__dirname, '..', 'app');
const {
  deriveKeyInsights,
  roundLedger,
  rowTreasury,
  choiceLabel,
  fmtDeltaM,
} = require('../app/lib/keyInsights');

/** The real dashboard row shape, with the real numbers from a played run.
 *  Row K is the state ENTERING round K (row 1 = the seed); CLOSING is what
 *  round 10 produced — the history never carries it (SEAM-08). */
const REAL = [
  [1, 'option_b', 49500000.0, 47.0],
  [2, 'option_c', 39720216.88, 52.29],
  [3, 'option_b', 44515682.11, 42.29],
  [4, 'option_a', 42260721.99, 51.29],
  [5, 'option_a', 40256384.44, 22.95],
  [6, 'option_c', 17593154.9, 50.29],
  [7, 'option_c', 10359101.46, 42.29],
  [8, 'option_b', -10263520.06, 47.29],
  [9, 'option_c', -42650419.57, 29.29],
  [10, 'option_c', -188544427.86, 37.29],
].map(([round_number, choice_selected, corporate_treasury, group_reputation]) => ({
  round_number,
  choice_selected,
  business_units: [],
  global_state: { corporate_treasury, group_reputation },
}));
const CLOSING = { corporate_treasury: -200044427.86, group_reputation: 12.29 };

describe('keyInsights — reads the real history shape', () => {
  test('the treasury comes from global_state, not the row top level', () => {
    // THE bug, isolated: the row has no `treasury` and no top-level
    // `corporate_treasury`.
    expect(REAL[0].treasury).toBeUndefined();
    expect(REAL[0].corporate_treasury).toBeUndefined();
    expect(rowTreasury(REAL[0])).toBe(49500000.0);
  });

  test('deltas are real, not a column of zeroes', () => {
    const led = roundLedger(REAL, CLOSING);
    const deltas = led.filter((r) => Number.isFinite(r.delta)).map((r) => r.delta);
    expect(deltas).toHaveLength(10);
    expect(deltas.every((d) => d === 0)).toBe(false);
    // Round 2's call: entered on row 2, produced row 3.
    expect(led[1].round).toBe(2);
    expect(led[1].delta).toBeCloseTo(44515682.11 - 39720216.88, 2);
    expect(led[1].treasury).toBeCloseTo(44515682.11, 2);
    expect(led[1].choice).toBe('Option C');
  });

  test('round 1 has a real delta — the seed row is its opening balance', () => {
    const led = roundLedger(REAL, CLOSING);
    expect(led[0].round).toBe(1);
    expect(led[0].opening).toBe(49500000.0);
    expect(led[0].treasury).toBeCloseTo(39720216.88, 2);
    expect(led[0].delta).toBeCloseTo(39720216.88 - 49500000.0, 2);
  });

  test('round 10 closes on the closing state, and is not listed without one', () => {
    const led = roundLedger(REAL, CLOSING);
    expect(led).toHaveLength(10);
    expect(led[9].round).toBe(10);
    expect(led[9].treasury).toBeCloseTo(CLOSING.corporate_treasury, 2);
    expect(led[9].delta).toBeCloseTo(CLOSING.corporate_treasury - (-188544427.86), 2);
    expect(led[9].reputation).toBeCloseTo(12.29, 2);
    // The history alone says nothing about what round 10 produced.
    const bare = roundLedger(REAL);
    expect(bare).toHaveLength(9);
    expect(bare[8].round).toBe(9);
    // A game-over global_state (the dashboard shape) works as the closing state too.
    expect(roundLedger(REAL, { global_state: CLOSING })[9].treasury).toBeCloseTo(CLOSING.corporate_treasury, 2);
  });

  test('a round still being played has no outcome and is not listed', () => {
    // Mid-game: rows 1..5, the team is playing round 5. Passing the current
    // global_state as "closing" must not manufacture a round-5 outcome.
    const mid = REAL.slice(0, 5);
    const led = roundLedger(mid, mid[4].global_state);
    expect(led.map((r) => r.round)).toEqual([1, 2, 3, 4]);
  });

  test('an is_final row in the history is not a round of its own', () => {
    const withFinal = [...REAL, { round_number: 11, is_final: true, global_state: CLOSING }];
    const led = roundLedger(withFinal, CLOSING);
    expect(led.map((r) => r.round)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  });

  test('best and worst are different rounds with different, real figures', () => {
    const ki = deriveKeyInsights(REAL, CLOSING);
    expect(ki).not.toBeNull();
    expect(ki.best.round).not.toBe(ki.worst.round);
    expect(ki.best.delta).toBeGreaterThan(0);
    expect(ki.worst.delta).toBeLessThan(0);
    // Round 2's call is the only one that gained; round 9's is the collapse.
    expect(ki.best.round).toBe(2);
    expect(ki.worst.round).toBe(9);
    expect(fmtDeltaM(ki.best.delta)).toBe('+$4.8M');
    expect(fmtDeltaM(ki.worst.delta)).toBe('−$145.9M');
  });

  test('choices are labelled from choice_selected', () => {
    expect(choiceLabel(REAL[2])).toBe('Option B');
    expect(choiceLabel({ choice_selected: null })).toBeNull();
  });

  test('the reputation swing is the round whose call moved it, with its from/to', () => {
    const ki = deriveKeyInsights(REAL, CLOSING);
    expect(ki.swing.round).toBe(4);          // round 4's call: 51.29 -> 22.95, the largest jump
    expect(ki.swing.from).toBeCloseTo(51.29, 2);
    expect(ki.swing.reputation).toBeCloseTo(22.95, 2);
    expect(ki.swing.change).toBeLessThan(0);
  });
});

describe('keyInsights — refuses to invent an insight', () => {
  const flat = (n) => Array.from({ length: n }, (_, i) => ({
    round_number: i + 1,
    choice_selected: 'option_a',
    global_state: { corporate_treasury: 1_000_000 },
  }));

  test('a flat run yields no best/worst at all', () => {
    // Every delta identical -> nothing distinguishes them. This is the exact
    // state the old code reached via undefined fields, and it must print
    // NOTHING rather than the same round twice.
    expect(deriveKeyInsights(flat(6))).toBeNull();
  });

  test('a single scored round is not enough', () => {
    expect(deriveKeyInsights(flat(1))).toBeNull();
    expect(deriveKeyInsights([])).toBeNull();
    expect(deriveKeyInsights(null)).toBeNull();
  });

  test('rows with no treasury at all are not scored as zero', () => {
    const rows = [
      { round_number: 1, choice_selected: 'option_a', global_state: {} },
      { round_number: 2, choice_selected: 'option_b', global_state: {} },
    ];
    expect(roundLedger(rows).every((r) => r.treasury === null)).toBe(true);
    expect(deriveKeyInsights(rows)).toBeNull();
  });

  test('reputation that never moves yields no third insight', () => {
    const rows = REAL.map((r) => ({
      ...r,
      global_state: { ...r.global_state, group_reputation: 50 },
    }));
    expect(deriveKeyInsights(rows).swing).toBeNull();
  });
});

/* ── Source tripwires: the shapes that caused the defect ──────────────────── */

const gameOver = fs.readFileSync(path.join(APP, 'components', 'GameOverSummary.js'), 'utf8');
const frontPage = fs.readFileSync(path.join(APP, 'components', 'FrontPageReveal.js'), 'utf8');
/** Strip comments so a tripwire cannot match its own explanation. */
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
const gameOverCode = strip(gameOver);

describe('tripwires', () => {
  test('nothing reads a treasury off the top level of a history row', () => {
    expect(gameOverCode).not.toMatch(/history\[[^\]]*\]\?\.\s*treasury/);
    expect(gameOverCode).not.toMatch(/h\?\.\s*treasury\b/);
    expect(gameOverCode).not.toMatch(/h\?\.\s*corporate_treasury\b/);
  });

  test('both surfaces derive insights from the one shared module', () => {
    expect(gameOver).toMatch(/from '\.\.\/lib\/keyInsights'/);
    expect(frontPage).toMatch(/from '\.\.\/lib\/keyInsights'/);
    // …and the scorecard hands over the closing state (row K is the state
    // ENTERING K, so round 10's outcome is not in the history — SEAM-08).
    expect(gameOverCode).toMatch(/deriveKeyInsights\(history, globalState\)/);
    expect(strip(frontPage)).toMatch(/roundLedger\(history, closing\)/);
  });

  test('the scorecard bails out when the derivation declines', () => {
    // Without this, a null return would crash instead of printing nothing.
    expect(gameOverCode).toMatch(/if \(!ki\) return null;/);
  });

  test('the toggle tooltip describes what the panel renders today', () => {
    // CLAUDE.md: a tooltip must describe what its surface RENDERS today —
    // change the surface, change the tooltip, same commit. Three prior audits
    // found aspirational tooltips. This one advertised "Best Decision / Most
    // Costly Mistake / Road Not Taken" after the third insight became the
    // reputation swing and the second was renamed.
    const registry = fs.readFileSync(path.join(APP, 'config', 'playerVisibilityRegistry.js'), 'utf8');
    const entry = registry.split('\n').find((l) => l.includes("key: 'three_key_insights'"));
    expect(entry).toBeDefined();
    expect(entry).toMatch(/Sharpest Reputation Swing/);
    expect(entry).not.toMatch(/Road Not Taken/);
    expect(entry).not.toMatch(/Most Costly Mistake/);
    // The insight titles the component actually renders.
    for (const title of ['Best Decision', 'Most Costly Decision', 'Sharpest Reputation Swing']) {
      expect(gameOverCode).toContain(title);
    }
  });

  test('no counterfactual is asserted without a computed counterfactual', () => {
    // The old third insight told players "an alternative approach could have
    // changed your trajectory" for a round nothing had modelled. The newspaper
    // may only speak about alternatives via decision_regret, which the engine
    // actually computes.
    expect(strip(gameOver)).not.toMatch(/Road Not Taken/);
    expect(frontPage).toMatch(/data\.decision_regret/);
  });
});

describe('the newspaper is a full-screen four-column broadsheet', () => {
  test('the body is set in four columns, narrowing on small screens', () => {
    expect(frontPage).toMatch(/\.fpr-body\s*\{[^}]*column-count:\s*4/);
    expect(frontPage).toMatch(/@media \(max-width:1500px\)\{ \.fpr-body\{ column-count:3; \} \}/);
    expect(frontPage).toMatch(/@media \(max-width:720px\)\s*\{ \.fpr-body\{ column-count:1; \} \}/);
  });

  test('the edition itself takes the whole screen', () => {
    expect(frontPage).toMatch(/position: 'fixed', inset: 0/);
  });

  /* PHASE 8. This used to assert the literal string aria-modal="true" in the
     source. That passed for as long as the modal hand-rolled its own overlay —
     and it passed while the same overlay had NO focus trap, NO focus restore
     and an Escape handler that fired even when something was stacked on top of
     it. A source-text assertion on one attribute cannot tell a declared modal
     from an honoured one.

     The edition now goes through the Dialog primitive, which is where
     aria-modal, the trap, the restore and topmost-only Escape all come from.
     Assert the adoption, not the attribute — and assert the two properties
     specific to THIS modal, because Dialog's own guarantees are tested in
     Dialog's own suite. */
  test('the edition is a real modal: it adopts Dialog, and the paper is not a backdrop', () => {
    expect(frontPage).toMatch(/import Dialog from '\.\/Dialog'/);
    expect(frontPage).toMatch(/<Dialog\b/);
    // The paper fills the viewport, so a "backdrop" click is a click on the
    // newspaper. Closing on it would fire on every stray click in the margin.
    expect(frontPage).toMatch(/closeOnBackdrop=\{false\}/);
    // And the overlay must no longer carry a hand-rolled Escape listener:
    // two handlers for one key is how a stacked dialog collapses both.
    expect(frontPage).not.toMatch(/addEventListener\('keydown'/);
  });

  test('it occupies one slot: a launcher in the results stage, the paper in the overlay', () => {
    // CLAUDE.md V-D — a new always-visible panel is a review defect. The
    // results stage keeps only the one-line trigger.
    expect(frontPage).toMatch(/Slot: OverlayHost/);
    expect(frontPage).toMatch(/if \(!open\) \{/);
  });
});

/* ── Render: the sections the debrief promises, from real payloads only ───── */

const EVENTS = {
  terminal_value: -56160770.27,
  equity_value: 5958741.55,
  net_debt: -62119511.82,
  price_per_share: 1.0,
  regenerative_multiple: 1.03,
  profile: 'fragile_giant',
  profile_title: 'The Fragile Giant',
  group_reputation: 47.29,
  just_transition_passed: true,
  equity_wiped_out: true,
  total_revenue: 30117745.55,
  total_opex: 46904768.52,
  terminal_ebitda: -16964099.33,
  final_treasury: -200044427.86,   // = CLOSING: what round 10 produced (the ledger's last close)
  exit_multiple: 6.0,
  shares_outstanding: 100000000,
  competitor_ebitda: 34384275.78,
  relative_market_advantage: -0.4882,
  competitor_warning: 'Market competitor EBITDA ($34,384,276) exceeds yours. Relative advantage: -0.49x',
  carbon_tonnage_group: 708.3054438683,
  carbon_cost: 177076.36,
  workforce_readiness: 40.0,
  avg_social_license: 0.0,
  synergy_score: 62.08,
  crisis_count_lifetime: 1,
  greenwashing_risk_active: true,
  mr_breakdown: {
    base: 1.0, resilience_bonus: 0.2, wellbeing_bonus: 0.05,
    instability_discount: -0.4, synergy_bonus: 0, max_achievable_mr: 1.93,
  },
  ceo_diary: {
    entry: 'Full divestiture. Everything must go. Maximum cash extraction.',
    mood: 'distressed',
    round_label: 'Grand Finale',
    round_number: 10,
  },
  decision_regret: {
    your_choice: 'option_b',
    alternatives: {
      option_a: { treasury_delta: 15200594.15, reputation_delta: 26.0 },
      option_c: { treasury_delta: 15200594.15, reputation_delta: 26.0 },
    },
  },
};

const PEERS = [
  { rank: 1, name: 'Team Alpha', treasury: 110641651.8, reputation: 37.29, co2: 865, isYou: false },
  { rank: 2, name: 'Team Bravo', treasury: 103709451.07, reputation: 49.29, co2: 246, isYou: false },
  { rank: 3, name: 'Your Team', treasury: -188544427.86, reputation: 37.29, co2: 488, isYou: true },
];

describe('rendered edition', () => {
  let FrontPageReveal;
  beforeAll(() => {
    FrontPageReveal = require('../app/components/FrontPageReveal').default;
  });
  beforeEach(() => {
    global.fetch = jest.fn(() => Promise.resolve({ ok: false, json: () => Promise.resolve(null) }));
  });
  afterEach(() => { delete global.fetch; });

  const open = async () => {
    await act(async () => {
      render(React.createElement(FrontPageReveal, {
        sessionId: 'S1', data: EVENTS, cohortName: 'MBA1', history: REAL, peers: PEERS,
      }));
    });
    // The results stage shows only the launcher.
    expect(screen.queryByText(/Inside the numbers/i)).toBeNull();
    await act(async () => { fireEvent.click(screen.getByText(/Read the full edition/i)); });
  };

  test('every promised desk is present', async () => {
    await open();
    for (const heading of [
      /By the numbers/i,
      /The terminal year/i,
      /The five-year decision ledger/i,
      /Inside the numbers: three key insights/i,
      /Market desk: how rivals fared/i,
      /From the chief executive/i,
      /How the multiple was built/i,
      /Sustainability desk/i,
      /The road not taken/i,
    ]) {
      expect(screen.getByText(heading)).toBeInTheDocument();
    }
  });

  test('competitor figures are the engine\'s, and rivals are named from the leaderboard', async () => {
    await open();
    expect(screen.getByText('Team Alpha')).toBeInTheDocument();
    expect(screen.getByText(/Your Team/)).toBeInTheDocument();
    expect(screen.getByText('$34.4M')).toBeInTheDocument();   // competitor EBITDA
    expect(screen.getByText('−0.49×')).toBeInTheDocument();   // relative advantage
  });

  test('the CEO paragraph is the diary entry verbatim — not paraphrased', async () => {
    await open();
    expect(screen.getByText(new RegExp(EVENTS.ceo_diary.entry.slice(0, 40)))).toBeInTheDocument();
    expect(screen.getByText(/tone recorded as distressed/i)).toBeInTheDocument();
  });

  test('the insights carry real money, never $0.0M for both', async () => {
    await open();
    // Each figure appears twice — once in the ledger row, once in the insight
    // that cites it — which is itself the proof the two agree.
    expect(screen.getAllByText(/\+\$4\.8M/).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText(/−\$145\.9M/).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/Best round — Round 2/)).toBeInTheDocument();
    expect(screen.getByText(/Costliest round — Round 9/)).toBeInTheDocument();
    // Round 10 is in the ledger with what it produced (closing − entering R10).
    expect(screen.getByText('−$11.5M')).toBeInTheDocument();
    expect(screen.queryByText(/\$0\.0M/)).toBeNull();
  });

  test('a negative figure keeps its sign outside the currency', async () => {
    await open();
    // Regression: the numbers box printed "$-62.1M" for net debt.
    expect(screen.getByText('−$62.1M')).toBeInTheDocument();
    expect(screen.queryByText(/\$-/)).toBeNull();
  });

  test('a run with nothing to say prints no insights section', async () => {
    global.fetch = jest.fn(() => Promise.resolve({ ok: false, json: () => Promise.resolve(null) }));
    await act(async () => {
      render(React.createElement(FrontPageReveal, {
        sessionId: 'S2', data: EVENTS, cohortName: '', history: [], peers: [],
      }));
    });
    await act(async () => { fireEvent.click(screen.getByText(/Read the full edition/i)); });
    expect(screen.queryByText(/Inside the numbers/i)).toBeNull();
    expect(screen.queryByText(/five-year decision ledger/i)).toBeNull();
    // …but the desks that DO have data still print.
    expect(screen.getByText(/From the chief executive/i)).toBeInTheDocument();
  });

  test('missing measures print as an em dash, never as an estimate', async () => {
    global.fetch = jest.fn(() => Promise.resolve({ ok: false, json: () => Promise.resolve(null) }));
    const sparse = { regenerative_multiple: 1.2, terminal_value: 1_000_000 };
    await act(async () => {
      render(React.createElement(FrontPageReveal, {
        sessionId: 'S3', data: sparse, history: [], peers: [],
      }));
    });
    await act(async () => { fireEvent.click(screen.getByText(/Read the full edition/i)); });
    expect(screen.queryByText(/From the chief executive/i)).toBeNull();
    expect(screen.queryByText(/Market desk/i)).toBeNull();
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });
});
