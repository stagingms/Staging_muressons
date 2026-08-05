/**
 * currency-rate.test.js — the conversion factor, and the boundary it must not
 * cross.
 *
 * OWNER DECISION: cohort figures convert using a factor a super admin sets on
 * the session, rather than the symbol changing while the quantity stays put.
 * A rupee cohort used to read "₹11.0M" for an engine value of 11,000,000
 * dollars — the glyph localised, the number not, which is a worse lie than
 * leaving it in dollars.
 *
 * The interesting assertions here are not that multiplication works. They are:
 *   - the rate ships INERT (default 1), so this cannot change a live cohort
 *     until somebody sets it
 *   - a bad rate cannot zero or invert every money figure in the product
 *   - authored teaching copy rounds to one significant figure, and COMPUTED
 *     figures do not — because rounded numbers stop summing, and a team that
 *     checks the arithmetic must find that it ties
 */
const fmt = require('../app/utils/format');

const reset = () => { fmt.setCurrencySymbol('$'); fmt.setCurrencyRate(1); };

describe('the rate ships inert', () => {
  beforeEach(reset);

  test('default is 1, so every existing figure is unchanged', () => {
    expect(fmt.currencyRate()).toBe(1);
    expect(fmt.money(11_000_000)).toBe('$11.0M');
    expect(fmt.moneyM(2_500_000)).toBe('$2.5M');
  });
});

describe('a bad rate cannot take the product down', () => {
  beforeEach(reset);

  test.each([
    ['zero', 0], ['negative', -83], ['NaN', NaN], ['a string', 'eighty-three'],
    ['null', null], ['undefined', undefined], ['Infinity', Infinity],
  ])('%s is refused, and the previous rate stands', (_label, bad) => {
    fmt.setCurrencyRate(83);
    fmt.setCurrencyRate(bad);
    expect(fmt.currencyRate()).toBe(83);
  });

  test('a zero rate would have zeroed every figure in the product', () => {
    // Stated explicitly because this is the failure that would read as an
    // engine bug rather than a config one: every treasury, every allocation,
    // every option cost at $0, with nothing in the logs.
    fmt.setCurrencyRate(0);
    expect(fmt.money(11_000_000)).toBe('$11.0M');
  });
});

describe('computed figures convert at full precision', () => {
  beforeEach(() => { reset(); fmt.setCurrencySymbol('₹'); fmt.setCurrencyRate(83); });

  test('money() scales, and the ladder re-steps with the new magnitude', () => {
    // 11M dollars is 913M rupees — still an M, but nearly a B. The ladder has
    // to be applied AFTER the rate, or a converted figure lands in the wrong
    // unit band.
    expect(fmt.money(11_000_000)).toBe('₹913.0M');
    expect(fmt.money(20_000_000)).toBe('₹1.66B');
  });

  test('moneyM stays pinned to millions, as a comparable column must', () => {
    expect(fmt.moneyM(2_500_000)).toBe('₹207.5M');
  });

  test('the minus glyph survives conversion', () => {
    expect(fmt.money(-2_500_000).startsWith('−')).toBe(true);
  });

  test('"not recorded" is still not zero', () => {
    expect(fmt.money(null)).toBe('—');
    expect(fmt.money(undefined)).toBe('—');
  });
});

describe('authored teaching numbers round to one significant figure', () => {
  beforeEach(() => { reset(); fmt.setCurrencySymbol('₹'); fmt.setCurrencyRate(83); });

  test('the shadow price reads as approximate, not as arithmetic', () => {
    // $40/tonne * 83 = ₹3,320, which is false precision on a number an author
    // chose because it was round.
    expect(fmt.authoredMoney(40, { unit: '/tonne' })).toBe('₹3,000/tonne');
  });

  test('it is aggressive at the low end, and that is the right trade', () => {
    // $2 * 83 = ₹166 -> ₹200. A 20% distortion on a teaching number that is
    // doing its job by reading as approximate. Anyone who needs the exact
    // figure is looking at the wrong number.
    expect(fmt.authoredMoney(2)).toBe('₹200');
  });

  test('zero stays zero rather than becoming a rounded nothing', () => {
    expect(fmt.authoredMoney(0)).toBe('₹0');
  });

  test('at rate 1 it still rounds — the rounding is about AUTHORSHIP, not conversion', () => {
    fmt.setCurrencyRate(1);
    expect(fmt.authoredMoney(40, { unit: '/tonne' })).toBe('₹40/tonne');
    expect(fmt.authoredMoney(4_200_000)).toBe('₹4,000,000');
  });
});

describe('the boundary between authored and computed', () => {
  beforeEach(() => { reset(); fmt.setCurrencySymbol('₹'); fmt.setCurrencyRate(83); });

  test('rounded authored figures do NOT sum, which is why computed ones are not rounded', () => {
    /* Three option costs of $40 each. Authored, they read ₹3,000 apiece.
       Their true total is ₹9,960 and money() reports it honestly. If the
       computed path also rounded, a team adding the column would get ₹9,000
       and conclude the engine had lost ₹960. */
    const each = fmt.authoredMoney(40);
    expect(each).toBe('₹3,000');
    expect(fmt.moneyFull(120)).toBe('₹9,960');
  });

  test('money() and authoredMoney() disagree on the same input, on purpose', () => {
    expect(fmt.moneyFull(40)).toBe('₹3,320');
    expect(fmt.authoredMoney(40)).toBe('₹3,000');
  });
});

describe('the rate is applied in exactly one place', () => {
  const fs = require('fs');
  const path = require('path');
  const src = fs.readFileSync(path.join(__dirname, '..', 'app/utils/format.js'), 'utf8');

  test('format.js is the only module that reads it', () => {
    /* A component that converts on its own reintroduces the three-formatting-
       systems defect the currency pass existed to kill — and this time the
       symptom would be a figure that is 83x too large, in one panel. */
    const walk = (dir, out = []) => {
      for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
        const p = path.join(dir, e.name);
        if (e.isDirectory()) { if (e.name !== 'node_modules') walk(p, out); continue; }
        if (/\.js$/.test(e.name)) out.push(p);
      }
      return out;
    };
    const root = path.join(__dirname, '..', 'app');
    const offenders = walk(root)
      .filter((f) => !/utils[\\/]format\.js$/.test(f))
      .filter((f) => !/contexts[\\/]CurrencyContext\.js$/.test(f))
      .filter((f) => /currencyRate\s*\(/.test(fs.readFileSync(f, 'utf8')))
      .map((f) => path.relative(root, f));
    expect(offenders).toEqual([]);
  });

  test('the engine boundary is documented where it would be crossed', () => {
    // config.py's constants are engine units. Multiplying before the engine
    // silently redefines every tuned ratio in the simulation.
    expect(src).toMatch(/Not in the engine/);
  });
});
