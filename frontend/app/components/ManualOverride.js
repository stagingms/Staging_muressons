'use client';

import { useState, useCallback, useEffect } from 'react';
import styles from './ManualOverride.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * ManualOverride — God Mode buttons for immediate state mutations.
 *
 * Props:
 *  - sessionId: selected session to override
 *  - onOverrideApplied: (result) => void
 */
export default function ManualOverride({ sessionId, onOverrideApplied }) {
    const [confirming, setConfirming] = useState(null);
    const [loading, setLoading] = useState(null);
    const [lastResult, setLastResult] = useState(null);
    const [overrides, setOverrides] = useState([]);

    useEffect(() => {
        if (!sessionId) {
            setOverrides([]);
            return;
        }
        fetch(`${API}/api/admin/${sessionId}/interventions`)
            .then(r => r.ok ? r.json() : { overrides: [] })
            .then(d => setOverrides(d.overrides || []))
            .catch(() => setOverrides([]));
    }, [sessionId]);

    const handleOverride = useCallback(
        async (override) => {
            if (!sessionId) return;
            setLoading(override.id);
            setConfirming(null);

            try {
                const res = await fetch(`${API}/api/admin/${sessionId}/override`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        override_type: override.id,
                        parameters: override.params,
                    }),
                });
                const data = await res.json();
                setLastResult({ id: override.id, ...data });
                onOverrideApplied?.(data);
            } catch (err) {
                setLastResult({ id: override.id, error: err.message });
            } finally {
                setLoading(null);
            }
        },
        [sessionId, onOverrideApplied]
    );

    return (
        <section className={styles.panel}>
            <div className={styles.header}>
                <span>⚡</span>
                <h2>Manual Override</h2>
                {!sessionId && (
                    <span className={styles.noSession}>Select a session first</span>
                )}
            </div>

            <div className={styles.overrides}>
                {overrides.length === 0 && sessionId && (
                    <div style={{ color: 'var(--text-muted)', padding: '1rem', fontStyle: 'italic' }}>No manual overrides are permitted for this cohort.</div>
                )}
                {overrides.map((o) => {
                    const params = o.params && Object.keys(o.params).length > 0
                        ? Object.entries(o.params).map(([k, v]) => `${k}: ${v}`).join(' · ')
                        : null;
                    const tooltipParts = [o.title];
                    if (o.dangerLevel) tooltipParts.push(`Tag: ${o.dangerLevel}`);
                    if (o.description) tooltipParts.push(o.description);
                    if (params) tooltipParts.push(`Parameters: ${params}`);
                    const tooltipText = tooltipParts.join('\n\n');

                    return (
                    <div
                        key={o.id}
                        className={styles.card}
                        style={{ '--ov-color': o.color }}
                        data-tooltip={tooltipText}
                        data-tooltip-pos="above"
                    >
                        <div className={styles.cardHeader}>
                            <span className={styles.ovIcon}>{o.icon}</span>
                            <div>
                                <h3 className={styles.ovTitle}>{o.title}</h3>
                                <span className={`${styles.dangerBadge} ${o.dangerLevel === 'CRITICAL' ? styles.critical : styles.high}`}>
                                    {o.dangerLevel}
                                </span>
                            </div>
                        </div>
                        <p className={styles.ovDesc}>{o.description}</p>

                        {confirming === o.id ? (
                            <div className={styles.confirmRow}>
                                <span className={styles.confirmText}>Are you sure?</span>
                                <button
                                    className={styles.cancelBtn}
                                    onClick={() => setConfirming(null)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className={styles.executeBtn}
                                    onClick={() => handleOverride(o)}
                                    disabled={loading === o.id}
                                >
                                    {loading === o.id ? '⏳' : '🔒'} Execute
                                </button>
                            </div>
                        ) : (
                            <button
                                className={styles.activateBtn}
                                onClick={() => setConfirming(o.id)}
                                disabled={!sessionId || loading}
                            >
                                Activate Override
                            </button>
                        )}

                        {lastResult?.id === o.id && (
                            <div className={`${styles.resultBar} ${lastResult.error ? styles.resultError : ''}`}>
                                {lastResult.error
                                    ? `❌ ${lastResult.error}`
                                    : `✅ ${lastResult.result?.message || 'Applied'}`}
                            </div>
                        )}
                    </div>
                    );
                })}
            </div>
        </section>
    );
}
