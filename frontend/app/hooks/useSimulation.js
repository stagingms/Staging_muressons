'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * API_BASE: Uses Next.js rewrites proxy in development (relative URL → /api/).
 * In production, set NEXT_PUBLIC_API_URL to the backend origin.
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// SEC-3 / F-22: attach the player's identity to every game request.
//   • X-Player-Id  — the team's player id (display / legacy; not a credential).
//   • Authorization: Bearer <player_token> — the signed, session-scoped token
//     minted by /player-login. Since the 2026-09-01 launch audit an OWNED
//     session refuses requests without it (401, code player_token_required),
//     so a forged header can no longer read or commit for another team.
// Header-less requests still work for solo sessions and never block facilitators.
export function playerIdHeader() {
    try {
        if (typeof window === 'undefined') return {};
        const pid = window.localStorage.getItem('muressons_playerId');
        const tok = window.localStorage.getItem('muressons_player_token');
        const h = {};
        if (pid) h['X-Player-Id'] = pid;
        if (tok) h['Authorization'] = `Bearer ${tok}`;
        return h;
    } catch (e) {
        return {};
    }
}

// F-01 (audit 2026-09-04): the server refuses every write from a driver still
// on the issued password with a 403 whose detail is an OBJECT
// ({code: "password_change_required", message}). Surfaces that reliably:
// `errorDetailText` turns any FastAPI detail (string, object, pydantic list)
// into a sentence, and `isPasswordChangeRequired` recognises the code so the
// caller can raise the forced change-password screen instead of showing
// "[object Object]" or "incomplete data".
export function errorDetailText(detail, fallback = 'Request failed.') {
    if (detail == null) return fallback;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        const parts = detail.map(d => (d && typeof d === 'object' ? d.msg || d.message : d)).filter(Boolean);
        return parts.length ? parts.join('; ') : fallback;
    }
    if (typeof detail === 'object') return detail.message || detail.msg || detail.error || fallback;
    return String(detail);
}

export function isPasswordChangeRequired(res, data) {
    return res?.status === 403 && (data?.detail?.code === 'password_change_required');
}

// F-22: a 401 carrying code=player_token_required means the token expired (or
// the client pre-dates tokens). Clear the stale identity so the login screen
// comes back instead of a frozen board. Returns true when it acted.
export function handlePlayerAuthFailure(res, data) {
    try {
        if (res?.status !== 401) return false;
        const code = data?.detail?.code || data?.code;
        if (code !== 'player_token_required') return false;
        if (typeof window !== 'undefined') {
            localStorage.removeItem('muressons_player_token');
            localStorage.removeItem('muressons_session_id');
            localStorage.removeItem('muressons_playerId');
            localStorage.removeItem('muressons_is_observer');
            window.location.reload();
        }
        return true;
    } catch (e) {
        return false;
    }
}

/**
 * useSimulation — Full lifecycle hook for the Muressons simulation.
 *
 * Manages:  session start → round config fetch → commit turn → game over
 */
export default function useSimulation() {
    const [sessionId, setSessionId] = useState(null);
    const [username, setUsernameState] = useState('');
    const [roundNumber, setRoundNumber] = useState(1);
    const [globalState, setGlobalState] = useState(null);
    const [businessUnits, setBusinessUnits] = useState([]);
    const [history, setHistory] = useState([]);
    const [events, setEvents] = useState({});
    const [roundConfig, setRoundConfig] = useState(null);
    const [gameOver, setGameOver] = useState(false);
    const [finalReport, setFinalReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [roundLocked, setRoundLocked] = useState(false);
    // F-18(ii): why the last commit was refused — 'facilitator' (manual/timed
    // pacing) or 'teams' (the free-mode barrier the server now enforces), with
    // the server's own sentence and tally, so the overlay says the right thing.
    const [roundLockReason, setRoundLockReason] = useState(null);
    const [commitResults, setCommitResults] = useState(null); // Holds results after commit, before advance
    const [practiceReset, setPracticeReset] = useState(false); // True when practice round reset occurs
    const [mustChangePassword, setMustChangePassword] = useState(false); // True when player must change password
    // TEAM-1 (UX audit #7): true when signed in with the team's VIEW CODE
    // (MUR-NNN-VIEW). The cockpit renders read-only. Advisory only — the
    // server refuses every mutation from an observer independently.
    const [isObserver, setIsObserver] = useState(false);
    // Session metadata: cohort_name, simulation_mode, etc. — populated from session-info API by page.js
    const [sessionMeta, setSessionMeta] = useState({ cohort_name: null, simulation_mode: null, assigned_bu: null, industry_vertical: null });
    const commitInProgressRef = useRef(false); // Guard against double-submit
    const advanceInProgressRef = useRef(false); // Guard against double-advance

    // Track round to auto-open crisis modal
    const prevRoundRef = useRef(1);
    const [roundChanged, setRoundChanged] = useState(false);

    // audit #11: surface connection health so the UI can show a reconnecting /
    // staleness banner instead of silently displaying an out-of-date board.
    // 'ok' after a good fetch; 'stale' after consecutive failures.
    const [connectionState, setConnectionState] = useState('ok');
    // CONN-1: consecutive failures of the 5s background poller. Separate from
    // _dashFailuresRef because the two run independently.
    const _pollFailuresRef = useRef(0);
    const [lastSyncAt, setLastSyncAt] = useState(null);
    const _dashFailuresRef = useRef(0);
    // audit #12: remember the highest round we already hold so a poll can ask
    // the server for only newer history (?since_round=) instead of re-sending
    // the whole game each time.
    const _highestRoundRef = useRef(1);

    // F-27 (launch audit 2026-09-01): merge a partial history (rounds newer than
    // what we hold) into the one already in state — by round_number, newest
    // server copy wins — so the poller can stop re-downloading the whole game
    // (~1 MB by round 10, every 5 s, per cockpit) and fetch only what changed.
    const mergeHistory = useCallback((prev, incoming) => {
        const byRound = new Map((prev || []).map((h) => [h.round_number, h]));
        for (const h of incoming || []) byRound.set(h.round_number, h);
        return [...byRound.values()].sort((a, b) => a.round_number - b.round_number);
    }, []);

    useEffect(() => {
        if (typeof window !== 'undefined') {
            const savedUsername = localStorage.getItem('muressons_username');
            if (savedUsername) setUsernameState(savedUsername);
        }
    }, []);

    const setUsername = useCallback((val) => {
        setUsernameState(val);
        if (typeof window !== 'undefined') {
            if (val) localStorage.setItem('muressons_username', val);
            else localStorage.removeItem('muressons_username');
        }
    }, []);

    // ── Fetch round config ───────────────────────────────────
    const fetchRoundConfig = useCallback(async (roundNum, sid) => {
        try {
            const sessionParam = sid || sessionId;
            const url = sessionParam
                ? `${API_BASE}/api/simulations/round-config/${roundNum}?session_id=${sessionParam}`
                : `${API_BASE}/api/simulations/round-config/${roundNum}`;
            const res = await fetch(url);
            if (!res.ok) return null;
            const data = await res.json();
            setRoundConfig(data);
            return data;
        } catch {
            // Backend offline — use null (frontend falls back to defaults)
            setRoundConfig(null);
            return null;
        }
    }, [sessionId]);

    // ── Start a new session ───────────────────────────────────
    const startSession = useCallback(
        async (cohortName = 'Default Cohort', facilitatorId = 'admin') => {
            setLoading(true);
            setError(null);
            setGameOver(false);
            setFinalReport(null);
            try {
                const res = await fetch(`${API_BASE}/api/simulations/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        cohort_name: cohortName,
                        facilitator_id: facilitatorId,
                    }),
                });
            if (!res.ok) {
                // 403 = not authorised to start without a cohort
                if (res.status === 403) {
                    throw new Error('JOIN_REQUIRED: Please join a cohort using your session code. Direct session starts are not permitted.');
                }
                throw new Error(`Start failed: ${res.status}`);
            }
                const rawData = await res.json();
                const data = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;

                setSessionId(data.session_id);
                if (typeof window !== 'undefined') {
                    localStorage.setItem('muressons_session_id', data.session_id);
                }
                setRoundNumber(data.round_number);
                setGlobalState(data.global_state);
                setBusinessUnits(data.business_units);
                setHistory([]);
                setEvents({});

                // Signal new round
                prevRoundRef.current = 0;
                setRoundChanged(true);

                // Fetch R1 config
                await fetchRoundConfig(data.round_number);

                return data;
            } catch (err) {
                setError(err.message);
                // Only fall back to demo mode for non-auth errors
                if (!err.message?.startsWith('JOIN_REQUIRED')) {
                    setSessionId('demo');
                    setRoundNumber(1);
                    prevRoundRef.current = 0;
                    setRoundChanged(true);
                    await fetchRoundConfig(1);
                    // Auto-clear transient error after 3s in demo mode
                    setTimeout(() => setError(null), 3000);
                } else {
                    // JOIN_REQUIRED: informational toast, auto-dismiss after 6s
                    // so it never permanently overlays the cockpit or join modal
                    setTimeout(() => setError(null), 6000);
                }
                return null;
            } finally {
                setLoading(false);
            }
        },
        [fetchRoundConfig]
    );

    // ── Start a solo/self-paced session ───────────────────────
    const startSoloSession = useCallback(
        async (playerName = 'Solo Player', decisionParadigm = 'legacy_abc') => {
            setLoading(true);
            setError(null);
            setGameOver(false);
            setFinalReport(null);
            try {
                const res = await fetch(`${API_BASE}/api/simulations/solo-start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        player_name: playerName,
                        decision_paradigm: decisionParadigm,
                    }),
                });
                if (!res.ok) throw new Error(`Solo start failed: ${res.status}`);
                const data = await res.json();

                setSessionId(data.session_id);
                if (typeof window !== 'undefined') {
                    localStorage.setItem('muressons_session_id', data.session_id);
                    localStorage.setItem('muressons_is_solo', 'true');
                }
                setRoundNumber(data.round_number);
                setGlobalState(data.global_state);
                setBusinessUnits(data.business_units);
                setHistory([]);
                setEvents({});

                prevRoundRef.current = 0;
                setRoundChanged(true);

                // Fetch the pre-seeded R1 config (from solo-round-configs or fallback)
                try {
                    const rcRes = await fetch(`${API_BASE}/api/simulations/${data.session_id}/solo-round-configs`);
                    if (rcRes.ok) {
                        const rcData = await rcRes.json();
                        const r1cfg = rcData.round_configs?.['1'];
                        if (r1cfg) setRoundConfig(r1cfg);
                    }
                } catch { /* fallback to standard fetch */ }
                if (!roundConfig) await fetchRoundConfig(1, data.session_id);

                return data;
            } catch (err) {
                setError(err.message);
                return null;
            } finally {
                setLoading(false);
            }
        },
        [fetchRoundConfig, roundConfig]
    );

    // ── Fetch dashboard state ─────────────────────────────────
    const fetchDashboard = useCallback(
        async (sid, opts = {}) => {
            const id = sid || sessionId;
            if (!id || id === 'demo') return;
            setLoading(true);
            setError(null);
            try {
                // audit #12: optional payload trim. Pass { since: N } to fetch only
                // history rounds >= N (the server supports ?since_round=). Default
                // (no since) returns the full history — unchanged behaviour, so
                // existing callers are unaffected.
                const _qs = (opts && opts.since != null)
                    ? `?since_round=${encodeURIComponent(opts.since)}`
                    : '';
                const res = await fetch(
                    `${API_BASE}/api/simulations/${id}/dashboard${_qs}`,
                    { headers: { ...playerIdHeader() } }
                );
                if (!res.ok) {
                    // F-22: an expired/absent player token sends us back to login.
                    if (res.status === 401) {
                        const errData = await res.json().catch(() => ({}));
                        if (handlePlayerAuthFailure(res, errData)) return null;
                    }
                    throw new Error(`Dashboard fetch failed: ${res.status}`);
                }
                const data = await res.json();

                // audit #11: mark the connection healthy on every good fetch.
                _dashFailuresRef.current = 0;
                setConnectionState('ok');
                setLastSyncAt(Date.now());
                if (typeof data.current_round === 'number') {
                    _highestRoundRef.current = Math.max(_highestRoundRef.current, data.current_round);
                }

                setRoundNumber(data.current_round);
                setGlobalState(data.global_state);
                setBusinessUnits(data.business_units);
                setHistory(data.history || []);

                // Detect completed session: round > 10 OR round == 10 with final report
                const flags = data.global_state?.active_event_flags || {};
                if (data.current_round > 10 || (data.current_round === 10 && flags.profile)) {
                    // Final report is stored in active_event_flags after R10 commit
                    if (flags.profile) {
                        setFinalReport(flags);
                    } else {
                        // Fallback: build minimal report from available state
                        setFinalReport({
                            profile: 'completed',
                            profile_title: 'Simulation Completed',
                            profile_description: 'This simulation has been completed.',
                            terminal_ebitda: data.global_state?.historical_ebitda || 0,
                            terminal_value: 0,
                            regenerative_multiple: 1.0,
                            mr_breakdown: {},
                        });
                    }
                    setGameOver(true);
                }

                return data;
            } catch (err) {
                setError(err.message);
                // audit #11: after a couple of consecutive failures, flag the
                // board as stale so the UI can show a reconnecting banner instead
                // of silently presenting out-of-date numbers.
                _dashFailuresRef.current += 1;
                if (_dashFailuresRef.current >= 2) setConnectionState('stale');
                throw err;
            } finally {
                setLoading(false);
            }
        },
        [sessionId]
    );

    // ── Fetch active cohorts for join screen ─────────────────
    const fetchActiveCohorts = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/simulations/public/sessions`);
            if (res.ok) {
                return await res.json();
            }
        } catch (err) {
            console.error(err);
        }
        return { sessions: [] };
    }, []);

    // ── Join a session ────────────────────────────────────────
    const joinSession = useCallback(async (sid, playerId = 'Guest', password = '', playerName = '') => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/simulations/public/sessions/${sid}/join`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_id: playerId, password: password, player_name: playerName })
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || 'Failed to join cohort.');
            }

            const joinData = await res.json();
            // Use the player's own session_id (independent game state)
            const playerSessionId = joinData.session_id;
            setSessionId(playerSessionId);
            if (typeof window !== 'undefined') {
                localStorage.setItem('muressons_session_id', playerSessionId);
                if (joinData.player_token) localStorage.setItem('muressons_player_token', joinData.player_token);
            }
            const dashData = await fetchDashboard(playerSessionId);
            // If game is already over (round > 10), don't fetch round config
            if (dashData?.current_round && dashData.current_round <= 10) {
                await fetchRoundConfig(dashData.current_round);
            }
            return true;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [fetchDashboard]);

    // ── Player login (auto-resolve cohort) ────────────────────
    const playerLogin = useCallback(async (playerId, password) => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/api/simulations/player-login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ player_id: playerId, password }),
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || 'Login failed.');
            }
            const loginData = await res.json();
            const playerSessionId = loginData.session_id;
            setSessionId(playerSessionId);
            if (loginData.username) {
                setUsername(loginData.username);
            }
            if (typeof window !== 'undefined') {
                localStorage.setItem('muressons_session_id', playerSessionId);
                localStorage.setItem('muressons_playerId', playerId);
                // SEC/HIGH-001: store the signed ws ticket for the push channel.
                if (loginData.ws_ticket) {
                    localStorage.setItem('muressons_ws_ticket', loginData.ws_ticket);
                } else {
                    localStorage.removeItem('muressons_ws_ticket');
                }
                // F-22: the HTTP credential — sent by playerIdHeader() on every request.
                if (loginData.player_token) {
                    localStorage.setItem('muressons_player_token', loginData.player_token);
                } else {
                    localStorage.removeItem('muressons_player_token');
                }
            }
            // Flag if first-login password change is required
            if (loginData.must_change_password) {
                setMustChangePassword(true);
            }
            // TEAM-1: observer seat — read-only cockpit. Persisted so a refresh
            // does not silently promote a watcher into the driver's UI.
            setIsObserver(!!loginData.is_observer);
            if (typeof window !== 'undefined') {
                if (loginData.is_observer) localStorage.setItem('muressons_is_observer', 'true');
                else localStorage.removeItem('muressons_is_observer');
            }
            const dashData = await fetchDashboard(playerSessionId);
            if (dashData?.current_round && dashData.current_round <= 10) {
                await fetchRoundConfig(dashData.current_round);
            }
            // Signal round change so the briefing page shows on login
            prevRoundRef.current = 0;
            setRoundChanged(true);
            return loginData;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [fetchDashboard, fetchRoundConfig]);

    // ── Commit a turn ─────────────────────────────────────────
    const commitTurn = useCallback(
        async (payload) => {
            if (!sessionId) throw new Error('No active session');
            // Guard: prevent double-submit (avoids backend 429 rate limit)
            if (commitInProgressRef.current) {
                console.warn('[commitTurn] Commit already in progress — ignoring duplicate call');
                return null;
            }
            commitInProgressRef.current = true;
            setLoading(true);
            setError(null);
            try {
                // Demo mode — simulate locally
                if (sessionId === 'demo') {
                    const nextRound = roundNumber + 1;
                    if (nextRound > 10) {
                        setGameOver(true);
                        // Build synthetic final report from seed data
                        setFinalReport({
                            terminal_ebitda: 14_250_000,
                            carbon_tonnage_group: 183,
                            carbon_cost: 45_750,
                            carbon_tax_per_ton: 250,
                            regenerative_multiple: 1.35,
                            // demo figures shaped like the live calculate_mr breakdown (F-16)
                            mr_breakdown: {
                                base: 1.0,
                                materiality_governance: 0.10,
                                synergy_bonus: 0.15,
                                resilience_bonus: 0.20,
                                truth_premium: 0.15,
                                instability_discount: -0.25,
                            },
                            terminal_value: 230_850_000,
                            exit_multiple: 12.0,
                            final_treasury: 38_500_000,
                            profile: 'derisked_safe_haven',
                            profile_title: 'The De-risked Safe-Haven',
                            profile_description:
                                'A resilient corporation that avoided the worst tail risks. ' +
                                'Investors value the predictability, but innovation is stalling. ' +
                                'Solid, but not transformational.',
                            synergy_score: 120,
                            avg_social_license: 58.5,
                            r10_choice: payload?.decisions?.[0]?.choice_selected || 'option_b',
                        });
                        return null;
                    }
                    setRoundNumber(nextRound);
                    setRoundChanged(true);
                    setEvents({ round_advanced: true, choice: payload?.decisions?.[0]?.choice_selected });
                    await fetchRoundConfig(nextRound);
                    return null;
                }

                // Live mode — call backend
                //
                // CMT-1 (2026-08-02): always send expected_round. The retry
                // below re-POSTs the SAME payload after the 5s cooldown, so a
                // commit whose RESPONSE was lost (proxy timeout, phone waking,
                // flaky venue wifi) used to land a SECOND time — by which point
                // the round had moved on, and the same decisions committed the
                // NEXT round. uq_session_round does not catch that: the round
                // numbers differ. The server has had this guard since ITEM 1;
                // nothing ever sent the field, so it had never once fired.
                const res = await fetch(
                    `${API_BASE}/api/simulations/${sessionId}/commit-turn`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', ...playerIdHeader() },
                        body: JSON.stringify({ ...payload, expected_round: roundNumber }),
                    }
                );
                if (!res.ok) {
                    // A stale-round 409 means an EARLIER attempt of ours already
                    // landed. That is success arriving late, not a failure —
                    // re-sync rather than showing the player an error they can
                    // neither understand nor act on.
                    if (res.status === 409) {
                        const conflict = await res.json().catch(() => ({}));
                        if (conflict?.detail?.code === 'stale_round') {
                            console.warn('[commitTurn] stale round — an earlier attempt already committed; re-syncing');
                            setRoundLocked(false);
                            try { await fetchDashboard(sessionId); } catch { /* the poller will catch up */ }
                            return null;
                        }
                    }
                    // Handle round-locked (403) specially
                    if (res.status === 403) {
                        // F-22: the server refuses to advance a team still on its
                        // initial password. Re-open the change-password flow
                        // rather than telling the player the round is locked.
                        const denied = await res.json().catch(() => ({}));
                        if (denied?.detail?.code === 'password_change_required') {
                            setMustChangePassword(true);
                            setLoading(false);
                            return null;
                        }
                        if (denied?.detail?.code === 'waiting_for_teams') {
                            // F-18(ii): the free-mode barrier, now server-side. Refresh
                            // the board so the tally and the "Waiting for Other Teams"
                            // card reflect the cohort, and say why in the overlay.
                            setRoundLockReason({
                                kind: 'teams',
                                message: errorDetailText(denied.detail, 'Waiting for other teams to commit.'),
                                committed: denied.detail.committed ?? null,
                                teams: denied.detail.teams ?? null,
                                deadlineAt: denied.detail.deadline_at ?? null,
                            });
                            setRoundLocked(true);
                            setLoading(false);
                            commitInProgressRef.current = false;
                            try { await fetchDashboard(sessionId); } catch { /* the poller will catch up */ }
                            return null;
                        }
                        setRoundLockReason({ kind: 'facilitator', message: errorDetailText(denied?.detail, '') });
                        setRoundLocked(true);
                        setLoading(false);
                        return null;
                    }
                    // Handle rate-limit (429) and a busy server (503: F-26 commit
                    // gate queue full / pool exhausted) — both mean "nothing was
                    // lost, try again shortly": auto-retry after the cooldown the
                    // server suggests (Retry-After, default 5s), max 2 retries.
                    if (res.status === 429 || res.status === 503) {
                        const retryCount = payload._retryCount || 0;
                        const retryAfterS = Math.min(30, Math.max(1, Number(res.headers.get('Retry-After')) || 5));
                        if (retryCount < 2) {
                            console.warn(`[commitTurn] ${res.status === 503 ? 'Server busy' : 'Rate limited'} — retry ${retryCount + 1}/2 in ${retryAfterS}s`);
                            commitInProgressRef.current = false;
                            setLoading(false);
                            await new Promise(r => setTimeout(r, retryAfterS * 1000 + 200));
                            return commitTurn({ ...payload, _retryCount: retryCount + 1 });
                        }
                        console.error(`[commitTurn] ${res.status} — max retries exceeded`);
                        throw new Error(res.status === 503
                            ? 'The server is busy processing other teams\' commits. Your decisions are still on screen — please submit again in a moment.'
                            : 'Rate limited. Please wait a few seconds and try again.');
                    }
                    const body = await res.json().catch(() => ({}));
                    const detail = typeof body.detail === 'string' ? body.detail
                        : body.detail ? JSON.stringify(body.detail) : `Commit failed: ${res.status}`;
                    throw new Error(detail);
                }

                // Successful commit — clear locked state
                setRoundLocked(false);
                const data = await res.json();

                // Update events for the results overlay
                setEvents(data.events || {});

                // Check for practice mode reset
                if (data.events?.practice_reset) {
                    // Practice round completed — session was reset to Round 1
                    setRoundNumber(1);
                    setGlobalState(data.global_state);
                    setBusinessUnits(data.business_units);
                    setCommitResults(null);
                    setHistory([]);
                    setPracticeReset(true);
                    setRoundChanged(true);
                    await fetchRoundConfig(1);
                    // Auto-dismiss after 5s
                    setTimeout(() => setPracticeReset(false), 5000);
                    return data;
                }

                // Check for game over (R10 produces final report in events)
                if (data.events?.profile || data.new_round_number > 10) {
                    // Audit F-08 / SEAM-06: the game-over ladder (ArchetypeReveal,
                    // GameOverSummary, Scorecard) renders sim.globalState /
                    // sim.businessUnits, and the poller stops on gameOver, so
                    // without this the live reveal showed the state ENTERING
                    // round 10 while a reload showed the final state.
                    if (data.global_state) setGlobalState(data.global_state);
                    if (Array.isArray(data.business_units)) setBusinessUnits(data.business_units);
                    setGameOver(true);
                    setFinalReport(data.events);
                }

                // Store commit results for review — do NOT advance the UI yet.
                // roundNumber, globalState, businessUnits stay on the CURRENT round
                // until the user clicks "Advance".
                console.log(`[commitTurn] Success: current round ${roundNumber} → new round ${data.new_round_number}`);
                setCommitResults({
                    newRoundNumber: data.new_round_number,
                    events: data.events || {},
                    globalState: data.global_state,
                    businessUnits: data.business_units,
                });

                return data;
            } catch (err) {
                setError(err.message);
                throw err;
            } finally {
                setLoading(false);
                commitInProgressRef.current = false;
            }
        },
        [sessionId, roundNumber, fetchRoundConfig, fetchDashboard]
    );

    // ── Save uncommitted decisions ────────────────────────────
    const saveDecisions = useCallback(
        async (payload) => {
            if (!sessionId || sessionId === 'demo') return null;
            setLoading(true);
            setError(null);
            try {
                const res = await fetch(
                    `${API_BASE}/api/simulations/${sessionId}/save-decisions`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', ...playerIdHeader() },
                        body: JSON.stringify(payload),
                    }
                );
                if (!res.ok) {
                    const body = await res.json().catch(() => ({}));
                    // F-01: raise the forced change-password screen; the page
                    // renders it as soon as the flag is set.
                    if (isPasswordChangeRequired(res, body)) setMustChangePassword(true);
                    throw new Error(errorDetailText(body.detail, `Save failed: ${res.status}`));
                }
                const data = await res.json();

                // Locally cache the saved data so it's instantly available without refresh
                setGlobalState(prev => prev ? {
                    ...prev,
                    saved_allocations: payload.allocations,
                    saved_decision_choice: payload.decision_choice
                } : prev);

                return data;
            } catch (err) {
                setError(err.message);
                throw err;
            } finally {
                setLoading(false);
            }
        },
        [sessionId]
    );

    // ── Advance to next round (after reviewing commit results) ──
    const advanceToNextRound = useCallback(async () => {
        if (!commitResults) {
            console.warn('[advanceToNextRound] No commitResults — ignoring');
            return;
        }
        // Guard against double-advance (e.g. user double-clicks the advance button)
        if (advanceInProgressRef.current) {
            console.warn('[advanceToNextRound] Advance already in progress — ignoring');
            return;
        }
        advanceInProgressRef.current = true;

        const nextRound = commitResults.newRoundNumber;
        console.log(`[advanceToNextRound] Advancing from commitResults: → Round ${nextRound}`);

        // NOW apply the new state to the UI
        setRoundNumber(nextRound);
        setGlobalState(commitResults.globalState);
        setBusinessUnits(commitResults.businessUnits);
        setCommitResults(null);
        setRoundChanged(true);

        try {
            if (nextRound <= 10) {
                await fetchRoundConfig(nextRound);
            }

            // Re-fetch full dashboard for history
            try { await fetchDashboard(); } catch { /* non-critical */ }
        } finally {
            advanceInProgressRef.current = false;
        }
    }, [commitResults, fetchRoundConfig, fetchDashboard]);

    // ── Reset roundChanged flag after a render tick ────────────
    useEffect(() => {
        if (roundChanged) {
            const timer = setTimeout(() => setRoundChanged(false), 100);
            return () => clearTimeout(timer);
        }
    }, [roundChanged]);

    // ── Auto-advance detection (scheduled mode) ──────────────
    // Poll dashboard every 10s to detect if the server auto-committed
    const [autoAdvanceDetected, setAutoAdvanceDetected] = useState(false);
    const autoAdvanceDismissRef = useRef(null);
    const lastAutoAdvancedRoundRef = useRef(0); // Track which round was already flagged

    useEffect(() => {
        if (!sessionId || sessionId === 'demo' || gameOver) return;
        let cancelled = false;

        const poll = async () => {
            try {
                // F-27: ask only for rounds we do not hold yet. The latest
                // global_state + business_units always come back (that is what
                // the badges and the round-advance check read); `history` is
                // empty unless the server has moved on, in which case it holds
                // exactly the new round(s) and is merged into state below.
                const sinceRound = Math.max(1, (_highestRoundRef.current || 1) + 1);
                const res = await fetch(
                    `${API_BASE}/api/simulations/${sessionId}/dashboard?since_round=${sinceRound}`,
                    { headers: { ...playerIdHeader() } }
                );
                if (!res.ok) {                       // CONN-1: 5xx is a failure, not a no-op
                    if (res.status === 401) {        // F-22: token expired → back to login
                        const errData = await res.json().catch(() => ({}));
                        if (handlePlayerAuthFailure(res, errData)) return;
                    }
                    _pollFailuresRef.current += 1;
                    if (_pollFailuresRef.current >= 2) setConnectionState('stale');
                    return;
                }
                if (cancelled) return;
                const data = await res.json();
                // CONN-1: a good poll is the freshest evidence we have.
                _pollFailuresRef.current = 0;
                setConnectionState('ok');
                setLastSyncAt(Date.now());

                // Server round is ahead of client round → facilitator or timer advanced
                if (data.current_round > roundNumber && !commitResults && !advanceInProgressRef.current) {
                    const flags = data.global_state?.active_event_flags || {};
                    const wasAutoCommitted = flags.auto_committed === true;

                    console.log(`[AUTO-ADVANCE] Server round ${data.current_round} > client round ${roundNumber}, auto_committed=${wasAutoCommitted}`);

                    // Update client state to match server
                    setRoundNumber(data.current_round);
                    setGlobalState(data.global_state);
                    setBusinessUnits(data.business_units);
                    // F-27: partial history → merge, never replace. If we somehow
                    // hold nothing older (state lost), fall back to one full fetch.
                    if (Array.isArray(data.history) && data.history.length >= data.current_round) {
                        setHistory(data.history);
                    } else {
                        setHistory((prev) => {
                            if (!prev || prev.length === 0) {
                                fetchDashboard(sessionId).catch(() => {});
                                return data.history || [];
                            }
                            return mergeHistory(prev, data.history);
                        });
                    }
                    _highestRoundRef.current = Math.max(_highestRoundRef.current, data.current_round);
                    setRoundChanged(true);

                    // Only show "Time expired" banner if the backend actually auto-committed
                    // AND we haven't already shown it for this round
                    if (wasAutoCommitted && lastAutoAdvancedRoundRef.current < data.current_round) {
                        lastAutoAdvancedRoundRef.current = data.current_round;
                        setAutoAdvanceDetected(true);

                        // Clear the flag after 5s so the alert auto-dismisses
                        if (autoAdvanceDismissRef.current) clearTimeout(autoAdvanceDismissRef.current);
                        autoAdvanceDismissRef.current = setTimeout(() => setAutoAdvanceDetected(false), 5000);
                    }

                    // Check for game over
                    if (data.current_round > 10 || (data.current_round === 10 && flags.profile)) {
                        setFinalReport(flags.profile ? flags : {
                            profile: 'completed',
                            profile_title: 'Simulation Completed',
                            profile_description: 'This simulation has been completed.',
                        });
                        setGameOver(true);
                    } else {
                        await fetchRoundConfig(data.current_round);
                    }
                }
            } catch {
                // CONN-1 (2026-08-02): this catch used to be `{ /* silent */ }`.
                // ConnectionBanner was already built and already rendered — but
                // connectionState was only ever written by fetchDashboard, which
                // is event-driven (resume / post-commit / quiz). So a player
                // sitting on a round with the backend down saw a frozen board
                // with confident-looking numbers and NO banner at all. The 5s
                // poller is the only thing running at that moment, so it has to
                // be the thing that reports the connection.
                _pollFailuresRef.current += 1;
                if (_pollFailuresRef.current >= 2) setConnectionState('stale');
            }
        };

        const interval = setInterval(poll, 5_000);
        return () => { cancelled = true; clearInterval(interval); };
    }, [sessionId, roundNumber, gameOver, commitResults, fetchRoundConfig, fetchDashboard, mergeHistory]);

    // ── Resume Session from Storage ───────────────────────────
    const resumeSession = useCallback(async (sid) => {
        setSessionId(sid);
        // TEAM-1: restore observer status on refresh BEFORE the board renders,
        // so a watcher never briefly sees a writable cockpit.
        try {
            if (typeof window !== 'undefined') {
                setIsObserver(localStorage.getItem('muressons_is_observer') === 'true');
            }
        } catch { /* private mode */ }
        try {
            const data = await fetchDashboard(sid);
            if (data?.current_round && data.current_round <= 10) {
                await fetchRoundConfig(data.current_round);
            }
            // Signal round change so the briefing page shows on session resume
            prevRoundRef.current = 0;
            setRoundChanged(true);
            return data;
        } catch (err) {
            // Stale session — clear localStorage and show friendly error
            if (typeof window !== 'undefined') {
                localStorage.removeItem('muressons_session_id');
            }
            setSessionId(null);
            setError('SESSION_EXPIRED: Your previous session could not be restored. Please rejoin using your session code.');
            // Auto-clear after 5s so the JoinCohortModal shows
            setTimeout(() => setError(null), 5000);
            return null;
        }
    }, [fetchDashboard, fetchRoundConfig]);

    // ── Logout — clears local session, game state persists on server ──
    const logout = useCallback(() => {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('muressons_session_id');
            localStorage.removeItem('muressons_username');
            localStorage.removeItem('muressons_playerId');
            localStorage.removeItem('muressons_is_solo');
            localStorage.removeItem('muressons_player_token');
            localStorage.removeItem('muressons_ws_ticket');
        }
        // Reset all state to initial values
        setSessionId(null);
        setUsernameState('');
        setRoundNumber(1);
        setGlobalState(null);
        setBusinessUnits([]);
        setHistory([]);
        setEvents({});
        setRoundConfig(null);
        setGameOver(false);
        setFinalReport(null);
        setLoading(false);
        setError(null);
        setRoundLocked(false);
        setCommitResults(null);
        setPracticeReset(false);
        setMustChangePassword(false);
        setSessionMeta({ cohort_name: null, simulation_mode: null, assigned_bu: null, industry_vertical: null });
    }, []);

    return {
        // State
        sessionId,
        username,
        roundNumber,
        globalState,
        businessUnits,
        history,
        events,
        roundConfig,
        gameOver,
        finalReport,
        loading,
        error,
        roundChanged,
        // audit #11: connection health for the reconnecting/staleness banner.
        connectionState,
        lastSyncAt,
        roundLocked,
        setRoundLocked,
        roundLockReason,
        commitResults,
        autoAdvanceDetected,
        setAutoAdvanceDetected,
        practiceReset,
        mustChangePassword,
        isObserver,
        setIsObserver,
        setMustChangePassword,
        sessionMeta,
        setSessionMeta,

        // Actions
        setUsername,
        startSession,
        startSoloSession,
        joinSession,
        playerLogin,
        fetchActiveCohorts,
        fetchDashboard,
        commitTurn,
        advanceToNextRound,
        saveDecisions,
        fetchRoundConfig,
        resumeSession,
        logout,

        // Session type helpers
        isSolo: typeof window !== 'undefined' && localStorage.getItem('muressons_is_solo') === 'true',
    };
}
