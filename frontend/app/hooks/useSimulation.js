'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * API_BASE: Uses Next.js rewrites proxy in development (relative URL → /api/).
 * In production, set NEXT_PUBLIC_API_URL to the backend origin.
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * useSimulation — Full lifecycle hook for the Muressons simulation.
 *
 * Manages:  session start → round config fetch → commit turn → game over
 */
export default function useSimulation() {
    const [sessionId, setSessionId] = useState(null);
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
    const [commitResults, setCommitResults] = useState(null); // Holds results after commit, before advance

    // Track round to auto-open crisis modal
    const prevRoundRef = useRef(1);
    const [roundChanged, setRoundChanged] = useState(false);

    // ── Fetch round config ───────────────────────────────────
    const fetchRoundConfig = useCallback(async (roundNum) => {
        try {
            const res = await fetch(
                `${API_BASE}/api/simulations/round-config/${roundNum}`
            );
            if (!res.ok) return null;
            const data = await res.json();
            setRoundConfig(data);
            return data;
        } catch {
            // Backend offline — use null (frontend falls back to defaults)
            setRoundConfig(null);
            return null;
        }
    }, []);

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
                if (!res.ok) throw new Error(`Start failed: ${res.status}`);
                const data = await res.json();

                setSessionId(data.session_id);
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
                // If backend is offline, start in demo mode
                setSessionId('demo');
                setRoundNumber(1);
                prevRoundRef.current = 0;
                setRoundChanged(true);
                await fetchRoundConfig(1);
                return null;
            } finally {
                setLoading(false);
            }
        },
        [fetchRoundConfig]
    );

    // ── Fetch dashboard state ─────────────────────────────────
    const fetchDashboard = useCallback(
        async (sid) => {
            const id = sid || sessionId;
            if (!id || id === 'demo') return;
            setLoading(true);
            setError(null);
            try {
                const res = await fetch(
                    `${API_BASE}/api/simulations/${id}/dashboard`
                );
                if (!res.ok)
                    throw new Error(`Dashboard fetch failed: ${res.status}`);
                const data = await res.json();

                setRoundNumber(data.current_round);
                setGlobalState(data.global_state);
                setBusinessUnits(data.business_units);
                setHistory(data.history || []);

                // Detect completed session: round > 10 means game is over
                if (data.current_round > 10) {
                    const flags = data.global_state?.active_event_flags || {};
                    // Final report is stored in active_event_flags after R10 commit
                    if (flags.profile) {
                        setFinalReport(flags);
                    } else {
                        // Fallback: build minimal report from available state
                        setFinalReport({
                            profile: 'completed',
                            profile_title: 'Simulation Completed',
                            profile_description: 'This simulation has been completed.',
                            ebitda_2050: data.global_state?.historical_ebitda || 0,
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
            const dashData = await fetchDashboard(playerSessionId);
            if (dashData?.current_round && dashData.current_round <= 10) {
                await fetchRoundConfig(dashData.current_round);
            }
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
                            ebitda_2050: 14_250_000,
                            carbon_tonnage_group: 183,
                            carbon_cost: 45_750,
                            carbon_tax_per_ton: 250,
                            regenerative_multiple: 1.35,
                            mr_breakdown: {
                                base: 1.0,
                                synergy_bonus: 0.3,
                                resilience_bonus: 0.0,
                                truth_premium: 0,
                                instability_discount: -0.4,
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
                const res = await fetch(
                    `${API_BASE}/api/simulations/${sessionId}/commit-turn`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    }
                );
                if (!res.ok) {
                    // Handle round-locked (403) specially
                    if (res.status === 403) {
                        setRoundLocked(true);
                        setLoading(false);
                        return null;
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

                // Check for game over (R10 produces final report in events)
                if (data.events?.profile || data.new_round_number > 10) {
                    setGameOver(true);
                    setFinalReport(data.events);
                }

                // Store commit results for review — do NOT advance the UI yet.
                // roundNumber, globalState, businessUnits stay on the CURRENT round
                // until the user clicks "Advance".
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
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    }
                );
                if (!res.ok) {
                    const body = await res.json().catch(() => ({}));
                    throw new Error(body.detail || `Save failed: ${res.status}`);
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
        if (!commitResults) return;
        const nextRound = commitResults.newRoundNumber;

        // NOW apply the new state to the UI
        setRoundNumber(nextRound);
        setGlobalState(commitResults.globalState);
        setBusinessUnits(commitResults.businessUnits);
        setCommitResults(null);
        setRoundChanged(true);

        if (nextRound <= 10) {
            await fetchRoundConfig(nextRound);
        }

        // Re-fetch full dashboard for history
        try { await fetchDashboard(); } catch { /* non-critical */ }
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

    useEffect(() => {
        if (!sessionId || sessionId === 'demo' || gameOver) return;
        let cancelled = false;

        const poll = async () => {
            try {
                const res = await fetch(
                    `${API_BASE}/api/simulations/${sessionId}/dashboard`
                );
                if (!res.ok || cancelled) return;
                const data = await res.json();

                // Server round is ahead of client round → auto-committed
                if (data.current_round > roundNumber && !commitResults) {
                    console.log(`[AUTO-ADVANCE] Server round ${data.current_round} > client round ${roundNumber}`);
                    setRoundNumber(data.current_round);
                    setGlobalState(data.global_state);
                    setBusinessUnits(data.business_units);
                    setHistory(data.history || []);
                    setAutoAdvanceDetected(true);
                    setRoundChanged(true);

                    // Check for game over
                    if (data.current_round > 10) {
                        const flags = data.global_state?.active_event_flags || {};
                        setFinalReport(flags.profile ? flags : {
                            profile: 'completed',
                            profile_title: 'Simulation Completed',
                            profile_description: 'This simulation has been completed.',
                        });
                        setGameOver(true);
                    } else {
                        await fetchRoundConfig(data.current_round);
                    }

                    // Clear the flag after 5s so the alert auto-dismisses
                    setTimeout(() => { if (!cancelled) setAutoAdvanceDetected(false); }, 5000);
                }
            } catch { /* silent */ }
        };

        const interval = setInterval(poll, 10_000);
        return () => { cancelled = true; clearInterval(interval); };
    }, [sessionId, roundNumber, gameOver, commitResults, fetchRoundConfig]);

    return {
        // State
        sessionId,
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
        roundLocked,
        setRoundLocked,
        commitResults,
        autoAdvanceDetected,

        // Actions
        startSession,
        joinSession,
        playerLogin,
        fetchActiveCohorts,
        fetchDashboard,
        commitTurn,
        advanceToNextRound,
        saveDecisions,
        fetchRoundConfig,
    };
}
