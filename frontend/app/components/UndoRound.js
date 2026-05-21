'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './UndoRound.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function UndoRound({ session }) {
    const sessionId = session?.session_id;
    const shortCode = session?.short_code || sessionId?.slice(0, 8);
    const isPlayer = !!session?.player_id;
    const [currentRound, setCurrentRound] = useState(null);
    const [targetRound, setTargetRound] = useState(null);   // chosen rollback destination
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const fetchRound = useCallback(async () => {
        if (!sessionId) return;
        try {
            const res = await fetch(`${API}/api/simulations/${sessionId}/dashboard`);
            if (res.ok) {
                const data = await res.json();
                const r = data.current_round || 1;
                setCurrentRound(r);
                // Default target = one round back
                setTargetRound(Math.max(1, r - 1));
            }
        } catch { /* offline */ }
    }, [sessionId]);

    useEffect(() => { fetchRound(); }, [fetchRound]);

    // Reset target whenever session changes
    useEffect(() => {
        setTargetRound(null);
        setResult(null);
        setError(null);
    }, [sessionId]);

    const handleUndo = async (cohortWide = false) => {
        if (!sessionId || !targetRound || targetRound >= currentRound) return;

        const roundsToUndo = currentRound - targetRound;
        const promptMsg = cohortWide
            ? `⚠️ Roll back ENTIRE COHORT from Round ${currentRound} → Round ${targetRound}?\n\nThis will delete ALL decisions and state for ${roundsToUndo} round(s) across all connected player sessions.`
            : `⚠️ Roll back from Round ${currentRound} → Round ${targetRound}?\n\nThis will permanently delete decisions and state for ${roundsToUndo} round(s). This cannot be undone.`;

        if (!confirm(promptMsg)) return;
        if (!confirm(`Are you absolutely sure? Click OK to confirm rollback to Round ${targetRound}.`)) return;

        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const url = `${API}/api/admin/${sessionId}/undo-round?cohort_wide=${cohortWide}&target_round=${targetRound}`;
            const res = await fetch(url, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                setResult(data);
                setCurrentRound(data.new_current_round);
                setTargetRound(Math.max(1, data.new_current_round - 1));
            } else {
                setError(data.detail || 'Undo failed');
            }
        } catch {
            setError('Network error');
        } finally {
            setLoading(false);
        }
    };

    // Build the round options: rounds 1..(currentRound-1)
    const roundOptions = currentRound && currentRound > 1
        ? Array.from({ length: currentRound - 1 }, (_, i) => i + 1)
        : [];

    if (!sessionId) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <span className={styles.icon}>⏪</span>
                    <div>
                        <h2 className={styles.title}>Undo Round / Rollback</h2>
                        <p className={styles.subtitle}>Select a session from the Leaderboard to roll it back.</p>
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
                    <p className={styles.subtitle}>
                        Roll back to any earlier round. All rounds between current and target will be permanently erased.
                    </p>
                </div>
            </div>

            {/* Session info row */}
            <div className={styles.infoCard}>
                <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Session</span>
                    <code className={styles.sessionId}>{shortCode}</code>
                </div>
                <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Current Round</span>
                    <span className={styles.roundBadge}>Round {currentRound || '...'}</span>
                </div>
                {targetRound && currentRound && targetRound < currentRound && (
                    <div className={styles.infoRow}>
                        <span className={styles.infoLabel}>Will Revert To</span>
                        <span className={styles.revertBadge}>Round {targetRound}</span>
                    </div>
                )}
                {targetRound && currentRound && targetRound < currentRound && (
                    <div className={styles.infoRow}>
                        <span className={styles.infoLabel}>Rounds Erased</span>
                        <span style={{ fontSize: '0.82rem', color: '#ef4444', fontWeight: 700 }}>
                            {currentRound - targetRound} round{currentRound - targetRound !== 1 ? 's' : ''} deleted
                        </span>
                    </div>
                )}
            </div>

            {/* Target round picker */}
            {roundOptions.length > 0 ? (
                <>
                    <div style={{ marginTop: '1.25rem' }}>
                        <p style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
                            Roll Back To
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                            {roundOptions.map(r => (
                                <button
                                    key={r}
                                    onClick={() => setTargetRound(r)}
                                    style={{
                                        padding: '0.45rem 0.9rem',
                                        borderRadius: '8px',
                                        border: targetRound === r
                                            ? '2px solid #f59e0b'
                                            : '1px solid var(--border-subtle)',
                                        background: targetRound === r
                                            ? 'rgba(245,158,11,0.12)'
                                            : 'var(--bg-card)',
                                        color: targetRound === r ? '#f59e0b' : 'var(--text-secondary)',
                                        fontWeight: targetRound === r ? 700 : 500,
                                        fontSize: '0.85rem',
                                        cursor: 'pointer',
                                        transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                    }}
                                >
                                    Round {r}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Action buttons */}
                    <div style={{ display: 'flex', gap: '1rem', marginTop: '1.25rem' }}>
                        <button
                            className={styles.undoBtn}
                            onClick={() => handleUndo(false)}
                            disabled={loading || !targetRound || targetRound >= currentRound}
                            style={{ flex: 1 }}
                        >
                            {loading
                                ? '⏳ Rolling back...'
                                : `⏪ Roll Back to Round ${targetRound ?? '?'}`}
                        </button>
                        {!isPlayer && (
                            <button
                                className={styles.undoBtn}
                                onClick={() => handleUndo(true)}
                                disabled={loading || !targetRound || targetRound >= currentRound}
                                style={{ flex: 1, background: '#ef4444', borderColor: '#b91c1c' }}
                            >
                                {loading ? '⏳ Rolling cohort...' : `⏪ Roll Back Entire Cohort`}
                            </button>
                        )}
                    </div>
                </>
            ) : (
                currentRound !== null && (
                    <div className={styles.warning}>
                        ℹ️ Cannot undo Round 1 — this is the initial seed state.
                    </div>
                )
            )}

            {result && (
                <div className={styles.success}>
                    ✅ Successfully rolled back to Round {result.new_current_round}
                    {result.deleted_round && ` (deleted up to Round ${result.deleted_round})`}
                </div>
            )}
            {error && (
                <div className={styles.error}>❌ {error}</div>
            )}

            <div className={styles.cautionBox}>
                <strong>⚠️ Caution</strong>
                <ul>
                    <li>All rounds between current and target will be permanently erased</li>
                    <li>Players will be notified of the rollback</li>
                    <li>Decision audit trail for undone rounds will be removed</li>
                    <li>This action cannot be undone</li>
                </ul>
            </div>
        </div>
    );
}
