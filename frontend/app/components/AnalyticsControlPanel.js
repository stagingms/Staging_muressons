'use client';
import { useState, useEffect } from 'react';
import styles from './AnalyticsControlPanel.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export const FACILITATOR_ANALYTICS = [
    { key: 'decision_heatmap', label: 'Decision Heatmap', icon: '📊', desc: 'Choice distributions per round', tooltip: 'Choice distribution matrix showing which strategic options (A, B, C, etc.) were selected in each round across all players. Includes a heatmap grid with counts/percentages and stacked bar charts for visual comparison. Answers: "What are the most popular choices per round?"' },
    { key: 'time_to_decision', label: 'Time-to-Decision', icon: '⏱', desc: 'Decision speed analytics', tooltip: 'Decision speed analytics — how long players take to commit their choices each round. Displays average, median, min, and max times in seconds with horizontal bar visualizations. Answers: "Are players deliberating or rushing?"' },
    { key: 'cohort_comparison', label: 'Cohort Comparison', icon: '📈', desc: 'KPI trajectories side-by-side', tooltip: 'Plots KPI trajectories side-by-side for multiple cohorts on an SVG line chart. Togglable between Treasury, Reputation, Synergy, and EBITDA metrics. Answers: "How do different cohorts perform against each other over time?"' },
    { key: 'convergence_analysis', label: 'Convergence Analysis', icon: '🔄', desc: 'Strategy similarity metrics', tooltip: 'Measures strategy similarity using a convergence gauge (0–100%). Tracks choice entropy (bits of unpredictability) and CapEx standard deviation per round. Low entropy = players thinking alike. Answers: "Are teams converging on the same strategy or diversifying?"' },
    { key: 'learning_outcomes', label: 'Learning Outcomes', icon: '🎯', desc: 'Quiz scores, badges, engagement', tooltip: 'Tracks gamification and engagement: total learning bonuses awarded, manual facilitator awards, badge distribution counts, and bonuses by category. Answers: "How engaged are students and what milestones have they hit?"' },
    { key: 'risk_exposure', label: 'Risk Exposure', icon: '📉', desc: 'Carbon, NCD, social license trends', tooltip: 'Multi-axis tracking of non-financial risks per cohort over time: Carbon Intensity, Natural Capital Debt, Social License, and Governance Risk. Rendered as vertical bar charts per cohort. Answers: "How are teams managing ESG/sustainability risks?"' },
    { key: 'materiality_matrix', label: 'Materiality Matrix', icon: '🧩', desc: 'Show/hide Materiality Matrix on Facilitator Dashboard', tooltip: 'Toggles the Mendelow\'s Materiality Matrix panel — the drag-and-drop issue mapping grid with financial vs. societal impact axes for stakeholder analysis. Used for teaching ESG materiality assessment.' },
    { key: 'technical_reference', label: 'Technical Reference', icon: '📐', desc: 'Show/hide Technical Glossary on Facilitator Dashboard', tooltip: 'Toggles the Technical Glossary panel — a comprehensive reference guide explaining simulation terminology, engine mechanics, KPI calculation formulas, and contagion/talent engine parameters.' },
];

const PLAYER_ANALYTICS = [
    { key: 'peer_benchmarking', label: 'Peer Benchmarking', icon: '🏆', desc: 'Anonymous percentile rankings', tooltip: 'Shows the player their anonymous percentile ranking vs. the cohort for Treasury, Reputation, and Synergy. Includes bar visualizations with their value compared against the cohort average. Answers: "How do I rank among my peers?"' },
    { key: 'decision_impact', label: 'Decision Impact', icon: '🧠', desc: 'Per-round KPI attribution', tooltip: 'Per-round KPI attribution — shows how each choice affected Treasury, Reputation, and Synergy with colour-coded delta badges (+/-) and a narrative explanation of the outcome. Answers: "What impact did my decisions actually have?"' },
    { key: 'what_if_simulator', label: 'What-If Simulator', icon: '📈', desc: 'Counterfactual analysis', tooltip: 'Counterfactual analysis — shows what would have happened if the player had chosen the most popular alternative option. Displays projected Treasury and Reputation diffs. Only appears when choices differ from the majority. Disabled by default.' },
];

// Player-facing round surfaces. These are cohort SETTINGS (not analytics
// visibility), so they persist to the per-cohort override layer via
// /player-feature-toggles and are read back cohort-effective from
// global-settings. Each cohort is independent; with no cohort selected the
// controls set the global default.
const PLAYER_FEATURES = [
    { key: 'consequence_map_enabled', label: 'Decision Consequence Map', icon: '🗺️', desc: "Results-view timeline linking each round's decisions to their downstream effects" },
    { key: 'board_room_moments_enabled', label: 'Board Room Moment', icon: '🏢', desc: 'Guided post-round reflection (Noticing → Making Sense → Working with Meaning)' },
];

export default function AnalyticsControlPanel({ sessionId }) {
    const [visibility, setVisibility] = useState(null);
    const [saving, setSaving] = useState(false);
    const [status, setStatus] = useState(null);
    // Player-facing round surfaces — cohort-effective, persisted separately
    // from analytics visibility (see PLAYER_FEATURES).
    const [features, setFeatures] = useState({ consequence_map_enabled: true, board_room_moments_enabled: true });

    useEffect(() => {
        const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
        fetch(`${API}/api/admin/global-settings${qs}`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : {})
            .then(d => setFeatures({
                consequence_map_enabled: d.consequence_map_enabled !== false,
                board_room_moments_enabled: d.board_room_moments_enabled !== false,
            }))
            .catch(() => {});
    }, [sessionId]);

    // ── Briefing videos (per-cohort): URL pattern + per-round overrides ──
    const [videoBase, setVideoBase] = useState('');
    const [videoLines, setVideoLines] = useState('');   // "1 = https://…" per line
    const [videoStatus, setVideoStatus] = useState(null);
    useEffect(() => {
        const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
        fetch(`${API}/api/admin/global-settings${qs}`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : {})
            .then(d => {
                setVideoBase(d.briefing_video_base || '');
                const map = d.briefing_videos || {};
                setVideoLines(Object.entries(map).map(([k, v]) => `${k} = ${v}`).join('\n'));
            }).catch(() => {});
    }, [sessionId]);
    const saveVideos = async () => {
        if (!sessionId) { setVideoStatus('❌ Select a cohort first'); return; }
        const map = {};
        for (const line of videoLines.split('\n')) {
            const m = line.match(/^\s*(\d{1,2})\s*[=:]\s*(\S.*)$/);
            if (m) map[m[1]] = m[2].trim();
        }
        try {
            const r = await fetch(`${API}/api/admin/sessions/${sessionId}/briefing-videos`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ briefing_video_base: videoBase.trim(), briefing_videos: map }),
            });
            setVideoStatus(r.ok ? '✅ Saved — players see Watch on their next briefing' : '❌ Save failed');
        } catch { setVideoStatus('❌ Connection error'); }
        setTimeout(() => setVideoStatus(null), 4000);
    };

    const toggleFeature = async (key) => {
        const next = !features[key];
        setFeatures(f => ({ ...f, [key]: next }));   // optimistic
        setSaving(true);
        try {
            const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
            const res = await fetch(`${API}/api/admin/player-feature-toggles${qs}`, {
                method: 'POST', credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [key]: next }),
            });
            if (res.ok) {
                const d = await res.json();
                setFeatures(f => ({ ...f, [key]: d[key] !== false }));
                setStatus('✅ Saved'); setTimeout(() => setStatus(null), 2000);
            } else {
                setFeatures(f => ({ ...f, [key]: !next }));   // revert
            }
        } catch { setFeatures(f => ({ ...f, [key]: !next })); }
        setSaving(false);
    };

    const DEFAULT_VIS = {
        facilitator: Object.fromEntries(FACILITATOR_ANALYTICS.map(a => [a.key, true])),
        player: Object.fromEntries(PLAYER_ANALYTICS.map(a => [a.key, a.key !== 'what_if_simulator'])),
    };

    useEffect(() => {
        const endpoint = sessionId 
            ? `${API}/api/admin/cohort/${sessionId}/analytics-visibility` 
            : `${API}/api/admin/god/analytics-visibility`;
            
        fetch(endpoint)
            .then(r => r.json())
            .then(d => {
                const data = sessionId ? (d.cohort_overrides || {}) : d;
                setVisibility({
                    facilitator: { ...DEFAULT_VIS.facilitator, ...(data.facilitator || {}) },
                    player: { ...DEFAULT_VIS.player, ...(data.player || {}) },
                });
            })
            .catch(() => setVisibility(DEFAULT_VIS));
    }, [sessionId]);

    const toggle = async (role, key) => {
        const updated = {
            ...visibility,
            [role]: { ...visibility[role], [key]: !visibility[role][key] }
        };
        setVisibility(updated);
        setSaving(true);
        try {
            const endpoint = sessionId 
                ? `${API}/api/admin/cohort/${sessionId}/analytics-visibility` 
                : `${API}/api/admin/god/analytics-visibility`;
                
            const res = await fetch(endpoint, {
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
                    <h2 className={styles.title}>Analytics Visibility Controls {sessionId ? `(${sessionId.slice(0,12)})` : ''}</h2>
                    <p className={styles.subtitle}>
                        {sessionId ? "Override analytics visibility and player-facing round surfaces for this specific cohort." : "Choose which analytics are available to Facilitators and Players, and the default player-facing round surfaces, globally."}
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
                        <div key={a.key} className={styles.toggleRow} data-tooltip={a.tooltip}>
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
                        <div key={a.key} className={styles.toggleRow} data-tooltip={a.tooltip}>
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

                    {/* Player-facing round surfaces — per-cohort settings (not
                        analytics visibility). Persist via /player-feature-toggles. */}
                    <div className={styles.roleHeader} style={{ marginTop: '0.9rem' }}>
                        <span>🎬</span>
                        <h3>Round Surfaces</h3>
                    </div>
                    {/* Briefing videos — URLs only; media lives on YouTube/Vimeo/CDN. */}
                    <div className={styles.roleHeader} style={{ marginTop: '0.9rem' }}>
                        <span>🎬</span>
                        <h3>Briefing Videos</h3>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '4px 2px' }}>
                        <label style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.75 }}>URL pattern (optional, {'{round}'} = round no.)</label>
                        <input type="text" value={videoBase} onChange={e => setVideoBase(e.target.value)}
                            placeholder="https://cdn.example.edu/briefing-{round}.mp4"
                            style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(148,163,184,0.3)', background: 'transparent', color: 'inherit', fontSize: '0.78rem' }} />
                        <label style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.75, marginTop: 4 }}>Per-round URLs — one per line, e.g. “1 = https://youtu.be/…”</label>
                        <textarea value={videoLines} onChange={e => setVideoLines(e.target.value)} rows={3}
                            placeholder={"1 = https://youtu.be/K_6cGzU7vrI\n2 = https://youtu.be/…"}
                            style={{ padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(148,163,184,0.3)', background: 'transparent', color: 'inherit', fontSize: '0.76rem', fontFamily: 'inherit', resize: 'vertical' }} />
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <button onClick={saveVideos}
                                style={{ padding: '6px 14px', borderRadius: 8, border: '1px solid rgba(99,102,241,0.5)', background: 'rgba(99,102,241,0.18)', color: 'inherit', fontWeight: 700, fontSize: '0.74rem', cursor: 'pointer' }}>
                                💾 Save briefing videos
                            </button>
                            {videoStatus && <span style={{ fontSize: '0.74rem', fontWeight: 700 }}>{videoStatus}</span>}
                        </div>
                    </div>

                    {PLAYER_FEATURES.map(a => (
                        <div key={a.key} className={styles.toggleRow} data-tooltip={a.desc}>
                            <div className={styles.toggleInfo}>
                                <span className={styles.toggleIcon}>{a.icon}</span>
                                <div>
                                    <div className={styles.toggleLabel}>{a.label}</div>
                                    <div className={styles.toggleDesc}>{a.desc}</div>
                                </div>
                            </div>
                            <button
                                className={`${styles.toggleBtn} ${features[a.key] ? styles.toggleOn : styles.toggleOff}`}
                                onClick={() => toggleFeature(a.key)}
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
