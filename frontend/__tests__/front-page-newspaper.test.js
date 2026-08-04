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

/** The real dashboard row shape, with the real numbers from a played run. */
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

describe('keyInsights — reads the real history shape', () => {
  test('the treasury comes from global_state, not the row top level', () => {
    // THE bug, isolated: the row has no `treasury` and no top-level
    // `corporate_treasury`.
    expect(REAL[0].treasury).toBeUndefined();
    expect(REAL[0].corporate_treasury).toBeUndefined();
    expect(rowTreasury(REAL[0])).toBe(49500000.0);
  });

  test('deltas are real, not a column of zeroes', () => {
    const led = roundLedger(REAL);
    const deltas = led.filter((r) => Number.isFinite(r.delta)).map((r) => r.delta);
    expect(deltas).toHaveLength(9);
    expect(deltas.every((d) => d === 0)).toBe(false);
    expect(led[2].delta).toBeCloseTo(44515682.11 - 39720216.88, 2);
  });

  test('round 1 carries no delta rather than a fabricated zero', () => {
    // Its opening balance is not in `history` (row 1 is already a CLOSE), and
    // the engine can inherit a starting treasury from a parent track — so any
    // baseline here would be a guess.
    const led = roundLedger(REAL);
    expect(led[0].round).toBe(1);
    expect(led[0].delta).toBeNull();
    expect(led[0].treasury).toBe(49500000.0);
  });

  test('best and worst are different rounds with different, real figures', () => {
    const ki = deriveKeyInsights(REAL);
    expect(ki).not.toBeNull();
    expect(ki.best.round).not.toBe(ki.worst.round);
    expect(ki.best.delta).toBeGreaterThan(0);
    expect(ki.worst.delta).toBeLessThan(0);
    // Round 3 is the only round that gained; round 10 is the collapse.
    expect(ki.best.round).toBe(3);
    expect(ki.worst.round).toBe(10);
    expect(fmtDeltaM(ki.best.delta)).toBe('+$4.8M');
    expect(fmtDeltaM(ki.worst.delta)).toBe('−$145.9M');
  });

  test('choices are labelled from choice_selected', () => {
    expect(choiceLabel(REAL[2])).toBe('Option B');
    expect(choiceLabel({ choice_selected: null })).toBeNull();
  });

  test('the reputation swing is a real move, with its from/to', () => {
    const ki = deriveKeyInsights(REAL);
    expect(ki.swing.round).toBe(5);          // 51.29 -> 22.95, the largest jump
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
    expect(gameOverCode).toMatch(/deriveKeyInsights\(history\)/);
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
    expect(frontPage).toMatch(/aria-modal="true"/);
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
  final_treasury: 114251564.8,
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
    expect(screen.getByText(/Best round — Round 3/)).toBeInTheDocument();
    expect(screen.getByText(/Costliest round — Round 10/)).toBeInTheDocument();
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
