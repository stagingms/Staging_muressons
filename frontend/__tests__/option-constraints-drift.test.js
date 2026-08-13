/**
 * option-constraints-drift.test.js
 *
 * The constraint sentence — the line under the option cards saying how a choice
 * narrows the next step — is AUTHORED CONTENT. It lives in
 * backend/option_constraints.json, which is where a facilitator edits it, and
 * is mirrored into frontend/app/utils/optionConstraints.js so the decision
 * screen renders without a round-trip.
 *
 * Two files, one truth. This is the same drift risk the shockwave catalogue has
 * and the same answer: parse the backend source and fail the build when they
 * disagree. Edit the JSON, regenerate the mirror, same commit.
 *
 * It also pins the keys to detailed_descriptions.json, because a constraint for
 * an option that no longer exists is dead copy nobody will ever see, and an
 * option with no slot cannot be authored at all.
 */
const fs = require('fs');
const path = require('path');

const repo = path.join(__dirname, '..', '..');
/* Sources are read with CRLF NORMALISED AWAY. Twenty-eight files in this repo
   carry Windows line endings (several with a stray CR before them), and the
   slicing below matches on literal '\n'. When a file flipped to CRLF the
   indexOf returned -1, the slice came back empty, and the assertion passed
   vacuously -- or, here, threw. Both of these tripwires were dark. */
const readSrc = (p) => fs.readFileSync(p, 'utf8').replace(/\r\n?/g, '\n');

const readJson = (p) => JSON.parse(fs.readFileSync(path.join(repo, p), 'utf8'));

const constraints = readJson('backend/option_constraints.json');
const descriptions = readJson('backend/detailed_descriptions.json');

const mirrorSrc = readSrc(
  path.join(__dirname, '..', 'app/utils/optionConstraints.js'), 'utf8');

/* keys of paradigm → round → [area →] option, as a flat sorted list */
function keyPaths(tree, skip = new Set(['_README'])) {
  const out = [];
  const walk = (node, trail) => {
    if (typeof node !== 'object' || node === null) { out.push(trail.join('/')); return; }
    for (const k of Object.keys(node)) { if (skip.has(k)) continue; walk(node[k], [...trail, k]); }
  };
  walk(tree, []);
  return out.sort();
}

describe('option constraints', () => {
  test('the frontend mirror matches the backend source exactly', () => {
    const literal = mirrorSrc.slice(
      mirrorSrc.indexOf('export const OPTION_CONSTRAINTS =') + 'export const OPTION_CONSTRAINTS ='.length,
      mirrorSrc.lastIndexOf(';\n\n/**'));
    const mirror = JSON.parse(literal.trim());
    const source = { ...constraints };
    delete source._README;   // the writing guide is for humans, not the bundle
    expect(mirror).toEqual(source);
  });

  test('every option that can be described can also be constrained', () => {
    const src = { ...descriptions };
    const con = { ...constraints };
    delete con._README;
    expect(keyPaths(con)).toEqual(keyPaths(src));
  });

  test('the writing guide travels with the file', () => {
    // A schema with no instructions gets filled in badly, or not at all.
    expect(Array.isArray(constraints._README)).toBe(true);
    expect(constraints._README.join(' ')).toMatch(/EMPTY IS SAFE/);
  });

  test('authored constraints stay short and stay in plain English', () => {
    const bad = [];
    const walk = (node, trail) => {
      if (typeof node === 'string') {
        if (!node) return;                                   // empty is a valid state
        const words = node.replace(/<\/?b>/g, '').split(/\s+/).length;
        if (words > 60) bad.push(`${trail.join('/')}: ${words} words — this is a paragraph, not a line`);
        if (/ESRS|§|M_R|M_SDG|CAROIC|NCD\b/.test(node)) bad.push(`${trail.join('/')}: carries a spec-sheet term`);
        if (/<(?!\/?b>)/.test(node)) bad.push(`${trail.join('/')}: only <b> renders`);
        return;
      }
      for (const k of Object.keys(node)) { if (k === '_README') continue; walk(node[k], [...trail, k]); }
    };
    walk(constraints, []);
    expect(bad).toEqual([]);
  });
});
