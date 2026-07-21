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
 */
const fs = require('fs');
const path = require('path');

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
    // Native title attribute as a touch/no-hover fallback
    expect(component).toMatch(/title=\{describe\(optKey\)\}/);
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
