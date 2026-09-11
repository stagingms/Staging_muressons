/**
 * Strategic-pillar option descriptions.
 *
 * Two defects this pins down, both of which produced the same user-visible
 * symptom (hovering an option told you nothing):
 *
 *  1. KEY MISMATCH. detailedDescriptions keys pillar copy positionally
 *     (option_1, option_2, option_3) while the engine's option keys are
 *     semantic (renewable_ppa, blockchain_trace, …). A direct
 *     detailedDescs[optKey] lookup missed for 100% of options — measured at
 *     150/150 before the fix. The resolver must fall back to the positional
 *     key for the option's index.
 *
 *  2. CLIPPING. The menu and hover card were absolutely positioned inside a
 *     scrolling ancestor (.content overflow-y:auto, .panel overflow:hidden),
 *     so the card rendered but was clipped out of view. Both layers must be
 *     portalled to <body>; the CSS must therefore NOT re-introduce
 *     position/left/top on .menu or .tooltip.
 *
 *  3. DOUBLE TOOLTIP (Sept 2026, seen on production with the Classroom-50
 *     cohort). Each option row also carried the description in a native
 *     `title` attribute, meant as a touch/no-hover fallback. On a desktop
 *     browser the title box appeared after ~1 s ON TOP of the formatted hover
 *     card, so every option showed its description twice, one box overlapping
 *     the other. The option rows must carry no `title`; the formatted card is
 *     the only hover surface, and the description appears in the DOM exactly
 *     once while an option is hovered.
 */
const fs = require('fs');
const path = require('path');
const React = require('react');
const { render, fireEvent, act } = require('@testing-library/react');
const PillarSelectDropdown = require('../app/components/PillarSelectDropdown').default;

const APP = path.join(__dirname, '..', 'app');
const component = fs.readFileSync(path.join(APP, 'components/PillarSelectDropdown.js'), 'utf8');
const css = fs.readFileSync(path.join(APP, 'components/PillarSelectDropdown.module.css'), 'utf8');
const descSrc = fs.readFileSync(path.join(APP, 'utils/detailedDescriptions.js'), 'utf8');

/** Pull the `pillars` object out of the descriptions module by brace matching. */
function pillarDescriptions() {
  const i = descSrc.indexOf('"pillars"');
  const start = descSrc.indexOf('{', i);
  let depth = 0;
  let j = start;
  for (; j < descSrc.length; j += 1) {
    if (descSrc[j] === '{') depth += 1;
    else if (descSrc[j] === '}') {
      depth -= 1;
      if (depth === 0) break;
    }
  }
  return JSON.parse(descSrc.slice(start, j + 1));
}

/** Mirror of the component's describe() resolution order. */
function resolve(areaDescs, optionKeys, key, shortDesc) {
  const idx = optionKeys.indexOf(key);
  return (
    areaDescs[key] ||
    (idx >= 0 ? areaDescs[`option_${idx + 1}`] : undefined) ||
    shortDesc ||
    null
  );
}

describe('pillar option descriptions', () => {
  test('resolver falls back from semantic key to positional key', () => {
    const areaDescs = { option_1: 'first', option_2: 'second' };
    const keys = ['renewable_ppa', 'fossil_status_quo'];
    expect(resolve(areaDescs, keys, 'renewable_ppa')).toBe('first');
    expect(resolve(areaDescs, keys, 'fossil_status_quo')).toBe('second');
  });

  test('semantic key wins over positional when both exist', () => {
    const areaDescs = { renewable_ppa: 'specific', option_1: 'positional' };
    expect(resolve(areaDescs, ['renewable_ppa'], 'renewable_ppa')).toBe('specific');
  });

  test('falls back to the short engine description, else null', () => {
    expect(resolve({}, ['x'], 'x', 'short copy')).toBe('short copy');
    expect(resolve({}, ['x'], 'x')).toBeNull();
  });

  test('descriptions file still uses positional keys (the mismatch is real)', () => {
    const pillars = pillarDescriptions();
    const r1 = pillars['1'] || {};
    const anyArea = Object.values(r1)[0] || {};
    const keys = Object.keys(anyArea);
    expect(keys.length).toBeGreaterThan(0);
    // If this ever flips to semantic keys the fallback is harmless, but the
    // assumption behind the resolver should be re-read rather than assumed.
    expect(keys.some((k) => /^option_\d+$/.test(k))).toBe(true);
  });

  test('component resolves descriptions and portals both layers', () => {
    expect(component).toContain('option_${idx + 1}');           // positional fallback
    expect(component).toContain('createPortal');                 // actually used now
    expect(component).toContain('document.body');                // escapes the clip
    // No native title on the option rows — it drew a second, overlapping
    // tooltip on top of the formatted card (defect 3).
    expect(component).not.toMatch(/title=\{describe\(/);
    expect(component).not.toMatch(/role="option"[\s\S]{0,400}?\btitle=/);
  });

  describe('rendered: one hover surface per option (defect 3)', () => {
    const OPTIONS = {
      renewable_ppa: {
        title: 'Renewable PPA', cost: 2000000, description: 'short engine copy',
        impacts: { revenue_delta: 100000, carbon: -8, reputation: 3 },
      },
      fossil_status_quo: { title: 'Fossil Status Quo', cost: 0, description: 'stay put', impacts: {} },
    };
    const DESCS = { option_1: 'Sign a long-term renewable power purchase agreement.' };
    const fmt = (v) => `₹${(v / 1e6).toFixed(1)}M`;

    async function openMenu() {
      const utils = render(
        React.createElement(PillarSelectDropdown, {
          options: OPTIONS, value: null, onChange: () => {}, fmtCurrency: fmt, detailedDescs: DESCS,
        }),
      );
      await act(async () => { fireEvent.click(utils.getByRole('button')); });
      return utils;
    }

    const optionRows = () =>
      [...document.querySelectorAll('[role="option"]')].filter((el) => el.textContent.trim() !== '— Select —');

    test('option rows carry no native title attribute', async () => {
      await openMenu();
      const rows = optionRows();
      expect(rows.length).toBe(2);
      for (const row of rows) expect(row.hasAttribute('title')).toBe(false);
    });

    test('hovering an option shows its description exactly once, in the formatted card', async () => {
      await openMenu();
      const row = optionRows().find((el) => /Renewable PPA/.test(el.textContent));
      await act(async () => { fireEvent.mouseEnter(row); });
      const text = document.body.textContent;
      const occurrences = text.split(DESCS.option_1).length - 1;
      expect(occurrences).toBe(1);
      // the card is the formatted one: title, cost, impact chips
      expect(text).toMatch(/💰 ₹2\.0M/);
      expect(text).toMatch(/\+100000 revenue_delta/);
      expect(text).toMatch(/-8 Carbon/);
      expect(text).toMatch(/\+3 Reputation/);
      // and nothing in the DOM repeats the description as a title
      expect(document.querySelector(`[title="${DESCS.option_1}"]`)).toBeNull();
    });
  });

  test('CSS does not re-introduce clipping-prone positioning', () => {
    const block = (name) => {
      const i = css.indexOf(`.${name} {`);
      return i === -1 ? '' : css.slice(i, css.indexOf('}', i));
    };
    expect(block('menu')).not.toMatch(/position:\s*absolute/);
    expect(block('tooltip')).not.toMatch(/position:\s*absolute/);
  });
});
