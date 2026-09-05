/**
 * OPS-2 (audit 2026-09-04, WP-26): "Roll Back Entire Cohort" was permanently
 * disabled because the panel read the cohort SHELL's round (1 forever). For a
 * cohort the panel now takes the round the class is on from cohort-pulse
 * (the furthest team), which is what the server's cohort-wide undo counts.
 */
import { render, screen, waitFor } from '@testing-library/react';
import UndoRound from '../app/components/UndoRound';

function mockFetch(routes) {
  global.fetch = jest.fn((url) => {
    for (const [frag, body] of routes) {
      if (String(url).includes(frag)) return Promise.resolve({ ok: true, status: 200, json: async () => body });
    }
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}) });
  });
}
afterEach(() => jest.resetAllMocks());

test('a cohort shell reads the furthest team round, not its own round 1', async () => {
  mockFetch([
    ['/cohort-pulse/', { teams: [
      { session_id: 'shell', is_cohort_shell: true, round: 1 },
      { session_id: 'a', round: 4 },
      { session_id: 'b', round: 3 },
    ] }],
    ['/dashboard', { current_round: 1 }],
  ]);
  render(<UndoRound session={{ session_id: 'shell', short_code: 'SHELL' }} />);
  await waitFor(() => expect(screen.getByText(/Roll Back Entire Cohort/)).not.toBeDisabled());
  expect(screen.getByText(/Roll Back to Round 3/)).toBeInTheDocument();
});

test('a player session still reads its own dashboard round', async () => {
  mockFetch([
    ['/dashboard', { current_round: 5 }],
  ]);
  render(<UndoRound session={{ session_id: 'p1', player_id: 'MUR-ABCD' }} />);
  await waitFor(() => expect(screen.getByText(/Roll Back to Round 4/)).toBeInTheDocument());
  expect(screen.queryByText(/Roll Back Entire Cohort/)).toBeNull();
  expect(global.fetch.mock.calls.some(([u]) => String(u).includes('/cohort-pulse/'))).toBe(false);
});
