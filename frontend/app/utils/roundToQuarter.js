/**
 * roundToQuarter.js
 *
 * Maps a simulation round number to a fiscal year + half-year label.
 * Each round = 6 months (1 semester / 2 quarters).
 *
 * Mapping:
 *   Round 1  → baseYear H1
 *   Round 2  → baseYear H2
 *   Round 3  → baseYear+1 H1
 *   Round 4  → baseYear+1 H2
 *   Round 5  → baseYear+2 H1
 *   ...
 *   Round 10 → baseYear+4 H2
 *
 * @param {number} round     — Simulation round (1-based)
 * @param {number} [baseYear] — Starting calendar year (defaults to current year)
 * @returns {{ year: number, quarter: number, label: string, shortLabel: string }}
 */
export function roundToQuarter(round, baseYear = new Date().getFullYear()) {
  const r = Math.max(1, Math.round(round));
  const year = baseYear + Math.floor((r - 1) / 2);
  const half = ((r - 1) % 2) + 1;
  return {
    year,
    quarter: half,
    label: `${year} H${half}`,
    shortLabel: `H${half}'${String(year).slice(2)}`,
  };
}

/**
 * Returns a compact range label for a span of rounds, e.g. "2026 H1–H2"
 * or "2026–2027" if they span multiple years.
 */
export function roundRangeLabel(minRound, maxRound, baseYear = new Date().getFullYear()) {
  const start = roundToQuarter(minRound, baseYear);
  const end = roundToQuarter(maxRound, baseYear);
  if (start.year === end.year) {
    return `${start.year} H${start.quarter}–H${end.quarter}`;
  }
  return `${start.year}–${end.year}`;
}
