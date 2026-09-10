/**
 * F06(a) (audit AUDIT_Engines_Flow_Classroom50_20260909) — a reload during an
 * outage must not log the participant out.
 *
 * resumeSession cleared `muressons_session_id` and showed SESSION_EXPIRED on
 * ANY failure of the first dashboard fetch — a network error, a 429, a 5xx,
 * a backend restart — while page.js promised the pointer would be kept
 * (NEW-07). The audit's client probe reproduced it ("OFFLINE_RESUME
 * sessionPointer:false"). Now only 403 / 404 / 410 clear the pointer;
 * everything else keeps the identity, raises the reconnecting banner and
 * retries with backoff until the board loads.
 *
 * These tests run the REAL hook (renderHook) against a stubbed fetch and
 * localStorage — the audit's probe as a permanent test.
 */
import { renderHook, act } from '@testing-library/react';
import useSimulation from '../app/hooks/useSimulation';

const SID = 'isolated-session';

function dashboardPayload(round = 2) {
  return {
    session_id: SID, current_round: round,
    global_state: { corporate_treasury: 50e6, group_reputation: 50, active_event_flags: {} },
    business_units: [{ bu_id: 'pharma', revenue_base: 18e6, opex_base: 12e6 }],
    history: [],
  };
}

function okResponse(payload) {
  return { ok: true, status: 200, json: async () => payload };
}
function failResponse(status) {
  return { ok: false, status, json: async () => ({ detail: `status ${status}` }) };
}

beforeEach(() => {
  jest.useFakeTimers();
  window.localStorage.clear();
  window.sessionStorage.clear();
  window.localStorage.setItem('muressons_session_id', SID);
  jest.spyOn(console, 'warn').mockImplementation(() => {});
  jest.spyOn(console, 'error').mockImplementation(() => {});
  jest.spyOn(console, 'log').mockImplementation(() => {});
});
afterEach(() => {
  jest.useRealTimers();
  jest.restoreAllMocks();
  delete global.fetch;
});

describe('F06 — resumeSession keeps the identity through a transient failure', () => {
  test('a network error (TypeError: Failed to fetch) keeps the pointer, flags the connection stale, and retries', async () => {
    let calls = 0;
    global.fetch = jest.fn(async (url) => {
      calls += 1;
      if (String(url).includes('/dashboard')) {
        if (calls <= 2) throw new TypeError('Failed to fetch');   // the outage
        return okResponse(dashboardPayload(2));                    // the network is back
      }
      return okResponse({});                                        // round-config etc.
    });

    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });

    // after the first failure: identity intact, banner up, no SESSION_EXPIRED
    expect(window.localStorage.getItem('muressons_session_id')).toBe(SID);
    expect(result.current.sessionId).toBe(SID);
    expect(result.current.connectionState).toBe('stale');
    expect(result.current.error ?? null).toBeNull();

    // retry 1 at 2 s fails too, retry 2 at 4 s succeeds
    await act(async () => { jest.advanceTimersByTime(2_000); await Promise.resolve(); });
    await act(async () => { await Promise.resolve(); });
    expect(window.localStorage.getItem('muressons_session_id')).toBe(SID);
    await act(async () => { jest.advanceTimersByTime(4_000); await Promise.resolve(); });
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });

    expect(result.current.sessionId).toBe(SID);
    expect(result.current.roundNumber).toBe(2);
    expect(result.current.globalState?.corporate_treasury).toBe(50e6);
    expect(result.current.connectionState).toBe('ok');
    expect(window.localStorage.getItem('muressons_session_id')).toBe(SID);
  });

  test('a 503 (busy / restarting backend) is retryable too', async () => {
    let calls = 0;
    global.fetch = jest.fn(async (url) => {
      if (String(url).includes('/dashboard')) {
        calls += 1;
        return calls === 1 ? failResponse(503) : okResponse(dashboardPayload(3));
      }
      return okResponse({});
    });
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    expect(window.localStorage.getItem('muressons_session_id')).toBe(SID);
    expect(result.current.sessionId).toBe(SID);
    expect(result.current.connectionState).toBe('stale');
    await act(async () => { jest.advanceTimersByTime(2_000); await Promise.resolve(); });
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    expect(result.current.roundNumber).toBe(3);
    expect(result.current.connectionState).toBe('ok');
  });

  test('a 404 (the session really is gone) clears the pointer and says SESSION_EXPIRED', async () => {
    global.fetch = jest.fn(async (url) => (
      String(url).includes('/dashboard') ? failResponse(404) : okResponse({})
    ));
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    expect(window.localStorage.getItem('muressons_session_id')).toBeNull();
    expect(result.current.sessionId).toBeNull();
    expect(String(result.current.error)).toMatch(/^SESSION_EXPIRED/);
    // no retry is scheduled for a terminal answer
    const dashCalls = global.fetch.mock.calls.filter(([u]) => String(u).includes('/dashboard')).length;
    await act(async () => { jest.advanceTimersByTime(30_000); await Promise.resolve(); });
    expect(global.fetch.mock.calls.filter(([u]) => String(u).includes('/dashboard')).length).toBe(dashCalls);
  });

  test('logout cancels a pending resume retry', async () => {
    global.fetch = jest.fn(async () => { throw new TypeError('Failed to fetch'); });
    const { result } = renderHook(() => useSimulation());
    await act(async () => { await result.current.resumeSession(SID); });
    const before = global.fetch.mock.calls.length;
    act(() => { result.current.logout(); });
    await act(async () => { jest.advanceTimersByTime(20_000); await Promise.resolve(); });
    expect(global.fetch.mock.calls.length).toBe(before);
    expect(result.current.sessionId).toBeNull();
  });
});
