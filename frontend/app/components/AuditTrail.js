'use client';

import { useState, useEffect, useCallback } from 'react';
import styles from './AuditTrail.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const CHOICE_COLORS = {
    option_a: '#10b981',
    option_b: '#f59e0b',
    option_c: '#ef4444',
};

const CHOICE_LABELS = {
    option_a: 'A',
    option_b: 'B',
    option_c: 'C',
};

const BU_LABELS = {
    pharma: '💊 Pharma',
    electronics: '🔌 Electronics',
    consumer_goods: '🛒 Consumer Goods',
    software: '💻 Software',
    hospitals: '🏥 Hospitals',
    clinics: '🩺 Clinics',
    specialised_care: '🔬 Specialised Care',
    telehealth: '📱 Telehealth',
};

export default function AuditTrail({ sessionId }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [expandedRound, setExpandedRound] = useState(null);

    const fetchAudit = useCallback(async () => {
        if (!sessionId) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/audit-trail`);
            if (res.ok) {
                const json = await res.json();
                setData(json);
            }
        } catch (err) {
            console.error('Failed to fetch audit trail:', err);
        } finally {
            setLoading(false);
        }
    }, [sessionId]);

    useEffect(() => {
        fetchAudit();
        const interval = setInterval(fetchAudit, 15000);
        return () => clearInterval(interval);
    }, [fetchAudit]);

    if (!sessionId) {
        return (
            <section className={styles.panel}>
                <div className={styles.header}>
                    <span>📋</span>
                    <h2>Decision Audit Trail</h2>
                </div>
                <div className={styles.empty}>
                    Select a session in the Leaderboard to view player decisions.
                </div>
            </section>
        );
    }

    if (loading && !data) {
        return (
            <section className={styles.panel}>
                <div className={styles.header}>
                    <span>📋</span>
                    <h2>Decision Audit Trail</h2>
                </div>
                <div className={styles.empty}>Loading audit data...</div>
            </section>
        );
    }

    const rounds = data?.rounds || {};
    const roundKeys = Object.keys(rounds).sort((a, b) => Number(b) - Number(a));

    return (
        <section className={styles.panel}>
            <div className={styles.header}>
                <div className={styles.titleRow}>
                    <span>📋</span>
                    <h2>Decision Audit Trail</h2>
                </div>
                <span className={styles.totalBadge}>
                    {data?.total_decisions || 0} decisions
                </span>
            </div>

            <div className={styles.body}>
                {roundKeys.length === 0 ? (
                    <div className={styles.empty}>
                        No decisions recorded yet. Players need to commit at least one round.
                    </div>
                ) : (
                    roundKeys.map(roundKey => {
                        const entries = rounds[roundKey];
                        const isOpen = expandedRound === roundKey;

                        return (
                            <div key={roundKey} className={styles.roundGroup}>
                                <button
                                    className={styles.roundToggle}
                                    onClick={() => setExpandedRound(isOpen ? null : roundKey)}
                                >
                                    <span className={styles.roundIcon}>
                                        {isOpen ? '▾' : '▸'}
                                    </span>
                                    <span className={styles.roundLabel}>
                                        Round {roundKey}
                                    </span>
                                    <span className={styles.roundCount}>
                                        {entries.length} {entries.length === 1 ? 'decision' : 'decisions'}
                                    </span>
                                </button>

                                {isOpen && (
                                    <div className={styles.roundBody}>
                                        <table className={styles.table}>
                                            <thead>
                                                <tr>
                                                    <th>Player</th>
                                                    <th>BU</th>
                                                    <th>Decision</th>
                                                    <th>Choice</th>
                                                    <th style={{ textAlign: 'right' }}>CapEx</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {entries.map((entry, i) => (
                                                    <tr key={i}>
                                                        <td>
                                                            <span className={styles.playerId}>
                                                                {entry.player_id || '—'}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <span className={styles.buTag}>
                                                                {BU_LABELS[entry.bu_id] || entry.bu_id || '—'}
                                                            </span>
                                                        </td>
                                                        <td className={styles.decisionNode}>
                                                            {entry.decision_node_id || '—'}
                                                        </td>
                                                        <td>
                                                            {entry.choice_selected ? (
                                                                <span
                                                                    className={styles.choiceBadge}
                                                                    style={{
                                                                        '--choice-color': CHOICE_COLORS[entry.choice_selected] || '#6366f1'
                                                                    }}
                                                                >
                                                                    {CHOICE_LABELS[entry.choice_selected] || entry.choice_selected}
                                                                </span>
                                                            ) : '—'}
                                                        </td>
                                                        <td style={{ textAlign: 'right' }}>
                                                            {entry.capex_allocated
                                                                ? `$${(entry.capex_allocated / 1_000_000).toFixed(2)}M`
                                                                : '—'
                                                            }
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
            </div>
        </section>
    );
}
