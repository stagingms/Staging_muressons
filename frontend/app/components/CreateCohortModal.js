import React, { useState, useEffect } from 'react';
import styles from './CreateCohortModal.module.css';
import { CURRENCIES } from '../contexts/CurrencyContext';

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

const PEDAGOGICAL_TOGGLES = [
    { key: 'prediction_gates_enabled', label: 'Prediction Gates', icon: '🔮', tooltip: 'Pre-mortem prediction prompt before each decision. Players predict outcomes before committing — compared post-round. Klein (2007) Prospective Hindsight.', default: false },
    { key: 'confidence_calibration_enabled', label: 'Confidence Calibration', icon: '🎰', tooltip: 'Players rate their confidence (1-5) for each decision. Generates a calibration curve at R10 showing overconfidence/underconfidence patterns. Dunning-Kruger awareness.', default: false },
    { key: 'round_recap_enabled', label: 'Round Recap', icon: '📋', tooltip: 'Post-round "What Just Happened?" narrative showing the top 3 causal chains, stochastic vs strategic labelling, and a 3-word facilitator anchor.', default: false },
    { key: 'real_world_cards_enabled', label: 'Real-World Case Cards', icon: '🌍', tooltip: 'Displays real corporate case briefs (VW, Ørsted, Nike, etc.) paralleling each round\'s dilemma. Bridges simulation-reality transfer gap. Baldwin & Ford (1988).', default: false },
    { key: 'strategy_memo_enabled', label: 'Strategy Memo (R5)', icon: '📝', tooltip: 'Post-R5 structured writing exercise. Players assess position, identify risks, and justify resource allocation. Bloom\'s Create level.', default: false },
    { key: 'debrief_protocol_enabled', label: 'Debrief Protocol', icon: '🎭', tooltip: 'Thiagarajan (1993) three-phase structured debrief at R10: How Do You Feel? → What Happened? → So What / Now What?', default: false },
    { key: 'self_learning_mode', label: 'Self-Learning Mode', icon: '🎓', tooltip: 'Enables ALL pedagogical scaffolding automatically. Designed for facilitator-absent cohorts where the simulation must self-teach.', default: false },
];

// DIFFICULTY_TIERS removed — now bundled into scenario presets from backend

export default function CreateCohortModal({ isOpen, onClose, onCreated, currentFacilitatorId }) {
    const [cohortName, setCohortName] = useState('');
    const [facilitatorId, setFacilitatorId] = useState('');
    const [availableFacilitators, setAvailableFacilitators] = useState([]);
    const [selectedParadigm, setSelectedParadigm] = useState('legacy_abc');

    // Cohort authorship (mandatory metadata)
    const [createdBy, setCreatedBy] = useState('');
    const [createdWhen, setCreatedWhen] = useState('');

    // Cohort scheduling
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    // Per-cohort experience level (unified preset replacing scenario_preset + difficulty_tier)
    const [scenarioPresets, setScenarioPresets] = useState([]);
    const [selectedExperienceLevel, setSelectedExperienceLevel] = useState('workshop_standard');
    const [pedagogyCustomised, setPedagogyCustomised] = useState(false);
    const [selectedCurrency, setSelectedCurrency] = useState('INR'); // stored as code

    // Ending Pathway
    const [endingPathways, setEndingPathways] = useState([]);
    const [selectedPathway, setSelectedPathway] = useState('activist_ultimatum');

    // CEO Interview
    const [ceoInterviewEnabled, setCeoInterviewEnabled] = useState(false);
    const [ceoVoiceGender, setCeoVoiceGender] = useState('female');
    const [elevenlabsStatus, setElevenlabsStatus] = useState(null);

    // Side Tracks
    const [sideTrackCatalog, setSideTrackCatalog] = useState([]);
    const [selectedSideTracks, setSelectedSideTracks] = useState([]);

    const [masterOverrides, setMasterOverrides] = useState([]);
    const [masterSwipes, setMasterSwipes] = useState([]);

    const [selectedOverrides, setSelectedOverrides] = useState([]);
    const [selectedSwipes, setSelectedSwipes] = useState([]);

    // Round Pacing
    const [pacingMode, setPacingMode] = useState('free_play');
    const [maxUnlockedRound, setMaxUnlockedRound] = useState(10);

    // Analytics visibility per-cohort overrides
    const [visibilityDefaults, setVisibilityDefaults] = useState(null);
    const [visibility, setVisibility] = useState({
        facilitator: {},
        player: {},
    });

    const [pedagogicalToggles, setPedagogicalToggles] = useState(
        Object.fromEntries(PEDAGOGICAL_TOGGLES.map(t => [t.key, t.default]))
    );
    // difficultyTier is now derived from selectedExperienceLevel
    const [openTab, setOpenTab] = useState('core');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!isOpen) return;
        setCohortName('');
        setError(null);
        setSelectedExperienceLevel('workshop_standard');
        setPedagogyCustomised(false);
        setSelectedCurrency('INR');
        setSelectedParadigm('legacy_abc');
        setCreatedBy('');
        setCreatedWhen(new Date().toISOString().slice(0, 10)); // default to today
        setStartDate(new Date().toISOString().slice(0, 10)); // default to today
        setEndDate(''); // no default end date
        
        setOpenTab('core');

        // Fetch experience level presets
        fetch(`${API}/api/admin/scenario-presets`)
            .then(r => r.json()).then(d => {
                const presets = d.presets || [];
                setScenarioPresets(presets);
                // Auto-apply default preset's pedagogy
                const defaultPreset = presets.find(p => p.id === 'workshop_standard');
                if (defaultPreset?.default_pedagogy) {
                    setPedagogicalToggles(prev => ({ ...prev, ...defaultPreset.default_pedagogy }));
                }
            }).catch(() => {});

        // Fetch available ending pathways
        fetch(`${API}/api/admin/ending-pathways`)
            .then(r => r.json())
            .then(d => {
                setEndingPathways(d.pathways || []);
                setSelectedPathway(d.default || 'activist_ultimatum');
            })
            .catch(() => {});

        // Fetch CEO Interview state from global settings
        fetch(`${API}/api/admin/global-settings`)
            .then(r => r.json())
            .then(d => {
                setCeoInterviewEnabled(d.ceo_interview_enabled || false);
                setCeoVoiceGender(d.ceo_interview_voice_gender || 'female');
            })
            .catch(() => {});

        // Fetch ElevenLabs TTS API status
        fetch(`${API}/api/simulations/elevenlabs/status`)
            .then(r => r.ok ? r.json() : null)
            .then(d => { if (d) setElevenlabsStatus(d); })
            .catch(() => {});

        // Fetch side track catalog
        fetch(`${API}/api/admin/side-tracks/catalog`)
            .then(r => r.ok ? r.json() : null)
            .then(d => {
                if (d?.catalog) {
                    setSideTrackCatalog(d.catalog);
                    // Pre-select globally-enabled tracks
                    setSelectedSideTracks(d.catalog.filter(t => t.enabled_globally).map(t => t.track_id));
                }
            })
            .catch(() => {});

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

    const PARADIGM_OPTIONS = [
        {
            id: 'legacy_abc',
            label: 'Narrative Crises',
            sub: 'A / B / C Choices',
            icon: '🏭',
            desc: 'Classic scenario-based rounds with structured A/B/C decision options. Best for standard MBA and leadership development.',
            color: '#6366f1',
            bg: 'rgba(99,102,241,0.1)',
            border: 'rgba(99,102,241,0.35)',
        },
        {
            id: 'multi_toggles',
            label: 'Strategic Pillars',
            sub: 'Toggle Investments',
            icon: '🎛️',
            desc: 'Players allocate investment across strategic pillars using toggles. No binary choices — continuous re-balancing.',
            color: '#f59e0b',
            bg: 'rgba(245,158,11,0.1)',
            border: 'rgba(245,158,11,0.3)',
        },
        {
            id: 'advanced_climate',
            label: 'Advanced Climate',
            sub: 'CSRD / ESG Engine',
            icon: '🌍',
            desc: 'CSRD-aligned simulation with Double Materiality Matrix, carbon accounting, and green transition fund mechanics.',
            color: '#10b981',
            bg: 'rgba(16,185,129,0.1)',
            border: 'rgba(16,185,129,0.3)',
        },
        {
            id: 'healthcare',
            label: 'Healthcare Edition',
            sub: 'Hospital BU Model',
            icon: '🏥',
            desc: 'Hospital and clinical network simulation. Business units are Hospitals, Clinics, Specialised Care, and Digital Health.',
            color: '#ef4444',
            bg: 'rgba(239,68,68,0.1)',
            border: 'rgba(239,68,68,0.3)',
        },
        {
            id: 'un_sdg',
            label: 'UN SDG Edition',
            sub: 'Sustainable Goals',
            icon: '🌐',
            desc: 'Strategy decisions are mapped to UN Sustainable Development Goals. Reputation is linked to SDG achievement scores.',
            color: '#0ea5e9',
            bg: 'rgba(14,165,233,0.1)',
            border: 'rgba(14,165,233,0.3)',
        },
    ];

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

    const AccordionItem = ({ id, title, summary, children }) => {
        const isOpen = openTab === id;
        return (
            <div className={`${styles.accordionItem} ${isOpen ? styles.open : ''}`}>
                <button type="button" className={styles.accordionHeader} onClick={() => setOpenTab(isOpen ? null : id)}>
                    <div className={styles.accHeaderContent}>
                        <span className={styles.accTitle}>{title}</span>
                        {!isOpen && summary && <span className={styles.accSummary}>{summary}</span>}
                    </div>
                    <span className={styles.accIcon}>{isOpen ? '▼' : '▶'}</span>
                </button>
                {isOpen && <div className={styles.accordionBody}>{children}</div>}
            </div>
        );
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        setError(null);

        // Validate mandatory fields
        if (!createdBy.trim()) {
            setError('"Created By" is required.');
            return;
        }
        if (!createdWhen) {
            setError('"Created When" date is required.');
            return;
        }

        setLoading(true);

        try {
            const res = await fetch(`${API}/api/simulations/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cohort_name: cohortName.trim() || `Cohort_${Date.now()}`,
                    facilitator_id: facilitatorId,
                    decision_paradigm: selectedParadigm,
                    allowed_overrides: selectedOverrides,
                    allowed_swipes: selectedSwipes,
                    currency_symbol: (CURRENCIES.find(c => c.code === selectedCurrency) || CURRENCIES[0]).symbol,
                    scenario_preset: selectedExperienceLevel || null,
                    experience_level: selectedExperienceLevel || null,
                    difficulty_tier: (scenarioPresets.find(p => p.id === selectedExperienceLevel) || {}).difficulty_tier || 'advanced',
                    ending_pathway: selectedPathway || null,
                    created_by: createdBy.trim(),
                    created_when: createdWhen,
                    start_date: startDate || null,
                    end_date: endDate || null,
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

            // Save per-cohort pedagogical scaffolding settings
            if (newSession.session_id) {
                try {
                    await fetch(`${API}/api/admin/cohort/${newSession.session_id}/pedagogical-settings`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            experience_level: selectedExperienceLevel,
                            difficulty_tier: (scenarioPresets.find(p => p.id === selectedExperienceLevel) || {}).difficulty_tier || 'advanced',
                            ...pedagogicalToggles,
                        }),
                    });
                } catch { /* non-critical */ }
            }

            // Apply per-cohort CEO Interview settings
            if (newSession.session_id) {
                try {
                    await fetch(`${API}/api/admin/sessions/${newSession.session_id}/ceo-interview`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            ceo_interview_enabled: ceoInterviewEnabled,
                            ceo_interview_voice_gender: ceoVoiceGender,
                        }),
                    });
                } catch { /* non-critical */ }
            }

            // Assign per-cohort side tracks
            if (newSession.session_id && selectedSideTracks.length > 0) {
                try {
                    await fetch(`${API}/api/admin/cohorts/${newSession.session_id}/side-tracks`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tracks: selectedSideTracks }),
                    });
                } catch { /* non-critical */ }
            }

            // Save per-cohort round pacing settings
            if (newSession.session_id) {
                try {
                    await fetch(`${API}/api/admin/cohort/${newSession.session_id}/pacing`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            pacing_mode: pacingMode,
                            max_unlocked_round: pacingMode === 'free_play' ? 10 : maxUnlockedRound,
                        }),
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

                        

                        
                                

                                

                        

                                

                        

                        

                        

                        
                        <AccordionItem id="core" title="1. Core Configuration" summary="Cohort Name, Facilitator, Scenario, & Currency">
{/* ── Section 1: Core Details ── */}
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
                                        {currentFacilitatorId && currentFacilitatorId !== 'admin' ? (
                                            <input
                                                type="text"
                                                value={currentFacilitatorId}
                                                disabled
                                                style={{ background: 'rgba(30,41,59,0.8)', color: '#94a3b8', border: '1px solid rgba(71,85,105,0.4)', borderRadius: 6, padding: '0.75rem 1rem' }}
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

{/* ── Created By / When (mandatory authorship metadata) ── */}
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 4 }}>
                                        <div className={styles.formGroup}>
                                            <label>
                                                Created By <span style={{ color: '#ef4444', fontWeight: 700 }}>*</span>
                                            </label>
                                            <input
                                                type="text"
                                                value={createdBy}
                                                onChange={(e) => setCreatedBy(e.target.value)}
                                                placeholder="e.g. Prof. Sharma"
                                                required
                                                style={{
                                                    borderColor: !createdBy.trim() && error ? '#ef4444' : undefined,
                                                }}
                                            />
                                            <span style={{ fontSize: '0.65rem', color: '#64748b', marginTop: 2 }}>
                                                Name of the person setting up this cohort
                                            </span>
                                        </div>
                                        <div className={styles.formGroup}>
                                            <label>
                                                Created When <span style={{ color: '#ef4444', fontWeight: 700 }}>*</span>
                                            </label>
                                            <input
                                                type="date"
                                                value={createdWhen}
                                                onChange={(e) => setCreatedWhen(e.target.value)}
                                                required
                                                style={{
                                                    borderColor: !createdWhen && error ? '#ef4444' : undefined,
                                                }}
                                            />
                                            <span style={{ fontSize: '0.65rem', color: '#64748b', marginTop: 2 }}>
                                                Date this cohort session is being created
                                            </span>
                                        </div>
                                    </div>

{/* ── Cohort Schedule (Start / End dates) ── */}
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 8 }}>
                                        <div className={styles.formGroup}>
                                            <label>
                                                Start Date
                                            </label>
                                            <input
                                                type="date"
                                                value={startDate}
                                                onChange={(e) => setStartDate(e.target.value)}
                                            />
                                            <span style={{ fontSize: '0.65rem', color: '#64748b', marginTop: 2 }}>
                                                Game accessible from this date (optional)
                                            </span>
                                        </div>
                                        <div className={styles.formGroup}>
                                            <label>
                                                End Date
                                            </label>
                                            <input
                                                type="date"
                                                value={endDate}
                                                onChange={(e) => setEndDate(e.target.value)}
                                                min={startDate || undefined}
                                            />
                                            <span style={{ fontSize: '0.65rem', color: '#64748b', marginTop: 2 }}>
                                                Game locked after this date — results stay visible
                                            </span>
                                        </div>
                                    </div>
                                </section>
{/* ── Section 3: Scenario & Display Currency ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>3. Scenario &amp; Display Currency</h3>
                                <p>Set the starting engine difficulty and the currency symbol shown on all monetary KPIs, investment panels, and reports for this cohort.</p>
                            </div>

{/* ── Experience Level (unified: engine difficulty + visibility + pedagogy) ── */}
                            {scenarioPresets.length > 0 && (
                                <div className={styles.formGroup}>
                                    <label>Experience Level</label>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
                                        {scenarioPresets.map(p => {
                                            const isSelected = selectedExperienceLevel === p.id;
                                            const presetColor = p.color || '#6366f1';
                                            return (
                                                <button
                                                    key={p.id}
                                                    type="button"
                                                    onClick={() => {
                                                        setSelectedExperienceLevel(p.id);
                                                        // Auto-apply preset pedagogy if user hasn't customised
                                                        if (!pedagogyCustomised && p.default_pedagogy) {
                                                            setPedagogicalToggles(prev => ({ ...prev, ...p.default_pedagogy }));
                                                        }
                                                    }}
                                                    style={{
                                                        display: 'flex', alignItems: 'center', gap: 12,
                                                        padding: '12px 16px', borderRadius: 10, cursor: 'pointer',
                                                        border: isSelected ? `2px solid ${presetColor}` : '1.5px solid rgba(100,116,139,0.3)',
                                                        background: isSelected ? `${presetColor}12` : 'rgba(15,23,42,0.5)',
                                                        transition: 'all 0.18s', textAlign: 'left', width: '100%',
                                                    }}
                                                >
                                                    <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{p.icon}</span>
                                                    <span style={{ flex: 1 }}>
                                                        <span style={{ display: 'block', fontWeight: 700, fontSize: '0.9rem', color: isSelected ? presetColor : '#e2e8f0' }}>
                                                            {p.name}
                                                            <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 8, color: isSelected ? presetColor : '#64748b', opacity: 0.85 }}>
                                                                {p.subtitle || ''}
                                                            </span>
                                                        </span>
                                                        <span style={{ display: 'block', fontSize: '0.72rem', color: isSelected ? '#cbd5e1' : '#64748b', marginTop: 2 }}>
                                                            {p.description}
                                                        </span>
                                                        {p.target_audience && (
                                                            <span style={{ display: 'block', fontSize: '0.65rem', color: isSelected ? presetColor : '#475569', marginTop: 3, fontStyle: 'italic' }}>
                                                                👥 {p.target_audience}
                                                            </span>
                                                        )}
                                                    </span>
                                                    {isSelected && (
                                                        <span style={{
                                                            fontSize: '0.72rem', fontWeight: 700, color: presetColor,
                                                            background: `${presetColor}18`, border: `1px solid ${presetColor}50`,
                                                            padding: '2px 8px', borderRadius: 999, whiteSpace: 'nowrap', flexShrink: 0,
                                                        }}>Selected</span>
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                    {selectedExperienceLevel && (() => {
                                        const sel = scenarioPresets.find(p => p.id === selectedExperienceLevel);
                                        return sel ? (
                                            <div style={{
                                                marginTop: 8, padding: '8px 12px', borderRadius: 8,
                                                background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(148,163,184,0.15)',
                                                fontSize: '0.7rem', color: '#94a3b8',
                                            }}>
                                                <strong style={{ color: '#cbd5e1' }}>This sets:</strong>{' '}
                                                Engine difficulty ({sel.name}) · Visibility tier ({sel.difficulty_tier}) ·{' '}
                                                {Object.entries(sel.default_pedagogy || {}).filter(([,v]) => v).map(([k]) =>
                                                    k.replace(/_enabled$/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                                                ).join(', ') || 'No scaffolding'} enabled by default
                                                {pedagogyCustomised && (
                                                    <span style={{ marginLeft: 6, color: '#f59e0b', fontWeight: 700 }}>⚙ Pedagogy customised</span>
                                                )}
                                            </div>
                                        ) : null;
                                    })()}
                                </div>
                            )}

                            {/* Currency Selector */}
                            <div className={styles.formGroup}>
                                <label>Display Currency</label>
                                <div style={{
                                    display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 6, marginTop: 4,
                                    background: 'rgba(255,255,255,0.02)', borderRadius: 10, padding: 6,
                                    border: '1px solid var(--border-subtle,#334155)',
                                }}>
                                    {CURRENCIES.map(c => {
                                        const isActive = c.code === selectedCurrency;
                                        return (
                                            <button
                                                key={c.code}
                                                type="button"
                                                onClick={() => setSelectedCurrency(c.code)}
                                                style={{
                                                    padding: '10px 4px', borderRadius: 8, cursor: 'pointer',
                                                    border: isActive ? '2px solid #6366f1' : '1.5px solid transparent',
                                                    background: isActive ? 'rgba(99,102,241,0.12)' : 'transparent',
                                                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
                                                    transition: 'all 0.15s',
                                                }}
                                                title={`${c.label} (${c.symbol})`}
                                            >
                                                <span style={{ fontSize: '1.25rem' }}>{c.flag}</span>
                                                <span style={{ fontWeight: 800, fontSize: '1rem', color: isActive ? '#818cf8' : '#e2e8f0' }}>{c.symbol}</span>
                                                <span style={{ fontSize: '0.6rem', color: isActive ? '#818cf8' : '#94a3b8', letterSpacing: '0.05em', fontWeight: 700 }}>{c.code}</span>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </section>
                        </AccordionItem>

                        <AccordionItem id="engine" title="2. Simulation Engine" summary="Decision Paradigm & Ending Pathway">
{/* ── Section 2: Decision Paradigm ── */}
                                <section className={styles.configSection}>
                                    <div className={styles.sectionHeader}>
                                        <h3>2. Decision Paradigm</h3>
                                        <p>
                                            Choose the simulation engine for this cohort.
                                            
                                        </p>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {PARADIGM_OPTIONS.map(p => {
                                            const isSelected = selectedParadigm === p.id;
                                            return (
                                                <button
                                                    key={p.id}
                                                    type="button"
                                                    onClick={() => setSelectedParadigm(p.id)}
                                                    style={{
                                                        display: 'flex', alignItems: 'center', gap: 12,
                                                        padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                                                        border: isSelected ? `2px solid ${p.color}` : '1.5px solid rgba(100,116,139,0.3)',
                                                        background: isSelected ? p.bg : 'rgba(15,23,42,0.5)',
                                                        transition: 'all 0.18s',
                                                        textAlign: 'left', width: '100%',
                                                        opacity: 1,
                                                    }}
                                                >
                                                    <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{p.icon}</span>
                                                    <span style={{ flex: 1 }}>
                                                        <span style={{ display: 'block', fontWeight: 700, fontSize: '0.88rem', color: isSelected ? p.color : '#e2e8f0' }}>
                                                            {p.label}
                                                            <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 6, color: isSelected ? p.color : '#64748b', opacity: 0.85 }}>({p.sub})</span>
                                                        </span>
                                                        <span style={{ display: 'block', fontSize: '0.72rem', color: isSelected ? '#cbd5e1' : '#64748b', marginTop: 2 }}>{p.desc}</span>
                                                    </span>
                                                    {isSelected && (
                                                        <span style={{
                                                            flexShrink: 0, fontSize: '0.68rem', fontWeight: 700,
                                                            padding: '2px 10px', borderRadius: 20,
                                                            background: p.bg, color: p.color,
                                                            border: `1px solid ${p.border}`,
                                                        }}>
                                                            Selected
                                                        </span>
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </section>
{/* ── Section 3.5: Ending Pathway ── */}
                        {endingPathways.length > 0 && (
                            <section className={styles.configSection}>
                                <div className={styles.sectionHeader}>
                                    <h3>🎯 Ending Pathway</h3>
                                    <p>Choose the R10 endgame crisis scenario. Players will never see the pathway name — only indirect hints between R5–R8.</p>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                    {/* Random option */}
                                    <button
                                        type="button"
                                        onClick={() => setSelectedPathway('random')}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: 10,
                                            padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                                            border: selectedPathway === 'random' ? '2px solid #a78bfa' : '1.5px solid rgba(100,116,139,0.3)',
                                            background: selectedPathway === 'random' ? 'rgba(167,139,250,0.1)' : 'rgba(15,23,42,0.5)',
                                            textAlign: 'left', width: '100%', transition: 'all 0.18s',
                                        }}
                                    >
                                        <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>🎲</span>
                                        <span style={{ flex: 1 }}>
                                            <span style={{ display: 'block', fontWeight: 700, fontSize: '0.88rem', color: selectedPathway === 'random' ? '#a78bfa' : '#e2e8f0' }}>
                                                Random
                                                <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 6, color: '#64748b' }}>(Surprise ending)</span>
                                            </span>
                                            <span style={{ display: 'block', fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>System randomly selects a pathway at session creation. Maximum surprise for facilitator and players.</span>
                                        </span>
                                    </button>
                                    {/* Pathway options */}
                                    {endingPathways.filter(p => p.implemented).map(p => {
                                        const isSelected = selectedPathway === p.id;
                                        return (
                                            <button
                                                key={p.id}
                                                type="button"
                                                onClick={() => setSelectedPathway(p.id)}
                                                style={{
                                                    display: 'flex', alignItems: 'center', gap: 10,
                                                    padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                                                    border: isSelected ? '2px solid #6366f1' : '1.5px solid rgba(100,116,139,0.3)',
                                                    background: isSelected ? 'rgba(99,102,241,0.1)' : 'rgba(15,23,42,0.5)',
                                                    textAlign: 'left', width: '100%', transition: 'all 0.18s',
                                                    opacity: p.implemented ? 1 : 0.4,
                                                }}
                                                disabled={!p.implemented}
                                            >
                                                <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{p.icon}</span>
                                                <span style={{ flex: 1 }}>
                                                    <span style={{ display: 'block', fontWeight: 700, fontSize: '0.88rem', color: isSelected ? '#818cf8' : '#e2e8f0' }}>
                                                        {p.title}
                                                        {!p.implemented && <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 6, color: '#f59e0b' }}>(Coming Soon)</span>}
                                                    </span>
                                                    <span style={{ display: 'block', fontSize: '0.72rem', color: isSelected ? '#cbd5e1' : '#64748b', marginTop: 2, lineHeight: 1.4 }}>{p.description?.substring(0, 120)}{p.description?.length > 120 ? '…' : ''}</span>
                                                </span>
                                                {isSelected && (
                                                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#818cf8', background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.3)', padding: '2px 8px', borderRadius: 999, whiteSpace: 'nowrap', flexShrink: 0 }}>Selected</span>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            </section>
                        )}
                        </AccordionItem>

                        <AccordionItem id="modules" title="3. Optional Modules" summary="Side Tracks & CEO Interview">
{/* ── Section 3.9: Side Tracks ── */}
                        {sideTrackCatalog.length > 0 && (
                            <section className={styles.configSection}>
                                <div className={styles.sectionHeader}>
                                    <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                        🛤️ Side Track Simulations
                                    </h3>
                                    <p>Enable optional mini-simulations that run alongside the main game. Players can access these between rounds.</p>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                    {sideTrackCatalog.map(track => {
                                        const isSelected = selectedSideTracks.includes(track.track_id);
                                        return (
                                            <button
                                                key={track.track_id}
                                                type="button"
                                                onClick={() => {
                                                    setSelectedSideTracks(prev =>
                                                        prev.includes(track.track_id)
                                                            ? prev.filter(t => t !== track.track_id)
                                                            : [...prev, track.track_id]
                                                    );
                                                }}
                                                style={{
                                                    display: 'flex', alignItems: 'center', gap: 10,
                                                    padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                                                    border: isSelected ? '2px solid #6366f1' : '1.5px solid rgba(100,116,139,0.3)',
                                                    background: isSelected ? 'rgba(99,102,241,0.1)' : 'rgba(15,23,42,0.5)',
                                                    textAlign: 'left', width: '100%', transition: 'all 0.18s',
                                                }}
                                            >
                                                <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{track.icon || '📦'}</span>
                                                <span style={{ flex: 1 }}>
                                                    <span style={{ display: 'block', fontWeight: 700, fontSize: '0.88rem', color: isSelected ? '#818cf8' : '#e2e8f0' }}>
                                                        {track.display_name || track.track_id}
                                                        <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 6, color: '#64748b' }}>
                                                            ({track.num_rounds || '?'} rounds)
                                                        </span>
                                                    </span>
                                                    <span style={{ display: 'block', fontSize: '0.72rem', color: isSelected ? '#cbd5e1' : '#64748b', marginTop: 2 }}>
                                                        {track.description?.substring(0, 140) || 'No description available'}
                                                    </span>
                                                </span>
                                                <div style={{
                                                    width: 32, height: 18, borderRadius: 9, flexShrink: 0,
                                                    background: isSelected ? '#6366f1' : 'rgba(100,116,139,0.3)',
                                                    position: 'relative', transition: 'background 0.15s',
                                                }}>
                                                    <div style={{
                                                        width: 14, height: 14, borderRadius: 7,
                                                        background: '#fff', position: 'absolute', top: 2,
                                                        left: isSelected ? 16 : 2,
                                                        transition: 'left 0.15s',
                                                    }} />
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                                {selectedSideTracks.length > 0 && (
                                    <div style={{ marginTop: 6, fontSize: '0.68rem', color: '#818cf8', fontWeight: 600 }}>
                                        ✓ {selectedSideTracks.length} side track{selectedSideTracks.length !== 1 ? 's' : ''} will be activated for this cohort
                                    </div>
                                )}
                            </section>
                        )}
{/* ── Section 3.7: CEO Interview ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <div>
                                    <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                        🎤 Post-Game CEO Interview
                                    </h3>
                                    <p>Optional AI-driven competency assessment after R10. Players are interviewed by the CEO and scored on 6 dimensions.</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={async () => {
                                        const next = !ceoInterviewEnabled;
                                        setCeoInterviewEnabled(next);
                                        try {
                                            await fetch(`${API}/api/admin/global-settings`, {
                                                method: 'PATCH',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({ ceo_interview_enabled: next }),
                                            });
                                        } catch {}
                                    }}
                                    style={{
                                        padding: '5px 14px', borderRadius: 8, border: 'none',
                                        background: ceoInterviewEnabled ? '#10b981' : 'rgba(148,163,184,0.15)',
                                        color: ceoInterviewEnabled ? '#fff' : '#94a3b8',
                                        fontWeight: 800, fontSize: '0.72rem', cursor: 'pointer',
                                        transition: 'all 0.15s', flexShrink: 0,
                                    }}
                                >
                                    {ceoInterviewEnabled ? '● ENABLED' : '○ DISABLED'}
                                </button>
                            </div>
                            {ceoInterviewEnabled && (
                                <div style={{
                                    display: 'flex', flexDirection: 'column', gap: '0.5rem',
                                    padding: '0.6rem 1rem', marginTop: '0.4rem',
                                    background: 'rgba(16,185,129,0.04)',
                                    border: '1px solid rgba(16,185,129,0.15)',
                                    borderRadius: 8,
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                        <span style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600 }}>CEO Voice:</span>
                                        <select
                                            value={ceoVoiceGender}
                                            onChange={async (e) => {
                                                setCeoVoiceGender(e.target.value);
                                                try {
                                                    await fetch(`${API}/api/admin/global-settings`, {
                                                        method: 'PATCH',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        body: JSON.stringify({ ceo_interview_voice_gender: e.target.value }),
                                                    });
                                                } catch {}
                                            }}
                                            style={{
                                                padding: '3px 8px', borderRadius: 6, fontSize: '0.72rem',
                                                border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                                                color: 'var(--text-primary)', fontWeight: 600, cursor: 'pointer',
                                            }}
                                        >
                                            <option value="female">👩‍💼 Victoria Muressons (Female)</option>
                                            <option value="male">👨‍💼 Alexander Muressons (Male)</option>
                                        </select>
                                        <span style={{ fontSize: '0.62rem', color: '#64748b' }}>
                                            5 questions · 6-dimension spider diagram · narrative feedback
                                        </span>
                                    </div>
                                    {/* ElevenLabs TTS Status */}
                                    <div style={{
                                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                                        padding: '0.5rem 0.8rem', borderRadius: 6,
                                        background: elevenlabsStatus?.available
                                            ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                                        border: `1px solid ${elevenlabsStatus?.available
                                            ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                                    }}>
                                        <span style={{ fontSize: '1rem' }}>
                                            {elevenlabsStatus?.available ? '🔊' : '🔇'}
                                        </span>
                                        <div style={{ flex: 1 }}>
                                            <div style={{
                                                fontSize: '0.68rem', fontWeight: 700,
                                                color: elevenlabsStatus?.available ? '#10b981' : '#ef4444',
                                            }}>
                                                ElevenLabs TTS {elevenlabsStatus?.available ? 'Connected' : 'Unavailable'}
                                            </div>
                                            <div style={{ fontSize: '0.6rem', color: '#64748b', marginTop: 1 }}>
                                                {elevenlabsStatus?.available
                                                    ? `${((elevenlabsStatus.subscription?.remaining || 0) / 1000).toFixed(0)}K characters remaining · Voice synthesis active`
                                                    : (elevenlabsStatus?.error || 'API key not configured — interview will use text-only mode')}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </section>
                        </AccordionItem>

                        <AccordionItem id="interventions" title="4. Team Interventions" summary="Manual Overrides, Swipe Files & Round Pacing">
{/* ── Section 4: Team Interventions ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>4. Team Interventions Configuration</h3>
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

{/* ── Round Pacing Configuration ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>Round Pacing</h3>
                                <p>Control how rounds are unlocked for players in this cohort.</p>
                            </div>

                            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                {[
                                    { id: 'free_play', icon: '🔓', label: 'Free Play', desc: 'All rounds unlocked immediately' },
                                    { id: 'manual', icon: '✋', label: 'Manual', desc: 'Facilitator unlocks each round' },
                                    { id: 'scheduled', icon: '📅', label: 'Scheduled', desc: 'Pre-schedule unlocks for all rounds' },
                                ].map(mode => (
                                    <div
                                        key={mode.id}
                                        onClick={() => setPacingMode(mode.id)}
                                        style={{
                                            flex: '1 1 160px',
                                            padding: '12px 14px',
                                            borderRadius: 10,
                                            border: pacingMode === mode.id
                                                ? '2px solid var(--accent-blue, #3b82f6)'
                                                : '1px solid var(--border-subtle)',
                                            background: pacingMode === mode.id
                                                ? 'rgba(59,130,246,0.08)'
                                                : 'var(--bg-card)',
                                            cursor: 'pointer',
                                            transition: 'all 0.15s',
                                        }}
                                    >
                                        <div style={{ fontSize: '1rem', marginBottom: 4 }}>{mode.icon} <strong style={{ color: 'var(--text-primary)' }}>{mode.label}</strong></div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{mode.desc}</div>
                                    </div>
                                ))}
                            </div>

                            {pacingMode === 'manual' && (
                                <div style={{ marginTop: 12 }} className={styles.formGroup}>
                                    <label>Unlock Up To Round</label>
                                    <select
                                        value={maxUnlockedRound}
                                        onChange={e => setMaxUnlockedRound(Number(e.target.value))}
                                        className={styles.selectFacilitator}
                                    >
                                        {[...Array(10)].map((_, i) => (
                                            <option key={i + 1} value={i + 1}>Round {i + 1}</option>
                                        ))}
                                    </select>
                                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>
                                        Players can play up to this round. You can change this later from the dashboard.
                                    </span>
                                </div>
                            )}
                        </section>

                        
                        </AccordionItem>

                        <AccordionItem id="pedagogy" title="5. Pedagogy &amp; Analytics" summary="Toggles and Visibility">
{/* ── Section 5: Pedagogical Scaffolding ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>5. Pedagogical Scaffolding</h3>
                                <p>Fine-tune metacognitive and formative assessment features.
                                    {selectedExperienceLevel && (() => {
                                        const sel = scenarioPresets.find(p => p.id === selectedExperienceLevel);
                                        return sel ? <span style={{ color: sel.color || '#6366f1', fontWeight: 600 }}> Defaults from: {sel.icon} {sel.name}</span> : null;
                                    })()}
                                    {pedagogyCustomised && <span style={{ color: '#f59e0b', fontWeight: 600, marginLeft: 6 }}>⚙ Customised</span>}
                                </p>
                            </div>

                            <div className={styles.visSection}>
                                <div className={styles.visRoleLabel}>🧠 Pedagogical Features</div>
                                <div className={styles.visGrid}>
                                    {PEDAGOGICAL_TOGGLES.map(t => (
                                        <div
                                            key={t.key}
                                            className={`${styles.visCard} ${pedagogicalToggles[t.key] ? styles.visCardActive : ''}`}
                                            onClick={() => {
                                                setPedagogicalToggles(prev => ({ ...prev, [t.key]: !prev[t.key] }));
                                                setPedagogyCustomised(true);
                                            }}
                                            data-tooltip={t.tooltip}
                                        >
                                            <span className={styles.visIcon}>{t.icon}</span>
                                            <span className={styles.visLabel}>{t.label}</span>
                                            <div className={styles.visToggleTrack}
                                                style={{ background: pedagogicalToggles[t.key] ? '#10b981' : '#475569' }}
                                            >
                                                <div className={styles.visToggleThumb}
                                                    style={{ left: pedagogicalToggles[t.key] ? '14px' : '2px' }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </section>
{/* ── Section 6: Analytics Visibility ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>6. Analytics Visibility</h3>
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

                        </AccordionItem>

                        <AccordionItem id="lock" title="6. Summary & Lock Configuration" summary="Review and permanently lock choices for this cohort">
                            <div style={{ padding: '0.5rem 0' }}>
                                <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '12px 16px', borderRadius: 8, color: '#fcd34d', fontSize: '0.85rem', display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                    <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>⚠️</span>
                                    <div>
                                        <strong style={{ display: 'block', marginBottom: 4, color: '#f59e0b' }}>PERMANENT COHORT CONFIGURATION</strong>
                                        By proceeding, choices made here (Decision Paradigm, Scenario Preset, Currency, Ending Pathway, Side Tracks, etc.) become <strong>permanent</strong> for this cohort and cannot be changed later.
                                    </div>
                                </div>
                                
                                <div className={styles.footer} style={{ borderTop: 'none', paddingTop: 0, marginTop: 0 }}>
                                    <button type="button" className={styles.cancelBtn} onClick={onClose} disabled={loading}>Cancel</button>
                                    <button type="submit" className={styles.submitBtn} disabled={loading || !cohortName.trim()} style={{ background: '#f59e0b', color: '#1e293b' }}>
                                        {loading ? 'Initializing Server...' : 'Permanently Lock & Create Cohort'}
                                    </button>
                                </div>
                            </div>
                        </AccordionItem>
                    </form>
                </div>
            </div>
        </div>
    );
}
