import React, { useState, useEffect } from 'react';
import styles from './CreateCohortModal.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const FACILITATOR_ANALYTICS = [
    { key: 'decision_heatmap', label: 'Decision Heatmap', icon: '📊', tooltip: 'Choice distribution matrix showing which strategic options (A, B, C, etc.) were selected in each round across all players. Includes a heatmap grid with counts/percentages and stacked bar charts for visual comparison. Answers: "What are the most popular choices per round?"' },
    { key: 'time_to_decision', label: 'Time-to-Decision', icon: '⏱', tooltip: 'Decision speed analytics — how long players take to commit their choices each round. Displays average, median, min, and max times in seconds with horizontal bar visualizations. Answers: "Are players deliberating or rushing?"' },
    { key: 'cohort_comparison', label: 'Cohort Comparison', icon: '📈', tooltip: 'Plots KPI trajectories side-by-side for multiple cohorts on an SVG line chart. Togglable between Treasury, Reputation, Synergy, and EBITDA metrics. Answers: "How do different cohorts perform against each other over time?"' },
    { key: 'convergence_analysis', label: 'Convergence Analysis', icon: '🔄', tooltip: 'Measures strategy similarity using a convergence gauge (0–100%). Tracks choice entropy (bits of unpredictability) and CapEx standard deviation per round. Low entropy = players thinking alike. Answers: "Are teams converging on the same strategy or diversifying?"' },
    { key: 'learning_outcomes', label: 'Learning Outcomes', icon: '🎯', tooltip: 'Tracks gamification and engagement: total learning bonuses awarded, manual facilitator awards, badge distribution counts, and bonuses by category. Answers: "How engaged are students and what milestones have they hit?"' },
    { key: 'risk_exposure', label: 'Risk Exposure', icon: '📉', tooltip: 'Multi-axis tracking of non-financial risks per cohort over time: Carbon Intensity, Natural Capital Debt, Social License, and Governance Risk. Rendered as vertical bar charts per cohort. Answers: "How are teams managing ESG/sustainability risks?"' },
    { key: 'materiality_matrix', label: 'Materiality Matrix', icon: '🧩', tooltip: 'Toggles the Mendelow\'s Materiality Matrix panel — the drag-and-drop issue mapping grid with financial vs. societal impact axes for stakeholder analysis. Used for teaching ESG materiality assessment.' },
    { key: 'technical_reference', label: 'Technical Reference', icon: '📐', tooltip: 'Toggles the Technical Glossary panel — a comprehensive reference guide explaining simulation terminology, engine mechanics, KPI calculation formulas, and contagion/talent engine parameters.' },
];

const PLAYER_ANALYTICS = [
    { key: 'peer_benchmarking', label: 'Peer Benchmarking', icon: '🏆', tooltip: 'Shows the player their anonymous percentile ranking vs. the cohort for Treasury, Reputation, and Synergy. Includes bar visualizations with their value compared against the cohort average. Answers: "How do I rank among my peers?"' },
    { key: 'decision_impact', label: 'Decision Impact', icon: '🧠', tooltip: 'Per-round KPI attribution — shows how each choice affected Treasury, Reputation, and Synergy with colour-coded delta badges (+/-) and a narrative explanation of the outcome. Answers: "What impact did my decisions actually have?"' },
    { key: 'what_if_simulator', label: 'What-If Simulator', icon: '📈', tooltip: 'Counterfactual analysis — shows what would have happened if the player had chosen the most popular alternative option. Displays projected Treasury and Reputation diffs. Only appears when choices differ from the majority. Disabled by default.' },
];

export default function CreateCohortModal({ isOpen, onClose, onCreated, currentFacilitatorId }) {
    const [cohortName, setCohortName] = useState('');
    const [facilitatorId, setFacilitatorId] = useState('');
    const [availableFacilitators, setAvailableFacilitators] = useState([]);
    const [detectedParadigm, setDetectedParadigm] = useState('legacy_abc');

    const [masterOverrides, setMasterOverrides] = useState([]);
    const [masterSwipes, setMasterSwipes] = useState([]);

    const [selectedOverrides, setSelectedOverrides] = useState([]);
    const [selectedSwipes, setSelectedSwipes] = useState([]);

    // Analytics visibility per-cohort overrides
    const [visibilityDefaults, setVisibilityDefaults] = useState(null);
    const [visibility, setVisibility] = useState({
        facilitator: {},
        player: {},
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!isOpen) return;
        setCohortName('');
        setError(null);

        // Fetch global analytics visibility defaults
        fetch(`${API}/api/admin/god/analytics-visibility`)
            .then(res => res.json())
            .then(data => {
                setVisibilityDefaults(data);
                setVisibility({
                    facilitator: { ...data.facilitator },
                    player: { ...data.player },
                });
            })
            .catch(() => {});

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
            
        if (currentFacilitatorId) {
            setFacilitatorId(currentFacilitatorId);
        }

        // Detect paradigm from facilitator's existing sessions
        fetch(`${API}/api/admin/leaderboard`)
            .then(r => r.json())
            .then(data => {
                const facSessions = (data.leaderboard || []).filter(s =>
                    s.facilitator_id === (currentFacilitatorId || facilitatorId)
                );
                if (facSessions.length > 0) {
                    // Get paradigm from the first session
                    const firstSession = facSessions[0];
                    if (firstSession.session_id) {
                        fetch(`${API}/api/simulations/${firstSession.session_id}/paradigm`)
                            .then(r => r.json())
                            .then(pData => {
                                if (pData.decision_paradigm) {
                                    setDetectedParadigm(pData.decision_paradigm);
                                }
                            })
                            .catch(() => {});
                    }
                }
            })
            .catch(() => {});
    }, [isOpen, currentFacilitatorId]);

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

    const PARADIGM_LABELS = {
        legacy_abc: 'Narrative Crises (A/B/C)',
        multi_toggles: 'Strategic Pillars (Toggles)',
        advanced_climate: 'Advanced Climate Engine',
        healthcare: 'Healthcare Edition',

    };

    const toggleVis = (role, key) => {
        setVisibility(prev => ({
            ...prev,
            [role]: { ...prev[role], [key]: !prev[role][key] },
        }));
    };

    // Check if any visibility setting differs from global defaults
    const hasVisibilityOverrides = () => {
        if (!visibilityDefaults) return false;
        for (const role of ['facilitator', 'player']) {
            for (const [key, val] of Object.entries(visibility[role] || {})) {
                if ((visibilityDefaults[role] || {})[key] !== val) return true;
            }
        }
        return false;
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
                    decision_paradigm: detectedParadigm,
                    allowed_overrides: selectedOverrides,
                    allowed_swipes: selectedSwipes
                })
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || `Failed to create cohort (${res.status})`);
            }

            const newSession = await res.json();

            // Save per-cohort visibility overrides if any differ from defaults
            if (hasVisibilityOverrides() && newSession.session_id) {
                try {
                    await fetch(`${API}/api/admin/cohort/${newSession.session_id}/analytics-visibility`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(visibility),
                    });
                } catch { /* non-critical */ }
            }

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
                            {detectedParadigm && detectedParadigm !== 'legacy_abc' && (
                                <div className={styles.formGroup} style={{ marginTop: 4 }}>
                                    <label>Decision Paradigm</label>
                                    <div style={{
                                        padding: '0.6rem 0.8rem', borderRadius: 6,
                                        background: 'rgba(99,102,241,0.1)',
                                        border: `1px solid rgba(99,102,241,0.3)`,
                                        fontSize: '0.85rem', fontWeight: 600,
                                        color: '#6366f1',
                                    }}>
                                        {detectedParadigm === 'healthcare' ? '🏥' : '⚙️'}{' '}
                                        {PARADIGM_LABELS[detectedParadigm] || detectedParadigm}
                                        <span style={{ fontSize: '0.72rem', fontWeight: 400, opacity: 0.7, marginLeft: 8 }}>(inherited from existing sessions)</span>
                                    </div>
                                </div>
                            )}
                            <div className={styles.formGroup}>
                                <label>Assigned Facilitator</label>
                                {currentFacilitatorId && currentFacilitatorId !== 'admin' ? (
                                    <input
                                        type="text"
                                        value={currentFacilitatorId}
                                        disabled
                                        style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ccc', background: '#f5f5f5' }}
                                    />
                                ) : (
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
                                )}
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

                        {/* Section 3: Analytics Visibility */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>3. Analytics Visibility</h3>
                                <p>Choose which analytics panels are visible for this cohort. Changes override the global defaults.</p>
                            </div>

                            <div className={styles.visSection}>
                                <div className={styles.visRoleLabel}>🎓 Facilitator Dashboard</div>
                                <div className={styles.visGrid}>
                                    {FACILITATOR_ANALYTICS.map(a => (
                                        <div
                                            key={a.key}
                                            className={`${styles.visCard} ${visibility.facilitator[a.key] ? styles.visCardActive : ''}`}
                                            onClick={() => toggleVis('facilitator', a.key)}
                                            data-tooltip={a.tooltip}
                                        >
                                            <span className={styles.visIcon}>{a.icon}</span>
                                            <span className={styles.visLabel}>{a.label}</span>
                                            <div className={styles.visToggleTrack}
                                                style={{ background: visibility.facilitator[a.key] ? '#10b981' : '#475569' }}
                                            >
                                                <div className={styles.visToggleThumb}
                                                    style={{ left: visibility.facilitator[a.key] ? '14px' : '2px' }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className={styles.visRoleLabel}>👤 Player Dashboard</div>
                                <div className={styles.visGrid}>
                                    {PLAYER_ANALYTICS.map(a => (
                                        <div
                                            key={a.key}
                                            className={`${styles.visCard} ${visibility.player[a.key] ? styles.visCardActive : ''}`}
                                            onClick={() => toggleVis('player', a.key)}
                                            data-tooltip={a.tooltip}
                                        >
                                            <span className={styles.visIcon}>{a.icon}</span>
                                            <span className={styles.visLabel}>{a.label}</span>
                                            <div className={styles.visToggleTrack}
                                                style={{ background: visibility.player[a.key] ? '#10b981' : '#475569' }}
                                            >
                                                <div className={styles.visToggleThumb}
                                                    style={{ left: visibility.player[a.key] ? '14px' : '2px' }}
                                                />
                                            </div>
                                        </div>
                                    ))}
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
