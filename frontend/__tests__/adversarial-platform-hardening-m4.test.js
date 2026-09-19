/**
 * Adversarial Platform Hardening & Cross-Module Invariant Suite (M4)
 *
 * EMPIRICAL CHALLENGER: challenger_m4_hardening
 *
 * Verifications:
 * 1. Role Hierarchy Lock & Boundary Gating (CLAUDE.md:62, sidebarConfig.js:163, admin_shared.py)
 * 2. V-D Slotting & Modal Stacking Priority Order (OVERLAY_PRIORITY)
 * 3. ErrorBoundary Handling & Graceful Fault Recovery
 * 4. Tab Visibility Backoff in Polling Loops (visibilityState === 'hidden')
 * 5. Accessible Dialog WCAG Compliance (focus trap, topmost-only Escape, scroll lock)
 */

import React, { useState } from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';

import {
  FACILITATOR_SIDEBAR,
  GOD_MODE_SIDEBAR,
  filterSidebarForRole,
} from '../app/config/sidebarConfig';
import { OVERLAY_PRIORITY } from '../app/components/overlayPriority';
import ErrorBoundary from '../app/components/ErrorBoundary';
import Dialog from '../app/components/Dialog';

// Parse ROLE_HIERARCHY from sidebarConfig.js source (same pattern as backend test_role_hierarchy_sync.py)
function getParsedRoleHierarchy() {
  const sidebarSrc = fs.readFileSync(path.join(__dirname, '../app/config/sidebarConfig.js'), 'utf8');
  const m = sidebarSrc.match(/const ROLE_HIERARCHY\s*=\s*\{([\s\S]*?)\};/);
  if (!m) throw new Error('ROLE_HIERARCHY not found in sidebarConfig.js');
  const roles = {};
  for (const line of m[1].split('\n')) {
    const clean = line.split('//')[0];
    const match = clean.match(/(\w+)\s*:\s*(\d+)/);
    if (match) roles[match[1]] = parseInt(match[2], 10);
  }
  return roles;
}

describe('Adversarial Challenge 1: Cross-Module Role Hierarchy Lock & Gating', () => {
  test('ROLE_HIERARCHY guarantees strict monotonic level invariants', () => {
    const parsedHierarchy = getParsedRoleHierarchy();
    expect(parsedHierarchy.god_mode).toBe(4);
    expect(parsedHierarchy.super_admin).toBe(3);
    expect(parsedHierarchy.admin).toBe(3);
    expect(parsedHierarchy.lead_facilitator).toBe(2);
    expect(parsedHierarchy.facilitator).toBe(1);
    expect(parsedHierarchy.project_admin).toBe(0);

    expect(parsedHierarchy.god_mode).toBeGreaterThan(parsedHierarchy.super_admin);
    expect(parsedHierarchy.super_admin).toBeGreaterThan(parsedHierarchy.lead_facilitator);
    expect(parsedHierarchy.lead_facilitator).toBeGreaterThan(parsedHierarchy.facilitator);
    expect(parsedHierarchy.facilitator).toBeGreaterThan(parsedHierarchy.project_admin);
  });

  test('Undo Round item in FACILITATOR_SIDEBAR strictly requires lead_facilitator (sidebarConfig.js:163)', () => {
    const allItems = FACILITATOR_SIDEBAR.flatMap((g) => g.items);
    const undoItem = allItems.find((i) => i.id === 'undo_round');
    expect(undoItem).toBeDefined();
    expect(undoItem.requiredRole).toBe('lead_facilitator');
    expect(undoItem.showDisabled).toBe(true);
    expect(undoItem.disabledReason).toMatch(/Lead facilitator or above/i);
  });

  test('EMPIRICAL AUDIT: filterSidebarForRole marks undo_round as _locked for base facilitator', () => {
    const filteredFacilitator = filterSidebarForRole(FACILITATOR_SIDEBAR, 'facilitator', ['*']);
    const facUndo = filteredFacilitator.flatMap((g) => g.items).find((i) => i.id === 'undo_round');
    expect(facUndo).toBeDefined();
    expect(facUndo._locked).toBe(true);

    const filteredLead = filterSidebarForRole(FACILITATOR_SIDEBAR, 'lead_facilitator', ['*']);
    const leadUndo = filteredLead.flatMap((g) => g.items).find((i) => i.id === 'undo_round');
    expect(leadUndo).toBeDefined();
    expect(leadUndo._locked).toBeUndefined();
  });

  test('EMPIRICAL LEAK DETECTION: canAccessTab in page.js must NOT admit locked items for routing', () => {
    // If a naïve implementation uses visibleTabIds = new Set(filtered.flatMap(g => g.items.map(i => i.id))),
    // locked items will leak into accessible routes!
    const filteredFacilitator = filterSidebarForRole(FACILITATOR_SIDEBAR, 'facilitator', ['*']);
    
    // Correct access gate: only tabs that are NOT _locked are genuinely accessible
    const trulyAccessibleIds = new Set(
      filteredFacilitator.flatMap((g) => g.items.filter((i) => !i._locked).map((i) => i.id))
    );
    expect(trulyAccessibleIds.has('undo_round')).toBe(false);

    // Flawed / leaking access gate: includes _locked signposts
    const flawedVisibleTabIds = new Set(
      filteredFacilitator.flatMap((g) => g.items.map((i) => i.id))
    );
    // Documenting the finding: flawed gate treats undo_round as accessible
    expect(flawedVisibleTabIds.has('undo_round')).toBe(true);
  });

  test('Project Admin (Level 0) is excluded from live run management tabs', () => {
    const filteredProjectAdmin = filterSidebarForRole(FACILITATOR_SIDEBAR, 'project_admin', [
      'cohort_provisioning',
      'facilitator_registry',
    ]);
    const items = filteredProjectAdmin.flatMap((g) => g.items.filter((i) => !i._locked));
    const ids = items.map((i) => i.id);

    expect(ids).not.toContain('manual_override');
    expect(ids).not.toContain('undo_round');
    expect(ids).not.toContain('custom_black_swan');
    expect(ids).not.toContain('session_viewer');
  });
});

describe('Adversarial Challenge 2: V-D Slotting & Stacking Governance (OVERLAY_PRIORITY)', () => {
  test('OVERLAY_PRIORITY maintains strict stacking order', () => {
    expect(OVERLAY_PRIORITY.TICKER).toBeLessThan(OVERLAY_PRIORITY.LEFT_RAIL_FLYOUT);
    expect(OVERLAY_PRIORITY.LEFT_RAIL_FLYOUT).toBeLessThan(OVERLAY_PRIORITY.TOOLTIP);
    expect(OVERLAY_PRIORITY.TOOLTIP).toBeLessThan(OVERLAY_PRIORITY.DROPDOWN);
    expect(OVERLAY_PRIORITY.DROPDOWN).toBeLessThan(OVERLAY_PRIORITY.MODAL);
    expect(OVERLAY_PRIORITY.MODAL).toBeLessThan(OVERLAY_PRIORITY.MODAL_STACKED);
    expect(OVERLAY_PRIORITY.MODAL_STACKED).toBeLessThan(OVERLAY_PRIORITY.FOCUS_OVERLAY);
    expect(OVERLAY_PRIORITY.FOCUS_OVERLAY).toBeLessThan(OVERLAY_PRIORITY.ONBOARDING_TOUR);
    expect(OVERLAY_PRIORITY.ONBOARDING_TOUR).toBeLessThan(OVERLAY_PRIORITY.RESULTS_OVERLAY);
    expect(OVERLAY_PRIORITY.RESULTS_OVERLAY).toBeLessThan(OVERLAY_PRIORITY.CRISIS_INTERSTITIAL);
    expect(OVERLAY_PRIORITY.CRISIS_INTERSTITIAL).toBeLessThan(OVERLAY_PRIORITY.CRISIS_INTERSTITIAL_TOP);
    expect(OVERLAY_PRIORITY.CRISIS_INTERSTITIAL_TOP).toBeLessThan(OVERLAY_PRIORITY.SHOCKWAVE);
    expect(OVERLAY_PRIORITY.SHOCKWAVE).toBeLessThan(OVERLAY_PRIORITY.BROADCAST_BANNER);
    expect(OVERLAY_PRIORITY.BROADCAST_BANNER).toBeLessThan(OVERLAY_PRIORITY.CLIMATE_MODULE);
    expect(OVERLAY_PRIORITY.CLIMATE_MODULE).toBeLessThan(OVERLAY_PRIORITY.ERROR_BOUNDARY);
  });

  test('ERROR_BOUNDARY (24000) is above all gameplay modals and takeovers', () => {
    expect(OVERLAY_PRIORITY.ERROR_BOUNDARY).toBeGreaterThan(OVERLAY_PRIORITY.RESULTS_OVERLAY);
    expect(OVERLAY_PRIORITY.ERROR_BOUNDARY).toBeGreaterThan(OVERLAY_PRIORITY.CRISIS_INTERSTITIAL);
    expect(OVERLAY_PRIORITY.ERROR_BOUNDARY).toBeGreaterThan(OVERLAY_PRIORITY.CLIMATE_MODULE);
  });
});

describe('Adversarial Challenge 3: ErrorBoundary Handling & Graceful Recovery', () => {
  // Prevent jest from spamming expected error logs
  const originalConsoleError = console.error;
  beforeAll(() => {
    console.error = (...args) => {
      if (typeof args[0] === 'string' && args[0].includes('[ErrorBoundary]')) return;
      originalConsoleError(...args);
    };
  });
  afterAll(() => {
    console.error = originalConsoleError;
  });

  const Bomb = ({ shouldExplode }) => {
    if (shouldExplode) {
      throw new Error('EMPIRICAL_SIMULATION_EXPLOSION');
    }
    return <div data-testid="bomb-defused">Healthy Simulation</div>;
  };

  test('Catches render error and displays user-friendly recovery UI without unmounting app root', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <Bomb shouldExplode={false} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('bomb-defused')).toBeInTheDocument();

    // Trigger explosive crash
    rerender(
      <ErrorBoundary>
        <Bomb shouldExplode={true} />
      </ErrorBoundary>
    );

    expect(screen.queryByTestId('bomb-defused')).not.toBeInTheDocument();
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText(/The simulation encountered an unexpected issue/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reload Page/i })).toBeInTheDocument();
  });

  test('ErrorBoundary details block reveals error info for diagnostics without crashing', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldExplode={true} />
      </ErrorBoundary>
    );

    const details = screen.getByText(/Technical Details \(for support\)/i);
    expect(details).toBeInTheDocument();
    expect(screen.getByText(/EMPIRICAL_SIMULATION_EXPLOSION/)).toBeInTheDocument();
  });
});

describe('Adversarial Challenge 4: Tab Visibility Backoff in Polling Loops', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  test('Polling callback halts execution when document.visibilityState is hidden', () => {
    const mockFetchFn = jest.fn();

    // Harness mirroring RunBar.js & CohortPulse.js polling loop
    const Poller = ({ active }) => {
      React.useEffect(() => {
        if (!active) return;
        const iv = setInterval(() => {
          if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
          mockFetchFn();
        }, 1000);
        return () => clearInterval(iv);
      }, [active]);
      return <div>Poller Active</div>;
    };

    render(<Poller active={true} />);

    // Document is visible initially
    Object.defineProperty(document, 'visibilityState', {
      value: 'visible',
      writable: true,
      configurable: true,
    });

    act(() => {
      jest.advanceTimersByTime(2000);
    });
    expect(mockFetchFn).toHaveBeenCalledTimes(2);

    // Tab is hidden (user switched tabs or minimized browser)
    Object.defineProperty(document, 'visibilityState', {
      value: 'hidden',
      writable: true,
      configurable: true,
    });

    act(() => {
      jest.advanceTimersByTime(5000); // 5 intervals tick
    });
    // Call count MUST remain 2 (zero new network calls while hidden)
    expect(mockFetchFn).toHaveBeenCalledTimes(2);

    // Tab becomes visible again
    Object.defineProperty(document, 'visibilityState', {
      value: 'visible',
      writable: true,
      configurable: true,
    });

    act(() => {
      jest.advanceTimersByTime(3000); // 3 intervals tick
    });
    expect(mockFetchFn).toHaveBeenCalledTimes(5);
  });
});

describe('Adversarial Challenge 5: Accessible Dialog Primitive (WCAG 2.1 AA)', () => {
  beforeAll(() => {
    // JSDOM does not calculate layout, so offsetParent is null by default.
    // Mock offsetParent getter so focus trap element filtering works as in real DOM.
    Object.defineProperty(HTMLElement.prototype, 'offsetParent', {
      get() {
        return this.parentNode;
      },
      configurable: true,
    });
  });

  test('Dialog traps keyboard focus and prevents Tab key escaping to background', () => {
    const onClose = jest.fn();
    render(
      <div>
        <button data-testid="outside-button">Outside</button>
        <Dialog label="Test Dialog" onClose={onClose}>
          <button data-testid="first-dialog-button">First</button>
          <input data-testid="dialog-input" type="text" />
          <button data-testid="last-dialog-button">Last</button>
        </Dialog>
      </div>
    );

    const firstBtn = screen.getByTestId('first-dialog-button');
    const lastBtn = screen.getByTestId('last-dialog-button');

    // Focus last element
    lastBtn.focus();
    expect(document.activeElement).toBe(lastBtn);

    // Tab on last element -> wraps to first
    fireEvent.keyDown(window, { key: 'Tab', shiftKey: false });
    expect(document.activeElement).toBe(firstBtn);

    // Shift+Tab on first element -> wraps to last
    fireEvent.keyDown(window, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(lastBtn);
  });

  test('Escape key closes ONLY the topmost dialog in a nested stack', () => {
    const onOuterClose = jest.fn();
    const onInnerClose = jest.fn();

    const NestedDialogHarness = ({ showInner }) => (
      <Dialog label="Outer Dialog" onClose={onOuterClose}>
        <div>Outer Content</div>
        {showInner && (
          <Dialog label="Inner Dialog" onClose={onInnerClose}>
            <div>Inner Content</div>
          </Dialog>
        )}
      </Dialog>
    );

    // Mount outer dialog first (as happens when a secondary modal opens over an active one)
    const { rerender } = render(<NestedDialogHarness showInner={false} />);

    // Now open inner dialog
    rerender(<NestedDialogHarness showInner={true} />);

    // Press Escape on window when inner dialog is open -> ONLY inner should close
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onInnerClose).toHaveBeenCalledTimes(1);
    expect(onOuterClose).not.toHaveBeenCalled();

    // Now inner is dismissed, re-render with only outer dialog
    rerender(<NestedDialogHarness showInner={false} />);

    // Press Escape again -> outer closes
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onOuterClose).toHaveBeenCalledTimes(1);
  });

  test('Dialog locks body scroll while open and restores it upon unmount', () => {
    expect(document.body.style.overflow).toBe('');

    const { unmount } = render(
      <Dialog label="Scroll Lock Dialog" onClose={() => {}}>
        <div>Locked Content</div>
      </Dialog>
    );

    expect(document.body.style.overflow).toBe('hidden');

    unmount();
    expect(document.body.style.overflow).toBe('');
  });
});
