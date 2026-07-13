import { stripPedagogy } from '../app/briefings/stripPedagogy';
import { STANDARD_BRIEFINGS } from '../app/briefings/data/standard';
import { HEALTHCARE_BRIEFINGS } from '../app/briefings/data/healthcare';
import { SDG_BRIEFINGS } from '../app/briefings/data/sdg';

describe('player briefing pedagogy strip', () => {
  test('removes tagged academic spans and leaves clean prose', () => {
    const html = 'Complete the <strong>Grid</strong><span class="ped-academic"> (Mendelow’s Matrix)</span> to map.';
    expect(stripPedagogy(html)).toBe('Complete the <strong>Grid</strong> to map.');
  });

  test('standard R2 is tagged and strips the CSRD explanation', () => {
    const r2 = STANDARD_BRIEFINGS[2].narrative.join(' ');
    expect(r2).toContain('ped-academic');
    const stripped = STANDARD_BRIEFINGS[2].narrative.map(stripPedagogy).join(' ');
    expect(stripped).not.toContain('ped-academic');
    expect(stripped).not.toContain('Corporate Sustainability Reporting Directive');
  });

  test('no academic markers or double spaces survive in any standard round', () => {
    for (const r of Object.keys(STANDARD_BRIEFINGS)) {
      const stripped = (STANDARD_BRIEFINGS[r].narrative || []).map(stripPedagogy).join(' ');
      expect(stripped).not.toContain('ped-academic');
      expect(stripped).not.toMatch(/\s{2,}/);
    }
  });

  // Healthcare & SDG have no textbook asides — strip must be a byte-for-byte no-op
  // (their narratives are untouched, so nothing breaks).
  test.each([
    ['healthcare', HEALTHCARE_BRIEFINGS],
    ['sdg', SDG_BRIEFINGS],
  ])('%s narratives are untagged and pass through strip unchanged', (_name, dict) => {
    for (const r of Object.keys(dict)) {
      for (const para of (dict[r].narrative || [])) {
        expect(para).not.toContain('ped-academic');
        expect(stripPedagogy(para)).toBe(para);
      }
    }
  });
});
