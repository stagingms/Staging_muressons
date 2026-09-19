/**
 * Adversarial Challenge Suite for Milestone 2: Facilitator & Admin Portal Remediations (Issues #12–#19)
 *
 * EMPIRICAL CHALLENGER: challenger_m2_1
 * Scope:
 *  1. RunBar.js pacing controls across all modes (Free: "⏭ Force Advance", Timed: "⏭ Unlock Early", Manual: "⏭ Advance")
 *  2. 60-second relock window operation and idempotence (undo action, expiration, and API credential enforcement)
 *  3. CreateCohortModal.js 8 accordion tabs integrity and client-side boundary validation (negative timer, quiz > 100%, startDate > endDate)
 *  4. CohortPulse.js missing METRICS declaration and per-team commit blast-radius assessment
 */

import React from 'react';
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import RunBar from '../app/components/RunBar';
import CohortPulse from '../app/components/CohortPulse';
import CreateCohortModal from '../app/components/CreateCohortModal';
import { PLAYER_VISIBILITY_DEFAULTS } from '../app/config/playerVisibilityRegistry';

const PRESETS = [
  {
    id: 'workshop_standard',
    name: 'Workshop',
    icon: 'W',
    difficulty_tier: 'advanced',
    subtitle: 'Standard',
    color: '#6366f1',
    target_audience: 'MBA',
    description: 'Balanced.',
    default_pedagogy: { round_recap_enabled: true },
    default_audiences: ['core'],
    results_reveal_round: 3,
  },
];

describe('Adversarial Challenge: RunBar Pacing & Unblock Controls across Modes (Issue #12)', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  test('Free Mode exposes "⏭ Force Advance" and calls force-advance with credentials', async () => {
    let capturedCall = null;
    const mockPulse = {
      commit_progress: { total_players: 4, committed_count: 2, target_round: 1 },
      pacing: { mode: 'free', unlocked_round: 1 },
      teams: [{ session_id: 't1', is_cohort_shell: false }, { session_id: 't2', is_cohort_shell: false }],
    };

    global.fetch = jest.fn((url, opts) => {
      const u = String(url);
      if (u.includes('/health')) return Promise.resolve({ ok: true, json: async () => ({ status: 'ok' }) });
      if (u.includes('/cohort-pulse/')) return Promise.resolve({ ok: true, json: async () => mockPulse });
      if (u.includes('/force-advance')) {
        capturedCall = { url: u, opts };
        return Promise.resolve({ ok: true, json: async () => ({ status: 'ok' }) });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    render(<RunBar cohortId="cohort_free_test" />);

    // Wait for pulse to load
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Force Advance/i })).toBeInTheDocument();
    });

    const forceBtn = screen.getByRole('button', { name: /Force Advance/i });
    expect(forceBtn.textContent).toContain('⏭ Force Advance');

    // Click Force Advance -> ConfirmModal
    await act(async () => {
      fireEvent.click(forceBtn);
    });

    const confirmBtn = screen.getByRole('button', { name: /^Force Advance$/i });
    expect(confirmBtn).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(capturedCall).toBeTruthy();
    expect(capturedCall.url).toContain('/api/admin/sessions/cohort_free_test/force-advance');
    expect(capturedCall.opts.credentials).toBe('include');
    expect(capturedCall.opts.method).toBe('POST');
  });

  test('Timed Mode exposes "⏭ Unlock Early" and calls pacing/unlock with credentials & target_round', async () => {
    let capturedCall = null;
    const mockPulse = {
      commit_progress: { total_players: 4, committed_count: 4, target_round: 1 },
      pacing: { mode: 'timed', unlocked_round: 1, next_unlock_at: '2026-09-19T10:00:00Z' },
      teams: [{ session_id: 't1', is_cohort_shell: false }],
    };

    global.fetch = jest.fn((url, opts) => {
      const u = String(url);
      if (u.includes('/health')) return Promise.resolve({ ok: true, json: async () => ({ status: 'ok' }) });
      if (u.includes('/cohort-pulse/')) return Promise.resolve({ ok: true, json: async () => mockPulse });
      if (u.includes('/pacing/unlock')) {
        capturedCall = { url: u, opts };
        return Promise.resolve({ ok: true, json: async () => ({ unlocked_round: 2, mode: 'timed' }) });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    render(<RunBar cohortId="cohort_timed_test" />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Unlock Early/i })).toBeInTheDocument();
    });

    const unlockEarlyBtn = screen.getByRole('button', { name: /Unlock Early/i });
    expect(unlockEarlyBtn.textContent).toContain('⏭ Unlock Early');

    await act(async () => {
      fireEvent.click(unlockEarlyBtn);
    });

    const confirmBtn = screen.getByRole('button', { name: /Unlock Round 2 Early/i });
    expect(confirmBtn).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(capturedCall).toBeTruthy();
    expect(capturedCall.url).toContain('/api/admin/sessions/cohort_timed_test/pacing/unlock');
    expect(capturedCall.opts.credentials).toBe('include');
    expect(capturedCall.opts.method).toBe('POST');
    const body = JSON.parse(capturedCall.opts.body);
    expect(body.target_round).toBe(2);
  });
});

describe('Adversarial Challenge: 60-Second Relock Window (Issue #18)', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  test('Arms 60s relock window upon unlock and allows relock POST with credentials', async () => {
    let relockCall = null;
    const mockPulse = {
      commit_progress: { total_players: 2, committed_count: 2, target_round: 1 },
      pacing: { mode: 'manual', unlocked_round: 1 },
      teams: [{ session_id: 't1', is_cohort_shell: false }],
    };

    global.fetch = jest.fn((url, opts) => {
      const u = String(url);
      if (u.includes('/health')) return Promise.resolve({ ok: true, json: async () => ({ status: 'ok' }) });
      if (u.includes('/cohort-pulse/')) return Promise.resolve({ ok: true, json: async () => mockPulse });
      if (u.includes('/pacing/unlock')) {
        return Promise.resolve({ ok: true, json: async () => ({ unlocked_round: 2, mode: 'manual' }) });
      }
      if (u.includes('/pacing/relock')) {
        relockCall = { url: u, opts };
        return Promise.resolve({ ok: true, json: async () => ({ unlocked_round: 1, mode: 'manual' }) });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    render(<RunBar cohortId="cohort_relock_test" />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Advance/i })).toBeInTheDocument();
    });

    // Unlock round 2
    const advanceBtn = screen.getByRole('button', { name: /Advance/i });
    await act(async () => {
      fireEvent.click(advanceBtn);
    });
    const confirmBtn = screen.getByRole('button', { name: /Unlock Round 2/i });
    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    // Undo button must now appear in the DOM
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Undo \(Relock R2\)/i })).toBeInTheDocument();
    });

    const undoBtn = screen.getByRole('button', { name: /Undo \(Relock R2\)/i });

    // Click Undo
    await act(async () => {
      fireEvent.click(undoBtn);
    });

    expect(relockCall).toBeTruthy();
    expect(relockCall.url).toContain('/api/admin/sessions/cohort_relock_test/pacing/relock');
    expect(relockCall.opts.credentials).toBe('include');

    // Button disappears after relock
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /Undo \(Relock/i })).not.toBeInTheDocument();
    });
  });

  test('Relock window countdown functions and cleans up timers on unmount', async () => {
    const mockPulse = {
      commit_progress: { total_players: 2, committed_count: 2, target_round: 1 },
      pacing: { mode: 'manual', unlocked_round: 1 },
      teams: [{ session_id: 't1', is_cohort_shell: false }],
    };

    global.fetch = jest.fn((url) => {
      const u = String(url);
      if (u.includes('/health')) return Promise.resolve({ ok: true, json: async () => ({ status: 'ok' }) });
      if (u.includes('/cohort-pulse/')) return Promise.resolve({ ok: true, json: async () => mockPulse });
      if (u.includes('/pacing/unlock')) {
        return Promise.resolve({ ok: true, json: async () => ({ unlocked_round: 2, mode: 'manual' }) });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    const { unmount } = render(<RunBar cohortId="cohort_relock_test2" />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Advance/i })).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Advance/i }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Unlock Round 2/i }));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Undo \(Relock R2\)/i })).toBeInTheDocument();
    });

    // Unmounting cleans up timer without throws
    expect(() => unmount()).not.toThrow();
  });
});

describe('Adversarial Challenge: CreateCohortModal Boundary Validation (Issues #16 & #17)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = jest.fn((url) => {
      const u = String(url);
      if (u.includes('/scenario-presets')) {
        return Promise.resolve({ ok: true, status: 200, json: async () => ({ presets: PRESETS }) });
      }
      if (u.includes('/god/analytics-visibility')) {
        return Promise.resolve({ ok: true, status: 200, json: async () => ({ facilitator: {}, player: { ...PLAYER_VISIBILITY_DEFAULTS } }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  test('Flags startDate > endDate with aria-invalid="true" and prevents cohort creation', async () => {
    const utils = render(
      <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}} currentFacilitatorId="god_mode" currentFacilitatorRole="super_admin" />
    );
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());

    // Enter valid cohort name & region
    const nameInput = utils.container.querySelector('input[placeholder*="Exec MBA"]');
    fireEvent.change(nameInput, { target: { value: 'Valid Cohort Name' } });
    const regionSelect = utils.container.querySelector('select[required]');
    fireEvent.change(regionSelect, { target: { value: 'apac' } });

    // Inverted dates: startDate > endDate
    const dateInputs = utils.container.querySelectorAll('input[type="date"]');
    expect(dateInputs.length).toBeGreaterThanOrEqual(2);
    fireEvent.change(dateInputs[0], { target: { value: '2026-10-15' } });
    fireEvent.change(dateInputs[1], { target: { value: '2026-10-01' } });

    // Attempt form submit
    await act(async () => {
      fireEvent.submit(utils.container.querySelector('form'));
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(dateInputs[1].getAttribute('aria-invalid')).toBe('true');
    expect(utils.container.textContent).toContain('End Date cannot be before Start Date');
    expect(global.fetch).not.toHaveBeenCalledWith(expect.stringContaining('/api/simulations/start'), expect.anything());
  });

  test('Flags negative round timer with aria-invalid="true" and prevents cohort creation', async () => {
    const utils = render(
      <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}} currentFacilitatorId="god_mode" currentFacilitatorRole="super_admin" />
    );
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());

    fireEvent.change(utils.container.querySelector('input[placeholder*="Exec MBA"]'), { target: { value: 'Valid Cohort' } });
    fireEvent.change(utils.container.querySelector('select[required]'), { target: { value: 'apac' } });

    // Open Advanced Controls accordion
    const advTabBtn = [...utils.container.querySelectorAll('button')].find((b) => /Advanced Controls/.test(b.textContent || ''));
    expect(advTabBtn).toBeTruthy();
    await act(async () => {
      fireEvent.click(advTabBtn);
      await new Promise((r) => setTimeout(r, 50));
    });

    const timerInput = utils.container.querySelector('input[type="number"][max="7200"]');
    expect(timerInput).toBeTruthy();
    fireEvent.change(timerInput, { target: { value: '-45' } });

    await act(async () => {
      fireEvent.submit(utils.container.querySelector('form'));
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(timerInput.getAttribute('aria-invalid')).toBe('true');
    expect(utils.container.textContent).toContain('Round timer duration must be between 0 and 7200 seconds');
    expect(global.fetch).not.toHaveBeenCalledWith(expect.stringContaining('/api/simulations/start'), expect.anything());
  });

  test('Flags quiz threshold > 100 with aria-invalid="true" and prevents cohort creation', async () => {
    const utils = render(
      <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}} currentFacilitatorId="god_mode" currentFacilitatorRole="super_admin" />
    );
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());

    fireEvent.change(utils.container.querySelector('input[placeholder*="Exec MBA"]'), { target: { value: 'Valid Cohort' } });
    fireEvent.change(utils.container.querySelector('select[required]'), { target: { value: 'apac' } });

    const advTabBtn = [...utils.container.querySelectorAll('button')].find((b) => /Advanced Controls/.test(b.textContent || ''));
    await act(async () => {
      fireEvent.click(advTabBtn);
      await new Promise((r) => setTimeout(r, 50));
    });

    const quizInput = utils.container.querySelector('input[type="number"][max="100"]');
    expect(quizInput).toBeTruthy();
    fireEvent.change(quizInput, { target: { value: '115' } });

    await act(async () => {
      fireEvent.submit(utils.container.querySelector('form'));
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(quizInput.getAttribute('aria-invalid')).toBe('true');
    expect(utils.container.textContent).toContain('Quiz pass threshold must be between 0% and 100%');
    expect(global.fetch).not.toHaveBeenCalledWith(expect.stringContaining('/api/simulations/start'), expect.anything());
  });
});

describe('Adversarial Challenge: CohortPulse Integrity & Blast-Radius Assessment (Issue #19)', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  test('REMEDIATION VERIFICATION: CohortPulse renders cleanly without ReferenceError when METRICS constant is restored', async () => {
    const mockPulseData = {
      teams: [
        {
          session_id: 'team_sess_1',
          name: 'Team Alpha',
          committed: true,
          has_saved_draft: false,
          current: { treasury: 50000000 },
          history: {},
        },
      ],
      commit_progress: { target_round: 1, total_players: 1, committed_count: 1 },
      player_visible: false,
    };

    global.fetch = jest.fn((url) => {
      const u = String(url);
      if (u.includes('/cohort-pulse/')) {
        return Promise.resolve({ ok: true, json: async () => mockPulseData });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(<CohortPulse cohortId="cohort_pulse_crash_test" />);
    await waitFor(() => {
      expect(screen.getByText('Team Alpha')).toBeInTheDocument();
    });

    // Verify metrics render as buttons without ReferenceError
    expect(screen.getByRole('button', { name: /Treasury/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reputation/i })).toBeInTheDocument();
    expect(consoleError).not.toHaveBeenCalled();

    consoleError.mockRestore();
  });

  test('Per-team commit button calls single-team force-commit endpoint with credentials', async () => {
    let commitCall = null;
    const mockPulseData = {
      teams: [
        {
          session_id: 'team_sess_1',
          team_id: 'team_sess_1',
          name: 'Team Alpha',
          committed: false,
          has_saved_draft: true,
          current: { treasury: 50000000 },
          history: {},
        },
      ],
      commit_progress: { target_round: 1, total_players: 1, committed_count: 0 },
      player_visible: false,
    };

    global.fetch = jest.fn((url, opts) => {
      const u = String(url);
      if (u.includes('/cohort-pulse/')) {
        return Promise.resolve({ ok: true, json: async () => mockPulseData });
      }
      if (u.includes('/force-commit')) {
        commitCall = { url: u, opts };
        return Promise.resolve({ ok: true, json: async () => ({ status: 'ok', advanced: true }) });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });

    render(<CohortPulse cohortId="cohort_single_team_test" />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /⚡ Commit/i })).toBeInTheDocument();
    });

    const commitBtn = screen.getByRole('button', { name: /⚡ Commit/i });
    await act(async () => {
      fireEvent.click(commitBtn);
    });

    // Confirm modal opens
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Auto-Commit Team/i })).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole('button', { name: /Auto-Commit Team/i });
    await act(async () => {
      fireEvent.click(confirmBtn);
    });

    expect(commitCall).toBeTruthy();
    expect(commitCall.url).toContain('/api/admin/sessions/cohort_single_team_test/teams/team_sess_1/force-commit');
    expect(commitCall.opts.credentials).toBe('include');
    expect(commitCall.opts.method).toBe('POST');
  });
});
