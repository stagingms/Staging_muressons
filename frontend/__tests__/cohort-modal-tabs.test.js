/**
 * Cohort-creation modal: tab structure.
 *
 * The modal is a set of sibling AccordionItem tabs. "Advanced Controls" was
 * NESTED inside the "Pedagogy & Analytics" tab, so ~230 lines of quiz,
 * result-visibility, roster, RNG-seed, scheduling, report-access and template
 * settings lived behind an unrelated heading — reachable only by scrolling
 * past the analytics toggles, and invisible to anyone who never opened that
 * tab. Promoted to its own tab (2026-07-20).
 *
 * These are source-level structural pins: a nesting mistake still renders and
 * still parses, so neither a build nor a snapshot would catch it.
 */
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(
  path.join(__dirname, '..', 'app', 'components', 'CreateCohortModal.js'),
  'utf8'
);

/** Every AccordionItem with the nesting depth at which it is declared. */
function accordionTabs() {
  const out = [];
  let depth = 0;
  for (const line of src.split('\n')) {
    const open = /<AccordionItem\s+id="([a-z]+)"[^>]*title="([^"]*)"/.exec(line);
    if (open) {
      out.push({ id: open[1], title: open[2], depth });
      depth += 1;
    }
    depth -= (line.match(/<\/AccordionItem>/g) || []).length;
  }
  return { tabs: out, finalDepth: depth };
}

describe('cohort-creation modal tabs', () => {
  const { tabs, finalDepth } = accordionTabs();

  test('every tab is a top-level sibling (none nested inside another)', () => {
    const nested = tabs.filter((t) => t.depth !== 0).map((t) => `${t.id} (${t.title})`);
    expect(nested).toEqual([]);
  });

  test('accordion open/close tags are balanced', () => {
    expect(finalDepth).toBe(0);
  });

  test('Advanced Controls is its own tab', () => {
    const advanced = tabs.find((t) => t.id === 'advanced');
    expect(advanced).toBeDefined();
    expect(advanced.title).toMatch(/Advanced Controls/);
    expect(advanced.depth).toBe(0);
  });

  test('the expected tabs are present, in order', () => {
    expect(tabs.map((t) => t.id)).toEqual([
      'core', 'engine', 'verticals', 'modules',
      'interventions', 'pedagogy', 'advanced', 'lock',
    ]);
  });

  test('Advanced Controls carries its settings, not just a heading', () => {
    // Guard against a move that leaves the tab shell behind and drops the body.
    const start = src.indexOf('id="advanced"');
    const end = src.indexOf('id="lock"');
    const body = src.slice(start, end);
    for (const marker of ['quizEnabled', 'rngSeed', 'teamCount',
                          'cohortTimezone', 'reportAccess', 'saveTemplateName']) {
      expect(body).toContain(marker);
    }
  });

  test('the default open tab still exists', () => {
    const ids = new Set(tabs.map((t) => t.id));
    const initial = /useState\('([a-z]+)'\)[^\n]*\/\/?/.exec(src);
    expect(ids.has('core')).toBe(true); // setOpenTab('core') is used for validation jumps
  });
});
