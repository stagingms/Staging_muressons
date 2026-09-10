/**
 * F06(b) (audit AUDIT_Engines_Flow_Classroom50_20260909) — a lost commit
 * response no longer loses the round's results screen.
 *
 * The audit's client probe: a retry after an earlier successful commit got
 * 409 stale_round; the hook refreshed the dashboard and left
 * commitResults=null ("STALE_COMMIT_RECOVERY {round:2, commitResults:null}").
 * The participant landed on the next briefing without ever seeing round 1's
 * outcome — and nothing could rebuild it, because the events dict lived only
 * in the lost HTTP response.
 *
 * The server now keeps every round's response (GET /commit-result/{round});
 * the hook rebuilds commitResults from it on stale_round, and on resume when
 * the server is exactly one round ahead of what this tab last showed.
 */
import { renderHook, act } from '@testing-library/react';
import useSimulation from '../app/hooks/useSimulation';

const SID = 'isolated-session';

const gs = (treasury, extraFlags = {}) => ({
  corporate_treasury: treasury, group_reputation: 50, active_event_flags: { ...extraFlags },
});
const bus = [{ bu_id: 'pharma', revenue_base: 18e6, opex_base: 12e6 }];
const dashboard = (round, flags = {}) => ({
  session_id: SID, current_round: round, global_state: gs(50e6 + round * 1e6, flags), business_units: bus,
  history: [
    { round_number: 1, choice_selected: 'option_a', global_state: gs(50e6), business_units: bus },
    { round_number: 2, choice_selected: '', global_state: gs(52e6, flags), business_units: bus },
  ].filter((h) => h.round_number <= round),
});
const storedResult = {
  round_committed: 1, new_round_number: 2,
  events: { strike_triggered: false, decision_regret: { your_choice: 'option_a' } },
  global_state: gs(52e6), business_units: bus,
};
const ok = (payload) => ({ ok: true, status: 200, json: async () => payload });
const fail = (status, body = {}) => ({ ok: false, status, json: async () => body, clone() { return this; } });

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
  window.localStorage.setItem('muressons_session_id', SID);
  jest.spyOn(console, 'warn').mockImplementation(() => {});
  jest.spyOn(console, 'log').mockImplementation(() => {});
  jest.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => { jest.restoreAllMocks(); delete global.fetch; });

describe('F06(b) — stale_round after a lost response rebuilds the results screen', () => {
  test('commitTurn on 409 stale_round fetches the stored result and shows it, staying on the committed round', async () => {
    const calls = [];
    global.fetch = jest.fn(async (url, opts = {}) => {
      const u = String(url);
      calls.push(u);
      if (u.includes('/commit-turn')) return fail(409, { detail: { code: 'stale_round', current_round: 2 } });
      if (u.includes('/commit-result/1')) return ok(storedResult);
      if (u.includes('/dashboard')) return ok(dashboard(1));   // the board the tab is showing: round 1
      return ok({});
    });
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    expect(result.current.roundNumber).toBe(1);

    await act(async () => { await result.current.commitTurn({ decisions: [] }); });

    expect(calls.some((u) => u.includes('/commit-result/1'))).toBe(true);
    expect(result.current.commitResults).not.toBeNull();
    expect(result.current.commitResults.roundCommitted).toBe(1);
    expect(result.current.commitResults.newRoundNumber).toBe(2);
    expect(result.current.commitResults.recovered).toBe(true);
    expect(result.current.events?.decision_regret?.your_choice).toBe('option_a');
    // the board stays on the committed round until Advance, exactly like a live commit
    expect(result.current.roundNumber).toBe(1);
    expect(JSON.parse(window.sessionStorage.getItem(`muressons_pending_results_${SID}`)).roundCommitted).toBe(1);
  });

  test('without a stored result the old re-sync behaviour stands', async () => {
    let dashRound = 1;
    global.fetch = jest.fn(async (url) => {
      const u = String(url);
      if (u.includes('/commit-turn')) { dashRound = 2; return fail(409, { detail: { code: 'stale_round', current_round: 2 } }); }
      if (u.includes('/commit-result/')) return fail(404, { detail: { code: 'no_commit_result' } });
      if (u.includes('/dashboard')) return ok(dashboard(dashRound));
      return ok({});
    });
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    await act(async () => { await result.current.commitTurn({ decisions: [] }); });
    expect(result.current.commitResults).toBeNull();
    expect(result.current.roundNumber).toBe(2);   // re-synced to the server's round
  });
});

describe('F06(b) — resume rebuilds the results when the server is one round ahead of what this tab showed', () => {
  test('a reload after a lost response puts the results screen back', async () => {
    // this tab last showed round 1; the server is on round 2; no pending results in sessionStorage
    window.sessionStorage.setItem(`muressons_last_round_${SID}`, '1');
    global.fetch = jest.fn(async (url) => {
      const u = String(url);
      if (u.includes('/commit-result/1')) return ok(storedResult);
      if (u.includes('/dashboard')) return ok(dashboard(2));
      return ok({});
    });
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    expect(result.current.commitResults?.roundCommitted).toBe(1);
    expect(result.current.commitResults?.recovered).toBe(true);
    expect(result.current.roundNumber).toBe(1);                 // the committed round, under its results
    expect(result.current.globalState?.corporate_treasury).toBe(50e6);   // history row 1 = state entering R1
    expect(result.current.roundChanged).toBe(false);
  });

  test('a facilitator Force Advance is not a lost response — the ordinary resume runs', async () => {
    window.sessionStorage.setItem(`muressons_last_round_${SID}`, '1');
    global.fetch = jest.fn(async (url) => {
      const u = String(url);
      if (u.includes('/commit-result/')) return ok(storedResult);
      if (u.includes('/dashboard')) return ok(dashboard(2, { auto_committed: true }));
      return ok({});
    });
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    expect(result.current.commitResults).toBeNull();
    expect(result.current.roundNumber).toBe(2);
    expect(global.fetch.mock.calls.some(([u]) => String(u).includes('/commit-result/'))).toBe(false);
  });

  test('an ordinary reload on the round the tab was showing does not fetch anything extra', async () => {
    window.sessionStorage.setItem(`muressons_last_round_${SID}`, '2');
    global.fetch = jest.fn(async (url) => (String(url).includes('/dashboard') ? ok(dashboard(2)) : ok({})));
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    expect(result.current.commitResults).toBeNull();
    expect(result.current.roundNumber).toBe(2);
    expect(global.fetch.mock.calls.some(([u]) => String(u).includes('/commit-result/'))).toBe(false);
  });

  test('the round the tab shows is remembered once the board has loaded', async () => {
    global.fetch = jest.fn(async (url) => (String(url).includes('/dashboard') ? ok(dashboard(2)) : ok({})));
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    expect(result.current.roundNumber).toBe(2);
    expect(window.sessionStorage.getItem(`muressons_last_round_${SID}`)).toBe('2');
  });
});
