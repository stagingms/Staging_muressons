/**
 * The cohort form, actually rendered.
 *
 * Everything else in this area is source inspection — regexes over the file.
 * That is how a whole afternoon's work can pass its tests and still show the
 * facilitator the old nineteen-toggle wall, which is exactly what happened: the
 * code was right, the running bundle was stale, and no test could tell the two
 * apart. This one mounts the real CreateCohortModal against mocked endpoints and
 * asserts what the DOM contains, so "it renders" stops being an assumption.
 *
 * The grid is inside the "5. Pedagogy & Analytics" accordion, collapsed by
 * default — the test opens it the way a facilitator would, which also pins that
 * the section is reachable at all.
 */
import React from 'react';
import { render, act, waitFor } from '@testing-library/react';
import CreateCohortModal from '../app/components/CreateCohortModal';
import { PLAYER_VISIBILITY_DEFAULTS, PLAYER_VISIBILITY_CARDS }
  from '../app/config/playerVisibilityRegistry';

const PRESETS = [
  { id: 'classroom_easy', name: 'Classroom', icon: '🎓', difficulty_tier: 'foundation',
    subtitle: 'Easy · Foundation Visibility', color: '#10b981',
    target_audience: 'Undergraduates', description: 'Gentle settings.',
    default_pedagogy: { round_recap_enabled: true },
    default_audiences: ['core', 'scaffold', 'narrative', 'insight', 'debrief', 'flourish'],
    results_reveal_round: 0 },
  { id: 'workshop_standard', name: 'Workshop', icon: '🏢', difficulty_tier: 'advanced',
    subtitle: 'Standard · Progressive Disclosure', color: '#6366f1',
    target_audience: 'MBA', description: 'Balanced.',
    default_pedagogy: { round_recap_enabled: true },
    default_audiences: ['core', 'scaffold', 'narrative', 'insight', 'finance', 'causal',
                        'compare', 'metacog', 'debrief', 'flourish'],
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

/** Mount, settle the fetches, and open the analytics accordion. */
async function openForm() {
  const utils = render(
    <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}}
                       currentFacilitatorId="god_mode" currentFacilitatorRole="super_admin" />);
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  await act(async () => { await new Promise(r => setTimeout(r, 300)); });
  const btn = [...utils.container.querySelectorAll('button')]
    .find(b => /Pedagogy\s*&\s*Analytics/.test(b.textContent || ''));
  expect(btn).toBeTruthy();               // the section must be reachable
  await act(async () => { btn.click(); await new Promise(r => setTimeout(r, 300)); });
  return utils;
}

const clickText = async (container, re, pred = () => true) => {
  // Buttons first: a wrapping <div> often matches the same text and clicking it
  // does nothing, which reads as "the control is broken" rather than "the test
  // grabbed the wrong node".
  const match = (e) => re.test(e.textContent || '') && pred(e);
  const el = [...container.querySelectorAll('button')].find(match)
          || [...container.querySelectorAll('div')].find(match);
  if (!el) {
    const buttons = [...container.querySelectorAll('button')]
      .map(b => (b.textContent || '').trim().slice(0, 40)).filter(Boolean);
    throw new Error(`no element for ${re}. buttons present:\n  ` + buttons.join('\n  '));
  }
  await act(async () => { el.click(); await new Promise(r => setTimeout(r, 250)); });
};

test('the Player Dashboard renders all 65 switches, grouped', async () => {
  const { container } = await openForm();
  const text = container.textContent;

  expect(text).toContain('Player Dashboard');
  expect(text).toMatch(/\d+ \/ 65 shown/);

  // Every card label present — the wall is complete, not truncated.
  for (const c of PLAYER_VISIBILITY_CARDS) expect(text).toContain(c.label);

  // ...and sectioned, each with its own count and bulk control.
  for (const g of ['Core analytics', 'End of game & debrief',
                   'Valuation & causal analytics', 'Narrative & stakeholders']) {
    expect(text).toContain(g);
  }
  expect(text).toMatch(/12\/12/);          // a full group
});

test('the reported count matches the switches actually on', async () => {
  const { container } = await openForm();
  const shown = Number(container.textContent.match(/(\d+) \/ 65 shown/)[1]);
  // Workshop is the default selection.
  expect(shown).toBe(58);
});

test('the header names the experience level the state came from', async () => {
  const { container } = await openForm();
  expect(container.textContent).toMatch(/from\s*🏢\s*Workshop/);
});

test('choosing Classroom re-profiles the grid', async () => {
  const { container } = await openForm();
  expect(container.textContent).toMatch(/58 \/ 65 shown/);

  // Reopen Core Configuration, pick Classroom, come back.
  await clickText(container, /Core Configuration/);
  await clickText(container, /Classroom/, e => (e.textContent || '').length < 200);
  await clickText(container, /Pedagogy\s*&\s*Analytics/);

  const text = container.textContent;
  expect(text).toMatch(/40 \/ 65 shown/);        // the Classroom profile
  expect(text).toMatch(/from\s*🎓\s*Classroom/);
});

test('a hand-edit marks the form customised and offers a way back', async () => {
  const { container } = await openForm();
  expect(container.textContent).not.toMatch(/Customised/);

  const card = [...container.querySelectorAll('[class*="visCard"]')]
    .find(e => /Boardroom Moment/.test(e.textContent || ''));
  expect(card).toBeTruthy();               // a NEW key, reachable and clickable
  await act(async () => { card.click(); await new Promise(r => setTimeout(r, 200)); });

  const text = container.textContent;
  expect(text).toMatch(/Customised/);
  expect(text).toMatch(/Reset to/);
  expect(text).toMatch(/57 \/ 65 shown/);        // the count followed the edit
});

test('opening the modal from closed does not violate the Rules of Hooks', async () => {
  // The crash this pins: the preset-application effect originally sat BELOW the
  // `if (!isOpen) return null` guard, so a closed render mounted fewer hooks
  // than an open one — "Rendered more hooks than during the previous render"
  // the moment a facilitator opened the form. The earlier tests all mount with
  // isOpen already true, which is exactly why none of them caught it: the bug
  // lives in the TRANSITION, not in either state.
  const errors = [];
  const spy = jest.spyOn(console, 'error').mockImplementation((...a) => errors.push(a.join(' ')));
  try {
    const { rerender, container } = render(
      <CreateCohortModal isOpen={false} onClose={() => {}} onCreated={() => {}}
                         currentFacilitatorId="god_mode" currentFacilitatorRole="super_admin" />);
    await act(async () => { await new Promise(r => setTimeout(r, 100)); });
    await act(async () => {
      rerender(
        <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}}
                           currentFacilitatorId="god_mode" currentFacilitatorRole="super_admin" />);
      await new Promise(r => setTimeout(r, 300));
    });
    const hookErrors = errors.filter(e =>
      /order of Hooks|more hooks than|Rules of Hooks/i.test(e));
    expect(hookErrors).toEqual([]);
    expect(container.textContent).toContain('Core Configuration');  // it actually opened
  } finally { spy.mockRestore(); }
});

describe('Negotiation Rooms toggle', () => {
  // Capability-gated: the server 403s negotiation_rooms_enabled:true from any
  // account that is neither admin nor a capability holder — and a 403 there
  // takes the WHOLE cohort-settings PATCH down with it (reveal round, quiz
  // settings). So the switch must only exist where the save can succeed, and
  // the payload must only carry the key for accounts allowed to send it.
  afterEach(() => localStorage.clear());

  const openPedagogy = async (container) => {
    const { act } = require('@testing-library/react');
    const btn = [...container.querySelectorAll('button')]
      .find(b => /Pedagogy\s*&\s*Analytics/.test(b.textContent || ''));
    await act(async () => { btn.click(); await new Promise(r => setTimeout(r, 250)); });
  };

  test('visible to a capability holder who is not an admin', async () => {
    localStorage.setItem('facilitator_auth',
      JSON.stringify({ role: 'facilitator', negotiation_rooms_enabled: true }));
    const { container } = render(
      <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}}
                         currentFacilitatorId="FAC-7" currentFacilitatorRole="facilitator" />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    await act(async () => { await new Promise(r => setTimeout(r, 300)); });
    await openPedagogy(container);
    expect(container.textContent).toContain('Negotiation Rooms');
  });

  test('hidden from a plain facilitator without the capability', async () => {
    localStorage.setItem('facilitator_auth', JSON.stringify({ role: 'facilitator' }));
    const { container } = render(
      <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}}
                         currentFacilitatorId="FAC-7" currentFacilitatorRole="facilitator" />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    await act(async () => { await new Promise(r => setTimeout(r, 300)); });
    await openPedagogy(container);
    expect(container.textContent).not.toContain('Negotiation Rooms');
  });

  test('admins see it without the per-account capability', async () => {
    const { container } = await openForm();   // super_admin fixture
    expect(container.textContent).toContain('Negotiation Rooms');
  });

  test('persists via cohort-settings, never the pedagogy PUT', () => {
    // Trap 1: the pedagogy PUT allow-list derives from
    // DEFAULT_PEDAGOGICAL_TOGGLES, which lacks this key — a save through it
    // looks successful and stores nothing.
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.join(__dirname, '..', 'app', 'components', 'CreateCohortModal.js'), 'utf8');
    const cohortStep = src.slice(src.indexOf('/cohort-settings`'),
                                 src.indexOf('quiz_max_attempts'));
    expect(cohortStep).toMatch(/negotiation_rooms_enabled: negotiationRoomsEnabled/);
    // Trap 2: only capability holders may carry the key at all.
    expect(cohortStep).toMatch(/\.\.\.\(negoCapable \? \{ negotiation_rooms_enabled/);
    const pedStep = src.slice(src.indexOf('/pedagogical-settings`'),
                              src.indexOf('/cohort-settings`'));
    expect(pedStep).not.toMatch(/negotiation_rooms_enabled/);
    // And it must stay out of the PEDAGOGICAL_TOGGLES const, whose every entry
    // is asserted persistable through the pedagogy PUT.
    const toggles = src.slice(src.indexOf('const PEDAGOGICAL_TOGGLES'),
                              src.indexOf('const ENGINE_MODULE_TOGGLES'));
    expect(toggles).not.toMatch(/negotiation_rooms_enabled/);
  });
});
