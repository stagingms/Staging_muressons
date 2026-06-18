import React, { useState } from 'react';
import styles from './InductPlayerModal.module.css';

export default function InductPlayerModal({ isOpen, onClose, sessions, onInduct }) {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [sessionId, setSessionId] = useState('');
    const [assignedBu, setAssignedBu] = useState('Pharma');
    const [regionId, setRegionId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successData, setSuccessData] = useState(null);

    const API = process.env.NEXT_PUBLIC_API_URL || '';

    const ASSIGNABLE_ROLES = [
        // Single-business verticals
        { value: 'agriculture',                label: '🌾 Agriculture' },
        { value: 'banking_financial_services', label: '🏦 Banking & Finance' },
        { value: 'oil_gas',                    label: '⛽ Oil & Gas' },
        { value: 'retail_fmcg',               label: '🛒 Retail / FMCG' },
        { value: 'technology',                 label: '💻 Technology' },
        { value: 'pharma',                     label: '💊 Pharma / Healthcare' },
        // Legacy conglomerate BUs
        { value: 'Pharma',         label: 'Muressons Pharma (Legacy Conglomerate)' },
        { value: 'Electronics',    label: 'Muressons Electronics (Legacy Conglomerate)' },
        { value: 'Consumer Goods', label: 'Muressons Consumer Goods (Legacy Conglomerate)' },
        { value: 'Software',       label: 'Muressons Software (Legacy Conglomerate)' },
        // Special
        { value: 'Observer',       label: '👁 Observer / Not Assigned' },
    ];

    const REGIONS = [
        { id: 'asean',         label: 'ASEAN',          flag: '🌏' },
        { id: 'south_asia',    label: 'India',           flag: '🇮🇳' },
        { id: 'europe',        label: 'Europe',          flag: '🇪🇺' },
        { id: 'north_america', label: 'North America',   flag: '🇺🇸' },
        { id: 'africa',        label: 'Africa',          flag: '🌍' },
    ];

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const res = await fetch(`${API}/api/admin/players/induct`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    email,
                    session_id: sessionId,
                    assigned_bu: assignedBu,
                    region_id: regionId,
                }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || `Induction failed: ${res.status}`);
            }

            const data = await res.json();
            setSuccessData(data);
            if (onInduct) onInduct(data);

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = () => {
        const textToCopy = `Welcome to Muressons!\nLogin Link: ${window.location.origin}\nPlayer ID: ${successData.player_id}\nPassword: ${successData.password}`;
        navigator.clipboard.writeText(textToCopy);
    };

    const handleClose = () => {
        setSuccessData(null);
        setName('');
        setEmail('');
        setSessionId('');
        setAssignedBu('Pharma');
        setRegionId('');
        onClose();
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <h2>Induct New Player</h2>
                    <button className={styles.closeBtn} onClick={handleClose}>×</button>
                </div>

                <div className={styles.body}>
                    {successData ? (
                        <div className={styles.successScreen}>
                            <div className={styles.successIcon}>✓</div>
                            <h3>Player Successfully Inducted!</h3>
                            <p>Here are their temporary credentials. Please copy and send them securely.</p>

                            <div className={styles.credentialsBox}>
                                <div className={styles.credRow}>
                                    <span className={styles.credLabel}>Player ID:</span>
                                    <span className={styles.credValue}>{successData.player_id}</span>
                                </div>
                                <div className={styles.credRow}>
                                    <span className={styles.credLabel}>Password:</span>
                                    <span className={styles.credValue} style={{ fontFamily: 'monospace', letterSpacing: '1px' }}>{successData.password}</span>
                                </div>
                                <button className={styles.copyBtn} onClick={handleCopy}>
                                    📋 Copy to Clipboard
                                </button>
                            </div>
                            <button className={styles.submitBtn} onClick={handleClose}>Finish</button>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className={styles.form}>
                            {error && <div className={styles.error}>{error}</div>}

                            <div className={styles.formGroup}>
                                <label>Player Name / Call Sign</label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={e => setName(e.target.value)}
                                    required
                                    placeholder="e.g. Jane Doe"
                                />
                            </div>

                            <div className={styles.formGroup}>
                                <label>Email Address</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    required
                                    placeholder="jane@example.com"
                                />
                            </div>

                            <div className={styles.formGroup}>
                                <label>Assign to Cohort</label>
                                <select
                                    value={sessionId}
                                    onChange={e => setSessionId(e.target.value)}
                                    required
                                >
                                    <option value="" disabled>Select an active session...</option>
                                    {sessions.map(s => (
                                        <option key={s.session_id} value={s.session_id}>
                                            {s.cohort_name} ({s.short_code || s.session_id.slice(0, 8)})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className={styles.formGroup}>
                                <label>Business Unit / Industry Vertical</label>
                                <select
                                    value={assignedBu}
                                    onChange={e => setAssignedBu(e.target.value)}
                                    required
                                >
                                    <option value="">-- Select Role --</option>
                                    {ASSIGNABLE_ROLES.map(r => (
                                        <option key={r.value} value={r.value}>{r.label}</option>
                                    ))}
                                </select>
                            </div>

                            <div className={styles.formGroup}>
                                <label>
                                    Geographic Region
                                    <span style={{color:'#94a3b8', fontWeight:400, marginLeft:'6px', fontSize:'12px'}}>
                                        (overrides cohort default)
                                    </span>
                                </label>
                                <select
                                    value={regionId}
                                    onChange={e => setRegionId(e.target.value)}
                                >
                                    <option value="">-- Select Region --</option>
                                    {REGIONS.map(r => (
                                        <option key={r.id} value={r.id}>{r.flag} {r.label}</option>
                                    ))}
                                </select>
                            </div>

                            <div className={styles.footer}>
                                <button type="button" className={styles.cancelBtn} onClick={handleClose}>Cancel</button>
                                <button type="submit" className={styles.submitBtn} disabled={loading || !sessionId}>
                                    {loading ? 'Inducting...' : 'Induct & Generate Credentials'}
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}
