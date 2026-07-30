/**
 * "Show Cohort Trends" must never rewrite the player's own history.
 *
 * The bug, as reported from a live end-of-game screen: a player finished at
 * −$375M EBITDA with a reputation that touched 0; flipping the cohort-trends
 * toggle redrew their SOLID lines as a smooth +$26M / steady-50 series. Cause:
 * /peer-trend-history returns each round's cohort aggregates under the SAME
 * keys the player's chart rows use (avgCI / tco2e / ebitda / rep), and the
 * merge spread the whole round object into the row — so the toggle replaced
 * the player's data with the cohort average. Worst kind of bug for a teaching
 * tool: it lies about what the student actually did, and only while they are
 * comparing themselves to others.
 */
import { mergePeerTrendRows }
  from '../app/components/SustainabilityBalancedScorecard';

const COLORS = ['#fb923c', '#c084fc', '#f472b6'];

// The player's own rows — shaped like the live chartDataWithCum, with the
// screenshot's character: collapsing EBITDA, a reputation crash to 0.
const PLAYER_ROWS = [
  { round: 2, label: '2026 H2', avgCI: 45.1, tco2e: 2400, ebitda: 8_000_000,   rep: 46, cumulativeCarbon: 2400 },
  { round: 3, label: '2027 H1', avgCI: 43.9, tco2e: 2100, ebitda: -1_000_000,  rep: 0,  cumulativeCarbon: 4500 },
  { round: 4, label: '2027 H2', avgCI: 26.0, tco2e: 1800, ebitda: -375_000_000, rep: 53, cumulativeCarbon: 6300 },
];

// What the endpoint actually sends: aggregates in COLLIDING key names, plus
// the per-peer detail. Values chosen to be unmistakably different.
const PEER_ROUNDS = [
  { round: 2, avgCI: 44.0, tco2e: 150, ebitda: 20_000_000, rep: 50, peerStockPrice: 48,
    peers: [{ id: 'ai_0', name: 'Steady Eddie', ci: 44, tco2e: 150, ebitda: 20_000_000, rep: 50, stock: 48 }] },
  { round: 3, avgCI: 42.0, tco2e: 140, ebitda: 22_000_000, rep: 52, peerStockPrice: 50,
    peers: [{ id: 'ai_0', name: 'Steady Eddie', ci: 42, tco2e: 140, ebitda: 22_000_000, rep: 52, stock: 50 }] },
];

describe('mergePeerTrendRows', () => {
  test('the player series survives the merge byte-for-byte', () => {
    const { rows } = mergePeerTrendRows(PLAYER_ROWS, PEER_ROUNDS, COLORS);
    for (const key of ['avgCI', 'tco2e', 'ebitda', 'rep', 'cumulativeCarbon', 'label']) {
      expect(rows.map(r => r[key])).toEqual(PLAYER_ROWS.map(r => r[key]));
    }
    // The reported symptom, pinned exactly: the −$375M round stays −$375M.
    expect(rows[2].ebitda).toBe(-375_000_000);
    expect(rows[1].rep).toBe(0);
  });

  test('per-peer dashed series are added, namespaced, with running cumulative', () => {
    const { rows, peerIds } = mergePeerTrendRows(PLAYER_ROWS, PEER_ROUNDS, COLORS);
    expect(peerIds).toEqual([{ id: 'ai_0', name: 'Steady Eddie', color: COLORS[0] }]);
    expect(rows[0].peer_ai_0_ebitda).toBe(20_000_000);
    expect(rows[1].peer_ai_0_cum).toBe(290);          // 150 + 140
    expect(rows[2].peer_ai_0_ci).toBeUndefined();     // no peer data for round 4
  });

  test('the aggregate keys never reach the rows at all', () => {
    // peerStockPrice is consumed straight from peerRounds by the stock chart;
    // nothing aggregate belongs in the player's rows, where a future rename
    // could resurrect the collision.
    const { rows } = mergePeerTrendRows(PLAYER_ROWS, PEER_ROUNDS, COLORS);
    for (const r of rows) {
      expect(r.peerStockPrice).toBeUndefined();
      expect(r.peerCount).toBeUndefined();
      expect(r.peers).toBeUndefined();
    }
  });

  test('toggle off (no peer rounds) is an identity', () => {
    const { rows, peerIds } = mergePeerTrendRows(PLAYER_ROWS, [], COLORS);
    expect(rows).toEqual(PLAYER_ROWS);
    expect(peerIds).toEqual([]);
  });
});
