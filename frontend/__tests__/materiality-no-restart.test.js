/**
 * The CSRD Double Materiality matrix must never restart mid-exercise.
 *
 * Reported twice. First in pillar/BRSR mode, fixed by holding the mount until
 * the R2 BU selection resolved. Reported AGAIN for single-BU games, because
 * that guard was necessary but not sufficient:
 *
 *   decisionParadigm starts at the PLACEHOLDER 'legacy_abc' and is fetched
 *   from /paradigm (then re-polled every 8s). If the player opened the matrix
 *   before that fetch returned, isPillarMode was false — so the existing guard
 *   passed immediately and r2BuLoaded was set true. The paradigm then landed,
 *   isPillarMode flipped true, buId went null → BU, and the config useEffect
 *   keyed on [buId] re-ran. That effect REBUILDS every quadrant, so all placed
 *   issues were wiped and the assessment started over.
 *
 * Two independent defences, both pinned here:
 *   1. page.js holds the mount until the paradigm has actually RESOLVED.
 *   2. DoubleMaterialityMatrix FREEZES buId for the life of the mount, so no
 *      future prop churn (from any source) can reset an exercise in progress.
 *
 * Source-level pins: the failure is a state-timing race that still compiles,
 * renders, and passes a snapshot — only the sequencing is wrong.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const matrix = fs.readFileSync(path.join(APP, 'components', 'DoubleMaterialityMatrix.js'), 'utf8');
const page = fs.readFileSync(path.join(APP, 'page.js'), 'utf8');

describe('materiality matrix — no mid-exercise restart', () => {
  test('buId is frozen for the lifetime of the mount', () => {
    expect(matrix).toMatch(/const frozenBuIdRef = useRef\(buId\)/);
    expect(matrix).toMatch(/const effectiveBuId = frozenBuIdRef\.current/);
  });

  test('the config fetch is keyed on the FROZEN id, never the live prop', () => {
    // [buId] is the exact dependency that caused the wipe.
    expect(matrix).not.toMatch(/\}, \[buId\]\);/);
    expect(matrix).toMatch(/\}, \[effectiveBuId\]\);/);
  });

  test('the config fetch uses the frozen id for its endpoint', () => {
    const i = matrix.indexOf('const endpoint =');
    const block = matrix.slice(i, i + 220);
    expect(block).toContain('effectiveBuId');
    expect(block).not.toMatch(/\bbuId\b\s*\n?\s*\?/);
  });

  test('the submission carries the same BU the player was scored against', () => {
    // A mismatch would score the wrong dictionary AND break the server's
    // idempotency key (which includes bu_id), re-enabling double submits.
    expect(matrix).toMatch(/bu_id: effectiveBuId \|\| undefined/);
    expect(matrix).not.toMatch(/bu_id: buId \|\| undefined/);
  });

  test('the matrix mount waits for the paradigm to resolve', () => {
    expect(page).toMatch(/!paradigmResolved \|\| \(isPillarMode && !r2BuLoaded\)/);
  });

  test('paradigmResolved is set once the fetch returns', () => {
    expect(page).toMatch(/setParadigmResolved\(true\)/);
  });

  test('a demo/absent session does not block the matrix forever', () => {
    // That path never fetches, so it must resolve the gate itself.
    expect(page).toMatch(/=== 'demo'\) \{ setParadigmResolved\(true\); return; \}/);
  });

  test("the placeholder default is not treated as a known paradigm", () => {
    // useState('legacy_abc') is a guess; the guard must depend on the flag,
    // not on the value being non-empty.
    const i = page.indexOf("const [decisionParadigm");
    expect(page.slice(i, i + 600)).toMatch(/PLACEHOLDER/i);
  });
});
