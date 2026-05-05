'use client';
import { useState, useEffect, useRef } from 'react';
import { useCurrency, CURRENCIES } from '../contexts/CurrencyContext';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// ─── Preset card color palette ───────────────────────────────────────────────
const PRESET_COLORS = [
    { color: '#3b82f6', bg: 'rgba(59,130,246,0.06)',  border: 'rgba(59,130,246,0.2)' },
    { color: '#10b981', bg: 'rgba(16,185,129,0.06)',  border: 'rgba(16,185,129,0.2)' },
    { color: '#f59e0b', bg: 'rgba(245,158,11,0.06)',  border: 'rgba(245,158,11,0.2)' },
    { color: '#8b5cf6', bg: 'rgba(139,92,246,0.06)',  border: 'rgba(139,92,246,0.2)' },
    { color: '#ef4444', bg: 'rgba(239,68,68,0.06)',   border: 'rgba(239,68,68,0.2)' },
    { color: '#06b6d4', bg: 'rgba(6,182,212,0.06)',   border: 'rgba(6,182,212,0.2)' },
];

// ─── Per-group accent color palette ─────────────────────────────────────────
const GROUP_ACCENTS = {
    'Inflation & Macro':              { h: '199', color: '#38bdf8', glow: 'rgba(56,189,248,0.16)', track: 'linear-gradient(90deg,#0ea5e9,#38bdf8)' },
    'Investment Lag & Overruns':      { h: '24',  color: '#fb923c', glow: 'rgba(251,146,60,0.16)',  track: 'linear-gradient(90deg,#ea580c,#fb923c)' },
    'Neglect & Debt':                 { h: '340', color: '#f472b6', glow: 'rgba(244,114,182,0.16)', track: 'linear-gradient(90deg,#db2777,#f472b6)' },
    'Cannibalization & Contagion':    { h: '271', color: '#a78bfa', glow: 'rgba(167,139,250,0.16)', track: 'linear-gradient(90deg,#7c3aed,#a78bfa)' },
    'Board & Dividends':              { h: '43',  color: '#fbbf24', glow: 'rgba(251,191,36,0.16)',  track: 'linear-gradient(90deg,#d97706,#fbbf24)' },
    'ESG & Greenwashing':             { h: '142', color: '#4ade80', glow: 'rgba(74,222,128,0.16)',  track: 'linear-gradient(90deg,#16a34a,#4ade80)' },
    'Competition & Lock-In':          { h: '0',   color: '#f87171', glow: 'rgba(248,113,113,0.16)', track: 'linear-gradient(90deg,#dc2626,#f87171)' },
    'Information & Fog':              { h: '220', color: '#93c5fd', glow: 'rgba(147,197,253,0.16)', track: 'linear-gradient(90deg,#3b82f6,#93c5fd)' },
    'Stakeholder Dynamics':           { h: '168', color: '#34d399', glow: 'rgba(52,211,153,0.16)',  track: 'linear-gradient(90deg,#059669,#34d399)' },
};

const TOOLTIP_DATA = {
    inflation_rate:                 { def: 'Baseline year-over-year increase in OPEX costs.', impact: 'Erodes EBITDA over time. Hyperinflation directly shrinks profit margins if revenue doesn\'t keep pace.' },
    implementation_lag_threshold:   { def: 'Probability that a CapEx project is delayed by 1 round.', impact: 'Postpones the benefits to subsequent rounds, damaging short-term liquidity.' },
    overrun_probability:            { def: 'Chance that a CapEx project goes over budget.', impact: 'Randomly triggers budget overruns, unexpectedly draining corporate treasury.' },
    overrun_severity:               { def: 'Percentage increase in cost when an overrun occurs.', impact: 'Scales the damage to the treasury when an overrun triggers (e.g., 20% extra CapEx).' },
    overrun_capex_floor:            { def: 'Minimum project cost required to trigger overrun risks.', impact: 'Protects small tactical investments from triggering massive cost penalties.' },
    technical_debt_threshold:       { def: 'Consecutive rounds a BU can lack investment before accumulating debt.', impact: 'Forces players to allocate baseline maintenance CapEx or suffer exponential margin erosion.' },
    technical_debt_penalty:         { def: 'Margin penalty multiplier applied when a BU is starved of CapEx.', impact: 'Steeply reduces OPEX efficiency and kills EBITDA if assets are neglected.' },
    talent_neglect_threshold:       { def: 'Deficit in reputation/ESG investment before talent attrition begins.', impact: 'Connects ESG metrics to operational talent retention.' },
    talent_neglect_penalty:         { def: 'Margin penalty applied due to high staff turnover and burnout.', impact: 'Creates a hidden cost to purely financial (anti-ESG) playstyles.' },
    cannibalization_rate:           { def: 'Percentage of new revenue that cannibalizes existing BU revenue.', impact: 'Limits exponential growth by ensuring new investments slightly eat into older product lines.' },
    supply_chain_overlap_coeff:     { def: 'Degree of shared supply chain risk across Business Units.', impact: 'A crisis in one BU bleeds over and damages the margins of adjacent BUs proportionally.' },
    cash_conversion_base:           { def: 'Baseline efficiency of converting EBITDA to raw Treasury cash.', impact: 'Reflects working capital locked in operations. Low values restrict liquidity even when highly profitable.' },
    dividend_cut_threshold:         { def: 'Minimum safe EBITDA ratio before dividends are automatically slashed.', impact: 'Creates a hard floor where poor performance instantly triggers market panic.' },
    dividend_reputation_penalty:    { def: 'Drop in global reputation if dividends are cut.', impact: 'Severely damages social license and trust if the CFO cannot manage cash flow.' },
    greenwashing_investment_threshold: { def: 'Minimum threshold of actual ESG CapEx required to back up PR claims.', impact: 'Checks if a player is talking a big game but starving real sustainability initiatives.' },
    greenwashing_penalty:           { def: 'Reputation damage when caught greenwashing.', impact: 'Triggers catastrophic trust loss if a player invests purely in Marketing while ignoring ESG foundations.' },
    competitor_growth_rate:         { def: 'Baseline organic growth of the competitor\'s EBITDA each round.', impact: 'Acts as a rising tide. If the player stagnates, they will lose market leadership.' },
    lockin_streak_threshold:        { def: 'Consecutive rounds required pursuing a single strategy to gain synergy.', impact: 'Rewards long-term strategic consistency instead of erratic pivot-every-round behaviors.' },
    lockin_synergy_penalty:         { def: 'Penalty applied if a player breaks a long-term strategic streak.', impact: 'Creates a switching cost, making it painful to abandon mature strategies.' },
    fog_of_war_rounds:              { def: 'Number of rounds into the future that the AI masks exact results.', impact: 'Forces players to deal with uncertainty rather than min-maxing a spreadsheet.' },
    fog_noise_range:                { def: 'Variance injected into projected future returns.', impact: 'Creates a standard deviation in ROI calculations.' },
    stakeholder_fatigue_factor:     { def: 'Rate at which the public demands newer, better ESG initiatives.', impact: 'Prevents a player from riding on the coattails of early wins; they must continuously innovate.' },
};



const GROUPS = [
    { label: 'Inflation & Macro',           icon: '📈', keys: ['inflation_rate'] },
    { label: 'Investment Lag & Overruns',   icon: '⏱️', keys: ['implementation_lag_threshold', 'overrun_probability', 'overrun_severity', 'overrun_capex_floor'] },
    { label: 'Neglect & Debt',              icon: '🔧', keys: ['technical_debt_threshold', 'technical_debt_penalty', 'talent_neglect_threshold', 'talent_neglect_penalty'] },
    { label: 'Cannibalization & Contagion', icon: '🔗', keys: ['cannibalization_rate', 'supply_chain_overlap_coeff', 'cash_conversion_base'] },
    { label: 'Board & Dividends',           icon: '💰', keys: ['dividend_cut_threshold', 'dividend_reputation_penalty'] },
    { label: 'ESG & Greenwashing',          icon: '🌿', keys: ['greenwashing_investment_threshold', 'greenwashing_penalty'] },
    { label: 'Competition & Lock-In',       icon: '🏆', keys: ['competitor_growth_rate', 'lockin_streak_threshold', 'lockin_synergy_penalty'] },
    { label: 'Information & Fog',           icon: '🌫️', keys: ['fog_of_war_rounds', 'fog_noise_range'] },
    { label: 'Stakeholder Dynamics',        icon: '📣', keys: ['stakeholder_fatigue_factor'] },
];

// ─── Helpers ─────────────────────────────────────────────
function isFloatPct(key, val) {
    return typeof val === 'number' && !Number.isInteger(val) && Math.abs(val) < 1;
}

function getRange(key, float) {
    if (!float) {
        if (key === 'overrun_capex_floor') return { min: 0, max: 10000000, step: 500000 };
        if (key.includes('threshold') && !key.includes('invest')) return { min: 1, max: 10, step: 1 };
        if (key.includes('penalty') && !float) return { min: 0, max: 20, step: 0.5 };
        return { min: 0, max: 10, step: 1 };
    }
    return { min: 0, max: 100, step: 0.5 };
}

function formatVal(key, val, currSymbol) {
    const sym = currSymbol || '$';
    if (typeof val !== 'number') return String(val);
    if (isFloatPct(key, val)) return `${(val * 100).toFixed(1)}%`;
    if (key === 'overrun_capex_floor') return `${sym}${(val / 1000000).toFixed(1)}M`;
    if (Number.isInteger(val)) return val.toLocaleString();
    return val.toFixed(2);
}

function pct(key, val) {
    const float = isFloatPct(key, val);
    const r = getRange(key, float);
    const v = float ? val * 100 : val;
    return Math.min(100, Math.max(0, ((v - r.min) / (r.max - r.min)) * 100));
}

// ─── Rich tooltip popover component ─────────────────────
function Tooltip({ data, accentColor }) {
    if (!data) return null;
    return (
        <div style={{
            position: 'absolute', zIndex: 999, bottom: 'calc(100% + 8px)', left: '50%',
            transform: 'translateX(-50%)', width: '280px', pointerEvents: 'none',
            background: 'rgba(15,23,42,0.97)', border: `1px solid ${accentColor}44`,
            borderRadius: '10px', padding: '12px 14px',
            boxShadow: `0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04), 0 2px 8px ${accentColor}22`,
            backdropFilter: 'blur(12px)',
        }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.12em', color: accentColor, marginBottom: '6px' }}>
                Definition
            </div>
            <p style={{ margin: '0 0 10px', fontSize: '0.75rem', color: '#e2e8f0', lineHeight: 1.6 }}>
                {data.def}
            </p>
            <div style={{ fontSize: '0.65rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.12em', color: '#f59e0b', marginBottom: '6px' }}>
                ⚡ Simulation Impact
            </div>
            <p style={{ margin: 0, fontSize: '0.75rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                {data.impact}
            </p>
            {/* Arrow */}
            <div style={{
                position: 'absolute', bottom: '-5px', left: '50%', transform: 'translateX(-50%) rotate(45deg)',
                width: '8px', height: '8px',
                background: 'rgba(15,23,42,0.97)', borderRight: `1px solid ${accentColor}44`, borderBottom: `1px solid ${accentColor}44`,
            }} />
        </div>
    );
}

// ─── Custom slider row ────────────────────────────────────
function TunableRow({ varKey, val, accentColor, trackGradient, onChange, currSymbol }) {
    const [hovering, setHovering] = useState(false);
    const [editing, setEditing] = useState(false);
    const [draft, setDraft] = useState('');
    const inputRef = useRef(null);

    const float = isFloatPct(varKey, val);
    const range = getRange(varKey, float);
    const sliderVal = float ? val * 100 : val;
    const fillPct = pct(varKey, val);
    const tdata = TOOLTIP_DATA[varKey];

    const handleSlider = (e) => onChange(varKey, float ? parseFloat(e.target.value) / 100 : parseFloat(e.target.value));

    const startEdit = () => {
        setDraft(float ? (val * 100).toFixed(1) : String(val));
        setEditing(true);
        setTimeout(() => inputRef.current?.select(), 50);
    };

    const commitEdit = () => {
        const n = parseFloat(draft);
        if (!isNaN(n)) onChange(varKey, float ? n / 100 : n);
        setEditing(false);
    };

    // Human-readable label from snake_case
    const label = varKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

    return (
        <div
            style={{
                position: 'relative',
                padding: '14px 16px',
                borderRadius: '10px',
                border: hovering ? `1px solid ${accentColor}55` : '1px solid transparent',
                background: hovering ? `rgba(255,255,255,0.025)` : 'transparent',
                transition: 'border-color 0.15s, background 0.15s',
                cursor: 'default',
            }}
            onMouseEnter={() => setHovering(true)}
            onMouseLeave={() => setHovering(false)}
        >
            {/* Rich tooltip */}
            {hovering && tdata && <Tooltip data={tdata} accentColor={accentColor} />}

            {/* Header row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '10px', gap: '8px' }}>
                <div style={{ minWidth: 0 }}>
                    {/* Human label */}
                    <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary,#f1f5f9)', lineHeight: 1.2, marginBottom: '2px' }}>
                        {label}
                    </div>
                    {/* Machine key */}
                    <code style={{ fontSize: '0.68rem', color: 'var(--text-muted,#64748b)', fontFamily: 'var(--font-mono,monospace)', letterSpacing: '0.04em' }}>
                        {varKey}
                    </code>
                </div>
                {/* Value badge — click to edit numerically */}
                {editing ? (
                    <input
                        ref={inputRef}
                        value={draft}
                        onChange={e => setDraft(e.target.value)}
                        onBlur={commitEdit}
                        onKeyDown={e => { if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') setEditing(false); }}
                        style={{
                            width: '72px', textAlign: 'right', background: 'rgba(255,255,255,0.08)',
                            border: `1px solid ${accentColor}`, borderRadius: '5px',
                            color: accentColor, fontFamily: 'var(--font-mono,monospace)', fontWeight: 700,
                            fontSize: '0.88rem', padding: '2px 6px', outline: 'none',
                        }}
                    />
                ) : (
                    <button
                        onClick={startEdit}
                        title="Click to type a precise value"
                        style={{
                            background: `${accentColor}18`, border: `1px solid ${accentColor}33`,
                            borderRadius: '5px', padding: '2px 10px', cursor: 'text',
                            color: accentColor, fontFamily: 'var(--font-mono,monospace)', fontWeight: 700,
                            fontSize: '0.88rem', whiteSpace: 'nowrap', transition: 'all 0.15s',
                            flexShrink: 0,
                        }}
                        onMouseOver={e => { e.currentTarget.style.background = `${accentColor}28`; e.currentTarget.style.borderColor = `${accentColor}66`; }}
                        onMouseOut={e => { e.currentTarget.style.background = `${accentColor}18`; e.currentTarget.style.borderColor = `${accentColor}33`; }}
                    >
                        {formatVal(varKey, val, currSymbol)}
                    </button>
                )}
            </div>

            {/* Custom slider track */}
            <div style={{ position: 'relative', height: '20px', display: 'flex', alignItems: 'center' }}>
                {/* Track background */}
                <div style={{
                    position: 'absolute', left: 0, right: 0, height: '4px',
                    borderRadius: '2px', background: 'rgba(255,255,255,0.08)',
                }}/>
                {/* Fill */}
                <div style={{
                    position: 'absolute', left: 0, width: `${fillPct}%`, height: '4px',
                    borderRadius: '2px', background: trackGradient, transition: 'width 0.1s',
                }}/>
                {/* Range input — invisible but functional */}
                <input
                    type="range"
                    min={range.min} max={range.max} step={range.step}
                    value={sliderVal}
                    onChange={handleSlider}
                    style={{
                        position: 'absolute', left: 0, right: 0, width: '100%', height: '20px',
                        opacity: 0, cursor: 'pointer', margin: 0,
                    }}
                />
                {/* Custom thumb */}
                <div style={{
                    position: 'absolute',
                    left: `calc(${fillPct}% - 7px)`,
                    width: '14px', height: '14px', borderRadius: '50%',
                    background: '#fff', border: `2px solid ${accentColor}`,
                    boxShadow: `0 0 0 3px ${accentColor}22, 0 2px 4px rgba(0,0,0,0.3)`,
                    transition: 'left 0.1s, box-shadow 0.15s',
                    pointerEvents: 'none',
                    ...(hovering ? { boxShadow: `0 0 0 5px ${accentColor}33, 0 2px 4px rgba(0,0,0,0.3)` } : {}),
                }}/>
            </div>

            {/* Description — always visible, never truncated */}
            {tdata && (
                <p style={{ margin: '8px 0 0', fontSize: '0.68rem', color: 'var(--text-muted,#64748b)', lineHeight: 1.55 }}>
                    {tdata.def}
                </p>
            )}
        </div>
    );
}

// ─── Main Component ───────────────────────────────────────
export default function EconomicEngineTunables() {
    const { currency, setCurrency } = useCurrency();
    const [tunables, setTunables] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState(null);
    const [activePreset, setActivePreset] = useState(null);
    const [dirty, setDirty] = useState(false);

    // API-backed presets (merged from ScenarioPresets)
    const [presets, setPresets] = useState([]);
    const [applyingPreset, setApplyingPreset] = useState(null);
    const [showCreatePreset, setShowCreatePreset] = useState(false);
    const [newPresetName, setNewPresetName] = useState('');
    const [newPresetDesc, setNewPresetDesc] = useState('');
    const [newPresetIcon, setNewPresetIcon] = useState('⚙️');

    const loadPresets = () => {
        fetch(`${API}/api/admin/scenario-presets`)
            .then(r => r.json())
            .then(d => setPresets(d.presets || []))
            .catch(() => {});
    };

    useEffect(() => {
        fetch(`${API}/api/admin/engine-tunables`)
            .then(r => r.json())
            .then(d => { setTunables(d.tunables || {}); setLoading(false); })
            .catch(() => setLoading(false));
        loadPresets();
    }, []);

    const handleChange = (key, value) => {
        setTunables(prev => ({ ...prev, [key]: value }));
        setActivePreset(null);
        setDirty(true);
    };

    const handleSave = async () => {
        setSaving(true); setError(null);
        try {
            const res = await fetch(`${API}/api/admin/engine-tunables`, {
                method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(tunables),
            });
            if (res.ok) { setSaved(true); setDirty(false); setTimeout(() => setSaved(false), 2500); }
            else setError('Save failed — server returned an error');
        } catch { setError('Save failed — network error'); }
        setSaving(false);
    };

    const applyPreset = async (presetId) => {
        setApplyingPreset(presetId);
        try {
            const res = await fetch(`${API}/api/admin/scenario-presets/apply/${presetId}`, { method: 'POST' });
            if (res.ok) {
                const d = await res.json();
                setTunables(d.tunables);
                setActivePreset(presetId);
                setDirty(false);
            }
        } catch {}
        setApplyingPreset(null);
    };

    const saveCustomPreset = async () => {
        if (!newPresetName.trim()) return;
        try {
            const res = await fetch(`${API}/api/admin/scenario-presets`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newPresetName, description: newPresetDesc, icon: newPresetIcon, tunables }),
            });
            if (res.ok) { loadPresets(); setShowCreatePreset(false); setNewPresetName(''); setNewPresetDesc(''); }
        } catch {}
    };

    const deletePreset = async (presetId) => {
        if (!confirm('Delete this custom preset?')) return;
        await fetch(`${API}/api/admin/scenario-presets/${presetId}`, { method: 'DELETE' });
        loadPresets();
    };

    if (loading) return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: 'var(--text-muted,#64748b)', gap: '10px' }}>
            <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: '2px solid currentColor', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite' }} />
            Loading engine tunables…
            <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
        </div>
    );

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', fontFamily: 'var(--font-sans,system-ui,sans-serif)' }}>

            {/* ── Scenario Presets (API-backed) ── */}
            <div style={{
                background: 'var(--bg-card,#1e293b)', border: '1px solid var(--border-subtle,#334155)',
                borderRadius: '14px',
            }}>
                {/* Header with create button */}
                <div style={{
                    padding: '14px 20px',
                    background: 'linear-gradient(90deg, rgba(99,102,241,0.08), transparent)',
                    borderBottom: '1px solid var(--border-subtle,#334155)',
                    display: 'flex', alignItems: 'center', gap: '10px',
                    borderRadius: '13px 13px 0 0',
                }}>
                    <span style={{ fontSize: '0.9rem' }}>⚡</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-primary,#f1f5f9)' }}>Scenario Presets</span>
                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted,#64748b)', marginLeft: '4px' }}>— One-click templates & custom snapshots</span>
                    <button
                        onClick={() => setShowCreatePreset(!showCreatePreset)}
                        style={{
                            marginLeft: 'auto', padding: '4px 10px', borderRadius: '5px', fontSize: '0.68rem',
                            fontWeight: 700, border: '1px solid var(--border-subtle,#334155)', cursor: 'pointer',
                            background: showCreatePreset ? 'rgba(239,68,68,0.1)' : 'rgba(255,255,255,0.04)',
                            color: showCreatePreset ? '#f87171' : 'var(--text-muted,#94a3b8)',
                        }}
                    >
                        {showCreatePreset ? '✕ Cancel' : '+ Save Current'}
                    </button>
                </div>

                {/* Create custom preset drawer */}
                {showCreatePreset && (
                    <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle,#334155)', display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <select value={newPresetIcon} onChange={e => setNewPresetIcon(e.target.value)} style={{
                            padding: '6px', borderRadius: '6px', border: '1px solid var(--border-subtle,#334155)',
                            background: 'rgba(255,255,255,0.04)', fontSize: '1rem', cursor: 'pointer', color: 'var(--text-primary,#f1f5f9)',
                        }}>
                            {['⚙️','🎯','🏢','🎓','💼','🔥','🌍','🧪','⚖️','⚔️','🌱'].map(i => <option key={i} value={i}>{i}</option>)}
                        </select>
                        <input type="text" placeholder="Preset name…" value={newPresetName} onChange={e => setNewPresetName(e.target.value)}
                            style={{ flex: '1 1 120px', padding: '6px 10px', borderRadius: '6px', fontSize: '0.78rem', border: '1px solid var(--border-subtle,#334155)', background: 'rgba(255,255,255,0.04)', color: 'var(--text-primary,#f1f5f9)', outline: 'none' }} />
                        <input type="text" placeholder="Description…" value={newPresetDesc} onChange={e => setNewPresetDesc(e.target.value)}
                            style={{ flex: '2 1 180px', padding: '6px 10px', borderRadius: '6px', fontSize: '0.78rem', border: '1px solid var(--border-subtle,#334155)', background: 'rgba(255,255,255,0.04)', color: 'var(--text-primary,#f1f5f9)', outline: 'none' }} />
                        <button onClick={saveCustomPreset} style={{
                            padding: '6px 14px', borderRadius: '6px', border: 'none',
                            background: newPresetName.trim() ? '#10b981' : 'rgba(255,255,255,0.06)',
                            color: newPresetName.trim() ? '#fff' : 'var(--text-muted,#64748b)', fontWeight: 700, fontSize: '0.75rem',
                            cursor: newPresetName.trim() ? 'pointer' : 'default',
                        }}>💾 Save</button>
                    </div>
                )}

                {/* Preset grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', padding: '16px 20px' }}>
                    {presets.length === 0 && (
                        <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '20px', color: 'var(--text-muted,#64748b)', fontSize: '0.78rem' }}>
                            No presets configured. Create one using the button above.
                        </div>
                    )}
                    {presets.map((p, idx) => {
                        const pc = PRESET_COLORS[idx % PRESET_COLORS.length];
                        const isActive = activePreset === p.id;
                        const isApplying = applyingPreset === p.id;
                        return (
                            <button key={p.id} onClick={() => applyPreset(p.id)} disabled={isApplying}
                                style={{
                                    padding: '14px 16px', borderRadius: '10px', border: `1.5px solid ${isActive ? pc.color : pc.border}`,
                                    background: isActive ? pc.bg : 'rgba(255,255,255,0.02)',
                                    cursor: isApplying ? 'wait' : 'pointer', textAlign: 'left', transition: 'all 0.15s',
                                    boxShadow: isActive ? `0 0 0 3px ${pc.color}22` : 'none',
                                    outline: 'none', position: 'relative', opacity: isApplying ? 0.6 : 1,
                                }}
                                onMouseOver={e => { if (!isActive && !isApplying) { e.currentTarget.style.borderColor = pc.color; e.currentTarget.style.background = pc.bg; }}}
                                onMouseOut={e => { if (!isActive && !isApplying) { e.currentTarget.style.borderColor = pc.border; e.currentTarget.style.background = 'rgba(255,255,255,0.02)'; }}}
                            >
                                {p.is_custom && <span onClick={e => { e.stopPropagation(); deletePreset(p.id); }} style={{ position: 'absolute', top: '6px', right: '8px', fontSize: '0.7rem', color: 'var(--text-muted,#64748b)', cursor: 'pointer' }} title="Delete">×</span>}
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                                    <span style={{ fontSize: '1.1rem' }}>{p.icon}</span>
                                    <span style={{ fontSize: '0.78rem', fontWeight: 700, color: isActive ? pc.color : 'var(--text-primary,#f1f5f9)' }}>
                                        {isApplying ? '⏳ Applying…' : p.name}
                                    </span>
                                    {p.is_custom && <span style={{ fontSize: '0.5rem', fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', padding: '1px 5px', borderRadius: '3px', background: 'rgba(245,158,11,0.12)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.3)' }}>Custom</span>}
                                </div>
                                <p style={{ margin: 0, fontSize: '0.68rem', color: 'var(--text-muted,#64748b)', lineHeight: 1.5 }}>{p.description}</p>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* ── Currency Selector ── */}
            <div style={{
                background: 'var(--bg-card,#1e293b)', border: '1px solid var(--border-subtle,#334155)',
                borderRadius: '14px', overflow: 'hidden',
            }}>
                {/* Header */}
                <div style={{
                    padding: '14px 20px',
                    background: 'linear-gradient(90deg, rgba(251,191,36,0.08), transparent)',
                    borderBottom: '1px solid var(--border-subtle,#334155)',
                    display: 'flex', alignItems: 'center', gap: '10px',
                    borderLeft: '3px solid #fbbf24',
                }}>
                    <span style={{ fontSize: '0.9rem' }}>💱</span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#fbbf24' }}>Simulation Currency</span>
                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted,#64748b)', marginLeft: '4px' }}>— Display currency for all monetary values</span>
                    {/* Active indicator */}
                    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{
                            fontSize: '1.1rem',
                            lineHeight: 1,
                        }}>{currency.flag}</span>
                        <span style={{
                            fontSize: '0.68rem', fontWeight: 700,
                            padding: '2px 8px', borderRadius: '4px',
                            background: 'rgba(251,191,36,0.1)',
                            border: '1px solid rgba(251,191,36,0.25)',
                            color: '#fbbf24',
                            fontFamily: 'var(--font-mono,monospace)',
                        }}>{currency.symbol} {currency.code}</span>
                    </div>
                </div>

                {/* Toggle strip */}
                <div style={{ padding: '16px 20px' }}>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(6, 1fr)',
                        gap: '6px',
                        background: 'rgba(255,255,255,0.03)',
                        borderRadius: '10px',
                        padding: '6px',
                        border: '1px solid rgba(255,255,255,0.05)',
                    }}>
                        {CURRENCIES.map(c => {
                            const isActive = c.code === currency.code;
                            return (
                                <button
                                    key={c.code}
                                    onClick={() => setCurrency(c)}
                                    style={{
                                        padding: '10px 8px',
                                        borderRadius: '8px',
                                        border: isActive
                                            ? '1.5px solid rgba(251,191,36,0.5)'
                                            : '1.5px solid transparent',
                                        background: isActive
                                            ? 'rgba(251,191,36,0.12)'
                                            : 'transparent',
                                        cursor: 'pointer',
                                        transition: 'all 0.18s ease',
                                        display: 'flex', flexDirection: 'column',
                                        alignItems: 'center', gap: '4px',
                                        boxShadow: isActive
                                            ? '0 0 0 3px rgba(251,191,36,0.1), inset 0 1px 0 rgba(255,255,255,0.05)'
                                            : 'none',
                                    }}
                                    onMouseOver={e => { if (!isActive) { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; } }}
                                    onMouseOut={e => { if (!isActive) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'transparent'; } }}
                                    title={`${c.label} (${c.symbol})`}
                                >
                                    <span style={{ fontSize: '1.4rem', lineHeight: 1 }}>{c.flag}</span>
                                    <span style={{
                                        fontFamily: 'var(--font-mono,monospace)',
                                        fontWeight: 800, fontSize: '1rem',
                                        color: isActive ? '#fbbf24' : 'var(--text-secondary,#94a3b8)',
                                        transition: 'color 0.18s',
                                    }}>{c.symbol}</span>
                                    <span style={{
                                        fontSize: '0.6rem', fontWeight: 600,
                                        color: isActive ? '#fbbf24' : 'var(--text-muted,#64748b)',
                                        letterSpacing: '0.04em', transition: 'color 0.18s',
                                    }}>{c.code}</span>
                                </button>
                            );
                        })}
                    </div>
                    <p style={{
                        margin: '10px 0 0', fontSize: '0.68rem',
                        color: 'var(--text-muted,#64748b)', lineHeight: 1.55,
                    }}>
                        Sets the symbol displayed on all monetary KPIs, investment panels, leaderboard values, and reports across both the Executive Cockpit and Facilitator Dashboard. Takes effect immediately — no session restart required.
                    </p>
                </div>
            </div>

            {/* ── Engine Groups ── */}
            {GROUPS.map(group => {
                const accent = GROUP_ACCENTS[group.label] || { color: '#94a3b8', glow: 'rgba(148,163,184,0.1)', track: 'linear-gradient(90deg,#475569,#94a3b8)' };
                const visibleKeys = group.keys.filter(k => k in tunables);
                if (visibleKeys.length === 0) return null;

                return (
                    <div
                        key={group.label}
                        style={{
                            background: 'var(--bg-card,#1e293b)',
                            border: '1px solid var(--border-subtle,#334155)',
                            borderRadius: '14px',
                            transition: 'box-shadow 0.2s',
                        }}
                        onMouseEnter={e => e.currentTarget.style.boxShadow = `0 0 0 1px ${accent.color}22, 0 4px 24px ${accent.glow}`}
                        onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
                    >
                        {/* Section header with accent rail */}
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '10px',
                            padding: '12px 20px',
                            background: `linear-gradient(90deg, ${accent.glow}, transparent)`,
                            borderBottom: `1px solid ${accent.color}22`,
                            borderLeft: `3px solid ${accent.color}`,
                            borderRadius: '13px 13px 0 0',
                        }}>
                            <span style={{ fontSize: '0.9rem' }}>{group.icon}</span>
                            <span style={{ fontSize: '0.78rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.12em', color: accent.color }}>
                                {group.label}
                            </span>
                            <span style={{
                                marginLeft: 'auto', fontSize: '0.6rem', fontFamily: 'var(--font-mono,monospace)',
                                color: 'var(--text-muted,#64748b)', padding: '1px 8px',
                                background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-subtle,#334155)', borderRadius: '3px',
                            }}>
                                {visibleKeys.length} param{visibleKeys.length !== 1 ? 's' : ''}
                            </span>
                        </div>

                        {/* 2-column grid of tunable rows */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                            gap: '0',
                            padding: '8px',
                        }}>
                            {visibleKeys.map(key => (
                                <TunableRow
                                    key={key}
                                    varKey={key}
                                    val={tunables[key]}
                                    accentColor={accent.color}
                                    trackGradient={accent.track}
                                    onChange={handleChange}
                                    currSymbol={currency.symbol}
                                />
                            ))}
                        </div>
                    </div>
                );
            })}

            {/* ── Sticky Save Bar ── */}
            <div style={{
                position: 'sticky', bottom: '16px', zIndex: 100,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                gap: '1rem', padding: '12px 20px',
                background: 'rgba(15,23,42,0.92)', backdropFilter: 'blur(16px)',
                border: dirty ? '1px solid rgba(99,102,241,0.4)' : '1px solid var(--border-subtle,#334155)',
                borderRadius: '12px',
                boxShadow: dirty ? '0 4px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(99,102,241,0.1)' : '0 4px 24px rgba(0,0,0,0.2)',
                transition: 'border-color 0.3s, box-shadow 0.3s',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {dirty && (
                        <span style={{
                            display: 'flex', alignItems: 'center', gap: '5px',
                            fontSize: '0.72rem', fontWeight: 600, color: '#f59e0b',
                            padding: '3px 10px', borderRadius: '4px',
                            background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.25)',
                        }}>
                            ● Unsaved changes
                        </span>
                    )}
                    {saved && (
                        <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#4ade80' }}>
                            ✓ All tunables saved
                        </span>
                    )}
                    {error && (
                        <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#f87171' }}>
                            ✕ {error}
                        </span>
                    )}
                    {!dirty && !saved && !error && (
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted,#64748b)' }}>
                            {Object.keys(tunables).length} parameters loaded · changes auto-overwrite the live simulation engine
                        </span>
                    )}
                </div>

                <button
                    onClick={handleSave}
                    disabled={saving || !dirty}
                    style={{
                        padding: '0.6rem 1.75rem', borderRadius: '8px', border: 'none',
                        background: dirty
                            ? 'linear-gradient(135deg, #6366f1, #3b82f6)'
                            : 'rgba(255,255,255,0.06)',
                        color: dirty ? '#fff' : 'var(--text-muted,#64748b)',
                        fontWeight: 700, fontSize: '0.85rem', cursor: dirty ? 'pointer' : 'default',
                        transition: 'all 0.2s',
                        boxShadow: dirty ? '0 4px 16px rgba(99,102,241,0.35)' : 'none',
                        opacity: saving ? 0.7 : 1,
                    }}
                    onMouseOver={e => { if (dirty) e.currentTarget.style.transform = 'translateY(-1px)'; }}
                    onMouseOut={e => { e.currentTarget.style.transform = 'none'; }}
                >
                    {saving ? '⏳ Saving…' : saved ? '✓ Saved' : '💾 Save All Tunables'}
                </button>
            </div>
        </div>
    );
}
