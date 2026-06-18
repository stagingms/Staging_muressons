'use client';
import { useState, useEffect, useMemo } from 'react';
import styles from './GodModeStatus.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function GodModeStatus({ facilitatorId }) {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    // Global settings state (merged from GlobalSettings)
    const [settings, setSettings] = useState(null);
    const [freezeMsg, setFreezeMsg] = useState('System maintenance in progress.');
    const [settingsStatus, setSettingsStatus] = useState('');

    const load = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/system-status`);
            if (res.ok) setStatus(await res.json());
        } catch { /* ignore */ }
        setLoading(false);
    };

    const loadSettings = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/settings`);
            if (res.ok) setSettings(await res.json());
        } catch {}
    };

    useEffect(() => {
        load();
        loadSettings();
        const i = setInterval(load, 10000);
        return () => clearInterval(i);
    }, []);

    // ── Global Settings handlers ──
    const handleFreeze = async () => {
        if (!confirm('⚠️ This will freeze ALL active simulations. Continue?')) return;
        const res = await fetch(`${API}/api/admin/god/freeze`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: freezeMsg }),
        });
        if (res.ok) { load(); loadSettings(); setSettingsStatus('System FROZEN'); setTimeout(() => setSettingsStatus(''), 3000); }
    };

    const handleUnfreeze = async () => {
        const res = await fetch(`${API}/api/admin/god/unfreeze`, { method: 'POST' });
        if (res.ok) { load(); loadSettings(); setSettingsStatus('System UNFROZEN'); setTimeout(() => setSettingsStatus(''), 3000); }
    };

    if (loading) return <div className={styles.loading}>Loading system status…</div>;
    if (!status) return <div className={styles.error}>Failed to load system status</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🏠</span>
                <div>
                    <h2>System Status</h2>
                    <p className={styles.subtitle}>Real-time overview of the entire platform</p>
                </div>
            </div>

            {status.system_frozen && (
                <div className={styles.freezeBanner}>
                    ❄️ <strong>System is FROZEN</strong> — All simulations are paused
                </div>
            )}

            <div className={styles.cardGrid}>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>👨‍🏫</div>
                    <div className={styles.cardValue}>{status.total_facilitators}</div>
                    <div className={styles.cardLabel}>FACILITATORS</div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>🏢</div>
                    <div className={styles.cardValue}>{status.total_cohorts}</div>
                    <div className={styles.cardLabel}>COHORTS</div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>👥</div>
                    <div className={styles.cardValue}>{status.total_players}</div>
                    <div className={styles.cardLabel}>PLAYERS</div>
                </div>
                <div className={styles.card}>
                    <div className={styles.cardIcon}>🔌</div>
                    <div className={styles.cardValue}>{status.active_ws_connections}</div>
                    <div className={styles.cardLabel}>WS CONNECTIONS</div>
                </div>
            </div>


            {/* ── Platform Controls (merged from GlobalSettings) ── */}
            {settings && (
                <div className={styles.section}>
                    <h3>⚙️ Platform Controls</h3>
                    {settingsStatus && (
                        <div style={{
                            marginBottom: '1rem', padding: '0.5rem 1rem', borderRadius: '6px',
                            background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
                            fontSize: '0.82rem', fontWeight: 600, color: '#10b981',
                        }}>
                            {settingsStatus}
                        </div>
                    )}
                    <div className={styles.controlsGrid}>
                        {/* Emergency Freeze */}
                        <div className={`${styles.controlCard} ${settings.system_frozen ? styles.controlCardFrozen : ''}`}>
                            <div>
                                <div className={styles.controlTitle}>🚨 Emergency Freeze</div>
                                <div className={styles.controlDesc}>
                                    {settings.system_frozen
                                        ? `❄️ Frozen since ${new Date(settings.freeze_started_at).toLocaleString()}`
                                        : 'Instantly pause all simulations with a maintenance banner.'}
                                </div>
                            </div>
                            {!settings.system_frozen ? (
                                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                    <input
                                        type="text"
                                        placeholder="Freeze message…"
                                        value={freezeMsg}
                                        onChange={e => setFreezeMsg(e.target.value)}
                                        style={{
                                            padding: '0.4rem 0.6rem', borderRadius: '6px', fontSize: '0.78rem',
                                            border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                                            color: 'var(--text-primary)', width: '180px',
                                        }}
                                    />
                                    <button onClick={handleFreeze} style={{
                                        padding: '0.4rem 0.8rem', borderRadius: '6px', border: 'none',
                                        background: '#ef4444', color: '#fff', fontWeight: 700, fontSize: '0.75rem',
                                        cursor: 'pointer', whiteSpace: 'nowrap',
                                    }}>
                                        🔴 Freeze
                                    </button>
                                </div>
                            ) : (
                                <button onClick={handleUnfreeze} style={{
                                    padding: '0.4rem 0.8rem', borderRadius: '6px', border: 'none',
                                    background: '#10b981', color: '#fff', fontWeight: 700, fontSize: '0.75rem',
                                    cursor: 'pointer', whiteSpace: 'nowrap',
                                }}>
                                    🟢 Unfreeze
                                </button>
                            )}
                        </div>

                        {/* ── Pedagogical Scaffolding Controls ── */}
                        <div className={styles.controlCard} style={{
                            borderLeft: settings.prediction_gates_enabled || settings.round_recap_enabled || settings.real_world_cards_enabled
                                ? '3px solid #a855f7' : '3px solid rgba(148,163,184,0.15)',
                        }}>
                            <div style={{ flex: 1 }}>
                                <div className={styles.controlTitle}>🧠 Pedagogical Scaffolding</div>
                                <div className={styles.controlDesc}>
                                    Metacognitive features, formative checkpoints, and learner journey aids.
                                    <span style={{ fontSize: '0.6rem', color: '#a78bfa', fontStyle: 'italic', marginLeft: 4 }}>
                                        Experience level is set per-cohort during creation
                                    </span>
                                </div>

                                <div style={{
                                    display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.6rem',
                                    alignItems: 'center',
                                }}>
                                    {[
                                        { key: 'prediction_gates_enabled', label: '🔮 Predictions', default: false, tip: 'Students must predict outcomes before submitting decisions. Forces metacognitive reflection — "What do I think will happen?"' },
                                        { key: 'confidence_calibration_enabled', label: '🎰 Confidence', default: false, tip: 'Students rate their confidence (1-5) in each prediction. Tracks calibration accuracy over rounds to reveal overconfidence bias.' },
                                        { key: 'board_room_moments_enabled', label: '🏢 Board Room', default: true, tip: 'Triggers Boardroom Showdown mini-game at key rounds. Students defend their strategy under simulated board scrutiny.' },
                                        { key: 'round_recap_enabled', label: '📋 Recap', default: false, tip: 'Shows an auto-generated summary at round end: key decisions, KPI deltas, and engine events. Reduces need for facilitator verbal recap.' },
                                        { key: 'real_world_cards_enabled', label: '🌍 Case Cards', default: false, tip: 'Surfaces real-world case study cards (e.g. BP Deepwater, Unilever Living Plan) when relevant engine events fire.' },
                                        { key: 'strategy_memo_enabled', label: '📝 Memo', default: false, tip: 'Students write a strategy memo before Round 1, then compare against actual outcomes post-game. Encourages strategic planning.' },
                                        { key: 'debrief_protocol_enabled', label: '🎭 Debrief', default: false, tip: 'Enables structured debrief protocol at game end: guided reflection questions, peer discussion prompts, and learning journal.' },
                                        { key: 'self_learning_mode', label: '🎓 Self-Learn', default: false, tip: 'Activates solo self-paced mode with AI-guided hints and contextual help. For asynchronous or flipped-classroom use.' },
                                        { key: 'r6_revelation_enabled', label: '🚨 R6 Twist', default: true, tip: 'Round 6 narrative twist: a major revelation event (e.g. supply chain scandal, regulatory change) that forces strategic pivot.' },
                                        { key: 'r7_budget_allocation_enabled', label: '♻️ R7 Budget', default: true, tip: 'Round 7 budget allocation challenge: students must prioritize competing sustainability investments under constrained capital.' },
                                        { key: 'r8_tribunal_enabled', label: '⚖️ R8 Tribunal', default: true, tip: 'Round 8 stakeholder tribunal: students face a simulated ESG tribunal and must justify their track record.' },
                                    ].map(t => (
                                        <div key={t.key} className={styles.pillWrap} data-tip={t.tip}>
                                        <button
                                            onClick={async () => {
                                                const next = !settings[t.key];
                                                const res = await fetch(`${API}/api/admin/global-settings`, {
                                                    method: 'PATCH',
                                                    headers: { 'Content-Type': 'application/json', ...(facilitatorId ? { 'X-Facilitator-Id': facilitatorId } : {}) },
                                                    body: JSON.stringify({ [t.key]: next }),
                                                });
                                                if (res.ok) { loadSettings(); setSettingsStatus(`${t.label} ${next ? 'ON' : 'OFF'}`); setTimeout(() => setSettingsStatus(''), 3000); }
                                            }}
                                            style={{
                                                padding: '3px 9px', borderRadius: 4, border: 'none',
                                                background: settings[t.key] ? 'rgba(168,85,247,0.15)' : 'rgba(148,163,184,0.08)',
                                                color: settings[t.key] ? '#c084fc' : '#64748b',
                                                fontWeight: 700, fontSize: '0.68rem', cursor: 'pointer',
                                                transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                            }}
                                        >
                                            {settings[t.key] ? '●' : '○'} {t.label}
                                        </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* ── System Engine Modules Controls ── */}
                        <div className={styles.controlCard} style={{
                            borderLeft: settings.biodiversity_engine_enabled || settings.board_governance_enabled
                                ? '3px solid #10b981' : '3px solid rgba(148,163,184,0.15)',
                        }}>
                            <div style={{ flex: 1 }}>
                                <div className={styles.controlTitle}>🔬 System Engine Modules</div>
                                <div className={styles.controlDesc}>
                                    High-fidelity simulation engines. Toggle modules for different cohort complexity levels.
                                    <span style={{ fontSize: '0.6rem', color: '#4ade80', fontStyle: 'italic', marginLeft: 4 }}>
                                        Disabled engines skip gracefully — no data loss
                                    </span>
                                </div>

                                <div style={{
                                    display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.6rem',
                                    alignItems: 'center',
                                }}>
                                    {[
                                        { key: 'biodiversity_engine_enabled', label: '🌿 Biodiversity', default: true, tip: 'TNFD-aligned ecosystem health tracking. Tracks Ecosystem Health Index (EHI), deforestation risk, and water stress across BUs.' },
                                        { key: 'balance_sheet_enabled', label: '📊 Balance Sheet', default: true, tip: 'Full double-entry balance sheet: assets, liabilities, equity, D/E ratio, and covenant monitoring. Adds financial realism.' },
                                        { key: 'board_governance_enabled', label: '🏛️ Board Gov', default: true, tip: 'Board of Directors simulation: director profiles, ESG alignment scores, voting resolutions, and activist investor pressure.' },
                                        { key: 'supply_chain_network_enabled', label: '🔗 Supply Chain', default: true, tip: '3-tier supply chain network with Scope 3 emissions estimation, supplier audit trails, and cascading risk propagation.' },
                                        { key: 'npc_stakeholders_enabled', label: '👥 NPC Agents', default: true, tip: 'AI-ready NPC stakeholders (activist investor, regulator, community leader, media) that react dynamically to player decisions.' },
                                        { key: 'org_politics_enabled', label: '🤝 Org Politics', default: true, tip: 'C-suite coalition dynamics: political capital, departmental resistance, and internal change management friction.' },
                                        { key: 'branching_enabled', label: '🔀 Branching', default: true, tip: 'Non-linear R5 branching: classifies players into archetypes (Regenerative Leader, Pragmatic Optimizer, etc.) with adaptive crisis severity.' },
                                        { key: 'dynamic_cases_enabled', label: '📰 Case Studies', default: true, tip: 'Contextual real-world case injection (BP, VW, Danone, Patagonia) triggered by matching game state conditions.' },
                                        { key: 'tcfd_scenarios_enabled', label: '🌡️ TCFD', default: true, tip: 'TCFD-aligned climate scenario analysis: orderly 1.5°C, disorderly 2°C, and hothouse 4°C pathway projections.' },
                                        { key: 'meadows_leverage_enabled', label: '🎯 Leverage Pts', default: true, tip: 'Donella Meadows leverage point analysis for post-game debrief. Identifies where systemic interventions had maximum effect.' },
                                        { key: 'system_archetypes_enabled', label: '🔄 Archetypes', default: true, tip: 'Peter Senge system archetype detection: shifting the burden, fixes that fail, limits to growth, tragedy of the commons.' },
                                        { key: 'peer_learning_prompts_enabled', label: '💬 Peer Prompts', default: true, tip: 'Mid-game and post-game peer reflection prompts at R5 and R10. Encourages collaborative sense-making.' },
                                        { key: 'decision_timer_enabled', label: '⏱️ Timer', default: false, tip: 'Cognitive pressure timer: forces decisions within a time limit. Simulates real boardroom time pressure.' },
                                        { key: 'market_dynamics_enabled', label: '📈 Market Sim', default: false, tip: 'Cross-player market dynamics for multiplayer: shared carbon credit pool, competitive talent hiring, scarcity pricing.' },
                                        { key: 'regulatory_sandbox_enabled', label: '⚖️ Reg Sandbox', default: false, tip: 'Expert-tier regulatory design: students create carbon taxes, ETS, disclosure mandates with configurable parameters.' },
                                        { key: 'sdg_linkage_engine_enabled', label: '🌐 SDG Linkage', default: true, tip: 'BU-to-SDG materiality mapping engine. Tracks per-BU alignment to material SDGs (3,6,8,9,10,12,15) with live gap analysis and M_SDG terminal multiplier.' },
                                        { key: 'brsr_ngrbc_enabled', label: '🇮🇳 BRSR NGRBC', default: false, tip: 'SEBI BRSR deep-dive: 10-round NGRBC track covering all nine NGRBC principles — Governance, Workforce, Environment, Value Chain, Human Rights, Policy Advocacy, MSME Protection, Assurance & Integrated Reporting. Injects dynamic crises and awards +0.05 ESG Alpha Dividend to BRSR Pioneers.' },
                                    ].map(t => (
                                        <div key={t.key} className={styles.pillWrap} data-tip={t.tip}>
                                        <button
                                            onClick={async () => {
                                                const next = !settings[t.key];
                                                const res = await fetch(`${API}/api/admin/global-settings`, {
                                                    method: 'PATCH',
                                                    headers: { 'Content-Type': 'application/json', ...(facilitatorId ? { 'X-Facilitator-Id': facilitatorId } : {}) },
                                                    body: JSON.stringify({ [t.key]: next }),
                                                });
                                                if (res.ok) { loadSettings(); setSettingsStatus(`${t.label} ${next ? 'ON' : 'OFF'}`); setTimeout(() => setSettingsStatus(''), 3000); }
                                            }}
                                            style={{
                                                padding: '3px 9px', borderRadius: 4, border: 'none',
                                                background: settings[t.key] ? 'rgba(16,185,129,0.15)' : 'rgba(148,163,184,0.08)',
                                                color: settings[t.key] ? '#4ade80' : '#64748b',
                                                fontWeight: 700, fontSize: '0.68rem', cursor: 'pointer',
                                                transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                            }}
                                        >
                                            {settings[t.key] ? '●' : '○'} {t.label}
                                        </button>
                                        </div>
                                    ))}
                                </div>

                                {/* Decision Timer Duration (only when timer is enabled) */}
                                {settings.decision_timer_enabled && (
                                    <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600 }}>⏱️ Timer:</span>
                                        <input
                                            type="number"
                                            min="60" max="600" step="30"
                                            value={settings.decision_timer_seconds || 300}
                                            onChange={async (e) => {
                                                const val = parseInt(e.target.value) || 300;
                                                const res = await fetch(`${API}/api/admin/global-settings`, {
                                                    method: 'PATCH',
                                                    headers: { 'Content-Type': 'application/json', ...(facilitatorId ? { 'X-Facilitator-Id': facilitatorId } : {}) },
                                                    body: JSON.stringify({ decision_timer_seconds: val }),
                                                });
                                                if (res.ok) loadSettings();
                                            }}
                                            style={{
                                                width: '70px', padding: '2px 6px', borderRadius: 4,
                                                border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                                                color: 'var(--text-primary)', fontSize: '0.72rem', fontWeight: 600,
                                            }}
                                        />
                                        <span style={{ fontSize: '0.68rem', color: '#64748b' }}>seconds per round</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Hardening Phase Intelligence ── */}
            {status.hardening && (() => {
                const h = status.hardening;
                const regimeColors = { easing: '#10b981', neutral: '#94a3b8', tightening: '#f59e0b', crisis: '#ef4444' };
                const regimeIcons = { easing: '🕊️', neutral: '⚖️', tightening: '🦅', crisis: '🔥' };
                const hasData = Object.keys(h.macro_rate_distribution || {}).length > 0 ||
                                Object.keys(h.pathway_distribution || {}).length > 0;
                if (!hasData) return null;
                return (
                    <div className={styles.section}>
                        <h3>🧪 Hardening Phase Intelligence</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem' }}>
                            {/* Macro Rate Distribution */}
                            <div style={{
                                padding: '0.8rem', borderRadius: 8,
                                background: 'rgba(99,102,241,0.04)',
                                border: '1px solid rgba(99,102,241,0.15)',
                            }}>
                                <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#818cf8', marginBottom: '0.5rem' }}>
                                    🏦 Monetary Policy Distribution
                                </div>
                                {Object.entries(h.macro_rate_distribution || {}).map(([regime, count]) => (
                                    <div key={regime} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                                        <span style={{ fontSize: '0.85rem' }}>{regimeIcons[regime] || '📊'}</span>
                                        <span style={{ flex: 1, fontSize: '0.72rem', fontWeight: 600, color: regimeColors[regime] || '#94a3b8', textTransform: 'capitalize' }}>{regime}</span>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#e2e8f0', fontFamily: "'JetBrains Mono', monospace" }}>{count}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Ending Pathways */}
                            <div style={{
                                padding: '0.8rem', borderRadius: 8,
                                background: 'rgba(168,85,247,0.04)',
                                border: '1px solid rgba(168,85,247,0.15)',
                            }}>
                                <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#a78bfa', marginBottom: '0.5rem' }}>
                                    🗺️ Active Ending Pathways
                                </div>
                                {Object.keys(h.pathway_distribution || {}).length > 0 ? Object.entries(h.pathway_distribution).map(([path, count]) => (
                                    <div key={path} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                                        <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#c4b5fd', textTransform: 'capitalize' }}>{path.replace(/_/g, ' ')}</span>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#e2e8f0', fontFamily: "'JetBrains Mono', monospace" }}>{count}</span>
                                    </div>
                                )) : (
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontStyle: 'italic' }}>No R10 completions yet</div>
                                )}
                            </div>

                            {/* NBS + Retraining Outcomes */}
                            <div style={{
                                padding: '0.8rem', borderRadius: 8,
                                background: 'rgba(16,185,129,0.04)',
                                border: '1px solid rgba(16,185,129,0.15)',
                            }}>
                                <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#10b981', marginBottom: '0.5rem' }}>
                                    🌿 Stochastic Outcomes
                                </div>
                                <div style={{ fontSize: '0.68rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                                    <strong style={{ color: '#4ade80' }}>NBS Success:</strong>{' '}
                                    {h.nbs_outcomes?.succeeded || 0} ✓ · {h.nbs_outcomes?.failed || 0} ✗ · {h.nbs_outcomes?.not_triggered || 0} pending
                                </div>
                                <div style={{ fontSize: '0.68rem', color: '#cbd5e1' }}>
                                    <strong style={{ color: '#818cf8' }}>Retraining:</strong>{' '}
                                    {h.retraining_outcomes?.succeeded || 0} ✓ · {h.retraining_outcomes?.failed || 0} ✗
                                </div>
                            </div>

                            {/* Scope 3 + AI Act */}
                            <div style={{
                                padding: '0.8rem', borderRadius: 8,
                                background: 'rgba(245,158,11,0.04)',
                                border: '1px solid rgba(245,158,11,0.15)',
                            }}>
                                <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#f59e0b', marginBottom: '0.5rem' }}>
                                    📋 Regulatory Exposure
                                </div>
                                <div style={{ fontSize: '0.68rem', color: '#cbd5e1', marginBottom: '0.3rem' }}>
                                    <strong style={{ color: '#fbbf24' }}>Scope 3 Completeness:</strong>{' '}
                                    {h.avg_scope3_completeness != null ? `${h.avg_scope3_completeness}% avg` : 'Not yet triggered'}
                                </div>
                                <div style={{ fontSize: '0.68rem', color: '#cbd5e1' }}>
                                    <strong style={{ color: '#f87171' }}>AI Monetised:</strong>{' '}
                                    {h.ai_monetised_count} sessions — {h.ai_monetised_count > 0 ? 'EU AI Act costs active R7+' : 'no AI deployment'}
                                </div>
                            </div>

                            {/* SDG Orchestrator Intelligence */}
                            {h.sdg_intelligence && (() => {
                                const sdg = h.sdg_intelligence;
                                return (
                                    <div style={{
                                        padding: '0.8rem', borderRadius: 8,
                                        background: 'linear-gradient(135deg, rgba(99,102,241,0.06), rgba(0,229,195,0.04))',
                                        border: '1px solid rgba(99,102,241,0.2)',
                                        gridColumn: '1 / -1',
                                    }}>
                                        <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#818cf8', marginBottom: '0.5rem' }}>
                                            🌐 SDG Orchestrator Intelligence
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.6rem', marginBottom: '0.5rem' }}>
                                            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: 6, textAlign: 'center' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: 900, color: '#818cf8', fontFamily: "'JetBrains Mono', monospace" }}>{sdg.sdg_track_completions || 0}</div>
                                                <div style={{ fontSize: '0.58rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Track Completions</div>
                                            </div>
                                            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: 6, textAlign: 'center' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: 900, color: '#00e5c3', fontFamily: "'JetBrains Mono', monospace" }}>{sdg.avg_group_sdg_score?.toFixed(1) ?? '—'}</div>
                                                <div style={{ fontSize: '0.58rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Avg SDG Score</div>
                                            </div>
                                            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: 6, textAlign: 'center' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: 900, color: sdg.avg_m_sdg >= 1.1 ? '#10b981' : '#f59e0b', fontFamily: "'JetBrains Mono', monospace" }}>{sdg.avg_m_sdg?.toFixed(4) ?? '—'}×</div>
                                                <div style={{ fontSize: '0.58rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Avg M<sub>SDG</sub></div>
                                            </div>
                                            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: 6, textAlign: 'center' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: 900, color: (sdg.total_material_gaps || 0) > 5 ? '#ef4444' : '#10b981', fontFamily: "'JetBrains Mono', monospace" }}>{sdg.total_material_gaps || 0}</div>
                                                <div style={{ fontSize: '0.58rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Active Gaps</div>
                                            </div>
                                        </div>
                                        {sdg.m_sdg_distribution && Object.keys(sdg.m_sdg_distribution).length > 0 && (
                                            <div style={{ marginTop: '0.4rem' }}>
                                                <div style={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, marginBottom: '0.3rem' }}>M_SDG Distribution</div>
                                                {Object.entries(sdg.m_sdg_distribution).map(([band, count]) => (
                                                    <div key={band} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                                                        <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#c4b5fd', width: '80px' }}>{band}</span>
                                                        <div style={{ flex: 1, height: '6px', borderRadius: 3, background: 'rgba(255,255,255,0.04)' }}>
                                                            <div style={{ width: `${Math.min(count * 20, 100)}%`, height: '100%', borderRadius: 3, background: 'linear-gradient(90deg, #818cf8, #00e5c3)' }} />
                                                        </div>
                                                        <span style={{ fontSize: '0.68rem', fontWeight: 800, color: '#e2e8f0', fontFamily: "'JetBrains Mono', monospace" }}>{count}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                );
                            })()}

                            {/* BRSR NGRBC Intelligence */}
                            {h.brsr_intelligence && (() => {
                                const brsr = h.brsr_intelligence;
                                return (
                                    <div style={{
                                        padding: '0.8rem', borderRadius: 8,
                                        background: 'linear-gradient(135deg, rgba(16,185,129,0.06), rgba(245,158,11,0.04))',
                                        border: '1px solid rgba(16,185,129,0.2)',
                                        gridColumn: '1 / -1',
                                    }}>
                                        <div style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#10b981', marginBottom: '0.5rem' }}>
                                            🇮🇳 BRSR NGRBC Intelligence
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.6rem', marginBottom: '0.5rem' }}>
                                            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: 6, textAlign: 'center' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: 900, color: '#10b981', fontFamily: "'JetBrains Mono', monospace" }}>{brsr.brsr_track_completions || 0}</div>
                                                <div style={{ fontSize: '0.58rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Track Completions</div>
                                            </div>
                                            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: 6, textAlign: 'center' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: 900, color: (brsr.pioneer_count || 0) > 0 ? '#10b981' : '#94a3b8', fontFamily: "'JetBrains Mono', monospace" }}>{brsr.pioneer_count || 0}</div>
                                                <div style={{ fontSize: '0.58rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>BRSR Pioneers</div>
                                            </div>
                                            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: 6, textAlign: 'center' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: 900, color: (brsr.greenwash_risk_count || 0) > 0 ? '#ef4444' : '#94a3b8', fontFamily: "'JetBrains Mono', monospace" }}>{brsr.greenwash_risk_count || 0}</div>
                                                <div style={{ fontSize: '0.58rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Greenwash Risk</div>
                                            </div>
                                            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: 6, textAlign: 'center' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: 900, color: (brsr.governance_fragility_count || 0) > 0 ? '#f59e0b' : '#94a3b8', fontFamily: "'JetBrains Mono', monospace" }}>{brsr.governance_fragility_count || 0}</div>
                                                <div style={{ fontSize: '0.58rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Gov Fragility</div>
                                            </div>
                                        </div>
                                        {brsr.avg_brsr_score != null && (
                                            <div style={{ fontSize: '0.68rem', color: '#cbd5e1', marginTop: '0.3rem' }}>
                                                <strong style={{ color: '#10b981' }}>Avg BRSR Score:</strong>{' '}
                                                {brsr.avg_brsr_score.toFixed(1)}/100 · <strong style={{ color: '#f59e0b' }}>Crises Injected:</strong> {brsr.crises_injected || 0}
                                            </div>
                                        )}
                                    </div>
                                );
                            })()}
                        </div>
                    </div>
                );
            })()}

            {Object.keys(status.round_distribution).length > 0 && (
                <div className={styles.section}>
                    <h3>Round Distribution</h3>
                    <div className={styles.roundBars}>
                        {Object.entries(status.round_distribution).sort().map(([r, count]) => (
                            <div key={r} className={styles.roundBar}>
                                <div className={styles.roundBarLabel}>{r}</div>
                                <div className={styles.roundBarTrack}>
                                    <div className={styles.roundBarFill} style={{ width: `${Math.min(count * 20, 100)}%` }} />
                                </div>
                                <span className={styles.roundBarCount}>{count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {status.recent_audit?.length > 0 && (
                <div className={styles.section}>
                    <h3>Recent Activity</h3>
                    <div className={styles.activityList}>
                        {status.recent_audit.slice(0, 5).map((e, i) => (
                            <div key={i} className={styles.activityItem}>
                                <span className={styles.activityAction}>{e.action.replace(/_/g, ' ')}</span>
                                <span className={styles.activityTime}>{new Date(e.timestamp).toLocaleString()}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
