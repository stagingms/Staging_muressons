/**
 * ConfigLiveStatus, actually rendered.
 *
 * WHY THIS PANEL AND THIS TEST EXIST
 *   The uploader immediately above this panel returns {"reload": "complete"}
 *   whether or not the new values reached the engine — its hot-reload rebinds
 *   only some modules, and the file it writes lives in the image, so the next
 *   redeploy reverts it. The panel is the check on that claim. A panel that
 *   silently rendered nothing would therefore be worse than no panel: it would
 *   read as "no problems".
 *
 *   So these tests assert the DOM, not the source. Three properties matter:
 *     1. A clean process reads unambiguously clean.
 *     2. Problems are SHOWN, worst first, with their message intact — a
 *        stale_binding buried below a fold is a stale_binding nobody acts on.
 *     3. The 238 constants stay behind a disclosure, so the verdict is never
 *        pushed off screen by data.
 */
import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import ConfigLiveStatus from '../app/components/ConfigLiveStatus';

const CLEAN = {
  fingerprint: 'sha256:06f865fbd868e65c',
  constant_count: 2,
  healthy: true,
  problems: [],
  summary: 'Configuration is coherent: the file, this process and every consumer module agree.',
  file_vs_process: { status: 'in_sync' },
  stale_bindings: [], god_mode_shadowing: [], inert_tunables: [],
  constants: { SIM_ROUNDS: 10, FINANCIAL_SHADOW_CARBON_PRICE: 250.0 },
};

const DIRTY = {
  ...CLEAN,
  healthy: false,
  summary: '3 configuration problem(s). The engine is NOT necessarily running the values you last set — see \'problems\'.',
  problems: [
    { severity: 'low', kind: 'inert_tunable',
      message: "_engine_tunables['cannibalization_rate'] is not forwarded and reaches nothing." },
    { severity: 'high', kind: 'stale_binding',
      message: 'round_logic.SIM_ROUNDS is stale: it holds 10 while config.SIM_ROUNDS is 12.' },
    { severity: 'medium', kind: 'shadowed_by_god_mode',
      message: "_god_mode_settings['overrun_probability'] is what the engine reads." },
  ],
};

function mockFetch(payload, ok = true) {
  global.fetch = jest.fn().mockResolvedValue({
    ok,
    status: ok ? 200 : 401,
    json: async () => payload,
  });
}

async function renderPanel(props = {}) {
  await act(async () => { render(<ConfigLiveStatus {...props} />); });
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
}

afterEach(() => { jest.resetAllMocks(); });

describe('ConfigLiveStatus', () => {
  it('reads a clean process as unambiguously clean', async () => {
    mockFetch(CLEAN);
    await renderPanel();
    expect(await screen.findByTestId('config-live-summary')).toHaveTextContent(/coherent/i);
    expect(screen.queryByTestId('config-live-problems')).toBeNull();
  });

  it('shows every problem, with its message intact', async () => {
    mockFetch(DIRTY);
    await renderPanel();
    const list = await screen.findByTestId('config-live-problems');
    expect(list.querySelectorAll('li')).toHaveLength(3);
    // The specific sentence a facilitator has to act on must survive rendering.
    expect(list).toHaveTextContent(/round_logic\.SIM_ROUNDS is stale/);
    expect(list).toHaveTextContent(/overrun_probability/);
  });

  it('orders problems worst-first', async () => {
    mockFetch(DIRTY);
    await renderPanel();
    const list = await screen.findByTestId('config-live-problems');
    const kinds = [...list.querySelectorAll('li')].map((li) => li.textContent);
    expect(kinds[0]).toMatch(/stale_binding/);      // high
    expect(kinds[1]).toMatch(/shadowed_by_god_mode/); // medium
    expect(kinds[2]).toMatch(/inert_tunable/);      // low
  });

  it('CFG-03: advisories never colour the verdict and sit behind a disclosure', async () => {
    // A pristine install has 16 inert god-mode tunables. They used to be
    // low-severity PROBLEMS, so `healthy` was false forever and the warning
    // sentence was permanently on — a real problem read exactly like the noise.
    mockFetch({
      ...CLEAN,
      summary: 'Configuration is coherent: the file, this process and every consumer module agree, and no value was clamped. 1 advisory note(s) — see \'advisories\'.',
      advisories: [{ severity: 'low', kind: 'inert_tunable',
        message: "_engine_tunables['cannibalization_rate'] is not forwarded and reaches nothing." }],
      clamped_values: [], image_vs_volume: { status: 'in_sync' },
    });
    await renderPanel();
    expect(await screen.findByTestId('config-live-summary')).toHaveTextContent(/coherent/i);
    expect(screen.queryByTestId('config-live-problems')).toBeNull();
    const adv = screen.getByTestId('config-live-advisories');
    expect(adv.open).toBe(false);
    expect(adv).toHaveTextContent(/1 advisory note/);
    expect(adv).toHaveTextContent(/cannibalization_rate/);
    expect(screen.getByText(/image_vs_volume: in_sync/)).toBeInTheDocument();
    expect(screen.getByText(/clamped: 0/)).toBeInTheDocument();
  });

  it('CFG-02: a clamped value is a HIGH problem, named with what the engine runs', async () => {
    mockFetch({
      ...CLEAN, healthy: false,
      summary: '2 configuration problem(s). The engine is NOT necessarily running the values you last set — see \'problems\'.',
      problems: [
        { severity: 'medium', kind: 'image_vs_volume', keys: ['terminal_valuation.shares_outstanding'],
          message: 'The config on the data volume differs from the copy this build ships on 1 key(s): terminal_valuation.shares_outstanding.' },
        { severity: 'high', kind: 'clamped_value', key: 'engine_parameters.regulatory_ratchet.baseline', configured: 10, using: 20,
          message: 'engine_parameters.regulatory_ratchet.baseline on the data volume is 10.0 — is at or below the pre-F-10 value; the engine is running 20.0 instead.' },
      ],
      advisories: [], clamped_values: [{ key: 'engine_parameters.regulatory_ratchet.baseline' }],
      image_vs_volume: { status: 'differs', differing_count: 1 },
    });
    await renderPanel();
    const list = await screen.findByTestId('config-live-problems');
    const items = [...list.querySelectorAll('li')].map((li) => li.textContent);
    expect(items[0]).toMatch(/HIGH/);
    expect(items[0]).toMatch(/clamped_value/);
    expect(items[0]).toMatch(/engine is running 20\.0 instead/);
    expect(items[1]).toMatch(/image_vs_volume/);
    expect(screen.getByText(/clamped: 1/)).toBeInTheDocument();
  });

  it('keeps the constants behind a disclosure so the verdict stays visible', async () => {
    mockFetch(CLEAN);
    const { container } = await act(async () => render(<ConfigLiveStatus />)) || {};
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    const details = document.querySelector('details');
    expect(details).not.toBeNull();
    expect(details.open).toBe(false);
    expect(details).toHaveTextContent(/All 2 live values/);
  });

  it('surfaces an auth or network failure instead of reading as healthy', async () => {
    mockFetch({ detail: 'Facilitator authentication required' }, false);
    await renderPanel();
    expect(await screen.findByRole('alert')).toHaveTextContent(/Facilitator authentication required/);
    // The critical property: a failed read must NOT render a clean verdict.
    expect(screen.queryByTestId('config-live-summary')).toBeNull();
  });

  it('re-reads when the uploader bumps refreshToken', async () => {
    mockFetch(CLEAN);
    const { rerender } = render(<ConfigLiveStatus refreshToken={0} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    await act(async () => { rerender(<ConfigLiveStatus refreshToken={1} />); });
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));
  });
});

/**
 * Wiring. This one IS a source check, deliberately and narrowly.
 *
 * The repo has been here before: NegotiationRoom.js existed, worked, and was
 * imported by nothing, so every test passed while the feature was invisible
 * (see __tests__/negotiation-room-wired.test.js). A verification panel that
 * ships orphaned is worth less than no panel, because its absence reads as
 * "nothing to report". Rendering the whole switchboard to prove this would drag
 * in a dozen unrelated endpoints; asserting the wiring exists is the cheap 90%.
 */
describe('ConfigLiveStatus is wired into the god-mode switchboard', () => {
  const fs = require('fs');
  const path = require('path');
  const src = fs.readFileSync(
    path.join(__dirname, '..', 'app', 'components', 'SimulationSwitchboard.js'), 'utf8');

  it('is imported and rendered', () => {
    expect(src).toMatch(/import\s+ConfigLiveStatus\s+from\s+'\.\/ConfigLiveStatus'/);
    expect(src).toMatch(/<ConfigLiveStatus/);
  });

  it('re-reads after a config upload', () => {
    // Without this, the panel shows the state from before the upload — the one
    // moment its answer matters most.
    expect(src).toMatch(/<ConfigLiveStatus\s+refreshToken=/);
    expect(src).toMatch(/onUploaded/);
  });

  it('no longer promises that an upload takes effect immediately', () => {
    // The old copy read "Changes take effect immediately — no server restart
    // required." The reload rebinds only some modules and the file lives in the
    // image, so both halves of that sentence were false.
    expect(src).not.toMatch(/take effect immediately/);
    expect(src).not.toMatch(/no server restart required/);
  });
});
