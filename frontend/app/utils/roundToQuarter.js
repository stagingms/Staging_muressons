/**
 * roundToQuarter.js
 *
 * Maps a simulation round number to a fiscal year + quarter label.
 *
 * Mapping:
 *   Round 1  → baseYear Q1
 *   Round 2  → baseYear Q2
 *   Round 3  → baseYear Q3
 *   Round 4  → baseYear Q4
 *   Round 5  → baseYear+1 Q1
 *   Round 6  → baseYear+1 Q2
 *   ...
 *   Round 10 → baseYear+2 Q2
 *
 * @param {number} round     — Simulation round (1-based)
 * @param {number} [baseYear] — Starting calendar year (defaults to current year)
 * @returns {{ year: number, quarter: number, label: string, shortLabel: string }}
 */
export function roundToQuarter(round, baseYear = new Date().getFullYear()) {
  const r = Math.max(1, Math.round(round));
  const year = baseYear + Math.floor((r - 1) / 4);
  const quarter = ((r - 1) % 4) + 1;
  return {
    year,
    quarter,
    label: `${year} Q${quarter}`,
    shortLabel: `Q${quarter}'${String(year).slice(2)}`,
  };
}

/**
 * Returns a compact range label for a span of rounds, e.g. "2026 Q1–Q4"
 * or "2026–2027" if they span multiple years.
 */
export function roundRangeLabel(minRound, maxRound, baseYear = new Date().getFullYear()) {
  const start = roundToQuarter(minRound, baseYear);
  const end = roundToQuarter(maxRound, baseYear);
  if (start.year === end.year) {
    return `${start.year} Q${start.quarter}–Q${end.quarter}`;
  }
  return `${start.year}–${end.year}`;
}
