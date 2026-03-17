'use client';

import React, { useState, useEffect, useCallback } from 'react';
import styles from './InterventionConfig.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * RoundDropdown — Standalone component to avoid re-mount on parent re-render.
 */
function RoundDropdown({ value, onChange }) {
    return (
        <select
            className={styles.roundSelect}
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
            onClick={(e) => e.stopPropagation()}
        >
            <option value="">Any Round</option>
            {Array.from({ length: 10 }, (_, i) => (
                <option key={i + 1} value={i + 1}>R{i + 1}</option>
            ))}
        </select>
    );
}

/**
 * InterventionConfig — Facilitator panel to select which overrides
 * and swipe files are active for the currently selected session,
 * and assign each to a specific round.
 */
export default function InterventionConfig({ sessionId }) {
    const [masterOverrides, setMasterOverrides] = useState([]);
    const [masterSwipes, setMasterSwipes] = useState([]);
    const [selectedOverrides, setSelectedOverrides] = useState([]);
    const [selectedSwipes, setSelectedSwipes] = useState([]);
    const [overrideRounds, setOverrideRounds] = useState({});  // {id: round_number|null}
    const [swipeRounds, setSwipeRounds] = useState({});        // {id: round_number|null}
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    // Fetch master list + current session permissions
    useEffect(() => {
        if (!sessionId) return;
        setLoading(true);
        Promise.all([
            fetch(`${API}/api/admin/interventions/master`).then(r => r.json()),
            fetch(`${API}/api/admin/${sessionId}/interventions`).then(r => r.json()),
        ])
            .then(([master, session]) => {
                setMasterOverrides(master.overrides || []);
                setMasterSwipes(master.swipes || []);
                // Current selection — if session returns full objects, extract IDs
                const sessionOvIds = (session.overrides || []).map(o => o.id || o);
                const sessionSwIds = (session.swipes || []).map(s => s.id || s);
                setSelectedOverrides(sessionOvIds);
                setSelectedSwipes(sessionSwIds);
                setOverrideRounds(session.override_rounds || {});
                setSwipeRounds(session.swipe_rounds || {});
            })
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [sessionId]);

    const toggleOverride = (id) => {
        setSelectedOverrides(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
        setSaved(false);
    };

    const toggleSwipe = (id) => {
        setSelectedSwipes(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
        setSaved(false);
    };

    const setOverrideRound = (id, round) => {
        setOverrideRounds(prev => ({ ...prev, [id]: round }));
        setSaved(false);
    };

    const setSwipeRound = (id, round) => {
        setSwipeRounds(prev => ({ ...prev, [id]: round }));
        setSaved(false);
    };

    const selectAll = (type) => {
        if (type === 'overrides') {
            setSelectedOverrides(masterOverrides.map(o => o.id));
        } else {
            setSelectedSwipes(masterSwipes.map(s => s.id));
        }
        setSaved(false);
    };

    const selectNone = (type) => {
        if (type === 'overrides') {
            setSelectedOverrides([]);
        } else {
            setSelectedSwipes([]);
        }
        setSaved(false);
    };

    const handleSave = useCallback(async () => {
        if (!sessionId) return;
        setSaving(true);
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/interventions`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    allowed_overrides: selectedOverrides,
                    allowed_swipes: selectedSwipes,
                    override_rounds: overrideRounds,
                    swipe_rounds: swipeRounds,
                }),
            });
            if (res.ok) {
                setSaved(true);
                setTimeout(() => setSaved(false), 3000);
            }
        } catch (err) {
            console.error('Save failed', err);
        } finally {
            setSaving(false);
        }
    }, [sessionId, selectedOverrides, selectedSwipes, overrideRounds, swipeRounds]);

    if (!sessionId) {
        return (
            <section className={styles.panel}>
                <div className={styles.header}>
                    <span>🎛️</span>
                    <h2>Intervention Config</h2>
                </div>
                <div className={styles.empty}>
                    Select a session in the Leaderboard first to configure its available interventions.
                </div>
            </section>
        );
    }

    if (loading) {
        return (
            <section className={styles.panel}>
                <div className={styles.header}>
                    <span>🎛️</span>
                    <h2>Intervention Config</h2>
                </div>
                <div className={styles.empty}>Loading interventions...</div>
            </section>
        );
    }

    return (
        <section className={styles.panel}>
            <div className={styles.header}>
                <div>
                    <span>🎛️</span>
                    <h2>Intervention Config</h2>
                </div>
                <div className={styles.sessionTag}>
                    Session: {sessionId.slice(0, 12)}…
                </div>
            </div>

            <p className={styles.subtitle}>
                Choose which overrides and swipe files are available, and assign each to a specific round.
            </p>

            <div className={styles.grid}>
                {/* Overrides column */}
                <div className={styles.col}>
                    <div className={styles.colHeader}>
                        <h3>⚡ Manual Overrides</h3>
                        <span className={styles.count}>{selectedOverrides.length}/{masterOverrides.length}</span>
                    </div>
                    <div className={styles.quickActions}>
                        <button onClick={() => selectAll('overrides')}>Select All</button>
                        <button onClick={() => selectNone('overrides')}>Clear All</button>
                    </div>
                    <div className={styles.list}>
                        {masterOverrides.map(ov => (
                            <div key={ov.id} className={`${styles.item} ${selectedOverrides.includes(ov.id) ? styles.selected : ''}`}>
                                <label className={styles.itemLabel}>
                                    <input
                                        type="checkbox"
                                        checked={selectedOverrides.includes(ov.id)}
                                        onChange={() => toggleOverride(ov.id)}
                                    />
                                    <span className={styles.itemIcon}>{ov.icon}</span>
                                    <div className={styles.itemInfo}>
                                        <span className={styles.itemTitle}>{ov.title}</span>
                                        <span className={styles.itemDesc}>{ov.description}</span>
                                    </div>
                                </label>
                                {selectedOverrides.includes(ov.id) && (
                                    <RoundDropdown
                                        value={overrideRounds[ov.id]}
                                        onChange={(val) => setOverrideRound(ov.id, val)}
                                    />
                                )}
                            </div>
                        ))}
                        {masterOverrides.length === 0 && (
                            <div className={styles.emptyList}>No overrides defined in Master DB.</div>
                        )}
                    </div>
                </div>

                {/* Swipes column */}
                <div className={styles.col}>
                    <div className={styles.colHeader}>
                        <h3>✉️ Swipe Files</h3>
                        <span className={styles.count}>{selectedSwipes.length}/{masterSwipes.length}</span>
                    </div>
                    <div className={styles.quickActions}>
                        <button onClick={() => selectAll('swipes')}>Select All</button>
                        <button onClick={() => selectNone('swipes')}>Clear All</button>
                    </div>
                    <div className={styles.list}>
                        {masterSwipes.map(sw => (
                            <div key={sw.id} className={`${styles.item} ${selectedSwipes.includes(sw.id) ? styles.selected : ''}`}>
                                <label className={styles.itemLabel}>
                                    <input
                                        type="checkbox"
                                        checked={selectedSwipes.includes(sw.id)}
                                        onChange={() => toggleSwipe(sw.id)}
                                    />
                                    <span className={styles.itemIcon}>{sw.icon}</span>
                                    <div className={styles.itemInfo}>
                                        <span className={styles.itemTitle}>{sw.label}</span>
                                        <span className={styles.itemDesc}>{sw.title}: {sw.body?.substring(0, 60)}</span>
                                    </div>
                                </label>
                                {selectedSwipes.includes(sw.id) && (
                                    <RoundDropdown
                                        value={swipeRounds[sw.id]}
                                        onChange={(val) => setSwipeRound(sw.id, val)}
                                    />
                                )}
                            </div>
                        ))}
                        {masterSwipes.length === 0 && (
                            <div className={styles.emptyList}>No swipe files defined in Master DB.</div>
                        )}
                    </div>
                </div>
            </div>

            <div className={styles.footer}>
                <button
                    className={styles.saveBtn}
                    onClick={handleSave}
                    disabled={saving}
                >
                    {saving ? '⏳ Saving...' : saved ? '✅ Saved' : '💾 Save Configuration'}
                </button>
            </div>
        </section>
    );
}
