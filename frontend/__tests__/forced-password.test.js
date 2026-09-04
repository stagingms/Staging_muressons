/**
 * Audit 2026-09-04 F-01 (P0) — the forced change-password screen renders in
 * the cockpit.
 *
 * Players are issued MUR-NNNN / MUR-NNNN@123 with must_change_password=true
 * and the server refuses every write until the password is personal. The
 * only renderer of ChangePasswordModal was JoinCohortModal, which page.js
 * mounts only while there is NO session — so a fresh participant landed in
 * the briefing and then hit "Server returned incomplete data" on the R1 map.
 *
 * Rendering page.js with sessionId set and mustChangePassword=true must show
 * the forced dialog and nothing else; once the flag clears, the briefing.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';

const mockSim = {
  sessionId: 'sess-1', username: 'Alice', roundNumber: 1, globalState: null, businessUnits: [], history: [], events: {},
  roundConfig: null, gameOver: false, finalReport: null, loading: false, error: null, roundChanged: false,
  connectionState: 'ok', lastSyncAt: null, roundLocked: false, setRoundLocked: jest.fn(), commitResults: null,
  autoAdvanceDetected: false, setAutoAdvanceDetected: jest.fn(), practiceReset: false,
  mustChangePassword: true, isObserver: false, setIsObserver: jest.fn(),
  setMustChangePassword: jest.fn((v) => { mockSim.mustChangePassword = v; }),
  sessionMeta: {}, setSessionMeta: jest.fn(), setUsername: jest.fn(), startSession: jest.fn(), startSoloSession: jest.fn(),
  joinSession: jest.fn(), playerLogin: jest.fn(), fetchActiveCohorts: jest.fn(), fetchDashboard: jest.fn().mockResolvedValue({}),
  commitTurn: jest.fn(), advanceToNextRound: jest.fn(), saveDecisions: jest.fn(), fetchRoundConfig: jest.fn(),
  resumeSession: jest.fn().mockResolvedValue({}), logout: jest.fn(), isSolo: false,
};

jest.mock('../app/hooks/useSimulation', () => {
  const actual = jest.requireActual('../app/hooks/useSimulation');
  return {
    __esModule: true,
    default: () => mockSim,
    playerIdHeader: () => ({}),
    handlePlayerAuthFailure: () => false,
    errorDetailText: actual.errorDetailText,
    isPasswordChangeRequired: actual.isPasswordChangeRequired,
  };
});
jest.mock('../app/components/RoundBriefing', () => ({ __esModule: true, default: () => <div data-testid="briefing">BRIEFING-SCREEN</div> }));
jest.mock('../app/components/ExecutiveCockpit', () => ({ __esModule: true, default: () => <div data-testid="cockpit">COCKPIT</div> }));
jest.mock('../app/components/CrisisAlerts', () => ({ __esModule: true, default: () => null, CrisisScreen: () => null }));
jest.mock('../app/components/DecisionPressureTimer', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/ConnectionBanner', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/ResourceSidebar', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/GlossaryPanel', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/AchievementBadges', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/AIAdvisor', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/PeerComparison', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/PlayerAnalytics', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/OnboardingWalkthrough', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/components/RoundChecklist', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/utils/soundManager', () => ({ __esModule: true, default: { commit: jest.fn(), error: jest.fn(), toggle: jest.fn() } }));

beforeAll(() => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 404, json: async () => ({}) }));
  try { localStorage.setItem('muressons_playerId', 'MUR-0042'); } catch { /* jsdom */ }
});

describe('forced password change in the cockpit (F-01)', () => {
  test('with must_change_password the forced dialog renders and the game does not', async () => {
    mockSim.mustChangePassword = true;
    const Page = require('../app/page.js').default;
    render(<Page />);
    const title = await screen.findByText(/Set Your New Password/i);
    expect(title).toBeInTheDocument();
    expect(document.getElementById('change-password-title')).not.toBeNull();
    expect(screen.queryByTestId('briefing')).toBeNull();
    expect(screen.queryByTestId('cockpit')).toBeNull();
    // the issued id is pre-filled so the participant only types passwords
    expect(document.querySelector('input[value="MUR-0042"]')).not.toBeNull();
    // forced: no Cancel
    expect(screen.queryByRole('button', { name: /cancel/i })).toBeNull();
  }, 60000);

  test('once the flag clears, the briefing renders', async () => {
    mockSim.mustChangePassword = false;
    const Page = require('../app/page.js').default;
    render(<Page />);
    expect(await screen.findByTestId('briefing')).toBeInTheDocument();
    expect(document.getElementById('change-password-title')).toBeNull();
  }, 60000);

  test('an observer seat is never asked to change a password', async () => {
    mockSim.mustChangePassword = true;
    mockSim.isObserver = true;
    const Page = require('../app/page.js').default;
    render(<Page />);
    expect(await screen.findByTestId('briefing')).toBeInTheDocument();
    expect(document.getElementById('change-password-title')).toBeNull();
    mockSim.isObserver = false;
  }, 60000);
});

describe('403 password_change_required is surfaced, not swallowed', () => {
  const { errorDetailText, isPasswordChangeRequired } = jest.requireActual('../app/hooks/useSimulation');
  const detail = { code: 'password_change_required', message: 'Set a personal password before playing — the initial one is only for signing in.' };

  test('helpers recognise the code and render the message as text', () => {
    expect(isPasswordChangeRequired({ status: 403 }, { detail })).toBe(true);
    expect(isPasswordChangeRequired({ status: 403 }, { detail: 'Round 2 is locked' })).toBe(false);
    expect(isPasswordChangeRequired({ status: 400 }, { detail })).toBe(false);
    expect(errorDetailText(detail)).toMatch(/personal password/);
    expect(errorDetailText('plain')).toBe('plain');
    expect(errorDetailText([{ loc: ['body'], msg: 'field required' }])).toBe('field required');
    expect(errorDetailText(undefined, 'fb')).toBe('fb');
  });

  test('source pins: the map, the matrix and save-decisions raise the flag', () => {
    const fs = require('fs');
    const path = require('path');
    const read = (f) => fs.readFileSync(path.join(__dirname, '..', 'app', f), 'utf8');
    const page = read('page.js');
    expect(page).toMatch(/if \(isPasswordChangeRequired\(res, data\)\) sim\.setMustChangePassword\(true\)/);
    expect(page).toMatch(/onPasswordChangeRequired=\{\(\) => sim\.setMustChangePassword\(true\)\}/);
    expect(page).toMatch(/error: errorDetailText\(data\.detail/);
    const map = read('components/StakeholderMapModal.js');
    expect(map).toMatch(/isPasswordChangeRequired\(res, data\)/);
    expect(map).toMatch(/onPasswordChangeRequired\(\)/);
    const hook = read('hooks/useSimulation.js');
    const i = hook.indexOf('const saveDecisions = useCallback');
    expect(hook.slice(i, i + 1500)).toMatch(/if \(isPasswordChangeRequired\(res, body\)\) setMustChangePassword\(true\)/);
  });
});
