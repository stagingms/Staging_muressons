'use client';

/**
 * CohortSummaryTooltip
 * ─────────────────────────────────────────────────────────────────
 * Portal-based rich card that surfaces a full cohort configuration
 * summary when the user hovers over a cohort name in privileged
 * roles (god_mode, lead_facilitator, super_admin).
 *
 * Architecture contract:
 *  • The *parent* is responsible for role-gating (only render this
 *    component when the user has sufficient privilege).
 *  • This component owns all positioning, animation, and layout.
 *  • It attaches to document.body via createPortal so it is immune
 *    to any parent overflow:hidden / z-index constraints.
 *
 * Props:
 *  session   {object}  Full leaderboard / session object for the cohort
 *  anchorRect {DOMRect} getBoundingClientRect() of the hover target
 *  visible   {boolean} Whether to show the tooltip
 */

import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { resolveVerticalMeta } from '../lib/verticalCatalog';

/* ── Label maps shared with SimulationManager ───────────────────── */
const PARADIGM_LABELS = {
    legacy_abc:           '🏭 Legacy (Manufacturing)',
    stakeholder_weighted: '⚖️ Stakeholder Weighted',
    esg_integrated:       '🌿 ESG Integrated',
    healthcare:           '🏥 Healthcare',
    un_sdg:               '🌍 UN SDG',
    multi_toggles:        '🎛️ Strategic Pillars',
    defense:              '🚀 Defense / Aero',
    brsr_ngrbc:           '🇮🇳 BRSR NGRBC',
};

const EXP_LABELS = {
    classroom_easy:    '🏫 Classroom',
    workshop_standard: '🔧 Workshop',
    executive_hard:    '💼 Executive',
    chaos_extreme:     '🌪️ Chaos Mode',
};

const PACING_LABELS = {
    free_play: '🔓 Free Play',
    manual:    '✋ Manual',
    scheduled: '📅 Scheduled',
};

const MODE_LABELS = {
    multi_bu:  '🏢 Multi Business Unit',
    single_bu: '🏗️ Single Business Unit',
};

// Climate branch (C6: canonical climate_paradigm; falls back to legacy
// simulation_mode which historically doubled as the climate value).
const CLIMATE_LABELS = {
    standard:         'Standard',
    advanced_climate: '⚡ Advanced Climate',
};

const DIFFICULTY_LABELS = {
    easy:     '🟢 Easy',
    standard: '🟡 Standard',
    advanced: '🟠 Advanced',
    hard:     '🔴 Hard',
    extreme:  '🌪️ Extreme',
};

/** Format a fractional rate (0.12 → "12%") or pass through a percent-ish value. */
function fmtRate(v) {
    if (v == null || v === '') return null;
    const n = Number(v);
    if (Number.isNaN(n)) return String(v);
    return n <= 1 ? `${(n * 100).toFixed(n * 100 % 1 ? 1 : 0)}%` : `${n}%`;
}

/* ── Helpers ─────────────────────────────────────────────────────── */
function fmtDate(d) {
    if (!d) return '—';
    // Accept ISO strings like "2026-05-28" or full timestamps
    try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }); }
    catch { return d; }
}

function countEnabled(obj = {}) {
    return Object.values(obj).filter(Boolean).length;
}

/* ── Sub-components ──────────────────────────────────────────────── */

/** Small labelled row: "Label   Value" */
function Row({ label, value, accent }) {
    return (
        <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '0.5rem',
            padding: '2px 0',
        }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--cs-muted)', flexShrink: 0, paddingTop: '1px' }}>
                {label}
            </span>
            <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: accent || 'var(--cs-primary)',
                textAlign: 'right',
                maxWidth: '200px',
                wordBreak: 'break-word',
            }}>
                {value || '—'}
            </span>
        </div>
    );
}

/** Panel with a header + rows */
function Panel({ icon, title, children, accentColor = '#3b82f6' }) {
    return (
        <div style={{
            background: 'rgba(255,255,255,0.03)',
            border: `1px solid rgba(255,255,255,0.06)`,
            borderRadius: '10px',
            overflow: 'hidden',
        }}>
            <div style={{
                padding: '6px 12px',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: `rgba(255,255,255,0.04)`,
            }}>
                <span style={{ fontSize: '0.8rem' }}>{icon}</span>
                <span style={{
                    fontSize: '0.63rem',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.12em',
                    color: accentColor,
                }}>
                    {title}
                </span>
            </div>
            <div style={{ padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {children}
            </div>
        </div>
    );
}

/** Chip badge for lists (pedagogy features, side tracks, etc.) */
function Chip({ label, color }) {
    return (
        <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '2px 8px',
            borderRadius: '20px',
            fontSize: '0.65rem',
            fontWeight: 700,
            background: `${color}18`,
            border: `1px solid ${color}40`,
            color,
            whiteSpace: 'nowrap',
        }}>
            {label}
        </span>
    );
}

/* ── Main component ──────────────────────────────────────────────── */
export default function CohortSummaryTooltip({ session, anchorRect, visible }) {
    const [mounted, setMounted] = useState(false);
    const [finalPos, setFinalPos] = useState({ left: 0, top: 0 });
    const cardRef = useRef(null);

    useEffect(() => { setMounted(true); }, []);

    // Compute position whenever anchorRect or visibility changes
    useEffect(() => {
        if (!visible || !anchorRect || !cardRef.current) return;

        const CARD_W = 580;
        const CARD_H = 520; // approximate (grows with the full parameter set)
        const GAP = 10;
        const PAD = 12; // viewport padding
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        // Prefer anchoring below the hover element; flip up if not enough space
        let top = anchorRect.bottom + GAP;
        if (top + CARD_H > vh - PAD) {
            top = anchorRect.top - CARD_H - GAP;
        }
        if (top < PAD) top = PAD;

        // Centre horizontally on the anchor element, then clamp to viewport
        let left = anchorRect.left + anchorRect.width / 2 - CARD_W / 2;
        if (left + CARD_W > vw - PAD) left = vw - CARD_W - PAD;
        if (left < PAD) left = PAD;

        setFinalPos({ left, top });
    }, [visible, anchorRect]);

    if (!mounted || !session) return null;

    /* ── Derive display values ─────────────────────────────────── */
    const s = session;

    // Core config
    const paradigm    = PARADIGM_LABELS[s.decision_paradigm] || s.decision_paradigm || '—';
    const expLevel    = EXP_LABELS[s.experience_level || s.scenario_preset] || s.experience_level || s.scenario_preset || '—';
    const currency    = s.currency_symbol || s.display_currency || s.currency || '—';
    const startDate   = fmtDate(s.start_date);
    const endDate     = s.end_date ? fmtDate(s.end_date) : '∞ Open';
    const facilitator = s.facilitator_id || '—';
    const cohortName  = s.cohort_name || s.session_id?.slice(0, 16) || '—';

    // Simulation engine
    const endingPathway = (s.ending_pathway || s.active_event_flags?.ending_pathway || '—').replace(/_/g, ' ');
    const simMode       = MODE_LABELS[s.simulation_mode] || s.simulation_mode || '—';
    const _rawVertical  = s.industry_vertical || s.selected_business_unit;
    const _vMeta        = resolveVerticalMeta(_rawVertical);
    const buSelected    = _rawVertical ? `${_vMeta.icon} ${_vMeta.label}` : '—';
    const rawRegion     = s.region || s.selected_region || s.region_id || '—';
    const REGION_LABELS = {
        asean: 'ASEAN',
        south_asia: 'India',
        europe: 'Europe',
        north_america: 'North America',
        africa: 'Africa',
    };
    const region        = REGION_LABELS[rawRegion] || rawRegion;

    // Extra core-config params
    const shortCode      = s.short_code || s.join_code || s.sim_code || '—';
    const difficulty     = DIFFICULTY_LABELS[s.difficulty_tier] || (s.difficulty_tier ? s.difficulty_tier.replace(/_/g, ' ') : '—');
    const loanRate       = fmtRate(s.loan_interest_rate ?? s.loan_interest_rate_start) || '—';
    const scenarioPreset = s.scenario_preset ? String(s.scenario_preset).replace(/_/g, ' ') : null;

    // Climate engine params (C6/C2: climate_paradigm + numeric inputs). These
    // may arrive on the session directly or via its effective settings; render
    // whichever are present. `climate` sub-object supports the new
    // /effective-settings/summary shape.
    const climate       = s.climate || s.effective_settings || {};
    const climateRaw    = s.climate_paradigm ?? climate.climate_paradigm;
    const climateBranch = CLIMATE_LABELS[climateRaw] || (climateRaw ? String(climateRaw).replace(/_/g, ' ') : '—');
    const carbonFeeVal  = s.global_carbon_fee ?? climate.global_carbon_fee;
    const carbonFee     = carbonFeeVal != null ? `$${carbonFeeVal}/t` : null;
    const hostilityVal  = s.market_hostility_index ?? climate.market_hostility_index;
    const hostility     = hostilityVal != null ? `${hostilityVal}/10` : null;
    const scope3Val     = s.scope_3_threshold ?? climate.scope_3_threshold;
    const scope3        = scope3Val != null ? `${scope3Val} kg CO₂e/u` : null;
    const isAdvanced    = climateRaw === 'advanced_climate';

    // Optional modules
    const engines    = s.engine_toggles || s.enabled_engines || {};
    const engOn      = countEnabled(engines);
    const engTotal   = Object.keys(engines).length || 15;
    const sideTracks = s.side_tracks || s.enabled_side_tracks || [];
    const ceoEnabled = !!s.ceo_interview_enabled;
    const ceoVoice   = ceoEnabled ? (s.ceo_interview_voice_gender === 'male' ? '👨‍💼 Alexander' : '👩‍💼 Victoria') : null;

    // Team interventions
    const overrides  = s.interventions_config || s.overrides || {};
    const overridesOn = countEnabled(overrides);
    const overridesTotal = Object.keys(overrides).length || 3;
    const swipeFiles  = s.swipe_files || s.enabled_swipe_files || [];
    const swipeOn     = Array.isArray(swipeFiles) ? swipeFiles.length : 0;
    const swipeTotal  = s.total_swipe_files || 8;
    const pacing      = PACING_LABELS[s.pacing_mode] || '🔓 Free Play';

    // Pedagogy & analytics
    const pedagogy        = s.pedagogical_overrides || s.pedagogical_toggles || s.pedagogy || {};
    const enabledPedagogy = Object.entries(pedagogy)
        .filter(([, v]) => v)
        .map(([k]) => k.replace(/_enabled$/, '').replace(/_/g, ' '));
    const visibilityOverrides = s.analytics_visibility_overrides || s.visibility_overrides || null;
    const visibilityLabel     = visibilityOverrides
        ? `${Object.keys(visibilityOverrides).length} custom override${Object.keys(visibilityOverrides).length !== 1 ? 's' : ''}`
        : 'System default';

    /* ── Render ─────────────────────────────────────────────────── */
    const cardStyle = {
        position: 'fixed',
        zIndex: 2147483647, // max z-index
        left: `${finalPos.left}px`,
        top: `${finalPos.top}px`,
        width: '580px',
        maxWidth: 'calc(100vw - 24px)',
        background: 'rgba(10, 14, 28, 0.97)',
        backdropFilter: 'blur(24px) saturate(1.4)',
        WebkitBackdropFilter: 'blur(24px) saturate(1.4)',
        border: '1px solid rgba(99, 130, 246, 0.2)',
        borderRadius: '16px',
        boxShadow: '0 24px 64px rgba(0,0,0,0.7), 0 4px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06)',
        padding: '14px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        opacity: visible ? 1 : 0,
        transform: visible ? 'scale(1) translateY(0)' : 'scale(0.97) translateY(-6px)',
        transition: 'opacity 0.18s cubic-bezier(0.23,1,0.32,1), transform 0.18s cubic-bezier(0.23,1,0.32,1)',
        pointerEvents: 'none',
        // CSS custom props scoped to this component
        '--cs-primary': '#e2e8f0',
        '--cs-muted': '#64748b',
        '--cs-accent': '#3b82f6',
        fontFamily: 'var(--font-sans, system-ui, -apple-system, sans-serif)',
    };

    return createPortal(
        <div ref={cardRef} style={cardStyle} role="tooltip" aria-live="polite">
            {/* Header */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '2px',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '1.1rem' }}>🗂️</span>
                    <div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#e2e8f0', lineHeight: 1.2 }}>
                            {cohortName}
                        </div>
                        <div style={{ fontSize: '0.63rem', color: '#64748b', fontFamily: 'monospace' }}>
                            {s.session_id?.slice(0, 20)}
                        </div>
                    </div>
                </div>
                <span style={{
                    fontSize: '0.6rem', fontWeight: 800, textTransform: 'uppercase',
                    letterSpacing: '0.12em', color: '#f59e0b',
                    background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.25)',
                    padding: '2px 8px', borderRadius: '6px',
                }}>
                    Cohort Summary
                </span>
            </div>

            {/* 2-column grid for the four main panels */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {/* CORE CONFIGURATION */}
                <Panel icon="📋" title="Core Configuration" accentColor="#818cf8">
                    <Row label="Cohort"      value={cohortName} />
                    <Row label="Code"        value={shortCode} accent="#94a3b8" />
                    <Row label="Facilitator" value={facilitator} />
                    <Row label="Level"       value={expLevel} accent="#a78bfa" />
                    {difficulty !== '—' && <Row label="Difficulty" value={difficulty} accent="#f59e0b" />}
                    {scenarioPreset     && <Row label="Preset"     value={scenarioPreset} />}
                    <Row label="Dates"       value={`${startDate} → ${endDate}`} />
                    <Row label="Region"      value={region}     accent="#34d399" />
                    <Row label="Currency"    value={currency} accent="#22c55e" />
                    {loanRate !== '—'   && <Row label="Loan Rate" value={loanRate} accent="#fbbf24" />}
                </Panel>

                {/* SIMULATION ENGINE */}
                <Panel icon="⚙️" title="Simulation Engine" accentColor="#3b82f6">
                    <Row label="Paradigm" value={paradigm}      accent="#60a5fa" />
                    <Row label="Climate"  value={climateBranch} accent={isAdvanced ? '#f97316' : '#60a5fa'} />
                    <Row label="Ending"   value={endingPathway} accent="#f59e0b" />
                    <Row label="Mode"     value={simMode}       accent="#818cf8" />
                    <Row label="BU"       value={buSelected}    accent="#60a5fa" />
                    {carbonFee && <Row label="Carbon Fee" value={carbonFee} accent="#f97316" />}
                    {hostility && <Row label="Hostility"  value={hostility} accent="#f97316" />}
                    {scope3    && <Row label="Scope-3"    value={scope3}    accent="#f97316" />}
                </Panel>

                {/* OPTIONAL MODULES */}
                <Panel icon="🎛️" title="Optional Modules" accentColor="#f59e0b">
                    <Row label="Engine"
                         value={engTotal > 0 ? `${engOn}/${engTotal} on` : '—'}
                         accent="#f59e0b" />
                    <Row label="Side Tracks"
                         value={sideTracks.length > 0 ? `${sideTracks.length} selected` : 'None'}
                         accent={sideTracks.length > 0 ? '#f59e0b' : undefined} />
                    {sideTracks.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '2px' }}>
                            {sideTracks.slice(0, 2).map(t => (
                                <Chip
                                    key={typeof t === 'string' ? t : t.track_id}
                                    label={(typeof t === 'string' ? t : t.track_id).replace(/_/g, ' ')}
                                    color="#f59e0b"
                                />
                            ))}
                            {sideTracks.length > 2 && (
                                <Chip label={`+${sideTracks.length - 2} more`} color="#94a3b8" />
                            )}
                        </div>
                    )}
                    <Row label="CEO Interview"
                         value={ceoEnabled ? `● Enabled ${ceoVoice ? `— ${ceoVoice}` : ''}` : '○ Off'}
                         accent={ceoEnabled ? '#10b981' : undefined} />
                </Panel>

                {/* TEAM INTERVENTIONS */}
                <Panel icon="⚡" title="Team Interventions" accentColor="#f59e0b">
                    <Row label="Overrides"
                         value={overridesTotal > 0
                             ? `${overridesOn}/${overridesTotal} selected`
                             : (s.overrides_count != null ? `${s.overrides_count}/3 selected` : '—')}
                         accent={overridesOn > 0 ? '#22c55e' : undefined} />
                    <Row label="Swipe Files"
                         value={swipeOn > 0
                             ? `${swipeOn}/${swipeTotal} selected`
                             : (s.swipe_file_count != null ? `${s.swipe_file_count}/${swipeTotal} selected` : '—')}
                         accent={swipeOn > 0 ? '#22c55e' : undefined} />
                    <Row label="Round Pacing" value={pacing} />
                </Panel>
            </div>

            {/* PEDAGOGY & ANALYTICS — full width */}
            <Panel icon="🎓" title="Pedagogy & Analytics" accentColor="#a78bfa">
                <Row label="Scaffolding"
                     value={enabledPedagogy.length > 0
                         ? `${enabledPedagogy.length} feature${enabledPedagogy.length !== 1 ? 's' : ''} active`
                         : 'None enabled'}
                     accent={enabledPedagogy.length > 0 ? '#a78bfa' : undefined} />
                {enabledPedagogy.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '2px' }}>
                        {enabledPedagogy.map(p => (
                            <Chip key={p} label={p} color="#a78bfa" />
                        ))}
                    </div>
                )}
                <Row label="Visibility" value={visibilityLabel}
                     accent={visibilityOverrides ? '#22c55e' : undefined} />
            </Panel>
        </div>,
        document.body
    );
}
