'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './UndoRound.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function UndoRound({ session }) {
    const sessionId = session?.session_id;
    const isPlayer = !!session?.player_id;
    const [currentRound, setCurrentRound] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const fetchRound = useCallback(async () => {
        if (!sessionId) return;
        try {
            const res = await fetch(`${API}/api/simulations/${sessionId}/dashboard`);
            if (res.ok) {
                const data = await res.json();
                setCurrentRound(data.current_round || 1);
            }
        } catch { /* offline */ }
    }, [sessionId]);

    useEffect(() => { fetchRound(); }, [fetchRound]);

    const handleUndo = async (cohortWide = false) => {
        if (!sessionId) return;
        
        const promptMsg = cohortWide
            ? `⚠️ Undo Round ${currentRound} FOR ENTIRE COHORT?\n\nThis will roll back the template AND ALL connected player sessions to Round ${currentRound - 1}.`
            : `⚠️ Undo Round ${currentRound}?\n\nThis will delete all decisions and state for Round ${currentRound} and revert the session to Round ${currentRound - 1}.\n\nThis action cannot be undone.`;

        if (!confirm(promptMsg)) return;
        if (!confirm(`Are you absolutely sure? Click OK to confirm rollback to Round ${currentRound - 1}.`)) return;

        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/undo-round?cohort_wide=${cohortWide}`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                setResult(data);
                setCurrentRound(data.new_current_round);
            } else {
                setError(data.detail || 'Undo failed');
            }
        } catch {
            setError('Network error');
        } finally {
            setLoading(false);
        }
    };

    if (!sessionId) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <span className={styles.icon}>⏪</span>
                    <div>
                        <h2 className={styles.title}>Undo Round / Rollback</h2>
                        <p className={styles.subtitle}>Select a session from the Leaderboard to undo its latest round.</p>
                    </div>
                </div>
                <div className={styles.empty}>Select a session in the Leaderboard first.</div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>⏪</span>
                <div>
                    <h2 className={styles.title}>Undo Round / Rollback</h2>
                    <p className={styles.subtitle}>Revert the latest round for the selected session. Deletes all decisions and state data for that round.</p>
                </div>
            </div>

            <div className={styles.infoCard}>
                <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Session</span>
                    <code className={styles.sessionId}>{sessionId.slice(0, 16)}...</code>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Current Round</span>
                    <span className={styles.roundBadge}>Round {currentRound || '...'}</span>
                </div>
                {currentRound && currentRound > 1 && (
                    <div className={styles.infoRow}>
                        <span className={styles.infoLabel}>Will Revert To</span>
                        <span className={styles.revertBadge}>Round {currentRound - 1}</span>
                    </div>
                )}
            </div>

            {currentRound && currentRound <= 1 ? (
                <div className={styles.warning}>
                    ℹ️ Cannot undo Round 1 — this is the initial seed state.
                </div>
            ) : (
                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                    <button
                        className={styles.undoBtn}
                        onClick={() => handleUndo(false)}
                        disabled={loading || !currentRound}
                        style={{ flex: 1 }}
                    >
                        {loading ? '⏳ Rolling back...' : `⏪ Undo Round ${currentRound || '?'}`}
                    </button>
                    {!isPlayer && (
                        <button
                            className={styles.undoBtn}
                            onClick={() => handleUndo(true)}
                            disabled={loading || !currentRound}
                            style={{ flex: 1, background: '#ef4444', borderColor: '#b91c1c' }}
                        >
                            {loading ? '⏳ Rolling cohort...' : `⏪ Undo For Entire Cohort`}
                        </button>
                    )}
                </div>
            )}

            {result && (
                <div className={styles.success}>
                    ✅ Successfully rolled back Round {result.deleted_round} → now at Round {result.new_current_round}
                </div>
            )}
            {error && (
                <div className={styles.error}>❌ {error}</div>
            )}

            <div className={styles.cautionBox}>
                <strong>⚠️ Caution</strong>
                <ul>
                    <li>This permanently deletes the round&apos;s decisions and state data</li>
                    <li>Players will be notified their round was rolled back</li>
                    <li>The decision audit trail for the undone round will be removed</li>
                    <li>You can undo multiple rounds by repeating this action</li>
                </ul>
            </div>
        </div>
    );
}
