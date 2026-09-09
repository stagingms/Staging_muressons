/**
 * The cohort form's error surfaces, actually rendered.
 *
 * WHY THIS EXISTS
 *   apiError.test.js proves toErrorText is correct in isolation, and
 *   no-raw-detail-coercion.test.js proves the bad idiom is absent from the
 *   source. Neither would have caught the defect this file is named for: the
 *   first fix patched three throw sites, passed both kinds of test, and still
 *   left the summary panel rendering `st.error` from a pre-coerced
 *   `err.message`. Source inspection cannot tell you what reaches the screen.
 *
 *   So this mounts the real modal, makes the API fail the way FastAPI actually
 *   fails, and asserts on the DOM. There are two paths a failure can take to
 *   the facilitator and both are exercised:
 *
 *     1. /api/simulations/start rejects  -> the `error` banner (via setError)
 *     2. a sub-config step rejects       -> the step chip (via runOneStep)
 *
 *   The load-bearing assertion in every case is the same: the text
 *   "[object Object]" must not appear, and the field the server rejected must.
 */
import React from 'react';
import { render, act, waitFor, fireEvent } from '@testing-library/react';
import CreateCohortModal from '../app/components/CreateCohortModal';
import { PLAYER_VISIBILITY_DEFAULTS } from '../app/config/playerVisibilityRegistry';

const PRESETS = [
  { id: 'workshop_standard', name: 'Workshop', icon: 'W', difficulty_tier: 'advanced',
    subtitle: 'Standard', color: '#6366f1', target_audience: 'MBA', description: 'Balanced.',
    default_pedagogy: { round_recap_enabled: true },
    default_audiences: ['core'], results_reveal_round: 3 },
];

/** The exact body FastAPI emits for a 422: detail is an ARRAY, not a string. */
const VALIDATION_422 = {
  detail: [
    { loc: ['body', 'region_id'], msg: 'Input should be a valid string', type: 'string_type' },
    { loc: ['body', 'cohort_name'], msg: 'String should have at least 1 character',
      type: 'string_too_short' },
  ],
};

/** A structured raise: detail is a DICT. Also coerces to "[object Object]". */
const STRUCTURED_409 = {
  detail: { code: 'cohort_exists', message: 'A cohort with that name is already running.' },
};

const okJson = (body) => Promise.resolve({ ok: true, status: 200, json: async () => body });

const defaultRoute = (u) => {
  if (u.includes('/scenario-presets')) return okJson({ presets: PRESETS });
  if (u.includes('/god/analytics-visibility'))
    return okJson({ facilitator: {}, player: { ...PLAYER_VISIBILITY_DEFAULTS } });
  if (u.includes('/ending-pathways')) return okJson({ pathways: [] });
  if (u.includes('/side-tracks')) return okJson({ catalog: [] });
  return okJson({});
};

/**
 * @param overrides - url-substring -> {status, body} | {reject} | {rawJsonThrows}
 *                    for the calls under test. Everything else answers 200 {}.
 */
const mockApi = (overrides = {}) => {
  global.fetch = jest.fn((url, opts = {}) => {
    const u = String(url);
    calls.push({ url: u, body: opts && opts.body ? JSON.parse(opts.body) : null });
    for (const [needle, spec] of Object.entries(overrides)) {
      if (u.includes(needle)) {
        if (spec && 'reject' in spec) return Promise.reject(spec.reject);
        if (spec && spec.rawJsonThrows) {
          return Promise.resolve({
            ok: false, status: spec.status,
            json: async () => { throw new SyntaxError('Unexpected token < in JSON'); },
          });
        }
        return Promise.resolve({
          ok: spec.status >= 200 && spec.status < 300,
          status: spec.status,
          json: async () => spec.body,
        });
      }
    }
    return defaultRoute(u);
  });
};

let calls = [];
beforeEach(() => { calls = []; });
afterEach(() => { jest.restoreAllMocks(); delete global.fetch; });

/** Mount, settle the load fetches, choose a region, and submit the form. */
async function submitForm() {
  const utils = render(
    <CreateCohortModal isOpen onClose={() => {}} onCreated={() => {}}
                       currentFacilitatorId="god_mode" currentFacilitatorRole="super_admin" />);
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  await act(async () => { await new Promise(r => setTimeout(r, 300)); });

  // Region is the one client-side mandatory field; without it handleCreate
  // returns before ever calling the API and the test would prove nothing.
  const region = [...utils.container.querySelectorAll('select')]
    .find(s => [...s.options].some(o => o.value === 'europe'));
  expect(region).toBeTruthy();
  await act(async () => { fireEvent.change(region, { target: { value: 'europe' } }); });

  const form = utils.container.querySelector('form');
  expect(form).toBeTruthy();
  await act(async () => { fireEvent.submit(form); await new Promise(r => setTimeout(r, 500)); });
  return utils;
}

describe('cohort creation failure reaches the facilitator as words', () => {
  it('renders the rejected fields for a 422, not "[object Object]"', async () => {
    mockApi({ '/api/simulations/start': { status: 422, body: VALIDATION_422 } });
    const { container } = await submitForm();
    const text = container.textContent;

    expect(text).not.toContain('[object Object]');
    expect(text).toContain('Create cohort');       // which call failed
    expect(text).toContain('422');                 // and how
    expect(text).toContain('region_id');           // and which field
    expect(text).toContain('Input should be a valid string');
    expect(text).toContain('cohort_name');
  });

  it('renders the message from a structured dict detail', async () => {
    mockApi({ '/api/simulations/start': { status: 409, body: STRUCTURED_409 } });
    const { container } = await submitForm();

    expect(container.textContent).not.toContain('[object Object]');
    expect(container.textContent)
      .toContain('A cohort with that name is already running.');
  });

  it('still says something when the body is not JSON at all', async () => {
    // .json() rejects -> the call site falls back to {}. The banner must still
    // name the failing call and its status rather than going blank.
    mockApi({ '/api/simulations/start': { status: 502, rawJsonThrows: true } });
    const { container } = await submitForm();

    expect(container.textContent).not.toContain('[object Object]');
    expect(container.textContent).toContain('Create cohort');
    expect(container.textContent).toContain('502');
  });
});

describe('a failed sub-config step reaches the facilitator as words', () => {
  // This is the surface the first fix missed: the summary panel renders
  // st.error directly, never passing through setError.
  const startsOk = {
    '/api/simulations/start': {
      status: 200,
      body: { session_id: 'sess_test_1', round_number: 1, global_state: {}, business_units: [] },
    },
  };

  it('names the rejected field in the step chip, not "[object Object]"', async () => {
    mockApi({
      ...startsOk,
      '/pedagogical-settings': { status: 422, body: VALIDATION_422 },
    });
    const { container } = await submitForm();
    await act(async () => { await new Promise(r => setTimeout(r, 400)); });
    const text = container.textContent;

    expect(text).not.toContain('[object Object]');
    expect(text).toContain('Pedagogical Settings');
    expect(text).toContain('region_id');
  });

  it('never shows a failed step with no text, even for a non-Error throw', async () => {
    // `throw undefined` is the case that made err.message undefined and drew a
    // red cross with nothing beside it - a failure that reads as success.
    mockApi({
      ...startsOk,
      '/pedagogical-settings': { reject: undefined },
    });
    const { container } = await submitForm();
    await act(async () => { await new Promise(r => setTimeout(r, 400)); });

    expect(container.textContent).not.toContain('[object Object]');
    expect(container.textContent).toContain('Pedagogical Settings');
    expect(container.textContent).toMatch(/failed for an unknown reason/);
  });

  it('survives a network-level fetch rejection', async () => {
    mockApi({
      ...startsOk,
      '/pedagogical-settings': { reject: new TypeError('Failed to fetch') },
    });
    const { container } = await submitForm();
    await act(async () => { await new Promise(r => setTimeout(r, 400)); });

    expect(container.textContent).not.toContain('[object Object]');
    expect(container.textContent).toContain('Failed to fetch');
  });
});

describe('the allow-list payload cannot carry a value the server will reject', () => {
  // ROOT-CAUSE GUARD. The create payload's allowed_overrides / allowed_swipes
  // are typed list[str] on the server. The form built them with
  // `.map(o => o.id)`, so a master row without a usable id became undefined,
  // JSON.stringify wrote it as null, and Pydantic answered with one 422 error
  // per bad element - which is exactly how a single malformed row turns into a
  // row of "[object Object]" repeats. Verified against the real model:
  //   [null, null] -> 2 errors -> "[object Object],[object Object]"
  // Dropping an id-less row is correct, not a workaround: the server has no
  // way to resolve a row it was never given an id for.
  const MALFORMED_MASTER = {
    overrides: [
      { id: 'force_strike', title: 'Force Strike' },
      { title: 'No id at all' },          // -> undefined -> null on the wire
      { id: '', title: 'Empty id' },      // -> '' , not a usable reference
      { id: 42, title: 'Numeric id' },    // -> Pydantic rejects int for str
    ],
    swipes: [
      { id: 'swipe_ok', label: 'Fine' },
      { label: 'No id' },
    ],
  };

  const startBody = () =>
    (calls.find((c) => c.url.includes('/api/simulations/start')) || {}).body;

  it('sends only non-empty string ids, whatever the master list contains', async () => {
    mockApi({
      '/interventions/master': { status: 200, body: MALFORMED_MASTER },
      '/api/simulations/start': {
        status: 200,
        body: { session_id: 's1', round_number: 1, global_state: {}, business_units: [] },
      },
    });
    await submitForm();
    const body = startBody();
    expect(body).toBeTruthy();

    expect(body.allowed_overrides).toEqual(['force_strike']);
    expect(body.allowed_swipes).toEqual(['swipe_ok']);

    // The property that actually matters, stated directly: nothing in either
    // array can be anything but a non-empty string.
    for (const arr of [body.allowed_overrides, body.allowed_swipes]) {
      expect(Array.isArray(arr)).toBe(true);
      for (const v of arr) {
        expect(typeof v).toBe('string');
        expect(v.length).toBeGreaterThan(0);
      }
    }
  });

  it('sends well-formed ids through untouched', async () => {
    mockApi({
      '/interventions/master': {
        status: 200,
        body: { overrides: [{ id: 'a' }, { id: 'b' }], swipes: [{ id: 'x' }] },
      },
      '/api/simulations/start': {
        status: 200,
        body: { session_id: 's1', round_number: 1, global_state: {}, business_units: [] },
      },
    });
    await submitForm();
    const body = startBody();

    expect(body.allowed_overrides).toEqual(['a', 'b']);
    expect(body.allowed_swipes).toEqual(['x']);
  });
});
