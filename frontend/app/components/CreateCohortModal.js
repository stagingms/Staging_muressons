import React, { useState, useEffect } from 'react';
import styles from './CreateCohortModal.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function CreateCohortModal({ isOpen, onClose, onCreated }) {
    const [cohortName, setCohortName] = useState('');
    const [facilitatorId, setFacilitatorId] = useState('');
    const [availableFacilitators, setAvailableFacilitators] = useState([]);

    const [masterOverrides, setMasterOverrides] = useState([]);
    const [masterSwipes, setMasterSwipes] = useState([]);

    const [selectedOverrides, setSelectedOverrides] = useState([]);
    const [selectedSwipes, setSelectedSwipes] = useState([]);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!isOpen) return;
        setCohortName('');
        setError(null);

        // Fetch master lists
        fetch(`${API}/api/admin/interventions/master`)
            .then(res => res.json())
            .then(data => {
                setMasterOverrides(data.overrides || []);
                setMasterSwipes(data.swipes || []);
                // By default, select all
                setSelectedOverrides(data.overrides?.map(o => o.id) || []);
                setSelectedSwipes(data.swipes?.map(s => s.id) || []);
            })
            .catch(err => setError("Failed to load master interventions: " + err.message));

        // Fetch facilitators
        fetch(`${API}/api/admin/facilitators`)
            .then(res => res.json())
            .then(data => setAvailableFacilitators(data.facilitators || []))
            .catch(err => console.error("Failed to fetch facilitators", err));
    }, [isOpen]);

    if (!isOpen) return null;

    const toggleOverride = (id) => {
        setSelectedOverrides(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
    };

    const toggleSwipe = (id) => {
        setSelectedSwipes(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const res = await fetch(`${API}/api/simulations/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cohort_name: cohortName.trim() || `Cohort_${Date.now()}`,
                    facilitator_id: facilitatorId,
                    allowed_overrides: selectedOverrides,
                    allowed_swipes: selectedSwipes
                })
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || `Failed to create cohort (${res.status})`);
            }

            const newSession = await res.json();
            onCreated(newSession);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <h2>🚀 Set Up New Cohort</h2>
                    <button className={styles.closeBtn} onClick={onClose} disabled={loading}>×</button>
                </div>

                <div className={styles.body}>
                    <form onSubmit={handleCreate} className={styles.form}>
                        {error && <div className={styles.errorBox}>{error}</div>}

                        <section className={styles.configSection}>
                            <h3>1. Core Details</h3>
                            <div className={styles.formGroup}>
                                <label>Cohort Name / Identifier</label>
                                <input
                                    type="text"
                                    value={cohortName}
                                    onChange={(e) => setCohortName(e.target.value)}
                                    placeholder="e.g. Exec MBA Spring 2026"
                                    required
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label>Assigned Facilitator</label>
                                <select
                                    value={facilitatorId}
                                    onChange={(e) => setFacilitatorId(e.target.value)}
                                    required
                                    className={styles.selectFacilitator}
                                >
                                    <option value="" disabled>-- Select a Facilitator --</option>
                                    {availableFacilitators.map(fac => (
                                        <option key={fac.facilitator_id} value={fac.facilitator_id}>
                                            {fac.name} ({fac.facilitator_id})
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </section>

                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>2. Team Interventions Configuration</h3>
                                <p>Select which specific Master Interventions are exposed for this session.</p>
                            </div>

                            <div className={styles.splitLists}>
                                <div className={styles.listCol}>
                                    <h4>⚡ Manual Overrides ({selectedOverrides.length}/{masterOverrides.length})</h4>
                                    <div className={styles.checkboxList}>
                                        {masterOverrides.map(ov => (
                                            <label key={ov.id} className={styles.checkboxItem}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedOverrides.includes(ov.id)}
                                                    onChange={() => toggleOverride(ov.id)}
                                                />
                                                <span className={styles.checkText}>
                                                    {ov.icon} {ov.title}
                                                </span>
                                            </label>
                                        ))}
                                        {masterOverrides.length === 0 && <div className={styles.empty}>No overrides defined globally.</div>}
                                    </div>
                                </div>

                                <div className={styles.listCol}>
                                    <h4>✉️ Swipe Files ({selectedSwipes.length}/{masterSwipes.length})</h4>
                                    <div className={styles.checkboxList}>
                                        {masterSwipes.map(sw => (
                                            <label key={sw.id} className={styles.checkboxItem}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedSwipes.includes(sw.id)}
                                                    onChange={() => toggleSwipe(sw.id)}
                                                />
                                                <span className={styles.checkText}>
                                                    {sw.icon} {sw.label}
                                                </span>
                                            </label>
                                        ))}
                                        {masterSwipes.length === 0 && <div className={styles.empty}>No swipe files defined globally.</div>}
                                    </div>
                                </div>
                            </div>
                        </section>

                        <div className={styles.footer}>
                            <button type="button" className={styles.cancelBtn} onClick={onClose} disabled={loading}>Cancel</button>
                            <button type="submit" className={styles.submitBtn} disabled={loading || !cohortName.trim()}>
                                {loading ? 'Initializing Server...' : 'Create Cohort Session'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
