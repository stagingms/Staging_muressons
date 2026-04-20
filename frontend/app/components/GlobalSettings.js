'use client';
import { useState, useEffect } from 'react';
import styles from './GlobalSettings.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function GlobalSettings() {
    const [settings, setSettings] = useState(null);
    const [freezeMsg, setFreezeMsg] = useState('System maintenance in progress.');
    const [status, setStatus] = useState('');

    const load = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/settings`);
            if (res.ok) setSettings(await res.json());
        } catch {}
    };
    useEffect(() => { load(); }, []);

    const toggleCohortCreation = async () => {
        const newVal = !settings.allow_facilitator_cohort_creation;
        const res = await fetch(`${API}/api/admin/god/settings`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ allow_facilitator_cohort_creation: newVal }),
        });
        if (res.ok) { setSettings(await res.json()); setStatus(`Cohort creation ${newVal ? 'enabled' : 'disabled'}`); }
    };

    const handleFreeze = async () => {
        if (!confirm('⚠️ This will freeze ALL active simulations. Continue?')) return;
        const res = await fetch(`${API}/api/admin/god/freeze`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: freezeMsg }),
        });
        if (res.ok) { load(); setStatus('System FROZEN'); }
    };

    const handleUnfreeze = async () => {
        const res = await fetch(`${API}/api/admin/god/unfreeze`, { method: 'POST' });
        if (res.ok) { load(); setStatus('System UNFROZEN'); }
    };

    if (!settings) return <div className={styles.loading}>Loading settings…</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>⚙️</span>
                <div>
                    <h2>Global Settings</h2>
                    <p className={styles.subtitle}>Platform-wide toggles and emergency controls.</p>
                </div>
            </div>

            {status && <div className={styles.statusMsg}>{status}</div>}

            {/* Cohort Creation Toggle (#1) */}
            <div className={styles.settingCard}>
                <div className={styles.settingInfo}>
                    <h3>🏗️ Facilitator Cohort Creation</h3>
                    <p>When enabled, facilitators can create their own cohorts (up to their limit). When disabled, only God Mode can create cohorts.</p>
                </div>
                <button
                    className={`${styles.toggle} ${settings.allow_facilitator_cohort_creation ? styles.toggleOn : styles.toggleOff}`}
                    onClick={toggleCohortCreation}
                >
                    <span className={styles.toggleKnob} />
                    <span className={styles.toggleLabel}>
                        {settings.allow_facilitator_cohort_creation ? 'ENABLED' : 'DISABLED'}
                    </span>
                </button>
            </div>

            {/* Emergency Freeze (#7) */}
            <div className={`${styles.settingCard} ${settings.system_frozen ? styles.frozenCard : ''}`}>
                <div className={styles.settingInfo}>
                    <h3>🚨 Emergency Freeze</h3>
                    <p>Instantly pause all simulations. A maintenance banner will be shown to all connected users.</p>
                    {settings.system_frozen && (
                        <div className={styles.frozenBadge}>
                            ❄️ System frozen since {new Date(settings.freeze_started_at).toLocaleString()}
                        </div>
                    )}
                </div>
                {!settings.system_frozen ? (
                    <div className={styles.freezeControls}>
                        <input
                            className={styles.freezeInput}
                            placeholder="Freeze message…"
                            value={freezeMsg}
                            onChange={e => setFreezeMsg(e.target.value)}
                        />
                        <button className={styles.freezeBtn} onClick={handleFreeze}>
                            🔴 Freeze All
                        </button>
                    </div>
                ) : (
                    <button className={styles.unfreezeBtn} onClick={handleUnfreeze}>
                        🟢 Unfreeze System
                    </button>
                )}
            </div>
        </div>
    );
}
