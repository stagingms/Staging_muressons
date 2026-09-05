/**
 * CFG-08 (audit 2026-09-04, WP-25): 16 of the 24 god-mode "engine tunables"
 * reach nothing, and the panel said "saved" for all of them. The server now
 * reports the inert set and the panel shows those knobs disabled with a note.
 */
import { render, screen, waitFor } from '@testing-library/react';
import EconomicEngineTunables from '../app/components/EconomicEngineTunables';

const PAYLOAD = {
  tunables: { inflation_rate: 0.025, overrun_probability: 0.25, overrun_severity: 0.15, fog_noise_range: 0.1 },
  inert: ['inflation_rate', 'fog_noise_range'],
  descriptions: {},
};

beforeEach(() => {
  global.fetch = jest.fn((url) => {
    if (String(url).includes('/engine-tunables')) {
      return Promise.resolve({ ok: true, status: 200, json: async () => PAYLOAD });
    }
    return Promise.resolve({ ok: true, status: 200, json: async () => ({ presets: [], tunables: {} }) });
  });
});
afterEach(() => jest.resetAllMocks());

test('inert knobs are marked and disabled; wired knobs are not', async () => {
  render(<EconomicEngineTunables />);
  await waitFor(() => expect(screen.getByTestId('tunable-inert-inflation_rate')).toBeInTheDocument());
  expect(screen.getByTestId('tunable-inert-inflation_rate')).toHaveTextContent(/not wired/i);
  expect(screen.getByTestId('tunable-inert-fog_noise_range')).toBeInTheDocument();
  expect(screen.queryByTestId('tunable-inert-overrun_probability')).toBeNull();
  const sliders = screen.getAllByRole('slider');
  const byLabel = Object.fromEntries(sliders.map((s) => [s.getAttribute('aria-label'), s]));
  expect(byLabel['Inflation Rate (not wired to the engine)']).toBeDisabled();
  expect(byLabel['Overrun Probability']).not.toBeDisabled();
});

test('a payload without the inert list renders every knob live', async () => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: true, status: 200, json: async () => ({ tunables: PAYLOAD.tunables, descriptions: {} }) }));
  render(<EconomicEngineTunables />);
  await waitFor(() => expect(screen.getAllByRole('slider').length).toBeGreaterThan(0));
  expect(screen.queryByText(/not wired/i)).toBeNull();
});
