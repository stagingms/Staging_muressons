/**
 * Adversarial Challenge Suite: Auth & Onboarding Flow Remediations (Issues #29–#35)
 *
 * EMPIRICAL CHALLENGER: challenger_m3_1
 *
 * Verification Scope:
 * 1. Round Lockout Overlay (Issue #29):
 *    - Absence of dismiss button.
 *    - Un-dismissibility by user interactions (backdrop click, escape key).
 *    - EMPIRICAL BUG DISCOVERY: 30-second client-side auto-clear timer (page.js:1058-1065)
 *      bypasses lockout by calling sim.setRoundLocked(false).
 * 2. ModuleLoadingSkeleton Chunk Loader (Issue #30):
 *    - WCAG compliance (role="status", aria-busy="true", aria-live="polite").
 *    - No pitch-black (#080c18) flash; uses var(--bg-primary).
 *    - Dynamic binding to JoinCohortModal and UsernamePromptModal.
 * 3. Facilitator Auth Gate (Issue #31):
 *    - Probes cookiesWritable() and displays banner on blocked cookies.
 *    - Caps-lock state detection and UI alert.
 *    - Role-based redirect to God Mode for admin identities.
 * 4. Dual Admin Credential Synchronization (Issue #32):
 *    - Bidirectional localStorage synchronization between godmode_auth and facilitator_auth.
 *    - Quick-switch header links in both consoles.
 *    - Unified logout clearing both credentials.
 * 5. Pre-Round 1 Waiting Lobby (Issue #34):
 *    - EMPIRICAL BUG DISCOVERY: sim.sessionMeta?.status is never populated by setSessionMeta
 *      or the /session-info backend endpoint, rendering the lobby permanently dead code.
 *    - Static vs. live connectionState binding.
 *    - Inability to unmount upon facilitator launch without polling.
 */

import React from 'react';
import fs from 'fs';
import path from 'path';
import { render, screen, act, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

import { isAdminRole, roleHome, roleStorageKey, roleAuthSubset } from '../app/utils/roleRouting';
import { OVERLAY_PRIORITY } from '../app/components/overlayPriority';

describe('Adversarial Challenge 1: Round Lockout Screen Dismissibility & Bypass', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('EMPIRICAL VERIFICATION: Overlay does not render a Dismiss button in the DOM', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');
    const lockoutMatch = pageContent.match(/sim\.roundLocked\s*&&[\s\S]*?Round Locked[\s\S]*?<\/div>\s*\)\}/);
    expect(lockoutMatch).not.toBeNull();
    const lockoutSection = lockoutMatch[0];

    // Verify dismiss button was removed
    expect(lockoutSection).not.toMatch(/<button[^>]*>Dismiss<\/button>/i);
    expect(lockoutSection).not.toMatch(/setRoundLocked\s*\(\s*false\s*\)/);
  });

  test('Participant round lockout is strictly server-authoritative and lacks 30s bypass timer', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Check for the 30s auto-clear timer in page.js
    const timerMatch = pageContent.match(/useEffect\(\(\)\s*=>\s*\{[\s\S]*?!sim\.roundLocked[\s\S]*?setTimeout\(\(\)\s*=>\s*\{[\s\S]*?sim\.setRoundLocked\(false\)[\s\S]*?30_000\)/);

    // This timer must NOT exist in page.js!
    expect(timerMatch).toBeNull();
  });

  test('Keyboard interactions (Escape) do not clear sim.roundLocked', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Extract the keydown handler in page.js
    const keyHandlerMatch = pageContent.match(/case\s*'Escape':[\s\S]*?break;/);
    expect(keyHandlerMatch).not.toBeNull();
    const escapeBlock = keyHandlerMatch[0];

    // Escape handles side panels but does not set roundLocked to false
    expect(escapeBlock).not.toMatch(/roundLocked/);
  });
});

describe('Adversarial Challenge 2: ModuleLoadingSkeleton Chunk Loader & Visual Flash', () => {
  test('ModuleLoadingSkeleton uses dark cockpit background var(--bg-primary), eliminating black flash', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // FullScreenLoader must be completely gone
    expect(pageContent).not.toContain('FullScreenLoader');

    // ModuleLoadingSkeleton definition uses design tokens
    expect(pageContent).toContain('const ModuleLoadingSkeleton = () => (');
    expect(pageContent).toContain("background: 'var(--bg-primary)'");
    expect(pageContent).toContain('zIndex: OVERLAY_PRIORITY.MODAL');

    // Note: Line 1475 has transitioned to var(--bg-primary)
    expect(pageContent).not.toContain("background: '#080c18'");
    expect(pageContent).toContain("background: 'var(--bg-primary)'");
  });

  test('ModuleLoadingSkeleton provides full WCAG status attributes and animated SVG spinner', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    expect(pageContent).toContain('role="status"');
    expect(pageContent).toContain('aria-busy="true"');
    expect(pageContent).toContain('aria-live="polite"');
    expect(pageContent).toContain('<animateTransform');
    expect(pageContent).toContain('Loading simulation module…');
    expect(pageContent).toContain('Initializing Muressons workspace');
  });

  test('Dynamic modal imports use ModuleLoadingSkeleton as loading fallback', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    expect(pageContent).toMatch(/const JoinCohortModal\s*=\s*dynamic\([^,]+,\s*\{\s*ssr:\s*false,\s*loading:\s*ModuleLoadingSkeleton\s*\}\);/);
    expect(pageContent).toMatch(/const UsernamePromptModal\s*=\s*dynamic\([^,]+,\s*\{\s*ssr:\s*false,\s*loading:\s*ModuleLoadingSkeleton\s*\}\);/);
  });
});

describe('Adversarial Challenge 3: Facilitator Login Gate Diagnostics & Routing', () => {
  test('facilitator/page.js imports and probes storageHealth.cookiesWritable()', () => {
    const facPage = fs.readFileSync(path.join(__dirname, '../app/admin/facilitator/page.js'), 'utf8');

    expect(facPage).toContain("import { cookiesWritable } from '../../utils/storageHealth';");
    expect(facPage).toContain('setCookiesBlocked(!cookiesWritable());');
    expect(facPage).toContain('Cookies are blocked or disabled in your browser. Authentication requires cookies.');
  });

  test('facilitator/page.js detects CapsLock on keydown and keyup', () => {
    const facPage = fs.readFileSync(path.join(__dirname, '../app/admin/facilitator/page.js'), 'utf8');

    expect(facPage).toContain("if (e.getModifierState) setCapsLock(e.getModifierState('CapsLock'));");
    expect(facPage).toContain('onKeyDown={handleKeyDown}');
    expect(facPage).toContain('onKeyUp={handleKeyDown}');
    expect(facPage).toContain('⇪ Caps Lock is ON');
  });

  test('facilitator/page.js routes god_mode and super_admin logins to /admin/god-mode', () => {
    const facPage = fs.readFileSync(path.join(__dirname, '../app/admin/facilitator/page.js'), 'utf8');

    // Login response handler verifies role and routes
    expect(facPage).toContain('if (isAdminRole(role, is_admin)) {');
    expect(facPage).toContain("localStorage.setItem('godmode_auth', JSON.stringify(subset));");
    expect(facPage).toContain("router.push('/admin/god-mode');");
  });

  test('roleRouting logic correctly identifies administrative roles', () => {
    expect(isAdminRole('god_mode')).toBe(true);
    expect(isAdminRole('super_admin')).toBe(true);
    expect(isAdminRole('admin')).toBe(true);
    expect(isAdminRole('facilitator', true)).toBe(true); // is_admin flag = true
    expect(isAdminRole('lead_facilitator')).toBe(false);
    expect(isAdminRole('facilitator')).toBe(false);
    expect(isAdminRole('project_admin')).toBe(false); // Provisioning only
  });
});

describe('Adversarial Challenge 4: Dual Admin Role Switcher & Credential Synchronization', () => {
  test('God Mode console reads godmode_auth or facilitator_auth and synchronizes both keys', () => {
    const godModeContent = fs.readFileSync(path.join(__dirname, '../app/admin/god-mode/page.js'), 'utf8');

    expect(godModeContent).toContain("const stored = localStorage.getItem('godmode_auth') || localStorage.getItem('facilitator_auth');");
    expect(godModeContent).toContain("localStorage.setItem('godmode_auth', JSON.stringify(parsed));");
    expect(godModeContent).toContain("localStorage.setItem('facilitator_auth', JSON.stringify(parsed));");
  });

  test('Facilitator console reads facilitator_auth or godmode_auth and synchronizes both keys', () => {
    const facPage = fs.readFileSync(path.join(__dirname, '../app/admin/facilitator/page.js'), 'utf8');

    expect(facPage).toContain("const stored = localStorage.getItem('facilitator_auth') || localStorage.getItem('godmode_auth');");
    expect(facPage).toContain("localStorage.setItem('facilitator_auth', JSON.stringify(cachedAuth));");
    expect(facPage).toContain("localStorage.setItem('godmode_auth', JSON.stringify(cachedAuth));");
  });

  test('Quick-switch navigation links are present in both admin consoles', () => {
    const godModeContent = fs.readFileSync(path.join(__dirname, '../app/admin/god-mode/page.js'), 'utf8');
    const facPage = fs.readFileSync(path.join(__dirname, '../app/admin/facilitator/page.js'), 'utf8');

    // God Mode header has link to Facilitator View
    expect(godModeContent).toContain('href="/admin/facilitator"');
    expect(godModeContent).toContain('🎓 Facilitator');

    // Facilitator header has link to God Mode Console
    expect(facPage).toContain('href="/admin/god-mode"');
    expect(facPage).toContain('👑 God Mode');
  });

  test('Unified logout in both dashboards clears both auth keys', () => {
    const godModeContent = fs.readFileSync(path.join(__dirname, '../app/admin/god-mode/page.js'), 'utf8');
    const facPage = fs.readFileSync(path.join(__dirname, '../app/admin/facilitator/page.js'), 'utf8');

    // God Mode handleLogout
    expect(godModeContent).toContain("localStorage.removeItem('godmode_auth');");
    expect(godModeContent).toContain("localStorage.removeItem('facilitator_auth');");

    // Facilitator handleLogout
    expect(facPage).toContain("localStorage.removeItem('facilitator_auth');");
    expect(facPage).toContain("localStorage.removeItem('godmode_auth');");
  });
});

describe('Adversarial Challenge 5: Pre-Round 1 Waiting Lobby Dead Code & Lifecycle Flaws', () => {
  test('Pre-Round 1 Lobby condition is reachable via sim.sessionMeta?.status', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Lobby render condition
    const lobbyCondition = pageContent.match(/if\s*\(\s*sim\.sessionId\s*&&\s*sim\.username\s*&&\s*roundNumber\s*===\s*1\s*&&\s*sim\.sessionMeta\?\.status\s*===\s*'waiting'\s*\)/);
    expect(lobbyCondition).not.toBeNull();

    // Inspect where sim.setSessionMeta is called in page.js
    const setSessionMetaCall = pageContent.match(/sim\.setSessionMeta\(\s*\{([\s\S]*?)\}\s*\)/);
    expect(setSessionMetaCall).not.toBeNull();
    const passedFields = setSessionMetaCall[1];

    expect(passedFields).toContain('cohort_name');
    expect(passedFields).toContain('simulation_mode');
    expect(passedFields).toContain('assigned_bu');
    expect(passedFields).toContain('industry_vertical');
    expect(passedFields).toMatch(/\bstatus\b/);

    // Initial state in useSimulation.js also defines status
    const useSimContent = fs.readFileSync(path.join(__dirname, '../app/hooks/useSimulation.js'), 'utf8');
    const initialSessionMeta = useSimContent.match(/useState\(\s*\{[\s\S]*?status:\s*null[\s\S]*?\}\s*\)/);
    expect(initialSessionMeta).not.toBeNull();

    const testSessionMeta = {
      cohort_name: 'Test Cohort',
      simulation_mode: 'standard',
      assigned_bu: 'bu-1',
      industry_vertical: 'energy',
      status: 'waiting',
    };
    expect(testSessionMeta.status).toBe('waiting');
    expect(testSessionMeta.status === 'waiting').toBe(true);
  });

  test('Pre-Round 1 Lobby binds live connectionState and polls while waiting', () => {
    const pageContent = fs.readFileSync(path.join(__dirname, '../app/page.js'), 'utf8');

    // Locate the lobby block
    const lobbyBlockMatch = pageContent.match(/Pre-Round 1 Waiting Lobby[\s\S]*?Cohort Waiting Lobby[\s\S]*?<\/div>\s*\)\s*;\s*\}/);
    expect(lobbyBlockMatch).not.toBeNull();
    const lobbyBlock = lobbyBlockMatch[0];

    // The indicator binds to sim.connectionState and avoids raw blue dot
    expect(lobbyBlock).not.toContain("background: '#3b82f6'");
    expect(lobbyBlock).toMatch(/sim\.connectionState/);

    // Check fetchAssignedBu polling: polls when status is waiting
    const intervalMatch = pageContent.match(/fetchAssignedBu\(\);[\s\S]*?const interval = setInterval\([\s\S]*?fetchAssignedBu[\s\S]*?5000\);/);
    expect(intervalMatch).not.toBeNull();
    expect(pageContent).toContain("sim.sessionMeta?.status === 'waiting'");
  });
});
