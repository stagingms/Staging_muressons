/**
 * The god-mode console can choose a cohort's paradigm.
 *
 * Found setting up the 2026-09 classroom cohort on production: signed in as
 * god_mode, the Set Up Cohort form showed sections 1, 5, 6 and 7 only. The
 * "2. Simulation Engine" accordion (decision paradigm, ending pathway), "2b",
 * "3. Optional Modules" and "4. Team Interventions" were missing, the summary's
 * "✎ Edit" for them opened nothing, and the cohort was created as Narrative
 * Crises. CreateCohortModal decided "is this an admin?" with
 * `role === 'super_admin' || role === 'admin'` — the exact string comparison
 * CLAUDE.md's role model forbids in the backend ("god_mode ≥ super_admin by
 * level, so use the level, not the string") — so god_mode fell into the
 * base-facilitator branch. The modal now asks roleRouting.isAdminRole, the
 * frontend's mirror of admin_shared.is_admin_role.
 *
 * Rendered, not regexed: the section must be in the DOM for god_mode exactly
 * as it is for super_admin, and stay absent for a base facilitator.
 */
import React from 'react';
import { render, act, waitFor, fireEvent } from '@testing-library/react';
import CreateCohortModal from '../app/components/CreateCohortModal';
import { PLAYER_VISIBILITY_DEFAULTS } from '../app/config/playerVisibilityRegistry';

const PRESETS = [
  { id: 'workshop_standard', name: 'Workshop', icon: '🏢', difficulty_tier: 'advanced',
    subtitle: 'Standard · Progressive Disclosure', color: '#6366f1',
    target_audience: 'MBA', description: 'Balanced.',
    default_pedagogy: { round_recap_enabled: true },
    default_audiences: ['core', 'scaffold', 'narrative', 'insight', 'debrief', 'flourish'],
    results_reveal_round: 3 },
];

beforeEach(() => {
  global.fetch = jest.fn((url) => {
    const u = String(url);
    const json = (body) => Promise.resolve({ ok: true, status: 200, json: async () => body });
    if (u.includes('/scenario-presets')) return json({ presets: PRESETS });
    if (u.includes('/god/analytics-visibility'))
      return json({ facilitator: {}, player: { ...PLAYER_VISIBILITY_DEFAULTS } });
    if (u.includes('/ending-pathways')) return json({ pathways: [] });
    if (u.includes('/side-tracks')) return json({ catalog: [] });
    return json({});
  });
});
afterEach(() => { jest.restoreAllMocks(); delete global.fetch; });

async function mountAs(role) {
  const utils = render(
    <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}}
                       currentFacilitatorId={role} currentFacilitatorRole={role} />);
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  await act(async () => { await new Promise(r => setTimeout(r, 300)); });
  return utils;
}

const sectionButton = (container, re) =>
  [...container.querySelectorAll('button')].find(b => re.test(b.textContent || ''));

test('god_mode sees the Simulation Engine section and can pick Strategic Pillars', async () => {
  const { container } = await mountAs('god_mode');
  const engine = sectionButton(container, /2\.\s*Simulation Engine/);
  expect(engine).toBeTruthy();
  await act(async () => { fireEvent.click(engine); });
  expect(container.textContent).toMatch(/Strategic Pillars/);
  expect(sectionButton(container, /3\.\s*Optional Modules/)).toBeTruthy();
  expect(sectionButton(container, /4\.\s*Team Interventions/)).toBeTruthy();
});

test('super_admin sees the same sections (the case that always worked)', async () => {
  const { container } = await mountAs('super_admin');
  expect(sectionButton(container, /2\.\s*Simulation Engine/)).toBeTruthy();
  expect(sectionButton(container, /3\.\s*Optional Modules/)).toBeTruthy();
});

test('a base facilitator still does not see them', async () => {
  const { container } = await mountAs('facilitator');
  expect(sectionButton(container, /2\.\s*Simulation Engine/)).toBeFalsy();
  expect(sectionButton(container, /3\.\s*Optional Modules/)).toBeFalsy();
  expect(sectionButton(container, /5\.\s*Pedagogy/)).toBeTruthy();
});
