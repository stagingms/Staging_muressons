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
const BASELINE_EBITDA = 19_200_000; // Sum of 4 BU EBITDA margins at seed
const DAYS_PER_ROUND = 20;          // Interpolated daily ticks per round

// ── MACRO ENGINE ─────────────────────────────────────────────

/**
 * Calculate the deterministic stock price for a given round state.
 *
 * @param {Object} roundState
 * @param {number} roundState.ebitda           — Current round EBITDA (post OPEX/CAPEX)
 * @param {number} roundState.synergy_multiplier — Group synergy multiplier (default 1.0)
 * @param {number} roundState.natural_capital_debt — Average NCD across BUs
 * @param {number} roundState.group_reputation — 0-100 reputation score
 * @returns {number} Stock price rounded to 2 decimal places
 */
export function calculateRoundStockPrice(roundState) {
  const {
    ebitda = BASELINE_EBITDA,
    synergy_multiplier = 1.0,
    natural_capital_debt = 0,
    group_reputation = 50,
  } = roundState || {};

  // ESG Sentiment Multiplier
  // sentiment = 1.0 + (synergy - 1.0) - (NCD / 100) - ((100 - rep) / 200)
  const synergyBoost = synergy_multiplier - 1.0;
  const ncdPenalty = natural_capital_debt / 100;
  const repPenalty = (100 - group_reputation) / 200;
  const sentiment = Math.max(0.1, 1.0 + synergyBoost - ncdPenalty - repPenalty);

  // Stock Price = IPO * (EBITDA / Baseline) * Sentiment
  const ebitdaRatio = Math.max(0, ebitda) / BASELINE_EBITDA;
  const price = IPO_PRICE * ebitdaRatio * sentiment;

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
    const roundState = {
      ebitda: h.ebitda || BASELINE_EBITDA,
      synergy_multiplier: h.synergy_multiplier || globalState?.synergy_multiplier || 1.0,
      natural_capital_debt: avgNCD,
      group_reputation: h.reputation || globalState?.group_reputation || 50,
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
        label: d === dailyData.length - 1 ? `${2027 + roundNum - 1}` : '',
      });
    }

    prevPrice = currentPrice;
  }

  return allPoints;
}

// Re-export constants for consumers
export { IPO_PRICE, BASELINE_EBITDA, DAYS_PER_ROUND };
