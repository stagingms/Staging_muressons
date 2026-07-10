/**
 * W-B determinism spot-check — rivalIntel derivations.
 * Doctrine: same inputs ⇒ same outputs (shared-dice determinism), correct
 * tone bands, even-round-only rating reviews, correct direction arrows.
 */
import {
  deriveRivalRelease,
  deriveRatingLetter,
  ratingGrade,
  rivalBenchmarkEV,
} from '../app/components/rivalIntel';

const mkRound = (round, { playerEbitda = 20_000_000, rivalEbitda = 19_200_000, rep = 50, ci = 40, ncd = 10, wacc = 0.06 } = {}) => ({
  round_number: round,
  business_units: [
    { revenue_base: playerEbitda + 30_000_000, opex_base: 30_000_000, carbon_intensity: ci, natural_capital_debt: ncd },
  ],
  global_state: {
    competitor_ebitda: rivalEbitda,
    historical_ebitda: playerEbitda,
    group_reputation: rep,
    cost_of_capital: wacc,
  },
});

describe('deriveRivalRelease (W2)', () => {
  test('is deterministic: same history ⇒ deep-equal output', () => {
    const history = [mkRound(1), mkRound(2, { playerEbitda: 25_000_000 })];
    expect(deriveRivalRelease(history)).toEqual(deriveRivalRelease(history));
    expect(deriveRivalRelease(history)).toEqual(deriveRivalRelease(JSON.parse(JSON.stringify(history))));
  });

  test('null before any committed round with competitor data', () => {
    expect(deriveRivalRelease([])).toBeNull();
    expect(deriveRivalRelease(null)).toBeNull();
    expect(deriveRivalRelease([{ round_number: 1, global_state: {} }])).toBeNull();
  });

  test('tone bands follow relative advantage', () => {
    const at = (player, rival) => deriveRivalRelease([mkRound(3, { playerEbitda: player, rivalEbitda: rival })]).tone;
    expect(at(23_000_000, 19_200_000)).toBe('defensive');   // 1.20×
    expect(at(20_000_000, 19_200_000)).toBe('neutral');     // 1.04×
    expect(at(18_000_000, 19_200_000)).toBe('confident');   // 0.94×
    expect(at(15_000_000, 19_200_000)).toBe('aggressive');  // 0.78×
  });

  test('uses the LATEST committed round and reports real figures', () => {
    const r = deriveRivalRelease([mkRound(1), mkRound(4, { playerEbitda: 30_000_000, rivalEbitda: 20_000_000 })]);
    expect(r.round).toBe(4);
    expect(r.advantage).toBe(1.5);
    expect(r.body).toContain('$20.0M');
    expect(r.body).toContain('$30.0M');
  });
});

describe('deriveRatingLetter (W6)', () => {
  test('is deterministic', () => {
    const history = [mkRound(1), mkRound(2), mkRound(3), mkRound(4, { rep: 70 })];
    expect(deriveRatingLetter(history)).toEqual(deriveRatingLetter(history));
  });

  test('null before the first even committed round', () => {
    expect(deriveRatingLetter([mkRound(1)])).toBeNull();
    expect(deriveRatingLetter([])).toBeNull();
  });

  test('reviews on even rounds only, latest even round wins', () => {
    const letter = deriveRatingLetter([mkRound(1), mkRound(2), mkRound(3)]);
    expect(letter.round).toBe(2);
    const letter2 = deriveRatingLetter([mkRound(1), mkRound(2), mkRound(3), mkRound(4)]);
    expect(letter2.round).toBe(4);
  });

  test('direction: initiated → upgrade → downgrade', () => {
    const strong = { rep: 90, ci: 10, ncd: 0, wacc: 0.05 };
    const weak = { rep: 25, ci: 80, ncd: 60, wacc: 0.12 };
    expect(deriveRatingLetter([mkRound(2)]).direction).toBe('initiated');
    expect(deriveRatingLetter([mkRound(2), mkRound(4, strong)]).direction).toBe('upgrade');
    expect(deriveRatingLetter([mkRound(2, strong), mkRound(4, weak)]).direction).toBe('downgrade');
    expect(deriveRatingLetter([mkRound(2), mkRound(4)]).direction).toBe('affirmed');
  });

  test('grade bands are monotonic in inputs', () => {
    const g = (o) => ratingGrade(mkRound(2, o)).letter;
    expect(g({ rep: 95, ci: 5, ncd: 0, wacc: 0.05 })).toBe('AAA');
    expect(g({ rep: 20, ci: 90, ncd: 80, wacc: 0.14 })).toBe('CCC');
  });

  test('rationale names strongest and weakest factors', () => {
    const letter = deriveRatingLetter([mkRound(2, { rep: 90, ci: 85 })]);
    expect(letter.rationale).toContain('stakeholder reputation');
    expect(letter.rationale).toContain('carbon intensity trajectory');
  });
});

describe('rivalBenchmarkEV (W2c)', () => {
  test('deterministic compounding from baseline', () => {
    expect(rivalBenchmarkEV(1)).toBeCloseTo(19_200_000 * 17, 0);
    expect(rivalBenchmarkEV(5)).toBeCloseTo(19_200_000 * Math.pow(1.03, 4) * 17, 0);
    expect(rivalBenchmarkEV(5)).toBe(rivalBenchmarkEV(5));
  });
});
