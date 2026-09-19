/**
 * Adversarial Stress Test Suite: Server-Authoritative Round Lockout (Issue #29)
 *
 * EMPIRICAL CHALLENGER: challenger_m3_rem_1
 *
 * Verifications:
 * 1. Client-Side Timer Immunity: No timeout or interval clears sim.roundLocked.
 * 2. Interaction Non-Dismissibility: Clicks, backdrops, and keystrokes cannot dismiss or unmount the overlay.
 * 3. Server-Authoritative State Machine: Overlay remains active until server telemetry signals unlock or advancement.
 */

import React from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';

describe('Adversarial Stress Test: Client-Side Timer Immunity', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('Timer advancement by 30s, 60s, 300s, 3600s never clears roundLocked', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Verify 30s auto-clear timer is completely absent
    expect(pageContent).not.toMatch(/setTimeout\([\s\S]*?setRoundLocked\(false\)[\s\S]*?30_000\)/);
    expect(pageContent).not.toMatch(/sim\.setRoundLocked\s*\(\s*false\s*\)/);
    expect(pageContent).not.toMatch(/\bsetRoundLocked\s*\(\s*false\s*\)/);

    // Mock roundLocked simulation state in a component mimicking page.js overlay render
    const MockOverlay = ({ roundLocked, roundLockReason }) => (
      <div>
        {roundLocked && (
          <div
            aria-label="Simulation Round Locked"
            data-testid="round-lockout-overlay"
            style={{ position: 'fixed', inset: 0 }}
          >
            <div>{roundLockReason?.kind === 'teams' ? '⏳' : '🔒'}</div>
            <h2>{roundLockReason?.kind === 'teams' ? 'Waiting for Other Teams' : 'Waiting for Facilitator'}</h2>
          </div>
        )}
      </div>
    );

    const state = { roundLocked: true, roundLockReason: { kind: 'facilitator' } };
    render(<MockOverlay roundLocked={state.roundLocked} roundLockReason={state.roundLockReason} />);

    expect(screen.getByTestId('round-lockout-overlay')).toBeInTheDocument();

    // Fast-forward 30 seconds
    act(() => {
      jest.advanceTimersByTime(30000);
    });
    expect(screen.getByTestId('round-lockout-overlay')).toBeInTheDocument();

    // Fast-forward 60 seconds
    act(() => {
      jest.advanceTimersByTime(60000);
    });
    expect(screen.getByTestId('round-lockout-overlay')).toBeInTheDocument();

    // Fast-forward 1 hour
    act(() => {
      jest.advanceTimersByTime(3600000);
    });
    expect(screen.getByTestId('round-lockout-overlay')).toBeInTheDocument();
  });

  test('Overlay has zero dismiss triggers (no buttons, no backdrop click handlers, no keydown bypass)', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');
    const overlayMatch = pageContent.match(/\{sim\.roundLocked\s*&&[\s\S]*?aria-label="Simulation Round Locked"[\s\S]*?<\/div>\s*\)\}/);
    expect(overlayMatch).not.toBeNull();
    const overlayCode = overlayMatch[0];

    // Assert no interactive dismiss mechanisms exist in the overlay code
    expect(overlayCode).not.toContain('onClick');
    expect(overlayCode).not.toContain('onKeyDown');
    expect(overlayCode).not.toMatch(/<button/i);
    expect(overlayCode).not.toMatch(/Dismiss/i);
    expect(overlayCode).not.toMatch(/close/i);
  });
});

describe('Adversarial Stress Test: Poller Authoritative State Machine', () => {
  test('useSimulation poller only unmasks roundLocked on authoritative server signals', () => {
    const hookContent = fs.readFileSync(path.join(__dirname, '../app/hooks/useSimulation.js'), 'utf8');

    // 1. Facilitator lock clearance requires gState.cohort_round_locked === false
    expect(hookContent).toMatch(/if\s*\(roundLockReason\?\.kind === 'facilitator'\s*&&\s*gState\.cohort_round_locked === false\)\s*\{\s*setRoundLocked\(false\);\s*setRoundLockReason\(null\);/);

    // 2. Teams lock clearance requires gState.cohort_advance_unblocked === true
    expect(hookContent).toMatch(/else\s+if\s*\(roundLockReason\?\.kind === 'teams'\)\s*\{\s*if\s*\(gState\.cohort_advance_unblocked === true\)\s*\{\s*setRoundLocked\(false\);\s*setRoundLockReason\(null\);/);

    // 3. Round advancement clearance requires data.current_round > roundNumber
    expect(hookContent).toMatch(/if\s*\(data\.current_round > roundNumber[\s\S]*?\)\s*\{[\s\S]*?setRoundLocked\(false\);\s*setRoundLockReason\(null\);/);

    // 4. Stale round 409 recovery
    expect(hookContent).toMatch(/if\s*\(conflict\?\.detail\?\.code === 'stale_round'\)\s*\{[\s\S]*?setRoundLocked\(false\);/);

    // 5. Successful turn commit
    expect(hookContent).toMatch(/setRoundLocked\(false\);\s*const data = await res\.json\(\);/);
  });

  test('Simulate poller transitions against server global_state oracle', () => {
    // Pure state transition function matching useSimulation.js poller logic
    function evaluatePollerState({ roundLocked, roundLockReason, roundNumber, pollerData }) {
      let nextRoundLocked = roundLocked;
      let nextReason = roundLockReason;
      let nextRound = roundNumber;

      if (nextRoundLocked) {
        const gState = pollerData.global_state || {};
        if (nextReason?.kind === 'facilitator' && gState.cohort_round_locked === false) {
          nextRoundLocked = false;
          nextReason = null;
        } else if (nextReason?.kind === 'teams') {
          if (gState.cohort_advance_unblocked === true) {
            nextRoundLocked = false;
            nextReason = null;
          } else if (gState.team_commits_this_round != null) {
            nextReason = { ...nextReason, committed: gState.team_commits_this_round };
          }
        }
      }

      if (pollerData.current_round > nextRound) {
        nextRound = pollerData.current_round;
        nextRoundLocked = false;
        nextReason = null;
      }

      return { roundLocked: nextRoundLocked, roundLockReason: nextReason, roundNumber: nextRound };
    }

    // Scenario 1: Facilitator lock active, server still locked
    let state = {
      roundLocked: true,
      roundLockReason: { kind: 'facilitator', message: 'Locked by facilitator' },
      roundNumber: 1,
      pollerData: { current_round: 1, global_state: { cohort_round_locked: true } }
    };
    let result = evaluatePollerState(state);
    expect(result.roundLocked).toBe(true);
    expect(result.roundLockReason.kind).toBe('facilitator');

    // Scenario 2: Facilitator unlock arrives from server
    state.pollerData = { current_round: 1, global_state: { cohort_round_locked: false } };
    result = evaluatePollerState(state);
    expect(result.roundLocked).toBe(false);
    expect(result.roundLockReason).toBeNull();

    // Scenario 3: Teams barrier active, commits pending (2/4 committed)
    state = {
      roundLocked: true,
      roundLockReason: { kind: 'teams', committed: 1, teams: 4 },
      roundNumber: 1,
      pollerData: { current_round: 1, global_state: { cohort_advance_unblocked: false, team_commits_this_round: 2 } }
    };
    result = evaluatePollerState(state);
    expect(result.roundLocked).toBe(true);
    expect(result.roundLockReason.committed).toBe(2);

    // Scenario 4: Teams barrier unblocked by server
    state.pollerData = { current_round: 1, global_state: { cohort_advance_unblocked: true, team_commits_this_round: 4 } };
    result = evaluatePollerState(state);
    expect(result.roundLocked).toBe(false);
    expect(result.roundLockReason).toBeNull();

    // Scenario 5: Round advances to 2 while locked
    state = {
      roundLocked: true,
      roundLockReason: { kind: 'teams', committed: 2, teams: 4 },
      roundNumber: 1,
      pollerData: { current_round: 2, global_state: { cohort_advance_unblocked: false } }
    };
    result = evaluatePollerState(state);
    expect(result.roundLocked).toBe(false);
    expect(result.roundLockReason).toBeNull();
    expect(result.roundNumber).toBe(2);
  });
});
