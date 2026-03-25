'use client';
import { useState, useEffect } from 'react';
import styles from './AnalyticsControlPanel.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const FACILITATOR_ANALYTICS = [
    { key: 'decision_heatmap', label: 'Decision Heatmap', icon: '📊', desc: 'Choice distributions per round' },
    { key: 'time_to_decision', label: 'Time-to-Decision', icon: '⏱', desc: 'Decision speed analytics' },
    { key: 'cohort_comparison', label: 'Cohort Comparison', icon: '📈', desc: 'KPI trajectories side-by-side' },
    { key: 'convergence_analysis', label: 'Convergence Analysis', icon: '🔄', desc: 'Strategy similarity metrics' },
    { key: 'learning_outcomes', label: 'Learning Outcomes', icon: '🎯', desc: 'Quiz scores, badges, engagement' },
    { key: 'risk_exposure', label: 'Risk Exposure', icon: '📉', desc: 'Carbon, NCD, social license trends' },
];

const PLAYER_ANALYTICS = [
    { key: 'peer_benchmarking', label: 'Peer Benchmarking', icon: '🏆', desc: 'Anonymous percentile rankings' },
    { key: 'decision_impact', label: 'Decision Impact', icon: '🧠', desc: 'Per-round KPI attribution' },
    { key: 'what_if_simulator', label: 'What-If Simulator', icon: '📈', desc: 'Counterfactual analysis' },
];

export default function AnalyticsControlPanel() {
    const [visibility, setVisibility] = useState(null);
    const [saving, setSaving] = useState(false);
    const [status, setStatus] = useState(null);

    const DEFAULT_VIS = {
        facilitator: Object.fromEntries(FACILITATOR_ANALYTICS.map(a => [a.key, true])),
        player: Object.fromEntries(PLAYER_ANALYTICS.map(a => [a.key, a.key !== 'what_if_simulator'])),
    };

    useEffect(() => {
        fetch(`${API}/api/admin/god/analytics-visibility`)
            .then(r => r.json())
            .then(d => setVisibility({
                facilitator: { ...DEFAULT_VIS.facilitator, ...(d.facilitator || {}) },
                player: { ...DEFAULT_VIS.player, ...(d.player || {}) },
            }))
            .catch(() => setVisibility(DEFAULT_VIS));
    }, []);

    const toggle = async (role, key) => {
        const updated = {
            ...visibility,
            [role]: { ...visibility[role], [key]: !visibility[role][key] }
        };
        setVisibility(updated);
        setSaving(true);
        try {
            const res = await fetch(`${API}/api/admin/god/analytics-visibility`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updated),
            });
            if (res.ok) {
                setStatus('✅ Saved');
                setTimeout(() => setStatus(null), 2000);
            }
        } catch {}
        setSaving(false);
    };

    if (!visibility) return <div className={styles.loading}>Loading visibility settings…</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🎛️</span>
                <div>
                    <h2 className={styles.title}>Analytics Visibility Controls</h2>
                    <p className={styles.subtitle}>
                        Choose which analytics are available to Facilitators and Players.
                        {saving && <span className={styles.savingBadge}>Saving…</span>}
                        {status && <span className={styles.savedBadge}>{status}</span>}
                    </p>
                </div>
            </div>

            <div className={styles.rolesGrid}>
                {/* Facilitator column */}
                <div className={styles.roleColumn}>
                    <div className={styles.roleHeader}>
                        <span>🎓</span>
                        <h3>Facilitator Dashboard</h3>
                    </div>
                    {FACILITATOR_ANALYTICS.map(a => (
                        <div key={a.key} className={styles.toggleRow}>
                            <div className={styles.toggleInfo}>
                                <span className={styles.toggleIcon}>{a.icon}</span>
                                <div>
                                    <div className={styles.toggleLabel}>{a.label}</div>
                                    <div className={styles.toggleDesc}>{a.desc}</div>
                                </div>
                            </div>
                            <button
                                className={`${styles.toggleBtn} ${visibility.facilitator[a.key] ? styles.toggleOn : styles.toggleOff}`}
                                onClick={() => toggle('facilitator', a.key)}
                            >
                                <span className={styles.toggleKnob} />
                            </button>
                        </div>
                    ))}
                </div>

                {/* Player column */}
                <div className={styles.roleColumn}>
                    <div className={styles.roleHeader}>
                        <span>👤</span>
                        <h3>Player Dashboard</h3>
                    </div>
                    {PLAYER_ANALYTICS.map(a => (
                        <div key={a.key} className={styles.toggleRow}>
                            <div className={styles.toggleInfo}>
                                <span className={styles.toggleIcon}>{a.icon}</span>
                                <div>
                                    <div className={styles.toggleLabel}>{a.label}</div>
                                    <div className={styles.toggleDesc}>{a.desc}</div>
                                </div>
                            </div>
                            <button
                                className={`${styles.toggleBtn} ${visibility.player[a.key] ? styles.toggleOn : styles.toggleOff}`}
                                onClick={() => toggle('player', a.key)}
                            >
                                <span className={styles.toggleKnob} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.footer}>
                <p>💡 Changes take effect immediately. Disabled analytics are hidden from the respective dashboard but data is still collected.</p>
            </div>
        </div>
    );
}
