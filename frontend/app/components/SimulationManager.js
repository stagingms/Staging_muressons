'use client';

import { useState, useMemo } from 'react';
import styles from './SimulationManager.module.css';
import CreateCohortModal from './CreateCohortModal';
import { formatSessionId } from '../utils/sessionUtils';

export default function SimulationManager({ leaderboard = [], onSessionCreated }) {
    const [createOpen, setCreateOpen] = useState(false);

    const grouped = useMemo(() => {
        const groups = {};
        leaderboard.forEach(s => {
            const fac = s.facilitator_id || 'Unknown';
            if (!groups[fac]) groups[fac] = { facilitator: fac, sessions: [], totalTreasury: 0, avgRound: 0 };
            groups[fac].sessions.push(s);
            groups[fac].totalTreasury += (s.total_cash || s.corporate_treasury || 0);
        });
        Object.values(groups).forEach(g => {
            g.avgRound = g.sessions.length ? Math.round(g.sessions.reduce((s, x) => s + (x.round_number || 1), 0) / g.sessions.length * 10) / 10 : 0;
            g.totalTreasury = g.totalTreasury;
        });
        return Object.values(groups);
    }, [leaderboard]);

    const handleCreated = (newSession) => {
        setCreateOpen(false);
        onSessionCreated?.(newSession);
    };

    const formatCurrency = (val) => val >= 1e6 ? `$${(val / 1e6).toFixed(1)}M` : `$${val?.toFixed(0) || '0'}`;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🗂️</span>
                <div style={{ flex: 1 }}>
                    <h2 className={styles.title}>Simulation Manager</h2>
                    <p className={styles.subtitle}>Manage and compare multiple simulation instances grouped by facilitator.</p>
                </div>
                <button className={styles.createBtn} onClick={() => setCreateOpen(true)}>+ Set Up Cohort</button>
            </div>

            <CreateCohortModal
                isOpen={createOpen}
                onClose={() => setCreateOpen(false)}
                onCreated={handleCreated}
            />

            {grouped.length === 0 ? (
                <div className={styles.empty}>No active simulations.</div>
            ) : (
                <div className={styles.groupGrid}>
                    {grouped.map(g => (
                        <div key={g.facilitator} className={styles.groupCard}>
                            <div className={styles.groupHeader}>
                                <span className={styles.groupFac}>👤 {g.facilitator}</span>
                                <span className={styles.groupCount}>{g.sessions.length} cohort{g.sessions.length !== 1 ? 's' : ''}</span>
                            </div>
                            <div className={styles.groupStats}>
                                <div><span className={styles.statLabel}>Avg Round</span><span className={styles.statVal}>R{g.avgRound}</span></div>
                                <div><span className={styles.statLabel}>Combined Treasury</span><span className={styles.statVal}>{formatCurrency(g.totalTreasury)}</span></div>
                            </div>
                            <div className={styles.sessionList}>
                                {g.sessions.map(s => (
                                    <div key={s.session_id} className={styles.sessionItem}>
                                        <span className={styles.sessionName}>{s.cohort_name || formatSessionId(s)}</span>
                                        <span className={styles.sessionRound}>R{s.round_number || 1}</span>
                                        <span className={styles.sessionTreasury}>{formatCurrency(s.total_cash || s.corporate_treasury || 0)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
