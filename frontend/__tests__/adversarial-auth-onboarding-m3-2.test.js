/**
 * Adversarial Challenge Suite: Auth & Onboarding Flow Remediations (Issues #36–#42 + #29–#35)
 *
 * EMPIRICAL CHALLENGER: challenger_m3_2
 *
 * Stress-testing:
 * 1. GlobalTooltip WCAG 1.4.13 compliance (hoverable content, grace buffer, Escape dismiss, font sizes >= 12px)
 * 2. ChangePasswordModal & OnboardingWalkthrough dark theme token conformance & exact veil preservation (0.55 & 0.38)
 * 3. JoinCohortModal typography (zero sub-12px), checkbox dimensions (24px), label-input associations
 * 4. Z-index hierarchy across auth components clamped to OVERLAY_PRIORITY
 * 5. Server-authoritative lockout in page.js (no client dismiss bypass)
 * 6. ModuleLoadingSkeleton accessibility and dynamic chunk fallback
 * 7. OnboardingWizard copy accuracy (no PDF promise, 5-tier role hierarchy)
 * 8. Provisioning admin badge presentation in admin/facilitator
 */

import React from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen, act, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

import GlobalTooltip from '../app/components/GlobalTooltip';
import ChangePasswordModal from '../app/components/ChangePasswordModal';
import OnboardingWalkthrough from '../app/components/OnboardingWalkthrough';
import JoinCohortModal from '../app/components/JoinCohortModal';
import { OVERLAY_PRIORITY } from '../app/components/overlayPriority';

const mockSim = {
  sessionId: 'sess-1',
  username: 'Alice',
  roundNumber: 1,
  globalState: null,
  businessUnits: [],
  history: [],
  events: {},
  roundConfig: null,
  gameOver: false,
  finalReport: null,
  loading: false,
  error: null,
  roundChanged: false,
  connectionState: 'ok',
  lastSyncAt: null,
  roundLocked: false,
  setRoundLocked: jest.fn(),
  commitResults: null,
  autoAdvanceDetected: false,
  setAutoAdvanceDetected: jest.fn(),
  practiceReset: false,
  mustChangePassword: false,
  isObserver: false,
  setIsObserver: jest.fn(),
  setMustChangePassword: jest.fn(),
  sessionMeta: { status: 'waiting', cohort_name: 'Titan Strategic Cohort' },
  setSessionMeta: jest.fn((v) => {
    mockSim.sessionMeta = typeof v === 'function' ? v(mockSim.sessionMeta) : v;
  }),
  setUsername: jest.fn(),
  startSession: jest.fn(),
  startSoloSession: jest.fn(),
  joinSession: jest.fn(),
  playerLogin: jest.fn(),
  fetchActiveCohorts: jest.fn(),
  fetchDashboard: jest.fn().mockResolvedValue({}),
  commitTurn: jest.fn(),
  advanceToNextRound: jest.fn(),
  saveDecisions: jest.fn(),
  fetchRoundConfig: jest.fn(),
  resumeSession: jest.fn().mockResolvedValue({}),
  logout: jest.fn(),
  isSolo: false,
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
jest.mock('../app/components/RoundChecklist', () => ({ __esModule: true, default: () => null }));
jest.mock('../app/utils/soundManager', () => ({ __esModule: true, default: { commit: jest.fn(), error: jest.fn(), toggle: jest.fn() } }));

beforeAll(() => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 404, json: async () => ({}) }));
  try { localStorage.setItem('muressons_playerId', 'MUR-0042'); } catch { /* jsdom */ }
});

describe('Adversarial Challenge 1: GlobalTooltip WCAG 1.4.13 Compliance', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('Tooltip appears on mouseover of [data-tooltip] after delay and has pointerEvents: auto', () => {
    render(
      <div>
        <GlobalTooltip />
        <button id="target-btn" data-tooltip="Important system telemetry information">
          Target
        </button>
      </div>
    );

    const btn = document.getElementById('target-btn');
    fireEvent.mouseOver(btn);

    // Before 180ms delay, tooltip is not visible
    act(() => {
      jest.advanceTimersByTime(100);
    });
    let tooltip = document.getElementById('global-tooltip');
    expect(tooltip).toBeInTheDocument();
    expect(tooltip.style.opacity).toBe('0');

    // After 180ms delay, tooltip becomes visible
    act(() => {
      jest.advanceTimersByTime(90);
    });
    expect(tooltip.style.opacity).toBe('1');
    expect(tooltip.style.pointerEvents).toBe('auto');
    expect(tooltip.style.zIndex).toBe(String(OVERLAY_PRIORITY.TOOLTIP));
    expect(screen.getByText('Important system telemetry information')).toBeInTheDocument();
  });

  test('WCAG 1.4.13 Hoverable: user can transition pointer from trigger to tooltip without dismissal', () => {
    render(
      <div>
        <GlobalTooltip />
        <button id="hover-trigger" data-tooltip="Detailed paragraph one.\n\nAnswers: Insightful breakdown\n\nTag: Security">
          Hover Source
        </button>
        <div id="neutral-canvas-area" />
      </div>
    );

    const btn = document.getElementById('hover-trigger');
    const neutral = document.getElementById('neutral-canvas-area');

    fireEvent.mouseOver(btn);
    act(() => {
      jest.advanceTimersByTime(200);
    });

    const tooltip = document.getElementById('global-tooltip');
    expect(tooltip.style.opacity).toBe('1');

    // Pointer leaves trigger towards tooltip
    fireEvent.mouseOut(btn, { relatedTarget: tooltip });

    // Transition time (50ms < 120ms hide buffer)
    act(() => {
      jest.advanceTimersByTime(50);
    });

    // Pointer enters tooltip
    fireEvent.mouseEnter(tooltip);

    // Advance beyond the original 120ms hide timeout
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Tooltip MUST remain visible while mouse is inside it! (WCAG 1.4.13 Hoverable)
    expect(tooltip.style.opacity).toBe('1');

    // Now pointer leaves tooltip to a neutral canvas DOM element
    fireEvent.mouseLeave(tooltip, { relatedTarget: neutral });

    // Still visible immediately due to 120ms grace period
    expect(tooltip.style.opacity).toBe('1');

    // After 120ms grace period expires, tooltip dismisses
    act(() => {
      jest.advanceTimersByTime(130);
    });
    expect(tooltip.style.opacity).toBe('0');
  });

  test('Escape key immediately dismisses tooltip without moving pointer or focus', () => {
    render(
      <div>
        <GlobalTooltip />
        <button id="esc-trigger" data-tooltip="Dismissible notice">
          Trigger
        </button>
      </div>
    );

    const btn = document.getElementById('esc-trigger');
    fireEvent.mouseOver(btn);
    act(() => {
      jest.advanceTimersByTime(200);
    });

    const tooltip = document.getElementById('global-tooltip');
    expect(tooltip.style.opacity).toBe('1');

    // Press Escape
    fireEvent.keyDown(document, { key: 'Escape' });

    // Immediately dismissed!
    expect(tooltip.style.opacity).toBe('0');
  });

  test('Source code scan: GlobalTooltip has zero sub-12px type declarations', () => {
    const filePath = path.join(__dirname, '../app/components/GlobalTooltip.js');
    const content = fs.readFileSync(filePath, 'utf8');

    const toPx = (raw) => {
      const v = String(raw).trim().replace(/\s*!important$/i, '');
      if (/^[\d.]+px$/.test(v)) return parseFloat(v);
      if (/^[\d.]+rem$/.test(v)) return parseFloat(v) * 16;
      return null;
    };

    const sub12Matches = [];
    for (const m of content.matchAll(/fontSize:\s*['"]([^'"]+)['"]/g)) {
      const px = toPx(m[1]);
      if (px !== null && px < 12) {
        sub12Matches.push(m[1]);
      }
    }

    expect(sub12Matches).toEqual([]);
  });

  test('EMPIRICAL STRESS TEST: pointer leaving viewport (relatedTarget is Window) reveals unprotected Node.contains call', () => {
    // This test verifies whether GlobalTooltip line 304 guards against non-Node relatedTarget
    const filePath = path.join(__dirname, '../app/components/GlobalTooltip.js');
    const content = fs.readFileSync(filePath, 'utf8');

    // Observation: line 304 does `activeElRef.current.contains(related)` without checking if `related` is a Node or checking `closest`
    // In DOM spec, Node.contains(other) throws TypeError if other is not a Node (such as Window).
    const hasNodeGuard = content.includes('related instanceof Node') ||
                         content.includes('typeof related?.closest === \'function\'') ||
                         content.includes('related?.nodeType');

    // We record whether this defensive guard is present:
    // (Line 79 uses `typeof related.closest === 'function'`, but line 76 and line 304 do not)
    expect({
      line76_line304_unprotected_contains: !hasNodeGuard,
    }).toEqual({
      line76_line304_unprotected_contains: false, // Confirmed: defensive Node guard is active!
    });
  });

  test('EMPIRICAL RUNTIME STRESS: GlobalTooltip handleOut with window, null, or document as relatedTarget throws ZERO TypeErrors', () => {
    render(
      <div>
        <GlobalTooltip />
        <button id="stress-trigger-window" data-tooltip="Testing tooltip window departure">
          Window Departure
        </button>
      </div>
    );

    const btn = document.getElementById('stress-trigger-window');
    const tooltip = document.getElementById('global-tooltip');

    // Case 1: relatedTarget is Window (pointer exits browser viewport directly from trigger)
    fireEvent.mouseOver(btn);
    act(() => { jest.advanceTimersByTime(200); });
    expect(tooltip.style.opacity).toBe('1');

    expect(() => {
      fireEvent.mouseOut(btn, { relatedTarget: window });
    }).not.toThrow();

    act(() => { jest.advanceTimersByTime(130); });
    expect(tooltip.style.opacity).toBe('0');

    // Case 2: relatedTarget is null (pointer exits window / offscreen)
    fireEvent.mouseOver(btn);
    act(() => { jest.advanceTimersByTime(200); });
    expect(tooltip.style.opacity).toBe('1');

    expect(() => {
      fireEvent.mouseOut(btn, { relatedTarget: null });
    }).not.toThrow();

    act(() => { jest.advanceTimersByTime(130); });
    expect(tooltip.style.opacity).toBe('0');

    // Case 3: relatedTarget is document
    fireEvent.mouseOver(btn);
    act(() => { jest.advanceTimersByTime(200); });
    expect(tooltip.style.opacity).toBe('1');

    expect(() => {
      fireEvent.mouseOut(btn, { relatedTarget: document });
    }).not.toThrow();

    act(() => { jest.advanceTimersByTime(130); });
    expect(tooltip.style.opacity).toBe('0');
  });

  test('EMPIRICAL RUNTIME STRESS: GlobalTooltip onMouseLeave with window, null, or arbitrary object throws ZERO TypeErrors', () => {
    render(
      <div>
        <GlobalTooltip />
        <button id="stress-trigger-leave" data-tooltip="Testing tooltip container exit">
          Container Exit
        </button>
      </div>
    );

    const btn = document.getElementById('stress-trigger-leave');
    const tooltip = document.getElementById('global-tooltip');

    // Hover trigger and move pointer into tooltip
    fireEvent.mouseOver(btn);
    act(() => { jest.advanceTimersByTime(200); });
    expect(tooltip.style.opacity).toBe('1');
    fireEvent.mouseEnter(tooltip);

    // Case 1: Pointer leaves tooltip container towards Window
    expect(() => {
      fireEvent.mouseLeave(tooltip, { relatedTarget: window });
    }).not.toThrow();

    act(() => { jest.advanceTimersByTime(130); });
    expect(tooltip.style.opacity).toBe('0');

    // Re-trigger
    fireEvent.mouseOver(btn);
    act(() => { jest.advanceTimersByTime(200); });
    expect(tooltip.style.opacity).toBe('1');
    fireEvent.mouseEnter(tooltip);

    // Case 2: Pointer leaves tooltip container towards null
    expect(() => {
      fireEvent.mouseLeave(tooltip, { relatedTarget: null });
    }).not.toThrow();

    act(() => { jest.advanceTimersByTime(130); });
    expect(tooltip.style.opacity).toBe('0');

    // Re-trigger
    fireEvent.mouseOver(btn);
    act(() => { jest.advanceTimersByTime(200); });
    expect(tooltip.style.opacity).toBe('1');
    fireEvent.mouseEnter(tooltip);

    // Case 3: Pointer leaves tooltip container towards non-Node EventTarget (e.g. new EventTarget())
    const nonNodeTarget = new EventTarget();
    expect(() => {
      fireEvent.mouseLeave(tooltip, { relatedTarget: nonNodeTarget });
    }).not.toThrow();

    act(() => { jest.advanceTimersByTime(130); });
    expect(tooltip.style.opacity).toBe('0');
  });
});

describe('Adversarial Challenge 2: ChangePasswordModal & OnboardingWalkthrough Token & Veil Conformance', () => {
  test('ChangePasswordModal uses dark cockpit design tokens and OVERLAY_PRIORITY.MODAL', () => {
    const { rerender } = render(
      <ChangePasswordModal isOpen={true} onClose={() => {}} isForced={false} />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog.style.zIndex).toBe(String(OVERLAY_PRIORITY.MODAL));

    // Non-forced has close button
    const closeBtn = screen.getByRole('button', { name: '×' });
    expect(closeBtn).toBeInTheDocument();

    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    expect(cancelBtn).toBeInTheDocument();

    // Rerender as isForced=true
    rerender(<ChangePasswordModal isOpen={true} onClose={() => {}} isForced={true} />);

    // In forced mode, close '×' and 'Cancel' buttons are NOT rendered
    expect(screen.queryByRole('button', { name: '×' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument();
    expect(screen.getByText(/You must set a personal password before continuing/i)).toBeInTheDocument();
  });

  test('ChangePasswordModal source verification: tokenized styling without hardcoded white backgrounds', () => {
    const filePath = path.join(__dirname, '../app/components/ChangePasswordModal.js');
    const content = fs.readFileSync(filePath, 'utf8');

    // Must use design tokens for surfaces
    expect(content).toContain("background: 'var(--bg-card)'");
    expect(content).toContain("border: '1px solid var(--border-subtle)'");
    expect(content).toContain("background: 'var(--bg-elevated)'");
    expect(content).toContain("color: 'var(--text-primary)'");
    expect(content).toContain("color: 'var(--text-secondary)'");

    // Must NOT have hardcoded white card backgrounds
    expect(content).not.toMatch(/background:\s*['"]#fff['"]/);
    expect(content).not.toMatch(/background:\s*['"]#ffffff['"]/);
  });

  test('OnboardingWalkthrough strictly preserves exact veil values (0.55 and 0.38) and uses ONBOARDING_TOUR priority', () => {
    const filePath = path.join(__dirname, '../app/components/OnboardingWalkthrough.js');
    const content = fs.readFileSync(filePath, 'utf8');

    // Extract all rgba(15, 23, 42, X)
    const veilMatches = [...content.matchAll(/rgba\(15,\s*23,\s*42,\s*([\d.]+)\)/g)].map(m => parseFloat(m[1]));

    expect(veilMatches).toHaveLength(2);
    expect(veilMatches[0]).toBe(0.55); // Spotlight veil
    expect(veilMatches[1]).toBe(0.38); // Fallback / no-target veil

    // Must use OVERLAY_PRIORITY.ONBOARDING_TOUR
    expect(content).toContain('zIndex: OVERLAY_PRIORITY.ONBOARDING_TOUR');

    // Must use dark theme tokens for card
    expect(content).toContain("background: 'var(--bg-card)'");
    expect(content).toContain("border: '1px solid var(--border-subtle)'");
  });

  test('OnboardingWalkthrough renders fallback veil when target element is absent', () => {
    const { container } = render(
      <OnboardingWalkthrough roundNumber={1} onComplete={() => {}} />
    );

    // Initial step target is null (Welcome card)
    const veilFallback = container.querySelector('div[style*="rgba(15, 23, 42, 0.38)"]');
    expect(veilFallback).toBeInTheDocument();
  });
});

describe('Adversarial Challenge 3: JoinCohortModal Accessible Typography & Checkbox Target', () => {
  test('JoinCohortModal.js and JoinCohortModal.module.css have exactly ZERO sub-12px declarations', () => {
    const toPx = (raw) => {
      const v = String(raw).trim().replace(/\s*!important$/i, '');
      if (/^[\d.]+px$/.test(v)) return parseFloat(v);
      if (/^[\d.]+rem$/.test(v)) return parseFloat(v) * 16;
      return null;
    };

    // Check JS
    const jsPath = path.join(__dirname, '../app/components/JoinCohortModal.js');
    const jsContent = fs.readFileSync(jsPath, 'utf8');
    const jsSub12 = [];
    for (const m of jsContent.matchAll(/fontSize:\s*['"]([^'"]+)['"]/g)) {
      const px = toPx(m[1]);
      if (px !== null && px < 12) jsSub12.push(m[1]);
    }
    expect(jsSub12).toEqual([]);

    // Check CSS
    const cssPath = path.join(__dirname, '../app/components/JoinCohortModal.module.css');
    const cssContent = fs.readFileSync(cssPath, 'utf8');
    const cssSub12 = [];
    for (const m of cssContent.matchAll(/font-size:\s*([^;{}]+);/g)) {
      const px = toPx(m[1]);
      if (px !== null && px < 12) cssSub12.push(m[1].trim());
    }
    expect(cssSub12).toEqual([]);
  });

  test('JoinCohortModal.module.css defines checkbox at minimum 24x24px for touch targets', () => {
    const cssPath = path.join(__dirname, '../app/components/JoinCohortModal.module.css');
    const cssContent = fs.readFileSync(cssPath, 'utf8');

    const checkboxBlock = cssContent.match(/\.checkbox\s*\{([^}]+)\}/);
    expect(checkboxBlock).not.toBeNull();
    const body = checkboxBlock[1];
    expect(body).toMatch(/width:\s*24px/);
    expect(body).toMatch(/height:\s*24px/);
  });

  test('JoinCohortModal provides explicit accessible label associated with input and uses Company Access Code terminology', async () => {
    const originalFetch = global.fetch;
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ solo_mode_enabled: false }),
    });

    try {
      await act(async () => {
        render(
          <JoinCohortModal sim={{ playerLogin: jest.fn(), startSoloSession: jest.fn() }} />
        );
      });

      const input = screen.getByLabelText(/Team ID \/ Company Access Code/i);
      expect(input).toBeInTheDocument();
      expect(input.id).toBe('join-player-id');

      expect(screen.getByText(/Enter the Company Access Code and password your facilitator gave you/i)).toBeInTheDocument();
    } finally {
      global.fetch = originalFetch;
    }
  });
});

describe('Adversarial Challenge 4: Z-Index Priority & Stacking Order Harmonization', () => {
  test('OVERLAY_PRIORITY constants define strict monotonicity across layers', () => {
    expect(OVERLAY_PRIORITY.TOOLTIP).toBe(9500);
    expect(OVERLAY_PRIORITY.MODAL).toBe(10000);
    expect(OVERLAY_PRIORITY.MODAL_STACKED).toBe(10001);
    expect(OVERLAY_PRIORITY.FOCUS_OVERLAY).toBe(12000);
    expect(OVERLAY_PRIORITY.ONBOARDING_TOUR).toBe(15000);
    expect(OVERLAY_PRIORITY.RESULTS_OVERLAY).toBe(18000);
    expect(OVERLAY_PRIORITY.BROADCAST_BANNER).toBe(20500);
    expect(OVERLAY_PRIORITY.ERROR_BOUNDARY).toBe(24000);

    // Stacking verification: tooltip < modal < tour < lockout results < broadcast banner
    expect(OVERLAY_PRIORITY.TOOLTIP).toBeLessThan(OVERLAY_PRIORITY.MODAL);
    expect(OVERLAY_PRIORITY.MODAL).toBeLessThan(OVERLAY_PRIORITY.ONBOARDING_TOUR);
    expect(OVERLAY_PRIORITY.ONBOARDING_TOUR).toBeLessThan(OVERLAY_PRIORITY.RESULTS_OVERLAY);
    expect(OVERLAY_PRIORITY.RESULTS_OVERLAY).toBeLessThan(OVERLAY_PRIORITY.BROADCAST_BANNER);
    expect(OVERLAY_PRIORITY.BROADCAST_BANNER).toBeLessThan(OVERLAY_PRIORITY.ERROR_BOUNDARY);
  });

  test('Page.js, Admin Facilitator, and Modals correctly import and bind OVERLAY_PRIORITY', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');
    expect(pageContent).toMatch(/zIndex:\s*OVERLAY_PRIORITY\.RESULTS_OVERLAY/);
    expect(pageContent).toMatch(/zIndex:\s*OVERLAY_PRIORITY\.MODAL/);
    expect(pageContent).toMatch(/zIndex:\s*OVERLAY_PRIORITY\.BROADCAST_BANNER/);

    const facilitatorContent = fs.readFileSync(path.join(__dirname, '../app/admin/facilitator/page.js'), 'utf8');
    expect(facilitatorContent).toMatch(/zIndex:\s*OVERLAY_PRIORITY\.BROADCAST_BANNER/);
    // Legacy 99999 z-index must be completely eliminated
    expect(facilitatorContent).not.toContain('zIndex: 99999');

    const tooltipContent = fs.readFileSync(path.join(__dirname, '../app/components/GlobalTooltip.js'), 'utf8');
    expect(tooltipContent).toMatch(/zIndex:\s*OVERLAY_PRIORITY\.TOOLTIP/);
    // Legacy 999999 z-index must be completely eliminated
    expect(tooltipContent).not.toContain('zIndex: 999999');
  });
});

describe('Adversarial Challenge 5: Server-Authoritative Round Lockout & Dynamic Fallback', () => {
  test('Page.js round lockout overlay has no client-side dismiss bypass button', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Extract the round lockout section
    const lockoutMatch = pageContent.match(/sim\.roundLocked\s*&&[\s\S]*?Round Locked[\s\S]*?<\/div>\s*\)\}/);
    expect(lockoutMatch).not.toBeNull();
    const lockoutSection = lockoutMatch[0];

    // Must NOT contain any dismiss handler that alters client state
    expect(lockoutSection).not.toMatch(/setRoundLocked\s*\(\s*false\s*\)/);
    expect(lockoutSection).not.toMatch(/sim\.setRoundLocked\s*\(\s*false\s*\)/);
    expect(lockoutSection).not.toMatch(/<button[^>]*>Dismiss<\/button>/i);
  });

  test('Page.js dynamic imports use ModuleLoadingSkeleton with WCAG accessibility attributes', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Verify ModuleLoadingSkeleton definition
    expect(pageContent).toContain('const ModuleLoadingSkeleton =');
    expect(pageContent).toContain('role="status"');
    expect(pageContent).toContain('aria-busy="true"');
    expect(pageContent).toContain('Loading simulation module…');
    expect(pageContent).toContain('Initializing Muressons workspace');

    // Verify it replaced FullScreenLoader
    expect(pageContent).not.toMatch(/const FullScreenLoader =/);
    expect(pageContent).toMatch(/loading:\s*ModuleLoadingSkeleton/);
  });
});

describe('Adversarial Challenge 6: Onboarding Copy Accuracy & Role Model Verification', () => {
  test('OnboardingWizard does not promise PDF exports and accurately describes 5-tier role hierarchy', () => {
    const wizardContent = fs.readFileSync(path.join(__dirname, '../app/components/OnboardingWizard.js'), 'utf8');

    // Must NOT promise PDF dossiers/export
    expect(wizardContent).not.toMatch(/PDF\s+dossiers/i);
    expect(wizardContent).not.toMatch(/CSV\/PDF/i);

    // Must accurately mention CSV and JSON
    expect(wizardContent).toMatch(/CSV/);
    expect(wizardContent).toMatch(/JSON/);

    // Must describe 5-tier role hierarchy
    expect(wizardContent).toMatch(/5-tier/i);
    expect(wizardContent).toMatch(/God Mode/);
    expect(wizardContent).toMatch(/Super Admin/);
    expect(wizardContent).toMatch(/Lead Facilitator/);
    expect(wizardContent).toMatch(/Facilitator/);
    expect(wizardContent).toMatch(/Provisioning Admin/);
  });

  test('Admin Facilitator displays dedicated badge for project_admin', () => {
    const facilitatorContent = fs.readFileSync(path.join(__dirname, '../app/admin/facilitator/page.js'), 'utf8');

    expect(facilitatorContent).toMatch(/authData\?\.role === 'project_admin' \? '📁 Provisioning Admin'/);
  });
});

describe('Adversarial Challenge 7: Pre-Round 1 Waiting Lobby Lifecycle & Unmounting Stress Test', () => {
  const Page = require('../app/page.js').default;

  beforeEach(() => {
    jest.useFakeTimers();
    mockSim.sessionId = 'sess-m3-lobby';
    mockSim.username = 'Phoebe';
    mockSim.roundNumber = 1;
    mockSim.mustChangePassword = false;
    mockSim.connectionState = 'ok';
    mockSim.sessionMeta = { status: 'waiting', cohort_name: 'Titan Strategic Cohort' };
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('Pre-Round 1 Waiting Lobby renders when sessionMeta.status is waiting at round 1', () => {
    render(<Page />);

    expect(screen.getByText('Cohort Waiting Lobby')).toBeInTheDocument();
    expect(screen.getByText('Phoebe')).toBeInTheDocument();
    expect(screen.getByText('Titan Strategic Cohort')).toBeInTheDocument();
    expect(screen.getByText('Waiting for Facilitator Launch')).toBeInTheDocument();

    // Briefing and Cockpit must NOT be mounted while waiting
    expect(screen.queryByTestId('briefing')).toBeNull();
    expect(screen.queryByTestId('cockpit')).toBeNull();
  });

  test('Pre-Round 1 Waiting Lobby UNMOUNTS when sessionMeta.status transitions from waiting to active', () => {
    const { rerender } = render(<Page />);

    // Initially in lobby
    expect(screen.getByText('Cohort Waiting Lobby')).toBeInTheDocument();
    expect(screen.queryByTestId('briefing')).toBeNull();

    // Facilitator initiates round 1 -> status transitions to 'active'
    act(() => {
      mockSim.sessionMeta = { status: 'active', cohort_name: 'Titan Strategic Cohort' };
    });
    rerender(<Page />);

    // Waiting lobby must be completely unmounted from the DOM
    expect(screen.queryByText('Cohort Waiting Lobby')).toBeNull();
    expect(screen.queryByText('Waiting for Facilitator Launch')).toBeNull();

    // Round briefing mounts cleanly in place of the lobby
    expect(screen.getByTestId('briefing')).toBeInTheDocument();
  });

  test('Pre-Round 1 Waiting Lobby never mounts if roundNumber > 1 even if status is waiting', () => {
    mockSim.roundNumber = 2;
    mockSim.sessionMeta = { status: 'waiting', cohort_name: 'Titan Strategic Cohort' };

    render(<Page />);

    expect(screen.queryByText('Cohort Waiting Lobby')).toBeNull();
    expect(screen.getByTestId('briefing')).toBeInTheDocument();
  });

  test('Pre-Round 1 Waiting Lobby does not mount if username or sessionId is missing', () => {
    mockSim.username = '';
    const { rerender } = render(<Page />);
    expect(screen.queryByText('Cohort Waiting Lobby')).toBeNull();

    mockSim.username = 'Phoebe';
    mockSim.sessionId = '';
    rerender(<Page />);
    expect(screen.queryByText('Cohort Waiting Lobby')).toBeNull();
  });

  test('Polling lifecycle: page.js sets up 5-second poll while status is waiting', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Assert polling interval in page.js
    expect(pageContent).toContain("if (sim.sessionMeta?.status === 'waiting') {");
    expect(pageContent).toContain('fetchAssignedBu();');
    expect(pageContent).toContain('}, 5000);');
    expect(pageContent).toContain('clearInterval(interval)');
  });
});

describe('Adversarial Challenge 8: Waiting Lobby Connection Indicator Dynamic Transitions & Hex Conformance', () => {
  const Page = require('../app/page.js').default;

  beforeEach(() => {
    jest.useFakeTimers();
    mockSim.sessionId = 'sess-m3-lobby';
    mockSim.username = 'Phoebe';
    mockSim.roundNumber = 1;
    mockSim.mustChangePassword = false;
    mockSim.sessionMeta = { status: 'waiting', cohort_name: 'Titan Strategic Cohort' };
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('Connection indicator reflects "ok" state with positive design tokens', () => {
    mockSim.connectionState = 'ok';
    render(<Page />);

    const badge = screen.getByText('Waiting for Facilitator Launch');
    expect(badge).toBeInTheDocument();
    expect(badge.style.background).toBe('var(--positive-soft)');
    expect(badge.style.color).toBe('var(--positive)');
    expect(badge.style.border).toContain('rgba(34, 197, 94, 0.3)');

    const dot = badge.querySelector('span');
    expect(dot).not.toBeNull();
    expect(dot.style.background).toBe('var(--positive)');
  });

  test('Connection indicator dynamically transitions to "degraded" and "stale" with caution design tokens', () => {
    mockSim.connectionState = 'degraded';
    const { rerender } = render(<Page />);

    let badge = screen.getByText('Connection Degraded — Reconnecting…');
    expect(badge).toBeInTheDocument();
    expect(badge.style.background).toBe('var(--caution-soft)');
    expect(badge.style.color).toBe('var(--caution)');
    expect(badge.style.border).toContain('rgba(245, 158, 11, 0.3)');

    let dot = badge.querySelector('span');
    expect(dot).not.toBeNull();
    expect(dot.style.background).toBe('var(--caution)');

    // Test stale state
    act(() => {
      mockSim.connectionState = 'stale';
    });
    rerender(<Page />);

    badge = screen.getByText('Connection Degraded — Reconnecting…');
    expect(badge).toBeInTheDocument();
    expect(badge.style.background).toBe('var(--caution-soft)');
  });

  test('Connection indicator dynamically transitions to "offline" with danger design tokens', () => {
    mockSim.connectionState = 'offline';
    render(<Page />);

    const badge = screen.getByText('Offline — Reconnecting…');
    expect(badge).toBeInTheDocument();
    expect(badge.style.background).toBe('var(--danger-soft)');
    expect(badge.style.color).toBe('var(--danger)');
    expect(badge.style.border).toContain('rgba(239, 68, 68, 0.3)');

    const dot = badge.querySelector('span');
    expect(dot).not.toBeNull();
    expect(dot.style.background).toBe('var(--danger)');
  });

  test('Strict token audit: Pre-Round 1 Waiting Lobby has ZERO hardcoded semantic hex codes or black flashes', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Extract the lobby block in page.js
    const lobbyMatch = pageContent.match(/Pre-Round 1 Waiting Lobby[\s\S]*?Cohort Waiting Lobby[\s\S]*?<\/div>\s*\)\s*;\s*\}/);
    expect(lobbyMatch).not.toBeNull();
    const lobbyBlock = lobbyMatch[0];

    // Semantic raw hex pattern
    const SEMANTIC_HEX_REGEX = /#(?:10b981|22c55e|4ade80|34d399|059669|16a34a|86efac|6ee7b7|a7f3d0|0a7d3c|15803d|047857|ef4444|f87171|dc2626|b91c1c|fca5a5|b42318|450a0a|f59e0b|fbbf24|fcd34d|d97706|a16207|b45309|92400e|3b82f6|080c18)\b/gi;

    const matches = lobbyBlock.match(SEMANTIC_HEX_REGEX) || [];
    expect(matches).toEqual([]);

    // Verify token usage
    expect(lobbyBlock).toContain("background: 'var(--bg-primary)'");
    expect(lobbyBlock).toContain("background: 'var(--bg-card)'");
    expect(lobbyBlock).toContain("border: '1px solid var(--border-subtle)'");
    expect(lobbyBlock).toContain("color: 'var(--text-primary)'");
    expect(lobbyBlock).toContain("color: 'var(--text-secondary)'");
    expect(lobbyBlock).toContain("fontSize: 'var(--type-caption)'");
    expect(lobbyBlock).toContain('zIndex: OVERLAY_PRIORITY.MODAL');
  });
});

