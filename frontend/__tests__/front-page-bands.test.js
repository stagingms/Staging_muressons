/**
 * The Year-5 front page must report the run it describes.
 *
 * Verification requested from a live run: "the front page appears the same
 * irrespective of the final simulation outcome." It is not — five bands exist
 * with distinct copy — but the suspicion was worth pinning, because the band
 * selector has exactly one failure mode that WOULD make it true: `Number(
 * d.terminal_value) || 0` reads a missing/renamed key as 0, and `ev <= 0`
 * forces the 'relic' band unconditionally. One backend rename and every
 * cohort's newspaper reports a collapse. These tests hold the branch matrix
 * and that the five stories genuinely differ.
 *
 * Also pinned: the equity-truth overrides. A run can post a healthy M_R while
 * enterprise value is gone (the reported run: 1.03x but -$3643M EV) — the
 * front page must print the collapse, not the multiple.
 */
import { bandFor, TEMPLATES } from '../app/components/FrontPageReveal';

const RUNS = {
  titan:    { regenerative_multiple: 1.9,  terminal_value: 5_000_000_000, price_per_share: 82, equity_value: 4_000_000_000 },
  safe:     { regenerative_multiple: 1.3,  terminal_value: 800_000_000,  price_per_share: 34, equity_value: 500_000_000 },
  fragile:  { regenerative_multiple: 0.9,  terminal_value: 200_000_000,  price_per_share: 9,  equity_value: 80_000_000 },
  // The reported run: M_R alone would say 'fragile'; EV <= 0 must win.
  relic:    { regenerative_multiple: 1.03, terminal_value: -3_643_300_000, price_per_share: 1, equity_value: -4_650_300_000 },
  // EV positive but owners wiped out — the flattering bands are forbidden.
  insolvent:{ regenerative_multiple: 1.4,  terminal_value: 600_000_000,  price_per_share: -2, equity_value: -50_000_000 },
};

describe('front page band selection', () => {
  test.each(Object.entries(RUNS))('%s outcome selects its own band', (band, d) => {
    expect(bandFor(d.regenerative_multiple, d)).toBe(band);
  });

  test('the backend archetype is honoured when equity allows it', () => {
    expect(bandFor(0.9, { ...RUNS.titan, profile: 'regenerative_titan' })).toBe('titan');
    // ...but never against the equity truth.
    expect(bandFor(1.9, { ...RUNS.relic, profile: 'regenerative_titan' })).toBe('relic');
  });

  test('all five stories are genuinely different', () => {
    const t = { tvM: '500.0', mr: '1.20', price: '10.00', rep: 50, ncdM: '5.0' };
    const headlines = Object.values(TEMPLATES).map(tpl => tpl.headline(t));
    expect(new Set(headlines).size).toBe(headlines.length);
    expect(headlines.join(' ')).toMatch(/Pays Off/);          // a triumph exists
    expect(headlines.join(' ')).toMatch(/Stranded Assets/);   // and a collapse
  });

  test('every band selectable by bandFor has a template', () => {
    for (const band of ['titan', 'safe', 'fragile', 'relic', 'insolvent']) {
      expect(TEMPLATES[band]).toBeDefined();
      expect(typeof TEMPLATES[band].headline).toBe('function');
    }
  });
});
