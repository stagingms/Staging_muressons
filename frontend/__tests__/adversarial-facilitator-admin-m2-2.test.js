/**
 * Adversarial Challenge Suite for Milestone 2: Facilitator & Admin Portal Remediations (Issues #20–#28)
 *
 * EMPIRICAL CHALLENGER: challenger_m2_2
 * Scope:
 *  1. trading-floor/page.js ?cohort= reading, multi-cohort collision prevention, and room-scale typography
 *  2. war-map/page.js ambient auto-rotating summary functionality without mouse hover
 *  3. Complete eradication of window.confirm() from destructive admin flows and typed confirmation in ConfirmModal
 *  4. CustomBlackSwanBuilder unselected initial session state and accidental injection prevention
 *  5. admin/facilitator/page.js persistent frozen alert banner and durable AuditTrail mounting
 *  6. Polling loops pausing when document.visibilityState === 'hidden'
 */

import React from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mocks
let mockSearchParams = new URLSearchParams();
jest.mock('next/navigation', () => ({
  useSearchParams: () => mockSearchParams,
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  usePathname: () => '/admin/trading-floor',
}));

import TradingFloorPage from '../app/admin/trading-floor/page';
import WarMapPage from '../app/admin/war-map/page';
import ConfirmModal from '../app/components/ConfirmModal';
import CustomBlackSwanBuilder from '../app/components/CustomBlackSwanBuilder';
import RunBar from '../app/components/RunBar';

describe('Adversarial Challenge 1: Trading Floor ?cohort= scoping & collision prevention', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    mockSearchParams = new URLSearchParams('cohort=cohort_omega');
    if (!window.matchMedia) {
      window.matchMedia = jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));
    }
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  test('Filters multi-cohort leaderboard strictly to the requested cohort', async () => {
    const mockLeaderboard = {
      leaderboard: [
        { session_id: 'team_alpha_1', parent_cohort_id: 'cohort_alpha', player_name: 'Alpha Wolves', terminal_value: 5000000 },
        { session_id: 'team_omega_1', parent_cohort_id: 'cohort_omega', player_name: 'Omega Prime', terminal_value: 9000000 },
        { session_id: 'team_omega_2', parent_cohort_id: 'cohort_omega', player_name: 'Omega Delta', terminal_value: 7000000 },
      ],
    };

    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('/api/admin/leaderboard')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockLeaderboard),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    localStorage.setItem('muressons_finale_enabled', '1');

    render(<TradingFloorPage />);

    await waitFor(() => {
      const omegaPrimes = screen.getAllByText('Omega Prime');
      expect(omegaPrimes.length).toBeGreaterThan(0);
      const omegaDeltas = screen.getAllByText('Omega Delta');
      expect(omegaDeltas.length).toBeGreaterThan(0);
    });

    // Alpha Wolves MUST NOT be displayed on cohort_omega board!
    expect(screen.queryByText('Alpha Wolves')).not.toBeInTheDocument();
  });

  test('Ringing the closing bell targets the scoped cohort, preventing cross-cohort collision', async () => {
    let bellTargetUrl = '';
    global.fetch = jest.fn().mockImplementation((url, opts) => {
      if (url.includes('/api/admin/leaderboard')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            leaderboard: [
              { session_id: 'team_omega_1', parent_cohort_id: 'cohort_omega', player_name: 'Omega Prime', terminal_value: 9000000 },
            ],
          }),
        });
      }
      if (url.includes('/finale/ring-bell')) {
        bellTargetUrl = url;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'bell_rung', cohort_id: 'cohort_omega' }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    localStorage.setItem('muressons_finale_enabled', '1');

    render(<TradingFloorPage />);

    await waitFor(() => {
      expect(screen.getAllByText('Omega Prime').length).toBeGreaterThan(0);
    });

    const bellBtn = screen.getByText(/Ring the Closing Bell/i);
    fireEvent.click(bellBtn);

    // Confirm modal opens
    await waitFor(() => {
      expect(screen.getByText(/Every connected player/i)).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole('button', { name: /Ring the bell/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(bellTargetUrl).toBe('/api/admin/cohort_omega/finale/ring-bell');
    });
  });

  test('Projector typography complies with room-scale requirements', () => {
    const fileContent = fs.readFileSync(
      path.resolve(__dirname, '../app/admin/trading-floor/page.js'),
      'utf8'
    );
    expect(fileContent).toContain("maxWidth: 'min(1600px, 94vw)'");
    expect(fileContent).toContain("fontSize: '1.8rem'");
    expect(fileContent).toContain("fontSize: '2.4rem'");
    expect(fileContent).toContain('height: 24');
  });
});

describe('Adversarial Challenge 2: War Map ambient summary & room-scale presentation', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.useFakeTimers();
    mockSearchParams = new URLSearchParams('cohort=cohort_test');
    if (!window.matchMedia) {
      window.matchMedia = jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));
    }
  });

  afterEach(() => {
    jest.useRealTimers();
    global.fetch = originalFetch;
    jest.clearAllTimers();
  });

  test('Ambient summary renders and auto-rotates without requiring mouse hover', async () => {
    const mockWarMapData = {
      cohort_round: 3,
      team_count: 4,
      cohort_name: 'Alpha Cohort',
      crisis: { name: 'Supply Shock', icon: '⚡' },
      business_units: [
        { bu_id: 'consumer_goods', health: 35, revenue: 1000, slo: 40, carbon_intensity: 130, burnout: 0 },
      ],
      stakeholders: [
        { agent_id: 'the_regulator', name: 'The Regulator', stage: 'hostile', teams_hostile: 2 },
      ],
      events: [{ kind: 'bu', bu_id: 'consumer_goods', health: 35 }],
    };

    global.fetch = jest.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockWarMapData),
      })
    );

    localStorage.setItem('muressons_warmap_enabled', '1');

    render(<WarMapPage />);

    // Fast-forward initial promise
    await act(async () => {
      await Promise.resolve();
    });

    // Slide 1: Crisis should be active
    expect(screen.getByText('🚨 LIVE CRISIS')).toBeInTheDocument();
    expect(screen.getAllByText(/Supply Shock/).length).toBeGreaterThan(0);

    // Advance timer by 6000ms to cycle to next slide (BU Strain)
    act(() => {
      jest.advanceTimersByTime(6000);
    });

    expect(screen.getByText('⚡ BU STRAIN')).toBeInTheDocument();
    expect(screen.getAllByText(/Consumer Goods/).length).toBeGreaterThan(0);

    // Advance timer by another 6000ms to cycle to next slide (Stakeholder Watch)
    act(() => {
      jest.advanceTimersByTime(6000);
    });

    expect(screen.getByText('⚠️ STAKEHOLDER WATCH')).toBeInTheDocument();
    expect(screen.getAllByText(/The Regulator/).length).toBeGreaterThan(0);

    // Pause toggle test
    const pauseBtn = screen.getByText('⏸ Pause rotation');
    fireEvent.click(pauseBtn);

    expect(screen.getByText('▶ Resume rotation')).toBeInTheDocument();

    // After pausing, timer advance should NOT cycle the slide
    act(() => {
      jest.advanceTimersByTime(12000);
    });
    expect(screen.getByText('⚠️ STAKEHOLDER WATCH')).toBeInTheDocument();
  });
});

describe('Adversarial Challenge 3: window.confirm eradication & typed modal confirmation', () => {
  test('Native window.confirm is completely absent from all admin pages and components', () => {
    const adminDir = path.resolve(__dirname, '../app/admin');
    const componentsDir = path.resolve(__dirname, '../app/components');

    const adminFiles = fs.readdirSync(adminDir, { recursive: true })
      .map((f) => path.join(adminDir, f))
      .filter((f) => fs.statSync(f).isFile() && f.endsWith('.js'));

    for (const file of adminFiles) {
      const code = fs.readFileSync(file, 'utf8');
      const cleanCode = code.replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '');
      expect(cleanCode).not.toMatch(/\bwindow\.confirm\s*\(/);
      expect(cleanCode).not.toMatch(/\bconfirm\s*\(/);
    }

    // Check specific critical admin components from Issue #23
    const targetAdminComponents = [
      'CrisisTriggerConfig.js',
      'PlayerRegistry.js',
      'AutoPauseConfig.js',
      'RegulatorySandboxControl.js',
      'MaterialityConfig.js',
      'StakeholderConfig.js',
      'SystemExport.js',
      'MasterInterventions.js',
      'StudentBonuses.js',
      'ResourceManager.js',
      'FacilitatorNotes.js',
      'SwipeFile.js',
      'EconomicEngineTunables.js',
    ];

    for (const comp of targetAdminComponents) {
      const file = path.join(componentsDir, comp);
      if (fs.existsSync(file)) {
        const code = fs.readFileSync(file, 'utf8');
        const cleanCode = code.replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '');
        expect(cleanCode).not.toMatch(/\bwindow\.confirm\s*\(/);
      }
    }
  });

  test('ConfirmModal strictly locks confirm button until exact typed phrase matches', () => {
    const handleClose = jest.fn();

    render(
      <ConfirmModal
        title="Destroy Session"
        message="Are you sure?"
        impact="Permanent data loss"
        requirePhrase="DELETE"
        confirmLabel="Delete Now"
        onClose={handleClose}
      />
    );

    const confirmBtn = screen.getByRole('button', { name: 'Delete Now' });
    const phraseInput = screen.getByLabelText(/Type DELETE to unlock/i);

    // Initially aria-disabled / not unlockable per WCAG A11Y-F3
    expect(confirmBtn).toHaveAttribute('aria-disabled', 'true');

    // Clicking while locked must NOT trigger confirm
    fireEvent.click(confirmBtn);
    expect(handleClose).not.toHaveBeenCalled();

    // Typing wrong text leaves button aria-disabled
    fireEvent.change(phraseInput, { target: { value: 'DEL' } });
    expect(confirmBtn).toHaveAttribute('aria-disabled', 'true');
    fireEvent.click(confirmBtn);
    expect(handleClose).not.toHaveBeenCalled();

    // Typing with lowercase and spaces works via case-fold + trim
    fireEvent.change(phraseInput, { target: { value: '  delete  ' } });
    expect(confirmBtn).toHaveAttribute('aria-disabled', 'false');

    // Clicking confirm triggers onClose(true)
    fireEvent.click(confirmBtn);
    expect(handleClose).toHaveBeenCalledWith(true);
  });
});

describe('Adversarial Challenge 4: CustomBlackSwanBuilder accidental injection prevention', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('/api/admin/sessions')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            sessions: [
              { session_id: 'sess_1', cohort_name: 'Cohort Alpha', current_round: 1, custom_black_swan_enabled: true },
              { session_id: 'sess_2', cohort_name: 'Cohort Beta', current_round: 2, custom_black_swan_enabled: true },
            ],
          }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  test('Starts with unselected session and disables injection button', async () => {
    render(<CustomBlackSwanBuilder isAdmin={true} />);

    await waitFor(() => {
      expect(screen.getByText('Cohort Alpha (R1)')).toBeInTheDocument();
    });

    const select = screen.getAllByRole('combobox')[0];
    expect(select.value).toBe('');
    expect(screen.getByText('— Select a session —')).toBeInTheDocument();

    // Provide title and narrative but leave session unselected
    const titleInput = screen.getByPlaceholderText(/e\.g\. Global Shipping Canal Blocked/i);
    const narrativeInput = screen.getByPlaceholderText(/The news story presented to the executives/i);

    fireEvent.change(titleInput, { target: { value: 'Oil Spill in Harbor' } });
    fireEvent.change(narrativeInput, { target: { value: 'A tanker leaked crude oil near the port.' } });

    const injectBtn = screen.getByRole('button', { name: /Inject Custom Event Now/i });
    expect(injectBtn).toBeDisabled();

    // Selecting a session enables the button
    fireEvent.change(select, { target: { value: 'sess_1' } });
    expect(injectBtn).not.toBeDisabled();
  });
});

describe('Adversarial Challenge 5: Facilitator Portal persistent frozen banner & durable AuditTrail', () => {
  test('Codebase evidence: persistent frozen alert banner is mounted', () => {
    const facPage = fs.readFileSync(
      path.resolve(__dirname, '../app/admin/facilitator/page.js'),
      'utf8'
    );
    expect(facPage).toContain('scaffoldingStatus?.system_frozen');
    expect(facPage).toContain('SYSTEM FROZEN:');
    expect(facPage).toContain('role="alert"');
  });

  test('Codebase evidence: ephemeral in-memory activity log text is eliminated', () => {
    const facPage = fs.readFileSync(
      path.resolve(__dirname, '../app/admin/facilitator/page.js'),
      'utf8'
    );
    expect(facPage).not.toContain('Entries are kept in memory only and cleared on refresh');
    expect(facPage).toContain("<AuditTrail sessionId={selectedSession} />");
  });
});

describe('Adversarial Challenge 6: Polling pauses when document.visibilityState === hidden', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    global.fetch = originalFetch;
    jest.clearAllTimers();
  });

  test('RunBar pauses polling when document.visibilityState is hidden', async () => {
    let fetchCount = 0;
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('/api/admin/cohort-pulse/')) {
        fetchCount++;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ round: 2, committed_count: 1, total_count: 2 }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    render(<RunBar cohortId="cohort_123" />);

    // Initial fetch on mount
    await act(async () => {
      await Promise.resolve();
    });
    expect(fetchCount).toBe(1);

    // Mock document.visibilityState as hidden
    Object.defineProperty(document, 'visibilityState', {
      value: 'hidden',
      writable: true,
      configurable: true,
    });

    // Advance 15 seconds (3 poll intervals)
    act(() => {
      jest.advanceTimersByTime(15000);
    });

    // Fetch count must NOT increase while hidden!
    expect(fetchCount).toBe(1);

    // Restore to visible
    Object.defineProperty(document, 'visibilityState', {
      value: 'visible',
      writable: true,
      configurable: true,
    });

    // Advance 5 seconds
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    // Now fetch count should increase
    expect(fetchCount).toBe(2);
  });
});
