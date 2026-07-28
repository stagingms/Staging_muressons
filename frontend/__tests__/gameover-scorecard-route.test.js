/**
 * End-game routing when the Balanced Scorecard is disabled for a cohort.
 *
 * Reported: "in the single BU version, clicking Review Balanced Scorecard does
 * not go to the right page."
 *
 * balanced_scorecard defaults to OFF in the visibility catalogue. Wiring that
 * toggle to real rendering (2026-07-20) made the scorecard PHASE skip
 * forward — but the button that entered the phase was still shown, and the
 * skip rendered BoardroomShowdown unconditionally. A player who had already
 * finished the boardroom therefore tapped "Review Balanced Scorecard" and was
 * dropped back into a COMPLETED phase.
 *
 * The rule this pins: hiding a surface must hide its ENTRY POINTS too, and a
 * skip-forward must never land on a phase the player has already played.
 */
const fs = require('fs');
const path = require('path');

const APP = path.join(__dirname, '..', 'app');
const page = fs.readFileSync(path.join(APP, 'page.js'), 'utf8');
const gameOver = fs.readFileSync(path.join(APP, 'components', 'GameOverSummary.js'), 'utf8');

describe('end-game scorecard routing', () => {
  test('the entry handler is withheld when the scorecard is hidden', () => {
    expect(page).toMatch(
      /onReviewScorecard=\{isPlayerVisible\('balanced_scorecard'\)[\s\S]{0,80}?: null\}/
    );
  });

  test('the Review button renders only when it can actually navigate', () => {
    expect(gameOver).toMatch(/\{onReviewScorecard && \([\s\S]{0,200}?Review Balanced Scorecard/);
  });

  test('the PDF button renders only when the scorecard exists', () => {
    // handleDownload is implemented by OPENING the scorecard, so without it
    // the button silently does nothing.
    expect(gameOver).toMatch(/\{onReviewScorecard && \([\s\S]{0,220}?Download Report \(PDF\)/);
  });

  test('skipping a hidden scorecard never re-enters a completed boardroom', () => {
    const i = page.indexOf("gameOverPhase === 'scorecard' && !isPlayerVisible");
    expect(i).toBeGreaterThan(-1);
    const block = page.slice(i, i + 1400);
    // Must branch on boardroomDone before falling through to BoardroomShowdown.
    expect(block).toMatch(/if \(boardroomDone\)/);
    const doneBranch = block.slice(block.indexOf('if (boardroomDone)'));
    expect(doneBranch.slice(0, 400)).toContain('GameOverSummary');
  });

  test('the archetype step also skips to done when the boardroom is finished', () => {
    expect(page).toMatch(
      /isPlayerVisible\('balanced_scorecard'\) \? 'scorecard' : \(!boardroomDone \? 'boardroom' : 'done'\)/
    );
  });
});
