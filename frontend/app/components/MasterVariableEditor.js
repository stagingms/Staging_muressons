'use client';
import { useState, useEffect, useRef } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// ─── Per-section design tokens ─────────────────────────────────────────────
const SECTION_STYLE = {
    economic:   { color: '#6366f1', bg: 'rgba(99,102,241,0.06)',  border: 'rgba(99,102,241,0.2)',  icon: '💰', label: 'Global Economic & Capital Vectors' },
    reputation: { color: '#06b6d4', bg: 'rgba(6,182,212,0.06)',   border: 'rgba(6,182,212,0.2)',   icon: '🛡️', label: 'Reputational & Contagion Vectors' },
    climate:    { color: '#10b981', bg: 'rgba(16,185,129,0.06)',  border: 'rgba(16,185,129,0.2)',  icon: '🌍', label: 'Advanced Climate Engine Mechanics' },
    bu_metrics: { color: '#f59e0b', bg: 'rgba(245,158,11,0.06)', border: 'rgba(245,158,11,0.2)', icon: '🏭', label: 'Business Unit Sub-Level Metrics' },
};

const SCOPE_COLORS = {
    Global:         { color: '#6366f1', bg: 'rgba(99,102,241,0.1)' },
    'Global (Tick)': { color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)' },
    Universal:      { color: '#06b6d4', bg: 'rgba(6,182,212,0.1)' },
    'Global Toggle': { color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
    'Event Toggle':  { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
    'BU Level':     { color: '#f97316', bg: 'rgba(249,115,22,0.1)' },
    'BU (Software)': { color: '#ec4899', bg: 'rgba(236,72,153,0.1)' },
};

// ─── Variable definitions ──────────────────────────────────────────────────
// Each variable: { key, formKey?, scope, boundary, logic, editable }
const SECTIONS = [
    {
        id: 'economic',
        vars: [
            { key: 'corporate_treasury',  formKey: 'corporate_treasury_start',  scope: 'Global', boundary: '[-$500M, +∞]', editable: true,  step: 1000000,
              logic: 'Master cash pool. If < 0, mathematically attracts |abs(treasury) × cost_of_capital| interest. Clamped rigidly at -$500,000,000 to halt infinite Javascript insolvency limits.',
              refs: ['cost_of_capital'] },
            { key: 'cost_of_capital',     formKey: 'cost_of_capital_start',     scope: 'Global', boundary: '[0.05, 1.0]', editable: true, step: 0.01,
              logic: 'Interest rate applied dynamically to negative treasury balances. Spikes permanently by +0.015 (1.5%) round-over-round if any single BU holds a carbon_intensity > 120.',
              refs: ['carbon_intensity'] },
            { key: 'loan_interest_rate',  formKey: 'loan_interest_rate_start',  scope: 'Global', boundary: '[0.0, 1.0]', editable: true, step: 0.01,
              logic: 'Instantaneous loan rate charged if total_capex_requested across all 4 BUs exceeds base_treasury × 0.20 within a single round.',
              refs: ['corporate_treasury'] },
            { key: 'dividends_paid',      formKey: null,                         scope: 'Global', boundary: '[0.0, treasury]', editable: false, defaultDisplay: '0.0',
              logic: 'Selected explicitly by the player. Mathematically capped by the UI to never physically exceed the base_treasury balance.',
              refs: ['corporate_treasury'] },
            { key: 'historical_ebitda',   formKey: null,                         scope: 'Global', boundary: '[0.0, +∞]', editable: false, defaultDisplay: 'Derived',
              logic: 'Group-level gross profit proxy calculated each tick: Σ(revenue_base − opex_base) across all BUs.',
              formula: 'Σ(revenue_base − opex_base)', refs: ['revenue_base', 'opex_base'] },
        ],
    },
    {
        id: 'reputation',
        vars: [
            { key: 'group_reputation',    formKey: 'group_reputation_start',    scope: 'Global', boundary: '[0.0, 100.0]', editable: true, step: 1,
              logic: 'Master resilience stat. Suppresses structural damage inside calc_contagion() when crisis_severity initiates. Hard-drops −20 if AI Bias (R6) is exploited.',
              refs: ['crisis_severity'] },
            { key: 'crisis_severity',     formKey: null,                         scope: 'Global (Tick)', boundary: '[0.0, 100.0]', editable: false, defaultDisplay: '0.0 – 50.0',
              logic: 'Base reputational or structural damage incoming from a round\'s narrative event.',
              formula: 'Contagion = severity × (1.0 − group_reputation/100)', refs: ['group_reputation'] },
            { key: 'synergy_multiplier',  formKey: 'synergy_multiplier_start',  scope: 'Global', boundary: '[1.0, 1.35×]', editable: true, step: 0.1,
              logic: 'Lowers global OPEX through the calc_synergy_opex formula. Option C in R7 unlocks a massive +0.35 multiplier, heavily boosting profitability.',
              refs: ['opex_base'] },
            { key: 'imitation_decay_rate', formKey: null, scope: 'Universal', boundary: '[0.0, 1.0]', editable: false, defaultDisplay: '0.05 (engine constant)', step: 0.01,
              logic: 'The "VRIO Advantage Bleed." Mathematically decays the synergy_multiplier passively by 5% every turn to simulate competitors catching up. This is a hardcoded engine constant — not adjustable via the admin UI.',
              refs: ['synergy_multiplier'] },
        ],
    },
    {
        id: 'climate',
        vars: [
            { key: 'market_hostility_index', formKey: 'market_hostility_index', scope: 'Global', boundary: '[1.0, 5.0]', editable: true, step: 1,
              logic: 'Abstract scalar. In Advanced Climate mode, determines Toxic NCD OPEX penalties: NCD × 50,000 × hostility. Multiplies by 2 if Tipping Point triggers.',
              formula: 'NCD × 50,000 × hostility', refs: ['natural_capital_debt'] },
            { key: 'tipping_point_active', formKey: null,                        scope: 'Global Toggle', boundary: 'True/False', editable: false, defaultDisplay: 'False',
              logic: 'Triggered irreversibly in Round ≥ 5 if the group\'s avg(carbon_intensity) > 100. Permanently doubles the market_hostility_index.',
              refs: ['carbon_intensity', 'market_hostility_index'] },
            { key: 'green_transition_fund', formKey: 'green_transition_fund_start', scope: 'Global', boundary: '[0, +∞]', editable: true, step: 1000000,
              logic: 'Accrues via internal taxation. Every round: green_fund += tco2e_emissions × carbon_fee_per_ton. Can explicitly offset R7, R8, R9 systemic CapEx requirements.',
              formula: 'green_fund += tCO₂e × carbon_fee', refs: ['carbon_fee_per_ton'] },
            { key: 'carbon_fee_per_ton',  formKey: 'global_carbon_fee',          scope: 'Global', boundary: '[0, 1000]', editable: true, step: 10,
              logic: 'Internal tax rate parameter. Spikes to $250 automatically at R10 (Year 3) Terminal Valuation calculation.',
              refs: ['green_transition_fund'] },
            { key: 'resilience_factor',   formKey: null,                         scope: 'Event Toggle', boundary: '[0.0, 1.0]', editable: false, defaultDisplay: '0.0',
              logic: 'Stored in the pending_capex_projects array. When R5 Hard-Engineering completes after a 2-round delay, it is extracted as active_resilience_factor (usually 0.85) mitigating stochastic cyclone damage.',
              refs: [] },
        ],
    },
    {
        id: 'bu_metrics',
        vars: [
            { key: 'natural_capital_debt', formKey: null, scope: 'BU Level', boundary: '[0, 1,000,000]', editable: false, defaultDisplay: 'Phar: 10, Elec: 25, Other: 0',
              logic: 'Accrues cost_of_capital simple interest. Penalizes OPEX in Advanced Climate: bu_opex += (NCD × 50,000 × hostility) / 1,000,000.',
              formula: 'bu_opex += (NCD × 50k × hostility) / 1M', refs: ['cost_of_capital', 'market_hostility_index'] },
            { key: 'carbon_intensity', formKey: null, scope: 'BU Level', boundary: '[0, +∞]', editable: false, defaultDisplay: 'Phar: 45 · Elec: 72 · Cons: 38 · Soft: 28',
              logic: 'Tracks fossil fuel reliance. > 120 = Stranded Asset (+1.5% CoC debt multiplier). Avg > 100 = Tipping Point.',
              refs: ['cost_of_capital'] },
            { key: 'social_license_score', formKey: null, scope: 'BU Level', boundary: '[0.0, 100.0]', editable: false, defaultDisplay: 'Soft: 60 · Phar: 55 · Other: ~50',
              logic: 'Local community trust. Determines Strike Probability in R9: p = calc_strike_probability(base_risk, SL). If avg(SL) < 50 in R9, probability overrides to 75% for revenue zeroization.',
              formula: 'p(strike) = f(gov_risk, SL)', refs: ['governance_risk_score'] },
            { key: 'governance_risk_score', formKey: null, scope: 'BU Level', boundary: '[0.0, 100.0]', editable: false, defaultDisplay: 'Elec: 20 · Phar: 15 · Other: ≤10',
              logic: 'Spikes heavily (+10) via Supply Chain disruptions in R3. Acts as the base_risk multiplier for strikes, and informs the VRIO organization vector.',
              refs: ['social_license_score'] },
            { key: 'revenue_base', formKey: null, scope: 'BU Level', boundary: '[0, +∞]', editable: false, defaultDisplay: '$8M – $18M',
              logic: 'Top-line revenue per BU unit. Mathematically zeroed out ($0) entirely by labour union strikes in R9.',
              refs: [] },
            { key: 'opex_base', formKey: null, scope: 'BU Level', boundary: '[0, +∞]', editable: false, defaultDisplay: '$4M – $11M',
              logic: 'Operating expenses per BU. Drops through synergy_multiplier and spikes via NCD penalties.',
              refs: ['synergy_multiplier', 'natural_capital_debt'] },
            { key: 'water_dependency', formKey: null, scope: 'BU Level', boundary: '[0, 100]', editable: false, defaultDisplay: 'Phar: 82 · Elec: 58 · Cons: 65 · Soft: 12',
              logic: 'Modified by R8 Desalination (−40, delayed 2 rounds) or Water Efficiency (−20, immediate). High values increase exposure to Round 8 Blue Stress crisis.',
              refs: [] },
            { key: 'talent_penalty', formKey: null, scope: 'BU (Software)', boundary: '[0, opex]', editable: false, defaultDisplay: '$0',
              logic: 'Exclusive to the Software BU. Emulates Brain-Drain by adding overhead. Derived exponentially against dropping group_reputation.',
              refs: ['group_reputation'] },
        ],
    },
];

// ─── Human label from snake_case ─────────────────────────────────────────
function humanize(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ─── Variable Card ────────────────────────────────────────────────────────
function VariableCard({ v, formValue, onChangeForm, sectionColor }) {
    const [expanded, setExpanded] = useState(false);

    const scopeStyle = SCOPE_COLORS[v.scope] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)' };

    return (
        <div style={{
            background: 'var(--bg-card,#1e293b)',
            border: '1px solid var(--border-subtle,#334155)',
            borderRadius: '12px',
            transition: 'border-color 0.15s, box-shadow 0.15s',
            overflow: 'hidden',
        }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = `${sectionColor}44`; e.currentTarget.style.boxShadow = `0 2px 12px ${sectionColor}11`; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-subtle,#334155)'; e.currentTarget.style.boxShadow = 'none'; }}
        >
            {/* ── Top stripe ── */}
            <div style={{ height: '2px', background: sectionColor, opacity: 0.5 }} />

            <div style={{ padding: '16px 18px 14px' }}>
                {/* Row 1: Variable name + scope + boundary */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', flexWrap: 'wrap' }}>
                    {/* Variable name */}
                    <code style={{
                        fontSize: '0.78rem', fontWeight: 700, fontFamily: 'var(--font-mono,monospace)',
                        color: sectionColor, background: `${sectionColor}12`,
                        padding: '3px 9px', borderRadius: '5px', border: `1px solid ${sectionColor}30`,
                        letterSpacing: '0.02em',
                    }}>
                        {v.key}
                    </code>

                    {/* Scope badge */}
                    <span style={{
                        fontSize: '0.68rem', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase',
                        padding: '2px 7px', borderRadius: '3px',
                        background: scopeStyle.bg, color: scopeStyle.color,
                        border: `1px solid ${scopeStyle.color}33`,
                    }}>
                        {v.scope}
                    </span>

                    {/* Boundary */}
                    <span style={{
                        marginLeft: 'auto', fontSize: '0.68rem', fontFamily: 'var(--font-mono,monospace)',
                        color: 'var(--text-muted,#64748b)', padding: '2px 7px',
                        background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle,#334155)',
                        borderRadius: '3px',
                    }}>
                        {v.boundary}
                    </span>
                </div>

                {/* Row 2: Human-readable name */}
                <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-primary,#f1f5f9)', marginBottom: '10px', lineHeight: 1.3 }}>
                    {humanize(v.key)}
                </div>

                {/* Row 3: Value display / input */}
                <div style={{ marginBottom: '10px' }}>
                    {v.editable && v.formKey && formValue !== undefined ? (
                        <input
                            type="number"
                            step={v.step || 1}
                            value={formValue}
                            onChange={e => onChangeForm(v.formKey, e.target.value)}
                            style={{
                                width: '100%', maxWidth: '180px', boxSizing: 'border-box',
                                padding: '8px 12px', borderRadius: '6px',
                                border: `1.5px solid ${sectionColor}55`,
                                background: 'rgba(255,255,255,0.04)', color: 'var(--text-primary,#f1f5f9)',
                                fontFamily: 'var(--font-mono,monospace)', fontSize: '0.95rem', fontWeight: 700,
                                outline: 'none', transition: 'border-color 0.15s, box-shadow 0.15s',
                            }}
                            onFocus={e => { e.target.style.borderColor = sectionColor; e.target.style.boxShadow = `0 0 0 3px ${sectionColor}22`; }}
                            onBlur={e => { e.target.style.borderColor = `${sectionColor}55`; e.target.style.boxShadow = 'none'; }}
                        />
                    ) : (
                        <div style={{
                            display: 'inline-flex', alignItems: 'center', gap: '6px',
                            padding: '6px 12px', borderRadius: '6px',
                            background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle,#334155)',
                        }}>
                            <span style={{ fontSize: '0.6rem', color: 'var(--text-muted,#475569)' }}>⏹</span>
                            <span style={{
                                fontFamily: 'var(--font-mono,monospace)', fontSize: '0.82rem', fontWeight: 600,
                                color: 'var(--text-muted,#94a3b8)',
                            }}>
                                {v.defaultDisplay}
                            </span>
                            <span style={{
                                fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em',
                                color: 'var(--text-muted,#475569)', textTransform: 'uppercase',
                            }}>
                                Read-only
                            </span>
                        </div>
                    )}
                </div>

                {/* Row 4: Formula badge (if exists) */}
                {v.formula && (
                    <div style={{
                        display: 'inline-block', marginBottom: '8px',
                        padding: '3px 10px', borderRadius: '4px',
                        background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
                        fontFamily: 'var(--font-mono,monospace)', fontSize: '0.7rem', fontWeight: 600,
                        color: '#10b981',
                    }}>
                        ƒ {v.formula}
                    </div>
                )}

                {/* Row 5: Expandable math/trigger logic */}
                <div
                    onClick={() => setExpanded(!expanded)}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                >
                    <div style={{
                        fontSize: '0.72rem', color: 'var(--text-muted,#94a3b8)', lineHeight: 1.65,
                        overflow: 'hidden',
                        maxHeight: expanded ? '200px' : '2.8em',
                        transition: 'max-height 0.25s ease',
                    }}>
                        {v.logic}
                    </div>
                    {v.logic.length > 100 && (
                        <button style={{
                            background: 'none', border: 'none', padding: '4px 0 0', cursor: 'pointer',
                            fontSize: '0.68rem', fontWeight: 700, color: sectionColor,
                            letterSpacing: '0.06em', textTransform: 'uppercase',
                        }}>
                            {expanded ? '▲ Less' : '▼ More'}
                        </button>
                    )}
                </div>

                {/* Row 6: Cross-reference tags */}
                {v.refs && v.refs.length > 0 && (
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '8px' }}>
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted,#475569)', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', alignSelf: 'center', marginRight: '2px' }}>
                            Refs:
                        </span>
                        {v.refs.map(r => (
                            <span key={r} style={{
                                fontSize: '0.68rem', fontFamily: 'var(--font-mono,monospace)',
                                padding: '1px 6px', borderRadius: '3px',
                                background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-subtle,#334155)',
                                color: 'var(--text-muted,#64748b)',
                            }}>
                                {r}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

// ─── Main Component ────────────────────────────────────────────────────────
export default function MasterVariableEditor() {
    const [settings, setSettings] = useState(null);
    const [status, setStatus] = useState('');
    const [error, setError] = useState('');
    const [saving, setSaving] = useState(false);
    const [search, setSearch] = useState('');

    const [form, setForm] = useState({
        corporate_treasury_start: 25000000,
        cost_of_capital_start: 0.05,
        loan_interest_rate_start: 0.12,
        group_reputation_start: 50.0,
        synergy_multiplier_start: 1.0,
        market_hostility_index: 5,
        global_carbon_fee: 40,
        green_transition_fund_start: 0,
    });

    const load = async () => {
        try {
            const res = await fetch(`${API}/api/admin/god/settings`);
            if (res.ok) {
                const data = await res.json();
                setSettings(data);
                setForm(prev => ({
                    corporate_treasury_start: data.corporate_treasury_start ?? prev.corporate_treasury_start,
                    cost_of_capital_start: data.cost_of_capital_start ?? prev.cost_of_capital_start,
                    loan_interest_rate_start: data.loan_interest_rate_start ?? prev.loan_interest_rate_start,
                    group_reputation_start: data.group_reputation_start ?? prev.group_reputation_start,
                    synergy_multiplier_start: data.synergy_multiplier_start ?? prev.synergy_multiplier_start,
                    market_hostility_index: data.market_hostility_index ?? prev.market_hostility_index,
                    global_carbon_fee: data.global_carbon_fee ?? prev.global_carbon_fee,
                    green_transition_fund_start: data.green_transition_fund_start ?? prev.green_transition_fund_start,
                }));
            }
        } catch (e) { setError('Failed to load global settings.'); }
    };

    useEffect(() => { load(); }, []);

    const handleChange = (key, val) => setForm(prev => ({ ...prev, [key]: Number(val) }));

    const handleSave = async () => {
        setSaving(true); setStatus(''); setError('');
        try {
            const res = await fetch(`${API}/api/admin/god/settings`, {
                method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            });
            if (res.ok) { setStatus('✅ Master variables published for all future cohorts.'); load(); }
            else setError('Failed to update master variables.');
        } catch { setError('Network error occurred.'); }
        finally { setSaving(false); setTimeout(() => { setStatus(''); setError(''); }, 4000); }
    };

    const hasChanges = settings && Object.keys(form).some(k => form[k] !== (settings[k] ?? form[k]));

    // Search filter
    const q = search.trim().toLowerCase();
    const filteredSections = SECTIONS.map(sec => ({
        ...sec,
        vars: q ? sec.vars.filter(v =>
            v.key.includes(q) || humanize(v.key).toLowerCase().includes(q) ||
            v.logic.toLowerCase().includes(q) || v.scope.toLowerCase().includes(q)
        ) : sec.vars,
    })).filter(sec => sec.vars.length > 0);

    const totalVars = SECTIONS.reduce((s, sec) => s + sec.vars.length, 0);
    const editableCount = SECTIONS.reduce((s, sec) => s + sec.vars.filter(v => v.editable).length, 0);

    if (!settings) return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: 'var(--text-muted,#64748b)', gap: '10px' }}>
            <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: '2px solid currentColor', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite' }} />
            Loading master variable tables…
            <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
        </div>
    );

    return (
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', fontFamily: 'var(--font-sans,system-ui,sans-serif)' }}>

            {/* ── Header ── */}
            <div style={{
                display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
                gap: '16px', flexWrap: 'wrap', paddingBottom: '1.25rem',
                borderBottom: '1px solid var(--border-subtle,#334155)',
            }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
                        <div style={{
                            width: '42px', height: '42px', borderRadius: '10px', display: 'flex',
                            alignItems: 'center', justifyContent: 'center', fontSize: '1.4rem',
                            background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15))',
                            border: '1px solid rgba(139,92,246,0.25)',
                        }}>🎛️</div>
                        <div>
                            <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary,#f1f5f9)' }}>
                                Master Variables
                            </h2>
                            <p style={{ margin: '2px 0 0', fontSize: '0.72rem', color: 'var(--text-muted,#64748b)' }}>
                                Exhaustive global dataset — overrides defaults for newly created simulation cohorts
                            </p>
                        </div>
                    </div>
                    {/* Stats */}
                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                        <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted,#475569)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                            {totalVars} Variables · {editableCount} Editable · {SECTIONS.length} Sections
                        </span>
                    </div>
                </div>

                {/* Search */}
                <div style={{ position: 'relative', minWidth: '220px', alignSelf: 'center' }}>
                    <span style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', fontSize: '0.8rem', color: 'var(--text-muted,#64748b)', pointerEvents: 'none' }}>🔍</span>
                    <input
                        type="search"
                        placeholder="Filter variables…"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        style={{
                            paddingLeft: '32px', paddingRight: '10px', paddingTop: '8px', paddingBottom: '8px',
                            borderRadius: '8px', border: '1.5px solid var(--border-subtle,#334155)',
                            background: 'rgba(255,255,255,0.03)', color: 'var(--text-primary,#f1f5f9)',
                            fontSize: '0.78rem', outline: 'none', width: '100%', boxSizing: 'border-box',
                            fontFamily: 'var(--font-sans,system-ui)', transition: 'border-color 0.2s',
                        }}
                        onFocus={e => e.target.style.borderColor = '#6366f1'}
                        onBlur={e => e.target.style.borderColor = 'var(--border-subtle,#334155)'}
                    />
                </div>
            </div>

            {/* ── Status ── */}
            {status && (
                <div style={{ padding: '10px 16px', borderRadius: '8px', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', color: '#10b981', fontSize: '0.8rem', fontWeight: 600 }}>
                    {status}
                </div>
            )}
            {error && (
                <div style={{ padding: '10px 16px', borderRadius: '8px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', color: '#ef4444', fontSize: '0.8rem', fontWeight: 600 }}>
                    {error}
                </div>
            )}

            {/* ── No results ── */}
            {filteredSections.length === 0 && q && (
                <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-muted,#64748b)' }}>
                    <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>🤷</div>
                    <div style={{ fontWeight: 600, marginBottom: '4px', fontSize: '0.85rem' }}>No variables match "{search}"</div>
                </div>
            )}

            {/* ── Sections ── */}
            {filteredSections.map(sec => {
                const style = SECTION_STYLE[sec.id];
                return (
                    <section key={sec.id}>
                        {/* Section header */}
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '10px',
                            marginBottom: '12px', paddingBottom: '10px',
                            borderBottom: `2px solid ${style.color}33`,
                        }}>
                            <span style={{ fontSize: '1rem' }}>{style.icon}</span>
                            <span style={{
                                fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase',
                                letterSpacing: '0.12em', color: style.color,
                            }}>
                                {style.label}
                            </span>
                            <span style={{
                                marginLeft: 'auto', fontSize: '0.68rem', fontFamily: 'var(--font-mono,monospace)',
                                color: 'var(--text-muted,#64748b)', padding: '1px 8px',
                                background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle,#334155)',
                                borderRadius: '3px',
                            }}>
                                {sec.vars.length} var{sec.vars.length !== 1 ? 's' : ''}
                            </span>
                        </div>

                        {/* Card grid */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                            gap: '12px',
                            marginBottom: '20px',
                        }}>
                            {sec.vars.map(v => (
                                <VariableCard
                                    key={v.key}
                                    v={v}
                                    formValue={v.formKey ? form[v.formKey] : undefined}
                                    onChangeForm={handleChange}
                                    sectionColor={style.color}
                                />
                            ))}
                        </div>
                    </section>
                );
            })}

            {/* ── Sticky Save Bar ── */}
            <div style={{
                position: 'sticky', bottom: '16px', zIndex: 100,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                gap: '1rem', padding: '12px 20px',
                background: 'rgba(15,23,42,0.92)', backdropFilter: 'blur(16px)',
                border: hasChanges ? '1px solid rgba(99,102,241,0.4)' : '1px solid var(--border-subtle,#334155)',
                borderRadius: '12px',
                boxShadow: hasChanges ? '0 4px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(99,102,241,0.1)' : '0 4px 24px rgba(0,0,0,0.2)',
                transition: 'border-color 0.3s, box-shadow 0.3s',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {hasChanges ? (
                        <span style={{
                            fontSize: '0.72rem', fontWeight: 600, color: '#f59e0b',
                            padding: '3px 10px', borderRadius: '4px',
                            background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.25)',
                        }}>
                            ● Unsaved changes
                        </span>
                    ) : (
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted,#64748b)' }}>
                            Publishing overwrites defaults for all future simulation cohorts
                        </span>
                    )}
                </div>

                <button
                    onClick={handleSave}
                    disabled={saving || !hasChanges}
                    style={{
                        padding: '0.6rem 1.5rem', borderRadius: '8px', border: 'none',
                        background: hasChanges ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(255,255,255,0.06)',
                        color: hasChanges ? '#fff' : 'var(--text-muted,#64748b)',
                        fontWeight: 700, fontSize: '0.82rem', cursor: hasChanges ? 'pointer' : 'default',
                        transition: 'all 0.2s',
                        boxShadow: hasChanges ? '0 4px 16px rgba(99,102,241,0.35)' : 'none',
                        opacity: saving ? 0.7 : 1, whiteSpace: 'nowrap',
                    }}
                    onMouseOver={e => { if (hasChanges) e.currentTarget.style.transform = 'translateY(-1px)'; }}
                    onMouseOut={e => { e.currentTarget.style.transform = 'none'; }}
                >
                    {saving ? '⏳ Publishing…' : hasChanges ? '🚀 Publish Globals' : '✓ Published'}
                </button>
            </div>
        </div>
    );
}
