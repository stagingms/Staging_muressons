'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import styles from './RoundPacingControl.module.css';
import { useConfirm } from './ConfirmModal';

const TOTAL_ROUNDS = 10;
const WIZARD_MODE_IDS = { free_play: 'free', scheduled: 'timed' };

const MODES = [
    {
        id: 'free',
        label: '🔓 Free Play',
        desc: 'All rounds open; teams advance together when everyone commits (or the auto-advance timeout lapses)',
    },
    {
        id: 'manual',
        label: '✋ Manual',
        desc: 'Teams commit whenever they are ready (values saved); the next round opens only when you advance it',
    },
    {
        id: 'timed',
        label: '📅 Scheduled',
        desc: 'Teams commit whenever they are ready; each round opens automatically at its scheduled time',
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
    // Free-advance auto-release timeout (minutes in the UI, seconds on the wire).
    // 0 = wait indefinitely for all teams (legacy behaviour).
    const [faTimeoutMin, setFaTimeoutMin] = useState(0);
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('');
    const [statusOk, setStatusOk] = useState(true);
    // RL-1 (UX audit §7.6): shared confirm pattern + the 60s post-unlock
    // relock ("undo") window.
    const [confirmDialog, confirmModal] = useConfirm();
    const [relockWindow, setRelockWindow] = useState(null); // { round, expiresAt }
    const relockTimerRef = useRef(null);

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
        fetch(`${API}/api/admin/sessions`, { credentials: 'include' })
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
                // F-18: cohorts created by the wizard before the pacing fix may
                // still carry its ids ("free_play" / "scheduled") in a restored
                // snapshot; show them as the mode they meant.
                const normMode = WIZARD_MODE_IDS[data.mode] || data.mode;
                setPacing({ ...data, mode: normMode });
                setMode(normMode);
                setFaTimeoutMin(Math.round((data.free_advance_timeout_seconds || 0) / 60));
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
            if (mode === 'free') {
                body.free_advance_timeout_seconds = Math.max(0, Math.round((Number(faTimeoutMin) || 0) * 60));
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

    // RB-2: live commit tally for confirm-dialog blast radius. Best-effort —
    // the confirm still works (with generic copy) if the pulse is unreachable.
    const fetchCommitTally = async () => {
        try {
            const res = await fetch(`${API}/api/admin/cohort-pulse/${sessionId}`, { credentials: 'include' });
            if (res.ok) {
                const d = await res.json();
                return d?.commit_progress || null;
            }
        } catch { /* fall through */ }
        return null;
    };

    // UX audit §7.1: this previously POSTed /unlock-next — an endpoint that has
    // NEVER existed (backend route is /pacing/unlock) — so Manual mode's only
    // advance control 404ed on every click. Fixed URL + credentials, plus a
    // §7.6 blast-radius confirm and a 60s relock (undo) window on success.
    const unlockNext = async () => {
        if (!sessionId || loading) return;
        const nextRound = (Number(pacing?.unlocked_round) || 1) + 1;
        const tally = await fetchCommitTally();
        const impact = [];
        if (tally && tally.total_players > 0) {
            impact.push(`${tally.committed_count} of ${tally.total_players} players have committed Round ${tally.target_round ?? '—'}.`);
            const behind = tally.total_players - tally.committed_count;
            if (behind > 0) impact.push(`${behind} player(s) have not committed — their current round stays open; nothing is auto-committed by unlocking.`);
            if (tally.diverged) impact.push(`⚠ Players are already spread across rounds R${tally.min_round}–R${tally.target_round}.`);
        }
        const ok = await confirmDialog({
            title: `Open Round ${nextRound} for this cohort?`,
            message: 'Players will be able to commit the newly opened round as soon as they are ready. You can relock within 60 seconds if this was a misclick (as long as nobody has committed into it).',
            impact: impact.length ? impact : null,
            confirmLabel: `Unlock Round ${nextRound}`,
            cancelLabel: 'Cancel',
            danger: false,
        });
        if (!ok) return;
        setLoading(true);
        try {
            // F-34: send the round we are opening so a double-click or a retried
            // request is a no-op server-side instead of opening two rounds.
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/pacing/unlock`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_round: nextRound }),
            });
            if (res.ok) {
                const data = await res.json();
                setPacing(prev => ({ ...prev, unlocked_round: data.unlocked_round }));
                flash(data.already_unlocked
                    ? `ℹ️ Round ${data.unlocked_round} was already open`
                    : `✅ Round ${data.unlocked_round} unlocked`);
                // Arm the 60s relock window.
                if (relockTimerRef.current) clearTimeout(relockTimerRef.current);
                setRelockWindow({ round: data.unlocked_round, expiresAt: Date.now() + 60_000 });
                relockTimerRef.current = setTimeout(() => setRelockWindow(null), 60_000);
            } else if (res.status === 403) {
                flash('❌ You do not have permission to advance this cohort.', false);
            } else {
                let detail = '';
                try { detail = (await res.json())?.detail || ''; } catch { /* ignore */ }
                flash(`❌ Unlock failed${detail ? ` — ${detail}` : ''}`, false);
            }
        } catch {
            flash('❌ Connection error — the round was NOT unlocked.', false);
        } finally {
            setLoading(false);
        }
    };

    // RL-1 (UX audit §7.6): inverse of unlock — refused server-side (409) if any
    // player already committed into the round being relocked.
    const relockRound = async () => {
        if (!sessionId || loading || !relockWindow) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/pacing/relock`, {
                method: 'POST', credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                setPacing(prev => ({ ...prev, unlocked_round: data.unlocked_round }));
                setRelockWindow(null);
                if (relockTimerRef.current) clearTimeout(relockTimerRef.current);
                flash(`↩️ Relocked — cohort is back to Round ${data.unlocked_round}`);
            } else {
                let detail = '';
                try { detail = (await res.json())?.detail || ''; } catch { /* ignore */ }
                flash(`❌ Could not relock${detail ? ` — ${detail}` : ''}`, false);
            }
        } catch {
            flash('❌ Connection error — nothing was changed.', false);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => () => { if (relockTimerRef.current) clearTimeout(relockTimerRef.current); }, []);

    const forceAdvance = async () => {
        if (!sessionId || loading) return;
        const tally = await fetchCommitTally();
        const impact = [];
        if (tally && tally.total_players > 0) {
            const behind = tally.total_players - tally.committed_count;
            impact.push(`${tally.committed_count} of ${tally.total_players} players have committed Round ${tally.target_round ?? '—'}.`);
            impact.push(behind > 0
                ? `${behind} player(s) will be AUTO-COMMITTED — from their saved draft if one exists, otherwise with defaults (Option B, $1 per business unit).`
                : 'Every player has already committed — this releases the barrier only.');
        } else {
            impact.push('Any player who hasn’t committed will be auto-committed from saved decisions (or defaults if nothing was saved).');
        }
        const ok = await confirmDialog({
            title: 'Force-advance this cohort now?',
            message: 'This releases the waiting barrier immediately. Auto-committed rounds are flagged and disclosed to the affected players and in the debrief.',
            impact,
            confirmLabel: 'Force Advance',
            cancelLabel: 'Cancel',
            danger: true,
        });
        if (!ok) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/force-advance`, {
                method: 'POST', credentials: 'include',
            });
            flash(res.ok ? '✅ Advancing — stragglers auto-committed' : '❌ Force-advance failed', res.ok);
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

            {/* Free mode: auto-release timeout + manual force-advance */}
            {mode === 'free' && (
                <div style={{ marginTop: 12, padding: '12px 14px', borderRadius: 10, background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#c7d2fe', marginBottom: 4 }}>Auto-advance when everyone commits — or after a timeout</div>
                    <div style={{ fontSize: 'var(--type-caption)', color: '#94a3b8', marginBottom: 10 }}>
                        A round advances as soon as all teams commit. Set a per-round time limit so one absent
                        team can’t stall the cohort — when it lapses, any team that hasn’t committed is
                        auto-committed from its saved decisions. 0 = wait indefinitely.
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                        <label style={{ fontSize: 'var(--type-caption)', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: 6 }}>
                            Per-round limit
                            <input
                                type="number" min={0} max={120} step={1} value={faTimeoutMin}
                                onChange={e => setFaTimeoutMin(e.target.value)}
                                style={{ width: 68, padding: '4px 8px', borderRadius: 6, border: '1px solid rgba(148,163,184,0.3)', background: 'rgba(15,23,42,0.6)', color: '#e2e8f0', fontFamily: "'JetBrains Mono', monospace" }}
                            />
                            min
                        </label>
                        <span style={{ fontSize: 'var(--type-caption)', color: '#64748b' }}>
                            {Number(faTimeoutMin) > 0 ? `≈ ${Math.round(Number(faTimeoutMin) * 60)}s` : 'off — waits for all teams'}
                        </span>
                        <button
                            onClick={forceAdvance}
                            disabled={loading || !sessionId}
                            style={{
                                marginLeft: 'auto', padding: '6px 14px', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: 'var(--type-caption)',
                                border: '1px solid rgba(245,158,11,0.5)', background: 'rgba(245,158,11,0.14)', color: '#fbbf24',
                                opacity: (loading || !sessionId) ? 0.5 : 1,
                            }}
                        >⏭️ Force Advance Now</button>
                    </div>
                </div>
            )}

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
                        disabled={loading || !sessionId || (Number(pacing?.unlocked_round) || 1) >= TOTAL_ROUNDS}
                        title={(Number(pacing?.unlocked_round) || 1) >= TOTAL_ROUNDS ? 'All rounds are unlocked' : undefined}
                    >
                        {(Number(pacing?.unlocked_round) || 1) >= TOTAL_ROUNDS ? '✔ All Rounds Unlocked' : '⏭ Unlock Next Round'}
                    </button>
                )}

                {mode === 'manual' && relockWindow && (
                    <button
                        className={styles.btnWarning}
                        onClick={relockRound}
                        disabled={loading}
                        title="Undo the unlock you just made — refused automatically if a player has already committed into it"
                    >
                        ↩️ Undo — Relock Round {relockWindow.round}
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
            {confirmModal}
        </div>
    );
}
