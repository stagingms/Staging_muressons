/**
 * Found by the scripted classroom rehearsal (2026-09-10): useAnalyticsVisibility
 * read the console-only /api/admin/cohort/{id}/analytics-visibility, got 401 as a
 * participant, and failed open — so every player-audience toggle the
 * facilitator set was ignored on the participant's screen. The hook now falls
 * back to the team-readable /api/simulations/{id}/player-visibility.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { useAnalyticsVisibility } from '../app/hooks/useAnalyticsVisibility';

const ok = (payload) => ({ ok: true, status: 200, json: async () => payload });
const fail = (status) => ({ ok: false, status, json: async () => ({ detail: 'Facilitator authentication required' }) });

afterEach(() => { delete global.fetch; window.localStorage.clear(); });

test('a participant gets the player column from the team route when the console route refuses', async () => {
  window.localStorage.setItem('muressons_playerId', 'MUR-0001');
  window.localStorage.setItem('muressons_player_token', 'tok');
  const calls = [];
  global.fetch = jest.fn(async (url, opts = {}) => {
    calls.push([String(url), opts]);
    if (String(url).includes('/api/admin/cohort/')) return fail(401);
    if (String(url).includes('/player-visibility')) return ok({ effective: { player: { boardroom_showdown: false, student_report_export: true } } });
    return fail(404);
  });
  const { result } = renderHook(() => useAnalyticsVisibility('sid-1'));
  await waitFor(() => expect(result.current.player).not.toBeNull());
  expect(result.current.isPlayerVisible('boardroom_showdown')).toBe(false);
  expect(result.current.isPlayerVisible('student_report_export')).toBe(true);
  expect(result.current.isPlayerVisible('something_unlisted')).toBe(true);
  const teamCall = calls.find(([u]) => u.includes('/player-visibility'));
  expect(teamCall[0]).toBe('/api/simulations/sid-1/player-visibility');
  expect(teamCall[1].headers['X-Player-Id']).toBe('MUR-0001');
  expect(teamCall[1].headers.Authorization).toBe('Bearer tok');
});

test('the console keeps reading both columns from the console route', async () => {
  global.fetch = jest.fn(async (url) => {
    if (String(url).includes('/api/admin/cohort/')) return ok({ effective: { facilitator: { decision_heatmap: false }, player: { boardroom_showdown: false } } });
    throw new Error('the team route must not be called when the console route answers');
  });
  const { result } = renderHook(() => useAnalyticsVisibility('sid-2'));
  await waitFor(() => expect(result.current.facilitator).not.toBeNull());
  expect(result.current.isFacilitatorVisible('decision_heatmap')).toBe(false);
  expect(result.current.isPlayerVisible('boardroom_showdown')).toBe(false);
  expect(global.fetch).toHaveBeenCalledTimes(1);
});
