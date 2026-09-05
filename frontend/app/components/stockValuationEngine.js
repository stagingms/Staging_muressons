import { roundToQuarter } from '../utils/roundToQuarter';

/**
 * stockValuationEngine.js
 *
 * Two-tiered stock valuation system for the Muressons simulation.
 *
 * MACRO ENGINE — calculateRoundStockPrice(roundState)
 *   Derives a deterministic "true" stock price per round.
 *
 * MICRO ENGINE — generateStockTickerData(prevSP, currSP, isShockEvent)
 *   Interpolates 20 stochastic daily data points between two round anchors.
 */

// ── Constants ────────────────────────────────────────────────
const IPO_PRICE = 50.00;            // Round 0 stock price
const SHARES_OUTSTANDING = 6_500_000;    // F-20: matches simulation_config.json terminal_valuation.shares_outstanding (baseline EV $19.2M×17 ÷ $50 IPO)
const BASELINE_EBITDA = 19_200_000; // Sum of 4 BU EBITDA margins at seed
const DAYS_PER_ROUND = 40;          // Interpolated daily ticks per 6-month round
const LONG_RUN_GROWTH = 0.02;       // 2% terminal growth for Gordon Growth Model
const EXIT_FLOOR = 6.0;             // Minimum exit multiple (distressed)
const EXIT_CEILING = 18.0;          // Maximum exit multiple (very low WACC)

// ── STRAT-010: Gordon Growth Exit Multiple ───────────────────
/**
 * Dynamic exit multiple = (1+g) / (WACC−g)
 * Links WACC to valuation — bad ESG governance = higher WACC = lower multiple.
 */
function calcExitMultiple(wacc = 0.08) {
  if (wacc <= LONG_RUN_GROWTH) return EXIT_CEILING;
  const m = (1 + LONG_RUN_GROWTH) / (wacc - LONG_RUN_GROWTH);
  return Math.max(EXIT_FLOOR, Math.min(EXIT_CEILING, m));
}

/**
 * Calculate the deterministic stock price for a given round state.
 *
 * STRAT-010: Uses dynamic exit multiple derived from WACC (Gordon Growth Model)
 * instead of a fixed multiple. Teams with poor ESG governance accumulate higher
 * WACC → lower exit multiple → lower stock price. Feedback loop is now real.
 *
 * @param {Object} roundState
 * @param {number} roundState.ebitda           — Current round EBITDA (post OPEX/CAPEX)
 * @param {number} roundState.synergy_multiplier — Group synergy multiplier (default 1.0)
 * @param {number} roundState.natural_capital_debt — Average NCD across BUs
 * @param {number} roundState.group_reputation — 0-100 reputation score
 * @param {number} [roundState.cost_of_capital=0.08] — WACC (drives exit multiple)
 * @returns {number} Stock price rounded to 2 decimal places
 */
export function calculateRoundStockPrice(roundState) {
  const {
    ebitda = BASELINE_EBITDA,
    synergy_multiplier = 1.0,
    natural_capital_debt = 0,
    group_reputation = 50,
    cost_of_capital = 0.08,
    exit_multiple = null,   // F-17: the server's valuation_preview.exit_multiple when available
  } = roundState || {};

  // STRAT-010: Dynamic exit multiple from WACC. F-17: prefer the multiple the
  // backend computed for this round (same Gordon formula, same clamps) so the
  // ticker, the briefing and the finale agree; fall back to the local formula.
  const exitMultiple = Number.isFinite(exit_multiple) && exit_multiple > 0
    ? exit_multiple
    : calcExitMultiple(cost_of_capital);
  // Baseline multiple at 8% WACC: (1.02)/(0.08−0.02) = 17× → seed at IPO_PRICE
  const baselineMultiple = calcExitMultiple(0.08);  // ~17.0

  // ESG Sentiment Multiplier
  const synergyBoost = synergy_multiplier - 1.0;
  // F-17: natural_capital_debt is an INDEX (seed 0; ten rounds of neglect ≈ 2,000;
  // hard cap 5,000). Dividing by 100 made NCD 50 a −50% sentiment hit; scale to the
  // real range and cap the penalty so the price never collapses on NCD alone.
  const ncdPenalty = Math.min(0.6, Math.max(0, natural_capital_debt) / 4000);
  const repPenalty = (100 - group_reputation) / 200;
  const sentiment = Math.max(0.1, 1.0 + synergyBoost - ncdPenalty - repPenalty);

  // Stock Price = IPO × (EBITDA / Baseline) × Sentiment × (ExitMultiple / BaselineMultiple)
  // The exit-multiple ratio means WACC degradation now deflates the price
  const ebitdaRatio = Math.max(0, ebitda) / BASELINE_EBITDA;
  const multipleRatio = exitMultiple / baselineMultiple;
  const price = IPO_PRICE * ebitdaRatio * sentiment * multipleRatio;

  return Math.max(1.0, Math.round(price * 100) / 100);
}

// ── MICRO ENGINE ─────────────────────────────────────────────

/**
 * Seeded pseudo-random generator (Mulberry32) for deterministic charts.
 * @param {number} seed
 * @returns {function(): number} Returns value in [0, 1)
 */
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Generate interpolated daily stock data between two round anchor prices.
 *
 * @param {number} prevSP          — Previous round's stock price
 * @param {number} currSP          — Current round's calculated stock price (hard anchor)
 * @param {boolean} isShockEvent   — If true, apply a "gap down" Black Swan shock
 * @param {number} [roundIndex=0]  — Round number for seed determinism
 * @returns {Array<{day: number, price: number}>} 20 data points
 */
export function generateStockTickerData(prevSP, currSP, isShockEvent = false, roundIndex = 0) {
  const rng = mulberry32(roundIndex * 1337 + Math.round(prevSP * 100));
  const points = [];
  const n = DAYS_PER_ROUND;

  // Determine general drift direction
  const totalDrift = currSP - prevSP;

  let price = prevSP;

  for (let i = 0; i < n; i++) {
    const t = (i + 1) / n; // progress 0→1

    if (isShockEvent && i < 2) {
      // ── Black Swan: sharp gap down on first 2 days ──
      const gapPct = 0.08 + rng() * 0.04; // 8-12% drop
      price = price * (1 - gapPct);
    } else {
      // ── Stochastic random walk trending toward currSP ──
      // Daily noise: ±1% to ±3%
      const volatility = 0.01 + rng() * 0.02;
      const noise = (rng() - 0.5) * 2 * volatility * price;

      // Mean-reversion pull toward the target (stronger as t → 1)
      const target = prevSP + totalDrift * t;
      const pull = (target - price) * (0.15 + 0.35 * t);

      price = price + noise + pull;
    }

    // Ensure price doesn't go below $1
    price = Math.max(1.0, price);

    // Hard anchor: final data point MUST equal currSP exactly
    if (i === n - 1) {
      price = currSP;
    }

    points.push({
      day: i + 1,
      price: Math.round(price * 100) / 100,
    });
  }

  return points;
}

/**
 * Build the complete stock ticker dataset from round history.
 *
 * @param {Array} historyData — Array of { round, ebitda, reputation, ... }
 * @param {Object} globalState — Current global state
 * @param {Array} businessUnits — Current BU list (for avg NCD calculation)
 * @param {number} currentRound — Current round number
 * @param {Object} [events] — Current round events (for shock detection)
 * @returns {Array<{day: number, roundDay: number, round: number, price: number, label: string}>}
 */
export function buildFullStockData(historyData, globalState, businessUnits, currentRound, events) {
  const allPoints = [];
  let prevPrice = IPO_PRICE;

  // IPO anchor point (Round 0)
  allPoints.push({
    day: 0,
    roundDay: 0,
    round: 0,
    price: IPO_PRICE,
    label: 'IPO',
  });

  // Calculate average NCD from business units
  const avgNCD = (businessUnits || []).length > 0
    ? (businessUnits || []).reduce((s, bu) => s + (bu.natural_capital_debt || 0), 0) / businessUnits.length
    : 0;

  // Process each round in history
  const rounds = [...(historyData || [])];

  for (let i = 0; i < rounds.length; i++) {
    const h = rounds[i];
    const roundNum = h.round || (i + 1);

    // Only show data for committed rounds (before the current round).
    // During round 1, nothing is committed yet, so stay flat at IPO.
    if (roundNum >= currentRound) continue;

    // Build round state for macro engine
    // NEW-10: Guard against zero/null EBITDA in history — a raw 0 causes stock to crash to $1.
    // Use a minimum floor of 30% baseline to keep the chart realistic after resets.
    const roundEbitda = (h.ebitda != null && h.ebitda > 0)
      ? h.ebitda
      : BASELINE_EBITDA;
    const roundState = {
      ebitda: Math.max(BASELINE_EBITDA * 0.3, roundEbitda),
      synergy_multiplier: h.synergy_multiplier || globalState?.synergy_multiplier || 1.0,
      natural_capital_debt: avgNCD,
      group_reputation: h.reputation ?? globalState?.group_reputation ?? 50,
      // STRAT-010: Pass WACC so exit multiple is dynamic per round
      cost_of_capital: h.cost_of_capital || globalState?.cost_of_capital || 0.08,
    };

    const currentPrice = calculateRoundStockPrice(roundState);

    // Detect shock events
    const isShock = roundNum === currentRound
      ? !!(events?.strike_occurred || events?.talent_penalty_applied > 1.1 || events?.cfo_override_used)
      : false;

    // Generate micro-interpolated daily data
    const dailyData = generateStockTickerData(prevPrice, currentPrice, isShock, roundNum);

    for (let d = 0; d < dailyData.length; d++) {
      allPoints.push({
        day: allPoints.length,
        roundDay: d + 1,
        round: roundNum,
        price: dailyData[d].price,
        label: d === dailyData.length - 1 ? roundToQuarter(roundNum).label : '',
      });
    }

    prevPrice = currentPrice;
  }

  return allPoints;
}

// Re-export constants for consumers
export { IPO_PRICE, BASELINE_EBITDA, DAYS_PER_ROUND, SHARES_OUTSTANDING };
