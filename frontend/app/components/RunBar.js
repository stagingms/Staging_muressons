'use client';

/**
 * RunBar — persistent facilitator "run bar" (UX audit §9 / §7.2, RB-2).
 *
 * The Preview/Program idea from broadcast switchers: the state that matters
 * during a live round — which round the cohort is on, who has committed, how
 * the room is paced, whether the backend is healthy — is ALWAYS visible,
 * regardless of which sidebar tab is open. Mounted once in
 * admin/facilitator/page.js above the tab content whenever a cohort is
 * selected.
 *
 * Read-only over GET /api/admin/cohort-pulse/{id} (commit_progress + pacing
 * blocks) and GET /health. The one action it offers — Advance (manual mode) —
 * calls the same /pacing/unlock endpoint as RoundPacingControl, behind the
 * same blast-radius confirm. Engine untouched.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useConfirm } from './ConfirmModal';

const API = process.env.NEXT_PUBLIC_API_URL || '';

function fmtTime(iso) {
    if (!iso) return null;
    try {
        return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch { return null; }
}

export default function RunBar({ cohortId, onOpenPacing }) {
    const [pulse, setPulse] = useState(null);
    const [stale, setStale] = useState(false);
    const [lastAt, setLastAt] = useState(null);
    const [healthy, setHealthy] = useState(true);
    const [busy, setBusy] = useState(false);
    const [note, setNote] = useState('');
    const [relockWindow, setRelockWindow] = useState(null);
    const relockTimerRef = useRef(null);
    const [confirmDialog, confirmModal] = useConfirm();
    const noteTimer = useRef(null);

    const fetchPulse = useCallback(async () => {
        if (!cohortId) return;
        try {
            const res = await fetch(`${API}/api/admin/cohort-pulse/${cohortId}`, { credentials: 'include' });
            if (res.ok) {
                setPulse(await res.json());
                setStale(false);
                setLastAt(new Date());
                return;
            }
            setStale(true);
        } catch {
            setStale(true);
        }
    }, [cohortId]);

    useEffect(() => {
        setPulse(null);
        if (!cohortId) return undefined;
        fetchPulse();
        const iv = setInterval(() => {
            if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
            fetchPulse();
        }, 5000);
        return () => clearInterval(iv);
    }, [cohortId, fetchPulse]);

    useEffect(() => {
        let alive = true;
        const check = async () => {
            try {
                const res = await fetch(`${API}/health`);
                if (alive) setHealthy(res.ok);
            } catch {
                if (alive) setHealthy(false);
            }
        };
        check();
        const iv = setInterval(() => {
            if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
            check();
        }, 15000);
        return () => { alive = false; clearInterval(iv); };
    }, []);

    useEffect(() => () => {
        if (noteTimer.current) clearTimeout(noteTimer.current);
        if (relockTimerRef.current) clearTimeout(relockTimerRef.current);
    }, []);

    const flash = (msg) => {
        setNote(msg);
        if (noteTimer.current) clearTimeout(noteTimer.current);
        noteTimer.current = setTimeout(() => setNote(''), 5000);
    };

    if (!cohortId) return null;

    const cp = pulse?.commit_progress || {};
    const pacing = pulse?.pacing || {};
    const players = (pulse?.teams || []).filter((t) => !t.is_cohort_shell);
    const total = cp.total_players ?? players.length;
    const committed = cp.committed_count ?? 0;
    const targetRound = cp.target_round;
    const diverged = cp.diverged === true;
    const autoCount = cp.auto_committed_count || 0;
    const mode = pacing.mode || '—';
    const nextUnlock = fmtTime(pacing.next_unlock_at);
    const modeLabel = mode === 'free' ? '🔓 Free' : mode === 'manual' ? '✋ Manual' : mode === 'timed' ? '📅 Scheduled' : mode;

    const advance = async () => {
        if (busy) return;
        const nextRound = (Number(pacing.unlocked_round) || 1) + 1;
        const behind = Math.max(0, total - committed);
        const actionTitle = mode === 'timed'
            ? `Unlock Round ${nextRound} early for this cohort?`
            : `Open Round ${nextRound} for this cohort?`;
        const actionBtn = mode === 'timed'
            ? `Unlock Round ${nextRound} Early`
            : `Unlock Round ${nextRound}`;
        const ok = await confirmDialog({
            title: actionTitle,
            message: 'You can relock from Round Pacing within 60 seconds if this was a misclick (as long as nobody has committed into it).',
            impact: total > 0 ? [
                `${committed} of ${total} players have committed Round ${targetRound ?? '—'}.`,
                behind > 0
                    ? `${behind} player(s) have not committed — their current round stays open; unlocking auto-commits nothing.`
                    : 'Every player has committed the current round.',
                ...(diverged ? [`⚠ Players are already spread across rounds R${cp.min_round}–R${targetRound}.`] : []),
            ] : null,
            confirmLabel: actionBtn,
            cancelLabel: 'Cancel',
            danger: false,
        });
        if (!ok) return;
        setBusy(true);
        try {
            // FLOW-11: name the round being opened so a double-click or a retried
            // request is idempotent (the server opens up to target_round, and a
            // repeat answers already_unlocked instead of opening one more).
            const res = await fetch(`${API}/api/admin/sessions/${cohortId}/pacing/unlock`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_round: nextRound }),
            });
            if (res.ok) {
                const d = await res.json();
                flash(`✅ Round ${d.unlocked_round} unlocked — undo available for 60s`);
                if (relockTimerRef.current) clearTimeout(relockTimerRef.current);
                setRelockWindow({ round: d.unlocked_round, expiresAt: Date.now() + 60_000 });
                relockTimerRef.current = setTimeout(() => setRelockWindow(null), 60_000);
                fetchPulse();
            } else if (res.status === 403) {
                flash('❌ You do not have permission to advance this cohort.');
            } else {
                flash('❌ Unlock failed — see Round Pacing for details.');
            }
        } catch {
            flash('❌ Connection error — the round was NOT unlocked.');
        } finally {
            setBusy(false);
        }
    };

    const forceAdvance = async () => {
        if (busy) return;
        const behind = Math.max(0, total - committed);
        const nextRound = (Number(pacing.unlocked_round) || 1) + 1;
        const impact = total > 0 ? [
            `${committed} of ${total} players have committed Round ${targetRound ?? '—'}.`,
            behind > 0
                ? `${behind} player(s) will be AUTO-COMMITTED — from saved drafts or defaults.`
                : 'Every player has committed; barrier will be released.',
            ...(diverged ? [`⚠ Players are already spread across rounds R${cp.min_round}–R${targetRound}.`] : []),
        ] : ['Any player who hasn\'t committed will be auto-committed.'];

        const ok = await confirmDialog({
            title: `Force-advance cohort to Round ${nextRound}?`,
            message: 'This releases the waiting barrier immediately. Auto-committed rounds are flagged and disclosed to the affected players and in the debrief.',
            impact,
            confirmLabel: 'Force Advance',
            cancelLabel: 'Cancel',
            danger: true,
        });
        if (!ok) return;
        setBusy(true);
        try {
            const res = await fetch(`${API}/api/admin/sessions/${cohortId}/force-advance`, {
                method: 'POST', credentials: 'include',
            });
            if (res.ok) {
                flash('✅ Cohort force-advanced — stragglers auto-committed');
                fetchPulse();
            } else {
                flash('❌ Force-advance failed — see Round Pacing for details.');
            }
        } catch {
            flash('❌ Connection error during force-advance.');
        } finally {
            setBusy(false);
        }
    };

    const relockRound = async () => {
        if (!cohortId || busy || !relockWindow) return;
        setBusy(true);
        try {
            const res = await fetch(`${API}/api/admin/sessions/${cohortId}/pacing/relock`, {
                method: 'POST', credentials: 'include',
            });
            if (res.ok) {
                const d = await res.json();
                setRelockWindow(null);
                if (relockTimerRef.current) clearTimeout(relockTimerRef.current);
                flash(`↩️ Relocked — cohort is back to Round ${d.unlocked_round}`);
                fetchPulse();
            } else {
                let detail = '';
                try {
                    const data = await res.json();
                    detail = typeof data?.detail === 'string' ? data.detail : (data?.message || '');
                } catch { /* ignore */ }
                flash(`❌ Could not relock${detail ? ` — ${detail}` : ''}`);
            }
        } catch {
            flash('❌ Connection error during relock.');
        } finally {
            setBusy(false);
        }
    };

    const chip = (bg, border, color) => ({
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '0.25rem 0.65rem', borderRadius: 8, whiteSpace: 'nowrap',
        fontSize: 'var(--type-caption)', fontWeight: 700,
        background: bg, border: `1px solid ${border}`, color,
    });

    return (
        <div
            role="region"
            aria-label="Live run status"
            style={{
                display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap',
                padding: '0.5rem 0.9rem', marginBottom: '0.9rem',
                background: 'linear-gradient(180deg, rgba(15,23,42,0.92), rgba(15,23,42,0.78))',
                border: '1px solid rgba(99,102,241,0.28)', borderRadius: 10,
            }}
        >
            {/* Round */}
            <span style={chip('rgba(99,102,241,0.14)', 'rgba(99,102,241,0.4)', '#c7d2fe')}>
                ROUND {targetRound ?? '—'}
            </span>

            {/* Commit tally: dots + text (never colour-only) */}
            <span style={chip('rgba(30,41,59,0.7)', 'rgba(148,163,184,0.25)', '#e2e8f0')} title="Players committed at the cohort's current round">
                <span aria-hidden="true" style={{ letterSpacing: 2, fontSize: '0.8rem' }}>
                    {total > 0 && total <= 20
                        ? '●'.repeat(committed) + '○'.repeat(Math.max(0, total - committed))
                        : null}
                </span>
                {committed}/{total} committed
                {autoCount > 0 && <span style={{ color: '#fbbf24', fontWeight: 800 }}> · {autoCount} auto</span>}
            </span>

            {/* Divergence warning — shape + text, not colour alone */}
            {diverged && (
                <span style={chip('rgba(245,158,11,0.15)', 'rgba(245,158,11,0.45)', '#fbbf24')}>
                    ⚠ Split field: R{cp.min_round}–R{targetRound}
                </span>
            )}

            {/* Pacing */}
            <span style={chip('rgba(30,41,59,0.7)', 'rgba(148,163,184,0.25)', '#cbd5e1')} title="Round pacing mode">
                {modeLabel}
                {mode === 'timed' && nextUnlock ? ` · opens ${nextUnlock}` : ''}
                {mode === 'manual' ? ' · you advance the round' : ''}
            </span>

            <span style={{ flex: 1 }} />

            {/* Actions across pacing modes */}
            {mode === 'manual' && (
                <button
                    onClick={advance}
                    disabled={busy || (Number(pacing.unlocked_round) || 1) >= 10}
                    style={{
                        padding: '0.3rem 0.8rem', borderRadius: 8, cursor: busy ? 'wait' : 'pointer',
                        fontWeight: 800, fontSize: 'var(--type-caption)',
                        border: '1px solid rgba(34,197,94,0.5)', background: 'var(--positive-soft)', color: 'var(--positive-text)',
                        opacity: (Number(pacing.unlocked_round) || 1) >= 10 ? 0.4 : 1,
                    }}
                    title={(Number(pacing.unlocked_round) || 1) >= 10 ? 'All rounds are unlocked' : 'Open the next round (confirmation follows)'}
                >
                    ⏭ Advance
                </button>
            )}
            {mode === 'free' && (
                <button
                    onClick={forceAdvance}
                    disabled={busy || (Number(pacing.unlocked_round) || 1) >= 10}
                    style={{
                        padding: '0.3rem 0.8rem', borderRadius: 8, cursor: busy ? 'wait' : 'pointer',
                        fontWeight: 800, fontSize: 'var(--type-caption)',
                        border: '1px solid rgba(245,158,11,0.5)', background: 'var(--caution-soft)', color: 'var(--caution-text)',
                        opacity: (Number(pacing.unlocked_round) || 1) >= 10 ? 0.4 : 1,
                    }}
                    title={(Number(pacing.unlocked_round) || 1) >= 10 ? 'All rounds are unlocked' : 'Force advance all teams and release waiting barrier'}
                >
                    ⏭ Force Advance
                </button>
            )}
            {mode === 'timed' && (
                <button
                    onClick={advance}
                    disabled={busy || (Number(pacing.unlocked_round) || 1) >= 10}
                    style={{
                        padding: '0.3rem 0.8rem', borderRadius: 8, cursor: busy ? 'wait' : 'pointer',
                        fontWeight: 800, fontSize: 'var(--type-caption)',
                        border: '1px solid rgba(99,102,241,0.5)', background: 'var(--accent-soft)', color: 'var(--accent-text)',
                        opacity: (Number(pacing.unlocked_round) || 1) >= 10 ? 0.4 : 1,
                    }}
                    title={(Number(pacing.unlocked_round) || 1) >= 10 ? 'All rounds are unlocked' : 'Unlock the scheduled round early'}
                >
                    ⏭ Unlock Early
                </button>
            )}
            {relockWindow && (
                <button
                    onClick={relockRound}
                    disabled={busy}
                    style={{
                        padding: '0.3rem 0.8rem', borderRadius: 8, cursor: busy ? 'wait' : 'pointer',
                        fontWeight: 700, fontSize: 'var(--type-caption)',
                        border: '1px solid rgba(245,158,11,0.5)', background: 'var(--caution-soft)', color: 'var(--caution-text)',
                    }}
                    title="Relock this round (allowed for 60s if no team has committed)"
                >
                    ↩️ Undo (Relock R{relockWindow.round})
                </button>
            )}
            {onOpenPacing && (
                <button
                    onClick={onOpenPacing}
                    style={{
                        padding: '0.3rem 0.7rem', borderRadius: 8, cursor: 'pointer', fontWeight: 600, fontSize: 'var(--type-caption)',
                        border: '1px solid rgba(148,163,184,0.3)', background: 'rgba(30,41,59,0.6)', color: '#cbd5e1',
                    }}
                    title="Round Pacing — mode, schedule, force advance, relock"
                >
                    ⏱ Pacing
                </button>
            )}
            <a
                href={`/admin/projector?cohort=${encodeURIComponent(cohortId)}`}
                target="_blank"
                rel="noreferrer"
                style={{
                    padding: '0.3rem 0.7rem', borderRadius: 8, fontWeight: 600, fontSize: 'var(--type-caption)',
                    border: '1px solid rgba(148,163,184,0.3)', background: 'rgba(30,41,59,0.6)', color: '#cbd5e1',
                    textDecoration: 'none',
                }}
                title="Open the room-screen projector view for this cohort in a new tab"
            >
                🖥 Projector
            </a>

            {/* Health + freshness — text paired with colour */}
            <span
                style={chip(
                    healthy && !stale ? 'rgba(34,197,94,0.1)' : 'rgba(245,158,11,0.14)',
                    healthy && !stale ? 'rgba(34,197,94,0.35)' : 'rgba(245,158,11,0.4)',
                    healthy && !stale ? '#4ade80' : '#fbbf24',
                )}
                title={healthy ? (stale ? 'Cohort data is stale — retrying' : 'Backend healthy, data live') : 'Backend /health is failing'}
            >
                {healthy ? (stale ? '⟳ stale' : '● live') : '⚠ backend'}
                {lastAt ? ` · ${lastAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}` : ''}
            </span>

            {note && (
                <span role="status" style={{ width: '100%', fontSize: 'var(--type-caption)', color: '#cbd5e1' }}>{note}</span>
            )}
            {confirmModal}
        </div>
    );
}
