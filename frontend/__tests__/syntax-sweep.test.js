/**
 * Pre-deploy check turned tripwire (2026-09-06). The C-1 glossary edit left an
 * unescaped apostrophe inside a single-quoted string; no jest suite imports
 * TechnicalGlossary.js, so 1,145 tests were green while `next build` — the
 * Dockerfile stage Railway runs — could not parse the file. Every source file
 * under app/ is now parsed here, so a syntax error fails the suite, not the
 * deploy.
 */
const fs = require('fs');
const path = require('path');
const parser = require('@babel/parser');

const root = path.join(__dirname, '..', 'app');
const files = [];
(function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (/\.(js|jsx|mjs)$/.test(entry.name)) files.push(full);
  }
})(root);

describe('every source file under app/ parses', () => {
  test('there is something to sweep', () => {
    expect(files.length).toBeGreaterThan(100);
  });

  test('no file fails to parse as an ES module with JSX', () => {
    const failures = [];
    for (const f of files) {
      try {
        parser.parse(fs.readFileSync(f, 'utf8'), { sourceType: 'module', plugins: ['jsx'], errorRecovery: false });
      } catch (e) {
        failures.push(`${path.relative(root, f)}: ${e.message.split('\n')[0]}`);
      }
    }
    expect(failures).toEqual([]);
  });
});
