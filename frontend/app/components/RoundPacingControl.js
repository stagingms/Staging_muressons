'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './RoundPacingControl.module.css';

const TOTAL_ROUNDS = 10;

const MODES = [
    {
        id: 'free',
        label: '🔓 Free Play',
        desc: 'All rounds unlocked immediately',
    },
    {
        id: 'manual',
        label: '✋ Manual',
        desc: 'Facilitator unlocks each round',
    },
    {
        id: 'timed',
        label: '📅 Scheduled',
        desc: 'Pre-schedule unlocks for all rounds',
    },
];

/** Format a per-round date for display */
function fmtScheduledTime(iso) {
    if (!iso) return null;
    try {
        const d = new Date(iso);
        return d.toLocaleString(undefined, {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
    } catch {
        return null;
    }
}

/** Convert ISO to local datetime-local value */
function isoToLocal(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Convert datetime-local value to UTC ISO string */
function localToIso(local) {
    if (!local) return null;
    return new Date(local).toISOString();
}

export default function RoundPacingControl({ sessions: propSessions, selectedSession: globalSelectedSession = null } = {}) {
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    const [sessions, setSessions] = useState(propSessions || []);
    const [sessionId, setSessionId] = useState('');
    const [pacing, setPacing] = useState(null);
    const [mode, setMode] = useState('free');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('');
    const [statusOk, setStatusOk] = useState(true);

    // 10-element array of ISO strings (null = unscheduled)
    const [schedule, setSchedule] = useState(Array(TOTAL_ROUNDS).fill(null));

    // Sync propSessions if provided (facilitator mode — already filtered).
    // Phase 3 (F2): NO silent default-to-first-session. Pacing acting on a
    // cohort the facilitator never consciously chose is how a mode change
    // lands on the wrong room. Selection must be explicit (or follow the
    // dashboard-wide target cohort below).
    useEffect(() => {
        if (propSessions) setSessions(propSessions);
    }, [propSessions]);

    // Follow the dashboard-wide selection when it is present in our list.
    useEffect(() => {
        if (!globalSelectedSession) return;
        const list = propSessions || sessions;
        if (list.some(s => (s?.session_id || s?.id || s) === globalSelectedSession)) {
            setSessionId(globalSelectedSession);
        }
    }, [globalSelectedSession, propSessions]); // eslint-disable-line react-hooks/exhaustive-deps

    // Fetch sessions list — only in God Mode (no propSessions)
    useEffect(() => {
        if (propSessions) return; // skip: caller provides sessions
        fetch(`${API}/api/admin/sessions`)
            .then(r => r.ok ? r.json() : [])
            .then(d => {
                const list = Array.isArray(d) ? d : (d?.sessions || []);
                setSessions(list);
                // Phase 3 (F2): no auto-select of the first session — see above.
            })
            .catch(() => { });
    }, [API]); // eslint-disable-line react-hooks/exhaustive-deps

    // Fetch current pacing when session changes
    const fetchPacing = useCallback(async () => {
        if (!sessionId) return;
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/pacing`);
            if (res.ok) {
                const data = await res.json();
                setPacing(data);
                setMode(data.mode);
                if (Array.isArray(data.schedule) && data.schedule.length > 0) {
                    // Pad/trim to TOTAL_ROUNDS
                    const arr = [...data.schedule];
                    while (arr.length < TOTAL_ROUNDS) arr.push(null);
                    setSchedule(arr.slice(0, TOTAL_ROUNDS));
                } else {
                    setSchedule(Array(TOTAL_ROUNDS).fill(null));
                }
            }
        } catch { /* offline */ }
    }, [API, sessionId]);

    useEffect(() => { fetchPacing(); }, [fetchPacing]);

    const flash = (msg, ok = true) => {
        setStatus(msg);
        setStatusOk(ok);
        setTimeout(() => setStatus(''), 4000);
    };

    const applyPacing = async () => {
        if (!sessionId) return;
        setLoading(true);
        try {
            const body = { mode };
            if (mode === 'timed') {
                body.schedule = schedule;
                body.interval_seconds = 0;
            }
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/pacing`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (res.ok) {
                const data = await res.json();
                setPacing(data);
                flash('✅ Pacing updated');
            } else {
                flash('❌ Failed to update pacing', false);
            }
        } catch {
            flash('❌ Connection error', false);
        } finally {
            setLoading(false);
        }
    };

    const unlockNext = async () => {
        if (!sessionId) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/unlock-next`, {
                method: 'POST',
            });
            if (res.ok) {
                const data = await res.json();
                setPacing(prev => ({ ...prev, unlocked_round: data.unlocked_round }));
                flash(`✅ Round ${data.unlocked_round} unlocked`);
            } else {
                flash('❌ Unlock failed', false);
            }
        } catch {
            flash('❌ Connection error', false);
        } finally {
            setLoading(false);
        }
    };

    const clearSchedule = () => setSchedule(Array(TOTAL_ROUNDS).fill(null));

    const setRoundTime = (roundIdx, localVal) => {
        setSchedule(prev => {
            const next = [...prev];
            next[roundIdx] = localToIso(localVal);
            return next;
        });
    };

    const clearRound = (roundIdx) => {
        setSchedule(prev => {
            const next = [...prev];
            next[roundIdx] = null;
            return next;
        });
    };

    // Derive display label for session in dropdown
    const sessionLabel = (s) => {
        const name = s.cohort_name || '(unnamed)';
        const code = s.short_code || s.session_id?.slice(0, 8);
        return `${name} · ${code}`;
    };

    const currentRound = pacing?.unlocked_round === 999 ? '∞' : (pacing?.unlocked_round ?? '—');
    const scheduledCount = schedule.filter(Boolean).length;
    const now = new Date();

    return (
        <div className={styles.panel}>
            <h2 className={styles.title}>Round Pacing Control</h2>
            <p className={styles.subtitle}>Set the pace for round progression — per session.</p>

            {/* Session selector */}
            <div className={styles.fieldGroup}>
                <label className={styles.label}>Session</label>
                <select
                    className={styles.select}
                    value={sessionId}
                    onChange={e => setSessionId(e.target.value)}
                >
                    <option value="">— Select a cohort —</option>
                    {sessions.map(s => {
                        const id = s.session_id || s.id;
                        return (
                            <option key={id} value={id}>
                                {sessionLabel(s)}
                            </option>
                        );
                    })}
                </select>
            </div>

            {/* Current status */}
            {pacing && (
                <div className={styles.statusBox}>
                    <div className={styles.statusItem}>
                        <div className={styles.statusKey}>Mode</div>
                        <div className={styles.statusVal}>
                            {pacing.mode === 'free' ? '🔓 Free Play' :
                                pacing.mode === 'manual' ? '✋ Manual' : '📅 Scheduled'}
                        </div>
                    </div>
                    <div className={styles.statusItem}>
                        <div className={styles.statusKey}>Unlocked up to</div>
                        <div className={styles.statusVal}>Round {currentRound}</div>
                    </div>
                    {pacing.next_unlock_at && (
                        <div className={styles.statusItem}>
                            <div className={styles.statusKey}>Next unlock</div>
                            <div className={styles.statusValWarning}>
                                {fmtScheduledTime(pacing.next_unlock_at) || pacing.next_unlock_at}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Mode selector — always 3 columns, never wraps */}
            <div className={styles.modeRow}>
                {MODES.map(m => (
                    <button
                        key={m.id}
                        className={`${styles.modeBtn} ${mode === m.id ? styles.modeBtnActive : ''}`}
                        onClick={() => setMode(m.id)}
                    >
                        <span className={styles.modeBtnLabel}>{m.label}</span>
                        <span className={styles.modeBtnDesc}>{m.desc}</span>
                    </button>
                ))}
            </div>

            {/* Scheduled mode: 10-round grid */}
            {mode === 'timed' && (
                <>
                    <div className={styles.scheduleGrid}>
                        <div className={styles.scheduleHeader}>
                            <span className={styles.scheduleHeaderLabel}>Round</span>
                            <span className={styles.scheduleHeaderLabel}>Unlock Date &amp; Time</span>
                            <span />
                        </div>
                        {Array.from({ length: TOTAL_ROUNDS }, (_, i) => {
                            const roundNum = i + 1;
                            const iso = schedule[i];
                            const isPast = iso && new Date(iso) < now;
                            const isActive = pacing?.unlocked_round === roundNum;
                            const isScheduled = Boolean(iso) && !isPast;
                            const dotClass =
                                isPast ? styles.scheduleDotPast :
                                    isActive ? styles.scheduleDotActive :
                                        isScheduled ? styles.scheduleDotScheduled :
                                            styles.scheduleDot;

                            return (
                                <div
                                    key={roundNum}
                                    className={`${styles.scheduleRow} ${isPast ? styles.scheduleRowPast : ''}`}
                                >
                                    <span className={styles.scheduleRoundLabel}>
                                        <span className={dotClass} />
                                        R{roundNum}
                                    </span>
                                    <input
                                        type="datetime-local"
                                        className={styles.scheduleDateInput}
                                        value={isoToLocal(iso)}
                                        onChange={e => setRoundTime(i, e.target.value)}
                                        disabled={isPast}
                                    />
                                    <button
                                        className={styles.scheduleClearBtn}
                                        onClick={() => clearRound(i)}
                                        title="Clear"
                                        disabled={!iso}
                                    >
                                        ✕
                                    </button>
                                </div>
                            );
                        })}
                        {scheduledCount > 0 && (
                            <div className={styles.scheduleNote}>
                                {scheduledCount} of {TOTAL_ROUNDS} rounds scheduled
                            </div>
                        )}
                    </div>
                </>
            )}

            {/* Actions */}
            <div className={styles.actions}>
                <button
                    className={styles.btnPrimary}
                    onClick={applyPacing}
                    disabled={loading || !sessionId}
                >
                    {loading ? '⏳ Saving…' : '💾 Apply Pacing'}
                </button>

                {mode === 'manual' && (
                    <button
                        className={styles.btnSuccess}
                        onClick={unlockNext}
                        disabled={loading || !sessionId}
                    >
                        ⏭ Unlock Next Round
                    </button>
                )}

                {mode === 'timed' && scheduledCount > 0 && (
                    <button
                        className={styles.btnWarning}
                        onClick={clearSchedule}
                        disabled={loading}
                    >
                        ✕ Clear All
                    </button>
                )}
            </div>

            {status && (
                <div className={`${styles.statusMsg} ${statusOk ? styles.statusMsgOk : styles.statusMsgErr}`}>
                    {status}
                </div>
            )}
        </div>
    );
}
