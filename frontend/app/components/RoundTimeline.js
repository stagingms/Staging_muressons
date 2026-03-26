'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './RoundTimeline.module.css';
import { formatSessionId } from '../utils/sessionUtils';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function RoundTimeline({ sessionId, leaderboard = [] }) {
    const [currentRound, setCurrentRound] = useState(1);
    const [pacing, setPacing] = useState(null);

    const fetchData = useCallback(async () => {
        if (!sessionId) return;
        try {
            const [dashRes, paceRes] = await Promise.all([
                fetch(`${API}/api/simulations/${sessionId}/dashboard`),
                fetch(`${API}/api/admin/sessions/${sessionId}/pacing`),
            ]);
            if (dashRes.ok) { const d = await dashRes.json(); setCurrentRound(d.current_round || 1); }
            if (paceRes.ok) { const p = await paceRes.json(); setPacing(p); }
        } catch { /* offline */ }
    }, [sessionId]);

    useEffect(() => { fetchData(); }, [fetchData]);

    const rounds = Array.from({ length: 10 }, (_, i) => i + 1);
    const unlockedRound = pacing?.unlocked_round || 999;

    const getRoundStatus = (r) => {
        if (r < currentRound) return 'completed';
        if (r === currentRound) return 'active';
        if (r <= unlockedRound) return 'unlocked';
        return 'locked';
    };

    const roundLabels = {
        1: 'Water Crisis',
        2: 'CFO Gate',
        3: 'Supply Chain',
        4: 'Data Ethics',
        5: 'Carbon Trading',
        6: 'Talent War',
        7: 'Board Pressure',
        8: 'Innovation',
        9: 'Regulation',
        10: 'Terminal',
    };

    if (!sessionId) {
        return (
            <div className={styles.container}>
                <div className={styles.header}><span className={styles.icon}>📅</span><div><h2 className={styles.title}>Round Timeline</h2><p className={styles.subtitle}>Select a session from the Leaderboard to view its timeline.</p></div></div>
                {leaderboard.length > 0 && (
                    <div className={styles.overviewGrid}>
                        {leaderboard.slice(0, 10).map(s => (
                            <div key={s.session_id} className={styles.overviewCard}>
                                <span className={styles.overviewName}>{s.cohort_name || formatSessionId(s)}</span>
                                <div className={styles.miniTimeline}>
                                    {rounds.map(r => (
                                        <div key={r} className={`${styles.miniDot} ${r < (s.round_number || 1) ? styles.miniComplete : r === (s.round_number || 1) ? styles.miniActive : styles.miniLocked}`} />
                                    ))}
                                </div>
                                <span className={styles.overviewRound}>R{s.round_number || 1}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📅</span>
                <div>
                    <h2 className={styles.title}>Round Timeline</h2>
                    <p className={styles.subtitle}>Visual progress through the 10-round simulation</p>
                </div>
            </div>

            {pacing && (
                <div className={styles.pacingInfo}>
                    <span className={styles.pacingMode}>Mode: <strong>{pacing.mode?.toUpperCase()}</strong></span>
                    {pacing.next_unlock_at && (
                        <span className={styles.pacingTimer}>Next unlock: {new Date(pacing.next_unlock_at).toLocaleTimeString()}</span>
                    )}
                    <span className={styles.pacingUnlocked}>Unlocked up to: R{Math.min(unlockedRound, 10)}</span>
                </div>
            )}

            <div className={styles.timeline}>
                <div className={styles.track} />
                {rounds.map(r => {
                    const status = getRoundStatus(r);
                    return (
                        <div key={r} className={`${styles.node} ${styles[`node_${status}`]}`}>
                            <div className={styles.nodeCircle}>
                                {status === 'completed' ? '✓' : status === 'active' ? '●' : status === 'unlocked' ? '○' : '🔒'}
                            </div>
                            <div className={styles.nodeLabel}>R{r}</div>
                            <div className={styles.nodeDesc}>{roundLabels[r]}</div>
                        </div>
                    );
                })}
            </div>

            <div className={styles.legend}>
                <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendComplete}`} /> Completed</span>
                <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendActive}`} /> Active</span>
                <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendUnlocked}`} /> Unlocked</span>
                <span className={styles.legendItem}><span className={`${styles.legendDot} ${styles.legendLocked}`} /> Locked</span>
            </div>
        </div>
    );
}

